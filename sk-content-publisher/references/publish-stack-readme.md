# 发布基础设施层

这个目录用于把图文内容统一发布到：

- 小红书
- 推特 / X
- 抖音
- 快手
- Bilibili

## 它在整个工作区里的角色

- 这里放的是“怎么发”
- 真正的内容资产现在统一放在顶层 `products/`
- 也就是说：`publish-stack` 是基础设施层，不再是内容主目录

顶层工作区入口：

- 工作区根目录下的 `README.md`

当前 canonical 内容样例：

- `products/<product>/topics/<yyyy-mm-dd-topic-slug>/`

## 当前主线

- 小红书 / 抖音 / 快手：`social-auto-upload`
- 推特 / X：`twitter-cli`
- Bilibili：`bilibili-cli`

`opencli` 先不作为今天的主线，因为它更适合做浏览器自动化 hub，不是这次最短上线路径。

## 已准备好的东西

- `tools/social-auto-upload/conf.py`
- `bin/login_all.sh`
- `bin/check_stack.sh`
- `bin/publish_bundle.sh`
- `content-bundles/example-post/`

补充：

- `content-bundles/example-post/` 是一个工具侧快捷入口
- canonical 路径已经迁到顶层 `products/` 下

## 第一次使用

1. 复制环境文件

```bash
cd <workspace>/tools/publish-stack
cp .env.example .env
```

2. 登录 4 个国内平台和 B 站

```bash
./bin/login_all.sh
```

补充：

- `twitter-cli` 复用浏览器 cookies，不单独弹登录流程
- 只要你的 Chrome 已登录 X，后面执行 `twitter status` 能通过就可以

3. 检查状态

```bash
./bin/check_stack.sh
```

## 发布一条内容

把内容做成一个 bundle 目录，至少包含：

```text
bundle-name/
├── title.txt
├── note.txt
├── twitter-article.md
├── bilibili.txt
└── images/
    ├── 01.png
    ├── 02.png
    └── 03.png
```

然后执行：

```bash
./bin/publish_bundle.sh ./content-bundles/example-post
```

如果你这次只想发一部分平台，可以显式指定：

```bash
./bin/publish_bundle.sh \
  --platforms douyin,kuaishou,x,bilibili \
  ./content-bundles/example-post
```

## 平台注意事项

### 小红书 / 抖音 / 快手

- 统一走图文命令 `sau <platform> upload-note`
- 图片数量不要太少，建议 3 张以上
- 标题和正文会直接取 `title.txt` 和 `note.txt`
- 如果不想误发某个平台，比如这次不发小红书，就用 `--platforms` 明确收窄范围
- 抖音和快手的话题 / Tag 总数上限按 `4` 处理
- 这里的 `4` 是总数，不是“额外可加 4 个”；正文里自带的 `#标签` 和发布时额外补的话题要一起算
- 所以发抖音或快手时，`note.txt` 末尾不要再堆很多 `#标签`，否则很容易出现“点了发布没反应”或被平台静默拦截
- 抖音默认改成“工具填内容，你手动收尾”的流程：脚本会填好图文、标题、正文和封面，然后停在发布页
- 你在抖音发布页里自己选背景音乐，再手动点最终 `发布`
- 如果你临时真的想恢复抖音自动发布，可以在命令前加 `DOUYIN_MANUAL_FINALIZE=0`

### 推特 / X

- 默认主线是 `X Article`
- 会优先读取 `twitter-article.md`
- 推荐形态是：**长文 + 1 张封面图**
- X 未来默认只发送长文本
- 工作室图文稿正文，默认直接复用为 `twitter-article.md` 的正文，不再单独重写一版 X 正文
- `twitter-article.md` 用 Markdown frontmatter 写标题和封面图：

```md
---
title: 你的文章标题
cover_image: ./images/x-cover.jpg
---

# 你的文章标题

正文从这里开始写。
```

- 如果你提供了 `twitter-article.md`，`publish_bundle.sh` 会调用 X Article 草稿流程，**默认只填充内容，不自动点击最终发布**
- 正文里如果不想再插图，就不要写 `![](...)`
- 如果你仍然只想发传统短帖，保留 `twitter.txt` 也兼容；但这只作为历史兼容，不再是工作室默认发布形态
- 如果同一主题同时做图文分发和 X Article，优先共用同一份主正文，只在平台简介和结尾收束上做轻微调整

推荐封面图要求：

- 比例：优先 `4:3`
- 尺寸：建议 `1600x1200`、`2048x1536` 或同等 `4:3` 尺寸
- 格式：`JPG` 或 `PNG`
- 关键主体放在中间安全区，避免预览裁切
- 同一主题仍然必须保留一张 `3:4` 竖版封面，供图文平台主分发使用

### Bilibili

- 今天先走 `bili dynamic-post`
- 这是文字动态，不是视频投稿
- 文案读取 `bilibili.txt`

## 这套方案的边界

- 今天能跑通的是“图文 / 动态 / X Article 草稿填充”的统一发布
- `social-auto-upload` 目前对 Bilibili 的主线还是视频上传，不是图文
- 所以 B 站今天走 `dynamic-post`，这是最短路径
