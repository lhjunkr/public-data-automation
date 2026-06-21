from __future__ import annotations

from sources.daegu_notice_classifier import (
    DAEGU_BUSINESS_SUPPORT_CATEGORY,
    DAEGU_PUBLIC_OPPORTUNITY_CATEGORY,
)
from sources.daegu_notice_rss import DaeguNotice
from sources.daegu_public_recruitment import DaeguPublicRecruitmentNotice
from sources.kstartup_daegu_support import KStartupDaeguSupportItem
from selection.content_candidate import ContentCandidate


DAEGU_RECRUITMENT_CATEGORY = "대구 채용·시험"
DAEGU_STARTUP_SUPPORT_CATEGORY = "대구 창업지원"


def recruitment_notice_to_candidate(
    notice: DaeguPublicRecruitmentNotice,
) -> ContentCandidate:
    return ContentCandidate(
        category=DAEGU_RECRUITMENT_CATEGORY,
        title=notice.title,
        source_name=notice.source_name,
        source_url=notice.source_url,
        published_at=notice.published_at,
        deadline_at="",
        summary="",
        raw_payload=notice,
    )


def kstartup_item_to_candidate(
    support_item: KStartupDaeguSupportItem,
) -> ContentCandidate:
    return ContentCandidate(
        category=DAEGU_STARTUP_SUPPORT_CATEGORY,
        title=support_item.title,
        source_name=support_item.source_name,
        source_url=support_item.source_url,
        published_at=support_item.published_at,
        deadline_at=extract_kstartup_deadline(support_item.application_period),
        summary=support_item.support_content,
        raw_payload=support_item,
    )


def business_notice_to_candidate(notice: DaeguNotice) -> ContentCandidate:
    return ContentCandidate(
        category=DAEGU_BUSINESS_SUPPORT_CATEGORY,
        title=notice.title,
        source_name=notice.source_name,
        source_url=notice.source_url,
        published_at=notice.published_at,
        deadline_at="",
        summary=notice.summary,
        raw_payload=notice,
    )


def public_opportunity_notice_to_candidate(notice: DaeguNotice) -> ContentCandidate:
    return ContentCandidate(
        category=DAEGU_PUBLIC_OPPORTUNITY_CATEGORY,
        title=notice.title,
        source_name=notice.source_name,
        source_url=notice.source_url,
        published_at=notice.published_at,
        deadline_at="",
        summary=notice.summary,
        raw_payload=notice,
    )


def extract_kstartup_deadline(application_period: str) -> str:
    if "~" not in application_period:
        return ""

    return application_period.rsplit("~", 1)[1].strip()