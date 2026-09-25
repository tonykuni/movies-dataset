# =====================================================================
# Invoke-VIA-GroupPipeline-v0103.ps1 — 族群分類一鍵管線(批316;批317/318 實錄修;批319 不卡斷)
# =====================================================================
# 批319 操作員令:「卡斷 powershell 都要加 20 格加速器 py 檔都要導入加速器 不卡斷」。
# 治本三律(VIA-ALL 全背景派工同款):
#   Ⅰ 啟動器/工人分離:本窗只做 ⓪ 同步+自前進,鏈體交由分離最小化進程
#      (關窗不斷;Ctrl-C 只離開觀看,背景照跑);本窗即時尾讀 log 直播。
#   Ⅱ 每引擎節=加速器 18 看門狗同款(Start-Process 重導+逾時 Kill 整樹
#      =單節永不卡死全鏈;逾時記 FAIL/SKIP 誠實續走)+16 動態進度條。
#   Ⅲ 補料改增量:ENG054 尾版 v0101 依庫內 MAX(date) 只抓缺口(批內
#      SuperAccel accel_map 4 工);OmniFetch 定向 L12。
# 節序:⓪ 同步律→⓪b 自前進→[分離工人] ①補料七節→②ENG070 十四檢+run
#       →③ENG071 六檢+run→④開頁+彙總(誠實三態)→「=== 畢 ===」。
# 律:引擎路徑一律 glob 尾版(Newest);嚴禁寫死版號;零 CDN;自測 FAIL 仍續 run。
# 用法:via-pipeline.cmd [-SkipSync] [-SkipFill] [-NoOpen] [-Foreground]
#   -Foreground = 舊式同窗阻塞(除錯用);-Worker/-LogPath/-SyncNote = 內部派工參數。
# 加速器覆蓋實查(批319):PS 723/723 全掛 PS-ACCEL;py 2166/2185 掛 ACCEL-BRIDGE,
#   缺 19 檔全屬 VIA_RetiredEngines/_review_quarantine/vendor/bundle 歷史件(非現役)。
# =====================================================================
param(
    [switch]$SkipSync,
    [switch]$SkipFill,
    [switch]$NoOpen,
    [switch]$Foreground,
    [switch]$Worker,
    [string]$LogPath = "",
    [string]$SyncNote = ""
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
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch { }
$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"
$env:PYTHONUNBUFFERED = "1"     # 批319:直播需逐行即時
$env:PYTHONWARNINGS = "ignore:Unverified HTTPS request"
# 雙同意閘(fail-closed 引擎;操作員令「補齊資料」=明令開閘)
$env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"

$VIA  = $PSScriptRoot
$REPO = Split-Path $VIA -Parent
$ENG  = Join-Path $VIA "functional modules\VDF\engine"
$UI   = Join-Path $VIA "supportive modules\ui_support"
$LOGD = Join-Path $VIA "VIA_Reports\group_pipeline"
New-Item -ItemType Directory -Force -Path $LOGD | Out-Null
$STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
if ($LogPath) { $LOG = $LogPath } else { $LOG = Join-Path $LOGD "group_pipeline_$STAMP.log" }
$T0 = Get-Date
$PSEXE = "powershell"
if (Get-Command pwsh -ErrorAction SilentlyContinue) { $PSEXE = "pwsh" }
$PY = "python"
if (Get-Command py -ErrorAction SilentlyContinue) { $PY = "py" }
if (Get-Command python -ErrorAction SilentlyContinue) { $PY = "python" }
$UTF8 = New-Object System.Text.UTF8Encoding($false)
$script:Rows = @()
$script:StepN = 0

function Newest([string]$dir, [string]$pat) {
    (Get-ChildItem -Path $dir -Filter $pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}
function Say([string]$msg, [string]$color = "Gray") {
    Write-Host $msg -ForegroundColor $color
    try { Add-Content -Path $LOG -Value $msg -Encoding UTF8 } catch { }
}
function Record([string]$label, [string]$state, [string]$note, [double]$sec) {
    $script:Rows += [pscustomobject]@{ 節 = $label; 態 = $state; 秒 = [math]::Round($sec, 1); 註 = $note }
    $c = switch ($state) { "OK" { "Green" } "FAIL" { "Red" } default { "Yellow" } }
    Say ("  [{0}] {1} ({2}s) {3}" -f $state, $label, [math]::Round($sec, 1), $note) $c
}
function Read-NewText([string]$path, [ref]$pos) {
    # 共享讀(寫端持有中亦可讀)=直播尾讀原語
    if (-not (Test-Path $path)) { return "" }
    try {
        $fs = New-Object System.IO.FileStream($path, [System.IO.FileMode]::Open,
              [System.IO.FileAccess]::Read, [System.IO.FileShare]::ReadWrite)
        try {
            if ($fs.Length -le $pos.Value) { return "" }
            $fs.Seek($pos.Value, [System.IO.SeekOrigin]::Begin) | Out-Null
            $buf = New-Object byte[] ($fs.Length - $pos.Value)
            $n = $fs.Read($buf, 0, $buf.Length)
            $pos.Value += $n
            return $UTF8.GetString($buf, 0, $n)
        } finally { $fs.Dispose() }
    } catch { return "" }
}
function Step([string]$label, [string]$script, [string[]]$argv, [switch]$Optional, [int]$TimeoutSec = 1800) {
    # 加速器 18 看門狗同款:重導輸出+逾時 Kill 整樹=不卡斷;16 動態進度
    Say "--- $label" "Cyan"
    if (-not $script) {
        Record $label "SKIP" "引擎缺(誠實;glob 尾版無命中)" 0
        return 1
    }
    $script:StepN++
    $so = Join-Path $LOGD ("step_{0}_{1:d2}.out" -f $STAMP, $script:StepN)
    $se = Join-Path $LOGD ("step_{0}_{1:d2}.err" -f $STAMP, $script:StepN)
    $t = Get-Date
    Say ("  > {0} {1} {2}(逾時 {3}s)" -f $PY, (Split-Path $script -Leaf), ($argv -join " "), $TimeoutSec) "DarkGray"
    $al = @('"' + $script + '"') + @($argv | ForEach-Object { if ($_ -match '\s') { '"' + $_ + '"' } else { $_ } })
    try {
        $p = Start-Process -FilePath $PY -ArgumentList $al -NoNewWindow -PassThru `
             -WorkingDirectory $ENG -RedirectStandardOutput $so -RedirectStandardError $se
    } catch {
        Record $label "FAIL" ("啟動敗:" + $_.Exception.Message) 0
        return 1
    }
    $pos = 0; $killed = $false
    while (-not $p.HasExited) {
        $el = [int]((Get-Date) - $t).TotalSeconds
        $txt = Read-NewText $so ([ref]$pos)
        if ($txt) { Write-Host $txt -NoNewline; try { Add-Content -Path $LOG -Value $txt.TrimEnd("`r", "`n") -Encoding UTF8 } catch { } }
        if (Get-Command Write-VIAProgress -ErrorAction SilentlyContinue) {
            Write-VIAProgress -Activity "VIA 族群管線看門狗" -Status "$label · $el s / $TimeoutSec s" -Percent ([int](100 * $el / $TimeoutSec))
        }
        if ($el -ge $TimeoutSec) { try { $p.Kill($true) } catch { try { $p.Kill() } catch { } }; $killed = $true; break }
        Start-Sleep -Milliseconds 800
    }
    try { $p.WaitForExit(5000) | Out-Null } catch { }
    $txt = Read-NewText $so ([ref]$pos)
    if ($txt) { Write-Host $txt -NoNewline; try { Add-Content -Path $LOG -Value $txt.TrimEnd("`r", "`n") -Encoding UTF8 } catch { } }
    try { Write-Progress -Id 11 -Activity "VIA 族群管線看門狗" -Completed } catch { }
    $errTxt = ""
    try { if ((Test-Path $se) -and ((Get-Item $se).Length -gt 0)) { $errTxt = (Get-Content $se -Raw -Encoding UTF8) } } catch { }
    if ($errTxt) { $tail = ($errTxt -split "`n" | Select-Object -Last 12) -join "`n"; Say ("  [stderr 尾]`n" + $tail) "DarkYellow" }
    $sec = ((Get-Date) - $t).TotalSeconds
    if ($killed) { $rc = 124 } else { $rc = $p.ExitCode }
    if ($rc -eq 0) { Record $label "OK" "" $sec }
    elseif ($killed) { Record $label ($(if ($Optional) { "SKIP" } else { "FAIL" })) "逾時 ${TimeoutSec}s 看門狗 Kill(誠實續走)" $sec }
    elseif ($Optional) { Record $label "SKIP" "rc=$rc(非阻斷;引擎自述見 log)" $sec }
    else { Record $label "FAIL" "rc=$rc" $sec }
    return $rc
}

function Invoke-Chain {
    # ---------- ① 補齊資料 ----------
    if ($SkipFill) {
        Record "① 補齊資料" "SKIP" "-SkipFill" 0
    } else {
        Step "①a OmniFetch 當沖市場級 L12(定向)"  (Newest $ENG "VDF_ENG055_OmniFetch_v*.py") @("run", "--lane", "L12") -Optional -TimeoutSec 600 | Out-Null
        Step "①b 台股價格增量(依庫內缺口)"       (Newest $ENG "VDF_ENG054_TWDailyBackfill_v*.py") @("run") -TimeoutSec 3600 | Out-Null
        Step "①c 歷史回補(2022/2023 段增量)"      (Newest $ENG "VDF_ENG064_HistoryBackfill_v*.py") @("run") -Optional -TimeoutSec 1800 | Out-Null
        Step "①d 調整後價格層重建"                (Newest $ENG "VDF_ENG060_AdjPriceLayer_v*.py") @("build") -TimeoutSec 900 | Out-Null
        Step "①e 籌碼增量(法人/融資融券)"         (Newest $ENG "VDF_ENG056_ChipBackfill_v*.py") @("run") -Optional -TimeoutSec 1800 | Out-Null
        Step "①f 籌碼衍生欄(當沖比)"              (Newest $ENG "VDF_ENG056_ChipBackfill_v*.py") @("--derive") -Optional -TimeoutSec 900 | Out-Null
        Step "①g 逐股成交值增量"                  (Newest $ENG "VDF_ENG057_TradingValueBackfill_v*.py") @("run") -Optional -TimeoutSec 1800 | Out-Null
    }
    # ---------- ② 分類引擎 ----------
    $e70 = Newest $ENG "VDF_ENG070_GroupClassificationIndex_v*.py"
    Step "②a 分類引擎自測(十四檢)" $e70 @("--selftest") -TimeoutSec 1800 | Out-Null
    Step "②b 分類引擎 run(故事×產業×指標×整合清單)" $e70 @() -TimeoutSec 1800 | Out-Null
    # ---------- ③ 回測引擎 ----------
    $e71 = Newest $ENG "VDF_ENG071_GroupBacktest_v*.py"
    Step "③a 回測引擎自測(六檢)" $e71 @("--selftest") -TimeoutSec 1800 | Out-Null
    Step "③b 回測引擎 run(S1 聚焦 vs 等權 vs 全市場)" $e71 @() -TimeoutSec 1800 | Out-Null
    # ---------- ④ 開頁+彙總 ----------
    $p70 = Newest $UI "VIA_UI_GroupClassIndex_v*.html"
    $p71 = Newest $UI "VIA_UI_GroupBacktest_v*.html"
    if (-not $NoOpen) {
        foreach ($p in @($p70, $p71)) {
            if ($p) { try { Start-Process $p } catch { Say "  [開頁] 失敗:$p" "Yellow" } }
        }
    }
    $total = ((Get-Date) - $T0).TotalSeconds
    Say ""; Say "=== 彙總(誠實三態)===" "White"
    $script:Rows | Format-Table -AutoSize | Out-String -Width 160 | ForEach-Object { Say $_ }
    $nOK = @($script:Rows | Where-Object 態 -eq "OK").Count
    $nF  = @($script:Rows | Where-Object 態 -eq "FAIL").Count
    $nS  = @($script:Rows | Where-Object 態 -eq "SKIP").Count
    Say ("  計 OK {0} · FAIL {1} · SKIP {2} · 總耗時 {3}s" -f $nOK, $nF, $nS, [math]::Round($total, 0)) "White"
    Say ("  分類頁={0}" -f ($(if ($p70) { $p70 } else { "缺(引擎未產出)" })))
    Say ("  回測頁={0}" -f ($(if ($p71) { $p71 } else { "缺(引擎未產出)" })))
    Say "  存證=$(Join-Path $VIA 'VIA_Reports\group_class')(分類 GROUP_CLASS/STORY_CLASS/MASTER_LIST+回測 BACKTEST_<stamp>.json)"
    Say "  log=$LOG"
    $code = $(if ($nF -gt 0) { 1 } else { 0 })
    Say "=== 畢(退出碼 $code)===" "White"
    try { Copy-Item $LOG (Join-Path $LOGD "LAST_RUN.log") -Force } catch { }
    return $code
}

# =====================================================================
# 工人模式:分離進程內跑鏈體(啟動器已同步)
# =====================================================================
if ($Worker) {
    $host.UI.RawUI.WindowTitle = "VIA 族群管線工人 · $STAMP"
    Say "=== [工人] 鏈體開跑 · 分離進程 PID $PID ===" "White"
    Record "⓪ 同步律" "OK" $(if ($SyncNote) { $SyncNote } else { "由啟動器完成" }) 0
    $code = Invoke-Chain
    exit $code
}

# =====================================================================
# 啟動器模式
# =====================================================================
Say "=== VIA 族群分類一鍵管線 v0103(不卡斷)· $STAMP ===" "White"
Say "  根=$VIA"
Say "  log=$LOG"

# ---------- ⓪ 同步律 ----------
$syncNote = "-SkipSync"
if ($SkipSync) {
    Record "⓪ 同步律" "SKIP" "-SkipSync" 0
} else {
    $t = Get-Date
    Say "--- ⓪ 同步律(stash→fetch→ff-only;分流=備份留痕後對齊)" "Cyan"
    git -C $REPO stash push --include-untracked -m "VIA-pipeline-preclean-$STAMP" 2>&1 | Tee-Object -FilePath $LOG -Append | Out-Host
    git -C $REPO fetch origin main 2>&1 | Tee-Object -FilePath $LOG -Append | Out-Host
    $fetchRc = $LASTEXITCODE
    if ($fetchRc -ne 0) {
        $syncNote = "fetch rc=$fetchRc(離線?續用本機版)"
        Record "⓪ 同步律" "FAIL" $syncNote (((Get-Date) - $t).TotalSeconds)
    } else {
        $cur = (git -C $REPO rev-parse --abbrev-ref HEAD).Trim()
        git -C $REPO merge --ff-only origin/main 2>&1 | Tee-Object -FilePath $LOG -Append | Out-Host
        $note = ""
        if ($LASTEXITCODE -ne 0) {
            $sha = (git -C $REPO rev-parse --short HEAD).Trim()
            git -C $REPO branch "via-local-backup-$sha" 2>$null
            git -C $REPO reset --hard origin/main 2>&1 | Tee-Object -FilePath $LOG -Append | Out-Host
            $note = "分流→備份分支 via-local-backup-$sha 後對齊 origin/main;"
        }
        if ($cur -ne "main") {
            git -C $REPO switch -C main origin/main 2>&1 | Tee-Object -FilePath $LOG -Append | Out-Host
            $note += "分支 $cur→main;"
        }
        $syncNote = $note + "HEAD=" + (git -C $REPO rev-parse --short HEAD).Trim()
        Record "⓪ 同步律" "OK" $syncNote (((Get-Date) - $t).TotalSeconds)
    }
}

# ---------- ⓪b 自前進:同步後尾版≠本檔→轉呼尾版 ----------
$newest = Newest $VIA "Invoke-VIA-GroupPipeline-v*.ps1"
if ($newest -and $PSCommandPath -and ((Split-Path $newest -Leaf) -ne (Split-Path $PSCommandPath -Leaf))) {
    Say ("--- ⓪b 尾版前進:{0} → {1}(原參數轉呼;本輪由尾版接手)" -f (Split-Path $PSCommandPath -Leaf), (Split-Path $newest -Leaf)) "Cyan"
    $fwd = @("-SkipSync", "-LogPath", $LOG, "-SyncNote", $syncNote)
    if ($SkipFill)   { $fwd += "-SkipFill" }
    if ($NoOpen)     { $fwd += "-NoOpen" }
    if ($Foreground) { $fwd += "-Foreground" }
    & $PSEXE -NoProfile -ExecutionPolicy Bypass -File $newest @fwd
    exit $LASTEXITCODE
}

# ---------- 同窗阻塞(除錯用) ----------
if ($Foreground) {
    Say "--- [前景] -Foreground:同窗阻塞跑鏈體(除錯用)" "Cyan"
    $code = Invoke-Chain
    exit $code
}

# ---------- 分離派工+直播尾讀(不卡斷) ----------
$wargs = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"' + $PSCommandPath + '"'),
           "-Worker", "-SkipSync", "-LogPath", ('"' + $LOG + '"'), "-SyncNote", ('"' + $syncNote + '"'))
if ($SkipFill) { $wargs += "-SkipFill" }
if ($NoOpen)   { $wargs += "-NoOpen" }
try {
    $wp = Start-Process -FilePath $PSEXE -ArgumentList $wargs -WindowStyle Minimized -PassThru
    Say ("--- [背景] 鏈體已派工:分離進程 PID {0}(關窗不斷;Ctrl-C 只離開觀看)" -f $wp.Id) "Cyan"
} catch {
    Say ("  [FAIL] 派工敗:" + $_.Exception.Message + " → 退前景同窗跑") "Red"
    $code = Invoke-Chain
    exit $code
}
Say "--- [直播] 尾讀 log(結束自動收;隨時 Ctrl-C 離開,再看:Get-Content -Wait '$LOG')" "Cyan"
$pos = 0; $done = $false; $tStart = Get-Date
# 啟動器已寫入的段落先跳過(避免重印)
try { if (Test-Path $LOG) { $pos = (Get-Item $LOG).Length } } catch { }
while (-not $done -and (((Get-Date) - $tStart).TotalHours -lt 8)) {
    $txt = Read-NewText $LOG ([ref]$pos)
    if ($txt) {
        Write-Host $txt -NoNewline
        if ($txt -match "=== 畢") { $done = $true }
    }
    if (-not $done -and $wp.HasExited) {
        # 工人已退但無畢記=異常收場(誠實)
        $txt = Read-NewText $LOG ([ref]$pos); if ($txt) { Write-Host $txt -NoNewline }
        if (-not ($txt -match "=== 畢")) { Write-Host "  [FAIL] 工人進程提前退出(退出碼 $($wp.ExitCode));見 log" -ForegroundColor Red }
        break
    }
    Start-Sleep -Milliseconds 700
}
if ($done) { exit $(if ($wp.HasExited) { $wp.ExitCode } else { 0 }) } else { exit 1 }
