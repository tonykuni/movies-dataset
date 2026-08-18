#requires -Version 7.0
<# =====================================================================
 Invoke-VRN-Shimmed-Entry v0100 - P2 opt-in shimmed launcher
 Runs any legacy-regex .py/.ps1 through the TickerRegex v0100 shim:
   canonical source -> run-local shimmed copy -> execute the copy.
 Canonical files are never written. Old entries keep working unchanged.
 Usage:
   pwsh -File Invoke-VRN-Shimmed-Entry-v0100.ps1 -Target ".\VRN_ENG014_MDL001StockReportPipeline.py" [-Args @("--flag","v")]
===================================================================== #>
param(
    [Parameter(Mandatory)][string]$Target,
    [string[]]$Args = @(),
    [switch]$DryRun
)
Set-StrictMode -Off
$ErrorActionPreference = "Continue"
$via  = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent | Join-Path -ChildPath "VeritasIntelligenceAnalytics"
if (-not (Test-Path $via)) { $via = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent }
$shim = Join-Path (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent) "VeritasIntelligenceAnalytics\supportive modules\70_VRN_Rules\SUP_MDL031_VISVRNTickerRegexShim_v0100.py"
if (-not (Test-Path -LiteralPath $shim)) { $shim = Join-Path (Split-Path $PSScriptRoot -Parent) "..\supportive modules\70_VRN_Rules\SUP_MDL031_VISVRNTickerRegexShim_v0100.py" }
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
$runDir = Join-Path $env:USERPROFILE "VIA_Reports\_shim_runs\$ts"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$src = (Resolve-Path -LiteralPath $Target).Path
$dst = Join-Path $runDir ([IO.Path]::GetFileName($src))
$py = @("C:\Users\tonyk\envs\via_core_312\Scripts\python.exe","py") |
      Where-Object { ($_ -eq "py") -or (Test-Path $_) } | Select-Object -First 1

Write-Host "[SHIM] $src" -ForegroundColor Cyan
$rec = & $py $shim $src $dst 2>&1
$rec | Out-Host
if ($LASTEXITCODE -ne 0) { Write-Host "[ABORT] shim failed" -ForegroundColor Red; return }

if ($src.EndsWith(".py")) {
    & $py -m py_compile $dst 2>&1 | Out-Host
    if ($LASTEXITCODE -ne 0) { Write-Host "[ABORT] shimmed copy fails py_compile - not executing" -ForegroundColor Red; return }
    Write-Host "[VERIFY] shimmed copy py_compile PASS" -ForegroundColor Green
    if ($DryRun) { Write-Host "[DRYRUN] stopping before execution. Shimmed copy: $dst" -ForegroundColor Yellow; return }
    & $py $dst @Args
} elseif ($src.EndsWith(".ps1")) {
    if ($DryRun) { Write-Host "[DRYRUN] stopping before execution. Shimmed copy: $dst" -ForegroundColor Yellow; return }
    pwsh -NoProfile -NonInteractive -File $dst @Args
} else {
    Write-Host "[ABORT] unsupported target type" -ForegroundColor Red
}
Write-Host "[SHIM-RUN DONE] run-local: $runDir (canonical untouched)" -ForegroundColor Cyan
