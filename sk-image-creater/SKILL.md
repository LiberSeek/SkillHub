---
name: sk-image-creater
description: Generate images by calling an OpenAI-compatible image generation API endpoint. Use when the user wants Codex to create image assets through a configured custom base URL and API key, especially requests involving /v1/images/generations, gpt-image-2, prompts, image sizes, or OpenAI-like image generation providers.
---

# SK Image Creater

## Quick Start

Use `scripts/generate_image.py` to call an OpenAI-compatible image generation endpoint and save returned images locally. Use `scripts/edit_image.py` when the user provides one or more reference images and wants `gpt-image-2` to generate a new image from them.

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

## Workflow

1. Confirm the user has configured `SK_IMAGE_BASE_URL` and `SK_IMAGE_API_KEY`, or `~/.codex/sk-image-creater.env`; ask them to provide safe runtime values if missing.
2. If the user provided reference images, verify the local image paths exist and use `scripts/edit_image.py`; otherwise use `scripts/generate_image.py`.
3. Translate the user's visual request into a concise image prompt. Preserve the user's intended style, subject, aspect ratio, text requirements, reference-image constraints, and output count.
4. Run the selected script with `--model`, `--size`, and optional generation parameters.
5. Return the saved absolute image paths to the user. If the app can render local images, include Markdown image previews with absolute paths.

## Endpoint Rules

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

- `--model`: default `gpt-image-2`
- `--prompt`: required unless using `--prompt-file`
- `--size`: default `auto` for `gpt-image-2` style APIs; accepts `auto`, `square`, `portrait`, `landscape`, common ratios such as `1:1`, `3:4`, `4:3`, or any provider-supported `WIDTHxHEIGHT`
- `--n`: number of images when the provider supports it
- `--outdir`: output directory for generated files
- `--extra-json`: JSON object merged into the request body for provider-specific options

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
