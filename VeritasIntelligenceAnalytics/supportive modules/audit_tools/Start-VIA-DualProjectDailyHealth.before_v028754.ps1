#requires -Version 7.0
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference = 'Stop'
$ScriptPath = 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\tools\VIA_DualProjectDailyHealth\Invoke-VIA-DualProjectDailyHealth.ps1'

Write-Host ''
Write-Host '================================================================================' -ForegroundColor Cyan
Write-Host 'VIA DUAL PROJECT DAILY HEALTH · MANUAL LAUNCHER' -ForegroundColor Cyan
Write-Host '================================================================================' -ForegroundColor Cyan

if (Test-Path -LiteralPath $ScriptPath -PathType Leaf) {
    & pwsh -NoProfile -ExecutionPolicy Bypass -File $ScriptPath -OpenHtmlReport
}
else {
    Write-Host ('[BLOCK] Daily health script missing: ' + $ScriptPath) -ForegroundColor Red
}

Write-Host ''
Write-Host 'PowerShell remains open. No exit. No Stop-Process.' -ForegroundColor Green

