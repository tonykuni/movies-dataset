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
