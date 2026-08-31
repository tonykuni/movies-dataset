# =============================================================================
# def VIA · Next Commands after v0113D
# =============================================================================

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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\report\VIA_v0113D_ManualSecretResolution_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\output\VIA_v0113D_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution\VIA_v0113D_USER_EDIT_SecretResolution_RESOLVED.csv" | Format-Table -AutoSize

# P0/P1 still manual:
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution\VIA_v0113D_USER_EDIT_P0_RefinedManualGate.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution\VIA_v0113D_USER_EDIT_P1_RefinedManualGate.csv"

# After manual P0/P1 edit:
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\output\Invoke-VIA-v0114-Precheck-After-v0113D.ps1"

# v0114 may only generate sandbox patch candidate, not overwrite canonical source.

