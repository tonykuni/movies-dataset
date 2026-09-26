#Requires -Version 7.0
# 兩層美國總體各探一點。沒有 FRED 鑰匙不當成序列死亡。不改樹、不改鎖、不進母冊。
$ErrorActionPreference = "Stop"
Set-Location -LiteralPath (Split-Path -Parent $MyInvocation.MyCommand.Path)
$env:VIA_FROM_VCGC = "YES"
$py = Join-Path (Get-Location) "functional modules/VDF/engine/VDF_ENG110_USMacroProbe_v0101.py"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python $py
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $LASTEXITCODE
