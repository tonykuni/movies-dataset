$ErrorActionPreference = "Stop"

$P0GroupCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_USER_EDIT_P0_GroupDecisionBoard.csv"
$P1AliasCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_USER_EDIT_P1_AliasDecisionBoard.csv"
$SecretCsv = "C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0113G_p0p1_gate_compression\RUN_20260622_200208_VIA_v0113G_P0P1_GATE_COMPRESSION\_user_edit_group_decision\VIA_v0113G_SecretGateFinal.csv"

function def_Load {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) { throw "Missing file: $Path" }
    return @(Import-Csv -LiteralPath $Path)
}

$p0 = def_Load $P0GroupCsv
$p1 = def_Load $P1AliasCsv
$sec = def_Load $SecretCsv

$secPending = @($sec | Where-Object { ([string]$_.def_user_secret_resolved).Trim().ToUpperInvariant() -ne "YES" }).Count
$p0Pending = @($p0 | Where-Object { ([string]$_.def_group_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count
$p1Pending = @($p1 | Where-Object { ([string]$_.def_alias_user_accept).Trim().ToUpperInvariant() -ne "YES" }).Count

Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0113H Precheck after v0113G" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Secret pending  : $secPending / $($sec.Count)" -ForegroundColor Yellow
Write-Host "P0 group pending: $p0Pending / $($p0.Count)" -ForegroundColor Yellow
Write-Host "P1 alias pending: $p1Pending / $($p1.Count)" -ForegroundColor Yellow

if ($secPending -gt 0) {
    throw "BLOCKED_SECRET_RESOLUTION_REQUIRED."
}

if ($p0Pending -gt 0 -or $p1Pending -gt 0) {
    throw "BLOCKED_GROUP_ACCEPT_REQUIRED. Edit compressed group boards and set accepted groups to YES."
}

Write-Host "[OK] READY_FOR_v0113H_ROW_LEVEL_ACCEPT_EXPANSION_PREVIEW" -ForegroundColor Green

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
