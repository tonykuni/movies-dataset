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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114I_final_apply_plan_draft_only\RUN_20260622_220949_VIA_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY\report\VIA_v0114I_FinalApplyPlanDraftOnly_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114I_final_apply_plan_draft_only\RUN_20260622_220949_VIA_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114I_final_apply_plan_draft_only\RUN_20260622_220949_VIA_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY\_final_apply_plan_draft_only" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114I_final_apply_plan_draft_only\RUN_20260622_220949_VIA_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY\output\VIA_v0114I_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114I_final_apply_plan_draft_only\RUN_20260622_220949_VIA_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY\output\VIA_v0114I_ValidationMatrix.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114I_final_apply_plan_draft_only\RUN_20260622_220949_VIA_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY\_final_apply_plan_draft_only\VIA_v0114I_FinalApplyPlanDraft.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114I_final_apply_plan_draft_only\RUN_20260622_220949_VIA_v0114I_FINAL_APPLY_PLAN_DRAFT_ONLY\output\Invoke-VIA-v0114J-Precheck-After-v0114I.ps1" # Next: v0114J explicit final user approval gate only. # v0114I did not apply anything.

