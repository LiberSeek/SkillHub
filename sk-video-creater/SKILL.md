---
name: sk-video-creater
description: Generate AI videos with HappyHorse (Alibaba Cloud Model Studio), Seedance (Volcengine Ark), or Grok Video (xAI). Use for text-to-video, image-to-video, asynchronous video task submission and polling, resuming an existing task, or downloading generated MP4 files when the user mentions HappyHorse, Seedance, Grok Imagine Video, Grok Video, or one of these providers' video models and APIs.
---

# SK Video Creater

Use `scripts/generate_video.py` for all API calls. It normalizes provider endpoints, request payloads, task states, polling, and result downloads without third-party Python packages.

## Provider Selection

Honor an explicitly requested provider. If none is specified, choose only from providers with configured credentials and state the choice before submitting a paid task.

- Use `happyhorse` for Alibaba Cloud Model Studio HappyHorse text-to-video or first-frame image-to-video.
- Use `seedance` for Volcengine Ark Seedance generation, especially multimodal references or native audio.
- Use `grok-video` for xAI Grok Imagine Video text-to-video or image-to-video.

Do not silently switch providers after an API failure. Model availability, price, moderation, and output behavior differ.

## Configuration

Never invent, expose, or persist API keys in repository files. Prefer provider-specific environment variables:

```bash
export DASHSCOPE_API_KEY="..."  # HappyHorse
export ARK_API_KEY="..."        # Seedance
export XAI_API_KEY="..."        # Grok Video
```

Optional provider base URL overrides:

```bash
export HAPPYHORSE_BASE_URL="https://dashscope.aliyuncs.com"
export SEEDANCE_BASE_URL="https://ark.cn-beijing.volces.com"
export GROK_VIDEO_BASE_URL="https://api.x.ai"
```

`SK_VIDEO_API_KEY` and `SK_VIDEO_BASE_URL` override provider-specific values for compatible gateways. For persistent local configuration, use `~/.codex/sk-video-creater.env` with mode `600`; the script loads it automatically.

HappyHorse requires the API key, model, and endpoint to belong to the same Alibaba Cloud region. Prefer a workspace-specific Model Studio domain when available.

## Generate

Text-to-video:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider seedance \
  --prompt "A cinematic tracking shot through a rain-soaked neon street" \
  --duration 5 \
  --ratio 16:9 \
  --resolution 720p \
  --outdir ./generated-videos
```

Image-to-video:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider grok-video \
  --image /path/to/reference.png \
  --prompt "The camera slowly pulls back while the waterfall gains force" \
  --duration 8 \
  --outdir ./generated-videos
```

HappyHorse requires `--image` to be an HTTP(S) URL. Seedance and Grok Video also accept local image paths; the script converts them to data URLs.

## Workflow

1. Confirm the provider and that its API key is configured.
2. Preserve the user's subject, motion, camera direction, scene progression, duration, aspect ratio, resolution, audio intent, and reference-image constraints in the prompt and parameters.
3. Run `--dry-run` when using a new model, custom gateway, or provider-specific payload. Check the endpoint and body without exposing credentials.
4. Submit the task once. Poll the returned task ID instead of creating duplicate paid tasks.
5. Download the result immediately because provider result URLs expire.
6. Return the absolute MP4 path. In Codex desktop, render a playable local preview when useful.

Use `--model` to override the provider default. Use `--extra-json` with a JSON object or JSON file for fields such as `generate_audio`, `seed`, `watermark`, `draft`, or newer provider options. The object is deep-merged into the native request body and may replace arrays such as Seedance `content`.

Read `references/providers.md` before changing native payload fields, adding multimodal Seedance inputs, using regional HappyHorse endpoints, or diagnosing a provider-specific response.

## Async Control

Submit without waiting:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider happyhorse \
  --prompt "A miniature paper city wakes at night" \
  --submit-only
```

The command prints the task ID. Resume it later without creating another task:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider happyhorse \
  --task-id "TASK_ID" \
  --outdir ./generated-videos
```

Use `--no-download` to print the signed result URL. Use `--poll-interval`, `--poll-timeout`, and `--request-timeout` only when provider latency requires adjustment.

## Failure Handling

- If credentials are missing, stop and tell the user which provider variable to set.
- If the API rejects a parameter, inspect `--dry-run` and the provider reference. Do not remove user constraints or retry a paid request without explaining the change.
- If polling times out, preserve the task ID and resume with `--task-id`; do not resubmit.
- If a task reaches a terminal failure state, report the provider error. Do not alter the prompt and retry unless the user authorizes another generation.
- Do not claim live provider validation unless a real credentialed task was run. Offline tests validate protocol handling, not current account access or model entitlement.
