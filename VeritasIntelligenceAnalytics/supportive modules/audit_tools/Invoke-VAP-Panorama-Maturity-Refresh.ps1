#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = "C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
$Builder = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_PANORAMA_MATURITY_OPT_20260507_110152\SUP_MDL557_PanoramaMaturityOptimizer.py"
$Html = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_PANORAMA_MATURITY_OPT_20260507_110152\VAP_Panorama_Maturity_Optimization_Report.html"
Write-Host ""
Write-Host "Refreshing VAP Panorama Maturity Optimizer..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) {
    Start-Process $Html
    Write-Host "[OK] HTML = $Html" -ForegroundColor Green
} else {
    Write-Host "[ERR] HTML not found: $Html" -ForegroundColor Red
}
