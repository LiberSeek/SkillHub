---
name: sk-content-publisher
description: |
  LiberSeek 工作室内容分发 skill。用于把已经生产完成的 bundle 发布到小红书、抖音、快手、X 和 Bilibili，并负责登录检查、账号状态检查、bundle 目录初始化和平台差异化发布。适用于“发到 X 和 B站”“检查发布栈”“登录账号”“发布这条图文”“把这个 bundle 推出去”这类请求。
---

# sk-content-publisher

这是工作室内容操作系统里的分发入口。

它整合了：

- `publish-stack` 的 bundle 规范
- `social-auto-upload` 的国内平台发布流程
- `twitter-cli` 的 X 发布方式
- `bilibili-cli` 的 B 站动态能力

## 什么时候用

- 内容已经生产完成
- 需要检查账号登录状态
- 需要初始化新主题的发布目录
- 需要多平台发布

## 默认平台主线

- 小红书 / 抖音 / 快手：`social-auto-upload`
- X：优先 `twitter-cli`，如果是长文则走 `baoyu-post-to-x` 的 article 脚本
- Bilibili：当前 baseline 先走 `bili dynamic-post`

## Bundle 约定

至少准备：

- `title.txt`
- `note.txt`
- `twitter-article.md` 或 `twitter.txt`
- `bilibili.txt`
- `images/`

## 脚本

- `scripts/check_stack.sh`
  检查 SAU、twitter-cli、bilibili-cli 状态。
- `scripts/login_all.sh`
  登录国内平台和 B 站。
- `scripts/publish_bundle.sh`
  把一个 bundle 发到多平台。
- `scripts/new_topic.sh`
  初始化主题目录。

这些脚本支持通过环境变量指定依赖位置：

- `SAU_ROOT`
- `X_POST_TO_X_DIR`
- `ACCOUNT_NAME`

如果不传，默认优先回退到 `skillhub/vendors/mirrors/` 下的镜像仓库。

## 工作流

### 1. 先检查栈

先跑：

- `scripts/check_stack.sh`

如果国内平台 cookie 失效，再跑：

- `scripts/login_all.sh`

### 2. 再发 bundle

主脚本：

- `scripts/publish_bundle.sh`

可以全平台发，也可以用 `--platforms` 缩小范围。

默认策略已经切成草稿优先：

- 小红书 / 抖音 / 快手：优先保存草稿
- X：优先走 article 草稿页填充
- Bilibili：默认只保留人工发送稿，不自动直发

### 3. 平台差异不要强行统一

- 默认 `draft` 模式下不追求“一键发出”，而是追求“稿件已经进平台草稿态，最后一步交给人”
- 抖音默认优先存草稿；如果页面结构变化，脚本退回到填完内容后停在发布页
- 快手 / 抖音的标签总数按 4 个内处理
- X 默认优先中文普通帖或中文长文
- B 站当前 baseline 不默认自动直发

## 参考文件

- `references/publish-stack-readme.md`
- `references/content-ops-checklist.md`

平台细节按需读取：

- `references/xiaohongshu/`
- `references/douyin/`
- `references/kuaishou/`
- `references/bilibili-sau/`
- `references/x/`
- `references/bilibili-cli/`
- `references/xiaohongshu-cli/`

## 示例

脚本模板在：

- `scripts/examples/`

这里只作为命令参考，不要默认全部执行。
