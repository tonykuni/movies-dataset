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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114G_package_validation\RUN_20260622_215649_VIA_v0114G_PACKAGE_VALIDATION\report\VIA_v0114G_ReleaseCandidatePackageValidation_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114G_package_validation\RUN_20260622_215649_VIA_v0114G_PACKAGE_VALIDATION\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114G_package_validation\RUN_20260622_215649_VIA_v0114G_PACKAGE_VALIDATION\_package_validation_seal" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114G_package_validation\RUN_20260622_215649_VIA_v0114G_PACKAGE_VALIDATION\output\VIA_v0114G_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114G_package_validation\RUN_20260622_215649_VIA_v0114G_PACKAGE_VALIDATION\output\VIA_v0114G_ValidationMatrix.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114G_package_validation\RUN_20260622_215649_VIA_v0114G_PACKAGE_VALIDATION\output\Invoke-VIA-v0114H-Precheck-After-v0114G.ps1" # Next: v0114H final release review gate only. # No apply. No source mutation. No canonical merge. No DB write.

