# Register-VIA-Commands-v0257.ps1 — -Python 只收字串。v0256 把三個路徑接成陣列，引數轉換失敗。
. (Join-Path $PSScriptRoot "Register-VIA-Commands-v0256.ps1")
$global:VIARegisterPath = $MyInvocation.MyCommand.Path
function global:via-vrnreport {
    $eng = Get-VIANewest "$VIA\functional modules\VRN" "VRN_ENG110_TabReport_v*.py"
    if (-not $eng) { Write-Host "  [via-vrnreport] ABSENT:VRN_ENG110_TabReport_v*.py 不在這棵樹" -ForegroundColor Yellow; $global:LASTEXITCODE = 2; return }
    $env:VIA_FROM_VCGC = "YES"
    if (-not $env:VIA_VRN_SAMPLES) { $env:VIA_VRN_SAMPLES = "C:\測試樣本報告" }
    $cands = New-Object System.Collections.Generic.List[string]
    foreach ($item in @((Get-VIAEnvPython "vdf"), (Get-VIAEnvPython "vrn"), "python")) {
        $text = ""
        if ($null -ne $item) { $text = [string]$item }
        if ($text -and -not $cands.Contains($text)) { [void]$cands.Add($text) }
    }
    if ($cands.Count -eq 0) { $cands.Add("python") }
    $py = [string]$cands[0]
    $pick = "none"
    foreach ($cand in $cands) {
        $cand = [string]$cand
        & $cand -c "import fitz" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $cand; $pick = "fitz"; break }
        & $cand -c "import pypdf" 2>$null
        if ($LASTEXITCODE -eq 0) { $py = $cand; $pick = "pypdf"; break }
    }
    Write-Host ("  [via-vrnreport] " + $pick + " · " + $py) -ForegroundColor DarkCyan
    Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow
    Invoke-VIAPython -Python ([string]$py) -Family "vdf" -TimeoutSec 300 $eng
    Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow
}
Set-Alias -Name 三頁報告 -Value via-vrnreport -Scope Global -Force
