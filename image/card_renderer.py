from __future__ import annotations

import re
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from content.post_content import PostContent


CARD_WIDTH = 1080
CARD_HEIGHT = 1080

CARD_MARGIN_X = 72
CARD_TOP_Y = 96
CARD_TITLE_Y = 232
CARD_META_Y_OFFSET = 34
CARD_BRAND_Y = 972

BACKGROUND_COLORS = {
    "대구 채용·시험": "#123C69",
    "대구 공모·모집": "#4A325D",
    "대구 창업지원": "#0B6B43",
    "대구 기업지원": "#8A4B2A",
}

DEFAULT_BACKGROUND_COLOR = "#1F4E5F"
PRIMARY_TEXT_COLOR = "#FFFFFF"
SECONDARY_TEXT_COLOR = "#CDE7DA"
SUBTLE_TEXT_COLOR = "#B7D4C7"

CATEGORY_FONT_SIZE = 38
TITLE_FONT_SIZE = 74
META_FONT_SIZE = 44
BRAND_FONT_SIZE = 38

TITLE_MAX_LINES = 5
MAX_TEXT_WIDTH = CARD_WIDTH - (CARD_MARGIN_X * 2)
BRAND_NAME = "Today Daegu"
UNSUPPORTED_CARD_TEXT_REPLACEMENTS = {
    "🗓️": "",
    "🗓": "",
    "⏰": "",
}


def render_post_content_card(
    post_content: PostContent,
    output_path: Path,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    background_color = BACKGROUND_COLORS.get(
        post_content.category,
        DEFAULT_BACKGROUND_COLOR,
    )
    image = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), background_color)
    draw = ImageDraw.Draw(image)

    category_font = load_korean_font(CATEGORY_FONT_SIZE, font_index=0)
    title_font = load_korean_font(TITLE_FONT_SIZE, font_index=7)
    meta_font = load_korean_font(META_FONT_SIZE, font_index=0)
    brand_font = load_brand_font(BRAND_FONT_SIZE)

    image_text_lines = normalize_image_text_lines(post_content.image_text_lines)
    title_text = select_title_text(post_content=post_content, image_text_lines=image_text_lines)
    meta_text = select_meta_text(image_text_lines)

    draw_category(
        draw=draw,
        category=post_content.category,
        font=category_font,
    )
    title_bottom_y = draw_title(
        draw=draw,
        title_text=title_text,
        font=title_font,
    )
    draw_meta(
        draw=draw,
        meta_text=meta_text,
        y=title_bottom_y + CARD_META_Y_OFFSET,
        font=meta_font,
    )
    draw_brand(draw=draw, font=brand_font)

    image.save(output_path, format="PNG", optimize=True)

    return output_path


def draw_category(
    draw: ImageDraw.ImageDraw,
    category: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    draw.text(
        (CARD_MARGIN_X, CARD_TOP_Y),
        category,
        font=font,
        fill=SECONDARY_TEXT_COLOR,
    )


def draw_title(
    draw: ImageDraw.ImageDraw,
    title_text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> int:
    wrapped_title_lines = wrap_text(
        text=title_text,
        font=font,
        max_width=MAX_TEXT_WIDTH,
    )[:TITLE_MAX_LINES]
    current_y = CARD_TITLE_Y

    for title_line in wrapped_title_lines:
        draw.text(
            (CARD_MARGIN_X, current_y),
            title_line,
            font=font,
            fill=PRIMARY_TEXT_COLOR,
        )
        current_y += get_line_height(font) + 22

    return current_y


def draw_meta(
    draw: ImageDraw.ImageDraw,
    meta_text: str,
    y: int,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    if not meta_text:
        return

    for meta_line in wrap_text(meta_text, font=font, max_width=MAX_TEXT_WIDTH):
        draw.text(
            (CARD_MARGIN_X, y),
            meta_line,
            font=font,
            fill=SUBTLE_TEXT_COLOR,
        )
        y += get_line_height(font) + 14


def draw_brand(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> None:
    brand_bbox = draw.textbbox((0, 0), BRAND_NAME, font=font)
    brand_width = brand_bbox[2] - brand_bbox[0]
    brand_x = (CARD_WIDTH - brand_width) // 2

    draw.text(
        (brand_x, CARD_BRAND_Y),
        BRAND_NAME,
        font=font,
        fill=PRIMARY_TEXT_COLOR,
    )


def normalize_image_text_lines(image_text_lines: list[str]) -> list[str]:
    normalized_lines: list[str] = []

    for image_text_line in image_text_lines:
        sanitized_line = sanitize_card_text(image_text_line)

        if sanitized_line:
            normalized_lines.append(sanitized_line)

    return normalized_lines[:4]


def sanitize_card_text(text: str) -> str:
    sanitized_text = text.strip()

    for unsupported_text, replacement_text in UNSUPPORTED_CARD_TEXT_REPLACEMENTS.items():
        sanitized_text = sanitized_text.replace(unsupported_text, replacement_text)

    return re.sub(r"\s+", " ", sanitized_text).strip()


def select_title_text(
    post_content: PostContent,
    image_text_lines: list[str],
) -> str:
    if len(image_text_lines) >= 2:
        return image_text_lines[1]

    return post_content.title


def select_meta_text(image_text_lines: list[str]) -> str:
    if len(image_text_lines) >= 3:
        return image_text_lines[2]

    return ""


def wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    words = split_text_for_wrapping(text)

    if not words:
        return []

    wrapped_lines: list[str] = []
    current_line = ""

    for word in words:
        candidate_line = word if not current_line else f"{current_line}{word}"

        if get_text_width(candidate_line, font) <= max_width:
            current_line = candidate_line
            continue

        if current_line:
            wrapped_lines.append(current_line.rstrip())
            current_line = ""

        if get_text_width(word, font) > max_width:
            wrapped_lines.extend(
                split_oversized_word_by_width(
                    text=word.strip(),
                    font=font,
                    max_width=max_width,
                )
            )
            continue

        current_line = word

    if current_line:
        wrapped_lines.append(current_line.rstrip())

    return wrapped_lines


def split_oversized_word_by_width(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    max_width: int,
) -> list[str]:
    split_lines: list[str] = []
    current_line = ""

    for character in text:
        candidate_line = f"{current_line}{character}"

        if get_text_width(candidate_line, font) <= max_width:
            current_line = candidate_line
            continue

        if current_line:
            split_lines.append(current_line)

        current_line = character

    if current_line:
        split_lines.append(current_line)

    return split_lines


def split_text_for_wrapping(text: str) -> list[str]:
    return re.findall(r"\S+\s*", text)


def get_text_width(
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
) -> int:
    bbox = font.getbbox(text)
    return bbox[2] - bbox[0]


def get_line_height(font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> int:
    bbox = font.getbbox("가나다ABC123")
    return bbox[3] - bbox[1]


def load_korean_font(
    font_size: int,
    font_index: int = 0,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    apple_sd_gothic_path = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")

    if apple_sd_gothic_path.exists():
        return ImageFont.truetype(
            str(apple_sd_gothic_path),
            font_size,
            index=font_index,
        )

    font_candidates = [
        "/Library/Fonts/AppleGothic.ttf",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    for font_path in font_candidates:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, font_size)

    return ImageFont.load_default()


def load_brand_font(font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    brand_font_candidates = [
        "/System/Library/Fonts/NewYorkItalic.ttf",
        "/System/Library/Fonts/Supplemental/Times New Roman Bold Italic.ttf",
        "/System/Library/Fonts/Times.ttc",
    ]

    for font_path in brand_font_candidates:
        if Path(font_path).exists():
            return ImageFont.truetype(font_path, font_size)

    return load_korean_font(font_size, font_index=2)
