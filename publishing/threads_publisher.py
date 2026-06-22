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


THREADS_CHANNEL_NAME = "threads"
THREADS_GRAPH_API_BASE_URL = "https://graph.threads.net/v1.0"
THREADS_USER_ID_ENV_NAME = "THREADS_USER_ID"
THREADS_ACCESS_TOKEN_ENV_NAME = "THREADS_ACCESS_TOKEN"
THREADS_REQUEST_TIMEOUT_SECONDS = 30


def publish_prepared_post_to_threads(prepared_post: PreparedPost) -> PublishResult:
    threads_user_id = get_required_environment_value(THREADS_USER_ID_ENV_NAME)
    threads_access_token = get_required_environment_value(
        THREADS_ACCESS_TOKEN_ENV_NAME
    )

    media_container_payload = create_threads_media_container(
        threads_user_id=threads_user_id,
        threads_access_token=threads_access_token,
        image_url=prepared_post.public_image_url,
        caption=prepared_post.post_content.caption,
    )

    if "error" in media_container_payload:
        return build_failed_publish_result(
            channel_name=THREADS_CHANNEL_NAME,
            error_message=extract_threads_error_message(media_container_payload),
            raw_response=media_container_payload,
        )

    creation_id = extract_threads_creation_id(media_container_payload)
    if not creation_id:
        return build_failed_publish_result(
            channel_name=THREADS_CHANNEL_NAME,
            error_message="Threads media container creation did not return creation id.",
            raw_response=media_container_payload,
        )

    publish_payload = publish_threads_media_container(
        threads_user_id=threads_user_id,
        threads_access_token=threads_access_token,
        creation_id=creation_id,
    )

    if "error" in publish_payload:
        return build_failed_publish_result(
            channel_name=THREADS_CHANNEL_NAME,
            error_message=extract_threads_error_message(publish_payload),
            raw_response=publish_payload,
        )

    remote_post_id = extract_threads_remote_post_id(publish_payload)
    if not remote_post_id:
        return build_failed_publish_result(
            channel_name=THREADS_CHANNEL_NAME,
            error_message="Threads media publish did not return post id.",
            raw_response=publish_payload,
        )

    return build_success_publish_result(
        channel_name=THREADS_CHANNEL_NAME,
        remote_post_id=remote_post_id,
        remote_url=build_threads_remote_url(remote_post_id),
        raw_response=publish_payload,
    )


def create_threads_media_container(
    *,
    threads_user_id: str,
    threads_access_token: str,
    image_url: str,
    caption: str,
) -> dict[str, Any]:
    response = requests.post(
        f"{THREADS_GRAPH_API_BASE_URL}/{threads_user_id}/threads",
        data={
            "media_type": "IMAGE",
            "image_url": image_url,
            "text": caption,
            "access_token": threads_access_token,
        },
        timeout=THREADS_REQUEST_TIMEOUT_SECONDS,
    )

    return parse_json_response(response)


def publish_threads_media_container(
    *,
    threads_user_id: str,
    threads_access_token: str,
    creation_id: str,
) -> dict[str, Any]:
    response = requests.post(
        f"{THREADS_GRAPH_API_BASE_URL}/{threads_user_id}/threads_publish",
        data={
            "creation_id": creation_id,
            "access_token": threads_access_token,
        },
        timeout=THREADS_REQUEST_TIMEOUT_SECONDS,
    )

    return parse_json_response(response)


def parse_json_response(response: requests.Response) -> dict[str, Any]:
    try:
        response_payload = response.json()
    except ValueError:
        return {
            "error": {
                "message": f"Threads API returned non-JSON response with status {response.status_code}."
            }
        }

    if response.ok:
        return response_payload

    if "error" in response_payload:
        return response_payload

    return {
        "error": {
            "message": f"Threads API request failed with status {response.status_code}."
        },
        "response": response_payload,
    }


def extract_threads_creation_id(response_payload: dict[str, Any]) -> str | None:
    creation_id = response_payload.get("id")
    if isinstance(creation_id, str) and creation_id:
        return creation_id

    return None


def extract_threads_remote_post_id(response_payload: dict[str, Any]) -> str | None:
    remote_post_id = response_payload.get("id")
    if isinstance(remote_post_id, str) and remote_post_id:
        return remote_post_id

    return None


def build_threads_remote_url(remote_post_id: str | None) -> str | None:
    if not remote_post_id:
        return None

    return f"https://www.threads.com/@todaydaegu/post/{remote_post_id}"


def extract_threads_error_message(response_payload: dict[str, Any]) -> str:
    error_payload = response_payload.get("error")
    if not isinstance(error_payload, dict):
        return "Threads API request failed."

    error_message = error_payload.get("message")
    if isinstance(error_message, str) and error_message:
        return error_message

    return "Threads API request failed."


def get_required_environment_value(environment_name: str) -> str:
    environment_value = os.getenv(environment_name)
    if environment_value:
        return environment_value

    raise RuntimeError(f"{environment_name} environment variable is required.")
