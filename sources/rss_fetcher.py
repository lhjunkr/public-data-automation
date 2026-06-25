from __future__ import annotations

import os
import time
from typing import Any
from urllib.parse import quote, urlsplit

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

# 해외 IP를 차단하는 호스트는 한국 IP에서 나가는 프록시(Cloudflare Worker)를
# 경유해 받아온다. 프록시 환경변수가 없으면 기존처럼 직접 요청한다.
RSS_PROXY_BASE_URL_ENV_NAME = "RSS_PROXY_BASE_URL"
RSS_PROXY_TOKEN_ENV_NAME = "RSS_PROXY_TOKEN"
RSS_PROXY_TOKEN_HEADER_NAME = "X-Proxy-Token"
RSS_PROXIED_HOSTS = ("www.daegu.go.kr",)


def fetch_rss_feed_safely(
    *,
    feed_url: str,
    source_name: str,
    timeout_seconds: int | tuple[int, int] = DEFAULT_RSS_REQUEST_TIMEOUT_SECONDS,
    max_attempts: int = DEFAULT_RSS_REQUEST_MAX_ATTEMPTS,
    retry_sleep_seconds: int = DEFAULT_RSS_RETRY_SLEEP_SECONDS,
) -> Any | None:
    request_url, request_headers = build_rss_request(feed_url)

    for attempt_number in range(1, max_attempts + 1):
        try:
            response = requests.get(
                request_url,
                headers=request_headers,
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


def build_rss_request(feed_url: str) -> tuple[str, dict[str, str]]:
    request_headers = dict(RSS_REQUEST_HEADERS)
    proxy_base_url = os.getenv(RSS_PROXY_BASE_URL_ENV_NAME, "").strip()

    if not proxy_base_url or not is_proxied_rss_host(feed_url):
        return feed_url, request_headers

    proxy_token = os.getenv(RSS_PROXY_TOKEN_ENV_NAME, "").strip()

    if proxy_token:
        request_headers[RSS_PROXY_TOKEN_HEADER_NAME] = proxy_token

    request_url = f"{proxy_base_url.rstrip('/')}/?url={quote(feed_url, safe='')}"

    return request_url, request_headers


def is_proxied_rss_host(feed_url: str) -> bool:
    return urlsplit(feed_url).hostname in RSS_PROXIED_HOSTS


def sleep_before_next_attempt(
    *,
    attempt_number: int,
    retry_sleep_seconds: int,
) -> None:
    if retry_sleep_seconds <= 0:
        return

    time.sleep(retry_sleep_seconds * attempt_number)
