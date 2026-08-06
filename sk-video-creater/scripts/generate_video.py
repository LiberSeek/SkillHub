#!/usr/bin/env python3
"""Generate videos with HappyHorse, Seedance, or Grok Video APIs."""

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


CONFIG_PATH = Path.home() / ".codex" / "sk-video-creater.env"
DEFAULT_MODELS = {
    "happyhorse": "happyhorse-1.1-t2v",
    "seedance": "doubao-seedance-2-0-260128",
    "grok-video": "grok-imagine-video-1.5",
}
DEFAULT_BASE_URLS = {
    "happyhorse": "https://dashscope.aliyuncs.com",
    "seedance": "https://ark.cn-beijing.volces.com",
    "grok-video": "https://api.x.ai",
}
HAPPYHORSE_NATIVE_HOSTS = {"dashscope.aliyuncs.com", "dashscope-intl.aliyuncs.com"}
PROVIDER_ALIASES = {
    "happy-horse": "happyhorse",
    "happyhorse": "happyhorse",
    "seedance": "seedance",
    "grok": "grok-video",
    "grok-video": "grok-video",
    "xai": "grok-video",
}
API_KEY_ENV_VARS = {
    "happyhorse": ("HAPPYHORSE_API_KEY", "DASHSCOPE_API_KEY"),
    "seedance": ("SEEDANCE_API_KEY", "ARK_API_KEY"),
    "grok-video": ("GROK_VIDEO_API_KEY", "XAI_API_KEY"),
}
BASE_URL_ENV_VARS = {
    "happyhorse": ("HAPPYHORSE_BASE_URL",),
    "seedance": ("SEEDANCE_BASE_URL", "ARK_BASE_URL"),
    "grok-video": ("GROK_VIDEO_BASE_URL", "XAI_BASE_URL"),
}
SUCCESS_STATUSES = {
    "happyhorse": {"SUCCEEDED"},
    "seedance": {"SUCCEEDED"},
    "grok-video": {"DONE"},
}
FAILURE_STATUSES = {
    "happyhorse": {"FAILED", "CANCELED", "CANCELLED", "UNKNOWN"},
    "seedance": {"FAILED", "CANCELED", "CANCELLED", "EXPIRED"},
    "grok-video": {"FAILED", "EXPIRED", "CANCELED", "CANCELLED"},
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
    return normalized.upper() if provider == "happyhorse" else normalized


def normalize_ratio(value: str | None) -> str | None:
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
    if not re.fullmatch(r"\d{1,2}:\d{1,2}", normalized):
        raise ValueError("--ratio must be a ratio such as 16:9, 9:16, or 1:1")
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
    if provider == "happyhorse":
        raise ValueError("HappyHorse requires a reachable image URL; upload the local image and pass its URL")
    mime_type = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def endpoint(base_url: str, provider: str, task_id: str | None = None) -> str:
    base = base_url.strip().rstrip("/")
    if not base:
        raise ValueError("base URL is empty")

    if provider == "happyhorse":
        if happyhorse_gateway(base_url):
            root = base[:-3] if base.endswith("/v1") else base
            return f"{root}/v1/videos/generations/{task_id}" if task_id else f"{root}/v1/videos/generations"
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


def happyhorse_gateway(base_url: str) -> bool:
    """Recognize OpenAI-compatible HappyHorse gateways such as api.boft.ai."""
    parsed = urlparse(base_url.strip())
    host = (parsed.hostname or "").lower()
    path = parsed.path.rstrip("/")
    return host == "api.boft.ai" or (path.endswith("/v1") and host not in HAPPYHORSE_NATIVE_HOSTS)


def build_payload(args: argparse.Namespace, provider: str) -> dict[str, Any]:
    prompt = read_prompt(args)
    image = media_source(args.image, provider) if args.image else None
    ratio = normalize_ratio(args.ratio)
    resolution = normalize_resolution(args.resolution, provider)
    model = args.model

    if provider == "happyhorse":
        if not model:
            model = "happyhorse-1.1-i2v" if image else DEFAULT_MODELS[provider]
        input_data: dict[str, Any] = {"prompt": prompt}
        if image:
            input_data["media"] = [{"type": "first_frame", "url": image}]
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
        if happyhorse_gateway(args.base_url or os.getenv("SK_VIDEO_BASE_URL") or first_env(BASE_URL_ENV_VARS[provider]) or DEFAULT_BASE_URLS[provider]):
            gateway_payload: dict[str, Any] = {"model": model, "prompt": prompt}
            if args.duration is not None:
                gateway_payload["duration"] = args.duration
            if ratio:
                gateway_payload["aspect_ratio"] = ratio
            if resolution:
                gateway_payload["resolution"] = resolution.lower()
            if image:
                gateway_payload["images"] = [image]
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
    if provider == "happyhorse":
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
            raw = response.read().decode("utf-8")
    except HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
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


def task_info(provider: str, response: dict[str, Any]) -> tuple[str | None, str | None, str | None]:
    if provider == "happyhorse":
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
        response = request_json(endpoint(base_url, provider, task_id), api_key, provider, request_timeout)
        if provider == "happyhorse" and happyhorse_gateway(base_url):
            _, raw_status, video_url = gateway_task_info(response)
        else:
            _, raw_status, video_url = task_info(provider, response)
        status = str(raw_status).upper() if raw_status is not None else None
        if status != last_status:
            print(f"{provider} task {task_id}: {status or 'status unavailable'}", file=sys.stderr)
            last_status = status
        success_statuses = {"COMPLETED", "COMPLETE", "DONE", "FINISHED", "SUCCESS", "SUCCEED", "SUCCEEDED", "READY"} if provider == "happyhorse" and happyhorse_gateway(base_url) else SUCCESS_STATUSES[provider]
        failure_statuses = {"FAILED", "FAILURE", "ERROR", "CANCELED", "CANCELLED", "TIMEOUT", "REJECTED", "EXPIRED"} if provider == "happyhorse" and happyhorse_gateway(base_url) else FAILURE_STATUSES[provider]
        if status in success_statuses:
            return response, video_url
        if status in failure_statuses:
            raise RuntimeError(f"{provider} task {task_id} ended as {status}: {error_summary(response)}")
        if status is None:
            raise RuntimeError(f"{provider} task response has no status: {error_summary(response)}")
        if time.monotonic() >= deadline:
            raise TimeoutError(f"timed out waiting for {provider} task {task_id}; resume with --task-id {task_id}")
        time.sleep(interval)


def suffix_from_response(url: str, content_type: str | None) -> str:
    suffix = Path(urlparse(url).path).suffix
    if suffix and len(suffix) <= 8:
        return suffix
    guessed = mimetypes.guess_extension((content_type or "").split(";", 1)[0].strip())
    return ".mp4" if not guessed else guessed


def download_video(url: str, outdir: Path, provider: str, task_id: str, timeout: int) -> Path:
    request = Request(url, headers={"User-Agent": "sk-video-creater/1.0"})
    try:
        with urlopen(request, timeout=timeout) as response:
            data = response.read()
            content_type = response.headers.get("Content-Type")
    except (HTTPError, URLError) as exc:
        raise RuntimeError(f"video was generated but download failed: {exc}; URL: {url}") from exc
    outdir.mkdir(parents=True, exist_ok=True)
    safe_id = re.sub(r"[^A-Za-z0-9_-]", "-", task_id)[:48]
    suffix = suffix_from_response(url, content_type)
    path = outdir / f"{provider}-{safe_id}{suffix}"
    path.write_bytes(data)
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
    parser.add_argument("--provider", required=True, help="happyhorse, seedance, or grok-video")
    parser.add_argument("--base-url", help="provider API base URL or full create endpoint")
    parser.add_argument("--api-key", help="runtime API key; prefer environment variables")
    parser.add_argument("--model", help="provider model name; defaults depend on provider and input mode")
    parser.add_argument("--prompt")
    parser.add_argument("--prompt-file")
    parser.add_argument("--image", help="reference image URL, data URL, or supported local path")
    parser.add_argument("--duration", type=int, help="video duration in seconds")
    parser.add_argument("--ratio", help="aspect ratio, for example 16:9, 9:16, or 1:1")
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
        if args.duration is not None and args.duration <= 0:
            raise ValueError("--duration must be positive")
        if provider == "grok-video" and args.duration is not None and args.duration > 15:
            raise ValueError("Grok Video duration must be between 1 and 15 seconds")
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
            if provider == "happyhorse" and happyhorse_gateway(base_url):
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
