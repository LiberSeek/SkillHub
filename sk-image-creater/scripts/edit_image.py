#!/usr/bin/env python3
"""Generate images from reference images with /v1/images/edits."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import sys
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from generate_image import (
    DEFAULT_MODEL,
    load_env_file,
    load_extra_json,
    normalize_size,
    request_json,
    save_outputs,
)


def normalize_edits_endpoint(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        raise ValueError("base URL is empty")
    if base.endswith("/v1/images/edits"):
        return base
    if base.endswith("/v1/images/generations"):
        return base[: -len("/generations")] + "/edits"
    if base.endswith("/v1"):
        return f"{base}/images/edits"
    return f"{base}/v1/images/edits"


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if args.prompt:
        return args.prompt.strip()
    raise ValueError("provide --prompt or --prompt-file")


def guess_mime(path: Path) -> str:
    return mimetypes.guess_type(str(path))[0] or "application/octet-stream"


def encode_image_for_json(path: Path, mode: str) -> str:
    data = path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    if mode == "base64":
        return encoded
    return f"data:{guess_mime(path)};base64,{encoded}"


def multipart_body(fields: dict[str, Any], images: list[Path], image_field: str) -> tuple[bytes, str]:
    boundary = f"sk-image-creater-{uuid.uuid4().hex}"
    chunks: list[bytes] = []

    def add_text(name: str, value: Any) -> None:
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
        chunks.append(str(value).encode("utf-8"))
        chunks.append(b"\r\n")

    def add_file(name: str, path: Path) -> None:
        chunks.append(f"--{boundary}\r\n".encode("utf-8"))
        chunks.append(
            (
                f'Content-Disposition: form-data; name="{name}"; '
                f'filename="{path.name}"\r\n'
            ).encode("utf-8")
        )
        chunks.append(f"Content-Type: {guess_mime(path)}\r\n\r\n".encode("utf-8"))
        chunks.append(path.read_bytes())
        chunks.append(b"\r\n")

    for key, value in fields.items():
        if value is None:
            continue
        if isinstance(value, (dict, list)):
            add_text(key, json.dumps(value, ensure_ascii=False))
        else:
            add_text(key, value)

    for image in images:
        add_file(image_field, image)

    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks), boundary


def request_multipart_json(
    endpoint: str,
    api_key: str,
    fields: dict[str, Any],
    images: list[Path],
    image_field: str,
    timeout: int,
) -> dict[str, Any]:
    body, boundary = multipart_body(fields, images, image_field)
    request = Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Authorization": f"Bearer {api_key}",
            "User-Agent": "sk-image-creater/1.0",
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from image edits API: {raw}") from exc
    except URLError as exc:
        raise RuntimeError(f"failed to reach image edits API: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"image edits API returned non-JSON response: {raw[:500]}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("image edits API returned JSON that is not an object")
    return parsed


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "model": args.model,
        "prompt": read_prompt(args),
    }
    size = normalize_size(args.size)
    if size is not None:
        payload["size"] = size
    if args.n is not None:
        payload["n"] = args.n
    payload.update(load_extra_json(args.extra_json))
    return payload


def build_json_payload(args: argparse.Namespace, images: list[Path]) -> dict[str, Any]:
    payload = build_payload(args)
    encoded_images = [encode_image_for_json(path, args.json_image_format) for path in images]
    payload[args.image_field] = encoded_images[0] if len(encoded_images) == 1 else encoded_images
    return payload


def summarize_images(images: list[Path]) -> list[dict[str, Any]]:
    return [
        {
            "path": str(path),
            "bytes": path.stat().st_size,
            "mime": guess_mime(path),
        }
        for path in images
    ]


def build_parser() -> argparse.ArgumentParser:
    load_env_file()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("SK_IMAGE_BASE_URL") or os.getenv("OPENAI_BASE_URL"))
    parser.add_argument("--api-key", default=os.getenv("SK_IMAGE_API_KEY") or os.getenv("OPENAI_API_KEY"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--image", action="append", required=True, help="reference image path; repeat for multiple images")
    parser.add_argument("--image-field", default="image", help="multipart/JSON field name for reference image data")
    parser.add_argument("--size", help="auto, square, portrait, landscape, WIDTHxHEIGHT, ratio, or omit")
    parser.add_argument("--n", type=int)
    parser.add_argument("--outdir", default="edited-images")
    parser.add_argument("--extra-json", help="JSON object merged into the request body")
    parser.add_argument("--json", action="store_true", help="send reference images as JSON base64/data URLs instead of multipart")
    parser.add_argument("--json-image-format", choices=["data-url", "base64"], default="data-url")
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if not args.base_url:
            raise ValueError("missing base URL; set SK_IMAGE_BASE_URL or pass --base-url")
        if not args.api_key and not args.dry_run:
            raise ValueError("missing API key; set SK_IMAGE_API_KEY or pass --api-key")

        endpoint = normalize_edits_endpoint(args.base_url)
        images = [Path(path) for path in args.image]
        missing = [str(path) for path in images if not path.exists()]
        if missing:
            raise ValueError(f"reference image not found: {', '.join(missing)}")

        if args.json:
            payload = build_json_payload(args, images)
            if args.dry_run:
                preview = dict(payload)
                preview[args.image_field] = "[base64 image data omitted]"
                print(json.dumps({"endpoint": endpoint, "mode": "json", "body": preview}, ensure_ascii=False, indent=2))
                return 0
            response = request_json(endpoint, args.api_key, payload, args.timeout)
        else:
            fields = build_payload(args)
            if args.dry_run:
                print(
                    json.dumps(
                        {
                            "endpoint": endpoint,
                            "mode": "multipart",
                            "fields": fields,
                            "images": summarize_images(images),
                            "image_field": args.image_field,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            response = request_multipart_json(endpoint, args.api_key, fields, images, args.image_field, args.timeout)

        saved = save_outputs(response, Path(args.outdir), args.timeout)
        for path in saved:
            print(path.resolve())
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
