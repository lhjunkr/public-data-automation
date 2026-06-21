from __future__ import annotations

import unittest
from datetime import date

from selection.content_candidate import ContentCandidate
from selection.content_selector import select_daily_content_candidates


class TestContentSelector(unittest.TestCase):
    def test_excludes_already_posted_source_url(self) -> None:
        candidates = [
            make_candidate(title="이미 게시한 공고", source_url="https://example.com/posted"),
            make_candidate(title="새 공고", source_url="https://example.com/new"),
        ]

        selected_candidates = select_daily_content_candidates(
            candidates=candidates,
            posted_source_urls={"https://example.com/posted"},
            today=date(2026, 6, 21),
        )

        selected_titles = [candidate.title for candidate in selected_candidates]

        self.assertEqual(selected_titles, ["새 공고"])

    def test_excludes_expired_candidate(self) -> None:
        candidates = [
            make_candidate(
                title="마감된 공고",
                source_url="https://example.com/expired",
                deadline_at="20260620",
            ),
            make_candidate(
                title="진행 중인 공고",
                source_url="https://example.com/open",
                deadline_at="20260622",
            ),
        ]

        selected_candidates = select_daily_content_candidates(
            candidates=candidates,
            posted_source_urls=set(),
            today=date(2026, 6, 21),
        )

        selected_titles = [candidate.title for candidate in selected_candidates]

        self.assertEqual(selected_titles, ["진행 중인 공고"])

    def test_selects_maximum_four_candidates_per_day(self) -> None:
        candidates = [
            make_candidate(
                category=f"카테고리 {candidate_number}",
                title=f"공고 {candidate_number}",
                source_url=f"https://example.com/{candidate_number}",
            )
            for candidate_number in range(1, 7)
        ]

        selected_candidates = select_daily_content_candidates(
            candidates=candidates,
            posted_source_urls=set(),
            today=date(2026, 6, 21),
        )

        self.assertEqual(len(selected_candidates), 4)

    def test_selects_one_candidate_per_category_first(self) -> None:
        candidates = [
            make_candidate(
                category="대구 창업지원",
                title="창업 최신 공고",
                source_url="https://example.com/startup-latest",
                published_at="2026-06-21",
            ),
            make_candidate(
                category="대구 창업지원",
                title="창업 이전 공고",
                source_url="https://example.com/startup-old",
                published_at="2026-06-20",
            ),
            make_candidate(
                category="대구 기업지원",
                title="기업 최신 공고",
                source_url="https://example.com/business-latest",
                published_at="2026-06-21",
            ),
            make_candidate(
                category="대구 공모·모집",
                title="공모 최신 공고",
                source_url="https://example.com/opportunity-latest",
                published_at="2026-06-21",
            ),
            make_candidate(
                category="대구 채용·시험",
                title="채용 최신 공고",
                source_url="https://example.com/recruitment-latest",
                published_at="2026-06-21",
            ),
        ]

        selected_candidates = select_daily_content_candidates(
            candidates=candidates,
            posted_source_urls=set(),
            today=date(2026, 6, 21),
        )

        selected_categories = [candidate.category for candidate in selected_candidates]

        self.assertEqual(
            selected_categories,
            ["대구 창업지원", "대구 기업지원", "대구 공모·모집", "대구 채용·시험"],
        )

    def test_fills_shortage_from_other_categories(self) -> None:
        candidates = [
            make_candidate(
                category="대구 창업지원",
                title="창업 최신 공고",
                source_url="https://example.com/startup-1",
                published_at="2026-06-21",
            ),
            make_candidate(
                category="대구 창업지원",
                title="창업 추가 공고",
                source_url="https://example.com/startup-2",
                published_at="2026-06-20",
            ),
            make_candidate(
                category="대구 기업지원",
                title="기업 최신 공고",
                source_url="https://example.com/business-1",
                published_at="2026-06-21",
            ),
        ]

        selected_candidates = select_daily_content_candidates(
            candidates=candidates,
            posted_source_urls=set(),
            today=date(2026, 6, 21),
        )

        selected_titles = [candidate.title for candidate in selected_candidates]

        self.assertEqual(
            selected_titles,
            ["창업 최신 공고", "기업 최신 공고", "창업 추가 공고"],
        )

    def test_does_not_select_more_than_two_candidates_per_category(self) -> None:
        candidates = [
            make_candidate(
                category="대구 창업지원",
                title=f"창업 공고 {candidate_number}",
                source_url=f"https://example.com/startup-{candidate_number}",
                published_at=f"2026-06-2{candidate_number}",
            )
            for candidate_number in range(1, 4)
        ]

        selected_candidates = select_daily_content_candidates(
            candidates=candidates,
            posted_source_urls=set(),
            today=date(2026, 6, 21),
        )

        self.assertEqual(len(selected_candidates), 2)
        self.assertTrue(
            all(candidate.category == "대구 창업지원" for candidate in selected_candidates)
        )

    def test_sorts_by_latest_published_at(self) -> None:
        candidates = [
            make_candidate(
                title="이전 공고",
                source_url="https://example.com/old",
                published_at="2026-06-20",
            ),
            make_candidate(
                title="최신 공고",
                source_url="https://example.com/latest",
                published_at="2026-06-21",
            ),
        ]

        selected_candidates = select_daily_content_candidates(
            candidates=candidates,
            posted_source_urls=set(),
            today=date(2026, 6, 21),
        )

        self.assertEqual(selected_candidates[0].title, "최신 공고")


def make_candidate(
    title: str,
    source_url: str,
    category: str = "대구 창업지원",
    published_at: str = "2026-06-21",
    deadline_at: str = "",
) -> ContentCandidate:
    return ContentCandidate(
        category=category,
        title=title,
        source_name="테스트 출처",
        source_url=source_url,
        published_at=published_at,
        deadline_at=deadline_at,
        summary="",
        raw_payload=None,
    )


if __name__ == "__main__":
    unittest.main()