<#
.SYNOPSIS
    VAP_Launcher.ps1 - VeritasAutoPlot PowerShell Launcher v4.0
.DESCRIPTION
    One-click automation: health check, demo, render, serve, test
    Safety: No auto-open (LL#12), no blocking input
#>
param(
    [switch]$Health,
    [switch]$Demo,
    [switch]$Serve,
    [int]$Port = 8080,
    [switch]$Test,
    [string]$Indicators,
    [string]$Source = "demo"
)

$VAPRoot = "C:\VeritasIntelligenceAnalytics\VeritasAutoPlot"
$PyExe = "C:\Users\tonyk\envs\via_core\Scripts\python.exe"

if (-not (Test-Path $PyExe)) {
    Write-Host "[FAIL] Python not found: $PyExe" -ForegroundColor Red
    return
}

$mainPy = Join-Path $VAPRoot "main.py"
if (-not (Test-Path $mainPy)) {
    Write-Host "[WARN] main.py not found at $mainPy, trying current directory..." -ForegroundColor Yellow
    $mainPy = Join-Path $PSScriptRoot "main.py"
}

if ($Health) {
    & $PyExe $mainPy --health
} elseif ($Demo) {
    & $PyExe $mainPy --demo
} elseif ($Serve) {
    & $PyExe $mainPy --serve --port $Port
} elseif ($Indicators) {
    & $PyExe $mainPy --indicators $Indicators --source $Source
} elseif ($Test) {
    & $PyExe -m pytest (Join-Path $VAPRoot "tests") -v --tb=short
} else {
    Write-Host "VAP_Launcher.ps1 - VeritasAutoPlot v4.0" -ForegroundColor Cyan
    Write-Host "  -Health       System health check" -ForegroundColor Gray
    Write-Host "  -Demo         Run full demo (all chart types)" -ForegroundColor Gray
    Write-Host "  -Serve        Launch web API server" -ForegroundColor Gray
    Write-Host "  -Test         Run test suite" -ForegroundColor Gray
    Write-Host '  -Indicators "standard" -Source demo' -ForegroundColor Gray
}

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
