Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\report\VIA_v0113H_GroupDecisionAutoDraft_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\_user_edit_final_group_decision"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\output\VIA_v0113H_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\output\VIA_v0113H_P0_GroupDecision_AUTODRAFT.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\output\VIA_v0113H_P1_AliasDecision_AUTODRAFT.csv" | Format-Table -AutoSize

# Manual step:
# Copy chosen recommendations into:
#   def_group_user_accept
#   def_selected_group_canonical_value
#   def_alias_user_accept
#   def_selected_alias_value
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\_user_edit_final_group_decision\VIA_v0113H_USER_EDIT_P0_GroupDecision_AUTODRAFT.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\_user_edit_final_group_decision\VIA_v0113H_USER_EDIT_P1_AliasDecision_AUTODRAFT.csv"

# After manual edit:
pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\output\Invoke-VIA-v0113I-Precheck-After-v0113H.ps1"

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
