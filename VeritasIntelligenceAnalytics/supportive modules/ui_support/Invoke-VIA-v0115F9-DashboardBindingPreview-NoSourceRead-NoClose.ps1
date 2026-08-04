$ErrorActionPreference = "Stop"
[Environment]::SetEnvironmentVariable("PYTHONINSPECT", $null, "Process")
[Environment]::SetEnvironmentVariable("PYTHONSTARTUP", $null, "Process")
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONNOUSERSITE = "1"
$Base = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics
"
$ManagerPy = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_via_governance_parameter_control\VIA_DashboardBindingPreview_v0115F9.py
"
$SourceRun = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_integration_v0115F8_governance_ui_contract_seal_only\RUN_20260623_130719_VIA_v0115F8_GOVERNANCE_UI_CONTRACT_SEAL_ONLY
"
$RunRoot = Join-Path $Base "_integration_v0115F9_dashboard_binding_preview_only"
$RunId = "RUN_{0}_VIA_v0115F9_DASHBOARD_BINDING_PREVIEW_ONLY" -f (Get-Date -Format "yyyyMMdd_HHmmss")
$RunDir = Join-Path $RunRoot $RunId
New-Item -ItemType Directory -Path $RunDir -Force | Out-Null
function FindPython {
  $venv = Join-Path $Base "_envs\via_operation_optimizer_2026\Scripts\python.exe"
  if (Test-Path -LiteralPath $venv) { return $venv }
  foreach ($cmd in @("python","py")) { try { $null = & $cmd --version 2>$null; if ($LASTEXITCODE -eq 0 -or $?) { return $cmd } } catch {} }
  throw "Python not found."
}
$Python = FindPython
$ArgList = @($ManagerPy,"--source-run",$SourceRun,"--run-dir",$RunDir)
if ($Python -eq "py") { & py -3 -I -X utf8 -B @ArgList } else { & $Python -I -X utf8 -B @ArgList }
if ($LASTEXITCODE -ne 0) { throw "Python failed with exit code $LASTEXITCODE." }
$Report = Join-Path $RunDir "report\VIA_v0115F9_DashboardBindingPreview_OnePage.html"
if (Test-Path -LiteralPath $Report) { Start-Process -FilePath $Report }
Write-Host "[OK] DASHBOARD_BINDING_PREVIEW_READY_REVIEW_ONLY" -ForegroundColor Green
Write-Host "PowerShell remains open." -ForegroundColor Cyan
