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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114B_candidate_validation_seal\RUN_20260622_211231_VIA_v0114B_CANDIDATE_VALIDATION_SEAL\report\VIA_v0114B_CandidateValidationSeal_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114B_candidate_validation_seal\RUN_20260622_211231_VIA_v0114B_CANDIDATE_VALIDATION_SEAL\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114B_candidate_validation_seal\RUN_20260622_211231_VIA_v0114B_CANDIDATE_VALIDATION_SEAL\_validation_seal" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114B_candidate_validation_seal\RUN_20260622_211231_VIA_v0114B_CANDIDATE_VALIDATION_SEAL\output\VIA_v0114B_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114B_candidate_validation_seal\RUN_20260622_211231_VIA_v0114B_CANDIDATE_VALIDATION_SEAL\output\VIA_v0114B_ValidationMatrix.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114B_candidate_validation_seal\RUN_20260622_211231_VIA_v0114B_CANDIDATE_VALIDATION_SEAL\output\Invoke-VIA-v0114C-Precheck-After-v0114B.ps1" # Next: v0114C sandbox dry-run simulation only. # No source mutation. No canonical merge. No DB write.

