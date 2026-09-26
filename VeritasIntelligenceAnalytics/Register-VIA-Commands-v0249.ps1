# Register-VIA-Commands-v0249.ps1 — +via-export。輸入與資料庫勾選後，只出局部 CSV/JSON/MD。其餘沿用 v0248。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0248.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-export {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG118_ExportDesk_v*.py"
    if (-not $eng) { Write-Host "  [via-export] ABSENT:VDF_ENG118_ExportDesk_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 180 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 局部輸出 -Value via-export -Scope Global -Force
