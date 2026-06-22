from __future__ import annotations

import unittest
from unittest.mock import patch

import requests

from sources.kstartup_daegu_support import (
    KStartupDaeguSupportItem,
    fetch_kstartup_daegu_support_items,
    fetch_kstartup_endpoint_items,
)


class TestKStartupDaeguSupportFallback(unittest.TestCase):
    @patch("sources.kstartup_daegu_support.print")
    @patch("sources.kstartup_daegu_support.fetch_kstartup_endpoint_page")
    def test_fetch_kstartup_endpoint_items_returns_empty_list_on_first_page_failure(
        self,
        mock_fetch_kstartup_endpoint_page,
        mock_print,
    ) -> None:
        mock_fetch_kstartup_endpoint_page.side_effect = requests.exceptions.Timeout(
            "timeout"
        )

        raw_items = fetch_kstartup_endpoint_items(
            api_key="api-key",
            source_type="지원사업 공고",
            endpoint_path="/getAnnouncementInformation01",
        )

        self.assertEqual(raw_items, [])
        mock_print.assert_called_once()

    @patch("sources.kstartup_daegu_support.KSTARTUP_PER_PAGE", 1)
    @patch("sources.kstartup_daegu_support.print")
    @patch("sources.kstartup_daegu_support.fetch_kstartup_endpoint_page")
    def test_fetch_kstartup_endpoint_items_keeps_collected_items_after_later_failure(
        self,
        mock_fetch_kstartup_endpoint_page,
        mock_print,
    ) -> None:
        first_page_item = make_raw_kstartup_item(
            title="2026년 대구 창업기업 모집",
            source_url="https://example.com/startup-1",
        )
        mock_fetch_kstartup_endpoint_page.side_effect = [
            [first_page_item],
            requests.exceptions.ConnectTimeout("timeout"),
        ]

        raw_items = fetch_kstartup_endpoint_items(
            api_key="api-key",
            source_type="지원사업 공고",
            endpoint_path="/getAnnouncementInformation01",
        )

        self.assertEqual(raw_items, [first_page_item])
        self.assertEqual(mock_fetch_kstartup_endpoint_page.call_count, 2)
        mock_print.assert_called_once()

    @patch("sources.kstartup_daegu_support.print")
    @patch("sources.kstartup_daegu_support.get_kstartup_api_key")
    @patch("sources.kstartup_daegu_support.fetch_kstartup_endpoint_page")
    def test_fetch_kstartup_daegu_support_items_continues_after_endpoint_failure(
        self,
        mock_fetch_kstartup_endpoint_page,
        mock_get_kstartup_api_key,
        mock_print,
    ) -> None:
        mock_get_kstartup_api_key.return_value = "api-key"
        second_endpoint_item = make_raw_kstartup_item(
            title="대구 창업 생태계 보고서",
            source_url="https://example.com/startup-report",
        )
        mock_fetch_kstartup_endpoint_page.side_effect = [
            requests.exceptions.ReadTimeout("timeout"),
            [second_endpoint_item],
            [],
            [],
        ]

        support_items = fetch_kstartup_daegu_support_items()

        self.assertEqual(len(support_items), 1)
        self.assertIsInstance(support_items[0], KStartupDaeguSupportItem)
        self.assertEqual(support_items[0].title, "대구 창업 생태계 보고서")
        self.assertEqual(support_items[0].source_type, "창업관련 통계보고서")
        mock_print.assert_called_once()


def make_raw_kstartup_item(title: str, source_url: str) -> dict[str, str]:
    return {
        "biz_pbanc_nm": title,
        "detl_pg_url": source_url,
        "fstm_reg_dt": "20260622",
        "pbanc_rcpt_bgng_dt": "20260622",
        "pbanc_rcpt_end_dt": "20260701",
        "aply_trgt_ctnt": "대구 창업기업",
        "pbanc_ctnt": "대구 창업기업 지원 내용",
        "prch_cnpl_no": "053-000-0000",
    }


if __name__ == "__main__":
    unittest.main()
