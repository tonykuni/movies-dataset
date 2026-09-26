# Register-VIA-Commands-v0252.ps1 — +via-vrntab。只測連結與驗證閘，不讀報告。其餘沿用 v0251。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0251.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vrntab {
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG109_TabStore_v*.py"
    if (-not $eng) { Write-Host "  [via-vrntab] ABSENT:VRN_ENG109_TabStore_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 90 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 三頁入庫 -Value via-vrntab -Scope Global -Force
