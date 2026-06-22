from __future__ import annotations

import unittest
from unittest.mock import patch

import requests

from sources.daegu_notice_rss import fetch_daegu_notices
from sources.daegu_public_recruitment import (
    DaeguRecruitmentRssFeed,
    fetch_daegu_public_recruitment_notices,
)


class TestRssSourceResilience(unittest.TestCase):
    @patch(
        "sources.daegu_public_recruitment.DAEGU_PUBLIC_RECRUITMENT_RSS_FEEDS",
        (
            DaeguRecruitmentRssFeed(
                source_name="실패 RSS",
                feed_url="https://example.com/fail.xml",
            ),
            DaeguRecruitmentRssFeed(
                source_name="성공 RSS",
                feed_url="https://example.com/success.xml",
            ),
        ),
    )
    @patch("sources.rss_fetcher.print")
    @patch("sources.rss_fetcher.requests.get")
    def test_fetch_daegu_public_recruitment_notices_continues_after_feed_timeout(
        self,
        mock_requests_get,
        mock_print,
    ) -> None:
        mock_requests_get.side_effect = [
            requests.exceptions.ConnectTimeout("timeout 1"),
            requests.exceptions.ConnectTimeout("timeout 2"),
            FakeResponse(
                content=build_rss_xml(
                    title="2026년도 대구광역시 공무원 시험 공고",
                    link="https://example.com/recruitment",
                    published_at="Mon, 22 Jun 2026 08:00:00 GMT",
                )
            ),
        ]

        notices = fetch_daegu_public_recruitment_notices()

        self.assertEqual(len(notices), 1)
        self.assertEqual(notices[0].source_name, "성공 RSS")
        self.assertEqual(notices[0].source_url, "https://example.com/recruitment")
        mock_print.assert_called_once()

    @patch("sources.rss_fetcher.print")
    @patch("sources.rss_fetcher.requests.get")
    def test_fetch_daegu_notices_returns_empty_list_when_notice_rss_fails(
        self,
        mock_requests_get,
        mock_print,
    ) -> None:
        mock_requests_get.side_effect = requests.exceptions.ConnectTimeout("timeout")

        notices = fetch_daegu_notices()

        self.assertEqual(notices, [])
        self.assertEqual(mock_requests_get.call_count, 2)
        mock_print.assert_called_once()


class FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content.encode("utf-8")

    def raise_for_status(self) -> None:
        return None


def build_rss_xml(title: str, link: str, published_at: str) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
  <channel>
    <title>테스트 RSS</title>
    <item>
      <title>{title}</title>
      <link>{link}</link>
      <pubDate>{published_at}</pubDate>
    </item>
  </channel>
</rss>
"""


if __name__ == "__main__":
    unittest.main()
