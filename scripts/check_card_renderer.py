from __future__ import annotations

from datetime import date
from pathlib import Path

from content.gemini_content_generator import enhance_post_contents_with_gemini
from content.post_content_builder import build_post_contents_from_candidates
from image.card_renderer import render_post_content_card
from pipeline.daily_selection import select_today_public_data_contents


def main() -> None:
    selected_candidates = select_today_public_data_contents(
        sync_posted_history=False,
    )
    post_contents = build_post_contents_from_candidates(selected_candidates)
    enhanced_post_contents = enhance_post_contents_with_gemini(post_contents)

    output_dir = Path("outputs") / date.today().isoformat() / "images"

    for index, post_content in enumerate(enhanced_post_contents, start=1):
        output_path = output_dir / f"post_{index}.png"
        rendered_path = render_post_content_card(
            post_content=post_content,
            output_path=output_path,
        )

        print(f"{index}. [{post_content.category}] {post_content.title}")
        print(f"   이미지: {rendered_path}")
        print()


if __name__ == "__main__":
    main()
