from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PublishResult:
    channel_name: str
    is_success: bool
    remote_post_id: str | None
    remote_url: str | None
    error_message: str | None
    raw_response: dict[str, Any] | None


def build_success_publish_result(
    *,
    channel_name: str,
    remote_post_id: str | None,
    remote_url: str | None,
    raw_response: dict[str, Any] | None,
) -> PublishResult:
    return PublishResult(
        channel_name=channel_name,
        is_success=True,
        remote_post_id=remote_post_id,
        remote_url=remote_url,
        error_message=None,
        raw_response=raw_response,
    )


def build_failed_publish_result(
    *,
    channel_name: str,
    error_message: str,
    raw_response: dict[str, Any] | None = None,
) -> PublishResult:
    return PublishResult(
        channel_name=channel_name,
        is_success=False,
        remote_post_id=None,
        remote_url=None,
        error_message=error_message,
        raw_response=raw_response,
    )
    
    