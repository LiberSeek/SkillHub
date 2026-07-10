# Image Backends

`sk-content-designer` 现在内置三条图片后端路线：

1. `gemini-web`
2. `chatgpt-proxy`
3. `manual-compose`

## 什么时候选哪条

### gemini-web

适合：

- 需要参考图理解
- 要快速试很多风格
- 已经有 Google 账号和 cookie
- 想复用 `baoyu-danger-gemini-web` 的能力

优先脚本：

- `scripts/providers/gemini_web.ts`

### chatgpt-proxy

适合：

- 已经有稳定的 OpenAI-compatible 中转接口
- 想统一接入你自己的反向代理
- 想把个人 IP 出图、封面底图、角色图都走同一条后端

优先脚本：

- `scripts/providers/chatgpt_proxy.py`

### manual-compose

适合：

- 底图已经由外部人工生成
- 只需要叠标题、贴纸、系列信息
- 只做封面合成，不做模型出图

优先脚本：

- `scripts/character/render_personal_cover.py`
- `scripts/compose_studio_gemini_cover.py`

## 默认选择策略

1. 有真人参考图，先看是否要锁角色一致性
2. 如果要锁一致性，先选 `chatgpt-proxy` 或 `gemini-web`
3. 如果已有可用底图，则退到 `manual-compose`
4. 如果要批量测试风格，先选 `gemini-web`
5. 如果要纳入工作室自己的中转能力，优先选 `chatgpt-proxy`

## 环境变量

### chatgpt-proxy

- `CONTENT_DESIGNER_CHATGPT_BASE_URL`
- `CONTENT_DESIGNER_CHATGPT_API_KEY`
- `CONTENT_DESIGNER_CHATGPT_IMAGE_MODEL`
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`

### gemini-web

- `GEMINI_WEB_DATA_DIR`
- `GEMINI_WEB_COOKIE_PATH`
- `GEMINI_WEB_CHROME_PROFILE_DIR`
- `GEMINI_WEB_CHROME_PATH`
- `HTTP_PROXY`
- `HTTPS_PROXY`

### router

- `CONTENT_DESIGNER_DEFAULT_IMAGE_BACKEND`
  可选：`chatgpt-proxy`、`gemini-web`、`manual-compose`

## 注意

- 后端负责“产图”，不是最终交付。
- 最终交付依旧要回到 `sk-content-designer` 的排版、标题、贴纸和比例控制流程里。
- 个人 IP 内容默认先锁脸，再谈风格。
