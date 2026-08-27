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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
