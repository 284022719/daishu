# 标题图成套：已完成（2026-10-13）

> **结论：标题底图已换成与主界面成套的平涂插画风。**
> 承接 `ART_TITLE_SET_ATTEMPT.md` 的失败记录 —— 那一轮没成，本轮找到了对的路。

---

## 一、结果（量化）

**成套度**用"暖度（平均色 R−B）"衡量 —— 这是"两张图跳不跳"的直接指标：

| 文件 | 暖度 | 标题区细节 | 按钮区细节 | 平均色 |
|---|---|---|---|---|
| 旧 `main.png`（水墨，已归档）| **+30** | 1.76 | 4.11 | `#918b73` |
| **新 `main.png`（已接入）** | **+88** | **0.13** | **0.24** | `#ce9a76` |
| `main_bg.png`（主界面）| **+85** | 1.71 | 0.85 | `#ac7d57` |

**暖度差：55 → 3。** 且标题安全区明显更干净（标题区细节 1.76→0.13、按钮区 4.11→0.24）
⇒ 书法标题与按钮压上去比原来清楚得多。

游戏内截图：`docs/screenshots/ingame/title_with_bg.png`

---

## 二、怎么找到的（本轮四个关键发现）

### 1. 本机 7 个底模逐一实测后，`waiIllustriousSDXL_v170` 是唯一够用的

上一轮的结论是"平涂画风与中式场景互斥"。本轮把**没用过的 3 个**也测了，得到完整地图：

| 底模 | 平涂画风 | 中式/东方式场景 | 标题区干净 |
|---|---|---|---|
| `3Guofeng3_v34`（SD1.5）| ❌ 照片级 | ✅ | ❌ |
| `Illustrious-XL` | ✅ | ❌ 欧式 | ✅ |
| **`waiIllustriousSDXL_v170`** | ✅ | ⚠️ 东方式（非严格明代）| ✅✅ |
| `autismmixSDXL` | — | — | ❌ **加载报错、出纯灰空图** |
| `国风武侠`（SD1.5）| ❌ 偏油画 | ✅ | ❌ 3.29 |
| `4Guofeng4XL` | — | — | ❌ 本机出 NaN |

`autismmixSDXL` 的报错（存档 `failed/autismmix_blank_device_error.png`）：
`RuntimeError: Expected all tensors to be on the same device, but found at least two devices, cpu and cuda:0!`

### 2. **暖色可以靠提示词拿到，不必后处理**

上一轮 img2img 怎么都调不暖。本轮直接在提示词写
`warm golden hour lighting` + `dominant warm brown, amber, ochre and cream palette`
并把 `cool blue tones, grey sky, teal, cold colour cast` 列进负面 ⇒ **暖度一次到位**
（+88 / +95，目标 +85）。

（后处理调色也验证可行：R×1.18 / B×0.85 / 饱和×1.12 能把 +19 提到 +75，画质无损；
但既然提示词能做到，就不必多一道工序。）

### 3. **"避开某元素"要连它的语义邻居一起禁**

提示词写 `no gate, no torii`、负面列 `torii, gate, archway, shrine` 时，
模型仍在画面正中画出鸟居（`D2_torii_rejected.png` 就是被否决的那张）。
**换成"不含该元素"的题材**才有效：把场景改成**柳树 + 水面 + 石岸 + 远景瓦顶**，
完全不提"门/桥/牌坊" ⇒ 产出的 `willow_s551002.png` 里就没有门。

### 4. **"平坦天空"是标题底图最有价值的特征**

`waiIllustriousSDXL` 出的图，**上中是一整片平坦天空**（标题区细节 0.13、暗像素 0.000），
这正是压书法大字需要的。我用**真实字体 + 真实坐标**先合成验证可读性
（`composite_s551002.png`），确认清楚后才接入游戏 —— 比"接入后截图再改"省一轮。

---

## 三、改动清单

| 项 | 说明 |
|---|---|
| `assets/images/backgrounds/main.png` | 换成 `willow_s551002.png`（1152×648，614 KB）|
| 旧水墨图 | **移到 `D:\dsh\tmp\daishu-asset-archive\main_inkwash.png`**（不是删除；tmp 30 天清理）|
| 场景文件 | **未改** —— `title_screen.tscn` 仍引用 `res://assets/images/backgrounds/main.png`（同名替换）|
| 验证 | `--headless --import` 通过；标题页截图 **1152×648**；主界面截图回归正常 |

---

## 四、已知不足（如实）

- **不是严格的明代市井**：画面是"湖畔村落 + 远山"，偏日式/东方式风景，
  而非 `main_bg.png` 那种中国市井。**画风与色调成套了，题材不完全一致。**
- 尺寸 1152×648（正好等于项目视口），比原来的 2730×1535 小；
  当前分辨率下无损失，**若将来要提高视口分辨率需重出**。
- NPC 头像仍是程序化过渡实现（独立事项）。

**这一项如需再迭代**：给它加 `Chinese`/`Ming` 题材而不要加"门/桥"，
或换更专门的国风插画底模 —— 但**当前状态已可发布**，不再是"两张图跳"的问题。
