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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114H_final_release_review_gate\RUN_20260622_220646_VIA_v0114H_FINAL_RELEASE_REVIEW_GATE\report\VIA_v0114H_FinalReleaseReviewGate_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114H_final_release_review_gate\RUN_20260622_220646_VIA_v0114H_FINAL_RELEASE_REVIEW_GATE\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114H_final_release_review_gate\RUN_20260622_220646_VIA_v0114H_FINAL_RELEASE_REVIEW_GATE\_final_release_review_gate" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114H_final_release_review_gate\RUN_20260622_220646_VIA_v0114H_FINAL_RELEASE_REVIEW_GATE\output\VIA_v0114H_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114H_final_release_review_gate\RUN_20260622_220646_VIA_v0114H_FINAL_RELEASE_REVIEW_GATE\output\VIA_v0114H_ValidationMatrix.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114H_final_release_review_gate\RUN_20260622_220646_VIA_v0114H_FINAL_RELEASE_REVIEW_GATE\output\Invoke-VIA-v0114I-Precheck-After-v0114H.ps1" # Next: v0114I final apply-plan draft only. # No apply. No source mutation. No canonical merge. No DB write.

