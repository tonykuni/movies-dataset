#requires -Version 7.0
# VIA-SYS-MGR-003 · Downward Controller v0110
# Dual-gate: -Commit AND -Token (plan digest). No delete. No Stop-Process. No exit.
param(
    [switch]$Commit,
    [string]$Token = "",
    [switch]$MintToken,
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$Roots = @(
    "C:\Users\tonyk\movies-dataset\VeritasIntelligenceAnalytics",
    "C:\Users\tonyk\OneDrive\Documents\movies-dataset\VeritasIntelligenceAnalytics"
)
$Tools = @(
    "C:\Users\tonyk\OneDrive\Documents\新增資料夾",
    "C:\Users\tonyk\Downloads"
)

$Root = $Roots | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $Root) {
    Write-Host "ROOT_MISSING · 灰待辦 · 核對 OneDrive 路徑" -ForegroundColor Yellow
    return
}
$ToolDir = $Tools | Where-Object { Test-Path -LiteralPath (Join-Path $_ "VIA_DownwardController.py") } | Select-Object -First 1
if (-not $ToolDir) {
    Write-Host "CONTROLLER_MISSING · 將 VIA_DownwardController.py 放到 新增資料夾" -ForegroundColor Yellow
    return
}

$Py = Join-Path $ToolDir "VIA_DownwardController.py"
$Work = Join-Path $Root "_governance"
$Argv = @($Py, "--root", $Root, "--tools", $ToolDir, "--work", $Work, "--no-open")
if ($Force) { $Argv += "--force" }
if ($MintToken) { $Argv += "--mint-token" }
if ($Commit) { $Argv += "--commit" }
if ($Token) { $Argv += @("--token", $Token) }

Write-Host "ENTER  $Root" -ForegroundColor Green
Write-Host "TOOLS  $ToolDir"
if (-not $Commit) { Write-Host "GATE   APPLY SKIPPED · 加 -Commit -Token 才下行變更類" -ForegroundColor Yellow }

$exe = Get-Command python -ErrorAction SilentlyContinue
if (-not $exe) { $exe = Get-Command py -ErrorAction SilentlyContinue }
if (-not $exe) {
    Write-Host "PYTHON_ABSENT · 本機無 python · 總管 DryRun 仍可用" -ForegroundColor Yellow
    return
}
& $exe.Source @Argv
