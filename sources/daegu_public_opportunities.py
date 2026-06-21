from __future__ import annotations

from sources.daegu_notice_classifier import (
    DAEGU_PUBLIC_OPPORTUNITY_CATEGORY,
    classify_daegu_notice,
)
from sources.daegu_notice_rss import DaeguNotice, fetch_daegu_notices


def filter_daegu_public_opportunity_notices(
    notices: list[DaeguNotice],
) -> list[DaeguNotice]:
    return [
        notice
        for notice in notices
        if classify_daegu_notice(notice) == DAEGU_PUBLIC_OPPORTUNITY_CATEGORY
    ]


def fetch_daegu_public_opportunity_notices() -> list[DaeguNotice]:
    notices = fetch_daegu_notices()
    return filter_daegu_public_opportunity_notices(notices)