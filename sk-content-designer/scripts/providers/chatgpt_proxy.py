from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


def resolve_base_url(explicit: str | None) -> str:
    return (
        explicit
        or os.environ.get("CONTENT_DESIGNER_CHATGPT_BASE_URL")
        or os.environ.get("OPENAI_BASE_URL")
        or ""
    ).rstrip("/")


def resolve_api_key(explicit: str | None) -> str:
    return (
        explicit
        or os.environ.get("CONTENT_DESIGNER_CHATGPT_API_KEY")
        or os.environ.get("OPENAI_API_KEY")
        or ""
    )


def save_image_from_payload(item: dict, out_path: Path) -> None:
    if "b64_json" in item:
        out_path.write_bytes(base64.b64decode(item["b64_json"]))
        return
    if "url" in item:
        with urllib.request.urlopen(item["url"]) as response:
            out_path.write_bytes(response.read())
        return
    raise ValueError("No image payload found in response item")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate image via OpenAI-compatible ChatGPT proxy")
    parser.add_argument("--prompt", required=True, help="Prompt for image generation")
    parser.add_argument("--image", required=True, help="Output image path")
    parser.add_argument("--model", default=os.environ.get("CONTENT_DESIGNER_CHATGPT_IMAGE_MODEL", "gpt-image-1"))
    parser.add_argument("--size", default="1024x1536")
    parser.add_argument("--quality", default="high")
    parser.add_argument("--style", default="")
    parser.add_argument("--base-url", dest="base_url", default="")
    parser.add_argument("--api-key", dest="api_key", default="")
    parser.add_argument("--reference", "--ref", action="append", default=[], help="Reference images to mention in metadata")
    parser.add_argument("--meta", default="", help="Optional sidecar metadata path")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    base_url = resolve_base_url(args.base_url)
    api_key = resolve_api_key(args.api_key)

    if not base_url:
      print("Missing CONTENT_DESIGNER_CHATGPT_BASE_URL / OPENAI_BASE_URL", file=sys.stderr)
      return 2
    if not api_key and not args.dry_run:
      print("Missing CONTENT_DESIGNER_CHATGPT_API_KEY / OPENAI_API_KEY", file=sys.stderr)
      return 2

    payload = {
        "model": args.model,
        "prompt": args.prompt,
        "size": args.size,
        "quality": args.quality,
        "response_format": "b64_json",
    }
    if args.style:
        payload["style"] = args.style

    out_path = Path(args.image)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    metadata = {
        "provider": "chatgpt-proxy",
        "base_url": base_url,
        "model": args.model,
        "size": args.size,
        "quality": args.quality,
        "references": args.reference,
        "prompt": args.prompt,
    }

    if args.meta:
        Path(args.meta).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.dry_run:
        print(json.dumps(metadata, ensure_ascii=False, indent=2))
        return 0

    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url}/images/generations",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request) as response:
            response_payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        print(detail, file=sys.stderr)
        return exc.code or 1

    data = response_payload.get("data") or []
    if not data:
        print(json.dumps(response_payload, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    save_image_from_payload(data[0], out_path)
    print(out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
