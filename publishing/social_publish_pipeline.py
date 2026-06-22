from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass

from publishing.facebook_publisher import publish_prepared_post_to_facebook
from publishing.instagram_publisher import publish_prepared_post_to_instagram
from publishing.naver_band_publisher import publish_prepared_post_to_naver_band
from publishing.prepared_post import PreparedPost
from publishing.publish_result import PublishResult, build_failed_publish_result
from publishing.threads_publisher import publish_prepared_post_to_threads


PublishFunction = Callable[[PreparedPost], PublishResult]


@dataclass(frozen=True)
class SocialPublisher:
    channel_name: str
    publish: PublishFunction
    enable_env_name: str | None = None


DEFAULT_SOCIAL_PUBLISHERS: tuple[SocialPublisher, ...] = (
    SocialPublisher(
        channel_name="facebook",
        publish=publish_prepared_post_to_facebook,
        enable_env_name="ENABLE_FACEBOOK_PUBLISH",
    ),
    SocialPublisher(
        channel_name="instagram",
        publish=publish_prepared_post_to_instagram,
        enable_env_name="ENABLE_INSTAGRAM_PUBLISH",
    ),
    SocialPublisher(
        channel_name="threads",
        publish=publish_prepared_post_to_threads,
        enable_env_name="ENABLE_THREADS_PUBLISH",
    ),
    SocialPublisher(
        channel_name="naver_band",
        publish=publish_prepared_post_to_naver_band,
        enable_env_name="ENABLE_NAVER_BAND_PUBLISH",
    ),
)


def publish_prepared_post_to_social_channels(
    prepared_post: PreparedPost,
    publishers: tuple[SocialPublisher, ...] = DEFAULT_SOCIAL_PUBLISHERS,
) -> list[PublishResult]:
    enabled_publishers = filter_enabled_publishers(publishers)
    publish_results: list[PublishResult] = []

    for publisher in enabled_publishers:
        publish_results.append(
            safely_publish_to_social_channel(
                prepared_post=prepared_post,
                publisher=publisher,
            )
        )

    return publish_results


def filter_enabled_publishers(
    publishers: tuple[SocialPublisher, ...],
) -> tuple[SocialPublisher, ...]:
    return tuple(
        publisher
        for publisher in publishers
        if is_publisher_enabled(publisher)
    )


def is_publisher_enabled(publisher: SocialPublisher) -> bool:
    if publisher.enable_env_name is None:
        return True

    environment_value = os.getenv(publisher.enable_env_name)

    if environment_value is None:
        return True

    return environment_value.strip().lower() == "true"


def safely_publish_to_social_channel(
    *,
    prepared_post: PreparedPost,
    publisher: SocialPublisher,
) -> PublishResult:
    try:
        return publisher.publish(prepared_post)
    except Exception as error:
        return build_failed_publish_result(
            channel_name=publisher.channel_name,
            error_message=str(error),
            raw_response=None,
        )
