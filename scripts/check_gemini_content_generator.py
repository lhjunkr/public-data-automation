from __future__ import annotations

from content.gemini_content_generator import enhance_post_content_with_gemini
from content.post_content_builder import build_post_content_from_candidate
from pipeline.daily_selection import select_today_public_data_contents


def main() -> None:
    selected_candidates = select_today_public_data_contents(
        sync_posted_history=False,
    )

    if not selected_candidates:
        print("오늘 게시 후보가 없습니다.")
        return

    original_post_content = build_post_content_from_candidate(selected_candidates[0])
    enhanced_post_content = enhance_post_content_with_gemini(original_post_content)

    print("[기본 Caption]")
    print(original_post_content.caption)
    print()

    print("[Gemini Caption]")
    print(enhanced_post_content.caption)
    print()

    print("[Gemini Image Text Lines]")
    for image_text_line in enhanced_post_content.image_text_lines:
        print(f"- {image_text_line}")

    print()

    print("[Gemini Hashtags]")
    print(" ".join(f"#{hashtag}" for hashtag in enhanced_post_content.hashtags))


if __name__ == "__main__":
    main()
    
    