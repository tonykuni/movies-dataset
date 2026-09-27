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
# Register-VIA-Commands-v0256.ps1 — 三頁報告用已註冊的非 OCR 對。先找有 PyMuPDF 或 pypdf 的解譯器。不啟動 OCR。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0255.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vrnreport {
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG110_TabReport_v*.py"
    if (-not $eng) { Write-Host "  [via-vrnreport] ABSENT:VRN_ENG110_TabReport_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    if (-not $env:VIA_VRN_SAMPLES) { $env:VIA_VRN_SAMPLES = "C:\測試樣本報告" }
    $cands = @(Get-VIAEnvPython "vdf"), @(Get-VIAEnvPython "vrn"), @("python")
    $py = $cands[0]
    $pick = "none"
    $seen = @{}
    foreach ($cand in $cands) {
        if (-not $cand -or $seen.ContainsKey($cand)) { continue }
        $seen[$cand] = $true
        & $cand -c "import fitz" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $cand; $pick = "fitz"; break }
        & $cand -c "import pypdf" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $cand; $pick = "pypdf"; break }
    }
    Write-Host ("  [via-vrnreport] " + $pick + " · " + $py) -ForegroundColor DarkCyan
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python $py -Family "vdf" -TimeoutSec 300 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 三頁報告 -Value via-vrnreport -Scope Global -Force
