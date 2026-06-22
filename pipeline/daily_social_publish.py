from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime

from pipeline.daily_post_preparation import prepare_daily_posts
from publishing.prepared_post import PreparedPost
from publishing.publish_result import PublishResult
from publishing.social_publish_pipeline import (
    DEFAULT_SOCIAL_PUBLISHERS,
    PublishFunction,
    publish_prepared_post_to_social_channels,
)
from storage.posted_history import (
    POST_STATUS_PARTIAL_FAILED,
    POST_STATUS_PUBLISHED,
    PostedHistoryRecord,
    append_posted_history_records,
    upload_today_posted_history_to_r2,
)


@dataclass(frozen=True)
class DailySocialPublishResult:
    prepared_post: PreparedPost
    publish_results: list[PublishResult]


def publish_daily_posts_to_social_channels(
    today: date | None = None,
    sync_posted_history: bool = True,
    upload_assets: bool = True,
    publish_functions: tuple[PublishFunction, ...] = DEFAULT_SOCIAL_PUBLISHERS,
    record_posted_history: bool = True,
    upload_posted_history: bool = True,
) -> list[DailySocialPublishResult]:
    run_date = today or date.today()
    prepared_posts = prepare_daily_posts(
        today=run_date,
        sync_posted_history=sync_posted_history,
        upload_assets=upload_assets,
    )

    daily_publish_results = publish_prepared_posts_to_social_channels(
        prepared_posts=prepared_posts,
        publish_functions=publish_functions,
    )

    if record_posted_history:
        history_records = build_posted_history_records_from_publish_results(
            daily_publish_results
        )
        append_posted_history_records(history_records)

        if upload_posted_history:
            upload_today_posted_history_to_r2(run_date=run_date.isoformat())

    return daily_publish_results


def publish_prepared_posts_to_social_channels(
    *,
    prepared_posts: list[PreparedPost],
    publish_functions: tuple[PublishFunction, ...] = DEFAULT_SOCIAL_PUBLISHERS,
) -> list[DailySocialPublishResult]:
    daily_publish_results: list[DailySocialPublishResult] = []

    for prepared_post in prepared_posts:
        publish_results = publish_prepared_post_to_social_channels(
            prepared_post=prepared_post,
            publish_functions=publish_functions,
        )
        daily_publish_results.append(
            DailySocialPublishResult(
                prepared_post=prepared_post,
                publish_results=publish_results,
            )
        )

    return daily_publish_results


def build_posted_history_records_from_publish_results(
    daily_publish_results: list[DailySocialPublishResult],
) -> list[PostedHistoryRecord]:
    history_records: list[PostedHistoryRecord] = []

    for daily_publish_result in daily_publish_results:
        successful_results = [
            publish_result
            for publish_result in daily_publish_result.publish_results
            if publish_result.is_success
        ]

        if not successful_results:
            continue

        history_records.append(
            build_posted_history_record(
                daily_publish_result=daily_publish_result,
                successful_result_count=len(successful_results),
            )
        )

    return history_records


def build_posted_history_record(
    *,
    daily_publish_result: DailySocialPublishResult,
    successful_result_count: int,
) -> PostedHistoryRecord:
    prepared_post = daily_publish_result.prepared_post
    post_content = prepared_post.post_content
    publish_results = daily_publish_result.publish_results

    return PostedHistoryRecord(
        recorded_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        status=build_posted_history_status(
            publish_results=publish_results,
            successful_result_count=successful_result_count,
        ),
        category=post_content.category,
        title=post_content.title,
        source_name=post_content.source_name,
        source_url=post_content.source_url,
        facebook_post_id=find_remote_post_id(publish_results, "facebook"),
        instagram_post_id=find_remote_post_id(publish_results, "instagram"),
        threads_post_id=find_remote_post_id(publish_results, "threads"),
        naver_band_post_key=find_remote_post_id(publish_results, "naver_band"),
    )


def build_posted_history_status(
    *,
    publish_results: list[PublishResult],
    successful_result_count: int,
) -> str:
    if successful_result_count == len(publish_results):
        return POST_STATUS_PUBLISHED

    return POST_STATUS_PARTIAL_FAILED


def find_remote_post_id(
    publish_results: list[PublishResult],
    channel_name: str,
) -> str:
    for publish_result in publish_results:
        if publish_result.channel_name != channel_name:
            continue

        if publish_result.remote_post_id:
            return publish_result.remote_post_id

    return ""

