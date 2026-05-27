# Voice Workflows

更新时间，2026-05-21

## 结论

如果目标是尽快稳定产出内容，语音不要一开始就绑定声音克隆。

推荐顺序：

1. 字幕稿先行
2. 剪映内配音或真人录音
3. 再尝试本地免费声音克隆
4. 如果本地已经装了 VoiceBox，直接接入 VoiceBox 作为主 TTS

## 路线 A，最稳

字幕稿件 + 剪映人工接手

流程：

- `khazix-writer` 产出口播稿
- 我们补停顿版字幕稿
- 你在剪映里导入字幕稿
- 你选择剪映内置音色，或者直接真人录音

适合现在就做内容验证。

优点：

- 零额外部署
- 免费
- 最少工程折腾
- 最适合先验证题、节奏、封面、点击率

缺点：

- 听感不一定像你本人
- 风格稳定性要靠人工调

## 路线 A2，本地 VoiceBox

如果你本地已经有 VoiceBox，并且文档地址是 `http://127.0.0.1:17493/docs`，推荐把它当成当前优先级最高的 TTS 路线。

用途：

- 口播稿直接出音频
- 图文稿可先出配音，再进剪映排字幕
- 视频稿可直接接到 `hyperframes` 或剪映

本地脚本：

- `tools/scripts/voicebox_tts.sh`
- `tools/scripts/voicebox_transcribe.sh`

基本流程：

1. 在 VoiceBox 里准备一个 voice profile
2. 用 `voicebox_tts.sh` 输入文字和 profile id，输出 wav
3. 如果需要反向整理音频，再用 `voicebox_transcribe.sh`

推荐参数：

- `language=zh`
- `engine=qwen`
- `model_size=1.7B`
- `normalize=true`

适合你的原因：

- 本地运行
- 不依赖外部付费 API
- 可以直接接入我们现在的内容目录
- 能把字幕稿、音频、视频串成一条线

## 路线 B，本地免费优先

### CosyVoice

参考：

- GitHub，https://github.com/FunAudioLLM/CosyVoice

优点：

- 官方 README 明确支持 zero-shot 多语言和跨语言语音克隆
- 中文支持强
- 更适合你这种中文内容账号

缺点：

- 环境依赖不轻
- 生产使用前需要你录一批比较干净的人声样本

### F5-TTS

参考：

- GitHub，https://github.com/SWivid/F5-TTS

优点：

- 开源社区热度高
- 本地推理路线清晰
- 对短样本适配能力不错

缺点：

- 想稳定出中文内容，还是要做样本筛选和人工试听
- 更像技术路线成熟，不等于你拿来马上就能出成片

### GPT-SoVITS

参考：

- GitHub，https://github.com/RVC-Boss/GPT-SoVITS

优点：

- 中文创作者圈使用广
- few-shot 声音克隆成熟

缺点：

- 环境和模型下载比较重
- 容易把大量时间花在调音和修字上

## 推荐决策

你现在更适合：

- 先走路线 A2，如果 VoiceBox 本地可用
- 否则先走路线 A
- 同时平行准备本地样本目录
- 在不影响内容发布的前提下，再试 `CosyVoice`

原因很简单：

你当前的瓶颈不是没有声音克隆，而是还没把内容生产和发布节奏完全固定住。

## 样本准备规范

- 时长，10 到 20 分钟
- 语言，普通话为主
- 环境，安静房间，无混响，无背景音乐
- 语气，像平时讲话，不要播音腔
- 文件格式，优先 `wav`

建议目录：

`assets/audio/source-voice-samples/`

## 本地免费方案的工作边界

这些方案适合：

- 固定人设账号
- 想形成统一听感
- 愿意为后期可复用投入一次配置成本

这些方案不适合：

- 今天就要发
- 不想碰环境
- 不想做试听和返修
