from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import os
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageDraw, ImageFont


def resolve_root() -> Path:
    override = os.environ.get("STUDIO_STICKER_ROOT")
    if override:
        return Path(override).expanduser()
    candidates = [
        Path.cwd(),
        Path.cwd() / "tools" / "sticker",
        Path.cwd() / "tools" / "stickers",
        Path.cwd() / "sticker",
        Path.cwd() / "stickers",
    ]
    for candidate in candidates:
        if (candidate / "manifest.csv").exists() or candidate.name in {"sticker", "stickers"}:
            return candidate
    return candidates[1]


ROOT = resolve_root()
OUT_STICKERS = ROOT / "clean" / "stickers"
OUT_REFERENCES = ROOT / "clean" / "references"
MANIFEST_MD = ROOT / "manifest.md"
MANIFEST_CSV = ROOT / "manifest.csv"
CONTACT_SHEET = ROOT / "clean" / "_contact_sheet_clean.png"


@dataclass(frozen=True)
class Asset:
    source: str
    target: str
    category: str
    mood: str
    note: str
    remove_bg: bool = True


ASSETS: list[Asset] = [
    Asset("13369aa3-e62f-49f1-a0b0-03db17a613ae_副本.png", "01-sleepy-shark-hug.png", "sticker", "sleepy", "抱着鲨鱼玩偶睡觉"),
    Asset("13369aa3-e62f-49f1-a0b0-03db17a613ae_副本2.png", "02-selfie-sparkle.png", "sticker", "confident", "举手机自拍，旁边有星光"),
    Asset("13369aa3-e62f-49f1-a0b0-03db17a613ae_副本3.png", "03-gym-shaker-smile.png", "sticker", "energetic", "手拿摇摇杯，像健身打卡"),
    Asset("13369aa3-e62f-49f1-a0b0-03db17a613ae_副本4.png", "04-flex-wink-heart.png", "sticker", "playful", "秀肌肉并眨眼，旁边有爱心"),
    Asset("ChatGPT Image 2026年5月21日 23_49_32.png", "05-watercolor-portrait.png", "sticker", "gentle", "水彩风半身肖像"),
    Asset("ChatGPT Image 2026年5月21日 23_49_32_副本.png", "06-smile-sparkle.png", "sticker", "happy", "开心微笑，旁边有小星星"),
    Asset("ChatGPT Image 2026年5月21日 23_49_32_副本2.png", "07-wink-thumbs-heart.png", "sticker", "playful", "眨眼比赞，旁边有爱心"),
    Asset("ChatGPT Image 2026年5月21日 23_49_32_副本3.png", "08-laugh-hand-behind-head.png", "sticker", "relaxed", "大笑挠头，轻松感"),
    Asset("ChatGPT Image 2026年5月21日 23_49_32_副本4.png", "09-coffee-hoodie.png", "sticker", "cozy", "穿卫衣抱着热咖啡"),
    Asset("ChatGPT Image 2026年5月21日 23_49_32_副本5.png", "10-notebook-study.png", "sticker", "focused", "趴桌写字学习，旁边有书"),
    Asset("ChatGPT Image 2026年5月21日 23_49_32_副本6.png", "11-wink-dumbbell.png", "sticker", "energetic", "单手举哑铃并眨眼"),
    Asset("ChatGPT Image 2026年5月21日 23_49_32_副本7.png", "12-dinosaur-hug.png", "sticker", "cute", "穿恐龙连体衣抱着玩偶"),
    Asset("ChatGPT Image 2026年5月21日 23_50_51_副本.png", "13-heart-cheek-rest.png", "sticker", "warm", "托脸微笑，旁边有爱心"),
    Asset("ChatGPT Image 2026年5月21日 23_50_51_副本2.png", "14-beach-peace-sunglasses.png", "sticker", "vacation", "戴墨镜比耶，海边背景"),
    Asset("ChatGPT Image 2026年5月21日 23_50_51_副本3.png", "15-wink-milk-tea.png", "sticker", "casual", "眨眼喝奶茶"),
    Asset("ChatGPT Image 2026年5月21日 23_50_51_副本4.png", "16-dumbbell-grin.png", "sticker", "energetic", "举哑铃露齿笑"),
    Asset("ChatGPT Image 2026年5月21日 23_50_51_副本5.png", "17-bear-hoodie-cute.png", "sticker", "cute", "穿熊熊连帽装"),
    Asset("ChatGPT Image 2026年5月21日 23_50_51_副本6.png", "18-night-coding-laptop.png", "sticker", "focused", "夜晚抱电脑写代码"),
    Asset("ChatGPT Image 2026年5月21日 23_50_51_副本7.png", "19-simple-portrait-green.png", "sticker", "neutral", "简洁头像，浅绿色圆底"),
    Asset("ChatGPT Image 2026年5月21日 23_50_51_副本8.png", "20-laugh-black-tee.png", "sticker", "happy", "穿黑 T 大笑"),
    Asset("Gemini_Generated_Image_6ur7vj6ur7vj6ur7_副本.png", "21-cat-rider.png", "sticker", "fun", "骑在大猫背上"),
    Asset("Gemini_Generated_Image_6ur7vj6ur7vj6ur7_副本2.png", "22-rhino-rider.png", "sticker", "adventure", "骑在犀牛背上"),
    Asset("Gemini_Generated_Image_6ur7vj6ur7vj6ur7_副本3.png", "23-pegasus-rider.png", "sticker", "dreamy", "骑在飞马背上"),
    Asset("Gemini_Generated_Image_6ur7vj6ur7vj6ur7_副本4.png", "24-elephant-rider.png", "sticker", "joyful", "骑大象，旁边有地球"),
    Asset("Gemini_Generated_Image_ie14odie14odie14_副本.png", "25-server-ops-laptop.png", "sticker", "builder", "坐在服务器上操作电脑"),
    Asset("Gemini_Generated_Image_ie14odie14odie14_副本2.png", "26-maker-workbench.png", "sticker", "maker", "坐在工作台前动手制作"),
    Asset("Gemini_Generated_Image_ie14odie14odie14_副本3.png", "27-swift-laptop-ghost.png", "sticker", "builder", "抱着笔记本，旁边有幽灵气泡"),
    Asset("Gemini_Generated_Image_ie14odie14odie14_副本4.png", "28-ios-dev-multiscreen.png", "sticker", "builder", "多屏工作台上的 iOS 开发形象"),
    Asset("Gemini_Generated_Image_ie14odie14odie14_副本5.png", "29-vr-gadget-hacker.png", "sticker", "futuristic", "戴 VR 眼镜摆弄硬件"),
    Asset("Gemini_Generated_Image_jdqxicjdqxicjdqx_副本.png", "30-astronaut-float.png", "sticker", "dreamy", "宇航员漂浮造型"),
    Asset("Gemini_Generated_Image_jdqxicjdqxicjdqx_副本2.png", "31-painter-easel.png", "sticker", "creative", "站在画架前画画"),
    Asset("Gemini_Generated_Image_jdqxicjdqxicjdqx_副本3.png", "32-chef-ramen.png", "sticker", "playful", "厨师造型端着拉面"),
    Asset("Gemini_Generated_Image_jdqxicjdqxicjdqx_副本4.png", "33-travel-camera-backpack.png", "sticker", "travel", "背包旅行，挂着相机"),
    Asset("Gemini_Generated_Image_m2dhqtm2dhqtm2dh.png", "34-wink-thumbs-up.png", "sticker", "approved", "眨眼比赞"),
    Asset("Gemini_Generated_Image_m2dhqtm2dhqtm2dh_副本.png", "35-surprised-cheek.png", "sticker", "surprised", "捂脸惊讶"),
    Asset("Gemini_Generated_Image_m2dhqtm2dhqtm2dh_副本2.png", "36-victory-jump.png", "sticker", "celebration", "开心跳起庆祝"),
    Asset("Gemini_Generated_Image_m2dhqtm2dhqtm2dh_副本3.png", "37-winter-scarf.png", "sticker", "winter", "围巾毛线帽冬日造型"),
    Asset("Gemini_Generated_Image_m2dhqtm2dhqtm2dh_副本4.png", "38-ice-cream-happy.png", "sticker", "happy", "拿着冰淇淋开怀笑"),
    Asset("Gemini_Generated_Image_m2dhqtm2dhqtm2dh_副本5.png", "39-reading-book.png", "sticker", "calm", "捧书阅读"),
    Asset("IMG_9720.jpg", "40-pricing-table-reference-01.png", "reference", "reference", "价格表截图素材", remove_bg=False),
    Asset("IMG_9721.jpg", "41-pricing-table-reference-02.png", "reference", "reference", "价格表截图素材", remove_bg=False),
    Asset("sticker.png", "42-oh-no-shrug.png", "sticker", "confused", "摊手说 oh no"),
    Asset("sticker_副本.png", "43-hello-wave.png", "sticker", "friendly", "挥手打招呼 Hello"),
    Asset("sticker_副本2.png", "44-awesome-thumbs-up.png", "sticker", "approved", "竖起大拇指 Awesome"),
    Asset("sticker_副本3.png", "45-thanks-heart.png", "sticker", "grateful", "抱着爱心说 Thanks"),
    Asset("sticker_副本4.png", "46-touched-tears.png", "sticker", "moved", "感动到流泪"),
    Asset("sticker_副本5.png", "47-thinking-question.png", "sticker", "thinking", "手托下巴，头顶问号"),
    Asset("sticker_副本6.png", "48-sleeping-pillow.png", "sticker", "sleepy", "趴枕头睡觉"),
    Asset("sticker_副本7.png", "49-milk-tea-sip.png", "sticker", "casual", "捧着奶茶喝"),
    Asset("sticker_副本8.png", "50-gaming-controller.png", "sticker", "gaming", "双手拿游戏手柄"),
]


def ensure_dirs() -> None:
    OUT_STICKERS.mkdir(parents=True, exist_ok=True)
    OUT_REFERENCES.mkdir(parents=True, exist_ok=True)


def is_near_white(pixel: tuple[int, int, int, int], threshold: int = 245) -> bool:
    r, g, b, a = pixel
    return a > 0 and r >= threshold and g >= threshold and b >= threshold


def clear_edge_background(img: Image.Image) -> Image.Image:
    rgba = img.convert("RGBA")
    w, h = rgba.size
    pixels = rgba.load()
    alpha = Image.new("L", (w, h), 255)
    alpha_px = alpha.load()
    queue: deque[tuple[int, int]] = deque()
    seen: set[tuple[int, int]] = set()

    def push(x: int, y: int) -> None:
        if (x, y) in seen:
            return
        seen.add((x, y))
        if is_near_white(pixels[x, y]):
            queue.append((x, y))

    for x in range(w):
        push(x, 0)
        push(x, h - 1)
    for y in range(h):
        push(0, y)
        push(w - 1, y)

    while queue:
        x, y = queue.popleft()
        if alpha_px[x, y] == 0:
            continue
        alpha_px[x, y] = 0
        for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            if 0 <= nx < w and 0 <= ny < h and (nx, ny) not in seen:
                seen.add((nx, ny))
                if is_near_white(pixels[nx, ny]):
                    queue.append((nx, ny))

    rgba.putalpha(alpha)
    return rgba


def crop_with_padding(img: Image.Image, padding: int = 18) -> Image.Image:
    alpha = img.getchannel("A") if "A" in img.getbands() else None
    bbox = alpha.getbbox() if alpha else img.getbbox()
    if bbox is None:
        return img

    left, top, right, bottom = bbox
    left = max(0, left - padding)
    top = max(0, top - padding)
    right = min(img.width, right + padding)
    bottom = min(img.height, bottom + padding)
    return img.crop((left, top, right, bottom))


def process_asset(asset: Asset) -> Path:
    src = ROOT / asset.source
    dst_root = OUT_REFERENCES if asset.category == "reference" else OUT_STICKERS
    dst = dst_root / asset.target

    img = Image.open(src)
    if asset.remove_bg:
        if "A" in img.getbands():
            img = img.convert("RGBA")
        else:
            img = clear_edge_background(img)
        img = crop_with_padding(img)
        img.save(dst, format="PNG")
    else:
        img = img.convert("RGBA")
        img.save(dst, format="PNG")
    return dst


def write_manifest(outputs: Iterable[tuple[Asset, Path]]) -> None:
    rows = list(outputs)

    md_lines = [
        "# Sticker Manifest",
        "",
        "| # | Source | Output | Category | Mood | Note |",
        "|---|---|---|---|---|---|",
    ]
    csv_lines = ["index,source,output,category,mood,note"]

    for idx, (asset, out_path) in enumerate(rows, 1):
        rel_out = out_path.relative_to(ROOT)
        md_lines.append(
            f"| {idx:02d} | {asset.source} | {rel_out.as_posix()} | {asset.category} | {asset.mood} | {asset.note} |"
        )
        csv_lines.append(
            f'{idx:02d},"{asset.source}","{rel_out.as_posix()}","{asset.category}","{asset.mood}","{asset.note}"'
        )

    MANIFEST_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    MANIFEST_CSV.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")


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
        canvas = Image.new("RGBA", (thumb, thumb), (250, 250, 250, 255))
        preview = img.copy()
        preview.thumbnail((thumb - 16, thumb - 16))
        px = (thumb - preview.width) // 2
        py = (thumb - preview.height) // 2
        canvas.alpha_composite(preview, (px, py))

        x = margin + ((i - 1) % cols) * (thumb + margin)
        y = margin + ((i - 1) // cols) * (thumb + label_h + margin)
        sheet.alpha_composite(canvas, (x, y + label_h))
        draw.rounded_rectangle((x, y, x + thumb, y + 32), radius=10, fill=(24, 24, 24, 255))
        draw.text((x + 8, y + 7), path.name[:22], fill="white", font=font)
        draw.rectangle((x, y + label_h, x + thumb, y + label_h + thumb), outline=(220, 220, 220, 255), width=1)

    CONTACT_SHEET.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(CONTACT_SHEET)


def main() -> None:
    ensure_dirs()
    outputs: list[tuple[Asset, Path]] = []
    for asset in ASSETS:
        outputs.append((asset, process_asset(asset)))

    write_manifest(outputs)
    build_contact_sheet([path for _, path in outputs if path.parent == OUT_STICKERS])
    print(f"Processed {len(outputs)} assets")
    print(f"Manifest: {MANIFEST_MD}")
    print(f"Contact sheet: {CONTACT_SHEET}")


if __name__ == "__main__":
    main()
