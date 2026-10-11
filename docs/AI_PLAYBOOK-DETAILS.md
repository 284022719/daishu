# godot-docs 细则（按需读）

> **判据在 `AI_PLAYBOOK.md`**（= DSH 技能 `godot-docs` 的 `SKILL.md`，每会话注入）。
> 本文件放**只在用到时才需要**的东西：完整踩坑场景、godot-mcp 接线沿革、导出模板安装、语料维护命令。
> 写代码时不必先读它；命中了 SKILL.md 里某条"结论"再回来查细节。
>
> 两个文件同源、同镜像：改完都要跑 `tools\sync-ai-playbook.ps1`。

## 本机踩坑（完整版）

### 1. `godot --check-only --script` 不注册 autoload

任何引用单例的脚本都会报
`SCRIPT ERROR: Compile Error: Identifier not found: PlayerManager / JudgeSystem`。
这是**假阳性，不是代码错误**：未改动的 `main.gd`、`title_screen.gd`、`EndGameScreen.gd` 同样报。
判定方法：**拿一个没动过、且同样引用单例的脚本做对照组** —— 全报就是模式问题，只有你改的那个报才是真问题。

### 2. 整数除法会警告

GDScript 4 对 `/` 两侧都是 `int` 的情况报
`WARNING: Integer division. Decimal part will be discarded`。
`int(a / b)` 里的 `int()` 是**多余**的且消不掉警告；改用 `floori(a / b.0)`（负数时二者语义不同，注意）。
该警告**只在运行时 `GDScript::reload` 出现，headless 启动看不到** —— 想抓它得真跑项目。

### 3. Godot 跑不起来 ≠ 项目有问题

若沙箱拦截 `user://`（`%APPDATA%\Godot\app_userdata\<项目名>`）写入，Godot 会在**项目加载之前**就
signal 11 段错误，且 `--check-only` 单脚本同样崩、`--verbose` 也无任何资源加载输出。
先怀疑文件权限，别怀疑代码。

### 4. `unique_id=` 是 4.6 新语法

（`engine_details\file_formats\tscn.rst:104`），不是 3.x 残留；`load_steps` 在 4.6 已废弃、可忽略
（同文件 `:51-53`）。别把它们当错误去"修"。

### 5. godot-mcp 接线：会"自己消失"，状态必须现查

14 个 `mcp__godot__*` 工具：`launch_editor` / `run_project` / `get_debug_output` / `stop_project` /
`get_godot_version` / `list_projects` / `get_project_info` / `create_scene` / `add_node` /
`load_sprite` / `export_mesh_library` / `save_scene` / `get_uid` / `update_project_uids`。
实测 `get_godot_version` → `4.6.1.stable.mono.official.14d19694e`，
`get_project_info D:\个人项目\daishu` → 认出项目结构（6 场景 / 15 脚本 / 11 素材）。

**沿革（两次消失，都发生在"改 profile"前后）**：这条接线原先**只在 `web` profile** 里，10 月改用
`desktop` 后 14 个工具就消失了（会话统计佐证：带 godot 工具的请求全部来自 web 时期）；2026-10-10 把同一条
`insert` 抄进 desktop 的 patch 后恢复；**2026-10-11 19:33 桌面 patch 又被应用重写成 1144 B 的权威副本、
手写 insert 再次消失**（同目录 `cordis.patch.yml.bak-1791718157270` 里还留着 7411 B 的旧版），同日按迁移后的
新路径抄回。**热重组即时生效、不用重启，但工具清单在新会话才刷新**（实测 2026-10-11：抄回后同会话内工具就出现了）。

三个坑：

- `GODOT_PATH` **必须指向 `*_console.exe`**：不带 console 的 exe 在 stdout 被重定向时输出 0 字节，而
  `run_project` / `get_debug_output` 靠捕获 stdout 工作 —— 指错**不报错，只是静默拿不到调试输出**。
  更隐蔽的是：路径失效时服务端**静默回落到内置默认**（`C:\Program Files\Godot\Godot.exe`），
  症状是"MCP 起得来、一调用就 `spawn … ENOENT`"，**不会报"你的配置指错了"**。
- 接线有**两处、互不相干**：项目内 `.claude\mcp.json`（被 gitignore）与 DSH profile 的
  `cordis.patch.yml`（`mcp-godot` 条目，热监听，保存即生效）。
  复现用 `tools\setup-godot-mcp.ps1` —— 它**必须用 SSH 克隆**（本机 HTTPS 到 github.com 不通）。
- **DSH profile 的 patch 文件里有两种东西，可靠性不同**：`insert` / `id` 覆盖这类
  **loader patch 手写可靠**；而同一个文件里的 **settings 命名空间**（如
  `subagent-model-selection-settings`）会被应用以它自己的权威副本覆盖，手写会被剪掉 ——
  那种设置要去 GUI 改。

**Godot 装在哪**：`D:\Program Files\Godot_v4.6.1-stable_mono_win64\`
（沿革：最早在 `C:\Users\28402\Downloads\...` —— Downloads 是临时目录，清理下载就会失效；
2026-10 先迁到 D 盘根，**2026-10-11 又按 `D:\dsh\AGENTS.md`「软件只往两个 Program Files 落」归位到
`D:\Program Files\`**。所以更早文档里那条"D 盘根 + 版本号目录名"的写法**已全部失效**，别再照抄 ——
这也是 2026-10-11 那次 godot-mcp 起得来却报 `ENOENT` 的原因。）
console exe 的完整路径：
`D:\Program Files\Godot_v4.6.1-stable_mono_win64\Godot_v4.6.1-stable_mono_win64_console.exe`。
⚠️ 新路径**含空格**：这些引用点要么用引号整体包起来、要么作为 `spawn` 的参数传入（不经 shell），
所以空格安全 —— 但**别**把它拼进一条未加引号的命令行。
**引用这个路径的地方共 6 处**（2026-10-11 逐处核对），升级 Godot 版本或再搬目录时要一起改：
两个 profile 的 `cordis.patch.yml`（`mcp-godot` 的 `GODOT_PATH`）、
`D:\个人项目\daishu\.claude\mcp.json`、`D:\个人项目\daishu\.claude\settings.local.json`（3 条权限项）、
`D:\个人项目\daishu\.vscode\settings.json` 的 `godotTools.editorPath.godot4`、以及 Godot 自带的
`godot.cmd` / `godot-console.cmd`（这两个已由搬移脚本同步改好）。

### 6. 美术素材必须像素级校验，禁止目测

（`ART_PLAN.md` §四 已把这写成硬规范）—— 用 `tools\art_check.mjs`
（零依赖，只用 node 内置 `zlib`，自带 PNG 解码/编码，**不需要 npm install**）：
`info` / `palette`（对照 ART_PLAN §二 锚点色，色距 >0.30 判偏离）/ `grid`（栏线像素检测）/
`watermark`（白色文字水印判定）/ `crop`（取局部交给人眼或 vision 复核）。
已知事实：`letter.png` 是**双线制** —— 13 道栏界 = 12 栏，栏距 174.09px（CV 1.8%）；`grid` 检测值复现了
`letter.tscn` 里既有 6 个锚点（最大差 0.0009），说明锚点本来就是像素实测来的。
**任何带网格的底图，改锚点必须走 `grid` → 写锚点 → 截图复验三步**；裁边会平移全部栏线，必须重跑。

### 7. 沙箱拦截 `user://` 的 signal 11 有了确切判据

（细化第 3 条）：崩溃前首行必然是
`ERROR: Failed to open 'user://logs/godot<时间戳>.log'`，随后
`CrashHandlerException: Program crashed with signal 11`，且**没有任何资源加载输出**（崩溃早于项目加载）。
放宽文件权限后同一条命令 **exit 0 且零输出** —— "崩溃点早于任何资源加载"就是环境问题的判据。

### 8. `--script` 模式不导入新资源（2026-10-11 实测）

给项目新加一张图片后，跑 `--script`（截图/测试工具）时 `ResourceLoader.exists("res://…png")` 返回
**false**，`load()` 得到 `null`，**代码不报错**，只是那条分支静默走了 fallback —— 表现为"功能没生效但看不出原因"。
第一次实测：`brush_cursor.png` 已放进 `assets/images/ui/`，但 `.godot/imported/` 里没有对应的 `.ctex`，
`ui/` 目录下也没有 `.import`。

**判据**：`.godot/imported/` 里没有该资源的 `.ctex` 就是没导入。修法：

```powershell
godot --headless --path . --import     # 生成 .import + .ctex；实测约数十秒
```

`--script` 模式不会触发资源导入，所以**新增任何资源后、跑依赖它的脚本前，先执行上面这条**。
另：`--import` 会给 `docs\` 下用作配图的 png 也生成 `.import` —— 那些是文档图，不该进仓库，记得剔除。

### 9. `_get_drag_data()` 不能在测试里直接调（2026-10-11 实测）

想为拖拽写单测时直接调 `btn._get_drag_data(Vector2.ZERO)`，会刷出：

```
ERROR: Condition "!get_viewport()->gui_is_dragging()" is true.
   at: _get_drag_data (res://scripts/word_button.gd:NN)
SCRIPT ERROR: Invalid call. Nonexistent function 'gui_get_drag_preview' in base 'Window'.
```

原因：**没有真实拖拽在进行时，`set_drag_preview()` 属于非法调用**（`Control.gui_is_dragging()` 为假）。
另外 `gui_get_drag_preview` **在 4.6 的 Viewport/Window 上并不存在**（只有 `gui_get_drag_data()` /
`gui_is_dragging()`，见 `classes\class_viewport.rst:2430`、`:2492`），所以"读回预览节点"这条路走不通。

**判据**：把预览构造抽成独立函数（本项目 `word_button.gd` 的 `build_drag_preview()`），
`_get_drag_data()` 只负责组装数据 + 调它；测试改调 `build_drag_preview()`，
即可在**不触发拖拽引擎**的前提下断言"预览里有毛笔贴图 + 词文本"。

## 维护与导出

### 升级引擎（例如 4.7）—— 语料要跟着切分支

```
git -C D:\godot-docs fetch --depth 1 origin 4.7
git -C D:\godot-docs checkout 4.7
```

### 需要恢复图片时（D 盘空间紧张，谨慎）

```
git -C D:\godot-docs sparse-checkout set --no-cone "*.rst" "*.png" "*.svg"
```

### 装导出模板（没有它就无法产出 exe）

`%APPDATA%\Godot\export_templates\` 默认为**空**，`export_presets.cfg` 形同虚设。
官方下载端点**可达**：

```powershell
# 版本号与 slug 要跟引擎对齐：mono 引擎要 mono_export_templates.tpz
$u = 'https://downloads.godotengine.org/?version=4.6.1&flavor=stable&slug=mono_export_templates.tpz&platform=templates'
Invoke-WebRequest -Uri $u -OutFile "$env:TEMP\templates.tpz"     # ≈1.09 GiB
```

装法：把 .tpz 解压出的 `templates/` 目录整个放到
`%APPDATA%\Godot\export_templates\4.6.1.stable.mono\`。

⚠️ 先确认 `slug` 与引擎口味一致 —— **用错口味不会报错，只会导出失败**。

### 网络可达性（导出模板正是从这些端点下）

`godotengine.org`（主站，HTTP 200）、`downloads.godotengine.org`（会 302 到
`release-assets.githubusercontent.com`）—— 2026-09 实测。

> 注意区分：`web_fetch`（宿主工具，不受 `rules.yaml` 代理约束）与 shell 里的 `Invoke-WebRequest`
> （走白名单代理，未列出即 403）是两条路。抓网页优先用 `web_fetch`。
