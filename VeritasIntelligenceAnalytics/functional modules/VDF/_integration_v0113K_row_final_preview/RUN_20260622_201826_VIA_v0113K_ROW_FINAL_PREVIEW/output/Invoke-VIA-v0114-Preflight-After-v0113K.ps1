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
