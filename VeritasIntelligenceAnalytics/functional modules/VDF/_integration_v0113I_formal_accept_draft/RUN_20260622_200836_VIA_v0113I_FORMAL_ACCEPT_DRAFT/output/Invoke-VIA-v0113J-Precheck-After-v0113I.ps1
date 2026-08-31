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

$P0FormalCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113I_formal_accept_draft\RUN_20260622_200836_VIA_v0113I_FORMAL_ACCEPT_DRAFT\_user_edit_formal_accept_draft\VIA_v0113I_USER_EDIT_P0_FormalAcceptDraft.csv"
$P1FormalCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113I_formal_accept_draft\RUN_20260622_200836_VIA_v0113I_FORMAL_ACCEPT_DRAFT\_user_edit_formal_accept_draft\VIA_v0113I_USER_EDIT_P1_FormalAcceptDraft.csv"
$SecretCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113I_formal_accept_draft\RUN_20260622_200836_VIA_v0113I_FORMAL_ACCEPT_DRAFT\_user_edit_formal_accept_draft\VIA_v0113I_SecretGateFinal.csv"

function def_Load {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
    return @(Import-Csv -LiteralPath $Path)
}

$p0 = def_Load $P0FormalCsv
$p1 = def_Load $P1FormalCsv
$sec = def_Load $SecretCsv

$secPending = @($sec | Where-Object { ([string]$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
$p0Pending = @($p0 | Where-Object { ([string]$_.def_group_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
$p1Pending = @($p1 | Where-Object { ([string]$_.def_alias_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0113J Precheck after v0113I" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending : $secPending / $($sec.Count)" -ForegroundColor Yellow
Write-Host "P0 pending     : $p0Pending / $($p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending     : $p1Pending / $($p1.Count)" -ForegroundColor Yellow

if ($secPending -gt 0) {
    throw "BLOCKED_SECRET_GATE."
}

if ($p0Pending -gt 0 -or $p1Pending -gt 0) {
    throw "BLOCKED_FORMAL_ACCEPT_REQUIRED. Promote draft choices to formal accept fields first."
}

Write-Host "[OK] READY_FOR_v0113J_FORMAL_ACCEPT_ROW_EXPANSION" -ForegroundColor Green

