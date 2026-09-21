<#
VIA_B535_PANORAMA_ALL_IN_ONE.ps1 — 批535 一貼即用:進環境 → 25 加速器 → 全景式分析(AST 精準/彈性定位)
→ 顯示所有問題類型與位置 → 能同時修的同時修、不能同時修的順序修(不傷系統、零九頭龍)
→ 動態進度條 → 自動跳出多 TAB 矩陣報告(TAB1 給 AI 與你,內附 JSON/MD;TAB2 起逐項測試結果;紅黃綠燈、分系統分範疇)

用法(PowerShell 7,VIA 根目錄):
    .\VIA_B535_PANORAMA_ALL_IN_ONE.ps1                 # 乾跑:只看問題,不寫檔
    .\VIA_B535_PANORAMA_ALL_IN_ONE.ps1 -Apply          # 實修(加速器橋/網路工具橋/自測動詞;純增量)
    .\VIA_B535_PANORAMA_ALL_IN_ONE.ps1 -Apply -Fast    # 實修 + 快測(每站 300s 上限)
    .\VIA_B535_PANORAMA_ALL_IN_ONE.ps1 -SkipPull       # 不 pull(本地已是最新)

政策:網路預設 OFF、不代設同意閘、不代裝任何套件;收容件/退役夾零觸碰;TA-Lib 禁用(L50,QuantGuard 為唯一活動路徑)。
#>
[CmdletBinding()]
param(
    [string]$RepositoryRoot = 'C:\Users\tonyk\OneDrive\Documents\movies-dataset',
    [switch]$Apply,
    [switch]$Fast,
    [switch]$SkipPull,
    [switch]$NoOpen,
    [int]$Workers = 0
)
# ===== [VIA:PS-ACCEL:v0101] PS 25 加速器橋(B531 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$ErrorActionPreference = 'Stop'
$Branch = 'claude/via-envmanager-governance-7cls8h'
$VIA = Join-Path $RepositoryRoot 'VeritasIntelligenceAnalytics'
$Stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

# ── ① 進入環境 ────────────────────────────────────────────────────────────────
Write-Host ''
Write-Host '=== VIA B535 · 全景稽核修復 · 一貼式 ===' -ForegroundColor Cyan
if (-not (Test-Path -LiteralPath $VIA)) { throw "找不到 VIA 根目錄:$VIA" }
Set-Location -LiteralPath $VIA
Write-Host ("  VIA    = {0}" -f $VIA)

$cur = (git branch --show-current).Trim()
if ($cur -ne $Branch) { Write-Host ("  [注意] 目前分支 {0} ≠ {1};繼續但不 pull" -f $cur, $Branch) -ForegroundColor Yellow; $SkipPull = $true }
if (-not $SkipPull) {
    $dirty = @(git status --porcelain | Where-Object { $_ -notmatch '^\?\? ' })
    if ($dirty.Count -gt 0) {
        Write-Host '  [注意] 工作樹有已追蹤變更 → 不自動 pull(避免覆蓋你的東西):' -ForegroundColor Yellow
        $dirty | Select-Object -First 8 | ForEach-Object { Write-Host "    $_" }
    } else {
        git pull --ff-only origin $Branch | Out-Null
        Write-Host ("  pull   = OK · HEAD {0}" -f (git rev-parse --short HEAD))
    }
}

$book = Get-ChildItem (Join-Path $VIA 'Register-VIA-Commands-v*.ps1') | Sort-Object Name | Select-Object -Last 1
. $book.FullName | Out-Null
Write-Host ("  命令冊 = {0}" -f $book.Name)
$env:VIA_NET_CONSENT = 'OFF'; $env:VIA_SCRAPE_CONSENT = 'OFF'     # 網路預設關;要開是你的手
if ($NoOpen) { $env:VIA_NO_OPEN = '1' }

# 家族境 python(匯流排正主解析;缺境=base 退路,誠實印出)
function Get-VIAFamPython([string]$fam) {
    try { $p = (Get-VIAEnvPython $fam); if ($p -and (Test-Path -LiteralPath $p)) { return $p } } catch { }
    return 'python'
}
$pyCore = Get-VIAFamPython 'core'
Write-Host ("  境     = core:{0}" -f $pyCore)

# ── ② 25 加速器 ──────────────────────────────────────────────────────────────
$accelN = 0
$probe = Join-Path $VIA 'VIA_Reports\handover\VIA_B531_25_ACCELERATOR_CONTROL.ps1'
if (Test-Path -LiteralPath $probe) {
    try { & $probe | Out-Null } catch { Write-Host "  [加速器] probe 略過:$($_.Exception.Message)" -ForegroundColor DarkYellow }
}
$accelJson = Join-Path $VIA 'VIA_Reports\accelerator\VIA_ACCELERATOR_CONTROL_latest.json'
$ctl = Get-ChildItem (Join-Path $VIA 'supportive modules\registry\CGC_MDL156_VIAAcceleratorControl_v*.py') -EA SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if ($ctl) { & $pyCore $ctl.FullName --selftest | Out-Null }
if (Test-Path -LiteralPath $accelJson) {
    try { $accelN = [int](Get-Content -LiteralPath $accelJson -Raw | ConvertFrom-Json).roster_count } catch { $accelN = 0 }
}
Write-Host ("  加速器 = {0} 項名冊(平行工人上限;CGC_MDL156)" -f $accelN) -ForegroundColor Green

# ── ③ 全景稽核 + 修復 + 實測(動態進度條) ────────────────────────────────────
$eng = Get-ChildItem (Join-Path $VIA 'supportive modules\registry\CGC_MDL158_VIAPanoramaAuditRepair_v*.py') | Sort-Object Name | Select-Object -Last 1
if (-not $eng) { throw '找不到 CGC_MDL158 全景稽核修復正主' }
$argsList = @($eng.FullName, 'all')
if ($Apply) { $argsList += '--apply' }
if ($Fast) { $argsList += '--fast' }
if (-not $NoOpen) { $argsList += '--open' }
if ($Workers -gt 0) { $argsList += @('--workers', "$Workers") }

Write-Host ''
Write-Host ("  正主   = {0} · 模式 {1}" -f $eng.Name, $(if ($Apply) { '實修' } else { '乾跑(加 -Apply 才寫檔)' })) -ForegroundColor Cyan
$log = Join-Path $VIA ("VIA_Reports\panorama_audit\run_{0}.log" -f $Stamp)
New-Item -ItemType Directory -Path (Split-Path $log) -Force | Out-Null

$t0 = Get-Date
$tail = New-Object System.Collections.Generic.List[string]
& $pyCore @argsList 2>&1 | ForEach-Object {
    $line = "$_"
    Add-Content -LiteralPath $log -Value $line
    if ($line -match '^@@PROGRESS\|([\d.]+)\|(.*)$') {
        $pct = [double]$Matches[1]; $msg = $Matches[2]
        $el = [int]((Get-Date) - $t0).TotalSeconds
        Write-Progress -Activity 'VIA 全景稽核修復' -Status ("{0}  ·  已跑 {1}s" -f $msg, $el) -PercentComplete $pct
    } else {
        $tail.Add($line)
        if ($line -match '^\s*\[|^===|^\s*\[計\]') { Write-Host "  $line" }
    }
}
$rc = $LASTEXITCODE
Write-Progress -Activity 'VIA 全景稽核修復' -Completed

# ── ④ 多 TAB 矩陣報告(自動跳出) ─────────────────────────────────────────────
$rep = Join-Path $VIA 'VIA_Reports\panorama_audit\PANORAMA_AUDIT_latest.html'
$jsn = Join-Path $VIA 'VIA_Reports\panorama_audit\PANORAMA_AUDIT_latest.json'
if (Test-Path -LiteralPath $jsn) {
    $d = Get-Content -LiteralPath $jsn -Raw | ConvertFrom-Json
    $lamp = @{ GREEN = 'Green'; YELLOW = 'Yellow'; RED = 'Red' }[$d.verdict]
    Write-Host ''
    Write-Host ('=== 裁決 {0} · 掃 {1} 檔(活樹)· 問題 {2} · 自動修 {3} 處 · 實測 {4} ===' -f `
        $d.verdict, $d.scan.files_scanned, $d.scan.issues, (($d.fix.applied_by_class.PSObject.Properties | Measure-Object -Property Value -Sum).Sum), $d.tests.verdict) -ForegroundColor $(if ($lamp) { $lamp } else { 'Gray' })
    foreach ($k in $d.scan.by_class.PSObject.Properties) {
        Write-Host ('   {0,-9} {1,5}' -f $k.Name, $k.Value)
    }
    Write-Host ('   加速器橋 {0}% · VDF 網路工具 {1}%' -f $d.coverage.accel_pct, $d.coverage.net_pct)
    Write-Host ('   報告 HTML = {0}' -f $rep) -ForegroundColor Cyan
    Write-Host ('   報告 JSON = {0}' -f $jsn) -ForegroundColor DarkCyan
    Write-Host ('   報告 MD   = {0}' -f (Join-Path $VIA 'VIA_Reports\panorama_audit\PANORAMA_AUDIT_latest.md')) -ForegroundColor DarkCyan
}
if ((Test-Path -LiteralPath $rep) -and (-not $NoOpen)) {
    try { Start-Process $rep } catch { Write-Host "  [開頁] 手動開:$rep" -ForegroundColor Yellow }
}
Write-Host ''
Write-Host '[政策] 網路 OFF · 不代設同意閘 · 不代裝套件 · 收容件/退役夾零觸碰 · TA-Lib 禁用(QuantGuard 唯一活動路徑)' -ForegroundColor DarkYellow
Write-Host ("[紀錄] {0}" -f $log) -ForegroundColor DarkGray
exit $rc
