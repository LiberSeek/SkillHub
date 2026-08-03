---
name: sk-minimal-zine-poster
description: LiberSeek 工作室极简 ZINE 海报生成 skill。把主题、句子、物件、情绪、文章观点、照片或内容 brief 编译成带大面积留白、旧纸质感、实验排版、单一高饱和色锚点的编辑海报提示词，并直接生成位图。适用于“做一张极简 ZINE 海报”“做日系或韩系独立杂志风封面”“把这篇内容变成旧纸海报”“用这张照片做留白很多的编辑设计”“给图文内容做安静克制的 3:4 封面”这类请求。
---

# LiberSeek Minimal Zine Poster

把用户内容压缩成一个可成像的视觉隐喻，交付最终提示词和生成后的海报图像。除非用户明确只要 prompt，否则不要停在提示词阶段。

## 读取顺序

1. 开始设计前读取 `references/visual-grammar.md`。
2. 写最终提示词前读取 `references/prompt-compiler.md`。
3. 只有需要追溯来源或分发本 skill 时才查看 `LICENSE`。

## 默认决策

- 使用 `Standard` 模式。
- 社交媒体封面默认 `3:4`；B 站或桌面横图用 `4:3`；用户明确要求原版比例时用 `3:5`。
- 默认色锚为 LiberSeek 的 `IKB / #002FA7`，每张图只保留一个高饱和主色。
- 默认只放一条短句和少量半可读微型文字；不要让图像模型排长文。
- 默认生成一张图。批量任务必须改变视觉语法，不只是移动主体。
- 工作室署名仅在用户需要品牌版时添加。优先在生成后排版阶段叠加小型 `LIBERSEEK / FIELD NOTES`，不要让模型伪造 logo。

## 工作流

### 1. 提炼内容

提取：

- 一个核心主题或情绪
- 一句必须保留的短文字，如用户提供
- 一个能被直接画出来的物件、片段或关系
- 参考图的用途：主体、质感、构图或人物一致性

文章或复杂观点只取一个视觉命题，不要试图把全文画进一张海报。

### 2. 选择视觉配方

从 `references/visual-grammar.md` 各选一个：

- layout
- anchor
- typography
- texture
- mood
- accent

先回看本轮已生成结果，避免连续使用同一配方。内容较弱时优先减少文字和装饰，不要增加拼贴元素来填满画面。

### 3. 编译提示词

按 `references/prompt-compiler.md` 的四段结构写最终 prompt：

1. 画布、纸张、留白和视觉簇位置
2. 主体隐喻、锚点形态和纸上处理方式
3. 字体系统、准确色锚和印刷瑕疵
4. 平面扫描观感、情绪和 avoid-list

提示词必须说明主体大小、位置、色锚材质和大致占比。描述像素里能出现的内容，不写设计解释或工作过程。

### 4. 生成图像

优先使用当前环境内置的图像生成或编辑能力。若环境没有内置能力，但已安装同仓库的 `sk-image-creater`，使用其脚本：

```bash
python3 /path/to/sk-image-creater/scripts/generate_image.py \
  --prompt "<final-prompt>" \
  --model gpt-image-2 \
  --size 3:4 \
  --outdir ./generated-images
```

有参考图时使用支持图像输入的编辑接口，不要只把图片路径写进文字 prompt。凭据缺失时说明需要的配置，不要把密钥写入 skill 或产物。

若用户提供内容 bundle，把成品放进该 bundle 的图片目录；否则保存到任务工作目录，并使用可辨认文件名，例如 `minimal-zine-3x4.png`。

### 5. 视觉验收

生成后检查缩略图和原图。出现以下任一问题时，收紧 prompt 并最多重生成一次：

- 留白不足 70% 或主体接近满版
- 色锚消失、发灰或缩小到不可见
- 画面变成商业广告、电影海报、3D 场景或密集手账拼贴
- 文字过长、乱码成为主视觉噪声
- 纸张出现样机边框、桌面背景或强投影

### 6. 交付

返回：

1. 可直接查看的生成图
2. 实际使用的最终 prompt
3. `layout / anchor / typography / accent / texture / mood` 配方
4. 一句内容转译说明

## 质量门槛

- 画面是否仍是稀疏的纸张编辑海报？
- 是否有 70%-90% 的有效留白？
- 视觉簇是否只占约 8%-25%？
- 是否只有一个明确、可成像的视觉隐喻？
- 是否有旧照片、剪报、复印、孔版、网点或扫描纸张处理？
- 是否只有一个缩略图下仍清楚的高饱和色锚？
- 是否避开商业标题层级、CTA、光泽样机、3D、霓虹、电影光效、可爱卡通和长段文字？
- 是否真的生成并检查了图像，而不只是返回 prompt？

## 输出格式

````markdown
**生成图**

![LiberSeek minimal zine poster](/absolute/path/to/image.png)

**最终 Prompt**

```text
[actual prompt used]
```

**配方**

`layout / anchor / typography / accent / texture / mood`

[一句内容转译说明]
````

## 来源与许可

本 skill 基于 [LiamGvchi/gc-minimal-zine-poster](https://github.com/LiamGvchi/gc-minimal-zine-poster) 的视觉语法改造，并接入 LiberSeek 工作室规范。上游版权声明与 MIT 许可保留在 `LICENSE`。
