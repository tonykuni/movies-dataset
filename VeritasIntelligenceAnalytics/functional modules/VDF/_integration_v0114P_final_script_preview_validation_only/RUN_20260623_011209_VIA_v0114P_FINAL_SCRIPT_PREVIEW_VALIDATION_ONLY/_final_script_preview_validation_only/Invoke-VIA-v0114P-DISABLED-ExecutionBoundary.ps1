$ErrorActionPreference = "Continue"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114P Disabled Execution Boundary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "[BLOCKED] v0114P is script preview validation only." -ForegroundColor Yellow
Write-Host "[BLOCKED] No execution. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow
Write-Host "PowerShell remains open." -ForegroundColor Cyan
return
