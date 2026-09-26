#Requires -Version 7.0
# 不直呼 python。路徑由這支腳本自己解，不看目前目錄。
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
$reg = Get-ChildItem -LiteralPath $via -Filter "Register-VIA-Commands-v*.ps1" -File |
    Sort-Object Name | Select-Object -Last 1
if (-not $reg) { Write-Host "  [via-akshare] ABSENT:Register-VIA-Commands 不在這棵樹" -ForegroundColor Yellow; exit 2 }
. $reg.FullName
via-akshare
exit $global:LASTEXITCODE
