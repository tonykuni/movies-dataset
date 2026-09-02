# =====================================================================
# Invoke-VIA-GroupPipeline-v0101.ps1 — 族群分類一鍵管線(批316;批317 實錄修)
# 批317 工作站實錄三修:①a OmniFetch 全 14 車道太慢=操作員 Ctrl-C→只跑 L12
# 當沖市場級(價格/籌碼/成交值各有專屬節);urllib3 InsecureRequestWarning
# 洗版→PYTHONWARNINGS 定向靜音(僅該訊息;其他警告照出);⓪ HEAD 站在
# 5h274b 分流分支=同步後 switch -C main origin/main(舊分支 ref 留=只增不減)。
# =====================================================================
# 操作員令(批316):「給一個 powershell 指令補齊資料然後啟動驗證分類即
# 回測引擎 一個 powershell 跑完全部」。
# 節序(全同步阻塞;每節 rc 誠實三態 OK/FAIL/SKIP;失敗續行不卡斷):
#   ⓪ 同步律(VIA-ALL 律):stash -u→fetch→ff-only;分流=備份分支留痕
#      後 reset --hard 對齊 origin/main(-SkipSync 略)
#   ① 補齊資料(-SkipFill 略;雙同意閘本檔設 YES=操作員明令補料):
#      ①a ENG055 OmniFetch 僅 L12 當沖市場級(批317:全車道太慢改定向)
#      ①b ENG054 台股價格增量 run
#      ①c ENG064 歷史回補 run(2022/2023 段 checkpoint 增量;秒過零重抓)
#      ①d ENG060 調整後價格層 build(ENG070 讀 tw_prices_adj=必重建)
#      ①e ENG056 籌碼增量 run → ①f --derive 衍生欄(當沖比)
#      ①g ENG057 逐股成交值增量 run
#   ② 分類引擎 ENG070 尾版:--selftest(十四檢)→ run(故事×產業×指標
#      ×整合清單;頁 VIA_UI_GroupClassIndex_v*.html)
#   ③ 回測引擎 ENG071 尾版:--selftest(六檢)→ run(S1 聚焦 vs 全員等權
#      vs 全市場 ex-2330 等權;頁 VIA_UI_GroupBacktest_v*.html)
#   ④ 開兩頁(-NoOpen 略)+彙總表+log VIA_Reports\group_pipeline\
# 律:引擎路徑一律 glob 尾版(Newest),嚴禁寫死版號;零 CDN;
#     自測 FAIL 仍續 run(誠實標紅不假綠;run 由引擎自身守衛)。
# 用法:powershell -NoProfile -ExecutionPolicy Bypass -File ".\Invoke-VIA-GroupPipeline-v0101.ps1"
#       [-SkipSync] [-SkipFill] [-NoOpen]
#       cmd 殼:via-pipeline.cmd(同參數);PS 短令:via-pipeline
# =====================================================================
param(
    [switch]$SkipSync,
    [switch]$SkipFill,
    [switch]$NoOpen
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
# 批317:定向靜音 urllib3 本機代理自簽憑證警告(僅此訊息;其餘警告照出)
$env:PYTHONWARNINGS = "ignore:Unverified HTTPS request"

$VIA  = $PSScriptRoot
$REPO = Split-Path $VIA -Parent
$ENG  = Join-Path $VIA "functional modules\VDF\engine"
$UI   = Join-Path $VIA "supportive modules\ui_support"
$LOGD = Join-Path $VIA "VIA_Reports\group_pipeline"
New-Item -ItemType Directory -Force -Path $LOGD | Out-Null
$STAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$LOG = Join-Path $LOGD "group_pipeline_$STAMP.log"
$T0 = Get-Date

# 雙同意閘(fail-closed 引擎;操作員令「補齊資料」=明令開閘)
$env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"

$PY = "python"
if (Get-Command py -ErrorAction SilentlyContinue) { $PY = "py" }
if (Get-Command python -ErrorAction SilentlyContinue) { $PY = "python" }

$script:Rows = @()

function Newest([string]$dir, [string]$pat) {
    (Get-ChildItem -Path $dir -Filter $pat -File -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}
function Say([string]$msg, [string]$color = "Gray") {
    Write-Host $msg -ForegroundColor $color
    Add-Content -Path $LOG -Value $msg -Encoding UTF8
}
function Record([string]$label, [string]$state, [string]$note, [double]$sec) {
    $script:Rows += [pscustomobject]@{ 節 = $label; 態 = $state; 秒 = [math]::Round($sec, 1); 註 = $note }
    $c = switch ($state) { "OK" { "Green" } "FAIL" { "Red" } default { "Yellow" } }
    Say ("  [{0}] {1} ({2}s) {3}" -f $state, $label, [math]::Round($sec, 1), $note) $c
}
function Step([string]$label, [string]$script, [string[]]$argv, [switch]$Optional) {
    Say "--- $label" "Cyan"
    if (-not $script) {
        Record $label "SKIP" "引擎缺(誠實;glob 尾版無命中)" 0
        return 1
    }
    $t = Get-Date
    Say ("  > {0} {1} {2}" -f $PY, (Split-Path $script -Leaf), ($argv -join " ")) "DarkGray"
    & $PY $script @argv 2>&1 | Tee-Object -FilePath $LOG -Append | Out-Host
    $rc = $LASTEXITCODE
    $sec = ((Get-Date) - $t).TotalSeconds
    if ($rc -eq 0) { Record $label "OK" "" $sec }
    elseif ($Optional) { Record $label "SKIP" "rc=$rc(非阻斷;引擎自述見 log)" $sec }
    else { Record $label "FAIL" "rc=$rc" $sec }
    return $rc
}

Say "=== VIA 族群分類一鍵管線 v0101 · $STAMP ===" "White"
Say "  根=$VIA"
Say "  log=$LOG"

# ---------- ⓪ 同步律 ----------
if ($SkipSync) {
    Record "⓪ 同步律" "SKIP" "-SkipSync" 0
} else {
    $t = Get-Date
    Say "--- ⓪ 同步律(stash→fetch→ff-only;分流=備份留痕後對齊)" "Cyan"
    git -C $REPO stash push --include-untracked -m "VIA-pipeline-preclean-$STAMP" 2>&1 | Tee-Object -FilePath $LOG -Append | Out-Host
    git -C $REPO fetch origin main 2>&1 | Tee-Object -FilePath $LOG -Append | Out-Host
    $fetchRc = $LASTEXITCODE
    if ($fetchRc -ne 0) {
        Record "⓪ 同步律" "FAIL" "fetch rc=$fetchRc(離線?續用本機版)" (((Get-Date) - $t).TotalSeconds)
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
        # 批317:HEAD 站在分流分支(實錄 5h274b)=切回 main 對齊;舊分支 ref 留(只增不減)
        if ($cur -ne "main") {
            git -C $REPO switch -C main origin/main 2>&1 | Tee-Object -FilePath $LOG -Append | Out-Host
            $note += "分支 $cur→main;"
        }
        Record "⓪ 同步律" "OK" ($note + "HEAD=" + (git -C $REPO rev-parse --short HEAD).Trim()) (((Get-Date) - $t).TotalSeconds)
    }
}

# ---------- ① 補齊資料 ----------
if ($SkipFill) {
    Record "① 補齊資料" "SKIP" "-SkipFill" 0
} else {
    Step "①a OmniFetch 當沖市場級 L12(定向)"  (Newest $ENG "VDF_ENG055_OmniFetch_v*.py") @("run", "--lane", "L12") -Optional | Out-Null
    Step "①b 台股價格增量"                    (Newest $ENG "VDF_ENG054_TWDailyBackfill_v*.py") @("run") | Out-Null
    Step "①c 歷史回補(2022/2023 段增量)"      (Newest $ENG "VDF_ENG064_HistoryBackfill_v*.py") @("run") -Optional | Out-Null
    Step "①d 調整後價格層重建"                (Newest $ENG "VDF_ENG060_AdjPriceLayer_v*.py") @("build") | Out-Null
    Step "①e 籌碼增量(法人/融資融券)"         (Newest $ENG "VDF_ENG056_ChipBackfill_v*.py") @("run") -Optional | Out-Null
    Step "①f 籌碼衍生欄(當沖比)"              (Newest $ENG "VDF_ENG056_ChipBackfill_v*.py") @("--derive") -Optional | Out-Null
    Step "①g 逐股成交值增量"                  (Newest $ENG "VDF_ENG057_TradingValueBackfill_v*.py") @("run") -Optional | Out-Null
}

# ---------- ② 分類引擎 ----------
$e70 = Newest $ENG "VDF_ENG070_GroupClassificationIndex_v*.py"
Step "②a 分類引擎自測(十四檢)" $e70 @("--selftest") | Out-Null
Step "②b 分類引擎 run(故事×產業×指標×整合清單)" $e70 @() | Out-Null

# ---------- ③ 回測引擎 ----------
$e71 = Newest $ENG "VDF_ENG071_GroupBacktest_v*.py"
Step "③a 回測引擎自測(六檢)" $e71 @("--selftest") | Out-Null
Step "③b 回測引擎 run(S1 聚焦 vs 等權 vs 全市場)" $e71 @() | Out-Null

# ---------- ④ 開頁+彙總 ----------
$p70 = Newest $UI "VIA_UI_GroupClassIndex_v*.html"
$p71 = Newest $UI "VIA_UI_GroupBacktest_v*.html"
if (-not $NoOpen) {
    foreach ($p in @($p70, $p71)) {
        if ($p) { try { Start-Process $p } catch { Say "  [開頁] 失敗:$p" "Yellow" } }
    }
}
$total = ((Get-Date) - $T0).TotalSeconds
Say "" ; Say "=== 彙總(誠實三態)===" "White"
$script:Rows | Format-Table -AutoSize | Out-String | ForEach-Object { Say $_ }
$nOK = @($script:Rows | Where-Object 態 -eq "OK").Count
$nF  = @($script:Rows | Where-Object 態 -eq "FAIL").Count
$nS  = @($script:Rows | Where-Object 態 -eq "SKIP").Count
Say ("  計 OK {0} · FAIL {1} · SKIP {2} · 總耗時 {3}s" -f $nOK, $nF, $nS, [math]::Round($total, 0)) "White"
Say ("  分類頁={0}" -f ($(if ($p70) { $p70 } else { "缺(引擎未產出)" })))
Say ("  回測頁={0}" -f ($(if ($p71) { $p71 } else { "缺(引擎未產出)" })))
Say "  存證=$(Join-Path $VIA 'VIA_Reports\group_class')(分類 GROUP_CLASS/STORY_CLASS/MASTER_LIST+回測 BACKTEST_<stamp>.json)"
Say "  log=$LOG"
exit $(if ($nF -gt 0) { 1 } else { 0 })
