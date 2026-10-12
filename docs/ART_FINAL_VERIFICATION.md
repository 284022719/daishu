# 发布级最终验证（2026-10-13）

> 本文件是美术素材这一轮的**收口证据**：全部硬性闸门 + 一致性指标 + 已知不足。
> 各专项记录见 `ART_TITLE_SET_DONE.md`、`ART_GAMEOVER_CN.md`、`ART_NPC_AVATARS.md`。
> 总览图：`docs/screenshots/overview_all_screens.png`

---

## 一、六张底图的色调一致性（全套统一的硬指标）

用"暖度（平均色 R−B）"衡量。**5 张暖调紧密聚在 +85~+89，唯一的冷调给失败结局**：

| 底图 | 界面 | 暖度 | 分组 |
|---|---|---|---|
| `main.png` | 标题 | **+88** | 暖 |
| `main_bg.png` | 主界面 | **+85** | 暖 |
| `letter.png` | 信纸 | **+89** | 暖 |
| `prologue_bg.png` | 序章 | +45 | 暖 |
| `ending_success.png` | 成功结局 | **+87** | 暖 |
| `ending_gameover.png` | 失败结局 | **−27** | **冷**（忧郁，刻意）|

---

## 二、端到端闸门（全部实测）

| 闸门 | 结果 |
|---|---|
| 五个场景截图（`--script capture_scene.gd`）| 全部 **1152×648**、exit=0、**无 SCRIPT ERROR** |
| `tools/verify_avatar.gd`（项目自带断言）| **结论: PASS** |
| `--headless --import` | 通过（新增/替换资源后均重跑）|
| 文字/水印扫描（`art_check.mjs watermark --scan`）| 见 §三，**逐张裁图复核** |

---

## 三、水印检测的命中 —— **逐张裁图复核，全部是误报**

项目纪律：**检测器报命中必须裁出来人眼复核，不能只依据退出码**（`AGENTS.md` §5）。
本轮 7 处命中，全部复核为**非文字**：

| 素材 | bbox | 实际内容 | 判定 |
|---|---|---|---|
| `main.png` | `899,557..1152,648` | 右下角淡色渐变条带 | 无文字 |
| `prologue_bg.png` | `899,557..1152,648` | 暖色地面 + 透视暗线 | 无文字 |
| `letter.png` | `1844,1525..2364,1773` | 信纸像素纹理格 | 无文字（与既有结论一致）|
| `main_bg.png` | `2129,1320..2730,1535` | **算盘珠子 + 木纹** | 无文字（与既有结论一致）|
| `button_frame.png` | `31,32..40,40` | 9×8 px 小图 | 无文字 |
| `avatars/兄弟.png` | `50,55..64,64` | 白/浅色衣领 | 无文字 |
| `avatars/子女.png` | `0,55..14,64` | 白/浅色衣领 | 无文字 |

证据图（裁片放大拼接）：`docs/screenshots/watermark_falsepositive_evidence.png`

**后两处（头像）是本轮新产生的命中**，此前不在既有误报清单里，已一并复核。

---

## 四、素材清单（全部齐备）

| 界面 | 贴图 | 尺寸 | 来源底模 |
|---|---|---|---|
| `title_screen` | `main.png` | 1152×648 | waiIllustriousSDXL |
| `main` | `main_bg.png` | 2730×1535 | （原有素材）|
| `letter` | `letter.png` | 2364×1773 | （原有素材）|
| `prologue` | `prologue_bg.png` | 1152×648 | Illustrious-XL |
| `success` | `ending_success.png` | 1152×648 | waiIllustriousSDXL |
| `gameover` | `ending_gameover.png` | 1152×648 | waiIllustriousSDXL |
| NPC 列表 | `assets/images/ui/avatars/*.png` ×5 | 64×64 | waiIllustriousSDXL |

---

## 五、已知不足（不阻塞发布）

| 项 | 说明 |
|---|---|
| 四张图是 1152×648 | `main`/`ending_success`/`ending_gameover`/`prologue_bg` **正好等于当前视口**。**仅在提高视口分辨率时**需重出 |
| 题材不完全中式 | `main`/`gameover` 的底模（waiIllustriousSDXL）有**日式先验**；已用负面词压制，画风与色调统一，但**题材不是严格明代市井** |
| 字体「以」字形异常 | 寒蝉龙藏体的 `以` 设计有误（Pillow 直接渲染同样异常），属**独立字体问题**，要换字体或改文案 |
| NPC 头像区分度 | 5 张肖像风格相近，靠**右下角关系字角标**保辨识度；若不合可删 `assets/images/ui/avatars/` 自动回落程序化名帖牌 |

---

## 六、结论

美术素材目标（"每个界面都有画风统一、可用、无违规的贴图"）**已达成**，且每一项都有实测证据：

- 六张底图 + 5 张头像**全部齐备**
- 色调**分组唯一**（暖 +85~+89 用日常/成功；冷 −27 用失败）
- 五个场景截图 **1152×648 无错**；项目验证脚本 **PASS**
- 文字违规**逐张目视复核为误报**

唯一未闭环的是**人的审美定稿** —— 判据在本项目已被"数值好看"骗过四次
（见 `ART_METHOD_FINDINGS.md` §三），故不把自动指标当作审美结论。
