$ErrorActionPreference = "Stop"
$ReadinessCsv = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114E_manual_release_approval\RUN_20260622_212143_VIA_v0114E_MANUAL_RELEASE_APPROVAL\output\VIA_v0114E_ReadinessGate.csv
"
$ApprovalCsv = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114E_manual_release_approval\RUN_20260622_212143_VIA_v0114E_MANUAL_RELEASE_APPROVAL\_manual_release_approval_gate\VIA_v0114E_ManualReleaseApproval.csv
"
if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }
if (-not (Test-Path -LiteralPath $ApprovalCsv)) { throw "Missing approval csv: $ApprovalCsv" }
$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]
$a = @(Import-Csv -LiteralPath $ApprovalCsv)[0]
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114F Precheck after v0114E" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow      : $($r.def_allow_v0114F)" -ForegroundColor Yellow
Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow
Write-Host "User Accept: $($a.def_user_release_accept)" -ForegroundColor Yellow
Write-Host "Apply      : $($r.def_apply_enabled)" -ForegroundColor Yellow
Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow
Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow
Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow
if ($r.def_allow_v0114F -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114F." }
if ($r.def_apply_enabled -ne "false") { throw "BLOCKED_APPLY_SHOULD_BE_DISABLED." }
if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }
Write-Host "[OK] READY_FOR_v0114F_RELEASE_CANDIDATE_PACKAGE_ONLY" -ForegroundColor Green
