from __future__ import annotations

import json
import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from content.gemini_content_generator import (
    build_enhanced_post_content,
    build_final_hashtags,
    enhance_post_content_with_gemini,
    get_gemini_model_candidates,
    parse_gemini_json_response,
    remove_markdown_code_fence,
    sanitize_generated_hashtag,
    validate_description_lines,
    validate_demand_prediction_lines,
    validate_image_text_lines,
    validate_recommended_target_lines,
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
                "recommended_targets": [
                    "대구 창업지원 공고를 찾는 예비창업자",
                    "원문 공고를 확인할 창업기업",
                ],
                "demand_prediction_lines": [
                    "마감일이 있어 관련 창업기업의 확인 수요가 있을 수 있습니다."
                ],
                "image_text_lines": ["AI 헤더", "AI 제목"],
                "hashtags": ["#대구", "창업지원", "사업공고", "예비창업"],
            },
        )

        self.assertIn("AI가 다듬은 설명입니다.", enhanced_post_content.caption)
        self.assertIn("신청 대상자는 원문 공고를 확인하세요.", enhanced_post_content.caption)
        self.assertIn("📌 [대구 창업지원]", enhanced_post_content.caption)
        self.assertIn("✅ 한눈에 보기", enhanced_post_content.caption)
        self.assertIn("• AI가 다듬은 설명입니다.", enhanced_post_content.caption)
        self.assertIn("🎯 추천 대상", enhanced_post_content.caption)
        self.assertIn("• 대구 창업지원 공고를 찾는 예비창업자", enhanced_post_content.caption)
        self.assertIn("📈 수요 예측", enhanced_post_content.caption)
        self.assertIn(
            "• 마감일이 있어 관련 창업기업의 확인 수요가 있을 수 있습니다.",
            enhanced_post_content.caption,
        )
        self.assertIn("🏛️ 출처: K-Startup", enhanced_post_content.caption)
        self.assertIn("🔗 원문 보기\nhttps://example.com/startup", enhanced_post_content.caption)
        self.assertEqual(enhanced_post_content.image_text_lines, ["AI 헤더", "AI 제목"])
        self.assertEqual(
            enhanced_post_content.hashtags,
            ["대구", "창업지원", "사업공고", "예비창업"],
        )
        self.assertEqual(enhanced_post_content.source_url, original_post_content.source_url)

    def test_build_enhanced_post_content_caps_description_to_max_lines(self) -> None:
        original_post_content = make_post_content()

        enhanced_post_content = build_enhanced_post_content(
            original_post_content=original_post_content,
            generated_payload={
                "description_lines": ["설명1", "설명2", "설명3", "설명4"],
                "image_text_lines": ["AI 헤더", "AI 제목"],
                "hashtags": ["대구", "창업지원", "사업공고", "예비창업"],
            },
        )

        self.assertIn("• 설명1", enhanced_post_content.caption)
        self.assertIn("• 설명3", enhanced_post_content.caption)
        self.assertNotIn("설명4", enhanced_post_content.caption)

    def test_build_enhanced_post_content_drops_risky_line_but_keeps_ai_hashtags(
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
                "hashtags": ["대구", "창업지원", "사업공고", "예비창업"],
            },
        )

        # 위험 키워드가 든 설명문은 제외되지만, 요약은 기본값으로 유지되고
        # AI 해시태그는 그대로 반영된다.
        self.assertNotIn("격차", enhanced_post_content.caption)
        self.assertIn("• 테스트 요약", enhanced_post_content.caption)
        self.assertEqual(
            enhanced_post_content.hashtags,
            ["대구", "창업지원", "사업공고", "예비창업"],
        )

    def test_build_enhanced_post_content_falls_back_to_default_when_payload_empty(
        self,
    ) -> None:
        original_post_content = make_post_content()

        enhanced_post_content = build_enhanced_post_content(
            original_post_content=original_post_content,
            generated_payload={
                "description_lines": [],
                "image_text_lines": [],
                "hashtags": [],
            },
        )

        # 보강할 내용이 없으면 요약은 기본값, 해시태그는 카테고리 기본값으로 채운다.
        self.assertIn("• 테스트 요약", enhanced_post_content.caption)
        self.assertNotIn("🎯 추천 대상", enhanced_post_content.caption)
        self.assertEqual(
            enhanced_post_content.image_text_lines,
            original_post_content.image_text_lines,
        )
        self.assertEqual(
            enhanced_post_content.hashtags,
            ["대구", "창업", "사업", "지원"],
        )

    def test_build_enhanced_post_content_includes_recommended_targets(self) -> None:
        original_post_content = make_post_content()

        enhanced_post_content = build_enhanced_post_content(
            original_post_content=original_post_content,
            generated_payload={
                "description_lines": ["AI 설명"],
                "recommended_targets": ["대구 창업지원 공고를 찾는 예비창업자"],
                "image_text_lines": ["AI 헤더", "AI 제목"],
                "hashtags": ["딥테크", "창업중심대학"],
            },
        )

        self.assertIn("🎯 추천 대상", enhanced_post_content.caption)
        self.assertIn(
            "• 대구 창업지원 공고를 찾는 예비창업자",
            enhanced_post_content.caption,
        )
        # AI 태그 2개를 우선 채택하고 부족분은 카테고리 기본 태그로 보충한다.
        self.assertEqual(
            enhanced_post_content.hashtags,
            ["딥테크", "창업중심대학", "대구", "창업"],
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
                "hashtags": ["대구", "창업지원", "사업공고", "예비창업"],
            },
        )

        self.assertEqual(
            enhanced_post_content.image_text_lines,
            original_post_content.image_text_lines,
        )

    def test_sanitize_generated_hashtag_strips_hash_and_spaces(self) -> None:
        self.assertEqual(sanitize_generated_hashtag("#대구 창업"), "대구창업")

    def test_sanitize_generated_hashtag_drops_special_characters(self) -> None:
        self.assertEqual(sanitize_generated_hashtag("K-Startup"), "KStartup")

    def test_sanitize_generated_hashtag_drops_too_long_tag(self) -> None:
        self.assertEqual(
            sanitize_generated_hashtag("지나치게긴해시태그테스트입니다"),
            "",
        )

    def test_build_final_hashtags_prefers_ai_and_fills_with_defaults(self) -> None:
        self.assertEqual(
            build_final_hashtags(
                ["딥테크", "창업중심대학", "지나치게긴해시태그테스트입니다"],
                "대구 창업지원",
            ),
            ["딥테크", "창업중심대학", "대구", "창업"],
        )

    def test_build_final_hashtags_dedupes_against_defaults(self) -> None:
        self.assertEqual(
            build_final_hashtags(["대구", "#대구", "창업"], "대구 창업지원"),
            ["대구", "창업", "사업", "지원"],
        )

    def test_build_final_hashtags_uses_defaults_when_no_valid_ai_tag(self) -> None:
        self.assertEqual(
            build_final_hashtags([], "대구 창업지원"),
            ["대구", "창업", "사업", "지원"],
        )

    def test_validate_description_lines_accepts_valid_lines(self) -> None:
        self.assertEqual(
            validate_description_lines(["창업기업 모집 공고입니다.", "원문 공고를 확인하세요."]),
            ["창업기업 모집 공고입니다.", "원문 공고를 확인하세요."],
        )

    def test_validate_description_lines_caps_to_max_lines(self) -> None:
        self.assertEqual(
            validate_description_lines(["1", "2", "3", "4"]),
            ["1", "2", "3"],
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

    def test_validate_recommended_target_lines_accepts_valid_lines(self) -> None:
        self.assertEqual(
            validate_recommended_target_lines(["창업지원 공고를 찾는 예비창업자"]),
            ["창업지원 공고를 찾는 예비창업자"],
        )

    def test_validate_recommended_target_lines_caps_to_max_lines(self) -> None:
        self.assertEqual(
            validate_recommended_target_lines(["1", "2", "3", "4"]),
            ["1", "2", "3"],
        )

    def test_validate_demand_prediction_lines_accepts_valid_lines(self) -> None:
        self.assertEqual(
            validate_demand_prediction_lines(
                ["마감일이 있어 관련 기업의 확인 수요가 있을 수 있습니다."]
            ),
            ["마감일이 있어 관련 기업의 확인 수요가 있을 수 있습니다."],
        )

    def test_validate_demand_prediction_lines_rejects_risky_expansion_keyword(
        self,
    ) -> None:
        self.assertEqual(
            validate_demand_prediction_lines(["지역 창업 생태계 강화 수요가 큽니다."]),
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

    @patch.dict(os.environ, {}, clear=True)
    def test_get_gemini_model_candidates_uses_primary_then_fallback(self) -> None:
        self.assertEqual(
            get_gemini_model_candidates(),
            ["gemini-3.5-flash", "gemini-2.5-flash"],
        )

    @patch.dict(
        os.environ,
        {"GEMINI_MODEL": "gemini-2.5-flash", "GEMINI_FALLBACK_MODEL": "gemini-2.5-flash"},
        clear=True,
    )
    def test_get_gemini_model_candidates_dedupes_identical_models(self) -> None:
        self.assertEqual(get_gemini_model_candidates(), ["gemini-2.5-flash"])

    @patch.dict(os.environ, {}, clear=True)
    @patch("content.gemini_content_generator.create_gemini_client")
    def test_enhance_falls_back_to_second_model_on_empty_response(
        self,
        mock_create_gemini_client,
    ) -> None:
        original_post_content = make_post_content()
        empty_response = SimpleNamespace(text="")
        valid_response = SimpleNamespace(
            text=json.dumps(
                {
                    "description_lines": ["폴백 모델이 만든 설명입니다."],
                    "image_text_lines": ["헤더", "제목"],
                    "hashtags": ["대구", "창업"],
                }
            )
        )
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = [empty_response, valid_response]
        mock_create_gemini_client.return_value = mock_client

        enhanced_post_content = enhance_post_content_with_gemini(original_post_content)

        # 프라이머리가 빈 응답을 줘도 폴백 모델 결과로 본문이 채워진다.
        self.assertIn("폴백 모델이 만든 설명입니다.", enhanced_post_content.caption)
        called_models = [
            call.kwargs["model"]
            for call in mock_client.models.generate_content.call_args_list
        ]
        self.assertEqual(called_models, ["gemini-3.5-flash", "gemini-2.5-flash"])


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
