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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114L_final_pre_apply_dryrun_only\RUN_20260622_233757_VIA_v0114L_FINAL_PRE_APPLY_DRYRUN_ONLY\report\VIA_v0114L_FinalPreApplyDryrunOnly_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114L_final_pre_apply_dryrun_only\RUN_20260622_233757_VIA_v0114L_FINAL_PRE_APPLY_DRYRUN_ONLY\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114L_final_pre_apply_dryrun_only\RUN_20260622_233757_VIA_v0114L_FINAL_PRE_APPLY_DRYRUN_ONLY\_final_pre_apply_dryrun_only" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114L_final_pre_apply_dryrun_only\RUN_20260622_233757_VIA_v0114L_FINAL_PRE_APPLY_DRYRUN_ONLY\output\VIA_v0114L_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114L_final_pre_apply_dryrun_only\RUN_20260622_233757_VIA_v0114L_FINAL_PRE_APPLY_DRYRUN_ONLY\output\VIA_v0114L_ValidationMatrix.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114L_final_pre_apply_dryrun_only\RUN_20260622_233757_VIA_v0114L_FINAL_PRE_APPLY_DRYRUN_ONLY\_final_pre_apply_dryrun_only\VIA_v0114L_FinalPreApplyDryrunRows.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114L_final_pre_apply_dryrun_only\RUN_20260622_233757_VIA_v0114L_FINAL_PRE_APPLY_DRYRUN_ONLY\output\Invoke-VIA-v0114M-Precheck-After-v0114L.ps1" # Next: v0114M final apply authorization gate only. # v0114L did not execute apply.

