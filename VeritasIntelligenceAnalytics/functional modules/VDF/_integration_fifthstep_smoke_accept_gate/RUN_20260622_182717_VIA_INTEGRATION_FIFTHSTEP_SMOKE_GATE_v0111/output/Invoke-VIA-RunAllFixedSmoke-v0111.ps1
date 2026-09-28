# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
# CELERITAS-TEMPLATE-JOIN v1 (no-wrap join, L103-3; batch R16-9; PS 5.1 runs unchanged, only PS7 loads the template)
# ===== [VIA:PS-TEMPLATE:v0101] Celeritas PS7 template: this process only, restore on exit, skip when absent, param() untouched =====
$VIACelTplOwn = $false
if ($PSVersionTable.PSVersion.Major -ge 7) {
    try {
        $VIACelTplFile = $null
        $VIACelTplProbe = $PSScriptRoot
        while ($VIACelTplProbe) {
            $VIACelTplTry = Join-Path $VIACelTplProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
            if (Test-Path -LiteralPath $VIACelTplTry) { $VIACelTplFile = $VIACelTplTry; break }
            $VIACelTplUp = Split-Path $VIACelTplProbe -Parent
            if ((-not $VIACelTplUp) -or ($VIACelTplUp -eq $VIACelTplProbe)) { break }
            $VIACelTplProbe = $VIACelTplUp
        }
        if ($VIACelTplFile -and (-not (Get-Command Restore-CeleritasPS7 -ErrorAction Ignore))) {
            $VIACelTplKeep = @{}
            foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                $VIACelTplVar = Get-Variable -Name $VIACelTplName -Scope 0 -ErrorAction Ignore
                if ($VIACelTplVar) { $VIACelTplKeep[$VIACelTplName] = $VIACelTplVar.Value }
            }
            try { $null = . $VIACelTplFile -RestoreOnly }
            finally {
                Set-StrictMode -Off
                foreach ($VIACelTplName in 'RestoreOnly', 'Report', 'Body') {
                    Remove-Variable -Name $VIACelTplName -Scope 0 -Force -ErrorAction Ignore
                    if ($VIACelTplKeep.ContainsKey($VIACelTplName)) { Set-Variable -Name $VIACelTplName -Value $VIACelTplKeep[$VIACelTplName] -Scope 0 }
                }
            }
            if (Get-Command Start-CeleritasPS7 -ErrorAction Ignore) {
                if (-not (Get-EventSubscriber -Force -ErrorAction Ignore | Where-Object { $_.SourceIdentifier -eq 'PowerShell.Exiting' })) {
                    $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -SupportEvent -Action { try { Restore-CeleritasPS7 } catch { } }
                }
                [void](Start-CeleritasPS7)
                $VIACelTplOwn = $true
            }
        }
    } catch { }
}
# ===== [VIA:PS-TEMPLATE:END] =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference = "Stop"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · Run All Fixed Sandbox Smoke · v0111" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
$rows = @()

Write-Host '[RUN] VDF' -ForegroundColor Cyan
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts\VDF\Invoke-VIA_VDF_FixedSandboxSmoke_v0111.ps1'
    $rows += [pscustomobject]@{ Project='VDF'; Status='OK'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts\VDF\Invoke-VIA_VDF_FixedSandboxSmoke_v0111.ps1' }
} catch {
    $rows += [pscustomobject]@{ Project='VDF'; Status='FAIL'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts\VDF\Invoke-VIA_VDF_FixedSandboxSmoke_v0111.ps1'; Message=$_.Exception.Message }
}

Write-Host '[RUN] VIA' -ForegroundColor Cyan
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts\VIA\Invoke-VIA_VIA_FixedSandboxSmoke_v0111.ps1'
    $rows += [pscustomobject]@{ Project='VIA'; Status='OK'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts\VIA\Invoke-VIA_VIA_FixedSandboxSmoke_v0111.ps1' }
} catch {
    $rows += [pscustomobject]@{ Project='VIA'; Status='FAIL'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts\VIA\Invoke-VIA_VIA_FixedSandboxSmoke_v0111.ps1'; Message=$_.Exception.Message }
}

Write-Host '[RUN] VRN' -ForegroundColor Cyan
try {
    pwsh -NoProfile -ExecutionPolicy Bypass -File 'C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts\VRN\Invoke-VIA_VRN_FixedSandboxSmoke_v0111.ps1'
    $rows += [pscustomobject]@{ Project='VRN'; Status='OK'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts\VRN\Invoke-VIA_VRN_FixedSandboxSmoke_v0111.ps1' }
} catch {
    $rows += [pscustomobject]@{ Project='VRN'; Status='FAIL'; Smoke='C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fifthstep_smoke_accept_gate\RUN_20260622_182717_VIA_INTEGRATION_FIFTHSTEP_SMOKE_GATE_v0111\_fixed_smoke_scripts\VRN\Invoke-VIA_VRN_FixedSandboxSmoke_v0111.ps1'; Message=$_.Exception.Message }
}

$out = Join-Path (Split-Path -Parent $PSCommandPath) "VIA_RunAllFixedSmoke_Result_v0111.csv"
$rows | Export-Csv -LiteralPath $out -NoTypeInformation -Encoding UTF8
Write-Host "[OK] Result: $out" -ForegroundColor Green

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
