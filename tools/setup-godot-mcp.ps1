#requires -Version 7
<#
.SYNOPSIS
    复现 godot-mcp（Godot 引擎 MCP 服务器）开发环境。

.DESCRIPTION
    godot-mcp 被 .gitignore 忽略，克隆本仓库后它并不存在，MCP 会直接失效。
    本脚本把它一条命令装回来：克隆 → 构建 → 校验 → 生成 .claude/mcp.json。

    两个已踩过的坑，脚本会主动规避：
      1) 必须用 **SSH** 克隆：本机 HTTPS 到 github.com 不通（SSL 被拦），
         SSH 通。写成 https:// 会静默超时。
      2) GODOT_PATH 必须指向 **_console.exe**：Windows 上不带 console 的 exe
         在 stdout 被重定向时输出 0 字节，而 run_project / get_debug_output
         正是靠捕获 stdout 工作的 —— 指错 exe 不报错，只是静默拿不到调试输出。

.PARAMETER GodotConsolePath
    Godot *_console.exe 的完整路径。省略则自动搜索常见位置。

.PARAMETER SkipInstall
    跳过 npm install / build（仅校验与写配置）。

.EXAMPLE
    pwsh -File tools\setup-godot-mcp.ps1
#>
[CmdletBinding()]
param(
    [string]$GodotConsolePath = '',
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$mcpDir      = Join-Path $projectRoot 'godot-mcp'
$repoUrl     = 'git@github.com:Coding-Solo/godot-mcp.git'   # 必须 SSH，见 .DESCRIPTION
$mcpJson     = Join-Path $projectRoot '.claude\mcp.json'

function Say([string]$m, [string]$c = 'Gray') { Write-Host $m -ForegroundColor $c }

Say "`n=== godot-mcp 环境安装 ===" Cyan
Say "项目根目录: $projectRoot"

# --- 1. 前置检查 -----------------------------------------------------------
foreach ($cmd in @('git', 'node', 'npm')) {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "缺少必需命令: $cmd"
    }
}
Say ("node {0} / git {1}" -f (node --version), ((git --version) -split ' ')[2])

# --- 2. 定位 Godot _console.exe -------------------------------------------
if (-not $GodotConsolePath) {
    Say "`n[1/4] 搜索 Godot *_console.exe ..."
    # 先按目录名过滤再深入：直接对整个盘递归会慢到不可用
    $searchRoots = @(
        (Join-Path $env:USERPROFILE 'Downloads'),
        'C:\Program Files', 'C:\Program Files (x86)',
        'D:\', 'D:\Tools', 'C:\Tools'
    ) | Where-Object { Test-Path $_ }

    $godotDirs = foreach ($root in $searchRoots) {
        Get-ChildItem -Path $root -Directory -Depth 2 -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match 'Godot' }
    }
    $found = foreach ($d in $godotDirs) {
        Get-ChildItem -Path $d.FullName -Filter '*_console.exe' -Recurse -Depth 2 -File -ErrorAction SilentlyContinue
    }
    $GodotConsolePath = ($found | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
}
if (-not $GodotConsolePath -or -not (Test-Path -LiteralPath $GodotConsolePath)) {
    throw "找不到 Godot 的 *_console.exe。请用 -GodotConsolePath 显式指定。"
}
Say ("Godot console: {0}" -f $GodotConsolePath) Green

# 与引擎同目录的普通 exe 一并报出，便于人工确认是同一次下载
$plain = Get-ChildItem (Split-Path $GodotConsolePath) -Filter '*.exe' -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -notmatch '_console' }
if ($plain) { Say ("同目录主程序 : {0}" -f ($plain.Name -join ', ')) DarkGray }

# --- 3. 克隆 + 构建 --------------------------------------------------------
Say "`n[2/4] godot-mcp 本体 ..."
if (-not (Test-Path (Join-Path $mcpDir '.git'))) {
    if (Test-Path $mcpDir) { Remove-Item $mcpDir -Recurse -Force }
    Say ("克隆 {0}" -f $repoUrl) Yellow
    git clone --depth 1 $repoUrl $mcpDir
    if ($LASTEXITCODE -ne 0) { throw "git clone 失败。确认 SSH key 可用： ssh -T git@github.com" }
} else {
    $head = git -C $mcpDir log -1 --format='%h %s'
    Say ("已存在（{0}），跳过克隆" -f $head)
}

$built = Join-Path $mcpDir 'build\index.js'
if ($SkipInstall) {
    Say "已指定 -SkipInstall"
} elseif (Test-Path $built) {
    Say ("build 已存在且不旧于 src，跳过构建")
} else {
    Say "`n[3/4] npm install && npm run build ..."
    Push-Location $mcpDir
    try {
        npm install --silent
        if ($LASTEXITCODE -ne 0) { throw "npm install 失败" }
        npm run build --silent
        if ($LASTEXITCODE -ne 0) { throw "npm run build 失败" }
    } finally { Pop-Location }
}

if (-not (Test-Path $built)) { throw "构建产物缺失: $built" }
Say ("build/index.js OK（{0:N0} 字节）" -f (Get-Item $built).Length) Green

# --- 4. 写 .claude/mcp.json ------------------------------------------------
Say "`n[4/4] 生成 .claude/mcp.json ..."
$nodeExe = (Get-Command node).Source
$config = [ordered]@{
    mcpServers = [ordered]@{
        godot = [ordered]@{
            command = $nodeExe
            args    = @(($built -replace '\\', '/'))
            env     = [ordered]@{
                DEBUG      = 'false'
                GODOT_PATH = ($GodotConsolePath -replace '\\', '/')
            }
        }
    }
}
New-Item -ItemType Directory -Force -Path (Split-Path $mcpJson) | Out-Null
$config | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $mcpJson -Encoding utf8
Say ("已写入 {0}" -f $mcpJson) Green

# --- 自检 ------------------------------------------------------------------
Say "`n=== 自检 ===" Cyan
$ok = $true
$j = Get-Content -LiteralPath $mcpJson -Raw | ConvertFrom-Json
$gp = $j.mcpServers.godot.env.GODOT_PATH

if ($gp -match '_console\.exe$') { Say "  [PASS] GODOT_PATH 指向 _console.exe" Green }
else { Say "  [FAIL] GODOT_PATH 不是 _console.exe：$gp" Red; $ok = $false }

if ($j.mcpServers.godot.args[0] -match '/build/index\.js$' -and (Test-Path $built)) {
    Say "  [PASS] server 入口存在" Green
} else { Say "  [FAIL] server 入口无效" Red; $ok = $false }

$ver = & $GodotConsolePath --version 2>&1 | Select-Object -First 1
if ($LASTEXITCODE -eq 0) { Say ("  [PASS] 引擎可执行：{0}" -f $ver) Green }
else { Say "  [FAIL] 引擎无法执行" Red; $ok = $false }

Say ""
if ($ok) {
    Say "完成。若 DSH 侧也要用，请把同样的 GODOT_PATH 填进" -ForegroundColor Green
    Say "  ~/.dsh/profiles/web/cordis.patch.yml  →  mcp-godot.config.env.GODOT_PATH" -ForegroundColor Green
    Say "（该文件由 watchUserPatches 热监听，保存即生效，无需重启 DSH）" -ForegroundColor DarkGray
} else {
    Say "自检未通过，请按上面的 FAIL 项修复。" -ForegroundColor Red
    exit 1
}
