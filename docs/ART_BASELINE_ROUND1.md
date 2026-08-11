# 《代书》美术生成首轮基线（Anything XL）

本文用于首轮美术素材批量生成，目标是先拿到一批可用候选素材，再进行二次筛选与游戏内替换。

## 1. 首轮目标与产出

- 生成三类核心素材：毛笔光标、信纸纹理、书法字库。
- 每类先生成 5 张候选图（共 15 张）。
- 统一输出到 `assets/images/generated/` 目录，便于后续接入场景。

## 2. 统一参数（基线）

优先在 Anything XL Web 界面中固定以下参数：

- 分辨率：`832x832`（8GB 显存更稳）
- 步数：`28`
- CFG：`7.0`
- Sampler：保持默认
- Seed：`-1`（随机）先跑首轮
- CPU offload：开启（若有对应选项）

若显存稳定且希望更细节，可二轮提升到 `1024x1024`。

## 3. 通用负面提示词

```text
lowres, blurry, text, watermark, logo, signature, jpeg artifacts, bad anatomy, deformed, extra fingers, cropped, worst quality
```

## 4. 三类素材提示词模板（每类 5 条）

### 4.1 毛笔光标动画帧（cursor）

风格目标：黑墨、透明背景倾向、边缘清晰、适合做精灵帧。

1)
```text
single Chinese calligraphy brush stroke cursor icon, black ink, dry brush texture, minimal, high contrast, isolated, transparent background style
```

2)
```text
ink brush tip mark, dynamic stroke, Chinese painting style, monochrome black, clean silhouette, isolated object, transparent background style
```

3)
```text
small calligraphy brushstroke symbol, sharp edge, subtle ink diffusion, minimal UI asset style, black on transparent background style
```

4)
```text
flying ink stroke shape, elegant Chinese brush line, game cursor asset, high contrast black ink, isolated
```

5)
```text
brush cursor frame, handcrafted ink stroke, slight variation angle, anime game UI asset, isolated black ink mark
```

建议：从 5 张中挑 3 张做序列帧（轻微角度或形态变化），后续在 Godot 里做动画。

### 4.2 信纸纹理（paper）

风格目标：古风、米黄、低对比噪点、可平铺或大图裁切。

1)
```text
ancient Chinese rice paper texture, warm beige, subtle fiber grain, soft stains, high detail, seamless texture style
```

2)
```text
old letter paper background, handmade xuan paper fibers, light yellow tone, gentle aging marks, no text, no border
```

3)
```text
vintage Chinese stationery paper, soft ink bleed traces, natural fiber pattern, flat top view, texture scan style
```

4)
```text
clean parchment for calligraphy, mild wrinkles, warm off-white, balanced grain noise, game background texture
```

5)
```text
traditional East Asian writing paper texture, subtle worn corners, paper fibers, neutral lighting, high resolution
```

建议：后续在图像工具中做无缝化处理，得到可重复铺贴底图。

### 4.3 书法字库素材（calligraphy）

风格目标：单字或短词，黑墨，笔锋明显，高可读性，便于切图。

1)
```text
Chinese calligraphy character on plain background, bold black ink, clear brush rhythm, high contrast, centered composition
```

2)
```text
handwritten Chinese ink character, elegant stroke order feel, xuan paper background, minimal composition, no seal
```

3)
```text
traditional brush script Chinese glyph, sharp and flowing strokes, monochrome ink, isolated character
```

4)
```text
calligraphy style Chinese word, clean spacing, black ink texture, legible strokes, high resolution
```

5)
```text
ink calligraphy symbol set style, single character focus, subtle dry brush effect, centered, no decoration
```

建议：首轮先验证风格，不要求覆盖全字库。二轮再按游戏词汇表批量生产。

## 5. 文件命名规范

统一命名，便于筛选与导入：

- 光标：`cursor_r1_01.png` ~ `cursor_r1_05.png`
- 信纸：`paper_r1_01.png` ~ `paper_r1_05.png`
- 字库：`calligraphy_r1_01.png` ~ `calligraphy_r1_05.png`

存放目录：

- `assets/images/generated/cursor/`
- `assets/images/generated/paper/`
- `assets/images/generated/calligraphy/`

## 6. 验收标准（首轮）

每类至少保留 2 张可用图，满足：

- 无明显畸形/错字/乱码
- 画面清晰，无水印和签名
- 风格统一（古风、墨感）
- 在游戏中缩放后仍可辨识

## 7. 接入建议（下一步）

1. 先替换 `letter` 场景背景纸纹，观察文本可读性。  
2. 选 3 帧光标图做 Godot 动画资源。  
3. 将可用书法字素材映射到常用词槽位（称谓/正文/落款），做小范围 A/B 测试。  
