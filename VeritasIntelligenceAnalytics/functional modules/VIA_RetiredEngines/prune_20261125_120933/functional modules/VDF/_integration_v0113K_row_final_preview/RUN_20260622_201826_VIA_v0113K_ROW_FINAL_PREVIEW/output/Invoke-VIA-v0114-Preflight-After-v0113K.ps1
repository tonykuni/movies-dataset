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

$InputJson = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113K_row_final_preview\RUN_20260622_201826_VIA_v0113K_ROW_FINAL_PREVIEW\_v0114_sandbox_candidate_input_pack\VIA_v0114_SandboxPatchCandidate_InputPack.json"
$ReadinessCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113K_row_final_preview\RUN_20260622_201826_VIA_v0113K_ROW_FINAL_PREVIEW\_v0114_sandbox_candidate_input_pack\VIA_v0114_INPUT_ReadinessGate.csv"

if (-not (Test-Path -LiteralPath $InputJson)) {
    throw "Missing v0114 input json: $InputJson"
}

if (-not (Test-Path -LiteralPath $ReadinessCsv)) {
    throw "Missing readiness csv: $ReadinessCsv"
}

$ready = @(Import-Csv -LiteralPath $ReadinessCsv)[0]
$pack = Get-Content -LiteralPath $InputJson -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114 Sandbox Candidate Preflight after v0113K" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate        : $($ready.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow v0114 : $($ready.def_allow_v0114_sandbox_candidate)" -ForegroundColor Yellow
Write-Host "Rows Include: $($ready.def_row_included)" -ForegroundColor Cyan
Write-Host "Rows Exclude: $($ready.def_row_excluded)" -ForegroundColor Cyan
Write-Host "Unsafe Flags: $($ready.def_unsafe_flags)" -ForegroundColor Yellow
Write-Host "Source Mut. : $($ready.def_source_mutation)" -ForegroundColor Yellow
Write-Host "Canonical   : $($ready.def_canonical_merge)" -ForegroundColor Yellow
Write-Host "DB Write    : $($ready.def_db_write)" -ForegroundColor Yellow

if ($ready.def_allow_v0114_sandbox_candidate -ne "true") {
    throw "BLOCKED_NOT_READY_FOR_v0114_SANDBOX_CANDIDATE."
}

if ($ready.def_source_mutation -ne "false" -or $ready.def_canonical_merge -ne "false" -or $ready.def_db_write -ne "false") {
    throw "BLOCKED_UNSAFE_MUTATION_FLAG."
}

Write-Host "[OK] READY_FOR_v0114_SANDBOX_PATCH_CANDIDATE_GENERATION_ONLY" -ForegroundColor Green
Write-Host "Input JSON: $InputJson" -ForegroundColor Cyan

if ($VIACelTplOwn) { try { Restore-CeleritasPS7 } catch { } }  # [VIA:PS-TEMPLATE] restore on exit
