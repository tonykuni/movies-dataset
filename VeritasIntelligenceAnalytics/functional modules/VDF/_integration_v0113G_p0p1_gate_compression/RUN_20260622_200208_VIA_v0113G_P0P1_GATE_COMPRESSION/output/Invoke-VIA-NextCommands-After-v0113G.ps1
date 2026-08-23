Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\report\VIA_v0113G_P0P1GateCompression_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output\VIA_v0113G_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output\VIA_v0113G_P0_GroupDecisionBoard.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output\VIA_v0113G_P1_AliasDecisionBoard.csv" | Format-Table -AutoSize

# Manual edit required:
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_USER_EDIT_P0_GroupDecisionBoard.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_USER_EDIT_P1_AliasDecisionBoard.csv"

# After manual group edit:
pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output\Invoke-VIA-v0113H-Precheck-After-v0113G.ps1"

# Next phase:
# v0113H expands accepted groups to row-level preview only.
# No source mutation. No canonical merge.

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
