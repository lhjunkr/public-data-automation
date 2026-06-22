from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from storage.asset_storage import (
    build_asset_image_key,
    build_asset_public_url,
    upload_image_asset_to_r2,
)


class TestAssetStorage(unittest.TestCase):
    def test_build_asset_image_key(self) -> None:
        self.assertEqual(
            build_asset_image_key(
                run_date="2026-06-21",
                image_filename="post_1.png",
            ),
            "images/2026-06-21/post_1.png",
        )

    def test_build_asset_image_key_strips_directory_from_filename(self) -> None:
        self.assertEqual(
            build_asset_image_key(
                run_date="2026-06-21",
                image_filename="outputs/2026-06-21/images/post_1.png",
            ),
            "images/2026-06-21/post_1.png",
        )

    def test_build_asset_image_key_rejects_empty_filename(self) -> None:
        with self.assertRaises(ValueError):
            build_asset_image_key(
                run_date="2026-06-21",
                image_filename="",
            )

    def test_build_asset_public_url(self) -> None:
        self.assertEqual(
            build_asset_public_url(
                object_key="images/2026-06-21/post_1.png",
                public_base_url="https://pub-example.r2.dev/",
            ),
            "https://pub-example.r2.dev/images/2026-06-21/post_1.png",
        )

    @patch("storage.asset_storage.get_r2_assets_public_base_url")
    @patch("storage.asset_storage.get_r2_assets_bucket_name")
    @patch("storage.asset_storage.create_r2_assets_client")
    def test_upload_image_asset_to_r2_raises_clear_message_on_upload_failure(
        self,
        mock_create_r2_assets_client,
        mock_get_r2_assets_bucket_name,
        mock_get_r2_assets_public_base_url,
    ) -> None:
        with TemporaryDirectory() as temp_dir:
            local_image_path = Path(temp_dir) / "post_1.png"
            local_image_path.write_bytes(b"image")

            mock_client = Mock()
            mock_client.upload_file.side_effect = RuntimeError("network error")
            mock_create_r2_assets_client.return_value = mock_client
            mock_get_r2_assets_bucket_name.return_value = "public-data-automation-assets"
            mock_get_r2_assets_public_base_url.return_value = "https://pub-example.r2.dev"

            with self.assertRaisesRegex(RuntimeError, "R2 이미지 업로드 실패") as error:
                upload_image_asset_to_r2(
                    local_image_path=local_image_path,
                    object_key="images/2026-06-21/post_1.png",
                )

        error_message = str(error.exception)
        self.assertIn("local_image_path=", error_message)
        self.assertIn("bucket=public-data-automation-assets", error_message)
        self.assertIn("object_key=images/2026-06-21/post_1.png", error_message)
        self.assertIn("cause=network error", error_message)


if __name__ == "__main__":
    unittest.main()
