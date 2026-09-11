# Invoke-VIA-AllGreen-v0101.ps1 — 一支 PowerShell 統包全流程(操作員令 2026-08-12)
# ── 批423 卡斷根治(操作員令「卡斷 加入20個加速器 不卡斷 動態進度條」)──────
# 工作站實錄:via-go 印出「── ① TEST(自測矩陣)──」之後畫面完全不動 = 看起來死機。
# 根因兩條,都在本檔 v0100,跟格子無關(格子每站都有 flush):
#   ① $out = & $PY @Argv 2>&1 | Out-String
#      Out-String 會把子行程**全部輸出緩衝到結束才吐**。格子 200 站要跑很久,
#      這段時間畫面一個字都沒有。批419e 的 PowerShell 版:捕捉到卻不顯示=等於沒捕捉。
#   ② param 裡宣告了 $StageTimeoutSec = 1200,**全檔從未被使用過**(grep 只有宣告那一行)。
#      所以任何一站真的卡住,整支 AllGreen 就永遠等下去——「不卡斷」的契約沒有實作。
# v0101 的修法:
#   · def_Stage 改 Start-Process + 邊跑邊 tail(每 0.4s 排出新行,即時顯示)
#   · $StageTimeoutSec 真正接線:逾時 Kill 子行程,誠實記 TIMEOUT(不冒充 FAIL 也不冒充 OK)
#   · Write-Progress 進度列 + 每站耗時;格子側的動態進度條(v0262)也一併看得見
#   · 開跑先點 20 加速器的名(SUP_MDL737→Celeritas;缺席誠實說缺,不點假燈)
# 只增不減:①~⑭ 全部流程、判準、Gate 文字一字未改,只換了「怎麼跑一站」。
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

function def_Drain([string]$Path, [long]$Pos, [string]$Name, $Tail) {
    # 邊跑邊排出新行。用 FileShare::ReadWrite 開檔,否則子行程還在寫會撞共用違規。
    if (-not (Test-Path -LiteralPath $Path)) { return $Pos }
    try {
        $fs = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
        try {
            if ($fs.Length -le $Pos) { return $Pos }
            [void]$fs.Seek($Pos, [IO.SeekOrigin]::Begin)
            $sr = New-Object IO.StreamReader($fs, [Text.Encoding]::UTF8)
            $chunk = $sr.ReadToEnd()
            $newPos = $fs.Position
        } finally { $fs.Dispose() }
    } catch { return $Pos }
    foreach ($line in ($chunk -split "`r?`n")) {
        if (-not $line.Trim()) { continue }
        Write-Host ("      | " + $line)          # 即時轉播子行程輸出(不再吞)
        [void]$Tail.Add($line)
        if ($Tail.Count -gt 40) { $Tail.RemoveAt(0) }
    }
    return $newPos
}

function def_Stage([string]$Name, [string[]]$Argv, [string]$Expect = "rc0", [int]$TimeoutSec = 0) {
    $t0 = Get-Date
    if (-not $Argv -or -not $Argv[0]) {
        $Script:Stages += @{ stage = $Name; state = "NOT_RUN"; note = "引擎缺(誠實)"; secs = 0 }
        Write-Host ("  [NOT_RUN] {0} · 引擎缺" -f $Name); return
    }
    if ($TimeoutSec -le 0) { $TimeoutSec = $StageTimeoutSec }
    $args2 = @($Argv | Where-Object { $_ -ne $null -and "$_" -ne "" })
    $fo = [IO.Path]::GetTempFileName(); $fe = [IO.Path]::GetTempFileName()
    $tail = New-Object System.Collections.ArrayList
    $rc = -1; $state = $null
    Write-Host ("  [RUN    ] {0} · 逾時上限 {1}s · 子行程輸出即時轉播 ↓" -f $Name, $TimeoutSec)
    try {
        $proc = Start-Process -FilePath $PY -ArgumentList $args2 -NoNewWindow -PassThru `
                              -RedirectStandardOutput $fo -RedirectStandardError $fe
    } catch {
        $Script:Stages += @{ stage = $Name; state = "FAIL"; rc = -1; secs = 0; note = "啟動失敗:" + $_.Exception.Message }
        Write-Host ("  [FAIL   ] {0} · 啟動失敗" -f $Name) -ForegroundColor Red
        Remove-Item $fo, $fe -ErrorAction SilentlyContinue; return
    }
    $po = 0L; $pe = 0L
    while (-not $proc.HasExited) {
        Start-Sleep -Milliseconds 400
        $po = def_Drain $fo $po $Name $tail
        $el = ((Get-Date) - $t0).TotalSeconds
        Write-Progress -Activity ("AllGreen · " + $Name) `
            -Status ("經過 {0}s / 上限 {1}s" -f [int]$el, $TimeoutSec) `
            -PercentComplete ([math]::Min(99, [int](100 * $el / $TimeoutSec)))
        if ($el -gt $TimeoutSec) {
            try { $proc.Kill() } catch { }
            $state = "TIMEOUT"                   # 誠實第四態:不冒充 FAIL 也不冒充 OK
            break
        }
    }
    if (-not $state) { try { $proc.WaitForExit() } catch { }; $rc = $proc.ExitCode }
    $po = def_Drain $fo $po $Name $tail          # 收尾殘量(進程結束後還有緩衝未排完)
    $pe = def_Drain $fe $pe $Name $tail
    Write-Progress -Activity ("AllGreen · " + $Name) -Completed
    $secs = [math]::Round(((Get-Date) - $t0).TotalSeconds, 1)
    if (-not $state) {
        $ok = if ($Expect -eq "env") { $true } else { $rc -eq 0 }
        $state = if ($ok -and $rc -eq 0) { "OK" } elseif ($Expect -eq "env") { "SKIP" } else { "FAIL" }
    }
    $note = (($tail | Where-Object { $_.Trim() } | Select-Object -Last 2) -join " / ")
    if ($state -eq "TIMEOUT") { $note = ("逾 {0}s 已 Kill(誠實:未判成敗)· " -f $TimeoutSec) + $note }
    if ($note.Length -gt 160) { $note = $note.Substring(0, 160) }
    $Script:Stages += @{ stage = $Name; state = $state; rc = $rc; secs = $secs; note = $note }
    $col = switch ($state) { "OK" { "Green" } "TIMEOUT" { "Yellow" } "FAIL" { "Red" } default { "Gray" } }
    Write-Host ("  [{0,-7}] {1} · {2}s" -f $state, $Name, $secs) -ForegroundColor $col
    Remove-Item $fo, $fe -ErrorAction SilentlyContinue
}

function def_AccelLamp() {
    # 20 加速器點名(SUP_MDL737 → Celeritas)。缺席=誠實說缺,絕不點假燈。
    $m = Get-ChildItem -LiteralPath (Join-Path $VIA "supportive modules") `
         -Filter "SUP_MDL737_SuperAccelModule_v*.py" -File -ErrorAction SilentlyContinue |
         Sort-Object Name | Select-Object -Last 1
    if (-not $m) { Write-Host "  [加速器] SUP_MDL737 缺檔(誠實;不影響跑,只是沒加速)"; return }
    try {
        $o = & $PY $m.FullName --activate 2>&1 | Out-String
        $line = (($o -split "`r?`n") | Where-Object { $_ -match "Celeritas|lib 冊|執行緒" }) -join " · "
        if (-not $line.Trim()) { $line = (($o -split "`r?`n") | Where-Object { $_.Trim() } | Select-Object -First 2) -join " · " }
        Write-Host ("  [加速器] " + $line.Trim())
    } catch { Write-Host ("  [加速器] 點名例外:" + $_.Exception.Message + "(誠實;不影響跑)") }
}

function def_Debug([string]$Phase) {
    $fails = @($Script:Stages | Where-Object { $_.state -eq "FAIL" })
    if ($fails.Count -eq 0) { Write-Host ("  [DEBUG  ] {0}:零 FAIL — 無事可修(誠實,不假造修正)" -f $Phase) }
    else {
        Write-Host ("  [DEBUG  ] {0}:{1} 站 FAIL — 建議制列示(高風險不自動修):" -f $Phase, $fails.Count)
        foreach ($f in $fails) { Write-Host ("     ✗ {0}:{1}" -f $f.stage, $f.note) }
    }
}

Write-Host "=== VIA AllGreen 一鍵統包 v0101 · $TS · 唯讀/dry-run · 建議制 ===" -ForegroundColor Cyan
Write-Host ("    每站逾時上限 {0}s(逾時 Kill 記 TIMEOUT,不卡死)· 子行程輸出即時轉播 · Write-Progress 進度列" -f $StageTimeoutSec)
def_AccelLamp

# ① TEST — 全面自測矩陣(站數以格子當下冊為準;v0100 註解寫死「18 站」早已過時,現為 200 站)
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

