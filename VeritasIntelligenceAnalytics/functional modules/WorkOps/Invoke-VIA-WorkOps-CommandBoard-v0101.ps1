#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-CommandBoard v0101 — WorkOps 指揮板(v0100 版本前送)
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
 回退:動態 pattern 自動指回 v0100(刪本檔即回退)。
==========================================================================================
#>
param(
    [int]$Days = 14,
    [switch]$NoScan,
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
$Here    = $PSScriptRoot
$ViaRoot = Split-Path (Split-Path $Here -Parent) -Parent
$OutDir  = Join-Path $Here "out"
$Control = Join-Path $Here "control_sheet.csv"
$RunDir  = Join-Path $ViaRoot "VIA_Reports\workops_run"
New-Item -ItemType Directory -Force -Path $RunDir, $OutDir | Out-Null

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  VIA WorkOps 指揮板 v0101  |  專案指揮 x 追蹤哨 x 範疇關係人" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

# ---- [1/5] 掃描 + 對帳(重用 v001 引擎;Outlook 不在 = 誠實降級)----
$engine = Join-Path $Here "Invoke-VeritasMailOps.ps1"
if (-not $NoScan -and (Test-Path -LiteralPath $engine)) {
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
$pendSorted = @($pend | Sort-Object { $v = 0; [int]::TryParse([string]$_.WaitingDays, [ref]$v) | Out-Null; -$v })
$mailsAll   = @($mails | Select-Object -First 500)

# ---- [3/5] 草稿佇列預填(≥3 天未回 → recipients_auto.csv;引擎只建草稿不寄)----
Write-Host "[3/5] 預填追蹤草稿佇列(降低修改量;絕不代寄)..." -ForegroundColor Yellow
$codeRe = [regex]'\b[A-Z]{2,6}[-_ ]?\d{2,6}\b'
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
        ProjectCode = $code; ProjectName = $name; To = [string]$p.TO; Cc = ""
        Template = "followup"; OrigSubject = [string]$p.Subject
        SentOn = [string]$p.SentOn; WaitingDays = $wd
    }
}
$autoCsv = Join-Path $OutDir "recipients_auto.csv"
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
<title>VIA WorkOps 指揮板</title>
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
</div>
<div class="page on" id="p1"></div>
<div class="page" id="p2"></div>
<div class="page" id="p3"></div>
<div class="foot">VIA WorkOps · read-only · drafts never auto-sent · run-local</div>
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
 h1:["燈","案號 / 案名","負責人","控管表狀態","郵件最後活動","往來","系統建議"],
 upd:"更新日",noCtrl:"尚未接上控管表",g1:"把 control_sheet.csv 放到 WorkOps 資料夾(或 via-workops Templates 產生範例)",
 g2:"再跑一次 via-workops — 系統自動吃入並交叉核對",g3:"之後控管表由本頁代讀,你不需要再開 Excel",
 urgB:"{n} 件寄出 ≥3 天未獲回覆 — 草稿已預填,執行 via-workops drafts 一次產生(只建草稿,絕不代寄)",
 calmQ:"目前沒有等待回覆超過 3 天的信",
 h2:["燈","主旨","對象","寄出時間","已等","狀態"],ovd:"逾期",due:"該追了",obs:"觀察",nr:"未回覆",
 dqT:"草稿佇列(預填完成,待你過目)",h2b:["案號","範本","收件人","原主旨","已等"],
 dqNote:"系統只建 Outlook 草稿(.Display/.Save),永不 .Send — 你微調後親自寄。預填=案號/對象/範本/敬語,要改的只剩重點一兩句。",
 inT:"最近收到(自動記錄)",h3:["時間","寄件者","主旨","未讀"],unread:"未讀",
 scT:"範疇歸納:郵件叢集 × 控管表覆蓋",h4:["叢集代號","郵件數","關係人數","控管表","裁決"],
 inC:"已控管",missC:"遺漏 — 建議建案",scNote:"從郵件主旨自動歸納專案代號;「遺漏」= 郵件中活躍但控管表沒有的範疇。",
 skT:"利害關係人彙總(全域)",h5:["Email","網域","來信數","最後來信"],
 skPT:"依專案歸戶",h6:["叢集代號","關係人"],empty:"(本窗無資料)"},
cn:{ttl:"VIA WorkOps 指挥板",sub:"生成 {g} · 证据窗 {d} 天 · 项目 {p} 案 · 未回跟踪 {q} 件",
 t1:"① 项目指挥",t2:"② 跟踪哨",t3:"③ 范畴与关系人",
 cases:"管控案件",ok:"一致",warn:"需注意",bad:"矛盾",none:"无证据/不全",
 hotB:"{n} 案需要你的眼睛(矛盾或待更新)— 已排前列",calmB:"管控表与邮件证据全部一致",
 h1:["灯","案号 / 案名","负责人","管控表状态","邮件最后活动","往来","系统建议"],
 upd:"更新日",noCtrl:"尚未接上管控表",g1:"把 control_sheet.csv 放到 WorkOps 文件夹(或 via-workops Templates 生成示例)",
 g2:"再跑一次 via-workops — 系统自动吃入并交叉核对",g3:"之后管控表由本页代读,你不需要再开 Excel",
 urgB:"{n} 件寄出 ≥3 天未获回复 — 草稿已预填,执行 via-workops drafts 一次生成(只建草稿,绝不代发)",
 calmQ:"目前没有等待回复超过 3 天的信",
 h2:["灯","主题","对象","寄出时间","已等","状态"],ovd:"逾期",due:"该追了",obs:"观察",nr:"未回复",
 dqT:"草稿队列(预填完成,待你过目)",h2b:["案号","模板","收件人","原主题","已等"],
 dqNote:"系统只建 Outlook 草稿,永不代发 — 你微调后亲自发送。预填=案号/对象/模板/敬语。",
 inT:"最近收到(自动记录)",h3:["时间","寄件者","主题","未读"],unread:"未读",
 scT:"范畴归纳:邮件簇 × 管控表覆盖",h4:["簇代号","邮件数","关系人数","管控表","裁决"],
 inC:"已管控",missC:"遗漏 — 建议建案",scNote:"从邮件主题自动归纳项目代号;「遗漏」= 邮件中活跃但管控表没有的范畴。",
 skT:"利害关系人汇总(全域)",h5:["Email","域名","来信数","最后来信"],
 skPT:"按项目归户",h6:["簇代号","关系人"],empty:"(本窗无数据)"},
en:{ttl:"VIA WorkOps Command Board",sub:"Generated {g} · window {d}d · {p} projects · {q} awaiting reply",
 t1:"1. Projects",t2:"2. Follow-up Sentinel",t3:"3. Scope & Stakeholders",
 cases:"Tracked cases",ok:"Verified",warn:"Attention",bad:"Conflicted",none:"No evidence",
 hotB:"{n} cases need your eyes (conflicted or stale) — sorted first",calmB:"Control sheet fully consistent with mail evidence",
 h1:["Light","Code / Name","Owner","Sheet status","Last mail activity","Msgs","Suggestion"],
 upd:"updated",noCtrl:"Control sheet not connected",g1:"Put control_sheet.csv in the WorkOps folder (or run via-workops Templates)",
 g2:"Run via-workops again — it ingests and cross-checks automatically",g3:"From then on this page reads the sheet for you — no Excel",
 urgB:"{n} sent mails unanswered for 3+ days — drafts pre-filled; run via-workops drafts to generate them all (drafts only, never auto-sent)",
 calmQ:"Nothing has waited over 3 days",
 h2:["Light","Subject","To","Sent","Waited","State"],ovd:"Overdue",due:"Chase now",obs:"Watch",nr:"No reply",
 dqT:"Draft queue (pre-filled, awaiting your review)",h2b:["Code","Template","To","Original subject","Waited"],
 dqNote:"Drafts are created in Outlook (.Display/.Save) and NEVER sent by the system — you tweak and send yourself.",
 inT:"Recently received (auto-recorded)",h3:["Time","Sender","Subject","Unread"],unread:"unread",
 scT:"Scope induction: mail clusters vs control sheet coverage",h4:["Cluster code","Mails","People","In sheet","Verdict"],
 inC:"Covered",missC:"MISSING — propose new case",scNote:"Project codes induced from mail subjects; MISSING = active in mail but absent from the control sheet.",
 skT:"Stakeholders (global)",h5:["Email","Domain","Mails from","Last seen"],
 skPT:"By project cluster",h6:["Cluster code","People"],empty:"(no data in window)"}};
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
  h+="<tr><td>"+light(p.Confidence)+"</td><td><b>"+esc(p.ProjectCode)+"</b> "+esc(p.ProjectName)+"</td>"
   +"<td>"+esc(p.Owner)+"</td><td>"+esc(p.BaselineStatus)+"<div class='ev'>"+esc(t("upd"))+" "+esc(p.BaselineUpdated||"—")+"</div></td>"
   +"<td>"+esc(p.ObservedLast||"—")+" <span class='mut'>"+esc(p.ObservedDir||"")+"</span></td>"
   +"<td class='mono'>"+esc(p.ObservedMsgs||"0")+"</td>"
   +"<td>"+(p.ProposeValue?("<b>"+esc(p.ProposeValue)+"</b>"):"<span class='mut'>—</span>")
   +"<div class='ev'>"+esc(p.Evidence)+"</div></td></tr>";});
 h+="</tbody></table>";
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
   h+="<tr><td><span class='lt "+k+"'>"+esc(d>=7?t("ovd"):(d>=3?t("due"):t("obs")))+"</span></td>"
    +"<td>"+esc(p.Subject)+"</td><td>"+esc(p.TO)+"</td><td class='mono'>"+esc(p.SentOn)+"</td>"
    +"<td class='days'>"+d+"</td><td>"+esc(t("nr"))+"</td></tr>";});
  h+="</tbody></table>";
 }
 if(DQ.length){
  h+="<div class='sec'>"+esc(t("dqT"))+"</div><div class='banner info'>"+esc(t("dqNote"))+"</div>";
  h+="<table>"+th(t("h2b"))+"<tbody>";
  DQ.forEach(function(q){
   h+="<tr><td><b>"+esc(q.ProjectCode||"—")+"</b></td><td class='mono'>"+esc(q.Template)+"</td>"
    +"<td>"+esc(q.To)+"</td><td>"+esc(q.OrigSubject)+"</td><td class='days'>"+esc(q.WaitingDays)+"</td></tr>";});
  h+="</tbody></table>";
 }
 h+="<div class='sec'>"+esc(t("inT"))+"</div>";
 var IR=MA.slice(0,40);
 if(IR.length){
  h+="<table>"+th(t("h3"))+"<tbody>";
  IR.forEach(function(m){
   h+="<tr><td class='mono'>"+esc(m.EventDate)+"</td><td>"+esc(m.SenderEmail)+"</td><td>"+esc(m.Subject)+"</td>"
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

function render(){
 document.getElementById("ttl").textContent=t("ttl");
 document.getElementById("sub").textContent=fmt(t("sub"),{g:DATA.generated,d:DATA.days,p:P.length,q:PD.length});
 var tabs=document.querySelectorAll(".tab");
 tabs[0].textContent=t("t1");tabs[1].textContent=t("t2");tabs[2].textContent=t("t3");
 rP1();rP2();rP3();
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

# ---- [5/5] 非阻塞開啟 ----
Write-Host "[5/5] 開啟(非阻塞)..." -ForegroundColor Yellow
if (-not $NoOpen) { Start-Process $outFile | Out-Null }
Write-Host ("[總結] 專案 {0} 案 · 未回追蹤 {1} 件 · 草稿佇列 {2} 件(絕不代寄)· 關係人 {3} 人" -f @($rec).Count, @($pendSorted).Count, @($queue).Count, @($stak).Count) -ForegroundColor Green

