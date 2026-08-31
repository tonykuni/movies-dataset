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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\report\VIA_v0113G_P0P1GateCompression_Report.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output\VIA_v0113G_ReadinessGate.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output\VIA_v0113G_P0_GroupDecisionBoard.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output\VIA_v0113G_P1_AliasDecisionBoard.csv" | Format-Table -AutoSize

# Manual edit required:
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_USER_EDIT_P0_GroupDecisionBoard.csv"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_USER_EDIT_P1_AliasDecisionBoard.csv"

# After manual group edit:
pwsh -NoProfile -NoExit -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\output\Invoke-VIA-v0113H-Precheck-After-v0113G.ps1"

# Next phase:
# v0113H expands accepted groups to row-level preview only.
# No source mutation. No canonical merge.

