Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113J_formal_decision_promotion\RUN_20260622_201203_VIA_v0113J_FORMAL_DECISION_PROMOTION\report\VIA_v0113J_FormalDecisionPromotion_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113J_formal_decision_promotion\RUN_20260622_201203_VIA_v0113J_FORMAL_DECISION_PROMOTION\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113J_formal_decision_promotion\RUN_20260622_201203_VIA_v0113J_FORMAL_DECISION_PROMOTION\_formal_decision_final"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113J_formal_decision_promotion\RUN_20260622_201203_VIA_v0113J_FORMAL_DECISION_PROMOTION\output\VIA_v0113J_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113J_formal_decision_promotion\RUN_20260622_201203_VIA_v0113J_FORMAL_DECISION_PROMOTION\_formal_decision_final\VIA_v0113J_P0_FormalFinalDecision.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113J_formal_decision_promotion\RUN_20260622_201203_VIA_v0113J_FORMAL_DECISION_PROMOTION\_formal_decision_final\VIA_v0113J_P1_FormalFinalDecision.csv" | Format-Table -AutoSize

pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113J_formal_decision_promotion\RUN_20260622_201203_VIA_v0113J_FORMAL_DECISION_PROMOTION\output\Invoke-VIA-v0113K-Precheck-After-v0113J.ps1"

# Next:
# v0113K will generate final row-level preview and v0114 sandbox patch candidate input only.
# No source mutation. No canonical merge.

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
