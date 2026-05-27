from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


CARD_SIZE = (1200, 1600)
PADDING = 72

ACCENTS = {
    "orange": (255, 145, 76),
    "green": (56, 217, 138),
    "blue": (79, 208, 255),
    "gold": (248, 176, 97),
    "red": (255, 107, 87),
}


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if bold:
        candidates = [
            "/Users/raven/Library/Fonts/_思源黑体SourceHanSansCN-Heavy.otf",
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Medium.ttc",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        ]
    else:
        candidates = [
            "/System/Library/Fonts/Hiragino Sans GB.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
            "/System/Library/Fonts/Supplemental/Songti.ttc",
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def mono_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in [
        "/System/Library/Fonts/SFNSMono.ttf",
        "/System/Library/Fonts/Menlo.ttc",
        "/System/Library/Fonts/Supplemental/Courier New.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return font(size)


def round_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def fit_text(text: str, max_width: int, start_size: int, min_size: int, bold: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        current = font(size, bold=bold)
        bbox = current.getbbox(text)
        if bbox[2] - bbox[0] <= max_width:
            return current
    return font(min_size, bold=bold)


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    max_width: int,
    size: int,
    line_gap: int,
    fill,
    bold: bool = False,
) -> int:
    current_font = font(size, bold=bold)
    if not text.strip():
        return xy[1]

    lines: list[str] = []
    line = ""
    for raw_char in text:
        if raw_char == "\n":
            if line:
                lines.append(line)
                line = ""
            continue
        candidate = f"{line}{raw_char}"
        width = current_font.getbbox(candidate)[2] - current_font.getbbox(candidate)[0]
        if width <= max_width or not line:
            line = candidate
        else:
            lines.append(line)
            line = raw_char
    if line:
        lines.append(line)

    x, y = xy
    for item in lines:
        draw.text((x, y), item, fill=fill, font=current_font)
        y += size + line_gap
    return y


def vertical_gradient(size: tuple[int, int], top: tuple[int, int, int], bottom: tuple[int, int, int]) -> Image.Image:
    w, h = size
    img = Image.new("RGB", size)
    px = img.load()
    for y in range(h):
        t = y / max(1, h - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        for x in range(w):
            px[x, y] = (r, g, b)
    return img


def add_glow(base: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> None:
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    cx, cy = center
    for i in range(radius, 0, -24):
        a = max(0, int(alpha * (i / radius) ** 2))
        draw.ellipse((cx - i, cy - i, cx + i, cy + i), fill=(*color, a))
    base.alpha_composite(overlay)


def render_grid(draw: ImageDraw.ImageDraw, size: tuple[int, int], step: int = 96) -> None:
    w, h = size
    for x in range(48, w, step):
        draw.line((x, 0, x, h), fill=(255, 255, 255, 14), width=1)
    for y in range(48, h, step):
        draw.line((0, y, w, y), fill=(255, 255, 255, 12), width=1)


def build_card(spec: dict, card: dict, out_path: Path) -> None:
    accent = ACCENTS[card["accent"]]
    bg = vertical_gradient(CARD_SIZE, (10, 23, 33), (18, 33, 48)).convert("RGBA")
    add_glow(bg, (180, 240), 260, accent, 86)
    add_glow(bg, (1020, 1280), 320, (79, 208, 255), 28)

    overlay = Image.new("RGBA", CARD_SIZE, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    round_rect(draw, (28, 28, 1172, 1572), 40, fill=(255, 255, 255, 10), outline=(255, 255, 255, 36))
    render_grid(draw, CARD_SIZE)

    chip_box = (PADDING, 70, PADDING + 380, 126)
    round_rect(draw, chip_box, 26, fill=(255, 255, 255, 24), outline=(255, 255, 255, 50))
    draw.text((PADDING + 24, 86), "API 聚合站成本判断", fill=(240, 245, 248), font=mono_font(20))

    draw.text((PADDING, 170), spec["title"], fill=(248, 250, 252), font=fit_text(spec["title"], 920, 72, 48, True))
    draw.text((PADDING, 276), spec["subtitle"], fill=(196, 208, 220), font=fit_text(spec["subtitle"], 920, 30, 22, False))

    panel = (PADDING, 386, 1128, 1328)
    round_rect(draw, panel, 38, fill=(255, 255, 255, 18), outline=(*accent, 180), width=2)
    round_rect(draw, (PADDING + 34, 420, PADDING + 300, 474), 26, fill=(*accent, 48), outline=(*accent, 160))
    draw.text((PADDING + 58, 435), card["eyebrow"], fill=(244, 248, 250), font=font(22, bold=True))

    headline_y = 526
    for idx, line in enumerate(card["headline"].split("\n")):
        headline_font = fit_text(line, 860, 98, 60, True)
        draw.text((PADDING + 34, headline_y + idx * 112), line, fill=(252, 253, 255), font=headline_font)

    number_box = (PADDING + 34, 792, 1088, 950)
    round_rect(draw, number_box, 30, fill=(9, 16, 25, 138), outline=(255, 255, 255, 24))
    if "250" in card["headline"] or "25" in card["headline"] or "7.5" in card["headline"]:
        draw.text((PADDING + 76, 838), card["headline"].replace("\n", "  "), fill=accent, font=fit_text(card["headline"].replace("\n", "  "), 900, 74, 48, True))
    else:
        draw.text((PADDING + 76, 838), "看真实账单，不看表面标价", fill=accent, font=fit_text("看真实账单，不看表面标价", 900, 58, 38, True))

    body_y = 1012
    draw_wrapped_text(draw, card["body"], (PADDING + 34, body_y), 980, 34, 16, (220, 228, 236), False)

    footer_box = (PADDING, 1398, 1128, 1510)
    round_rect(draw, footer_box, 28, fill=(8, 14, 24, 188), outline=(255, 255, 255, 22))
    draw.text((PADDING + 34, 1432), "结论：别只问多少钱，还要问缓存命中和号池稳定性", fill=(242, 247, 250), font=fit_text("结论：别只问多少钱，还要问缓存命中和号池稳定性", 1000, 28, 20, True))

    bg.alpha_composite(overlay)
    bg.save(out_path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate studio-style social cards from JSON config.")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    config = json.loads(args.config.read_text(encoding="utf-8"))
    topic_root = Path(config["topic_root"])
    out_root = topic_root / "assets" / "images" / "generated"
    out_root.mkdir(parents=True, exist_ok=True)

    for index, card in enumerate(config["cards"], start=2):
        out_name = f"{index:02d}-{card['id']}.png"
        build_card(config, card, out_root / out_name)

    print(out_root)


if __name__ == "__main__":
    main()
