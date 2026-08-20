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
