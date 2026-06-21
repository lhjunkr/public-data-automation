from sources.kstartup_daegu_support import fetch_kstartup_daegu_support_items


def main() -> None:
    support_items = fetch_kstartup_daegu_support_items()

    print(f"대구 창업지원 수집 결과: {len(support_items)}건")

    for index, support_item in enumerate(support_items[:5], start=1):
        print(f"{index}. [{support_item.source_type}] {support_item.title}")
        print(f"   URL: {support_item.source_url}")
        print(f"   기간: {support_item.application_period}")
        print()


if __name__ == "__main__":
    main()