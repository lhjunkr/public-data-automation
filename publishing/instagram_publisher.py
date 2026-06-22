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


INSTAGRAM_CHANNEL_NAME = "instagram"
INSTAGRAM_GRAPH_API_BASE_URL = "https://graph.facebook.com/v25.0"
IG_USER_ID_ENV_NAME = "IG_USER_ID"
META_ACCESS_TOKEN_ENV_NAME = "META_ACCESS_TOKEN"
INSTAGRAM_REQUEST_TIMEOUT_SECONDS = 30


def publish_prepared_post_to_instagram(prepared_post: PreparedPost) -> PublishResult:
    instagram_user_id = get_required_environment_value(IG_USER_ID_ENV_NAME)
    meta_access_token = get_required_environment_value(META_ACCESS_TOKEN_ENV_NAME)

    media_container_payload = create_instagram_media_container(
        instagram_user_id=instagram_user_id,
        meta_access_token=meta_access_token,
        image_url=prepared_post.public_image_url,
        caption=prepared_post.post_content.caption,
    )

    if "error" in media_container_payload:
        return build_failed_publish_result(
            channel_name=INSTAGRAM_CHANNEL_NAME,
            error_message=extract_instagram_error_message(media_container_payload),
            raw_response=media_container_payload,
        )

    creation_id = extract_instagram_creation_id(media_container_payload)
    if not creation_id:
        return build_failed_publish_result(
            channel_name=INSTAGRAM_CHANNEL_NAME,
            error_message="Instagram media container creation did not return creation id.",
            raw_response=media_container_payload,
        )

    publish_payload = publish_instagram_media_container(
        instagram_user_id=instagram_user_id,
        meta_access_token=meta_access_token,
        creation_id=creation_id,
    )

    if "error" in publish_payload:
        return build_failed_publish_result(
            channel_name=INSTAGRAM_CHANNEL_NAME,
            error_message=extract_instagram_error_message(publish_payload),
            raw_response=publish_payload,
        )

    remote_post_id = extract_instagram_remote_post_id(publish_payload)

    return build_success_publish_result(
        channel_name=INSTAGRAM_CHANNEL_NAME,
        remote_post_id=remote_post_id,
        remote_url=None,
        raw_response=publish_payload,
    )


def create_instagram_media_container(
    *,
    instagram_user_id: str,
    meta_access_token: str,
    image_url: str,
    caption: str,
) -> dict[str, Any]:
    response = requests.post(
        f"{INSTAGRAM_GRAPH_API_BASE_URL}/{instagram_user_id}/media",
        data={
            "image_url": image_url,
            "caption": caption,
            "access_token": meta_access_token,
        },
        timeout=INSTAGRAM_REQUEST_TIMEOUT_SECONDS,
    )

    return parse_json_response(response)


def publish_instagram_media_container(
    *,
    instagram_user_id: str,
    meta_access_token: str,
    creation_id: str,
) -> dict[str, Any]:
    response = requests.post(
        f"{INSTAGRAM_GRAPH_API_BASE_URL}/{instagram_user_id}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": meta_access_token,
        },
        timeout=INSTAGRAM_REQUEST_TIMEOUT_SECONDS,
    )

    return parse_json_response(response)


def parse_json_response(response: requests.Response) -> dict[str, Any]:
    try:
        response_payload = response.json()
    except ValueError:
        return {
            "error": {
                "message": f"Instagram API returned non-JSON response with status {response.status_code}."
            }
        }

    if response.ok:
        return response_payload

    if "error" in response_payload:
        return response_payload

    return {
        "error": {
            "message": f"Instagram API request failed with status {response.status_code}."
        },
        "response": response_payload,
    }


def extract_instagram_creation_id(response_payload: dict[str, Any]) -> str | None:
    creation_id = response_payload.get("id")
    if isinstance(creation_id, str) and creation_id:
        return creation_id

    return None


def extract_instagram_remote_post_id(response_payload: dict[str, Any]) -> str | None:
    remote_post_id = response_payload.get("id")
    if isinstance(remote_post_id, str) and remote_post_id:
        return remote_post_id

    return None


def extract_instagram_error_message(response_payload: dict[str, Any]) -> str:
    error_payload = response_payload.get("error")
    if not isinstance(error_payload, dict):
        return "Instagram API request failed."

    error_message = error_payload.get("message")
    if isinstance(error_message, str) and error_message:
        return error_message

    return "Instagram API request failed."


def get_required_environment_value(environment_name: str) -> str:
    environment_value = os.getenv(environment_name)
    if environment_value:
        return environment_value

    raise RuntimeError(f"{environment_name} environment variable is required.")

