#requires -Version 7
<#
.SYNOPSIS
    把仓库里的 AI 知识源同步到 DSH 技能目录（godot-docs）。

.DESCRIPTION
    `docs\AI_PLAYBOOK.md` 是**唯一源**（受 git 版本控制）；DSH 实际读取的技能文件在
    用户目录下、**不属于任何 git 仓库** —— 换机器或重装 DSH 就会丢。所以这里做单向镜像：

        docs\AI_PLAYBOOK.md  →  %USERPROFILE%\.dsh\skills\godot-docs\SKILL.md

    写入前会备份旧文件，写入后**回读校验**；校验不过自动回滚，避免把技能文件写坏。
    技能文件必须是无 BOM 的 UTF-8（YAML frontmatter 在首行），脚本按此写出。

.PARAMETER Check
    只比对不写盘；有漂移则 exit 1。适合挂 pre-commit 或 CI。

.PARAMETER SkillDir
    技能目录，默认 `%USERPROFILE%\.dsh\skills\godot-docs`。

.EXAMPLE
    pwsh -File tools\sync-ai-playbook.ps1
    pwsh -File tools\sync-ai-playbook.ps1 -Check
#>
[CmdletBinding()]
param(
    [string]$SkillDir = (Join-Path $env:USERPROFILE '.dsh\skills\godot-docs'),
    [switch]$Check
)

$ErrorActionPreference = 'Stop'

$projectRoot = Split-Path -Parent $PSScriptRoot
$srcPath     = Join-Path $projectRoot 'docs\AI_PLAYBOOK.md'
$dstPath     = Join-Path $SkillDir 'SKILL.md'

if (-not (Test-Path -LiteralPath $srcPath)) { throw "源文件不存在：$srcPath" }

# 技能文件必须是无 BOM 的 UTF-8、LF 行尾（frontmatter 在首行）。
# 两个辅助函数分开：Read-Raw 用于"逐字节"判定，Normalize 只用于判断差异是否仅来自行尾。
function Read-Raw([string]$path) { [System.IO.File]::ReadAllText($path) }
function Normalize([string]$text) { ($text -replace "`r`n", "`n").TrimEnd("`n") + "`n" }

$srcText = Normalize (Read-Raw $srcPath)
$kb      = [math]::Round($srcText.Length / 1024, 1)

if ($Check) {
    if (-not (Test-Path -LiteralPath $dstPath)) {
        Write-Host "[DRIFT] 技能文件不存在：$dstPath" -ForegroundColor Red
        Write-Host "        修复：pwsh -File tools\sync-ai-playbook.ps1" -ForegroundColor Yellow
        exit 1
    }
    $dstRaw = Read-Raw $dstPath
    if ($srcText -ceq $dstRaw -and (Read-Raw $srcPath) -ceq $dstRaw) {
        Write-Host "[OK] 技能文件与仓库源逐字节一致（$kb KB）" -ForegroundColor Green
        exit 0
    }
    if ($srcText -ceq $dstRaw) {
        Write-Host "[DRIFT] 内容一致，但**行尾不同**：源含 CRLF，技能文件是 LF。" -ForegroundColor Red
        Write-Host "        项目约定为 LF（.gitattributes: * text=auto eol=lf），请先把源改成 LF。" -ForegroundColor Yellow
        exit 1
    }
    Write-Host "[DRIFT] 技能文件与仓库源内容不一致：$dstPath" -ForegroundColor Red
    Write-Host "        修复：pwsh -File tools\sync-ai-playbook.ps1" -ForegroundColor Yellow
    exit 1
}

if ($srcText -ceq (Read-Raw $dstPath)) {
    Write-Host "[SKIP] 已一致，无需写入（$kb KB）" -ForegroundColor Green
    exit 0
}

New-Item -ItemType Directory -Force -Path $SkillDir | Out-Null
$backup = "$dstPath.bak"
if (Test-Path -LiteralPath $dstPath) { Copy-Item -LiteralPath $dstPath -Destination $backup -Force }

# 无 BOM 写出：frontmatter 必须在首行，BOM 会让技能解析失败
[System.IO.File]::WriteAllText($dstPath, $srcText, [System.Text.UTF8Encoding]::new($false))

# 回读校验（逐字节），不过就回滚
if ((Read-Raw $dstPath) -cne $srcText) {
    if (Test-Path -LiteralPath $backup) { Copy-Item -LiteralPath $backup -Destination $dstPath -Force }
    throw "写入后回读校验失败，已回滚。$dstPath"
}

Write-Host "[OK] 已同步 → $dstPath（$kb KB，无 BOM，逐字节校验通过）" -ForegroundColor Green
if (Test-Path -LiteralPath $backup) { Write-Host "     旧文件备份：$backup" -ForegroundColor DarkGray }
