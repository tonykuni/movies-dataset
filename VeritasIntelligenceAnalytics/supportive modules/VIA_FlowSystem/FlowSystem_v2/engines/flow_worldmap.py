# -*- coding: utf-8 -*-
"""VDF-FLOW-WORLDMAP-23 flow_worldmap.py — 世界地圖/風險階梯 資金流動畫(v0100R)。

README v0106-v0108:自含離線(零 CDN)· 真實每日 FIS panel 驅動(rows 給定時按
region/risk_tier 每日 AUM 加權聚合取 26 幀,date-key 一律 str 對齊);無 rows 退情境 demo。
v0100R 以自含 SVG 實作(plotly 在位時原版行為到件替換);world_flow.html + tier_flow.html。
"""
import json
from pathlib import Path

from flow_core import bucket_fis, load_universe
from flow_sim import load_sim, build_frames
from flow_ui import TOKENS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
W_OUT = ROOT / "world_flow.html"
T_OUT = ROOT / "tier_flow.html"


def _frames_from_rows(rows, key):
    """真實 panel → 每日聚合 → 取樣 ≤26 幀;date-key 統一 str(v0108 修 bug)。"""
    uni = load_universe()
    by_d = {}
    for r in rows:
        by_d.setdefault(str(r["date"]), []).append(r)
    dates = sorted(by_d)
    step = max(1, len(dates) // 26)
    frames = []
    for d in dates[::step][:26]:
        agg = bucket_fis(by_d[d], key, universe=uni)
        frames.append({"date": d, "vals": agg})
    return frames


def _page(title, payload, node_mode):
    t = dict(TOKENS)
    head = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>%s</title><style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:%(bg)s;color:%(ink2)s;font-family:"Microsoft JhengHei","Segoe UI",sans-serif;font-size:13px;padding:16px}
.wrap{max-width:1100px;margin:0 auto}
.kick{font:700 10px "DM Mono",Consolas,monospace;letter-spacing:.14em;text-transform:uppercase;color:%(teal)s}
h1{font-size:clamp(15px,2vw,18px);color:%(ink)s;margin-bottom:8px}
.card{background:%(paper)s;border:1px solid %(line)s;border-radius:8px;padding:12px 14px;margin-bottom:12px}
.ctrl{display:flex;gap:10px;align-items:center;margin-bottom:6px}
.ctrl button{font-family:inherit;font-size:12px;border:1px solid %(line)s;background:%(paper2)s;border-radius:6px;padding:5px 12px;cursor:pointer}
input[type=range]{flex:1}
svg{width:100%%;height:auto;display:block}
.hint{font-size:10.5px;color:%(mut)s}
</style></head><body><div class="wrap">""" % dict(t)
    head = head % title if "%s" in head else head
    return (head.replace("%s", title, 1)
            + """<div class="kick">VIA FlowSystem v2(v0100R · 自含離線 · 零 CDN)</div>
<h1>""" + title + """</h1>
<div class="card"><div class="ctrl"><button id="play">▶ 播放</button>
<input type="range" id="tl" min="0" max="0" value="0"><span class="hint" id="ph"></span></div>
<svg id="cv" viewBox="0 0 760 """ + ("470" if node_mode == "map" else "430") + """"></svg></div>
<div class="hint">紅=流入 · 綠=流出 · 節點大小=|流量| · region=曝險非來源</div>
<script>
var D=""" + json.dumps(payload, ensure_ascii=False) + """;
var MODE=\"""" + node_mode + """\";
var cur=0,playing=false;
var UP='""" + t["up"] + """',DN='""" + t["down"] + """',MUT='""" + t["mut2"] + """',INK='""" + t["ink"] + """',SOFT='""" + t["line2"] + """',PAPER2='""" + t["paper2"] + """';
document.getElementById("tl").max=D.frames.length-1;
function color(v){return v>0?UP:(v<0?DN:MUT);}
function pos(n,i,N){
 if(MODE==="map"){return [(n.lon+180)/360*720+20,(74-n.lat)/114*400+25];}
 return [180+i*140,380-i*100];}
function render(){
 var f=D.frames[cur],svg="";
 if(MODE==="map"){svg+='<rect width="760" height="470" fill="'+PAPER2+'"/>';
  svg+='<path d="M60 170 Q150 90 260 135 Q330 100 420 145 Q520 80 640 125 Q705 175 690 255 Q600 330 500 305 Q400 360 300 330 Q180 370 100 295 Q40 230 60 170 Z" fill="'+SOFT+'" opacity="0.55"/>';}
 var vals=f.vals||{};
 D.nodes.forEach(function(n,i){
  var p=pos(n,i,D.nodes.length);
  var v=vals[n.key]!=null?vals[n.key]:0;
  var r=8+Math.min(16,Math.abs(v)/5);
  svg+='<circle cx="'+p[0]+'" cy="'+p[1]+'" r="'+r+'" fill="'+color(v)+'" opacity="0.8"><title>'+n.name+' · FIS '+v.toFixed(1)+'</title></circle>';
  svg+='<text x="'+p[0]+'" y="'+(p[1]-r-6)+'" text-anchor="middle" font-size="11" font-weight="700" fill="'+INK+'">'+n.name+'</text>';
  svg+='<text x="'+p[0]+'" y="'+(p[1]+r+13)+'" text-anchor="middle" font-size="10" font-family="Consolas,monospace" fill="'+color(v)+'">'+v.toFixed(1)+'</text>';});
 if(MODE==="tier"){
  var hi=(vals["T3"]||0)+(vals["T4"]||0),lo=(vals["T1"]||0)+(vals["T2"]||0);
  var up=hi>lo;
  svg+='<path d="M90 340 L90 120" stroke="'+(up?UP:DN)+'" stroke-width="'+Math.min(8,2+Math.abs(hi-lo)/25)+'" marker-end="url(#a2)" opacity="0.6" transform="'+(up?'':'rotate(180 90 230)')+'"/>';
  svg='<defs><marker id="a2" markerWidth="4" markerHeight="4" refX="3" refY="2" orient="auto"><path d="M0 0 L4 2 L0 4 Z" fill="'+(up?UP:DN)+'"/></marker></defs>'+svg;
  svg+='<text x="60" y="60" font-size="11" fill="'+INK+'">'+(up?"資金爬升追逐風險 ↑":"下滑逃向安全 ↓")+'</text>';}
 document.getElementById("cv").innerHTML=svg;
 document.getElementById("ph").textContent=(f.date||("第 "+f.day+" 天 · "+(f.label||"")))+" · 幀 "+(cur+1)+"/"+D.frames.length+(D.real?" · 真實每日資料":" · 情境 demo");
}
document.getElementById("tl").addEventListener("input",function(){cur=+this.value;render();});
document.getElementById("play").addEventListener("click",function(){
 playing=!playing;this.textContent=playing?"⏸":"▶ 播放";
 if(playing)(function tick(){if(!playing)return;cur=(cur+1)%D.frames.length;
  document.getElementById("tl").value=cur;render();setTimeout(tick,220);})();});
render();
</script></div></body></html>""")


def build_worldmap(rows=None, write=True):
    sim = load_sim()
    regions = sim.get("regions", [])
    if rows:
        rmap = {"US": "us_eq", "Europe": "europe", "Japan": "jpy", "China": "china",
                "Taiwan": "taiwan", "Korea": "korea", "India": "india",
                "LatAm": "em_latam", "EM": "em_latam"}
        frames = _frames_from_rows(rows, lambda r, u: rmap.get(u.get("region", "US"), "us_eq"))
        real = True
    else:
        frames = [{"day": f["day"], "label": f["label"],
                   "vals": {n["id"]: round(100 * __import__("math").tanh(n["risk_loading"] * f["RISK"]), 1)
                            for n in regions}}
                  for f in build_frames(sim)[::4]]
        real = False
    payload = {"real": real, "frames": frames,
               "nodes": [{"key": n["id"], "name": n["name"], "lat": n["lat"], "lon": n["lon"]}
                         for n in regions]}
    page = _page("世界地圖 · 動態資金流", payload, "map")
    if write:
        W_OUT.write_text(page, encoding="utf-8")
    return page


def build_tierflow(rows=None, write=True):
    sim = load_sim()
    tiers = sim.get("tiers", [])
    if rows:
        frames = _frames_from_rows(rows, lambda r, u: "T%d" % u.get("risk_tier", 3))
        real = True
    else:
        frames = [{"day": f["day"], "label": f["label"],
                   "vals": {t["id"]: round(100 * __import__("math").tanh(t["risk_loading"] * f["RISK"]), 1)
                            for t in tiers}}
                  for f in build_frames(sim)[::4]]
        real = False
    payload = {"real": real, "frames": frames,
               "nodes": [{"key": t["id"], "name": t["name"]} for t in tiers]}
    page = _page("風險類別 · 動態資金階梯", payload, "tier")
    if write:
        T_OUT.write_text(page, encoding="utf-8")
    return page
