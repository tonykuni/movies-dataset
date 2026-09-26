#Requires -Version 7.0
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath (Split-Path -Parent $via)
$env:VIA_FROM_VCGC = "YES"
$engine = Join-Path $via "functional modules/VRN/references/intake/VIA_NLP_OneEngine_v1_9_0/VIA_NLP_OneEngine_v1_9_0.py"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python (Join-Path $via "supportive modules/registry/CGC_MDL197_NlpOneEngine_v0100.py")
if ($LASTEXITCODE -ne 0) {
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
    exit $LASTEXITCODE
}
& python $engine health
$code = $LASTEXITCODE
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $code
