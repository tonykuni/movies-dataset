$ErrorActionPreference = "Stop"

$ReadinessCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113J_formal_decision_promotion\RUN_20260622_201203_VIA_v0113J_FORMAL_DECISION_PROMOTION\output\VIA_v0113J_ReadinessGate.csv"

if (-not (Test-Path -LiteralPath $ReadinessCsv)) {
    throw "Missing readiness CSV: $ReadinessCsv"
}

$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0113K Precheck after v0113J" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate        : $($r.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow v0113K: $($r.def_allow_v0113K)" -ForegroundColor Yellow
Write-Host "P0 pending  : $($r.def_p0_pending) / $($r.def_p0_total)" -ForegroundColor Yellow
Write-Host "P1 pending  : $($r.def_p1_pending) / $($r.def_p1_total)" -ForegroundColor Yellow

if ($r.def_allow_v0113K -ne "true") {
    throw "BLOCKED_NOT_READY_FOR_v0113K."
}

Write-Host "[OK] READY_FOR_v0113K_ROW_LEVEL_FINAL_PREVIEW" -ForegroundColor Green
