---
name: sk-image-creater
description: Generate and edit images through OpenAI-compatible, Grok Imagine, and Gemini image APIs with a configured custom base URL and API key. Use when the user asks for text-to-image or reference-image generation with gpt-image-2, grok-imagine-image, grok-imagine-image-quality, Gemini image models, custom prompts, aspect ratios, resolution tiers, or OpenAI-like and Gemini-compatible providers.
---

# SK Image Creater

## Quick Start

Use `scripts/generate_image.py` for text-to-image and `scripts/edit_image.py` for reference-image generation. The scripts automatically select the OpenAI-compatible, Grok Imagine, or Gemini protocol from `--model`.

Before making a request, require the user to configure credentials. Do not invent, expose, or persist API keys in repository files.

Preferred environment variables:

```bash
export SK_IMAGE_BASE_URL="https://your-provider.example.com"
export SK_IMAGE_API_KEY="your-api-key"
```

Fallback environment variables are also supported: `OPENAI_BASE_URL` and `OPENAI_API_KEY`.

For persistent local configuration, use `~/.codex/sk-image-creater.env` with file mode `600`:

```bash
export SK_IMAGE_BASE_URL="https://your-provider.example.com"
export SK_IMAGE_API_KEY="your-api-key"
```

The script reads this file automatically when environment variables are not already set.

Run:

```bash
python3 /path/to/sk-image-creater/scripts/generate_image.py \
  --prompt "用户的提示词" \
  --model gpt-image-2 \
  --size auto \
  --outdir ./generated-images
```

Reference-image generation:

```bash
python3 /path/to/sk-image-creater/scripts/edit_image.py \
  --image /path/to/reference.png \
  --prompt "根据参考图生成一张新的图片" \
  --model gpt-image-2 \
  --size auto \
  --outdir ./edited-images
```

Gemini image generation:

```bash
python3 /path/to/sk-image-creater/scripts/generate_image.py \
  --base-url https://api-direct.boft.ai \
  --model gemini-3.1-flash-image \
  --prompt "a lone red maple tree on a misty hill, watercolor" \
  --size 2:3 \
  --image-size 2K \
  --outdir ./generated-images
```

Grok Imagine image generation:

```bash
python3 /path/to/sk-image-creater/scripts/generate_image.py \
  --model grok-imagine-image \
  --prompt "a cinematic product photo of a translucent orange mechanical keyboard" \
  --size landscape \
  --outdir ./generated-images
```

High-quality Grok Imagine generation:

```bash
python3 /path/to/sk-image-creater/scripts/generate_image.py \
  --model grok-imagine-image-quality \
  --prompt "a detailed editorial portrait with soft studio lighting" \
  --size portrait \
  --outdir ./generated-images
```

## Workflow

1. Confirm the user has configured `SK_IMAGE_BASE_URL` and `SK_IMAGE_API_KEY`, or `~/.codex/sk-image-creater.env`; ask them to provide safe runtime values if missing.
2. If the user provided reference images, verify the local image paths exist and use `scripts/edit_image.py`; otherwise use `scripts/generate_image.py`.
3. Translate the user's visual request into a concise image prompt. Preserve the user's intended style, subject, aspect ratio, text requirements, reference-image constraints, and output count.
4. Run the selected script with `--model`, `--size`, and optional generation parameters. For Gemini, `--size` is the aspect ratio and `--image-size` is the resolution tier.
5. Return the saved absolute image paths to the user. If the app can render local images, include Markdown image previews with absolute paths.

## Endpoint Rules

For Gemini image models, the scripts use Google Generative Language protocol:

- `https://host` or `https://host/v1beta` becomes `https://host/v1beta/models/{model}:generateContent`
- Text-to-image and reference-image generation use the same endpoint; local references are sent as Gemini `inlineData` parts.
- `gemini-3-pro-image`, `gemini-3.1-flash-image`, and `gemini-3.1-flash-lite-image` are supported. Their `-preview` aliases are normalized to the base model name.

For Grok Imagine image models, the scripts use the OpenAI-compatible image protocol:

- `grok-imagine-image` and `grok-imagine-image-quality` are explicitly supported.
- Text-to-image uses `/v1/images/generations` with JSON fields such as `model`, `prompt`, `size`, `n`, and any `--extra-json` values.
- Reference-image generation uses `/v1/images/edits` with multipart form data by default, or JSON image data when `--json` is set. Confirm that the configured Grok-compatible provider supports edits before using reference images.
- `grok-imagine-image-quality` is the high-quality model variant; use provider-supported `--extra-json` fields for any additional quality, style, or response-format options.

The script normalizes the endpoint from the configured base URL:

- `https://host` becomes `https://host/v1/images/generations`
- `https://host/v1` becomes `https://host/v1/images/generations`
- `https://host/v1/images/generations` is used as-is

For reference-image edits, `scripts/edit_image.py` normalizes to `/v1/images/edits`:

- `https://host` becomes `https://host/v1/images/edits`
- `https://host/v1` becomes `https://host/v1/images/edits`
- `https://host/v1/images/edits` is used as-is
- `https://host/v1/images/generations` becomes `https://host/v1/images/edits`

The request body is JSON and starts with:

```json
{
  "model": "gpt-image-2",
  "prompt": "用户的提示词",
  "size": "auto"
}
```

The request uses `Content-Type: application/json` and `Authorization: Bearer <API key>`.

For `/v1/images/edits`, the default request is `multipart/form-data` with one or more `image` files plus text fields such as `model`, `prompt`, and `size`. Use `--json` only when the provider explicitly accepts base64/data-URL images in JSON.

## Parameters

Common options:

- `--model`: default `gpt-image-2`; explicitly supported models include `gpt-image-2`, `grok-imagine-image`, `grok-imagine-image-quality`, `gemini-3-pro-image`, `gemini-3.1-flash-image`, and `gemini-3.1-flash-lite-image`
- `--prompt`: required unless using `--prompt-file`
- `--size`: default `auto` for `gpt-image-2` style APIs; accepts `auto`, `square`, `portrait`, `landscape`, common ratios such as `1:1`, `3:4`, `4:3`, or any provider-supported `WIDTHxHEIGHT`
- `--n`: number of images when the provider supports it
- `--outdir`: output directory for generated files
- `--extra-json`: JSON object merged into the request body for provider-specific options

Gemini-specific options and limits:

- `--size`: `1:1`, `2:3`, `3:2`, `3:4`, `4:3`, `4:5`, `5:4`, `9:16`, `16:9`, or `21:9`; `square`, `portrait`, and `landscape` remain convenient aliases.
- `--image-size`: `512`, `1K`, `2K`, or `4K`; omit it to use the gateway default.
- Gemini always returns one image, so `--n` may only be `1`.
- Reference-image generation supports at most 14 files, each no larger than 20 MB.

Grok-specific notes:

- Grok Imagine uses the OpenAI-compatible size normalization rules below.
- If the provider has model-specific constraints for `--n`, `--size`, or edits, the API response is authoritative; pass provider-specific fields with `--extra-json`.
- Use `grok-imagine-image-quality` when the user asks for the higher-quality Grok Imagine variant.

Use `--dry-run` to inspect the normalized endpoint and JSON body without sending a request.

Reference-image options for `scripts/edit_image.py`:

- `--image`: local reference image path; repeat for multiple images
- `--image-field`: field name for image data; default `image`
- `--json`: send image data as JSON instead of multipart
- `--json-image-format`: `data-url` or `base64`; default `data-url`

Size aliases:

- `square` or `1:1` -> `1024x1024`
- `portrait`, `vertical`, `2:3`, or `3:4` -> `1024x1536`
- `landscape`, `horizontal`, `3:2`, or `4:3` -> `1536x1024`
- `auto` -> `auto`
- `omit`, `none`, or `default` -> omit the `size` field
- Any `WIDTHxHEIGHT` value, such as `1024x1024`, `1536x1024`, `1024x1536`, or provider-specific larger sizes, is passed through

## Failure Handling

If credentials are missing, stop and ask the user to set `SK_IMAGE_BASE_URL` and `SK_IMAGE_API_KEY`.

If the provider returns a non-2xx response, report the HTTP status and the response body summary. Do not retry with altered prompts unless the user asks.

If the response contains image URLs instead of base64 data, the script downloads each URL. If it cannot download an image, it saves the raw API response JSON for inspection.
