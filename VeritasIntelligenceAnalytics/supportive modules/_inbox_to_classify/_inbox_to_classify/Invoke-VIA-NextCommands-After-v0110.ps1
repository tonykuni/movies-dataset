# =============================================================================
# def VIA · Next Commands after v0110
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
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\report\VIA_FourthStep_SandboxAdapterCandidate_Report_v0110.html"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\output"
Start-Process "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates"

Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\output\VIA_v0110_SandboxAdapter_Candidates.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\output\VIA_v0110_SandboxSmoke_Results.csv" | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\output\VIA_v0110_P0_ReviewBoard.csv" | Select-Object -First 60 | Format-Table -AutoSize
Import-Csv "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\output\VIA_v0110_PathAliasRegistry.csv" | Format-Table -AutoSize

# Run sandbox smoke again manually:
pwsh -NoProfile -ExecutionPolicy Bypass -File "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\output\Invoke-VIA-RunAllSandboxAdapterSmoke-v0110.ps1"

# Next safe phase:
# v0111 = P0/P1 Accept Gate.
# Only after P0/P1 approved, generate canonical integration patch candidates.

