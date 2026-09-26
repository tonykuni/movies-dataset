# Register-VIA-Commands-v0251.ps1 — +via-managers。只對接三個 System Manager 的自測，不跑 VRN 邏輯。其餘沿用 v0250。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0250.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-managers {
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_SystemManager_v*.py"
    if (-not $eng) { Write-Host "  [via-managers] ABSENT:CGC_SystemManager_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 60 $eng --selftest
    if ($global:LASTEXITCODE -ne 0) { Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow; return }
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 60 $eng
    if ($global:LASTEXITCODE -ne 0) { Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow; return }
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 90 (Join-Path $VIA "functional modules\VDF\VDF_SystemManager_v0105.py") --selftest
    if ($global:LASTEXITCODE -ne 0) { Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow; return }
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 90 (Join-Path $VIA "functional modules\VRN\VRN_SystemManager_v0105.py") --selftest
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 三管理 -Value via-managers -Scope Global -Force
