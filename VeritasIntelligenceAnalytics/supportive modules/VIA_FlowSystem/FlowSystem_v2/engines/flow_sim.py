# -*- coding: utf-8 -*-
"""VDF-FLOW-SIM flow_sim.py — 全球資金流動情境模擬引擎(v0100R)。

README v0111-v0116:自含 SVG(零 Plotly/CDN)· 三維合一(區域/風險層/類型)·
84 步時間軸插值 · 區間累積(prefix-sum)· 評價 V=(ER−λ·風險)/成本 · 自動結論。
FM#1/#2:ground_loadings() 由真實 FIS panel 回歸估 RISK 載荷(標 estimated/prior)。
"""
import json
import math
from pathlib import Path

from flow_core import load_json, bucket_fis, load_universe
from flow_ui import TOKENS, esc

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CFG = ROOT / "config" / "sim.json"
OUTP = ROOT / "global_map_sim.html"


def load_sim():
    return load_json(CFG, {}) or {}


def ground_loadings(rows, universe=None):
    """FM#1:群組 FIS vs 實現 RORO 因子簡回歸估 RISK 載荷;樣本不足回 None(用 prior)。"""
    if not rows:
        return None
    uni = universe or load_universe()
    by_d = {}
    for r in rows:
        by_d.setdefault(r["date"], []).append(r)
    dates = sorted(by_d)
    if len(dates) < 10:
        return None
    risk_series, grp_series = [], {}
    for d in dates:
        day = by_d[d]
        tf = bucket_fis(day, lambda r, u: "T%d" % u.get("risk_tier", 3), universe=uni)
        risk = (tf.get("T4", 0) + tf.get("T3", 0) - tf.get("T1", 0) - tf.get("T2", 0)) / 2.0
        risk_series.append(risk)
        cf = bucket_fis(day, lambda r, u: u.get("asset_class"), universe=uni)
        for k, v in cf.items():
            grp_series.setdefault(k, []).append(v)
    out = {}
    var_r = sum(x * x for x in risk_series) or 1e-9
    for k, ys in grp_series.items():
        n = min(len(ys), len(risk_series))
        beta = sum(a * b for a, b in zip(ys[:n], risk_series[:n])) / var_r
        out[k] = round(max(-1.0, min(1.0, 0.5 * beta)), 3)  # 向先驗收縮
    return out


def _interp(kfs, day):
    ks = sorted(kfs, key=lambda k: k["day"])
    if day <= ks[0]["day"]:
        return ks[0]
    for a, b in zip(ks, ks[1:]):
        if a["day"] <= day <= b["day"]:
            t = (day - a["day"]) / max(1, b["day"] - a["day"])
            return {k: (a[k] + t * (b[k] - a[k])) if isinstance(a.get(k), (int, float)) else b[k]
                    for k in ("day", "RISK", "USD", "INFL", "GEO", "label")}
    return ks[-1]


def build_frames(sim, loadings=None, src="prior"):
    steps = int(sim.get("steps", 84))
    span = int(sim.get("span_days", 180))
    kfs = sim.get("keyframes", [])
    frames = []
    for i in range(steps):
        day = round(i * span / (steps - 1))
        f = _interp(kfs, day)
        frames.append({"day": day, "label": f.get("label", ""),
                       "RISK": round(f["RISK"], 3), "USD": round(f["USD"], 3),
                       "GEO": round(f["GEO"], 3), "INFL": round(f["INFL"], 3)})
    return frames


def build_map_sim(rows=None, write=True):
    sim = load_sim()
    loads = ground_loadings(rows) if rows else None
    src = "estimated" if loads else "prior"
    frames = build_frames(sim, loads, src)
    val = sim.get("valuation", {})
    payload = {"frames": frames, "regions": sim.get("regions", []),
               "tiers": sim.get("tiers", []), "types": sim.get("types", []),
               "loading_source": src, "grounded": loads or {},
               "lam": val.get("lambda", 0.5), "costk": val.get("cost_sensitivity", 0.8),
               "unc": val.get("uncertainty_pct", 18), "span": sim.get("span_days", 180)}
    t = TOKENS
    page = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA FlowSystem · 全球資金流動情境模擬</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",sans-serif;font-size:13px;padding:16px}
.wrap{max-width:1180px;margin:0 auto}
.kick{font:700 10px "DM Mono",Consolas,monospace;letter-spacing:.14em;text-transform:uppercase;color:%(teal)s}
h1{font-size:clamp(15px,2vw,18px);color:%(ink)s;margin-bottom:8px}
.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:12px 14px;margin-bottom:12px}
.ctrl{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:8px}
.ctrl button{font-family:inherit;font-size:12px;border:1px solid %(line)s;background:%(paper2)s;border-radius:6px;padding:5px 12px;cursor:pointer}
.ctrl button.on{background:%(ink)s;color:#fff;border-color:%(ink)s}
input[type=range]{flex:1;min-width:140px}
.grid{display:flex;gap:12px}
.grid>.card{flex:1;min-width:0}
svg{width:100%%;height:auto;display:block}
.rank div{display:flex;align-items:center;gap:6px;font-size:11.5px;margin:2px 0}
.rank i{display:block;height:9px;border-radius:3px}
.concl{font-size:12px;background:%(paper2)s;border:1px solid %(line2)s;border-radius:6px;padding:9px 12px;line-height:1.7}
.hint{font-size:10.5px;color:%(mut)s}
@media (max-width:860px){.grid{flex-direction:column}}
</style></head><body><div class="wrap">
<div class="kick">VIA FlowSystem v2 · 情境模擬(v0100R · 情境推演非預測 · 載荷來源:__SRC__)</div>
<h1>全球資金流動 — 時間軸 × 方向 × 區間累積 × 評價</h1>
<div class="card"><div class="ctrl">
<button class="on" data-v="regions">🌍 區域</button><button data-v="tiers">📊 風險分類</button><button data-v="types">🏷️ 類型分類</button>
<span style="margin-left:12px"></span>
<button id="play">▶ 播放</button><input type="range" id="tl" min="0" max="83" value="0">
<button id="mark">⚑ 設此刻為累積起點</button>
<button class="on" id="mFis">資金流</button><button id="mVal">評價</button>
</div>
<div class="hint" id="phase"></div></div>
<div class="grid">
<div class="card"><svg id="map" viewBox="0 0 760 430"></svg></div>
<div class="card"><b style="font-size:12px">區間累積淨流($B ±__UNC__%%)</b>
<div class="hint">← 紅 淨流入 ｜ 綠 淨流出 →</div><div class="rank" id="rank"></div>
<div class="concl" id="concl"></div></div>
</div>
<div class="hint">說明:類型分類 — 股票=全球股市 · 債券=IG/主權 · 現金=短債 · 大宗商品=原油/工業金屬 · 黃金=避險 · 加密 · 地產=REIT · 外匯=美元指數。情境推演非預測;region=曝險非來源。</div>
<script>
var D=__PAYLOAD__;
var view="regions",mode="fis",cur=0,mark0=0,playing=false;
function nodesOf(){return D[view];}
function fisOf(n,f){var v=100*Math.tanh((n.risk_loading*f.RISK - 0.3*n.risk_loading*f.USD - 0.2*Math.abs(n.risk_loading)*f.GEO)/0.8);return v;}
function cum(n,to,from){var s=0;for(var i=from;i<=to;i++){var f=D.frames[i];s+=fisOf(n,f)/100*(n.aum/1000)*(D.span/D.frames.length)/30;}return s;}
function valScore(n,to,from){var c=cum(n,to,from);var er=fisOf(n,D.frames[to])/100;var cost=1+D.costk*Math.max(0,c)/(n.aum/1000+1);var v=(er-D.lam*Math.abs(n.risk_loading)*0.3)/cost;return Math.max(0,Math.min(100,50+120*v));}
function color(v){return v>0?"%(up)s":(v<0?"%(down)s":"%(mut2)s");}
function xy(n,i,N){
 if(view==="regions"){var x=(n.lon+180)/360*720+20,y=(74-n.lat)/114*370+20;return[x,y];}
 if(view==="tiers"){return[180+i*140,360-i*95];}
 var a=Math.PI*(0.15+0.7*i/(N-1));return[380+300*Math.cos(a),400-330*Math.sin(a)];}
function render(){
 var f=D.frames[cur],ns=nodesOf(),svg="";
 if(view==="regions"){svg+='<rect x="0" y="0" width="760" height="430" fill="%(paper2)s"/>';
  svg+='<path d="M60 150 Q150 80 260 120 Q330 90 420 130 Q520 70 640 110 Q700 160 690 230 Q600 300 500 280 Q400 330 300 300 Q180 340 100 270 Q40 210 60 150 Z" fill="%(line2)s" opacity="0.5"/>';}
 var pts={};
 ns.forEach(function(n,i){pts[n.id]=xy(n,i,ns.length);});
 // 遷移弧線:載荷相反端之間依 RISK 畫向
 var srcs=ns.filter(function(n){return n.risk_loading<0;}),dsts=ns.filter(function(n){return n.risk_loading>0;});
 if(f.RISK<0){var t2=srcs;srcs=dsts;dsts=t2;}
 srcs.slice(0,3).forEach(function(s){dsts.slice(0,3).forEach(function(d){
  var a=pts[s.id],b=pts[d.id];if(!a||!b)return;
  var w=Math.min(5,1+3*Math.abs(f.RISK));
  var col=f.RISK>=0?"%(up)s":"%(down)s";
  var mx=(a[0]+b[0])/2,my=Math.min(a[1],b[1])-40;
  svg+='<path d="M'+a[0].toFixed(0)+' '+a[1].toFixed(0)+' Q'+mx.toFixed(0)+' '+my.toFixed(0)+' '+b[0].toFixed(0)+' '+b[1].toFixed(0)+'" fill="none" stroke="'+col+'" stroke-width="'+w+'" opacity="0.4" stroke-dasharray="7 5" marker-end="url(#ah)"><animate attributeName="stroke-dashoffset" from="24" to="0" dur="1.2s" repeatCount="indefinite"/></path>';});});
 svg='<defs><marker id="ah" markerWidth="3.4" markerHeight="3.4" refX="2.6" refY="1.7" orient="auto"><path d="M0 0 L3.4 1.7 L0 3.4 Z" fill="%(mut)s"/></marker></defs>'+svg;
 ns.forEach(function(n,i){
  var p=pts[n.id];var v=mode==="fis"?fisOf(n,f):valScore(n,cur,mark0);
  var c=mode==="fis"?color(v):(v>=60?"%(down)s":(v<=40?"%(up)s":"%(amber)s"));
  var r=7+Math.min(15,Math.abs(mode==="fis"?v:v-50)/5);
  var cc=cum(n,cur,mark0);
  svg+='<circle cx="'+p[0]+'" cy="'+p[1]+'" r="'+(r+3)+'" fill="none" stroke="'+color(cc)+'" stroke-width="2" opacity="0.5"/>';
  svg+='<circle cx="'+p[0]+'" cy="'+p[1]+'" r="'+r+'" fill="'+c+'" opacity="0.8"><title>'+n.name+' · FIS '+fisOf(n,f).toFixed(0)+' · 累積 '+cc.toFixed(1)+'B · 評價 '+valScore(n,cur,mark0).toFixed(0)+'</title></circle>';
  svg+='<text x="'+p[0]+'" y="'+(p[1]-r-6)+'" text-anchor="middle" font-size="10.5" fill="%(ink)s" font-weight="700">'+n.name+'</text>';
  svg+='<text x="'+p[0]+'" y="'+(p[1]+r+12)+'" text-anchor="middle" font-size="9.5" fill="'+c+'" font-family="Consolas,monospace">'+(mode==="fis"?fisOf(n,f).toFixed(0):valScore(n,cur,mark0).toFixed(0))+'</text>';});
 document.getElementById("map").innerHTML=svg;
 var gram=100*Math.tanh(f.RISK);
 document.getElementById("phase").textContent="第 "+f.day+" 天 · "+f.label+" · GRAM "+gram.toFixed(0)+" · "+(f.RISK>0.05?"RISK_ON":(f.RISK<-0.05?"RISK_OFF":"NEUTRAL"))+" · 累積視窗:第 "+D.frames[mark0].day+"→"+f.day+" 天";
 var rows=ns.map(function(n){return{n:n,c:cum(n,cur,mark0),v:valScore(n,cur,mark0)};}).sort(function(a,b){return b.c-a.c;});
 var mx=Math.max.apply(null,rows.map(function(r){return Math.abs(r.c);}))||1;
 document.getElementById("rank").innerHTML=rows.map(function(r){
  var w=Math.abs(r.c)/mx*46;
  var lab=r.n.name+" "+(r.c>=0?"+":"")+r.c.toFixed(1)+"B · 評價"+r.v.toFixed(0);
  return '<div><span style="width:118px;flex:none;overflow:hidden;white-space:nowrap">'+r.n.name+'</span>'
   +'<span style="width:47%%;display:flex;justify-content:flex-end"><i style="width:'+(r.c>0?w:0)+'%%;background:%(up)s"></i></span>'
   +'<span style="width:47%%"><i style="width:'+(r.c<0?w:0)+'%%;background:%(down)s"></i></span>'
   +'<span class="hint" style="flex:none">'+(r.c>=0?"+":"")+r.c.toFixed(1)+'B·評'+r.v.toFixed(0)+'</span></div>';}).join("");
 var win=rows[0],lose=rows[rows.length-1];
 var instMax=ns.map(function(n){return{n:n,f:fisOf(n,f)};}).sort(function(a,b){return b.f-a.f;});
 var agree=(instMax[0].n.id===win.n.id)?"一致":"不一致(瞬時 vs 累積方向分歧 — 前期主導)";
 var winVal=win.v>=60?"划算":(win.v<=40?"偏貴":"中性");
 var eff=win.v<=40?"資金流入評價偏貴標的 → 追高存疑":"資金流入評價尚可 → 健康";
 document.getElementById("concl").innerHTML="📌 <b>自動結論</b>:第 "+f.day+" 天("+f.label+"),GRAM "+gram.toFixed(0)+"。"
  +"瞬時最大流入 <b>"+instMax[0].n.name+"</b>(FIS "+instMax[0].f.toFixed(0)+"),最大流出 <b>"+instMax[instMax.length-1].n.name+"</b>。"
  +"本期間累積最大贏家 <b>"+win.n.name+"</b>(+"+win.c.toFixed(1)+"B,評價"+win.v.toFixed(0)+"="+winVal+"),最大輸家 <b>"+lose.n.name+"</b>("+lose.c.toFixed(1)+"B)。"
  +"瞬時與累積方向:"+agree+"。有效性:"+eff+"。";
}
document.querySelectorAll("[data-v]").forEach(function(b){b.addEventListener("click",function(){
 document.querySelectorAll("[data-v]").forEach(function(x){x.classList.remove("on");});
 b.classList.add("on");view=b.dataset.v;render();});});
document.getElementById("mFis").addEventListener("click",function(){mode="fis";this.classList.add("on");document.getElementById("mVal").classList.remove("on");render();});
document.getElementById("mVal").addEventListener("click",function(){mode="val";this.classList.add("on");document.getElementById("mFis").classList.remove("on");render();});
document.getElementById("tl").addEventListener("input",function(){cur=+this.value;render();});
document.getElementById("mark").addEventListener("click",function(){mark0=cur;render();});
document.getElementById("play").addEventListener("click",function(){
 playing=!playing;this.textContent=playing?"⏸ 暫停":"▶ 播放";
 if(playing)(function tick(){if(!playing)return;cur=(cur+1)%%D.frames.length;
  document.getElementById("tl").value=cur;render();setTimeout(tick,90);})();});
render();
</script></div></body></html>""" % t
    page = page.replace("__PAYLOAD__", json.dumps(payload, ensure_ascii=False))
    page = page.replace("__SRC__", src).replace("__UNC__", str(payload["unc"]))
    if write:
        OUTP.write_text(page, encoding="utf-8")
    return page
