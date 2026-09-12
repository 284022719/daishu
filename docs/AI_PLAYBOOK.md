---
name: godot-docs
description: 查本地 Godot 4.6 官方文档语料（类参考 1066 篇 + 教程 426 篇）核对 API、节点、信号、属性、注解与引擎用法。写或审 GDScript 前先在这里查证，不要凭记忆写 API。
whenToUse: 任务涉及 Godot 引擎 / GDScript / 场景 / 节点 / 信号 / 资源 / 导出 / 渲染或物理设置 / 报错排查时
---

# 语料

- 位置：`D:\godot-docs`（gitcode 镜像的 godot-docs 仓库，**4.6 分支**，HEAD `b10b7ed`）
- **版本锚点 4.6**：本机引擎是 Godot v4.6.1-stable (mono)，文档与引擎同代。升引擎要切分支（见文末）。
- 纯文本稀疏检出：只有 `.rst`，1568 篇 / 30.7 MB。图片与动图**未检出**，文档正文里的图片链接指向 `raw.githubusercontent.com`，本机也访问不了 —— **不要追图片**。

# 目录地图

| 要查什么 | 去哪 |
|---|---|
| 类参考（属性 / 方法 / 信号 / 枚举 / 常量） | `D:\godot-docs\classes\class_<小写类名>.rst`：`Node2D`→`class_node2d.rst`，`HTTPRequest`→`class_httprequest.rst` |
| GDScript 语言本身（语法、类型、注解） | `D:\godot-docs\classes\class_@gdscript.rst` |
| 全局函数与单例（`print` / `load` / `Input` / `Engine`…） | `D:\godot-docs\classes\class_@globalscope.rst` |
| 教程与最佳实践 | `D:\godot-docs\tutorials\<主题>\`：2d 3d animation assets_pipeline audio best_practices editor export i18n inputs io math migrating navigation networking performance physics platform plugins rendering scripting shaders ui xr |
| 入门 | `D:\godot-docs\getting_started\` |
| 引擎内部机制 | `D:\godot-docs\engine_details\` |

# 检索配方

用 DSH 的 `grep` / `glob` / `read` 工具；**本机 shell 里没有 `rg` 命令**，别在 pwsh 里拼 ripgrep。

1. **查某个类**：先 `grep` 定位行号，再 `read` 该片段（类文件通常 300–3000 行）。例如查节点平移：
   `grep pattern="move_and_slide|position" path=D:\godot-docs\classes\class_characterbody2d.rst`
2. **查某个方法/信号/属性在哪个类**（不确定归属时最有用的起手式）：
   `grep pattern="^\.\. _class_\w+_method_move_and_slide:" path=D:\godot-docs\classes`
   锚点命名规则是 `class_<类名>_(method|property|signal|constant|enum)_<名字>`，把 `method` 换成 `signal`/`property` 就能反查信号和属性。
3. **查主题做法**（"怎么做拖放 / 存档 / 相机跟随 / 状态机"）：
   `grep pattern="drag and drop" path=D:\godot-docs\tutorials`，命中后读对应 rst。
4. **查废弃与版本迁移**：`grep pattern="deprecated|removed in 4\." path=D:\godot-docs\tutorials\migrating`。

# 类参考的文件结构（读的时候用得上的锚点）

```
.. _class_Node2D_method_apply_scale:
.. rst-class:: classref-method
|void| **apply_scale**\ (\ ratio\: :ref:`Vector2<class_Vector2>`\ )
```

- `:ref:`X<class_X>`` 是交叉引用，括号里的类型名（转小写）就是下一个能查的文件名。
- 章节顺序：Description → Properties → Methods → Signals → Enumerations → Constants → Property/Method Descriptions。
- 顶部的 `Properties` / `Methods` 总览表用来快速判断"这个类到底有没有这个能力"。

# 纪律

- **断言 API 必须给出处**：`classes\class_xxx.rst` 文件名 + 行号。查不到就直说"文档里没有"，不要拿 3.x 的旧记忆补齐。
- 本项目是 4.x：留意 `@export` 注解写法、`Tween`、`Callable`、`Node.owner` 语义、单例访问方式等 4.x 与 3.x 的差异；文档里标 `deprecated` 的一律不用。
- **本机不能联网取文档**：`docs.godotengine.org`、`github.com`、`raw.githubusercontent.com`、`downloads.tuxfamily.org` 均 SSL 不通，且本部署没有 `web_fetch` 工具（只有 `web_search`）。不要试图抓网页，一律查本地语料；需要引用官网 URL 时只把它当"给人看的链接"，不作检索源。
- **但以下主机可达**（2026-09 实测）：`godotengine.org`（主站，HTTP 200）、`downloads.godotengine.org`（会 302 到 `release-assets.githubusercontent.com`）。**导出模板正是从这里下**，见文末。
- 拿不准就是在猜。宁可多读一篇 rst，也不要写一个没出处的 API。

# 项目文档地图（代书，`D:\daishu`）

写《代书》的代码前，先看项目自己的文档——它们比通用教程更贴近本项目约定：

| 要查什么 | 去哪 |
|---|---|
| 总览 / API 摘要 / 判定规则 | `docs\readme.md` |
| 三单例职责与依赖关系 | `docs\ARCHITECTURE_SINGLETONS.md`、`docs\SINGLETON_APIS.md` |
| 场景节点树与信号连接 | `docs\SCENE_OVERVIEW.md` |
| NPC 字典 / 存档 / 玩家答案字段 | `docs\DATA_FORMATS.md`、`docs\NPC_GENERATION.md` |
| 判定计费逻辑 | `docs\JUDGE_SYSTEM_LOGIC.md` |
| 平衡数值与模拟结论 | `docs\BALANCE_REPORT.md` |
| 开发路线图与已知风险 | `docs\DEV_PLAN.md` |
| 美术方向 / 色板 / 生成提示词 | `docs\ART_PLAN.md`、`docs\ART_BASELINE_ROUND1.md` |
| 美术素材**校验工具**（色板/栏线/水印）+ 生成提示词 JSON | `tools\art_check.mjs`、`data\art_prompts_round1.json`、`data\art_prompts_round2.json` |
| 给 AI 助手的项目约定 | `CLAUDE.md` |

⚠️ `docs\readme.md` 曾长期滞后于代码（2026-09 校正过一次）。**代码为准**；文档与实现冲突时以实际实现为准，并顺手把文档改对。

# 本机踩坑记录（都是实际踩过的）

1. **`godot --check-only --script` 不注册 autoload** —— 任何引用单例的脚本都会报
   `SCRIPT ERROR: Compile Error: Identifier not found: PlayerManager / JudgeSystem`。
   这是**假阳性，不是代码错误**：未改动的 `main.gd`、`title_screen.gd`、`EndGameScreen.gd` 同样报。
   判定方法：**拿一个没动过、且同样引用单例的脚本做对照组**——全报就是模式问题，只有你改的那个报才是真问题。
2. **整数除法会警告** —— GDScript 4 对 `/` 两侧都是 `int` 的情况报
   `WARNING: Integer division. Decimal part will be discarded`。
   `int(a / b)` 里的 `int()` 是**多余**的且消不掉警告；改用 `floori(a / b.0)`（负数时二者语义不同，注意）。
   该警告**只在运行时 `GDScript::reload` 出现，headless 启动看不到** —— 想抓它得真跑项目。
3. **Godot 跑不起来 ≠ 项目有问题** —— 若沙箱拦截 `user://`（`%APPDATA%\Godot\app_userdata\<项目名>`）写入，
   Godot 会在**项目加载之前**就 signal 11 段错误，且 `--check-only` 单脚本同样崩、`--verbose` 也无任何资源加载输出。
   先怀疑文件权限，别怀疑代码。
4. **`unique_id=` 是 4.6 新语法**（`engine_details\file_formats\tscn.rst:104`），不是 3.x 残留；
   `load_steps` 在 4.6 已废弃、可忽略（同文件 `:51-53`）。别把它们当错误去"修"。
5. **godot-mcp 已接通，但 `GODOT_PATH` 指错会静默失效** —— 本部署注册了 **14 个** `mcp__godot__*` 工具
   （`launch_editor` / `run_project` / `get_debug_output` / `stop_project` / `get_godot_version` /
   `list_projects` / `get_project_info` / `create_scene` / `add_node` / `load_sprite` /
   `export_mesh_library` / `save_scene` / `get_uid` / `update_project_uids`），实测 `get_godot_version`
   返回 `4.6.1.stable.mono.official`。两个坑：
   - `GODOT_PATH` **必须指向 `*_console.exe`**：不带 console 的 exe 在 stdout 被重定向时输出 0 字节，而
     `run_project` / `get_debug_output` 靠捕获 stdout 工作 —— 指错**不报错，只是静默拿不到调试输出**。
   - 接线有**两处、互不相干**：项目内 `.claude\mcp.json`（被 gitignore）与 DSH 的
     `~\.dsh\profiles\web\cordis.patch.yml`（`mcp-godot` 条目，由 watchUserPatches 热监听，保存即生效）。
     复现用 `tools\setup-godot-mcp.ps1` —— 它**必须用 SSH 克隆**（本机 HTTPS 到 github.com 不通）。
6. **美术素材必须像素级校验，禁止目测**（ART_PLAN §四 已把这写成硬规范）—— 用 `tools\art_check.mjs`
   （零依赖，只用 node 内置 `zlib`，自带 PNG 解码/编码，**不需要 npm install**）：
   `info` / `palette`（对照 ART_PLAN §二 锚点色，色距 >0.30 判偏离）/ `grid`（栏线像素检测）/
   `watermark`（白色文字水印判定）/ `crop`（取局部交给人眼或 vision 复核）。
   已知事实：`letter.png` 是**双线制** —— 13 道栏界 = 12 栏，栏距 174.09px（CV 1.8%）；`grid` 检测值
   复现了 `letter.tscn` 里既有 6 个锚点（最大差 0.0009），说明锚点本来就是像素实测来的。
   **任何带网格的底图，改锚点必须走 `grid` → 写锚点 → 截图复验三步**；裁边会平移全部栏线，必须重跑。
7. **沙箱拦截 `user://` 的 signal 11 有了确切判据**（细化第 3 条）：崩溃前首行必然是
   `ERROR: Failed to open 'user://logs/godot<时间戳>.log'`，随后 `CrashHandlerException: Program crashed with signal 11`，
   且**没有任何资源加载输出**（崩溃早于项目加载）。放宽文件权限后同一条命令 **exit 0 且零输出** ——
   "崩溃点早于任何资源加载"就是环境问题的判据。

# 维护

引擎升级时（例如 4.7）：

```
git -C D:\godot-docs fetch --depth 1 origin 4.7
git -C D:\godot-docs checkout 4.7
```

需要恢复图片时（D 盘空间紧张，谨慎）：

```
git -C D:\godot-docs sparse-checkout set --no-cone "*.rst" "*.png" "*.svg"
```

## 装导出模板（没有它就无法产出 exe）

`%APPDATA%\Godot\export_templates\` 默认为**空**，`export_presets.cfg` 形同虚设。官方下载端点**可达**：

```powershell
# 版本号与 slug 要跟引擎对齐：mono 引擎要 mono_export_templates.tpz
$u = 'https://downloads.godotengine.org/?version=4.6.1&flavor=stable&slug=mono_export_templates.tpz&platform=templates'
Invoke-WebRequest -Uri $u -OutFile "$env:TEMP\templates.tpz"     # ≈1.09 GiB
```

装法：把 .tpz 解压出的 `templates/` 目录整个放到
`%APPDATA%\Godot\export_templates\4.6.1.stable.mono\`。

⚠️ 先确认 `slug` 与引擎口味一致——**用错口味不会报错，只会导出失败**。

# 源码与同步（本文件即 DSH 技能 `godot-docs` 的源）

- **唯一源**：`D:\daishu\docs\AI_PLAYBOOK.md`（本文件，受 git 版本控制）
- **镜像**：`C:\Users\28402\.dsh\skills\godot-docs\SKILL.md` —— DSH 实际读取的技能文件。
  它在用户目录下，**不属于任何 git 仓库**，换机器或重装 DSH 会丢，所以源放在仓库、镜像是派生物。
- 改完必须同步，否则 DSH 读到的仍是旧知识：

```powershell
pwsh -File tools\sync-ai-playbook.ps1          # 源 → 技能目录
pwsh -File tools\sync-ai-playbook.ps1 -Check   # 只查漂移；不一致 exit 1
```
