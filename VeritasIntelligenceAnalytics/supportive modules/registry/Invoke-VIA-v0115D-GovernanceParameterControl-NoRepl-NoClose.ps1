$ErrorActionPreference = "Stop"
Remove-Item Env:PYTHONINSPECT -ErrorAction SilentlyContinue
Remove-Item Env:PYTHONSTARTUP -ErrorAction SilentlyContinue
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONNOUSERSITE = "1"
$Base = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics
"
$GovManagerPy = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_via_governance_parameter_control\VIA_GovernanceParameterControl_v0115D.py
"
$ParamJson = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_integration_v0115D_governance_parameter_control\RUN_20260623_034419_VIA_v0115D_GOVERNANCE_PARAMETER_CONTROL\_governance_parameters\VIA_v0115D_GovernanceParameters_Default.json
"
$SourceRun = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_integration_v0115C_no_repl_matrix_total_progress\RUN_20260623_031535_VIA_v0115C_NO_REPL_MATRIX_TOTAL_PROGRESS
"
$RunRoot = Join-Path $Base "_integration_v0115D_governance_parameter_control"
$RunId = "RUN_{0}_VIA_v0115D_GOVERNANCE_PARAMETER_CONTROL" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$RunDir = Join-Path $RunRoot $RunId
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
function FindPython {
  $venv = Join-Path $Base "_envs\via_operation_optimizer_2026\Scripts\python.exe"
  if (Test-Path -LiteralPath $venv) { return $venv }
  foreach ($cmd in @("python","py")) { try { $null = & $cmd --version 2>$null; if ($LASTEXITCODE -eq 0 -or $?) { return $cmd } } catch {} }
  throw "Python not found."
}
$Python = FindPython
$ArgList = @($GovManagerPy,"--source-run",$SourceRun,"--run-dir",$RunDir,"--params",$ParamJson)
if ($Python -eq "py") { & py -3 -I -X utf8 -B @ArgList } else { & $Python -I -X utf8 -B @ArgList }
if ($LASTEXITCODE -ne 0) { throw "Python failed with exit code $LASTEXITCODE." }
$Report = Join-Path $RunDir "report\VIA_v0115D_GovernanceParameterControl_OnePage_UI.html"
if (Test-Path -LiteralPath $Report) { Start-Process -FilePath $Report }
Write-Host "[OK] GOVERNANCE_PARAMETER_CONTROL_READY_REVIEW_ONLY" -ForegroundColor Green
Write-Host "PowerShell remains open." -ForegroundColor Cyan
