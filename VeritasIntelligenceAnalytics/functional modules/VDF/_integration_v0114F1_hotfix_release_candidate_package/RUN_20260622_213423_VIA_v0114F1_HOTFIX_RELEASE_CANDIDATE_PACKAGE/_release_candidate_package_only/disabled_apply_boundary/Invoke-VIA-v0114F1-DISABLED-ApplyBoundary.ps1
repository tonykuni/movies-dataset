$ErrorActionPreference = "Continue"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114F1 Release Candidate Package · Disabled Apply Boundary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "[BLOCKED] Package only. Apply is disabled." -ForegroundColor Yellow
Write-Host "[BLOCKED] No source mutation." -ForegroundColor Yellow
Write-Host "[BLOCKED] No canonical merge." -ForegroundColor Yellow
Write-Host "[BLOCKED] No DB write." -ForegroundColor Yellow
Write-Host "PowerShell remains open." -ForegroundColor Cyan
return
