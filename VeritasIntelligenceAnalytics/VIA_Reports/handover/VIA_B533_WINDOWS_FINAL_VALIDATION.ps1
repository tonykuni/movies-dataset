[CmdletBinding()]
param(
    [string]$RepositoryRoot = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset',
    [switch]$SkipPull,
    [switch]$IncludeQuantGuardStatus
)

$ErrorActionPreference = 'Stop'
$Branch = 'claude/via-envmanager-governance-7cls8h'
$VIA = Join-Path $RepositoryRoot 'VeritasIntelligenceAnalytics'
$LogDir = Join-Path $VIA 'VIA_Reports\handover'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$Log = Join-Path $LogDir ("windows_final_validation_{0}.txt" -f $Stamp)

if (-not (Test-Path -LiteralPath $VIA)) {
    throw "找不到 VIA 根目錄：$VIA"
}
Set-Location -LiteralPath $VIA

Write-Host '=== VIA B533 · Windows Final Validation ===' -ForegroundColor Cyan
Write-Host "VIA=$VIA"
Write-Host "Branch=$Branch"

$currentBranch = (git branch --show-current).Trim()
if ($currentBranch -ne $Branch) {
    throw "目前分支為 '$currentBranch'，不是 '$Branch'。請切換到指定分支後重跑。"
}

$trackedDirty = @(git status --porcelain | Where-Object { $_ -notmatch '^\?\? ' })
if ($trackedDirty.Count -gt 0) {
    Write-Host '工作樹有已追蹤的未提交變更，為避免覆蓋而停止：' -ForegroundColor Yellow
    $trackedDirty | ForEach-Object { Write-Host $_ }
    throw '請先人工處理已追蹤變更，再執行最終驗證。'
}

$untracked = @(git status --porcelain | Where-Object { $_ -match '^\?\? ' })
if ($untracked.Count -gt 0) {
    Write-Host '注意：工作樹有未追蹤檔案；不自動刪除，先繼續 pull。' -ForegroundColor Yellow
    $untracked | ForEach-Object { Write-Host $_ }
}

if (-not $SkipPull) {
    Write-Host '--- Git pull --ff-only ---' -ForegroundColor Cyan
    git pull --ff-only origin $Branch
    if ($LASTEXITCODE -ne 0) { throw 'git pull --ff-only 失敗。' }
}

$head = (git rev-parse HEAD).Trim()
$remote = (git ls-remote origin ("refs/heads/{0}" -f $Branch) | ForEach-Object { ($_ -split '\s+')[0] } | Select-Object -First 1).Trim()
Write-Host "HEAD=$head" -ForegroundColor Cyan
Write-Host "REMOTE=$remote" -ForegroundColor Cyan
if ($head -ne $remote) { throw '本地 HEAD 與遠端分支不一致。' }

. (Join-Path $VIA 'Register-VIA-Commands-v0208.ps1')
$env:VIA_NO_OPEN = '1'
$env:VIA_NET_CONSENT = 'OFF'
$env:VIA_SCRAPE_CONSENT = 'OFF'

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
Start-Transcript -Path $Log -Force | Out-Null

function Assert-VIAExitCode([string]$Name) {
    if ($global:LASTEXITCODE -ne 0) {
        throw "$Name 失敗，return code=$global:LASTEXITCODE"
    }
}

try {
    Write-Host '--- Environment paths ---' -ForegroundColor Cyan
    via-envpy core
    via-envpy vrn
    via-envpy vdf

    Write-Host '--- B531 25-accelerator probe ---' -ForegroundColor Cyan
    $probe = Join-Path $VIA 'VIA_Reports\handover\VIA_B531_25_ACCELERATOR_CONTROL.ps1'
    if (-not (Test-Path -LiteralPath $probe)) { throw "找不到 B531 probe：$probe" }
    if ($IncludeQuantGuardStatus) {
        & $probe -RunQuantGuardStatus
    } else {
        & $probe
    }
    Assert-VIAExitCode 'B531 accelerator probe'

    Write-Host '--- CGC157 unique-entry check ---' -ForegroundColor Cyan
    via-unique-check
    Assert-VIAExitCode 'CGC157 unique-entry check'

    Write-Host '--- VIA central VRN ---' -ForegroundColor Cyan
    via-central vrn -SelfTest
    Assert-VIAExitCode 'VIA central VRN'

    Write-Host '--- VIA central VDF ---' -ForegroundColor Cyan
    via-central vdf -SelfTest
    Assert-VIAExitCode 'VIA central VDF'

    Write-Host '--- VIA central QuantGuard ---' -ForegroundColor Cyan
    via-central quantguard -SelfTest
    Assert-VIAExitCode 'VIA central QuantGuard'

    Write-Host '--- Interface contract read-only sync ---' -ForegroundColor Cyan
    via-iface sync
    Assert-VIAExitCode 'CGC054 interface sync'

    Write-Host ''
    Write-Host '[PASS] VIA B533 Windows final validation completed.' -ForegroundColor Green
    Write-Host '[POLICY] Network OFF; operator consent unchanged; QuantGuard-only; TA-Lib forbidden.' -ForegroundColor Yellow
    Write-Host "TRANSCRIPT=$Log" -ForegroundColor Cyan
}
finally {
    Stop-Transcript | Out-Null
}
