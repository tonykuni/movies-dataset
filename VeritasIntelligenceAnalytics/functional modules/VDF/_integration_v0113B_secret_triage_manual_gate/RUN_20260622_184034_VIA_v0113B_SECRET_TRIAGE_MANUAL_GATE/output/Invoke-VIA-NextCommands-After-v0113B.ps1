# =============================================================================
# def VIA · Next Commands after v0113B
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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\report\VIA_v0113B_SecretTriage_ManualGate_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\_user_edit_refined"

# Review secret split
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\output\VIA_v0113B_SecretTriage.csv" | Format-Table -AutoSize

# Review readiness
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\output\VIA_v0113B_ReadinessGate.csv" | Format-Table -AutoSize

# Open refined edit boards
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\_user_edit_refined\VIA_v0113B_USER_EDIT_P0_RefinedManualGate.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\_user_edit_refined\VIA_v0113B_USER_EDIT_P1_RefinedManualGate.csv"

# After manual review/edit:
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\output\Invoke-VIA-v0114-Precheck-After-v0113B.ps1"

# Only after precheck returns OK:
# v0114 may generate sandbox patch candidate.
# Still no canonical overwrite.

