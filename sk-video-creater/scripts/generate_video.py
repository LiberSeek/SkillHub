#!/usr/bin/env python3
"""Generate videos with Alibaba DashScope (HappyHorse/Wan), Seedance, or Grok Video APIs."""

from __future__ import annotations

import argparse
import base64
import json
import ipaddress
import mimetypes
import os
import re
import shlex
import socket
import sys
import tempfile
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, Request, build_opener, urlopen


CONFIG_PATH = Path.home() / ".codex" / "sk-video-creater.env"
DEFAULT_MODELS = {
    "happyhorse": "happyhorse-1.1-t2v",
    "wan": "wan3.0-video",
    "seedance": "doubao-seedance-2-0-260128",
    "grok-video": "grok-imagine-video-1.5",
}
MODE_CHOICES = ("auto", "t2v", "i2v", "kf2v", "r2v", "videoedit")
DEFAULT_BASE_URLS = {
    "happyhorse": "https://dashscope.aliyuncs.com",
    "wan": "https://dashscope.aliyuncs.com",
    "seedance": "https://ark.cn-beijing.volces.com",
    "grok-video": "https://api.x.ai",
}
DASHSCOPE_NATIVE_HOSTS = {"dashscope.aliyuncs.com", "dashscope-intl.aliyuncs.com"}
BOFT_GATEWAY_HOSTS = {"api.boft.ai", "api-direct.boft.ai"}
MAX_JSON_RESPONSE_BYTES = 4 * 1024 * 1024
MAX_VIDEO_DOWNLOAD_BYTES = 512 * 1024 * 1024
PROVIDER_ALIASES = {
    "happy-horse": "happyhorse",
    "happyhorse": "happyhorse",
    "wan": "wan",
    "wan-video": "wan",
    "seedance": "seedance",
    "grok": "grok-video",
    "grok-video": "grok-video",
    "xai": "grok-video",
}
API_KEY_ENV_VARS = {
    "happyhorse": ("HAPPYHORSE_API_KEY", "DASHSCOPE_API_KEY"),
    "wan": ("WAN_API_KEY", "DASHSCOPE_API_KEY", "HAPPYHORSE_API_KEY"),
    "seedance": ("SEEDANCE_API_KEY", "ARK_API_KEY"),
    "grok-video": ("GROK_VIDEO_API_KEY", "XAI_API_KEY"),
}
BASE_URL_ENV_VARS = {
    "happyhorse": ("HAPPYHORSE_BASE_URL",),
    "wan": ("WAN_BASE_URL", "HAPPYHORSE_BASE_URL"),
    "seedance": ("SEEDANCE_BASE_URL", "ARK_BASE_URL"),
    "grok-video": ("GROK_VIDEO_BASE_URL", "XAI_BASE_URL"),
}
SUCCESS_STATUSES = {
    "happyhorse": {"SUCCEEDED"},
    "wan": {"SUCCEEDED"},
    "seedance": {"SUCCEEDED"},
    "grok-video": {"DONE"},
}
FAILURE_STATUSES = {
    "happyhorse": {"FAILED", "CANCELED", "CANCELLED", "UNKNOWN"},
    "wan": {"FAILED", "CANCELED", "CANCELLED", "UNKNOWN"},
    "seedance": {"FAILED", "CANCELED", "CANCELLED", "EXPIRED"},
    "grok-video": {"FAILED", "EXPIRED", "CANCELED", "CANCELLED"},
}


def is_dashscope_video_provider(provider: str) -> bool:
    return provider in {"happyhorse", "wan"}


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


def first_env(names: tuple[str, ...]) -> str | None:
    for name in names:
        value = os.getenv(name)
        if value:
            return value
    return None


def canonical_provider(value: str) -> str:
    provider = PROVIDER_ALIASES.get(value.strip().lower())
    if not provider:
        choices = ", ".join(sorted(PROVIDER_ALIASES))
        raise ValueError(f"unsupported provider {value!r}; choose one of: {choices}")
    return provider


def read_prompt(args: argparse.Namespace) -> str:
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text(encoding="utf-8").strip()
    else:
        prompt = (args.prompt or "").strip()
    if not prompt:
        raise ValueError("provide --prompt or --prompt-file")
    return prompt


def load_extra_json(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    raw = value
    if not value.lstrip().startswith("{"):
        candidate = Path(value)
        try:
            if candidate.is_file():
                raw = candidate.read_text(encoding="utf-8")
        except OSError:
            pass
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"--extra-json is not valid JSON: {exc}") from exc
    if not isinstance(parsed, dict):
        raise ValueError("--extra-json must be a JSON object or a path to one")
    return parsed


def deep_merge(target: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = value
    return target


def normalize_resolution(value: str | None, provider: str) -> str | None:
    if not value:
        return None
    normalized = value.strip().lower()
    if normalized not in {"480p", "720p", "1080p"}:
        raise ValueError("--resolution must be 480p, 720p, or 1080p")
    return normalized.upper() if is_dashscope_video_provider(provider) else normalized


def normalize_ratio(value: str | None, provider: str | None = None) -> str | None:
    if not value:
        return None
    aliases = {
        "landscape": "16:9",
        "horizontal": "16:9",
        "portrait": "9:16",
        "vertical": "9:16",
        "square": "1:1",
    }
    normalized = aliases.get(value.strip().lower(), value.strip())
    allowed = {"16:9", "9:16", "1:1"}
    if provider == "wan":
        allowed.add("adaptive")
    if normalized.lower() == "adaptive":
        if provider not in (None, "wan"):
            raise ValueError(f"{provider} does not support adaptive ratio")
        return "adaptive"
    if not re.fullmatch(r"\d{1,2}:\d{1,2}", normalized):
        raise ValueError("--ratio must be adaptive or a ratio such as 16:9, 9:16, or 1:1")
    if normalized not in allowed and provider is not None:
        raise ValueError(f"{provider} supports only {', '.join(sorted(allowed))}")
    width, height = (int(part) for part in normalized.split(":"))
    if width == 0 or height == 0:
        raise ValueError("--ratio components must be positive")
    return normalized


def media_source(value: str, provider: str) -> str:
    if value.startswith(("http://", "https://", "data:")):
        return value
    path = Path(value).expanduser()
    if not path.is_file():
        raise ValueError(f"reference image not found: {path}")
    if is_dashscope_video_provider(provider):
        raise ValueError("DashScope video models require a reachable image URL; upload the local image and pass its URL")
    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def requested_mode(args: argparse.Namespace) -> str:
    if args.mode != "auto":
        return args.mode
    if args.model:
        model = args.model.strip().lower()
        if model.endswith("-video-edit"):
            return "videoedit"
        if model.endswith("-r2v"):
            return "r2v"
        if model.endswith("-i2v"):
            return "i2v"
    if args.video:
        return "videoedit"
    if args.references:
        return "r2v"
    if args.last_frame:
        return "kf2v"
    if args.image or args.first_frame:
        return "i2v"
    return "t2v"


def media_url(value: str, provider: str) -> str:
    return media_source(value, provider)


def build_dashscope_media(args: argparse.Namespace, provider: str, mode: str) -> list[dict[str, str]]:
    first_frame = args.first_frame or args.image
    if mode == "i2v":
        if not first_frame:
            raise ValueError("i2v requires --image or --first-frame")
        return [{"type": "first_frame", "url": media_url(first_frame, provider)}]
    if mode == "kf2v":
        if not first_frame or not args.last_frame:
            raise ValueError("kf2v requires both --first-frame/--image and --last-frame")
        return [
            {"type": "first_frame", "url": media_url(first_frame, provider)},
            {"type": "last_frame", "url": media_url(args.last_frame, provider)},
        ]
    if mode == "r2v":
        if not args.references:
            raise ValueError("r2v requires one or more --reference URLs")
        if len(args.references) > 9:
            raise ValueError("r2v supports at most 9 reference URLs")
        return [{"type": "reference_image", "url": media_url(value, provider)} for value in args.references]
    if mode == "videoedit":
        if not args.video:
            raise ValueError("videoedit requires --video")
        if len(args.references) > 5:
            raise ValueError("videoedit supports at most 5 reference URLs")
        media = [{"type": "video", "url": media_url(args.video, provider)}]
        media.extend({"type": "reference_image", "url": media_url(value, provider)} for value in args.references)
        return media
    return []


def model_for_mode(provider: str, model: str | None, mode: str, has_image: bool) -> str:
    if model:
        return model
    if provider == "wan":
        return DEFAULT_MODELS[provider]
    if provider == "happyhorse":
        if mode == "kf2v":
            raise ValueError("HappyHorse does not support first+last-frame mode; use Wan 3.0")
        if mode == "videoedit":
            return "happyhorse-1.0-video-edit"
        if mode == "r2v":
            return "happyhorse-1.1-r2v"
        if mode == "i2v" or has_image:
            return "happyhorse-1.1-i2v"
    return DEFAULT_MODELS[provider]


def validate_mode_constraints(provider: str, mode: str, model: str, duration: int | None, resolution: str | None) -> None:
    if provider == "happyhorse":
        if resolution == "480P":
            raise ValueError("HappyHorse supports 720p or 1080p; 480p is not available")
        if mode in {"t2v", "i2v", "r2v"} and duration is not None and not 3 <= duration <= 15:
            raise ValueError("HappyHorse t2v/i2v/r2v duration must be between 3 and 15 seconds")
        if mode == "kf2v":
            raise ValueError("HappyHorse does not support first+last-frame mode; use Wan 3.0")


def endpoint(base_url: str, provider: str, task_id: str | None = None) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        raise ValueError("base URL is empty")

    if is_dashscope_video_provider(provider):
        if dashscope_gateway(base_url):
            generations_path = "/v1/videos/generations"
            parsed = urlparse(base)
            path = parsed.path.rstrip("/")
            if path.endswith(generations_path):
                root_path = path[: -len(generations_path)]
            elif path.endswith("/v1"):
                root_path = path[:-3]
            else:
                root_path = path
            root = urlunparse((parsed.scheme, parsed.netloc, root_path.rstrip("/"), "", "", ""))
            return f"{root}{generations_path}/{task_id}" if task_id else f"{root}{generations_path}"
        create_path = "/api/v1/services/aigc/video-generation/video-synthesis"
        if create_path in base:
            root = base.split(create_path, 1)[0]
        elif base.endswith("/api/v1"):
            root = base[: -len("/api/v1")]
        else:
            root = base
        return f"{root}/api/v1/tasks/{task_id}" if task_id else f"{root}{create_path}"

    if provider == "seedance":
        tasks_path = "/api/v3/contents/generations/tasks"
        if tasks_path in base:
            root = base.split(tasks_path, 1)[0]
        elif base.endswith("/api/v3"):
            root = base[: -len("/api/v3")]
        else:
            root = base
        suffix = f"{tasks_path}/{task_id}" if task_id else tasks_path
        return f"{root}{suffix}"

    generations_path = "/v1/videos/generations"
    videos_path = "/v1/videos"
    if generations_path in base:
        root = base.split(generations_path, 1)[0]
    elif base.endswith("/v1"):
        root = base[: -len("/v1")]
    else:
        root = base
    return f"{root}{videos_path}/{task_id}" if task_id else f"{root}{generations_path}"


def dashscope_gateway(base_url: str) -> bool:
    """Recognize BOFT-compatible DashScope gateways."""
    parsed = urlparse(base_url.strip())
    host = (parsed.hostname or "").lower()
    path = parsed.path.rstrip("/")
    return host in BOFT_GATEWAY_HOSTS or (path.endswith("/v1") and host not in DASHSCOPE_NATIVE_HOSTS)


def happyhorse_gateway(base_url: str) -> bool:
    """Backward-compatible alias for callers importing the old helper."""
    return dashscope_gateway(base_url)


def build_payload(args: argparse.Namespace, provider: str) -> dict[str, Any]:
    prompt = read_prompt(args)
    mode = requested_mode(args)
    first_frame = args.first_frame or args.image
    image = media_source(first_frame, provider) if first_frame else None
    ratio = normalize_ratio(args.ratio, provider)
    resolution = normalize_resolution(args.resolution, provider)
    model = model_for_mode(provider, args.model, mode, bool(first_frame))
    validate_mode_constraints(provider, mode, model, args.duration, resolution)

    if is_dashscope_video_provider(provider):
        input_data: dict[str, Any] = {"prompt": prompt}
        media = build_dashscope_media(args, provider, mode)
        if media:
            input_data["media"] = media
        parameters: dict[str, Any] = {}
        if args.duration is not None:
            parameters["duration"] = args.duration
        if ratio:
            parameters["ratio"] = ratio
        if resolution:
            parameters["resolution"] = resolution
        payload: dict[str, Any] = {"model": model, "input": input_data}
        if parameters:
            payload["parameters"] = parameters
        if provider == "happyhorse" and mode == "i2v" and not dashscope_gateway(args.base_url or os.getenv("SK_VIDEO_BASE_URL") or first_env(BASE_URL_ENV_VARS[provider]) or DEFAULT_BASE_URLS[provider]):
            parameters.pop("ratio", None)
        if dashscope_gateway(args.base_url or os.getenv("SK_VIDEO_BASE_URL") or first_env(BASE_URL_ENV_VARS[provider]) or DEFAULT_BASE_URLS[provider]):
            gateway_payload: dict[str, Any] = {"model": model, "prompt": prompt}
            if args.duration is not None:
                gateway_payload["duration"] = args.duration
            if ratio:
                gateway_payload["aspect_ratio"] = ratio
            if resolution:
                gateway_payload["resolution"] = resolution.lower()
            if media:
                gateway_payload["media"] = media
            payload = gateway_payload
    elif provider == "seedance":
        model = model or DEFAULT_MODELS[provider]
        content: list[dict[str, Any]] = [{"type": "text", "text": prompt}]
        if image:
            content.append({"type": "image_url", "image_url": {"url": image}})
        payload = {"model": model, "content": content}
        if args.duration is not None:
            payload["duration"] = args.duration
        if ratio:
            payload["ratio"] = ratio
        if resolution:
            payload["resolution"] = resolution
    else:
        model = model or DEFAULT_MODELS[provider]
        payload = {"model": model, "prompt": prompt}
        if image:
            payload["image"] = {"url": image}
        if args.duration is not None:
            payload["duration"] = args.duration
        if ratio:
            payload["aspect_ratio"] = ratio
        if resolution:
            payload["resolution"] = resolution

    return deep_merge(payload, load_extra_json(args.extra_json))


def request_headers(provider: str, api_key: str) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "User-Agent": "sk-video-creater/1.0",
    }
    if is_dashscope_video_provider(provider):
        headers["X-DashScope-Async"] = "enable"
    return headers


def request_json(
    url: str,
    api_key: str,
    provider: str,
    timeout: int,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
    request = Request(
        url,
        data=body,
        headers=request_headers(provider, api_key),
        method="POST" if payload is not None else "GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = read_limited_response(response, MAX_JSON_RESPONSE_BYTES).decode("utf-8")
    except HTTPError as exc:
        raw = read_limited_response(exc, MAX_JSON_RESPONSE_BYTES).decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {provider}: {raw[:2000]}") from exc
    except URLError as exc:
        raise RuntimeError(f"failed to reach {provider}: {exc}") from exc

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"{provider} returned non-JSON: {raw[:500]}") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError(f"{provider} returned JSON that is not an object")
    return parsed


def read_limited_response(response: Any, limit: int) -> bytes:
    content_length = response.headers.get("Content-Length")
    if content_length and content_length.isdigit() and int(content_length) > limit:
        raise RuntimeError(f"response exceeds the {limit} byte limit")
    data = bytearray()
    while True:
        chunk = response.read(min(64 * 1024, limit - len(data) + 1))
        if not chunk:
            return bytes(data)
        data.extend(chunk)
        if len(data) > limit:
            raise RuntimeError(f"response exceeds the {limit} byte limit")


def task_info(provider: str, response: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    if is_dashscope_video_provider(provider):
        output = response.get("output") if isinstance(response.get("output"), dict) else response
        return output.get("task_id"), output.get("task_status"), output.get("video_url")
    if provider == "seedance":
        content = response.get("content") if isinstance(response.get("content"), dict) else {}
        return response.get("id"), response.get("status"), content.get("video_url")
    video = response.get("video") if isinstance(response.get("video"), dict) else {}
    return response.get("request_id"), response.get("status"), video.get("url")


def gateway_task_info(response: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    """Read the common /v1/videos/generations response envelope."""
    nodes: list[dict[str, Any]] = []
    for value in (response, response.get("data"), response.get("detail"), response.get("result")):
        if isinstance(value, dict):
            nodes.append(value)
    task_id = status = video_url = None
    for node in nodes:
        task_id = task_id or node.get("task_id") or node.get("taskId") or node.get("id")
        status = status or node.get("status") or node.get("task_status")
        result = node.get("result") if isinstance(node.get("result"), dict) else node
        video_url = video_url or node.get("url") or result.get("video_url")
        if not video_url and isinstance(result.get("videos"), list) and result["videos"]:
            first = result["videos"][0]
            video_url = first.get("url") if isinstance(first, dict) else first
    return task_id, status, video_url


def error_summary(response: dict[str, Any]) -> str:
    error = response.get("error")
    if isinstance(error, dict):
        return json.dumps(error, ensure_ascii=False)
    for key in ("message", "code", "request_error"):
        if response.get(key):
            return str(response[key])
    return json.dumps(response, ensure_ascii=False)[:1000]


def poll_task(
    provider: str,
    base_url: str,
    api_key: str,
    task_id: str,
    interval: float,
    poll_timeout: int,
    request_timeout: int,
) -> tuple[dict[str, Any], str | None]:
    deadline = time.monotonic() + poll_timeout
    last_status: str | None = None
    while True:
        try:
            response = request_json(endpoint(base_url, provider, task_id), api_key, provider, request_timeout)
        except RuntimeError as exc:
            if not retryable_poll_error(exc) or time.monotonic() >= deadline:
                raise
            delay = min(max(interval, 1.0), 30.0)
            print(f"{provider} task {task_id}: transient poll error, retrying in {delay:g}s", file=sys.stderr)
            time.sleep(min(delay, max(0.0, deadline - time.monotonic())))
            continue
        if is_dashscope_video_provider(provider) and dashscope_gateway(base_url):
            _, raw_status, video_url = gateway_task_info(response)
        else:
            _, raw_status, video_url = task_info(provider, response)
        status = str(raw_status).upper() if raw_status is not None else None
        if status != last_status:
            print(f"{provider} task {task_id}: {status or 'status unavailable'}", file=sys.stderr)
            last_status = status
        success_statuses = {"COMPLETED", "COMPLETE", "DONE", "FINISHED", "SUCCESS", "SUCCEED", "SUCCEEDED", "READY"} if is_dashscope_video_provider(provider) and dashscope_gateway(base_url) else SUCCESS_STATUSES[provider]
        failure_statuses = {"FAILED", "FAILURE", "ERROR", "CANCELED", "CANCELLED", "TIMEOUT", "REJECTED", "EXPIRED"} if is_dashscope_video_provider(provider) and dashscope_gateway(base_url) else FAILURE_STATUSES[provider]
        if status in success_statuses:
            return response, video_url
        if status in failure_statuses:
            raise RuntimeError(f"{provider} task {task_id} ended as {status}: {error_summary(response)}")
        if status is None:
            raise RuntimeError(f"{provider} task response has no status: {error_summary(response)}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"timed out waiting for {provider} task {task_id}; resume with --task-id {task_id}")
        time.sleep(interval)


def retryable_poll_error(error: RuntimeError) -> bool:
    message = str(error).lower()
    return (
        "failed to reach" in message
        or "timed out" in message
        or "returned non-json" in message
        or any(f"http {status}" in message for status in (408, 425, 429, 500, 502, 503, 504))
    )


def suffix_from_response(url: str, content_type: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix
    if suffix and len(suffix) <= 8:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";", 1)[0].strip())
    return ".mp4" if not guessed else guessed


def validate_download_url(url: str) -> None:
    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname:
        raise RuntimeError("video result URL must use HTTP(S)")
    hostname = parsed.hostname.lower().rstrip(".")
    if hostname == "localhost" or hostname.endswith(".local"):
        raise RuntimeError("video result URL points to a local host")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        try:
            port = parsed.port or (443 if parsed.scheme.lower() == "https" else 80)
            resolved = socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"video result URL host could not be resolved: {hostname}") from exc
        addresses = {item[4][0] for item in resolved}
        if not addresses:
            raise RuntimeError(f"video result URL host could not be resolved: {hostname}")
        for value in addresses:
            address = ipaddress.ip_address(value)
            if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast or address.is_unspecified:
                raise RuntimeError("video result URL points to a private or reserved address")
        return
    if address.is_private or address.is_loopback or address.is_link_local or address.is_reserved or address.is_multicast or address.is_unspecified:
        raise RuntimeError("video result URL points to a private or reserved address")


class SafeRedirectHandler(HTTPRedirectHandler):
    def redirect_request(self, req: Request, fp: Any, code: int, msg: str, headers: Any, newurl: str) -> Request | None:
        validate_download_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def download_video(url: str, outdir: Path, provider: str, task_id: str, timeout: int) -> Path:
    validate_download_url(url)
    request = Request(url, headers={"User-Agent": "sk-video-creater/1.0"})
    outdir.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "-", task_id)[:48]
    suffix = ".mp4"
    path = outdir / f"{provider}-{safe_id}{suffix}"
    temporary_path: Path | None = None
    try:
        opener = build_opener(SafeRedirectHandler())
        with opener.open(request, timeout=timeout) as response:
            validate_download_url(response.geturl())
            content_type = response.headers.get("Content-Type")
            media_type = (content_type or "").split(";", 1)[0].strip().lower()
            if media_type and not media_type.startswith("video/") and media_type != "application/octet-stream":
                raise RuntimeError(f"video result has unexpected content type: {media_type}")
            content_length = response.headers.get("Content-Length")
            if content_length and content_length.isdigit() and int(content_length) > MAX_VIDEO_DOWNLOAD_BYTES:
                raise RuntimeError(f"video exceeds the {MAX_VIDEO_DOWNLOAD_BYTES} byte limit")
            suffix = suffix_from_response(response.geturl(), content_type)
            path = outdir / f"{provider}-{safe_id}{suffix}"
            with tempfile.NamedTemporaryFile(dir=outdir, prefix=f".{safe_id}-", suffix=".part", delete=False) as temporary:
                temporary_path = Path(temporary.name)
                total = 0
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_VIDEO_DOWNLOAD_BYTES:
                        raise RuntimeError(f"video exceeds the {MAX_VIDEO_DOWNLOAD_BYTES} byte limit")
                    temporary.write(chunk)
        os.replace(temporary_path, path)
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"video was generated but download failed: {exc}; URL: {url}") from exc
    except Exception:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
        raise
    return path.resolve()


def redact_data_urls(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: redact_data_urls(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_data_urls(item) for item in value]
    if isinstance(value, str) and value.startswith("data:"):
        return value.split(",", 1)[0] + ",[base64 data omitted]"
    return value


def resolve_configuration(args: argparse.Namespace, provider: str) -> tuple[str, str | None]:
    base_url = (
        args.base_url
        or os.getenv("SK_VIDEO_BASE_URL")
        or first_env(BASE_URL_ENV_VARS[provider])
        or DEFAULT_BASE_URLS[provider]
    )
    api_key = args.api_key or os.getenv("SK_VIDEO_API_KEY") or first_env(API_KEY_ENV_VARS[provider])
    return base_url, api_key


def build_parser() -> argparse.ArgumentParser:
    load_env_file()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--provider", required=True, help="happyhorse, wan, seedance, or grok-video")
    parser.add_argument("--base-url", help="provider API base URL or full create endpoint")
    parser.add_argument("--api-key", help="runtime API key; prefer environment variables")
    parser.add_argument("--model", help="provider model name; defaults depend on provider and input mode")
    parser.add_argument("--mode", choices=MODE_CHOICES, default="auto", help="auto, t2v, i2v, kf2v, r2v, or videoedit")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--image", help="backward-compatible alias for --first-frame")
    parser.add_argument("--first-frame", help="first-frame image URL")
    parser.add_argument("--last-frame", help="last-frame image URL for Wan 3.0 keyframe transitions")
    parser.add_argument("--reference", dest="references", action="append", default=[], help="reference image URL; repeat for r2v or videoedit")
    parser.add_argument("--video", help="input video URL for videoedit")
    parser.add_argument("--duration", type=int, help="video duration in seconds")
    parser.add_argument("--ratio", help="aspect ratio, for example adaptive, 16:9, 9:16, or 1:1")
    parser.add_argument("--resolution", help="480p, 720p, or 1080p")
    parser.add_argument("--extra-json", help="JSON object or JSON file merged into the provider payload")
    parser.add_argument("--outdir", default="generated-videos")
    parser.add_argument("--task-id", help="resume polling an existing provider task")
    parser.add_argument("--submit-only", action="store_true", help="submit and print the task ID without polling")
    parser.add_argument("--no-download", action="store_true", help="print the result URL instead of downloading it")
    parser.add_argument("--poll-interval", type=float, default=5.0)
    parser.add_argument("--poll-timeout", type=int, default=1200)
    parser.add_argument("--request-timeout", type=int, default=120)
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        provider = canonical_provider(args.provider)
        mode = requested_mode(args)
        if args.duration is not None and args.duration <= 0:
            raise ValueError("--duration must be positive")
        if provider == "grok-video" and args.duration is not None and args.duration > 15:
            raise ValueError("Grok Video duration must be between 1 and 15 seconds")
        if provider == "wan" and args.duration is not None and args.duration > 30:
            raise ValueError("Wan 3.0 duration must be between 1 and 30 seconds")
        if provider == "happyhorse" and mode == "videoedit" and not args.model:
            args.model = "happyhorse-1.0-video-edit"
        if args.poll_interval <= 0 or args.poll_timeout <= 0 or args.request_timeout <= 0:
            raise ValueError("timeouts and poll interval must be positive")
        if args.task_id and args.submit_only:
            raise ValueError("--task-id and --submit-only cannot be used together")

        base_url, api_key = resolve_configuration(args, provider)
        if args.task_id:
            if args.dry_run:
                print(json.dumps({"provider": provider, "query_endpoint": endpoint(base_url, provider, args.task_id)}, indent=2))
                return 0
            task_id = args.task_id
        else:
            payload = build_payload(args, provider)
            if args.dry_run:
                preview = {
                    "provider": provider,
                    "create_endpoint": endpoint(base_url, provider),
                    "query_endpoint_template": endpoint(base_url, provider, "{task_id}"),
                    "headers": {key: value for key, value in request_headers(provider, "[redacted]").items() if key != "Authorization"},
                    "body": redact_data_urls(payload),
                }
                print(json.dumps(preview, ensure_ascii=False, indent=2))
                return 0
            if not api_key:
                names = ", ".join(("SK_VIDEO_API_KEY",) + API_KEY_ENV_VARS[provider])
                raise ValueError(f"missing API key; set one of {names} or pass --api-key")
            response = request_json(endpoint(base_url, provider), api_key, provider, args.request_timeout, payload)
            if is_dashscope_video_provider(provider) and dashscope_gateway(base_url):
                task_id, _, immediate_url = gateway_task_info(response)
            else:
                task_id, _, immediate_url = task_info(provider, response)
            if not task_id:
                raise RuntimeError(f"{provider} create response has no task ID: {error_summary(response)}")
            if args.submit_only:
                print(task_id)
                return 0
            if immediate_url:
                video_url = immediate_url
                final_response = response
            else:
                final_response, video_url = poll_task(
                    provider,
                    base_url,
                    api_key,
                    task_id,
                    args.poll_interval,
                    args.poll_timeout,
                    args.request_timeout,
                )

        if args.task_id:
            if not api_key:
                names = ", ".join(("SK_VIDEO_API_KEY",) + API_KEY_ENV_VARS[provider])
                raise ValueError(f"missing API key; set one of {names} or pass --api-key")
            final_response, video_url = poll_task(
                provider,
                base_url,
                api_key,
                task_id,
                args.poll_interval,
                args.poll_timeout,
                args.request_timeout,
            )

        if not video_url:
            outdir = Path(args.outdir)
            outdir.mkdir(parents=True, exist_ok=True)
            path = (outdir / f"{provider}-{task_id}-response.json").resolve()
            path.write_text(json.dumps(final_response, ensure_ascii=False, indent=2), encoding="utf-8")
            raise RuntimeError(f"task succeeded without a video URL; saved response to {path}")
        if args.no_download:
            print(video_url)
            return 0
        print(download_video(video_url, Path(args.outdir), provider, task_id, args.request_timeout))
        return 0
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
