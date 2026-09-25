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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114C_sandbox_dryrun_simulation\RUN_20260622_211537_VIA_v0114C_SANDBOX_DRYRUN_SIMULATION\report\VIA_v0114C_SandboxDryRunSimulation_Report.html" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114C_sandbox_dryrun_simulation\RUN_20260622_211537_VIA_v0114C_SANDBOX_DRYRUN_SIMULATION\output" Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114C_sandbox_dryrun_simulation\RUN_20260622_211537_VIA_v0114C_SANDBOX_DRYRUN_SIMULATION\_dryrun_sandbox_only" Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114C_sandbox_dryrun_simulation\RUN_20260622_211537_VIA_v0114C_SANDBOX_DRYRUN_SIMULATION\output\VIA_v0114C_ReadinessGate.csv" | Format-Table -AutoSize Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114C_sandbox_dryrun_simulation\RUN_20260622_211537_VIA_v0114C_SANDBOX_DRYRUN_SIMULATION\output\VIA_v0114C_ValidationMatrix.csv" | Format-Table -AutoSize pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114C_sandbox_dryrun_simulation\RUN_20260622_211537_VIA_v0114C_SANDBOX_DRYRUN_SIMULATION\output\Invoke-VIA-v0114D-Precheck-After-v0114C.ps1" # Next: v0114D sandbox review seal only. # No source mutation. No canonical merge. No DB write.

