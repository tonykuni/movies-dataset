#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = "C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
$Builder = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_WAREHOUSE_V5_NEXT3_20260506_231125\vap_warehouse_v5_next3_builder.py"
$Html = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_WAREHOUSE_V5_NEXT3_20260506_231125\VAP_Warehouse_V5_Next3_Report.html"

Write-Host ""
Write-Host "Refreshing VAP Warehouse V5 Next3..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)

if (Test-Path -LiteralPath $Html) {
    Start-Process $Html
    Write-Host "[OK] HTML = $Html" -ForegroundColor Green
} else {
    Write-Host "[ERR] HTML not found: $Html" -ForegroundColor Red
}
