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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114E_manual_release_approval\RUN_20260622_212143_VIA_v0114E_MANUAL_RELEASE_APPROVAL\report\VIA_v0114E_ManualReleaseApproval_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114E_manual_release_approval\RUN_20260622_212143_VIA_v0114E_MANUAL_RELEASE_APPROVAL\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114E_manual_release_approval\RUN_20260622_212143_VIA_v0114E_MANUAL_RELEASE_APPROVAL\_manual_release_approval_gate" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114E_manual_release_approval\RUN_20260622_212143_VIA_v0114E_MANUAL_RELEASE_APPROVAL\output\VIA_v0114E_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114E_manual_release_approval\RUN_20260622_212143_VIA_v0114E_MANUAL_RELEASE_APPROVAL\output\VIA_v0114E_ValidationMatrix.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114E_manual_release_approval\RUN_20260622_212143_VIA_v0114E_MANUAL_RELEASE_APPROVAL\output\Invoke-VIA-v0114F-Precheck-After-v0114E.ps1" # Next: v0114F release candidate package only. # No apply. No source mutation. No canonical merge. No DB write.

