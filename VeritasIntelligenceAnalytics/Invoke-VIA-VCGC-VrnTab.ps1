#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
$reg = Get-ChildItem -LiteralPath $via -Filter "Register-VIA-Commands-v*.ps1" -File | Sort-Object Name | Select-Object -Last 1
if (-not $reg) { Write-Host "  [via-vrntab] ABSENT:Register-VIA-Commands 不在這棵樹" -ForegroundColor Yellow; exit 2 }
. $reg.FullName
via-vrntab
exit $global:LASTEXITCODE
