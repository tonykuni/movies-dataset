# =============================================================================
# def VIA · Next Commands after v0112
# =============================================================================

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
