#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CGC_MDL120_SystemUI v0102 — 標準系統 U/I 前端(批332 收官;批334 輸入介面/矩陣/功能鍵;批335 完工自動化)
====================================================================
操作員令:「將 VIA VAP VDF(首頁要附上所有擷取資料)ACTIVE TAIWAN STOCK
ETF CLASSIFICATION AND ROTATION MONTHLY REVENUE 這幾個主體統整成
標準系統 U/I 前後端相連 收官」。
產出:VIA_UI_System_v0100.html(頁名穩定律;單頁六主體;零 CDN 零外網)
版型=批302 統一殼五律(左欄品牌+編號導航+底部狀態格/麵包屑/規格帶
/統計卡/內容卡)+響應雙態;色票=單一中性(操作員裁示)。
前後端相連三態(誠實):
  LIVE     頁載即 fetch 樞紐 http://127.0.0.1:8765/api/all(MDL095 尾版
           →MDL119 in-process 真值);每主體可「從樞紐重取」/api/<id>
  SNAPSHOT 樞紐不在線→退本頁產頁時內嵌之 MDL119 all() 快照(印快照
           時戳;橫幅誠實)
  OFFLINE  快照亦缺→誠實空
六主體(MDL119 SUBJECTS 單一 SSOT):00 VIA 首頁(所有擷取資料=兩庫全表
+ETF 庫+共識增益庫+OmniFetch 15 車道→落表+存證十冊)/01 VDF/02 VAP
(含 K線快查=樞紐 /vap_kline 律量)/03 主動台股 ETF 分類/04 族群分類×
輪動/05 月營收。每主體尾附「深頁」真連結(既有現役頁)。
圖形律:單色序列量尺(CSS meter;數值必標);極性=雙色+中性零點;
狀態色僅作 OK/PART/SKIP/FAIL 燈,不作序列色。
v0100→v0101(批334 操作員令「輸入介面導入 介面優化 顯示 WELL-ORGANIZED MATRIX
補功能按鍵導入高自動化」):
  ①輸入介面=左欄「執行輸入」(工作下拉四系統分組+契約參數動態顯示 codes/
    range/cats+▶執行/檢測+操作紀錄);同源 CSRF POST /run(Codex 律);file://=
    唯讀停用誠實
  ②運轉矩陣視圖=四系統 × 36 工作:狀態燈/run_id/開始/耗時/進度/尾行+解方/▶
    一鍵;/status 4s 輪詢(run_id 對應本次)
  ③功能鍵=每主體「功能鍵」卡:單鍵+自動鏈(依序執行、任一失敗即停、完成自動
    重取六主體;靶=DeckServer v0116 白名單 +system_ui/group_class/
    group_backtest/story_rotation)
  ④任務冊由 DeckServer 尾版 task_registry() 產頁時嵌入(契約旗標+系統歸屬)
v0101→v0102(批335 操作員令「完成一切未完工作自動化」):+07 完工自動化視圖=
  未完工作冊矩陣(完成度條/現況/自動靶/閘/三態)+閘冊+完工鏈 16 步計畫+最近完工
  實錄+一鍵完工(⟳ 樞紐任務 complete_all=伺服端依序 16 步,PROG 進度;或 ▶ 前端
  自動鏈=僅 AUTO 項靶依序)。閘零自動解除誠實列。
用法:python3 CGC_MDL120_SystemUI_v0102.py [--open] | --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import html
import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
UI = VIA / "supportive modules" / "ui_support"
OUT = UI / "VIA_UI_System_v0100.html"   # 頁名穩定律(連結網指此名;版前進=引擎)
BRIDGE = "http://127.0.0.1:8765"
BUILD = "SYSTEM v0102"


def _api():
    p = sorted(HERE.glob("CGC_MDL119_SystemAPI_v0*.py"))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    sys.modules[p.stem] = m
    spec.loader.exec_module(m)
    return m


CSS = r"""
:root{--bg:#f5f5f2;--paper:#fff;--paper2:#fafaf8;--ink:#1f2530;--ink2:#3c4658;
--mut:#6d7688;--mut2:#9aa2b1;--line:#dcdfe6;--soft:#eef0ee;--acc:#3e6b8f;
--acc2:#c9d8e4;--ok:#4f8f6b;--warn:#b58a3e;--bad:#b05c4d;--neg:#b05c4d;--negs:#efd9d5}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);font:12px/1.5 "Segoe UI","Noto Sans TC",system-ui,sans-serif;display:flex;min-height:100vh}
code,.mono{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}
a{color:var(--acc);text-decoration:none}a:hover{text-decoration:underline}
.rail{width:232px;min-width:232px;background:var(--paper);border-right:1px solid var(--line);padding:14px 0 10px;display:flex;flex-direction:column;gap:4px}
.brand{padding:0 16px 10px;border-bottom:1px solid var(--line)}
.brand .latin{font-size:9.5px;letter-spacing:.22em;color:var(--mut);font-weight:700}
.brand h1{font-size:17px;margin:4px 0 2px;letter-spacing:.02em}
.brand .en{font-size:9.5px;letter-spacing:.14em;color:var(--acc);font-weight:700}
.brand .badge{display:inline-block;margin-top:7px;font-size:10px;font-weight:700;padding:2px 8px;border:1px solid var(--line);border-radius:4px;color:var(--mut);letter-spacing:.08em}
.seal{float:right;width:28px;height:28px;border:2px solid var(--ink2);border-radius:6px;display:grid;place-items:center;font-size:15px;font-weight:700}
.navsec{font-size:8.5px;letter-spacing:.2em;color:var(--mut2);font-weight:700;padding:10px 16px 3px}
.nav a{display:grid;grid-template-columns:26px 1fr;gap:8px;align-items:baseline;padding:5px 16px;color:var(--ink2);cursor:pointer}
.nav a:hover{background:var(--paper2);text-decoration:none}
.nav a.active{background:var(--soft);border-right:3px solid var(--acc);color:var(--ink);font-weight:700}
.nav .no{font-size:9px;color:var(--mut2);font-weight:700}
.nav .lb small{display:block;font-size:8.5px;letter-spacing:.14em;color:var(--mut2);font-weight:600}
.railfoot{margin-top:auto;border-top:1px solid var(--line);padding:8px 16px 0;display:grid;grid-template-columns:1fr 1fr;gap:8px}
.railfoot .k{font-size:9px;letter-spacing:.16em;color:var(--mut2);font-weight:700}
.railfoot .v{font-size:11.5px;font-weight:700;font-variant-numeric:tabular-nums}
.main{flex:1;padding:16px 22px;max-width:1240px;min-width:0}
.crumb{font-size:10px;color:var(--mut);letter-spacing:.04em;margin-bottom:7px}.crumb b{color:var(--acc)}
.crumb .lock{letter-spacing:.16em;font-weight:700}
.head{display:flex;align-items:flex-end;gap:18px;flex-wrap:wrap;border-bottom:2px solid var(--ink);padding-bottom:9px;margin-bottom:12px}
.head h2{font-size:clamp(17px,2.4vw,23px);letter-spacing:.01em}
.head h2 small{font-size:10px;color:var(--mut);font-weight:400;margin-left:10px;letter-spacing:.1em}
.head .sub{width:100%;font-size:11px;color:var(--mut)}
.spec{margin-left:auto;display:flex;gap:16px;flex-wrap:wrap}
.spec .k{font-size:9px;letter-spacing:.18em;color:var(--mut2);font-weight:700}
.spec .v{font-size:11px;font-weight:700;font-variant-numeric:tabular-nums}
.v.ok{color:var(--ok)}.v.warn{color:var(--warn)}.v.bad{color:var(--bad)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(128px,1fr));gap:8px;margin-bottom:12px}
.stat{background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:9px 12px;min-width:0}
.stat .n{font-size:clamp(17px,2vw,21px);font-weight:800;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.stat .zh{font-size:10.5px;color:var(--ink2);margin-top:2px}
.stat .en{font-size:9px;letter-spacing:.18em;color:var(--mut2);font-weight:700}
.card{background:var(--paper);border:1px solid var(--line);border-radius:7px;padding:12px 14px;margin-bottom:10px}
.card h3{font-size:12.5px;letter-spacing:.02em;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}
.card h3 small{font-size:10px;letter-spacing:.16em;color:var(--mut2);font-weight:700}
.card h3 .re{margin-left:auto;font-size:10px;font-weight:600;cursor:pointer;border:1px solid var(--line);padding:1px 8px;border-radius:4px;background:var(--paper2);color:var(--ink2)}
.card .note{font-size:10px;color:var(--mut);margin:3px 0 7px}
.tbl{width:100%;border-collapse:collapse;font-size:11px}
.tbl th{text-align:left;font-size:10px;letter-spacing:.14em;color:var(--mut2);border-bottom:1px solid var(--line);padding:4px 8px 4px 0;font-weight:700;white-space:nowrap}
.tbl td{border-bottom:1px solid var(--soft);padding:4px 8px 4px 0;vertical-align:top;font-variant-numeric:tabular-nums}
.tbl tr:last-child td{border-bottom:0}
.tbl td.r,.tbl th.r{text-align:right}.tbl td.nw{white-space:nowrap}
.tag{display:inline-block;font-size:10px;font-weight:700;padding:1px 7px;border-radius:3px;background:var(--soft);color:var(--ink2);white-space:nowrap}
.tag.ok{background:#e3efe8;color:var(--ok)}.tag.warn{background:#f3ece1;color:var(--warn)}
.tag.bad{background:var(--negs);color:var(--bad)}.tag.mut{color:var(--mut2)}
.wrap-x{overflow-x:auto}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:10px}
.meter{display:grid;grid-template-columns:1fr 68px;gap:6px;align-items:center;min-width:140px}
.meter .bar{height:8px;background:var(--soft);border-radius:2px;overflow:hidden;position:relative}
.meter .bar i{display:block;height:100%;background:var(--acc);border-radius:0 2px 2px 0}
.meter .bar.div{background:linear-gradient(90deg,var(--soft) 50%,var(--soft) 50%)}
.meter .bar.div i{position:absolute;top:0;height:100%;border-radius:2px}
.meter .bar.div i.neg{background:var(--neg);right:50%}
.meter .bar.div i.pos{background:var(--acc);left:50%}
.meter .bar.div:before{content:"";position:absolute;left:50%;top:-2px;width:1px;height:12px;background:var(--mut2)}
.meter .num{font-size:10.5px;text-align:right;font-variant-numeric:tabular-nums;color:var(--ink2);white-space:nowrap}
.banner{border:1px solid var(--line);background:var(--paper2);border-radius:7px;padding:8px 12px;font-size:11px;margin-bottom:10px;display:none}
.banner.on{display:block}.banner.warn{border-color:#e6d2b0;background:#f9f3e7;color:#6b4f1d}
.banner.bad{border-color:#e6c3bd;background:#f9ebe8;color:#6b2e24}
.view{display:none}.view.on{display:block}
.chips span{display:inline-block;font-size:10px;padding:1px 6px;border:1px solid var(--line);border-radius:3px;margin:1px 3px 1px 0;color:var(--ink2)}
.foot{font-size:10.5px;color:var(--mut2);margin-top:6px}
input.q{font:12px/1.4 inherit;padding:3px 8px;border:1px solid var(--line);border-radius:4px;width:110px}
button.b{font:11px/1.4 inherit;padding:3px 10px;border:1px solid var(--line);border-radius:4px;background:var(--paper2);color:var(--ink2);cursor:pointer}
svg.k{width:100%;height:220px;display:block;background:var(--paper2);border:1px solid var(--soft);border-radius:4px}
.deep a{display:inline-block;margin:2px 10px 2px 0}
.inp{padding:8px 16px 6px;border-bottom:1px solid var(--line)}
.inp summary{cursor:pointer;font-size:9px;letter-spacing:.2em;color:var(--mut2);font-weight:700;list-style:none}
.inp label{display:block;font-size:9px;letter-spacing:.16em;color:var(--mut2);font-weight:700;margin-top:6px}
.inp select,.inp input{width:100%;font:11.5px/1.4 inherit;padding:4px 7px;border:1px solid var(--line);border-radius:4px;background:var(--paper);color:var(--ink)}
.inp .row{display:flex;gap:6px;margin-top:8px}.inp .row button{flex:1}
button.b.pri{background:var(--acc);color:#fff;border-color:var(--acc)}button.b:disabled{opacity:.45;cursor:not-allowed}
.xlog{font:10px/1.4 Consolas,ui-monospace,monospace;background:var(--paper2);border:1px solid var(--soft);border-radius:4px;padding:5px 7px;max-height:130px;overflow:auto;white-space:pre-wrap;margin-top:8px;color:var(--ink2)}
.dot{display:inline-block;width:9px;height:9px;border-radius:50%;background:var(--mut2);vertical-align:middle;margin-right:5px}
.dot.running{background:var(--warn)}.dot.ok{background:var(--ok)}.dot.fail{background:var(--bad)}
.tbl th.sys{background:var(--soft);font-size:10px;letter-spacing:.14em;padding:5px 8px;color:var(--ink2)}
.acts{display:flex;flex-wrap:wrap;gap:6px}.acts button.b{padding:5px 11px}
.prog{height:6px;background:var(--soft);border-radius:2px;overflow:hidden;min-width:70px;display:inline-block;width:70px;vertical-align:middle;margin-right:4px}.prog i{display:block;height:100%;background:var(--acc)}
@media(max-width:860px){body{flex-direction:column}.rail{width:100%;min-width:0;padding:14px 0 8px}
.nav{display:flex;overflow-x:auto;gap:2px;padding:0 10px;-webkit-overflow-scrolling:touch}
.nav a{grid-template-columns:auto;white-space:nowrap;padding:7px 10px;border-radius:6px}
.nav a.active{border-right:0;border-bottom:3px solid var(--acc)}.nav .no,.nav .lb small{display:none}
.railfoot{grid-template-columns:repeat(4,1fr);padding:10px 16px 0}.main{padding:16px 14px}
.spec{margin-left:0;gap:14px}.stats{grid-template-columns:repeat(2,1fr)}.grid2{grid-template-columns:1fr}}
@media(max-width:400px){.stats{grid-template-columns:1fr}}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
"""

JS = r"""
var B='__BRIDGE__';
var SNAP=null;try{SNAP=JSON.parse(document.getElementById('snap').textContent);}catch(e){SNAP=null;}
var D=null,SRC='OFFLINE',CUR='home';
/* ---------- 批334:輸入介面 · 運轉矩陣 · 功能鍵 · 自動鏈 ---------- */
var TASKS={};try{TASKS=JSON.parse(document.getElementById('tasks').textContent);}catch(e){TASKS={};}
var TORDER=Object.keys(TASKS),SYSN={CGC:'中央治理',VDF:'資料鍛造',VRN:'報告新星',VAP:'自動繪圖'};
var CSRF=((document.querySelector('meta[name="via-csrf"]')||{}).content||'').trim();
var SAME=location.origin===B,LAST=null,CHAIN=null;
var EXTRA={matrix:{id:'matrix',zh:'運轉矩陣',en:'WELL-ORGANIZED MATRIX · '+TORDER.length+' TASKS',sub:'四系統 × 白名單工作 · 狀態燈 · run_id · 進度 · 解方 · 一鍵'}};
var ACTIONS={
 home:[{zh:'全鏈日更 boot',ids:['boot']},{zh:'歷史回補',ids:['backfill']},{zh:'再生本頁',ids:['system_ui']},{zh:'重生全部 UI',ids:['ui']}],
 vdf:[{zh:'全鏈日更',ids:['boot']},{zh:'歷史回補',ids:['backfill']},{zh:'全球宇宙擷取',ids:['global']},{zh:'月營收 MOPS',ids:['revenue']},{zh:'自動鏈:日更→回補→再生本頁',ids:['boot','backfill','system_ui'],chain:true}],
 vap:[{zh:'標準儀表板',ids:['std_dashboard']},{zh:'重生全部 UI',ids:['ui']},{zh:'自動鏈:儀表板→再生本頁',ids:['std_dashboard','system_ui'],chain:true}],
 etf:[{zh:'ETF 持股抓取',ids:['etf_fetch']},{zh:'持股×共識增益',ids:['etf_enrich']},{zh:'ETF×共識分析',ids:['etf_analysis']},{zh:'自動鏈:抓取→增益→分析→再生本頁',ids:['etf_fetch','etf_enrich','etf_analysis','system_ui'],chain:true}],
 rotation:[{zh:'族群分類 ENG070',ids:['group_class']},{zh:'族群回測 ENG071',ids:['group_backtest']},{zh:'故事輪動橋接 ENG072',ids:['story_rotation']},{zh:'自動鏈:分類→回測→橋接→再生本頁',ids:['group_class','group_backtest','story_rotation','system_ui'],chain:true}],
 revenue:[{zh:'月營收 MOPS',ids:['revenue']},{zh:'族群月營收榜',ids:['revenue_groups']},{zh:'月營收×共識',ids:['revenue_consensus']},{zh:'自動鏈:營收→榜→共識→再生本頁',ids:['revenue','revenue_groups','revenue_consensus','system_ui'],chain:true}]};
function canRun(){return SAME&&/^[A-Za-z0-9_-]{20,200}$/.test(CSRF);}
function xlog(m){var el=document.getElementById('xlog');if(!el)return;var t=new Date().toLocaleTimeString('zh-TW',{hour12:false});el.textContent+=(el.textContent?'\n':'')+'['+t+'] '+m;el.scrollTop=el.scrollHeight;}
function xinit(){var s=document.getElementById('xt');if(!s)return;['CGC','VDF','VRN','VAP'].forEach(function(sys){var ks=TORDER.filter(function(k){return TASKS[k].sys===sys;});if(!ks.length)return;var og=document.createElement('optgroup');og.label=sys+' · '+SYSN[sys];ks.forEach(function(k){var o=document.createElement('option');o.value=k;o.textContent=TASKS[k].zh+(TASKS[k].net?' · NET':'');og.appendChild(o);});s.appendChild(og);});xparams();xgate();}
function xparams(){var t=TASKS[document.getElementById('xt').value]||{};document.getElementById('xf-codes').hidden=!t.codes;document.getElementById('xf-range').hidden=!t.range;document.getElementById('xf-cats').hidden=!t.cats;}
function xgate(){var ok=canRun();var b=document.getElementById('xrun');if(b)b.disabled=!ok;var st=document.getElementById('inpstate');if(st)st.textContent=ok?'同源 · 可執行':(SAME?'權杖缺(重新整理)':'file:// 唯讀預覽');document.querySelectorAll('.acts button,.mxb').forEach(function(x){x.disabled=!ok;});}
function postJson(path,body){return fetch(B+path,{method:'POST',headers:{'Accept':'application/json','Content-Type':'application/json','X-VIA-CSRF':CSRF},body:JSON.stringify(body)}).then(function(r){return r.json().then(function(j){return {code:r.status,j:j};});});}
function runTask(id,p){p=p||{};var t=TASKS[id]||{zh:id};var body={task:id,codes:p.codes||'',start:p.start||'',end:p.end||'',cats:p.cats||''};return postJson('/run',body).then(function(x){var j=x.j||{};if(j.ok&&j.run_id){xlog('已接受:'+t.zh+' · run '+String(j.run_id).slice(0,8));return j;}xlog('拒絕:'+t.zh+' · '+(j.err||('HTTP '+x.code)));return null;}).catch(function(e){xlog('樞紐錯誤:'+e);return null;});}
function waitTerminal(id,rid,ms){ms=ms||45*60000;var t0=Date.now();return new Promise(function(res){(function tick(){fetch(B+'/status').then(function(r){return r.json();}).then(function(st){LAST=st;drawMatrix();var it=st[id];if(it&&it.run_id===rid&&(it.state==='ok'||it.state==='fail')){res(it);return;}if(it&&it.run_id!==rid&&it.state!=='idle'){res({state:'unknown',tail:'樞紐回另一 run_id,停止監看'});return;}if(Date.now()-t0>ms){res({state:'unknown',tail:'逾時停止監看'});return;}setTimeout(tick,3000);}).catch(function(){if(Date.now()-t0>ms){res({state:'unknown',tail:'連線中斷'});return;}setTimeout(tick,4000);});})();});}
function chain(ids,label,p){ids=(ids||[]).filter(function(k){return TASKS[k];});if(!ids.length){xlog('任務不在白名單(先 git pull 樞紐尾版)');return;}if(!canRun()){xlog('file:// 或權杖缺=無法執行(誠實;由樞紐 /system 開啟)');return;}if(CHAIN){xlog('已有鏈執行中:'+CHAIN+'(全域單通道)');return;}CHAIN=label||ids.join('→');xlog((ids.length>1?'自動鏈啟動:':'執行:')+CHAIN);
(function step(i){if(i>=ids.length){xlog('完成:'+CHAIN+' · 重取六主體');CHAIN=null;refetchAll();return;}runTask(ids[i],i===0?p:null).then(function(j){if(!j){xlog('停止(拒絕)');CHAIN=null;return;}return waitTerminal(ids[i],j.run_id).then(function(it){xlog((TASKS[ids[i]]||{}).zh+' → '+it.state+(it.rc!=null?' rc'+it.rc:'')+(it.state!=='ok'&&(it.fix||it.tail)?' · '+(it.fix||it.tail):''));if(it.state!=='ok'){xlog('停止(任一失敗即停=誠實;不假綠)');CHAIN=null;refetchAll();return;}step(i+1);});});})(0);}
function xrun(){var id=document.getElementById('xt').value,t=TASKS[id]||{};var p={codes:t.codes?document.getElementById('xcodes').value.trim():'',start:t.range?document.getElementById('xstart').value.trim():'',end:t.range?document.getElementById('xend').value.trim():'',cats:t.cats?document.getElementById('xcats').value.trim():''};chain([id],t.zh,p);}
function xping(){fetch(B+'/ping').then(function(r){return r.json();}).then(function(j){xlog('樞紐在線 '+(j.v||'')+(j.accel?' · 加速器在位':''));}).catch(function(){xlog('樞紐離線(於倉庫根打 via)');});}
function refetchAll(){if(!SAME)return;fetch(B+'/api/all').then(function(r){return r.json();}).then(function(j){if(j&&j.subjects){D=j;SRC='LIVE';render();show(CUR);}}).catch(function(){});}
function actionsCard(id){var a=(ACTIONS[id]||[]).map(function(x){return {zh:x.zh,chain:x.chain,ids:x.ids.filter(function(k){return TASKS[k];})};}).filter(function(x){return x.ids.length;});if(!a.length)return '';var ok=canRun();
return '<div class="card" id="c-acts"><h3>功能鍵<small>ACTIONS · 一鍵 · 自動鏈</small></h3><div class="note">'+(ok?'同源 CSRF POST 真跑(樞紐白名單);自動鏈=依序執行、任一失敗即停(誠實)、完成後自動重取六主體。':'file:// 或樞紐離線=唯讀(按鍵停用);由樞紐 '+esc(B)+'/system 開啟即可執行。')+'</div><div class="acts">'+a.map(function(x){return '<button class="b'+(x.chain?' pri':'')+'" onclick="chain('+JSON.stringify(x.ids).replace(/"/g,'&quot;')+',\''+esc(x.zh)+'\')"'+(ok?'':' disabled')+'>'+(x.chain?'⟳ ':'▶ ')+esc(x.zh)+'</button>';}).join('')+'</div></div>';}
function drawMatrix(){var el=document.getElementById('v-matrix');if(!el)return;var st=LAST||{};var cnt={idle:0,running:0,ok:0,fail:0};TORDER.forEach(function(k){var s=(st[k]||{}).state||'idle';cnt[s]=(cnt[s]||0)+1;});
var h='<div class="stats">'+stat(n(TORDER.length),'白名單工作','TASKS')+stat('<span class="dot running"></span>'+n(cnt.running),'執行中','RUNNING')+stat('<span class="dot ok"></span>'+n(cnt.ok),'完成','OK')+stat('<span class="dot fail"></span>'+n(cnt.fail),'失敗','FAIL')+stat(n(cnt.idle),'待命','IDLE')+stat(SAME?(LAST?'即時 4s':'等待'):'唯讀','狀態源','STATUS')+'</div>';
var rows=[];['CGC','VDF','VRN','VAP'].forEach(function(sys){var ks=TORDER.filter(function(k){return TASKS[k].sys===sys;});if(!ks.length)return;rows.push('<tr><th class="sys" colspan="10">'+sys+' · '+SYSN[sys]+' · '+ks.length+'</th></tr>');ks.forEach(function(k){var t=TASKS[k],s=st[k]||{state:'idle'};var pc=s.pct!=null?'<span class="prog"><i style="width:'+s.pct+'%"></i></span><span class="mono">'+s.pct+'%</span>':(s.state==='running'?'<span class="tag warn">進行中</span>':'');
rows.push(tr(td('<span class="dot '+esc(s.state)+'"></span>'+esc(s.state),'nw'),td('<code>'+esc(k)+'</code>'),td(esc(t.zh)),td(t.net?'<span class="tag warn">NET</span>':'<span class="tag">本機</span>'),td(s.run_id?'<code>'+esc(String(s.run_id).slice(0,8))+'</code>':'—'),td(esc(s.started||'—')),td(s.elapsed!=null?n(s.elapsed)+'s':'—','r'),td(pc),td(esc((s.tail||'').split('\n').slice(-1)[0]||'').slice(0,120)+(s.fix?'<br><span class="tag bad">解方</span> '+esc(s.fix):'')),td('<button class="b mxb" onclick="chain([\''+k+'\'],\''+esc(t.zh)+'\')"'+(canRun()?'':' disabled')+'>▶</button>')));});});
h+=card('mx','運轉矩陣','WELL-ORGANIZED MATRIX · 4 系統 × '+TORDER.length+' 工作 · /status 4s',SAME?'狀態=樞紐 /status 即時(run_id 對應本次;fail 附解方冊);▶=同源 CSRF POST 單發;全域單通道=同時僅一工作。':'file:// 唯讀預覽:即時狀態與按鍵須由樞紐 /system 開啟。',tbl(['狀態','工作','名稱','通路','run','開始','>耗時','進度','尾行 · 解方','一鍵'],rows));
el.innerHTML=h;}
function poll(){if(!SAME||document.hidden)return;fetch(B+'/status').then(function(r){return r.json();}).then(function(st){LAST=st;drawMatrix();var run=TORDER.filter(function(k){return (st[k]||{}).state==='running';}).length;var e=document.getElementById('runn');if(e)e.textContent=run;}).catch(function(){});}
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
function n(v,d){if(v==null||v===''||isNaN(v))return '—';d=d==null?0:d;return Number(v).toLocaleString('en-US',{minimumFractionDigits:d,maximumFractionDigits:d});}
function pct(v,d){return v==null||isNaN(v)?'—':n(v,d==null?1:d)+'%';}
function tag(s){s=String(s||'SKIP');var c=s==='OK'?'ok':(s==='PART'||s==='BUSY'||s==='SNAPSHOT'?'warn':(s==='FAIL'||s==='OFFLINE'?'bad':'mut'));return '<span class="tag '+c+'">'+esc(s)+'</span>';}
function meter(v,max,d,suf){var p=max>0?Math.max(0,Math.min(100,100*v/max)):0;return '<div class="meter"><div class="bar"><i style="width:'+p.toFixed(1)+'%"></i></div><div class="num">'+n(v,d)+(suf||'')+'</div></div>';}
function dmeter(v,max,d){if(v==null||isNaN(v))return '<div class="meter"><div class="bar div"></div><div class="num">—</div></div>';var p=max>0?Math.min(50,50*Math.abs(v)/max):0;return '<div class="meter"><div class="bar div"><i class="'+(v<0?'neg':'pos')+'" style="width:'+p.toFixed(1)+'%"></i></div><div class="num">'+n(v,d==null?1:d)+'%</div></div>';}
function stat(v,zh,en){return '<div class="stat"><div class="n">'+v+'</div><div class="zh">'+esc(zh)+'</div><div class="en">'+esc(en)+'</div></div>';}
function tbl(h,rows){return '<div class="wrap-x"><table class="tbl"><tr>'+h.map(function(x){return '<th'+(x.charAt(0)==='>'?' class="r"':'')+'>'+esc(x.replace(/^>/,''))+'</th>';}).join('')+'</tr>'+(rows.length?rows.join(''):'<tr><td colspan="'+h.length+'">無資料(誠實空)</td></tr>')+'</table></div>';}
function card(id,zh,en,note,body,re){return '<div class="card" id="c-'+id+'"><h3>'+esc(zh)+'<small>'+esc(en)+'</small>'+(re?'<span class="re" onclick="refetch(\''+re+'\')">從樞紐重取 ↻</span>':'')+'</h3>'+(note?'<div class="note">'+note+'</div>':'')+body+'</div>';}
function deep(pages){if(!pages||!pages.length)return '';return '<div class="card deep"><h3>深頁<small>DEEP PAGES</small></h3><div class="note">既有現役頁(尾版真連結;同夾相對)。</div>'+pages.map(function(p){return '<a href="'+esc(p[1])+'">'+esc(p[0])+' ↗</a>';}).join('')+'</div>';}
function bad(d,zh){return '<div class="card"><h3>'+esc(zh)+'</h3><div class="note">'+tag(d&&d.state)+' '+esc(d&&d.reason||'資料缺(誠實空)')+'</div></div>';}
function td(x,cls){return '<td'+(cls?' class="'+cls+'"':'')+'>'+x+'</td>';}
function tr(){return '<tr>'+Array.prototype.slice.call(arguments).join('')+'</tr>';}
/* ---------- 00 首頁:所有擷取資料 ---------- */
function vHome(d){if(!d||d.state!=='OK')return bad(d,'VIA 首頁');var t=d.totals||{},a=d.atlas||{};var h='';
h+='<div class="stats">'+stat(n(t.dbs),'資料庫 在位','DATABASES')+stat(n(t.tables),'落表','TABLES')+stat(n(t.rows),'總列數','ROWS')+stat(n(t.lanes_ok)+'/'+n(t.lanes),'OmniFetch 車道在位','LANES')+stat(n(t.evidence_ok)+'/'+n((d.evidence||[]).length),'存證冊尾件','EVIDENCE')+stat(n(a.ledger),'台帳筆數','LEDGER')+'</div>';
(d.dbs||[]).forEach(function(db,i){var rows=(db.tables||[]).map(function(x){return tr(td('<code>'+esc(x.table)+'</code>'),td(n(x.rows),'r'),td(n(x.ncols),'r'),td(x.min?esc(x.min)+' → '+esc(x.max):'<span class="tag mut">無日期欄</span>'),td(esc(x.source||'')));});
h+=card('db'+i,db.label,(db.exists?n(db.mb)+' MB · '+(db.tables||[]).length+' 表 · '+n(db.rows)+' 列':'缺'),tag(db.state)+' <code>'+esc(db.path)+'</code>'+(db.ts?' · 更新 '+esc(db.ts):'')+(db.reason?' · '+esc(db.reason):''),db.exists?tbl(['表 TABLE','>列 ROWS','>欄','日期域 RANGE','擷取來源 SOURCE'],rows):'');});
var lr=(d.lanes||[]).map(function(l){return tr(td('<code>'+esc(l.id)+'</code>'),td(esc(l.name)),td(tag(l.state)),td((l.tables||[]).map(function(x){return '<span class="tag '+(x.present?'ok':'mut')+'">'+esc(x.table)+(x.present?' · '+n(x.rows):' · 缺')+'</span>';}).join(' ')||'<span class="tag mut">無落表(統包/派生)</span>'));});
h+=card('lanes','OmniFetch 擷取車道','LANES · '+esc(d.engine_src),'車道→落表=引擎尾版源碼動態解析(零寫死);在位=表存在於庫。工作站 <b>via-pipeline</b> ①a 跑 L12,L15;全車道=OmniFetch run。',tbl(['車道','名稱','狀態','落表 → 列數'],lr));
var er=(d.evidence||[]).map(function(e){return tr(td(esc(e.name)),td(tag(e.state)),td('<code>'+esc(e.latest||'—')+'</code>'),td(esc(e.ts||'')),td(n(e.count),'r'),td('<code>'+esc(e.dir)+'</code>'));});
h+=card('ev','引擎存證冊(尾件)','EVIDENCE · LATEST BY MTIME','分析引擎產出=存證 JSON(append-only);本頁各主體讀尾件。',tbl(['存證','狀態','尾件','時戳','>件數','目錄'],er));
h+=card('atlas','系統總圖 Atlas','SYSTEM ATLAS · MDL112','',tbl(['鍵','值'],Object.keys(a).map(function(k){return tr(td('<code>'+esc(k)+'</code>'),td(esc(a[k])));})));
return h;}
/* ---------- 01 VDF ---------- */
function vVdf(d){if(!d||d.state!=='OK')return bad(d,'VDF');var c=d.counts||{},g=d.global||{};var h='';
h+='<div class="stats">'+stat(esc(d.last_date),'價表尾日','LAST SESSION')+stat(n(c.tickers_daily),'日價標的','TICKERS')+stat(n(c.tickers_adj),'還原價標的','ADJUSTED')+stat(n(c.listings_twse)+'/'+n(c.listings_tpex),'名冊 TWSE/TPEX','LISTINGS')+stat(g.state==='OK'?n(g.tickers):'—','全球標的','GLOBAL')+'</div>';
var ts=(d.tail_sessions||[]).map(function(s){return tr(td(esc(s.date)),td(n(s.n),'r'),td(meter(s.n,d.median_n_60||1,0)),td(s.partial?'<span class="tag warn">不完整(截去)</span>':'<span class="tag ok">完整</span>'));});
h+=card('tail','尾端交易日守衛','TAIL SESSIONS · 近 60 日中位 '+n(d.median_n_60),esc(d.partial_guard),tbl(['日期','>標的數','占中位','判定'],ts));
var rr=Object.keys(d.ranges||{}).map(function(k){var r=d.ranges[k];return tr(td('<code>'+esc(k)+'</code>'),td(tag(r.state)),td(n(r.rows),'r'),td(r.min?esc(r.min)+' → '+esc(r.max):esc(r.reason||'—')));});
h+=card('ranges','核心表日期域','CORE TABLES · 3-STATE','SKIP=表缺或空(工作站補源後即 OK;雲端誠實)。',tbl(['表','狀態','>列','域'],rr));
h+=card('gl','全球單庫','GLOBAL DB',tag(g.state)+' '+(g.state==='OK'?n(g.tickers)+' 標的 · '+esc(g.min)+' → '+esc(g.max):esc(g.reason)),'');
h+=card('eng','擷取引擎尾版','ENGINES','',tbl(['引擎'],(d.engines||[]).map(function(e){return tr(td('<code>'+esc(e)+'</code>'));})));
return h+deep(d.pages);}
/* ---------- 02 VAP ---------- */
function vVap(d){if(!d||d.state!=='OK')return bad(d,'VAP');var h='';var g=d.groups||{},r=d.revenue||{},e=d.etf||{},pl=d.plot_law||{};
h+='<div class="stats">'+stat(n(g.total),'產業族群','GROUPS')+stat(esc(g.date),'交易尾日','SESSION')+stat(esc(r.ym),'月營收尾月','REVENUE YM')+stat(n(e.n_holdable)+'/'+n(e.n_book),'ETF 可查持股/冊','ETF BOOK')+stat(pl.state==='OK'?n(pl.n_ok)+'·'+n(pl.n_fail)+'·'+n(pl.n_legacy):'—','繪圖律稽核 OK·FAIL·LEGACY','PLOT LAW')+'</div>';
var mx=Math.max.apply(null,(g.rows||[]).map(function(x){return x[4]||0;}).concat([1]));
var gr=(g.rows||[]).map(function(x){return tr(td(esc(x[0])),td(n(x[1]),'r'),td(n(x[2])+'/'+n(x[3]),'r'),td(meter(x[4],mx,1,' 億')),td(n(x[5],1),'r'),td(pct(x[6],2),'r'));});
h+=card('groups','族群日況','GROUPS · '+esc(g.date)+' vs '+esc(g.prev),esc(g.lane),tbl(['產業','>家數','>漲/跌','成交值(億)','>平均 PE','>殖利率'],gr),'vap');
var ry=(r.top_yoy||[]).map(function(x){return tr(td('<code>'+esc(x[0])+'</code>'),td(n(x[1]/1000,0),'r'),td(dmeter(x[2],100,1)),td(dmeter(x[3],100,1)));});
h+=card('rev','月營收 YoY 榜','REVENUE TOP YOY · '+esc(r.ym),esc(r.lane),tbl(['代號','>營收(百萬)','MoM','YoY'],ry));
h+=card('kline','個股 K線快查(律量)','KLINE · /vap_kline · 價=還原 量=扣當沖','<input class="q" id="kq" value="2330" maxlength="8"> <button class="b" onclick="kline()">查詢</button> <span id="kmsg" class="tag mut">LIVE 限定(樞紐在線)</span>','<div id="kout"></div>');
var pr=(pl.rows||[]).map(function(x){return tr(td(esc(x.engine)),td(tag(x.state)),td(esc(x.note)));});
h+=card('law','繪圖/TA 資料律稽核','PLOT-DATA LAW · MDL118 · '+esc(pl.file||''),pl.state==='OK'?'律一 價=還原價;律二 量=扣當沖三階(個股→市場比→NaN 缺值)。2330 樣本:個股 '+n((pl.sample||{}).stock)+' · 市場比 '+n((pl.sample||{}).market_ratio)+' · 無料 '+n((pl.sample||{}).none)+' 日。':tag(pl.state)+' '+esc(pl.reason),tbl(['引擎','狀態','註'],pr));
h+=card('stack','Seaborn 圖組存證','VAP STACK · ENG015',tag(d.vap_stack.state)+' '+esc(d.vap_stack.ts||''),'<div class="chips">'+(d.vap_stack.files||[]).map(function(f){return '<span>'+esc(f)+'</span>';}).join('')+'</div>');
h+=card('ep','樞紐分析端點','BRIDGE ENDPOINTS','','<div class="chips">'+(d.bridge_endpoints||[]).map(function(f){return '<span><code>'+esc(f)+'</code></span>';}).join('')+'</div>');
return h+deep(d.pages);}
function kline(){var code=(document.getElementById('kq').value||'').trim();var o=document.getElementById('kout'),m=document.getElementById('kmsg');if(SRC!=='LIVE'){m.className='tag warn';m.textContent='樞紐離線=無法查(誠實;於倉庫根打 via 帶起)';return;}m.className='tag mut';m.textContent='查詢中…';
fetch(B+'/vap_kline?code='+encodeURIComponent(code)+'&months=3').then(function(r){return r.json();}).then(function(k){if(!k||!k.bars||!k.bars.length){m.className='tag bad';m.textContent=(k&&(k.err||k.lane))||'無料';o.innerHTML='';return;}m.className='tag ok';m.textContent=k.lane||'OK';
var bars=k.bars.slice(-60);var lo=Math.min.apply(null,bars.map(function(b){return b[3];})),hi=Math.max.apply(null,bars.map(function(b){return b[2];}));var W=900,H=220,pad=30,w=(W-pad*2)/bars.length;function y(v){return pad+(H-pad*2)*(1-(v-lo)/((hi-lo)||1));}
var s='<svg class="k" viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none">';[0,.5,1].forEach(function(f){var v=lo+(hi-lo)*f;s+='<line x1="'+pad+'" x2="'+(W-pad)+'" y1="'+y(v)+'" y2="'+y(v)+'" stroke="#dcdfe6" stroke-width="1"/><text x="'+(pad-4)+'" y="'+(y(v)+3)+'" font-size="9" text-anchor="end" fill="#6d7688">'+n(v,0)+'</text>';});
bars.forEach(function(b,i){var x=pad+i*w+w/2,up=b[4]>=b[1],c=up?'#3e6b8f':'#b05c4d';s+='<line x1="'+x+'" x2="'+x+'" y1="'+y(b[2])+'" y2="'+y(b[3])+'" stroke="'+c+'" stroke-width="1"/><rect x="'+(x-w*.3)+'" y="'+Math.min(y(b[1]),y(b[4]))+'" width="'+(w*.6)+'" height="'+Math.max(1,Math.abs(y(b[1])-y(b[4])))+'" fill="'+(up?'#fff':c)+'" stroke="'+c+'" stroke-width="1"><title>'+esc(b[0])+' O '+n(b[1],1)+' H '+n(b[2],1)+' L '+n(b[3],1)+' C '+n(b[4],1)+' · 律量 '+(b[5]==null?'缺值(NaN)':n(b[5]))+' · 原始量 '+n(b[7])+' · '+esc(b[8])+'</title></rect>';});
s+='</svg>';var rows=k.bars.slice(-10).reverse().map(function(b){return tr(td(esc(b[0])),td(n(b[1],1),'r'),td(n(b[2],1),'r'),td(n(b[3],1),'r'),td(n(b[4],1),'r'),td(b[5]==null?'<span class="tag warn">缺值</span>':n(b[5]),'r'),td(n(b[7]),'r'),td(esc(b[8])));});
o.innerHTML='<div class="note">'+esc(k.code)+' '+esc(k.name)+' · 近 '+bars.length+' 根(還原價;藍=收≥開 紅=收<開;滑過蠟燭看 OHLCV+律量)</div>'+s+tbl(['日期','>開','>高','>低','>收','>律量(扣當沖)','>原始量','量源'],rows);}).catch(function(e){m.className='tag bad';m.textContent='樞紐錯誤 '+e;});}
/* ---------- 03 主動台股 ETF ---------- */
function vEtf(d){if(!d||d.state!=='OK')return bad(d,'主動台股 ETF');var b=d.book||{},c=d.classification||{},k=d.consensus||{};var h='';
h+='<div class="stats">'+stat(n(b.n_book),'主動 ETF 冊','ETF BOOK')+stat(n(b.n_holdable),'可查持股','HOLDINGS')+stat(c.state==='OK'?n(c.n_etfs):'—','已產業歸類','CLASSIFIED')+stat(c.state==='OK'?n(c.n_sectors):'—','產業數','SECTORS')+stat(k.state==='OK'?esc(k.asof):'—','共識截至','CONSENSUS ASOF')+stat(k.state==='OK'?n(k.consensus_codes):'—','共識覆蓋代號','COVERED')+'</div>';
if(c.state==='OK'){var mx=Math.max.apply(null,c.sectors.map(function(s){return s.avg_w;}).concat([1]));var sr=c.sectors.map(function(s){return tr(td(esc(s.sector)),td(meter(s.avg_w,mx,2,'%')),td(n(s.n_etfs),'r'),td(n(s.n_codes),'r'));});
h+=card('sec','產業分類(全 ETF 平均權重)','SECTOR CLASSIFICATION · '+esc(c.lane),'每 ETF 最新 portfolio_date 持股 × 名冊產業;平均權重=Σ權重/ETF 數。',tbl(['產業 SECTOR','平均權重','>持有 ETF 數','>成分代號數'],sr),'etf');
var pr=c.per_etf.map(function(p){return tr(td('<code>'+esc(p.etf)+'</code>'),td(esc(p.name)),td(esc(p.date)),td(n(p.n),'r'),td(n(p.w_sum,1)+'%','r'),td('<b>'+esc(p.top_sector)+'</b>'),td('<div class="chips">'+p.sectors.map(function(s){return '<span>'+esc(s[0])+' '+n(s[1],1)+'%</span>';}).join('')+'</div>'),td(p.top.map(function(t){return esc(t[0])+' '+esc(t[1])+' '+n(t[2],1)+'%';}).join('<br>')));});
h+=card('per','逐 ETF 分類','PER ETF · '+n(c.n_etfs),'',tbl(['ETF','名稱','持股日','>檔數','>權重和','主產業','產業分布(前 6)','前五持股'],pr));
if(c.changes&&c.changes.length)h+=card('chg','最新持股變動','HOLDINGS CHANGES · '+esc(c.changes[0].date),'',tbl(['類型','>筆數'],c.changes.map(function(x){return tr(td(esc(x.type)),td(n(x.n),'r'));})));}else h+=bad(c,'產業分類');
if(k.state==='OK'){var kr=k.etfs.map(function(e){return tr(td('<code>'+esc(e.etf)+'</code>'),td(esc(e.name)),td(n(e.n),'r'),td(n(e.n_cov)+' ('+pct(e.cov_w_pct,1)+')','r'),td(dmeter(e.wtd_upside,60,1)));});
h+=card('cons','ETF×共識加權 upside','CONSENSUS · ENG068 · '+esc(k.file),'加權 upside=Σ(權重×(目標價/現價−1))/覆蓋權重;覆蓋=有 FactSet 共識之成分。',tbl(['ETF','名稱','>持股','>覆蓋(權重%)','加權 upside'],kr));
var orr=k.overlap.map(function(o){return tr(td('<code>'+esc(o.code)+'</code>'),td(esc(o.name)),td(n(o.etfs),'r'),td(n(o.w_sum,1)+'%','r'),td(n(o.tp,0),'r'),td(dmeter(o.upside,80,1)),td(n(o.n_analysts),'r'));});
h+=card('ov','重疊持股 × 共識','OVERLAP TOP 20','',tbl(['代號','名稱','>持有 ETF','>權重和','>目標價','upside','>分析師'],orr));}else h+=bad(k,'ETF×共識');
return h+deep(d.pages);}
/* ---------- 04 族群分類×輪動 ---------- */
function vRot(d){if(!d||d.state!=='OK')return bad(d,'族群分類×輪動');var g=d.group||{},s=d.story||{},r=d.rotation||{},b=d.backtest||{},p=d.gap||{};var h='';var ro=g.roles||{};
h+='<div class="stats">'+stat(g.state==='OK'?n((g.meta||{}).n_groups):'—','產業族群','GROUPS')+stat(g.state==='OK'?n(ro.LEADER)+'/'+n(ro.PEER)+'/'+n(ro.LAGGER):'—','LEAD/PEER/LAG','ROLES')+stat(s.state==='OK'?n(s.n_sig)+'/'+n(s.n):'—','故事族群顯著/總','STORIES SIG')+stat(r.state==='OK'?n(r.n_edges)+'/'+n(r.n_pairs_tested):'—','輪動顯著邊/測試對','ROTATION')+stat(b.state==='OK'?n(b.n_backtested)+'/'+n(b.n_groups):'—','回測族群','BACKTEST')+stat(p.state==='OK'?esc(p.run_state):'—','v0.5 橋接','GAP')+'</div>';
if(g.state==='OK'){var mx=Math.max.apply(null,g.top_att.map(function(x){return x.idx_att;}).concat([1]));h+=card('gc','族群指數(等權/分層/歸因)','GROUP INDEX · ENG070 · '+esc(g.file),'尾日 '+esc((g.meta||{}).last)+' · 截去不完整日 '+n(((g.meta||{}).dropped_partial||[]).length)+' · 角色 '+Object.keys(ro).map(function(k){return k+' '+n(ro[k]);}).join(' · ')+' · 規模 '+Object.keys(g.sizes||{}).map(function(k){return k+' '+n(g.sizes[k]);}).join(' · '),tbl(['產業','>成員','>等權','>分層','歸因指數'],g.top_att.map(function(x){return tr(td(esc(x.industry)),td(n(x.n),'r'),td(n(x.idx_eq,1),'r'),td(n(x.idx_tier,1),'r'),td(meter(x.idx_att,mx,1)));})),'rotation');}else h+=bad(g,'族群指數');
if(s.state==='OK'){h+=card('st','故事族群分類','STORY CLASSIFICATION · '+esc(s.file),'p 虛無=隨機群+循環移位 IU;q=BH FDR≤0.10;角色 '+Object.keys(s.roles||{}).map(function(k){return k+' '+n(s.roles[k]);}).join(' · '),tbl(['故事','>層','母','>註冊/現役','>PC1','>p IU','>q FDR','顯著','領頭'],s.stories.map(function(x){return tr(td(esc(x.story)),td(n(x.level),'r'),td(esc(x.parent||'')),td(n(x.n)+'/'+n(x.n_act),'r'),td(x.pc1==null?'—':n(x.pc1,2),'r'),td(x.p_iu==null?'—':n(x.p_iu,3),'r'),td(x.q_fdr==null?'—':n(x.q_fdr,3),'r'),td(x.cohesion_sig?'<span class="tag ok">SIG</span>':'<span class="tag mut">—</span>'),td((x.leaders||[]).join(' ')));})));}else h+=bad(s,'故事族群');
if(r.state==='OK'){h+=card('ro','輪動關聯(領先→落後)','ROTATION · FFT lag 1~5 · '+esc(r.file),n(r.n_days)+' 日自 '+esc(r.start)+' · 測試 '+n(r.n_pairs_tested)+' 對 · 顯著邊 '+n(r.n_edges)+'(BH;0=誠實無顯著輪動,組成型負相關)。',tbl(['自','→ 至','>lag','r','>p','重疊'],r.pairs.map(function(x){return tr(td(esc(x.from)),td(esc(x.to)),td(n(x.lag),'r'),td(dmeter(x.r*100,30,1)),td(n(x.p,3),'r'),td(x.overlap?'<span class="tag warn">重疊排除</span>':''));})));}else h+=bad(r,'輪動關聯');
if(b.state==='OK'){h+=card('bt','族群回測(S1 歸因策略 vs 等權)','BACKTEST · '+esc(b.engine)+' · '+esc(b.classifier),'rf '+n((b.risk_free||{}).rf*100,2)+'% ('+esc((b.risk_free||{}).flag)+') · '+esc(b.ts),tbl(['族群','>S1 成員','>天','總報酬','>CAGR','>Sharpe','>MaxDD','>超額','>等權基準','旗標'],b.results.map(function(x){return tr(td(esc(x.group)),td(n(x.n_s1),'r'),td(n(x.n_days),'r'),td(dmeter(x.ret==null?null:x.ret*100,80,1)),td(pct(x.cagr==null?null:x.cagr*100,1),'r'),td(x.sharpe==null?'—':n(x.sharpe,2),'r'),td(pct(x.maxdd==null?null:x.maxdd*100,1),'r'),td(pct(x.excess==null?null:x.excess*100,1),'r'),td(pct(x.bench_ret==null?null:x.bench_ret*100,1),'r'),td(x.flag?'<span class="tag warn">'+esc(x.flag)+'</span>':''));})));}else h+=bad(b,'族群回測');
if(p.state==='OK'){h+=card('gap','故事輪動 v0.5 橋接缺口冊','GAP BOOK · ENG072 · '+esc(p.file),tag(p.run_state)+' '+esc(p.ts)+' · '+esc(p.package)+'<br>'+(p.attribution||[]).map(function(a){return '· '+esc(a);}).join('<br>'),tbl(['ID','欄位','缺口','補源'],(p.gap_book||[]).map(function(x){return tr(td('<code>'+esc(x.id)+'</code>'),td(esc(x.field)),td(esc(x.gap)),td(esc(x.fix)));})));}else h+=bad(p,'缺口冊');
return h+deep(d.pages);}
/* ---------- 05 月營收 ---------- */
function vRev(d){if(!d||d.state!=='OK')return bad(d,'月營收');var k=d.consensus||{},q=k.quad||{};var h='';
h+='<div class="stats">'+stat(esc(d.latest_ym),'尾月','LATEST YM')+stat(n(d.n_codes),'公司數','COMPANIES')+stat(n(d.n_months),'月數','MONTHS')+stat(k.state==='OK'?n(k.n_covered)+'/'+n(k.n_market):'—','共識覆蓋/全市場','COVERED')+stat(k.state==='OK'?n(q.strong):'—','雙強(營收+共識)','STRONG')+'</div>';
var mx=Math.max.apply(null,d.sectors.map(function(s){return s.revenue;}).concat([1]));
h+=card('sec','產業月營收彙總','SECTORS · '+esc(d.latest_ym)+' · YoY=同月合計比','營收單位=千元(MOPS);YoY 以 ym−100 同月合計(缺=—)。',tbl(['產業','>家數','營收合計(百萬)','YoY'],d.sectors.map(function(s){return tr(td(esc(s.industry)),td(n(s.n),'r'),td(meter(s.revenue/1000,mx/1000,0)),td(dmeter(s.yoy,100,1)));})),'revenue');
h+=card('top','YoY 榜(營收>1 億)','TOP YOY · monthly_revenue_analysis',esc(d.lane),tbl(['代號','名稱','產業','>營收(百萬)','MoM','YoY','>連續','60月新高'],d.top_yoy.map(function(x){return tr(td('<code>'+esc(x.code)+'</code>'),td(esc(x.name)),td(esc(x.industry)),td(n(x.revenue/1000,0),'r'),td(dmeter(x.mom,100,1)),td(dmeter(x.yoy,200,1)),td(n(x.streak),'r'),td(x.high_60m?'<span class="tag ok">新高</span>':''));})));
if(k.state==='OK'){h+=card('quad','月營收×共識四象限','QUADRANT · ENG069 · '+esc(k.file),'strong=營收強+共識 upside 強;rev_only=僅營收;cons_only=僅共識;weak=皆弱。','<div class="stats">'+stat(n(q.strong),'雙強','STRONG')+stat(n(q.rev_only),'僅營收','REV ONLY')+stat(n(q.cons_only),'僅共識','CONS ONLY')+stat(n(q.weak),'皆弱','WEAK')+'</div>'+tbl(['代號','>營收(百萬)','MoM','YoY','>連續','>目標價','upside','>分析師','來源'],k.dual.map(function(x){return tr(td('<code>'+esc(x.code)+'</code>'),td(n(x.revenue/1000,0),'r'),td(dmeter(x.mom*100,100,1)),td(dmeter(x.yoy*100,200,1)),td(n(x.streak),'r'),td(n(x.tp,0),'r'),td(dmeter(x.upside,150,1)),td(n(x.n_analysts),'r'),td(esc(x.source)));})));}else h+=bad(k,'月營收×共識');
return h+deep(d.pages);}
/* ---------- 06 完工自動化(批335) ---------- */
function vComp(d){if(!d||d.state!=='OK')return bad(d,'完工自動化');var h='';var lr=d.last_run||null;
h+='<div class="stats">'+stat(pct(d.overall,1),'總完成度(實證均值)','OVERALL')+stat(n(d.n_done)+'/'+n((d.items||[]).length),'已完成項','DONE')+stat(n(d.n_auto),'可自動化項','AUTO')+stat(n((d.gates||[]).length),'閘(零自動解除)','GATES')+stat(n(d.n_steps),'完工鏈步數','CHAIN STEPS')+stat(lr?esc(lr.state)+' '+n(lr.n_ok)+'/'+n(lr.n_fail)+'/'+n(lr.n_skip):'—','最近完工 OK/FAIL/SKIP','LAST RUN')+'</div>';
var auto=[];(d.items||[]).forEach(function(x){(x.auto||[]).forEach(function(t){if(auto.indexOf(t)<0)auto.push(t);});});
var order=(d.plan||[]).map(function(p){return p.id;});auto.sort(function(a,b){return order.indexOf(a)-order.indexOf(b);});
var ok=canRun();
h+='<div class="card"><h3>一鍵完工<small>ONE-BUTTON COMPLETION</small></h3><div class="note">'+(ok?'⟳ 完工鏈=樞紐任務 complete_all(伺服端依序 16 步、逐步 rc 存證、閘零觸碰;NET 步帶同意閘;進度看運轉矩陣)。▶ 自動鏈=前端依序只跑未完項的自動靶。':'file:// 或樞紐離線=唯讀;由樞紐 '+esc(B)+'/system#completion 開啟即可執行。')+'</div><div class="acts">'
+'<button class="b pri" onclick="chain([\'complete_all\'],\'一鍵完工鏈(16 步)\')"'+(ok?'':' disabled')+'>⟳ 一鍵完工鏈 complete_all</button>'
+'<button class="b" onclick="chain('+JSON.stringify(auto.concat(['system_ui'])).replace(/"/g,'&quot;')+',\'未完項自動靶鏈\')"'+(ok||!auto.length?'':' disabled')+(auto.length?'':' disabled')+'>▶ 未完項自動靶鏈('+auto.length+' 靶)</button>'
+'<button class="b" onclick="refetch(\'completion\')">↻ 重取未完工作冊</button></div></div>';
var mx=100;h+=card('items','未完工作冊','UNFINISHED LEDGER · MDL096 實證直取','狀態:DONE=100%;AUTO=有自動靶;ENFORCED_SKIP/PENDING_OPERATOR/AWAITING_OPERATOR=閘(零自動解除);MANUAL=無靶。',tbl(['狀態','子系統','完成度','現況','自動靶 / 閘','接續方法'],(d.items||[]).map(function(x){var st=x.state;var tg=st==='DONE'?'ok':(st==='AUTO'?'warn':(st==='MANUAL'?'mut':'bad'));return tr(td('<span class="tag '+tg+'">'+esc(st)+'</span>','nw'),td(esc(x.sub)),td(meter(x.pct,mx,1,'%')),td(esc(x.now)),td((x.auto||[]).length?(x.auto||[]).map(function(t){return '<button class="b mxb" onclick="chain([\''+t+'\'],\''+esc((TASKS[t]||{}).zh||t)+'\')"'+(ok?'':' disabled')+'>▶ '+esc(t)+'</button>';}).join(' '):(x.gate?'<span class="tag bad">'+esc(x.gate)+'</span>':'—')),td(esc(x.next)));})));
h+=card('gates','閘冊(零自動解除)','GATES · OPERATOR ONLY','本自動化對閘零觸碰;解除僅憑操作員明令。',tbl(['閘','狀態','標的','說明'],(d.gates||[]).map(function(g){return tr(td('<code>'+esc(g.id)+'</code>'),td('<span class="tag bad">'+esc(g.state)+'</span>','nw'),td(esc(g.sub)),td(esc(g.why)));})));
h+=card('plan','完工鏈計畫','COMPLETION CHAIN · '+n(d.n_steps)+' STEPS · 依賴序','',tbl(['>#','步驟','名稱','完成何項','通路','>逾時','在冊','引擎'],(d.plan||[]).map(function(p){return tr(td(n(p.no),'r'),td('<code>'+esc(p.id)+'</code>'),td(esc(p.zh)),td(esc(p.why)),td(p.net?'<span class="tag warn">NET</span>':'<span class="tag">本機</span>'),td(n(p.timeout)+'s','r'),td(p.in_registry?'<span class="tag ok">是</span>':'<span class="tag bad">否</span>'),td(p.engine_ok?'<span class="tag ok">在位</span>':'<span class="tag bad">缺</span>'));})));
if(lr)h+=card('last','最近完工實錄','LAST RUN · '+esc(lr.file||'')+' · '+esc(lr.ts||''),tag(lr.state)+' OK '+n(lr.n_ok)+' · FAIL '+n(lr.n_fail)+' · SKIP '+n(lr.n_skip)+' · '+n(lr.sec)+'s'+(lr.only&&lr.only.length?' · 子集 '+esc(lr.only.join(',')):'')+(lr.skip_net?' · 離線試跑':''),tbl(['>#','步驟','狀態','>rc','>秒','註 / 尾行'],(lr.steps||[]).map(function(s){return tr(td(n(s.no),'r'),td('<code>'+esc(s.id)+'</code>'),td('<span class="tag '+(s.state==='OK'?'ok':(s.state==='FAIL'?'bad':'mut'))+'">'+esc(s.state)+'</span>','nw'),td(s.rc==null?'—':n(s.rc),'r'),td(n(s.sec,1),'r'),td(esc(s.note||'')+(s.tail?'<br><code>'+esc(String(s.tail).split('\n').slice(-1)[0]).slice(0,140)+'</code>':'')));})));
else h+=card('last','最近完工實錄','LAST RUN','尚無完工實錄(誠實空;按一鍵完工或工作站 via-complete run)','');
return h+deep(d.pages);}
var VIEWS={home:vHome,vdf:vVdf,vap:vVap,etf:vEtf,rotation:vRot,revenue:vRev,completion:vComp};
function render(){var main=document.getElementById('views');var subs=(D&&D.subjects)||(SNAP&&SNAP.subjects)||[];subs.forEach(function(s){var el=document.getElementById('v-'+s.id);if(!el)return;var fn=VIEWS[s.id];el.innerHTML=actionsCard(s.id)+(fn?fn(D?D[s.id]:null):'');});drawMatrix();xgate();
var st=document.getElementById('st');st.textContent=SRC;st.className='v '+(SRC==='LIVE'?'ok':(SRC==='SNAPSHOT'?'warn':'bad'));var st2=document.getElementById('st2');st2.textContent=SRC;st2.className='v '+st.className.replace('v ','');
document.getElementById('ts').textContent=D?(D.ts||''):'—';document.getElementById('rows').textContent=D&&D.home&&D.home.totals?n(D.home.totals.rows):'—';
var bn=document.getElementById('banner');if(SRC==='LIVE'){bn.className='banner';bn.textContent='';}else if(SRC==='SNAPSHOT'){bn.className='banner on warn';bn.innerHTML='⚠ 樞紐 '+esc(B)+' 未連線(誠實):顯示產頁時內嵌快照 '+esc(D.ts)+'。於倉庫根打 <b>via</b> 帶起樞紐後 <a href="'+esc(B)+'/system">由樞紐同源開啟</a>(同源安全律:file:// 頁唯讀預覽;批333)。';}else{bn.className='banner on bad';bn.textContent='✖ 樞紐離線且快照缺=誠實空(先 via-system 再生本頁)。';}}
function show(id){CUR=id;document.querySelectorAll('.view').forEach(function(v){v.className='view'+(v.id==='v-'+id?' on':'');});document.querySelectorAll('.nav a[data-v]').forEach(function(a){a.className=a.getAttribute('data-v')===id?'active':'';});var s=((D&&D.subjects)||(SNAP&&SNAP.subjects)||[]).filter(function(x){return x.id===id;})[0]||EXTRA[id];if(s){document.getElementById('hzh').textContent=s.zh;document.getElementById('hen').textContent=s.en;document.getElementById('hsub').textContent=s.sub;document.getElementById('crumbcur').textContent=s.zh;}if(location.hash!=='#'+id)history.replaceState(null,'','#'+id);window.scrollTo(0,0);}
function refetch(id){if(SRC!=='LIVE'){boot();return;}fetch(B+'/api/'+id).then(function(r){return r.json();}).then(function(j){D[id]=j;D.ts=new Date().toISOString().slice(0,19).replace('T',' ');render();show(CUR);}).catch(function(){});}
function sameOriginFirst(){if(location.protocol!=='file:')return Promise.resolve(false);var c=new AbortController();var t=setTimeout(function(){c.abort();},1400);return fetch(B+'/probe',{mode:'no-cors',cache:'no-store',signal:c.signal}).then(function(){clearTimeout(t);location.replace(B+'/system'+(location.hash||'#home'));return true;}).catch(function(){clearTimeout(t);return false;});}
function boot(){if(location.protocol==='file:'){sameOriginFirst().then(function(moved){if(!moved){if(SNAP){D=SNAP;SRC='SNAPSHOT';}else{D=null;SRC='OFFLINE';}render();show(CUR);}});return;}var ctl=new AbortController();var t=setTimeout(function(){ctl.abort();},8000);
fetch(B+'/api/all',{signal:ctl.signal}).then(function(r){return r.json();}).then(function(j){clearTimeout(t);if(!j||!j.subjects)throw new Error('bad');D=j;SRC='LIVE';render();show(CUR);}).catch(function(){clearTimeout(t);if(SNAP){D=SNAP;SRC='SNAPSHOT';}else{D=null;SRC='OFFLINE';}render();show(CUR);});}
document.addEventListener('DOMContentLoaded',function(){var id=(location.hash||'#home').slice(1);if(!VIEWS[id]&&!EXTRA[id])id='home';CUR=id;xinit();if(SNAP){D=SNAP;SRC='SNAPSHOT';render();}show(id);boot();if(SAME){poll();setInterval(poll,4000);}window.addEventListener('hashchange',function(){var i=(location.hash||'#home').slice(1);if(VIEWS[i]||EXTRA[i])show(i);});});
"""


def _sys_of(argv) -> str:
    s = " ".join(str(a) for a in argv).replace("\\", "/")
    if "/VDF/" in s or "VDF_" in s:
        return "VDF"
    if "/VRN/" in s or "VRN_" in s:
        return "VRN"
    if "/VAP/" in s or "VAP_" in s:
        return "VAP"
    return "CGC"


def tasks_catalog() -> dict:
    """DeckServer 尾版任務冊→頁內嵌(契約旗標 codes/range/cats+net+系統歸屬;缺=誠實空)"""
    try:
        p = sorted(HERE.glob("CGC_MDL095_DeckServer_v0*.py"))[-1]
        spec = importlib.util.spec_from_file_location("deck_for_ui", p)
        m = importlib.util.module_from_spec(spec)
        sys.modules["deck_for_ui"] = m
        spec.loader.exec_module(m)
        T = m.task_registry()
    except Exception:
        return {}
    return {k: {"zh": v.get("zh", k), "net": bool(v.get("net")), "codes": bool(v.get("codes")),
                "range": bool(v.get("range")), "cats": bool(v.get("cats")),
                "sys": _sys_of(v.get("argv", []))} for k, v in T.items()}


def build(snapshot: dict, subjects: list) -> str:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M")
    tasks = tasks_catalog()
    tasks_json = json.dumps(tasks, ensure_ascii=False).replace("</", "<\\/")
    nav = []
    for i, s in enumerate(subjects):
        nav.append(f'<a data-v="{s["id"]}" href="#{s["id"]}" onclick="show(\'{s["id"]}\')"><span class="no">{i:02d}</span>'
                   f'<span class="lb">{html.escape(s["zh"])}<small>{html.escape(s["en"])}</small></span></a>')
    nav.append('<a data-v="matrix" href="#matrix" onclick="show(\'matrix\')"><span class="no">07</span>'
               '<span class="lb">運轉矩陣<small>WELL-ORGANIZED MATRIX</small></span></a>')
    views = "".join(f'<section class="view" id="v-{s["id"]}"></section>' for s in subjects) + '<section class="view" id="v-matrix"></section>'
    shells = [("總控台 MasterControl", "VIA_UI_MasterControl_v0100.html"),
              ("中央治理主控台", "VIA_UI_GovernanceConsole_v0100.html"),
              ("CGC 現況台(統一殼)", "VIA_UI_Shell_CGC_v0100.html"),
              ("VDF 現況台", "VIA_UI_Shell_VDF_v0100.html"),
              ("VRN 現況台", "VIA_UI_Shell_VRN_v0100.html"),
              ("VAP 現況台", "VIA_UI_Shell_VAP_v0100.html"),
              ("總控台 MasterControl(樞紐同源 /master)", BRIDGE + "/master"),
              ("指令甲板(樞紐 /deck)", BRIDGE + "/deck")]
    sh = "".join(f'<a href="{html.escape(h)}"><span class="no">{j:02d}</span><span class="lb">{html.escape(z)}</span></a>'
                 for j, (z, h) in enumerate(shells, 1))
    snap = json.dumps(snapshot, ensure_ascii=False, default=str).replace("</", "<\\/")
    tot = snapshot.get("home", {}).get("totals", {})
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
<title>VIA · 系統總台 System</title><style>{CSS}</style></head><body>
<aside class="rail">
<div class="brand"><span class="seal">統</span>
<div class="latin">VERITAS INTELLIGENCE ANALYTICS</div>
<h1>系統總台</h1>
<div class="en">STANDARD SYSTEM UI · 7 SUBJECTS</div>
<span class="badge">{BUILD} · API {html.escape(snapshot.get("api", ""))}</span></div>
<details class="inp" id="inp" open><summary>執行輸入 INPUT · <span id="inpstate">—</span></summary>
<label>工作 TASK({len(tasks)} 白名單)</label><select id="xt" onchange="xparams()"></select>
<div id="xf-codes" hidden><label>股票代號 CODES(逗號分隔,最多 50)</label><input id="xcodes" placeholder="2330,2317"></div>
<div id="xf-range" hidden><label>起 START</label><input id="xstart" placeholder="YYYY-MM-DD"><label>迄 END</label><input id="xend" placeholder="YYYY-MM-DD"></div>
<div id="xf-cats" hidden><label>類別 CATS</label><input id="xcats" placeholder="idx,etf,fx"></div>
<div class="row"><button class="b pri" id="xrun" onclick="xrun()" disabled>▶ 執行</button><button class="b" onclick="xping()">檢測</button></div>
<div class="xlog" id="xlog">待命。同源 CSRF POST;file:// 頁唯讀。</div></details>
<div class="navsec">主體 SUBJECTS</div><div class="nav">{"".join(nav)}</div>
<div class="navsec">系統殼 SHELLS</div><div class="nav">{sh}</div>
<div class="railfoot">
<div><div class="k">SOURCE</div><div class="v" id="st">—</div></div>
<div><div class="k">ROWS</div><div class="v" id="rows">{tot.get("rows", "—")}</div></div>
<div><div class="k">RUNNING</div><div class="v" id="runn">—</div></div>
<div><div class="k">DATA TS</div><div class="v" id="ts">{html.escape(snapshot.get("ts", ""))}</div></div>
</div></aside>
<main class="main">
<div class="crumb"><b>VIA 母系統</b> → <b>系統總台</b> → <b id="crumbcur">首頁</b> · <span class="lock">LAYOUT SPEC(批302)· 前後端相連(批332)</span></div>
<div class="head"><h2><span id="hzh">VIA 首頁</span><small id="hen">ALL FETCHED DATA</small></h2>
<div class="spec">
<div><div class="k">BUILD</div><div class="v">{BUILD}</div></div>
<div><div class="k">SOURCE</div><div class="v" id="st2">—</div></div>
<div><div class="k">BRIDGE</div><div class="v ok">127.0.0.1:8765</div></div>
<div><div class="k">GATE</div><div class="v ok">HONEST 3-STATE</div></div>
</div><div class="sub" id="hsub"></div></div>
<div class="banner" id="banner"></div>
<div id="views">{views}</div>
<div class="foot">VIA · 系統總台 · 六主體(VIA 首頁=所有擷取資料 / VDF / VAP / 主動台股 ETF 分類 / 族群分類×輪動 / 月營收)
· 後端=MDL095 樞紐 /api/* → MDL119 聚合層(唯讀短連線;誠實三態)· 前端=本頁(LIVE/SNAPSHOT/OFFLINE 三態)
· 輸入介面/運轉矩陣/功能鍵自動鏈=同源 CSRF POST(批334)· 快照產於 {html.escape(snapshot.get("ts", ""))} · 頁產於 {ts} · 零 CDN 零外網</div>
</main>
<script id="snap" type="application/json">{snap}</script>
<script id="tasks" type="application/json">{tasks_json}</script>
<script>{JS.replace("__BRIDGE__", BRIDGE)}</script>
</body></html>"""


def run(open_after: bool = False, do_print: bool = True) -> int:
    api = _api()
    snap = api.all_subjects()
    subjects = snap.get("subjects", [])
    UI.mkdir(parents=True, exist_ok=True)
    OUT.write_text(build(snap, subjects), encoding="utf-8")
    if do_print:
        st = " ".join(f"{k}={snap.get(k, {}).get('state')}" for k, _, _, _ in api.SUBJECTS)
        print(f"[系統總台] {OUT.name} 產出 · 快照 {snap.get('ts')} · {st} · "
              f"{round(OUT.stat().st_size / 1024, 1)} KB")
    if open_after:
        import webbrowser
        webbrowser.open(OUT.as_uri())
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run(do_print=False)
    page = OUT.read_text(encoding="utf-8")
    api = _api()
    subs = [s[0] for s in api.SUBJECTS]
    chk("① 頁產出(rc0+頁名穩定律 VIA_UI_System_v0100.html)", rc == 0 and OUT.exists())
    chk("② 六主體導航+六視圖容器(MDL119 SUBJECTS 單一 SSOT)",
        all(f'data-v="{s}"' in page and f'id="v-{s}"' in page for s in subs) and len(subs) == 7)
    import re
    m = re.search(r'<script id="snap" type="application/json">(.*?)</script>', page, re.S)
    snap = json.loads(m.group(1).replace("<\\/", "</")) if m else {}
    chk("③ 內嵌快照可解析+六主體三態+首頁=所有擷取資料(庫表/車道/存證)",
        bool(snap) and all(k in snap for k in subs)
        and snap["home"].get("totals", {}).get("tables", 0) >= 10
        and len(snap["home"].get("lanes", [])) >= 14 and len(snap["home"].get("evidence", [])) >= 8,
        f"(state={snap.get('state')} · 表 {snap.get('home', {}).get('totals', {}).get('tables')})")
    chk("④ 前後端相連三態(LIVE fetch /api/all+SNAPSHOT 退位+OFFLINE 誠實)",
        f"var B='{BRIDGE}'" in page and "fetch(B+'/api/all'" in page and "SRC='SNAPSHOT'" in page
        and "SRC='OFFLINE'" in page and "fetch(B+'/api/'+id)" in page)
    chk("⑤ 版型五律(左欄導航+麵包屑+規格帶+統計卡+內容卡)+響應雙態",
        all(k in page for k in ('class="rail"', 'class="crumb"', 'class="spec"', 'class="stats"', "class=\"card\""))
        and "@media(max-width:860px)" in page)
    deep_pages = [h for k in subs for _, h in snap.get(k, {}).get("pages", []) if not h.startswith("http")]
    missing = [h for h in deep_pages if not (UI / h).exists()]
    chk("⑥ 深頁真連結(六主體 pages 尾版檔全在位)", deep_pages and not missing,
        f"({len(deep_pages)} 連結" + (f";缺 {missing}" if missing else "") + ")")
    chk("⑦ 零 CDN 零外網+加速橋+誠實宣告",
        'src="http' not in page and "@import" not in page and "ACCEL-BRIDGE" in src and "誠實" in page)
    chk("⑨ 同源安全律(file:// 先探同源 /system 導向;總控台 /master 連結;批333)",
        "sameOriginFirst" in page and "location.replace(B+'/system'" in page and BRIDGE + "/master" in page)
    chk("⑧ VAP K線快查=樞紐律量(價還原/量扣當沖;離線誠實拒)+圖形律(單色量尺/極性雙色)",
        "/vap_kline?code=" in page and "樞紐離線=無法查" in page and ".meter .bar.div i.neg" in page
        and "dmeter(" in page and "meter(" in page)
    tasks = tasks_catalog()
    chk("⑩ 輸入介面(工作下拉+契約參數+▶/檢測+紀錄;同源 CSRF POST;file:// 停用)",
        'id="xt"' in page and 'id="xf-codes"' in page and 'id="xrun"' in page
        and "X-VIA-CSRF" in page and "canRun()" in page and "file:// 唯讀預覽" in page)
    chk("⑪ 運轉矩陣視圖(四系統 × 任務;/status 4s;run_id 對應;解方;▶)+任務冊嵌入 ≥36",
        'id="v-matrix"' in page and "drawMatrix" in page and "setInterval(poll,4000)" in page
        and len(tasks) >= 36 and "system_ui" in tasks and "group_class" in tasks,
        f"(任務 {len(tasks)})")
    chk("⑬ 完工自動化視圖(未完工作冊/閘冊/完工鏈/一鍵完工 complete_all;批335)",
        'id="v-completion"' in page and "function vComp(" in page
        and "complete_all" in page and "零自動解除" in page and "UNFINISHED LEDGER" in page)
    chk("⑫ 功能鍵+自動鏈(六主體 ACTIONS;依序/任一失敗即停/完成重取)",
        "function chain(" in page and "任一失敗即停" in page and "refetchAll()" in page
        and all(f" {k}:[" in page for k in ("home", "vdf", "vap", "etf", "rotation", "revenue")))
    print(f"  [計] 十三檢 OK {13 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 標準系統 U/I 前端(CGC_MDL120 v0102)· 十三檢自測(零網路)===")
        return selftest()
    return run(open_after="--open" in sys.argv[1:])


if __name__ == "__main__":
    sys.exit(main())
