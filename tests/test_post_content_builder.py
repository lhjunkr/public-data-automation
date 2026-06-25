from __future__ import annotations

import unittest

from content.post_content_builder import (
    build_caption,
    build_hashtags,
    build_post_content_from_candidate,
    build_caption_summary_lines,
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
        self.assertIn("📌 [대구 창업지원]", post_content.caption)
        self.assertIn("✅ 한눈에 보기", post_content.caption)
        self.assertIn("• 테스트 요약", post_content.caption)
        self.assertIn("\n\n✅ 한눈에 보기\n", post_content.caption)
        self.assertIn("\n\n⏰ 마감일: 2026.07.07", post_content.caption)
        self.assertIn("⏰ 마감일: 2026.07.07", post_content.caption)
        self.assertIn("🏛️ 출처: 테스트 출처", post_content.caption)
        self.assertIn("🔗 원문 보기\nhttps://example.com/startup", post_content.caption)
        self.assertIn("#대구 #창업 #사업 #지원", post_content.caption)
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
            "🗓️ 게시일: 2026.06.21",
            post_content.caption,
        )
        self.assertIn("게시일: 2026.06.21", post_content.image_text_lines)

    def test_build_caption_summary_lines_formats_multiline_notice_summary(self) -> None:
        summary_lines = build_caption_summary_lines(
            "\n".join(
                [
                    "2026년 임산부 친환경농산물 지원사업 신청을 다음과 같이 알려드립니다.",
                    "",
                    "- 지원대상 : 2025년 1월 1일 이후 출산한 산모 또는 사업신청일 기준 임신부",
                    "- 지원내용 : 임산부 1인당 연 24만원(자부담 4만8천원 포함) 친환경농산물 꾸러미 지원",
                    "- 신청기간 : 2026. 7.1.(수) 10:00 ~ 7.14(화) 18:00",
                    "- 신청방법 :",
                ]
            )
        )

        self.assertEqual(
            summary_lines,
            [
                "2026년 임산부 친환경농산물 지원사업 신청을 다음과 같이 알려드립니다.",
                "지원대상: 2025년 1월 1일 이후 출산한 산모 또는 사업신청일 기준 임신부",
                "지원내용: 임산부 1인당 연 24만원(자부담 4만8천원 포함) 친환경농산물 꾸러미 지원",
                "신청기간: 2026. 7.1.(수) 10:00 ~ 7.14(화) 18:00",
            ],
        )

    def test_build_caption_includes_ai_recommended_targets_and_demand_prediction(
        self,
    ) -> None:
        caption = build_caption(
            category="대구 창업지원",
            title="2026년 대구 창업기업 모집",
            summary_lines=["창업기업 모집 공고입니다."],
            recommended_target_lines=["대구 창업지원 공고를 찾는 예비창업자"],
            demand_prediction_lines=["마감일이 있어 확인 수요가 있을 수 있습니다."],
            period_line="⏰ 마감일: 2026.07.07",
            source_name="K-Startup",
            source_url="https://example.com/startup",
            hashtags=["대구", "창업지원", "사업공고", "예비창업"],
        )

        self.assertIn("✅ 한눈에 보기", caption)
        self.assertIn("🎯 추천 대상", caption)
        self.assertIn("• 대구 창업지원 공고를 찾는 예비창업자", caption)
        self.assertIn("📈 수요 예측", caption)
        self.assertIn("• 마감일이 있어 확인 수요가 있을 수 있습니다.", caption)
        self.assertIn("#대구 #창업지원 #사업공고 #예비창업", caption)

    def test_build_hashtags_combines_default_and_category_hashtags(self) -> None:
        hashtags = build_hashtags("대구 기업지원")

        self.assertEqual(
            hashtags,
            [
                "대구",
                "기업",
                "사업",
                "지원",
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
