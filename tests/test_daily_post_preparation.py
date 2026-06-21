from __future__ import annotations

import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

from content.post_content import PostContent
from pipeline.daily_post_preparation import prepare_post_assets


class TestDailyPostPreparation(unittest.TestCase):
    def test_prepare_post_assets_renders_and_uploads_images(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("pipeline.daily_post_preparation.Path") as mock_path:
                mock_path.side_effect = Path
                mock_path.return_value = Path(temp_dir)

                with patch(
                    "pipeline.daily_post_preparation.upload_image_asset_to_r2",
                    return_value="https://pub-example.r2.dev/images/2026-06-21/post_1.png",
                ) as mock_upload_image_asset:
                    prepared_posts = prepare_post_assets(
                        post_contents=[make_post_content()],
                        run_date=date(2026, 6, 21),
                        upload_assets=True,
                    )

        self.assertEqual(len(prepared_posts), 1)
        self.assertTrue(prepared_posts[0].local_image_path.endswith("post_1.png"))
        self.assertEqual(
            prepared_posts[0].public_image_url,
            "https://pub-example.r2.dev/images/2026-06-21/post_1.png",
        )
        mock_upload_image_asset.assert_called_once()

    def test_prepare_post_assets_can_skip_upload(self) -> None:
        with patch(
            "pipeline.daily_post_preparation.upload_image_asset_to_r2"
        ) as mock_upload_image_asset:
            prepared_posts = prepare_post_assets(
                post_contents=[make_post_content()],
                run_date=date(2026, 6, 21),
                upload_assets=False,
            )

        self.assertEqual(len(prepared_posts), 1)
        self.assertEqual(prepared_posts[0].public_image_url, "")
        mock_upload_image_asset.assert_not_called()


def make_post_content() -> PostContent:
    return PostContent(
        category="대구 창업지원",
        title="2026년 대구 창업기업 모집",
        source_name="K-Startup",
        source_url="https://example.com/startup",
        published_at="2026.06.21",
        deadline_at="2026.07.07",
        summary="",
        caption="테스트 본문",
        hashtags=["대구", "공공정보"],
        image_text_lines=[
            "대구 창업지원",
            "창업기업 모집",
            "2026.07.07 마감",
            "원문 공고 확인",
        ],
        raw_candidate=None,
    )


if __name__ == "__main__":
    unittest.main()
