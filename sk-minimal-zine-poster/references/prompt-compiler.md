# Prompt Compiler

## 编译原则

只写最终会成为像素的内容。不要写来源路径、样本数量、设计分析、检查清单或“为什么这种风格有效”。不要逐句模仿示例 prompt。

先确定以下字段，再合并成四段紧凑 prompt：

1. `canvas`：比例、整张旧纸表面、无边框和无样机
2. `attention geometry`：留白比例、视觉簇占比和明确位置
3. `image anchor`：一个可成像主体或关系
4. `anchor treatment`：剪报、影印、孔版、网点、油墨或扫描处理
5. `typography`：字体类型、短句、微型字和空间行为
6. `color`：准确颜色、物质形态和画面占比
7. `reproduction`：平视扫描、纸纤维、漫射光和低到中对比
8. `emotional temperature`：识别物件之前先感受到的情绪
9. `hard avoids`：明确禁止的视觉结果

## 四段结构

### 第一段：画布和注意力几何

说明：

- `3:4`、`4:3` 或用户指定比例
- full-frame aged paper
- 70%-90% 留白
- 8%-25% 的视觉簇及其具体方位
- no border, no mockup, no edge-hugging

### 第二段：主体和纸上处理

把主题转成一个具体隐喻，说明主体是什么、如何裁切、如何印在纸上。避免抽象口号和整场景叙事。

### 第三段：文字、色锚和印刷缺陷

必须写明：

- 一条短句或极小题注
- 字体与排版行为
- 精确的高饱和色，如 `fully saturated IKB cobalt blue #002FA7`
- 色锚的物质形态，如 `opaque risograph ink` 或 `flat paper cutout`
- 色锚约占全画面的 0.8%-2.5%，或视觉簇的 15%-35%
- 一到两种印刷缺陷，不要把所有纹理同时堆上去

### 第四段：扫描观感、情绪和禁用项

说明 flat orthographic scan、matte absorbent paper、diffuse light、quiet archival mood，并给出短 avoid-list。

## 文字规则

- 用户提供准确短句时原样保留。
- 没有文案时，生成一句短中文或英文诗性短句。
- 主短句尽量不超过 12 个汉字或 6 个英文单词。
- 微型字允许半可读；重要信息不要依赖图像模型准确排版。
- 需要品牌署名时，先生成无品牌底图，再用排版工具叠加 `LIBERSEEK / FIELD NOTES`。

## 模板

```text
[aspect-ratio] full-frame aged [paper-tone] paper poster, flat scanned surface with no border or mockup. Keep [70%-90%] as quiet negative space. Place one compact visual cluster occupying [8%-25%] at [position], with comfortable distance from every edge.

Translate [theme] into [one concrete object/relation]. Render it as [anchor type] using [one or two paper/print treatments]. Keep the subject isolated and small; do not expand it into a complete illustrated scene.

Set the exact phrase "[short text]" in [type mode], with optional fragmented archive microtext. Use one fully saturated [exact hue and hex] [material form], occupying about [share] of the canvas or cluster. Add [selected print defects] while preserving the color anchor's opacity and saturation.

Flat orthographic paper scan, matte absorbent fibers, diffuse light, low-to-medium contrast in the paper and grayscale elements, [mood] editorial zine atmosphere. Avoid full-bleed scenes, commercial headline hierarchy, product ads, logo/CTA, glossy mockups, cinematic lighting, 3D, neon, cute illustration, dense collage, many colors, and long clean text.
```

## 缩略图强化

如果第一次生成中色锚缺失、发灰或缩成不可见标记，把第三段改成更明确的词：

- `fully saturated`
- `opaque`
- `substantial flat cutout`
- `clearly visible at thumbnail size`
- `occupying about 2% of the entire canvas`

只强化主色和面积，不增加第二种颜色。
