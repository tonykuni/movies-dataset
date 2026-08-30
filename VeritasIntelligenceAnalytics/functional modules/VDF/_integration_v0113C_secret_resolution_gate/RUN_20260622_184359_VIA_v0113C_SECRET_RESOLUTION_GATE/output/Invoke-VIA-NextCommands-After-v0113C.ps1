# =============================================================================
# def VIA · Next Commands after v0113C
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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\report\VIA_v0113C_SecretResolutionGate_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution"

# Review secret resolution board
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution\VIA_v0113C_USER_EDIT_SecretResolution.csv" | Format-Table -AutoSize

# Review readiness
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\output\VIA_v0113C_ReadinessGate.csv" | Format-Table -AutoSize

# Open manual edit boards
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution\VIA_v0113C_USER_EDIT_SecretResolution.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution\VIA_v0113C_USER_EDIT_P0_RefinedManualGate.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\_user_edit_secret_resolution\VIA_v0113C_USER_EDIT_P1_RefinedManualGate.csv"

# After manual review/edit:
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113C_secret_resolution_gate\RUN_20260622_184359_VIA_v0113C_SECRET_RESOLUTION_GATE\output\Invoke-VIA-v0114-Precheck-After-v0113C.ps1"

# Only after precheck returns OK:
# v0114 may generate sandbox patch candidate.
# Still no canonical overwrite.

