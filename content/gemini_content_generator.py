from __future__ import annotations

import json
import os
import re
from typing import Any

from google import genai
from google.genai import types

from content.date_formatting import format_display_date
from content.post_content import PostContent
from content.post_content_builder import (
    build_caption,
    build_caption_summary_lines,
    build_hashtags,
)


GEMINI_API_KEY_ENV_NAME = "GEMINI_API_KEY"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"

MAX_DESCRIPTION_LINES = 3
MAX_DESCRIPTION_LINE_LENGTH = 90
MAX_RECOMMENDED_TARGET_LINES = 3
MAX_RECOMMENDED_TARGET_LINE_LENGTH = 80
MAX_DEMAND_PREDICTION_LINES = 2
MAX_DEMAND_PREDICTION_LINE_LENGTH = 90
MAX_IMAGE_TEXT_LINES = 4
MAX_IMAGE_TEXT_LINE_LENGTH = 28
GENERATED_HASHTAG_COUNT = 4
MAX_GENERATED_HASHTAG_LENGTH = 12
DESCRIPTION_RISKY_EXPANSION_KEYWORDS = [
    "수도권",
    "비수도권",
    "양극화",
    "생태계 강화",
    "격차",
]


def enhance_post_contents_with_gemini(
    post_contents: list[PostContent],
) -> list[PostContent]:
    return [
        enhance_post_content_with_gemini(post_content)
        for post_content in post_contents
    ]


def enhance_post_content_with_gemini(post_content: PostContent) -> PostContent:
    try:
        client = create_gemini_client()
        prompt = build_gemini_prompt(post_content)
        response = client.models.generate_content(
            model=get_gemini_model_name(),
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        generated_payload = parse_gemini_json_response(response.text or "")

        return build_enhanced_post_content(
            original_post_content=post_content,
            generated_payload=generated_payload,
        )
    except Exception as error:
        print(f"Gemini 콘텐츠 생성 실패, 기본 게시 문구를 사용합니다: {error}")
        return post_content


def create_gemini_client() -> genai.Client:
    api_key = os.getenv(GEMINI_API_KEY_ENV_NAME, "").strip()

    if not api_key:
        raise RuntimeError(f"{GEMINI_API_KEY_ENV_NAME} GitHub Actions Secret이 필요합니다.")

    return genai.Client(api_key=api_key)


def get_gemini_model_name() -> str:
    return os.getenv("GEMINI_MODEL", DEFAULT_GEMINI_MODEL).strip() or DEFAULT_GEMINI_MODEL


def build_gemini_prompt(post_content: PostContent) -> str:
    return f"""
당신은 대구 시민에게 공공정보를 쉽고 정확하게 전달하는 SNS 콘텐츠 에디터입니다.

목표:
- 과장하지 않습니다.
- 원문에 없는 혜택, 조건, 날짜, 지역, 기관명을 만들어내지 않습니다.
- 입력 정보에서 확인 가능한 내용만 사용합니다.
- 확실하지 않은 내용은 쓰지 않습니다.
- 시민이 바로 이해할 수 있게 간결하게 씁니다.
- description_lines에는 출처, 링크, 해시태그를 넣지 않습니다. 시스템이 별도로 붙입니다.
- description_lines는 2~3문장만 작성합니다.
- description_lines는 제목과 입력 요약을 쉬운 말로 풀어쓰는 용도로만 사용합니다.
- description_lines에 입력 정보보다 구체적인 사업 목적, 대상 지역, 지원 내용, 혜택을 추가하지 않습니다.
- recommended_targets에는 이 정보를 확인하면 좋을 대상을 1~3개 작성합니다.
- recommended_targets는 원문에서 확인되는 대상만 쓰고, 확실하지 않으면 "관심 있는 시민은 원문 공고를 확인하세요."라고 씁니다.
- demand_prediction_lines에는 수요 예측을 1~2문장 작성합니다.
- demand_prediction_lines는 정량 예측, 경쟁률, 신청 규모를 만들어내지 않습니다.
- demand_prediction_lines는 카테고리, 마감일, 정보 성격을 바탕으로 보수적으로 작성합니다.
- 대상자가 명확하지 않으면 "관심 있는 시민은 원문 공고를 확인하세요."라고 씁니다.
- 제목에 없는 지역명은 쓰지 않습니다.
- 입력 요약에 없는 정책 목적이나 지원 내용을 쓰지 않습니다.
- image_text_lines는 최대 4줄입니다.
- image_text_lines 각 줄은 28자 이내로 작성합니다.
- 카드뉴스 문구는 한 줄당 짧고 명확하게 씁니다.
- image_text_lines에는 사업 목적이나 배경 설명을 넣지 않습니다.
- image_text_lines에는 이모지나 특수 아이콘을 넣지 않습니다.
- 알 수 없는 내용은 "원문 공고 확인"처럼 짧게 씁니다.
- hashtags는 게시물 텍스트에 맞는 4개를 정확히 작성합니다.
- hashtags에는 # 기호를 붙이지 않습니다.
- hashtags에는 공백, 특수문자, 중복을 넣지 않습니다.
- hashtags는 너무 넓은 태그만 반복하지 말고 제목과 카테고리에 맞게 작성합니다.
- 대구 관련 정보이므로 가능하면 "대구"를 포함합니다.

입력 정보:
카테고리: {post_content.category}
제목: {post_content.title}
출처: {post_content.source_name}
게시일: {post_content.published_at}
마감일: {post_content.deadline_at}
요약: {post_content.summary}
원본 URL: {post_content.source_url}

반드시 아래 JSON 형식만 응답하세요.
마크다운 코드블록은 쓰지 마세요.

{{
  "description_lines": [
    "이 정보가 무엇인지 설명하는 문장",
    "누가 보면 좋은 정보인지 설명하는 문장"
  ],
  "recommended_targets": [
    "추천 대상"
  ],
  "demand_prediction_lines": [
    "수요 예측 문장"
  ],
  "image_text_lines": [
    "카테고리",
    "짧은 제목",
    "마감일 또는 게시일",
    "원문 공고 확인"
  ],
  "hashtags": ["대구", "창업", "지원사업", "공고"]
}}
""".strip()


def parse_gemini_json_response(response_text: str) -> dict[str, Any]:
    cleaned_response_text = response_text.strip()

    if cleaned_response_text.startswith("```"):
        cleaned_response_text = remove_markdown_code_fence(cleaned_response_text)

    parsed_payload = json.loads(cleaned_response_text)

    if not isinstance(parsed_payload, dict):
        raise ValueError("Gemini 응답이 JSON 객체가 아닙니다.")

    return parsed_payload


def remove_markdown_code_fence(response_text: str) -> str:
    lines = response_text.splitlines()

    if lines and lines[0].startswith("```"):
        lines = lines[1:]

    if lines and lines[-1].startswith("```"):
        lines = lines[:-1]

    return "\n".join(lines).strip()


def build_enhanced_post_content(
    original_post_content: PostContent,
    generated_payload: dict[str, Any],
) -> PostContent:
    description_lines = validate_description_lines(
        clean_generated_text_list(generated_payload.get("description_lines"))
    )
    recommended_target_lines = validate_recommended_target_lines(
        clean_generated_text_list(generated_payload.get("recommended_targets"))
    )
    demand_prediction_lines = validate_demand_prediction_lines(
        clean_generated_text_list(generated_payload.get("demand_prediction_lines"))
    )
    image_text_lines = validate_image_text_lines(
        clean_generated_text_list(generated_payload.get("image_text_lines"))
    )
    hashtags = build_final_hashtags(
        clean_generated_text_list(generated_payload.get("hashtags")),
        original_post_content.category,
    )

    # 설명문이 모두 검증에서 제외되어도 본문에 요약은 항상 남기고, 추천 대상과
    # AI 해시태그는 Gemini가 만들어 준 만큼 그대로 반영한다.
    summary_lines = description_lines or build_caption_summary_lines(
        original_post_content.summary
    )

    enhanced_caption = build_caption(
        category=original_post_content.category,
        title=original_post_content.title,
        summary_lines=summary_lines,
        recommended_target_lines=recommended_target_lines,
        demand_prediction_lines=demand_prediction_lines,
        period_line=build_period_line_from_post_content(original_post_content),
        source_name=original_post_content.source_name,
        source_url=original_post_content.source_url,
        hashtags=hashtags,
    )

    return PostContent(
        category=original_post_content.category,
        title=original_post_content.title,
        source_name=original_post_content.source_name,
        source_url=original_post_content.source_url,
        published_at=original_post_content.published_at,
        deadline_at=original_post_content.deadline_at,
        summary=original_post_content.summary,
        caption=enhanced_caption,
        hashtags=hashtags,
        image_text_lines=image_text_lines
        or original_post_content.image_text_lines,
        raw_candidate=original_post_content.raw_candidate,
    )


def build_period_line_from_post_content(post_content: PostContent) -> str:
    if post_content.deadline_at:
        return f"⏰ 마감일: {format_display_date(post_content.deadline_at)}"

    if post_content.published_at:
        return f"🗓️ 게시일: {format_display_date(post_content.published_at)}"

    return ""


def validate_description_lines(description_lines: list[str]) -> list[str]:
    return validate_bounded_text_lines(
        text_lines=description_lines,
        max_line_count=MAX_DESCRIPTION_LINES,
        max_line_length=MAX_DESCRIPTION_LINE_LENGTH,
        reject_risky_expansion=True,
    )


def validate_recommended_target_lines(recommended_target_lines: list[str]) -> list[str]:
    return validate_bounded_text_lines(
        text_lines=recommended_target_lines,
        max_line_count=MAX_RECOMMENDED_TARGET_LINES,
        max_line_length=MAX_RECOMMENDED_TARGET_LINE_LENGTH,
        reject_risky_expansion=True,
    )


def validate_demand_prediction_lines(demand_prediction_lines: list[str]) -> list[str]:
    return validate_bounded_text_lines(
        text_lines=demand_prediction_lines,
        max_line_count=MAX_DEMAND_PREDICTION_LINES,
        max_line_length=MAX_DEMAND_PREDICTION_LINE_LENGTH,
        reject_risky_expansion=True,
    )


def validate_bounded_text_lines(
    *,
    text_lines: list[str],
    max_line_count: int,
    max_line_length: int,
    reject_risky_expansion: bool,
) -> list[str]:
    valid_text_lines: list[str] = []

    for text_line in text_lines:
        if len(text_line) > max_line_length:
            continue

        if reject_risky_expansion and has_risky_expansion_keyword(text_line):
            continue

        valid_text_lines.append(text_line)

        if len(valid_text_lines) >= max_line_count:
            break

    return valid_text_lines


def has_risky_expansion_keyword(text: str) -> bool:
    return any(
        risky_keyword in text
        for risky_keyword in DESCRIPTION_RISKY_EXPANSION_KEYWORDS
    )


def validate_image_text_lines(image_text_lines: list[str]) -> list[str]:
    if not image_text_lines:
        return []

    if len(image_text_lines) > MAX_IMAGE_TEXT_LINES:
        return []

    for image_text_line in image_text_lines:
        if len(image_text_line) > MAX_IMAGE_TEXT_LINE_LENGTH:
            return []

    return image_text_lines


def build_final_hashtags(
    generated_hashtags: list[str],
    category: str,
) -> list[str]:
    final_hashtags: list[str] = []

    for generated_hashtag in generated_hashtags:
        sanitized_hashtag = sanitize_generated_hashtag(generated_hashtag)

        if sanitized_hashtag and sanitized_hashtag not in final_hashtags:
            final_hashtags.append(sanitized_hashtag)

        if len(final_hashtags) >= GENERATED_HASHTAG_COUNT:
            break

    for fallback_hashtag in build_hashtags(category):
        if len(final_hashtags) >= GENERATED_HASHTAG_COUNT:
            break

        if fallback_hashtag not in final_hashtags:
            final_hashtags.append(fallback_hashtag)

    return final_hashtags[:GENERATED_HASHTAG_COUNT]


def sanitize_generated_hashtag(hashtag: str) -> str:
    cleaned_hashtag = re.sub(r"\s+", "", hashtag.strip().lstrip("#"))
    cleaned_hashtag = "".join(
        character for character in cleaned_hashtag if character.isalnum()
    )

    if not cleaned_hashtag or len(cleaned_hashtag) > MAX_GENERATED_HASHTAG_LENGTH:
        return ""

    return cleaned_hashtag


def clean_generated_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    cleaned_values: list[str] = []

    for item in value:
        if not isinstance(item, str):
            continue

        cleaned_item = item.strip()

        if cleaned_item:
            cleaned_values.append(cleaned_item)

    return cleaned_values
