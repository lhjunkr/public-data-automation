from __future__ import annotations

import time
from typing import Any

import feedparser
import requests


DEFAULT_RSS_CONNECT_TIMEOUT_SECONDS = 20
DEFAULT_RSS_READ_TIMEOUT_SECONDS = 30
DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS = (
    DEFAULT_RSS_CONNECT_TIMEOUT_SECONDS,
    DEFAULT_RSS_READ_TIMEOUT_SECONDS,
)
DEFAULT_RSS_REQUEST_MAX_ATTEMPTS = 4
DEFAULT_RSS_RETRY_SLEEP_SECONDS = 2
RSS_REQUEST_HEADERS = {
    "User-Agent": "public-data-automation/1.0 (+https://github.com/lhjunkr/public-data-automation)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}


def fetch_rss_feed_safely(
    *,
    feed_url: str,
    source_name: str,
    timeout_seconds: int | tuple[int, int] = DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS,
    max_attempts: int = DEFAULT_RSS_REQUEST_MAX_ATTEMPTS,
    retry_sleep_seconds: int = DEFAULT_RSS_RETRY_SLEEP_SECONDS,
) -> Any | None:
    for attempt_number in range(1, max_attempts + 1):
        try:
            response = requests.get(
                feed_url,
                headers=RSS_REQUEST_HEADERS,
                timeout=timeout_seconds,
            )
            response.raise_for_status()

            return feedparser.parse(response.content)
        except requests.RequestException as error:
            if attempt_number >= max_attempts:
                print(
                    f"RSS 수집 실패: {source_name} "
                    f"({feed_url}) - {error}"
                )
                return None

            sleep_before_next_attempt(
                attempt_number=attempt_number,
                retry_sleep_seconds=retry_sleep_seconds,
            )

    return None


def sleep_before_next_attempt(
    *,
    attempt_number: int,
    retry_sleep_seconds: int,
) -> None:
    if retry_sleep_seconds <= 0:
        return

    time.sleep(retry_sleep_seconds * attempt_number)
