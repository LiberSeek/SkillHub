---
name: sk-content-designer
description: |
  LiberSeek 工作室内容包装与封面设计 skill。用于制作图文封面、视频封面、图文卡片、信息图、贴纸资产、HTML slide deck，以及 Swiss 风格和备忘录摘录卡风格的排版底图。也用于个人 IP 的角色定妆图、参考图变体、梦境身份图和系列封面。适用于“做封面”“给这个主题出 3:4 和 4:3 两版”“做图文卡片”“做一张备忘录风摘录图”“做一个浏览器可演讲的 deck”“导出可编辑 PPTX”“整理贴纸”“做一张瑞士风信息图”“给我做宇航员 / 钢琴家 / 侠客形象图”这类请求。默认承接写作结果，把主题转成可发布的视觉资产。
---

# sk-content-designer

这是工作室的内容包装入口。

它把三类能力收拢到一起：

- `baoyu-danger-gemini-web` 风格的底图生成思路
- `chatgpt-proxy` 风格的 OpenAI-compatible 出图后端
- `guizang-ppt-skill` 的 Swiss / 杂志风排版模板
- `huashu-design` 的设计方向顾问、HTML-first deck 与 PPTX 导出约束
- 工作室自己的贴纸、封面、图文卡片脚本

## 什么时候用

- 要做封面
- 要做图文卡片
- 要做信息图
- 要做备忘录风摘录卡 / memo-note 卡片
- 要做个人 IP 角色设定图 / 定妆图
- 要根据真人参考图生成稳定风格的角色图
- 要整理贴纸资产
- 要给视频补一张平台封面
- 要做 HTML 幻灯片或浏览器可演讲 deck
- 要导出可编辑 PPTX

## 默认路线

先按两段式做，不要求模型一次出成品：

1. 先出底图
2. 再叠标题、贴纸、固定视觉元素

当前工作室默认风格：

- `guizang-ppt-skill` 的 `Swiss`
- 主题色默认 `IKB / #002FA7`
- 竖版 `3:4`
- 高对比、强网格、信息优先

横版 `4:3` 继续保留，用作 B 站封面、桌面预览和横向补充分发。

如果内容更偏：

- 阅读摘录
- 长文摘要
- 金句拆解
- 财经 / 人文 / 观察类慢节奏图文

则增加第二条默认路线：

- `memo-note`
- 配色默认 `references/themes.md` 里的 `Kraft Paper`
- 竖版 `3:4`
- 纸张质感、摘录优先、装饰克制

如果任务更偏：

- 个人故事
- 个人风格写真
- 系列化身份图
- 梦境主题角色图
- “同一个人，不同职业 / 不同幻想身份”

则增加第三条默认路线：

- `personal-ip`
- 先锁定人物一致性，再做风格扩写
- 先出角色定妆图，再出封面图和系列图
- 先选出图后端，再做版式和贴纸合成

如果任务不是封面而是整套视觉表达，优先按下面的次序推进：

1. 先确认有没有现成设计上下文、品牌资产或参考截图
2. 没有上下文时，先用设计方向顾问给 3 个风格方向
3. 大于 5 页的 deck，先做 2 页 showcase 定 grammar
4. 再批量生产剩余页面或封面变体

## 工作流

### 1. 先选视觉路线

默认优先：

- 图文卡片：`guizang` 的 `template-swiss.html`
- 备忘录摘录卡：`template-memo-note.html`
- 个人 IP 形象图：先读 `references/personal-ip-workflow.md`
- 图文主图：`guizang` 的 `Swiss` 竖版 `3:4`
- 视频封面：`guizang` 的 `Swiss` + `3:4` / `4:3` 双版

默认锚点色直接用 `references/themes-swiss.md` 里的 `IKB / #002FA7`，除非用户明确指定改成另外 3 套预设之一。

如果用户提到：

- 备忘录
- 读书摘录
- 公众号摘录图
- 像纸张一样的卡片
- warm paper / memo-note / excerpt card

优先切到 `template-memo-note.html`，并先读 `references/memo-note-style.md`。

如果用户提到：

- 参考我的照片做形象图
- 做宇航员 / 钢琴家 / 侠客版本
- 个人 IP
- 小小罗
- 梦境系列 / 一千零一夜

优先走 `personal-ip` 路线，并先读：

- `references/personal-ip-workflow.md`
- `references/character-consistency.md`
- `references/image-backends.md`

先判断该任务更适合：

1. `gemini-web`
2. `chatgpt-proxy`
3. `manual-compose`

再决定是否要先做底图，再叠标题与贴纸。

如果要走 PPT / deck / 大图卡片风格：

- 先读 `references/design-workflow.md`
- 再读 `references/slide-decks-html-first.md`
- 如需可编辑导出，再读 `references/editable-pptx.md`

### 2. 底图与叠版分离

如果是封面或图文卡片，优先顺序改成：

1. 先用 `guizang` 版式做主视觉、层级和留白
2. 再补标题、摘要、数据点
3. 最后再叠工作室贴纸

只有在需要快速占位、当天先发、来不及做 `guizang` 版式时，才退回程序化封面脚本。

备忘录摘录卡不追求复杂底图，优先用固定视觉语法：

1. 牛皮纸或暖米纸背景
2. 深棕字色
3. 大段摘录或结论居中
4. 固定阅读信息行
5. 手写感下划线或边注
6. 可选工作室贴纸，只建议放封面页

个人 IP 视觉任务优先用三段式：

1. 先锁人物一致性
2. 再出 archetype 角色图
3. 最后合成封面或系列标题页

如果参考图还不够稳定，不要立刻批量出图，先产 2 到 4 张定妆图定人物 grammar。

### 3. 贴纸只放封面，不进正文

工作室贴纸默认作为品牌识别元素，优先固定在封面的右下角。

图文卡片正文默认不加贴纸，避免干扰信息层级。

如没有合适贴纸，可以退回 `base.png` 作为原始人物素材。

### 4. Deck 默认 HTML-first

如果任务是幻灯片或提案，不要先想 PPT 软件。

默认路线是：

1. 每页独立 HTML
2. 用 `assets/deck_index.html` 聚合成浏览器演讲版
3. 如需做多版本对比，用 `assets/design_canvas.jsx`
4. 只有在接收方明确要继续改字时，才走 `scripts/export_deck_pptx.mjs`

走可编辑 PPTX 时，HTML 必须从第一行就遵守硬约束，不要事后补救。

## 脚本

- `scripts/generate_studio_cover.py`
  根据主题配置输出 `3:4` / `4:3` 快速占位封面。
- `scripts/compose_studio_gemini_cover.py`
  把外部生成的底图和工作室文案、贴纸合成成品封面。
- `scripts/build_info_cover.py`
  做偏信息图风格的封面。
- `scripts/generate_studio_cards.py`
  做图文卡片。
- `scripts/providers/chatgpt_proxy.py`
  通过 OpenAI-compatible / ChatGPT 代理接口出图。
- `scripts/providers/gemini_web.ts`
  调用 `baoyu-danger-gemini-web` 镜像脚本做 Gemini Web 出图。
- `scripts/providers/route_image_backend.py`
  在 `chatgpt-proxy / gemini-web / manual-compose` 间路由。
- `scripts/character/build_character_sheet.py`
  为个人 IP 生成角色设定卡。
- `scripts/character/build_archetype_prompts.py`
  为宇航员、钢琴家、侠客等 archetype 生成提示词包。
- `scripts/character/render_personal_cover.py`
  把角色底图、标题和贴纸合成个人系列封面。
- `scripts/export_deck_pptx.mjs`
  将符合约束的多页 HTML deck 导出为可编辑 PPTX。
- `scripts/html2pptx.js`
  `export_deck_pptx.mjs` 依赖的 DOM 转 PPTX 引擎。
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
- `references/design-workflow.md`
  设计任务的提问方式、showcase 节奏和变体策略。
- `references/image-backends.md`
  图片后端选择策略、环境变量和调用建议。
- `references/personal-ip-workflow.md`
  个人 IP 图像生产流程，适用于角色图、系列图、梦境身份图。
- `references/character-consistency.md`
  控制人物脸型、气质、道具和 taboo drift 的规则。
- `references/memo-note-style.md`
  备忘录风、摘录卡、阅读卡的固定视觉语法。
- `references/design-directions.md`
  20 种设计哲学，用于没有明确风格时先定方向。
- `references/slide-decks-html-first.md`
  HTML-first deck 工作流。
- `references/editable-pptx.md`
  可编辑 PPTX 的硬约束和导出规则。
- `references/layouts-swiss.md`
- `references/themes-swiss.md`
- `references/swiss-layout-lock.md`
  Swiss 路线优先读这些。默认先选 `IKB / #002FA7`。
- `references/image-prompts.md`
  需要整理底图提示词时读。
- `references/screenshot-framing.md`
  处理截图卡片或 CleanShot 风格背景时读。

## 资产

- `assets/template-swiss.html`
- `assets/template-memo-note.html`
- `assets/template.html`
- `assets/deck_index.html`
- `assets/deck_stage.js`
- `assets/design_canvas.jsx`
- `assets/screenshot-backgrounds/`

这些用于图文卡片、大图、deck 和网页式视觉资产，不需要全部加载进上下文，按需使用。
