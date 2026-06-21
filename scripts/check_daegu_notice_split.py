from sources.daegu_business_support import filter_daegu_business_support_notices
from sources.daegu_notice_rss import fetch_daegu_notices
from sources.daegu_public_opportunities import filter_daegu_public_opportunity_notices


def main() -> None:
    notices = fetch_daegu_notices()

    business_notices = filter_daegu_business_support_notices(notices)
    opportunity_notices = filter_daegu_public_opportunity_notices(notices)

    business_urls = {notice.source_url for notice in business_notices}
    opportunity_urls = {notice.source_url for notice in opportunity_notices}
    overlapping_urls = business_urls & opportunity_urls

    print(f"공지사항 RSS 전체: {len(notices)}건")
    print(f"대구 기업지원: {len(business_notices)}건")
    print(f"대구 공모·모집: {len(opportunity_notices)}건")
    print(f"중복 분류: {len(overlapping_urls)}건")

    if overlapping_urls:
        raise RuntimeError(f"기업지원/공모·모집 중복 분류 발생: {overlapping_urls}")


if __name__ == "__main__":
    main()