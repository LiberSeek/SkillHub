# SkillHub Portable Manifest

更新时间：2026-05-27

这份索引说明 `portable/skills` 里每个正式 skill 的职责、来源和携带资源。

目标很简单：

- `vendors/` 放完整上游镜像
- `portable/skills/` 放工作室正式可加载版本
- Codex 和其他 Agent 后续优先加载这里的 skill，而不是直接依赖零散上游 skill

## 当前正式技能

### `sk-content-researcher`

- 职责：选题、对标、爆款拆解、热点跟踪、系统研究
- 主要来源：
  - `dbskill/skills/dbs-benchmark`
  - `khazix-skills/aihot`
  - `khazix-skills/hv-analysis`
- 携带资源：
  - `references/schema.json`
  - `scripts/md_to_pdf.py`
- 典型输出：
  - `source/内容生产方案.md`
  - `notes/研究记录.md`
  - `notes/对标拆解.md`

### `sk-content-writer`

- 职责：图文稿、口播稿、标题、简介、标签、平台文案
- 主要来源：
  - `khazix-skills/khazix-writer`
  - `dbskill/skills/dbs-content`
  - `dbskill/skills/dbs-xhs-title`
  - `dbskill/skills/dbs-hook`
  - `studio-content-os`
- 携带资源：
  - `references/content_methodology.md`
  - `references/style_examples.md`
  - `references/content-production-matrix.md`
  - `references/content-ops-checklist.md`
- 典型输出：
  - `图文稿.md`
  - `口播稿.md`
  - `title.txt`
  - `description.txt`
  - `tags.txt`
  - `twitter-article.md`
  - `bilibili.txt`

### `sk-content-designer`

- 职责：封面、图文卡片、信息图、贴纸资产、Swiss 风格视觉包装
- 主要来源：
  - `baoyu-skills/skills/baoyu-danger-gemini-web`
  - `guizang-ppt-skill`
  - 工作室本地封面与贴纸脚本
  - `studio-content-os`
- 携带资源：
  - `references/cover-automation.md`
  - `references/content-production-matrix.md`
  - `references/layouts*.md`
  - `references/themes*.md`
  - `references/image-prompts.md`
  - `references/screenshot-framing.md`
  - `assets/template.html`
  - `assets/template-swiss.html`
  - `assets/screenshot-backgrounds/`
  - `scripts/generate_studio_cover.py`
  - `scripts/compose_studio_gemini_cover.py`
  - `scripts/generate_studio_cards.py`
  - `scripts/process_stickers*.py`
- 典型输出：
  - `assets/cover/generated/*.png`
  - `assets/cards/`
  - 标准化贴纸素材

### `sk-content-producer`

- 职责：音频生成、字幕生成、音频驱动视频、图片驱动视频、HyperFrames 成片
- 主要来源：
  - `hyperframes`
  - 工作室本地 VoiceBox / 视频脚本
  - `studio-content-os`
- 携带资源：
  - `references/voice-workflows.md`
  - `references/voicebox-local.md`
  - `references/video-composition.md`
  - `references/motion-principles.md`
  - `references/captions.md`
  - `references/beat-direction.md`
  - `templates/design-picker.html`
  - `palettes/*.md`
  - `scripts/voicebox_tts.sh`
  - `scripts/voicebox_transcribe.sh`
  - `scripts/build_voice_driven_hyperframes_video.py`
  - `scripts/build_image_driven_video.py`
- 典型输出：
  - `audio/*.wav`
  - `subtitles/*.srt` 或字幕稿
  - `video/*.mp4`

### `sk-content-publisher`

- 职责：账号检查、登录、bundle 初始化、多平台发布
- 主要来源：
  - `social-auto-upload`
  - `publish-stack`
  - `twitter-cli`
  - `bilibili-cli`
  - `xiaohongshu-cli`
- 携带资源：
  - `references/publish-stack-readme.md`
  - `references/content-ops-checklist.md`
  - `references/xiaohongshu/`
  - `references/douyin/`
  - `references/kuaishou/`
  - `references/bilibili-sau/`
  - `references/x/`
  - `references/bilibili-cli/`
  - `references/xiaohongshu-cli/`
  - `scripts/check_stack.sh`
  - `scripts/login_all.sh`
  - `scripts/new_topic.sh`
  - `scripts/publish_bundle.sh`
  - `scripts/examples/`
- 典型输出：
  - 已发布的多平台 bundle
  - 登录态检查结果

## 设计原则

- 不把 vendor 仓库整个暴露给 Codex
- 只把工作室已经验证过的能力，映射成正式 skill
- `SKILL.md` 负责统一入口
- `references/ scripts/ assets/ templates/ palettes/` 负责携带能力

## 推荐加载顺序

如果是内容生产任务，默认按下面顺序触发：

1. `sk-content-researcher`
2. `sk-content-writer`
3. `sk-content-designer`
4. `sk-content-producer`
5. `sk-content-publisher`

## 安装到 Codex

推荐不要复制一份到 `~/.codex/skills`，而是用符号链接挂载。

原因：

- 只维护 `skillhub` 这一份正式源码
- 后续更新 `portable/skills` 后，不需要重复拷贝
- Codex 重启后就能读取最新版本

安装与更新方法见：

- `../install-codex-skills.sh`
- `../../docs/codex-local-skills.md`
