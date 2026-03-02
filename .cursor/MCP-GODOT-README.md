# Godot MCP 配置说明

项目已配置 **Godot MCP**（[Coding-Solo/godot-mcp](https://github.com/Coding-Solo/godot-mcp)），用于在 Cursor 中与 Godot 引擎交互（编辑项目、调试、场景管理等）。

## 前置要求

- **Node.js** 和 npm
- 已安装 **Godot 引擎**

## 安装步骤

1. **安装 Node.js**（若未安装）  
   例如从 [nodejs.org](https://nodejs.org/) 安装，或使用 nvm。

2. **克隆并构建 godot-mcp**（在项目根目录执行）：
   ```bash
   git clone https://github.com/Coding-Solo/godot-mcp.git
   cd godot-mcp
   npm install
   npm run build
   ```

3. **（可选）指定 Godot 路径**  
   若 Godot 不在系统 PATH 中，在 `.cursor/mcp.json` 的 `godot.env` 中添加：
   ```json
   "GODOT_PATH": "/你的/godot/可执行文件路径"
   ```

4. **重启 Cursor**  
   配置修改后重启 Cursor，或在设置中刷新 MCP 列表。

## 配置位置

- 项目级配置：`.cursor/mcp.json`  
- 当前使用的 godot-mcp 入口：`godot-mcp/build/index.js`（需先完成上述克隆与构建）。

## 使用说明

- MCP 工具需在 **Agent 对话**（Cursor Pro/Business）中使用。
- 可在 **设置 → MCP** 中查看并启用 “godot” 服务器。
- 若工具列表为空，点击 MCP 卡片右上角刷新。

## 关于 “godot-docs” 报错

若在 Cursor 的 MCP 设置中看到 **godot-docs** 报错，那是另一个文档类 MCP，与上述 godot-mcp 无关。可先在设置中关闭或移除 godot-docs，仅使用本项目的 godot MCP 配置。
