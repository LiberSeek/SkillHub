from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from pathlib import Path
import csv
import os

from PIL import Image, ImageDraw, ImageFont


def resolve_root() -> Path:
    override = os.environ.get("STUDIO_STICKER_ROOT")
    if override:
        return Path(override).expanduser()
    candidates = [
        Path.cwd(),
        Path.cwd() / "tools" / "stickers",
        Path.cwd() / "tools" / "sticker",
        Path.cwd() / "stickers",
        Path.cwd() / "sticker",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.name in {"stickers", "sticker"}:
            return candidate
    return candidates[1]


ROOT = resolve_root()
OUT_ROOT = ROOT / "processed"
RENAMED_DIR = OUT_ROOT / "renamed-originals"
TRANSPARENT_DIR = OUT_ROOT / "transparent"
STANDARDIZED_DIR = OUT_ROOT / "standardized"
MANIFEST_CSV = OUT_ROOT / "manifest.csv"
MANIFEST_MD = OUT_ROOT / "manifest.md"
CONTACT_SHEET = OUT_ROOT / "_contact_sheet_standardized.png"

CANVAS_SIZE = 1024
FIT_SIZE = 820
BLACK_THRESHOLD = 30
EDGE_PADDING = 20


@dataclass(frozen=True)
class Asset:
    source: str
    target: str
    category: str
    note: str


ASSETS: list[Asset] = [
    Asset("05-watercolor-portrait.png", "01-watercolor-portrait.png", "portrait", "水彩半身肖像"),
    Asset("14-beach-peace-sunglasses.png", "02-beach-peace-sunglasses.png", "lifestyle", "海边比耶墨镜"),
    Asset("20-laugh-black-tee.png", "03-laugh-black-tee.png", "expression", "黑T大笑"),
    Asset("ChatGPT Image 2026年5月22日 13_07_42.png", "04-confident-bare-portrait.png", "portrait", "自信裸肩肖像"),
    Asset("ChatGPT Image 2026年5月22日 13_07_44.png", "05-wink-finger-point.png", "expression", "眨眼竖食指"),
    Asset("ChatGPT Image 2026年5月22日 13_07_44_副本.png", "06-happy-wave.png", "expression", "开心挥手"),
    Asset("ChatGPT Image 2026年5月22日 13_07_44_副本2.png", "07-laugh-cheer.png", "expression", "闭眼大笑欢呼"),
    Asset("ChatGPT Image 2026年5月22日 13_07_44_副本3.png", "08-heart-eyes-blush.png", "expression", "爱心眼脸红"),
    Asset("ChatGPT Image 2026年5月22日 13_07_44_副本4.png", "09-sleepy-rub-eye.png", "expression", "困倦揉眼睛"),
    Asset("ChatGPT Image 2026年5月22日 13_07_44_副本5.png", "10-thinking-question.png", "expression", "思考问号"),
    Asset("ChatGPT Image 2026年5月22日 13_07_44_副本6.png", "11-gloomy-cloud.png", "expression", "低落乌云"),
    Asset("ChatGPT Image 2026年5月22日 13_07_44_副本7.png", "12-nervous-cold-sweat.png", "expression", "紧张发抖流汗"),
    Asset("ChatGPT Image 2026年5月22日 13_07_44_副本8.png", "13-angry-steam.png", "expression", "生气冒烟"),
    Asset("ChatGPT Image 2026年5月22日 13_07_47.png", "14-hoodie-laptop-coder.png", "work", "连帽衫程序员"),
    Asset("ChatGPT Image 2026年5月22日 13_07_47_副本.png", "15-whitecoat-laptop-mug.png", "work", "白大褂笔记本咖啡"),
    Asset("ChatGPT Image 2026年5月22日 13_07_47_副本2.png", "16-doctor-arms-crossed.png", "profession", "医生双手抱胸"),
    Asset("ChatGPT Image 2026年5月22日 13_07_47_副本3.png", "17-scientist-vial.png", "profession", "科学家举试剂"),
    Asset("ChatGPT Image 2026年5月22日 13_07_47_副本4.png", "18-teacher-blackboard.png", "profession", "老师黑板授课"),
    Asset("ChatGPT Image 2026年5月22日 13_07_47_副本5.png", "19-photographer-camera.png", "profession", "摄影师举相机"),
    Asset("ChatGPT Image 2026年5月22日 13_07_47_副本6.png", "20-barista-latte-art.png", "profession", "咖啡师拉花"),
    Asset("ChatGPT Image 2026年5月22日 13_07_47_副本7.png", "21-guitar-singer.png", "lifestyle", "弹吉他"),
    Asset("ChatGPT Image 2026年5月22日 13_07_47_副本8.png", "22-pilot-salute.png", "profession", "机长敬礼"),
    Asset("ChatGPT Image 2026年5月22日 13_07_49.png", "23-pilot-cap-hold.png", "profession", "机长手持帽子"),
    Asset("ChatGPT Image 2026年5月22日 13_07_49_副本.png", "24-engineer-hardhat-thumbsup.png", "profession", "工程师安全帽点赞"),
    Asset("ChatGPT Image 2026年5月22日 13_07_49_副本2.png", "25-firefighter-gear.png", "profession", "消防员装备"),
    Asset("ChatGPT Image 2026年5月22日 13_07_49_副本3.png", "26-chef-wok-toss.png", "profession", "厨师炒锅抛菜"),
    Asset("ChatGPT Image 2026年5月22日 13_07_49_副本4.png", "27-concierge-desk-bell.png", "profession", "礼宾员前台铃"),
    Asset("ChatGPT Image 2026年5月22日 13_07_49_副本5.png", "28-delivery-box.png", "profession", "快递员抱箱子"),
    Asset("ChatGPT Image 2026年5月22日 13_07_49_副本6.png", "29-presenter-microphone.png", "profession", "主持人拿麦"),
    Asset("ChatGPT Image 2026年5月22日 13_07_49_副本7.png", "30-stylist-scissors-comb.png", "profession", "造型师剪刀梳子"),
    Asset("ChatGPT Image 2026年5月22日 13_07_49_副本8.png", "31-gym-dumbbell-shaker.png", "lifestyle", "健身哑铃摇摇杯"),
    Asset("ChatGPT Image 2026年5月22日 13_07_51_副本.png", "32-stock-phone-uptrend.png", "business", "手机上涨行情"),
    Asset("ChatGPT Image 2026年5月22日 13_07_51_副本2.png", "33-laptop-lets-go-chart.png", "business", "笔记本 lets go 图表"),
    Asset("ChatGPT Image 2026年5月22日 13_07_51_副本3.png", "34-thinking-chart-bubble.png", "business", "思考行情气泡"),
    Asset("ChatGPT Image 2026年5月22日 13_07_51_副本4.png", "35-review-checklist-mug.png", "business", "复盘清单和杯子"),
    Asset("ChatGPT Image 2026年5月22日 13_07_51_副本5.png", "36-multi-screen-analyst.png", "business", "多屏分析师"),
    Asset("ChatGPT Image 2026年5月22日 13_07_51_副本6.png", "37-profit-phone-celebrate.png", "business", "盈利手机庆祝"),
    Asset("ChatGPT Image 2026年5月22日 13_07_51_副本7.png", "38-idea-bulb-thesis-board.png", "business", "灵感灯泡和 thesis 板"),
    Asset("ChatGPT Image 2026年5月22日 13_07_51_副本8.png", "39-long-term-meditation.png", "business", "长期主义打坐"),
    Asset("ChatGPT Image 2026年5月22日 13_20_18_副本.png", "40-resting-dev-multi-screen.png", "work", "多屏程序员躺椅休息"),
    Asset("ChatGPT Image 2026年5月22日 13_20_18_副本2.png", "41-debug-headphones-coder.png", "work", "耳机调试程序员"),
    Asset("ChatGPT Image 2026年5月22日 13_20_18_副本3.png", "42-laptop-lightbulb-idea.png", "work", "电脑和灯泡灵感"),
    Asset("ChatGPT Image 2026年5月22日 13_25_21.png", "43-laugh-black-tee-v2.png", "expression", "黑T大笑第二版"),
    Asset("ChatGPT Image 2026年5月22日 13_25_21_副本.png", "44-beach-peace-sunglasses-v2.png", "lifestyle", "海边比耶第二版"),
    Asset("ChatGPT Image 2026年5月22日 13_25_21_副本2.png", "45-watercolor-portrait-v2.png", "portrait", "水彩肖像第二版"),
    Asset("Gemini_Generated_Image_5f2llv5f2llv5f2l_副本.png", "46-server-deploy-pointer.png", "work", "服务器和 deploy 指示"),
    Asset("Gemini_Generated_Image_5f2llv5f2llv5f2l_副本2.png", "47-autoretry-sleepy-keyboard.png", "work", "autoretry 困倦键盘"),
    Asset("Gemini_Generated_Image_awub6tawub6tawub.png", "48-confused-broken-monitor.png", "work", "困惑和故障屏幕"),
    Asset("Gemini_Generated_Image_awub6tawub6tawub_副本.png", "49-code-hoodie-flex.png", "work", "code 连帽衫秀肌肉"),
    Asset("Gemini_Generated_Image_awub6tawub6tawub_副本2.png", "50-sleeping-on-keyboard.png", "work", "趴键盘睡觉"),
    Asset("Gemini_Generated_Image_d7ea3ad7ea3ad7ea (1).png", "51-surprised-omg.png", "expression", "惊讶 omg"),
    Asset("Gemini_Generated_Image_ebrzzaebrzzaebrz.png", "52-firefighter-water-hose.png", "profession", "消防员水枪"),
    Asset("Gemini_Generated_Image_ebrzzaebrzzaebrz_副本.png", "53-scientist-goggles-flask.png", "profession", "护目镜科学家"),
    Asset("Gemini_Generated_Image_ebrzzaebrzzaebrz_副本2.png", "54-dj-headset-mixer.png", "profession", "DJ 耳机打碟"),
    Asset("Gemini_Generated_Image_ebrzzaebrzzaebrz_副本3.png", "55-farmer-shovel-sprouts.png", "profession", "农夫铲子和嫩芽"),
]


def ensure_dirs() -> None:
    for path in (RENAMED_DIR, TRANSPARENT_DIR, STANDARDIZED_DIR):
        path.mkdir(parents=True, exist_ok=True)


def is_bg_black(pixel: tuple[int, int, int, int]) -> bool:
    r, g, b, a = pixel
    return a > 0 and r <= BLACK_THRESHOLD and g <= BLACK_THRESHOLD and b <= BLACK_THRESHOLD


def remove_edge_black_background(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    px = rgba.load()
    alpha = Image.new("L", (w, h), 255)
    a_px = alpha.load()
    queue: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    def push(x: int, y: int) -> None:
        if (x, y) in seen:
            return
        seen.add((x, y))
        if is_bg_black(px[x, y]) or px[x, y][3] == 0:
            queue.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while queue:
        x, y = queue.popleft()
        if a_px[x, y] == 0:
            continue
        a_px[x, y] = 0
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen:
                seen.add((nx, ny))
                if is_bg_black(px[nx, ny]) or px[nx, ny][3] == 0:
                    queue.append((nx, ny))

    rgba.putalpha(alpha)
    return rgba


def crop_transparent(img: Image.Image, padding: int = EDGE_PADDING) -> Image.Image:
    rgba = img.convert("RGBA")
    bbox = rgba.getchannel("A").getbbox()
    if bbox is None:
        return rgba
    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(rgba.width, right + padding)
    bottom = min(rgba.height, bottom + padding)
    return rgba.crop((left, top, right, bottom))


def standardize_canvas(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    target = Image.new("RGBA", (CANVAS_SIZE, CANVAS_SIZE), (0, 0, 0, 0))
    scale = min(FIT_SIZE / rgba.width, FIT_SIZE / rgba.height)
    new_size = (
        max(1, round(rgba.width * scale)),
        max(1, round(rgba.height * scale)),
    )
    resized = rgba.resize(new_size, Image.Resampling.LANCZOS)
    offset = ((CANVAS_SIZE - resized.width) // 2, (CANVAS_SIZE - resized.height) // 2)
    target.alpha_composite(resized, offset)
    return target


def save_original_copy(src: Path, dst: Path) -> None:
    img = Image.open(src)
    img.save(dst)


def build_contact_sheet(paths: list[Path]) -> None:
    thumb = 180
    label_h = 42
    margin = 16
    cols = 4
    rows = (len(paths) + cols - 1) // cols
    sheet = Image.new("RGBA", (cols * (thumb + margin) + margin, rows * (thumb + label_h + margin) + margin), (255, 255, 255, 255))
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Unicode.ttf", 15)
    except Exception:
        font = ImageFont.load_default()

    for i, path in enumerate(paths, 1):
        img = Image.open(path).convert("RGBA")
        canvas = Image.new("RGBA", (thumb, thumb), (245, 245, 245, 255))
        preview = img.copy()
        preview.thumbnail((thumb - 16, thumb - 16))
        x0 = (thumb - preview.width) // 2
        y0 = (thumb - preview.height) // 2
        canvas.alpha_composite(preview, (x0, y0))
        x = margin + ((i - 1) % cols) * (thumb + margin)
        y = margin + ((i - 1) // cols) * (thumb + label_h + margin)
        sheet.alpha_composite(canvas, (x, y + label_h))
        draw.rounded_rectangle((x, y, x + thumb, y + 32), radius=10, fill=(24, 24, 24, 255))
        draw.text((x + 8, y + 7), path.name[:22], fill="white", font=font)
        draw.rectangle((x, y + label_h, x + thumb, y + label_h + thumb), outline=(220, 220, 220, 255), width=1)

    sheet.convert("RGB").save(CONTACT_SHEET)


def main() -> None:
    ensure_dirs()
    manifest_rows: list[dict[str, str]] = []
    standardized_paths: list[Path] = []

    for asset in ASSETS:
        src = ROOT / asset.source
        renamed_path = RENAMED_DIR / asset.target
        transparent_path = TRANSPARENT_DIR / asset.target
        standardized_path = STANDARDIZED_DIR / asset.target

        save_original_copy(src, renamed_path)
        transparent = crop_transparent(remove_edge_black_background(Image.open(src)))
        transparent.save(transparent_path, format="PNG")
        standardized = standardize_canvas(transparent)
        standardized.save(standardized_path, format="PNG")
        standardized_paths.append(standardized_path)

        manifest_rows.append(
            {
                "source": asset.source,
                "target": asset.target,
                "category": asset.category,
                "note": asset.note,
                "renamed_original": str(renamed_path.relative_to(ROOT)),
                "transparent": str(transparent_path.relative_to(ROOT)),
                "standardized": str(standardized_path.relative_to(ROOT)),
            }
        )

    with MANIFEST_CSV.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["source", "target", "category", "note", "renamed_original", "transparent", "standardized"],
        )
        writer.writeheader()
        writer.writerows(manifest_rows)

    lines = [
        "# Stickers Manifest",
        "",
        "| Source | Target | Category | Note | Renamed Original | Transparent | Standardized |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in manifest_rows:
        lines.append(
            f'| {row["source"]} | {row["target"]} | {row["category"]} | {row["note"]} | {row["renamed_original"]} | {row["transparent"]} | {row["standardized"]} |'
        )
    MANIFEST_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    build_contact_sheet(standardized_paths)
    print(f"Processed {len(manifest_rows)} stickers")
    print(f"Output root: {OUT_ROOT}")


if __name__ == "__main__":
    main()
