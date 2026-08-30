#Requires -Version 7.0
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
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "VAP Next Optimization Actions" -ForegroundColor Cyan
Write-Host "1) Open V6 script and set EnableNetworkFetch = `$true" -ForegroundColor Yellow
Write-Host "2) Re-run V6 to fetch live data" -ForegroundColor Yellow
Write-Host "3) Re-run V7 to calculate quant tables" -ForegroundColor Yellow
Write-Host "4) Re-run maturity optimizer to confirm score improvement" -ForegroundColor Yellow
Write-Host ""
Write-Host "Commands are guidance only. This file intentionally does not auto-edit your scripts." -ForegroundColor DarkGray

