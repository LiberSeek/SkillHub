---
name: sk-content-designer
description: |
  LiberSeek 工作室内容包装与封面设计 skill。用于制作图文封面、视频封面、图文卡片、信息图、贴纸资产和 Swiss 风格排版底图。适用于“做封面”“给这个主题出 3:4 和 4:3 两版”“做图文卡片”“整理贴纸”“做一张瑞士风信息图”这类请求。默认承接写作结果，把主题转成可发布的视觉资产。
---

# sk-content-designer

这是工作室的内容包装入口。

它把三类能力收拢到一起：

- `baoyu-danger-gemini-web` 风格的底图生成思路
- `guizang-ppt-skill` 的 Swiss / 杂志风排版模板
- 工作室自己的贴纸、封面、图文卡片脚本

## 什么时候用

- 要做封面
- 要做图文卡片
- 要做信息图
- 要整理贴纸资产
- 要给视频补一张平台封面

## 默认路线

先按两段式做，不要求模型一次出成品：

1. 先出底图
2. 再叠标题、贴纸、固定视觉元素

当前工作室默认风格：

- `Swiss`
- 竖版 `3:4`
- 高对比、强网格、信息优先

横版 `4:3` 继续保留，用作 B 站封面、桌面预览和横向补充分发。

## 工作流

### 1. 先选视觉路线

默认优先：

- 图文主图：Swiss 竖版 `3:4`
- 视频封面：`3:4` + `4:3` 双版

如果要走 PPT / 大图卡片风格，再读 `guizang` 相关参考。

### 2. 底图与叠版分离

底图来源可以是：

- Gemini Web
- ChatGPT / Gemini 网页版
- 其他图像模型

拿到底图后再用本地脚本处理统一风格。

### 3. 贴纸只放封面，不进正文

工作室贴纸默认作为品牌识别元素，优先固定在右下角。

如没有合适贴纸，可以退回 `base.png` 作为原始人物素材。

## 脚本

- `scripts/generate_studio_cover.py`
  根据主题配置输出 `3:4` / `4:3` 封面。
- `scripts/compose_studio_gemini_cover.py`
  把外部生成的底图和工作室文案、贴纸合成成品封面。
- `scripts/build_info_cover.py`
  做偏信息图风格的封面。
- `scripts/generate_studio_cards.py`
  做图文卡片。
- `scripts/process_stickers.py`
- `scripts/process_stickers_black_bg.py`
- `scripts/rename_stickers.py`
  处理贴纸重命名、去底和标准化。

`generate_studio_cover.py` 支持用 `STUDIO_COVER_CONFIG` 和 `STUDIO_STICKERS_ROOT` 指定配置和贴纸目录。

## 参考文件

- `references/cover-automation.md`
  封面主流程说明。
- `references/content-production-matrix.md`
  判断什么时候该做封面、卡片、信息图。
- `references/layouts-swiss.md`
- `references/themes-swiss.md`
- `references/swiss-layout-lock.md`
  Swiss 路线优先读这些。
- `references/image-prompts.md`
  需要整理底图提示词时读。
- `references/screenshot-framing.md`
  处理截图卡片或 CleanShot 风格背景时读。

## 资产

- `assets/template-swiss.html`
- `assets/template.html`
- `assets/screenshot-backgrounds/`

这些用于图文卡片、大图和网页式视觉资产，不需要全部加载进上下文，按需使用。
