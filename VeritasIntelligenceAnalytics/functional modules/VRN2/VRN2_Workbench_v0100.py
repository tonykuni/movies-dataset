#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Workbench v0100 — VRN-2 工作台(前端 = 操作員 2026-10-28 上傳的「VIA VRN-2 Workbench」範本視覺,逐字鎖定;後端 = VRN-2 自己的收據與輸出冊;一支檔把兩邊連成一個頁面)。

操作員令(2026-10-28):「模板視覺鎖定作為前端 html u/i 與後端連棟整合為一個系統 · 透明去背 logo 無框無特效取代模板 logo」。

做法(只增不減 · 不動管理器 / 啟動器既有的 U/I):
  ① 範本的版面 CSS(色票 · 字級 · 格線 · 分頁 · 矩陣 · 卡片)原樣內嵌;字型(DM Sans / DM Mono / Syne / Noto Sans TC · 117 個 woff2)放 VRN2_Workbench_Assets_v0100.zip,
     渲染時解到 <輸出夾>/VRN2_Workbench_assets/ 並以相對路徑引用(沒有資產包 → 退回系統字型,版面不變)。
  ② 範本裡的 {{ 欄位 }} / sc-for / sc-if 在 Python 端用 VRN-2 的真資料展開:
     VIA_Reports/vrn2/{VRN2_Completion_latest · VRN2_Closeout_v*(最新)· VRN2_Activate_latest · VRN2_Scope_latest · VRN2_Input_latest · VRN2_Acceptance_latest ·
     IDEMPOTENCE_latest · VRN2_VerbatimVerify_latest · VRN2_Success_latest · VRN2_Env_latest · tools/VRN2_ToolManifest_*}.json + output/VRN2_{BasicInfo,FinancialData,Summary,Rejected,Combined}_latest.json
     + scope_in/(輸入清單:大小 · 修改時間 · SHA-256 · 完全重複 / 候選重複群組)+ backup/(快照目錄)+ registry/VRN2_Lock_*.json(鎖定版本)。
  ③ 範本按鈕接到 VRN-2 既有的 U/I 操作協定 vrn2://(VRN2_UIAction 處理器):選檔案夾 / 選檔案 / 重新稽核 / 完整重跑 / 不上船 / 清快取 / 還原封存;
     其他系統 Gate 只開本機已登記的入口(VRN-1 / VDF / VCGC),沒登記就標 UNCONFIGURED,不猜路徑。
     範本上「刪除勾選者 / 復原回收區」本版唯讀(按下只顯示說明),不假裝有做。
  ④ logo:找到 VRN2_Logo.(png|jpg|jpeg|webp)(--logo · SSOT/ · functional modules/VRN2/ · VIA_Reports/vrn2/)→ 去白底成透明 PNG(`logo` 動詞也可單獨用)→ 以 data URI 放進頁首,
     .logo 沒有底色 / 圓角 / 陰影 / 邊框(無框無特效);找不到 → 範本原本的「理」字方塊。
  ⑤ 產出 VIA_Reports/vrn2/VRN2_Workbench_latest.html(自含資料 · 分頁 / 匯出 / 擷取在瀏覽器端用 vanilla JS,不連網)。
動詞:render [--root <VIA 根>] [--out <html>] [--logo <圖>] · logo <來源圖> <輸出 png> · --selftest
[VIA:AST-CLASS] 類別 = 前端渲染器(VRN-2 工作台)· 入口 = ActivateVRN-2 收尾後 / 本檔 CLI
"""
from __future__ import annotations

import argparse
import base64
import glob
import hashlib
import html
import io
import json
import os
import re
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v0100"
DISPLAY_NAME = "VRN2_Workbench"
HERE = Path(__file__).resolve().parent
ASSETS_ZIP = "VRN2_Workbench_Assets_v0100.zip"
ASSETS_DIR = "VRN2_Workbench_assets"
OUT_NAME = "VRN2_Workbench_latest.html"
LOGO_NAMES = ("VRN2_Logo.png", "VRN2_Logo.jpg", "VRN2_Logo.jpeg", "VRN2_Logo.webp")
PAGE_SIZE = 25
BOOKS = ("BasicInfo", "FinancialData", "Summary", "Combined", "Rejected")
KEYS = {"BasicInfo": "FILENAME", "Summary": "FILENAME", "FinancialData": "FILENAME · ITEM · PERIOD · PAGE · TABLE", "Combined": "TICKER", "Rejected": "FILENAME · BOOK · ITEM · PERIOD · VALUE"}
LAMP_CLS = {"GREEN": "good", "YELLOW": "", "RED": "bad", "GRAY": "gray"}

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

PAGE_CSS = r""":root{--bg:#f5f4f0;--paper:#fff;--paper2:#faf9f6;--zebra:#f6f4ef;--soft:#eceae2;--ink:#1e1d1a;--ink2:#44423c;--mut:#6b6a66;--mut2:#9c9890;--line:#dbd9d3;
--up:#c96b5a;--down:#5a9e6f;--blue:#4c78a8;--teal:#439a9a;--am:#c4943a;--co:#b5291a;--vi:#8a6bb0;--hd:88px;
font:13px/1.5 "DM Sans","Noto Sans TC",system-ui,sans-serif;color:var(--ink);background:var(--bg)}
*{box-sizing:border-box}body{margin:0;background:var(--bg)}
*{scrollbar-width:thin;scrollbar-color:var(--line) transparent}
*::-webkit-scrollbar{width:6px;height:6px}*::-webkit-scrollbar-thumb{background:var(--line);border-radius:3px}*::-webkit-scrollbar-track{background:transparent}
a{color:var(--blue)}a:hover{color:var(--co)}
header.vh{position:sticky;top:0;z-index:40;height:var(--hd);display:flex;align-items:center;gap:14px;padding:10px 20px;background:var(--paper);color:var(--ink);border-bottom:1px solid var(--line)}
header.vh::after{content:"";position:absolute;left:0;right:0;bottom:-1px;height:4px;background:linear-gradient(90deg,var(--co),var(--am),var(--blue),var(--teal))}
header.vh .logo{width:40px;height:40px;border-radius:8px;background:var(--co);color:#fff;display:flex;align-items:center;justify-content:center;font:700 22px "Noto Sans TC",sans-serif;flex:none}
header.vh small{display:block;font:700 10px "DM Mono",monospace;letter-spacing:2px;text-transform:uppercase;color:var(--mut)}
header.vh h1{font:800 20px "Syne","DM Sans",sans-serif;margin:1px 0 2px;letter-spacing:.2px}
header.vh .tag{font-size:12px;color:var(--mut);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
header.vh .meta{margin-left:auto;text-align:right;font:500 10px "DM Mono",monospace;color:var(--mut2);line-height:1.6;flex:none}
.layout{display:grid;grid-template-columns:272px minmax(0,1fr);height:calc(100vh - var(--hd));align-items:stretch}
.layout.fold{grid-template-columns:30px minmax(0,1fr)}
aside{background:var(--paper);border-right:1px solid var(--line);padding:14px;display:flex;flex-direction:column;gap:12px;overflow:auto;min-height:0;transition:padding .18s}
.layout.fold aside{padding:0;overflow:hidden;align-items:center}
.layout.fold aside>*:not(.foldbtn){display:none}
.foldbtn{width:100%;border:1px solid var(--line);border-radius:6px;background:var(--paper2);color:var(--ink2);padding:5px 9px;font:600 11px "DM Mono",monospace;cursor:pointer;text-align:left;white-space:nowrap;flex:none}
.foldbtn:hover{background:var(--soft)}
.layout.fold .foldbtn{width:auto;height:100%;border-radius:0;border:none;border-right:1px solid var(--line);writing-mode:vertical-rl;letter-spacing:2px;padding:12px 0;text-align:center;background:var(--paper2)}
main{min-width:0;min-height:0;overflow:auto;padding:16px 20px;display:flex;flex-direction:column}
button,a.action,input,select{font:inherit}
button,a.action{padding:6px 11px;border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--ink2);font:600 11.5px "DM Sans","Noto Sans TC",sans-serif;cursor:pointer;text-decoration:none;white-space:nowrap;flex:none}
button:hover{background:var(--soft)}button.primary{background:var(--up);color:#fff;border-color:var(--up)}button.primary:hover{filter:saturate(1.08)}
button.danger{border-color:var(--up);color:var(--up);background:transparent}button:disabled{opacity:.5;cursor:not-allowed}
input[type=text],input[type=date],select{padding:6px 9px;border:1px solid var(--line);border-radius:6px;background:var(--paper);color:var(--ink);font:500 11.5px "DM Mono","Noto Sans TC",monospace}
.box{background:var(--paper);border:1px solid var(--line);border-radius:9px;padding:14px;margin-bottom:14px;box-shadow:0 1px 2px rgba(31,42,42,.05)}
h2{font:800 14.5px "Syne","DM Sans",sans-serif;margin:0 0 10px;display:flex;align-items:center;gap:9px;flex-wrap:wrap}
h3{font:700 10px "DM Mono",monospace;letter-spacing:1.2px;text-transform:uppercase;color:var(--mut);margin:10px 0 6px}
.subtle{font-size:11.5px;color:var(--mut);line-height:1.55}
#drop{padding:26px 12px;border:1.5px dashed var(--line);background:var(--paper2);border-radius:8px;text-align:center;cursor:pointer;color:var(--ink2);font-weight:600}
#drop.drag{border-color:var(--blue);background:rgba(76,120,168,.06)}
aside button{width:100%}.gates{margin-top:auto}.gates button{text-align:left;margin-bottom:5px;font-weight:500}
.gates button.off{opacity:.5;cursor:not-allowed;background:var(--soft)}
.bar,.tabs,.toolbar{display:flex;gap:7px;align-items:center;flex-wrap:wrap}
.bar{justify-content:space-between;margin-bottom:14px}
.tabs button{font:700 11.5px "Syne",sans-serif;color:var(--mut);border-color:transparent;background:transparent}
.tabs button:hover{background:var(--soft);color:var(--ink2)}
.subtabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:10px}
.subtabs button{font:600 11px "DM Sans","Noto Sans TC",sans-serif;color:var(--ink2);background:var(--paper);border-color:var(--line)}
.subtabs button:hover{background:var(--soft)}
.tabs button.active,.subtabs button.active{background:var(--ink);color:#fff;border-color:var(--ink)}
.toolbar{padding:8px 0}
.matrix{overflow:auto;max-height:42vh;border:1px solid var(--line);border-radius:8px}
table{border-collapse:collapse;width:100%;font-size:11.5px}
th,td{padding:6px 10px;text-align:left;border-bottom:1px solid var(--soft);white-space:nowrap}
th{position:sticky;top:0;background:var(--paper2);z-index:1;font:700 8.5px "Syne",sans-serif;text-transform:uppercase;letter-spacing:.5px;color:var(--mut)}
tbody tr:nth-child(even) td{background:var(--zebra)}
td.wrap{white-space:pre-wrap;min-width:220px;max-width:580px;overflow-wrap:anywhere}
td.n{text-align:right;font:600 11px "DM Mono",monospace;font-variant-numeric:tabular-nums}
tr.candidate td{background:rgba(196,148,58,.12)!important}tr.exact td{background:rgba(90,158,111,.12)!important}
input[type=checkbox]{accent-color:var(--up);width:14px;height:14px}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:10px;margin-bottom:14px}
.stat{padding:12px 14px;background:var(--paper2);border:1px solid var(--line);border-radius:8px;min-width:0}
.stat b{display:block;font:800 24px "Syne",sans-serif;line-height:1.2;color:var(--ink)}.stat small{font:500 9.5px "DM Mono",monospace;color:var(--mut);letter-spacing:.5px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:10px}
.cards>.box{margin:0;height:100%;border-left:3px solid var(--blue);border-radius:0 9px 9px 0}
pre{white-space:pre-wrap;overflow-wrap:anywhere;margin:0;font:500 11px "DM Mono",monospace}
.pill{font:700 9px "DM Mono",monospace;letter-spacing:.5px;padding:2px 8px;border-radius:3px;background:var(--am);color:var(--ink)}.pill.good{background:var(--down);color:#fff}.pill.bad{background:var(--up);color:#fff}.warning{color:var(--am)}
#notice{position:sticky;bottom:0;margin-top:auto;padding:9px 14px;background:var(--ink);color:#fff;border-radius:6px;white-space:pre-wrap;font:500 11px "DM Mono",monospace}
#notice:empty{display:none}
main>section,main>.box,main>.stats,main>.cards,main>.split{flex:none}
main::after{content:"";flex:none;height:6px}
.rowcount{margin-left:auto}.pager{display:flex;gap:9px;align-items:center;padding-top:10px}
.split{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:14px}
.dialog-note{padding:8px;background:var(--paper2);border:1px solid var(--line);border-left:3px solid var(--am);color:var(--ink2);border-radius:0 6px 6px 0;text-align:center;font-size:11.5px}
label{cursor:pointer}.frm{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:9px;align-items:end}
.frm label{display:flex;flex-direction:column;gap:4px;font:600 9.5px "DM Mono",monospace;letter-spacing:.5px;text-transform:uppercase;color:var(--mut)}
@media(max-width:850px){.layout{grid-template-columns:230px minmax(0,1fr)}main{padding:12px}}
@media(max-width:640px){:root{--hd:auto}header.vh{height:auto;flex-wrap:wrap;padding:10px 12px}header.vh .meta{margin-left:0;text-align:left;width:100%}
 .layout{grid-template-columns:1fr;height:auto}.layout.fold{grid-template-columns:1fr}aside{border-right:none;border-bottom:1px solid var(--line)}
 .layout.fold .foldbtn{writing-mode:horizontal-tb;width:100%;height:auto;border:none;border-bottom:1px solid var(--line);text-align:left;padding:7px 12px}
 main{overflow:visible}.matrix{max-height:50vh}}
@media print{header.vh,aside,.bar,.toolbar,#notice,.pager{display:none}.layout{display:block;height:auto}main{overflow:visible}.matrix{max-height:none;overflow:visible}th{position:static}table{font-size:9px}td{white-space:pre-wrap}}"""

EXTRA_CSS = r"""
/* v0100 加在範本之後:logo 影像模式(無框無特效)· 燈號 · 唯讀按鈕 · 分頁區塊 */
header.vh .logo.img{background:none;border-radius:0;box-shadow:none;border:none;padding:0;width:44px;height:44px}
header.vh .logo.img img{width:44px;height:44px;object-fit:contain;display:block;filter:none}
.pill.gray{background:var(--soft);color:var(--mut)}
.lamp{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:5px;vertical-align:middle;background:var(--mut2)}
.lamp.GREEN{background:var(--down)}.lamp.YELLOW{background:var(--am)}.lamp.RED{background:var(--up)}.lamp.GRAY{background:var(--mut2)}
a.action.primary{background:var(--up);color:#fff;border-color:var(--up)}a.action{display:inline-block;text-align:center}
aside a.action{width:100%;display:block}
.tabsec{display:none}.tabsec.on{display:block}
td.lampcell{white-space:normal;min-width:160px;max-width:420px;overflow-wrap:anywhere;font-size:11px}
.ro{opacity:.6}
"""

JS = r"""
(function(){
  var D = window.VRN2_DATA, PG = %(pg)d, st = {tab:'overview', ds: D.dsOrder[0] || 'BasicInfo', pg: 0, fold:false, fmt:'pdf', xDs: D.dsOrder.indexOf('FinancialData')>=0?'FinancialData':(D.dsOrder[0]||''), xFmt:'csv'};
  var $ = function(s, r){ return (r||document).querySelector(s); }, $$ = function(s, r){ return Array.prototype.slice.call((r||document).querySelectorAll(s)); };
  var nt; function say(m){ var n = $('#notice'); n.textContent = m; n.style.display = m ? 'block' : 'none'; clearTimeout(nt); nt = setTimeout(function(){ n.textContent=''; n.style.display='none'; }, 6000); }
  function esc(v){ var s = String(v == null ? '' : v); if (/^[=+\-@]/.test(s) && isNaN(+s)) s = "'" + s; return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }
  function csv(rows, cols, bom){ if (!rows.length) return ''; return (bom ? '\uFEFF' : '') + cols.join(',') + '\n' + rows.map(function(r){ return cols.map(function(c){ return esc(r[c]); }).join(','); }).join('\n'); }
  function dl(name, text, type){ var b = new Blob([text], {type: type || 'text/plain;charset=utf-8'}), a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(function(){ URL.revokeObjectURL(a.href); }, 500); }
  function md(title, rows, cols){ if (!rows.length) return '# ' + title + '\n\n(無資料)'; return '# ' + title + '\n\n| ' + cols.join(' | ') + ' |\n| ' + cols.map(function(){ return '---'; }).join(' | ') + ' |\n' + rows.map(function(r){ return '| ' + cols.map(function(c){ return String(r[c] == null ? '' : r[c]).replace(/\|/g, '\\|').replace(/\n/g, ' '); }).join(' | ') + ' |'; }).join('\n'); }
  function cols(ds){ return D.books[ds] ? D.books[ds].cols : []; }
  function rows(ds){ return D.books[ds] ? D.books[ds].rows : []; }
  function setTab(t){ st.tab = t; $$('.tabs button').forEach(function(b){ b.classList.toggle('active', b.getAttribute('data-tab') === t); }); $$('.tabsec').forEach(function(s){ s.classList.toggle('on', s.getAttribute('data-tab') === t); }); }
  function renderData(){
    var R = rows(st.ds), C = cols(st.ds), n = Math.max(1, Math.ceil(R.length / PG)); st.pg = Math.min(st.pg, n - 1);
    $$('.subtabs button[data-ds]').forEach(function(b){ b.classList.toggle('active', b.getAttribute('data-ds') === st.ds); });
    var meta = D.books[st.ds] ? D.books[st.ds].meta : '(無此冊)'; $('#dsMeta').textContent = meta;
    var th = '<tr>' + C.map(function(c){ return '<th>' + hx(c) + '</th>'; }).join('') + '</tr>';
    var page = R.slice(st.pg * PG, st.pg * PG + PG);
    var tb = page.map(function(r){ return '<tr>' + C.map(function(c){ var v = r[c]; var cl = /PRICE|VALUE|UPSIDE|PAGE|ROWS|BULLETS|EPS|MEAN|CLOSE|_PCT/.test(c) ? ' class="n"' : /POINT_|TITLE|REASON|DETAIL|BULLET/.test(c) ? ' class="wrap"' : ''; return '<td' + cl + '>' + hx(v) + '</td>'; }).join('') + '</tr>'; }).join('');
    $('#dsHead').innerHTML = th; $('#dsBody').innerHTML = tb;
    $('#pgRange').textContent = R.length ? ((st.pg * PG + 1) + '–' + Math.min(R.length, st.pg * PG + PG) + ' / ' + R.length) : '0 / 0';
  }
  function hx(v){ return String(v == null ? '' : v).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function xrows(){ var ds = $('#xDs').value, from = $('#xFrom').value, to = $('#xTo').value, q = $('#xQ').value.trim(); return rows(ds).filter(function(r){ var d = String(r.REPORT_DATE || r.LATEST_REPORT_DATE || ''); return (!from || d >= from) && (!to || d <= to) && (!q || JSON.stringify(r).indexOf(q) >= 0); }); }
  function renderX(){ var ds = $('#xDs').value, X = xrows(); $('#xCount').textContent = X.length.toLocaleString() + ' 列 · ' + ds; var pq = D.books[ds] ? D.books[ds].parquet : '(無)';
    $('#xSql').textContent = "-- DuckDB 查詢(直接讀 VRN-2 輸出的 Parquet,不複製)\nSELECT * FROM read_parquet('" + pq + "')\nWHERE REPORT_DATE BETWEEN '" + $('#xFrom').value + "' AND '" + $('#xTo').value + "'" + ($('#xQ').value.trim() ? "\n  AND (TICKER = '" + $('#xQ').value.trim() + "' OR FILENAME ILIKE '%%" + $('#xQ').value.trim() + "%%')" : '') + "\nORDER BY REPORT_DATE DESC;"; }
  function selCount(){ var n = $$('#files input[type=checkbox]:checked').length; $('#nSel').textContent = n + ' 份已勾選'; return n; }
  document.addEventListener('click', function(e){
    var b = e.target.closest('[data-act]'); if (!b) return; var a = b.getAttribute('data-act');
    if (a === 'tab') { setTab(b.getAttribute('data-tab')); if (st.tab === 'data') renderData(); if (st.tab === 'export') renderX(); }
    else if (a === 'ds') { st.ds = b.getAttribute('data-ds'); st.pg = 0; renderData(); }
    else if (a === 'prev') { st.pg = Math.max(0, st.pg - 1); renderData(); }
    else if (a === 'next') { st.pg = Math.min(Math.ceil(rows(st.ds).length / PG) - 1, st.pg + 1); renderData(); }
    else if (a === 'csvAll') { var R = rows(st.ds); dl('VRN2_' + st.ds + '.csv', csv(R, cols(st.ds), true), 'text/csv;charset=utf-8'); say('已匯出整冊 ' + st.ds + ' · ' + R.length + ' 列 · UTF-8 BOM · 公式前綴已轉義'); }
    else if (a === 'fold') { st.fold = !st.fold; $('#layout').classList.toggle('fold', st.fold); b.textContent = st.fold ? '⟩ 展開輸入面板' : '⟨ 折疊輸入面板'; }
    else if (a === 'selAll') { $$('#files input[type=checkbox]').forEach(function(c){ c.checked = true; }); selCount(); }
    else if (a === 'selNone') { $$('#files input[type=checkbox]').forEach(function(c){ c.checked = false; }); selCount(); }
    else if (a === 'selExtras') { var seen = {}; var n = 0; $$('#files tr[data-sha]').forEach(function(tr){ var s = tr.getAttribute('data-sha'); var c = tr.querySelector('input[type=checkbox]'); if (seen[s]) { c.checked = true; n++; } else { seen[s] = 1; c.checked = false; } }); selCount(); say('已勾選 ' + n + ' 份完全重複多餘副本(保留每組第一份)'); }
    else if (a === 'delSel') { say(selCount() ? '本版唯讀:刪除副本(搬回收區)尚未接到後端;請在來源夾自行整理後按「重新稽核輸入」。' : '未勾選任何副本'); }
    else if (a === 'restore') { say('本版唯讀:回收區尚未接到後端。'); }
    else if (a === 'exportPage') {
      var fmt = $('#fmt').value, title = $('.tabs button.active').textContent.trim();
      if (fmt === 'pdf') { window.print(); return; }
      var data, C;
      if (st.tab === 'data') { data = rows(st.ds); C = cols(st.ds); }
      else if (st.tab === 'export') { data = xrows(); C = cols($('#xDs').value); }
      else if (st.tab === 'overview') { data = D.files; C = ['name', 'ext', 'size', 'mtime', 'group', 'sha']; }
      else { data = [{handover: D.handover}]; C = ['handover']; }
      if (fmt === 'json') dl('VRN2_' + st.tab + '.json', JSON.stringify({page: title, generated: new Date().toISOString(), rows: data}, null, 1), 'application/json;charset=utf-8');
      else dl('VRN2_' + st.tab + '.md', md(title, data, C), 'text/markdown;charset=utf-8');
      say('已匯出 ' + title + ' · ' + fmt.toUpperCase() + ' · ' + data.length + ' 列(完整內容,非僅可見列)');
    }
    else if (a === 'extract') {
      var ds = $('#xDs').value, X = xrows(), fmt = $('#xFmt').value, nm = 'VRN2_' + ds + '_' + $('#xFrom').value + '_' + $('#xTo').value;
      if (fmt === 'json') dl(nm + '.json', JSON.stringify({dataset: ds, from: $('#xFrom').value, to: $('#xTo').value, query: $('#xQ').value, rows: X}, null, 1), 'application/json;charset=utf-8');
      else if (fmt === 'parquet') dl(nm + '.catalog.json', JSON.stringify({dataset: ds, path: D.books[ds] ? D.books[ds].parquet : '', filter: {from: $('#xFrom').value, to: $('#xTo').value, q: $('#xQ').value}, note: '瀏覽器不產二進位 Parquet;此為 DuckDB 讀取指標'}, null, 1), 'application/json;charset=utf-8');
      else dl(nm + '.csv', csv(X, cols(ds), true), 'text/csv;charset=utf-8');
      say('已擷取 ' + X.length + ' 列 · ' + fmt.toUpperCase() + (fmt === 'sheets' ? ' · 於 Google Sheets 選「檔案 › 匯入 › 上傳」' : ''));
    }
    else if (a === 'gateOff') { e.preventDefault(); say('未設定此系統的本機入口,不猜測路徑。'); }
  });
  document.addEventListener('change', function(e){ if (e.target.closest('#files')) selCount(); if (e.target.closest('#xform')) renderX(); });
  document.addEventListener('input', function(e){ if (e.target.id === 'xQ') renderX(); });
  var drop = $('#drop'); if (drop) { ['dragover','dragenter'].forEach(function(n){ drop.addEventListener(n, function(e){ e.preventDefault(); drop.classList.add('drag'); }); }); ['dragleave','drop'].forEach(function(n){ drop.addEventListener(n, function(e){ e.preventDefault(); drop.classList.remove('drag'); if (n === 'drop') say('瀏覽器拖曳只能讀檔名,不能寫入來源夾;請用「選擇檔案夾…」或「選擇檔案…」(vrn2:// 原生對話框)。'); }); }); }
  setTab('overview'); renderData(); renderX(); selCount();
})();
"""


# ===== helpers =====
def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def esc(value) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def jread(path: Path, default=None):
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return default


def latest(pattern: str, base: Path) -> Path | None:
    hits = sorted(base.glob(pattern), key=lambda p: (p.stat().st_mtime, p.name))
    return hits[-1] if hits else None


def file_uri(path) -> str:
    return Path(path).resolve().as_uri() if path else ""


def pill(text, cls="") -> str:
    return '<span class="pill %s">%s</span>' % (cls, esc(text))


def lamp(code) -> str:
    code = str(code or "GRAY").upper()
    return '<span class="lamp %s"></span>%s' % (esc(code if code in LAMP_CLS else "GRAY"), esc(code))


# ===== logo =====
def make_transparent(source: Path, target: Path) -> dict:
    """白底 → 透明(去背):alpha = 1 − 最亮通道;半透明邊緣去白暈;裁到內容框 + 4% 留白;PNG。"""
    from PIL import Image
    image = Image.open(source).convert("RGBA")
    try:
        import numpy as np
        a = np.asarray(image).astype("float32")
        rgb, alpha = a[..., :3], a[..., 3] / 255.0
        white = rgb.min(axis=2) / 255.0                                  # 1 = 純白
        new_alpha = np.clip((1.0 - white) * 1.15, 0.0, 1.0) * alpha
        safe = np.maximum(new_alpha, 0.02)[..., None]
        un = np.clip((rgb - 255.0 * (1.0 - safe)) / safe, 0, 255)       # 去白暈(un-premultiply)
        keep = (new_alpha > 0.02)[..., None]
        out = np.where(keep, un, rgb)
        result = np.concatenate([out, (new_alpha * 255.0)[..., None]], axis=2).round().astype("uint8")
        image = Image.fromarray(result, "RGBA")
    except ImportError:
        pixels = image.load()
        width, height = image.size
        for y in range(height):
            for x in range(width):
                r, g, b, a0 = pixels[x, y]
                white = min(r, g, b) / 255.0
                alpha = max(0.0, min(1.0, (1.0 - white) * 1.15)) * (a0 / 255.0)
                if alpha > 0.02:
                    r, g, b = (int(max(0, min(255, (c - 255 * (1 - alpha)) / alpha))) for c in (r, g, b))
                pixels[x, y] = (r, g, b, int(alpha * 255))
    bbox = image.split()[3].point(lambda v: 255 if v > 8 else 0).getbbox()
    if bbox:
        margin = int(max(image.size) * 0.04)
        bbox = (max(0, bbox[0] - margin), max(0, bbox[1] - margin), min(image.width, bbox[2] + margin), min(image.height, bbox[3] + margin))
        image = image.crop(bbox)
    if max(image.size) > 512:
        image.thumbnail((512, 512))
    target.parent.mkdir(parents=True, exist_ok=True)
    image.save(target, "PNG", optimize=True)
    return {"source": str(source), "target": str(target), "size": list(image.size), "bytes": target.stat().st_size}


def find_logo(root: Path, explicit: str | None) -> Path | None:
    candidates = [Path(explicit)] if explicit else []
    for folder in (root / "functional modules" / "VRN" / "SSOT", root / "functional modules" / "VRN2", root / "VIA_Reports" / "vrn2", HERE):
        candidates += [folder / name for name in LOGO_NAMES]
    for path in candidates:
        if path and path.is_file():
            return path
    return None


def logo_data_uri(source: Path, work: Path) -> tuple:
    """回 (data URI, 說明)。已是透明 PNG(有 alpha 且邊角透明)就直接用;否則去背後用。"""
    try:
        from PIL import Image
        image = Image.open(source)
        if image.mode == "RGBA" and image.getpixel((0, 0))[3] == 0 and source.suffix.lower() == ".png":
            data = source.read_bytes(); how = "已透明 · 原樣"
        else:
            target = work / "VRN2_Logo_transparent.png"
            make_transparent(source, target); data = target.read_bytes(); how = "去白底 → " + target.name
        return "data:image/png;base64," + base64.b64encode(data).decode("ascii"), how
    except Exception as exc:  # noqa: BLE001
        return "", "logo 讀取失敗:%s" % exc.__class__.__name__


# ===== data =====
def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def input_files(scope_dir: Path) -> list:
    rows = []
    if not scope_dir.is_dir():
        return rows
    for path in sorted(scope_dir.iterdir()):
        if not path.is_file():
            continue
        stat = path.stat()
        rows.append({"name": path.name, "ext": path.suffix.lower().lstrip("."), "size": stat.st_size, "mtime": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"), "sha": sha256_file(path)})
    by_sha, by_sig, groups = {}, {}, {}
    for row in rows:
        by_sha.setdefault(row["sha"], []).append(row["name"])
        by_sig.setdefault((row["size"], row["mtime"]), []).append(row["name"])
    counter = 0
    for sig, names in by_sig.items():
        if len(names) > 1:
            counter += 1
            for name in names:
                groups[name] = "G%d" % counter
    for row in rows:
        row["group"] = groups.get(row["name"], "")
        row["exact"] = len(by_sha[row["sha"]]) > 1
        row["cls"] = "exact" if row["exact"] else ("candidate" if row["group"] else "")
    return rows


def collect(root: Path) -> dict:
    v2 = root / "VIA_Reports" / "vrn2"
    out = v2 / "output"
    closeout_path = latest("VRN2_Closeout_v*.json", v2) if v2.is_dir() else None
    data = {"root": root, "v2": v2, "out": out,
            "completion": jread(v2 / "VRN2_Completion_latest.json", {}) or {}, "closeout": (jread(closeout_path, {}) if closeout_path else {}) or {},
            "closeout_name": closeout_path.name if closeout_path else "", "activate": jread(v2 / "VRN2_Activate_latest.json", {}) or {},
            "scope": jread(v2 / "VRN2_Scope_latest.json", {}) or {}, "input": jread(v2 / "VRN2_Input_latest.json", {}) or {},
            "acceptance": jread(v2 / "VRN2_Acceptance_latest.json", {}) or {}, "idem": jread(v2 / "IDEMPOTENCE_latest.json", {}) or {},
            "verbatim": jread(v2 / "VRN2_VerbatimVerify_latest.json", {}) or {}, "success": jread(v2 / "VRN2_Success_latest.json", {}) or {},
            "env": jread(v2 / "VRN2_Env_latest.json", {}) or {}, "books": {}, "parquet": {}}
    manifest = latest("VRN2_ToolManifest_v*.json", v2 / "tools") if (v2 / "tools").is_dir() else None
    data["manifest"] = (jread(manifest, {}) if manifest else {}) or {}
    for book in BOOKS:
        rows = jread(out / ("VRN2_%s_latest.json" % book))
        if isinstance(rows, list):
            data["books"][book] = [r for r in rows if isinstance(r, dict)]
        parquet = out / ("VRN2_%s_latest.parquet" % book)
        if parquet.is_file():
            data["parquet"][book] = parquet
    data["files"] = input_files(v2 / "scope_in")
    data["verify"] = latest("VRN2_IndependentVerify_*.json", v2 / "verify_independent") if (v2 / "verify_independent").is_dir() else None
    locks = []
    for folder in (root / "functional modules" / "VRN2" / "registry", root / "functional modules" / "VRN" / "registry"):
        locks += list(folder.glob("VRN2_Lock_2*.json")) if folder.is_dir() else []
    data["locks"] = sorted(locks, key=lambda p: p.name)
    data["backups"] = sorted([p for p in (v2 / "backup").iterdir() if p.is_dir()], key=lambda p: p.name) if (v2 / "backup").is_dir() else []
    return data


def gates(root: Path, data: dict) -> list:
    """其他系統 Gate:只列本機已登記的入口(VRN-1 倉 · VDF 啟動器 · VCGC 主控台);沒有就 UNCONFIGURED,不猜路徑。"""
    rows = []
    vrn1 = os.environ.get("VIA_VRN1_ROOT") or ""
    tools = (data["closeout"].get("tools") or {}) if isinstance(data["closeout"].get("tools"), dict) else {}
    vrn1_path = Path(vrn1) if vrn1 and Path(vrn1).is_dir() else (Path(tools.get("vrn1_root")) if tools.get("vrn1_root") and Path(str(tools.get("vrn1_root"))).is_dir() else None)
    rows.append(("VRN-1", vrn1_path, "VRN-1 倉(VIA_VRN1_ROOT / 借用紀錄)"))
    vdf = root / "functional modules" / "VDF" / "ActivateVDF.py"
    rows.append(("VDF", vdf.parent if vdf.is_file() else None, "VDF 啟動器 ActivateVDF.py"))
    vcgc = sorted((root / "supportive modules" / "registry").glob("CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")) if (root / "supportive modules" / "registry").is_dir() else []
    rows.append(("VCGC", vcgc[-1].parent if vcgc else None, "VCGC 主控台 " + (vcgc[-1].name if vcgc else "")))
    result = []
    for name, path, tip in rows:
        if path:
            result.append({"label": name + " Gate", "href": file_uri(path), "cls": "", "tip": "本機已登記入口 · " + tip + " · " + str(path), "off": False})
        else:
            result.append({"label": name + " Gate · UNCONFIGURED", "href": "", "cls": "off", "tip": "未登記 " + tip + ",不猜測路徑", "off": True})
    return result


# ===== render =====
def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    root = Path(root).resolve()
    data = collect(root)
    v2, out = data["v2"], data["out"]
    out_path = Path(out_path) if out_path else v2 / OUT_NAME
    out_path.parent.mkdir(parents=True, exist_ok=True)
    comp, close, act, inp, acc = data["completion"], data["closeout"], data["activate"], data["input"], data["acceptance"]
    audit = inp.get("audit") or {}
    stock = data["scope"].get("stock") or audit.get("stock_names") or []
    files = data["files"]
    # --- assets(字型)---
    fonts_link = ""
    assets_zip = Path(assets_zip) if assets_zip else (HERE / ASSETS_ZIP)
    if assets_zip.is_file():
        target = out_path.parent / ASSETS_DIR
        if not (target / "fonts.css").is_file():
            with zipfile.ZipFile(assets_zip) as zf:
                zf.extractall(target)
        fonts_link = '<link rel="stylesheet" href="%s/fonts.css">' % ASSETS_DIR
    # --- logo ---
    logo_path = find_logo(root, logo)
    logo_html, logo_note = '<div class="logo">理</div>', "範本預設字樣(找不到 VRN2_Logo.png)"
    if logo_path:
        uri, how = logo_data_uri(logo_path, out_path.parent)
        if uri:
            logo_html = '<div class="logo img"><img src="%s" alt="logo"></div>' % uri
            logo_note = "%s(%s)" % (logo_path.name, how)
    # --- header / aside ---
    meta_line = " · ".join(x for x in (close.get("version") or act.get("version") or "", comp.get("manager") or "", (comp.get("ts") or "")[:16],
                                      ("完成判定 %s · 紅 %s 黃 %s" % (comp.get("verdict"), comp.get("red"), comp.get("yellow"))) if comp else "尚未完成判定") if x)
    plan_info = esc(audit.get("line") or inp.get("audit_line") or "尚未選擇輸入 · 用「選擇檔案夾…」或「選擇檔案…」")
    source_dir = inp.get("source_dir") or ""
    gate_html = "".join(('<a class="action off" href="#" data-act="gateOff" title="%s">%s</a>' % (esc(g["tip"]), esc(g["label"]))) if g["off"] else ('<a class="action" href="%s" target="_blank" title="%s">%s</a>' % (esc(g["href"]), esc(g["tip"]), esc(g["label"]))) for g in gates(root, data))
    opens = [("📂 輸出冊", out), ("🔍 切割檢視(p1view)", v2 / "p1view"), ("📁 個股範圍夾", v2 / "scope_in"), ("🗂 備份夾", v2 / "backup"), ("🧾 舊版 U/I(驗證過的輸出 · 每檔細節)", v2 / "VRN2_UI_latest.html")]
    open_html = "".join('<a class="action" href="%s" target="_blank">%s</a>' % (esc(file_uri(p)), esc(label)) for label, p in opens if p.exists()) or '<small class="subtle">(尚未產生輸出)</small>'
    # --- stats ---
    dup_extra = sum(1 for f in files if f["exact"]) - len({f["sha"] for f in files if f["exact"]})
    summary_rows = data["books"].get("Summary") or []
    gaps = close.get("output_gaps") or []
    stats = [("輸入副本", audit.get("files", len(files))), ("個股範圍", len(stock)), ("完全重複多餘副本", max(0, dup_extra)), ("已出四冊的報告", len(summary_rows)),
             ("輸出缺項", len(gaps)), ("鎖定版本", data["locks"][-1].stem.replace("VRN2_Lock_", "") if data["locks"] else "—")]
    stats_html = "".join('<div class="stat"><small>%s</small><b>%s</b></div>' % (esc(k), esc(v)) for k, v in stats)
    # --- matrix one ---
    files_html = "".join('<tr class="%s" data-sha="%s"><td><input type="checkbox"></td><td>%s</td><td>%s</td><td class="n">%s</td><td>%s</td><td>%s</td><td style="font-family:ui-monospace,monospace;">%s</td></tr>' % (
        f["cls"], esc(f["sha"]), esc(f["name"]), esc(f["ext"]), "{:,}".format(f["size"]), esc(f["mtime"]), esc(f["group"] or "—"), esc(f["sha"][:12] + "…")) for f in files)
    if not files:
        files_html = '<tr><td colspan="7" class="subtle">scope_in 沒有檔案(先選輸入並跑一輪)</td></tr>'
    # --- matrix two(引擎)---
    steps = {str(s.get("step", "")): s for s in (act.get("steps") or [])}
    def step_detail(prefix):
        for key, s in steps.items():
            if key.startswith(prefix):
                return s.get("lamp", "GRAY"), str(s.get("detail", ""))[:160]
        return "GRAY", "—"
    verbatim = data["verbatim"]; idem = data["idem"]; env_rows = data["env"].get("rows") or []
    env_missing = [r.get("module") for r in env_rows if r.get("must") and not r.get("installed")]
    engines = [
        ("啟動器 ActivateVRN-2", close.get("version") or act.get("version") or "—", {0: "GREEN", 2: "YELLOW"}.get(close.get("rc"), "RED" if close else "GRAY"), "輸入夾 " + (source_dir or "—"), "①~⑫ · 跑了 %d 輪" % len(close.get("passes") or []), data["closeout_name"] or "—", "rc 0 綠 / 2 黃 / 1 紅"),
        ("VRN-2 SystemManager", comp.get("manager") or acc.get("manager") or "—", "GREEN" if comp.get("verdict") == "完成" else ("GRAY" if not comp else "YELLOW"), "scope_in %d 份" % len(files), "完成判定 %s · 紅 %s 黃 %s" % (comp.get("verdict", "—"), comp.get("red", "—"), comp.get("yellow", "—")), "output/VRN2_*_latest.{json,csv,parquet}", "退步 0 · 交互驗證 · 鎖定 + 備份"),
        ("擷取引擎 ENG397", idem.get("engine") or step_detail("② 擷取引擎")[1][:40] or "—", {"GREEN": "GREEN", "STALE_RECORD": "YELLOW", "NONDETERMINISTIC": "RED"}.get(idem.get("classification"), step_detail("⑥ ENG397")[0]), "PDF(文字層 / OCR 階梯)", "冪等閘 %s" % (idem.get("classification") or "—"), "p1view / FinancialData", (idem.get("method") or "")[:90] or "—"),
        ("摘要器 ENG062", acc.get("summarizer") or step_detail("② 摘要器")[1][:40] or "—", {"PASS": "GREEN", "REVIEW_MISSING": "YELLOW", "REVIEW_OCR": "YELLOW", "FAIL": "RED"}.get(verbatim.get("verdict"), "GRAY"), "前段本文區塊", "四點原文核對 %s" % json.dumps(verbatim.get("counts") or {}, ensure_ascii=False), "Summary 四點(逐字 · 頁碼 · 字元區間 · 雜湊)", "每點 = 來源精確字串"),
        ("獨立驗證器", (data["verify"].name if data["verify"] else "—"), "GREEN" if data["verify"] else "GRAY", "輸出冊 + 原文", "第二讀取器逐值回查", "verify_independent/", "只讀 · 不改輸出"),
        ("環境 / 加速器", "缺必裝 %d" % len(env_missing), "RED" if env_missing else ("GREEN" if env_rows else "GRAY"), "第三方套件 %d" % len(env_rows), step_detail("④ 加速器")[1][:80] or "—", "VRN2_Env_latest.json", "缺 → 交 VCGC 裝(VRN-2 只檢查)"),
    ]
    engines_html = "".join('<tr><td>%s</td><td>%s %s</td><td class="lampcell">%s</td><td class="lampcell">%s</td><td class="lampcell">%s</td><td class="lampcell">%s</td></tr>' % (
        esc(n), esc(v), pill(l, LAMP_CLS.get(l, "")), esc(i), esc(p), esc(o), esc(s)) for n, v, l, i, p, o, s in engines)
    # --- acceptance(個股四項)---
    acc_rows = acc.get("files") or []
    acc_html = "".join('<tr><td>%s</td>%s</tr>' % (esc(r.get("file")), "".join('<td class="lampcell">%s %s</td>' % (lamp((r.get(c) or ["GRAY", ""])[0]), esc((r.get(c) or ["", ""])[1])) for c in ("c1", "c2", "c3", "c5", "c7"))) for r in acc_rows)
    # --- jobs text ---
    jobs = ["收尾 %s · rc %s · %s 秒 · 輪數 %d" % (close.get("version", "—"), close.get("rc", "—"), close.get("elapsed_s", "—"), len(close.get("passes") or []))] if close else ["尚未跑過啟動器(沒有收尾收據)"]
    for p in close.get("passes") or []:
        jobs.append("  第 %s 輪 · rc %s · %s" % (p.get("attempt"), p.get("rc"), p.get("idempotence")))
    for s in close.get("steps") or act.get("steps") or []:
        jobs.append("  [%s] %s · %s" % (s.get("lamp"), s.get("step"), str(s.get("detail", ""))[:140]))
    jobs_text = "\n".join(jobs)
    # --- data books(嵌入)---
    books_js, ds_order = {}, []
    for book in BOOKS:
        rows = data["books"].get(book)
        if rows is None:
            continue
        cols = [c for c in (rows[0].keys() if rows else []) if not str(c).startswith("_")]
        parquet = data["parquet"].get(book)
        books_js[book] = {"cols": cols, "rows": [{c: r.get(c) for c in cols} for r in rows], "parquet": str(parquet) if parquet else "(無 parquet)",
                          "meta": "%s · %s 列 · 主鍵 %s · %s" % (book, "{:,}".format(len(rows)), KEYS.get(book, "—"), ("%s(%s B)" % (parquet.name, "{:,}".format(parquet.stat().st_size))) if parquet else "沒有 parquet")}
        ds_order.append(book)
    dsets_html = "".join('<button class="%s" data-act="ds" data-ds="%s">%s</button>' % ("active" if i == 0 else "", esc(b), esc("Bullet Points Summary" if b == "Summary" else re.sub(r"([A-Z])", r" \1", b).strip())) for i, b in enumerate(ds_order)) or '<span class="subtle">output/ 沒有輸出冊</span>'
    xds_html = "".join('<option%s>%s</option>' % (" selected" if b == ("FinancialData" if "FinancialData" in ds_order else (ds_order[0] if ds_order else "")) else "", esc(b)) for b in ds_order)
    dates = sorted({str(r.get("REPORT_DATE") or "") for b in data["books"].values() for r in b if r.get("REPORT_DATE")})
    x_from, x_to = (dates[0] if dates else "2020-01-01"), (dates[-1] if dates else datetime.now().strftime("%Y-%m-%d"))
    # --- lake / snapshots ---
    lock = data["locks"][-1] if data["locks"] else None
    lake = [("鎖定版本", lock.stem.replace("VRN2_Lock_", "") if lock else "—", (str(lock) if lock else "尚未鎖定(⑧ 完成判定過才鎖)")),
            ("Parquet 輸出冊", "%d 冊" % len(data["parquet"]), " · ".join("%s %s B" % (b, "{:,}".format(p.stat().st_size)) for b, p in data["parquet"].items()) or "沒有 parquet"),
            ("收尾收據", data["closeout_name"] or "—", "rc %s · 輸出缺項 %d · 四點原文核對 %s" % (close.get("rc", "—"), len(gaps), verbatim.get("verdict", "—"))),
            ("備份快照", "%d 份" % len(data["backups"]), (data["backups"][-1].name if data["backups"] else "backup/ 空") + " · 鎖定成功才備份")]
    lake_html = "".join('<div class="box"><small class="subtle">%s</small><div style="font-size:20px;font-weight:600;margin:3px 0;">%s</div><div class="subtle">%s</div></div>' % (esc(k), esc(v), esc(n)) for k, v, n in lake)
    snaps = []
    for i, b in enumerate(reversed(data["backups"][-10:])):
        counts = {}
        for book in ("BasicInfo", "FinancialData", "Summary"):
            p = b / ("VRN2_%s_latest.json" % book)
            if not p.is_file():
                p = next(iter(b.rglob("VRN2_%s_latest.json" % book)), None)
            rows = jread(p) if p else None
            counts[book] = "{:,}".format(len(rows)) if isinstance(rows, list) else "—"
        snaps.append((b.name, counts["BasicInfo"], counts["FinancialData"], counts["Summary"], datetime.fromtimestamp(b.stat().st_mtime).strftime("%Y-%m-%d %H:%M"), "CURRENT" if i == 0 else "KEPT"))
    snaps_html = "".join('<tr><td>%s</td><td class="n">%s</td><td class="n">%s</td><td class="n">%s</td><td>%s</td><td>%s</td></tr>' % (esc(v), esc(bi), esc(f), esc(s), esc(at), pill(st, "good" if st == "CURRENT" else "")) for v, bi, f, s, at, st in snaps) or '<tr><td colspan="6" class="subtle">backup/ 還沒有快照</td></tr>'
    incr = [("身份", "輸入檔以檔名進個股範圍(scope_in);矩陣一另算 SHA-256 標出完全重複(淡綠)與時間 / 格式 / 容量相同的候選(淡黃),只標不刪"),
            ("輸出", "每輪整本重寫 output/VRN2_{BasicInfo,FinancialData,Summary,Rejected}_latest.{json,csv,parquet};沒跑完不蓋舊冊(fresh_outputs)"),
            ("快取", "擷取快取按 PDF 雜湊 + 引擎簽章;冪等閘用主跑同一條子行程路徑重跑兩次,紀錄過期 → 清該檔快取自動再跑一輪"),
            ("鎖定", "⑧ 完成判定(退步 0 · 交互驗證 · 冪等 · 四點原文)通過才寫 registry/VRN2_Lock_<時間>.json 並備份到 backup/<時間>/"),
            ("剔除", "對不到原文 / 一格多值 / 非數據列的值進剔除冊(帶理由),不消失、不進主冊"),
            ("格式", "CSV UTF-8 BOM(Excel / Sheets 匯入)· JSON UTF-8 · Parquet 只讀;本頁匯出在瀏覽器端產生,不連網"),
            ("上船", "⑨ 只送 VRN-2 自己的檔;本套件(收尾驗證)⑨ 灰、不推 GitHub")]
    incr_html = "".join('<tr><td style="white-space:nowrap;color:#556f5b;">%s</td><td class="wrap">%s</td></tr>' % (esc(k), esc(v)) for k, v in incr)
    # --- handover ---
    pending = ["%s · %s · %s" % (i.get("lamp"), i.get("name"), i.get("detail")) for i in (comp.get("items") or []) if i.get("lamp") not in ("GREEN", "GRAY")]
    pending += ["輸出缺項 · %s · %s" % (g.get("book", g.get("file", "")), g.get("reason", ", ".join(g.get("missing") or []))) for g in gaps]
    if verbatim and verbatim.get("verdict") not in (None, "PASS"):
        pending.append("四點原文核對 · %s · %s" % (verbatim.get("verdict"), json.dumps(verbatim.get("counts") or {}, ensure_ascii=False)))
    if env_missing:
        pending.append("③ 缺必裝 · " + "、".join(map(str, env_missing)) + " · 交 VCGC 裝")
    if not pending:
        pending = ["(本輪沒有待跨越的條件)"]
    handover = "\n".join([
        "root: %s" % root, "ui: %s · %s %s" % (out_path.name, DISPLAY_NAME, VERSION), "logo: %s" % logo_note,
        "inputs: %s · 個股 %d · 副本 %d · 完全重複多餘 %d" % (source_dir or "—", len(stock), len(files), max(0, dup_extra)),
        "closeout: %s · rc %s · 輪數 %d · 四點原文 %s · 缺項 %d" % (close.get("version", "—"), close.get("rc", "—"), len(close.get("passes") or []), verbatim.get("verdict", "—"), len(gaps)),
        "completion: %s · %s · 紅 %s 黃 %s · %s" % (comp.get("manager", "—"), comp.get("verdict", "—"), comp.get("red", "—"), comp.get("yellow", "—"), comp.get("ts", "—")),
        "idempotence: %s · %s" % (idem.get("classification", "—"), "、".join(f.get("file", "") for f in idem.get("files") or [])[:160]),
        "books: " + " · ".join("%s %s" % (b, "{:,}".format(len(r))) for b, r in data["books"].items()),
        "lock: %s · backups %d" % (lock.name if lock else "—", len(data["backups"])), "generated: %s" % utc_now()])
    # --- page ---
    nopush = ""
    page = f'''<!DOCTYPE html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VRN-2 Workbench</title>
{fonts_link}
<style>{PAGE_CSS}
{EXTRA_CSS}</style></head>
<body>
<header class="vh">
  {logo_html}
  <div>
    <small>VERITAS INTELLIGENCE ANALYTICS · VRN-2 WORKBENCH</small>
    <h1>VeritasReportNova</h1>
    <div class="tag">AI-Powered System to Transform the Investment Reports into Database Intelligence Asset.</div>
  </div>
  <div class="meta">JSON 交換 · Parquet 主資料庫 (ZSTD) · DuckDB 增量管理<br>{esc(meta_line)}</div>
</header>
<div class="layout" id="layout">
  <aside>
    <button class="foldbtn" data-act="fold">⟨ 折疊輸入面板</button>
    <h2>報告輸入</h2>
    <div id="drop" tabindex="0" role="button">將 Windows 檔案拖曳到這裡<br><span class="subtle">(瀏覽器拖曳只讀檔名 · 正式匯入用下面兩個按鈕)</span></div>
    <a class="action" href="vrn2://pick?kind=folder&amp;cat=stock">📁 選擇檔案夾…(Windows 原生對話框)</a>
    <a class="action" href="vrn2://pick?kind=files&amp;cat=stock">📄 選擇檔案…(pdf / word / txt / 影像)</a>
    <div class="subtle">保留原始來源,工作副本匯入專屬目錄。PDF 可直接接成功基線;其他格式會明列待轉換。</div>
    <a class="action primary" href="vrn2://audit">確定輸入 · 先查資料庫缺漏(重新稽核)</a>
    <div class="dialog-note">{plan_info}</div>
    <a class="action primary" href="vrn2://run">啟動系統 · 只處理缺漏報告(完整重跑 · 快取沿用)</a>
    <a class="action" href="vrn2://run?nopush=1">▶ 重跑(不上船)</a>
    <a class="action" href="vrn2://run-clean">↻ 清快取後重跑</a>
    <a class="action" href="vrn2://restore-archive">↩ 還原封存舊版</a>
    <div class="subtle">目前來源:{esc(source_dir or "—")}<br>vrn2:// 沒反應 → PowerShell:<code>$env:VRN2_SOURCE='C:\\測試樣本報告'</code> 再跑一鍵</div>
    <div class="gates">
      <h3>開啟</h3>
      {open_html}
      <h3>其他系統 Gate</h3>
      {gate_html}
      <small class="subtle">只開啟本機已註冊入口;未設定不猜測路徑。</small>
    </div>
  </aside>
  <main>
    <div class="bar">
      <div class="tabs">
        <button class="active" data-act="tab" data-tab="overview">01 輸入總覽</button><button data-act="tab" data-tab="data">02 資料冊與整合庫</button><button data-act="tab" data-tab="export">03 匯出與增量管理</button><button data-act="tab" data-tab="handover">04 政策與交接</button>
      </div>
      <div class="toolbar">
        <select id="fmt"><option value="pdf">PDF</option><option value="md">Markdown</option><option value="json">JSON UTF-8</option></select>
        <button data-act="exportPage">匯出本頁完整內容</button>
      </div>
    </div>
    <section class="tabsec on" data-tab="overview">
      <div class="stats">{stats_html}</div>
      <div class="box">
        <h2>矩陣一 · 輸入清單與去重審查</h2>
        <div class="subtle">淡黃:時間／格式／容量相同,尚不能視為重複。淡綠:SHA256 完全相同。只刪除你勾選並確認的匯入副本;刪除僅搬移至回收區,可復原。(本版唯讀:勾選與統計可用,刪除 / 復原尚未接到後端)</div>
        <div class="toolbar">
          <button data-act="selAll">全選</button><button data-act="selNone">全部取消</button>
          <button data-act="selExtras">勾選完全重複的多餘副本</button>
          <button class="danger ro" data-act="delSel" title="本版唯讀">確認刪除勾選者</button>
          <button class="ro" data-act="restore" title="本版唯讀">復原回收區 (0)</button>
          <span class="rowcount" id="nSel">0 份已勾選</span>
        </div>
        <div class="matrix"><table>
          <thead><tr><th>勾選</th><th>報告名稱</th><th>格式</th><th>容量 bytes</th><th>修改時間</th><th>候選群組</th><th>完全重複指紋</th></tr></thead>
          <tbody id="files">{files_html}</tbody>
        </table></div>
      </div>
      <div class="box">
        <h2>矩陣二 · 引擎與輸入／生產／輸出／規格狀態</h2>
        <div class="matrix"><table>
          <thead><tr><th>引擎／功能</th><th>版本與狀態</th><th>輸入</th><th>生產／驗證</th><th>輸出</th><th>規格</th></tr></thead>
          <tbody>{engines_html}</tbody>
        </table></div>
        <div class="toolbar"><span class="pill">{esc(data["closeout_name"] or "尚無收尾收據")}</span> <span class="pill {LAMP_CLS.get(act.get("lamp", "GRAY"), "gray")}">啟動檢查 {esc(act.get("lamp", "—"))}</span></div>
        <p class="subtle">檔案存在 ≠ 已在這台機器真實執行;每一格的燈都來自本輪收據(VRN2_Activate / Closeout / Completion / IDEMPOTENCE / VerbatimVerify),沒有收據就是灰。</p>
      </div>
      <div class="box">
        <h2>個股四項驗收 · {len(acc_rows)} 份</h2>
        <div class="matrix"><table>
          <thead><tr><th>檔案</th><th>① 計算驗證</th><th>② 覆蓋</th><th>③ 回原文</th><th>⑤ 一標題四重點</th><th>⑦ 基本資料雙讀</th></tr></thead>
          <tbody>{acc_html or '<tr><td colspan="6" class="subtle">尚未驗收</td></tr>'}</tbody>
        </table></div>
      </div>
      <div class="box"><h2>本輪工作與增量計畫</h2><pre>{esc(jobs_text)}</pre></div>
    </section>
    <section class="tabsec" data-tab="data">
      <div class="box">
        <div class="toolbar subtabs">{dsets_html}<button data-act="csvAll">匯出 CSV／供 Sheets 匯入(整冊)</button></div>
        <div class="subtle">Parquet 為唯一主資料庫格式;CSV 與 Sheets 只是檢視副本(UTF-8 BOM · 公式前綴轉義)。Combined 以 TICKER 關聯三冊,不另建主庫。</div>
        <div class="toolbar"><span class="pill good" id="dsMeta"></span></div>
        <div class="matrix" style="max-height:60vh;"><table><thead id="dsHead"></thead><tbody id="dsBody"></tbody></table></div>
        <div class="pager"><button data-act="prev">上一頁</button><span id="pgRange"></span><button data-act="next">下一頁</button></div>
      </div>
      <div class="box">
        <h2>資料正確性政策</h2>
        <p>歷史實際優先,預估原值保留;一期重疊核對(3%),搭配加減、乘除、單位、期間及合併口徑交叉驗證(相對 1e-6 · 絕對 1 TWD)。缺證據、分母為零、會計口徑衝突、過期價格與無法確認的配息日程均列為待驗證。</p>
        <p class="warning">Parquet 沒有 Excel 式列數上限;仍受磁碟與運算資源限制。超過 Sheets／CSV 檢視能力時,請以 DuckDB 查詢或分頁匯出。</p>
      </div>
    </section>
    <section class="tabsec" data-tab="export">
      <div class="cards" style="margin-bottom:14px;">{lake_html}</div>
      <div class="split">
        <div class="box">
          <h2>擷取特定資料 · 特定日期 → 檢視副本</h2>
          <div class="frm" id="xform">
            <label>資料冊<select id="xDs">{xds_html}</select></label>
            <label>起始日<input type="date" id="xFrom" value="{esc(x_from)}"></label>
            <label>結束日<input type="date" id="xTo" value="{esc(x_to)}"></label>
            <label>標的／關鍵字<input type="text" id="xQ" value="" placeholder="2330 · 台積電 · 留空=全部"></label>
            <label>格式<select id="xFmt"><option value="csv">CSV · UTF-8 BOM</option><option value="sheets">Google Sheets 匯入用 CSV</option><option value="json">JSON UTF-8</option><option value="parquet">Parquet 快照指標</option></select></label>
          </div>
          <div class="toolbar">
            <span class="pill" id="xCount"></span>
            <button class="primary" data-act="extract">擷取並下載</button>
            <span class="subtle">本版未啟用雲端直接寫入;Sheets 走可匯入 CSV。</span>
          </div>
          <pre style="margin-top:8px;" id="xSql"></pre>
        </div>
        <div class="box">
          <h2>增量規則 · VRN-2 的做法</h2>
          <table><tbody>{incr_html}</tbody></table>
        </div>
      </div>
      <div class="box">
        <h2>快照目錄 · backup/</h2>
        <div class="matrix"><table>
          <thead><tr><th>版本</th><th>BasicInfo</th><th>FinancialData</th><th>Summary</th><th>提交時間</th><th>狀態</th></tr></thead>
          <tbody>{snaps_html}</tbody>
        </table></div>
        <p class="subtle">⑧ 完成判定通過 → 鎖定 + 備份;舊快照保留可回復(「還原封存舊版」)。同名不同內容不覆寫。</p>
      </div>
    </section>
    <section class="tabsec" data-tab="handover">
      <div class="box">
        <h2>交接快照 · 輸入、計畫、引擎、資料庫與工作結果</h2>
        <p class="subtle">每頁可匯出 PDF／Markdown／JSON。交接頁收錄完整現況、政策及尚未驗證項目,供下一位接手。</p>
        <pre>{esc(handover)}</pre>
      </div>
      <div class="box">
        <h2>尚未跨越的驗收條件</h2>
        {"".join('<p style="margin:4px 0;">· %s</p>' % esc(p) for p in pending)}
      </div>
    </section>
    <div id="notice" role="status" style="display:none"></div>
  </main>
</div>
<script>window.VRN2_DATA = {json.dumps({"dsOrder": ds_order, "books": books_js, "files": files, "handover": handover}, ensure_ascii=False).replace("</", "<\\/")};</script>
<script>{JS % {"pg": PAGE_SIZE}}</script>
</body></html>
'''
    tmp = out_path.with_suffix(".tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(out_path)
    return out_path


# ===== selftest =====
def _fixture(root: Path) -> None:
    v2 = root / "VIA_Reports" / "vrn2"; out = v2 / "output"; scope = v2 / "scope_in"
    for d in (out, scope, v2 / "backup" / "20261028_010101", root / "functional modules" / "VRN2" / "registry", root / "functional modules" / "VDF", root / "supportive modules" / "registry"):
        d.mkdir(parents=True, exist_ok=True)
    (root / "functional modules" / "VDF" / "ActivateVDF.py").write_text("# vdf\n", encoding="utf-8")
    (root / "supportive modules" / "registry" / "CGC_MDL149_VeritasCentralGovernanceConsole_v0166.py").write_text("# vcgc\n", encoding="utf-8")
    (scope / "A-2330 20260101.pdf").write_bytes(b"%PDF-1.4 a")
    (scope / "A-2330 20260101 (1).pdf").write_bytes(b"%PDF-1.4 a")
    (scope / "B-2454 20260102.pdf").write_bytes(b"%PDF-1.4 bb")
    json.dump({"ts": "2026-10-28T10:00:00", "manager": "VRN-2 SystemManager v0243", "verdict": "完成", "red": 0, "yellow": 1, "exceptions": [], "items": [{"name": "實測退步", "lamp": "GREEN", "detail": "退步 0"}, {"name": "輸出冊", "lamp": "YELLOW", "detail": "缺項 1 份"}]}, open(v2 / "VRN2_Completion_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"system": "VRN-2", "version": "ActivateVRN-2 v0142", "rc": 2, "elapsed_s": 12.5, "passes": [{"attempt": 1, "rc": 0, "idempotence": "GREEN"}], "steps": [{"step": "① CPU", "lamp": "GREEN", "detail": "ok"}], "output_gaps": [{"book": "BasicInfo", "file": "B-2454 20260102.pdf", "missing": ["TARGET_PRICE"]}], "tools": {}}, open(v2 / "VRN2_Closeout_v0142.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"ts": "2026-10-28", "lamp": "GREEN", "version": "ActivateVRN-2 v0142", "steps": [{"step": "② 擷取引擎 ENG397", "lamp": "GREEN", "detail": "VRN_ENG397_P1Segment_v0127.py"}, {"step": "④ 加速器覆蓋", "lamp": "GREEN", "detail": "py 0 · ps1 0"}]}, open(v2 / "VRN2_Activate_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"stock": ["A-2330 20260101.pdf", "B-2454 20260102.pdf"], "non_stock": []}, open(v2 / "VRN2_Scope_latest.json", "w", encoding="utf-8"))
    json.dump({"source_dir": "C:\\測試樣本報告", "audit": {"files": 3, "line": "檔 3(PDF 3)· 個股範圍 2", "stock_names": ["A-2330 20260101.pdf"]}}, open(v2 / "VRN2_Input_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"manager": "v0243", "summarizer": "VRN_ENG062_SummarizerV1_v0117.py", "files": [{"file": "A-2330 20260101.pdf", "c1": ["GREEN", "重算 3 過 <b>"], "c2": ["GREEN", "P1 100%"], "c3": ["GREEN", "12/12"], "c5": ["GREEN", "4/4"], "c7": ["YELLOW", "Email SINGLE"]}]}, open(v2 / "VRN2_Acceptance_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
    json.dump({"engine": "VRN_ENG397_P1Segment_v0127.py", "classification": "GREEN", "method": "shard ×2", "files": [{"file": "A-2330 20260101.pdf"}]}, open(v2 / "IDEMPOTENCE_latest.json", "w", encoding="utf-8"))
    json.dump({"verdict": "PASS", "rc": 0, "counts": {"PASS": 8}}, open(v2 / "VRN2_VerbatimVerify_latest.json", "w", encoding="utf-8"))
    json.dump({"rows": [{"module": "PIL", "must": False, "installed": True}, {"module": "accelerator", "must": True, "installed": False}]}, open(v2 / "VRN2_Env_latest.json", "w", encoding="utf-8"))
    basic = [{"REPORT_DATE": "2026-01-01", "FILENAME": "A-2330 20260101.pdf", "TICKER": "2330", "BROKER": "A", "TITLE": "t <b>", "TARGET_PRICE": "1200", "_STATUS": "x"}, {"REPORT_DATE": "2026-01-02", "FILENAME": "B-2454 20260102.pdf", "TICKER": "2454", "BROKER": "B", "TITLE": "u", "TARGET_PRICE": "", "_STATUS": "x"}]
    fin = [{"REPORT_DATE": "2026-01-01", "FILENAME": "A-2330 20260101.pdf", "TICKER": "2330", "ITEM": "Revenue", "PERIOD": "2026E", "VALUE": "1,000", "PAGE": 3} for _ in range(60)]
    summ = [{"REPORT_DATE": "2026-01-01", "FILENAME": "A-2330 20260101.pdf", "TICKER": "2330", "TITLE": "t", "POINT_1": "p1", "POINT_2": "p2 </script>", "POINT_3": "p3", "POINT_4": "p4", "POINTS_OK": 4}]
    for name, rows in (("BasicInfo", basic), ("FinancialData", fin), ("Summary", summ), ("Rejected", [])):
        json.dump(rows, open(out / ("VRN2_%s_latest.json" % name), "w", encoding="utf-8"), ensure_ascii=False)
        (out / ("VRN2_%s_latest.parquet" % name)).write_bytes(b"PAR1")
    json.dump(basic, open(v2 / "backup" / "20261028_010101" / "VRN2_BasicInfo_latest.json", "w", encoding="utf-8"))
    (root / "functional modules" / "VRN2" / "registry" / "VRN2_Lock_20261028_010101.json").write_text("{}", encoding="utf-8")


def selftest() -> int:
    from PIL import Image
    oks, fails = [], []

    def chk(label, cond):
        (oks if cond else fails).append(label)
        print("  [%s] %s" % ("OK" if cond else "FAIL", label))

    with tempfile.TemporaryDirectory() as td:
        root = Path(td) / "VIA"; _fixture(root)
        # 合成 logo:白底 + 紅方塊 + 淡粉邊
        logo = Path(td) / "seal.jpg"; img = Image.new("RGB", (200, 200), (255, 255, 255))
        for x in range(60, 140):
            for y in range(60, 140):
                img.putpixel((x, y), (181, 41, 26))
        for x in range(50, 60):
            for y in range(60, 140):
                img.putpixel((x, y), (235, 190, 185))
        img.save(logo, "JPEG", quality=95)
        info = make_transparent(logo, Path(td) / "seal.png"); png = Image.open(Path(td) / "seal.png")
        corner, center, edge = png.getpixel((0, 0)), png.getpixel((png.width // 2, png.height // 2)), None
        chk("① 去背:角落透明 · 中心不透明且仍是紅 · 裁到內容框", corner[3] == 0 and center[3] == 255 and center[0] > 150 and center[1] < 80 and info["size"][0] < 200)
        # 沒有 logo / 沒有資產包
        p1 = render(root, Path(td) / "wb1.html", assets_zip=Path(td) / "none.zip"); h1 = p1.read_text(encoding="utf-8")
        chk("② 沒有 logo → 範本「理」字方塊;沒有資產包 → 不引用字型但版面 CSS 在", '<div class="logo">理</div>' in h1 and "fonts.css" not in h1 and "header.vh .logo{" in h1)
        chk("③ 範本欄位全部展開(沒有殘留 {{ }} / sc-for / sc-if)", "{{" not in h1 and "<sc-" not in h1)
        chk("④b 開啟:輸出冊 / 範圍夾 / 備份夾 file:// 連結(存在的才列)", h1.count('target="_blank">📂 輸出冊') == 1 and "📁 個股範圍夾" in h1 and "🗂 備份夾" in h1 and "🔍 切割檢視" not in h1)
        chk("④ 四個分頁 + 五個 vrn2:// 動作 + 兩個 pick + audit", h1.count('data-act="tab"') == 4 and all(x in h1 for x in ("vrn2://run\"", "vrn2://run?nopush=1", "vrn2://run-clean", "vrn2://restore-archive", "vrn2://audit", "vrn2://pick?kind=folder&amp;cat=stock", "vrn2://pick?kind=files&amp;cat=stock")))
        chk("⑤ 矩陣一:3 個輸入 · 完全重複 2 列淡綠(同 sha)· 候選群組 G1", h1.count('<tr class="exact"') == 2 and ">G1<" in h1 and 'data-sha="' in h1)
        chk("⑥ Gate:VDF / VCGC 已登記(file:// 連結)· VRN-1 UNCONFIGURED 不猜路徑", "VDF Gate" in h1 and "VCGC Gate" in h1 and "VRN-1 Gate · UNCONFIGURED" in h1 and h1.count('data-act="gateOff"') == 1)
        chk("⑦ 資料冊嵌入:4 冊 · FinancialData 60 列 · 跳脫 </script> · 底線欄不入", '"dsOrder": ["BasicInfo", "FinancialData", "Summary", "Rejected"]' in h1 and '"rows": [' in h1 and "<\\/script>" in h1 and "</script></" not in h1.split("window.VRN2_DATA")[1].split("</script>")[0] and '"_STATUS"' not in h1)
        chk("⑧ 統計 / 引擎 / 驗收 / 待跨越都來自收據", "完成判定 完成 · 紅 0 黃 1" in h1 and "VRN2_Closeout_v0142.json" in h1 and "VRN_ENG062_SummarizerV1_v0117.py" in h1 and "輸出缺項 · BasicInfo" in h1 and "③ 缺必裝 · accelerator" in h1 and "YELLOW · 輸出冊 · 缺項 1 份" in h1)
        chk("⑨ 快照目錄:backup 一列 CURRENT · 鎖定版本 20261028_010101", 'CURRENT' in h1 and "20261028_010101" in h1)
        chk("⑩ 伺服端渲染的值跳脫(驗收表 <b> → &lt;b&gt;)· 資料冊 JSON 原值保留(瀏覽器端 hx() 再跳脫)", "重算 3 過 &lt;b&gt;" in h1 and '"TITLE": "t <b>"' in h1 and "<b>" not in h1.split('<h2>個股四項驗收')[1].split("</table>")[0])
        # logo + 資產包
        zp = Path(td) / ASSETS_ZIP
        with zipfile.ZipFile(zp, "w") as zf:
            zf.writestr("fonts.css", "@font-face{font-family:'DM Sans';src:url(\"fonts/x.woff2\")}"); zf.writestr("fonts/x.woff2", b"wOF2")
        p2 = render(root, Path(td) / "wb2.html", logo=str(logo), assets_zip=zp); h2 = p2.read_text(encoding="utf-8")
        chk("⑪ logo 去背後以 data URI 進頁首(.logo.img 無底色 / 圓角 / 陰影)· 字型資產解壓並引用", '<div class="logo img"><img src="data:image/png;base64,' in h2 and "header.vh .logo.img{background:none;border-radius:0;box-shadow:none" in h2 and (Path(td) / ASSETS_DIR / "fonts" / "x.woff2").is_file() and 'href="%s/fonts.css"' % ASSETS_DIR in h2)
        (root / "functional modules" / "VRN2" / "VRN2_Logo.png").write_bytes((Path(td) / "seal.png").read_bytes())
        p3 = render(root, Path(td) / "wb3.html", assets_zip=zp); h3 = p3.read_text(encoding="utf-8")
        chk("⑫ 不給 --logo 也會在 functional modules/VRN2/VRN2_Logo.png 找到(已透明 → 原樣)", "logo: VRN2_Logo.png(已透明 · 原樣)" in h3)
        h3b = render(root, Path(td) / "wb3.html", assets_zip=zp).read_text(encoding="utf-8")
        strip = lambda s: re.sub(r"generated: \S+", "", s)
        chk("⑬ 冪等:同輸入再渲染,除時間戳外逐字相同", strip(h3) == strip(h3b))
        from html.parser import HTMLParser
        class P(HTMLParser):
            n = 0
            def handle_starttag(self, tag, attrs): self.n += 1
        parser = P(); parser.feed(h2)
        chk("⑭ HTML 可解析(標籤 > 300)", parser.n > 300)
        empty = Path(td) / "empty"; (empty / "VIA_Reports" / "vrn2").mkdir(parents=True)
        h4 = render(empty, Path(td) / "wb4.html", assets_zip=Path(td) / "none.zip").read_text(encoding="utf-8")
        chk("⑮ 沒有任何收據也能渲染(灰 / 尚未)", "尚未完成判定" in h4 and "尚未跑過啟動器" in h4 and "{{" not in h4)
    print("[計] %s %s --selftest · OK %d · FAIL %d" % (DISPLAY_NAME, VERSION, len(oks), len(fails)))
    return 0 if not fails else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_%s" % VERSION)
    ap.add_argument("verb", nargs="?", choices=["render", "logo"], default="render")
    ap.add_argument("args", nargs="*")
    ap.add_argument("--root", default=None, help="VIA 根(預設 VRN2_ROOT / VIA_ROOT / 本檔往上找)")
    ap.add_argument("--out", default=None, help="輸出 html(預設 <VIA>/VIA_Reports/vrn2/%s)" % OUT_NAME)
    ap.add_argument("--logo", default=None, help="logo 圖(預設找 VRN2_Logo.png)")
    ap.add_argument("--assets", default=None, help="字型資產 zip(預設本檔旁的 %s)" % ASSETS_ZIP)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.verb == "logo":
        if len(a.args) != 2:
            print("用法:logo <來源圖> <輸出 png>"); return 2
        info = make_transparent(Path(a.args[0]), Path(a.args[1]))
        print("[GREEN] logo 去背 → %s · %sx%s · %s B" % (info["target"], info["size"][0], info["size"][1], info["bytes"])); return 0
    root = a.root or os.environ.get("VRN2_ROOT") or os.environ.get("VIA_ROOT")
    if not root:
        p = HERE
        while p.parent != p and not (p / "VIA_Reports").is_dir():
            p = p.parent
        root = str(p)
    path = render(Path(root), Path(a.out) if a.out else None, a.logo, Path(a.assets) if a.assets else None)
    print("[GREEN] %s %s · %s" % (DISPLAY_NAME, VERSION, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
