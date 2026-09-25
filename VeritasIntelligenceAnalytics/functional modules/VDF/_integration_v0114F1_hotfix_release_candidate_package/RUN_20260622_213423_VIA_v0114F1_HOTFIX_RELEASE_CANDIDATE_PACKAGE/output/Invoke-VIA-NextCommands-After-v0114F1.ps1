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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114F1_hotfix_release_candidate_package\RUN_20260622_213423_VIA_v0114F1_HOTFIX_RELEASE_CANDIDATE_PACKAGE\report\VIA_v0114F1_HotfixReleaseCandidatePackage_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114F1_hotfix_release_candidate_package\RUN_20260622_213423_VIA_v0114F1_HOTFIX_RELEASE_CANDIDATE_PACKAGE\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114F1_hotfix_release_candidate_package\RUN_20260622_213423_VIA_v0114F1_HOTFIX_RELEASE_CANDIDATE_PACKAGE\_release_candidate_package_only" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114F1_hotfix_release_candidate_package\RUN_20260622_213423_VIA_v0114F1_HOTFIX_RELEASE_CANDIDATE_PACKAGE\output\VIA_v0114F1_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114F1_hotfix_release_candidate_package\RUN_20260622_213423_VIA_v0114F1_HOTFIX_RELEASE_CANDIDATE_PACKAGE\output\VIA_v0114F1_ValidationMatrix.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114F1_hotfix_release_candidate_package\RUN_20260622_213423_VIA_v0114F1_HOTFIX_RELEASE_CANDIDATE_PACKAGE\output\Invoke-VIA-v0114G-Precheck-After-v0114F1.ps1" # Next: v0114G release candidate package validation only. # No apply. No source mutation. No canonical merge. No DB write.

