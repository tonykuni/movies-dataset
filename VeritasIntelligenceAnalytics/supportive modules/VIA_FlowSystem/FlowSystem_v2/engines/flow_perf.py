# -*- coding: utf-8 -*-
"""VDF-FLOW-PERF flow_perf.py — 正規化走勢圖 + 主題分類(v0100R)。

README v0118-v0119:adj-close 正規化(基準=100,瀏覽器內可調基準日)· 主題故事分類
(指數/美股主題ETF/GICS/台股主題/台股個股)· 分類下拉+勾選過濾 · 時間範圍鈕 ·
線粗規格 1.4/1.0/0.8 · 預設乾淨(主題ETF+指數)。容器=合成示意;perf_prices.json 在位自動切真實。
"""
import json
import math
import random
from pathlib import Path

from flow_core import load_json
from flow_bridge import load_perf_prices
from flow_ui import TOKENS, COMBO

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CFG = ROOT / "config" / "perf.json"
OUTP = ROOT / "perf_trend.html"

GROUP_ZH = {"index": "指數", "theme_us": "美股主題ETF", "gics": "GICS產業",
            "theme_tw": "台股主題個股", "tw_stock": "台股個股"}


def _synth_series(ticker, n=160, seed=None):
    rng = random.Random(seed if seed is not None else hash(ticker) % 99991)
    drift = rng.uniform(-0.0006, 0.0018)
    v, out = 100.0, []
    for i in range(n):
        v *= 1 + rng.gauss(drift, 0.012)
        out.append(round(v, 3))
    return out


def build_perf(write=True):
    cfg = load_json(CFG, {}) or {}
    groups = cfg.get("groups", {})
    real = load_perf_prices()
    n = 160
    dates = []
    import datetime as dt
    d0 = dt.date(2025, 1, 2)
    d = d0
    while len(dates) < n:
        if d.weekday() < 5:
            dates.append(str(d))
        d += dt.timedelta(days=1)
    series, src = [], "synthetic(示意)"
    if real:
        by_t = {}
        for r in real:
            by_t.setdefault(str(r["ticker"]), []).append((str(r["snapshot_date"]), float(r["close"])))
        src = "perf_prices.json(真實)"
    ci = 0
    for gkey, items in groups.items():
        for it in items:
            t = it["t"]
            if real and t in by_t:
                pts = sorted(by_t[t])
                ds = [p[0] for p in pts]
                vs = [p[1] for p in pts]
            else:
                ds, vs = dates, _synth_series(t, n)
            series.append({"t": t, "n": it["n"], "g": gkey, "dates": ds, "vals": vs,
                           "color": COMBO[ci % len(COMBO)]})
            ci += 1
    payload = {"series": series, "groups": {k: GROUP_ZH.get(k, k) for k in groups},
               "src": src, "base_date": cfg.get("base_date", "2025-01-02"),
               "lw": cfg.get("line_width", {})}
    t = TOKENS
    page = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA FlowSystem · 正規化走勢(主題分類)</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",sans-serif;font-size:13px;padding:16px}
.wrap{max-width:1180px;margin:0 auto}
.kick{font:700 10px "DM Mono",Consolas,monospace;letter-spacing:.14em;text-transform:uppercase;color:%(teal)s}
h1{font-size:clamp(15px,2vw,18px);color:%(ink)s;margin-bottom:8px}
.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:12px 14px;margin-bottom:12px}
.ctrl{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin-bottom:8px;font-size:12px}
select,button{font-family:inherit;font-size:12px;border:1px solid %(line)s;background:%(paper2)s;border-radius:6px;padding:5px 10px;cursor:pointer}
button.on{background:%(ink)s;color:#fff;border-color:%(ink)s}
.picks{display:flex;gap:8px;flex-wrap:wrap;font-size:11.5px;margin-bottom:8px;max-height:92px;overflow-y:auto}
.picks label{display:flex;align-items:center;gap:4px;border:1px solid %(line2)s;border-radius:5px;padding:2px 8px;cursor:pointer;background:%(paper2)s}
.sw{display:inline-block;width:9px;height:9px;border-radius:2px}
svg{width:100%%;height:auto;display:block}
.hint{font-size:10.5px;color:%(mut)s}
</style></head><body><div class="wrap">
<div class="kick">VIA FlowSystem v2(v0100R)· 資料來源:__SRC__</div>
<h1>正規化走勢 — 基準=100 · 主題比 GICS 更貼近資金敘事</h1>
<div class="card"><div class="ctrl">
<span>分類篩選</span><select id="gsel"></select>
<button data-a="all">全選</button><button data-a="none">全不選</button>
<span style="margin-left:10px">基準日</span><select id="bsel"></select>
<span style="margin-left:10px">範圍</span>
<button class="rb" data-r="21">1月</button><button class="rb" data-r="63">3月</button>
<button class="rb" data-r="126">6月</button><button class="rb on" data-r="0">全部</button>
</div><div class="picks" id="picks"></div>
<svg id="cv" viewBox="0 0 1100 430"></svg>
<div class="hint">線粗:勾選 1.4 · 一般 1.0 · 指數 benchmark 0.8 虛線 · 基準 100 線 0.8 虛線</div></div>
<script>
var D=__PAYLOAD__;
var SOFT='%(line2)s',FRAME='%(line)s',MUT='%(mut)s',MUT2='%(mut2)s';
var curG="theme_us",range=0,base=D.base_date;
var on={};
D.series.forEach(function(s){on[s.t]=(s.g==="theme_us"||s.g==="index");});
var gs=document.getElementById("gsel");
Object.keys(D.groups).forEach(function(g){var o=document.createElement("option");o.value=g;o.textContent=D.groups[g];if(g===curG)o.selected=true;gs.appendChild(o);});
var bs=document.getElementById("bsel");
var d0=D.series[0]?D.series[0].dates:[];
d0.forEach(function(d,i){if(i%%10===0){var o=document.createElement("o");o=document.createElement("option");o.value=d;o.textContent=d;if(d===base)o.selected=true;bs.appendChild(o);}});
function picks(){
 var box=document.getElementById("picks");box.innerHTML="";
 D.series.filter(function(s){return s.g===curG;}).forEach(function(s){
  var l=document.createElement("label");
  l.innerHTML='<input type="checkbox" '+(on[s.t]?"checked":"")+'><span class="sw" style="background:'+s.color+'"></span>'+s.n;
  l.querySelector("input").addEventListener("change",function(){on[s.t]=this.checked;render();});
  box.appendChild(l);});}
function norm(s){
 var bi=s.dates.indexOf(base);if(bi<0)bi=0;
 var b=s.vals[bi]||1;
 return s.vals.map(function(v){return 100*v/b;});}
function render(){
 var act=D.series.filter(function(s){return on[s.t];});
 var W=1100,H=430,PL=46,PR=90,PT=14,PB=30,pw=W-PL-PR,ph=H-PT-PB;
 var i0=0;
 var nAll=(D.series[0]||{dates:[]}).dates.length;
 if(range>0)i0=Math.max(0,nAll-range);
 var lo=90,hi=110;
 act.forEach(function(s){var nv=norm(s).slice(i0);lo=Math.min(lo,Math.min.apply(null,nv));hi=Math.max(hi,Math.max.apply(null,nv));});
 var pad=(hi-lo)*0.08;lo-=pad;hi+=pad;
 function y(v){return PT+ph-(v-lo)/(hi-lo)*ph;}
 var svg="";
 for(var k=0;k<=4;k++){var vv=lo+(hi-lo)*k/4,yy=y(vv);
  svg+='<line x1="'+PL+'" y1="'+yy+'" x2="'+(W-PR)+'" y2="'+yy+'" stroke="'+SOFT+'"/>';
  svg+='<text x="'+(PL-5)+'" y="'+(yy+3)+'" text-anchor="end" font-size="10" font-family="Consolas" fill="'+MUT2+'">'+vv.toFixed(0)+'</text>';}
 svg+='<line x1="'+PL+'" y1="'+y(100)+'" x2="'+(W-PR)+'" y2="'+y(100)+'" stroke="'+MUT2+'" stroke-width="0.8" stroke-dasharray="4 3"/>';
 svg+='<rect x="'+PL+'" y="'+PT+'" width="'+pw+'" height="'+ph+'" fill="none" stroke="'+FRAME+'"/>';
 act.forEach(function(s){
  var nv=norm(s).slice(i0);
  var lw=s.g==="index"?D.lw.benchmark:(D.lw.focus);
  var dash=s.g==="index"?' stroke-dasharray="5 3"':'';
  var pts=nv.map(function(v,i){return (PL+pw*i/Math.max(1,nv.length-1)).toFixed(1)+","+y(v).toFixed(1);}).join(" ");
  svg+='<polyline points="'+pts+'" fill="none" stroke="'+s.color+'" stroke-width="'+lw+'" opacity="0.9"'+dash+'><title>'+s.n+'</title></polyline>';
  svg+='<text x="'+(W-PR+5)+'" y="'+y(nv[nv.length-1])+'" font-size="10" font-weight="700" fill="'+s.color+'">'+s.n+' '+nv[nv.length-1].toFixed(0)+'</text>';});
 var ds=(D.series[0]||{dates:[]}).dates.slice(i0);
 for(var i=0;i<ds.length;i+=Math.max(1,Math.floor(ds.length/8))){
  svg+='<text x="'+(PL+pw*i/Math.max(1,ds.length-1))+'" y="'+(PT+ph+16)+'" text-anchor="middle" font-size="10" fill="'+MUT+'">'+ds[i]+'</text>';}
 document.getElementById("cv").innerHTML=svg;}
gs.addEventListener("change",function(){curG=this.value;picks();render();});
bs.addEventListener("change",function(){base=this.value;render();});
document.querySelectorAll("[data-a]").forEach(function(b){b.addEventListener("click",function(){
 D.series.filter(function(s){return s.g===curG;}).forEach(function(s){on[s.t]=b.dataset.a==="all";});
 picks();render();});});
document.querySelectorAll(".rb").forEach(function(b){b.addEventListener("click",function(){
 document.querySelectorAll(".rb").forEach(function(x){x.classList.remove("on");});
 b.classList.add("on");range=+b.dataset.r;render();});});
picks();render();
</script></div></body></html>""" % t
    page = page.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False)).replace("__SRC__", src)
    if write:
        OUTP.write_text(page, encoding="utf-8")
    return page
