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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
