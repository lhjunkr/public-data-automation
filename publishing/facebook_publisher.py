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


FACEBOOK_CHANNEL_NAME = "facebook"
FACEBOOK_GRAPH_API_BASE_URL = "https://graph.facebook.com/v25.0"
FACEBOOK_PAGE_ID_ENV_NAME = "FACEBOOK_PAGE_ID"
FACEBOOK_PAGE_ACCESS_TOKEN_ENV_NAME = "FACEBOOK_PAGE_ACCESS_TOKEN"
FACEBOOK_REQUEST_TIMEOUT_SECONDS = 30


def publish_prepared_post_to_facebook(prepared_post: PreparedPost) -> PublishResult:
    page_id = get_required_environment_value(FACEBOOK_PAGE_ID_ENV_NAME)
    page_access_token = get_required_environment_value(
        FACEBOOK_PAGE_ACCESS_TOKEN_ENV_NAME
    )

    response_payload = create_facebook_photo_post(
        page_id=page_id,
        page_access_token=page_access_token,
        image_url=prepared_post.public_image_url,
        caption=prepared_post.post_content.caption,
    )

    if "error" in response_payload:
        return build_failed_publish_result(
            channel_name=FACEBOOK_CHANNEL_NAME,
            error_message=extract_facebook_error_message(response_payload),
            raw_response=response_payload,
        )

    remote_post_id = extract_facebook_remote_post_id(response_payload)
    if not remote_post_id:
        return build_failed_publish_result(
            channel_name=FACEBOOK_CHANNEL_NAME,
            error_message="Facebook photo post did not return post id.",
            raw_response=response_payload,
        )

    return build_success_publish_result(
        channel_name=FACEBOOK_CHANNEL_NAME,
        remote_post_id=remote_post_id,
        remote_url=build_facebook_remote_url(remote_post_id),
        raw_response=response_payload,
    )


def create_facebook_photo_post(
    *,
    page_id: str,
    page_access_token: str,
    image_url: str,
    caption: str,
) -> dict[str, Any]:
    response = requests.post(
        f"{FACEBOOK_GRAPH_API_BASE_URL}/{page_id}/photos",
        data={
            "url": image_url,
            "caption": caption,
            "published": "true",
            "access_token": page_access_token,
        },
        timeout=FACEBOOK_REQUEST_TIMEOUT_SECONDS,
    )

    return parse_json_response(response)


def parse_json_response(response: requests.Response) -> dict[str, Any]:
    try:
        response_payload = response.json()
    except ValueError:
        return {
            "error": {
                "message": f"Facebook API returned non-JSON response with status {response.status_code}."
            }
        }

    if response.ok:
        return response_payload

    if "error" in response_payload:
        return response_payload

    return {
        "error": {
            "message": f"Facebook API request failed with status {response.status_code}."
        },
        "response": response_payload,
    }


def extract_facebook_remote_post_id(response_payload: dict[str, Any]) -> str | None:
    post_id = response_payload.get("post_id")
    if isinstance(post_id, str) and post_id:
        return post_id

    photo_id = response_payload.get("id")
    if isinstance(photo_id, str) and photo_id:
        return photo_id

    return None


def build_facebook_remote_url(remote_post_id: str | None) -> str | None:
    if not remote_post_id:
        return None

    return f"https://www.facebook.com/{remote_post_id}"


def extract_facebook_error_message(response_payload: dict[str, Any]) -> str:
    error_payload = response_payload.get("error")
    if not isinstance(error_payload, dict):
        return "Facebook API request failed."

    error_message = error_payload.get("message")
    if isinstance(error_message, str) and error_message:
        return error_message

    return "Facebook API request failed."


def get_required_environment_value(environment_name: str) -> str:
    environment_value = os.getenv(environment_name)
    if environment_value:
        return environment_value

    raise RuntimeError(f"{environment_name} environment variable is required.")
