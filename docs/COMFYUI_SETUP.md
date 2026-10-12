# ComfyUI 安装记录（2026-10-12）

> 起因：用户问「既然已经有 ComfyUI 了，为什么还要用绘世启动器」。
> 结论：**ComfyUI 能装起来，但它要求 torch ≥2.4，而本机只有 2.3.1** ——
> 而 CUDA 版 torch 只能从 pytorch 官方源下（约 0.5 MB/s、2.33 GB、~75 分钟）。
> 本文记录全过程、我打的补丁与当前状态。

---

## 一、位置与环境（关键：**独立 venv**，不碰绘世启动器）

| 项 | 值 |
|---|---|
| 代码 | `D:\ComfyUI`（git clone，1281 文件，`e8665ca` 2026-10-11）|
| **独立 venv** | `D:\ComfyUI\.venv-comfy`（`--system-site-packages`，复用 `.ext` 的 torch）|
| 启动 | `D:\ComfyUI\.venv-comfy\Scripts\python.exe main.py --listen 127.0.0.1 --port 8188 --lowvram` |
| 模型目录 | `D:\ComfyUI\models\...`（**可把绘世启动器的模型软链过来，避免重复占用 20+ GB**）|

### 为什么必须独立 venv —— 实际踩过一次

| 包 | 绘世启动器（`.ext`）需要 | ComfyUI 需要 |
|---|---|---|
| `pydantic` | **v1**（`gradio 3.41.2` 依赖 `pydantic.fields.Undefined`）| **v2**（`pydantic~=2.0` + `pydantic-settings~=2.0`）|

两者**不能共存于同一个 site-packages**。我第一次直接往 `.ext` 装 v2，
结果 SD WebUI 完全起不来：

```
ImportError: cannot import name 'Undefined' from 'pydantic.fields'
```

**修复**：`pip install "pydantic<2"` → `1.10.26`，`gradio`/`fastapi` 恢复。

**隔离已验证有效**（venv 的 site-packages 优先级更高，只遮蔽不改动 `.ext`）：

| 解释器 | 看到的 pydantic |
|---|---|
| `D:\ComfyUI\.venv-comfy\Scripts\python.exe` | **2.14.1** ✅ |
| `D:\绘世启动器\.ext\python.exe` | **1.10.26** ✅（`gradio 3.41.2` 仍可导入）|

pip 也明确拒绝跨环境卸载：
`Not uninstalling pydantic at d:\绘世启动器\.ext\lib\site-packages, outside environment D:\ComfyUI\.venv-comfy`

---

## 二、装依赖：**PyPI 镜像实测**（海外源关代理后不通）

| 镜像 | 索引 | **文件下载** |
|---|---|---|
| **腾讯云** | ✅ | **1.54 MB/s** ✅ |
| USTC | ✅ | 0.50 MB/s |
| 阿里云 | ✅ | 0.36 MB/s |
| **清华** | ✅ | ❌ **403** |
| pypi.org | 慢（索引 17 秒）| 0.04 MB/s |

**结论：用腾讯云** `--index-url https://mirrors.cloud.tencent.com/pypi/simple`。
（清华索引可通但文件 403 —— 只看索引页会误判可用。）

---

## 三、阻塞点：ComfyUI 要求 **torch ≥2.4**，本机是 **2.3.1**

`requirements.txt` 里只写 `torch`（**没写版本下限**），所以不兼容要到**运行时**才暴露。已实测撞到两个 2.4+ 的 API：

| 报错 | 需要的 torch |
|---|---|
| `AttributeError: module 'torch.library' has no attribute 'custom_op'` | ≥ 2.4 |
| `AttributeError: module 'torch.serialization' has no attribute 'add_safe_globals'` | ≥ 2.4 |

（另有 `main.py:280` 的软门槛：`torch ≥ 2.8` 才启用 DynamicVRAM，否则回退 legacy ModelPatcher —— 只是警告。）

### 我打的补丁（已备份，可回退）

`D:\ComfyUI\comfy\quant_ops.py` 第 44 行：

```python
# 改前
except ImportError as e:
# 改后
except (ImportError, AttributeError) as e:
```

**理由**：该 import 本来就在 `try` 里，且**降级分支是完整的**（定义 `QuantizedTensor` / `_CK*Layout` 桩类、
`_CK_AVAILABLE = False`，第 73 行也已用 `if _CK_AVAILABLE` 守卫 MXFP8 的 import）。
只是 `comfy_kitchen` 在 torch<2.4 下抛的是 `AttributeError` 而非 `ImportError`，没被接住。
放宽后正常降级（**只损失 fp8/fp4 支持**，SD1.5/SDXL 常规出图不受影响）。

备份：`comfy\quant_ops.py.bak-20261012-232409`

---

## 四、当前状态与代价

| 项 | 状态 |
|---|---|
| 代码 | ✅ 已 clone |
| 独立 venv | ✅ 已建，pydantic 隔离验证通过 |
| ComfyUI 依赖 | ✅ 已装（pydantic v2 / comfy_aimdo / comfy-kitchen / comfy-angle 等）|
| `torch` | ⏳ **正在下 CUDA 版 2.4.0**（2.33 GB @ ~0.5 MB/s ≈ 75 分钟，带断点续传）|
| API 可启动 | ❌ 待 torch 到位 |

**为什么 CUDA 版非下不可**：腾讯云 PyPI 给的 torch 轮子是 **CPU 版**
（实测 `torch 2.6.0+cpu`、`cuda available: False`），CPU 出 SDXL 一张要几十分钟，不可用。
而 **CUDA 轮子只有 pytorch 官方源有** —— `download.pytorch.org`（实测 0.53~0.78 MB/s），
清华/USTC/阿里/南大/SJTU 的 pytorch 镜像**都没有 cu124 的 Windows 轮子**（实测 404）。

---

## 五、要不要切到 ComfyUI：利弊

**ComfyUI 的真实优势（针对本项目的痛点）**：
1. **原生 inpainting 工作流**（`VAEEncodeForInpaint` + mask）——
   这正是水墨那轮反复失败后**最该用的手法**（把"题字+印章"用遮罩盖掉再重绘）
2. **低显存更稳**：8GB 卡上 ComfyUI 的模型管理比 WebUI 的 `--medvram` 更从容
3. 节点式可复现：工作流能存成 JSON 版本化，比 `COMMONLINE_ARGS` + 提示词更可审计

**成本**：一次性 ~75 分钟下 torch（已在跑），之后 ComfyUI 可用。

**若不想等**：绘世启动器**当前完全可用** —— 已修好 pydantic，且已有
**7 个底模**（含新下的 `4Guofeng4XL_v1125D`、`3Guofeng3_v34`），出图速度 SDXL ≈ 24 秒/张。
