#requires -Version 7.0
[CmdletBinding()]
param(
    [string]$AppRoot = (Split-Path -Parent $PSScriptRoot),
    [switch]$LiveGraphRead
)
$ErrorActionPreference="Stop"
Set-Location $AppRoot
$py=Get-Command python -ErrorAction Stop
Write-Host "def RC ACCEPTANCE · LOCAL" -ForegroundColor Cyan
& $py.Source -m compileall -q "engines"
if($LASTEXITCODE -ne 0){throw "Compile failed"}
& $py.Source "tests\rc_acceptance.py"
if($LASTEXITCODE -ne 0){throw "Local RC acceptance failed"}

if($LiveGraphRead){
    Write-Host "def LIVE GRAPH READ · explicit opt-in" -ForegroundColor Yellow
    & $py.Source "engines\workops_outlook_graph_connector.py" sync
    if($LASTEXITCODE -ne 0){throw "Live Graph read validation failed"}
    & $py.Source "engines\workops_orchestrator.py" refresh
    if($LASTEXITCODE -ne 0){throw "Post-sync refresh failed"}
}
& $py.Source "engines\workops_ssot_store.py" snapshot
& $py.Source "engines\workops_module_lifecycle_manager.py" health
& $py.Source "engines\workops_diagnostics.py" build
Write-Host "def RC ACCEPTANCE PASS" -ForegroundColor Green
Write-Host "def Diagnostics: $(Join-Path $AppRoot 'out\diagnostics.html')"
