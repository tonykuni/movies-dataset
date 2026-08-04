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
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_via_governance_parameter_control\VIA_GovernanceUIContractSeal_v0115F8.py
"
$SourceRun = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_integration_v0115F7_ledger_evidence_validation_only\RUN_20260623_130243_VIA_v0115F7_LEDGER_EVIDENCE_VALIDATION_ONLY
"
$RunRoot = Join-Path $Base "_integration_v0115F8_governance_ui_contract_seal_only"
$RunId = "RUN_{0}_VIA_v0115F8_GOVERNANCE_UI_CONTRACT_SEAL_ONLY" -f (Get-Date -Format "yyyyMMdd_HHmmss")
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
$Report = Join-Path $RunDir "report\VIA_v0115F8_GovernanceUIContractSeal_OnePage.html"
if (Test-Path -LiteralPath $Report) { Start-Process -FilePath $Report }
Write-Host "[OK] GOVERNANCE_UI_CONTRACT_SEAL_READY_REVIEW_ONLY" -ForegroundColor Green
Write-Host "PowerShell remains open." -ForegroundColor Cyan
