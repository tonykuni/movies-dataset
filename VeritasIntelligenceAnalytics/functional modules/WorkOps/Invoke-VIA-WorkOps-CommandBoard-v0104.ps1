#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-CommandBoard v0104 — WorkOps × Mail Tracker 統合指揮板(v0103 版本前送)
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
 回退:動態 pattern 自動指回 v0103(刪本檔即回退)。
==========================================================================================
#>
param(
    [int]$Days = 14,
    [switch]$NoScan,
    [switch]$NoOpen,
    [string]$DraftsFor = ""
)
$ErrorActionPreference = "Continue"
$Here    = $PSScriptRoot
$ViaRoot = Split-Path (Split-Path $Here -Parent) -Parent
$OutDir  = Join-Path $Here "out"
$Control = Join-Path $Here "control_sheet.csv"
$RunDir  = Join-Path $ViaRoot "VIA_Reports\workops_run"
New-Item -ItemType Directory -Force -Path $RunDir, $OutDir | Out-Null

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  VIA WorkOps x Mail Tracker 統合指揮板 v0104  |  單一系統 · 四頁 · 唯讀附掛 VMT" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

# ---- [1/5] 掃描 + 對帳(重用 v001 引擎;Outlook 不在 = 誠實降級)----
$engine = Join-Path $Here "Invoke-VeritasMailOps.ps1"
if (-not $NoScan -and -not $DraftsFor -and (Test-Path -LiteralPath $engine)) {
    Write-Host "[1/5] 掃描 Outlook(唯讀,使用者自身權限)+ 控管表對帳..." -ForegroundColor Yellow
    & $engine -Action Scan -Days $Days
    & $engine -Action Reconcile
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
        $selQ += [pscustomobject]@{
            CaseID = $id; ProjectCode = $(if ($mm.Success) { $mm.Value -replace "[_ ]", "-" } else { "" })
            ProjectName = ""; To = $to; Cc = ""; Template = "followup"
            OrigSubject = $subj; SentOn = ""; WaitingDays = ""
        }
    }
    if (@($selQ).Count -eq 0) { Write-Host "[總結] 圈選件皆無法成稿(見上方略過原因)。" -ForegroundColor Yellow; return }
    $selQ | Export-Csv -LiteralPath $autoCsv -NoTypeInformation -Encoding UTF8
    Write-Host ("   圈選 {0} 件 → {1}" -f @($selQ).Count, $autoCsv) -ForegroundColor Green
    & $engine -Action FollowUp -RecipientsCsv $autoCsv
    Write-Host "[總結] 圈選草稿已建於 Outlook(只建草稿,你過目後親自寄)。" -ForegroundColor Green
    return
}

# ---- [3/5] 草稿佇列預填(≥3 天未回 → recipients_auto.csv;引擎只建草稿不寄)----
Write-Host "[3/5] 預填追蹤草稿佇列(降低修改量;絕不代寄)..." -ForegroundColor Yellow
$queue = @()
foreach ($p in $pendSorted) {
    $wd = 0; [int]::TryParse([string]$p.WaitingDays, [ref]$wd) | Out-Null
    if ($wd -lt 3) { continue }
    $m = $codeRe.Match(([string]$p.Subject).ToUpper())
    $code = if ($m.Success) { $m.Value -replace "[_ ]", "-" } else { "" }
    $name = ""
    if ($code) {
        $hit = $rec | Where-Object { ([string]$_.ProjectCode).ToUpper() -eq $code } | Select-Object -First 1
        if ($hit) { $name = [string]$hit.ProjectName }
    }
    $queue += [pscustomobject]@{
        CaseID = [string]$p.ThrID; ProjectCode = $code; ProjectName = $name; To = [string]$p.TO; Cc = ""
        Template = "followup"; OrigSubject = [string]$p.Subject
        SentOn = [string]$p.SentOn; WaitingDays = $wd
    }
}
if (@($queue).Count -gt 0) {
    $queue | Export-Csv -LiteralPath $autoCsv -NoTypeInformation -Encoding UTF8
    Write-Host ("   佇列 {0} 件 → {1}(via-workops drafts 一次產生草稿)" -f @($queue).Count, $autoCsv) -ForegroundColor Green
} else {
    Write-Host "   無 ≥3 天未回件,佇列空。" -ForegroundColor DarkGray
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
</style>
</head>
<body>
<div class="mast"><div class="seal">務</div>
 <div><h1 id="ttl"></h1><div class="sub" id="sub"></div></div>
 <div class="lang"><button data-l="zh" class="on">繁</button><button data-l="cn">简</button><button data-l="en">EN</button></div></div>
<div class="strip"><i style="background:#4c78a8"></i><i style="background:#4f9465"></i><i style="background:#c4634f"></i><i style="background:#bf8f33"></i><i style="background:#3d8f8f"></i><i style="background:#7a6daa"></i></div>
<div class="tabs">
 <div class="tab on" data-p="p1"></div>
 <div class="tab" data-p="p2"></div>
 <div class="tab" data-p="p3"></div>
 <div class="tab" data-p="p4"></div>
</div>
<div class="page on" id="p1"></div>
<div class="page" id="p2"></div>
<div class="page" id="p3"></div>
<div class="page" id="p4"></div>
<div class="foot">VIA WorkOps · read-only · drafts never auto-sent · run-local</div>
<div class="selbar" id="selbar"><div><b id="selN"></b><div class="selhint" id="selHint"></div></div>
 <button id="selCopy"></button><button class="clr" id="selClr"></button></div>
<script>
var DATA = __VIA_DATA__;
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function arr(x){return x==null?[]:(Array.isArray(x)?x:[x]);}
var P=arr(DATA.projects),PD=arr(DATA.pending),MA=arr(DATA.mails_all),ST=arr(DATA.stakeholders),CT=arr(DATA.control_rows),DQ=arr(DATA.drafts_queue);

var T={
zh:{ttl:"VIA WorkOps 指揮板",sub:"產生 {g} · 佐證窗 {d} 天 · 專案 {p} 案 · 未回追蹤 {q} 件",
 t1:"① 專案指揮",t2:"② 追蹤哨",t3:"③ 範疇與關係人",
 cases:"控管案件",ok:"一致",warn:"需注意",bad:"矛盾",none:"無佐證/不全",
 hotB:"{n} 案需要你的眼睛(矛盾或待更新)— 已排前列",calmB:"控管表與郵件佐證全數一致",
 h1:["燈","編號","案號 / 案名","負責人","控管表狀態","郵件最後活動","往來","系統建議"],
 upd:"更新日",noCtrl:"尚未接上控管表",g1:"把 control_sheet.csv 放到 WorkOps 資料夾(或 via-workops Templates 產生範例)",
 g2:"再跑一次 via-workops — 系統自動吃入並交叉核對",g3:"之後控管表由本頁代讀,你不需要再開 Excel",
 urgB:"{n} 件寄出 ≥3 天未獲回覆 — 草稿已預填,執行 via-workops drafts 一次產生(只建草稿,絕不代寄)",
 calmQ:"目前沒有等待回覆超過 3 天的信",
 h2:["燈","編號","主旨","對象","寄出時間","已等","狀態"],ovd:"逾期",due:"該追了",obs:"觀察",nr:"未回覆",
 dqT:"草稿佇列(預填完成,待你過目)",h2b:["識別碼","案號","範本","收件人","原主旨","已等"],
 dqNote:"系統只建 Outlook 草稿(.Display/.Save),永不 .Send — 你微調後親自寄。預填=案號/對象/範本/敬語,要改的只剩重點一兩句。",
 inT:"最近收到(自動記錄)",h3:["時間","寄件者","主旨","未讀"],unread:"未讀",
 scT:"範疇歸納:郵件叢集 × 控管表覆蓋",h4:["叢集代號","郵件數","關係人數","控管表","裁決"],
 inC:"已控管",missC:"遺漏 — 建議建案",scNote:"從郵件主旨自動歸納專案代號;「遺漏」= 郵件中活躍但控管表沒有的範疇。",
 skT:"利害關係人彙總(全域)",h5:["Email","網域","來信數","最後來信"],
 skPT:"依專案歸戶",h6:["叢集代號","關係人"],empty:"(本窗無資料)",selN:"已圈選 {n} 件",selBtn:"複製草稿指令",selClr:"清除",selHint:"點列圈選/再點取消 · 指令貼回 PowerShell(只建草稿不寄)",copied:"已複製!回 PowerShell 貼上執行",t4:"④ 郵件追蹤 VMT",vmtOff:"VMT 資料層未布建",vmtG1:"跑一次 via-vmt-init 建立資料層(C:\\VIA\\VeritasMailTracker)",vmtG2:"之後 via-vmt 產生收斂與排程,本頁自動附掛(唯讀)",convT:"收斂分級(郵件追蹤自動化)",autoR:"自動化率",cpmT:"CPM 排程(關鍵路徑紅 · LATE=依現況排不進)",h7:["ISS","案件","工期","Slack","關鍵",  "開始","完成","Due","遲"],loadT:"負載對照(容量可視化)",h8:["負責人","控管案","需注意","未回件","負載"],ovl:"過載",okl:"正常",loadNote:"需注意 ≥3 亮紅 — 參考資源最佳化實務:先重分配再加人"},
cn:{ttl:"VIA WorkOps 指挥板",sub:"生成 {g} · 证据窗 {d} 天 · 项目 {p} 案 · 未回跟踪 {q} 件",
 t1:"① 项目指挥",t2:"② 跟踪哨",t3:"③ 范畴与关系人",
 cases:"管控案件",ok:"一致",warn:"需注意",bad:"矛盾",none:"无证据/不全",
 hotB:"{n} 案需要你的眼睛(矛盾或待更新)— 已排前列",calmB:"管控表与邮件证据全部一致",
 h1:["灯","编号","案号 / 案名","负责人","管控表状态","邮件最后活动","往来","系统建议"],
 upd:"更新日",noCtrl:"尚未接上管控表",g1:"把 control_sheet.csv 放到 WorkOps 文件夹(或 via-workops Templates 生成示例)",
 g2:"再跑一次 via-workops — 系统自动吃入并交叉核对",g3:"之后管控表由本页代读,你不需要再开 Excel",
 urgB:"{n} 件寄出 ≥3 天未获回复 — 草稿已预填,执行 via-workops drafts 一次生成(只建草稿,绝不代发)",
 calmQ:"目前没有等待回复超过 3 天的信",
 h2:["灯","编号","主题","对象","寄出时间","已等","状态"],ovd:"逾期",due:"该追了",obs:"观察",nr:"未回复",
 dqT:"草稿队列(预填完成,待你过目)",h2b:["识别码","案号","模板","收件人","原主题","已等"],
 dqNote:"系统只建 Outlook 草稿,永不代发 — 你微调后亲自发送。预填=案号/对象/模板/敬语。",
 inT:"最近收到(自动记录)",h3:["时间","寄件者","主题","未读"],unread:"未读",
 scT:"范畴归纳:邮件簇 × 管控表覆盖",h4:["簇代号","邮件数","关系人数","管控表","裁决"],
 inC:"已管控",missC:"遗漏 — 建议建案",scNote:"从邮件主题自动归纳项目代号;「遗漏」= 邮件中活跃但管控表没有的范畴。",
 skT:"利害关系人汇总(全域)",h5:["Email","域名","来信数","最后来信"],
 skPT:"按项目归户",h6:["簇代号","关系人"],empty:"(本窗无数据)",selN:"已圈选 {n} 件",selBtn:"复制草稿指令",selClr:"清除",selHint:"点行圈选/再点取消 · 指令贴回 PowerShell(只建草稿不发)",copied:"已复制!回 PowerShell 粘贴执行",t4:"④ 邮件跟踪 VMT",vmtOff:"VMT 数据层未部署",vmtG1:"跑一次 via-vmt-init 建立数据层",vmtG2:"之后 via-vmt 生成收敛与排程,本页自动附挂(只读)",convT:"收敛分级(邮件跟踪自动化)",autoR:"自动化率",cpmT:"CPM 排程(关键路径红 · LATE=按现况排不进)",h7:["ISS","案件","工期","Slack","关键","开始","完成","Due","迟"],loadT:"负载对照(容量可视化)",h8:["负责人","管控案","需注意","未回件","负载"],ovl:"过载",okl:"正常",loadNote:"需注意 ≥3 亮红 — 参考资源优化实践:先重分配再加人"},
en:{ttl:"VIA WorkOps Command Board",sub:"Generated {g} · window {d}d · {p} projects · {q} awaiting reply",
 t1:"1. Projects",t2:"2. Follow-up Sentinel",t3:"3. Scope & Stakeholders",
 cases:"Tracked cases",ok:"Verified",warn:"Attention",bad:"Conflicted",none:"No evidence",
 hotB:"{n} cases need your eyes (conflicted or stale) — sorted first",calmB:"Control sheet fully consistent with mail evidence",
 h1:["Light","ID","Code / Name","Owner","Sheet status","Last mail activity","Msgs","Suggestion"],
 upd:"updated",noCtrl:"Control sheet not connected",g1:"Put control_sheet.csv in the WorkOps folder (or run via-workops Templates)",
 g2:"Run via-workops again — it ingests and cross-checks automatically",g3:"From then on this page reads the sheet for you — no Excel",
 urgB:"{n} sent mails unanswered for 3+ days — drafts pre-filled; run via-workops drafts to generate them all (drafts only, never auto-sent)",
 calmQ:"Nothing has waited over 3 days",
 h2:["Light","ID","Subject","To","Sent","Waited","State"],ovd:"Overdue",due:"Chase now",obs:"Watch",nr:"No reply",
 dqT:"Draft queue (pre-filled, awaiting your review)",h2b:["CaseID","Code","Template","To","Original subject","Waited"],
 dqNote:"Drafts are created in Outlook (.Display/.Save) and NEVER sent by the system — you tweak and send yourself.",
 inT:"Recently received (auto-recorded)",h3:["Time","Sender","Subject","Unread"],unread:"unread",
 scT:"Scope induction: mail clusters vs control sheet coverage",h4:["Cluster code","Mails","People","In sheet","Verdict"],
 inC:"Covered",missC:"MISSING — propose new case",scNote:"Project codes induced from mail subjects; MISSING = active in mail but absent from the control sheet.",
 skT:"Stakeholders (global)",h5:["Email","Domain","Mails from","Last seen"],
 skPT:"By project cluster",h6:["Cluster code","People"],empty:"(no data in window)",selN:"{n} selected",selBtn:"Copy draft command",selClr:"Clear",selHint:"Tap a row to select · paste the command in PowerShell (drafts only, never sent)",copied:"Copied! Paste in PowerShell",t4:"4. Mail Tracker (VMT)",vmtOff:"VMT data layer not deployed",vmtG1:"Run via-vmt-init once to create the layer",vmtG2:"Then via-vmt produces convergence & schedule; this page attaches read-only",convT:"Convergence tiers (mail-tracking automation)",autoR:"automation rate",cpmT:"CPM schedule (critical path red; LATE = does not fit as-is)",h7:["ISS","Case","Dur","Slack","Crit","Start","Finish","Due","Late"],loadT:"Workload view (capacity visibility)",h8:["Owner","Cases","Attention","Unanswered","Load"],ovl:"OVER",okl:"ok",loadNote:"Attention >=3 turns red — per resource-optimization practice: rebalance before hiring"}};
var L="zh";
function t(k){return T[L][k];}
function fmt(s,o){return s.replace(/\{(\w+)\}/g,function(_,k){return o[k];});}

var CONFK={"Verified":"g","Stale":"a","Pending Review":"a","Conflicted":"r","Unmatched":"n","Incomplete":"n"};
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
  el.innerHTML=h;return;}
 var n={g:0,a:0,r:0,n:0};
 P.forEach(function(p){n[CONFK[p.Confidence]||"n"]++;});
 h+="<div class='band'><div class='chip'><b>"+P.length+"</b><span>"+esc(t("cases"))+"</span></div>"
  +"<div class='chip'><b style='color:var(--green2)'>"+n.g+"</b><span>"+esc(t("ok"))+"</span></div>"
  +"<div class='chip'><b style='color:#7a5a1f'>"+n.a+"</b><span>"+esc(t("warn"))+"</span></div>"
  +"<div class='chip'><b style='color:#8a3a2c'>"+n.r+"</b><span>"+esc(t("bad"))+"</span></div>"
  +"<div class='chip'><b style='color:var(--mut)'>"+n.n+"</b><span>"+esc(t("none"))+"</span></div></div>";
 var hot=n.r+n.a;
 h+=hot?"<div class='banner'>"+esc(fmt(t("hotB"),{n:hot}))+"</div>":"<div class='banner calm'>"+esc(t("calmB"))+"</div>";
 var order={r:0,a:1,g:2,n:3};
 var sorted=P.slice().sort(function(x,y){return order[CONFK[x.Confidence]||"n"]-order[CONFK[y.Confidence]||"n"];});
 h+="<table>"+th(t("h1"))+"<tbody>";
 sorted.forEach(function(p){
  h+="<tr><td>"+light(p.Confidence)+"</td><td class='mono'>"+esc(p.WopID||"—")+"</td><td><b>"+esc(p.ProjectCode)+"</b> "+esc(p.ProjectName)+"</td>"
   +"<td>"+esc(p.Owner)+"</td><td>"+esc(p.BaselineStatus)+"<div class='ev'>"+esc(t("upd"))+" "+esc(p.BaselineUpdated||"—")+"</div></td>"
   +"<td>"+esc(p.ObservedLast||"—")+" <span class='mut'>"+esc(p.ObservedDir||"")+"</span></td>"
   +"<td class='mono'>"+esc(p.ObservedMsgs||"0")+"</td>"
   +"<td>"+(p.ProposeValue?("<b>"+esc(p.ProposeValue)+"</b>"):"<span class='mut'>—</span>")
   +"<div class='ev'>"+esc(p.Evidence)+"</div></td></tr>";});
 h+="</tbody></table>";
 h+=rLoad();
 el.innerHTML=h;
}

function rP2(){
 var el=document.getElementById("p2"),h="";
 var urg=PD.filter(function(p){return parseInt(p.WaitingDays||0,10)>=3;});
 h+=urg.length?"<div class='banner'>"+esc(fmt(t("urgB"),{n:urg.length}))+"</div>"
              :"<div class='banner calm'>"+esc(t("calmQ"))+"</div>";
 if(PD.length){
  h+="<table>"+th(t("h2"))+"<tbody>";
  PD.forEach(function(p){
   var d=parseInt(p.WaitingDays||0,10),k=d>=7?"r":(d>=3?"a":"g");
   h+="<tr data-thr='"+esc(p.ThrID||"")+"'><td><span class='lt "+k+"'>"+esc(d>=7?t("ovd"):(d>=3?t("due"):t("obs")))+"</span></td>"
    +"<td class='mono'>"+esc(p.ThrID||"—")+"</td><td>"+esc(p.Subject)+"</td><td>"+esc(p.TO)+"</td><td class='mono'>"+esc(p.SentOn)+"</td>"
    +"<td class='days'>"+d+"</td><td>"+esc(t("nr"))+"</td></tr>";});
  h+="</tbody></table>";
 }
 if(DQ.length){
  h+="<div class='sec'>"+esc(t("dqT"))+"</div><div class='banner info'>"+esc(t("dqNote"))+"</div>";
  h+="<table>"+th(t("h2b"))+"<tbody>";
  DQ.forEach(function(q){
   h+="<tr><td class='mono'>"+esc(q.CaseID||"—")+"</td><td><b>"+esc(q.ProjectCode||"—")+"</b></td><td class='mono'>"+esc(q.Template)+"</td>"
    +"<td>"+esc(q.To)+"</td><td>"+esc(q.OrigSubject)+"</td><td class='days'>"+esc(q.WaitingDays)+"</td></tr>";});
  h+="</tbody></table>";
 }
 h+="<div class='sec'>"+esc(t("inT"))+"</div>";
 var IR=MA.slice(0,40);
 if(IR.length){
  h+="<table>"+th(t("h3"))+"<tbody>";
  IR.forEach(function(m){
   h+="<tr data-thr='"+esc(m.ThrID||"")+"'><td class='mono'>"+esc(m.EventDate)+"</td><td>"+esc(m.SenderEmail)+"</td><td>"+esc(m.Subject)+"</td>"
    +"<td>"+(String(m.Unread).toLowerCase()==="true"?"<span class='lt a'>"+esc(t("unread"))+"</span>":"<span class='mut'>—</span>")+"</td></tr>";});
  h+="</tbody></table>";
 } else { h+="<div class='mut'>"+esc(t("empty"))+"</div>"; }
 el.innerHTML=h;
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

var SEL={};
function selCount(){return Object.keys(SEL).length;}
function selBar(){
 var b=document.getElementById("selbar");
 if(selCount()){b.style.display="flex";
  document.getElementById("selN").textContent=fmt(t("selN"),{n:selCount()});
  document.getElementById("selHint").textContent=t("selHint");
  document.getElementById("selCopy").textContent=t("selBtn");
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
 var cmd="via-workops drafts "+Object.keys(SEL).join(",");
 function done(){var b=document.getElementById("selCopy");b.textContent=t("copied");setTimeout(selBar,1600);}
 if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(cmd).then(done,function(){window.prompt("Copy:",cmd);done();});}
 else{window.prompt("Copy:",cmd);done();}
});
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
function render(){
 document.getElementById("ttl").textContent=t("ttl");
 document.getElementById("sub").textContent=fmt(t("sub"),{g:DATA.generated,d:DATA.days,p:P.length,q:PD.length});
 var tabs=document.querySelectorAll(".tab");
 tabs[0].textContent=t("t1");tabs[1].textContent=t("t2");tabs[2].textContent=t("t3");if(tabs[3])tabs[3].textContent=t("t4");
 rP1();rP2();rP3();rP4();
 selWire();selApply();
}
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
Write-Host ("[總結] 專案 {0} 案 · 未回追蹤 {1} 件 · 草稿佇列 {2} 件(絕不代寄)· 關係人 {3} 人" -f @($rec).Count, @($pendSorted).Count, @($queue).Count, @($stak).Count) -ForegroundColor Green

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
