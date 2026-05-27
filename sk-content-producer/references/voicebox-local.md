# VoiceBox Local

更新时间，2026-05-21

## 文档入口

- Swagger，`http://127.0.0.1:17493/docs`
- OpenAPI，`http://127.0.0.1:17493/openapi.json`

## 这套 VoiceBox 是什么

这是一个本地 FastAPI 语音工作台。

从 OpenAPI 描述来看，它不是单纯的一个 TTS 接口，而是包含：

- voice profiles
- TTS generation
- audio streaming
- transcription
- stories 时间线
- effects
- model download / load / unload
- MCP client binding

OpenAPI 信息：

- title，`voicebox API`
- description，`Production-quality Qwen3-TTS voice cloning API`
- version，`0.5.0`

## 和我们内容生产最相关的接口

### Voice Profiles

- `GET /profiles`
- `POST /profiles`
- `POST /profiles/{profile_id}/samples`

用途：

- 查看已有声音
- 创建新的声音 profile
- 给 profile 加样本

当前本地已发现 profile：

- `Raven`，`840ca9b8-d8e3-4f50-9eb8-ab55a4d9984e`
- `Lee`，`6efde8ea-d358-42a5-9b4d-c357216ebbb5`

### TTS

- `POST /generate`
- `POST /generate/stream`
- `GET /audio/{generation_id}`
- `GET /history/{generation_id}`

用途：

- 生成语音
- 轮询状态
- 下载生成后的音频

`POST /generate` 的关键参数：

- `profile_id`，必填
- `text`，必填
- `language`，默认可设 `zh`
- `engine`，当前推荐 `qwen`
- `model_size`，当前推荐 `1.7B`
- `personality`
- `seed`
- `instruct`

### REST 版 MCP Speak

- `POST /speak`

这个接口在文档里明确写着：

- 它镜像 `voicebox.speak`
- 属于 MCP 的 REST surface

也就是说，如果以后你的 agent runtime 真正把 VoiceBox 挂成 MCP server，逻辑上应该优先走 `voicebox.speak`。

如果当前只是本地 HTTP 可用，那么可以直接走 `/generate` 或 `/speak`。

### Transcribe

- `POST /transcribe`

用途：

- 音频反向转字幕
- 检查配音结果
- 给剪映字幕稿做校对

### MCP Bindings

- `GET /mcp/bindings`
- `PUT /mcp/bindings`
- `DELETE /mcp/bindings/{client_id}`

用途：

- 给某个 MCP client_id 绑定默认 profile
- 绑定默认 engine
- 控制默认 personality 开关

如果以后要把 VoiceBox 真正纳入 MCP 工作流，这组接口就是关键。

### Stories

- `POST /stories`
- `POST /stories/{story_id}/items`
- `GET /stories/{story_id}/export-audio`

用途：

- 把多段 generation 拼成一个故事时间线
- 导出混合音频

这组接口很适合以后做：

- 多段口播拼接
- 背景音乐和语音合成
- 多角色对话内容

## 当前本地状态

### 模型状态

已下载：

- `qwen-tts-1.7B`
- `whisper-base`

未下载但接口已支持：

- `qwen-custom-voice-*`
- `luxtts`
- `chatterbox-*`
- `tada-*`
- `kokoro`

### 当前 generation settings

- `max_chunk_chars = 800`
- `crossfade_ms = 50`
- `normalize_audio = true`
- `autoplay_on_generate = true`

## 我们已经补好的本地脚本

- `tools/scripts/voicebox_tts.sh`
- `tools/scripts/voicebox_transcribe.sh`

### 生成音频

```bash
tools/scripts/voicebox_tts.sh \
  --profile-id 840ca9b8-d8e3-4f50-9eb8-ab55a4d9984e \
  --text "你好，这是一个 VoiceBox 测试。" \
  --output /tmp/voicebox-test.wav
```

### 转写音频

```bash
tools/scripts/voicebox_transcribe.sh \
  --input /tmp/voicebox-test.wav
```

## 实测结果

已验证：

- `voicebox_tts.sh` 成功输出 `/tmp/voicebox-test.wav`
- `voicebox_transcribe.sh` 成功返回文本

转写结果存在轻微误识别，示例里把 `VoiceBox` 识别成了 `Wisebox`，这很正常，说明它可用，但字幕仍然建议人工过一遍。

## 推荐怎么纳入工作流

现在最推荐的用法：

1. `khazix-writer` 出口播稿
2. 调 `voicebox_tts.sh` 生成 wav
3. 需要字幕时，调 `voicebox_transcribe.sh`
4. 视频画面交给 `hyperframes` 或剪映
5. 最终发布交给 `publish-stack`

## 什么时候优先 VoiceBox

优先 VoiceBox 的情况：

- 你本地已经有可用 profile
- 你想避免外部 API 成本
- 你要快速把字幕稿变成音频
- 你要把语音生成接进我们现在的内容目录

暂时不优先 VoiceBox 的情况：

- 你今天只想快发一条
- 你觉得真人录音更自然
- 你当前更依赖剪映内置音色
