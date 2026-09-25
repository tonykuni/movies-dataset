# Veritas Subsystem Integration Audit v003 · review-only launcher
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
$def_Base = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics"
$def_LocalPy = "py"
$def_Script = Join-Path $def_Base "SUP_MDL548_SubsystemIntegrationAudit_v003.py"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def Veritas · Subsystem Integration Audit v003" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def Policy: append-only · review-only · no DB write · no canonical merge · no delete" -ForegroundColor Yellow
if (!(Test-Path $def_Script)) {
  Write-Host "def Script not found at project root. Put SUP_MDL548_SubsystemIntegrationAudit_v003.py there first." -ForegroundColor Red
  Write-Host "def PowerShell remains open." -ForegroundColor Cyan
  return
}
& $def_LocalPy -3.13 $def_Script
Write-Host ""
Write-Host "def PowerShell remains open." -ForegroundColor Cyan

