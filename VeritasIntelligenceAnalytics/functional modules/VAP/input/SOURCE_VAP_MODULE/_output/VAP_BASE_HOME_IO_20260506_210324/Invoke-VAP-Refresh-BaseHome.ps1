#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = "C:\Users\tonyk\envs\via_core_312\Scripts\python.exe"
$Builder = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_BASE_HOME_IO_20260506_210324\vap_base_home_io_builder.py"
$Html = "C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VAP\_output\VAP_BASE_HOME_IO_20260506_210324\VAP_Base_Home_WindowsIO_TemplateLibrary.html"

Write-Host ""
Write-Host "Refreshing VAP Base Home..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) {
    Start-Process $Html
    Write-Host "[OK] HTML = $Html" -ForegroundColor Green
} else {
    Write-Host "[ERR] HTML not found: $Html" -ForegroundColor Red
}
