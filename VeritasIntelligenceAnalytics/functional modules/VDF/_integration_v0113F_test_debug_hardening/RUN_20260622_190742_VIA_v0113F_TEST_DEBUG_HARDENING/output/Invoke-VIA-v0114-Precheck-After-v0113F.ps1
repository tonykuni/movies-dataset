# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
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

$SecretCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\_user_edit_after_secret_gate_cleared\VIA_v0113F_USER_EDIT_SecretResolution_FINAL.csv"
$P0Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\_user_edit_after_secret_gate_cleared\VIA_v0113F_USER_EDIT_P0_RefinedManualGate.csv"
$P1Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113F_test_debug_hardening\RUN_20260622_190742_VIA_v0113F_TEST_DEBUG_HARDENING\_user_edit_after_secret_gate_cleared\VIA_v0113F_USER_EDIT_P1_RefinedManualGate.csv"

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
Write-Host "def VIA · v0114 Precheck after v0113F" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending : $secPending / $($sec.Count)" -ForegroundColor Yellow
Write-Host "P0 pending     : $p0Pending / $($p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending     : $p1Pending / $($p1.Count)" -ForegroundColor Yellow

if ($secPending -gt 0) {
    throw "BLOCKED_SECRET_RESOLUTION_REQUIRED."
}

if ($p0Pending -gt 0 -or $p1Pending -gt 0) {
    throw "BLOCKED_MANUAL_ACCEPT_REQUIRED. Edit P0/P1 CSV and set accepted rows to YES."
}

Write-Host "[OK] READY_FOR_V0114_SANDBOX_PATCH_CANDIDATE" -ForegroundColor Green

