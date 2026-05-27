#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


FONT_PATH = Path("/Users/raven/Library/Fonts/_思源黑体SourceHanSansCN-Heavy.otf")


def rounded_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def fit_bg(image: Image.Image, width: int, height: int) -> Image.Image:
    scale = max(width / image.width, height / image.height)
    resized = image.resize((round(image.width * scale), round(image.height * scale)), Image.Resampling.LANCZOS)
    left = (resized.width - width) // 2
    top = (resized.height - height) // 2
    return resized.crop((left, top, left + width, top + height))


def draw_card(
    base: Image.Image,
    xy: tuple[int, int],
    size: tuple[int, int],
    accent: tuple[int, int, int],
    index_text: str,
    title: str,
    detail: str,
    font_path: Path,
) -> None:
    x, y = xy
    w, h = size
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    rounded_rect(draw, (x, y, x + w, y + h), radius=28, fill=(13, 18, 25, 205), outline=accent + (220,), width=3)
    rounded_rect(draw, (x, y, x + 18, y + h), radius=20, fill=accent + (255,))

    index_font = ImageFont.truetype(str(font_path), 34)
    title_font = ImageFont.truetype(str(font_path), 44)
    body_font = ImageFont.truetype(str(font_path), 27)

    draw.text((x + 38, y + 26), index_text, font=index_font, fill=(255, 255, 255, 235))
    draw.text((x + 38, y + 72), title, font=title_font, fill=(255, 255, 255, 255))
    draw.text((x + 38, y + 132), detail, font=body_font, fill=(210, 221, 235, 235))
    base.alpha_composite(overlay)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an info-style vertical cover image.")
    parser.add_argument("--background", required=True)
    parser.add_argument("--sticker", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--layout", choices=["vertical", "horizontal"], default="vertical")
    args = parser.parse_args()

    if args.layout == "horizontal":
        width, height = 1440, 1080
    else:
        width, height = 1080, 1920

    bg = Image.open(args.background).convert("RGB")
    bg = fit_bg(bg, width, height)
    bg = ImageEnhance.Brightness(bg).enhance(0.56)
    bg = ImageEnhance.Color(bg).enhance(0.92)
    bg = bg.filter(ImageFilter.GaussianBlur(radius=2))

    base = bg.convert("RGBA")
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    draw.rectangle((0, 0, width, height), fill=(6, 10, 16, 78))

    if args.layout == "horizontal":
        draw.rounded_rectangle((42, 38, 1030, 258), radius=34, fill=(8, 14, 22, 208), outline=(125, 240, 214, 150), width=3)
        draw.rounded_rectangle((66, 62, 286, 116), radius=20, fill=(38, 204, 176, 255))

        badge_font = ImageFont.truetype(str(FONT_PATH), 26)
        title_font = ImageFont.truetype(str(FONT_PATH), 60)
        sub_font = ImageFont.truetype(str(FONT_PATH), 28)

        draw.text((96, 72), "详细拆 3 种计算方式", font=badge_font, fill=(8, 18, 24, 255))
        draw.text((84, 128), "API 中转站价格到底怎么算？", font=title_font, fill=(255, 255, 255, 255))
        draw.text((86, 210), "别只看便宜，要先看便宜从哪来", font=sub_font, fill=(199, 214, 228, 255))

        base.alpha_composite(overlay)

        card_w, card_h = 720, 170
        draw_card(base, (68, 320), (card_w, card_h), (61, 227, 186), "01", "模型折扣型", "模型结算价本身更低\n便宜得最直接，也最透明", FONT_PATH)
        draw_card(base, (68, 520), (card_w, card_h), (255, 184, 77), "02", "对冲型", "单价看着很低\n但汇率和结算会把成本拉回来", FONT_PATH)
        draw_card(base, (68, 720), (card_w, card_h), (120, 188, 255), "03", "汇率折扣型", "模型价格照搬官方\n只是充值汇率更好看", FONT_PATH)

        sticker = Image.open(args.sticker).convert("RGBA")
        sticker.thumbnail((450, 450), Image.Resampling.LANCZOS)
        sticker_x = width - sticker.width - 56
        sticker_y = height - sticker.height - 82

        glow = Image.new("RGBA", (sticker.width + 40, sticker.height + 40), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((0, 24, glow.width, glow.height), fill=(36, 198, 171, 72))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=18))
        base.alpha_composite(glow, (sticker_x - 16, sticker_y - 12))
        base.alpha_composite(sticker, (sticker_x, sticker_y))

        draw = ImageDraw.Draw(base)
        footer_font = ImageFont.truetype(str(FONT_PATH), 24)
        rounded_rect(draw, (68, 940, 744, 1014), radius=24, fill=(9, 15, 24, 198), outline=(255, 255, 255, 45), width=2)
        draw.text((98, 964), "用户最该看懂的，是便宜背后的计算逻辑", font=footer_font, fill=(240, 246, 252, 255))
    else:
        draw.rounded_rectangle((42, 40, 1038, 360), radius=38, fill=(8, 14, 22, 204), outline=(125, 240, 214, 150), width=3)
        draw.rounded_rectangle((64, 68, 270, 122), radius=22, fill=(38, 204, 176, 255))

        badge_font = ImageFont.truetype(str(FONT_PATH), 28)
        title_font = ImageFont.truetype(str(FONT_PATH), 74)
        sub_font = ImageFont.truetype(str(FONT_PATH), 34)

        draw.text((96, 79), "详细拆 3 种计算方式", font=badge_font, fill=(8, 18, 24, 255))
        draw.text((86, 150), "API 中转站价格", font=title_font, fill=(255, 255, 255, 255))
        draw.text((86, 235), "到底是怎么算出来的？", font=title_font, fill=(255, 255, 255, 255))
        draw.text((88, 318), "别只看便宜，要先看便宜从哪来", font=sub_font, fill=(199, 214, 228, 255))

        base.alpha_composite(overlay)

        draw_card(
            base,
            (78, 465),
            (924, 220),
            (61, 227, 186),
            "01",
            "模型折扣型",
            "模型结算价本身更低\n便宜得最直接，也最透明",
            FONT_PATH,
        )
        draw_card(
            base,
            (78, 728),
            (924, 220),
            (255, 184, 77),
            "02",
            "对冲型",
            "单价看着很低\n但汇率和结算会把成本拉回来",
            FONT_PATH,
        )
        draw_card(
            base,
            (78, 991),
            (924, 220),
            (120, 188, 255),
            "03",
            "汇率折扣型",
            "模型价格照搬官方\n只是充值汇率更好看",
            FONT_PATH,
        )

        sticker = Image.open(args.sticker).convert("RGBA")
        sticker.thumbnail((420, 420), Image.Resampling.LANCZOS)
        sticker_x = width - sticker.width - 42
        sticker_y = height - sticker.height - 42

        glow = Image.new("RGBA", (sticker.width + 40, sticker.height + 40), (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        glow_draw.ellipse((0, 24, glow.width, glow.height), fill=(36, 198, 171, 72))
        glow = glow.filter(ImageFilter.GaussianBlur(radius=18))
        base.alpha_composite(glow, (sticker_x - 16, sticker_y - 12))
        base.alpha_composite(sticker, (sticker_x, sticker_y))

        draw = ImageDraw.Draw(base)
        footer_font = ImageFont.truetype(str(FONT_PATH), 24)
        rounded_rect(draw, (86, 1288, 706, 1388), radius=26, fill=(9, 15, 24, 198), outline=(255, 255, 255, 45), width=2)
        draw.text((118, 1318), "这一条会把三种定价逻辑讲透", font=footer_font, fill=(245, 248, 252, 255))
        draw.text((118, 1350), "适合用户判断哪种便宜才是真的便宜", font=footer_font, fill=(186, 200, 217, 255))

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(out, quality=95)


if __name__ == "__main__":
    main()
