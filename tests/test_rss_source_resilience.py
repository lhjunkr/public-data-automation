from __future__ import annotations

import os
import unittest
from unittest.mock import patch

import requests

from sources.daegu_notice_rss import fetch_daegu_notices
from sources.daegu_public_recruitment import (
    DaeguRecruitmentRssFeed,
    fetch_daegu_public_recruitment_notices,
)
from sources.rss_fetcher import build_rss_request


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
    @patch("sources.rss_fetcher.time.sleep")
    @patch("sources.rss_fetcher.requests.get")
    def test_fetch_daegu_public_recruitment_notices_continues_after_feed_timeout(
        self,
        mock_requests_get,
        mock_sleep,
        mock_print,
    ) -> None:
        mock_requests_get.side_effect = [
            requests.exceptions.ConnectTimeout("timeout 1"),
            requests.exceptions.ConnectTimeout("timeout 2"),
            requests.exceptions.ConnectTimeout("timeout 3"),
            requests.exceptions.ConnectTimeout("timeout 4"),
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
        self.assertEqual(mock_sleep.call_count, 3)

    @patch("sources.rss_fetcher.print")
    @patch("sources.rss_fetcher.time.sleep")
    @patch("sources.rss_fetcher.requests.get")
    def test_fetch_daegu_notices_returns_empty_list_when_notice_rss_fails(
        self,
        mock_requests_get,
        mock_sleep,
        mock_print,
    ) -> None:
        mock_requests_get.side_effect = requests.exceptions.ConnectTimeout("timeout")

        notices = fetch_daegu_notices()

        self.assertEqual(notices, [])
        self.assertEqual(mock_requests_get.call_count, 4)
        self.assertEqual(mock_sleep.call_count, 3)
        mock_print.assert_called_once()


class TestRssProxyRequest(unittest.TestCase):
    DAEGU_FEED_URL = "https://www.daegu.go.kr/icms/rss/feed.do?id=BBS_00029"

    @patch.dict(os.environ, {}, clear=True)
    def test_request_is_direct_when_proxy_not_configured(self) -> None:
        request_url, request_headers = build_rss_request(self.DAEGU_FEED_URL)

        self.assertEqual(request_url, self.DAEGU_FEED_URL)
        self.assertNotIn("X-Proxy-Token", request_headers)

    @patch.dict(
        os.environ,
        {
            "RSS_PROXY_BASE_URL": "https://daegu-rss-proxy.example.workers.dev",
            "RSS_PROXY_TOKEN": "secret-token",
        },
        clear=True,
    )
    def test_daegu_request_routes_through_proxy_with_token(self) -> None:
        request_url, request_headers = build_rss_request(self.DAEGU_FEED_URL)

        self.assertEqual(
            request_url,
            "https://daegu-rss-proxy.example.workers.dev/?url="
            "https%3A%2F%2Fwww.daegu.go.kr%2Ficms%2Frss%2Ffeed.do%3Fid%3DBBS_00029",
        )
        self.assertEqual(request_headers["X-Proxy-Token"], "secret-token")

    @patch.dict(
        os.environ,
        {"RSS_PROXY_BASE_URL": "https://daegu-rss-proxy.example.workers.dev"},
        clear=True,
    )
    def test_non_daegu_host_is_not_proxied(self) -> None:
        request_url, request_headers = build_rss_request(
            "https://apis.data.go.kr/some/feed"
        )

        self.assertEqual(request_url, "https://apis.data.go.kr/some/feed")
        self.assertNotIn("X-Proxy-Token", request_headers)


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
