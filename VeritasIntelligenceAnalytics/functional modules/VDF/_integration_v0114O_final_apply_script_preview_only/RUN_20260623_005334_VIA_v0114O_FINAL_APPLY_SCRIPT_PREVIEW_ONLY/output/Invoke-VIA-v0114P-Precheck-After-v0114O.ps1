$ErrorActionPreference = "Stop"
$ReadinessCsv = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114O_final_apply_script_preview_only\RUN_20260623_005334_VIA_v0114O_FINAL_APPLY_SCRIPT_PREVIEW_ONLY\output\VIA_v0114O_ReadinessGate.csv
"
if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }
$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114P Precheck after v0114O" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow      : $($r.def_allow_v0114P)" -ForegroundColor Yellow
Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow
Write-Host "Rows       : $($r.def_script_preview_rows)" -ForegroundColor Cyan
Write-Host "Execution  : $($r.def_execution_enabled)" -ForegroundColor Yellow
Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow
Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow
Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow
Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow
if ($r.def_allow_v0114P -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114P." }
if ($r.def_execution_enabled -ne "false" -or $r.def_apply_enabled -ne "false") { throw "BLOCKED_EXECUTION_OR_APPLY_SHOULD_BE_DISABLED." }
if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }
Write-Host "[OK] READY_FOR_v0114P_FINAL_SCRIPT_PREVIEW_VALIDATION_ONLY" -ForegroundColor Green
