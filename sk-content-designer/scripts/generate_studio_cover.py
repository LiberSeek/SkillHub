from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def resolve_stickers_root() -> Path:
    override = os.environ.get("STUDIO_STICKERS_ROOT")
    if override:
        return Path(override).expanduser()
    candidates = [
        Path.cwd() / "tools" / "stickers",
        Path.cwd() / "tools" / "sticker",
        Path.cwd() / "stickers",
        Path.cwd() / "sticker",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


STICKERS_ROOT = resolve_stickers_root()
DEFAULT_CONFIG = Path(os.environ["STUDIO_COVER_CONFIG"]).expanduser() if os.environ.get("STUDIO_COVER_CONFIG") else None
PORTRAIT_CANVAS = (1200, 1600)
LANDSCAPE_CANVAS = (1600, 1200)
PADDING = 54

ACCENTS = {
    "green": (56, 217, 138),
    "orange": (255, 145, 76),
    "blue": (79, 208, 255),
    "gold": (248, 176, 97),
    "mint": (106, 237, 193),
}

HEAVY_FONT_ENV = "CONTENT_DESIGNER_HEAVY_FONT"
HEAVY_FONT_CANDIDATES = [
    os.environ.get(HEAVY_FONT_ENV, ""),
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]

REGULAR_FONT_CANDIDATES = [
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "/System/Library/Fonts/STHeiti Light.ttc",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
]


@dataclass(frozen=True)
class ToolCard:
    name: str
    role: str
    note: str
    accent: tuple[int, int, int]


@dataclass(frozen=True)
class TopicSpec:
    slug: str
    date_prefix: str
    topic_root: Path
    chip: str
    headline: str
    landscape_headline: str
    subheadline: str
    landscape_subheadline: str
    deck: str
    landscape_deck: str
    hero_eyebrow: str
    hero_lines: list[str]
    hero_statement: str
    hero_workflow: str
    hero_footer: str
    footer: str
    stickers: list[str]
    cards: list[ToolCard]
    publish: dict[str, Any]


def font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if bold:
        candidates = HEAVY_FONT_CANDIDATES
    else:
        candidates = REGULAR_FONT_CANDIDATES
    for path in candidates:
        if not path:
            continue
        try:
            return ImageFont.truetype(path, size=size)
        except Exception:
            continue
    return ImageFont.load_default()


def round_rect(draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], radius: int, fill, outline=None, width: int = 1) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


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


def choose_sticker(preferred: list[str]) -> Path:
    for name in preferred:
        path = STICKERS_ROOT / name
        if path.exists():
            return path
    fallback = STICKERS_ROOT / "base.png"
    if fallback.exists():
        return fallback
    raise FileNotFoundError(f"No sticker matched {preferred} and base.png not found under {STICKERS_ROOT}")


def fit_sticker(sticker_path: Path, max_w: int, max_h: int) -> Image.Image:
    im = Image.open(sticker_path).convert("RGBA")
    scale = min(max_w / im.width, max_h / im.height)
    new_size = (max(1, int(im.width * scale)), max(1, int(im.height * scale)))
    return im.resize(new_size, Image.Resampling.LANCZOS)


def parse_accent(value: str) -> tuple[int, int, int]:
    value = value.strip()
    if value in ACCENTS:
        return ACCENTS[value]
    if value.startswith("#") and len(value) == 7:
        return tuple(int(value[i : i + 2], 16) for i in (1, 3, 5))
    raise ValueError(f"Unsupported accent color: {value}")


def fit_text(text: str, max_width: int, start_size: int, min_size: int, bold: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        current = font(size, bold=bold)
        bbox = current.getbbox(text)
        if bbox[2] - bbox[0] <= max_width:
            return current
    return font(min_size, bold=bold)


def split_title_lines(text: str) -> list[str]:
    stripped = text.strip()
    if len(stripped) <= 8:
        return [stripped]
    midpoint = len(stripped) // 2
    split_at = midpoint
    if " " in stripped:
        parts = stripped.split()
        if len(parts) >= 2:
            return [" ".join(parts[:-1]), parts[-1]]
    for offset in range(0, min(4, len(stripped) // 2)):
        idx = midpoint - offset
        if idx > 2:
            split_at = idx
            break
    return [stripped[:split_at], stripped[split_at:]]


def load_spec(config_path: Path) -> TopicSpec:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    cards = [
        ToolCard(
            name=item["name"],
            role=item["role"],
            note=item["note"],
            accent=parse_accent(item["accent"]),
        )
        for item in data["cards"]
    ]
    hero_lines = data.get("hero_lines") or split_title_lines(data["headline"])
    return TopicSpec(
        slug=data["slug"],
        date_prefix=data["date_prefix"],
        topic_root=Path(data["topic_root"]),
        chip=data["chip"],
        headline=data["headline"],
        landscape_headline=data.get("landscape_headline", data["headline"]),
        subheadline=data["subheadline"],
        landscape_subheadline=data.get("landscape_subheadline", data["subheadline"]),
        deck=data["deck"],
        landscape_deck=data.get("landscape_deck", data["deck"]),
        hero_eyebrow=data["hero_eyebrow"],
        hero_lines=hero_lines,
        hero_statement=data["hero_statement"],
        hero_workflow=data["hero_workflow"],
        hero_footer=data["hero_footer"],
        footer=data["footer"],
        stickers=data["stickers"],
        cards=cards,
        publish=data.get("publish", {}),
    )


def generated_paths(spec: TopicSpec) -> dict[str, Path]:
    generated_root = spec.topic_root / "assets" / "cover" / "generated"
    bundle_root = spec.topic_root / "bundles" / "studio-auto"
    stem = f"{spec.date_prefix}-studio-cover-{spec.slug}"
    return {
        "generated_root": generated_root,
        "bundle_root": bundle_root,
        "legacy": generated_root / f"{stem}.png",
        "portrait": generated_root / f"{stem}-3x4.png",
        "landscape": generated_root / f"{stem}-4x3.png",
    }


def draw_portrait_title(draw: ImageDraw.ImageDraw, spec: TopicSpec) -> None:
    chip_font = font(22)
    title_font = fit_text(spec.headline, 810, 94, 68, bold=True)
    sub_font = fit_text(spec.subheadline, 780, 32, 24, bold=True)
    body_font = fit_text(spec.deck, 900, 26, 20, bold=False)

    round_rect(draw, (PADDING, 62, 370, 122), 28, fill=(255, 255, 255, 28), outline=(255, 255, 255, 55))
    draw.text((86, 80), spec.chip, fill=(242, 247, 250), font=chip_font)
    draw.text((PADDING, 160), spec.headline, fill=(248, 250, 252), font=title_font)
    draw.text((PADDING, 272), spec.subheadline, fill=(196, 208, 220), font=sub_font)
    draw.text((PADDING, 326), spec.deck, fill=(142, 159, 177), font=body_font)


def draw_portrait_hero(draw: ImageDraw.ImageDraw, spec: TopicSpec) -> None:
    x1, y1, x2, y2 = PADDING, 470, 760, 1260
    round_rect(draw, (x1, y1, x2, y2), 36, fill=(255, 255, 255, 26), outline=(111, 231, 189, 170), width=2)
    round_rect(draw, (x1 + 36, y1 + 34, x1 + 360, y1 + 96), 28, fill=(71, 184, 138, 58), outline=(83, 220, 164, 170))
    draw.text((x1 + 58, y1 + 51), spec.hero_eyebrow, fill=(238, 250, 244), font=font(24, bold=True))
    draw.text((x1 + 36, y1 + 138), spec.hero_lines[0], fill=(241, 245, 249), font=font(56, bold=True))
    if len(spec.hero_lines) > 1:
        draw.text((x1 + 36, y1 + 206), spec.hero_lines[1], fill=(255, 255, 255), font=fit_text(spec.hero_lines[1], 610, 106, 74, bold=True))
    draw.text((x1 + 36, y1 + 356), spec.hero_statement, fill=(220, 228, 236), font=fit_text(spec.hero_statement, 610, 34, 26, bold=True))
    draw.text((x1 + 36, y1 + 416), spec.hero_workflow, fill=(150, 164, 180), font=fit_text(spec.hero_workflow, 620, 24, 18, bold=False))
    draw.line((x1 + 36, y2 - 58, x2 - 36, y2 - 58), fill=(255, 255, 255, 70), width=1)
    footer_font = fit_text(spec.hero_footer, 350, 24, 18, bold=False)
    draw.text((x1 + 310, y2 - 42), spec.hero_footer, fill=(210, 220, 230), font=footer_font)


def draw_portrait_cards(draw: ImageDraw.ImageDraw, cards: list[ToolCard]) -> None:
    start_x = 802
    y = 480
    for card in cards:
        box = (start_x, y, 1128, y + 154)
        round_rect(draw, box, 28, fill=(255, 255, 255, 22), outline=(*card.accent, 190), width=2)
        draw.ellipse((start_x + 20, y + 26, start_x + 42, y + 48), fill=card.accent)
        draw.text((start_x + 58, y + 18), card.name, fill=(249, 250, 251), font=font(32, bold=True))
        draw.text((start_x + 24, y + 68), card.role, fill=(232, 238, 243), font=font(23, bold=True))
        draw.text((start_x + 24, y + 104), card.note, fill=(163, 177, 191), font=font(20))
        y += 172


def draw_landscape_title(draw: ImageDraw.ImageDraw, spec: TopicSpec) -> None:
    round_rect(draw, (PADDING, 54, 364, 114), 28, fill=(255, 255, 255, 28), outline=(255, 255, 255, 55))
    draw.text((84, 73), spec.chip, fill=(242, 247, 250), font=font(22))
    draw.text((PADDING, 150), spec.landscape_headline, fill=(248, 250, 252), font=fit_text(spec.landscape_headline, 690, 82, 58, bold=True))
    draw.text((PADDING, 256), spec.landscape_subheadline, fill=(196, 208, 220), font=fit_text(spec.landscape_subheadline, 700, 34, 24, bold=True))
    draw.text((PADDING, 312), spec.landscape_deck, fill=(142, 159, 177), font=fit_text(spec.landscape_deck, 760, 25, 18, bold=False))


def draw_landscape_hero(draw: ImageDraw.ImageDraw, spec: TopicSpec) -> None:
    x1, y1, x2, y2 = PADDING, 392, 930, 980
    round_rect(draw, (x1, y1, x2, y2), 36, fill=(255, 255, 255, 24), outline=(111, 231, 189, 170), width=2)
    round_rect(draw, (x1 + 34, y1 + 32, x1 + 344, y1 + 88), 28, fill=(71, 184, 138, 58), outline=(83, 220, 164, 170))
    draw.text((x1 + 56, y1 + 45), spec.hero_eyebrow, fill=(238, 250, 244), font=font(22, bold=True))
    draw.text((x1 + 34, y1 + 132), spec.hero_lines[0], fill=(241, 245, 249), font=font(50, bold=True))
    hero_line = spec.hero_lines[1] if len(spec.hero_lines) > 1 else spec.hero_lines[0]
    draw.text((x1 + 34, y1 + 198), hero_line, fill=(255, 255, 255), font=fit_text(hero_line, 660, 92, 64, bold=True))
    draw.text((x1 + 34, y1 + 338), spec.hero_statement, fill=(220, 228, 236), font=fit_text(spec.hero_statement, 660, 30, 22, bold=True))
    draw.text((x1 + 34, y1 + 392), spec.hero_workflow, fill=(150, 164, 180), font=fit_text(spec.hero_workflow, 680, 22, 16, bold=False))
    draw.line((x1 + 34, y2 - 52, x2 - 34, y2 - 52), fill=(255, 255, 255, 70), width=1)
    draw.text((x1 + 358, y2 - 36), spec.hero_footer, fill=(210, 220, 230), font=fit_text(spec.hero_footer, 340, 22, 16, bold=False))


def draw_landscape_cards(draw: ImageDraw.ImageDraw, cards: list[ToolCard]) -> None:
    positions = [
        (970, 400),
        (1240, 400),
        (970, 586),
        (1240, 586),
        (970, 772),
    ]
    for card, (x, y) in zip(cards, positions):
        box = (x, y, x + 236, y + 150)
        round_rect(draw, box, 26, fill=(255, 255, 255, 22), outline=(*card.accent, 190), width=2)
        draw.ellipse((x + 20, y + 24, x + 42, y + 46), fill=card.accent)
        draw.text((x + 56, y + 16), card.name, fill=(249, 250, 251), font=font(28, bold=True))
        draw.text((x + 20, y + 64), card.role, fill=(232, 238, 243), font=font(19, bold=True))
        draw.text((x + 20, y + 100), card.note, fill=(163, 177, 191), font=font(17))


def draw_sticker_panel(
    base: Image.Image,
    sticker_path: Path,
    max_size: tuple[int, int],
    panel_size: tuple[int, int],
    position: tuple[int, int],
) -> None:
    sticker = fit_sticker(sticker_path, *max_size)
    panel = Image.new("RGBA", panel_size, (0, 0, 0, 0))
    panel_w, panel_h = panel_size

    shadow = Image.new("RGBA", panel.size, (0, 0, 0, 0))
    alpha = sticker.getchannel("A").point(lambda v: int(v * 0.35))
    shadow_shape = Image.new("RGBA", sticker.size, (8, 14, 20, 0))
    shadow_shape.putalpha(alpha)
    shadow.alpha_composite(
        shadow_shape,
        ((panel_w - sticker.width) // 2 + 18, (panel_h - sticker.height) // 2 + 24),
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(14))

    panel.alpha_composite(shadow)
    panel.alpha_composite(sticker, ((panel_w - sticker.width) // 2, (panel_h - sticker.height) // 2))
    base.alpha_composite(panel, position)


def render_background(canvas: tuple[int, int], glow_points: list[tuple[tuple[int, int], int, tuple[int, int, int], int]]) -> Image.Image:
    bg = vertical_gradient(canvas, (10, 23, 33), (18, 33, 48)).convert("RGBA")
    for center, radius, color, alpha in glow_points:
        add_glow(bg, center, radius, color, alpha)
    return bg


def render_grid(draw: ImageDraw.ImageDraw, canvas: tuple[int, int], step: int, alpha_x: int, alpha_y: int) -> None:
    width, height = canvas
    for x in range(40, width, step):
        draw.line((x, 0, x, height), fill=(255, 255, 255, alpha_x), width=1)
    for y in range(40, height, step):
        draw.line((0, y, width, y), fill=(255, 255, 255, alpha_y), width=1)


def build_portrait_cover(spec: TopicSpec, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bg = render_background(
        PORTRAIT_CANVAS,
        [
            ((130, 270), 260, (83, 220, 164), 92),
            ((1040, 310), 210, (255, 255, 255), 38),
            ((1010, 1460), 260, (63, 194, 255), 36),
        ],
    )
    overlay = Image.new("RGBA", PORTRAIT_CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    round_rect(draw, (28, 34, 1172, 1566), 36, fill=(255, 255, 255, 10), outline=(255, 255, 255, 44))
    render_grid(draw, PORTRAIT_CANVAS, step=96, alpha_x=14, alpha_y=12)
    draw_portrait_title(draw, spec)
    draw_portrait_hero(draw, spec)
    draw_portrait_cards(draw, spec.cards)
    draw.text((PADDING, 1506), spec.footer, fill=(194, 207, 222), font=font(24))

    bg.alpha_composite(overlay)
    draw_sticker_panel(bg, choose_sticker(spec.stickers), max_size=(560, 680), panel_size=(560, 700), position=(640, 950))
    bg.save(out_path)
    return out_path


def build_landscape_cover(spec: TopicSpec, out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    bg = render_background(
        LANDSCAPE_CANVAS,
        [
            ((120, 220), 250, (83, 220, 164), 84),
            ((1380, 220), 210, (255, 255, 255), 32),
            ((1440, 1040), 300, (63, 194, 255), 34),
        ],
    )
    overlay = Image.new("RGBA", LANDSCAPE_CANVAS, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    round_rect(draw, (26, 32, 1574, 1168), 34, fill=(255, 255, 255, 10), outline=(255, 255, 255, 44))
    render_grid(draw, LANDSCAPE_CANVAS, step=96, alpha_x=12, alpha_y=11)
    draw_landscape_title(draw, spec)
    draw_landscape_hero(draw, spec)
    draw_landscape_cards(draw, spec.cards)
    draw.text((PADDING, 1102), spec.footer, fill=(194, 207, 222), font=font(22))

    bg.alpha_composite(overlay)
    draw_sticker_panel(bg, choose_sticker(spec.stickers), max_size=(500, 560), panel_size=(520, 600), position=(1040, 620))
    bg.save(out_path)
    return out_path


def stringify_description(value: Any) -> str:
    if isinstance(value, list):
        return "\n".join(str(item).strip() for item in value if str(item).strip()).strip()
    return str(value).strip()


def stringify_tags(tags: Any) -> str:
    if isinstance(tags, list):
        return " ".join(f"#{tag.lstrip('#')}" for tag in tags if str(tag).strip())
    return str(tags).strip()


def stringify_markdown(value: Any) -> str:
    if isinstance(value, list):
        return "\n\n".join(str(item).strip() for item in value if str(item).strip()).strip()
    return str(value).strip()


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def write_publish_bundle(spec: TopicSpec, outputs: dict[str, Path]) -> Path:
    bundle_root = outputs["bundle_root"]
    bundle_root.mkdir(parents=True, exist_ok=True)

    publish = spec.publish
    title = str(publish.get("title", spec.headline)).strip()
    description = stringify_description(publish.get("description", spec.hero_statement))
    tags_text = stringify_tags(publish.get("tags", []))
    content_markdown = stringify_markdown(publish.get("content", description))
    oral_script = stringify_markdown(publish.get("oral_script", ""))
    platforms = publish.get("platforms", {})

    write_text(bundle_root / "title.txt", title)
    write_text(bundle_root / "description.txt", description)
    write_text(bundle_root / "tags.txt", tags_text)
    write_text(bundle_root / "content.md", content_markdown)
    if oral_script:
        write_text(bundle_root / "oral-script.md", oral_script)

    for platform, payload in platforms.items():
        for stale in [bundle_root / f"{platform}.md", bundle_root / f"{platform}-content.md"]:
            if stale.exists():
                stale.unlink()
        platform_title = str(payload.get("title", title)).strip()
        platform_description = stringify_description(payload.get("description", description))
        platform_tags = stringify_tags(payload.get("tags", publish.get("tags", [])))
        platform_content = stringify_markdown(payload.get("content", content_markdown))
        summary = "\n\n".join(part for part in [platform_title, platform_description, platform_tags] if part)
        write_text(bundle_root / f"{platform}.txt", summary)
        if platform_content:
            write_text(bundle_root / f"{platform}-content.md", platform_content)

    manifest = {
        "slug": spec.slug,
        "topic_root": str(spec.topic_root),
        "covers": {
            "portrait": str(outputs["portrait"]),
            "landscape": str(outputs["landscape"]),
            "legacy": str(outputs["legacy"]),
        },
        "publish": publish,
    }
    write_text(bundle_root / "manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
    return bundle_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate studio cover images and publish bundles.")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG, help="Path to studio cover JSON config.")
    parser.add_argument(
        "--mode",
        choices=["all", "portrait", "landscape", "bundle"],
        default="all",
        help="What to generate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.config is None:
        raise SystemExit("Missing --config. Pass a topic cover config file or set STUDIO_COVER_CONFIG.")
    spec = load_spec(args.config)
    outputs = generated_paths(spec)

    if args.mode in {"all", "portrait"}:
        build_portrait_cover(spec, outputs["portrait"])
        build_portrait_cover(spec, outputs["legacy"])
    if args.mode in {"all", "landscape"}:
        build_landscape_cover(spec, outputs["landscape"])
    if args.mode in {"all", "bundle"}:
        write_publish_bundle(spec, outputs)

    if args.mode == "portrait":
        print(outputs["portrait"])
    elif args.mode == "landscape":
        print(outputs["landscape"])
    elif args.mode == "bundle":
        print(outputs["bundle_root"])
    else:
        print(outputs["portrait"])
        print(outputs["landscape"])
        print(outputs["bundle_root"])


if __name__ == "__main__":
    main()
