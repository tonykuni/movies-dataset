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
# Register-VIA-Commands-v0245.ps1 — +via-pmipair（兩種 PMI）+via-sentiment（CNN 與 AAII）。
# 都走 Invoke-VIAPython。其餘沿用 v0244。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0244.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-pmipair {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG114_PmiPair_v*.py"
    if (-not $eng) { Write-Host "  [via-pmipair] ABSENT:VDF_ENG114_PmiPair_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 900 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
function global:via-sentiment {
    $eng = Get-VIANewest "$VIA\functional modules\VDF\engine" "VDF_ENG115_SentimentFetch_v*.py"
    if (-not $eng) { Write-Host "  [via-sentiment] ABSENT:VDF_ENG115_SentimentFetch_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python (Get-VIAEnvPython "vdf") -Family "vdf" -TimeoutSec 120 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 兩種PMI -Value via-pmipair -Scope Global -Force
Set-Alias -Name 情緒指數 -Value via-sentiment -Scope Global -Force
