from __future__ import annotations

import unittest

from storage.asset_storage import build_asset_image_key, build_asset_public_url


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


if __name__ == "__main__":
    unittest.main()
