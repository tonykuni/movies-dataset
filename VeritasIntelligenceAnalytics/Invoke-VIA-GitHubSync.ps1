$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $root
$env:VIA_FROM_VCGC = "YES"
$py = Join-Path $PSScriptRoot "supportive modules\registry\CGC_MDL189_GitHubSyncEngine_v0100.py"
$raw = python $py --mode compress-only --local-dir "VeritasIntelligenceAnalytics\supportive modules\registry" --limit 40
$on = $false
foreach ($line in $raw) {
    if ($line -eq "BEGIN_PASTE") { $on = $true; Write-Host "======== 只貼黃色 ========" -ForegroundColor Yellow; continue }
    if ($line -eq "END_PASTE") { Write-Host "======== 黃色到此 ========" -ForegroundColor Yellow; continue }
    if ($on) { Write-Host $line -ForegroundColor Yellow }
}
