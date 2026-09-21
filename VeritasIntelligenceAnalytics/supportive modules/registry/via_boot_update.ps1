# via_boot_update.ps1 — VIA 開機自動更新器(PowerShell 版;批198)
# 工作站無 WSL/bash 之對應面:與 via_boot_update.sh 同鏈 ⓪-⑳(單一
# 邏輯雙載體;.sh 為正主,本檔跟隨其節序;引擎呼叫全 python 直譯)。
# 側線 2026-09-21 d(Z94 結案;操作員令「擷取 VDF 的資料 · 完善到可啟動」;主線批號由併線的手指定 L25):
#   量出來 .ps1 比 .sh 正主少 13 步(④a ENG077 宇宙 · ④b ENG078 持股史 · ⑩ ENG076 合流 · ⑪–⑳ MDL131/133/135/136/ENG079/MDL137/ENG081/MDL139/140/141),
#   且用裸 python 起引擎(批384 律:VDF 引擎以家族境 via_vdf_312 啟動;缺 duckdb/pandas 的 base 會把每一步都跑成 ModuleNotFoundError)。
#   補齊節序 + ⓪ 家族境 python(尺=CGC_MDL136 envpy 正本,不另抄別名表);同鏈由 VDF_SystemManager launch ㉘ 每跑一次量一次。
#   本檔不裝套件(.sh ⓪ 的 pip 自補是容器非持久境的事;工作站家族境是操作員的手)、不改同意閘行為(批123/137/150 常令授權沿用)。
# marker 防重複:每日首跑才實跑;log 落 VIA_Reports/boot_update_logs/
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
$VIA  = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$ENG  = Join-Path $VIA "functional modules\VDF\engine"
$VRN  = Join-Path $VIA "functional modules\VRN"
$REG  = Join-Path $VIA "supportive modules\registry"
$GRP  = Join-Path $VIA "functional modules\GroupIndex\engine"
$MEGA = Join-Path $VIA "functional modules\VDF\output_hub\mega"
$MARK = Join-Path $MEGA ".last_boot_update"
$LOGD = Join-Path $VIA "VIA_Reports\boot_update_logs"
$TODAY = Get-Date -Format "yyyy-MM-dd"

New-Item -ItemType Directory -Force -Path $LOGD, $MEGA | Out-Null
if ((Test-Path $MARK) -and ((Get-Content $MARK -ErrorAction SilentlyContinue) -eq $TODAY)) {
    Add-Content (Join-Path $LOGD "skip.log") "[boot-update] $TODAY 已更(marker)=SKIP(ps1)"
    exit 0
}
Set-Content $MARK $TODAY
$LOG = Join-Path $LOGD ("BOOT_" + (Get-Date -Format "yyyyMMdd_HHmmss") + "_ps1.log")
$env:VIA_NET_CONSENT = "YES"; $env:VIA_SCRAPE_CONSENT = "YES"

function Newest([string]$dir, [string]$pat) {
    (Get-ChildItem -Path $dir -Filter $pat -ErrorAction SilentlyContinue |
     Sort-Object Name | Select-Object -Last 1).FullName
}
function Step([string]$label, [string]$script, [string[]]$argv) {
    Add-Content $LOG "--- $label"
    if (-not $script) { Add-Content $LOG "  [SKIP] 引擎缺(誠實)"; return }
    & $PY $script @argv *>> $LOG
}
# ⓪ 家族境 python(側線 2026-09-21 d;批384 律):尺=CGC_MDL136 EntryBridge envpy(Register 的 Get-VIAEnvPython 同一份正本);
#   境未見=base 退路且**寫進 log**(能跑≠本位;缺套件時每一步的 ModuleNotFoundError 就是這一行的下文)。
$PY = "python"; $PYSTATE = "base(尺缺:CGC_MDL136_EntryBridge_v*.py 不在)"
$envpy = Newest $REG "CGC_MDL136_EntryBridge_v*.py"
if ($envpy) {
    try {
        $line = (& python $envpy envpy vdf --json 2>$null | Select-Object -Last 1)
        $r = ("" + $line) | ConvertFrom-Json
        if ($r -and $r.python -and (Test-Path -LiteralPath ("" + $r.python))) { $PY = "" + $r.python; $PYSTATE = "" + $r.state + "(" + $r.source + ")" }
        else { $PYSTATE = "base(envpy 無解:" + ("" + $line) + ")" }
    } catch { $PYSTATE = "base(envpy 炸:" + $_.Exception.Message + ")" }
}

Add-Content $LOG "=== VIA 開機更新 $TODAY(ps1 載體;節序=via_boot_update.sh 正主)==="
Add-Content $LOG "--- ⓪ 家族境 python(尺=CGC_MDL136 envpy):$PY · $PYSTATE(本檔不裝套件;境缺=操作員的手)"
Step "① OmniFetch 全車道"          (Newest $ENG "VDF_ENG055_OmniFetch_v*.py") @("run")
Step "② 價格增量"                  (Newest $ENG "VDF_ENG054_TWDailyBackfill_v*.py") @("run")
Step "②b 調整後價格層(批178)"    (Newest $ENG "VDF_ENG060_AdjPriceLayer_v*.py") @("build")
Step "②c 因子庫(批188)"          (Newest $ENG "VDF_ENG061_FeatureStore_v*.py") @("build")
Step "③ 籌碼增量+衍生"            (Newest $ENG "VDF_ENG056_ChipBackfill_v*.py") @("run")
Step "③b 籌碼衍生"                (Newest $ENG "VDF_ENG056_ChipBackfill_v*.py") @("--derive")
Step "④a 主動 ETF 宇宙日更(批374;A 碼律+國內成分揭露律;ENG077)" (Newest $ENG "VDF_ENG077_ActiveETFUniverse_v*.py") @("run")
Step "④ 主動 ETF 持股(PARTIAL 常態)" (Join-Path $ENG "VDF_ENG051_ActiveTWETF_Holdings.py") @()
Step "④b 主動 ETF 每日持股史深覆蓋+缺口回補(批375;ENG078;IPO 起)" (Newest $ENG "VDF_ENG078_ActiveETFHoldingsHistory_v*.py") @("daily")
Step "⑥ 逐股成交值增量(批154)"   (Newest $ENG "VDF_ENG057_TradingValueBackfill_v*.py") @("run")
Step "⑦ 分析師估值快照(批155)"   (Newest $ENG "VDF_ENG059_EstimateBands_v*.py") @("run")
Step "⑦b 驗證共識庫(批176)"      (Newest $VRN "VRN_ENG069_ConsensusDB_v*.py") @("build")
Step "⑦c Yahoo 共識(批194)"      (Newest $VRN "VRN_ENG070_YahooConsensus_v*.py") @("run")
Step "⑦d 月營收(批194)"          (Newest $ENG "VDF_ENG063_MonthlyRevenue_v*.py") @("run")
Step "⑦e 鉅亨 FactSet 共識(批199)" (Newest $VRN "VRN_ENG071_CnyesFusion_v*.py") @("run")
Step "⑧ 台股輪動日快照(批153)"   (Newest $GRP "GRP_ENG040_GroupingRotationRunner_v*.py") @("run", "tw")
Step "⑧b 族群因子層(批193)"      (Newest $ENG "VDF_ENG062_GroupFeatureLayer_v*.py") @("build")
Step "⑤ 對帳"                      (Newest $ENG "VDF_ENG055_OmniFetch_v*.py") @("--status")
Add-Content $LOG "--- ⑨ 同步 UI 重生(批168)"
Step "⑨a 五系統分頁"               (Newest $REG "CGC_MDL088_SystemTestPages_v*.py") @("run")
Step "⑨b 系統樞紐"                 (Newest $REG "CGC_MDL090_SystemHub_v*.py") @("run")
Step "⑨b2 統一殼四頁(批324)"     (Newest $REG "CGC_MDL116_UnifiedShell_v*.py") @()
Step "⑨b4 系統總台六主體(批332)"  (Newest $REG "CGC_MDL120_SystemUI_v*.py") @()
Step "⑨b3 治理主控台(批324)"      (Newest $REG "CGC_MDL105_GovernanceConsole_v*.py") @()
Step "⑨c 儀表板"                   (Newest (Join-Path $VIA "functional modules\VAP\engine") "VAP_ENG009_DashboardUI_v*.py") @("run")
Step "⑨d 每日觀察"                 (Newest $VRN "VRN_ENG068_DailyBrief_v*.py") @("run")
# 批270:⑩ 上線分析組——新功能掛日更(資料鮮→分析頁自動鮮;全零網路在庫 join)
Step "⑩a ETF 持股×共識增益(批243)" (Newest $ENG "VDF_ENG067_ConsensusEnrichment_v*.py") @("run")
Step "⑩b 主動 ETF×共識分析(批264)" (Newest $ENG "VDF_ENG068_ETFConsensusAnalysis_v*.py") @("run")
Step "⑩c 月營收×共識分析(批264)"   (Newest $ENG "VDF_ENG069_RevenueConsensusAnalysis_v*.py") @("run")
Step "⑩c2 主動 ETF×月營收合流(批373;ENG076)" (Newest $ENG "VDF_ENG076_ETFRevenueMomentum_v*.py") @("run")
Step "⑩d 測試總表(批257)" (Newest $REG "CGC_MDL104_TestResultsHub_v*.py") @()
Step "⑩e 三軌矩陣(批267)"          (Newest $REG "CGC_MDL110_TriTestMatrix_v*.py") @()
Step "⑩f 標準儀表板模板(批279)"    (Newest (Join-Path $VIA "functional modules\VAP\engine") "VAP_ENG014_StdDashboardTemplate_v*.py") @("run")
Step "⑩g 統一編號冊(批287)"        (Newest $REG "CGC_MDL113_UnifiedRegistry_v*.py") @()
Step "⑩h AIO 健康圖(批288)"        (Newest $REG "CGC_MDL114_CommandCenterBridge_v*.py") @("run")
# ⑪–⑳(側線 2026-09-21 d 補齊;.sh 第 117–136 行同序;全段零跳出 VIA_NO_OPEN=1,與 .sh 逐步前置同義)
$env:VIA_NO_OPEN = "1"
Step "⑪ 四專案完工矩陣(批368;MDL131)"  (Newest $REG "CGC_MDL131_ProjectCompletion_v*.py") @("build")
Step "⑫ 產品資格閘(批376;MDL133;九閘;只讀存證)" (Newest $REG "CGC_MDL133_ProductGate_v*.py") @("build")
Step "⑬ 環境治理全景(批381;MDL135;唯讀 run --offline;LKGC 快照)" (Newest $REG "CGC_MDL135_EnvGovernance_v*.py") @("run", "--offline", "--quiet")
Step "⑭ 單一入口燈板(批383;MDL136;零網路;VIA_Reports/entry)" (Newest $REG "CGC_MDL136_EntryBridge_v*.py") @("status", "--quiet")
Step "⑮ 本機三庫整併盤點(批383;ENG079;scan 唯讀;三庫不在=誠實 ABSENT 不寫)" (Newest $ENG "VDF_ENG079_LocalDbConsolidate_v*.py") @("scan")
Step "⑯ 能跑閘(批384;MDL137;家族境 python 真跑引擎自測 --fast;境缺=base 退路誠實黃)" (Newest $REG "CGC_MDL137_RunGate_v*.py") @("run", "--fast", "--quiet")
Step "⑰ 台股日交易×籌碼數量對齊核對(批390;VDF_ENG081 check;唯讀;庫缺/籌碼落後=誠實不假綠)" (Newest $ENG "VDF_ENG081_UniverseAlign_v*.py") @("check")
Step "⑱ 輸入主控台頁再生(批390;MDL139 build;零 CDN;零網路)" (Newest $REG "CGC_MDL139_InputConsole_v*.py") @("build")
Step "⑲ 接棒狀態台再生(批392;MDL140 build;只讀現役 *_latest.json;零網路)" (Newest $REG "CGC_MDL140_HandoverConsole_v*.py") @("build")
Step "⑳ 收尾閘(批398;MDL141 all 只讀:VRN 逐份五段鏈+核對態、VAP 逐圖驗;無報告/無圖=誠實黃)" (Newest $REG "CGC_MDL141_ClosingGate_v*.py") @("all")
Add-Content $LOG "=== 畢(誠實三態見上)==="
Write-Host "[boot-ps1] 完成 · log=$LOG"
exit 0
