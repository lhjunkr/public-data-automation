from __future__ import annotations

import unittest
from unittest.mock import patch

from content.gemini_content_generator import (
    build_enhanced_post_content,
    clean_generated_hashtags,
    enhance_post_content_with_gemini,
    parse_gemini_json_response,
    remove_markdown_code_fence,
    validate_description_lines,
    validate_image_text_lines,
)
from content.post_content import PostContent


class TestGeminiContentGenerator(unittest.TestCase):
    def test_parse_gemini_json_response(self) -> None:
        parsed_payload = parse_gemini_json_response(
            '{"description_lines": ["본문"], "image_text_lines": ["줄1"], "hashtags": ["대구"]}'
        )

        self.assertEqual(parsed_payload["description_lines"], ["본문"])
        self.assertEqual(parsed_payload["image_text_lines"], ["줄1"])
        self.assertEqual(parsed_payload["hashtags"], ["대구"])

    def test_parse_gemini_json_response_removes_markdown_code_fence(self) -> None:
        parsed_payload = parse_gemini_json_response(
            """```json
{"description_lines": ["본문"], "image_text_lines": ["줄1"], "hashtags": ["#대구"]}
```"""
        )

        self.assertEqual(parsed_payload["description_lines"], ["본문"])
        self.assertEqual(parsed_payload["hashtags"], ["#대구"])

    def test_remove_markdown_code_fence(self) -> None:
        cleaned_text = remove_markdown_code_fence(
            """```json
{"description_lines": ["본문"]}
```"""
        )

        self.assertEqual(cleaned_text, '{"description_lines": ["본문"]}')

    def test_build_enhanced_post_content(self) -> None:
        original_post_content = make_post_content()

        enhanced_post_content = build_enhanced_post_content(
            original_post_content=original_post_content,
            generated_payload={
                "description_lines": [
                    "AI가 다듬은 설명입니다.",
                    "신청 대상자는 원문 공고를 확인하세요.",
                ],
                "image_text_lines": ["AI 헤더", "AI 제목"],
                "hashtags": ["#대구", "공공정보"],
            },
        )

        self.assertIn("AI가 다듬은 설명입니다.", enhanced_post_content.caption)
        self.assertIn("신청 대상자는 원문 공고를 확인하세요.", enhanced_post_content.caption)
        self.assertIn("📌 [대구 창업지원]", enhanced_post_content.caption)
        self.assertIn("✅ 핵심 내용", enhanced_post_content.caption)
        self.assertIn("🏛️ 출처: K-Startup", enhanced_post_content.caption)
        self.assertIn("🔗 자세히 보기\nhttps://example.com/startup", enhanced_post_content.caption)
        self.assertEqual(enhanced_post_content.image_text_lines, ["AI 헤더", "AI 제목"])
        self.assertEqual(
            enhanced_post_content.hashtags,
            ["대구", "창업", "사업", "지원"],
        )
        self.assertEqual(enhanced_post_content.source_url, original_post_content.source_url)

    def test_build_enhanced_post_content_limits_description_lines(self) -> None:
        original_post_content = make_post_content()

        enhanced_post_content = build_enhanced_post_content(
            original_post_content=original_post_content,
            generated_payload={
                "description_lines": ["설명1", "설명2", "설명3", "설명4"],
                "image_text_lines": ["AI 헤더", "AI 제목"],
                "hashtags": ["대구"],
            },
        )

        self.assertEqual(enhanced_post_content.caption, original_post_content.caption)

    def test_build_enhanced_post_content_falls_back_when_description_is_risky(
        self,
    ) -> None:
        original_post_content = make_post_content()

        enhanced_post_content = build_enhanced_post_content(
            original_post_content=original_post_content,
            generated_payload={
                "description_lines": [
                    "수도권과 비수도권의 창업 격차를 줄이는 공고입니다."
                ],
                "image_text_lines": ["AI 헤더", "AI 제목"],
                "hashtags": ["대구"],
            },
        )

        self.assertEqual(enhanced_post_content.caption, original_post_content.caption)

    def test_build_enhanced_post_content_falls_back_to_original_values(self) -> None:
        original_post_content = make_post_content()

        enhanced_post_content = build_enhanced_post_content(
            original_post_content=original_post_content,
            generated_payload={
                "description_lines": [],
                "image_text_lines": [],
                "hashtags": [],
            },
        )

        self.assertEqual(enhanced_post_content.caption, original_post_content.caption)
        self.assertEqual(
            enhanced_post_content.image_text_lines,
            original_post_content.image_text_lines,
        )
        self.assertEqual(
            enhanced_post_content.hashtags,
            ["대구", "창업", "사업", "지원"],
        )

    def test_build_enhanced_post_content_falls_back_when_image_text_is_invalid(
        self,
    ) -> None:
        original_post_content = make_post_content()

        enhanced_post_content = build_enhanced_post_content(
            original_post_content=original_post_content,
            generated_payload={
                "description_lines": ["AI 설명"],
                "image_text_lines": [
                    "대구 창업지원",
                    "이 문장은 이미지 카드에 넣기에는 너무 길어서 제외되어야 합니다",
                ],
                "hashtags": ["대구"],
            },
        )

        self.assertEqual(
            enhanced_post_content.image_text_lines,
            original_post_content.image_text_lines,
        )

    def test_clean_generated_hashtags_removes_hash_prefix_and_duplicates(self) -> None:
        self.assertEqual(
            clean_generated_hashtags(["#대구", "대구", "#공공정보", "", 123]),
            ["대구", "공공정보"],
        )

    def test_clean_generated_hashtags_keeps_unique_values(self) -> None:
        self.assertEqual(
            clean_generated_hashtags(
                [
                    "태그1",
                    "태그2",
                    "태그3",
                    "태그4",
                    "태그5",
                    "태그6",
                    "태그7",
                    "태그8",
                    "태그9",
                ]
            ),
            [
                "태그1",
                "태그2",
                "태그3",
                "태그4",
                "태그5",
                "태그6",
                "태그7",
                "태그8",
                "태그9",
            ],
        )

    def test_validate_description_lines_accepts_valid_lines(self) -> None:
        self.assertEqual(
            validate_description_lines(["창업기업 모집 공고입니다.", "원문 공고를 확인하세요."]),
            ["창업기업 모집 공고입니다.", "원문 공고를 확인하세요."],
        )

    def test_validate_description_lines_rejects_too_many_lines(self) -> None:
        self.assertEqual(
            validate_description_lines(["1", "2", "3", "4"]),
            [],
        )

    def test_validate_description_lines_rejects_too_long_line(self) -> None:
        self.assertEqual(
            validate_description_lines(
                [
                    "이 설명문은 게시물 본문에 넣기에는 지나치게 길어서 자동화 품질을 해칠 수 있으므로 제외되어야 하는 테스트 문장입니다. 원문에 없는 세부 내용을 덧붙일 위험도 있습니다."
                ]
            ),
            [],
        )

    def test_validate_description_lines_rejects_risky_expansion_keyword(self) -> None:
        self.assertEqual(
            validate_description_lines(["지역 창업 생태계 강화를 위한 공고입니다."]),
            [],
        )

    def test_validate_image_text_lines_accepts_valid_lines(self) -> None:
        self.assertEqual(
            validate_image_text_lines(["대구 창업지원", "창업기업 모집", "마감일 2026.07.07"]),
            ["대구 창업지원", "창업기업 모집", "마감일 2026.07.07"],
        )

    def test_validate_image_text_lines_rejects_too_many_lines(self) -> None:
        self.assertEqual(
            validate_image_text_lines(["1", "2", "3", "4", "5"]),
            [],
        )

    def test_validate_image_text_lines_rejects_too_long_line(self) -> None:
        self.assertEqual(
            validate_image_text_lines(
                ["대구 창업지원", "이 문장은 이미지 카드에 넣기에는 너무 길어서 제외되어야 합니다"]
            ),
            [],
        )

    @patch("content.gemini_content_generator.create_gemini_client")
    def test_enhance_post_content_with_gemini_returns_original_on_failure(
        self,
        mock_create_gemini_client,
    ) -> None:
        original_post_content = make_post_content()
        mock_create_gemini_client.side_effect = RuntimeError("API error")

        enhanced_post_content = enhance_post_content_with_gemini(original_post_content)

        self.assertEqual(enhanced_post_content, original_post_content)


def make_post_content() -> PostContent:
    return PostContent(
        category="대구 창업지원",
        title="2026년 대구 창업기업 모집",
        source_name="K-Startup",
        source_url="https://example.com/startup",
        published_at="2026.06.21",
        deadline_at="2026.07.07",
        summary="테스트 요약",
        caption="기본 본문",
        hashtags=["대구", "공공정보"],
        image_text_lines=["대구 창업지원", "2026년 대구 창업기업 모집"],
        raw_candidate=None,
    )


if __name__ == "__main__":
    unittest.main()
