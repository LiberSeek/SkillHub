from __future__ import annotations

import argparse
import re
from pathlib import Path


def slugify(text: str) -> str:
    lowered = text.strip().lower()
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", lowered).strip("-")
    return slug or "character"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a character sheet for personal IP production")
    parser.add_argument("--series-root", required=True, help="Series root, e.g. personal/series/xiaoxiaoluo-1001-nights")
    parser.add_argument("--name", required=True)
    parser.add_argument("--slug", default="")
    parser.add_argument("--summary", default="")
    parser.add_argument("--trait", action="append", default=[])
    parser.add_argument("--anchor", action="append", default=[])
    parser.add_argument("--reference", action="append", default=[])
    args = parser.parse_args()

    slug = args.slug or slugify(args.name)
    out_dir = Path(args.series_root) / "archetypes" / slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "character-sheet.md"

    traits = "\n".join(f"- {item}" for item in args.trait) or "- 待补充"
    anchors = "\n".join(f"- {item}" for item in args.anchor) or "- 待补充"
    refs = "\n".join(f"- {item}" for item in args.reference) or "- 待补充"

    content = f"""# {args.name}

## 一句话设定

{args.summary or "待补充"}

## 人物锚点

{anchors}

## 气质与关键词

{traits}

## taboo drift

- 不要让脸型漂移太大
- 不要频繁更换眼镜样式
- 不要在同一系列里突然改变年龄感

## 参考图

{refs}

## 推荐下一步

- 先做 2 到 4 张定妆图
- 选 1 张母版锚点图
- 再扩到具体 archetype 场景
"""
    out_file.write_text(content, encoding="utf-8")
    print(out_file)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
