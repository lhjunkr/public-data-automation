from sources.daegu_business_support import fetch_daegu_business_support_notices


def main() -> None:
    notices = fetch_daegu_business_support_notices()

    print(f"대구 기업지원 수집 결과: {len(notices)}건")

    for index, notice in enumerate(notices, start=1):
        print(f"{index}. {notice.title}")
        print(f"   URL: {notice.source_url}")
        print(f"   발행일: {notice.published_at}")
        print()


if __name__ == "__main__":
    main()