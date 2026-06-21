from __future__ import annotations

import unittest

from content.post_content_builder import (
    build_hashtags,
    build_post_content_from_candidate,
    format_hashtags,
)
from selection.content_candidate import ContentCandidate


class TestPostContentBuilder(unittest.TestCase):
    def test_build_post_content_from_candidate(self) -> None:
        candidate = make_candidate(
            category="대구 창업지원",
            title="2026년 대구 창업기업 모집",
            source_url="https://example.com/startup",
            deadline_at="20260707",
        )

        post_content = build_post_content_from_candidate(candidate)

        self.assertEqual(post_content.category, "대구 창업지원")
        self.assertEqual(post_content.title, "2026년 대구 창업기업 모집")
        self.assertEqual(post_content.source_url, "https://example.com/startup")
        self.assertIn("마감일: 20260707", post_content.caption)
        self.assertIn("#대구창업", post_content.caption)
        self.assertEqual(post_content.raw_candidate, candidate)

    def test_build_post_content_uses_published_at_when_deadline_is_empty(self) -> None:
        candidate = make_candidate(
            category="대구 채용·시험",
            title="2026년도 지방공무원 시험 공고",
            source_url="https://example.com/recruitment",
            published_at="Sun, 21 Jun 2026 10:41:04 GMT",
            deadline_at="",
        )

        post_content = build_post_content_from_candidate(candidate)

        self.assertIn(
            "게시일: Sun, 21 Jun 2026 10:41:04 GMT",
            post_content.caption,
        )
        self.assertIn("게시일: Sun, 21 Jun 2026 10:41:04 GMT", post_content.image_text_lines)

    def test_build_hashtags_combines_default_and_category_hashtags(self) -> None:
        hashtags = build_hashtags("대구 기업지원")

        self.assertEqual(
            hashtags,
            [
                "대구",
                "공공정보",
                "대구정보",
                "공공데이터",
                "대구기업지원",
                "중소기업지원",
                "소상공인",
            ],
        )

    def test_format_hashtags(self) -> None:
        self.assertEqual(
            format_hashtags(["대구", "공공정보"]),
            "#대구 #공공정보",
        )


def make_candidate(
    category: str,
    title: str,
    source_url: str,
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
        summary="테스트 요약",
        raw_payload=None,
    )


if __name__ == "__main__":
    unittest.main()