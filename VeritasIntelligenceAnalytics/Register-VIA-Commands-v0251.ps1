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
