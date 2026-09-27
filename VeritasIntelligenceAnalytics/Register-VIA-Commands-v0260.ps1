# Register-VIA-Commands-v0260.ps1 — via-vcgctest 跑完整條 VCGC 自測，不擷取、不推送。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0259.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vcgctest {
    $env:VIA_FROM_VCGC = "YES"
    $env:VIA_VCGC_PUSH = "NO"
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL224_TestAuto_v*.py"
    if (-not $eng) { Write-Host "  [via-vcgctest] FAIL:test tail missing" -ForegroundColor Red; return }
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Family "vrn" $eng
    $code = $LASTEXITCODE
    $page = Join-Path $VIA "VIA_Reports/vcgc/VIA_Test_Matrix_v0100.html"
    if (Test-Path -LiteralPath $page) {
        Write-Host ("  [矩陣] " + $page) -ForegroundColor DarkCyan
        if ($env:OS -eq "Windows_NT") { Start-Process -FilePath $page }
    }
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
    $global:LASTEXITCODE = $code
}
Set-Alias -Name VCGC自測 -Value via-vcgctest -Scope Global -Force
