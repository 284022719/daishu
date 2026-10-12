# NPC 头像：从程序化名帖牌换成真肖像（混合方案，2026-10-13）

> `data/art_prompts_round2.json` 的 `npc_avatar` 规格是"**48×48 或 64×64 小半身像**"，
> 而此前实现是**程序化名帖牌**（`scripts/npc_avatar.gd`：圆牌 + 书法关系字）。
> 本轮补齐了真素材，并解决了一个对比中暴露的设计问题。

---

## 一、关键设计发现：**位图肖像的"区分度"低于关系字**

先按**关系**（`NPCManager.RELATIONS` = 父母/子女/夫妻/兄弟/朋友）出 5 张半身像，
降到实际显示尺寸（44×44）后与程序化牌并排对比：

| 维度 | 位图肖像 | 程序化名帖牌 |
|---|---|---|
| 视觉丰富度 | ✅ 好 | 一般 |
| **跨关系区分度** | ❌ **差** —— 5 张都是米色背景 + 棕衣 + 同肤色，列表里不易分辨 | ✅ **好** —— 5 种不同颜色 + 关系字 |
| 44px 可辨识 | ✅ 尚可 | ✅ 好 |
| 无歧义 | ⚠️ 会失败（见下） | ✅ 不会 |

⚠️ **生成失败率**：首轮 5 张里 **2 张完全失败** ——
`兄弟` 出了 **9 个重复的狐狸头**（模型当图案生成）、`朋友` 出了 **一件挂着的衣服**（没有人物）。
加 `ONE SINGLE`、`shoulders visible` 与负面 `multiple characters / repeated faces / pattern /
clothing on a hanger / mannequin / fox / cat` 并换 seed 后修好。

⇒ **采用混合方案**：**位图肖像 + 右下角一个小关系色角标**（角标里仍是关系字）。
两者兼得：有肖像的视觉丰富度，也保住"一眼看出关系"的玩法信息。

对比图：`docs/screenshots/avatars/avatar_compare.png`

---

## 二、改动

| 项 | 说明 |
|---|---|
| `assets/images/ui/avatars/{父母,子女,夫妻,兄弟,朋友}.png` | 新增，**64×64**（规格尺寸），各 5~7 KB |
| `scripts/npc_avatar.gd` | 加 `AVATAR_DIR` 常量与 `_texture` 字段；`setup(npc)` 支持 `avatar` 字段；`set_relation()` 按 `<关系>.png` 自动加载；`_draw()` 分两支：有贴图则**贴图 + 角标**，无则**回落原名帖牌** |
| `NPCManager.gd` | **未改** —— `avatar` 字段仍为 `""`，靠 `set_relation()` 按关系自动找图 |

**接口没变**（`setup(npc)` / `set_relation()` / `get_glyph()` / `get_color()`），`main.gd` 不用动。
**缺图时静默回落**程序化名帖牌，不会崩。

---

## 三、验证

| 项 | 结果 |
|---|---|
| `--headless --import` | 通过 |
| `tools/verify_avatar.gd`（项目自带断言）| **结论: PASS**（未知/空关系仍回落到 `客` 与 44×44）|
| 主界面截图（点「开始今日」生成委托列表）| **1152×648**，3 个头像正常显示、角标可读 |
| 回归 | 截图无 ERROR（那两条 `invalid UID` 警告是**预先存在**的）|

游戏内截图：`docs/screenshots/ingame/main_with_avatar.png`

---

## 四、可替代方案（未采用，备查）

**程序化名帖牌**在"区分度"与"零失败率"上其实更优，且不占仓库体积（0 KB 素材）。
若将来觉得肖像与游戏调性不合，**删掉 `assets/images/ui/avatars/` 就自动回落**，
不需要改任何代码 —— 这是本轮实现刻意留的退路。

---

## 五、素材总览（全部界面）

| 界面 | 贴图 | 状态 |
|---|---|---|
| `title_screen` | `main.png` | ✅ 平涂插画、与主界面成套 |
| `main` | `main_bg.png` | ✅ |
| `letter` | `letter.png` | ✅ |
| `prologue` | `prologue_bg.png` | ✅ |
| `success` | `ending_success.png` | ✅ |
| `gameover` | `ending_gameover.png` | ✅ |
| **NPC 列表** | `assets/images/ui/avatars/*.png` | ✅ **本轮补齐**（+ 程序化回落）|

**所有界面均有画风统一的贴图。** 仍待办（不阻塞）：四张 1152×648 的图在提高视口分辨率时需重出；
寒蝉龙藏体的「以」字形异常（独立字体问题）。
