# Register-VIA-Commands-v0248.ps1 — +via-vdfmatrix。只讀下載矩陣，不抓數、不改母冊。其餘沿用 v0247。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0247.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vdfmatrix {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL195_FetchMatrix_v*.py"
    if (-not $eng) { Write-Host "  [via-vdfmatrix] ABSENT:CGC_MDL195_FetchMatrix_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 60 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 下載矩陣 -Value via-vdfmatrix -Scope Global -Force
