from collections import Counter

from sources.daegu_notice_classifier import classify_daegu_notice
from sources.daegu_notice_rss import fetch_daegu_notices


def main() -> None:
    notices = fetch_daegu_notices()
    category_counts: Counter[str] = Counter()

    print(f"대구시청 공지사항 분류 대상: {len(notices)}건")
    print()

    for index, notice in enumerate(notices, start=1):
        category = classify_daegu_notice(notice)
        category_label = category or "제외"
        category_counts[category_label] += 1

        print(f"{index}. [{category_label}] {notice.title}")
        print(f"   URL: {notice.source_url}")
        print()

    print("분류 결과 요약")
    for category_label, count in category_counts.items():
        print(f"- {category_label}: {count}건")


if __name__ == "__main__":
    main()