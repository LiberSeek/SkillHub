from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
CHATGPT_PROXY = SCRIPT_DIR / "chatgpt_proxy.py"
GEMINI_WEB = SCRIPT_DIR / "gemini_web.ts"


def main() -> int:
    parser = argparse.ArgumentParser(description="Route image generation to configured backend")
    parser.add_argument("--backend", default=os.environ.get("CONTENT_DESIGNER_DEFAULT_IMAGE_BACKEND", "chatgpt-proxy"))
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--image", required=True)
    parser.add_argument("--model", default="")
    parser.add_argument("--size", default="")
    parser.add_argument("--quality", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--reference", "--ref", action="append", default=[])
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("extra", nargs=argparse.REMAINDER)
    args = parser.parse_args()

    backend = args.backend.strip().lower()

    if backend == "manual-compose":
        print("manual-compose selected: skip model generation and use cover composition scripts")
        return 0

    if backend == "chatgpt-proxy":
        cmd = [sys.executable, str(CHATGPT_PROXY), "--prompt", args.prompt, "--image", args.image]
        if args.model:
            cmd.extend(["--model", args.model])
        if args.size:
            cmd.extend(["--size", args.size])
        if args.quality:
            cmd.extend(["--quality", args.quality])
        if args.base_url:
            cmd.extend(["--base-url", args.base_url])
        if args.api_key:
            cmd.extend(["--api-key", args.api_key])
        for ref in args.reference:
            cmd.extend(["--reference", ref])
        if args.dry_run:
            cmd.append("--dry-run")
        cmd.extend(args.extra)
        return subprocess.call(cmd)

    if backend == "gemini-web":
        bun = shutil.which("bun")
        if bun:
            runtime = [bun]
        else:
            npx = shutil.which("npx")
            if not npx:
                print("Missing bun or npx runtime for gemini-web backend", file=sys.stderr)
                return 2
            runtime = [npx, "-y", "bun"]

        cmd = runtime + [str(GEMINI_WEB), "--prompt", args.prompt, "--image", args.image]
        if args.model:
            cmd.extend(["--model", args.model])
        for ref in args.reference:
            cmd.extend(["--reference", ref])
        cmd.extend(args.extra)
        return subprocess.call(cmd)

    print(f"Unsupported backend: {backend}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
