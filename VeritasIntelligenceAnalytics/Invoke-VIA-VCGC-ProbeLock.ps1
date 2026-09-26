#Requires -Version 7.0
# 19:15 實測鎖定。排在狀態鎖之後。不重抓、不改原鎖、不進母冊。
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:VIA_FROM_VCGC = "YES"
$py = Join-Path (Get-Location) "supportive modules/registry/CGC_MDL193_ProbeLock_v0100.py"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python $py
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $LASTEXITCODE
