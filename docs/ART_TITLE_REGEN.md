# 标题底图重做作业单（`main.png` → 像素插画风）

> **这份是给人生图用的作业单**：照抄提示词 → 出 4~6 张 → 按判据挑一张 → 交给我接入。
> 方案背景与取舍见 `ART_PLAN.md` §二·五。
>
> - 建单：2026-10-12
> - **只出 1 张图**：标题背景 `main.png`
> - 目的：**统一画风**（**不是**去水印 —— 水印那轮已解决）

---

## 0. 先看这里：**本机 SD 能跑，但底模不对**（2026-10-12 实测）

⚠️ **这一节是实测结论，先读完再决定谁来出图。**

本机**装着完整的 Stable Diffusion WebUI**（绘世启动器），且我**已经把它跑通并实际出过图**：

| 事实 | 值 |
|---|---|
| 位置 | `D:\绘世启动器`（SD WebUI v1.10.1）|
| 便携 Python | `D:\绘世启动器\.ext\python.exe`（3.10.11，**依赖完整**，无需建 venv）|
| GPU | RTX 2060 SUPER **8GB**（`torch 2.3.1+cu121`、`xformers 0.0.27`）|
| 出图速度实测 | SDXL 1344×756 / 28 步 ≈ **36 秒/张**（一次 3 张用 108 秒）|
| 已验证 | API 可调（`/sdapi/v1/txt2img`），出图落盘正常 |

**但——`--no-download-sd-model` 与下面的事实导致"出一张能用的图"卡在底模上：**

| 本机已装底模 | 类型 | 与本项目 `main_bg.png` 的实测距离 |
|---|---|---|
| `Illustrious-XL-v2.0` | 动漫插画 | 相邻差 **32.2**（基准 6.3）= **5.07×** |
| `waiIllustriousSDXL_v170` | 动漫插画 | 同类 |
| `autismmixSDXL_autismmixConfetti` | 动漫插画 | 同类 |
| `v1-5-pruned-emaonly` | SD1.5 通用 | 太弱，出不了风格 |
| `国风武侠Chinese style.ckpt` | SD1.5 国风 | 非像素风 |

**实测三张 SDXL 出图 vs 项目基准 `main_bg.png`**：

| | 平均相邻差 | 硬边 ≥90 | 与基准比值 |
|---|---|---|---|
| 基准 `main_bg.png` | **6.3** | **0.1%** | — |
| 出图 ① | 32.2 | **9.2%** | 5.07× |
| 出图 ② | 30.2 | 8.7% | 4.76× |
| 出图 ③ | 34.2 | 11.9% | 5.39× |

**相邻差是基准的 5 倍、硬边是 90 倍。** 这不是"风格略不同"，是**完全不同的渲染方式**：
本机模型给的是"**抖动噪点**"，项目 `main_bg.png` 要的是"**大面积平坦色块 + 极低硬边**"。

**另一个坑**：提示词里的 `leaves the upper-center empty (plain sky) for a title` **对动漫底模基本无效** ——
三张出图的上中部全被楼阁/塔占满（正是标题要放的位置），选图阶段直接淘汰。

**结论**：卡点**不是算力，是缺一个像素风/扁平插画底模**（项目底图当初用的 `Anything XL` 本机已不在，
`D:\anythingxl\` 里只有个 streamlit 演示、没有模型权重）。
**所以作业单仍然成立**，出图这一步要么换底模，要么用外部工具。

**若换成"我来自动出图"**，需要先解决底模，从易到难：
1. **你指定一个本机已有的模型**，我照着出（但上表说明现有的都不合适）
2. **你提供一个像素风底模**（放进 `D:\绘世启动器\models\Stable-diffusion\`），我全程自动出图 + 跑判据 + 挑图
3. **放开 huggingface / civitai 的网络访问**，我下载一个像素风底模（**这需要你改策略，我不自行申请**）

---

## 1. 要解决的问题（一句话）

标题页 `main.png` 是**水墨风**、主界面 `main_bg.png` 是**像素插画风**，两张不是一族。
实测 `style` 判据：**相邻差比值 1.91×（超出同族阈值 1.6×）**。

离群者是**标题页**，不是主界面 —— 信纸 `letter.png` 与主界面实测同族（比值 0.91×）。
**所以只换这一张，三张就同族了。**

---

## 2. 提示词（直接粘贴）

### 2.1 正面提示词

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
