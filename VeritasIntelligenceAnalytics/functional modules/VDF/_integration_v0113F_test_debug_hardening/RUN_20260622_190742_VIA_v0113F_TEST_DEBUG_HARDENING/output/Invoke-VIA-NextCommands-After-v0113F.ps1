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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\report\VIA_v0113F_TestDebugHardening_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\_user_edit_after_secret_gate_cleared"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\_unified_html_ui_secret_parameter_contract"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\_unified_html_ui_secret_parameter_contract\VIA_UnifiedHtmlUI_FRED_RuntimeSecretParameter_v0113F.html"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\output\VIA_v0113F_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\output\VIA_v0113F_TestDebugMatrix.csv" | Format-Table -AutoSize

# P0/P1 still manual:
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\_user_edit_after_secret_gate_cleared\VIA_v0113F_USER_EDIT_P0_RefinedManualGate.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\_user_edit_after_secret_gate_cleared\VIA_v0113F_USER_EDIT_P1_RefinedManualGate.csv"

# After manual P0/P1 edit:
pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\output\Invoke-VIA-v0114-Precheck-After-v0113F.ps1"

