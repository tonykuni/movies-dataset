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
# Register-VIA-Commands-v0260.ps1 — via-vcgctest 跑完整條 VCGC 自測，不擷取、不推送。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0259.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vcgctest {
    $env:VIA_FROM_VCGC = "YES"
    $env:VIA_VCGC_PUSH = "NO"
    $eng = Get-VIANewest "$VIA\supportive modules\registry" "CGC_MDL224_TestAuto_v*.py"
    if (-not $eng) { Write-Host "  [via-vcgctest] FAIL:test tail missing" -ForegroundColor Red; return }
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Family "vrn" $eng
    $code = $LASTEXITCODE
    $page = Join-Path $VIA "VIA_Reports/vcgc/VIA_Test_Matrix_v0100.html"
    if (Test-Path -LiteralPath $page) {
        Write-Host ("  [矩陣] " + $page) -ForegroundColor DarkCyan
        if ($env:OS -eq "Windows_NT") { Start-Process -FilePath $page }
    }
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
    $global:LASTEXITCODE = $code
}
Set-Alias -Name VCGC自測 -Value via-vcgctest -Scope Global -Force
