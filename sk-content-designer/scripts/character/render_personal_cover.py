from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ModuleNotFoundError as exc:
    print(
        "Missing Pillow. Use the workspace venv Python or install pillow before running this script.",
        file=sys.stderr,
    )
    raise SystemExit(2) from exc


RATIOS = {
    "3:4": (1200, 1600),
    "4:3": (1600, 1200),
}

HEAVY_FONT_ENV = "CONTENT_DESIGNER_HEAVY_FONT"


def pick_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        os.environ.get(HEAVY_FONT_ENV, "") if bold else "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc" if bold else "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    ]
    for path in candidates:
        if not path:
            continue
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def fit_font(text: str, max_width: int, start: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for size in range(start, 48, -4):
        current = pick_font(size=size, bold=True)
        bbox = current.getbbox(text)
        if bbox[2] - bbox[0] <= max_width:
            return current
    return pick_font(48, bold=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Compose personal series cover from image, title, and sticker")
    parser.add_argument("--background", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--series", default="小小罗梦想中的一千零一夜")
    parser.add_argument("--ratio", default="3:4", choices=sorted(RATIOS))
    parser.add_argument("--sticker", default="")
    args = parser.parse_args()

    canvas_size = RATIOS[args.ratio]
    image = Image.open(args.background).convert("RGBA").resize(canvas_size)
    overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    w, h = canvas_size
    for y in range(h):
        alpha = int(220 * (y / h) ** 1.6)
        draw.line((0, y, w, y), fill=(0, 0, 0, alpha), width=1)

    image.alpha_composite(overlay)
    draw = ImageDraw.Draw(image)
    title_font = fit_font(args.title, w - 140, 120 if args.ratio == "3:4" else 96)
    subtitle_font = pick_font(34 if args.ratio == "3:4" else 28)
    series_font = pick_font(24)

    draw.text((72, 72), args.series, fill=(255, 255, 255, 230), font=series_font)
    draw.text((72, h - 420), args.title, fill=(255, 255, 255, 245), font=title_font)
    if args.subtitle:
        draw.text((72, h - 300), args.subtitle, fill=(236, 236, 236, 235), font=subtitle_font)

    if args.sticker:
        sticker = Image.open(args.sticker).convert("RGBA")
        target_w = int(w * 0.26)
        scale = target_w / sticker.width
        sticker = sticker.resize((target_w, int(sticker.height * scale)))
        image.alpha_composite(sticker, (w - sticker.width - 44, h - sticker.height - 44))

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
