---
name: sk-content-producer
description: |
  LiberSeek 工作室视频生产 skill。用于把口播稿或内容稿转成音频、字幕和视频成片，重点覆盖竖屏自媒体视频、字幕驱动视频和 HyperFrames 编排视频。适用于“把这篇稿子做成视频”“根据口播稿出音频和字幕”“用 hyperframes 做短视频”“做一个图驱动或音频驱动的视频”这类请求。
---

# sk-content-producer

这是工作室内容生产里的视频入口。

它整合了：

- `hyperframes` 的视频编排能力
- VoiceBox 本地 TTS / 转写流程
- 工作室自己的“先出音频，再算总时长，再做视频”做法

## 什么时候用

- 要做抖音 / 快手 / B 站竖屏视频
- 要把口播稿接成配音
- 要做字幕驱动视频
- 要做图片驱动视频

## 默认原则

先音频，后视频。

不要先把视频定长，再硬把音频塞进去。

正确顺序是：

1. 先从口播稿生成音频
2. 拼接音频并计算总时长
3. 再把总时长交给视频编排

这样视频里的语速不会被被动加快。

## 工作流

### 1. 先准备口播稿

口播稿默认来自 `sk-content-writer`。

如果用户只给了图文稿，先改成适合朗读的版本。

### 2. 优先走本地 VoiceBox

优先脚本：

- `scripts/voicebox_tts.sh`
- `scripts/voicebox_transcribe.sh`

如果本地 VoiceBox 可用，先出 wav，再决定是否回转字幕。

### 3. 用音频驱动 HyperFrames

优先脚本：

- `scripts/build_voice_driven_hyperframes_video.py`

如果是图片轮播或轻视频，可以用：

- `scripts/build_image_driven_video.py`

### 4. 成片节奏遵循 HyperFrames 规则

需要做视频编排时，再按需阅读：

- `references/video-composition.md`
- `references/motion-principles.md`
- `references/captions.md`
- `references/beat-direction.md`
- `references/transitions.md`

不要一次把所有 hyperframes 文档都加载进来。

## 参考文件

- `references/voice-workflows.md`
- `references/voicebox-local.md`
- `references/content-production-matrix.md`

这三个最贴近工作室当前流程，优先读。

## 模板与调色

- `templates/design-picker.html`
- `palettes/*.md`

当用户还没定视频视觉方向时再用，不要默认展开。
