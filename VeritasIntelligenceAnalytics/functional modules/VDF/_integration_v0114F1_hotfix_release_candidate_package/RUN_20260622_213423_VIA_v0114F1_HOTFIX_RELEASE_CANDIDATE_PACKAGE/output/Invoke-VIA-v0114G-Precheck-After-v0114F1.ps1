$ErrorActionPreference = "Stop"
$ReadinessCsv = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114F1_hotfix_release_candidate_package\RUN_20260622_213423_VIA_v0114F1_HOTFIX_RELEASE_CANDIDATE_PACKAGE\output\VIA_v0114F1_ReadinessGate.csv
"
if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }
$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114G Precheck after v0114F1" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow      : $($r.def_allow_v0114G)" -ForegroundColor Yellow
Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow
Write-Host "Items      : $($r.def_package_items)" -ForegroundColor Cyan
Write-Host "Zip        : $($r.def_zip_path)" -ForegroundColor Cyan
Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow
Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow
Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow
Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow
if ($r.def_allow_v0114G -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114G." }
if ($r.def_apply_enabled -ne "false") { throw "BLOCKED_APPLY_SHOULD_BE_DISABLED." }
if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }
Write-Host "[OK] READY_FOR_v0114G_RELEASE_CANDIDATE_PACKAGE_VALIDATION_ONLY" -ForegroundColor Green
