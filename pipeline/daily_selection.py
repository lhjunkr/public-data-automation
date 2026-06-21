from __future__ import annotations

from datetime import date

from selection.content_candidate import ContentCandidate
from selection.content_candidate_adapters import (
    business_notice_to_candidate,
    kstartup_item_to_candidate,
    public_opportunity_notice_to_candidate,
    recruitment_notice_to_candidate,
)
from selection.content_selector import select_daily_content_candidates
from sources.daegu_business_support import filter_daegu_business_support_notices
from sources.daegu_notice_rss import fetch_daegu_notices
from sources.daegu_public_opportunities import filter_daegu_public_opportunity_notices
from sources.daegu_public_recruitment import fetch_daegu_public_recruitment_notices
from sources.kstartup_daegu_support import fetch_kstartup_daegu_support_items
from storage.posted_history import (
    POSTED_HISTORY_RETENTION_DAYS,
    download_recent_posted_history_from_r2,
    load_posted_source_urls,
)


def select_today_public_data_contents(
    today: date | None = None,
    sync_posted_history: bool = True,
) -> list[ContentCandidate]:
    selection_date = today or date.today()

    if sync_posted_history:
        download_recent_posted_history_from_r2(
            today=selection_date,
            retention_days=POSTED_HISTORY_RETENTION_DAYS,
        )

    posted_source_urls = load_posted_source_urls()
    candidates = collect_public_data_content_candidates()

    return select_daily_content_candidates(
        candidates=candidates,
        posted_source_urls=posted_source_urls,
        today=selection_date,
    )


def collect_public_data_content_candidates() -> list[ContentCandidate]:
    candidates: list[ContentCandidate] = []

    candidates.extend(collect_daegu_public_recruitment_candidates())
    candidates.extend(collect_kstartup_daegu_support_candidates())
    candidates.extend(collect_daegu_notice_based_candidates())

    return candidates


def collect_daegu_public_recruitment_candidates() -> list[ContentCandidate]:
    recruitment_notices = fetch_daegu_public_recruitment_notices()

    return [
        recruitment_notice_to_candidate(recruitment_notice)
        for recruitment_notice in recruitment_notices
    ]


def collect_kstartup_daegu_support_candidates() -> list[ContentCandidate]:
    support_items = fetch_kstartup_daegu_support_items()

    return [
        kstartup_item_to_candidate(support_item)
        for support_item in support_items
    ]


def collect_daegu_notice_based_candidates() -> list[ContentCandidate]:
    daegu_notices = fetch_daegu_notices()

    business_support_notices = filter_daegu_business_support_notices(daegu_notices)
    public_opportunity_notices = filter_daegu_public_opportunity_notices(daegu_notices)

    business_support_candidates = [
        business_notice_to_candidate(business_support_notice)
        for business_support_notice in business_support_notices
    ]
    public_opportunity_candidates = [
        public_opportunity_notice_to_candidate(public_opportunity_notice)
        for public_opportunity_notice in public_opportunity_notices
    ]

    return business_support_candidates + public_opportunity_candidates


