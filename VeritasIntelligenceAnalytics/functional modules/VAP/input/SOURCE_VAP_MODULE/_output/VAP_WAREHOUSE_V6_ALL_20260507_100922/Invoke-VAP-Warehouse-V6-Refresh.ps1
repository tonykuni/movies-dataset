#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = "C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
$Builder = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_WAREHOUSE_V6_ALL_20260507_100922\vap_warehouse_v6_all_builder.py"
$Html = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_WAREHOUSE_V6_ALL_20260507_100922\VAP_Warehouse_V6_Workstation_Report.html"
Write-Host ""
Write-Host "Refreshing VAP Warehouse V6..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) {
    Start-Process $Html
    Write-Host "[OK] HTML = $Html" -ForegroundColor Green
} else {
    Write-Host "[ERR] HTML not found: $Html" -ForegroundColor Red
}
