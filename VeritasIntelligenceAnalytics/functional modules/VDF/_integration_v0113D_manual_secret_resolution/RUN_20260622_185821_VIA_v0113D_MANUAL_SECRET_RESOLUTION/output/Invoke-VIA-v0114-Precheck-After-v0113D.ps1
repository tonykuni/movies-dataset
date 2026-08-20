$ErrorActionPreference = "Stop"

$SecretCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution\VIA_v0113D_USER_EDIT_SecretResolution_RESOLVED.csv"
$P0Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution\VIA_v0113D_USER_EDIT_P0_RefinedManualGate.csv"
$P1Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113D_manual_secret_resolution\RUN_20260622_185821_VIA_v0113D_MANUAL_SECRET_RESOLUTION\_user_edit_after_secret_resolution\VIA_v0113D_USER_EDIT_P1_RefinedManualGate.csv"

function def_Load {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
    return @(Import-Csv -LiteralPath $Path)
}

$sec = def_Load $SecretCsv
$p0  = def_Load $P0Csv
$p1  = def_Load $P1Csv

$secPending = @($sec | Where-Object { ([string]$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
$p0Pending  = @($p0  | Where-Object { ([string]$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
$p1Pending  = @($p1  | Where-Object { ([string]$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114 Precheck after v0113D" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending : $secPending / $($sec.Count)" -ForegroundColor Yellow
Write-Host "P0 pending     : $p0Pending / $($p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending     : $p1Pending / $($p1.Count)" -ForegroundColor Yellow

if ($secPending -gt 0) {
    throw "BLOCKED_SECRET_RESOLUTION_REQUIRED. Resolve secret board first."
}

if ($p0Pending -gt 0 -or $p1Pending -gt 0) {
    throw "BLOCKED_MANUAL_ACCEPT_REQUIRED. Edit P0/P1 CSV and set accepted rows to YES."
}

Write-Host "[OK] READY_FOR_V0114_SANDBOX_PATCH_CANDIDATE" -ForegroundColor Green
