from __future__ import annotations

from typing import Any

import feedparser
import requests


DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS = 15
DEFAULT_RSS_REQUEST_MAX_ATTEMPTS = 2


def fetch_rss_feed_safely(
    *,
    feed_url: str,
    source_name: str,
    timeout_seconds: int = DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS,
    max_attempts: int = DEFAULT_RSS_REQUEST_MAX_ATTEMPTS,
) -> Any | None:
    for attempt_number in range(1, max_attempts + 1):
        try:
            response = requests.get(feed_url, timeout=timeout_seconds)
            response.raise_for_status()

            return feedparser.parse(response.content)
        except requests.RequestException as error:
            if attempt_number >= max_attempts:
                print(
                    f"RSS 수집 실패: {source_name} "
                    f"({feed_url}) - {error}"
                )
                return None

    return None
