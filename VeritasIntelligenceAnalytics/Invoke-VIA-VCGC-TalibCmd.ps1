# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
$eng = Join-Path $via "supportive modules\registry\CGC_MDL243_TalibCommandScan_v0100.py"
if (-not (Test-Path -LiteralPath $eng)) {
    Write-Host "  [talib-cmd] ABSENT: $eng" -ForegroundColor Yellow
    exit 2
}
$env:VIA_FROM_VCGC = "YES"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
python $eng
$code = $LASTEXITCODE
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $code
