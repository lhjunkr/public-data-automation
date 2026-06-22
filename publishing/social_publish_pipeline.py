from __future__ import annotations

import os
from collections.abc import Callable

from publishing.facebook_publisher import publish_prepared_post_to_facebook
from publishing.instagram_publisher import publish_prepared_post_to_instagram
from publishing.naver_band_publisher import publish_prepared_post_to_naver_band
from publishing.prepared_post import PreparedPost
from publishing.publish_result import PublishResult, build_failed_publish_result
from publishing.threads_publisher import publish_prepared_post_to_threads


PublishFunction = Callable[[PreparedPost], PublishResult]

CHANNEL_ENABLE_ENV_NAMES = {
    "facebook": "ENABLE_FACEBOOK_PUBLISH",
    "instagram": "ENABLE_INSTAGRAM_PUBLISH",
    "threads": "ENABLE_THREADS_PUBLISH",
    "naver_band": "ENABLE_NAVER_BAND_PUBLISH",
}

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
    enabled_publish_functions = filter_enabled_publish_functions(publish_functions)
    publish_results: list[PublishResult] = []

    for publish_function in enabled_publish_functions:
        publish_results.append(
            safely_publish_to_social_channel(
                prepared_post=prepared_post,
                publish_function=publish_function,
            )
        )

    return publish_results

def filter_enabled_publish_functions(
    publish_functions: tuple[PublishFunction, ...],
) -> tuple[PublishFunction, ...]:
    return tuple(
        publish_function
        for publish_function in publish_functions
        if is_publish_function_enabled(publish_function)
    )


def is_publish_function_enabled(publish_function: PublishFunction) -> bool:
    channel_name = extract_publish_function_channel_name(publish_function)
    environment_name = CHANNEL_ENABLE_ENV_NAMES.get(channel_name)

    if environment_name is None:
        return True

    environment_value = os.getenv(environment_name)

    if environment_value is None:
        return True

    return environment_value.strip().lower() == "true"

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

