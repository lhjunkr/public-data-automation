from __future__ import annotations

from collections import Counter
from datetime import date, datetime
from email.utils import parsedate_to_datetime

from selection.content_candidate import ContentCandidate


DAILY_CONTENT_LIMIT = 4
CATEGORY_BASE_LIMIT = 1
CATEGORY_FILL_LIMIT = 2


def select_daily_content_candidates(
    candidates: list[ContentCandidate],
    posted_source_urls: set[str],
    today: date | None = None,
) -> list[ContentCandidate]:
    selection_date = today or date.today()

    eligible_candidates = filter_eligible_candidates(
        candidates=candidates,
        posted_source_urls=posted_source_urls,
        today=selection_date,
    )
    latest_candidates = sort_candidates_by_latest_upload(eligible_candidates)

    selected_candidates = select_one_per_category(latest_candidates)
    selected_candidates = fill_remaining_slots(
        candidates=latest_candidates,
        selected_candidates=selected_candidates,
    )

    return selected_candidates[:DAILY_CONTENT_LIMIT]


def filter_eligible_candidates(
    candidates: list[ContentCandidate],
    posted_source_urls: set[str],
    today: date,
) -> list[ContentCandidate]:
    eligible_candidates: list[ContentCandidate] = []

    for candidate in candidates:
        if candidate.source_url in posted_source_urls:
            continue

        if is_expired_candidate(candidate, today):
            continue

        eligible_candidates.append(candidate)

    return eligible_candidates


def is_expired_candidate(candidate: ContentCandidate, today: date) -> bool:
    deadline_date = parse_date(candidate.deadline_at)

    if deadline_date is None:
        return False

    return deadline_date < today


def sort_candidates_by_latest_upload(
    candidates: list[ContentCandidate],
) -> list[ContentCandidate]:
    return sorted(
        candidates,
        key=lambda candidate: parse_date(candidate.published_at) or date.min,
        reverse=True,
    )


def select_one_per_category(
    candidates: list[ContentCandidate],
) -> list[ContentCandidate]:
    selected_candidates: list[ContentCandidate] = []
    selected_categories: set[str] = set()

    for candidate in candidates:
        if len(selected_candidates) >= DAILY_CONTENT_LIMIT:
            break

        if candidate.category in selected_categories:
            continue

        selected_candidates.append(candidate)
        selected_categories.add(candidate.category)

    return selected_candidates


def fill_remaining_slots(
    candidates: list[ContentCandidate],
    selected_candidates: list[ContentCandidate],
) -> list[ContentCandidate]:
    selected_source_urls = {
        selected_candidate.source_url for selected_candidate in selected_candidates
    }
    selected_category_counts = Counter(
        selected_candidate.category for selected_candidate in selected_candidates
    )

    for candidate in candidates:
        if len(selected_candidates) >= DAILY_CONTENT_LIMIT:
            break

        if candidate.source_url in selected_source_urls:
            continue

        if selected_category_counts[candidate.category] >= CATEGORY_FILL_LIMIT:
            continue

        selected_candidates.append(candidate)
        selected_source_urls.add(candidate.source_url)
        selected_category_counts[candidate.category] += 1

    return selected_candidates


def parse_date(raw_date: str) -> date | None:
    normalized_date = raw_date.strip()

    if not normalized_date:
        return None

    for date_format in ("%Y%m%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(normalized_date, date_format).date()
        except ValueError:
            pass

    try:
        return parsedate_to_datetime(normalized_date).date()
    except (TypeError, ValueError):
        return None