from __future__ import annotations

from sources.daegu_notice_rss import DaeguNotice


DAEGU_BUSINESS_SUPPORT_CATEGORY = "대구 기업지원"
DAEGU_PUBLIC_OPPORTUNITY_CATEGORY = "대구 공모·모집"


RECRUITMENT_EXCLUDE_KEYWORDS = [
    "채용",
    "임용",
    "공무원",
    "청원경찰",
    "개방형직위",
    "시험",
    "합격자",
    "면접",
    "서류전형",
    "필기시험",
]


STARTUP_EXCLUDE_KEYWORDS = [
    "창업",
    "스타트업",
    "예비창업자",
    "초기창업",
    "창업기업",
    "창업지원",
    "창업보육",
    "K-Startup",
    "케이스타트업",
]


GENERAL_NOTICE_EXCLUDE_KEYWORDS = [
    "입찰",
    "용역",
    "공사",
    "수의계약",
    "분실",
    "교통통제",
    "도로",
    "상수도",
    "하수도",
    "민원",
    "행정처분",
    "고시",
    "공시송달",
]


BUSINESS_SUPPORT_EXCLUDE_KEYWORDS = [
    "경력단절",
    "우수사례 공모전",
    "사진·영상 공모전",
    "사진 영상 공모전",
    "챌린지",
    "서포터즈",
    "기자단",
    "수강생",
    "교육생",
]


BUSINESS_SUPPORT_STRONG_KEYWORDS = [
    "기업지원",
    "기업 지원",
    "중소기업",
    "소상공인",
    "벤처기업",
    "참여기업",
    "참여업체",
    "지원사업",
    "마케팅 지원",
    "기술지원",
    "자금지원",
    "금융지원",
    "융자",
    "보조금",
    "지원금",
    "수출",
    "판로",
    "해외진출",
    "전시회",
    "박람회",
    "바우처",
    "스마트공장",
    "디지털전환",
    "인증",
    "특허",
    "지식재산",
    "가족친화인증",
]


BUSINESS_CONTEXT_KEYWORDS = [
    "기업",
    "업체",
    "사업자",
    "소상공인",
    "중소기업",
    "제조",
    "산업",
    "수출",
    "상공인",
]


BUSINESS_ACTION_KEYWORDS = [
    "지원",
    "지원사업",
    "모집",
    "참여",
    "신청",
    "선정",
    "컨설팅",
    "마케팅",
    "인증",
    "판로",
]


PUBLIC_OPPORTUNITY_EXCLUDE_KEYWORDS = [
    "적극행정",
    "응원 챌린지",
    "챌린지",
    "기업",
    "업체",
    "중소기업",
    "소상공인",
    "참여기업",
    "참여업체",
    "지원사업",
    "가족친화인증",
]


PUBLIC_OPPORTUNITY_KEYWORDS = [
    "공모",
    "공모전",
    "모집",
    "참가자",
    "참여자",
    "서포터즈",
    "기자단",
    "아이디어",
    "제안",
    "수강생",
    "교육생",
    "프로그램",
    "아카데미",
    "캠페인",
]


def classify_daegu_notice(notice: DaeguNotice) -> str | None:
    combined_text = build_notice_text(notice)

    if has_any_keyword(combined_text, GENERAL_NOTICE_EXCLUDE_KEYWORDS):
        return None

    if has_any_keyword(combined_text, RECRUITMENT_EXCLUDE_KEYWORDS):
        return None

    if has_any_keyword(combined_text, STARTUP_EXCLUDE_KEYWORDS):
        return None

    if is_business_support_notice(combined_text):
        return DAEGU_BUSINESS_SUPPORT_CATEGORY

    if is_public_opportunity_notice(combined_text):
        return DAEGU_PUBLIC_OPPORTUNITY_CATEGORY

    return None


def build_notice_text(notice: DaeguNotice) -> str:
    return " ".join(
        [
            notice.title,
            notice.source_name,
            notice.source_url,
            notice.published_at,
            notice.summary,
        ]
    )


def is_business_support_notice(combined_text: str) -> bool:
    if has_any_keyword(combined_text, BUSINESS_SUPPORT_EXCLUDE_KEYWORDS):
        return False

    if has_any_keyword(combined_text, BUSINESS_SUPPORT_STRONG_KEYWORDS):
        return True

    has_business_context = has_any_keyword(combined_text, BUSINESS_CONTEXT_KEYWORDS)
    has_business_action = has_any_keyword(combined_text, BUSINESS_ACTION_KEYWORDS)

    return has_business_context and has_business_action


def is_public_opportunity_notice(combined_text: str) -> bool:
    if has_any_keyword(combined_text, PUBLIC_OPPORTUNITY_EXCLUDE_KEYWORDS):
        return False

    return has_any_keyword(combined_text, PUBLIC_OPPORTUNITY_KEYWORDS)


def has_any_keyword(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)