# Register-VIA-Commands-v0247.ps1 — +via-fwdvintage。VDF 引擎自測，不改母冊、不套 registry。其餘沿用 v0246。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0246.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-fwdvintage {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG117_ForwardVintageDoor_v*.py"
    if (-not $eng) { Write-Host "  [via-fwdvintage] ABSENT:VDF_ENG117_ForwardVintageDoor_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 180 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 前瞻估值 -Value via-fwdvintage -Scope Global -Force
