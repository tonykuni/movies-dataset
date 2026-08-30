#requires -Version 7.0

param(
    [string]$UnifiedInputSSOT = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\VIA_UnifiedInput_SSOT.json",
    [string]$Action = "status"
)
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

$ErrorActionPreference = "Stop"

try {
    if (-not [System.IO.File]::Exists($UnifiedInputSSOT)) {
        throw "UnifiedInputSSOT missing."
    }

    $cfg = Get-Content -LiteralPath $UnifiedInputSSOT -Raw -Encoding UTF8 | ConvertFrom-Json

    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "def VIA ACTIVATION GATEWAY INLINE READY" -ForegroundColor Cyan
    Write-Host "================================================================================" -ForegroundColor Cyan
    Write-Host "Action : $Action"
    Write-Host "SSOT   : $UnifiedInputSSOT"
    Write-Host "Status : READY"
    Write-Host "PowerShell remains open. No exit was called." -ForegroundColor Green
}
catch {
    Write-Host "[FATAL] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "PowerShell remains open. No exit was called." -ForegroundColor Yellow
}

