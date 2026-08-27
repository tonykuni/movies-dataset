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

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
