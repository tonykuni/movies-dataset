#Requires -Version 7.0
# One pass over the VCGC selftests. No fetch. No GitHub push.
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath (Split-Path -Parent $via)
$env:VIA_FROM_VCGC = "YES"
$env:VIA_VCGC_PUSH = "NO"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python (Join-Path $via "supportive modules/registry/CGC_MDL224_TestAuto_v0100.py")
$code = $LASTEXITCODE
$page = Join-Path $via "VIA_Reports/vcgc/VIA_Test_Matrix_v0100.html"
if (Test-Path -LiteralPath $page) {
    Write-Host ("  [矩陣] " + $page) -ForegroundColor DarkCyan
    if ($env:OS -eq "Windows_NT") { Start-Process -FilePath $page }
}
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $code
