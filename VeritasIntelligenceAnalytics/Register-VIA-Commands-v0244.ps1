# CELERITAS-TEMPLATE-JOIN v1
#Requires -Version 7.0
# ===== [VIA:PS-TEMPLATE:v0100] Celeritas 模板章(L102 ②;不包裹接法 L103 ③:不 cd、不動 param()、只動 $PID、關閉即還原;模板 StrictMode 不外溢) =====
try {
    $VIACelProbe = $PSScriptRoot
    while ($VIACelProbe -and (Split-Path $VIACelProbe -Parent)) {
        $VIACelPS7 = Join-Path $VIACelProbe 'supportive modules\ps7\VeritasCeleritas.PS7.ps1'
        if (Test-Path -LiteralPath $VIACelPS7) { . $VIACelPS7 -RestoreOnly; break }
        $VIACelProbe = Split-Path $VIACelProbe -Parent
    }
    Set-StrictMode -Off
    if (Get-Command Restore-CeleritasPS7 -ErrorAction SilentlyContinue) {
        if (-not (Get-EventSubscriber -SourceIdentifier PowerShell.Exiting -ErrorAction SilentlyContinue)) { $null = Register-EngineEvent -SourceIdentifier PowerShell.Exiting -Action { try { Restore-CeleritasPS7 } catch { } } }
        # 短令冊只載函式;加速由各短令自己 Start/Restore
    }
} catch { }
# ===== [VIA:PS-TEMPLATE:END] =====
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
