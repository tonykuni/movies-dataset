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
# Register-VIA-Commands-v0255.ps1 — 三頁報告留在 VDF。第 1 頁走 pdfplumber，不改去找 PyMuPDF。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0254.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vrnreport {
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG110_TabReport_v*.py"
    if (-not $eng) { Write-Host "  [via-vrnreport] ABSENT:VRN_ENG110_TabReport_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    if (-not $env:VIA_VRN_SAMPLES) { $env:VIA_VRN_SAMPLES = "C:\測試樣本報告" }
    $py = Get-VIAEnvPython "vdf"
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python $py -Family "vdf" -TimeoutSec 300 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 三頁報告 -Value via-vrnreport -Scope Global -Force
