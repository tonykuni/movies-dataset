# Register-VIA-Commands-v0254.ps1 — 三頁報告：VDF 沒有 PyMuPDF 時改用已能讀報告的 python。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0253.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vrnreport {
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG110_TabReport_v*.py"
    if (-not $eng) { Write-Host "  [via-vrnreport] ABSENT:VRN_ENG110_TabReport_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    if (-not $env:VIA_VRN_SAMPLES) { $env:VIA_VRN_SAMPLES = "C:\測試樣本報告" }
    $py = Get-VIAEnvPython "vdf"
    & $py -c "import fitz" 2>$null
    if ($LASTEXITCODE -ne 0) {
        & python -c "import fitz" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = "python" } else { Write-Host "  [via-vrnreport] VDF 與 python 都沒有 PyMuPDF" -ForegroundColor Yellow }
    }
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python $py -Family "vdf" -TimeoutSec 300 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 三頁報告 -Value via-vrnreport -Scope Global -Force
