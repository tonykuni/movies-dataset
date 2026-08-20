$ErrorActionPreference = "Stop"

$P0Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\_user_edit_refined\VIA_v0113B_USER_EDIT_P0_RefinedManualGate.csv"
$P1Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\_user_edit_refined\VIA_v0113B_USER_EDIT_P1_RefinedManualGate.csv"
$SecretTriageCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113B_secret_triage_manual_gate\RUN_20260622_184034_VIA_v0113B_SECRET_TRIAGE_MANUAL_GATE\output\VIA_v0113B_SecretTriage.csv"

function def_Load {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
    return @(Import-Csv -LiteralPath $Path)
}

$p0 = def_Load $P0Csv
$p1 = def_Load $P1Csv
$sec = def_Load $SecretTriageCsv

$secretBlock = @($sec | Where-Object { ([string]$_.def_secret_block).Trim().ToLowerInvariant() -eq "true" }).Count
$p0Pending = @($p0 | Where-Object { ([string]$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
$p1Pending = @($p1 | Where-Object { ([string]$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114 Precheck after v0113B" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret blockers : $secretBlock" -ForegroundColor Yellow
Write-Host "P0 pending      : $p0Pending / $($p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending      : $p1Pending / $($p1.Count)" -ForegroundColor Yellow

if ($secretBlock -gt 0) {
    throw "BLOCKED_TRUE_SECRET_REVIEW_REQUIRED. Resolve/confirm env-only/rotate before v0114."
}

if ($p0Pending -gt 0 -or $p1Pending -gt 0) {
    throw "BLOCKED_MANUAL_ACCEPT_REQUIRED. Edit P0/P1 refined CSV and set accepted rows to YES."
}

Write-Host "[OK] READY_FOR_V0114_SANDBOX_PATCH_CANDIDATE" -ForegroundColor Green
