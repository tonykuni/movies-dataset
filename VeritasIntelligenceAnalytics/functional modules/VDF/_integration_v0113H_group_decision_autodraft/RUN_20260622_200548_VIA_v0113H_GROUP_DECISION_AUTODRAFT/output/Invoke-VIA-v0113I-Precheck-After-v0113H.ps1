$ErrorActionPreference = "Stop"

$P0DraftCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\_user_edit_final_group_decision\VIA_v0113H_USER_EDIT_P0_GroupDecision_AUTODRAFT.csv"
$P1DraftCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\_user_edit_final_group_decision\VIA_v0113H_USER_EDIT_P1_AliasDecision_AUTODRAFT.csv"
$SecretCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113H_group_decision_autodraft\RUN_20260622_200548_VIA_v0113H_GROUP_DECISION_AUTODRAFT\_user_edit_final_group_decision\VIA_v0113H_SecretGateFinal.csv"

function def_Load {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
    return @(Import-Csv -LiteralPath $Path)
}

$p0 = def_Load $P0DraftCsv
$p1 = def_Load $P1DraftCsv
$sec = def_Load $SecretCsv

$secPending = @($sec | Where-Object { ([string]$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
$p0Pending = @($p0 | Where-Object { ([string]$_.def_group_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
$p1Pending = @($p1 | Where-Object { ([string]$_.def_alias_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0113I Precheck after v0113H" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending : $secPending / $($sec.Count)" -ForegroundColor Yellow
Write-Host "P0 pending     : $p0Pending / $($p0.Count)" -ForegroundColor Yellow
Write-Host "P1 pending     : $p1Pending / $($p1.Count)" -ForegroundColor Yellow

if ($secPending -gt 0) {
    throw "BLOCKED_SECRET_GATE."
}

if ($p0Pending -gt 0 -or $p1Pending -gt 0) {
    throw "BLOCKED_MANUAL_CONFIRM_REQUIRED. Copy chosen recommendations into formal accept fields first."
}

Write-Host "[OK] READY_FOR_v0113I_FORMAL_ACCEPT_EXPANSION" -ForegroundColor Green
