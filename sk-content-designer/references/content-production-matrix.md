# Content Production Matrix

更新时间，2026-05-26

## 先说结论

你现在这套流程，已经可以覆盖两类内容的生产。

但覆盖方式不是完全自动化，而是：

- 图文稿，已经接近可稳定生产
- 视频稿，已经能生产，但目前更适合半自动工作流

也就是说，当前流程已经能满足你说的这两类交付物，只是视频这边还依赖人工配音、剪映处理和最终审稿。

## 两类内容是否可生产

### 图文稿

目标结构：

- 封面
- 图片
- 稿件标题
- 稿件简介
- 稿件标签

当前结论：

- 可以生产
- 其中封面和图片最适合交给 `baoyu-skills`
- 标题、简介、标签更适合交给你现在已有的 `dbs-*` + `khazix-writer`

### 视频稿

目标结构：

- 封面
- 视频
- 音频
- 字幕
- 稿件标题
- 稿件简介
- 稿件标签

当前结论：

- 可以生产
- 但目前最稳的是半自动
- `hyperframes` 负责视频成片逻辑最强
- 音频现在优先走字幕稿 + 剪映配音或真人录音

## 工具分工总表

| 交付物 | 当前是否能做 | 最适合工具 / skill | 说明 |
|---|---|---|---|
| 图文封面 | 可以 | `baoyu-danger-gemini-web` + 本地叠字 | 工作室默认封面底图方案，优先 Swiss 竖版 `3:4`，先出底图，再叠标题和贴纸 |
| 图文多图卡片 | 可以 | `baoyu-image-cards` | 最适合小红书图文、抖音图文、快手图文、图片卡组 |
| 图文信息图 | 可以 | `baoyu-infographic` | 适合高密度信息图、大图总结、流程图 |
| 文章配图 | 可以 | `baoyu-article-illustrator` | 适合给长文或图文稿自动补插图 |
| 通用图片生成 | 可以 | `baoyu-imagine` | 仍可作为通用图像引擎，但工作室封面默认不走官方 Gemini 图片 API 线路 |
| 视频封面 | 可以 | `baoyu-danger-gemini-web` + 本地叠字 | 与图文封面统一底图策略，便于形成固定视觉语言 |
| 视频画面 | 可以 | `hyperframes` | 适合把脚本、字幕、转场、镜头节奏编成视频 |
| 视频音频 | 可以，但半自动 | `khazix-writer` + 剪映 / 本地 TTS | 当前优先用字幕稿配音，不建议等声音克隆 |
| 视频音频 | 可以，但半自动 | `voicebox_tts.sh` / VoiceBox / 剪映 | 如果本地已有 VoiceBox，就优先它 |
| 视频字幕 | 可以 | `hyperframes` / 剪映 | 成片内字幕更适合 `hyperframes`，人工调更适合剪映 |
| 标题 | 可以 | `dbs-xhs-title` | 图文标题和短视频标题都适合 |
| 视频开头句 | 可以 | `dbs-hook` | 更适合短视频钩子 |
| 稿件简介 | 可以 | `khazix-writer` / `dbs-content` | 先诊断，再出简介和正文 |
| X 长文发布 | 可以 | `baoyu-post-to-x` + `publish-stack` | 当前工作室默认形态是中文 `X Article` 长文，正文直接复用图文正文 |
| 稿件标签 | 可以，但模板化 | `dbs-benchmark` + 人工模板 | 目前更适合基于对标沉淀模板，不是完全自动 |
| 多平台发布 | 可以 | `publish-stack` | 负责执行，不负责创作判断 |

## `baoyu-skills` 和 `hyperframes` 的边界

### 更适合 `baoyu-skills` 的内容

这些内容优先交给 `baoyu-*`：

- 小红书图文卡片
- 微信图文配图
- 多张轮播图
- 高密度信息图
- 文章插图
- 单张封面底图

原因：

- `baoyu-image-cards` 天生就是为社交媒体图片卡片设计的
- `baoyu-infographic` 适合做信息浓度高的大图
- `baoyu-article-illustrator` 适合从文章结构反推插图位置
- `baoyu-danger-gemini-web` 更适合当前工作室封面底图主流程

一句话说，`baoyu-skills` 更像图像内容生产线。

### 更适合 `hyperframes` 的内容

这些内容优先交给 `hyperframes`：

- 竖屏口播视频
- 横屏 B 站视频
- 带转场的视频卡点
- 带字幕的视频
- 带音频、BGM、时间轴的视频成片
- 标题卡、场景切换、动效画面

原因：

- `hyperframes` 的核心就是 HTML + GSAP + timeline
- 它处理的是时间维度，不只是单张图
- 它天然适合字幕、音频、镜头节奏、转场、场景组织

一句话说，`hyperframes` 更像视频编排引擎。

### 更适合 VoiceBox 的内容

这些内容优先交给 VoiceBox：

- 口播稿转音频
- 字幕稿配音
- 本地 TTS
- 反向转写

原因：

- 它是本地语音工作台
- 有 `/speak`、`/generate`、`/transcribe`
- 还能通过 MCP 绑定 profile
- 适合你现在这种“本地优先、先跑通内容”的路线

## 图文稿推荐生产流

如果目标是：

- 封面
- 图片组
- 标题
- 简介
- 标签

推荐顺序：

1. `dbs-benchmark` 找对标
2. `dbs-content` 判断内容形式
3. `dbs-xhs-title` 出标题
4. `khazix-writer` 出图文稿和简介
5. `baoyu-danger-gemini-web` 出封面底图
6. `baoyu-image-cards` 出轮播卡片
7. 需要高密度总结时，用 `baoyu-infographic`
8. 用模板法整理标签
9. 进入 `publish-stack`

### 当前工作室默认图文风格

如果没有单独指定视觉风格，当前默认优先：

- `Swiss` 瑞士国际主义
- 竖版 `3:4`
- 高对比、强网格、信息感清晰
- 用于抖音、快手、小红书这类图文主平台
- 图文内容卡和封面统一按同一套 `Swiss` 竖版 `3:4` 语言生产

横版补充规则：

- `4:3` 作为桌面预览、B 站封面、横向分发补充
- `4:3` 也作为 `X Article` 默认封面比例
- 不再默认先做横版，再被动裁成竖版

## 视频稿推荐生产流

如果目标是：

- 封面
- 视频
- 音频
- 字幕
- 标题
- 简介
- 标签

推荐顺序：

1. `dbs-benchmark` 找对标
2. `dbs-content` 判断做短视频还是长视频
3. `dbs-xhs-title` 出标题
4. `dbs-hook` 出开头钩子
5. `khazix-writer` 出口播稿、简介
6. 生成 `剪映字幕稿.txt`
7. 音频先走 VoiceBox，本地可用时优先
8. `baoyu-danger-gemini-web` 出视频封面底图
9. `hyperframes` 负责视频画面、字幕、转场、成片
10. 标签模板化
11. 进入 `publish-stack`

## 对你现在最有用的实际判断

### 图文稿

优先使用：

- `baoyu-danger-gemini-web`
- `baoyu-image-cards`
- `baoyu-infographic`
- `dbs-xhs-title`
- `khazix-writer`

这套更适合你现在先把小红书图文、抖音图文、快手图文、B 站动态跑起来。

### 视频稿

优先使用：

- `baoyu-danger-gemini-web`
- `khazix-writer`
- `hyperframes`
- `oral-video-llm-editing`

这套更适合你后面把竖屏口播和 B 站横屏视频补上。

## 当前还没有完全自动化的地方

- 标签，目前还是模板化，不是强智能生成
- 音频，目前最稳的是字幕稿 + 剪映 / 真人录音
- 封面标题，仍然建议本地叠字，不建议完全交给模型
- 最终平台发布前的审稿，仍然需要人工确认
- 抖音背景音乐，当前默认保留人工选择

## 平台风格约束

### 抖音

- 目标，不是搬长文，而是做“结论先行”的强节奏图文
- 正文宁可短一点，也不要一屏塞太满
- 默认人工选背景音乐
- Tag / 话题总数最多按 `4` 处理

### 快手

- 比抖音更白话
- 少一点术语，多一点“跟你有什么关系”
- Tag / 话题总数最多按 `4` 处理

### B 站动态

- 一条动态只讲一个判断
- 允许多一点“我为什么这样看”的主观句
- 不要写成平台公告口气

### X

- 默认中文内容
- 默认普通帖 + 1 张图
- 优先一句可转述判断，不要先写成长论文
- 如果单条装不下，再考虑 thread，不默认先走 Article

## 最终建议

现在不要把 `baoyu-skills` 和 `hyperframes` 当成竞争关系。

更好的理解是：

- `baoyu-skills` 负责图像资产生产
- `hyperframes` 负责视频资产生产
- `dbs-*` 和 `khazix-*` 负责选题、表达和文稿
- `publish-stack` 负责分发
