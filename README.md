# LiberSeek SkillHub

`LiberSeek/SkillHub` 用来存放 LiberSeek 工作室可复用的 Codex skill。

每个 skill 都是一个独立目录，目录内至少包含一个 `SKILL.md`，并可按需附带 `references/`、`scripts/`、`assets/`、`templates/` 等资源文件。这个仓库的目标是把已经整理好的正式 skill 统一沉淀下来，方便安装、复用和持续迭代。

## 当前收录的 Skills

| Skill | 用途 |
| --- | --- |
| `sk-content-researcher` | 做选题、对标、爆款拆解、热点跟踪和系统研究 |
| `sk-content-writer` | 写图文稿、口播稿、标题、简介、标签和平台文案 |
| `sk-content-designer` | 做封面、图文卡片、信息图、贴纸资产、HTML deck 和可编辑 PPTX |
| `sk-minimal-zine-poster` | 把主题、文章或照片转成留白克制的极简 ZINE 海报并直接生成图片 |
| `sk-content-producer` | 把文稿转成配音、字幕和视频成片 |
| `sk-content-publisher` | 管理登录态、检查发布栈并分发到各内容平台 |
| `sk-image-creater` | 通过 OpenAI-compatible 图像接口生成或编辑图片 |
| `sk-industry-researcher` | 做行业研究、价值链梳理和专题型深度调研 |

## 安装方式

### 方式一：按 skill 单独安装

如果你只想安装某一个 skill，直接把对应目录复制到本地 Codex skills 目录即可。

```bash
mkdir -p ~/.codex/skills
cp -R sk-content-writer ~/.codex/skills/
```

安装完成后，目标结构应类似：

```text
~/.codex/skills/
└── sk-content-writer/
    └── SKILL.md
```

### 方式二：整仓克隆后按需软链接

如果你会持续维护这个仓库，推荐直接克隆，再把需要的 skill 软链接到本地 skills 目录。

```bash
git clone https://github.com/LiberSeek/SkillHub.git
mkdir -p ~/.codex/skills
ln -s /path/to/SkillHub/sk-content-designer ~/.codex/skills/sk-content-designer
ln -s /path/to/SkillHub/sk-content-producer ~/.codex/skills/sk-content-producer
```

这样更新仓库后，本地 skill 会自动跟着最新内容走，不需要重复复制。

## 如何使用

安装后，Codex 会把这些目录当作可发现的 skill 来源。通常不需要手动执行 `SKILL.md`，而是直接在对话里描述任务，让 agent 选择对应 skill。

常见用法示例：

- “帮我研究一下这个赛道，顺便拆 3 个对标账号”
- “把这篇内容改写成小红书图文稿，再给我 5 个标题”
- “基于这篇稿子做一张 3:4 的 Swiss 风封面”
- “把这篇内容做成一张旧纸质感的极简 ZINE 海报”
- “把这篇口播稿转成配音、字幕和一个竖屏视频”
- “检查一下发布栈，然后把这个 bundle 发到 X 和 B 站”
- “用 OpenAI-compatible 接口给我生成一张封面底图”

如果你希望显式指定 skill，也可以直接在任务中点名，例如：

- “用 `sk-content-researcher` 帮我做这家公司研究”
- “用 `sk-minimal-zine-poster` 把这句话做成一张 3:4 海报”
- “用 `sk-content-producer` 把这篇稿子做成视频”

## 目录约定

每个 skill 目录通常包含以下结构：

```text
sk-example/
├── SKILL.md
├── references/
├── scripts/
├── assets/
└── templates/
```

- `SKILL.md`：skill 的入口说明、适用场景和工作流
- `references/`：给 agent 加载的参考文档
- `scripts/`：该 skill 需要调用的脚本
- `assets/` / `templates/`：模板、视觉素材和静态资源

## 依赖与注意事项

不同 skill 可能依赖不同的本地或外部环境，常见包括：

- Python 或 Node.js 运行时
- 本地 shell 脚本执行环境
- 图像、音频、视频处理工具
- OpenAI-compatible API 或其他第三方服务
- 平台登录态、Cookie 或发布 CLI

使用前建议先阅读目标 skill 下的 `SKILL.md`，确认它依赖的脚本、输入格式和运行环境。

## 仓库说明

- 顶层 `manifest.md` 是本地维护用索引，不纳入仓库版本管理
- 生成产物和系统缓存文件默认不提交
- 提交前建议只暂存你确认需要公开的 skill 目录和文档
