#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
from pathlib import Path

from PIL import Image, ImageColor, ImageDraw, ImageEnhance, ImageFilter, ImageFont


HEAVY_FONT_CANDIDATES = [
    os.environ.get("CONTENT_DESIGNER_HEAVY_FONT", ""),
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]
REGULAR_FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = HEAVY_FONT_CANDIDATES if bold else REGULAR_FONT_CANDIDATES
    for path in candidates:
        if not path:
            continue
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def fit_bg(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def text_width(value: str, current_font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> int:
    box = current_font.getbbox(value)
    return box[2] - box[0]


def fit_font_for_text(text: str, max_width: int, start: int, minimum: int, bold: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for size in range(start, minimum - 1, -2):
        current = load_font(size, bold=bold)
        if text_width(text, current) <= max_width:
            return current
    return load_font(minimum, bold=bold)


def parse_color(value: str) -> tuple[int, int, int]:
    return ImageColor.getrgb(value)


def add_sticker(base: Image.Image, sticker_path: Path, max_size: tuple[int, int], anchor: tuple[int, int]) -> None:
    sticker = Image.open(sticker_path).convert("RGBA")
    sticker.thumbnail(max_size, Image.Resampling.LANCZOS)

    shadow = Image.new("RGBA", (sticker.width + 40, sticker.height + 40), (0, 0, 0, 0))
    draw = ImageDraw.Draw(shadow)
    draw.ellipse((0, 28, shadow.width, shadow.height), fill=(25, 48, 73, 82))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))

    x, y = anchor
    base.alpha_composite(shadow, (x - 18, y - 10))
    base.alpha_composite(sticker, (x, y))


def build_cover(
    background_path: Path,
    sticker_path: Path,
    output_path: Path,
    layout: str,
    chip: str,
    title_line_1: str,
    title_line_2: str,
    subtitle: str,
    deck: str,
    footer: str,
    accent: tuple[int, int, int],
) -> None:
    width, height = (1200, 1600) if layout == "portrait" else (1600, 1200)
    bg = Image.open(background_path).convert("RGB")
    bg = fit_bg(bg, width, height)
    bg = ImageEnhance.Brightness(bg).enhance(0.72)
    bg = ImageEnhance.Color(bg).enhance(0.9)
    base = bg.convert("RGBA")

    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    draw.rectangle((0, 0, width, height), fill=(7, 13, 20, 64))
    rounded_rect(draw, (24, 24, width - 24, height - 24), 34, fill=(11, 18, 27, 36), outline=(255, 255, 255, 42))

    chip_w = 320 if layout == "portrait" else 300
    rounded_rect(draw, (54, 58, 54 + chip_w, 118), 28, fill=(255, 255, 255, 28), outline=(255, 255, 255, 58))
    draw.text((84, 77), chip, font=load_font(22), fill=(243, 247, 250, 255))

    if layout == "portrait":
        title_1 = fit_font_for_text(title_line_1, 980, 88, 64, bold=True)
        title_2 = fit_font_for_text(title_line_2, 980, 110, 76, bold=True)
        sub_font = fit_font_for_text(subtitle, 980, 32, 24, bold=True)
        deck_font = fit_font_for_text(deck, 980, 24, 18, bold=False)

        draw.text((54, 160), title_line_1, font=title_1, fill=(251, 252, 253, 255))
        draw.text((54, 268), title_line_2, font=title_2, fill=(251, 252, 253, 255))
        draw.text((54, 402), subtitle, font=sub_font, fill=(225, 233, 241, 255))
        draw.text((54, 454), deck, font=deck_font, fill=(171, 186, 201, 255))

        rounded_rect(draw, (54, 520, 760, 1280), 38, fill=(10, 18, 28, 170), outline=(*accent, 188), width=2)
        rounded_rect(draw, (90, 554, 416, 620), 28, fill=(*accent, 60), outline=(*accent, 180), width=2)
        draw.text((114, 575), "当前主线 · 模型往下压，底座往上抬", font=load_font(24, bold=True), fill=(241, 248, 244, 255))
        draw.text((92, 664), "算力出海", font=load_font(62, bold=True), fill=(247, 249, 251, 255))
        draw.text((92, 748), "已经变了", font=load_font(102, bold=True), fill=(255, 255, 255, 255))
        draw.text((92, 934), "以后不只拼模型强不强，还拼网络、机房、调度和电。", font=fit_font_for_text("以后不只拼模型强不强，还拼网络、机房、调度和电。", 620, 28, 20, bold=True), fill=(238, 242, 246, 255))
        draw.text((92, 998), "中国移动修路 / 中国电信搭场 / 中国联通开口", font=load_font(24), fill=(170, 183, 198, 255))
        draw.line((92, 1218, 724, 1218), fill=(255, 255, 255, 70), width=1)
        draw.text((364, 1234), "Qwen Cloud 只是开头 · 真正的战场在底座", font=load_font(22), fill=(215, 224, 233, 255))

        add_sticker(base, sticker_path, max_size=(420, 420), anchor=(765, 1086))
        draw.text((54, 1510), footer, font=load_font(22), fill=(208, 218, 228, 255))
    else:
        title_1 = fit_font_for_text(title_line_1, 840, 82, 58, bold=True)
        title_2 = fit_font_for_text(title_line_2, 840, 102, 74, bold=True)
        sub_font = fit_font_for_text(subtitle, 840, 34, 24, bold=True)
        deck_font = fit_font_for_text(deck, 840, 24, 18, bold=False)

        draw.text((54, 150), title_line_1, font=title_1, fill=(251, 252, 253, 255))
        draw.text((54, 252), title_line_2, font=title_2, fill=(251, 252, 253, 255))
        draw.text((54, 374), subtitle, font=sub_font, fill=(225, 233, 241, 255))
        draw.text((54, 428), deck, font=deck_font, fill=(171, 186, 201, 255))

        rounded_rect(draw, (54, 520, 940, 1002), 38, fill=(10, 18, 28, 168), outline=(*accent, 188), width=2)
        rounded_rect(draw, (90, 554, 398, 618), 28, fill=(*accent, 60), outline=(*accent, 180), width=2)
        draw.text((114, 574), "当前主线 · 模型往下压，底座往上抬", font=load_font(22, bold=True), fill=(241, 248, 244, 255))
        draw.text((92, 654), "算力出海", font=load_font(58, bold=True), fill=(247, 249, 251, 255))
        draw.text((92, 734), "已经变了", font=load_font(96, bold=True), fill=(255, 255, 255, 255))
        draw.text((92, 874), "以后不只拼模型强不强，还拼网络、机房、调度和电。", font=fit_font_for_text("以后不只拼模型强不强，还拼网络、机房、调度和电。", 760, 28, 20, bold=True), fill=(238, 242, 246, 255))
        draw.text((92, 936), "中国移动修路 / 中国电信搭场 / 中国联通开口", font=load_font(24), fill=(170, 183, 198, 255))
        draw.line((92, 948, 900, 948), fill=(255, 255, 255, 70), width=1)
        draw.text((430, 966), "Qwen Cloud 只是开头 · 真正的战场在底座", font=load_font(22), fill=(215, 224, 233, 255))

        add_sticker(base, sticker_path, max_size=(370, 370), anchor=(1120, 758))
        draw.text((54, 1126), footer, font=load_font(22), fill=(208, 218, 228, 255))

    base.alpha_composite(overlay)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(output_path, quality=95)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose a studio cover from a Gemini-generated background.")
    parser.add_argument("--background", type=Path, required=True)
    parser.add_argument("--sticker", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--layout", choices=["portrait", "landscape"], required=True)
    parser.add_argument("--chip", required=True)
    parser.add_argument("--title1", required=True)
    parser.add_argument("--title2", required=True)
    parser.add_argument("--subtitle", required=True)
    parser.add_argument("--deck", required=True)
    parser.add_argument("--footer", required=True)
    parser.add_argument("--accent", default="#4ee1b5")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    build_cover(
        background_path=args.background,
        sticker_path=args.sticker,
        output_path=args.output,
        layout=args.layout,
        chip=args.chip,
        title_line_1=args.title1,
        title_line_2=args.title2,
        subtitle=args.subtitle,
        deck=args.deck,
        footer=args.footer,
        accent=parse_color(args.accent),
    )


if __name__ == "__main__":
    main()
