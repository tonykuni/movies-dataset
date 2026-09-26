#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $env:VIA_VRN_SAMPLES) { $env:VIA_VRN_SAMPLES = "C:\測試樣本報告" }
$reg = Get-ChildItem -LiteralPath $via -Filter "Register-VIA-Commands-v*.ps1" -File | Sort-Object Name | Select-Object -Last 1
if (-not $reg) { Write-Host "  [via-vrnreport] ABSENT:Register-VIA-Commands 不在這棵樹" -ForegroundColor Yellow; exit 2 }
. $reg.FullName
via-vrnreport
exit $global:LASTEXITCODE
