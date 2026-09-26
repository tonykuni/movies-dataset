# Register-VIA-Commands-v0244.ps1 — +via-akshare（別名 總經對照）。
# 不直呼 python。短令走 Invoke-VIAPython：加速器、家族境、中央入口、逾時。
# 其餘沿用 v0243。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0243.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-akshare {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG110_AKShareProbe_v*.py"
    if (-not $eng) {
        Write-Host "  [via-akshare] ABSENT:VDF_ENG110_AKShareProbe_v*.py 不在這棵樹" -ForegroundColor Yellow
        $global:LASTEXITCODE = 2
        return
    }
    $env:VIA_FROM_VCGC = "YES"
    $py = Get-VIAEnvPython "vdf"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python $py -Family "vdf" -TimeoutSec 1200 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 總經對照 -Value via-akshare -Scope Global -Force
