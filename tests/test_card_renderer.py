from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from PIL import Image

from content.post_content import PostContent
from image.card_renderer import (
    BACKGROUND_COLORS,
    CARD_HEIGHT,
    CARD_WIDTH,
    get_text_width,
    load_korean_font,
    normalize_image_text_lines,
    render_post_content_card,
    wrap_text,
)


class TestCardRenderer(unittest.TestCase):
    def test_render_post_content_card_creates_png_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "card.png"

            rendered_path = render_post_content_card(
                post_content=make_post_content(),
                output_path=output_path,
            )

            self.assertEqual(rendered_path, output_path)
            self.assertTrue(output_path.exists())

            with Image.open(output_path) as image:
                self.assertEqual(image.size, (CARD_WIDTH, CARD_HEIGHT))
                self.assertEqual(image.format, "PNG")

    def test_render_post_content_card_uses_category_background_color(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "card.png"

            render_post_content_card(
                post_content=make_post_content(category="대구 창업지원"),
                output_path=output_path,
            )

            with Image.open(output_path) as image:
                self.assertEqual(
                    image.getpixel((10, 10)),
                    hex_to_rgb(BACKGROUND_COLORS["대구 창업지원"]),
                )

    def test_normalize_image_text_lines_limits_to_four_lines(self) -> None:
        self.assertEqual(
            normalize_image_text_lines(["1", "2", "3", "4", "5"]),
            ["1", "2", "3", "4"],
        )

    def test_normalize_image_text_lines_removes_empty_lines(self) -> None:
        self.assertEqual(
            normalize_image_text_lines(["대구", "", "  ", "공고"]),
            ["대구", "공고"],
        )

    def test_wrap_text_splits_oversized_word_by_width(self) -> None:
        font = load_korean_font(font_size=32)
        max_width = 120

        wrapped_lines = wrap_text(
            text="대구창업지원사업공고초장문텍스트",
            font=font,
            max_width=max_width,
        )

        self.assertGreater(len(wrapped_lines), 1)
        self.assertTrue(
            all(get_text_width(wrapped_line, font) <= max_width for wrapped_line in wrapped_lines)
        )


def make_post_content(category: str = "대구 창업지원") -> PostContent:
    return PostContent(
        category=category,
        title="2026년 대구 창업기업 모집",
        source_name="K-Startup",
        source_url="https://example.com/startup",
        published_at="2026.06.21",
        deadline_at="2026.07.07",
        summary="",
        caption="",
        hashtags=["대구", "공공정보"],
        image_text_lines=[
            category,
            "창업기업 모집",
            "2026.07.07 마감",
            "원문 공고 확인",
        ],
        raw_candidate=None,
    )


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    normalized_hex_color = hex_color.lstrip("#")

    return (
        int(normalized_hex_color[0:2], 16),
        int(normalized_hex_color[2:4], 16),
        int(normalized_hex_color[4:6], 16),
    )


if __name__ == "__main__":
    unittest.main()
