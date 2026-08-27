# via_boot_update.ps1 — VIA 開機自動更新器(PowerShell 版;批198)
# 工作站無 WSL/bash 之對應面:與 via_boot_update.sh 同鏈 ⓪-⑨(單一
# 邏輯雙載體;.sh 為正主,本檔跟隨其節序;引擎呼叫全 python 直譯)。
# marker 防重複:每日首跑才實跑;log 落 VIA_Reports/boot_update_logs/
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
    & python $script @argv *>> $LOG
}

Add-Content $LOG "=== VIA 開機更新 $TODAY(ps1 載體;節序=via_boot_update.sh 正主)==="
Step "① OmniFetch 全車道"          (Newest $ENG "VDF_ENG055_OmniFetch_v*.py") @("run")
Step "② 價格增量"                  (Newest $ENG "VDF_ENG054_TWDailyBackfill_v*.py") @("run")
Step "②b 調整後價格層(批178)"    (Newest $ENG "VDF_ENG060_AdjPriceLayer_v*.py") @("build")
Step "②c 因子庫(批188)"          (Newest $ENG "VDF_ENG061_FeatureStore_v*.py") @("build")
Step "③ 籌碼增量+衍生"            (Newest $ENG "VDF_ENG056_ChipBackfill_v*.py") @("run")
Step "③b 籌碼衍生"                (Newest $ENG "VDF_ENG056_ChipBackfill_v*.py") @("--derive")
Step "④ 主動 ETF 持股(PARTIAL 常態)" (Join-Path $ENG "VDF_ENG051_ActiveTWETF_Holdings.py") @()
Step "⑥ 逐股成交值增量(批154)"   (Newest $ENG "VDF_ENG057_TradingValueBackfill_v*.py") @("run")
Step "⑦ 分析師估值快照(批155)"   (Newest $ENG "VDF_ENG059_EstimateBands_v*.py") @("run")
Step "⑦b 驗證共識庫(批176)"      (Newest $VRN "VRN_ENG069_ConsensusDB_v*.py") @("build")
Step "⑦c Yahoo 共識(批194)"      (Newest $VRN "VRN_ENG070_YahooConsensus_v*.py") @("run")
Step "⑦d 月營收(批194)"          (Newest $ENG "VDF_ENG063_MonthlyRevenue_v*.py") @("run")
Step "⑧ 台股輪動日快照(批153)"   (Newest $GRP "GRP_ENG040_GroupingRotationRunner_v*.py") @("run", "tw")
Step "⑧b 族群因子層(批193)"      (Newest $ENG "VDF_ENG062_GroupFeatureLayer_v*.py") @("build")
Step "⑤ 對帳"                      (Newest $ENG "VDF_ENG055_OmniFetch_v*.py") @("--status")
Add-Content $LOG "--- ⑨ 同步 UI 重生(批168)"
Step "⑨a 五系統分頁"               (Newest $REG "CGC_MDL088_SystemTestPages_v*.py") @("run")
Step "⑨b 系統樞紐"                 (Newest $REG "CGC_MDL090_SystemHub_v*.py") @("run")
Step "⑨c 儀表板"                   (Newest (Join-Path $VIA "functional modules\VAP\engine") "VAP_ENG009_DashboardUI_v*.py") @("run")
Step "⑨d 每日觀察"                 (Newest $VRN "VRN_ENG068_DailyBrief_v*.py") @("run")
Add-Content $LOG "=== 畢(誠實三態見上)==="
Write-Host "[boot-ps1] 完成 · log=$LOG"
exit 0
