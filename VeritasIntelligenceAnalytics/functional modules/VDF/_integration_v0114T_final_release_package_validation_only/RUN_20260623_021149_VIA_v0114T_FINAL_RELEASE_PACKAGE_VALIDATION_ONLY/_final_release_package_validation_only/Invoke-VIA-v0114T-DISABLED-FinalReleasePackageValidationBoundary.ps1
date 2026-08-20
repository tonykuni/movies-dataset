$ErrorActionPreference = "Continue"
Write-Host ""
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "def VIA · v0114T Disabled Final Release Package Validation Boundary" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor DarkCyan
Write-Host "[BLOCKED] v0114T is final release package validation only." -ForegroundColor Yellow
Write-Host "[BLOCKED] No execution. No apply. No source mutation. No canonical merge. No DB write." -ForegroundColor Yellow
Write-Host "PowerShell remains open." -ForegroundColor Cyan
return
