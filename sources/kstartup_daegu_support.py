from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import requests


KSTARTUP_API_KEY_ENV_NAME = "KSTARTUP_API_KEY"
KSTARTUP_CATEGORY = "대구 창업지원"
KSTARTUP_SOURCE_NAME = "창업진흥원 K-Startup"

KSTARTUP_API_BASE_URL = "https://apis.data.go.kr/B552735/kisedKstartupService01"
KSTARTUP_PER_PAGE = 100
KSTARTUP_MAX_PAGES = 10
REQUEST_TIMEOUT_SECONDS = 30
KSTARTUP_FALLBACK_EXCEPTIONS = (
    requests.RequestException,
    ValueError,
    RuntimeError,
)

KSTARTUP_ENDPOINTS = [
    {
        "source_type": "지원사업 공고",
        "path": "/getAnnouncementInformation01",
    },
    {
        "source_type": "창업관련 통계보고서",
        "path": "/getStatisticalInformation01",
    },
    {
        "source_type": "창업관련 콘텐츠",
        "path": "/getContentInformation01",
    },
    {
        "source_type": "통합공고 지원사업",
        "path": "/getBusinessInformation01",
    },
]

DAEGU_RELEVANCE_KEYWORDS = [
    "대구",
    "대구광역시",
    "대구시",
    "대구창조경제혁신센터",
    "대구테크노파크",
    "대구디지털혁신진흥원",
    "DIP",
    "대구경북",
    "경북대학교",
]

# 주제 관련성을 판별하는 의미 있는 필드만 검사한다.
# URL·날짜·연락처·식별코드 등은 "대구"가 우연히 포함돼도 무관하므로 제외한다.
DAEGU_RELEVANCE_FIELD_NAMES = [
    "biz_pbanc_nm",
    "supt_biz_titl_nm",
    "titl_nm",
    "aply_trgt_ctnt",
    "aply_trgt",
    "biz_supt_trgt_info",
    "pbanc_ctnt",
    "biz_supt_ctnt",
    "supt_biz_intrd_info",
    "ctnt",
    "sprv_inst",
    "biz_prch_dprt_nm",
    "supt_regin",
]


@dataclass(frozen=True)
class KStartupDaeguSupportItem:
    category: str
    source_type: str
    title: str
    source_name: str
    source_url: str
    published_at: str
    application_period: str
    target: str
    support_content: str
    contact: str
    raw_payload: dict[str, Any]


def fetch_kstartup_daegu_support_items() -> list[KStartupDaeguSupportItem]:
    api_key = get_kstartup_api_key()

    support_items: list[KStartupDaeguSupportItem] = []

    for endpoint in KSTARTUP_ENDPOINTS:
        raw_items = fetch_kstartup_endpoint_items(
            api_key=api_key,
            source_type=endpoint["source_type"],
            endpoint_path=endpoint["path"],
        )

        for raw_item in raw_items:
            if not is_daegu_relevant_item(raw_item):
                continue

            support_item = normalize_kstartup_item(
                source_type=endpoint["source_type"],
                raw_item=raw_item,
            )

            if not is_valid_kstartup_support_item(support_item):
                continue

            support_items.append(support_item)

    return support_items


def get_kstartup_api_key() -> str:
    api_key = os.getenv(KSTARTUP_API_KEY_ENV_NAME)

    if not api_key:
        raise RuntimeError(f"{KSTARTUP_API_KEY_ENV_NAME} GitHub Actions Secret이 필요합니다.")

    return api_key


def fetch_kstartup_endpoint_items(
    api_key: str,
    source_type: str,
    endpoint_path: str,
) -> list[dict[str, Any]]:
    request_url = f"{KSTARTUP_API_BASE_URL}{endpoint_path}"
    all_items: list[dict[str, Any]] = []
    seen_item_keys: set[str] = set()
    current_page = 1

    while current_page <= KSTARTUP_MAX_PAGES:
        try:
            page_items = fetch_kstartup_endpoint_page(
                api_key=api_key,
                request_url=request_url,
                source_type=source_type,
                page=current_page,
            )
        except KSTARTUP_FALLBACK_EXCEPTIONS as error:
            log_kstartup_fetch_failure(
                source_type=source_type,
                page=current_page,
                error=error,
            )
            break

        if not page_items:
            break

        new_items = []

        for page_item in page_items:
            item_key = build_kstartup_item_key(page_item)

            if item_key in seen_item_keys:
                continue

            seen_item_keys.add(item_key)
            new_items.append(page_item)

        if not new_items:
            break

        all_items.extend(new_items)

        if len(page_items) < KSTARTUP_PER_PAGE:
            break

        current_page += 1

    return all_items


def log_kstartup_fetch_failure(
    *,
    source_type: str,
    page: int,
    error: Exception,
) -> None:
    print(f"K-Startup 수집 실패: {source_type} {page}페이지 - {error}")


def fetch_kstartup_endpoint_page(
    api_key: str,
    request_url: str,
    source_type: str,
    page: int,
) -> list[dict[str, Any]]:
    response = requests.get(
        request_url,
        params={
            "ServiceKey": api_key,
            "page": page,
            "perPage": KSTARTUP_PER_PAGE,
            "returnType": "json",
        },
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    response_data = response.json()
    items = response_data.get("data", [])

    if not isinstance(items, list):
        raise RuntimeError(
            f"{source_type} API {page}페이지 응답 data 형식이 list가 아닙니다."
        )

    return items


def build_kstartup_item_key(raw_item: dict[str, Any]) -> str:
    source_url = first_non_empty_value(
        raw_item,
        [
            "detl_pg_url",
            "biz_gdnc_url",
            "biz_aply_url",
        ],
    )

    if source_url:
        return source_url

    title = first_non_empty_value(
        raw_item,
        [
            "biz_pbanc_nm",
            "supt_biz_titl_nm",
            "titl_nm",
        ],
    )
    published_at = first_non_empty_value(
        raw_item,
        [
            "fstm_reg_dt",
            "pbanc_rcpt_bgng_dt",
            "biz_yr",
        ],
    )

    return f"{title}|{published_at}"


def is_daegu_relevant_item(raw_item: dict[str, Any]) -> bool:
    combined_text = " ".join(
        str(raw_item.get(field_name, ""))
        for field_name in DAEGU_RELEVANCE_FIELD_NAMES
    )
    return any(keyword in combined_text for keyword in DAEGU_RELEVANCE_KEYWORDS)


def normalize_kstartup_item(
    source_type: str,
    raw_item: dict[str, Any],
) -> KStartupDaeguSupportItem:
    title = first_non_empty_value(
        raw_item,
        [
            "biz_pbanc_nm",
            "supt_biz_titl_nm",
            "titl_nm",
        ],
    )

    source_url = first_non_empty_value(
        raw_item,
        [
            "detl_pg_url",
            "biz_gdnc_url",
            "biz_aply_url",
        ],
    )

    published_at = first_non_empty_value(
        raw_item,
        [
            "fstm_reg_dt",
            "pbanc_rcpt_bgng_dt",
            "biz_yr",
        ],
    )

    application_period = build_application_period(raw_item)

    target = first_non_empty_value(
        raw_item,
        [
            "aply_trgt_ctnt",
            "aply_trgt",
            "biz_supt_trgt_info",
        ],
    )

    support_content = first_non_empty_value(
        raw_item,
        [
            "pbanc_ctnt",
            "biz_supt_ctnt",
            "supt_biz_intrd_info",
            "ctnt",
            "file_nm",
        ],
    )

    contact = first_non_empty_value(
        raw_item,
        [
            "prch_cnpl_no",
            "biz_prch_dprt_nm",
            "sprv_inst",
        ],
    )

    return KStartupDaeguSupportItem(
        category=KSTARTUP_CATEGORY,
        source_type=source_type,
        title=title,
        source_name=KSTARTUP_SOURCE_NAME,
        source_url=normalize_kstartup_url(source_url),
        published_at=published_at,
        application_period=application_period,
        target=target,
        support_content=support_content,
        contact=contact,
        raw_payload=raw_item,
    )


def is_valid_kstartup_support_item(
    support_item: KStartupDaeguSupportItem,
) -> bool:
    return bool(support_item.title and support_item.source_url)


def first_non_empty_value(raw_item: dict[str, Any], field_names: list[str]) -> str:
    for field_name in field_names:
        value = str(raw_item.get(field_name, "")).strip()

        if value:
            return value

    return ""


def build_application_period(raw_item: dict[str, Any]) -> str:
    start_date = str(raw_item.get("pbanc_rcpt_bgng_dt", "")).strip()
    end_date = str(raw_item.get("pbanc_rcpt_end_dt", "")).strip()

    if start_date and end_date:
        return f"{start_date} ~ {end_date}"

    return start_date or end_date


def normalize_kstartup_url(source_url: str) -> str:
    source_url = source_url.strip()

    if not source_url:
        return ""

    if source_url.startswith("http://") or source_url.startswith("https://"):
        return source_url

    return f"https://{source_url}"
