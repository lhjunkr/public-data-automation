from __future__ import annotations

from dataclasses import dataclass

from sources.rss_fetcher import fetch_rss_feed_safely


DAEGU_RECRUITMENT_CATEGORY = "대구 채용·시험"
DAEGU_RECRUITMENT_SECTION = "공공"
DAEGU_RECRUITMENT_SOURCE_PREFIX = "대구광역시 시험정보"


@dataclass(frozen=True)
class DaeguRecruitmentRssFeed:
    source_name: str
    feed_url: str


@dataclass(frozen=True)
class DaeguPublicRecruitmentNotice:
    category: str
    section: str
    title: str
    source_name: str
    source_url: str
    published_at: str


DAEGU_PUBLIC_RECRUITMENT_RSS_FEEDS = [
    DaeguRecruitmentRssFeed(
        source_name=f"{DAEGU_RECRUITMENT_SOURCE_PREFIX} - 공채/경채 공무원",
        feed_url="https://www.daegu.go.kr/icms/rss/feed.do?id=BBS_02086",
    ),
    DaeguRecruitmentRssFeed(
        source_name=f"{DAEGU_RECRUITMENT_SOURCE_PREFIX} - 임기제/별정직 공무원",
        feed_url="https://www.daegu.go.kr/icms/rss/feed.do?id=BBS_02087",
    ),
    DaeguRecruitmentRssFeed(
        source_name=f"{DAEGU_RECRUITMENT_SOURCE_PREFIX} - 청원경찰",
        feed_url="https://www.daegu.go.kr/icms/rss/feed.do?id=BBS_02154",
    ),
    DaeguRecruitmentRssFeed(
        source_name=f"{DAEGU_RECRUITMENT_SOURCE_PREFIX} - 개방형직위",
        feed_url="https://www.daegu.go.kr/icms/rss/feed.do?id=BBS_02088",
    ),
    DaeguRecruitmentRssFeed(
        source_name=f"{DAEGU_RECRUITMENT_SOURCE_PREFIX} - 중앙 및 타기관 채용소식",
        feed_url="https://www.daegu.go.kr/icms/rss/feed.do?id=BBS_00064",
    ),
]


def parse_recruitment_rss_feed(feed_url: str):
    return fetch_rss_feed_safely(
        feed_url=feed_url,
        source_name="대구 채용·시험 공공 RSS",
    )


def fetch_daegu_public_recruitment_notices() -> list[DaeguPublicRecruitmentNotice]:
    notices: list[DaeguPublicRecruitmentNotice] = []
    seen_source_urls: set[str] = set()

    for rss_feed in DAEGU_PUBLIC_RECRUITMENT_RSS_FEEDS:
        parsed_feed = parse_recruitment_rss_feed(rss_feed.feed_url)
        if parsed_feed is None:
            continue

        for entry in parsed_feed.entries:
            title = str(getattr(entry, "title", "")).strip()
            source_url = str(getattr(entry, "link", "")).strip()
            published_at = str(getattr(entry, "published", "")).strip()

            if not title or not source_url:
                continue

            if source_url in seen_source_urls:
                continue

            notices.append(
                DaeguPublicRecruitmentNotice(
                    category=DAEGU_RECRUITMENT_CATEGORY,
                    section=DAEGU_RECRUITMENT_SECTION,
                    title=title,
                    source_name=rss_feed.source_name,
                    source_url=source_url,
                    published_at=published_at,
                )
            )

            seen_source_urls.add(source_url)

    return notices
