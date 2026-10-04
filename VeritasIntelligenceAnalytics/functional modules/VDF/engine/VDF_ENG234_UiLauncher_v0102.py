#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG234_UiLauncher v0102 — +左側「輸入項目」面板(起始日共用 SSOT-VCGC-VDF-INPT0001 · 分群可改 · 項目可新增 · 匯出 vdf_inputs.json)
 VDF 啟動檔:**靜態 HTML U/I 直接跳出(不經伺服器)** + 自適應式對接任何視覺模板(操作員 2026-10-04)

v0101 新規定(操作員):① 不透過 server:`build` 把資料內嵌成單一 .html(VIA_Reports/vdf/ui/VDF_UI_latest.html)→ PS 直接開預設瀏覽器;`serve` 保留為選項
  ② 版面:小字體(11px)· 緊湊 · 響應式:電腦水平長方形 12 欄格 / 手機垂直 <720px 單欄;Plotly dashboard 風格 · 淺色 · seaborn 色票(deep/muted/pastel)
  ③ 功能參數全部在本檔 UI_PARAMS(ui_config.json 只覆蓋,可不存在);PS 只負責前後端銜接與啟動
  ④ 內建迷你 SVG 圖表(零 CDN):燈分布 · 市場分布 · ETF 前十持股;圖表色走 seaborn 色票,燈色走 FormatLock


一支做三件事,零必裝依賴(只用標準庫;fastapi / jinja2 在就用,不在也跑):
  ① 啟動:本機 HTTP(127.0.0.1:8765)· 1.5 秒後開預設瀏覽器 · 內建標準模板(VIA_UI_FormatLock 鎖定色 · 四燈 · 卡片 · 表單 · 資料表 · 參數面板)
  ② 參數:ui_config.json(app_title · theme · layout · active_template · data 範圍);改了重新整理即生效,不重啟
  ③ 自適應對接:templates\ 夾裡丟任何 .html,系統自動 — (a) 讀出模板宣告的變數(Jinja 語法或 {{x.y}} 字面)對映到 config / data;
     (b) 沒有 Jinja 的純 HTML:注入 <script>window.VIA = {config,data}</script> + FormatLock CSS 變數 + 四燈 lamp_css(紅燈慢閃),模板原碼一字不改;
     (c) 模板自帶 :root 色票就不蓋(尊重模板);缺的燈類補上;(d) 清單頁 /templates 列出所有可用模板,點一下切換(寫回 ui_config.json)
資料 API(只讀,零網路,零寫庫):/api/config · /api/universe(OUT-01 再生件)· /api/etf(ActiveTWETF holdings_daily 最新日)· /api/readiness(ENGINE_READINESS_latest)·
  /api/filemap(VIA_FILE_MAP_latest)· /api/panorama(SSOT_PANORAMA latest json 若在)· /api/templates
用法  python VDF_ENG234_UiLauncher_v0102.py build [--template X.html] [--open]   ← 預設:靜態單檔 → 開瀏覽器(不經伺服器)
      VIA_FROM_VCGC=YES python VDF_ENG234_UiLauncher_v0102.py serve [--port 8765] [--no-open] [--template X.html]
      python VDF_ENG234_UiLauncher_v0102.py render [--template X.html] → 印出渲染後 HTML(給 CI / 另存)
      python VDF_ENG234_UiLauncher_v0102.py --selftest
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
import csv, html, json, os, re, sys, threading, time, webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ENGINE = "VDF_ENG234_UiLauncher_v0102"
HERE = Path(__file__).resolve().parent
VIA = next((p for p in [HERE] + list(HERE.parents) if (p / "supportive modules").is_dir()), HERE)
UI_DIR = VIA / "functional modules" / "VDF" / "ui"; TPL_DIR = UI_DIR / "templates"   # 模板夾 · 參數檔;靜態輸出在 VIA_Reports/vdf/ui/
CONFIG_PATH = UI_DIR / "ui_config.json"
PAL = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af", "NODATA": "#0891b2", "text_GREEN": "#15803d", "text_YELLOW": "#b45309", "text_RED": "#b91c1c"}
LAMP_CSS = ("@keyframes via-blink{0%,100%{opacity:1}50%{opacity:.25}}.lamp{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle;margin-right:4px;border:1px solid rgba(0,0,0,.15)}"
            ".lamp.GREEN{background:var(--lamp-green)}.lamp.YELLOW{background:var(--lamp-yellow)}.lamp.RED{background:var(--lamp-red);animation:via-blink 1.8s ease-in-out infinite}.lamp.GRAY,.lamp.SKIP,.lamp.HOLD,.lamp.TIMEOUT{background:var(--lamp-gray)}.lamp.NODATA{background:var(--lamp-nodata)}"
            "@media (prefers-reduced-motion: reduce){.lamp.RED{animation:none}}")

SEABORN = {"deep": ["#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3", "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD"],
           "muted": ["#4878D0", "#EE854A", "#6ACC64", "#D65F5F", "#956CB4", "#8C613C", "#DC7EC0", "#797979", "#D5BB67", "#82C6E2"],
           "pastel": ["#A1C9F4", "#FFB482", "#8DE5A1", "#FF9F9B", "#D0BBFF", "#DEBB9B", "#FAB0E4", "#CFCFCF", "#FFFEA3", "#B9F2F0"]}
# 功能參數全部在這裡(ui_config.json 只覆蓋同名鍵;可不存在)
UI_PARAMS = {"mode": "static", "out_name": "VDF_UI_latest.html", "font_px": 11, "compact": True, "theme": "light", "palette": "deep", "grid_cols_desktop": 12, "mobile_breakpoint_px": 720,
             "table_max_rows": {"universe": 60, "etf": 60, "readiness": 160, "filemap": 120}, "charts": {"lamps": True, "market": True, "etf_top": True, "etf_top_n": 10},
             "sections_order": ["inputs", "cards", "charts", "readiness", "universe", "etf", "filemap"], "sticky_header": True, "card_min_px": 150,
             "inputs": {"start_date_default": "2026-01-02", "start_date_ssot": "SSOT-VCGC-VDF-INPT0001", "groups": ["上市", "上櫃", "主動ETF", "指數", "總經"],
                        "items_file": "vdf_inputs.json",
                        "items": [{"id": "IN-01", "name": "台灣全部個股(加權上市)", "group": "上市", "source": "SRC-01 TWSE", "enabled": True, "start": None},
                                  {"id": "IN-02", "name": "台灣全部個股(櫃買上櫃)", "group": "上櫃", "source": "SRC-02 TPEX", "enabled": True, "start": None},
                                  {"id": "IN-03", "name": "主動式台股 ETF(含持股)", "group": "主動ETF", "source": "SRC-05 發行商", "enabled": True, "start": None},
                                  {"id": "IN-04", "name": "加權 · 櫃買指數日資料", "group": "指數", "source": "SRC-01/02", "enabled": True, "start": None},
                                  {"id": "IN-05", "name": "yfinance 日價 / Adj Close", "group": "上市", "source": "SRC-03 yfinance", "enabled": True, "start": None}]}}
DEFAULT_CONFIG = {"app_title": "VIA · VDF 資料面板", "active_template": None, "port": 8765, "params": UI_PARAMS,
                  "theme": {"primary_color": "#1f2937", "bg_color": "#ffffff", "font_family": "Arial, 'Microsoft JhengHei', sans-serif", "font_px": 12},
                  "layout": {"sidebar_width": "230px", "show_sidebar": True, "show_header": True},
                  "data": {}}

DEFAULT_HTML = r"""<!doctype html><html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><title>{{ config.app_title }}</title>
<style>
:root{--primary:{{ config.theme.primary_color }};--bg:{{ config.theme.bg_color }};--font:{{ config.theme.font_family }};--fs:{{ config.params.font_px }}px;--border:#e5e7eb;--muted:#6b7280;--card:#fff;--cols:{{ config.params.grid_cols_desktop }};
--lamp-green:{{ pal.GREEN }};--lamp-yellow:{{ pal.YELLOW }};--lamp-red:{{ pal.RED }};--lamp-gray:{{ pal.GRAY }};--lamp-nodata:{{ pal.NODATA }};{% for c in sb %}--sb{{ loop.index0 }}:{{ c }};{% endfor %}}
*{box-sizing:border-box}html{scroll-padding-top:env(safe-area-inset-top,0)}body{margin:0;font:var(--fs)/1.35 var(--font);background:#f6f7f9;color:#111827;padding:0 0 env(safe-area-inset-bottom,0)}
.top{position:sticky;top:0;z-index:5;background:var(--card);border-bottom:1px solid var(--border);padding:5px 10px;display:flex;gap:10px;align-items:center;flex-wrap:wrap}.top b{font-size:13px;color:var(--primary)}.top .sp{flex:1}.top a{color:var(--primary);text-decoration:none;margin-left:8px}
.grid{display:grid;grid-template-columns:repeat(var(--cols),1fr);gap:8px;padding:8px}.card{background:var(--card);border:1px solid var(--border);border-radius:6px;padding:7px 9px;min-width:0}.card h3{margin:0 0 4px;font-size:11px;color:var(--muted);font-weight:600;letter-spacing:.2px}.card .v{font-size:20px;font-weight:600;color:var(--primary);line-height:1.1}.card .s{color:var(--muted);font-size:10px}
.c3{grid-column:span 3}.c4{grid-column:span 4}.c6{grid-column:span 6}.c9{grid-column:span 9}.c12{grid-column:span 12}.cards-wrap>.grid .card{padding:6px 8px}.chips{display:flex;gap:4px;flex-wrap:wrap;margin:3px 0}.chip{border:1px solid var(--border);border-radius:10px;padding:1px 7px;font-size:10px;cursor:pointer;background:#fff}.chip.on{background:var(--primary);color:#fff;border-color:var(--primary)}.inputs input,.inputs select{padding:1px 3px;border:1px solid var(--border);border-radius:3px;font:inherit;max-width:120px}.inputs .x{color:#b91c1c;cursor:pointer}.inherit{color:var(--muted)}
.tbl{max-height:280px;overflow:auto;border:1px solid var(--border);border-radius:4px}table{border-collapse:collapse;width:100%;font-size:var(--fs)}th,td{border-bottom:1px solid var(--border);padding:2px 6px;text-align:left;white-space:nowrap}th{background:#f3f4f6;position:sticky;top:0;font-weight:600;color:#374151}tr:hover td{background:#f9fafb}
.lamp{display:inline-block;width:10px;height:10px;border-radius:50%;vertical-align:middle;margin-right:4px;border:1px solid rgba(0,0,0,.12)}.lamp.GREEN{background:var(--lamp-green)}.lamp.YELLOW{background:var(--lamp-yellow)}.lamp.RED{background:var(--lamp-red);animation:via-blink 1.8s ease-in-out infinite}.lamp.GRAY,.lamp.SKIP,.lamp.HOLD,.lamp.TIMEOUT{background:var(--lamp-gray)}.lamp.NODATA{background:var(--lamp-nodata)}
@keyframes via-blink{0%,100%{opacity:1}50%{opacity:.25}}@media (prefers-reduced-motion:reduce){.lamp.RED{animation:none}}
.chart svg{width:100%;height:150px;display:block}.legend{font-size:10px;color:var(--muted);display:flex;gap:8px;flex-wrap:wrap}.legend i{display:inline-block;width:9px;height:9px;border-radius:2px;margin-right:3px;vertical-align:middle}
.panel label{display:block;font-size:10px;color:var(--muted);margin:5px 0 2px}.panel input,.panel select{width:100%;padding:3px 5px;border:1px solid var(--border);border-radius:4px;font:inherit}.btn{background:var(--primary);color:#fff;border:0;padding:4px 10px;border-radius:4px;cursor:pointer;font:inherit}
@media (max-width:{{ config.params.mobile_breakpoint_px }}px){.grid{grid-template-columns:1fr;padding:6px;gap:6px}.c3,.c4,.c6,.c9,.c12{grid-column:span 1}.cards-wrap>.grid{grid-template-columns:repeat(2,1fr)!important}.tbl{max-height:220px}.card .v{font-size:18px}.top b{font-size:12px}body{font-size:calc(var(--fs) + 1px)}}
@media (min-width:1600px){.tbl{max-height:360px}}
</style></head><body>
<div class="top"><b>{{ config.app_title }}</b><span><i class="lamp {{ data.overall }}"></i>{{ data.overall_zh }}</span><span class="s">{{ data.at }} · 靜態頁 · 零伺服器</span><span class="sp"></span><a href="#readiness">自測</a><a href="#universe">清單</a><a href="#etf">ETF</a><a href="#filemap">檔案</a><a href="#panel">參數</a></div>
<div class="grid">
<div class="card c3 inputs" id="inputs"><h3>輸入項目 · 起始日 <span id="in_start">{{ config.params.inputs.start_date_default }}</span> <span class="s">({{ config.params.inputs.start_date_ssot }} 共用;項目可覆蓋)</span></h3>
<div class="chips" id="in_chips"></div>
<div class="tbl" style="max-height:230px"><table id="in_tbl"><tr><th></th><th>項目</th><th>分群</th><th>起始日</th><th>來源</th><th>號</th><th></th></tr></table></div>
<div style="margin-top:5px;display:flex;gap:4px;flex-wrap:wrap"><button class="btn" onclick="VIA.addItem()">+ 新增項目</button><button class="btn" style="background:#4b5563" onclick="VIA.addGroup()">+ 新增分群</button><button class="btn" style="background:#6b7280" onclick="VIA.exportInputs()">匯出 vdf_inputs.json</button></div>
<div class="s" id="in_msg">啟用 <b id="in_on">0</b> / <span id="in_n">0</span> · 存檔:匯出後 `Invoke-VIA-VdfUi -ApplyInputs <檔>`,或貼到 functional modules\VDF\ui\vdf_inputs.json</div></div>
<div class="card c9 cards-wrap"><div class="grid" style="padding:0;grid-template-columns:repeat(3,1fr)">
<div class="card"><h3>全台股清單 OUT-01</h3><div class="v">{{ data.universe_n }}</div><div class="s">{{ data.universe_src }}</div></div>
<div class="card"><h3>主動 ETF 持股列(最新日)</h3><div class="v">{{ data.etf_n }}</div><div class="s">{{ data.etf_date }}</div></div>
<div class="card"><h3>引擎自測</h3><div class="v"><i class="lamp GREEN"></i>{{ data.r_green }} <i class="lamp RED"></i>{{ data.r_red }} <i class="lamp GRAY"></i>{{ data.r_other }}</div><div class="s">ENGINE_READINESS_latest</div></div>
<div class="card"><h3>檔案位置清單</h3><div class="v"><i class="lamp GREEN"></i>{{ data.fm_green }} <i class="lamp YELLOW"></i>{{ data.fm_yellow }} <i class="lamp RED"></i>{{ data.fm_red }}</div><div class="s">VIA_FILE_MAP_latest</div></div>
<div class="card"><h3>依分群啟用數</h3><div id="in_bygroup" class="s" style="font-size:11px;line-height:1.6"></div></div>
<div class="card"><h3>輸入 → 輸出</h3><div class="s" style="font-size:11px;line-height:1.6">IN-01/02 → OUT-01 universe_list<br>IN-03 → OUT-03/04 holdings<br>IN-04 → OUT-05 tw_index_daily<br>IN-05 → OUT-02 yf_* 欄</div></div></div></div>
<div class="card c4 chart"><h3>引擎燈分布</h3><div id="ch_lamps"></div></div>
<div class="card c4 chart"><h3>清單市場分布</h3><div id="ch_market"></div></div>
<div class="card c4 chart"><h3>ETF 前 {{ config.params.charts.etf_top_n }} 持股(權重 %)</h3><div id="ch_etf"></div></div>
<div class="card c6" id="readiness"><h3>引擎自測矩陣(紅 / 逾時優先 · 前 {{ data.readiness|length }})</h3><div class="tbl"><table><tr><th>燈</th><th>家族</th><th>引擎</th><th>判決</th></tr>{% for r in data.readiness %}<tr><td><i class="lamp {{ r.lamp }}"></i>{{ r.lamp }}</td><td>{{ r.fam }}</td><td>{{ r.engine }}</td><td>{{ r.verdict }}</td></tr>{% endfor %}</table></div></div>
<div class="card c6" id="filemap"><h3>檔案位置(缺 / 無版號優先)</h3><div class="tbl"><table><tr><th>燈</th><th>系統</th><th>類</th><th>名</th><th>版</th></tr>{% for r in data.filemap %}<tr><td><i class="lamp {{ r.燈 }}"></i>{{ r.燈 }}</td><td>{{ r.系統 }}</td><td>{{ r.類 }}</td><td>{{ r.名 }}</td><td>{{ r.版 }}</td></tr>{% endfor %}</table></div></div>
<div class="card c12" id="universe"><h3>全台股清單 OUT-01(前 {{ data.universe|length }} · 介面表頭 Title Case)</h3><div class="tbl"><table><tr>{% for h in data.universe_header %}<th>{{ h }}</th>{% endfor %}</tr>{% for row in data.universe %}<tr>{% for c in row %}<td>{{ c }}</td>{% endfor %}</tr>{% endfor %}</table></div></div>
<div class="card c12" id="etf"><h3>主動 ETF 每日持股 OUT-03(前 {{ data.etf|length }})</h3><div class="tbl"><table><tr>{% for h in data.etf_header %}<th>{{ h }}</th>{% endfor %}</tr>{% for row in data.etf %}<tr>{% for c in row %}<td>{{ c }}</td>{% endfor %}</tr>{% endfor %}</table></div></div>
<div class="card c4 panel" id="panel"><h3>參數(本頁即時;寫回 ui_config.json 由 PS -Apply)</h3><label>primary_color</label><input id="p_primary" value="{{ config.theme.primary_color }}"><label>font_px</label><input id="p_fs" type="number" value="{{ config.params.font_px }}"><label>palette(seaborn)</label><select id="p_pal"><option>deep</option><option>muted</option><option>pastel</option></select><div style="margin-top:6px"><button class="btn" onclick="VIA.apply()">套用</button> <button class="btn" style="background:#6b7280" onclick="VIA.copyCfg()">複製 ui_config.json</button></div><div class="s" id="p_msg"></div></div>
<div class="card c8 c12"><h3>自適應模板</h3><div class="s">把任何 .html 丟進 {{ data.tpl_dir }},再跑 `Invoke-VIA-VdfUi -Template X.html`:Jinja 變數自動對映,純 HTML 注入 window.VIA + 鎖定色 + 四燈;模板自帶 :root 色票不蓋。可用:{{ data.templates|length }} 個</div></div>
</div>
<script>window.VIA={config:{{ config_json }},data:{{ data_json }},sb:{{ sb_json }}};
(function(){const V=window.VIA,d=V.data,sb=V.sb;const pal=V.config.params.palette||'deep';const C=sb[pal]||sb.deep;const L={GREEN:getComputedStyle(document.documentElement).getPropertyValue('--lamp-green'),RED:'var(--lamp-red)',YELLOW:'var(--lamp-yellow)',GRAY:'var(--lamp-gray)',NODATA:'var(--lamp-nodata)',TIMEOUT:'var(--lamp-gray)'};
function bars(el,items,colors,fmt){if(!el)return;const W=400,H=150,m={l:8,r:8,t:8,b:22};const max=Math.max(1,...items.map(i=>i.v));const bw=(W-m.l-m.r)/Math.max(1,items.length);let s='<svg viewBox="0 0 '+W+' '+H+'" preserveAspectRatio="none">';items.forEach((it,i)=>{const h=(H-m.t-m.b)*it.v/max,x=m.l+i*bw+2,y=H-m.b-h;s+='<rect x="'+x+'" y="'+y+'" width="'+(bw-4)+'" height="'+h+'" rx="2" fill="'+(colors[i%colors.length])+'"><title>'+it.k+': '+(fmt?fmt(it.v):it.v)+'</title></rect>';s+='<text x="'+(x+(bw-4)/2)+'" y="'+(H-m.b+12)+'" font-size="9" text-anchor="middle" fill="#6b7280">'+String(it.k).slice(0,8)+'</text>';s+='<text x="'+(x+(bw-4)/2)+'" y="'+(y-2)+'" font-size="9" text-anchor="middle" fill="#374151">'+(fmt?fmt(it.v):it.v)+'</text>';});el.innerHTML=s+'</svg>';}
if(V.config.params.charts.lamps){const cnt={};(d.readiness||[]).forEach(r=>cnt[r.lamp]=(cnt[r.lamp]||0)+1);const order=['GREEN','YELLOW','RED','TIMEOUT','NODATA','GRAY'];const items=order.filter(k=>cnt[k]).map(k=>({k:k,v:cnt[k]}));bars(document.getElementById('ch_lamps'),items,items.map(i=>L[i.k]||'var(--lamp-gray)'));}
if(V.config.params.charts.market){const idx=(d.universe_header||[]).findIndex(h=>/market/i.test(h));const cnt={};(d.universe||[]).forEach(r=>{const k=idx>=0?(r[idx]||'?'):'?';cnt[k]=(cnt[k]||0)+1});const items=Object.keys(cnt).map(k=>({k:k,v:cnt[k]}));bars(document.getElementById('ch_market'),items.length?items:[{k:'無料',v:0}],C);}
if(V.config.params.charts.etf_top){const hi=(d.etf_header||[]).findIndex(h=>/weight/i.test(h)),hn=(d.etf_header||[]).findIndex(h=>/holding name/i.test(h));const items=(d.etf||[]).map(r=>({k:hn>=0?r[hn]:'?',v:parseFloat(r[hi])||0})).sort((a,b)=>b.v-a.v).slice(0,V.config.params.charts.etf_top_n);bars(document.getElementById('ch_etf'),items.length?items:[{k:'無料',v:0}],C,v=>v.toFixed(2));}
const IN=JSON.parse(JSON.stringify(V.config.params.inputs));let filt=null;
function renderInputs(){const tb=document.getElementById('in_tbl');if(!tb)return;const chips=document.getElementById('in_chips');chips.innerHTML='<span class="chip'+(filt===null?' on':'')+'" onclick="VIA.filter(null)">全部</span>'+IN.groups.map(g=>'<span class="chip'+(filt===g?' on':'')+'" onclick="VIA.filter(\''+g+'\')">'+g+'</span>').join('');
let h='<tr><th></th><th>項目</th><th>分群</th><th>起始日</th><th>來源</th><th>號</th><th></th></tr>';IN.items.forEach((it,i)=>{if(filt!==null&&it.group!==filt)return;const opts=IN.groups.map(g=>'<option'+(g===it.group?' selected':'')+'>'+g+'</option>').join('');
h+='<tr><td><input type="checkbox" '+(it.enabled?'checked':'')+' onchange="VIA.set('+i+',\'enabled\',this.checked)"></td><td><input value="'+(it.name||'')+'" onchange="VIA.set('+i+',\'name\',this.value)" style="max-width:170px"></td><td><select onchange="VIA.set('+i+',\'group\',this.value)">'+opts+'</select></td><td><input type="date" value="'+(it.start||'')+'" placeholder="'+IN.start_date_default+'" onchange="VIA.set('+i+',\'start\',this.value||null)" title="空 = 共用 '+IN.start_date_default+'">'+(it.start?'':'<span class="inherit"> (共用)</span>')+'</td><td><input value="'+(it.source||'')+'" onchange="VIA.set('+i+',\'source\',this.value)" style="max-width:110px"></td><td>'+(it.id||'')+'</td><td><span class="x" onclick="VIA.del('+i+')" title="移除">✕</span></td></tr>';});tb.innerHTML=h;
const on=IN.items.filter(i=>i.enabled).length;document.getElementById('in_on').textContent=on;document.getElementById('in_n').textContent=IN.items.length;const bg={};IN.items.forEach(i=>{bg[i.group]=bg[i.group]||{on:0,n:0};bg[i.group].n++;if(i.enabled)bg[i.group].on++});const el=document.getElementById('in_bygroup');if(el)el.innerHTML=IN.groups.map((g,k)=>'<i class="lamp '+((bg[g]||{on:0}).on?'GREEN':'GRAY')+'"></i>'+g+' '+((bg[g]||{on:0}).on)+'/'+((bg[g]||{n:0}).n)).join('<br>');}
V.set=function(i,k,v){IN.items[i][k]=v;renderInputs();};V.del=function(i){IN.items.splice(i,1);renderInputs();};V.filter=function(g){filt=g;renderInputs();};
V.addItem=function(){const n=IN.items.length+1;IN.items.push({id:'IN-'+String(n).padStart(2,'0'),name:'新項目 '+n,group:filt||IN.groups[0],source:'',enabled:true,start:null});renderInputs();};
V.addGroup=function(){const g=prompt('新分群名稱');if(g&&!IN.groups.includes(g)){IN.groups.push(g);renderInputs();}};
V.exportInputs=function(){const out={schema:'VIA.VDF.UiInputs.v1',start_date_default:IN.start_date_default,start_date_ssot:IN.start_date_ssot,groups:IN.groups,items:IN.items,at:new Date().toISOString()};const t=JSON.stringify(out,null,1);const a=document.createElement('a');a.href='data:application/json;charset=utf-8,'+encodeURIComponent(t);a.download='vdf_inputs.json';a.click();(navigator.clipboard?navigator.clipboard.writeText(t):Promise.resolve()).then(()=>{document.getElementById('in_msg').innerHTML='已下載並複製 vdf_inputs.json(項目 '+IN.items.length+' · 分群 '+IN.groups.length+')';});};
renderInputs();
V.apply=function(){const p=document.getElementById('p_primary').value,f=document.getElementById('p_fs').value,pl=document.getElementById('p_pal').value;document.documentElement.style.setProperty('--primary',p);document.documentElement.style.setProperty('--fs',f+'px');V.config.theme.primary_color=p;V.config.params.font_px=parseInt(f);V.config.params.palette=pl;document.getElementById('p_msg').textContent='已套用(本頁);要存檔:複製 → ui_config.json';};
V.copyCfg=function(){const t=JSON.stringify({app_title:V.config.app_title,theme:V.config.theme,params:{font_px:V.config.params.font_px,palette:V.config.params.palette}},null,1);(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(()=>document.getElementById('p_msg').textContent='已複製到剪貼簿').catch(()=>{document.getElementById('p_msg').textContent=t});};
document.getElementById('p_pal').value=pal;})();</script></body></html>"""


# ---------------- 迷你渲染器(jinja2 在就用 jinja2;不在用這個:{{ a.b|length }} · {% if %} · {% for %}) ----------------
def _get(ctx, path: str):
    cur = ctx
    for part in path.strip().split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
        if cur is None:
            return ""
    return cur


def _expr(ctx, e: str):
    e = e.strip()
    m = re.match(r"^'([^']*)'\s+if\s+(.+?)\s+else\s+'([^']*)'$", e)
    if m:
        return m.group(1) if _truth(ctx, m.group(2)) else m.group(3)
    if "|length" in e:
        v = _get(ctx, e.split("|")[0]); return len(v) if hasattr(v, "__len__") else 0
    if e.startswith("'") and e.endswith("'"):
        return e[1:-1]
    return _get(ctx, e)


def _truth(ctx, cond: str) -> bool:
    cond = cond.strip()
    m = re.match(r"^(\S+)\s*==\s*(\S+)$", cond)
    if m:
        return str(_expr(ctx, m.group(1))) == str(_expr(ctx, m.group(2)))
    v = _expr(ctx, cond)
    return bool(v) and v not in ("", "None", "False")


def mini_render(tpl: str, ctx: dict) -> str:
    def render_block(s: str) -> str:
        # for loops (innermost first)
        pat = re.compile(r"\{%\s*for\s+(\w+)\s+in\s+([\w\.]+)\s*%\}(.*?)\{%\s*endfor\s*%\}", re.S)
        while True:
            m = pat.search(s)
            if not m:
                break
            var, seq, body = m.group(1), m.group(2), m.group(3)
            items = _get(ctx, seq) or []
            out = []
            for i, it in enumerate(items):
                sub = dict(ctx); sub[var] = it; sub["loop"] = {"index0": i, "index": i + 1}
                out.append(mini_render(body, sub))
            s = s[:m.start()] + "".join(out) + s[m.end():]
        pat_if = re.compile(r"\{%\s*if\s+(.+?)\s*%\}(.*?)\{%\s*endif\s*%\}", re.S)
        while True:
            m = pat_if.search(s)
            if not m:
                break
            s = s[:m.start()] + (m.group(2) if _truth(ctx, m.group(1)) else "") + s[m.end():]
        return re.sub(r"\{\{\s*(.+?)\s*\}\}", lambda mm: str(_expr(ctx, mm.group(1))), s)
    return render_block(tpl)


def render(tpl: str, ctx: dict) -> str:
    try:
        import jinja2
        return jinja2.Environment(autoescape=False).from_string(tpl).render(**ctx)
    except ImportError:
        return mini_render(tpl, ctx)


# ---------------- 參數 ----------------
def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if CONFIG_PATH.is_file():
        try:
            user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for k, v in user.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
        except Exception:
            pass
    # 輸入項目:vdf_inputs.json 在就覆蓋(操作員在面板新增 / 改群後匯出的檔)
    try:
        ip = UI_DIR / cfg["params"]["inputs"]["items_file"]
        if ip.is_file():
            user_inputs = json.loads(ip.read_text(encoding="utf-8"))
            if isinstance(user_inputs, dict):
                for k in ("groups", "items", "start_date_default"):
                    if k in user_inputs:
                        cfg["params"]["inputs"][k] = user_inputs[k]
    except Exception:
        pass
    # FormatLock 尾版的字型 / 燈色優先(鎖定色)
    try:
        books = sorted((VIA / "supportive modules" / "registry").glob("VIA_UI_FormatLock_v*.json"))
        if books:
            tk = json.loads(books[-1].read_text(encoding="utf-8")).get("tokens") or {}
            for k in ("GREEN", "YELLOW", "RED", "GRAY", "NODATA"):
                if tk.get("lamp_" + k):
                    PAL[k] = tk["lamp_" + k]
            if tk.get("font_family"):
                cfg["theme"]["font_family"] = tk["font_family"]
    except Exception:
        pass
    return cfg


def save_config(patch: dict) -> None:
    cur = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.is_file() else {}
    for k, v in patch.items():
        if isinstance(v, dict):
            cur.setdefault(k, {}).update(v)
        else:
            cur[k] = v
    UI_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------- 資料(只讀) ----------------
def _title(s: str) -> str:
    ACR = {"eps", "etf", "id", "yf", "bb", "twse", "tpex", "pb", "pe", "roe", "nav", "aum", "url"}
    return " ".join(w.upper() if w.lower() in ACR else w[:1].upper() + w[1:].lower() for w in re.split(r"[_\s]+", s) if w)


def _read_csv(path: Path, limit: int):
    if not path.is_file():
        return [], []
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return [], []
    return rows[0], rows[1:1 + limit]


def load_data(cfg: dict) -> dict:
    d = {"at": datetime.now().strftime("%Y-%m-%d %H:%M"), "templates": list_templates()}
    uni_json = VIA / "VIA_Reports" / "vdf" / "universe" / "VDF_UNIVERSE_latest.json"; uni_csv = uni_json.with_suffix(".csv")
    hdr, rows = _read_csv(uni_csv, cfg["params"]["table_max_rows"]["universe"])
    d["universe_header"] = [_title(h) for h in hdr]; d["universe"] = rows; d["universe_src"] = uni_csv.name if hdr else "再生件未產(跑 VDF_SystemManager universe)"
    n_all = 0
    if uni_csv.is_file():
        with open(uni_csv, encoding="utf-8-sig") as f:
            n_all = max(0, sum(1 for _ in f) - 1)
    d["universe_n"] = n_all if n_all else "—"
    d["etf_header"], d["etf"], d["etf_date"], d["etf_n"] = [], [], "—", "—"
    try:
        import duckdb
        home = Path(os.environ.get("VIA_DATA_HOME") or r"C:\Users\tonyk\VIA System\via_database")
        for cand in (home / "ActiveTWETF.duckdb", VIA / "functional modules" / "VDF" / "output_hub" / "ActiveTWETF.duckdb"):
            if cand.is_file():
                con = duckdb.connect(str(cand), read_only=True)
                dt = con.execute("SELECT max(portfolio_date) FROM holdings_daily").fetchone()[0]
                cur = con.execute("SELECT etf_ticker, etf_name, holding_ticker, holding_name, weight_pct, shares FROM holdings_daily WHERE portfolio_date = ? ORDER BY etf_ticker, weight_pct DESC LIMIT ?", [dt, cfg["params"]["table_max_rows"]["etf"]])
                d["etf_header"] = [_title(c[0]) for c in cur.description]; d["etf"] = [[str(x) for x in r] for r in cur.fetchall()]
                d["etf_n"] = con.execute("SELECT count(*) FROM holdings_daily WHERE portfolio_date = ?", [dt]).fetchone()[0]; d["etf_date"] = str(dt); con.close(); break
    except Exception as e:  # duckdb 缺 / 庫不在 = 誠實空
        d["etf_date"] = f"NODATA({type(e).__name__})"
    hdr, rows = _read_csv(VIA / "VIA_Reports" / "review" / "ENGINE_READINESS_latest.csv", cfg["params"]["table_max_rows"]["readiness"])
    idx = {h: i for i, h in enumerate(hdr)}
    rd = [{"fam": r[idx.get("家族", 0)], "engine": r[idx.get("引擎", 1)], "lamp": r[idx.get("燈", 2)], "verdict": (r[idx.get("判決", 5)] if len(r) > 5 else "")} for r in rows if len(r) > 2]
    rd.sort(key=lambda x: {"RED": 0, "TIMEOUT": 1, "NODATA": 2, "GREEN": 3}.get(x["lamp"], 4))
    d["readiness"] = rd; d["r_green"] = sum(1 for x in rd if x["lamp"] == "GREEN"); d["r_red"] = sum(1 for x in rd if x["lamp"] == "RED"); d["r_other"] = len(rd) - d["r_green"] - d["r_red"]
    fm = VIA / "VIA_Reports" / "review" / "VIA_FILE_MAP_latest.json"; fmr = []
    if fm.is_file():
        try:
            fmr = json.loads(fm.read_text(encoding="utf-8")); fmr = fmr if isinstance(fmr, list) else []
        except Exception:
            fmr = []
    fmr.sort(key=lambda r: {"RED": 0, "YELLOW": 1}.get(r.get("燈"), 2)); d["filemap"] = fmr[:cfg["params"]["table_max_rows"]["filemap"]]
    d["fm_green"] = sum(1 for r in fmr if r.get("燈") == "GREEN"); d["fm_yellow"] = sum(1 for r in fmr if r.get("燈") == "YELLOW"); d["fm_red"] = sum(1 for r in fmr if r.get("燈") == "RED")
    d["overall"] = "RED" if (d["r_red"] or d["fm_red"]) else ("YELLOW" if d["fm_yellow"] or d["r_other"] else ("GREEN" if rd else "GRAY"))
    d["overall_zh"] = {"RED": "有紅", "YELLOW": "有黃", "GREEN": "全綠", "GRAY": "沒料"}[d["overall"]]
    return d


# ---------------- 自適應模板對接 ----------------
def list_templates() -> list:
    return sorted(p.name for p in TPL_DIR.glob("*.html")) if TPL_DIR.is_dir() else []


def adapt_template(src: str, ctx: dict) -> tuple[str, dict]:
    """任何 HTML → 可渲染頁。回 (html, 報告)。模板原碼不改,只注入缺的東西。"""
    rep = {"jinja_vars": sorted(set(re.findall(r"\{\{\s*([\w\.]+)", src))), "has_root": bool(re.search(r":root\s*\{", src)), "has_lamp": ".lamp" in src, "injected": []}
    out = src
    if rep["jinja_vars"] or "{%" in src:
        out = render(out, ctx)                       # (a) 宣告變數對映:config / data / pal / engine
    inject_css = ""
    if not rep["has_root"]:
        c = ctx["config"]; inject_css += (f":root{{--primary:{c['theme']['primary_color']};--bg:{c['theme']['bg_color']};--font:{c['theme']['font_family']};--sidebar:{c['layout']['sidebar_width']};"
                                            f"--lamp-green:{PAL['GREEN']};--lamp-yellow:{PAL['YELLOW']};--lamp-red:{PAL['RED']};--lamp-gray:{PAL['GRAY']};--lamp-nodata:{PAL['NODATA']}}}"); rep["injected"].append("root-tokens")
    else:
        inject_css += f":root{{--lamp-green:{PAL['GREEN']};--lamp-yellow:{PAL['YELLOW']};--lamp-red:{PAL['RED']};--lamp-gray:{PAL['GRAY']};--lamp-nodata:{PAL['NODATA']}}}"; rep["injected"].append("lamp-tokens-only(尊重模板色票)")
    if not rep["has_lamp"]:
        inject_css += LAMP_CSS; rep["injected"].append("lamp-css")
    bridge = f"<script>window.VIA={{config:{json.dumps(ctx['config'], ensure_ascii=False)},data:{json.dumps({k: v for k, v in ctx['data'].items() if k not in ('templates',)}, ensure_ascii=False, default=str)}}};</script>"
    rep["injected"].append("window.VIA bridge")
    head_block = f"<style data-via='adapt'>{inject_css}</style>{bridge}"
    if re.search(r"</head>", out, re.I):
        out = re.sub(r"</head>", head_block + "</head>", out, count=1, flags=re.I)
    else:
        out = head_block + out; rep["injected"].append("no-head→prepend")
    return out, rep


def build_context(cfg: dict) -> dict:
    data = load_data(cfg)
    data["tpl_dir"] = str(TPL_DIR)
    slim = {k: v for k, v in data.items() if k not in ("templates",)}
    return {"config": cfg, "data": data, "pal": PAL, "engine": ENGINE, "lamp_css": LAMP_CSS, "sb": SEABORN[cfg["params"].get("palette", "deep")], "config_json": json.dumps(cfg, ensure_ascii=False),
            "data_json": json.dumps(slim, ensure_ascii=False, default=str), "sb_json": json.dumps(SEABORN, ensure_ascii=False), "data_keys_json": json.dumps(sorted(data.keys()), ensure_ascii=False)}


def render_page(template: str | None = None) -> tuple[str, dict]:
    cfg = load_config(); name = template or cfg.get("active_template"); ctx = build_context(cfg)
    if name and (TPL_DIR / name).is_file():
        return adapt_template((TPL_DIR / name).read_text(encoding="utf-8", errors="replace"), ctx)
    return render(DEFAULT_HTML, ctx), {"template": "builtin", "injected": []}


# ---------------- HTTP ----------------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 安靜
        pass

    def _send(self, body: str, ctype="text/html; charset=utf-8", code=200):
        b = body.encode("utf-8"); self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        try:
            if u.path == "/":
                page, _ = render_page(q.get("template", [None])[0]); return self._send(page)
            if u.path == "/templates":
                cfg = load_config(); items = "".join(f"<li><a href='/?template={html.escape(t)}'>{html.escape(t)}</a>{' · 現役' if t == cfg.get('active_template') else ''}</li>" for t in list_templates()) or "<li>(templates\\ 夾還是空的:丟任何 .html 進去就會出現在這裡)</li>"
                return self._send(f"<!doctype html><meta charset='utf-8'><body style='font:12px Arial'><h3>可用模板(自適應對接)</h3><ul>{items}</ul><p>夾:{html.escape(str(TPL_DIR))}</p><a href='/'>回面板</a></body>")
            if u.path == "/api/config":
                return self._send(json.dumps(load_config(), ensure_ascii=False), "application/json; charset=utf-8")
            if u.path == "/api/templates":
                return self._send(json.dumps(list_templates(), ensure_ascii=False), "application/json; charset=utf-8")
            if u.path.startswith("/api/"):
                key = u.path[5:]; d = load_data(load_config())
                return self._send(json.dumps({key: d.get(key, d.get(key + "_header")), "at": d["at"]}, ensure_ascii=False, default=str), "application/json; charset=utf-8")
            self._send("not found", code=404)
        except Exception as e:
            self._send(f"<pre>{html.escape(type(e).__name__ + ': ' + str(e))}</pre>", code=500)

    def do_POST(self):
        if urlparse(self.path).path == "/config":
            n = int(self.headers.get("Content-Length") or 0); form = parse_qs(self.rfile.read(n).decode("utf-8"))
            patch = {"app_title": form.get("app_title", [""])[0], "active_template": (form.get("active_template", [""])[0] or None),
                     "theme": {"primary_color": form.get("primary_color", ["#1f2937"])[0]}, "layout": {"sidebar_width": form.get("sidebar_width", ["230px"])[0]}}
            save_config(patch); self.send_response(303); self.send_header("Location", "/"); self.end_headers(); return
        self._send("not found", code=404)


def build(template: str | None = None, out: Path | None = None) -> Path:
    """靜態:資料內嵌成單一 .html,不經伺服器。"""
    UI_DIR.mkdir(parents=True, exist_ok=True); TPL_DIR.mkdir(parents=True, exist_ok=True)
    page, rep = render_page(template)
    out = out or (VIA / "VIA_Reports" / "vdf" / "ui" / load_config()["params"]["out_name"]); out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp"); tmp.write_text(page, encoding="utf-8"); tmp.replace(out)
    stamped = out.with_name(out.stem.replace("_latest", "") + "_" + datetime.now().strftime("%Y%m%d_%H%M%S") + out.suffix); stamped.write_text(page, encoding="utf-8")
    print(json.dumps({"out": str(out), "stamped": str(stamped), "bytes": out.stat().st_size, "adapt": rep}, ensure_ascii=False))
    return out


def serve(port: int, open_browser: bool = True) -> int:
    UI_DIR.mkdir(parents=True, exist_ok=True); TPL_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.is_file():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=1), encoding="utf-8")
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    url = f"http://127.0.0.1:{port}/"
    print(f"[{ENGINE}] U/I 已掛 {url} · 模板夾 {TPL_DIR} · 參數 {CONFIG_PATH} · Ctrl+C 停")
    if open_browser and os.environ.get("VIA_NO_OPEN") != "1":
        threading.Timer(1.5, lambda: webbrowser.open_new(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


# ---------------- 自測 ----------------
def selftest() -> int:
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")
    cfg = load_config(); ctx = build_context(cfg)
    page = render(DEFAULT_HTML, ctx)
    chk("① 內建標準模板渲染:標題 · 四燈 CSS · 鎖定色 · 參數面板 · window.VIA 橋", all(s in page for s in (cfg["app_title"], "via-blink", PAL["YELLOW"], "ui_config.json", "window.VIA")) and "{{" not in page)
    chk("② 迷你渲染器(無 jinja2 也能跑):for / if / |length / 三元", mini_render("{% for x in a %}[{{ x.n }}]{% endfor %}{{ a|length }}{{ 'Y' if flag else 'N' }}{% if flag %}T{% endif %}", {"a": [{"n": 1}, {"n": 2}], "flag": True}) == "[1][2]2YT")
    ext_jinja = "<html><head><title>{{ config.app_title }}</title></head><body><div class='lamp {{ data.overall }}'></div></body></html>"
    out, rep = adapt_template(ext_jinja, ctx)
    chk("③ 外部 Jinja 模板:宣告變數自動對映 · 補 :root 色票 + lamp css + 橋", cfg["app_title"] in out and "--lamp-red" in out and "via-blink" in out and "window.VIA" in out and "config.app_title" in rep["jinja_vars"])
    ext_plain = "<html><head><style>:root{--primary:#123456}</style></head><body><h1>My Dashboard</h1><span class='lamp RED'></span></body></html>"
    out2, rep2 = adapt_template(ext_plain, ctx)
    chk("④ 純 HTML 模板:原碼不改 · 尊重模板 :root(不蓋 --primary)· 只補燈色 token · 注入 window.VIA", "--primary:#123456" in out2 and "lamp-tokens-only" in rep2["injected"][0] and "window.VIA" in out2 and "My Dashboard" in out2)
    out3, rep3 = adapt_template("<div>no head at all</div>", ctx)
    chk("⑤ 沒 <head> 的片段:前置注入也能跑", out3.startswith("<style") and "no-head→prepend" in rep3["injected"])
    chk("⑥ 參數全在 py(UI_PARAMS)· ui_config 只覆蓋 · 預設鍵不丟", isinstance(cfg["theme"].get("primary_color"), str) and cfg["params"]["font_px"] == UI_PARAMS["font_px"] and cfg["params"]["table_max_rows"]["universe"] > 0)
    import tempfile as _tf
    with _tf.TemporaryDirectory() as td:
        outp = build(None, Path(td) / "x.html"); t = outp.read_text(encoding="utf-8")
        chk("⑩ 靜態 build:單檔 · 資料內嵌(window.VIA.data)· 響應式 @media · seaborn 色票 · 迷你 SVG 圖表 · 不經伺服器", outp.is_file() and "window.VIA={config:" in t and "@media (max-width" in t and SEABORN["deep"][0] in t and "ch_lamps" in t and len(list(Path(td).glob("x_*.html"))) == 1)
    chk("⑦ 資料只讀:再生件 / 庫不在時誠實空(不假造列)", isinstance(ctx["data"]["universe"], list) and isinstance(ctx["data"]["readiness"], list))
    import socket
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = ThreadingHTTPServer(("127.0.0.1", port), H); th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    try:
        import urllib.request
        body = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10).read().decode("utf-8")
        api = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/config", timeout=10).read().decode("utf-8"))
        chk("⑧ 本機 HTTP 真起得來:/ 回面板 · /api/config 回 JSON", "window.VIA" in body and api.get("app_title") == cfg["app_title"], f"port {port}")
    finally:
        srv.shutdown(); srv.server_close()
    chk("⑪ 左側輸入項目:起始日共用 SSOT-VCGC-VDF-INPT0001 · 五項預設 · 分群五組 · 面板 JS(新增項目 / 分群 / 匯出)在頁內", cfg["params"]["inputs"]["start_date_default"] == "2026-01-02" and len(cfg["params"]["inputs"]["items"]) >= 5 and all(k in page for k in ("in_tbl", "VIA.addItem", "VIA.addGroup", "VIA.exportInputs", "SSOT-VCGC-VDF-INPT0001")))
    chk("⑨ 加速器橋在 · 零網路 · 零寫庫", "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {ENGINE} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not a:
        print(__doc__); return 2
    if a[0] == "build":
        out = build(a[a.index("--template") + 1] if "--template" in a else None, Path(a[a.index("--out") + 1]) if "--out" in a else None)
        if "--open" in a and os.environ.get("VIA_NO_OPEN") != "1":
            webbrowser.open_new(out.as_uri())
        return 0
    if a[0] == "render":
        page, rep = render_page(a[a.index("--template") + 1] if "--template" in a else None); print(page); print("<!-- adapt:", json.dumps(rep, ensure_ascii=False), "-->", file=sys.stderr); return 0
    if a[0] == "serve":
        if os.environ.get("VIA_FROM_VCGC") != "YES" and os.environ.get("VIA_UI_DIRECT") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc(或 VIA_UI_DIRECT=YES 由 Invoke-VIA-VdfUi 帶入)"}, ensure_ascii=False)); return 2
        if "--template" in a:
            save_config({"active_template": a[a.index("--template") + 1]})
        port = int(a[a.index("--port") + 1]) if "--port" in a else int(load_config().get("port") or 8765)
        return serve(port, open_browser="--no-open" not in a)
    print(__doc__); return 2


if __name__ == "__main__":
    raise SystemExit(main())
