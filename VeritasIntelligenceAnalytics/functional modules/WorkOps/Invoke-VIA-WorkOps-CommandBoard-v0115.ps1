#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-CommandBoard v0115 — WorkOps × Mail Tracker 統合指揮板(v0114 版本前送)
------------------------------------------------------------------------------------------
 v0115(操作員 Gemini 研究令 2026/08/09:三段時間發信追蹤/跟進/緊急跟進):
   1) 三段追蹤升級鏈:T1 追蹤(followup)→ T2 跟進(followup_firm)→ T3 緊急升級
      (urgent_escalation;建議 CC 主管由人自加,系統絕不代加代寄);門檻以「工作日」
      計算(週末+engines\holidays_tw.txt 假日自動跳過);參數 watchtower_params.json
   2) 異質控管表表頭映射:各行各業欄名(案號/Trace_ID/承辦人/Deadline…)自動對齊
      標準七欄(alias 字典;對不上的欄位保留原名不丟)
   3) 佇列表增「段」欄(T1/T2/T3)+工作日數
------------------------------------------------------------------------------------------
 v0114(操作員 ONE POWERSHELL 令;ENG-028 實跑 87 案落地):
   ① 半自動建構第五源:WOP 歸戶(wop_registry;引擎自動歸戶之工作專案,≥2 串預勾)
      → 勾選複製貼入控管表 → S2 最強票 → 之後歸戶更準(閉環)
------------------------------------------------------------------------------------------
 v0113(操作員八項 U/I 令 2026/08/08):
   1) ⓪ 系統流程頁(第一頁·預設頁):全系統運作流程圖 — 節點顏色=模組即時狀態
      (綠=就緒/黃=待跑/灰=休眠),減震安全動畫,點節點跳轉分頁(邏輯指導);
      兩份正本報告(Outlook 唯讀掃描/超級引擎/進階分析)直連;註冊功能+編號功能即況上板
   2) ① 工作專案半自動建構:四源候選(控管表現有 · 郵件叢集歸納 · 命名帳本 · 自建歸類)
      → 系統先自動分類預勾 → 使用者核對勾選(名稱可直接改)→ 複製控管表格式列
      (系統不代寫控管表);附準確度提升指引(核對迴圈/自建規則/主旨帶代號/互鏈累積)
   3) ② 範本下拉選擇器:圈選件可選範本;預設 approval_request_v2(豐富版必回選擇題)
   4) -DraftsTemplate 參數 + via-workops drafts 第三參數傳遞;MailOps 增 approval_request_v2
      豐富範本、VotingOptions 擴至 approval_request*(投票鈕=收件人原生勾選 UI)
------------------------------------------------------------------------------------------
 v0112(操作員展示 TPL_approval_request + 問「如何勾選」):
   1) 圈選件草稿改用「必回選擇題」範本(approval_request;自動佇列維持 followup 軟催)
   2) 控管表路徑補後備:WorkOps\control_sheet.csv 缺席時改讀庫根 control_sheet.csv
      (Templates 範例產在庫根 — 操作員實跑抓到的錯位)
   3) ⑥矩陣追蹤哨列註記圈選=必回選擇題;搭配 MailOps 投票按鈕(原生勾選 UI)
------------------------------------------------------------------------------------------
 v0111(操作員裁決:功能拆開重檢→去重→補不足→重新串接):⑥矩陣收錄重串接後全系統 —
   新增 EnvManager 治理安裝/graphviz 可攜版/命名核對(編號·名稱)/智慧工作台結合
   (Forge 12 分頁共用語料)/ALL 總指揮 五列即時狀態;$data 增 dot_ready/naming/
   forge_ready/envmgr_ran。正本裁定:郵件語料=WorkOps 深度鏈;工作台=消費者。
------------------------------------------------------------------------------------------
 v0101 新增(操作員 2026/08/08 裁決:獨立系統/權限內唯讀/歸納範疇/彙總關係人/
 範本郵件一次產生草稿但絕不代寄/預填降低修改量/繁簡英三語):
   [1] ③ 範疇與關係人頁:從郵件主旨歸納專案代號叢集,與控管表交叉 → 遺漏偵測
       (郵件中活躍但控管表沒有的案 = 建議建案;控管表有但無郵件佐證 = 原有 Unmatched)
       利害關係人彙總:全域(stakeholders.csv)+ 依專案代號歸戶(寄件人集合)
   [2] 草稿佇列:追蹤哨 ≥3 天未回者自動預填 out\recipients_auto.csv
       (ProjectCode/To/Template=followup/原主旨/等待天數)→ via-workops drafts 一次產生
       Outlook 草稿;引擎只 .Display()/.Save(),永不 .Send() — 使用者過目微調後親自寄
   [3] 三語 UI:繁體/簡體/English 一鍵切換(介面層;資料照原樣)
 治理:唯讀 Outlook(使用者自身權限);不改控管表;run-local 輸出;不卡斷。
 v0102 新增(操作員裁決:郵件/專案自動編號作識別;絕不改 Outlook 原件與既有分類;
 PLM 式流程自動化;吸收市場工具同類功能):
   [4] 自動編號 side-car 帳本(out/workops_id_ledger.json,append-only 冪等):
       專案 WOP-####(依案號首見指配)· 郵件串 THR-#####(依 ConversationID 首見指配)
       編號只存在本系統與輸出,Outlook 原件/分類/標籤一概不動 — 尊重既有系統與原始資料
   [5] 一鍵週報(市場功能吸收:Monday/Asana 報表):每跑產出 VIA_WorkOps_WeeklyReport.html
 v0103 新增(操作員裁決:信件要能圈選,U/I 要簡單):
   [6] 圈選:指揮板點列=圈選(亮框)、再點=取消;右下浮條「已圈選 N 件→複製草稿指令」
       複製 via-workops drafts THR-…,… 貼回 PowerShell 即對圈選件一次建草稿(絕不代寄)
   [7] -DraftsFor "THR-…,…":依編號帳本反查圈選串(pending 對象;inbound 則回追寄件人)
       → 產 recipients_auto.csv → 呼叫 v001 FollowUp;不重掃、不開板,快進快出
 v0104 新增(操作員裁決:VIA WorkOps + VERITAS MAIL TRACKER 整合為一個系統;
 設計基準=資源最佳化文獻:單一平台/容量可視化/消滅斷裂系統與人工表格):
   [8] ④ 郵件追蹤 VMT 頁:唯讀附掛 VMT_ROOT 資料層 —
       收斂分級(AUTO/CONFIRMED/ASK/QUARANTINE+自動化率)· CPM 排程(關鍵路徑紅/LATE)
       未布建時誠實引導 via-vmt-init;引擎各自模組獨立,統合發生在指揮板(單一資訊源)
   [9] 負載對照(容量可視化在地版):Owner × 控管案/需注意/未回件 → 過載紅燈(≥3 需注意)
   [10] 週報併入 VMT 段(單一報表=single source of truth)
 v0105 新增(操作員裁決:dashboard/workflows/下拉/勾選/window I/O/選擇題,極易操作+互動動畫):
   [11] 工作流步驟條:掃描→對帳→編號→草稿佇列→週報 五節點即時亮燈(dashboard 化)
   [12] 下拉篩選:①頁 負責人/燈級、②頁 燈級 — 免捲動找目標
   [13] 勾選框:②頁列首 checkbox 與點列圈選同步(視覺明確)
   [14] Window I/O:①頁點列開專案詳情彈窗(完整佐證+選擇題)
   [15] 選擇題:需注意案 採納/不採納/擱置 三選一 →「匯出決定 CSV」(不回寫控管表)
   [16] 互動動畫:頁切換滑入/列懸浮/圈選脈衝/彈窗縮放/橫幅滑入(prefers-reduced-motion 全靜)
 v0106 新增(操作員裁決:ready-to-use Copilot 支援功能與提示語):
   [17] ⑤ Copilot 支援頁:預製提示語庫(摘要/回覆/追蹤/會議行動項/週報潤稿/風險分析/
        Teams 更新/控管表健檢)— 一鍵複製,貼進 M365 Copilot(Outlook/Teams/Word)即用;三語
   [18] 情境式提示:專案詳情彈窗「複製 Copilot 提示」= 案號/狀態/佐證自動填入之分析提示;
        圈選浮條第二鍵「Copilot 摘要提示」= 圈選郵件主旨自動列入之摘要提示
   治理不變:本系統不呼叫任何雲端 — 提示語由本地資料生成,由使用者自行貼入其已授權之 Copilot
 v0107 新增(操作員裁決:add important functions and libs into the system):
   [19] 執行日誌:out/workops_run.log append-only(時間-等級-訊息;錯誤自我診斷)
   [20] Windows 桌面通知:跑完右下角氣泡(成功=摘要;失敗=請看 log);非 Windows/失敗靜默略過
   [21] KPI 歷史:out/kpi_history.csv 每跑追加一列(專案/需注意/未回/佇列/關係人)— Excel 直開看趨勢
   [22] -Silent 靜默模式:掃描+對帳+報表+通知,不開瀏覽器(配 WorkOps_Background.vbs 背景執行)
   雲端 Graph/Copilot 線:依材料自身合規要求,IT 申請範本入庫 docs/,核准前休眠不啟用
 v0108 新增(操作員裁決:add watch list dashboard for U/I):
   [23] ⭐ 監看台:①②頁每列有 ☆ 星鍵,點星入列;①頁頂端監看儀表板即時顯示
        被監看之專案燈號/未回天數,一鍵移除;localStorage 跨次記憶(失敗降級單次)
 v0109 新增(操作員裁決 2026/08/08):
   [24] ⑥ 系統矩陣終頁:全流程/動詞/引擎/擷取方法/VMT × 即時狀態一表
   [25] CSV 編碼根治:對外 CSV 全改 utf8BOM(Excel 開中文不再亂碼)
   [26] 控管表拖曳上傳(window I/O):拖 CSV 入①頁 → UTF-8/Big5 自動辨識 → 預覽核對
        → 下載正規化 UTF-8 檔(存回 WorkOps\control_sheet.csv 重跑即對帳)
   [27] 追蹤信自動帶編號:佇列主旨自動嵌 [THR-#####] → 對方回信主旨保留編號 → 掃描歸戶管控
 v0110 新增(操作員裁決:完善串聯引擎/無衝突安裝/自動優化排版):
   [28] 深度鏈與 pm4py venv 即時狀態入⑥矩陣(跑過=綠+時間戳;venv 在位=綠)
   [29] 自動優化排版:資料量大(>60 列)自動緊湊密度;窄螢幕自動摺疊細節欄;
        列印樣式(白底、隱導航、僅當前頁)— prefers-reduced-motion 照舊全靜
 回退:動態 pattern 自動指回 v0109(刪本檔即回退)。
==========================================================================================
#>
param(
    [int]$Days = 14,
    [switch]$NoScan,
    [switch]$NoOpen,
    [switch]$Silent,
    [string]$DraftsFor = "",
    [string]$DraftsTemplate = ""
)
if ($Silent) { $NoOpen = $true }
$ErrorActionPreference = "Continue"
$Here    = $PSScriptRoot
$ViaRoot = Split-Path (Split-Path $Here -Parent) -Parent
$OutDir  = Join-Path $Here "out"
$Control = Join-Path $Here "control_sheet.csv"
if (-not (Test-Path -LiteralPath $Control)) {
    $rootSheet = Join-Path (Split-Path $ViaRoot -Parent) "control_sheet.csv"   # Templates 範例落庫根
    if (Test-Path -LiteralPath $rootSheet) { $Control = $rootSheet }
}
$RunDir  = Join-Path $ViaRoot "VIA_Reports\workops_run"
New-Item -ItemType Directory -Force -Path $RunDir, $OutDir | Out-Null

$LogPath = Join-Path $OutDir "workops_run.log"
function Write-WopsLog { param([string]$Msg, [string]$Level = "INFO")
    try { Add-Content -LiteralPath $LogPath -Value ("{0} - {1} - {2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Level, $Msg) -Encoding UTF8 } catch { }
}
function Send-WopsToast { param([string]$Title, [string]$Msg)
    if (-not ($env:OS -match "Windows")) { return }
    try {
        Add-Type -AssemblyName System.Windows.Forms, System.Drawing
        $n = New-Object System.Windows.Forms.NotifyIcon
        $n.Icon = [System.Drawing.SystemIcons]::Information
        $n.BalloonTipTitle = $Title; $n.BalloonTipText = $Msg; $n.Visible = $true
        $n.ShowBalloonTip(5000)
    } catch { Write-WopsLog ("toast 失敗(略過): " + $_.Exception.Message) "WARN" }
}
Write-WopsLog ("=== v0107 啟動 Days={0} Silent={1} DraftsFor={2}" -f $Days, [bool]$Silent, $DraftsFor)

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  VIA WorkOps x Mail Tracker 統合指揮板 v0115  |  三段追蹤升級鏈 · 異質表頭映射 · 半自動建構" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

# ---- [1/5] 掃描 + 對帳(重用 v001 引擎;Outlook 不在 = 誠實降級)----
$engine = Join-Path $Here "Invoke-VeritasMailOps.ps1"
if (-not $NoScan -and -not $DraftsFor -and (Test-Path -LiteralPath $engine)) {
    Write-Host "[1/5] 掃描 Outlook(唯讀,使用者自身權限)+ 控管表對帳..." -ForegroundColor Yellow
    & $engine -Action Scan -Days $Days
    & $engine -Action Reconcile
    Write-WopsLog "掃描+對帳完成(唯讀)"
} else {
    Write-Host "[1/5] 略過掃描 — 用既有 out\*.csv" -ForegroundColor DarkYellow
}

# ---- [2/5] 讀資料 ----
Write-Host "[2/5] 彙整佐證(專案/追蹤/關係人/控管表)..." -ForegroundColor Yellow
function Read-CsvSafe { param([string]$p)
    if ((Test-Path -LiteralPath $p) -and (Get-Item -LiteralPath $p).Length -gt 0) { return @(Import-Csv -LiteralPath $p -Encoding UTF8) }
    return @()
}
$rec   = Read-CsvSafe (Join-Path $OutDir "reconcile.csv")
$pend  = Read-CsvSafe (Join-Path $OutDir "pending.csv")
$mails = Read-CsvSafe (Join-Path $OutDir "mails.csv")
$stak  = Read-CsvSafe (Join-Path $OutDir "stakeholders.csv")
$ctrl  = Read-CsvSafe $Control

# ---- v0115:異質控管表表頭映射(各行各業欄名自動對齊;對不上者保留原名)----
$SheetAlias = [ordered]@{
    ProjectCode = @("projectcode","專案代號","案號","案件編號","代號","編號","trace_id","wop_id","tracking no","trackingno","code","id")
    ProjectName = @("projectname","專案名稱","案名","名稱","項目","project","task","activity","主題","作業步驟")
    Owner       = @("owner","負責人","對口","承辦人","pm","單位","owner_domain","stakeholder")
    Status      = @("status","狀態","進度","目前狀況","current_stage")
    Progress    = @("progress","完成度","百分比","完成率")
    DueDate     = @("duedate","截止","期限","deadline","預計完成","到期日","due")
    LastUpdated = @("lastupdated","更新日","最後更新","last_comm_date","最後通訊","updated")
}
function ConvertTo-StdSheet { param($rows)
    if (@($rows).Count -eq 0) { return @($rows) }
    $srcCols = @($rows[0].PSObject.Properties.Name)
    $map = @{}
    foreach ($src in $srcCols) {
        $k = $src.Trim().ToLower()
        foreach ($std in $SheetAlias.Keys) {
            if ($map.ContainsValue($std)) { continue }
            if ($SheetAlias[$std] -contains $k) { $map[$src] = $std; break }
        }
        if (-not $map.ContainsKey($src)) {
            foreach ($std in $SheetAlias.Keys) {
                if ($map.ContainsValue($std)) { continue }
                if (@($SheetAlias[$std] | Where-Object { $k -like ("*" + $_ + "*") }).Count -gt 0) { $map[$src] = $std; break }
            }
        }
    }
    return @($rows | ForEach-Object {
        $o = [ordered]@{}
        foreach ($pr in $_.PSObject.Properties) {
            $dst = if ($map.ContainsKey($pr.Name)) { $map[$pr.Name] } else { $pr.Name }
            if (-not $o.Contains($dst)) { $o[$dst] = $pr.Value }
        }
        [pscustomobject]$o
    })
}
$ctrl = ConvertTo-StdSheet $ctrl

# ---- VMT 資料層唯讀附掛(統合;未布建誠實降級)----
$VmtRoot = if ($env:VMT_ROOT) { $env:VMT_ROOT } else { "C:\VIA\VeritasMailTracker" }
$vmt = [ordered]@{ present = $false; root = $VmtRoot; conv = $null; tasks = @(); schedule = @() }
if (Test-Path -LiteralPath $VmtRoot) {
    $vmt.present = $true
    $cs = Join-Path $VmtRoot "reports\convergence_state.json"
    if (Test-Path -LiteralPath $cs) {
        try { $j = Get-Content -LiteralPath $cs -Raw -Encoding UTF8 | ConvertFrom-Json
              $vmt.conv = [ordered]@{ ts = [string]$j.ts; n_issues = [int]$j.n_issues
                                      auto_rate = [double]$j.auto_rate; tiers = $j.tiers } } catch { }
    }
    $pt = Join-Path $VmtRoot "planning_tasks.csv"
    if (Test-Path -LiteralPath $pt) {
        try { $vmt.tasks = @(Get-Content -LiteralPath $pt -Encoding UTF8 | Where-Object { $_ -notmatch "^\s*#" } |
                             ConvertFrom-Csv | Select-Object -First 100) } catch { }
    }
    $sc = Join-Path $VmtRoot "reports\planning_schedule.csv"
    if (Test-Path -LiteralPath $sc) {
        try { $vmt.schedule = @(Import-Csv -LiteralPath $sc -Encoding UTF8 | Select-Object -First 100) } catch { }
    }
    Write-Host ("   VMT 附掛:收斂={0} · 規劃任務 {1} · 排程 {2}(唯讀)" -f $(if($vmt.conv){"在位"}else{"未跑"}), @($vmt.tasks).Count, @($vmt.schedule).Count) -ForegroundColor Green
} else {
    Write-Host "   VMT 資料層未布建(via-vmt-init 可建)— 板上第④頁將顯示引導" -ForegroundColor DarkYellow
}
$pendSorted = @($pend | Sort-Object { $v = 0; [int]::TryParse([string]$_.WaitingDays, [ref]$v) | Out-Null; -$v })
$mailsAll   = @($mails | Select-Object -First 500)
$autoCsv = Join-Path $OutDir "recipients_auto.csv"
$codeRe = [regex]'\b[A-Z]{2,6}[-_ ]?\d{2,6}\b'

# ---- 自動編號 side-car 帳本(append-only 冪等;絕不動 Outlook 原件)----
$LedgerPath = Join-Path $OutDir "workops_id_ledger.json"
$Ledger = [ordered]@{ seq_wop = 0; seq_thr = 0; map = [ordered]@{} }
if (Test-Path -LiteralPath $LedgerPath) {
    try {
        $raw = Get-Content -LiteralPath $LedgerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $Ledger.seq_wop = [int]$raw.seq_wop; $Ledger.seq_thr = [int]$raw.seq_thr
        foreach ($prop in $raw.map.PSObject.Properties) { $Ledger.map[$prop.Name] = [string]$prop.Value }
    } catch { Write-Host "   [警告] 帳本讀取失敗,重新起帳(舊帳本已保留為 .bak)" -ForegroundColor DarkYellow
              Copy-Item -LiteralPath $LedgerPath -Destination ($LedgerPath + ".bak") -Force }
}
$script:LedgerDirty = $false
function Get-WopsId { param([string]$Kind, [string]$Key)
    if ([string]::IsNullOrWhiteSpace($Key)) { return "" }
    $k = "$Kind|$Key"
    if ($Ledger.map.Contains($k)) { return $Ledger.map[$k] }
    if ($Kind -eq "WOP") { $Ledger.seq_wop++; $id = "WOP-{0:d4}" -f $Ledger.seq_wop }
    else                 { $Ledger.seq_thr++; $id = "THR-{0:d5}" -f $Ledger.seq_thr }
    $Ledger.map[$k] = $id; $script:LedgerDirty = $true
    return $id
}
foreach ($r in $rec)  { $r | Add-Member -NotePropertyName WopID -NotePropertyValue (Get-WopsId "WOP" ([string]$r.ProjectCode)) -Force }
foreach ($p in $pendSorted) { $p | Add-Member -NotePropertyName ThrID -NotePropertyValue (Get-WopsId "THR" ([string]$p.CASE_ID)) -Force }
foreach ($m in $mailsAll)   { $m | Add-Member -NotePropertyName ThrID -NotePropertyValue (Get-WopsId "THR" ([string]$m.ConversationID)) -Force }
if ($script:LedgerDirty) {
    ($Ledger | ConvertTo-Json -Depth 4) | Set-Content -LiteralPath $LedgerPath -Encoding UTF8
}
Write-Host ("   編號帳本:WOP {0} 案 · THR {1} 串(side-car,Outlook 原件不動)" -f $Ledger.seq_wop, $Ledger.seq_thr) -ForegroundColor Green

# ---- 圈選模式:-DraftsFor "THR-…,…" → 只為圈選件建草稿,不開板 ----
if ($DraftsFor) {
    $want = @($DraftsFor -split "," | ForEach-Object { $_.Trim().ToUpper() } | Where-Object { $_ })
    $thr2case = @{}
    foreach ($k in $Ledger.map.Keys) { if ($k -like "THR|*") { $thr2case[$Ledger.map[$k]] = $k.Substring(4) } }
    $selQ = @()
    foreach ($id in $want) {
        $case = $thr2case[$id]
        if (-not $case) { Write-Host ("   [略過] 帳本查無 {0}" -f $id) -ForegroundColor DarkYellow; continue }
        $row = $pendSorted | Where-Object { [string]$_.CASE_ID -eq $case } | Select-Object -First 1
        $to = ""; $subj = ""
        if ($row) { $to = [string]$row.TO; $subj = [string]$row.Subject }
        else {
            $m2 = $mails | Where-Object { [string]$_.ConversationID -eq $case } | Select-Object -First 1
            if ($m2) { $to = [string]$m2.SenderEmail; $subj = [string]$m2.Subject }
        }
        if (-not $to) { Write-Host ("   [略過] {0} 無對象可回" -f $id) -ForegroundColor DarkYellow; continue }
        $mm = $codeRe.Match($subj.ToUpper())
        $code2 = $(if ($mm.Success) { $mm.Value -replace "[_ ]", "-" } else { "" })
        $selQ += [pscustomobject]@{
            CaseID = $id; ProjectCode = $code2
            ProjectName = $(if ($code2) { $code2 } else { "專案" })
            To = $to; Cc = ""; Template = $(if ($DraftsTemplate) { $DraftsTemplate } else { "approval_request_v2" })   # 圈選=必回選擇題豐富版;-DraftsTemplate 可指定
            OrigSubject = $(if ($subj -match [regex]::Escape($id)) { $subj } else { ("{0} [{1}]" -f $subj, $id) })
            SentOn = ""; WaitingDays = ""
        }
    }
    if (@($selQ).Count -eq 0) { Write-Host "[總結] 圈選件皆無法成稿(見上方略過原因)。" -ForegroundColor Yellow; return }
    $selQ | Export-Csv -LiteralPath $autoCsv -NoTypeInformation -Encoding utf8BOM
    Write-Host ("   圈選 {0} 件 → {1}" -f @($selQ).Count, $autoCsv) -ForegroundColor Green
    & $engine -Action FollowUp -RecipientsCsv $autoCsv
    Write-Host "[總結] 圈選草稿已建於 Outlook(只建草稿,你過目後親自寄)。" -ForegroundColor Green
    return
}

# ---- [3/5] 三段追蹤佇列(v0115:T1 追蹤/T2 跟進/T3 緊急;工作日計;絕不代寄)----
Write-Host "[3/5] 預填三段追蹤佇列(T1/T2/T3 工作日制;絕不代寄)..." -ForegroundColor Yellow
$WtCfg = @{ t1_days = 3; t2_days = 5; t3_days = 7; use_business_days = $true }
$wtPath = Join-Path $Here "engines\watchtower_params.json"
if (Test-Path -LiteralPath $wtPath) {
    try {
        $wtj = Get-Content -LiteralPath $wtPath -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($k in @("t1_days", "t2_days", "t3_days")) { if ($wtj.$k) { $WtCfg[$k] = [int]$wtj.$k } }
        if ($null -ne $wtj.use_business_days) { $WtCfg.use_business_days = [bool]$wtj.use_business_days }
    } catch { }
}
$Holidays = @()
$holPath = Join-Path $Here "engines\holidays_tw.txt"
if (Test-Path -LiteralPath $holPath) {
    $Holidays = @(Get-Content -LiteralPath $holPath -Encoding UTF8 |
        Where-Object { $_ -match "^\d{4}-\d{2}-\d{2}" } | ForEach-Object { $_.Substring(0, 10) })
}
function Get-WaitBusinessDays { param([string]$SentOn)
    $d = [datetime]::MinValue
    if (-not [datetime]::TryParse($SentOn, [ref]$d)) { return -1 }
    $n = 0; $cur = $d.Date.AddDays(1)
    while ($cur -le (Get-Date).Date) {
        if ($cur.DayOfWeek -ne "Saturday" -and $cur.DayOfWeek -ne "Sunday" -and
            ($Holidays -notcontains $cur.ToString("yyyy-MM-dd"))) { $n++ }
        $cur = $cur.AddDays(1)
    }
    return $n
}
$queue = @()
foreach ($p in $pendSorted) {
    $wd = 0; [int]::TryParse([string]$p.WaitingDays, [ref]$wd) | Out-Null
    $bd = if ($WtCfg.use_business_days) { Get-WaitBusinessDays ([string]$p.SentOn) } else { $wd }
    if ($bd -lt 0) { $bd = $wd }
    $stage = ""; $tpl = ""
    if ($bd -ge $WtCfg.t3_days)     { $stage = "T3"; $tpl = "urgent_escalation" }
    elseif ($bd -ge $WtCfg.t2_days) { $stage = "T2"; $tpl = "followup_firm" }
    elseif ($bd -ge $WtCfg.t1_days) { $stage = "T1"; $tpl = "followup" }
    if (-not $tpl) { continue }
    $m = $codeRe.Match(([string]$p.Subject).ToUpper())
    $code = if ($m.Success) { $m.Value -replace "[_ ]", "-" } else { "" }
    $name = ""
    if ($code) {
        $hit = $rec | Where-Object { ([string]$_.ProjectCode).ToUpper() -eq $code } | Select-Object -First 1
        if ($hit) { $name = [string]$hit.ProjectName }
    }
    $queue += [pscustomobject]@{
        CaseID = [string]$p.ThrID; ProjectCode = $code; ProjectName = $name; To = [string]$p.TO; Cc = ""
        Template = $tpl; Stage = $stage; BizDays = $bd
        OrigSubject = $(if (([string]$p.Subject) -match [regex]::Escape([string]$p.ThrID)) { [string]$p.Subject } else { ("{0} [{1}]" -f [string]$p.Subject, [string]$p.ThrID) })
        SentOn = [string]$p.SentOn; WaitingDays = $wd
    }
}
if (@($queue).Count -gt 0) {
    $queue | Export-Csv -LiteralPath $autoCsv -NoTypeInformation -Encoding utf8BOM
    Write-Host ("   佇列 {0} 件 → {1}(via-workops drafts 一次產生草稿)" -f @($queue).Count, $autoCsv) -ForegroundColor Green
} else {
    Write-Host "   無達 T1 工作日門檻之未回件,佇列空。" -ForegroundColor DarkGray
}

# ---- v0113:⓪系統流程頁資料(互鏈/決策/報告/註冊/命名候選)----
$thrLinks = 0
$thrMapPath = Join-Path $Here "out\thr_case_map.json"
if (Test-Path -LiteralPath $thrMapPath) {
    try { $thrLinks = @(((Get-Content -LiteralPath $thrMapPath -Raw -Encoding UTF8 | ConvertFrom-Json).map).PSObject.Properties).Count } catch { $thrLinks = 0 }
}
$decInfo = [ordered]@{ total = 0; done = 0 }
$decCsvPath = Join-Path $Here "out\decision_log.csv"
if (Test-Path -LiteralPath $decCsvPath) {
    try {
        $decRows = @(Import-Csv -LiteralPath $decCsvPath)
        $decInfo = [ordered]@{ total = @($decRows).Count; done = @($decRows | Where-Object { [string]$_."狀態" -eq "DONE" }).Count }
    } catch { }
}
$repScan = ""
$scanRoot = Join-Path $Here "out\deep\scanrange"
$newestRun = Get-ChildItem -Path $scanRoot -Directory -ErrorAction SilentlyContinue | Sort-Object Name | Select-Object -Last 1
if ($newestRun -and (Test-Path -LiteralPath (Join-Path $newestRun.FullName "VIA_Outlook_TimeRange_ReadOnly_Report.html"))) {
    $repScan = "../../functional modules/WorkOps/out/deep/scanrange/" + $newestRun.Name + "/VIA_Outlook_TimeRange_ReadOnly_Report.html"
}
$repEngine    = $(if (Test-Path -LiteralPath (Join-Path $Here "out\deep\engine_out\engine_report.html"))    { "../../functional modules/WorkOps/out/deep/engine_out/engine_report.html" } else { "" })
$repAnalytics = $(if (Test-Path -LiteralPath (Join-Path $Here "out\deep\engine_out\analytics_report.html")) { "../../functional modules/WorkOps/out/deep/engine_out/analytics_report.html" } else { "" })
$regEng = 0
$regPath = Join-Path $ViaRoot "supportive modules\registry\VIA_AutoCode_Registry_v0100.json"
if (Test-Path -LiteralPath $regPath) {
    try { $regEng = @(((Get-Content -LiteralPath $regPath -Raw -Encoding UTF8 | ConvertFrom-Json).components).PSObject.Properties | Where-Object { $_.Name -like "引擎|*" }).Count } catch { }
}
$wopTop = @(); $wopN = 0
$wopRegP = Join-Path $Here "out\wop_registry.json"
if (Test-Path -LiteralPath $wopRegP) {
    try {
        $wreg = Get-Content -LiteralPath $wopRegP -Raw -Encoding UTF8 | ConvertFrom-Json
        $wprops = @($wreg.projects.PSObject.Properties)
        $wopN = $wprops.Count
        $wopTop = @($wprops | Sort-Object { -1 * @($_.Value.thr).Count } | Select-Object -First 40 | ForEach-Object {
            [ordered]@{ id = $_.Name; name = [string]$_.Value.label; n = @($_.Value.thr).Count
                        ok = ([string]$_.Value.status -eq "confirmed") } })
    } catch { }
}
$namingTop = @(); $namingCustom = @()
$nmPath2 = Join-Path $Here "out\workops_naming.json"
if (Test-Path -LiteralPath $nmPath2) {
    try {
        $nm2 = Get-Content -LiteralPath $nmPath2 -Raw -Encoding UTF8 | ConvertFrom-Json
        $namingTop = @($nm2.entries.PSObject.Properties | Where-Object { $_.Name -like "CASE-*" } | Select-Object -First 40 | ForEach-Object {
            [ordered]@{ id = $_.Name; name = [string]$(if ($_.Value.approved) { $_.Value.approved } else { $_.Value.proposed }); ok = [bool]$_.Value.approved } })
        $namingCustom = @($nm2.custom_groups | Where-Object { $_ } | ForEach-Object { [ordered]@{ name = [string]$_.name; keyword = [string]$_.keyword } })
    } catch { }
}

$data = [ordered]@{
    generated      = (Get-Date).ToString("yyyy/MM/dd HH:mm")
    days           = $Days
    has_control    = (Test-Path -LiteralPath $Control)
    projects       = $rec
    pending        = $pendSorted
    mails_all      = $mailsAll
    stakeholders   = $stak
    control_rows   = $ctrl
    drafts_queue   = $queue
    vmt            = $vmt
    id_counts      = [ordered]@{ wop = $Ledger.seq_wop; thr = $Ledger.seq_thr }
    deep           = [ordered]@{
        present = (Test-Path -LiteralPath (Join-Path $Here "out\deep\engine_out\engine_report.html"))
        ts = $(if (Test-Path -LiteralPath (Join-Path $Here "out\deep\engine_out\engine_report.html")) {
                (Get-Item -LiteralPath (Join-Path $Here "out\deep\engine_out\engine_report.html")).LastWriteTime.ToString("yyyy/MM/dd HH:mm") } else { "" }) }
    pm_venv        = (Test-Path -LiteralPath (Join-Path $Here "engines\.venv_pm\Scripts\python.exe"))
    dot_ready      = ((Get-ChildItem -Path (Join-Path $Here "engines\.graphviz") -Filter "dot.exe" -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1) -ne $null -or (Get-Command dot -ErrorAction SilentlyContinue) -ne $null)
    envmgr_ran     = (Test-Path -LiteralPath (Join-Path $Here "out\envmanager\VIA_EnvManager_Health.json"))
    forge_ready    = (Test-Path -LiteralPath (Join-Path (Split-Path (Split-Path $Here -Parent) -Parent) "supportive modules\VIA_Forge\via_server.py"))
    naming         = $(
        $nmPath = Join-Path $Here "out\workops_naming.json"
        if (Test-Path -LiteralPath $nmPath) {
            try {
                $nm = Get-Content -LiteralPath $nmPath -Raw -Encoding UTF8 | ConvertFrom-Json
                $ents = @($nm.entries.PSObject.Properties)
                [ordered]@{ total = $ents.Count; approved = @($ents | Where-Object { $_.Value.approved }).Count }
            } catch { [ordered]@{ total = 0; approved = 0 } }
        } else { [ordered]@{ total = 0; approved = 0 } })
    thr_links      = $thrLinks
    decisions      = $decInfo
    reports        = [ordered]@{ scan = $repScan; engine = $repEngine; analytics = $repAnalytics }
    reg            = [ordered]@{ engines = $regEng }
    naming_top     = $namingTop
    naming_custom  = $namingCustom
    wop            = [ordered]@{ total = $wopN }
    wop_top        = $wopTop
}
$json = ($data | ConvertTo-Json -Depth 6 -Compress)
if ($null -eq $json) { $json = "{}" }
$json = $json.Replace("</", "<\/")

# ---- [4/5] 三頁式三語 Workbench HTML ----
Write-Host "[4/5] 生成指揮板(繁/简/EN)..." -ForegroundColor Yellow
$html = @'
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA WorkOps × Mail Tracker 統合指揮板</title>
<style>
:root{--bg:#f2f1ec;--panel:#f5f4f0;--card:#fbfaf7;--line:#dcdad4;--line2:#c8c5bd;
--ink:#1b1a17;--mut:#6b6860;--mut2:#8a877f;--green:#4f9465;--green2:#3f7a52;
--blue:#4c78a8;--red:#c4634f;--amber:#bf8f33;--teal:#3d8f8f;--violet:#7a6daa;
--sans:'Segoe UI','PingFang TC','Microsoft JhengHei','Noto Sans TC',system-ui,sans-serif;
--mono:'Cascadia Code','Consolas',ui-monospace,monospace}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:var(--sans);font-size:13px}
.mast{border-bottom:1px solid var(--line2);background:var(--panel);padding:14px 26px;display:flex;align-items:center;gap:14px}
.seal{width:34px;height:34px;background:var(--ink);color:#fff;display:flex;align-items:center;justify-content:center;font-size:17px;border-radius:4px}
.mast h1{font-size:16px;font-weight:600}.mast .sub{font-size:11px;color:var(--mut)}
.lang{margin-left:auto;display:flex;gap:4px}
.lang button{border:1px solid var(--line2);background:var(--card);padding:4px 10px;border-radius:6px;cursor:pointer;font-size:11px;color:var(--mut)}
.lang button.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.strip{height:3px;display:flex}.strip i{flex:1}
.tabs{display:flex;gap:4px;padding:12px 26px 0;border-bottom:1px solid var(--line);background:var(--panel)}
.tab{padding:9px 18px;font-size:13px;font-weight:600;color:var(--mut);cursor:pointer;border:1px solid transparent;border-bottom:none;border-radius:6px 6px 0 0}
.tab.on{color:var(--ink);background:var(--bg);border-color:var(--line)}
.page{display:none;padding:20px 26px;max-width:1180px;margin:0 auto}.page.on{display:block}
.band{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.chip{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:9px 16px;min-width:104px}
.chip b{display:block;font-size:20px;font-weight:600}.chip span{font-size:11px;color:var(--mut)}
.banner{background:#f7ecdc;border:1px solid var(--amber);border-radius:9px;padding:11px 16px;margin-bottom:14px;font-weight:600;color:#7a5a1f}
.banner.calm{background:#e9f0ea;border-color:var(--green);color:var(--green2)}
.banner.info{background:#e8edf3;border-color:var(--blue);color:#2f4a66}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:9px;overflow:hidden;margin-bottom:14px}
th{font-family:var(--mono);font-size:10px;text-transform:uppercase;color:var(--mut2);text-align:left;padding:8px 12px;border-bottom:1px solid var(--line);background:var(--panel)}
td{padding:9px 12px;border-bottom:1px solid var(--line);vertical-align:top}
tr:last-child td{border-bottom:none}
.lt{display:inline-block;padding:2px 10px;border-radius:99px;font-size:11px;font-weight:600}
.lt.g{background:#e9f0ea;color:var(--green2)}.lt.a{background:#f5ecd9;color:#7a5a1f}
.lt.r{background:#f5e3df;color:#8a3a2c}.lt.n{background:#ecebe6;color:var(--mut)}
.ev{font-size:11.5px;color:var(--mut);margin-top:3px}
.days{font-family:var(--mono);font-weight:700}
.guide{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:22px;max-width:640px}
.guide h3{font-size:14px;margin-bottom:10px}.guide li{margin:6px 0 6px 18px;color:var(--mut)}
.mono{font-family:var(--mono)}.mut{color:var(--mut)}
.sec{font-size:12px;font-weight:600;color:var(--mut);margin:18px 0 8px;text-transform:uppercase;letter-spacing:.04em}
.foot{text-align:center;color:var(--mut2);font-size:10px;font-family:var(--mono);padding:18px}
tr[data-thr]{cursor:pointer}
tr.selrow td{background:#e8edf3!important}
tr.selrow td:first-child{box-shadow:inset 3px 0 0 var(--blue)}
.selbar{position:fixed;right:18px;bottom:18px;background:var(--ink);color:#fff;border-radius:12px;padding:12px 16px;display:none;align-items:center;gap:12px;box-shadow:0 6px 24px rgba(27,26,23,.25);z-index:50;font-size:13px}
.selbar button{background:var(--green);color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:700;cursor:pointer}
.selbar .clr{background:transparent;border:1px solid #6b6860;font-weight:400}
.selhint{font-size:10.5px;color:#c8c5bd}
.steps{display:flex;gap:0;padding:10px 26px;background:var(--panel);border-bottom:1px solid var(--line);overflow-x:auto}
.step{display:flex;align-items:center;gap:7px;font-size:11px;color:var(--mut);white-space:nowrap}
.step .dot{width:20px;height:20px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:11px;background:#ecebe6;color:var(--mut2);border:1px solid var(--line2)}
.step.done .dot{background:var(--green);color:#fff;border-color:var(--green)}
.step.warn .dot{background:var(--amber);color:#fff;border-color:var(--amber)}
.step .bar{width:26px;height:1px;background:var(--line2);margin:0 8px}
.filters{display:flex;gap:10px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
.filters select{border:1px solid var(--line2);background:var(--card);color:var(--ink);border-radius:8px;padding:6px 10px;font-size:12px;font-family:var(--sans)}
.filters label{font-size:11px;color:var(--mut)}
.cb{width:15px;height:15px;border:1.5px solid var(--line2);border-radius:4px;display:inline-block;vertical-align:middle;pointer-events:none;background:var(--card);position:relative}
tr.selrow .cb{background:var(--blue);border-color:var(--blue)}
tr.selrow .cb::after{content:"✓";color:#fff;font-size:11px;position:absolute;left:2px;top:-2px}
.dchip{display:inline-block;border:1px solid var(--line2);border-radius:99px;padding:3px 12px;font-size:11.5px;cursor:pointer;color:var(--mut);margin-right:6px;user-select:none}
.dchip.on{background:var(--ink);color:#fff;border-color:var(--ink)}
.mback{position:fixed;inset:0;background:rgba(27,26,23,.35);display:none;align-items:center;justify-content:center;z-index:80}
.mback.on{display:flex}
.modal{background:var(--card);border:1px solid var(--line2);border-radius:14px;max-width:560px;width:92%;padding:22px 24px;box-shadow:0 18px 60px rgba(27,26,23,.3)}
.modal h3{font-size:15px;margin-bottom:4px}.modal .mrow{margin:9px 0;font-size:12.5px}.modal .mk{color:var(--mut2);font-size:10.5px;text-transform:uppercase;font-family:var(--mono)}
.modal .mclose{float:right;cursor:pointer;border:none;background:transparent;font-size:16px;color:var(--mut)}
.expbtn{border:none;background:var(--blue);color:#fff;border-radius:8px;padding:8px 14px;font-size:12.5px;font-weight:700;cursor:pointer}
.pgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:12px}
.pcard{background:var(--card);border:1px solid var(--line);border-radius:11px;padding:15px 16px;display:flex;flex-direction:column;gap:8px}
.pcard h4{font-size:13px}.pcard .pp{font-size:11.5px;color:var(--mut);white-space:pre-wrap;flex:1;font-family:var(--mono);background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:9px 11px;max-height:150px;overflow:auto}
.pcard button{align-self:flex-start;border:none;background:var(--teal);color:#fff;border-radius:8px;padding:7px 13px;font-size:12px;font-weight:700;cursor:pointer}
.copbtn{background:var(--teal)!important}
.star{cursor:pointer;font-size:15px;color:var(--line2);user-select:none;padding:0 3px}
.star.on{color:var(--amber)}
.wband{background:var(--card);border:1px solid var(--amber);border-radius:11px;padding:13px 16px;margin-bottom:14px}
.wband h4{font-size:12.5px;color:#7a5a1f;margin-bottom:9px;text-transform:uppercase;letter-spacing:.04em}
.wgrid{display:flex;gap:9px;flex-wrap:wrap}
.wcard{background:var(--panel);border:1px solid var(--line);border-radius:9px;padding:8px 12px;display:flex;align-items:center;gap:9px;font-size:12px}
.wcard .wx{cursor:pointer;color:var(--mut2);font-size:13px}
.wcard .wx:hover{color:var(--red)}
.dz{border:2px dashed var(--line2);border-radius:11px;padding:14px 16px;margin-bottom:14px;color:var(--mut);font-size:12px;text-align:center;background:var(--panel);transition:border-color .15s ease,background .15s ease}
.dz.hot{border-color:var(--blue);background:#e8edf3;color:var(--blue)}
.mx td:first-child{font-weight:600}
.mxs{font-family:var(--mono);font-size:11px}
body.dense{font-size:12px}
body.dense td{padding:5px 9px}body.dense th{padding:5px 9px}
body.dense .chip{padding:6px 12px;min-width:88px}body.dense .chip b{font-size:16px}
@media (max-width:900px){.ev{display:none}.chip{min-width:80px}.page{padding:14px 12px}.mast{padding:10px 12px}}
@media print{.tabs,.lang,.selbar,.steps,.dz,.foot,.star{display:none!important}
 body{background:#fff}.page{display:none}.page.on{display:block}
 table{border:1px solid #999}th,td{border-bottom:1px solid #ccc}}
@media (prefers-reduced-motion: no-preference){
 .page.on{animation:pgIn .28s ease}
 @keyframes pgIn{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:none}}
 tbody tr{transition:transform .12s ease,box-shadow .12s ease}
 tbody tr:hover{transform:translateY(-1px);box-shadow:0 2px 10px rgba(27,26,23,.08)}
 tr.selrow{animation:pulse .32s ease}
 @keyframes pulse{0%{transform:scale(1)}45%{transform:scale(1.006)}100%{transform:scale(1)}}
 .banner{animation:pgIn .32s ease}
 .selbar{animation:barIn .26s ease}
 @keyframes barIn{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
 .mback.on .modal{animation:mIn .22s ease}
 @keyframes mIn{from{opacity:0;transform:scale(.96)}to{opacity:1;transform:none}}
 .step .dot{transition:background .3s ease}
}
.flowwrap{margin:10px 0}
.flrow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;margin:8px 0}
.fnode{border:1.5px solid #c9c5ba;border-radius:9px;padding:7px 12px;font-size:12.5px;background:#fff}
.fnode[data-go]{cursor:pointer}
.fnode b{display:block;font-size:12.5px}
.fnode span{font-size:10.5px;color:#8a877f}
.fnode.g{border-color:#4f9465;box-shadow:inset 3px 0 0 #4f9465}
.fnode.a{border-color:#bf8f33;box-shadow:inset 3px 0 0 #bf8f33}
.fnode.n{border-color:#b7b3a8;opacity:.72}
.farr{color:#8a877f;font-size:15px}
.rptlinks a{display:inline-block;margin:4px 8px 4px 0;padding:7px 12px;border:1px solid #c9c5ba;border-radius:8px;font-size:12.5px;color:#1b1a17;text-decoration:none;background:#fff}
.rptlinks a.off{opacity:.5;pointer-events:none}
.regchips{display:flex;flex-wrap:wrap;gap:8px;margin:8px 0}
.pick{margin:0 0 10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.pick select{padding:6px 8px;border:1px solid #c9c5ba;border-radius:7px;font-size:12.5px;background:#fff}
.seminm{width:95%;border:1px solid #c9c5ba;border-radius:6px;padding:4px 6px;font-size:12px;background:#fff}
@media (prefers-reduced-motion: no-preference){
 .fnode.a{animation:fpulse 1.8s ease infinite}
 @keyframes fpulse{0%,100%{box-shadow:inset 3px 0 0 #bf8f33}50%{box-shadow:inset 3px 0 0 #bf8f33,0 0 0 3px rgba(191,143,51,.18)}}
 .farr{animation:fdash 1.3s ease infinite}
 @keyframes fdash{0%,100%{transform:translateX(0)}50%{transform:translateX(3px)}}
 .fnode[data-go]:hover{transform:translateY(-1px);transition:transform .12s ease}
}
</style>
</head>
<body>
<div class="mast"><div class="seal">務</div>
 <div><h1 id="ttl"></h1><div class="sub" id="sub"></div></div>
 <div class="lang"><button data-l="zh" class="on">繁</button><button data-l="cn">简</button><button data-l="en">EN</button></div></div>
<div class="strip"><i style="background:#4c78a8"></i><i style="background:#4f9465"></i><i style="background:#c4634f"></i><i style="background:#bf8f33"></i><i style="background:#3d8f8f"></i><i style="background:#7a6daa"></i></div>
<div class="steps" id="steps"></div>
<div class="tabs">
 <div class="tab on" data-p="p0"></div>
 <div class="tab" data-p="p1"></div>
 <div class="tab" data-p="p2"></div>
 <div class="tab" data-p="p3"></div>
 <div class="tab" data-p="p4"></div>
 <div class="tab" data-p="p5"></div>
 <div class="tab" data-p="p6"></div>
</div>
<div class="page on" id="p0"></div>
<div class="page" id="p1"></div>
<div class="page" id="p2"></div>
<div class="page" id="p3"></div>
<div class="page" id="p4"></div>
<div class="page" id="p5"></div>
<div class="page" id="p6"></div>
<div class="foot">VIA WorkOps · read-only · drafts never auto-sent · run-local</div>
<div class="mback" id="mback"><div class="modal" id="modal"></div></div>
<div class="selbar" id="selbar"><div><b id="selN"></b><div class="selhint" id="selHint"></div></div>
 <button id="selCopy"></button><button id="selCop" class="copbtn"></button><button class="clr" id="selClr"></button></div>
<script>
var DATA = __VIA_DATA__;
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function arr(x){return x==null?[]:(Array.isArray(x)?x:[x]);}
var P=arr(DATA.projects),PD=arr(DATA.pending),MA=arr(DATA.mails_all),ST=arr(DATA.stakeholders),CT=arr(DATA.control_rows),DQ=arr(DATA.drafts_queue);

var T={
zh:{ttl:"VIA WorkOps 指揮板",sub:"產生 {g} · 佐證窗 {d} 天 · 專案 {p} 案 · 未回追蹤 {q} 件",
 t0:"⓪ 系統流程",t1:"① 專案指揮",t2:"② 追蹤哨",t3:"③ 範疇與關係人",
 flowT:"全系統運作流程 — 點節點跳轉分頁;顏色=模組即時狀態(綠=就緒 · 黃=待跑 · 灰=休眠)",flowHint:"動畫依系統減震設定自動靜止;狀態由每次產板即時計算",rptT:"正本報告(點開;同機路徑)",rpt1:"Outlook 唯讀掃描報告",rpt2:"超級引擎報告",rpt3:"進階分析報告",regT:"註冊與編號即況",semiT:"工作專案半自動建構(候選 → 核對勾選 → 複製入控管表)",semiHint:"五個來源:WOP 歸戶(引擎自動) · 控管表現有列 · 郵件叢集歸納 · 命名帳本(已核對名優先) · 自建歸類。系統先自動分類預勾,你只核對(名稱可直接改);複製後貼進 control_sheet.csv — 系統不代寫控管表。",semiBtn:"複製勾選列(控管表格式)",semiH:["✓","來源","專案代號","專案名稱(可改)","佐證"],semiNone:"(尚無候選 — 先跑 via-workops all 產生郵件叢集與命名帳本)",accT:"如何再提高自動分類準確度(降低校正機率)",accL:["命名核對迴圈:names propose → 核對表改名 → names apply;已核對名永不被覆蓋,下輪直接命中","自建歸類規則:via-workops names add 名稱 關鍵字 — 規則優先於統計歸納","主旨帶代號:發信主旨帶 ABC-123 型代號,叢集歸納即與控管表完全對齊","互鏈累積:THR↔CASE 對映每輪自動擴充(thr_case_map),歷史越厚命中越準"],pickT:"草稿範本",pickHint:"圈選件套用之範本;留預設=豐富版必回選擇題;approval_request* 自動附 Outlook 投票鈕(原生勾選)",
 cases:"控管案件",ok:"一致",warn:"需注意",bad:"矛盾",none:"無佐證/不全",
 hotB:"{n} 案需要你的眼睛(矛盾或待更新)— 已排前列",calmB:"控管表與郵件佐證全數一致",
 h1:["☆","燈","編號","案號 / 案名","負責人","控管表狀態","郵件最後活動","往來","系統建議"],
 upd:"更新日",noCtrl:"尚未接上控管表",g1:"把 control_sheet.csv 放到 WorkOps 資料夾(或 via-workops Templates 產生範例)",
 g2:"再跑一次 via-workops — 系統自動吃入並交叉核對",g3:"之後控管表由本頁代讀,你不需要再開 Excel",
 urgB:"{n} 件寄出 ≥3 天未獲回覆 — 草稿已預填,執行 via-workops drafts 一次產生(只建草稿,絕不代寄)",
 calmQ:"目前沒有等待回覆超過 3 天的信",
 h2:["☆","✓","燈","編號","主旨","對象","寄出時間","已等","狀態"],ovd:"逾期",due:"該追了",obs:"觀察",nr:"未回覆",
 dqT:"草稿佇列(預填完成,待你過目)",h2b:["段","識別碼","案號","範本","收件人","原主旨","已等(工作日)"],
 dqNote:"系統只建 Outlook 草稿(.Display/.Save),永不 .Send — 你微調後親自寄。預填=案號/對象/範本/敬語,要改的只剩重點一兩句。",
 inT:"最近收到(自動記錄)",h3:["✓","時間","寄件者","主旨","未讀"],unread:"未讀",
 scT:"範疇歸納:郵件叢集 × 控管表覆蓋",h4:["叢集代號","郵件數","關係人數","控管表","裁決"],
 inC:"已控管",missC:"遺漏 — 建議建案",scNote:"從郵件主旨自動歸納專案代號;「遺漏」= 郵件中活躍但控管表沒有的範疇。",
 skT:"利害關係人彙總(全域)",h5:["Email","網域","來信數","最後來信"],
 skPT:"依專案歸戶",h6:["叢集代號","關係人"],empty:"(本窗無資料)",selN:"已圈選 {n} 件",selBtn:"複製草稿指令",selClr:"清除",selHint:"點列圈選/再點取消 · 指令貼回 PowerShell(只建草稿不寄)",copied:"已複製!回 PowerShell 貼上執行",t4:"④ 郵件追蹤 VMT",vmtOff:"VMT 資料層未布建",vmtG1:"跑一次 via-vmt-init 建立資料層(C:\\VIA\\VeritasMailTracker)",vmtG2:"之後 via-vmt 產生收斂與排程,本頁自動附掛(唯讀)",convT:"收斂分級(郵件追蹤自動化)",autoR:"自動化率",cpmT:"CPM 排程(關鍵路徑紅 · LATE=依現況排不進)",h7:["ISS","案件","工期","Slack","關鍵",  "開始","完成","Due","遲"],loadT:"負載對照(容量可視化)",h8:["負責人","控管案","需注意","未回件","負載"],ovl:"過載",okl:"正常",loadNote:"需注意 ≥3 亮紅 — 參考資源最佳化實務:先重分配再加人",stScan:"掃描",stRec:"對帳",stId:"編號",stQ:"草稿佇列",stRep:"週報",fOwner:"負責人",fLight:"燈級",fAll:"全部",decT:"你的決定(選擇題;不回寫控管表)",dAdopt:"採納",dRej:"不採納",dHold:"擱置",expDec:"匯出決定 CSV",decN:"已作答 {n} 題",mTitle:"專案詳情",mClose:"關閉",clickHint:"點任一列看詳情+作答",t5:"⑤ Copilot 支援",copT:"預製提示語庫 — 複製後貼進 M365 Copilot(Outlook/Teams/Word)即用",copNote:"本系統不連任何雲端:提示語由本地資料生成,你自行貼入已授權的 Copilot;寄出前一律人工過目",copCopy:"複製提示",copCase:"複製 Copilot 提示(帶本案資料)",copSel:"Copilot 摘要提示",watchT:"監看台(你釘選的重點)",watchE:"點列上的 ☆ 即可把專案或郵件釘進監看台",wDays:"已等 {n} 天",wGone:"(本窗已無此資料)",t6:"⑥ 系統矩陣",mxT:"全流程 × 功能 × 工具 × 即時狀態",mxH:["類別","項目","狀態","說明 / 指令"],dzT:"把控管表 CSV 拖到這裡(或點擊選檔)— 自動辨識 UTF-8 / Big5,預覽核對後下載正規化檔",dzPrev:"控管表預覽(前 20 列,{enc} 解碼,{n} 列)— 核對無誤後:",dzDl:"下載正規化 UTF-8 控管表",dzHint:"下載後存為 functional modules\\WorkOps\\control_sheet.csv,重跑 via-workops 即完成對帳",dzBad:"讀取失敗:非 CSV 或編碼無法辨識"},
cn:{ttl:"VIA WorkOps 指挥板",sub:"生成 {g} · 证据窗 {d} 天 · 项目 {p} 案 · 未回跟踪 {q} 件",
 t0:"⓪ 系统流程",t1:"① 项目指挥",t2:"② 跟踪哨",t3:"③ 范畴与关系人",
 flowT:"全系统运作流程 — 点节点跳转分页;颜色=模块实时状态(绿=就绪 · 黄=待跑 · 灰=休眠)",flowHint:"动画依系统减震设定自动静止;状态由每次产板实时计算",rptT:"正本报告(点开;同机路径)",rpt1:"Outlook 只读扫描报告",rpt2:"超级引擎报告",rpt3:"进阶分析报告",regT:"注册与编号实况",semiT:"工作项目半自动建构(候选 → 核对勾选 → 复制入管控表)",semiHint:"五个来源:WOP 归户(引擎自动) · 管控表现有行 · 邮件簇归纳 · 命名账本(已核对名优先) · 自建归类。系统先自动分类预勾,你只核对(名称可直接改);复制后贴进 control_sheet.csv — 系统不代写管控表。",semiBtn:"复制勾选行(管控表格式)",semiH:["✓","来源","项目代号","项目名称(可改)","证据"],semiNone:"(尚无候选 — 先跑 via-workops all 生成邮件簇与命名账本)",accT:"如何再提高自动分类准确度(降低校正概率)",accL:["命名核对回路:names propose → 核对表改名 → names apply;已核对名永不被覆盖,下轮直接命中","自建归类规则:via-workops names add 名称 关键字 — 规则优先于统计归纳","主题带代号:发信主题带 ABC-123 型代号,簇归纳即与管控表完全对齐","互链累积:THR↔CASE 对映每轮自动扩充(thr_case_map),历史越厚命中越准"],pickT:"草稿模板",pickHint:"圈选件套用之模板;留默认=丰富版必回选择题;approval_request* 自动附 Outlook 投票钮(原生勾选)",
 cases:"管控案件",ok:"一致",warn:"需注意",bad:"矛盾",none:"无证据/不全",
 hotB:"{n} 案需要你的眼睛(矛盾或待更新)— 已排前列",calmB:"管控表与邮件证据全部一致",
 h1:["☆","灯","编号","案号 / 案名","负责人","管控表状态","邮件最后活动","往来","系统建议"],
 upd:"更新日",noCtrl:"尚未接上管控表",g1:"把 control_sheet.csv 放到 WorkOps 文件夹(或 via-workops Templates 生成示例)",
 g2:"再跑一次 via-workops — 系统自动吃入并交叉核对",g3:"之后管控表由本页代读,你不需要再开 Excel",
 urgB:"{n} 件寄出 ≥3 天未获回复 — 草稿已预填,执行 via-workops drafts 一次生成(只建草稿,绝不代发)",
 calmQ:"目前没有等待回复超过 3 天的信",
 h2:["☆","✓","灯","编号","主题","对象","寄出时间","已等","状态"],ovd:"逾期",due:"该追了",obs:"观察",nr:"未回复",
 dqT:"草稿队列(预填完成,待你过目)",h2b:["段","识别码","案号","模板","收件人","原主题","已等(工作日)"],
 dqNote:"系统只建 Outlook 草稿,永不代发 — 你微调后亲自发送。预填=案号/对象/模板/敬语。",
 inT:"最近收到(自动记录)",h3:["✓","时间","寄件者","主题","未读"],unread:"未读",
 scT:"范畴归纳:邮件簇 × 管控表覆盖",h4:["簇代号","邮件数","关系人数","管控表","裁决"],
 inC:"已管控",missC:"遗漏 — 建议建案",scNote:"从邮件主题自动归纳项目代号;「遗漏」= 邮件中活跃但管控表没有的范畴。",
 skT:"利害关系人汇总(全域)",h5:["Email","域名","来信数","最后来信"],
 skPT:"按项目归户",h6:["簇代号","关系人"],empty:"(本窗无数据)",selN:"已圈选 {n} 件",selBtn:"复制草稿指令",selClr:"清除",selHint:"点行圈选/再点取消 · 指令贴回 PowerShell(只建草稿不发)",copied:"已复制!回 PowerShell 粘贴执行",t4:"④ 邮件跟踪 VMT",vmtOff:"VMT 数据层未部署",vmtG1:"跑一次 via-vmt-init 建立数据层",vmtG2:"之后 via-vmt 生成收敛与排程,本页自动附挂(只读)",convT:"收敛分级(邮件跟踪自动化)",autoR:"自动化率",cpmT:"CPM 排程(关键路径红 · LATE=按现况排不进)",h7:["ISS","案件","工期","Slack","关键","开始","完成","Due","迟"],loadT:"负载对照(容量可视化)",h8:["负责人","管控案","需注意","未回件","负载"],ovl:"过载",okl:"正常",loadNote:"需注意 ≥3 亮红 — 参考资源优化实践:先重分配再加人",stScan:"扫描",stRec:"对账",stId:"编号",stQ:"草稿队列",stRep:"周报",fOwner:"负责人",fLight:"灯级",fAll:"全部",decT:"你的决定(选择题;不回写管控表)",dAdopt:"采纳",dRej:"不采纳",dHold:"搁置",expDec:"导出决定 CSV",decN:"已作答 {n} 题",mTitle:"项目详情",mClose:"关闭",clickHint:"点任一行看详情+作答",t5:"⑤ Copilot 支援",copT:"预制提示语库 — 复制后贴进 M365 Copilot(Outlook/Teams/Word)即用",copNote:"本系统不连任何云端:提示语由本地数据生成,你自行贴入已授权的 Copilot;发出前一律人工过目",copCopy:"复制提示",copCase:"复制 Copilot 提示(带本案数据)",copSel:"Copilot 摘要提示",watchT:"监看台(你钉选的重点)",watchE:"点行上的 ☆ 即可把项目或邮件钉进监看台",wDays:"已等 {n} 天",wGone:"(本窗已无此数据)",t6:"⑥ 系统矩阵",mxT:"全流程 × 功能 × 工具 × 实时状态",mxH:["类别","项目","状态","说明 / 指令"],dzT:"把管控表 CSV 拖到这里(或点击选档)— 自动辨识 UTF-8 / Big5,预览核对后下载正规化档",dzPrev:"管控表预览(前 20 行,{enc} 解码,{n} 行)— 核对无误后:",dzDl:"下载正规化 UTF-8 管控表",dzHint:"下载后存为 functional modules\\WorkOps\\control_sheet.csv,重跑 via-workops 即完成对账",dzBad:"读取失败:非 CSV 或编码无法辨识"},
en:{ttl:"VIA WorkOps Command Board",sub:"Generated {g} · window {d}d · {p} projects · {q} awaiting reply",
 t0:"0. System Flow",t1:"1. Projects",t2:"2. Follow-up Sentinel",t3:"3. Scope & Stakeholders",
 flowT:"How the whole system runs — click a node to jump; color = live module status (green=ready, amber=pending, grey=dormant)",flowHint:"Animation honors reduced-motion; statuses computed at board generation",rptT:"Canonical reports (click to open; local paths)",rpt1:"Outlook read-only scan report",rpt2:"Super-engine report",rpt3:"Advanced analytics report",regT:"Registry & ID status",semiT:"Semi-automatic project builder (candidates -> review -> copy into control sheet)",semiHint:"Five sources: WOP assignments (engine-automatic), existing sheet rows, mail-cluster induction, naming ledger (approved names first), custom groups. The system pre-classifies and pre-checks; you only review (names editable). Paste the copied rows into control_sheet.csv — the system never writes the sheet itself.",semiBtn:"Copy checked rows (sheet format)",semiH:["✓","Source","Code","Name (editable)","Evidence"],semiNone:"(no candidates yet — run via-workops all first)",accT:"Raising auto-classification accuracy (less correction for you)",accL:["Naming review loop: names propose -> edit review CSV -> names apply; approved names are never overwritten and hit directly next round","Custom group rules: via-workops names add NAME KEYWORD — rules take precedence over statistics","Codes in subjects: putting ABC-123 style codes in outgoing subjects aligns clustering with the sheet exactly","Link accumulation: THR<->CASE mapping grows every run (thr_case_map); more history, better hits"],pickT:"Draft template",pickHint:"Template applied to selected mails; default = rich mandatory-choice; approval_request* auto-adds Outlook voting buttons (native tick UI)",
 cases:"Tracked cases",ok:"Verified",warn:"Attention",bad:"Conflicted",none:"No evidence",
 hotB:"{n} cases need your eyes (conflicted or stale) — sorted first",calmB:"Control sheet fully consistent with mail evidence",
 h1:["☆","Light","ID","Code / Name","Owner","Sheet status","Last mail activity","Msgs","Suggestion"],
 upd:"updated",noCtrl:"Control sheet not connected",g1:"Put control_sheet.csv in the WorkOps folder (or run via-workops Templates)",
 g2:"Run via-workops again — it ingests and cross-checks automatically",g3:"From then on this page reads the sheet for you — no Excel",
 urgB:"{n} sent mails unanswered for 3+ days — drafts pre-filled; run via-workops drafts to generate them all (drafts only, never auto-sent)",
 calmQ:"Nothing has waited over 3 days",
 h2:["☆","✓","Light","ID","Subject","To","Sent","Waited","State"],ovd:"Overdue",due:"Chase now",obs:"Watch",nr:"No reply",
 dqT:"Draft queue (pre-filled, awaiting your review)",h2b:["Tier","CaseID","Code","Template","To","Original subject","Waited (biz days)"],
 dqNote:"Drafts are created in Outlook (.Display/.Save) and NEVER sent by the system — you tweak and send yourself.",
 inT:"Recently received (auto-recorded)",h3:["✓","Time","Sender","Subject","Unread"],unread:"unread",
 scT:"Scope induction: mail clusters vs control sheet coverage",h4:["Cluster code","Mails","People","In sheet","Verdict"],
 inC:"Covered",missC:"MISSING — propose new case",scNote:"Project codes induced from mail subjects; MISSING = active in mail but absent from the control sheet.",
 skT:"Stakeholders (global)",h5:["Email","Domain","Mails from","Last seen"],
 skPT:"By project cluster",h6:["Cluster code","People"],empty:"(no data in window)",selN:"{n} selected",selBtn:"Copy draft command",selClr:"Clear",selHint:"Tap a row to select · paste the command in PowerShell (drafts only, never sent)",copied:"Copied! Paste in PowerShell",t4:"4. Mail Tracker (VMT)",vmtOff:"VMT data layer not deployed",vmtG1:"Run via-vmt-init once to create the layer",vmtG2:"Then via-vmt produces convergence & schedule; this page attaches read-only",convT:"Convergence tiers (mail-tracking automation)",autoR:"automation rate",cpmT:"CPM schedule (critical path red; LATE = does not fit as-is)",h7:["ISS","Case","Dur","Slack","Crit","Start","Finish","Due","Late"],loadT:"Workload view (capacity visibility)",h8:["Owner","Cases","Attention","Unanswered","Load"],ovl:"OVER",okl:"ok",loadNote:"Attention >=3 turns red — per resource-optimization practice: rebalance before hiring",stScan:"Scan",stRec:"Reconcile",stId:"IDs",stQ:"Draft queue",stRep:"Report",fOwner:"Owner",fLight:"Light",fAll:"All",decT:"Your decision (never written back to the sheet)",dAdopt:"Adopt",dRej:"Reject",dHold:"Hold",expDec:"Export decisions CSV",decN:"{n} answered",mTitle:"Project detail",mClose:"Close",clickHint:"Tap a row for detail + decision",t5:"5. Copilot Support",copT:"Ready-to-use prompt library — copy, then paste into M365 Copilot (Outlook/Teams/Word)",copNote:"This system calls no cloud: prompts are built from local data; you paste them into your own licensed Copilot; always review before sending",copCopy:"Copy prompt",copCase:"Copy Copilot prompt (with this case)",copSel:"Copilot summary prompt",watchT:"Watchlist (your pinned items)",watchE:"Tap ☆ on any row to pin a project or mail here",wDays:"waited {n}d",wGone:"(no longer in window)",t6:"6. System Matrix",mxT:"Every flow x function x tool x live status",mxH:["Category","Item","Status","Notes / command"],dzT:"Drop your control-sheet CSV here (or click) — UTF-8/Big5 auto-detected, preview then download normalized",dzPrev:"Sheet preview (first 20 rows, {enc} decoded, {n} rows) — if correct:",dzDl:"Download normalized UTF-8 sheet",dzHint:"Save as functional modules\\WorkOps\\control_sheet.csv and rerun via-workops",dzBad:"Read failed: not CSV or unknown encoding"}};
var L="zh";
function t(k){return T[L][k];}
function fmt(s,o){return s.replace(/\{(\w+)\}/g,function(_,k){return o[k];});}

var CONFK={"Verified":"g","Stale":"a","Pending Review":"a","Conflicted":"r","Unmatched":"n","Incomplete":"n"};
var FILT={owner:"",light:""}, DEC={};
function steps(){
 var q=DQ.length, done=[["stScan",MA.length>0||PD.length>0],["stRec",P.length>0],["stId",true],["stQ",q>0?"warn":true],["stRep",true]];
 var h="";
 done.forEach(function(d,i){
  var cls=d[1]==="warn"?"warn":(d[1]?"done":"");
  var mark=d[1]==="warn"?String(q):(d[1]?"✓":String(i+1));
  h+="<div class='step "+cls+"'><span class='dot'>"+mark+"</span>"+esc(t(d[0]))+"</div>";
  if(i<done.length-1)h+="<div class='step'><span class='bar'></span></div>";
 });
 document.getElementById("steps").innerHTML=h;
}
function decCsv(){
 var lines=["ProjectCode,ProjectName,Decision"];
 Object.keys(DEC).forEach(function(code){
  var p2=P.filter(function(x){return x.ProjectCode===code;})[0]||{};
  lines.push('"'+code+'","'+String(p2.ProjectName||"").replace(/"/g,"'")+'","'+DEC[code]+'"');});
 var csv=lines.join("\r\n");
 try{
  var a=document.createElement("a");
  a.href=URL.createObjectURL(new Blob(["\ufeff"+csv],{type:"text/csv"}));
  a.download="proposals_decided.csv";a.click();
 }catch(e){window.prompt("CSV:",csv);}
 return csv;
}
function openDetail(i){
 var p=P[i];if(!p)return;
 var m=document.getElementById("modal");
 var dec=DEC[p.ProjectCode]||"";
 function chip(v,lbl){return "<span class='dchip"+(dec===v?" on":"")+"' data-dec='"+v+"' data-code='"+esc(p.ProjectCode)+"'>"+esc(lbl)+"</span>";}
 m.innerHTML="<button class='mclose' id='mclose'>✕</button><h3>"+esc(t("mTitle"))+" · "+esc(p.WopID||"")+"</h3>"
  +"<div class='mrow'><span class='mk'>CASE</span><br><b>"+esc(p.ProjectCode)+"</b> "+esc(p.ProjectName)+" · "+esc(p.Owner)+" · "+light(p.Confidence)+"</div>"
  +"<div class='mrow'><span class='mk'>SHEET</span><br>"+esc(p.BaselineStatus)+"("+esc(p.BaselineUpdated||"—")+")</div>"
  +"<div class='mrow'><span class='mk'>MAIL</span><br>"+esc(p.ObservedLast||"—")+" "+esc(p.ObservedDir||"")+" · "+esc(p.ObservedMsgs||"0")+"</div>"
  +"<div class='mrow'><span class='mk'>EVIDENCE</span><br>"+esc(p.Evidence)+"</div>"
  +(p.ProposeValue?("<div class='mrow'><span class='mk'>SUGGEST</span><br><b>"+esc(p.ProposeValue)+"</b></div>"):"")
  +"<div class='mrow'><span class='mk'>"+esc(t("decT"))+"</span><br>"+chip("採納",t("dAdopt"))+chip("不採納",t("dRej"))+chip("擱置",t("dHold"))+"</div>"
  +"<div class='mrow'><button class='expbtn copbtn' id='mcop'>"+esc(t("copCase"))+"</button></div>";
 document.getElementById("mback").classList.add("on");
 document.getElementById("mclose").addEventListener("click",closeDetail);
 var mc=document.getElementById("mcop");
 if(mc)mc.addEventListener("click",function(){copyText(casePrompt(p),mc);});
 m.querySelectorAll(".dchip").forEach(function(c){
  c.addEventListener("click",function(){DEC[c.dataset.code]=c.dataset.dec;openDetail(i);rP1();selWire();selApply();});});
}
function closeDetail(){document.getElementById("mback").classList.remove("on");}

var CONFL={zh:{"Verified":"一致","Stale":"需更新","Pending Review":"待追蹤","Conflicted":"矛盾","Unmatched":"無佐證","Incomplete":"欄位不全"},
           cn:{"Verified":"一致","Stale":"需更新","Pending Review":"待跟踪","Conflicted":"矛盾","Unmatched":"无证据","Incomplete":"字段不全"},
           en:{"Verified":"Verified","Stale":"Stale","Pending Review":"Chase","Conflicted":"Conflict","Unmatched":"No evidence","Incomplete":"Incomplete"}};
function light(c){var k=CONFK[c]||"n";return "<span class='lt "+k+"'>"+esc(CONFL[L][c]||c)+"</span>";}
function th(a){return "<thead><tr>"+a.map(function(x){return "<th>"+esc(x)+"</th>";}).join("")+"</tr></thead>";}

/* 範疇歸納:主旨代號叢集 */
var CODE_RE=/\b[A-Z]{2,6}[-_ ]?\d{2,6}\b/g;
var clusters={};
MA.forEach(function(m){
 var s=String(m.Subject||"").toUpperCase(), mm=s.match(CODE_RE)||[];
 mm.forEach(function(c){c=c.replace(/[_ ]/,"-");
  if(!clusters[c])clusters[c]={n:0,people:{},last:""};
  clusters[c].n++; if(m.SenderEmail)clusters[c].people[m.SenderEmail]=1;
  if(String(m.EventDate||"")>clusters[c].last)clusters[c].last=String(m.EventDate||"");});
});
var ctrlCodes={};
P.forEach(function(p){if(p.ProjectCode)ctrlCodes[String(p.ProjectCode).toUpperCase()]=1;});
CT.forEach(function(r){var c=r.ProjectCode||r["專案代號"]||r["案號"]||r.Code;if(c)ctrlCodes[String(c).toUpperCase()]=1;});

function rP1(){
 var el=document.getElementById("p1"),h="";
 if(!DATA.has_control&&P.length===0){
  h="<div class='guide'><h3>"+esc(t("noCtrl"))+"</h3><ol><li>"+esc(t("g1"))+"</li><li>"+esc(t("g2"))+"</li><li>"+esc(t("g3"))+"</li></ol></div>";
  h=dzHtml()+h;
  h+=semiHtml();
  el.innerHTML=h;dzWire();semiWire();return;}
 var n={g:0,a:0,r:0,n:0};
 P.forEach(function(p){n[CONFK[p.Confidence]||"n"]++;});
 h+="<div class='band'><div class='chip'><b>"+P.length+"</b><span>"+esc(t("cases"))+"</span></div>"
  +"<div class='chip'><b style='color:var(--green2)'>"+n.g+"</b><span>"+esc(t("ok"))+"</span></div>"
  +"<div class='chip'><b style='color:#7a5a1f'>"+n.a+"</b><span>"+esc(t("warn"))+"</span></div>"
  +"<div class='chip'><b style='color:#8a3a2c'>"+n.r+"</b><span>"+esc(t("bad"))+"</span></div>"
  +"<div class='chip'><b style='color:var(--mut)'>"+n.n+"</b><span>"+esc(t("none"))+"</span></div></div>";
 var hot=n.r+n.a;
 h+=hot?"<div class='banner'>"+esc(fmt(t("hotB"),{n:hot}))+"</div>":"<div class='banner calm'>"+esc(t("calmB"))+"</div>";
 h+=rWatch();
 h+=dzHtml();
 var owners={};P.forEach(function(p){var o=String(p.Owner||"").trim();if(o)owners[o]=1;});
 h+="<div class='filters'><label>"+esc(t("fOwner"))+"</label><select id='fOwner'><option value=''>"+esc(t("fAll"))+"</option>";
 Object.keys(owners).sort().forEach(function(o){h+="<option"+(FILT.owner===o?" selected":"")+" value='"+esc(o)+"'>"+esc(o)+"</option>";});
 h+="</select><label>"+esc(t("fLight"))+"</label><select id='fLight'><option value=''>"+esc(t("fAll"))+"</option>";
 [["r",t("bad")],["a",t("warn")],["g",t("ok")],["n",t("none")]].forEach(function(x){h+="<option"+(FILT.light===x[0]?" selected":"")+" value='"+x[0]+"'>"+esc(x[1])+"</option>";});
 h+="</select><span class='mut' style='font-size:11px'>"+esc(t("clickHint"))+"</span>";
 var nDec=Object.keys(DEC).length;
 if(nDec)h+="<span style='margin-left:auto'></span><span class='mut' style='font-size:11px'>"+esc(fmt(t("decN"),{n:nDec}))+"</span><button class='expbtn' id='expDec'>"+esc(t("expDec"))+"</button>";
 h+="</div>";
 var order={r:0,a:1,g:2,n:3};
 var sorted=P.slice().sort(function(x,y){return order[CONFK[x.Confidence]||"n"]-order[CONFK[y.Confidence]||"n"];});
 h+="<table>"+th(t("h1"))+"<tbody>";
 sorted.forEach(function(p){
  var pi=P.indexOf(p);
  if(FILT.owner&&String(p.Owner||"").trim()!==FILT.owner)return;
  if(FILT.light&&(CONFK[p.Confidence]||"n")!==FILT.light)return;
  var dmark=DEC[p.ProjectCode]?" · <b>"+esc(DEC[p.ProjectCode])+"</b>":"";
  h+="<tr data-proj='"+pi+"'><td>"+starBtn("proj",p.ProjectCode,p.ProjectCode)+"</td><td>"+light(p.Confidence)+dmark+"</td><td class='mono'>"+esc(p.WopID||"—")+"</td><td><b>"+esc(p.ProjectCode)+"</b> "+esc(p.ProjectName)+"</td>"
   +"<td>"+esc(p.Owner)+"</td><td>"+esc(p.BaselineStatus)+"<div class='ev'>"+esc(t("upd"))+" "+esc(p.BaselineUpdated||"—")+"</div></td>"
   +"<td>"+esc(p.ObservedLast||"—")+" <span class='mut'>"+esc(p.ObservedDir||"")+"</span></td>"
   +"<td class='mono'>"+esc(p.ObservedMsgs||"0")+"</td>"
   +"<td>"+(p.ProposeValue?("<b>"+esc(p.ProposeValue)+"</b>"):"<span class='mut'>—</span>")
   +"<div class='ev'>"+esc(p.Evidence)+"</div></td></tr>";});
 h+="</tbody></table>";
 h+=rLoad();
 h+=semiHtml();
 el.innerHTML=h;
 dzWire();
 semiWire();
 var fo=document.getElementById("fOwner"),fl=document.getElementById("fLight"),xd=document.getElementById("expDec");
 if(fo)fo.addEventListener("change",function(){FILT.owner=fo.value;rP1();selWire();selApply();});
 if(fl)fl.addEventListener("change",function(){FILT.light=fl.value;rP1();selWire();selApply();});
 if(xd)xd.addEventListener("click",decCsv);
 el.querySelectorAll("tr[data-proj]").forEach(function(r){
  r.addEventListener("click",function(){openDetail(parseInt(r.dataset.proj,10));});});
}

function rP2(){
 var el=document.getElementById("p2"),h="";
 h+="<div class='pick'><label>"+esc(t("pickT"))+" <select id='tplPick'><option value=''>approval_request_v2</option>"
  +["approval_request","status_request","eta_confirm","blocker_check","followup","followup_firm"].map(function(k){return "<option value='"+k+"'"+(TPL===k?" selected":"")+">"+k+"</option>";}).join("")
  +"</select></label><span class='mut' style='font-size:11px'>"+esc(t("pickHint"))+"</span></div>";
 var urg=PD.filter(function(p){return parseInt(p.WaitingDays||0,10)>=3;});
 h+=urg.length?"<div class='banner'>"+esc(fmt(t("urgB"),{n:urg.length}))+"</div>"
              :"<div class='banner calm'>"+esc(t("calmQ"))+"</div>";
 if(PD.length){
  h+="<table>"+th(t("h2"))+"<tbody>";
  PD.forEach(function(p){
   var d=parseInt(p.WaitingDays||0,10),k=d>=7?"r":(d>=3?"a":"g");
   h+="<tr data-thr='"+esc(p.ThrID||"")+"'><td>"+starBtn("thr",p.ThrID,p.ThrID)+"</td><td><span class='cb'></span></td><td><span class='lt "+k+"'>"+esc(d>=7?t("ovd"):(d>=3?t("due"):t("obs")))+"</span></td>"
    +"<td class='mono'>"+esc(p.ThrID||"—")+"</td><td>"+esc(p.Subject)+"</td><td>"+esc(p.TO)+"</td><td class='mono'>"+esc(p.SentOn)+"</td>"
    +"<td class='days'>"+d+"</td><td>"+esc(t("nr"))+"</td></tr>";});
  h+="</tbody></table>";
 }
 if(DQ.length){
  h+="<div class='sec'>"+esc(t("dqT"))+"</div><div class='banner info'>"+esc(t("dqNote"))+"</div>";
  h+="<table>"+th(t("h2b"))+"<tbody>";
  DQ.forEach(function(q){
   var stg=String(q.Stage||"T1"),sk=stg==="T3"?"r":(stg==="T2"?"a":"g");
   h+="<tr><td><span class='lt "+sk+"'>"+esc(stg)+"</span></td><td class='mono'>"+esc(q.CaseID||"—")+"</td><td><b>"+esc(q.ProjectCode||"—")+"</b></td><td class='mono'>"+esc(q.Template)+"</td>"
    +"<td>"+esc(q.To)+"</td><td>"+esc(q.OrigSubject)+"</td><td class='days'>"+esc(q.BizDays!=null?q.BizDays:q.WaitingDays)+"</td></tr>";});
  h+="</tbody></table>";
 }
 h+="<div class='sec'>"+esc(t("inT"))+"</div>";
 var IR=MA.slice(0,40);
 if(IR.length){
  h+="<table>"+th(t("h3"))+"<tbody>";
  IR.forEach(function(m){
   h+="<tr data-thr='"+esc(m.ThrID||"")+"'><td><span class='cb'></span></td><td class='mono'>"+esc(m.EventDate)+"</td><td>"+esc(m.SenderEmail)+"</td><td>"+esc(m.Subject)+"</td>"
    +"<td>"+(String(m.Unread).toLowerCase()==="true"?"<span class='lt a'>"+esc(t("unread"))+"</span>":"<span class='mut'>—</span>")+"</td></tr>";});
  h+="</tbody></table>";
 } else { h+="<div class='mut'>"+esc(t("empty"))+"</div>"; }
 el.innerHTML=h;
 var tp=document.getElementById("tplPick");
 if(tp)tp.addEventListener("change",function(){TPL=tp.value;});
}

function rP3(){
 var el=document.getElementById("p3"),h="";
 h+="<div class='sec'>"+esc(t("scT"))+"</div><div class='banner info'>"+esc(t("scNote"))+"</div>";
 var keys=Object.keys(clusters).sort(function(a,b){return clusters[b].n-clusters[a].n;});
 var miss=keys.filter(function(c){return !ctrlCodes[c]&&clusters[c].n>=2;});
 if(keys.length){
  h+="<table>"+th(t("h4"))+"<tbody>";
  keys.forEach(function(c){
   var cl=clusters[c],inC=!!ctrlCodes[c];
   h+="<tr><td><b>"+esc(c)+"</b></td><td class='mono'>"+cl.n+"</td><td class='mono'>"+Object.keys(cl.people).length+"</td>"
    +"<td>"+(inC?"<span class='lt g'>"+esc(t("inC"))+"</span>":"<span class='lt "+(cl.n>=2?"r":"n")+"'>"+esc(cl.n>=2?t("missC"):"—")+"</span>")+"</td>"
    +"<td class='ev'>"+esc(cl.last)+"</td></tr>";});
  h+="</tbody></table>";
 } else { h+="<div class='mut'>"+esc(t("empty"))+"</div>"; }
 h+="<div class='sec'>"+esc(t("skT"))+"</div>";
 if(ST.length){
  h+="<table>"+th(t("h5"))+"<tbody>";
  ST.slice(0,60).forEach(function(s){
   h+="<tr><td>"+esc(s.Email)+"</td><td class='mono'>"+esc(s.Domain)+"</td><td class='mono'>"+esc(s.FromCount)+"</td><td class='mono'>"+esc(s.LastDate)+"</td></tr>";});
  h+="</tbody></table>";
 } else { h+="<div class='mut'>"+esc(t("empty"))+"</div>"; }
 h+="<div class='sec'>"+esc(t("skPT"))+"</div>";
 var pk=keys.filter(function(c){return Object.keys(clusters[c].people).length;});
 if(pk.length){
  h+="<table>"+th(t("h6"))+"<tbody>";
  pk.slice(0,30).forEach(function(c){
   h+="<tr><td><b>"+esc(c)+"</b></td><td>"+Object.keys(clusters[c].people).map(esc).join("、")+"</td></tr>";});
  h+="</tbody></table>";
 } else { h+="<div class='mut'>"+esc(t("empty"))+"</div>"; }
 el.innerHTML=h;
}

var WATCH={};
try{WATCH=JSON.parse(localStorage.getItem("via_workops_watch")||"{}")||{};}catch(e){WATCH={};}
function watchSave(){try{localStorage.setItem("via_workops_watch",JSON.stringify(WATCH));}catch(e){}}
function toggleWatch(kind,id,label){
 var k=kind+"|"+id;
 if(WATCH[k])delete WATCH[k];else WATCH[k]={kind:kind,id:id,label:label||id};
 watchSave();render();
}
function starBtn(kind,id,label){
 var k=kind+"|"+id;
 return "<span class='star"+(WATCH[k]?" on":"")+"' data-wk='"+esc(kind)+"' data-wid='"+esc(id)+"' data-wl='"+esc(label||"")+"'>"+(WATCH[k]?"★":"☆")+"</span>";
}
function watchWire(){
 document.querySelectorAll(".star").forEach(function(st){
  st.addEventListener("click",function(ev){
   if(ev&&ev.stopPropagation)ev.stopPropagation();
   toggleWatch(st.dataset.wk,st.dataset.wid,st.dataset.wl);});});
}
function rWatch(){
 var ks=Object.keys(WATCH);if(!ks.length)return "";
 var h="<div class='wband'><h4>⭐ "+esc(t("watchT"))+"</h4><div class='wgrid'>";
 ks.forEach(function(k){
  var w=WATCH[k],st="";
  if(w.kind==="proj"){
   var p2=P.filter(function(x){return x.ProjectCode===w.id;})[0];
   st=p2?light(p2.Confidence):"<span class='mut'>"+esc(t("wGone"))+"</span>";
  }else{
   var pd=PD.filter(function(x){return x.ThrID===w.id;})[0];
   if(pd){var d=parseInt(pd.WaitingDays||0,10),kk=d>=7?"r":(d>=3?"a":"g");
    st="<span class='lt "+kk+"'>"+esc(fmt(t("wDays"),{n:d}))+"</span>";}
   else{var m2=MA.filter(function(x){return x.ThrID===w.id;})[0];
    st=m2?"<span class='lt g'>INBOUND</span>":"<span class='mut'>"+esc(t("wGone"))+"</span>";}
  }
  h+="<div class='wcard'><b>"+esc(w.label||w.id)+"</b>"+st+"<span class='wx' data-unw='"+esc(k)+"'>✕</span></div>";});
 h+="</div></div>";
 return h;
}
function watchUnwire(){
 document.querySelectorAll(".wx").forEach(function(x){
  x.addEventListener("click",function(){delete WATCH[x.dataset.unw];watchSave();render();});});
}
var SEL={};
var TPL="";
var SEMI=null;
function selCount(){return Object.keys(SEL).length;}
function selBar(){
 var b=document.getElementById("selbar");
 if(selCount()){b.style.display="flex";
  document.getElementById("selN").textContent=fmt(t("selN"),{n:selCount()});
  document.getElementById("selHint").textContent=t("selHint");
  document.getElementById("selCopy").textContent=t("selBtn");
  document.getElementById("selCop").textContent=t("copSel");
  document.getElementById("selClr").textContent=t("selClr");}
 else{b.style.display="none";}
}
function selApply(){
 document.querySelectorAll("tr[data-thr]").forEach(function(r){
  if(SEL[r.dataset.thr])r.classList.add("selrow");else r.classList.remove("selrow");});
 selBar();
}
function selWire(){
 document.querySelectorAll("tr[data-thr]").forEach(function(r){
  r.addEventListener("click",function(){
   var id=r.dataset.thr;if(!id)return;
   if(SEL[id])delete SEL[id];else SEL[id]=1;
   selApply();});});
}
document.getElementById("selCopy").addEventListener("click",function(){
 var cmd="via-workops drafts "+Object.keys(SEL).join(",")+(TPL?" "+TPL:"");
 function done(){var b=document.getElementById("selCopy");b.textContent=t("copied");setTimeout(selBar,1600);}
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(cmd).then(done,function(){window.prompt("Copy:",cmd);done();});}
 else{window.prompt("Copy:",cmd);done();}
});
document.getElementById("selCop").addEventListener("click",function(){copyText(selPrompt(),document.getElementById("selCop"));});
document.getElementById("selClr").addEventListener("click",function(){SEL={};selApply();});
function rP4(){
 var el=document.getElementById("p4"),h="",V=DATA.vmt||{};
 if(!V.present){
  h="<div class='guide'><h3>"+esc(t("vmtOff"))+"</h3><ol><li>"+esc(t("vmtG1"))+"</li><li>"+esc(t("vmtG2"))+"</li></ol></div>";
  el.innerHTML=h;return;}
 var c=V.conv;
 h+="<div class='sec'>"+esc(t("convT"))+"</div>";
 if(c&&c.tiers){
  h+="<div class='band'>"
   +"<div class='chip'><b style='color:var(--green2)'>"+(c.tiers.AUTO||0)+"</b><span>AUTO</span></div>"
   +"<div class='chip'><b style='color:var(--blue)'>"+(c.tiers.CONFIRMED||0)+"</b><span>CONFIRMED</span></div>"
   +"<div class='chip'><b style='color:#7a5a1f'>"+(c.tiers.ASK||0)+"</b><span>ASK</span></div>"
   +"<div class='chip'><b style='color:#8a3a2c'>"+(c.tiers.QUARANTINE||0)+"</b><span>QUARANTINE</span></div>"
   +"<div class='chip'><b>"+Math.round((c.auto_rate||0)*100)+"%</b><span>"+esc(t("autoR"))+"</span></div></div>";
 } else { h+="<div class='mut'>"+esc(t("empty"))+"</div>"; }
 h+="<div class='sec'>"+esc(t("cpmT"))+"</div>";
 var SC=arr(V.schedule);
 if(SC.length){
  h+="<table>"+th(t("h7"))+"<tbody>";
  SC.forEach(function(r){
   var crit=String(r.Critical)==="1",late=String(r.Late)==="1";
   h+="<tr><td class='mono'"+(crit?" style='color:var(--red);font-weight:700'":"")+">"+esc(r.ISS)+"</td>"
    +"<td>"+esc(r.Case)+"</td><td class='mono'>"+esc(r.Duration)+"</td><td class='mono'>"+esc(r.Slack)+"</td>"
    +"<td>"+(crit?"<span class='lt r'>CP</span>":"<span class='mut'>—</span>")+"</td>"
    +"<td class='mono'>"+esc(r.Start)+"</td><td class='mono'>"+esc(r.Finish)+"</td><td class='mono'>"+esc(r.Due||"—")+"</td>"
    +"<td>"+(late?"<span class='lt r'>LATE</span>":"<span class='lt g'>ok</span>")+"</td></tr>";});
  h+="</tbody></table>";
 } else if(arr(V.tasks).length){
  h+="<table><thead><tr><th>ISS</th><th>Duration</th><th>Predecessors</th><th>Note</th></tr></thead><tbody>";
  arr(V.tasks).forEach(function(r){
   h+="<tr><td class='mono'>"+esc(r.ISS)+"</td><td class='mono'>"+esc(r.Duration)+"</td><td class='mono'>"+esc(r.Predecessors)+"</td><td>"+esc(r.Note)+"</td></tr>";});
  h+="</tbody></table>";
 } else { h+="<div class='mut'>"+esc(t("empty"))+"</div>"; }
 el.innerHTML=h;
}
function rLoad(){
 var own={};
 P.forEach(function(p){
  var o=String(p.Owner||"").trim()||"—";
  if(!own[o])own[o]={cases:0,att:0,un:0};
  own[o].cases++;
  var k=CONFK[p.Confidence]||"n";if(k==="r"||k==="a")own[o].att++;});
 PD.forEach(function(p){
  var s=String(p.Subject||"").toUpperCase(),hit="—";
  P.forEach(function(pr){if(pr.ProjectCode&&s.indexOf(String(pr.ProjectCode).toUpperCase())>=0)hit=String(pr.Owner||"").trim()||"—";});
  if(!own[hit])own[hit]={cases:0,att:0,un:0};
  own[hit].un++;});
 var ks=Object.keys(own);if(!ks.length)return "";
 var h="<div class='sec'>"+esc(t("loadT"))+"</div><div class='banner info'>"+esc(t("loadNote"))+"</div>";
 h+="<table>"+th(t("h8"))+"<tbody>";
 ks.sort(function(a,b){return (own[b].att+own[b].un)-(own[a].att+own[a].un);}).forEach(function(o){
  var d=own[o],over=d.att>=3;
  h+="<tr><td><b>"+esc(o)+"</b></td><td class='mono'>"+d.cases+"</td><td class='mono'>"+d.att+"</td><td class='mono'>"+d.un+"</td>"
   +"<td>"+(over?"<span class='lt r'>"+esc(t("ovl"))+"</span>":"<span class='lt g'>"+esc(t("okl"))+"</span>")+"</td></tr>";});
 h+="</tbody></table>";
 return h;
}
var PB={
zh:[
 {t:"郵件串摘要",p:"摘要這串郵件:①三句結論 ②各方立場 ③待辦(負責人+期限) ④未決問題。條列、繁體中文、150字內。"},
 {t:"起草回覆(確認+承諾)",p:"以專業簡潔語氣起草回覆:確認收到、說明我方目前進度、承諾具體回覆日期。繁體中文,120字內,保留原主旨,結尾附我的署名。"},
 {t:"追蹤信(禮貌催辦)",p:"起草一封禮貌的追蹤信:提及上封寄出日期、重申需要對方提供的事項、給出希望回覆的期限、語氣友善但明確。繁體中文,100字內。"},
 {t:"會議紀錄→行動項",p:"從這份會議紀錄擷取行動項,輸出表格:負責人|事項|期限|依賴|風險。缺期限的標記「待定」,不要遺漏口頭承諾。"},
 {t:"週報潤稿",p:"把以下週報改寫得更精煉:保留所有數字與燈號、合併重複句、商務語氣、條列優先。最後加一段三句話的管理層摘要。\n\n[貼上 via-workops report 的內容]"},
 {t:"專案風險分析",p:"根據以下專案現況,列出:①三大風險(依衝擊排序) ②每項風險的早期訊號 ③建議的下一步。用表格,繁體中文。\n\n[貼上①頁該案的資料]"},
 {t:"Teams 進度更新",p:"把以下內容改寫成一則 Teams 頻道進度更新:60字內、先講結論、標注需要誰做什麼、避免技術行話。"},
 {t:"控管表健檢",p:"檢查以下專案控管表資料:①缺欄位或過期的列 ②狀態與最後更新日矛盾的列 ③建議補充的欄位。輸出條列。\n\n[貼上控管表內容]"}],
cn:[
 {t:"邮件串摘要",p:"摘要这串邮件:①三句结论 ②各方立场 ③待办(负责人+期限) ④未决问题。条列、简体中文、150字内。"},
 {t:"起草回复(确认+承诺)",p:"以专业简洁语气起草回复:确认收到、说明我方目前进度、承诺具体回复日期。简体中文,120字内,保留原主题,结尾附我的署名。"},
 {t:"跟踪信(礼貌催办)",p:"起草一封礼貌的跟踪信:提及上封寄出日期、重申需要对方提供的事项、给出希望回复的期限、语气友善但明确。简体中文,100字内。"},
 {t:"会议纪录→行动项",p:"从这份会议纪录提取行动项,输出表格:负责人|事项|期限|依赖|风险。缺期限的标记「待定」,不要遗漏口头承诺。"},
 {t:"周报润稿",p:"把以下周报改写得更精炼:保留所有数字与灯号、合并重复句、商务语气、条列优先。最后加一段三句话的管理层摘要。\n\n[贴上 via-workops report 的内容]"},
 {t:"项目风险分析",p:"根据以下项目现况,列出:①三大风险(按冲击排序) ②每项风险的早期信号 ③建议的下一步。用表格,简体中文。\n\n[贴上①页该案的数据]"},
 {t:"Teams 进度更新",p:"把以下内容改写成一则 Teams 频道进度更新:60字内、先讲结论、标注需要谁做什么、避免技术行话。"},
 {t:"管控表健检",p:"检查以下项目管控表数据:①缺字段或过期的行 ②状态与最后更新日矛盾的行 ③建议补充的字段。输出条列。\n\n[贴上管控表内容]"}],
en:[
 {t:"Thread summary",p:"Summarize this email thread: (1) three-sentence conclusion (2) each party's position (3) action items (owner + deadline) (4) open questions. Bullets, under 150 words."},
 {t:"Draft reply (ack + commit)",p:"Draft a professional, concise reply: acknowledge receipt, state our current progress, commit to a specific reply date. Under 120 words, keep the original subject, end with my signature."},
 {t:"Polite follow-up",p:"Draft a polite follow-up: reference the date of my last mail, restate what I need from them, give a desired reply deadline. Friendly but firm, under 100 words."},
 {t:"Minutes to action items",p:"Extract action items from these meeting minutes as a table: Owner | Item | Deadline | Dependency | Risk. Mark missing deadlines as TBD; do not drop verbal commitments."},
 {t:"Polish weekly report",p:"Tighten the following weekly report: keep every number and status light, merge repetition, business tone, bullets first. End with a three-sentence executive summary.\n\n[paste via-workops report content]"},
 {t:"Project risk analysis",p:"From the project status below list: (1) top three risks by impact (2) early signals for each (3) recommended next steps. Table format.\n\n[paste the case data from page 1]"},
 {t:"Teams status update",p:"Rewrite the following as a Teams channel status update: under 60 words, conclusion first, tag who must do what, no jargon."},
 {t:"Control sheet health check",p:"Check this project control sheet for: (1) rows with missing or stale fields (2) rows where status contradicts last-updated (3) fields worth adding. Bullet output.\n\n[paste sheet content]"}]};
function copyText(txt,btn,okKey){
 function done(){if(btn){btn.textContent=t(okKey||"copied");setTimeout(render,1600);}}
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(txt).then(done,function(){window.prompt("Copy:",txt);done();});}
 else{window.prompt("Copy:",txt);done();}
}
function casePrompt(p2){
 var L2={zh:["你是專案助理。根據以下案件現況,先給三句摘要,再起草一封確認狀態的郵件(繁體中文、禮貌、150字內、保留案號):",
             "案號","案名","負責人","控管表狀態","最後更新","郵件最後活動","系統裁決","佐證"],
         cn:["你是项目助理。根据以下案件现况,先给三句摘要,再起草一封确认状态的邮件(简体中文、礼貌、150字内、保留案号):",
             "案号","案名","负责人","管控表状态","最后更新","邮件最后活动","系统裁决","证据"],
         en:["You are a project assistant. From the case status below, give a three-sentence summary, then draft a polite status-confirmation email (under 150 words, keep the case code):",
             "Code","Name","Owner","Sheet status","Last updated","Last mail activity","System verdict","Evidence"]}[L];
 return L2[0]+"\n"+L2[1]+": "+(p2.ProjectCode||"")+"\n"+L2[2]+": "+(p2.ProjectName||"")+"\n"+L2[3]+": "+(p2.Owner||"")
  +"\n"+L2[4]+": "+(p2.BaselineStatus||"")+"("+(p2.BaselineUpdated||"")+")\n"+L2[5]+": "+(p2.ObservedLast||"")+" "+(p2.ObservedDir||"")
  +"\n"+L2[6]+": "+(p2.Confidence||"")+"\n"+L2[7]+": "+(p2.Evidence||"");
}
function selPrompt(){
 var subs=[];
 Object.keys(SEL).forEach(function(id){
  PD.forEach(function(x){if(x.ThrID===id)subs.push(x.Subject);});
  MA.forEach(function(x){if(x.ThrID===id&&subs.indexOf(x.Subject)<0)subs.push(x.Subject);});});
 var head={zh:"請就以下郵件主旨對應的往來,逐一給:①現況一句話 ②未回原因推測 ③建議追蹤語句(繁體中文):",
           cn:"请就以下邮件主题对应的往来,逐一给:①现况一句话 ②未回原因推测 ③建议跟踪语句(简体中文):",
           en:"For each mail subject below give: (1) one-line status (2) likely reason for no reply (3) suggested chase line:"}[L];
 return head+"\n- "+subs.join("\n- ");
}
function rP5(){
 var el=document.getElementById("p5"),h="";
 h+="<div class='banner info'>"+esc(t("copT"))+"</div><div class='banner calm'>"+esc(t("copNote"))+"</div><div class='pgrid'>";
 PB[L].forEach(function(c,i){
  h+="<div class='pcard'><h4>"+esc(c.t)+"</h4><div class='pp'>"+esc(c.p)+"</div><button data-pi='"+i+"'>"+esc(t("copCopy"))+"</button></div>";});
 h+="</div>";
 el.innerHTML=h;
 el.querySelectorAll("button[data-pi]").forEach(function(b){
  b.addEventListener("click",function(){copyText(PB[L][parseInt(b.dataset.pi,10)].p,b);});});
}
var DROPPED=null;
function csvParse(text){
 var rows=[],row=[],cur="",q=false;
 for(var i=0;i<text.length;i++){var c=text[i];
  if(q){if(c==='"'){if(text[i+1]==='"'){cur+='"';i++;}else q=false;}else cur+=c;}
  else if(c==='"')q=true;
  else if(c===","){row.push(cur);cur="";}
  else if(c==="\n"||c==="\r"){if(cur!==""||row.length){row.push(cur);rows.push(row);row=[];cur="";}if(c==="\r"&&text[i+1]==="\n")i++;}
  else cur+=c;}
 if(cur!==""||row.length){row.push(cur);rows.push(row);}
 return rows.filter(function(r){return r.some(function(x){return String(x).trim()!=="";});});
}
var SHEET_ALIAS={ProjectCode:["projectcode","專案代號","案號","代號","code","项目代号","案号"],
 ProjectName:["projectname","專案名稱","案名","name","项目名称"],
 Owner:["owner","負責人","窗口","负责人"],Status:["status","狀態","进度状态","狀态","状态","進度狀態"],
 LastUpdated:["lastupdated","最後更新","更新日","更新日期","最后更新"]};
function sheetMap(hdr){
 var m={};hdr.forEach(function(h,i){var l=String(h).replace(/^\ufeff/,"").trim().toLowerCase();
  Object.keys(SHEET_ALIAS).forEach(function(k){if(SHEET_ALIAS[k].indexOf(l)>=0)m[k]=i;});});
 return m;
}
function handleSheet(buf){
 var enc="UTF-8",txt="";
 try{txt=new TextDecoder("utf-8",{fatal:false}).decode(buf);}catch(e){txt="";}
 var bad=(txt.match(/\uFFFD/g)||[]).length;
 if(bad>2){try{var t2=new TextDecoder("big5").decode(buf);
   if((t2.match(/\uFFFD/g)||[]).length<bad){txt=t2;enc="Big5";}}catch(e){}}
 var rows=csvParse(txt);
 if(!rows.length||rows.length<2){DROPPED={err:true};render();return;}
 var map=sheetMap(rows[0]);
 var out=rows.slice(1).map(function(r){function g(k){return map[k]!=null?String(r[map[k]]||"").trim():"";}
  return {ProjectCode:g("ProjectCode"),ProjectName:g("ProjectName"),Owner:g("Owner"),Status:g("Status"),LastUpdated:g("LastUpdated")};})
  .filter(function(x){return x.ProjectCode||x.ProjectName;});
 DROPPED={err:false,enc:enc,rows:out};render();
}
function dzHtml(){
 var h="<div class='dz' id='dz'>"+esc(t("dzT"))+"<input type='file' id='dzf' accept='.csv' style='display:none'></div>";
 if(DROPPED){
  if(DROPPED.err){h+="<div class='banner'>"+esc(t("dzBad"))+"</div>";}
  else{
   h+="<div class='banner info'>"+esc(fmt(t("dzPrev"),{enc:DROPPED.enc,n:DROPPED.rows.length}))
    +" <button class='expbtn' id='dzdl'>"+esc(t("dzDl"))+"</button><div class='ev'>"+esc(t("dzHint"))+"</div></div>";
   h+="<table><thead><tr><th>ProjectCode</th><th>ProjectName</th><th>Owner</th><th>Status</th><th>LastUpdated</th></tr></thead><tbody>";
   DROPPED.rows.slice(0,20).forEach(function(r){
    h+="<tr><td><b>"+esc(r.ProjectCode)+"</b></td><td>"+esc(r.ProjectName)+"</td><td>"+esc(r.Owner)+"</td><td>"+esc(r.Status)+"</td><td class='mono'>"+esc(r.LastUpdated)+"</td></tr>";});
   h+="</tbody></table>";
  }
 }
 return h;
}
function dzWire(){
 var dz=document.getElementById("dz");if(!dz)return;
 var f=document.getElementById("dzf");
 dz.addEventListener("click",function(){if(f&&f.click)f.click();});
 if(f)f.addEventListener("change",function(){if(f.files&&f.files[0])f.files[0].arrayBuffer().then(handleSheet);});
 dz.addEventListener("dragover",function(e){e.preventDefault();dz.classList.add("hot");});
 dz.addEventListener("dragleave",function(){dz.classList.remove("hot");});
 dz.addEventListener("drop",function(e){e.preventDefault();dz.classList.remove("hot");
  if(e.dataTransfer&&e.dataTransfer.files&&e.dataTransfer.files[0])e.dataTransfer.files[0].arrayBuffer().then(handleSheet);});
 var dl=document.getElementById("dzdl");
 if(dl)dl.addEventListener("click",function(){
  var lines=["ProjectCode,ProjectName,Owner,Status,LastUpdated"];
  DROPPED.rows.forEach(function(r){lines.push('"'+[r.ProjectCode,r.ProjectName,r.Owner,r.Status,r.LastUpdated].map(function(x){return String(x).replace(/"/g,"'");}).join('","')+'"');});
  var csv="\ufeff"+lines.join("\r\n");
  try{var a=document.createElement("a");a.href=URL.createObjectURL(new Blob([csv],{type:"text/csv"}));a.download="control_sheet.csv";a.click();}
  catch(e){window.prompt("CSV:",csv);}
 });
}
function rP6(){
 var el=document.getElementById("p6"),V=DATA.vmt||{},IDC=DATA.id_counts||{};
 function st(k,txt){return "<span class='lt "+k+"'>"+esc(txt)+"</span>";}
 var ok=st("g","✓"),cand=st("a","候補"),off=st("n","—");
 var rows=[
  ["流程","掃描(唯讀 Outlook)",MA.length?st("g",MA.length+" 封"):st("a","0"),"via-workops(自動)"],
  ["流程","控管表對帳",DATA.has_control?st("g","✓"):st("a","未接"),"control_sheet.csv 或 ①頁拖曳上傳"],
  ["流程","自動編號(PLM side-car)",st("g","WOP "+(IDC.wop||0)+" · THR "+(IDC.thr||0)),"Outlook 原件零觸碰"],
  ["流程","追蹤哨+草稿佇列",DQ.length?st("a",DQ.length+" 件"):st("g","0"),"drafts 一次產生;圈選件=必回選擇題+Outlook 投票勾選;主旨自動嵌 [THR-#]"],
  ["流程","週報 / KPI 歷史 / 執行日誌",ok,"report · out/kpi_history.csv(utf8BOM)· workops_run.log"],
  ["流程","深度鏈(掃描→橋→引擎→分析)",(DATA.deep&&DATA.deep.present)?st("g","跑過 "+DATA.deep.ts):st("a","未跑"),"deep [-Days n]"],
  ["流程","靜默背景 / 桌面通知",ok,"silent · WorkOps_Background.vbs(shell:startup)"],
  ["引擎","郵件智能超級引擎(CAP-001..007)",ok,"engine(修復/五維分類/E01-E07 庫/PMBOK)"],
  ["引擎","NLP/DM/PM 分析層(CAP-008..010)",DATA.pm_venv?st("g","venv 全配"):st("a","降級可跑"),"analytics · pmsetup=無衝突裝 pm4py(絕不進基底)"],
  ["引擎","EnvManager 中央治理安裝(ENG-020)",DATA.envmgr_ran?st("g","健檢在案"):st("a","未跑"),"pmsetup 一律經 gatekeeper 決策 · envmgr=健檢/plan/install"],
  ["引擎","graphviz 可攜版(DFG 圖,ENG-021)",DATA.dot_ready?st("g","dot 就位"):st("a","未裝"),"dotsetup install(免 winget/管理員;sha256 驗證)"],
  ["引擎","命名核對:編號·名稱(ENG-023)",(DATA.naming&&DATA.naming.total)?st("g",DATA.naming.total+" 筆·核對 "+DATA.naming.approved):st("a","未提議"),"deep 尾自動提議 · names apply 核對 · 編號永不變"],
  ["串接","智慧工作台(Forge 12 分頁)",DATA.forge_ready?st("g","結合:共用語料"):st("n","—"),"workbench=起活服務;郵箱分頁同編號·同名稱(正本=深度鏈)"],
  ["串接","ALL 總指揮(ENG-022)",ok,"all [-Days n] [-SkipDeep]:環境自癒→指揮板→深度鏈→總結表"],
  ["引擎","語料橋(schema 統一)",ok,"bridge(0 封問題根治)"],
  ["引擎","行動資料庫 / 時段唯讀匯出",ok,"actiondb · scanrange"],
  ["引擎","WorkMatrix→行事曆",st("a","寫入"),"matrixsync(唯一行事曆寫入,主動觸發)"],
  ["引擎","Forge v004 一貼式(前身)",st("n","保留"),"只增不減,參考工具不設動詞"],
  ["擷取方法","主旨代號叢集(regex)",Object.keys(clusters).length?st("g",Object.keys(clusters).length+" 群"):st("a","0"),"③頁 範疇歸納"],
  ["擷取方法","控管表交叉核對",DATA.has_control?ok:st("a","未接"),"①頁 五級亮燈"],
  ["擷取方法","Outlook 資料夾分類擷取",cand,"scanrange 已產資料夾稽核表;歸戶邏輯候補"],
  ["擷取方法","關鍵字擷取+使用者核對",cand,"engine 已抽關鍵詞;核對 UI 候補"],
  ["郵件追蹤","VMT 收斂/CPM",V.present?ok:st("a","未布建"),"④頁;via-vmt-init"],
  ["支援","Copilot 提示語庫(8 卡×3 語)",ok,"⑤頁;彈窗/圈選帶資料"],
  ["支援","監看台 watch list",Object.keys(WATCH).length?st("g",Object.keys(WATCH).length+" 項"):st("n","0"),"列首 ☆"],
  ["支援","雲端 Graph/Copilot 線",st("n","休眠"),"docs/IT 申請範本;核准前不啟用"]];
 var h="<div class='banner info'>"+esc(t("mxT"))+"</div><table class='mx'>"+th(t("mxH"))+"<tbody>";
 rows.forEach(function(r){h+="<tr><td class='mxs'>"+esc(r[0])+"</td><td>"+esc(r[1])+"</td><td>"+r[2]+"</td><td class='ev'>"+esc(r[3])+"</td></tr>";});
 h+="</tbody></table>";
 el.innerHTML=h;
}
var FL={
zh:{env:"環境自癒",scan:"Outlook 唯讀掃描",eng:"語料橋+超級引擎",ana:"分析層 NLP/DM/PM",nm:"命名核對",lk:"THR↔CASE 互鏈",bd:"六頁指揮板",sq:"追蹤哨+草稿佇列",dc:"決策日誌",cp:"Copilot 支援",wb:"智慧工作台",cl:"雲端 Graph 線",ready:"就緒",wait:"待跑",dorm:"休眠待 IT 核准",inwin:"封在窗",cases:"案",noreply:"未回",rev:"件待過目",appr:"已核對",links:"串",eng2:"引擎已註冊",wop:"WOP 專案編號",thr:"THR 郵件串編號",nmc:"已核對名稱",lkc:"THR↔CASE 互鏈",dcc:"DEC 決策"},
cn:{env:"环境自愈",scan:"Outlook 只读扫描",eng:"语料桥+超级引擎",ana:"分析层 NLP/DM/PM",nm:"命名核对",lk:"THR↔CASE 互链",bd:"六页指挥板",sq:"跟踪哨+草稿队列",dc:"决策日志",cp:"Copilot 支援",wb:"智慧工作台",cl:"云端 Graph 线",ready:"就绪",wait:"待跑",dorm:"休眠待 IT 核准",inwin:"封在窗",cases:"案",noreply:"未回",rev:"件待过目",appr:"已核对",links:"串",eng2:"引擎已注册",wop:"WOP 项目编号",thr:"THR 邮件串编号",nmc:"已核对名称",lkc:"THR↔CASE 互链",dcc:"DEC 决策"},
en:{env:"Env self-heal",scan:"Outlook read-only scan",eng:"Corpus bridge + Super engine",ana:"Analytics NLP/DM/PM",nm:"Naming review",lk:"THR-CASE links",bd:"Six-page board",sq:"Sentinel + draft queue",dc:"Decision log",cp:"Copilot support",wb:"Workbench",cl:"Cloud Graph line",ready:"ready",wait:"pending",dorm:"dormant until IT",inwin:"mails in window",cases:"cases",noreply:"awaiting",rev:"to review",appr:"approved",links:"links",eng2:"engines registered",wop:"WOP project IDs",thr:"THR thread IDs",nmc:"approved names",lkc:"THR-CASE links",dcc:"DEC decisions"}};
function fl(k){return (FL[L]||FL.zh)[k]||k;}
function fnode(cls,go,name,st){return "<div class='fnode "+cls+"'"+(go?" data-go='"+go+"'":"")+"><b>"+esc(name)+"</b><span>"+esc(st)+"</span></div>";}
function farrow(){return "<span class='farr'>→</span>";}
function rP0(){
 var el=document.getElementById("p0");if(!el)return;
 var h="<div class='banner info'>"+esc(t("flowT"))+"</div><div class='mut' style='font-size:11.5px;margin:-2px 0 8px'>"+esc(t("flowHint"))+"</div>";
 var NM=DATA.naming||{total:0,approved:0},DC=DATA.decisions||{total:0,done:0},DP=DATA.deep||{};
 h+="<div class='flowwrap'>";
 h+="<div class='flrow'>"+fnode(DATA.pm_venv?"g":"a","",fl("env"),DATA.pm_venv?fl("ready"):"pmsetup")+farrow()
  +fnode(MA.length?"g":"a","p2",fl("scan"),MA.length+" "+fl("inwin"))+farrow()
  +fnode(DP.present?"g":"a","",fl("eng"),DP.present?String(DP.ts||""):"deep "+fl("wait"))+farrow()
  +fnode(DATA.dot_ready?"g":"a","",fl("ana"),DATA.dot_ready?"DFG "+fl("ready"):"dotsetup")+"</div>";
 h+="<div class='flrow'>"+fnode(NM.total?"g":"a","",fl("nm"),NM.approved+"/"+NM.total+" "+fl("appr"))+farrow()
  +fnode(DATA.thr_links?"g":"a","",fl("lk"),String(DATA.thr_links||0)+" "+fl("links"))+farrow()
  +fnode("g","p1",fl("bd"),P.length+" "+fl("cases")+" · "+PD.length+" "+fl("noreply"))+farrow()
  +fnode(DQ.length?"a":"g","p2",fl("sq"),DQ.length+" "+fl("rev"))+"</div>";
 h+="<div class='flrow'>"+fnode(DC.total?"g":"a","",fl("dc"),DC.done+"/"+DC.total)+farrow()
  +fnode("g","p5",fl("cp"),"M365")+farrow()
  +fnode(DATA.forge_ready?"g":"a","",fl("wb"),"via-workops workbench")+farrow()
  +fnode("n","",fl("cl"),fl("dorm"))+"</div>";
 h+="</div>";
 var R=DATA.reports||{};
 function rl(u,lbl){return "<a "+(u?("href='"+encodeURI(u)+"' target='_blank'"):"class='off'")+">"+esc(lbl)+"</a>";}
 h+="<div class='sec'>"+esc(t("rptT"))+"</div><div class='rptlinks'>"+rl(R.scan,t("rpt1"))+rl(R.engine,t("rpt2"))+rl(R.analytics,t("rpt3"))+"</div>";
 var RG=DATA.reg||{},IC=DATA.id_counts||{};
 h+="<div class='sec'>"+esc(t("regT"))+"</div><div class='regchips'>"
  +"<div class='chip'><b>"+esc(RG.engines||0)+"</b><span>"+esc(fl("eng2"))+"</span></div>"
  +"<div class='chip'><b>"+esc(IC.wop||0)+"</b><span>"+esc(fl("wop"))+"</span></div>"
  +"<div class='chip'><b>"+esc(IC.thr||0)+"</b><span>"+esc(fl("thr"))+"</span></div>"
  +"<div class='chip'><b>"+esc(NM.approved)+"</b><span>"+esc(fl("nmc"))+"</span></div>"
  +"<div class='chip'><b>"+esc(DATA.thr_links||0)+"</b><span>"+esc(fl("lkc"))+"</span></div>"
  +"<div class='chip'><b>"+esc(DC.total)+"</b><span>"+esc(fl("dcc"))+"</span></div></div>";
 el.innerHTML=h;
 el.querySelectorAll(".fnode[data-go]").forEach(function(nd){
  nd.addEventListener("click",function(){
   var pg=nd.dataset.go;if(!pg)return;
   document.querySelectorAll(".tab").forEach(function(x){x.classList.remove("on");});
   document.querySelectorAll(".page").forEach(function(x){x.classList.remove("on");});
   var tb=document.querySelector(".tab[data-p='"+pg+"']"),pe=document.getElementById(pg);
   if(tb)tb.classList.add("on");if(pe)pe.classList.add("on");});});
}
function semiCands(){
 var c=[],seen={};
 CT.forEach(function(r){var code=String(r.ProjectCode||r["專案代號"]||r["案號"]||r.Code||"").trim();if(!code||seen[code.toUpperCase()])return;seen[code.toUpperCase()]=1;
  c.push({src:"控管表",code:code,name:String(r.ProjectName||r["專案名稱"]||"").trim(),ev:"既有列",owner:String(r.Owner||"").trim(),on:false});});
 Object.keys(clusters).sort(function(a,b){return clusters[b].n-clusters[a].n;}).forEach(function(k){
  if(seen[k])return;seen[k]=1;
  var cl=clusters[k];if(cl.n<2)return;
  c.push({src:"郵件叢集",code:k,name:"",ev:cl.n+" ✉ · "+Object.keys(cl.people).length+" 人",owner:"",on:cl.n>=3});});
 arr(DATA.wop_top).forEach(function(e){
  if(!e)return;var key="WP|"+e.id;if(seen[key])return;seen[key]=1;
  c.push({src:e.ok?"WOP 歸戶 ✔":"WOP 歸戶",code:e.id,name:e.name||"",ev:e.n+" ✉串",owner:"",on:e.n>=2});});
 arr(DATA.naming_top).forEach(function(e){
  if(!e||!e.name)return;var key="NM|"+e.id;if(seen[key])return;seen[key]=1;
  c.push({src:e.ok?"命名帳本 ✔":"命名帳本",code:e.id,name:e.name,ev:e.ok?"已核對":"提議",owner:"",on:false});});
 arr(DATA.naming_custom).forEach(function(g){
  if(!g||!g.name)return;var key="CG|"+g.name;if(seen[key])return;seen[key]=1;
  c.push({src:"自建歸類",code:"",name:g.name,ev:g.keyword?("關鍵字 "+g.keyword):"—",owner:"",on:false});});
 return c;
}
function semiHtml(){
 if(!SEMI)SEMI=semiCands();
 var h="<div class='sec'>"+esc(t("semiT"))+"</div><div class='banner info'>"+esc(t("semiHint"))+"</div>";
 if(!SEMI.length){h+="<div class='mut'>"+esc(t("semiNone"))+"</div>";}
 else{
  h+="<table>"+th(t("semiH"))+"<tbody>";
  SEMI.forEach(function(cd,i){
   h+="<tr><td><input type='checkbox' class='semick' data-i='"+i+"'"+(cd.on?" checked":"")+"></td><td>"+esc(cd.src)+"</td><td class='mono'>"+esc(cd.code||"—")+"</td>"
    +"<td><input type='text' class='seminm' data-i='"+i+"' value='"+esc(cd.name)+"'></td>"
    +"<td class='ev'>"+esc(cd.ev)+"</td></tr>";});
  h+="</tbody></table><button class='expbtn' id='semiCopy'>"+esc(t("semiBtn"))+"</button>";
 }
 h+="<div class='guide' style='margin-top:10px'><h3>"+esc(t("accT"))+"</h3><ol>";
 t("accL").forEach(function(x){h+="<li>"+esc(x)+"</li>";});
 h+="</ol></div>";
 return h;
}
function semiWire(){
 document.querySelectorAll(".semick").forEach(function(ck){ck.addEventListener("change",function(){var cd=SEMI[parseInt(ck.dataset.i,10)];if(cd)cd.on=!!ck.checked;});});
 document.querySelectorAll(".seminm").forEach(function(inp){inp.addEventListener("input",function(){var cd=SEMI[parseInt(inp.dataset.i,10)];if(cd)cd.name=inp.value;});});
 var sc=document.getElementById("semiCopy");
 if(sc)sc.addEventListener("click",function(){
  var td=new Date(),ds=td.getFullYear()+"/"+(td.getMonth()+1)+"/"+td.getDate();
  var lines=["ProjectCode,ProjectName,Owner,Status,Progress,DueDate,LastUpdated"];
  SEMI.forEach(function(cd){if(!cd.on)return;
   lines.push('"'+String(cd.code||cd.name).replace(/"/g,"'")+'","'+String(cd.name||cd.code).replace(/"/g,"'")+'","'+String(cd.owner||"").replace(/"/g,"'")+'","進行中","","","'+ds+'"');});
  copyText(lines.join("\r\n"),sc);
 });
}
function render(){
 document.getElementById("ttl").textContent=t("ttl");
 document.getElementById("sub").textContent=fmt(t("sub"),{g:DATA.generated,d:DATA.days,p:P.length,q:PD.length});
 var tabs=document.querySelectorAll(".tab");
 var __tl=["t0","t1","t2","t3","t4","t5","t6"];
 for(var __i=0;__i<__tl.length;__i++){if(tabs[__i])tabs[__i].textContent=t(__tl[__i]);}
 var __tot=P.length+PD.length+MA.length;
 if(document.body&&document.body.classList){if(__tot>60)document.body.classList.add("dense");else document.body.classList.remove("dense");}
 steps();rP0();rP1();rP2();rP3();rP4();rP5();rP6();
 selWire();selApply();watchWire();watchUnwire();
}
document.getElementById("mback").addEventListener("click",function(e){if(e.target&&e.target.id==="mback")closeDetail();});
document.querySelectorAll(".lang button").forEach(function(b){
 b.addEventListener("click",function(){
  document.querySelectorAll(".lang button").forEach(function(x){x.classList.remove("on");});
  b.classList.add("on");L=b.dataset.l;render();});});
document.querySelectorAll(".tab").forEach(function(tb){
 tb.addEventListener("click",function(){
  document.querySelectorAll(".tab").forEach(function(x){x.classList.remove("on");});
  document.querySelectorAll(".page").forEach(function(x){x.classList.remove("on");});
  tb.classList.add("on");document.getElementById(tb.dataset.p).classList.add("on");});});
render();
if(PD.some(function(p){return parseInt(p.WaitingDays||0,10)>=3;})){
 document.querySelector("[data-p='p2']").click();
}
</script>
</body>
</html>
'@
$html = $html.Replace("__VIA_DATA__", $json)
$outFile = Join-Path $RunDir "VIA_WorkOps_CommandBoard.html"
[System.IO.File]::WriteAllText($outFile, $html, (New-Object System.Text.UTF8Encoding($false)))
Write-Host ("   指揮板:{0}" -f $outFile) -ForegroundColor Green

# ---- 一鍵週報(市場功能吸收;run-local)----
$rp = New-Object System.Text.StringBuilder
[void]$rp.Append("<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>WorkOps 週報</title><style>")
[void]$rp.Append("body{background:#f2f1ec;color:#1b1a17;font-family:'Segoe UI','Microsoft JhengHei',sans-serif;font-size:13px;max-width:900px;margin:0 auto;padding:26px}")
[void]$rp.Append("h1{font-size:18px}h2{font-size:13px;color:#6b6860;margin:16px 0 8px;text-transform:uppercase}")
[void]$rp.Append("table{width:100%;border-collapse:collapse;background:#fbfaf7;border:1px solid #dcdad4}th,td{padding:7px 10px;border-bottom:1px solid #dcdad4;text-align:left;font-size:12px}")
[void]$rp.Append("th{font-size:10px;color:#8a877f;text-transform:uppercase;background:#f5f4f0}.mono{font-family:Consolas,monospace}</style></head><body>")
[void]$rp.Append("<h1>VIA WorkOps 週報 · " + (Get-Date).ToString("yyyy/MM/dd") + "</h1>")
[void]$rp.Append("<h2>專案狀態(" + @($rec).Count + " 案)</h2><table><tr><th>編號</th><th>案號</th><th>案名</th><th>負責人</th><th>裁決</th><th>建議</th></tr>")
foreach ($r in $rec) {
    [void]$rp.Append("<tr><td class='mono'>" + $r.WopID + "</td><td>" + [System.Net.WebUtility]::HtmlEncode([string]$r.ProjectCode) + "</td><td>" + [System.Net.WebUtility]::HtmlEncode([string]$r.ProjectName) + "</td><td>" + [System.Net.WebUtility]::HtmlEncode([string]$r.Owner) + "</td><td>" + [System.Net.WebUtility]::HtmlEncode([string]$r.Confidence) + "</td><td>" + [System.Net.WebUtility]::HtmlEncode([string]$r.ProposeValue) + "</td></tr>")
}
[void]$rp.Append("</table><h2>未回追蹤(" + @($pendSorted).Count + " 件)</h2><table><tr><th>編號</th><th>主旨</th><th>對象</th><th>已等(天)</th></tr>")
foreach ($p in $pendSorted) {
    [void]$rp.Append("<tr><td class='mono'>" + $p.ThrID + "</td><td>" + [System.Net.WebUtility]::HtmlEncode([string]$p.Subject) + "</td><td>" + [System.Net.WebUtility]::HtmlEncode([string]$p.TO) + "</td><td class='mono'>" + $p.WaitingDays + "</td></tr>")
}
if ($vmt.present -and $vmt.conv) {
    [void]$rp.Append("</table><h2>郵件追蹤 VMT(收斂分級)</h2><table><tr><th>AUTO</th><th>CONFIRMED</th><th>ASK</th><th>QUARANTINE</th><th>自動化率</th></tr>")
    [void]$rp.Append("<tr><td class='mono'>" + $vmt.conv.tiers.AUTO + "</td><td class='mono'>" + $vmt.conv.tiers.CONFIRMED + "</td><td class='mono'>" + $vmt.conv.tiers.ASK + "</td><td class='mono'>" + $vmt.conv.tiers.QUARANTINE + "</td><td class='mono'>" + [math]::Round($vmt.conv.auto_rate * 100) + "%</td></tr></table>")
} else { [void]$rp.Append("</table>") }
[void]$rp.Append("<p style='color:#8a877f;font-size:11px'>本報表由 WorkOps × Mail Tracker 統合指揮板自動彙整;編號為系統 side-car 識別,Outlook 原件未被修改。</p></body></html>")
$reportFile = Join-Path $RunDir "VIA_WorkOps_WeeklyReport.html"
[System.IO.File]::WriteAllText($reportFile, $rp.ToString(), (New-Object System.Text.UTF8Encoding($false)))
Write-Host ("   週報:{0}(via-workops report 可直接開)" -f $reportFile) -ForegroundColor Green

# ---- [5/5] 非阻塞開啟 ----
Write-Host "[5/5] 開啟(非阻塞)..." -ForegroundColor Yellow
if (-not $NoOpen) { Start-Process $outFile | Out-Null }
# ---- KPI 歷史(append-only;Excel 直開)----
$att = @($rec | Where-Object { $_.Confidence -in @("Conflicted","Stale","Pending Review") }).Count
$kpi = Join-Path $OutDir "kpi_history.csv"
if (-not (Test-Path -LiteralPath $kpi)) {
    Set-Content -LiteralPath $kpi -Value "Timestamp,Projects,Attention,Unanswered,DraftQueue,Stakeholders" -Encoding utf8BOM
}
Add-Content -LiteralPath $kpi -Value ("{0},{1},{2},{3},{4},{5}" -f (Get-Date -Format "yyyy-MM-dd HH:mm"), @($rec).Count, $att, @($pendSorted).Count, @($queue).Count, @($stak).Count) -Encoding UTF8
Write-WopsLog ("完成:專案 {0} · 需注意 {1} · 未回 {2} · 佇列 {3}" -f @($rec).Count, $att, @($pendSorted).Count, @($queue).Count)
Send-WopsToast "VIA WorkOps 指揮板" ("專案 {0} 案 · 需注意 {1} · 未回 {2} 件 · 草稿佇列 {3} 件" -f @($rec).Count, $att, @($pendSorted).Count, @($queue).Count)
Write-Host ("[總結] 專案 {0} 案 · 需注意 {1} · 未回追蹤 {2} 件 · 草稿佇列 {3} 件(絕不代寄)· 關係人 {4} 人 · log/kpi 已落 out\" -f @($rec).Count, $att, @($pendSorted).Count, @($queue).Count, @($stak).Count) -ForegroundColor Green
