# =============================================================================
# def VIA · Next Commands after v0113
# =============================================================================

Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\report\VIA_SeventhStep_AcceptGateBoard_Report_v0113.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\_accept_gate_user_edit"

# Review direct smoke board
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\output\VIA_v0113_DirectSmokeBoard.csv" | Format-Table -AutoSize

# Review readiness
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\output\VIA_v0113_ReadinessGate.csv" | Format-Table -AutoSize

# Edit these manually:
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\_accept_gate_user_edit\VIA_v0113_USER_EDIT_P0_AcceptGate.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\_accept_gate_user_edit\VIA_v0113_USER_EDIT_P1_PathAlias_AcceptGate.csv"

# After manual edit, run precheck:
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\output\Invoke-VIA-v0114-PrecheckBlocker.ps1"

# Only after blocker returns OK:
# v0114 can generate sandbox patch candidate.
# Still no canonical overwrite.

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
