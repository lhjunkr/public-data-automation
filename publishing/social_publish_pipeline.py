from __future__ import annotations

from collections.abc import Callable

from publishing.facebook_publisher import publish_prepared_post_to_facebook
from publishing.instagram_publisher import publish_prepared_post_to_instagram
from publishing.naver_band_publisher import publish_prepared_post_to_naver_band
from publishing.prepared_post import PreparedPost
from publishing.publish_result import PublishResult, build_failed_publish_result
from publishing.threads_publisher import publish_prepared_post_to_threads


PublishFunction = Callable[[PreparedPost], PublishResult]


DEFAULT_SOCIAL_PUBLISHERS: tuple[PublishFunction, ...] = (
    publish_prepared_post_to_facebook,
    publish_prepared_post_to_instagram,
    publish_prepared_post_to_threads,
    publish_prepared_post_to_naver_band,
)


def publish_prepared_post_to_social_channels(
    prepared_post: PreparedPost,
    publish_functions: tuple[PublishFunction, ...] = DEFAULT_SOCIAL_PUBLISHERS,
) -> list[PublishResult]:
    publish_results: list[PublishResult] = []

    for publish_function in publish_functions:
        publish_results.append(
            safely_publish_to_social_channel(
                prepared_post=prepared_post,
                publish_function=publish_function,
            )
        )

    return publish_results


def safely_publish_to_social_channel(
    *,
    prepared_post: PreparedPost,
    publish_function: PublishFunction,
) -> PublishResult:
    try:
        return publish_function(prepared_post)
    except Exception as error:
        return build_failed_publish_result(
            channel_name=extract_publish_function_channel_name(publish_function),
            error_message=str(error),
            raw_response=None,
        )


def extract_publish_function_channel_name(publish_function: PublishFunction) -> str:
    function_name = getattr(publish_function, "__name__", "")

    if "facebook" in function_name:
        return "facebook"

    if "instagram" in function_name:
        return "instagram"

    if "threads" in function_name:
        return "threads"

    if "naver_band" in function_name:
        return "naver_band"

    return "unknown"

