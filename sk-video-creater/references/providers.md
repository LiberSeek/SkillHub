# Provider Protocols

Read only the section for the selected provider. These schemas describe the native requests used by `scripts/generate_video.py`.

## HappyHorse

- Default model: `happyhorse-1.1-t2v`; with `--image`: `happyhorse-1.1-i2v`
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
