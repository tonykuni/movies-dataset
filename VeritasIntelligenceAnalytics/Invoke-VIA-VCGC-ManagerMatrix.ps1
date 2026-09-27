#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath (Split-Path -Parent $via)
$env:VIA_FROM_VCGC = "YES"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python (Join-Path $via "supportive modules/registry/CGC_SystemManager_v0106.py") matrix
$code = $LASTEXITCODE
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $code
