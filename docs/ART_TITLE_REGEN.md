# 画风统一作业单（**水墨风方向**，2026-10-12 修订）

> 本文件最初是为「标题底图 `main.png` → 像素插画风」建的（**方案 A**）。
> **2026-10-12 用户改选水墨风**，方向随之调整：**保留 `main.png`（水墨）当锚点，
> 改把主界面 `main_bg.png` 从像素风重做成水墨风**（即原方案 B）。
> 原因：实测本机 SD 底模全是动漫/国风插画，**水墨是它们的强项，像素风是它们做不到的**（见 §0）。
>
> - 建单：2026-10-12 ｜ 修订：2026-10-12（改方向）
> - **只出 1 张图**：主界面背景 `main_bg.png`
> - 目的：**统一画风**（**不是**去水印 —— 水印那轮已解决）
> - 锚点：现有 `main.png`（相邻差 12.1 / 平坦区 14.0% / 平均色 `#a29a81`）
> - 好消息：`main.tscn` 用的是 `stretch_mode = 5`（KEEP_ASPECT_CENTERED）
>   —— **比例不符只会留黑边，不会变形**（比标题页 `stretch_mode=0` 安全）

---

## 0. 先看这里：**本机 SD 能跑，但底模不对**（2026-10-12 实测）

⚠️ **这一节是实测结论，先读完再决定谁来出图。**

本机**装着完整的 Stable Diffusion WebUI**（绘世启动器），且我**已经把它跑通并实际出过图**：

| 事实 | 值 |
|---|---|
| 位置 | `D:\绘世启动器`（SD WebUI v1.10.1）|
| 便携 Python | `D:\绘世启动器\.ext\python.exe`（3.10.11，**依赖完整**，无需建 venv）|
| GPU | RTX 2060 SUPER **8GB**（`torch 2.3.1+cu121`、`xformers 0.0.27`）|
| 出图速度实测 | SDXL 1152×648 / 28 步 ≈ **24 秒/张**；SD1.5 国风 ≈ **13 秒/张** |
| 已验证 | API 可调（`/sdapi/v1/txt2img`），出图落盘正常 |

### 实测（一）：像素风方向 —— 本机**做不到**

已装底模全为动漫/国风。用 `art_check style` 量化（基准 `main_bg.png` 相邻差 6.3）：

| 出图 | 相邻差 | 与基准比值 | 硬边 |
|---|---|---|---|
| 基准 `main_bg.png` | 6.3 | — | **0.1%** |
| 本机出图 ①②③ | 30~34 | **4.8~5.4×** | **8.7~11.9%** |

相邻差 5 倍、硬边 **90 倍** —— 是"抖动噪点"而非"平坦色块"。
且提示词 `upper-center empty for a title` **对动漫底模无效**：三张的上中全被楼阁占满。

### 实测（二）：水墨风方向 —— 风格能做，**内容不达标**（12 张正式尺寸全废）

用户改选水墨方向后，我用 `国风武侠Chinese style`（SD1.5）与 SDXL 出了 **12 张 1152×648**，
**逐张目视复核**。结论明确：

| 方案 | 数值判据 | 目视 | 失败原因 |
|---|---|---|---|
| 内景 + 书案（英文）| 比值 1.16 ✅ | ❌ | **画面里有一个人物伏案写字** —— 主界面是"玩家当先生"，画里别人在写字语义不对，且人物压在 UI 面板区 |
| 内景 + 书案（中文）| 比值 **1.19** ✅ | ❌ | **画成三个动漫人物**（武侠语料带偏）；蓝金高饱和，与目标 `#a29a81` 暖灰完全不同 |
| 空场景（v2）| 比值 0.82 ✅ | ❌ | **过度纠正**：出成一排空白纸/木板，"书信铺"不成立 |
| 内景 v3 | 比值 1.26 | ❌ | 结构发闷 + **紫色/品红伪影**（VAE 解码不良）|
| 纸本 + 淡墨 | 比值 **0.92** ✅ | ❌ | **纸上出现书法字 + 红色印章** —— 触发 §一 硬规矩（禁文字）|
| 纸本（其余 2 张）| 0.73 / 1.16 | ❌ | 过亮、硬线、或近乎全空 |

⚠️ **必须记住的教训：数值判据会给出假阳性。**
`art_check style` 只量"笔触密度/平坦度"，**不看画面内容** ——
那张"三个动漫人物"的图拿了**最好的数值之一（1.19×）**，仍被判"✅ 同族"。
**判据是"画风一致"的必要条件，不是充分条件；每张仍须人眼复核内容与文字。**

**根本卡点**：本机全部底模（`Illustrious-XL`、`waiIllustrious`、`autismmixSDXL`、`国风武侠`）
的语料是**动漫/武侠人物插画**，与项目要的"**空无一人的明代文书铺内景**"不匹配 ——
提示词里写多少遍 `no people` / `空无一人` 都压不住（实测至少 3 轮）。
项目底图当初用的 `Anything XL` 本机已不在（`D:\anythingxl\` 只有 streamlit 演示、无权重）。

**证据（已入库，可直接打开看，不必听我说）**：

| 文件 | 说明 |
|---|---|
| `docs/screenshots/regen_ink_anchor_main.png` | 锚点：现有 `main.png`（水墨街景，目标风格）|
| `docs/screenshots/regen_ink_with_people.png` | 数值最好但画了动漫人物（**假阳性证据**）|
| `docs/screenshots/regen_ink_best_scene.png` | 场景成立但画质崩 + 紫色伪影 |
| `docs/screenshots/regen_ink_paper_best.png` | 最好看但**带书法字 + 红印章**（禁文字硬规矩）|

**结论**：本机 SD **能出图、风格也能对**，但**这些底模出不了"无人 + 无文字 + 结构成立"的内景**。
**若改为"我来自动出图"**，先解决底模，从易到难：
1. **你提供一个底模**（水墨插画风，放进 `D:\绘世启动器\models\Stable-diffusion\`），
   我全程自动出图 + 跑判据 + **逐张目视复核** + 接入
2. **放开 huggingface / civitai 的网络访问**，我下载合适底模（**这需要你改策略，我不自行申请**）
3. 你指定本机已有的某个底模，我照着出（但上表说明现有的都不合适）

---

## 1. 要解决的问题（一句话）

标题页 `main.png` 是**水墨风**、主界面 `main_bg.png` 是**像素插画风**，两张不是一族。
实测 `style` 判据：**相邻差比值 1.91×**（同族阈值 0.6~1.6×）。

**两种走法（2026-10-12 定案：走水墨）**：

| 走法 | 做什么 | 状态 |
|---|---|---|
| 像素风（原方案 A）| 重做 `main.png` 成像素风 | ❌ **已放弃** —— 本机底模做不到（§0 实测：相邻差 5 倍、硬边 90 倍）|
| **水墨风（当前）** | **重做 `main_bg.png` 成水墨风，`main.png` 留作锚点** | ✅ **已选**（本文件按这个方向写）|

**水墨方向的实测基础**：本机 `国风武侠Chinese style` / SDXL 底模出图，
与锚点 `main.png` 的距离能到 **1.16~1.26×**（原像素风是 1.91×）—— **风格上已经进圈**。
**但内容全部不达标**（出人物 / 出文字 / 出印章 / 结构崩），详见 §0 实测（二）。

**当前真正卡住的不是风格，是内容**：需要"**空无一人的明代文书铺内景 + 无任何文字**"，
而本机底模的语料是动漫/武侠人物插画，压不住。

---

## 2. 提示词（水墨风；已实测三轮，附失败记录）

> ⚠️ 下面 §2–§4 保留的是**原像素风方向**的提示词与参数（已被本机实测否决，见 §0），
> **不要照它出图**。水墨风当前可用提示词与三轮演进记录见 §11。

### 2.1 正面提示词（❌ 已否决，仅存档）

```
16-bit pixel art, morning street in a Ming dynasty town, a poor scholar with a small
writing stall in the foreground, distant city gate and roofs, warm rice-paper sky,
muted earth tones, composition leaves the upper-center empty (plain sky) for a title,
NO text
```

**备选**（同提示词库第 2 条，留白同样在上方）：

```
pixel art, Ming dynasty riverside market at dawn, wooden stalls, a young scholar
holding a letter, warm beige and brown palette, empty sky area at top for UI,
no text no watermark
```

> 两条都出自 `data/art_prompts_round2.json` 的 `title_bg` 组；我只补了**安全区**那句
> （原提示词写的是 "leaves the center empty"，而标题实际在**上中**，见 §3）。

### 2.2 负面提示词（独立框，用提示词库原文，不要改写）

```
text, letters, characters, watermark, signature, logo, brand, copyright, photorealistic,
3d render, smooth gradients, modern style, anime, high saturation, blurry, noise,
grid lines not aligned
```

---

## 3. 两条硬约束（都是实测出来的）

### 3.1 标题安全区：**上中必须干净**

标题「代书」节点（`title_screen.tscn` 的 `TitleBox`，顶部居中）占画面：

| 方向 | 范围 |
|---|---|
| 横向 | **33.5% ~ 66.5%** |
| 纵向 | **3.4% ~ 32.4%** |

→ **新图的上中区域必须是干净天空/远景。** 这块如果有屋顶、幌子、人物，墨色书法字压上去会糊
（⑬ 那轮已验证过一次：标题放左上角压在深色建筑上，笔画发脏、副标题几乎看不见）。

### 3.2 宽高比必须是 **16:9**

`title_screen.tscn` 的 `TextureRect` **没设 `stretch_mode`**，用的是默认 `0 = STRETCH_SCALE`（拉伸填满）。
所以比例不对就会**变形**：

| 新图比例 | 纵向拉伸偏差 |
|---|---|
| 1.7778（准 16:9）| 0% |
| 1.6000（16:10）| **10%** ← 看得出 |
| 1.5000（3:2）| **15.6%** ← 明显 |

→ 出图后要缩到精确 16:9（接入时我做，见 §5）。

---

## 4. 生成参数（Stable Diffusion / ComfyUI）

| 项 | 值 | 理由 |
|---|---|---|
| **生成尺寸** | **1344 × 756** | 恰好 16:9；1.02M 像素，落在 SDXL 甜点区（~1M），不易崩构图 |
| 备选尺寸 | 1536 × 864 | 1.33M，也安全 |
| 避开 | 1152 × 648 | 0.75M，对 SDXL 偏小 |
| 采样步数 / CFG | 你惯用值 | 提示词库未指定，它是给通用模型写的 |
| 数量 | **出 4~6 张**再挑 | 选图比调参快 |
| 挑选标准 | 按 §3.1 挑"**上中干净**"的那张 | 这是唯一必须人眼判断的一条 |

**色板锚点**（想对齐主界面色调时参考，取自 `ART_PLAN.md` §二）：

宣纸 `#fce4b4` `#fce49c` · 木构 `#9c5424` `#b46c3c` · 墨 `#3c3c2c` · 户外 `#846c54` `#6c846c`

> 参考：现在主界面 `main_bg.png` 的实测平均色是 `#ba916b`（木构暖调）。

---

## 5. 两条路：你出图 / 我自动出图

### 路 A：用外部工具出图（当前默认，因为本机底模不对）

**你**：按 §2–§4 出 4~6 张 → 挑"上中干净"的 → 放进 `assets/images/_incoming/` → 告诉我文件名。

### 路 B：我来自动出图（本机 SD，**管线已验证可跑**）

前提是**先解决底模**（见 §0）。底模就位后，以下步骤我全部可自动化：

```powershell
# 1. 启动 SD WebUI（离线模式，关键——见 §10）
$h = 'D:\绘世启动器'
$env:PYTHON            = "$h\.ext\python.exe"
$env:VENV_DIR          = '-'          # 跳过 venv，直接用 .ext 的 python
$env:SKIP_VENV         = '1'          #   否则首次启动要下 2-4 GB 的 torch
$env:HF_HOME           = 'D:\dsh\tmp\hfcache'   # 见 §10 的离线缓存
$env:HF_HUB_OFFLINE    = '1'
$env:TRANSFORMERS_OFFLINE = '1'
$env:PYTHONIOENCODING  = 'utf-8'      # 否则中文/emoji 打印会 UnicodeEncodeError
$env:COMMANDLINE_ARGS  = '--api --listen --port 7860 --medvram --xformers --skip-version-check --no-download-sd-model'
Set-Location $h
& "$h\.ext\python.exe" launch.py      # 后台跑

# 2. 出图（脚本 tools\gen_sd.py：用标准库 urllib，不依赖 requests）
& "$h\.ext\python.exe" tools\gen_sd.py --out D:\dsh\tmp\title_v1.png `
    --model '<底模文件名>' --width 1344 --height 756 --steps 28 --cfg 7 --seed -1 --n 4
```

**接入**（两条路都一样，我执行）：

1. **规整到精确 16:9**（若不是）—— `tools/wm_clean.gd`（`--crop-through`）+ `Image.resize(LANCZOS)`
2. **覆盖** `assets/images/backgrounds/main.png` 并**强制重导**（尺寸变了通常自动重导；
   若报旧图，按 `AI_PLAYBOOK` 第 17 条删 `.godot/imported/main.png-*.ctex`）
3. **可选加固**：给 `title_screen.tscn` 的 `TextureRect` 补 `stretch_mode = 5`，
   与另两个场景一致 —— 以后任何比例的图都只会留黑边，**不会静默拉伸变形**
4. **跑 §6 全部判据**，把实测数值贴给你
5. 达标 → 截图存档 → 更新 `ART_PLAN.md` → 登记成果 → 提交（显式列路径）

---

## 6. 验收判据（拿图后我跑，命令可直接抄）

```powershell
$d = 'D:\个人项目\daishu'
$bg = "$d\assets\images\backgrounds"

# ① 与主界面是否同族（核心判据）—— 期望 ✅ 同族、exit=0
node tools/art_check.mjs style "$bg\main.png" --ref "$bg\main_bg.png" --expect-ratio 16:9

# ② 色板是否不偏离且与主界面同族 —— 期望主导分组是 木构/宣纸，色距 < 0.30
node tools/art_check.mjs palette "$bg\main.png" --top 6

# ③ 无水印 —— 期望 ✅ 未检出；**若报命中必须裁出来人眼复核**（有已知误报）
node tools/art_check.mjs watermark "$bg\main.png" --scan
node tools/art_check.mjs crop "$bg\main.png" --box <可疑区> --out check.png

# ④ 标题可读 —— 期望「代书」笔画干净、不糊在纹理上
& $godot --path $d --script res://tools/capture_scene.gd -- --scene title --out title_new.png

# ⑤ 无回归
& $godot --path $d --script res://tools/verify_drop.gd
& $godot --path $d --script res://tools/verify_theme.gd
& $godot --path $d --script res://tools/verify_avatar.gd
```

**通过线**：

| 判据 | 现在（水墨） | 目标 |
|---|---|---|
| ① 相邻差比值 | **1.91×**（不同族 ❌）| **0.6 ~ 1.6×**（同族 ✅）|
| ① 平坦区差 | 15.3% | **< 12%** |
| ② 主导色分组 | 墨/字 + 宣纸 | **木构/宣纸** |
| ② 色距 | 0.087 | 全部 **< 0.30** |
| ③ 水印 | 未检出 | 未检出（**注意误报**）|

> 「同族」阈值 0.6~1.6× 是这么定的：同族实测 0.91×（信纸 vs 主界面）、
> 异族实测 1.91×（标题 vs 主界面）—— 阈值落在两者中间。

---

## 7. 风险与回退

| 情况 | 处理 |
|---|---|
| 出的图风格仍不像 | 判据 ① 会直接量出来。调整方向：提高 `16-bit pixel art` / `dithering` 权重，或直接改用 `main_bg` 那组提示词的措辞 |
| 上中区域总有建筑 | 换 §2.1 备选提示词；或**把标题节点移到图上真正干净的位置**（改 `TitleBox` 的 offset，代价 1 轮截图）|
| 色调与主界面不一致 | 判据 ② 会暴露。用 ComfyUI **锁种子** + 与 `main_bg` 相同的 checkpoint/LoRA 复现色调 |
| 效果不满意想回退 | **全程可逆**：`git checkout -- assets/images/backgrounds/main.png` 即可还原（原图一直在 git 里）|

---

## 8. 明确不做（避免白干）

| 不做 | 原因 |
|---|---|
| `letter_paper`（信纸）| 现图刚去完水印、栏线实测 12 栏 CV 2.1%、槽位锚点已对齐；重生成要重走整条锚定流程 |
| `word_panel`（词库底板）| **已由 `StyleBoxFlat_wordpanel` 实现**（`letter.tscn`）|
| `button_9slice`（按钮九宫格）| **已由 `theme/daishu_theme.tres` 实现**（⑧ 那轮）|
| `cursor_brush`（毛笔光标）| 拖拽预览已用 `brush_cursor.png`；真光标属 ⑫，另需"单一笔尖"图 |
| `main_bg` / 结局 / 序章 / 头像 | 本次范围只要标题图 1 张（提示词库里对应组仍有效，日后可直接取用）|

---

## 9. 本机 SD 出图产物（证据留档，2026-10-12）

**已入库**（可直接打开看，不必去 tmp 找）：

| 文件 | 说明 |
|---|---|
| `docs/screenshots/regen_try_sdxl_01.png` | 1344×756 / 28 步，seed 12345 —— 上中全被楼阁占满，**不合格** |
| `docs/screenshots/regen_try_sdxl_02.png` | 同上 —— 粉紫天空 + 高饱和青绿伪影，**不合格** |

**留在 tmp（中间产物，不登记）**：

| 文件 | 说明 |
|---|---|
| `D:\dsh\tmp\sd_smoke.png` | 冒烟验证（384×216/8 步），证明链路通 |
| `D:\dsh\tmp\title_sdxl_01..03.png` | 正式参数 3 张原图 |

**复用脚本**：`tools\gen_sd.py`（出图 → base64 解码 → 落盘，含底模切换与 seed 记录）。

---

## 10. 本机跑 SD 的两个坑（实测，下次直接绕）

### 坑 1：SDXL 加载失败 → 被策略代理 403（**已解决**）

**症状**：`Loading weights [...]` 之后立刻

```
requests.exceptions.ProxyError: ... huggingface.co ... /openai/clip-vit-large-patch14/resolve/main/vocab.json
  (Caused by ProxyError('Unable to connect to proxy', OSError('Tunnel connection failed: 403 Forbidden')))
Stable diffusion model failed to load
```

**原因**：SDXL 的文本编码器要 **CLIP tokenizer**（`openai/clip-vit-large-patch14` 的
`vocab.json` / `merges.txt` / `tokenizer_config.json`），它不在 `transformers` 默认缓存里，
WebUI 就去 huggingface.co 下 —— 而本机所有出网走策略代理，该域名被 403。

**关键发现：文件本来就在本机**，在绘世启动器自己的镜像缓存里：

```
D:\绘世启动器\.cache\sdwebuilauncher\hfmirror\refs\openai\clip-vit-large-patch14\main\
    config.json  merges.txt  model.safetensors  special_tokens_map.json  tokenizer_config.json  vocab.json
```

**解决**：把它摆成 HF 缓存布局，然后**离线启动**（`models--openai--clip-vit-large-patch14` 是 HF 的目录命名法）：

```
D:\dsh\tmp\hfcache\hub\models--openai--clip-vit-large-patch14\
    refs\main                                  ← 内容 = 快照目录名
    snapshots\<任意名>\{vocab.json, merges.txt, tokenizer_config.json, ...}
```

然后设 `HF_HOME=D:\dsh\tmp\hfcache`、`HF_HUB_OFFLINE=1`、`TRANSFORMERS_OFFLINE=1`。
**验证**（应输出 `TOKENIZER_OK vocab_size=49408`）：

```powershell
& 'D:\绘世启动器\.ext\python.exe' -c "from transformers import CLIPTokenizer; print('TOKENIZER_OK', CLIPTokenizer.from_pretrained('openai/clip-vit-large-patch14').vocab_size)"
```

### 坑 2：不要用 `.bat` 起，也不要 `-FilePath 'node'` 式的写法

- **`.bat` + 中文路径**：用 ASCII 编码写 bat 会把 `D:\绘世启动器` 变成 `D:\?????`，启动必失败。
  用 PowerShell 的 `$env:` + `& <绝对路径>` 代替。
- **`PYTHONIOENCODING=utf-8` 必须设**：控制台是 GBK，脚本里打印 `✅` 这类字符会
  `UnicodeEncodeError: 'gbk' codec can't encode character` —— **报错位置在最后一行 print，
  会让人误以为前面的逻辑失败**（实际前面已经成功）。
- **`Start-Process -FilePath 'node'` 静默失败**：Windows 上 `node` 不是可执行文件名，
  要用 `(Get-Command node).Source` 拿绝对路径，否则进程起不来、输出 0 字节。

---

## 11. 水墨风：当前提示词与三轮演进（实测，别退回旧版）

**目标**：把 `main_bg.png`（主界面底图）改成与 `main.png` 同族的水墨风。
**硬约束**：① 空无一人（玩家才是代笔先生）；② **无任何文字/印章**（`ART_PLAN` §一）；
③ 画面中部要有大片低细节区（UI 面板半透明 alpha 0.78，压在细密线条上会读不清）。

### 当前提示词（v3，可直接粘贴）

**正面**：

```
traditional Chinese ink wash painting (shuimo), xuan paper texture, interior of a Ming
dynasty letter-writing shop, an unattended wooden desk in the lower part of the frame with
writing brushes, an inkstone and stacked rice paper, blank paper sheets hanging on the
wall, empty room with no people, soft ink brushstrokes, muted warm earth tones, subtle
color wash, low contrast, uncluttered composition, large plain low-detail wall area in the
middle of the frame for UI panels, no text, no watermark, no signature
```

**负面**（分层写，每一层都是实测加上的）：

```
text, letters, characters, watermark, signature, logo, brand,
calligraphy, handwriting, writing, inscription, chinese characters, kanji,
typed text, captions, labels, posters, newspaper,
person, people, human, figure, portrait, face, hands,
photorealistic, 3d render, modern style, anime, high saturation, blurry, noise,
oil painting, thick impasto, purple fringing, chromatic aberration
```

**参数**：`1152×648` / `28` 步 / `cfg 7` / `DPM++ 2M Karras`
**底模**：`国风武侠Chinese style`（SD1.5，约 13 秒/张）或 `waiIllustriousSDXL_v170`（SDXL，约 24 秒/张）

### 三轮演进（**失败记录也是资产**，别退回旧版）

| 版本 | 提示词要点 | 数值判据 | 目视结果 |
|---|---|---|---|
| v1 | 内景 + 书案 + 信纸 | 1.16× | 构图对（书案/信纸/格架能认出来），**但出了人物伏案写字**，细节偏密 |
| v2 | 加"空无一人 / 刻意稀疏" | **0.82×**（最平）| **过度纠正**：出成一排空白纸/木板，**场景不成立** |
| **v3** | **以 v1 的实体描述为主干**，只把"无人"当约束加进去 | 1.26× | 场景成立、无人物，但结构发闷 + 有紫色伪影 |

**方法论教训**：v2 说明"**只加否定约束会把实体描述一起冲掉**" ——
措辞要**保留正向的实体描述**（内景/书案/毛笔/信纸），把"不要"作为附加约束，而不是让画面变空。

### 另一个方向（数值好但内容废）：极简纸本

提示词 `traditional Chinese ink wash painting on xuan paper, plain rice paper background ...
a faint suggestion of a wooden desk edge along the bottom ...`
—— 数值最优（**比值 0.92**、平坦区 29%、平均色 `#dcd1b8`），**但纸上被画了书法字 + 红印章**，
直接违反禁文字硬规矩。**失败模式温和**（最差是"一片纸"），如果哪天需要一个纯纸底，这条路值得再调。

---

## 12. 换模特/换 LoRA/换手法都试过了 —— **根因是风格的固有成分**（2026-10-12）

§11 的 txt2img 失败后，又试了**两条新路**，都记录了实测数据。

### 12.1 先解决了"拿不到新模型"的问题（实测，之前结论错了）

之前判断"`huggingface` 被策略代理 403 拦"，**这个结论只对了一半**：

| 环境 | 下载结果 |
|---|---|
| **带** `HTTP_PROXY/ALL_PROXY=http://127.0.0.1:56477` | ❌ CONNECT 被拒（`Tunnel connection failed: 403 Forbidden`）|
| **不带**代理变量（直连）| ✅ **成功**，实测 **4~6.7 MB/s** |

所以不是策略封了域名，是**那台本地代理（`Veee`）对 huggingface 的 CONNECT 返回 403**。
**试过用 `NO_PROXY=huggingface.co` 绕，无效**（requests 仍走代理）。有效做法是**不传代理变量**。

⚠️ **但代理这块有个反直觉的双重需求**（踩了两次才对，代码注释里已写明）：
- **下载**要**去掉**外网代理
- **gradio 启动**要**有 `NO_PROXY=127.0.0.1,localhost`** —— 否则它自检 localhost 失败：
  `ValueError: When localhost is not accessible, a shareable link must be created.`

**已下载到本机**（Civitai，无需登录，用了就删）：

| LoRA | 大小 | 来源 |
|---|---|---|
| `ink-landscape-sdxl_v2.safetensors` | 162.7 MB | [国画·水墨·山水画 SDXL](https://civitaiarchive.com/models/135594?modelVersionId=149480) |
| `chinese-ink-painting_v1.safetensors` | 870.3 MB | [造物云 中国文化模型 水墨画](https://civarchive.com/models/153225?modelVersionId=171579) |

> 选 LoRA 而不是换底模的理由：本机已有 3 个 SDXL 底模，**缺的只是"水墨风格"**；
> LoRA 只 0.16 GB（换底模要 6.5 GB / 26 分钟），可叠加、可调权重、不满意就删。

### 12.2 新手法：img2img 拿现有 `main_bg.png` 当构图骨架

**思路**：txt2img 的失败模式是**语义失控**（出人物/出印章/出产品摄影），
因为本机底模在"空无一人的明代内景"上没有对应语料。
那就**把构图和语义交给已有的图**（`main_bg.png` 本来就是对的：书案 + 笔筒 + 砚台 + 空桌面），
只让模型改**渲染风格** —— `denoising_strength` 就是那个连续可调的旋钮。

**实测结果**（LoRA 权重 0.85，30 步，cfg 7.5，seed 20261012）：

| 强度 | 比值 | 平坦区 | 目视 |
|---|---|---|---|
| 0.45 | 1.33~1.42 | 30~31% | 原图细节被保留成**满纸伪文字** |
| 0.65 | 1.20 | 20% | 出**书法字 + 红印章** |
| **0.80** | 1.22 | **46%** | ✅ **最干净**：空白信纸 + 毛笔 + 墨洗 + 宣纸底，只有一处小笔触 |
| 0.85 | 0.86 | 57% | **左下又一列题字 + 一枚红印章** |
| 0.92 | **1.06** | **53%** | 无字，但**太空**（几乎一片纸，场景不成立）|

**趋势明确**：强度越高，原图密集细节越不会被保留成伪文字；但太高就"空到没有场景"。
**中间那个能同时满足"无字"和"有场景"的窗口，实测没找到。**

### 12.3 结论：**"题字 + 印章"是水墨画风格的固有构图成分**

试过的所有组合（3 轮文字提示词 × 5 档重绘强度 × 2 个水墨 LoRA × 400+ 字符的负面词表，
其中 `calligraphy, handwriting, inscription, chinese characters, kanji, seal, stamp, wax seal`
全都列上）—— **没有任何一次得到"水墨画风 + 有场景 + 完全无文字"**。

原因（这是**推断**，但与全部实测一致）：传统水墨**作品的常规构图里就带题跋与落款印章**，
所以这类 LoRA 的训练数据里"画上题字 + 红印"是**风格的一部分**，不是一个可以从画面里
"排除掉"的物体。负面提示词只能部分压制它，压不死。

**证据（已入库，可直接打开看）**：

| 文件 | 说明 |
|---|---|
| `docs/screenshots/regen_i2i_src_mainbg.png` | 骨架原图（构图本来是对的，且无文字）|
| `docs/screenshots/regen_i2i_with_text.png` | 强度 0.85：构图最近，**但左下题字 + 红印** |
| `docs/screenshots/regen_i2i_waxseal.png` | 另一个 LoRA 也出**题字 + 红印章** |
| `docs/screenshots/regen_i2i_clean_empty.png` | 强度 0.92：**无字但太空**，场景不成立 |

### 12.4 那要怎么办（未采纳，供决策）

| 方案 | 说明 | 代价 |
|---|---|---|
| **① 局部重绘（inpainting）** | 把有字/印章的区域**遮罩掉**再重绘，其余保留 | **最对症** —— 文字是局部缺陷，整体风格已经合格；但要先做一个 mask |
| ② 用成品图去字 | 手工/AI 修掉文字区域 | 一旦 AI 修，可能又写上新字；手工则要人来做 |
| ③ 换个"无题跋"训练取向的模型 | 需要找专门做**背景/场景**而非"画作"的模型 | 要再找模型 + 下载 + 试，成本不确定 |
| ④ 接受"题字 + 印章" | 它本来就是水墨画的常见样子 | **违反 `ART_PLAN` §一 禁文字硬规矩**，不能出货（除非改规矩，那要你定）|
| ⑤ 改用纯抽象纸底 | 不要场景，只要宣纸质感 + 淡墨 | 数值能达标，但界面会偏"空"，看你要不要这个调性 |

**我的建议：先试 ①**。理由是本次实测已经把风格调到位了（0.80 强度那张），
只是**局部被加了两处墨迹** —— 用 inpainting 精确盖掉那两处，比继续换模型更省、更可控。
