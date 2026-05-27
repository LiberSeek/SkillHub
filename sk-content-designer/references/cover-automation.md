# Cover Automation

更新时间，2026-05-26

## 结论

封面自动化最稳的思路，不是让模型一次性生成最终封面。

而是两段式：

1. `baoyu-danger-gemini-web` 生成背景和主体氛围
2. 本地叠加标题、头像贴纸、工具卡片、固定角标

这样最适合工作室长期复用，也最容易做出固定风格。

## 当前工作室默认路线

工作室封面底图，默认统一走 `baoyu-danger-gemini-web`。

原因：

- 已经有本机登录态，实际可用
- 不受官方 Gemini 图片 API 免费配额波动影响
- 更适合快速试风格和连续迭代
- 能直接结合工作室贴纸做参考图生成

执行约定：

- 不再把官方 Gemini 图片 API 当成默认出图线路
- 不再优先走 `baoyu-imagine` 的 Google provider 作为封面主通道
- 封面提示词写在主题目录的 `assets/cover/prompts/`
- 封面底图输出到主题目录的 `assets/cover/generated/`
- 贴纸只用于封面，不进入正文配图和视频正片

## 标准封面流程

1. 根据主题写 `封面提示词.md`
2. 用 `baoyu-danger-gemini-web` 生成封面底图
3. 选择工作室贴纸，固定放右下角或左下角
4. 输出 `3:4` 和 `4:3` 两个版本
5. 人工检查缩略图可读性

## 当前默认风格

如果没有额外指定，当前工作室默认优先：

- `Swiss` 瑞士国际主义
- 竖版 `3:4`
- 信息图 / 图文卡片优先
- 高对比、强网格、文字区明确

这条默认风格特别适合：

- 抖音图文
- 快手图文
- 小红书图文

横版补充原则：

- `4:3` 继续保留
- 但默认不再让横版充当社媒主资产
- 横版更多用来做 B 站封面、桌面预览和补充分发

## 为什么不再默认走官方 Gemini 图片 API

- 免费配额容易波动
- 同一条链路今天能跑，明天不一定稳定
- 对工作室来说，真正要的是连续可复用，而不是名义上的官方接口

所以这里的默认策略很明确：

- 要快速稳定出封面，先用 `baoyu-danger-gemini-web`
- 真要接正式付费 API，再作为补充路线单独评估

## 备选路线，不是默认路线

### OpenAI Images API

参考：

- Guide，https://platform.openai.com/docs/guides/image-generation
- API，https://platform.openai.com/docs/api-reference/images

适合：

- 生成背景
- 生成风格探索版
- 做局部修改和图像编辑

优点：

- 官方接口稳定
- 既能生成也能编辑

限制：

- 中文标题生成不应该完全依赖模型
- 一致性仍然需要本地后处理

## 风格一致性增强路线

### fal.ai FLUX LoRA

参考：

- Overview，https://fal.ai/docs/model-api-reference/image-generation-api/overview
- FLUX LoRA，https://fal.ai/docs/model-api-reference/image-generation-api/flux-lora

适合：

- 想做固定封面风格
- 想把头像贴纸风格或封面风格训练成可复用的 LoRA
- 想用 API 跑批量背景图

优点：

- 官方文档明确支持 LoRA
- 适合品牌风格和人物风格一致性
- 支持 `portrait_4_3` 和 `landscape_4_3` 这类尺寸

限制：

- 需要额外准备 LoRA 或固定风格输入
- 纯 API 出成品仍然不如后置排版稳定

## 模型市场型备选

### Replicate

参考：

- HTTP API，https://replicate.com/api
- Official models，https://replicate.com/docs/topics/models/official-models

适合：

- 你想快速试不同模型
- 你还没决定长期押哪家图像 API

优点：

- 试错成本低
- 多模型统一调用方式

限制：

- 更像模型集市，不是统一品牌工作流
- 长期一致性仍然要靠你自己的排版模板

## 真正推荐的工作室方案

如果你要做长期封面自动化，我建议这样：

### 第一层，`baoyu-danger-gemini-web` 出底图

- 输入，主题、风格、画幅
- 输出，不带大段中文标题的背景图

### 第二层，本地模板叠版

- 固定叠加你的头像贴纸
- 固定叠加标题区域
- 固定叠加分类标签
- 固定叠加产品名或主题词

### 第三层，人工过稿

- 看是否清晰
- 看是否过暗
- 看缩略图状态是否能读

## 为什么不建议模型直接生成完整中文封面

- 中文标题稳定性差
- 排版容易跑偏
- 字体风格不统一
- 同一账号长期看会失去固定识别

所以模型更适合做：

- 场景
- 氛围
- 人物姿态
- 背景层次

本地模板更适合做：

- 标题
- 头像贴纸
- 固定视觉资产
- 平台画幅适配

## 你的当前最优解

现在先这样跑：

1. 我给你封面提示词
2. 用 `baoyu-danger-gemini-web` 出图
3. 保留不带大字标题的背景图
4. 在本地或设计工具里叠加标题和头像贴纸

等你确定一两个稳定风格之后，再决定是否补 OpenAI Images API 或 fal.ai。
