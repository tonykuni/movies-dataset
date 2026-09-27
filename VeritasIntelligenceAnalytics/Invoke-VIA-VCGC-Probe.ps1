#Requires -Version 7.0
# The only pop. A command that came through VCGC calls this after it finishes.
$ErrorActionPreference = "Stop"
$via = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -LiteralPath (Split-Path -Parent $via)
$env:VIA_FROM_VCGC = "YES"
Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
& python (Join-Path $via "supportive modules/registry/CGC_MDL222_SubsystemProbe_v0100.py")
$code = $LASTEXITCODE
$page = Join-Path $via "VIA_Reports/vcgc/VIA_Subsystem_Matrix_v0100.html"
if (Test-Path -LiteralPath $page) {
    Write-Host ("  [矩陣] " + $page) -ForegroundColor DarkCyan
    if ($env:OS -eq "Windows_NT") { Start-Process -FilePath $page }
}
Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
exit $code
