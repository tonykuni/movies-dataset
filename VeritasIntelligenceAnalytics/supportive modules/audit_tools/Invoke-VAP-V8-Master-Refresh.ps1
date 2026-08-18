#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = "C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
$Builder = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_V8_MASTER_20260507_233550\SUP_MDL558_V8MasterOrchestrator.py"
$Html = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_V8_MASTER_20260507_233550\VAP_V8_Master_Orchestrator_Report.html"
Write-Host ""
Write-Host "Refreshing VAP V8 Master Orchestrator..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) { Start-Process $Html; Write-Host "[OK] HTML = $Html" -ForegroundColor Green }
