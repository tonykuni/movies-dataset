#Requires -Version 7.0
# AKShare 總經候選。不安裝、不把沒叫到的函數記成同義來源、不改母冊。
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:VIA_FROM_VCGC = "YES"
$py = Join-Path (Get-Location) "functional modules/VDF/engine/VDF_ENG110_AKShareProbe_v0100.py"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python $py
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $LASTEXITCODE
