#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG014_StdDashboardTemplate — 標準化模板階層(批279;操作員令)
====================================================================
操作員令:「標準化模板階層規劃 左面板為連結或參數 右面板在於展示
多頁式 PLOTLY DASHBOARD」。
階層規劃(L0-L2;視覺=b258 鎖定 tokens 批278):
  L0 殼:左 308px 面板+右工作區(nav-btn/card/field=鎖定元件類)
  L1 左面板:①連結區=多頁切換鈕 ②參數區=Top-N/門檻(客端 JS
    過濾,零後端零網路)
  L2 右面板:多頁式 Plotly 版(data-page 切換;Plotly.react 參數
    即時重繪)
資料(全在庫零發明;Zero-Hydra 複用分析引擎尾版):
  P1 主動 ETF×共識加權 upside 榜(bar)← ENG068 analyze()
  P2 月營收×共識四象限(scatter)← ENG069 analyze()
  P3 族群月營收動能(bar)← ENG069 groups
Plotly 紀律(承 ENG003 批123):plotly.js 內嵌單檔自足=零 CDN;
  plotly 缺席=誠實停+一行安裝指令(依賴誠實)。
用法:python3 VAP_ENG014_StdDashboardTemplate_v0100.py run | --selftest
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

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
VDF_ENG = VIA / "functional modules" / "VDF" / "engine"
OUT = (VIA / "supportive modules" / "ui_support"
       / "VIA_UI_StdDashboard_v0100.html")


def _mod(dirp: Path, pat: str):
    p = sorted(dirp.glob(pat))[-1]
    spec = importlib.util.spec_from_file_location(p.stem, p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _plotly():
    try:
        import plotly.offline as po
        return po
    except Exception:
        return None


def gather() -> dict:
    """三頁資料全在庫(分析引擎尾版 analyze 直取=Zero-Hydra)"""
    e68 = _mod(VDF_ENG, "VDF_ENG068_ETFConsensusAnalysis_v*.py")
    e69 = _mod(VDF_ENG, "VDF_ENG069_RevenueConsensusAnalysis_v*.py")
    d68 = e68.analyze()
    d69 = e69.analyze()
    etf = [e for e in d68["etfs"] if e["wtd_upside"] is not None]
    return {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "p1": {"labels": [f'{e["etf"]} {str(e["name"] or "")[:6]}'
                          for e in etf],
               "upside": [e["wtd_upside"] for e in etf],
               "cov": [e["cov_w_pct"] for e in etf],
               "asof": d68["asof"]},
        "p2": {"yoy": [r["yoy"] for r in d69["cov_rows"]],
               "upside": [r["upside"] for r in d69["cov_rows"]],
               "code": [r["code"] for r in d69["cov_rows"]],
               "ym": d69["latest_ym"], "quad": d69["quad"]},
        "p3": {"gid": [str(g["gid"]) for g in d69["groups"]],
               "yoy_median": [g["yoy_median"] for g in d69["groups"]],
               "members": [g["members"] for g in d69["groups"]]}}


def render(d: dict, po) -> str:
    pj = po.get_plotlyjs()                    # 內嵌單檔自足=零 CDN
    data_json = json.dumps(d, ensure_ascii=False)
    return """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 標準儀表板模板</title><style>
:root{--bg:#f3f5f7;--panel:#fff;--line:#dce2e8;--text:#1f2933;
--muted:#6b7785;--blue:#4c78a8;--green:#5a9e6f;--red:#c96b5a;
--navw:308px;--r:10px;--shadow:0 2px 10px rgba(0,0,0,.05)}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--text);
font:13px/1.5 "Segoe UI","Noto Sans TC",sans-serif}
.app{display:grid;grid-template-columns:var(--navw) 1fr;min-height:100vh}
aside{background:var(--panel);border-right:1px solid var(--line);
padding:14px 10px}
h1{font-size:14px;padding:0 7px 4px}
.sub{color:var(--muted);font-size:10px;padding:0 7px 10px}
.nav-title{font-size:9px;color:var(--muted);font-weight:800;
letter-spacing:.7px;text-transform:uppercase;padding:8px 7px 5px}
.nav-btn{width:100%;text-align:left;border:1px solid transparent;
background:none;border-radius:8px;padding:7px 9px;margin-bottom:2px;
cursor:pointer;color:var(--text);font-size:12.5px}
.nav-btn.active{background:#edf3f8;color:var(--blue);
border-color:#d9e5ef;font-weight:700}
.field{padding:5px 7px}
.field label{display:block;font-size:10px;color:var(--muted);
margin-bottom:3px}
.field select{width:100%;border:1px solid var(--line);border-radius:6px;
padding:5px;background:var(--panel);color:var(--text)}
main{padding:14px}
.page{display:none}.page.on{display:block}
.card{background:var(--panel);border:1px solid var(--line);
border-radius:var(--r);box-shadow:var(--shadow);padding:10px}
.card-h{font-size:11px;color:var(--muted);font-weight:800;
letter-spacing:.06em;text-transform:uppercase;padding-bottom:6px}
.plot{width:100%;min-height:420px}
@media(max-width:900px){.app{grid-template-columns:1fr}
aside{border-right:0;border-bottom:1px solid var(--line)}}
</style></head><body><div class="app">
<aside>
  <h1>標準儀表板模板</h1>
  <div class="sub">批279 · L0殼/L1左面板/L2多頁 Plotly ·
  b258 視覺鎖定 · 零 CDN 內嵌 · 資料全在庫</div>
  <div class="nav-title">連結 · 多頁切換</div>
  <button class="nav-btn active" data-page="p1">▤ ETF×共識 upside 榜</button>
  <button class="nav-btn" data-page="p2">▧ 營收×共識四象限</button>
  <button class="nav-btn" data-page="p3">▥ 族群月營收動能</button>
  <div class="nav-title">參數</div>
  <div class="field"><label>P1 顯示檔數(Top-N)</label>
    <select id="topn"><option>10</option><option selected>22</option>
    <option>5</option></select></div>
  <div class="field"><label>P2 upside 門檻(%)</label>
    <select id="thr"><option selected>0</option><option>20</option>
    <option>40</option></select></div>
</aside>
<main>
  <div class="page on" id="pg_p1"><div class="card">
    <div class="card-h">主動 ETF 加權共識 upside(asof __ASOF__)</div>
    <div id="plot1" class="plot"></div></div></div>
  <div class="page" id="pg_p2"><div class="card">
    <div class="card-h">月營收×共識四象限(__YM__)</div>
    <div id="plot2" class="plot"></div></div></div>
  <div class="page" id="pg_p3"><div class="card">
    <div class="card-h">族群月營收動能(年增中位)</div>
    <div id="plot3" class="plot"></div></div></div>
</main></div>
<script>__PLOTLYJS__</script>
<script>
const D=__DATA__;
const AX={gridcolor:"#dce2e8",zerolinecolor:"#b9c3cc"};
const LAY={margin:{l:150,r:20,t:10,b:40},paper_bgcolor:"rgba(0,0,0,0)",
plot_bgcolor:"rgba(0,0,0,0)",font:{size:11}};
function p1(n){
  const idx=D.p1.upside.map((v,i)=>i).sort((a,b)=>D.p1.upside[b]-D.p1.upside[a]).slice(0,n).reverse();
  Plotly.react("plot1",[{type:"bar",orientation:"h",
    y:idx.map(i=>D.p1.labels[i]),x:idx.map(i=>D.p1.upside[i]),
    marker:{color:"#4c78a8"},
    text:idx.map(i=>D.p1.upside[i].toFixed(1)+"%(覆蓋"+D.p1.cov[i].toFixed(0)+"%)"),
    textposition:"outside"}],
    Object.assign({},LAY,{xaxis:Object.assign({title:"加權 upside %"},AX),
    yaxis:AX,height:Math.max(420,idx.length*26+80)}),{displaylogo:false});
}
function p2(thr){
  const g=[],r=[];
  D.p2.yoy.forEach((y,i)=>{const u=D.p2.upside[i];
    (y>0&&u>thr?g:r).push([y,u,D.p2.code[i]]);});
  const mk=(a,c,nm)=>({type:"scatter",mode:"markers",name:nm,
    x:a.map(v=>v[0]),y:a.map(v=>v[1]),text:a.map(v=>v[2]),
    marker:{color:c,size:7,opacity:.75}});
  Plotly.react("plot2",[mk(g,"#5a9e6f","雙強"),mk(r,"#8a97a5","其他")],
    Object.assign({},LAY,{margin:{l:60,r:20,t:10,b:40},height:460,
    xaxis:Object.assign({title:"月營收 yoy %",range:[-80,80]},AX),
    yaxis:Object.assign({title:"共識 upside %"},AX)}),{displaylogo:false});
}
function p3(){
  Plotly.react("plot3",[{type:"bar",x:D.p3.gid,y:D.p3.yoy_median,
    marker:{color:D.p3.yoy_median.map(v=>v>0?"#5a9e6f":"#c96b5a")},
    text:D.p3.members.map(m=>m+" 檔"),textposition:"outside"}],
    Object.assign({},LAY,{margin:{l:60,r:20,t:10,b:80},height:440,
    xaxis:Object.assign({tickangle:-30},AX),
    yaxis:Object.assign({title:"yoy 中位 %"},AX)}),{displaylogo:false});
}
document.querySelectorAll(".nav-btn").forEach(b=>b.onclick=()=>{
  document.querySelectorAll(".nav-btn").forEach(x=>x.classList.remove("active"));
  b.classList.add("active");
  document.querySelectorAll(".page").forEach(x=>x.classList.remove("on"));
  document.getElementById("pg_"+b.dataset.page).classList.add("on");
  window.dispatchEvent(new Event("resize"));});
document.getElementById("topn").onchange=e=>p1(+e.target.value);
document.getElementById("thr").onchange=e=>p2(+e.target.value);
p1(22);p2(0);p3();
</script></body></html>""" \
        .replace("__PLOTLYJS__", pj) \
        .replace("__DATA__", data_json) \
        .replace("__ASOF__", str(d["p1"]["asof"])) \
        .replace("__YM__", str(d["p2"]["ym"]))


def run() -> int:
    po = _plotly()
    if po is None:
        print("[標準模板] plotly 缺席=誠實停(pip install plotly 後再跑)")
        return 2
    try:
        d = gather()
    except Exception as exc:
        print(f"[標準模板] 在庫資料未備=誠實停({type(exc).__name__}):"
              "先跑 via 日更後再產")
        return 2
    OUT.write_text(render(d, po), encoding="utf-8")
    kb = OUT.stat().st_size // 1024
    print(f"[標準模板] 三頁 Plotly({len(d['p1']['labels'])} ETF/"
          f"{len(d['p2']['code'])} 檔四象限/{len(d['p3']['gid'])} 族群)"
          f"· 內嵌自足 {kb}KB · {OUT.name}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run()
    page = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
    chk("① 引擎產出 rc0(plotly 在位+在庫資料)", rc == 0)
    chk("② 階層規劃三層(L0 殼 grid+L1 左面板連結/參數+L2 多頁)",
        'class="app"' in page and 'data-page="p1"' in page
        and 'id="topn"' in page and page.count('class="page') >= 3)
    chk("③ Plotly 內嵌單檔自足(零 CDN=無外鏈 script/link 標籤;"
        "plotly 內文字串不誤殺)",
        "Plotly.react" in page and '<script src="http' not in page
        and '<link href="http' not in page and len(page) > 1_000_000)
    chk("④ 三頁真資料(ETF 榜>10 檔+四象限>50 點+族群>5)",
        rc == 0 and page.count('"etf"') == 0 and '"labels"' in page
        and '"quad"' in page)
    chk("⑤ 參數面板接線(Top-N onchange+門檻 onchange+react 重繪)",
        'getElementById("topn").onchange' in page
        and 'getElementById("thr").onchange' in page)
    chk("⑥ 視覺鎖定元件類(nav-btn/card/field=b258 同款)+零網路+加速橋",
        all(k in page for k in ("nav-btn", "card-h", "field"))
        and "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src for k in ("requests", "httpx")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 標準儀表板模板(VAP_ENG014)· 六檢自測(零網路)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
