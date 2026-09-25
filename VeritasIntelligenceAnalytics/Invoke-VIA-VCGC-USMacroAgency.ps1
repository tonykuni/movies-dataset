#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$env:VIA_FROM_VCGC = "YES"
$py = Join-Path $here "functional modules/VDF/engine/VDF_ENG111_USMacroAgency_v0100.py"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python $py
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $LASTEXITCODE
