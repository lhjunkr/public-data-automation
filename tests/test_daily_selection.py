from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from pipeline.daily_selection import (
    collect_daegu_notice_based_candidates,
    collect_public_data_content_candidates,
    select_today_public_data_contents,
)
from selection.content_candidate import ContentCandidate
from sources.daegu_notice_rss import DaeguNotice


class TestDailySelection(unittest.TestCase):
    @patch("pipeline.daily_selection.filter_daegu_public_opportunity_notices")
    @patch("pipeline.daily_selection.filter_daegu_business_support_notices")
    @patch("pipeline.daily_selection.fetch_daegu_notices")
    def test_collect_daegu_notice_based_candidates_reuses_single_notice_fetch(
        self,
        mock_fetch_daegu_notices,
        mock_filter_business_support_notices,
        mock_filter_public_opportunity_notices,
    ) -> None:
        business_notice = make_daegu_notice(
            title="기업지원 공고",
            source_url="https://example.com/business",
        )
        public_opportunity_notice = make_daegu_notice(
            title="공모모집 공고",
            source_url="https://example.com/opportunity",
        )
        all_notices = [business_notice, public_opportunity_notice]

        mock_fetch_daegu_notices.return_value = all_notices
        mock_filter_business_support_notices.return_value = [business_notice]
        mock_filter_public_opportunity_notices.return_value = [public_opportunity_notice]

        candidates = collect_daegu_notice_based_candidates()

        self.assertEqual(len(candidates), 2)
        mock_fetch_daegu_notices.assert_called_once_with()
        mock_filter_business_support_notices.assert_called_once_with(all_notices)
        mock_filter_public_opportunity_notices.assert_called_once_with(all_notices)

    @patch("pipeline.daily_selection.select_daily_content_candidates")
    @patch("pipeline.daily_selection.collect_public_data_content_candidates")
    @patch("pipeline.daily_selection.load_posted_source_urls")
    @patch("pipeline.daily_selection.download_recent_posted_history_from_r2")
    def test_select_today_public_data_contents_syncs_history_and_selects_candidates(
        self,
        mock_download_recent_posted_history_from_r2,
        mock_load_posted_source_urls,
        mock_collect_public_data_content_candidates,
        mock_select_daily_content_candidates,
    ) -> None:
        candidate = make_content_candidate(
            title="선정 후보",
            source_url="https://example.com/selected",
        )
        selection_date = date(2026, 6, 21)

        mock_load_posted_source_urls.return_value = {"https://example.com/posted"}
        mock_collect_public_data_content_candidates.return_value = [candidate]
        mock_select_daily_content_candidates.return_value = [candidate]

        selected_candidates = select_today_public_data_contents(
            today=selection_date,
            sync_posted_history=True,
        )

        self.assertEqual(selected_candidates, [candidate])
        mock_download_recent_posted_history_from_r2.assert_called_once()
        mock_load_posted_source_urls.assert_called_once_with()
        mock_collect_public_data_content_candidates.assert_called_once_with()
        mock_select_daily_content_candidates.assert_called_once_with(
            candidates=[candidate],
            posted_source_urls={"https://example.com/posted"},
            today=selection_date,
        )

    @patch("pipeline.daily_selection.download_recent_posted_history_from_r2")
    @patch("pipeline.daily_selection.load_posted_source_urls")
    @patch("pipeline.daily_selection.collect_public_data_content_candidates")
    @patch("pipeline.daily_selection.select_daily_content_candidates")
    def test_select_today_public_data_contents_can_skip_history_sync(
        self,
        mock_select_daily_content_candidates,
        mock_collect_public_data_content_candidates,
        mock_load_posted_source_urls,
        mock_download_recent_posted_history_from_r2,
    ) -> None:
        candidate = make_content_candidate(
            title="로컬 확인 후보",
            source_url="https://example.com/local",
        )

        mock_load_posted_source_urls.return_value = set()
        mock_collect_public_data_content_candidates.return_value = [candidate]
        mock_select_daily_content_candidates.return_value = [candidate]

        selected_candidates = select_today_public_data_contents(
            today=date(2026, 6, 21),
            sync_posted_history=False,
        )

        self.assertEqual(selected_candidates, [candidate])
        mock_download_recent_posted_history_from_r2.assert_not_called()

    @patch("pipeline.daily_selection.print")
    @patch("pipeline.daily_selection.collect_daegu_notice_based_candidates")
    @patch("pipeline.daily_selection.collect_kstartup_daegu_support_candidates")
    @patch("pipeline.daily_selection.collect_daegu_public_recruitment_candidates")
    def test_collect_public_data_content_candidates_continues_after_source_failure(
        self,
        mock_collect_recruitment_candidates,
        mock_collect_kstartup_candidates,
        mock_collect_notice_based_candidates,
        mock_print,
    ) -> None:
        recruitment_candidate = make_content_candidate(
            title="채용 시험 후보",
            source_url="https://example.com/recruitment",
        )
        notice_candidate = make_content_candidate(
            title="공지사항 후보",
            source_url="https://example.com/notice",
        )

        mock_collect_recruitment_candidates.return_value = [recruitment_candidate]
        mock_collect_kstartup_candidates.side_effect = RuntimeError(
            "K-Startup API error"
        )
        mock_collect_notice_based_candidates.return_value = [notice_candidate]

        candidates = collect_public_data_content_candidates()

        self.assertEqual(candidates, [recruitment_candidate, notice_candidate])
        mock_print.assert_called_once_with(
            "공공정보 수집 실패: 대구 창업지원 K-Startup API - K-Startup API error"
        )


def make_daegu_notice(title: str, source_url: str) -> DaeguNotice:
    return DaeguNotice(
        title=title,
        source_name="대구시청 공지사항",
        source_url=source_url,
        published_at="Sun, 21 Jun 2026 10:41:11 GMT",
        summary="",
    )


def make_content_candidate(title: str, source_url: str) -> ContentCandidate:
    return ContentCandidate(
        category="대구 창업지원",
        title=title,
        source_name="테스트 출처",
        source_url=source_url,
        published_at="2026-06-21",
        deadline_at="2026-07-01",
        summary="",
        raw_payload=None,
    )


if __name__ == "__main__":
    unittest.main()
