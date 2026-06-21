from sources.daegu_notice_rss import fetch_daegu_notices


def main() -> None:
    notices = fetch_daegu_notices()

    print(f"대구시청 공지사항 RSS 수집 결과: {len(notices)}건")

    for index, notice in enumerate(notices[:10], start=1):
        print(f"{index}. {notice.title}")
        print(f"   URL: {notice.source_url}")
        print(f"   발행일: {notice.published_at}")
        print()


if __name__ == "__main__":
    main()
