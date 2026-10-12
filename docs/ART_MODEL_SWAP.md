# 换底模实测（2026-10-12 晚，代理关闭后）

> **背景**：用户询问"不尝试换底模，或者换生图工具吗？"，并**关闭了本机代理**。
> 关代理后重测，前面的结论被推翻 —— 换底模**是可行的**，而且**已经做成**。

---

## 一、被推翻的结论（诚实记录）

我此前写过「本机持续带宽 ~0.11 MB/s，换源/换站/换工具都无效」。
**那个结论是在代理开着的状态下测的，是错的。**

代理关闭后重测（各取 3 MB）：

| 主机 | 性质 | 代理开 | **代理关** |
|---|---|---|---|
| GitHub Releases | 海外 | 0.11 MB/s | ❌ 连不上 |
| HuggingFace | 海外 | 连接失败 | ❌ 连不上 |
| npm registry | 海外 | 0.11 MB/s | 0.28 MB/s |
| **阿里 npmmirror** | **国内** | 0.11 MB/s | **2.81 MB/s** |

**真实图景**：代理**不是加速器而是限速器**（所有流量被压到 0.11）；关掉后**海外不通、国内飞快**。
⇒ 走**国内源**即可。

⚠️ 我之前的错误链条：拿**小文件**测到 4~6.7 MB/s → 外推 4 GB 只需十几分钟 →
发现实际 0.17 MB/s → 又测出"国内 CDN 也慢"（**那次是代理还开着**）→ 得出"换源无用"。
**每一步都有实测，但前提（代理状态）变了没重测**，导致结论错了一整轮。

---

## 二、modelscope（阿里）= 可用的国内源

接口形态是**试出来**的（不猜）：

| 用途 | 接口 |
|---|---|
| 搜索 | `PUT https://modelscope.cn/api/v1/dolphin/models`（body: `{Name, PageSize, PageNumber}`）|
| 单仓库信息 | `GET /api/v1/models/{owner}/{name}`（`Files` 字段为空，不可用）|
| **文件表** | `GET /api/v1/models/{owner}/{name}/repo/files?Revision=master` |
| **下载** | `GET /api/v1/models/{owner}/{name}/repo?Revision=master&FilePath={file}` |

**实测下载速度 10~29 MB/s。**

---

## 三、已下载并实测的两个国风底模

| 底模 | 大小 | 类型 | 来源 |
|---|---|---|---|
| `4Guofeng4XL_v1125D` | **6.46 GB** | SDXL | [NickYuan/4Guofeng4XL_v1125D](https://modelscope.cn/models/NickYuan/4Guofeng4XL_v1125D) |
| `3Guofeng3_v34` | **2.14 GB** | SD1.5 | [mixLine/Guofeng3](https://modelscope.cn/models/mixLine/Guofeng3) |

下载耗时：6.46 GB ≈ 5 分钟、2.14 GB ≈ 3.5 分钟（**代理关着才能到这个速度**）。

### 实测出图（同场景 / 同提示词 / 同 seed 880088）

| 文件 | 相邻差 | 与锚点比值 | 平坦区 | 硬边 | 目视 |
|---|---|---|---|---|---|
| `Guofeng3_1.png` | 15.6 | 1.29 ✅ | 20.3% | 3.2% | 空室内景、无字无人；偏西式 |
| `Guofeng3_2.png` | 11.0 | **0.91** ✅ | 33.4% | 1.8% | 同上 |
| `Guofeng4XL_1.png` | 8.4 | 0.70 ✅ | 48.4% | 1.5% | ⚠️ **3×3 分块接缝** |
| `Guofeng4XL_2.png` | 22.4 | 1.86 | 33.2% | 7.6% | 空房间（格栅窗+长案），无字无人 |

**归档**：`docs/screenshots/regen_newbase_guofeng4xl.png`、`regen_newbase_guofeng3.png`

### 结论（如实）

✅ **解决了顽疾**：新底模**没有出人物、没有出文字/印章** —— 这正是旧 5 个底模反复失败的点
（旧底模出的图见 `docs/screenshots/regen_i2i_with_text.png`、`regen_ink_with_people.png`）。

❌ **没有解决全部**：
1. **画风提示词几乎没被遵循** —— 我要的是"水彩童书插画"，出的是**写实/线稿感的西式房间**
2. **中式与道具没出来** —— 明代文书铺、毛笔、砚台、宣纸都没体现
3. **`4Guofeng4XL` 在 1152×648 上有 3×3 分块接缝**（疑似 tiling/vae 问题，需换尺寸或换 VAE 验证）

---

## 四、⚠️ 我造成的一次破坏（已修复，务必记住）

**为装 ComfyUI，我往共享的 `.ext` 环境装了 pydantic v2，把 SD WebUI 搞坏了：**

```
ImportError: cannot import name 'Undefined' from 'pydantic.fields'
```

**原因**：绘世启动器的 `gradio 3.41.2` 依赖 **pydantic v1**；ComfyUI 的 `pydantic-settings` 要求 **v2**。
两者**共用同一个 `.ext` 环境**，所以装 ComfyUI 的依赖 = 砸 WebUI。

**修复**：`pip install "pydantic<2"` → 回到 `1.10.26`，`gradio`/`fastapi` 恢复导入，WebUI 正常出图。

**遗留冲突（未解决，会再犯）**：pip 明确警告
`pydantic-settings 2.15.0 requires pydantic>=2.7.0, but you have pydantic 1.10.26`。

**判据（下次别再踩）**：
- **不要在 `.ext` 里装 ComfyUI 的依赖** —— 要给 ComfyUI 建**独立 venv**
- 若要动 `.ext`，先 `pip freeze > 备份.txt`，并想清"谁在共用这个环境"
- 本次损坏的发现方式是"起服务报 ImportError"，属于**显式失败**，比静默出错好；
  但代价是一轮返工

---

## 五、下一步（换底模通了，可以真正推进）

现在有了能用的底模 + 能下模型（国内源 10~29 MB/s），建议：

1. **换底模后重做"代表素材"**：`title_screen` 的标题背景（见 `ART_HERO_ASSET.md` 的规格）
2. **针对新底模重写提示词**：
   - 加回被忽略的"明代/中式"实体词（格栅窗、条案、笔筒、砚台）
   - 明确道具清单（因为提示词里的笔/砚/纸没出来）
   - `4Guofeng4XL` 先解决分块接缝：换 1024×576 或 1344×768 试，或换 VAE
3. **可再找更像"场景/背景向"的底模**（modelscope 上还有 `digiplay/Landscape_PhotoReal_v1` 1.99 GB、`Remade-AI/Fantasy-Landscapes` 0.33 GB 等候选，下载已不成问题）
4. **ComfyUI**：已 clone 到 `D:\ComfyUI`（1281 文件），但**它需要独立 venv**，别再用 `.ext`
