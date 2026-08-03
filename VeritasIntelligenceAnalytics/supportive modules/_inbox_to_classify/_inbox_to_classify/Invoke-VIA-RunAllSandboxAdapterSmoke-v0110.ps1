$ErrorActionPreference = "Stop"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · Run All Sandbox Adapter Smoke · v0110" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
$rows = @()

Write-Host '[RUN] VDF' -ForegroundColor Cyan
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VDF\Invoke-VIA_VDF_SandboxSmoke_v0110.ps1'
    $rows += [pscustomobject]@{ Project='VDF'; Status='OK'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VDF\Invoke-VIA_VDF_SandboxSmoke_v0110.ps1' }
} catch {
    $rows += [pscustomobject]@{ Project='VDF'; Status='FAIL'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VDF\Invoke-VIA_VDF_SandboxSmoke_v0110.ps1'; Message=$_.Exception.Message }
}

Write-Host '[RUN] VIA' -ForegroundColor Cyan
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VIA\Invoke-VIA_VIA_SandboxSmoke_v0110.ps1'
    $rows += [pscustomobject]@{ Project='VIA'; Status='OK'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VIA\Invoke-VIA_VIA_SandboxSmoke_v0110.ps1' }
} catch {
    $rows += [pscustomobject]@{ Project='VIA'; Status='FAIL'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VIA\Invoke-VIA_VIA_SandboxSmoke_v0110.ps1'; Message=$_.Exception.Message }
}

Write-Host '[RUN] VRN' -ForegroundColor Cyan
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VRN\Invoke-VIA_VRN_SandboxSmoke_v0110.ps1'
    $rows += [pscustomobject]@{ Project='VRN'; Status='OK'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VRN\Invoke-VIA_VRN_SandboxSmoke_v0110.ps1' }
} catch {
    $rows += [pscustomobject]@{ Project='VRN'; Status='FAIL'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VRN\Invoke-VIA_VRN_SandboxSmoke_v0110.ps1'; Message=$_.Exception.Message }
}

$out = Join-Path (Split-Path -Parent $PSCommandPath) "VIA_RunAllSandboxSmoke_Result_v0110.csv"
$rows | Export-Csv -LiteralPath $out -NoTypeInformation -Encoding UTF8
Write-Host "[OK] Result: $out" -ForegroundColor Green
