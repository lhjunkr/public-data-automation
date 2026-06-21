from __future__ import annotations

from dataclasses import dataclass

import feedparser
import requests


DAEGU_NOTICE_SOURCE_NAME = "대구시청 공지사항"
DAEGU_NOTICE_RSS_URL = "http://www.daegu.go.kr/icms/rss/feed.do?id=BBS_00029"
REQUEST_TIMEOUT_SECONDS = 30


@dataclass(frozen=True)
class DaeguNotice:
    title: str
    source_name: str
    source_url: str
    published_at: str
    summary: str


def parse_daegu_notice_rss_feed():
    response = requests.get(DAEGU_NOTICE_RSS_URL, timeout=REQUEST_TIMEOUT_SECONDS)
    response.raise_for_status()

    return feedparser.parse(response.content)


def fetch_daegu_notices() -> list[DaeguNotice]:
    parsed_feed = parse_daegu_notice_rss_feed()

    notices: list[DaeguNotice] = []
    seen_source_urls: set[str] = set()

    for entry in parsed_feed.entries:
        title = str(getattr(entry, "title", "")).strip()
        source_url = str(getattr(entry, "link", "")).strip()
        published_at = str(getattr(entry, "published", "")).strip()
        summary = str(getattr(entry, "summary", "")).strip()

        if not title or not source_url:
            continue

        if source_url in seen_source_urls:
            continue

        notices.append(
            DaeguNotice(
                title=title,
                source_name=DAEGU_NOTICE_SOURCE_NAME,
                source_url=source_url,
                published_at=published_at,
                summary=summary,
            )
        )

        seen_source_urls.add(source_url)

    return notices
