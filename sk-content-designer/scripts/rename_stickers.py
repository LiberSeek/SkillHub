from __future__ import annotations

import csv
import os
import shutil
from pathlib import Path


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
MANIFEST = ROOT / "manifest.csv"
RENAMED_STICKERS = ROOT / "renamed" / "stickers"
RENAMED_REFERENCES = ROOT / "renamed" / "references"
RENAMED_MANIFEST_MD = ROOT / "renamed" / "manifest-renamed.md"
RENAMED_MANIFEST_CSV = ROOT / "renamed" / "manifest-renamed.csv"


def ensure_dirs() -> None:
    RENAMED_STICKERS.mkdir(parents=True, exist_ok=True)
    RENAMED_REFERENCES.mkdir(parents=True, exist_ok=True)


def main() -> None:
    ensure_dirs()
    rows: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []

    with MANIFEST.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

    md_lines = [
        "# Renamed Sticker Manifest",
        "",
        "| # | Source | Renamed | Category | Mood | Note |",
        "|---|---|---|---|---|---|",
    ]
    csv_lines = ["index,source,renamed,category,mood,note"]

    for row in rows:
        source = row["source"]
        output = Path(row["output"]).name
        category = row["category"]
        mood = row["mood"]
        note = row["note"]
        src_path = ROOT / source
        if not src_path.exists():
            missing.append(row)
            continue
        dst_root = RENAMED_REFERENCES if category == "reference" else RENAMED_STICKERS
        dst_path = dst_root / output
        shutil.copy2(src_path, dst_path)

        rel_dst = dst_path.relative_to(ROOT)
        md_lines.append(
            f'| {row["index"]} | {source} | {rel_dst.as_posix()} | {category} | {mood} | {note} |'
        )
        csv_lines.append(
            f'{row["index"]},"{source}","{rel_dst.as_posix()}","{category}","{mood}","{note}"'
        )

    RENAMED_MANIFEST_MD.write_text("\n".join(md_lines) + "\n", encoding="utf-8")
    RENAMED_MANIFEST_CSV.write_text("\n".join(csv_lines) + "\n", encoding="utf-8")

    if missing:
        missing_md = ROOT / "renamed" / "missing-from-source.md"
        missing_lines = [
            "# Missing Source Files",
            "",
            "| # | Source | Category | Mood | Note |",
            "|---|---|---|---|---|",
        ]
        for row in missing:
            missing_lines.append(
                f'| {row["index"]} | {row["source"]} | {row["category"]} | {row["mood"]} | {row["note"]} |'
            )
        missing_md.write_text("\n".join(missing_lines) + "\n", encoding="utf-8")

    print(f"Renamed {len(rows) - len(missing)} files")
    print(f"Missing {len(missing)} files")
    print(f"Output root: {ROOT / 'renamed'}")


if __name__ == "__main__":
    main()
