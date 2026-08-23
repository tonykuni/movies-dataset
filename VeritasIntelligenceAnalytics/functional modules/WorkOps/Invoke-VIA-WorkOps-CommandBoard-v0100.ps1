#requires -Version 7.0
<#
==========================================================================================
 Invoke-VIA-WorkOps-CommandBoard v0100 — WorkOps 指揮板(一支到底)
------------------------------------------------------------------------------------------
 產品定位(操作員 2026/08/08 裁決):
   一、不是另一個 Outlook — 價值在「以專案為單位」的歸戶與控管表交叉核對,Outlook 沒有。
   二、人不看 Excel — control_sheet.csv 由系統自動吃入、自動對帳、自動亮燈;人只看本頁。
   三、不複雜 — 一個指令進、一頁出、零設定;主動浮出需要追的信,回沒回自動記錄。
 流程:重用 Invoke-VeritasMailOps.ps1(-Action Scan → Reconcile,唯讀 Outlook、不改控管表)
   → 讀 out\reconcile.csv / pending.csv / mails.csv → 資料內嵌 → 兩頁式 Workbench HTML
   → 輸出 run-local VIA_Reports\workops_run\(不入庫)→ 非阻塞開啟。
 治理:唯讀;不卡斷(無 Read-Host / exit);Outlook 未開誠實降級用既有佐證;缺控管表給引導卡。
 回退:bin\via-workops.cmd 改回 v002 靜態儀表板接線。
==========================================================================================
#>
param(
    [int]$Days = 14,
    [switch]$NoScan,
    [switch]$NoOpen
)
$ErrorActionPreference = "Continue"
$Here    = $PSScriptRoot
$ViaRoot = Split-Path (Split-Path $Here -Parent) -Parent
$OutDir  = Join-Path $Here "out"
$Control = Join-Path $Here "control_sheet.csv"
$RunDir  = Join-Path $ViaRoot "VIA_Reports\workops_run"
New-Item -ItemType Directory -Force -Path $RunDir | Out-Null

Write-Host "==========================================================" -ForegroundColor DarkCyan
Write-Host "  VIA WorkOps 指揮板 v0100  |  專案控管 x 追蹤哨 · 一支到底" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor DarkCyan

# ---- [1/4] 掃描 + 對帳(重用 v001 引擎;Outlook 不在 = 誠實降級用既有佐證)----
$engine = Join-Path $Here "Invoke-VeritasMailOps.ps1"
if (-not $NoScan -and (Test-Path -LiteralPath $engine)) {
    Write-Host "[1/4] 掃描 Outlook(唯讀)+ 控管表對帳..." -ForegroundColor Yellow
    & $engine -Action Scan -Days $Days
    & $engine -Action Reconcile
} else {
    Write-Host "[1/4] 略過掃描(-NoScan 或引擎缺席)— 用既有 out\*.csv" -ForegroundColor DarkYellow
}

# ---- [2/4] 讀資料 ----
Write-Host "[2/4] 彙整佐證..." -ForegroundColor Yellow
function Read-CsvSafe { param([string]$p)
    if ((Test-Path -LiteralPath $p) -and (Get-Item -LiteralPath $p).Length -gt 0) { return @(Import-Csv -LiteralPath $p -Encoding UTF8) }
    return @()
}
$rec   = Read-CsvSafe (Join-Path $OutDir "reconcile.csv")
$pend  = Read-CsvSafe (Join-Path $OutDir "pending.csv")
$mails = Read-CsvSafe (Join-Path $OutDir "mails.csv")
$pendSorted = @($pend | Sort-Object { $v = 0; [int]::TryParse([string]$_.WaitingDays, [ref]$v) | Out-Null; -$v })
$inRecent   = @($mails | Sort-Object EventDate -Descending | Select-Object -First 40)

$data = [ordered]@{
    generated      = (Get-Date).ToString("yyyy/MM/dd HH:mm")
    days           = $Days
    has_control    = (Test-Path -LiteralPath $Control)
    control_path   = $Control
    projects       = $rec
    pending        = $pendSorted
    inbound_recent = $inRecent
}
$json = ($data | ConvertTo-Json -Depth 6 -Compress)
if ($null -eq $json) { $json = "{}" }
$json = $json.Replace("</", "<\/")

# ---- [3/4] 兩頁式 Workbench HTML(資料內嵌,零點擊零設定)----
Write-Host "[3/4] 生成指揮板..." -ForegroundColor Yellow
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
.strip{height:3px;display:flex}.strip i{flex:1}
.tabs{display:flex;gap:4px;padding:12px 26px 0;border-bottom:1px solid var(--line);background:var(--panel)}
.tab{padding:9px 18px;font-size:13px;font-weight:600;color:var(--mut);cursor:pointer;border:1px solid transparent;border-bottom:none;border-radius:6px 6px 0 0}
.tab.on{color:var(--ink);background:var(--bg);border-color:var(--line)}
.page{display:none;padding:20px 26px;max-width:1180px;margin:0 auto}.page.on{display:block}
.band{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.chip{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:9px 16px;min-width:104px}
.chip b{display:block;font-size:20px;font-weight:600}.chip span{font-size:11px;color:var(--mut)}
.banner{background:#f7ecdC;border:1px solid var(--amber);border-radius:9px;padding:11px 16px;margin-bottom:14px;font-weight:600;color:#7a5a1f}
.banner.calm{background:#e9f0ea;border-color:var(--green);color:var(--green2)}
table{width:100%;border-collapse:collapse;background:var(--card);border:1px solid var(--line);border-radius:9px;overflow:hidden}
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
.mono{font-family:var(--mono)}.mut{color:var(--mut)}.sec{font-size:12px;font-weight:600;color:var(--mut);margin:18px 0 8px;text-transform:uppercase;letter-spacing:.04em}
.foot{text-align:center;color:var(--mut2);font-size:10px;font-family:var(--mono);padding:18px}
</style>
</head>
<body>
<div class="mast"><div class="seal">務</div>
 <div><h1>VIA WorkOps 指揮板</h1><div class="sub" id="sub"></div></div></div>
<div class="strip"><i style="background:#4c78a8"></i><i style="background:#4f9465"></i><i style="background:#c4634f"></i><i style="background:#bf8f33"></i><i style="background:#3d8f8f"></i><i style="background:#7a6daa"></i></div>
<div class="tabs">
 <div class="tab on" data-p="p1">① 專案指揮</div>
 <div class="tab" data-p="p2">② 追蹤哨</div>
</div>
<div class="page on" id="p1"></div>
<div class="page" id="p2"></div>
<div class="foot">VIA WorkOps · 控管表自動吃入 · 唯讀不回寫 · run-local</div>
<script>
var DATA = __VIA_DATA__;
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function arr(x){return x==null?[]:(Array.isArray(x)?x:[x]);}
var P = arr(DATA.projects), PD = arr(DATA.pending), IR = arr(DATA.inbound_recent);
document.getElementById("sub").textContent = "產生 " + DATA.generated + " · 佐證窗 " + DATA.days + " 天 · 專案 " + P.length + " 案 · 未回追蹤 " + PD.length + " 件";
var CONF = {"Verified":["g","一致"],"Stale":["a","需更新"],"Pending Review":["a","待追蹤"],"Conflicted":["r","矛盾"],"Unmatched":["n","無佐證"],"Incomplete":["n","欄位不全"]};
function light(c){var m=CONF[c]||["n",c];return "<span class='lt "+m[0]+"'>"+esc(m[1])+"</span>";}

/* ① 專案指揮:控管表 x 郵件佐證,一目了然;人不開 Excel */
(function(){
 var el = document.getElementById("p1"), h = "";
 if (!DATA.has_control && P.length === 0) {
  h = "<div class='guide'><h3>尚未接上控管表</h3><ol>"
    + "<li>把 control_sheet.csv 放到 WorkOps 資料夾(或 <span class='mono'>via-workops Templates</span> 產生範例)</li>"
    + "<li>再跑一次 <span class='mono'>via-workops</span> — 系統自動吃入並與郵件交叉核對</li>"
    + "<li>之後控管表由本頁代讀,你不需要再開 Excel</li></ol></div>";
  el.innerHTML = h; return;
 }
 var n = {g:0,a:0,r:0,n:0};
 P.forEach(function(p){ n[(CONF[p.Confidence]||["n"])[0]]++; });
 h += "<div class='band'>"
    + "<div class='chip'><b>"+P.length+"</b><span>控管案件</span></div>"
    + "<div class='chip'><b style='color:var(--green2)'>"+n.g+"</b><span>一致</span></div>"
    + "<div class='chip'><b style='color:#7a5a1f'>"+n.a+"</b><span>需注意</span></div>"
    + "<div class='chip'><b style='color:#8a3a2c'>"+n.r+"</b><span>矛盾</span></div>"
    + "<div class='chip'><b style='color:var(--mut)'>"+n.n+"</b><span>無佐證/不全</span></div></div>";
 var hot = P.filter(function(p){var k=(CONF[p.Confidence]||["n"])[0];return k==="r"||k==="a";});
 h += hot.length ? "<div class='banner'>⚠ "+hot.length+" 案需要你的眼睛(矛盾或待更新)— 已排前列</div>"
                 : "<div class='banner calm'>✓ 控管表與郵件佐證全數一致</div>";
 var order = {r:0,a:1,g:2,n:3};
 var sorted = P.slice().sort(function(x,y){return order[(CONF[x.Confidence]||["n"])[0]] - order[(CONF[y.Confidence]||["n"])[0]];});
 h += "<table><thead><tr><th>燈</th><th>案號 / 案名</th><th>負責人</th><th>控管表狀態</th><th>郵件最後活動</th><th>往來</th><th>系統建議</th></tr></thead><tbody>";
 sorted.forEach(function(p){
  h += "<tr><td>"+light(p.Confidence)+"</td>"
     + "<td><b>"+esc(p.ProjectCode)+"</b> "+esc(p.ProjectName)+"</td>"
     + "<td>"+esc(p.Owner)+"</td>"
     + "<td>"+esc(p.BaselineStatus)+"<div class='ev'>更新日 "+esc(p.BaselineUpdated||"—")+"</div></td>"
     + "<td>"+esc(p.ObservedLast||"—")+" <span class='mut'>"+esc(p.ObservedDir||"")+"</span></td>"
     + "<td class='mono'>"+esc(p.ObservedMsgs||"0")+"</td>"
     + "<td>"+(p.ProposeValue?("<b>"+esc(p.ProposeValue)+"</b>"):"<span class='mut'>—</span>")
     + "<div class='ev'>"+esc(p.Evidence)+"</div></td></tr>";
 });
 h += "</tbody></table>";
 el.innerHTML = h;
})();

/* ② 追蹤哨:未回的主動浮出;已回的自動離列歸戶(回沒回都有記錄) */
(function(){
 var el = document.getElementById("p2"), h = "";
 var urgent = PD.filter(function(p){return parseInt(p.WaitingDays||0,10) >= 3;});
 h += urgent.length ? "<div class='banner'>⚠ "+urgent.length+" 件寄出 ≥3 天未獲回覆 — 建議 <span class='mono'>via-workops FollowUp</span> 一鍵建追蹤草稿(不自動寄)</div>"
                    : "<div class='banner calm'>✓ 目前沒有等待回覆超過 3 天的信</div>";
 if (PD.length) {
  h += "<table><thead><tr><th>燈</th><th>主旨</th><th>對象</th><th>寄出時間</th><th>已等</th><th>狀態</th></tr></thead><tbody>";
  PD.forEach(function(p){
   var d = parseInt(p.WaitingDays||0,10);
   var k = d>=7?"r":(d>=3?"a":"g");
   h += "<tr><td><span class='lt "+k+"'>"+(d>=7?"逾期":(d>=3?"該追了":"觀察"))+"</span></td>"
      + "<td>"+esc(p.Subject)+"</td><td>"+esc(p.TO)+"</td>"
      + "<td class='mono'>"+esc(p.SentOn)+"</td>"
      + "<td class='days'>"+d+" 天</td><td>未回覆</td></tr>";
  });
  h += "</tbody></table>";
 } else {
  h += "<div class='guide'><h3>追蹤哨空表</h3><li>你寄出且對方尚未回覆的信會自動列在這裡</li><li>對方一回覆,該串自動離列並歸戶到專案活動 — 回沒回都有記錄</li></div>";
 }
 h += "<div class='sec'>最近收到(自動記錄,"+IR.length+" 筆)</div>";
 if (IR.length) {
  h += "<table><thead><tr><th>時間</th><th>寄件者</th><th>主旨</th><th>未讀</th></tr></thead><tbody>";
  IR.forEach(function(m){
   h += "<tr><td class='mono'>"+esc(m.EventDate)+"</td><td>"+esc(m.SenderEmail)+"</td><td>"+esc(m.Subject)+"</td>"
      + "<td>"+(String(m.Unread).toLowerCase()==="true"?"<span class='lt a'>未讀</span>":"<span class='mut'>—</span>")+"</td></tr>";
  });
  h += "</tbody></table>";
 } else { h += "<div class='mut'>佐證窗內無收件紀錄(或尚未掃描)。</div>"; }
 el.innerHTML = h;
})();

document.querySelectorAll(".tab").forEach(function(t){
 t.addEventListener("click", function(){
  document.querySelectorAll(".tab").forEach(function(x){x.classList.remove("on");});
  document.querySelectorAll(".page").forEach(function(x){x.classList.remove("on");});
  t.classList.add("on"); document.getElementById(t.dataset.p).classList.add("on");
 });
});
/* 主動跳出:有 ≥3 天未回件時,自動切到追蹤哨 */
if (PD.some(function(p){return parseInt(p.WaitingDays||0,10) >= 3;})) {
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

# ---- [4/4] 非阻塞開啟 ----
Write-Host "[4/4] 開啟(非阻塞)..." -ForegroundColor Yellow
if (-not $NoOpen) { Start-Process $outFile | Out-Null }
Write-Host ("[總結] 專案 {0} 案 · 未回追蹤 {1} 件 · 收件佐證 {2} 筆 · PowerShell 保持開啟" -f @($rec).Count, @($pendSorted).Count, @($mails).Count) -ForegroundColor Green

# ===== [VIA:PS-ACCEL:v0100] 20 加速器導入註記(批102 令;零執行純註解) =====
# 本檔已登記導入 VIA 20 加速器冊(01 AST/02 語意/03 Hydra/04 拓撲/05 沙盒/
# 06 修正建議/07 全景/08 SSOT/09 矩陣/10 分群/11 性能/12 同步/13 回滾/
# 14 覆蓋率/15 排程/16 進度條/17 說明/18 非阻塞/19 多引擎/20 部署)。
# 實體模組:supportive modules\VIA_PS_Accel_Module.ps1(dot-source 取用
# Invoke-VIAGuarded/Write-VIAProgress/Invoke-VIAParallel/$VIA_ACCEL20)。
# ===== [VIA:PS-ACCEL:END] =====
