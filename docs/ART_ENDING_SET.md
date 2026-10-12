# 补齐缺失背景：⑩ 结局 ×2 + ⑪ 序章（2026-10-13）

> **这三个界面此前完全没有贴图** —— `success.tscn` / `gameover.tscn` / `prologue.tscn`
> 里**没有任何 `TextureRect` 与图片 `ext_resource`**，只有纯色 `Panel` 与文字。
> 本文记录补上的三张及其判据。

产物：`docs/screenshots/ending_set/`（3 张 + 展示图 `ending_set.png`）

---

## 一、为什么先做这三张

上一轮定位到本机 txt2img 的真瓶颈是**构图控制**（不服从"下 40% 是桌面"这类空间关系）。
而这三张是**纯氛围图**：

| 场景 | 内容 | 是否需要精确空间控制 |
|---|---|---|
| `success` | 科举中第的夕阳宫门 | ❌ 不需要 |
| `gameover` | 黄昏雨中的空街 | ❌ 不需要 |
| `prologue` | 贫寒书生的书房 | ❌ 不需要 |

⇒ **正好绕开那个瓶颈**，是当前成功率最高的一批。

---

## 二、三张结果与判据

判据针对各场景的**文字占位**（据 `.tscn` 实测）：`success`/`gameover` 文字在中间带，
`prologue` 文字在正中带（`offset -180..180`）。所以量的是**对应区域的"细节量"与"暗像素占比"** ——
两项都低，文字压上去才读得清。

| 文件 | 文字区细节 | 文字区暗像素 | 平均亮度 | 色调 | 结论 |
|---|---|---|---|---|---|
| `success_background.png` | 1.18 | 0.031 | 173 | `#d39ca1` 暖 | ✅ 可用（夕阳宫门剪影）|
| `gameover_background.png` | 6.72 | 0.762 | 102 | `#536b84` 冷 | ⚠️ 可用（雨中空街；细节偏高但中央是大片亮路面）|
| `prologue_background.png` | **0.70** | **0.004** | **194** | `#d9baac` **暖褐** | ✅ **最优**（书房暖光，文字最清楚）|

（本作基调参照：`main_bg.png` 色调 `#ba916b` / 暖度 +；`main.png` 平均亮度 138。）

---

## 三、已知不足（如实）

| 项 | 说明 |
|---|---|
| `gameover` 建筑偏欧式 | 提示词写的是明代市井，出来是**带尖顶的木架房** —— 这是本机底模反复出现的"西式漂移"（之前 concept 轮也记录过）|
| `success` 色偏紫粉 | 不是本作主色（暖褐），但与"夕阳中第"的氛围相符 |
| `prologue` 物象偏抽象 | 书本、笔筒、格栅窗以剪影与色块呈现，不是写实场景 |

**三张都还需要人眼定夺**（判据只能筛掉明显不合格，不能替代审美判断 ——
这一点在前几轮已由三个实例确认，见 `ART_METHOD_FINDINGS.md` §三）。

---

## 四、复用配方

```
底模  Illustrious-XL-v2.0          ← 关键：画风由底模决定（ART_METHOD_FINDINGS.md §一）
接口  POST /sdapi/v1/txt2img
参数  1152x648 / 28 步 / cfg 6.0 / DPM++ 2M Karras / --no-half-vae
提示词结构 = [具体场景描述] + [flat illustration, clean flat colour shapes, low contrast,
             no text, no writing, no signs, no banners, no people]
负面词必列 = text / characters / calligraphy / chinese characters / kanji / seal /
            shop sign / signboard / hanging scroll / plaque / banner / person / face /
            photograph / photorealistic
```

**经验**：场景描述要**具体到实体**（"closed wooden shutters lining both sides"胜于"a street"），
否则出抽象几何（本轮 `gameover2` 第一版就是）。

脚本：`tools/gen_ending_shots.py`（参数化了 SHOTS/SEEDS/OUT，可继续加候选）
