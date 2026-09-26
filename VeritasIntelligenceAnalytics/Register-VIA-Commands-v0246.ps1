# Register-VIA-Commands-v0246.ps1 — +via-aaii。試算表才入庫，阻擋頁不寫。其餘沿用 v0245。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0245.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-aaii {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG116_AAIIWorkbook_v*.py"
    if (-not $eng) { Write-Host "  [via-aaii] ABSENT:VDF_ENG116_AAIIWorkbook_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 180 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 散戶情緒 -Value via-aaii -Scope Global -Force
