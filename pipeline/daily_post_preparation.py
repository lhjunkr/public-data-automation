from __future__ import annotations

from datetime import date
from pathlib import Path

from content.gemini_content_generator import enhance_post_contents_with_gemini
from content.post_content import PostContent
from content.post_content_builder import build_post_contents_from_candidates
from image.card_renderer import render_post_content_card
from pipeline.daily_selection import select_today_public_data_contents
from publishing.prepared_post import PreparedPost
from storage.asset_storage import build_asset_image_key, upload_image_asset_to_r2


def prepare_daily_posts(
    today: date | None = None,
    sync_posted_history: bool = True,
    upload_assets: bool = True,
) -> list[PreparedPost]:
    run_date = today or date.today()
    selected_candidates = select_today_public_data_contents(
        today=run_date,
        sync_posted_history=sync_posted_history,
    )
    post_contents = build_post_contents_from_candidates(selected_candidates)
    enhanced_post_contents = enhance_post_contents_with_gemini(post_contents)

    return prepare_post_assets(
        post_contents=enhanced_post_contents,
        run_date=run_date,
        upload_assets=upload_assets,
    )


def prepare_post_assets(
    post_contents: list[PostContent],
    run_date: date,
    upload_assets: bool = True,
) -> list[PreparedPost]:
    prepared_posts: list[PreparedPost] = []
    output_dir = Path("outputs") / run_date.isoformat() / "images"

    for index, post_content in enumerate(post_contents, start=1):
        image_filename = f"post_{index}.png"
        local_image_path = output_dir / image_filename
        rendered_image_path = render_post_content_card(
            post_content=post_content,
            output_path=local_image_path,
        )
        object_key = build_asset_image_key(
            run_date=run_date.isoformat(),
            image_filename=image_filename,
        )
        public_image_url = ""

        if upload_assets:
            public_image_url = upload_image_asset_to_r2(
                local_image_path=rendered_image_path,
                object_key=object_key,
            )

        prepared_posts.append(
            PreparedPost(
                post_content=post_content,
                local_image_path=str(rendered_image_path),
                public_image_url=public_image_url,
            )
        )

    return prepared_posts
