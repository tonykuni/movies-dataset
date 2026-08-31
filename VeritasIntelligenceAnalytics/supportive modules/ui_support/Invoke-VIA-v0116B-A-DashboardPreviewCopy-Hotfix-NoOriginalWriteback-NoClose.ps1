# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
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
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\supportive modules\_via_governance_parameter_control\VIA_DashboardPreviewCopy_v0116B_A_Hotfix.py
"
$SourceRun = "
C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\_integration_v0116_dashboard_binding_dryrun_plan_only\RUN_20260623_195719_VIA_v0116_DASHBOARD_BINDING_DRYRUN_PLAN_ONLY
"
$RunRoot = Join-Path $Base "_integration_v0116B_A_dashboard_preview_copy_hotfix"
$RunId = "RUN_{0}_VIA_v0116B_A_DASHBOARD_PREVIEW_COPY_HOTFIX" -f (Get-Date -Format "yyyyMMdd_HHmmss")
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
$Manifest = Join-Path $RunDir "output\VIA_v0116B_A_DashboardPreviewCopy_Manifest.json"
$Obj = Get-Content -LiteralPath $Manifest -Raw -Encoding UTF8 | ConvertFrom-Json
if (Test-Path -LiteralPath $Obj.preview_copy) { Start-Process -FilePath $Obj.preview_copy }
Write-Host "[OK] DASHBOARD_PREVIEW_COPY_READY_REVIEW_ONLY" -ForegroundColor Green
Write-Host "PowerShell remains open." -ForegroundColor Cyan

