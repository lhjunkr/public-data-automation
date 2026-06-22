from __future__ import annotations

import os
from typing import Any

import requests

from publishing.prepared_post import PreparedPost
from publishing.publish_result import (
    PublishResult,
    build_failed_publish_result,
    build_success_publish_result,
)


NAVER_BAND_CHANNEL_NAME = "naver_band"
NAVER_BAND_POST_CREATE_URL = "https://openapi.band.us/v2.2/band/post/create"
BAND_ACCESS_TOKEN_ENV_NAME = "BAND_ACCESS_TOKEN"
BAND_KEY_ENV_NAME = "BAND_KEY"
NAVER_BAND_REQUEST_TIMEOUT_SECONDS = 30


def publish_prepared_post_to_naver_band(prepared_post: PreparedPost) -> PublishResult:
    band_access_token = get_required_environment_value(BAND_ACCESS_TOKEN_ENV_NAME)
    band_key = get_required_environment_value(BAND_KEY_ENV_NAME)

    response_payload = create_naver_band_post(
        band_access_token=band_access_token,
        band_key=band_key,
        content=build_naver_band_content(prepared_post),
    )

    if has_naver_band_error(response_payload):
        return build_failed_publish_result(
            channel_name=NAVER_BAND_CHANNEL_NAME,
            error_message=extract_naver_band_error_message(response_payload),
            raw_response=response_payload,
        )

    remote_post_id = extract_naver_band_post_key(response_payload)

    return build_success_publish_result(
        channel_name=NAVER_BAND_CHANNEL_NAME,
        remote_post_id=remote_post_id,
        remote_url=None,
        raw_response=response_payload,
    )


def create_naver_band_post(
    *,
    band_access_token: str,
    band_key: str,
    content: str,
) -> dict[str, Any]:
    response = requests.post(
        NAVER_BAND_POST_CREATE_URL,
        data={
            "access_token": band_access_token,
            "band_key": band_key,
            "content": content,
            "do_push": "false",
        },
        timeout=NAVER_BAND_REQUEST_TIMEOUT_SECONDS,
    )

    return parse_json_response(response)


def build_naver_band_content(prepared_post: PreparedPost) -> str:
    post_content = prepared_post.post_content

    content_parts = [
        post_content.caption,
    ]

    if prepared_post.public_image_url:
        content_parts.extend(
            [
                "",
                "이미지:",
                prepared_post.public_image_url,
            ]
        )

    return "\n".join(content_parts).strip()


def parse_json_response(response: requests.Response) -> dict[str, Any]:
    try:
        response_payload = response.json()
    except ValueError:
        return {
            "result_code": -1,
            "message": f"Naver Band API returned non-JSON response with status {response.status_code}.",
        }

    if response.ok:
        return response_payload

    if isinstance(response_payload, dict):
        return response_payload

    return {
        "result_code": -1,
        "message": f"Naver Band API request failed with status {response.status_code}.",
    }


def has_naver_band_error(response_payload: dict[str, Any]) -> bool:
    result_code = response_payload.get("result_code")

    if result_code is None:
        return False

    return result_code != 1


def extract_naver_band_post_key(response_payload: dict[str, Any]) -> str | None:
    result_data = response_payload.get("result_data")

    if not isinstance(result_data, dict):
        return None

    post_key = result_data.get("post_key")

    if isinstance(post_key, str) and post_key:
        return post_key

    return None


def extract_naver_band_error_message(response_payload: dict[str, Any]) -> str:
    message = response_payload.get("message")

    if isinstance(message, str) and message:
        return message

    return "Naver Band API request failed."


def get_required_environment_value(environment_name: str) -> str:
    environment_value = os.getenv(environment_name)
    if environment_value:
        return environment_value

    raise RuntimeError(f"{environment_name} environment variable is required.")

