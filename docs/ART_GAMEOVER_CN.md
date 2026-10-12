# gameover 背景重出：去掉欧式建筑（2026-10-13）

> 承接 `ART_TITLE_SET_DONE.md` —— 那一轮解决了标题图。本轮用它验证的 `waiIllustriousSDXL_v170`
> 重出 `gameover` 背景，**去掉欧式尖顶木架房**，换成中式雨夜。

---

## 一、结果

| 文件 | 暖度 | 中央带细节 | 中央带暗像素 | 色调 |
|---|---|---|---|---|
| 旧 `ending_gameover.png`（欧式，已归档）| −49 | **6.72** | 0.558 | `#536b84` |
| **新 `ending_gameover.png`（已接入）** | −27 | **4.17** | **0.461** | `#657780` |

**三项都改善**：建筑中式化、中央带细节 6.72→4.17、暗像素 0.558→0.461
⇒ 半透明宣纸底板下的文字更好读。**冷调保持**（−27，忧郁雨夜的正确方向）。

游戏内截图：`docs/screenshots/ingame/gameover_with_bg.png`

---

## 二、配方

```
底模  waiIllustriousSDXL_v170      ← 见 ART_TITLE_SET_DONE.md：7 个底模里唯一"平涂+构图干净"
参数  1152x648 / 28 步 / cfg 6.0 / DPM++ 2M Karras / --no-half-vae
```

**提示词要点**（这是与标题图不同的地方）：

- **明确写中式构件**：`wooden lattice windows` / `whitewashed plaster walls` /
  `dark grey tiled roofs with gently upturned eaves` / `exposed wooden columns`
- **把欧式列进负面**：`european architecture` / `half-timbered house` / `romanesque arch` /
  `gothic` / `victorian` / `arched window` / `pointed roof` / `chimney`
- **gameover 要冷调，所以不加暖色词**，只留 `warm lantern accents` 作点缀
  （标题图那轮是反过来的：靠 `warm golden hour lighting` 提暖度）
- 负面里加 `torii, japanese shrine, pagoda` 防掉进日式（该底模有日式先验）

---

## 三、验证

| 项 | 结果 |
|---|---|
| `--headless --import` | 通过（同名替换，尺寸变化触发重导入）|
| `gameover` 截图 | **1152×648**，exit=0，无 ERROR |
| 回归：`success` / `prologue` / `title` | 全部 1152×648、exit=0、无 ERROR |
| 旧图处置 | **移到** `D:\dsh\tmp\daishu-asset-archive\ending_gameover_european.png`（不是删除）|

---

## 四、素材现状（全部六个界面）

| 界面 | 贴图 | 尺寸 | 状态 |
|---|---|---|---|
| `title_screen` | `main.png` | 1152×648 | ✅ 平涂插画，与主界面成套（暖度差 3）|
| `main` | `main_bg.png` | 2730×1535 | ✅ 原始素材 |
| `letter` | `letter.png` | 2364×1773 | ✅ 原始素材 |
| `prologue` | `prologue_bg.png` | 1152×648 | ✅ 已接入 |
| `success` | `ending_success.png` | 1152×648 | ✅ 已接入 |
| `gameover` | `ending_gameover.png` | 1152×648 | ✅ **本轮换成中式雨夜** |

**六个界面全部有贴图、且画风统一**（平涂插画 + 暖/冷按剧情分）。

---

## 五、仍待办（都不阻塞）

| 项 | 说明 |
|---|---|
| NPC 头像 | 仍是程序化过渡实现（`scripts/npc_avatar.gd`），接口按真素材可替换 |
| 部分图分辨率 | `main`/`main_bg`/`letter` 是高分原图；而 `main.png`/`ending_*`/`prologue_bg` 是 **1152×648**，正好等于当前视口。**若将来提高视口分辨率需重出这四张** |
| `success` 题材 | 现为夕阳宫门剪影，与 `gameover` 的中式雨夜风格统一，可保持 |
| 字体「以」字形 | 寒蝉龙藏体的 `以` 设计异常（见 `PRE_RELEASE_UI_CHECK.md`），要换字体或改文案 |
