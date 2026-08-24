#!/usr/bin/env python3
"""Generate images with OpenAI-compatible, Grok, or Gemini image APIs."""

from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import shlex
import sys
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


DEFAULT_MODEL = "gpt-image-2"
DEFAULT_SIZE = "auto"
CONFIG_PATH = Path.home() / ".codex" / "sk-image-creater.env"
GEMINI_MODELS = {
    "gemini-3-pro-image",
    "gemini-3.1-flash-image",
    "gemini-3.1-flash-lite-image",
}
GROK_MODELS = {
    "grok-imagine-image",
    "grok-imagine-image-quality",
}
GEMINI_ASPECT_RATIOS = {"1:1", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4", "9:16", "16:9", "21:9"}
SIZE_ALIASES = {
    "square": "1024x1024",
    "1:1": "1024x1024",
    "portrait": "1024x1536",
    "vertical": "1024x1536",
    "tall": "1024x1536",
    "2:3": "1024x1536",
    "3:4": "1024x1536",
    "landscape": "1536x1024",
    "horizontal": "1536x1024",
    "wide": "1536x1024",
    "3:2": "1536x1024",
    "4:3": "1536x1024",
}


def load_env_file(path: Path = CONFIG_PATH) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :].strip()
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue
        try:
            parts = shlex.split(value, comments=False, posix=True)
            os.environ[key] = parts[0] if parts else ""
        except ValueError:
            os.environ[key] = value.strip().strip("'\"")


def normalize_endpoint(base_url: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        raise ValueError("base URL is empty")
    if base.endswith("/v1/images/generations"):
        return base
    if base.endswith("/v1"):
        return f"{base}/images/generations"
    return f"{base}/v1/images/generations"


def normalize_gemini_model(model: str) -> str:
    normalized = model.strip()
    return normalized[: -len("-preview")] if normalized.endswith("-preview") else normalized


def is_gemini_image_model(model: str) -> bool:
    return normalize_gemini_model(model) in GEMINI_MODELS


def normalize_grok_model(model: str) -> str:
    return model.strip()


def is_grok_image_model(model: str) -> bool:
    return normalize_grok_model(model) in GROK_MODELS


def protocol_mode(model: str) -> str:
    if is_gemini_image_model(model):
        return "gemini"
    if is_grok_image_model(model):
        return "grok"
    return "openai-compatible"


def normalize_gemini_endpoint(base_url: str, model: str) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        raise ValueError("base URL is empty")
    marker = "/v1beta/models/"
    if marker in base:
        base = base.split(marker, 1)[0]
    elif base.endswith("/v1beta"):
        base = base[: -len("/v1beta")]
    elif "/v1/images/" in base:
        base = base.split("/v1/images/", 1)[0]
    elif base.endswith("/v1"):
        base = base[: -len("/v1")]
    return f"{base}/v1beta/models/{normalize_gemini_model(model)}:generateContent"


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        return Path(args.prompt_file).read_text(encoding="utf-8").strip()
    if args.prompt:
        return args.prompt.strip()
    raise ValueError("provide --prompt or --prompt-file")


def load_extra_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--extra-json is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--extra-json must be a JSON object")
    return parsed


def normalize_size(value: str | None) -> str | None:
    if value is None:
        return DEFAULT_SIZE

    normalized = value.strip().lower().replace("×", "x")
    if not normalized:
        return DEFAULT_SIZE
    if normalized in {"none", "omit", "default"}:
        return None
    if normalized in {"auto", "auto-size"}:
        return "auto"
    if normalized in SIZE_ALIASES:
        return SIZE_ALIASES[normalized]
    if re.match(r"^\d{2,5}x\d{2,5}$", normalized):
        return normalized

    raise ValueError(
        "--size must be auto, an alias like square/portrait/landscape, "
        "a ratio like 1:1/3:4/4:3, or WIDTHxHEIGHT"
    )


def normalize_gemini_aspect_ratio(value: str | None) -> str | None:
    if value is None or value.strip().lower() in {"", "auto", "auto-size", "omit", "none", "default"}:
        return None
    normalized = value.strip().lower().replace("×", "x")
    aliases = {
        "square": "1:1", "portrait": "2:3", "vertical": "2:3", "tall": "2:3",
        "landscape": "3:2", "horizontal": "3:2", "wide": "3:2",
        "1024x1024": "1:1", "1024x1536": "2:3", "1536x1024": "3:2",
    }
    normalized = aliases.get(normalized, normalized)
    if normalized not in GEMINI_ASPECT_RATIOS:
        raise ValueError("Gemini --size must be a supported ratio, such as 1:1, 2:3, or 16:9")
    return normalized


def normalize_gemini_image_size(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if normalized in {"", "AUTO", "OMIT", "NONE", "DEFAULT"}:
        return None
    if normalized not in {"512", "1K", "2K", "4K"}:
        raise ValueError("Gemini --image-size must be one of 512, 1K, 2K, or 4K")
    return normalized


def build_gemini_payload(prompt: str, size: str | None, image_size: str | None, extra: dict[str, Any], images: list[Path] | None = None) -> dict[str, Any]:
    parts: list[dict[str, Any]] = [{"text": prompt}]
    for image in images or []:
        if image.stat().st_size > 20 * 1024 * 1024:
            raise ValueError(f"Gemini reference image exceeds 20 MB: {image}")
        parts.append({"inlineData": {"mimeType": mimetypes.guess_type(image.name)[0] or "application/octet-stream", "data": base64.b64encode(image.read_bytes()).decode("ascii")}})
    image_config: dict[str, Any] = {}
    aspect_ratio = normalize_gemini_aspect_ratio(size)
    if aspect_ratio:
        image_config["aspectRatio"] = aspect_ratio
    quality = normalize_gemini_image_size(image_size)
    if quality:
        image_config["imageSize"] = quality
    payload: dict[str, Any] = {"contents": [{"parts": parts}]}
    if image_config:
        payload["generationConfig"] = {"imageConfig": image_config}
    payload.update(extra)
    return payload


def request_json(endpoint: str, api_key: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
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
        raise RuntimeError(f"HTTP {exc.code} from image API: {raw}") from exc
    except URLError as exc:
        raise RuntimeError(f"failed to reach image API: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"image API returned non-JSON response: {raw[:500]}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("image API returned JSON that is not an object")
    return parsed


def suffix_from_mime(mime_type: str | None, fallback: str = ".png") -> str:
    if not mime_type:
        return fallback
    suffix = mimetypes.guess_extension(mime_type.split(";")[0].strip())
    if suffix == ".jpe":
        return ".jpg"
    return suffix or fallback


def decode_data_url(value: str) -> tuple[bytes, str]:
    match = re.match(r"^data:([^;,]+)?(?:;[^,]*)?,(.*)$", value, flags=re.DOTALL)
    if not match:
        raise ValueError("not a data URL")
    mime_type, encoded = match.groups()
    if ";base64," in value[: value.find(",") + 1]:
        return base64.b64decode(encoded), suffix_from_mime(mime_type)
    return encoded.encode("utf-8"), suffix_from_mime(mime_type, ".txt")


def download_url(url: str, timeout: int) -> tuple[bytes, str]:
    request = Request(url, headers={"User-Agent": "sk-image-creater/1.0"})
    with urlopen(request, timeout=timeout) as response:
        data = response.read()
        content_type = response.headers.get("Content-Type")
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix
    return data, suffix if suffix else suffix_from_mime(content_type)


def save_outputs(response: dict[str, Any], outdir: Path, timeout: int) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    saved: list[Path] = []
    items = response.get("data")

    if isinstance(items, list):
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue

            image_bytes: bytes | None = None
            suffix = ".png"

            if isinstance(item.get("b64_json"), str):
                image_bytes = base64.b64decode(item["b64_json"])
            elif isinstance(item.get("url"), str):
                image_bytes, suffix = download_url(item["url"], timeout)
            elif isinstance(item.get("image"), str) and item["image"].startswith("data:"):
                image_bytes, suffix = decode_data_url(item["image"])

            if image_bytes is None:
                continue

            path = outdir / f"image-{stamp}-{index}{suffix}"
            path.write_bytes(image_bytes)
            saved.append(path)

    if saved:
        return saved

    path = outdir / f"image-response-{stamp}.json"
    path.write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
    return [path]


def save_gemini_outputs(response: dict[str, Any], outdir: Path) -> list[Path]:
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    saved: list[Path] = []
    for candidate in response.get("candidates", []):
        content = candidate.get("content") if isinstance(candidate, dict) else None
        if not isinstance(content, dict):
            continue
        for part in content.get("parts", []):
            inline_data = part.get("inlineData") if isinstance(part, dict) else None
            if not isinstance(inline_data, dict) or not isinstance(inline_data.get("data"), str):
                continue
            suffix = suffix_from_mime(inline_data.get("mimeType"))
            path = outdir / f"image-{stamp}-{len(saved) + 1}{suffix}"
            path.write_bytes(base64.b64decode(inline_data["data"]))
            saved.append(path)
    if saved:
        return saved
    path = outdir / f"image-response-{stamp}.json"
    path.write_text(json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8")
    return [path]


def build_parser() -> argparse.ArgumentParser:
    load_env_file()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default=os.getenv("SK_IMAGE_BASE_URL") or os.getenv("OPENAI_BASE_URL"))
    parser.add_argument("--api-key", default=os.getenv("SK_IMAGE_API_KEY") or os.getenv("OPENAI_API_KEY"))
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument(
        "--size",
        help=(
            "image size: auto, square, portrait, landscape, common ratios "
            "like 1:1/3:4/4:3, WIDTHxHEIGHT, or omit"
        ),
    )
    parser.add_argument("--image-size", help="Gemini resolution tier: 512, 1K, 2K, or 4K")
    parser.add_argument("--n", type=int)
    parser.add_argument("--outdir", default="generated-images")
    parser.add_argument("--extra-json", help="JSON object merged into the request body")
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

        prompt = read_prompt(args)
        extra = load_extra_json(args.extra_json)
        mode = protocol_mode(args.model)
        if mode == "gemini":
            if args.n not in {None, 1}:
                raise ValueError("Gemini image models support only --n 1")
            endpoint = normalize_gemini_endpoint(args.base_url, args.model)
            payload = build_gemini_payload(prompt, args.size, args.image_size, extra)
        else:
            endpoint = normalize_endpoint(args.base_url)
            payload = {"model": args.model, "prompt": prompt}
            size = normalize_size(args.size)
            if size is not None:
                payload["size"] = size
            if args.n is not None:
                payload["n"] = args.n
            payload.update(extra)

        if args.dry_run:
            print(json.dumps({"endpoint": endpoint, "mode": mode, "body": payload}, ensure_ascii=False, indent=2))
            return 0

        response = request_json(endpoint, args.api_key, payload, args.timeout)
        saved = save_gemini_outputs(response, Path(args.outdir)) if mode == "gemini" else save_outputs(response, Path(args.outdir), args.timeout)
        for path in saved:
            print(path.resolve())
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
