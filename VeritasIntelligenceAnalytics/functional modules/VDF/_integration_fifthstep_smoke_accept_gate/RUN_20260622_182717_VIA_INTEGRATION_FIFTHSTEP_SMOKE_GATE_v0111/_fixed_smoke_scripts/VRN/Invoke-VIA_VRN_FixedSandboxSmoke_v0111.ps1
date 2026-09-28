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

$def_PROJECT = '
VRN
'
$def_CONTRACT_JSON = '
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VRN\VIA_VRN_BridgeContract_v0110.json
'
$def_CANDIDATE_DIR = '
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_fourthstep_sandbox_adapter\RUN_20260622_181822_VIA_INTEGRATION_FOURTHSTEP_SANDBOX_ADAPTER_v0110\_sandbox_adapter_candidates\VRN
'

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA Fixed Sandbox Smoke v0111 · $def_PROJECT" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan

$rows = @()

if (-not (Test-Path -LiteralPath $def_CANDIDATE_DIR)) { throw "Candidate directory missing: $def_CANDIDATE_DIR" }
if (-not (Test-Path -LiteralPath $def_CONTRACT_JSON)) { throw "Contract JSON missing: $def_CONTRACT_JSON" }

$obj = Get-Content -LiteralPath $def_CONTRACT_JSON -Raw -Encoding UTF8 | ConvertFrom-Json

$rows += [pscustomobject]@{ Check="CandidateDirExists"; Status="OK"; Detail=$def_CANDIDATE_DIR }
$rows += [pscustomobject]@{ Check="ContractJsonExists"; Status="OK"; Detail=$def_CONTRACT_JSON }
$rows += [pscustomobject]@{ Check="ContractJsonReadable"; Status="OK"; Detail=$obj.schema_version }
$rows += [pscustomobject]@{ Check="Project"; Status="OK"; Detail=$obj.project }

$sourceMutation = [string]$obj.source_mutation
$canonicalMerge = [string]$obj.canonical_merge
$dbWrite = [string]$obj.db_write

if ($sourceMutation -notin @("False","false","0","")) { throw "source_mutation is not false: $sourceMutation" }
if ($canonicalMerge -notin @("False","false","0","")) { throw "canonical_merge is not false: $canonicalMerge" }
if ($dbWrite -notin @("False","false","0","")) { throw "db_write is not false: $dbWrite" }

$rows += [pscustomobject]@{ Check="NoSourceMutation"; Status="OK"; Detail=$sourceMutation }
$rows += [pscustomobject]@{ Check="NoCanonicalMerge"; Status="OK"; Detail=$canonicalMerge }
$rows += [pscustomobject]@{ Check="NoDbWrite"; Status="OK"; Detail=$dbWrite }
$rows += [pscustomobject]@{ Check="Policy"; Status="OK"; Detail=$obj.policy }

$csv = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_FixedSmoke_Result_v0111.csv")
$json = Join-Path $def_CANDIDATE_DIR ("VIA_" + $def_PROJECT + "_FixedSmoke_Result_v0111.json")
$rows | Export-Csv -LiteralPath $csv -NoTypeInformation -Encoding UTF8
$rows | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $json -Encoding UTF8

Write-Host "[OK] Fixed smoke complete: $def_PROJECT" -ForegroundColor Green
Write-Host "[OK] CSV : $csv" -ForegroundColor Cyan
Write-Host "[OK] JSON: $json" -ForegroundColor Cyan

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
