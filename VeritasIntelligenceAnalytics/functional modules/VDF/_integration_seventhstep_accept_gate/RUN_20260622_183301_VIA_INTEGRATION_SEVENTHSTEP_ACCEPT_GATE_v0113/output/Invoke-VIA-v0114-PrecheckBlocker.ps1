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

$P0Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\_accept_gate_user_edit\VIA_v0113_USER_EDIT_P0_AcceptGate.csv"
$P1Csv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_seventhstep_accept_gate\RUN_20260622_183301_VIA_INTEGRATION_SEVENTHSTEP_ACCEPT_GATE_v0113\_accept_gate_user_edit\VIA_v0113_USER_EDIT_P1_PathAlias_AcceptGate.csv"

function def_GetRows {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing accept CSV: $Path"
    }
    return @(Import-Csv -LiteralPath $Path)
}

$p0 = def_GetRows $P0Csv
$p1 = def_GetRows $P1Csv

$p0No = @($p0 | Where-Object { ([string]$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
$p1No = @($p1 | Where-Object { ([string]$_.def_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114 Precheck Blocker" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "P0 pending: $p0No / $($p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending: $p1No / $($p1.Count)" -ForegroundColor Yellow

if ($p0No -gt 0 -or $p1No -gt 0) {
    throw "BLOCKED_MANUAL_ACCEPT_REQUIRED. Edit P0/P1 accept CSV before v0114."
}

Write-Host "[OK] READY_FOR_V0114_PATCH_CANDIDATE" -ForegroundColor Green

