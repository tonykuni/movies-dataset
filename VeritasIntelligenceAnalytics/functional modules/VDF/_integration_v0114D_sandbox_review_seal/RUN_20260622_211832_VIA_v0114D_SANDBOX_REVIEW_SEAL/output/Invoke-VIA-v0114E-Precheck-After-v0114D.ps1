$ErrorActionPreference = "Stop"
$ReadinessCsv = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114D_sandbox_review_seal\RUN_20260622_211832_VIA_v0114D_SANDBOX_REVIEW_SEAL\output\VIA_v0114D_ReadinessGate.csv
"
$DecisionCsv = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\functional modules\VDF\_integration_v0114D_sandbox_review_seal\RUN_20260622_211832_VIA_v0114D_SANDBOX_REVIEW_SEAL\_manual_release_gate_draft\VIA_v0114D_USER_EDIT_ManualReleaseDecision.csv
"
if (-not (Test-Path -LiteralPath $ReadinessCsv)) { throw "Missing readiness csv: $ReadinessCsv" }
if (-not (Test-Path -LiteralPath $DecisionCsv)) { throw "Missing decision csv: $DecisionCsv" }
$r = @(Import-Csv -LiteralPath $ReadinessCsv)[0]
$d = @(Import-Csv -LiteralPath $DecisionCsv)[0]
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114E Precheck after v0114D" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "Gate       : $($r.def_gate_status)" -ForegroundColor Yellow
Write-Host "Allow      : $($r.def_allow_v0114E)" -ForegroundColor Yellow
Write-Host "Validation : $($r.def_validation_fail)" -ForegroundColor Yellow
Write-Host "User Accept: $($d.def_user_release_accept)" -ForegroundColor Yellow
Write-Host "Mutation   : $($r.def_source_mutation)" -ForegroundColor Yellow
Write-Host "Canonical  : $($r.def_canonical_merge)" -ForegroundColor Yellow
Write-Host "DB Write   : $($r.def_db_write)" -ForegroundColor Yellow
if ($r.def_allow_v0114E -ne "true") { throw "BLOCKED_NOT_READY_FOR_v0114E." }
if ($r.def_source_mutation -ne "false" -or $r.def_canonical_merge -ne "false" -or $r.def_db_write -ne "false") { throw "BLOCKED_UNSAFE_BOUNDARY." }
Write-Host "[OK] READY_FOR_v0114E_MANUAL_RELEASE_APPROVAL_GATE_ONLY" -ForegroundColor Green

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
