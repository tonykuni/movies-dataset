#requires -Version 7.0
[CmdletBinding()]
param(
  [string]$WorkOpsRoot="$env:USERPROFILE\Downloads\VeritasIntelligenceAnalytics\functional modules\WorkOps",
  [switch]$StageToOut
)
$ErrorActionPreference="Stop"
$Here=Split-Path -Parent $MyInvocation.MyCommand.Path
$Files=@(
 "workops_control_common.py",
 "workops_unified_work_register.py",
 "workops_commitment_intelligence.py",
 "workops_consistency_guard.py",
 "workops_project_health.py"
)
Write-Host "================================================================================================" -ForegroundColor DarkCyan
Write-Host "def VERITAS WORKOPS · ENG-050..053 · REVIEW ONLY · v0100" -ForegroundColor Cyan
Write-Host "================================================================================================" -ForegroundColor DarkCyan
$Target=Join-Path $WorkOpsRoot "engines"
$Rows=@()
foreach($f in $Files){
  $src=Join-Path $Here "engines\$f"
  $dst=Join-Path $Target $f
  $Rows += [pscustomobject]@{
    File=$f
    TargetState=$(if(Test-Path $dst){"EXISTS_REVIEW_CONFLICT"}else{"MISSING_OK_TO_STAGE"})
    SHA256=(Get-FileHash $src -Algorithm SHA256).Hash
  }
}
$Rows | Format-Table -AutoSize
if($StageToOut){
  $Run=Join-Path $WorkOpsRoot ("out\_eng050_053_staging\RUN_"+(Get-Date -Format "yyyyMMdd_HHmmss"))
  New-Item -ItemType Directory -Force -Path $Run | Out-Null
  foreach($f in $Files){Copy-Item (Join-Path $Here "engines\$f") (Join-Path $Run $f)}
  Copy-Item (Join-Path $Here "config\*.json") $Run
  Write-Host "def STAGED : $Run" -ForegroundColor Yellow
  Write-Host "def Canonical mutation : 0" -ForegroundColor Green
}
Write-Host "def Gate : REVIEW_REQUIRED" -ForegroundColor Yellow

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
