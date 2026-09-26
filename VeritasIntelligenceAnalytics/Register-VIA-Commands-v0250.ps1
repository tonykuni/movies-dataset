# Register-VIA-Commands-v0250.ps1 — +via-deck。全景缺口與左右頁準備。不抓數、不推 GitHub。其餘沿用 v0249。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0249.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-deck {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL196_RouteDeck_v*.py"
    if (-not $eng) { Write-Host "  [via-deck] ABSENT:CGC_MDL196_RouteDeck_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 60 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 對接準備 -Value via-deck -Scope Global -Force
