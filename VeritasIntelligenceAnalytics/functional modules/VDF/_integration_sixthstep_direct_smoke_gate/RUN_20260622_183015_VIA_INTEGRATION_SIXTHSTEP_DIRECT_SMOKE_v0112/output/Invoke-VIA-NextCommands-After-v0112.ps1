# =============================================================================
# def VIA · Next Commands after v0112
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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_sixthstep_direct_smoke_gate\RUN_20260622_183015_VIA_INTEGRATION_SIXTHSTEP_DIRECT_SMOKE_v0112\report\VIA_SixthStep_DirectContractSmokeGate_Report_v0112.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_sixthstep_direct_smoke_gate\RUN_20260622_183015_VIA_INTEGRATION_SIXTHSTEP_DIRECT_SMOKE_v0112\output"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_sixthstep_direct_smoke_gate\RUN_20260622_183015_VIA_INTEGRATION_SIXTHSTEP_DIRECT_SMOKE_v0112\output\VIA_v0112_DirectContractSmoke.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_sixthstep_direct_smoke_gate\RUN_20260622_183015_VIA_INTEGRATION_SIXTHSTEP_DIRECT_SMOKE_v0112\output\VIA_v0112_SmokeFailureTails.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_sixthstep_direct_smoke_gate\RUN_20260622_183015_VIA_INTEGRATION_SIXTHSTEP_DIRECT_SMOKE_v0112\output\VIA_v0112_GateRecommendation.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_sixthstep_direct_smoke_gate\RUN_20260622_183015_VIA_INTEGRATION_SIXTHSTEP_DIRECT_SMOKE_v0112\output\VIA_v0112_P0_AcceptGate_Template.csv" | Select-Object -First 60 | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_sixthstep_direct_smoke_gate\RUN_20260622_183015_VIA_INTEGRATION_SIXTHSTEP_DIRECT_SMOKE_v0112\output\VIA_v0112_P1_PathAlias_AcceptGate_Template.csv" | Format-Table -AutoSize

# Next safe phase:
# v0113 may generate canonical patch candidate only after P0/P1 accept gate is manually reviewed.
# Still no overwrite: sandbox candidate first.

