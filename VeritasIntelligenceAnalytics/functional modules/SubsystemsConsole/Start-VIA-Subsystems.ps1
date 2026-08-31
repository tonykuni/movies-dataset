#requires -Version 7.0
<#
.SYNOPSIS
    VIA 子系統主控台 · 一鍵自動啟動(USER-TEST → 主控台重建 → 開啟 HTML)

.DESCRIPTION
    [1] USER-TEST   VAP/VDF/VRN 五情境使用者測試(離線、暫存目錄隔離)
    [2] CONSOLE     重建自包含 HTML 主控台(嵌入最新測試結果與 HardGate 封印)
    [3] OPEN        自動開啟主控台(所有功能的啟動命令都列在「一鍵啟動」區)

    非阻塞需求時:pwsh -File .\Start-VIA-Subsystems.ps1 -Background 1
    (Start-Process 背景派工;含空白路徑一律顯式引號)
#>
[CmdletBinding()]
param(
    [string]$PythonExe = "python",
    [int]$Background = 0,
    [int]$OpenHtml = 1
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Here = $PSScriptRoot
$ViaRoot = Split-Path (Split-Path $Here -Parent) -Parent
$Console = Join-Path (Join-Path $ViaRoot "VeritasIntelligenceAnalytics") "VIA_Reports\VIA_Subsystems_Console_v0100.html"
if (-not (Test-Path -LiteralPath $Console)) {
    $Console = Join-Path (Split-Path $Here -Parent | Split-Path -Parent) "VIA_Reports\VIA_Subsystems_Console_v0100.html"
}

# via_ 環境自動解析(沿用 NexusCore 候選契約)
if ($PythonExe -eq "python") {
    foreach ($cand in @(
            (Join-Path $env:USERPROFILE "envs\via_core_313\Scripts\python.exe"),
            (Join-Path $env:USERPROFILE "envs\via_core_312\Scripts\python.exe"))) {
        if (Test-Path -LiteralPath $cand) { $PythonExe = $cand; break }
    }
}

if ($Background -eq 1) {
    $self = Join-Path $Here "Start-VIA-Subsystems.ps1"
    $argString = ('-NoProfile -ExecutionPolicy Bypass -File "{0}" -PythonExe "{1}" -OpenHtml {2}' -f
                  $self, $PythonExe, $OpenHtml)
    $p = Start-Process -FilePath "pwsh" -ArgumentList $argString -WindowStyle Hidden -PassThru
    Write-Host "def [LAUNCH] 背景派工 PID=$($p.Id)(不卡斷)" -ForegroundColor Green
    exit 0
}

Write-Host "def [1/3] USER-TEST(VAP/VDF/VRN 五情境)" -ForegroundColor Cyan
& $PythonExe (Join-Path $Here "VIA_Subsystems_UserTest_v0100.py")
if ($LASTEXITCODE -ne 0) { throw "USER-TEST blocked (exit $LASTEXITCODE)" }

Write-Host "def [2/3] CONSOLE 重建" -ForegroundColor Cyan
& $PythonExe (Join-Path $Here "VIA_Subsystems_Console_Builder_v0100.py")
if ($LASTEXITCODE -ne 0) { throw "Console build failed (exit $LASTEXITCODE)" }

Write-Host "def [3/3] OPEN" -ForegroundColor Cyan
if ($OpenHtml -eq 1 -and (Test-Path -LiteralPath $Console)) { Start-Process -FilePath $Console }
Write-Host "def DONE — SUBSYSTEMS CONSOLE GREEN" -ForegroundColor Green
