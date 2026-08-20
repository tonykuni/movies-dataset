#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = "C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
$Builder = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_WAREHOUSE_V4_20260506_222535\vap_warehouse_v4_builder.py"
$Html = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_WAREHOUSE_V4_20260506_222535\VAP_Warehouse_V4_Intelligence_Report.html"

if ([string]::IsNullOrWhiteSpace($Builder) -or -not (Test-Path -LiteralPath $Builder)) {
    Write-Host "[ERR] V4 builder not found. Re-run VAP_Warehouse_V4_AllInOne.ps1." -ForegroundColor Red
    return
}

Write-Host ""
Write-Host "Refreshing VAP Warehouse V4..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) {
    Start-Process $Html
    Write-Host "[OK] HTML = $Html" -ForegroundColor Green
}
