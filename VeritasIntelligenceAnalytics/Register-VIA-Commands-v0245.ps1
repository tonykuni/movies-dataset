# Register-VIA-Commands-v0245.ps1 — +via-pmipair（兩種 PMI）+via-sentiment（CNN 與 AAII）。
# 都走 Invoke-VIAPython。其餘沿用 v0244。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0244.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-pmipair {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG114_PmiPair_v*.py"
    if (-not $eng) { Write-Host "  [via-pmipair] ABSENT:VDF_ENG114_PmiPair_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 900 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
function global:via-sentiment {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG115_SentimentFetch_v*.py"
    if (-not $eng) { Write-Host "  [via-sentiment] ABSENT:VDF_ENG115_SentimentFetch_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 120 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 兩種PMI -Value via-pmipair -Scope Global -Force
Set-Alias -Name 情緒指數 -Value via-sentiment -Scope Global -Force
