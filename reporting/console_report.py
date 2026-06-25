from __future__ import annotations

from pipeline.daily_social_publish import DailySocialPublishResult


def print_daily_publish_results(
    daily_publish_results: list[DailySocialPublishResult],
) -> None:
    if not daily_publish_results:
        print("오늘 게시할 후보가 없습니다.")
        return

    print(f"오늘 게시 대상: {len(daily_publish_results)}건")

    for index, daily_publish_result in enumerate(daily_publish_results, start=1):
        post_content = daily_publish_result.prepared_post.post_content
        print(f"{index}. [{post_content.category}] {post_content.title}")

        for publish_result in daily_publish_result.publish_results:
            status_text = "성공" if publish_result.is_success else "실패"
            print(f"   - {publish_result.channel_name}: {status_text}")

            if publish_result.remote_post_id:
                print(f"     게시 ID: {publish_result.remote_post_id}")

            if publish_result.remote_url:
                print(f"     게시 URL: {publish_result.remote_url}")

            if publish_result.error_message:
                print(f"     오류: {publish_result.error_message}")

        if is_partially_failed_post(daily_publish_result):
            print("   ※ 일부 채널만 실패했습니다(부분 게시).")
        elif is_completely_failed_post(daily_publish_result):
            print("   ※ 모든 채널 게시에 실패했습니다.")


def has_completely_failed_post(
    daily_publish_results: list[DailySocialPublishResult],
) -> bool:
    return any(
        is_completely_failed_post(daily_publish_result)
        for daily_publish_result in daily_publish_results
    )


def is_completely_failed_post(
    daily_publish_result: DailySocialPublishResult,
) -> bool:
    publish_results = daily_publish_result.publish_results

    if not publish_results:
        return False

    return all(
        not publish_result.is_success
        for publish_result in publish_results
    )


def is_partially_failed_post(
    daily_publish_result: DailySocialPublishResult,
) -> bool:
    publish_results = daily_publish_result.publish_results

    has_success = any(
        publish_result.is_success for publish_result in publish_results
    )
    has_failure = any(
        not publish_result.is_success for publish_result in publish_results
    )

    return has_success and has_failure
