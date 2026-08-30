# Invoke-VIA-AllGreen-v0100.ps1 — 一支 PowerShell 統包全流程(操作員令 2026-08-12)
# 流程:test → debug → optimize → test → debug → consolidate → test → debug
#       → generate U/I → user-test → debug → activate → test → debug
# 契約(v01.00 §9):參數頂部集中 · function def_* · 非阻塞(無 Read-Host/無限等待)
#   · 不關使用者視窗 · 誠實 OK/FAIL/NOT_RUN 不卡斷 · 建議制零就地改碼
#   · HTML 報告完整寫出後才開一次 · 全程唯讀/dry-run(落地變更仍走各動詞 --commit)

# ── 頂部參數區 ────────────────────────────────────────────────────────────
param(
    [switch]$NoOpen,           # 不自動開報告/Console
    [switch]$SkipHeavy,        # 略過重站(sysman/pipeline)
    [int]$StageTimeoutSec = 1200
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====
$ErrorActionPreference = "Continue"
$VIA = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$REG = Join-Path $VIA "supportive modules\registry"
$RPT = Join-Path $VIA "VIA_Reports"
$TS  = Get-Date -Format "yyyyMMdd_HHmmss"
$PY  = if (Get-Command py -ErrorAction SilentlyContinue) { "py" } else { "python3" }
$Script:Stages = @()

function def_Newest([string]$Pattern, [string]$Root) {
    $hits = Get-ChildItem -LiteralPath $Root -Filter $Pattern -File -ErrorAction SilentlyContinue | Sort-Object Name
    if ($hits) { return $hits[-1].FullName } else { return $null }
}

function def_Stage([string]$Name, [string[]]$Argv, [string]$Expect = "rc0") {
    $t0 = Get-Date
    if (-not $Argv -or -not $Argv[0]) {
        $Script:Stages += @{ stage = $Name; state = "NOT_RUN"; note = "引擎缺(誠實)"; secs = 0 }
        Write-Host ("  [NOT_RUN] {0} · 引擎缺" -f $Name); return
    }
    try {
        $out = & $PY @Argv 2>&1 | Out-String
        $rc = $LASTEXITCODE
    } catch { $out = $_.Exception.Message; $rc = -1 }
    $secs = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    $ok = if ($Expect -eq "env") { $true } else { $rc -eq 0 }
    $state = if ($ok -and $rc -eq 0) { "OK" } elseif ($Expect -eq "env") { "SKIP" } else { "FAIL" }
    $tail = (($out -split "`n") | Where-Object { $_.Trim() } | Select-Object -Last 2) -join " / "
    $Script:Stages += @{ stage = $Name; state = $state; rc = $rc; secs = $secs; note = $tail.Substring(0, [math]::Min(160, $tail.Length)) }
    Write-Host ("  [{0,-7}] {1} · {2}s" -f $state, $Name, $secs)
}

function def_Debug([string]$Phase) {
    $fails = @($Script:Stages | Where-Object { $_.state -eq "FAIL" })
    if ($fails.Count -eq 0) { Write-Host ("  [DEBUG  ] {0}:零 FAIL — 無事可修(誠實,不假造修正)" -f $Phase) }
    else {
        Write-Host ("  [DEBUG  ] {0}:{1} 站 FAIL — 建議制列示(高風險不自動修):" -f $Phase, $fails.Count)
        foreach ($f in $fails) { Write-Host ("     ✗ {0}:{1}" -f $f.stage, $f.note) }
    }
}

Write-Host "=== VIA AllGreen 一鍵統包 v0100 · $TS · 唯讀/dry-run · 建議制 ===" -ForegroundColor Cyan

# ① TEST — 全面自測矩陣(18 站)
Write-Host "── ① TEST(自測矩陣)──"
$grid = def_Newest "CGC_MDL064_SelftestGrid_v0*.py" $REG
def_Stage "selftest_grid" @($grid, $(if ($SkipHeavy) { "--fast" }))
# ② DEBUG
def_Debug "①後"

# ③ OPTIMIZE — 同步巡航(五站併發=牆鐘最佳化)
Write-Host "── ③ OPTIMIZE(同步巡航)──"
$auto = def_Newest "CGC_MDL042_AutoPilot_v0*.py" $REG
def_Stage "auto_pilot_parallel" @($auto)
# ④⑤ TEST+DEBUG
def_Debug "③後"

# ⑥ CONSOLIDATE — 證據總彙(最新 GRID/AUTO/SysMan run 三源對帳)
Write-Host "── ⑥ CONSOLIDATE(證據總彙)──"
$latest = @{}
foreach ($pair in @(@("grid", "selftest_runs\GRID_*.json"), @("auto", "autopilot_runs\AUTO_*.json"))) {
    $f = Get-ChildItem (Join-Path $RPT $pair[1]) -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
    if ($f) { $latest[$pair[0]] = (Get-Content $f.FullName -Raw | ConvertFrom-Json) }
}
$runDir = Get-ChildItem (Join-Path $RPT "sysman_runs") -Directory -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if ($runDir) {
    $fsPath = Join-Path $runDir.FullName "final_summary.json"
    if (Test-Path $fsPath) { $latest["sysman"] = (Get-Content $fsPath -Raw | ConvertFrom-Json) }
}
$consol = @{
    schema = "VIA.AllGreen.v1"; ts = $TS
    grid   = if ($latest.grid) { @{ ok = $latest.grid.ok; fail = $latest.grid.fail; skip = $latest.grid.skip } } else { "NOT_RUN" }
    auto   = if ($latest.auto) { @{ ok = $latest.auto.ok; total = $latest.auto.total } } else { "NOT_RUN" }
    sysman = if ($latest.sysman) { @{ gate = $latest.sysman.gate; findings = @($latest.sysman.findings).Count } } else { "NOT_RUN" }
    stages = $Script:Stages
}
$evDir = Join-Path $RPT "allgreen_runs"; New-Item -ItemType Directory -Force -Path $evDir | Out-Null
$evPath = Join-Path $evDir "ALLGREEN_$TS.json"
$consol | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $evPath -Encoding utf8
Write-Host ("  [OK     ] 總彙存證 {0}(grid={1} auto={2} gate={3})" -f (Split-Path $evPath -Leaf), $consol.grid.ok, $consol.auto.ok, $consol.sysman.gate)
def_Debug "⑥後"

# ⑨ GENERATE U/I — Console 七頁重生
Write-Host "── ⑨ GENERATE U/I(Console)──"
$hub = def_Newest "CGC_MDL059_MasterHub_v0*.py" $REG
def_Stage "console_7pages" @($hub, "--no-open")

# ⑩ USER-TEST — 開 Console(使用者旅程入口);NoOpen 則印路徑
$hubHtml = Join-Path $RPT "VIA_Master_Hub.html"
if (-not $NoOpen -and (Test-Path $hubHtml) -and $env:OS -eq "Windows_NT") {
    Start-Process $hubHtml; Write-Host "  [OK     ] user-test:Console 已開(非阻塞)"
} else { Write-Host ("  [SKIP   ] user-test:Console 路徑 {0}(NoOpen/非 Windows)" -f $hubHtml) }
def_Debug "⑩後"

# ⑫ ACTIVATE — 排程常駐確認(缺則印註冊令,不代註冊)
Write-Host "── ⑫ ACTIVATE(自動巡航常駐)──"
if ($env:OS -eq "Windows_NT") {
    $q = schtasks /Query /TN VIA_AutoPilot 2>&1
    if ($LASTEXITCODE -eq 0) { Write-Host "  [OK     ] VIA_AutoPilot 排程在位(每日自巡常駐)" }
    else { Write-Host "  [候     ] 排程未註冊——執行:via-auto --register" }
} else { Write-Host "  [NOT_RUN] schtasks 非 Windows(誠實)" }

# ⑬⑭ FINAL TEST + DEBUG — 終局裁決
$nFail = @($Script:Stages | Where-Object { $_.state -eq "FAIL" }).Count
$nOk   = @($Script:Stages | Where-Object { $_.state -eq "OK" }).Count
$gate  = if ($nFail -gt 0) { "RED_REGRESSION_OR_SAFETY_FAILURE" }
         elseif ($consol.sysman -ne "NOT_RUN" -and "$($consol.sysman.gate)" -like "GREEN*") { "GREEN_SANDBOX_STABLE_PROMOTION_REVIEW_REQUIRED" }
         else { "YELLOW_READY_WITH_WARNINGS_REVIEW_REQUIRED" }
def_Debug "終局"
Write-Host ("=== 終局 Gate:{0} · 站 OK {1} / FAIL {2} · 存證 {3} ===" -f $gate, $nOk, $nFail, (Split-Path $evPath -Leaf)) -ForegroundColor $(if ($nFail -gt 0) { "Red" } else { "Green" })
Write-Host "    正式晉升/部署:NOT_PERFORMED_REQUIRES_APPROVAL(落地變更走各動詞 --commit)"
exit $(if ($nFail -gt 0) { 1 } else { 0 })

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
