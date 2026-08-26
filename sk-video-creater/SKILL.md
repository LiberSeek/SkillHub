---
name: sk-video-creater
description: Generate and edit AI videos with Alibaba DashScope Wan 3.0/HappyHorse, Seedance (Volcengine Ark), or Grok Video (xAI). Supports multimodal Wan text/image/video/audio inputs, first+last-frame transitions, reference-based role-play, video editing, asynchronous polling, task resumption, and MP4 downloads.
---

# SK Video Creater

Use `scripts/generate_video.py` for all API calls. It normalizes provider endpoints, request payloads, task states, polling, and result downloads without third-party Python packages.

## Provider Selection

Honor an explicitly requested provider. If none is specified, choose only from providers with configured credentials and state the choice before submitting a paid task.

- Use `happyhorse` for HappyHorse 1.1 text-to-video, first-frame image-to-video, or reference-based video; use `happyhorse-1.0-video-edit` for natural-language video editing. HappyHorse i2v requires exactly one first-frame media item; HappyHorse does not provide the Wan first+last-frame mode.
- Use `wan` for Wan 3.0 all-in-one video generation. The supported models are `wan3.0-video` and `wan3.0-video-prime`; override with `--model` when selecting Prime. Wan accepts text in `prompt` plus official `first_frame`, `last_frame`, `reference_image`, `reference_video`, and `reference_audio` media inputs. BOFT also accepts `video`/`audio` aliases and normalizes them to the official names. Output duration is 1-30 seconds.
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
export WAN_BASE_URL="https://dashscope.aliyuncs.com"
export SEEDANCE_BASE_URL="https://ark.cn-beijing.volces.com"
export GROK_VIDEO_BASE_URL="https://api.x.ai"
```

`SK_VIDEO_API_KEY` and `SK_VIDEO_BASE_URL` override provider-specific values for compatible gateways. For persistent local configuration, use `~/.codex/sk-video-creater.env` with mode `600`; the script loads it automatically.

For OpenAI-compatible DashScope gateways such as `https://api.boft.ai` or `https://api-direct.boft.ai`, set `SK_VIDEO_BASE_URL` to the gateway root. The script uses `POST /v1/videos/generations` and polls `GET /v1/videos/generations/{task_id}` for that gateway; Alibaba Cloud's native endpoint remains the default for the standard DashScope hosts. Gateway image inputs are normalized to BOFT's `media: [{"type":"first_frame","url":"..."}]` field.

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

Wan 3.0 text-to-video through BOFT:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider wan \
  --base-url https://api.boft.ai \
  --model wan3.0-video \
  --prompt "一只小猫在月光下的屋顶上奔跑" \
  --duration 5 \
  --ratio adaptive \
  --resolution 480p \
  --outdir ./generated-videos
```

Wan 3.0 first+last-frame transition:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider wan --mode kf2v \
  --first-frame https://example.com/start.png \
  --last-frame https://example.com/end.png \
  --prompt "A smooth camera rise connects the two moments" \
  --duration 5 --ratio 16:9 --resolution 720p
```

Wan 3.0 video and audio inputs:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider wan \
  --video https://example.com/guide.mp4 \
  --audio https://example.com/dialogue.mp3 \
  --prompt "保持人物身份，按照音频完成自然口型" \
  --duration 8 --resolution 1080p
```

Reference-based role-play (Wan 3.0 or HappyHorse R2V):

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider happyhorse --mode r2v \
  --reference https://example.com/character.png \
  --prompt "character1 walks through the neon market and looks into camera" \
  --duration 5 --ratio 16:9 --resolution 720p
```

Natural-language video editing:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider wan --mode videoedit --video https://example.com/input.mp4 \
  --reference https://example.com/wardrobe.png \
  --prompt "Replace the jacket with the referenced wardrobe while preserving motion" \
  --duration 5
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

DashScope image/video/audio inputs require reachable URLs (use `--first-frame`, `--last-frame`, `--reference`, `--video`, or `--audio`). Seedance and Grok Video also accept local image paths; the script converts them to data URLs. HappyHorse rejects Wan-only `last_frame`, `video`, and `audio` media types.

## Workflow

1. Confirm the provider and that its API key is configured.
2. Classify the generation as text-to-video or image-to-video, then build the prompt with the matching formula in `references/prompting.md`. Preserve explicit user wording; enhance only missing dimensions.
3. Run `--dry-run` when using a new model, custom gateway, or provider-specific payload. Check the endpoint and body without exposing credentials.
4. Submit the task once. Poll the returned task ID instead of creating duplicate paid tasks.
5. Download the result immediately because provider result URLs expire.
6. Return the absolute MP4 path. In Codex desktop, render a playable local preview when useful.

Use `--model` to override the provider default. Use `--extra-json` with a JSON object or JSON file for fields such as `generate_audio`, `seed`, `watermark`, `draft`, or newer provider options. The object is deep-merged into the native request body and may replace arrays such as Seedance `content`.

Read `references/prompting.md` when drafting or improving Wan/HappyHorse prompts, especially for motion, camera direction, audio, image-to-video, reference role-play, or timed shots. Read `references/providers.md` before changing native payload fields, adding multimodal inputs, using regional HappyHorse endpoints, or diagnosing a provider-specific response.

## Async Control

Submit without waiting:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider wan \
  --prompt "A miniature paper city wakes at night" \
  --submit-only
```

The command prints the task ID. Resume it later without creating another task:

```bash
python3 /path/to/sk-video-creater/scripts/generate_video.py \
  --provider wan \
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
