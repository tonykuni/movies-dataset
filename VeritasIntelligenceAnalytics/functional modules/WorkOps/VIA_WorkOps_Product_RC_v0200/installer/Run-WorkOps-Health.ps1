#requires -Version 7.0
param([string]$AppRoot=(Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference="Stop"
Set-Location $AppRoot
$py=Get-Command python -ErrorAction SilentlyContinue
if(-not $py){throw "python not found"}
& $py.Source "engines\workops_module_lifecycle_manager.py" health
& $py.Source "engines\VIA_ENG136_WorkopsSsotStore.py" snapshot
& $py.Source "engines\VIA_ENG113_WorkopsDiagnostics.py" build
Write-Host "def Diagnostics HTML: $(Join-Path $AppRoot 'out\diagnostics.html')" -ForegroundColor Cyan
