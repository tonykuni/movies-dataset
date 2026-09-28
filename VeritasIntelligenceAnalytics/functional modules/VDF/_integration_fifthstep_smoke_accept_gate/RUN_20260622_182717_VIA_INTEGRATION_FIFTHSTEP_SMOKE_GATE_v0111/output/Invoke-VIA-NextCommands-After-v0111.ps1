# =============================================================================
# def VIA · Next Commands after v0111
# =============================================================================

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

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
