from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def slugify(text: str) -> str:
    lowered = text.strip().lower()
    slug = re.sub(r"[^\w\u4e00-\u9fff]+", "-", lowered).strip("-")
    return slug or "archetype"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build prompt pack for a personal IP archetype")
    parser.add_argument("--series-root", required=True)
    parser.add_argument("--character", required=True)
    parser.add_argument("--archetype", required=True)
    parser.add_argument("--slug", default="")
    parser.add_argument("--mood", default="")
    parser.add_argument("--scene", default="")
    parser.add_argument("--outfit", default="")
    parser.add_argument("--prop", action="append", default=[])
    parser.add_argument("--style", default="cinematic illustration with stable facial identity")
    args = parser.parse_args()

    slug = args.slug or slugify(args.archetype)
    out_dir = Path(args.series_root) / "archetypes" / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    props = ", ".join(args.prop) if args.prop else "signature prop"
    prompt = (
        f"{args.character} as a {args.archetype}, keep the same face identity, glasses, hairstyle, and calm poetic temperament, "
        f"scene: {args.scene or 'dreamlike narrative setting'}, mood: {args.mood or 'gentle and imaginative'}, "
        f"outfit: {args.outfit or 'identity-matching wardrobe'}, props: {props}, style: {args.style}."
    )

    payload = {
        "character": args.character,
        "archetype": args.archetype,
        "prompt": prompt,
        "style": args.style,
        "mood": args.mood,
        "scene": args.scene,
        "outfit": args.outfit,
        "props": args.prop,
    }

    (out_dir / "prompt-pack.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "prompt-pack.md").write_text(
        f"# {args.character} · {args.archetype}\n\n## Prompt\n\n{prompt}\n",
        encoding="utf-8",
    )
    print(out_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
