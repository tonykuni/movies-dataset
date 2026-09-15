#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "VAP Next Optimization Actions" -ForegroundColor Cyan
Write-Host "1) Open V6 script and set EnableNetworkFetch = `$true" -ForegroundColor Yellow
Write-Host "2) Re-run V6 to fetch live data" -ForegroundColor Yellow
Write-Host "3) Re-run V7 to calculate quant tables" -ForegroundColor Yellow
Write-Host "4) Re-run maturity optimizer to confirm score improvement" -ForegroundColor Yellow
Write-Host ""
Write-Host "Commands are guidance only. This file intentionally does not auto-edit your scripts." -ForegroundColor DarkGray
