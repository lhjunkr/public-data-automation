from __future__ import annotations

from selection.content_candidate import ContentCandidate
from content.date_formatting import format_display_date
from content.post_content import PostContent


DEFAULT_HASHTAGS = [
    "대구",
    "공공정보",
    "대구정보",
    "공공데이터",
]


CATEGORY_HASHTAGS = {
    "대구 채용·시험": ["대구채용", "대구시험", "공무원채용"],
    "대구 공모·모집": ["대구공모전", "대구모집", "대구행사"],
    "대구 창업지원": ["대구창업", "창업지원", "KStartup"],
    "대구 기업지원": ["대구기업지원", "중소기업지원", "소상공인"],
}


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
    caption_lines = [
        f"[{candidate.category}]",
        candidate.title,
        "",
        build_period_line(candidate),
        f"출처: {candidate.source_name}",
        f"자세히 보기: {candidate.source_url}",
        "",
        format_hashtags(hashtags),
    ]

    return "\n".join(line for line in caption_lines if line.strip())


def build_period_line(candidate: ContentCandidate) -> str:
    if candidate.deadline_at:
        display_deadline = format_display_date(candidate.deadline_at)
        return f"마감일: {display_deadline}"

    if candidate.published_at:
        display_published_at = format_display_date(candidate.published_at)
        return f"게시일: {display_published_at}"

    return ""


def build_hashtags(category: str) -> list[str]:
    hashtags = [*DEFAULT_HASHTAGS]

    for category_hashtag in CATEGORY_HASHTAGS.get(category, []):
        if category_hashtag not in hashtags:
            hashtags.append(category_hashtag)

    return hashtags


def format_hashtags(hashtags: list[str]) -> str:
    return " ".join(f"#{hashtag}" for hashtag in hashtags)


def build_image_text_lines(candidate: ContentCandidate) -> list[str]:
    image_text_lines = [
        candidate.category,
        candidate.title,
    ]

    period_line = build_period_line(candidate)

    if period_line:
        image_text_lines.append(period_line)

    return image_text_lines