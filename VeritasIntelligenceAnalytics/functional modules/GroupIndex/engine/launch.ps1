#requires -Version 7.0
<#
.SYNOPSIS
    VIA GroupIndex · 非阻塞啟動器(KEY PROMPT 契約:不關閉、不阻塞、不卡斷)

.DESCRIPTION
    以 Start-Process 背景派工 OneClick 全套件,立即返回提示字元:
      - 全輸出即時落地 log 檔(-RedirectStandardOutput/-RedirectStandardError)
      - 回報 PID 與 log 路徑;隨時 Get-Content -Wait 追蹤、Stop-Process 中止
      - 子行程以 -KeepOpen 0 執行,結束不等待人工 Enter(不卡斷)

.EXAMPLE
    pwsh -ExecutionPolicy Bypass -File .\launch.ps1              # 背景跑全套件
    pwsh -ExecutionPolicy Bypass -File .\launch.ps1 -Follow 1    # 派工後跟看即時 log
#>
[CmdletBinding()]
param(
    [int]$Follow = 0,          # 1=派工後即時追蹤 log(Ctrl+C 只離開追蹤,不中止套件)
    [int]$EnforceEnv = 1,
    [int]$SyncRepo = 1,
    [int]$SkipEngines = 0,
    [int]$OpenHtml = 1
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$EngineDir = $PSScriptRoot
$OneClick = Join-Path $EngineDir "Invoke-VIA-GroupIndex-Suite-OneClick-v0100.ps1"
if (-not (Test-Path -LiteralPath $OneClick)) { throw "OneClick not found: $OneClick" }

$LogDir = Join-Path (Split-Path $EngineDir -Parent) "evidence\RUN_LAUNCH_LOGS"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutLog = Join-Path $LogDir "oneclick_$stamp.out.log"
$ErrLog = Join-Path $LogDir "oneclick_$stamp.err.log"

$argList = @(
    "-ExecutionPolicy", "Bypass", "-File", $OneClick,
    "-EnforceEnv", $EnforceEnv, "-SyncRepo", $SyncRepo,
    "-SkipEngines", $SkipEngines, "-OpenHtml", $OpenHtml,
    "-KeepOpen", 0            # 背景模式:結束不等待 Enter(不卡斷)
)
$proc = Start-Process -FilePath "pwsh" -ArgumentList $argList `
    -RedirectStandardOutput $OutLog -RedirectStandardError $ErrLog `
    -WindowStyle Hidden -PassThru

Write-Host "def [LAUNCH] 已背景派工(非阻塞)" -ForegroundColor Green
Write-Host "def   PID  : $($proc.Id)"
Write-Host "def   LOG  : $OutLog"
Write-Host "def   追蹤 : Get-Content -LiteralPath `"$OutLog`" -Wait -Tail 30"
Write-Host "def   中止 : Stop-Process -Id $($proc.Id)"

if ($Follow -eq 1) {
    Write-Host "def [FOLLOW] 即時追蹤中(Ctrl+C 只離開追蹤,套件續跑)" -ForegroundColor Yellow
    Get-Content -LiteralPath $OutLog -Wait -Tail 30
}
