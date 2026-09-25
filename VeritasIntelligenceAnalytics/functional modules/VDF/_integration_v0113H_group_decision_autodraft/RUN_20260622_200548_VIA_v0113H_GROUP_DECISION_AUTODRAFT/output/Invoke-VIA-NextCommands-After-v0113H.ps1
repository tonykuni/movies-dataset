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

