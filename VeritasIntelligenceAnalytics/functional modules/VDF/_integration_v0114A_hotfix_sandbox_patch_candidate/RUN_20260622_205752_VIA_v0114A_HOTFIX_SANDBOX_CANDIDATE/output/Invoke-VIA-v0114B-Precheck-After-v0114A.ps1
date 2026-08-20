$ErrorActionPreference = "Stop"
$ReadinessCsv = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114A_hotfix_sandbox_patch_candidate\RUN_20260622_205752_VIA_v0114A_HOTFIX_SANDBOX_CANDIDATE\output\VIA_v0114A_ReadinessGate.csv
"
if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }
$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114B Precheck after v0114A" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow      : $($r.def_allow_v0114B)" -ForegroundColor Yellow
Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow
Write-Host "Rows       : $($r.def_row_patch_plan_rows)" -ForegroundColor Cyan
Write-Host "Policy     : $($r.def_policy_candidate_rows)" -ForegroundColor Cyan
Write-Host "Alias      : $($r.def_alias_candidate_rows)" -ForegroundColor Cyan
Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow
Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow
Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow
if ($r.def_allow_v0114B -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114B." }
if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }
Write-Host "[OK] READY_FOR_v0114B_SANDBOX_CANDIDATE_VALIDATION_ONLY" -ForegroundColor Green
