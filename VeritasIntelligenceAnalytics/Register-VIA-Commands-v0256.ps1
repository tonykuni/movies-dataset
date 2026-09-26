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
