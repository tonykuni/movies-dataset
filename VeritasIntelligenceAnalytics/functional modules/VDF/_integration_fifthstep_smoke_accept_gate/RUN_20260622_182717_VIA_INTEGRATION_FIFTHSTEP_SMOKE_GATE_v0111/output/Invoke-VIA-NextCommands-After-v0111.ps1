# =============================================================================
# def VIA · Next Commands after v0111
# =============================================================================

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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\report\VIA_FifthStep_SmokeDiagnosticAcceptGate_Report_v0111.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\VIA_v0111_CandidateSmokeDiagnostics.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\VIA_v0111_FixedSmokeResults.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\VIA_v0111_P0_AcceptGate_Template.csv" | Select-Object -First 60 | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\VIA_v0111_P1_PathAlias_AcceptGate_Template.csv" | Format-Table -AutoSize

# Run fixed smoke again manually:
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\output\Invoke-VIA-RunAllFixedSmoke-v0111.ps1"

# Next safe phase:
# v0112 = only generate canonical patch candidates after P0/P1 accept gate is reviewed.

