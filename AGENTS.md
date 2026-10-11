# D:\个人项目\daishu —— 代书（Godot 4.x）工作区约定

> 本层只放**这个项目专属**的约定。跨工作区的东西在 `~\.dsh\AGENTS.md`；
> 下面第一条是 2026-10-12 从那里**下移**过来的 —— 它只对 Godot 项目成立，不该占每个会话的常驻预算。

- **写或审 GDScript 前先走 `godot-docs` 技能**：本地 Godot 4.6 语料（类参考 + 教程）是**第一依据**，
  不要凭记忆写 API；断言 API 必须给出处（`classes\class_xxx.rst` + 行号），查不到就直说"文档里没有"。
- **项目自己的约定与文档地图**见 `CLAUDE.md`（含美术硬规矩、目录结构、AI playbook 的位置）；
  技能判据的**源**是 `docs\AI_PLAYBOOK.md`，改完必须跑 `tools\sync-ai-playbook.ps1` 同步镜像
  （DSH 读的是 `~\.dsh\skills\godot-docs\`，`-Check` 只查漂移）。
