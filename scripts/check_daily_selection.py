from __future__ import annotations

from pipeline.daily_selection import select_today_public_data_contents


def main() -> None:
    selected_candidates = select_today_public_data_contents(
        sync_posted_history=False,
    )

    print(f"오늘 게시 후보: {len(selected_candidates)}건")

    for index, candidate in enumerate(selected_candidates, start=1):
        print(f"{index}. [{candidate.category}] {candidate.title}")
        print(f"   출처: {candidate.source_name}")
        print(f"   URL: {candidate.source_url}")

        if candidate.published_at:
            print(f"   게시일: {candidate.published_at}")

        if candidate.deadline_at:
            print(f"   마감일: {candidate.deadline_at}")

        print()


if __name__ == "__main__":
    main()