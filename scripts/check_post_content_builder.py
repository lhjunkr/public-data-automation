from __future__ import annotations

from content.post_content_builder import build_post_contents_from_candidates
from pipeline.daily_selection import select_today_public_data_contents


def main() -> None:
    selected_candidates = select_today_public_data_contents(
        sync_posted_history=False,
    )
    post_contents = build_post_contents_from_candidates(selected_candidates)

    print(f"게시 콘텐츠 변환 결과: {len(post_contents)}건")

    for index, post_content in enumerate(post_contents, start=1):
        print("=" * 60)
        print(f"{index}. [{post_content.category}] {post_content.title}")
        print("-" * 60)
        print("[Caption]")
        print(post_content.caption)
        print()
        print("[Hashtags]")
        print(" ".join(f"#{hashtag}" for hashtag in post_content.hashtags))
        print()
        print("[Image Text Lines]")
        for image_text_line in post_content.image_text_lines:
            print(f"- {image_text_line}")
        print()


if __name__ == "__main__":
    main()
    
    