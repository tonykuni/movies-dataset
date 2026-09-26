#Requires -Version 7.0
# 鎖定成功、鎖定紀錄、鎖定路徑。只從 VCGC 進，依序出。不改鎖。
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:VIA_FROM_VCGC = "YES"
$py = Join-Path (Get-Location) "supportive modules/registry/CGC_MDL193_StatusLock_v0101.py"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python $py
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $LASTEXITCODE
