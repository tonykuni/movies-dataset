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

