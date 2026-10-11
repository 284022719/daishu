---
name: godot-docs
description: 查本地 Godot 4.6 官方文档语料（类参考 1066 篇 + 教程 426 篇）核对 API、节点、信号、属性、注解与引擎用法。写或审 GDScript 前先在这里查证，不要凭记忆写 API。
whenToUse: 任务涉及 Godot 引擎 / GDScript / 场景 / 节点 / 信号 / 资源 / 导出 / 渲染或物理设置 / 报错排查时
---

# 语料（第一依据 —— 别凭记忆写 API）

- `D:\个人项目\daishu\godot-docs`：gitcode 镜像的 godot-docs 仓库，**4.6 分支**（HEAD `b10b7ed`），
  纯文本稀疏检出 1568 篇 `.rst`。
  **2026-10-11 从 `D:\godot-docs` 迁入本项目目录**（见下方「语料的边界」）。
- **版本锚点 4.6**：本机引擎 v4.6.1-stable (mono) 与文档同代。图片与动图**未检出**，正文里的图片链接指向
  `raw.githubusercontent.com`（本机访问不了）—— **不要追图片**。
- **语料的边界（2026-10-11 实测，别误解它）**：这是 `blob:none` 的**部分克隆**，本地只有那个提交的树，
  **没有 blob 对象**；`git status` / `git checkout` 会去 gitcode.com 取 blob，而本机代理拦 403 →
  报 `could not fetch … from promisor remote`。所以它现在是**只读的纯文本语料**：
  **拿它查文档可以，拿它切分支/回滚不行**（要切分支得先能连通 gitcode 或重新克隆）。

# 目录地图

| 要查什么 | 去哪 |
|---|---|
| 类参考（属性 / 方法 / 信号 / 枚举 / 常量） | `classes\class_<小写类名>.rst`：`Node2D`→`class_node2d.rst`、`HTTPRequest`→`class_httprequest.rst` |
| GDScript 语言本身（语法、类型、注解） | `classes\class_@gdscript.rst` |
| 全局函数与单例（`print` / `load` / `Input` / `Engine`…） | `classes\class_@globalscope.rst` |
| 教程与最佳实践 | `tutorials\<主题>\`：2d 3d animation assets_pipeline audio best_practices editor export i18n inputs io math migrating navigation networking performance physics platform plugins rendering scripting shaders ui xr |
| 入门 / 引擎内部机制 | `getting_started\` / `engine_details\` |

# 检索配方

用 DSH 的 `grep` / `glob` / `read` 工具；**本机 shell 里没有 `rg`**，别在 pwsh 里拼 ripgrep。

1. **查某个类**：先 `grep` 定位行号，再 `read` 该片段（类文件通常 300–3000 行）：
   `grep pattern="move_and_slide|position" path=D:\个人项目\daishu\godot-docs\classes\class_characterbody2d.rst`
2. **不确定方法/信号/属性属于哪个类**（最有用的起手式）：
   `grep pattern="^\.\. _class_\w+_method_move_and_slide:" path=D:\个人项目\daishu\godot-docs\classes`
   锚点规则是 `class_<类名>_(method|property|signal|constant|enum)_<名字>`，把 `method` 换成
   `signal`/`property` 即可反查信号与属性。
3. **查主题做法**（拖放 / 存档 / 相机跟随 / 状态机）：
   `grep pattern="drag and drop" path=D:\个人项目\daishu\godot-docs\tutorials`，命中后读对应 rst。
4. **查废弃与版本迁移**：`grep pattern="deprecated|removed in 4\." path=D:\个人项目\daishu\godot-docs\tutorials\migrating`。

**类参考结构**：`.. _class_Node2D_method_apply_scale:` + `|void| **apply_scale**(…)`；
`:ref:`X<class_X>`` 括号里的类型名（转小写）就是下一个能查的文件；章节顺序
Description → Properties → Methods → Signals → Enumerations → Constants；顶部 `Properties`/`Methods`
总览表用来快速判断"这个类到底有没有这个能力"。

# 纪律

- **断言 API 必须给出处**：`classes\class_xxx.rst` 文件名 + 行号。查不到就直说"文档里没有"，
  **不要拿 3.x 的旧记忆补齐**。
- 本项目是 4.x：留意 `@export` 注解写法、`Tween`、`Callable`、`Node.owner` 语义、单例访问方式；
  文档里标 `deprecated` 的一律不用。
- **可以联网，但第一依据仍是本地语料**（它锚定 4.6，官网 `/en/stable/` 未必是 4.6）：
  `web_fetch` 工具存在（2026-10-10 复测，推翻 2026-09 的旧结论），`docs.godotengine.org` 实测 HTTP 200。
  只在①本地语料确实没有 ②核对某条 API 在 4.6 之后是否变更 时用；引用官网时要说明它可能不是 4.6。
- 拿不准就是在猜。宁可多读一篇 rst，也不要写一个没出处的 API。

# 项目文档地图（代书，`D:\个人项目\daishu`）

写代码前先看项目自己的文档 —— 它们比通用教程更贴近本项目约定：

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
| 美术素材校验工具 + 提示词 JSON | `tools\art_check.mjs`、`data\art_prompts_round*.json` |
| 给 AI 助手的项目约定 | `CLAUDE.md` |

**代码为准**：文档与实现冲突时以实际实现为准（`docs\readme.md` 曾长期滞后，2026-09 校正过一次），
并顺手把文档改对。

# 本机踩坑（结论清单 —— 每条都实际踩过）

> 完整场景、命令与数字见 `DETAILS.md`「本机踩坑（完整版）」。这里只留"该怎么判"。

1. **`godot --check-only --script` 不注册 autoload** → 引用单例的脚本一律报 `Identifier not found`，
   **是假阳性**。判据：拿一个没动过、同样引用单例的脚本做对照组（全报＝模式问题）。
2. **整数除法警告**：`int(a / b)` 里的 `int()` 多余且消不掉警告，改用 `floori(a / b.0)`（负数语义不同）；
   该警告只在运行时出现，headless 看不到。
3. **Godot 段错误先怀疑文件权限**：沙箱拦 `user://` 写入时崩在项目加载**之前**（`--check-only` 也崩、
   `--verbose` 无任何资源加载输出）—— 是环境问题，不是代码问题。
4. **`unique_id=` 是 4.6 新语法**（`load_steps` 已废弃）—— 别当错误去"修"。
5. **godot-mcp 接线会"自己消失"，状态必须现查**：条目是 profile `cordis.patch.yml` 里的 `mcp-godot`
   （`insert`，热监听）。**判据三查**：① 文件里有 `mcp-godot` ② 进程表有
   `node.exe … godot-mcp\build\index.js` ③ 新会话工具清单里有 `mcp__godot__*`。`GODOT_PATH` 必须是
   `*_console.exe`，**指错不报错、只是静默没有调试输出**；路径失效则静默回落到内置默认值。
   Godot 现装在 `D:\Program Files\Godot_v4.6.1-stable_mono_win64\`（含空格，别拼进未加引号的命令行）。
6. **美术素材必须像素级校验，禁止目测**：`tools\art_check.mjs`（零依赖）——
   `info` / `palette`（色距 >0.30 判偏离）/ `grid` / `watermark` / `crop`；
   带网格的底图改锚点必须走 `grid` → 写锚点 → 截图复验三步。
7. **沙箱拦 `user://` 的确切判据**：崩溃前必有 `Failed to open 'user://logs/godot<时间戳>.log'` +
   `signal 11`，且无任何资源加载输出；放宽权限后同命令 exit 0 零输出。
8. **`--script` 模式不导入新资源**：新加的图片在 `--script` 下 `ResourceLoader.exists()` 返回 **false**、
   **静默加载失败**（贴图为 null，不报错）。判据：新资源先跑一次
   `godot --headless --path . --import`（生成 `.import` + `.ctex`），再跑截图/测试。
9. **`_get_drag_data()` 不能直接调**：没有真实拖拽在进行时，里面的 `set_drag_preview()` 会触发引擎断言
   `Condition "!get_viewport()->gui_is_dragging()" is true`。判据：**把预览构造抽成独立函数**
   （本项目 `build_drag_preview()`），测试只调它；顺带 Godot 会给 `docs\` 下的配图也生成 `.import`，
   那些是文档图、不该进仓库。
10. **`.tres` 里 stylebox 的键名别手写，让引擎写**：本地语料没有 `.tres` 示例，手写 `Button/styles/normal`
    这类键猜错会**静默失效**（主题挂上了却没样式）。判据：用代码建 `Theme` 再 `ResourceSaver.save()`；
    方向反过来时——**改完立即 `load()` 回读会命中写入前的缓存**（实测 `default_font_size` 读到上一版），
    回读要**读文件文本**，语义校验另起一个进程。
11. **`Font.fallbacks` 不会进 `.tres`，且 Godot 不会自动回退系统字体**：赋在 `FontFile` 上或包一层
    `FontVariation` 都一样，存盘再 load 回来都是 0 条 —— **只能运行时挂**（本项目 `scripts/FontFallback.gd`
    自启动）。判据：拿一个**主字体确实没有**的字符渲染一张图看是不是方块（实测项目外用字确实渲染成方块）。
    另：挂了兜底后字体变成 `FontVariation`，它**没有 `font_name`**，要取 `.base_font.font_name`。
12. **命令行 `--resolution` 会连同视口一起改，截图会被缩放**：实测给 `900x260` 时出图只有 `462x260`
    （约 0.40 倍），而拿它当像素依据会得出错误结论。判据：截图工具自己 `DisplayServer.window_set_size()`
    + `get_root().size`，**写完图断言尺寸**，不符就报错而不是静默产出。
13. **全局 Theme 的字号会改变布局、撑破容器**：实测字号 20 + 内容边距 8 时，代写界面左侧 15 个词库按钮
    撑出面板、底部被裁。判据：**换全局字号后必须重截所有用了列表/多按钮的界面**，
    并按"按钮数 × 单按钮高"估算是否装得下。

# 维护与导出

- **装导出模板**（没有它无法产出 exe）、**升级引擎切语料分支**、**恢复图片**、**网络可达性**：
  命令与注意事项见 `DETAILS.md`「维护与导出」。
- 要点：`%APPDATA%\Godot\export_templates\` 默认空；mono 引擎要 `mono_export_templates.tpz`；
  **slug 与引擎口味不一致不会报错、只会导出失败**。

# 源码与同步（本文件即 DSH 技能 `godot-docs` 的源）

- **源**（受 git 版本控制，改这里）：`docs\AI_PLAYBOOK.md`（判据，常驻）+
  `docs\AI_PLAYBOOK-DETAILS.md`（细则，按需）
- **镜像**（DSH 实际读取；它在用户目录下、不在任何 git 仓库里，换机器或重装 DSH 会丢）：
  `C:\Users\28402\.dsh\skills\godot-docs\SKILL.md` + 同目录 `DETAILS.md`
- 改完必须同步，否则 DSH 读到的仍是旧知识：
  `pwsh -File tools\sync-ai-playbook.ps1`（`-Check` 只查漂移，不一致 exit 1）
