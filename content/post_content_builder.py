from __future__ import annotations

import re

from selection.content_candidate import ContentCandidate
from content.date_formatting import format_display_date
from content.post_content import PostContent


CATEGORY_HASHTAGS = {
    "대구 채용·시험": ["대구", "취업", "취준", "시험"],
    "대구 공모·모집": ["대구", "공모전", "모집", "정보"],
    "대구 창업지원": ["대구", "창업", "사업", "지원"],
    "대구 기업지원": ["대구", "기업", "사업", "지원"],
}
DEFAULT_HASHTAGS = ["대구", "공공정보", "대구정보", "공공데이터"]
HASHTAG_COUNT = 4
CAPTION_SUMMARY_HEADING = "✅ 한눈에 보기"
CAPTION_BULLET_PREFIX = "• "
MAX_CAPTION_SUMMARY_LINES = 4


def build_post_content_from_candidate(candidate: ContentCandidate) -> PostContent:
    hashtags = build_hashtags(candidate.category)

    return PostContent(
        category=candidate.category,
        title=candidate.title,
        source_name=candidate.source_name,
        source_url=candidate.source_url,
        published_at=candidate.published_at,
        deadline_at=candidate.deadline_at,
        summary=candidate.summary,
        caption=build_default_caption(candidate, hashtags),
        hashtags=hashtags,
        image_text_lines=build_image_text_lines(candidate),
        raw_candidate=candidate,
    )


def build_post_contents_from_candidates(
    candidates: list[ContentCandidate],
) -> list[PostContent]:
    return [
        build_post_content_from_candidate(candidate)
        for candidate in candidates
    ]


def build_default_caption(
    candidate: ContentCandidate,
    hashtags: list[str],
) -> str:
    return build_caption(
        category=candidate.category,
        title=candidate.title,
        summary_lines=build_caption_summary_lines(candidate.summary),
        period_line=build_period_line(candidate),
        source_name=candidate.source_name,
        source_url=candidate.source_url,
        hashtags=hashtags,
    )


def build_caption(
    *,
    category: str,
    title: str,
    summary_lines: list[str],
    period_line: str,
    source_name: str,
    source_url: str,
    hashtags: list[str],
) -> str:
    caption_lines = [
        f"📌 [{category}]",
        title,
        "",
        *build_caption_summary_section(summary_lines),
        "",
        period_line,
        f"🏛️ 출처: {source_name}",
        "🔗 원문 보기",
        source_url,
        "",
        format_hashtags(hashtags),
    ]

    return join_caption_lines(caption_lines)


def build_period_line(candidate: ContentCandidate) -> str:
    if candidate.deadline_at:
        display_deadline = format_display_date(candidate.deadline_at)
        return f"⏰ 마감일: {display_deadline}"

    if candidate.published_at:
        display_published_at = format_display_date(candidate.published_at)
        return f"🗓️ 게시일: {display_published_at}"

    return ""


def build_image_period_line(candidate: ContentCandidate) -> str:
    if candidate.deadline_at:
        display_deadline = format_display_date(candidate.deadline_at)
        return f"마감일: {display_deadline}"

    if candidate.published_at:
        display_published_at = format_display_date(candidate.published_at)
        return f"게시일: {display_published_at}"

    return ""


def build_caption_summary_section(summary_lines: list[str]) -> list[str]:
    if not summary_lines:
        return []

    return [
        CAPTION_SUMMARY_HEADING,
        *[f"{CAPTION_BULLET_PREFIX}{summary_line}" for summary_line in summary_lines],
    ]


def build_caption_summary_lines(summary: str) -> list[str]:
    normalized_lines: list[str] = []

    for raw_summary_line in summary.splitlines():
        summary_line = normalize_caption_summary_line(raw_summary_line)

        if not summary_line:
            continue

        normalized_lines.append(summary_line)

        if len(normalized_lines) >= MAX_CAPTION_SUMMARY_LINES:
            break

    return normalized_lines


def normalize_caption_summary_line(raw_summary_line: str) -> str:
    summary_line = raw_summary_line.strip()
    summary_line = re.sub(r"^[\-•]\s*", "", summary_line)
    summary_line = re.sub(r"\s+", " ", summary_line)
    summary_line = re.sub(r"(?<!\d)\s*:\s*(?!\d)", ": ", summary_line)
    summary_line = re.sub(r"\s+", " ", summary_line).strip()

    if not summary_line:
        return ""

    if re.fullmatch(r"[^:：]{1,20}[:：]", summary_line):
        return ""

    return summary_line


def join_caption_lines(caption_lines: list[str]) -> str:
    joined_lines: list[str] = []
    previous_line_was_blank = False

    for caption_line in caption_lines:
        normalized_line = caption_line.strip()

        if not normalized_line:
            if joined_lines and not previous_line_was_blank:
                joined_lines.append("")

            previous_line_was_blank = True
            continue

        joined_lines.append(normalized_line)
        previous_line_was_blank = False

    while joined_lines and not joined_lines[-1]:
        joined_lines.pop()

    return "\n".join(joined_lines)


def build_hashtags(category: str) -> list[str]:
    return CATEGORY_HASHTAGS.get(category, DEFAULT_HASHTAGS)[:HASHTAG_COUNT]


def format_hashtags(hashtags: list[str]) -> str:
    return " ".join(f"#{hashtag}" for hashtag in hashtags)


def build_image_text_lines(candidate: ContentCandidate) -> list[str]:
    image_text_lines = [
        candidate.category,
        candidate.title,
    ]

    period_line = build_image_period_line(candidate)

    if period_line:
        image_text_lines.append(period_line)

    return image_text_lines
