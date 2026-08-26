# Provider Protocols

Read only the section for the selected provider. These schemas describe the native requests used by `scripts/generate_video.py`.

## Wan 3.0

- Provider: `wan` (Alibaba Cloud Model Studio / DashScope)
- Models: `wan3.0-video` and `wan3.0-video-prime`
- Default model: `wan3.0-video`
- Default base URL: `https://dashscope.aliyuncs.com`
- Native create: `POST /api/v1/services/aigc/video-generation/video-synthesis`
- Native query: `GET /api/v1/tasks/{task_id}`
- BOFT gateway create: `POST /v1/videos/generations`
- BOFT gateway query: `GET /v1/videos/generations/{task_id}`
- Required native header: `X-DashScope-Async: enable`
- Use the BOFT response `id` (for example `vidjob_xxx`) when polling a BOFT gateway. `upstream_task_id` is the internal DashScope UUID and is not the BOFT query ID.
- `resolution`: `480p`, `720p`, or `1080p`; `aspect_ratio`: `adaptive`, `16:9`, `9:16`, or `1:1`; `duration`: 1-30 seconds.
- BOFT image-to-video input uses `media: [{"type": "first_frame", "url": "https://..."}]`.
- Official unified media roles use `first_frame`, `last_frame`, `reference_image`, `reference_video`, and `reference_audio`; use `first_frame` + `last_frame` for a controlled transition, `reference_image` for subject/style consistency, `reference_video` for continuation/editing, and `reference_audio` for audio-driven or lip-sync input. BOFT also accepts `video`/`audio` aliases and normalizes them to the official names.
- Wan 3.0 keeps the native DashScope envelope (`input.prompt`, optional `input.media`, and `parameters.resolution`/`ratio`/`duration`). It is not the Wan 2.6 `size`/`reference_urls` protocol.
- Official base prices: `wan3.0-video` is ¥0.30/0.60/1.20 per second for 480p/720p/1080p; `wan3.0-video-prime` is ¥0.45/0.90/1.80 per second. BOFT group overrides and user multipliers may change the final user charge.

Native request:

```json
{
  "model": "wan3.0-video",
  "input": {"prompt": "一只小猫在月光下的屋顶上奔跑"},
  "parameters": {"resolution": "480P", "ratio": "adaptive", "duration": 5}
}
```

The Prime model uses the same protocol; replace only `model` with `wan3.0-video-prime`.

## HappyHorse

- Mode defaults: `happyhorse-1.1-t2v` (t2v), `happyhorse-1.1-i2v` (one first frame), `happyhorse-1.1-r2v` (reference images), and `happyhorse-1.0-video-edit` (video edit).
- Default base URL: `https://dashscope.aliyuncs.com`
- Create: `POST /api/v1/services/aigc/video-generation/video-synthesis`
- Query: `GET /api/v1/tasks/{task_id}`
- Required headers: `Authorization: Bearer ...`, `Content-Type: application/json`, `X-DashScope-Async: enable`
- Task ID/status: `output.task_id`, `output.task_status`
- Result: `output.video_url`
- Terminal states: `SUCCEEDED`, `FAILED`, `CANCELED`, `UNKNOWN`

Text-to-video body:

```json
{
  "model": "happyhorse-1.1-t2v",
  "input": {"prompt": "..."},
  "parameters": {"resolution": "720P", "ratio": "16:9", "duration": 5}
}
```

For first-frame image-to-video, use model `happyhorse-1.1-i2v` and add:

```json
{"input": {"prompt": "...", "media": [{"type": "first_frame", "url": "https://..."}]}}
```

Reference-based video uses up to 9 media items:

```json
{
  "model": "happyhorse-1.1-r2v",
  "input": {"prompt": "character1 walks through a market", "media": [{"type": "reference_image", "url": "https://..."}]},
  "parameters": {"resolution": "720P", "ratio": "16:9", "duration": 5}
}
```

Video editing uses `happyhorse-1.0-video-edit` and `input.media` with one `{"type":"video"}` item followed by optional `{"type":"reference_image"}` items. It does not use a VACE `function` field.

HappyHorse 1.1 does not support `last_frame`, `video`, or `audio` media input; use Wan 3.0 for those modes.

The key, model, and endpoint must be in the same Alibaba Cloud region. Workspace-specific regional domains are preferred. A successful task ID is valid for 24 hours; download signed results promptly.

Official references:

- <https://help.aliyun.com/zh/model-studio/happyhorse-text-to-video-api-reference>
- <https://help.aliyun.com/zh/model-studio/happyhorse-image-to-video-api-reference>

Compatible gateway variant (for example `https://api.boft.ai`):

- Create: `POST /v1/videos/generations`
- Query: `GET /v1/videos/generations/{task_id}`
- Body: `{"model":"happyhorse-1.1-t2v","prompt":"...","duration":5,"aspect_ratio":"16:9","resolution":"720p"}`
- The response may wrap `id`, `status`, and `result.video_url` under `data`.

## Seedance

- Default model: `doubao-seedance-2-0-260128`
- Default base URL: `https://ark.cn-beijing.volces.com`
- Create: `POST /api/v3/contents/generations/tasks`
- Query: `GET /api/v3/contents/generations/tasks/{id}`
- Task ID/status: top-level `id`, `status`
- Result: `content.video_url`
- States: `queued`, `running`, `cancelled`, `succeeded`, `failed`, `expired`

Basic body:

```json
{
  "model": "doubao-seedance-2-0-260128",
  "content": [
    {"type": "text", "text": "..."},
    {"type": "image_url", "image_url": {"url": "https://..."}}
  ],
  "duration": 5,
  "ratio": "16:9",
  "resolution": "720p"
}
```

Use `--extra-json '{"generate_audio":true}'` when the selected model supports native audio. For multiple image, video, or audio references, provide a JSON file that replaces `content` with the model's documented multimodal array. Query records are available for seven days; generated video URLs are valid for 24 hours.

Official references:

- <https://www.volcengine.com/docs/82379/1520757>
- <https://www.volcengine.com/docs/82379/1521309>

## Grok Video

- Default model: `grok-imagine-video-1.5`
- Default base URL: `https://api.x.ai`
- Create: `POST /v1/videos/generations`
- Query: `GET /v1/videos/{request_id}`
- Task ID/status: `request_id`, `status`
- Result: `video.url`
- States: `pending`, `done`, `failed`, `expired`

Body:

```json
{
  "model": "grok-imagine-video-1.5",
  "prompt": "...",
  "image": {"url": "https://..."},
  "duration": 10,
  "aspect_ratio": "16:9",
  "resolution": "720p"
}
```

Duration is 1-15 seconds. Supported resolutions depend on model and input mode; `grok-imagine-video-1.5` supports text-to-video up to 1080p. Omit `image` for text-to-video.

Official references:

- <https://docs.x.ai/developers/model-capabilities/video/generation>
- <https://docs.x.ai/developers/model-capabilities/video/image-to-video>
