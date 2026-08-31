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
$ErrorActionPreference = "Continue"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114O Final Apply Script Preview Only" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "[PREVIEW ONLY] This file is intentionally inert." -ForegroundColor Yellow
Write-Host "[BLOCKED] No execution. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow
Write-Host "Preview CSV:" -ForegroundColor Cyan
Write-Host "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114O_final_apply_script_preview_only\RUN_20260623_005334_VIA_v0114O_FINAL_APPLY_SCRIPT_PREVIEW_ONLY\_final_apply_script_preview_only\VIA_v0114O_FinalApplyScriptPreviewRows.csv
" -ForegroundColor Cyan
Write-Host "PowerShell remains open." -ForegroundColor Cyan
return

