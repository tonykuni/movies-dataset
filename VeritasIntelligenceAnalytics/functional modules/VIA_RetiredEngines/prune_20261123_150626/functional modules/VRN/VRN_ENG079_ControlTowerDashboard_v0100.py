#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VRN_ENG079_ControlTowerDashboard — VRN 控制塔儀表板(批306)
====================================================================
操作員令:「VIA CONTROL TOWER VRN ACTIVATE · DUAL-SET CROSS
VALIDATE✓ READY … 產出索引整合進來 首字母英文大寫 … 我們先把
VRN 做出來符合剛才上傳的模板」。
版面正本=批305 收容之 Codex 模板(intake/VIA_CodexParallel_b305/
VIA_UI_PlotlyDashboard_EditableTemplate_v0100_codex.html):
  固定 header(印章+品牌+motto+連線/誠實徽章)+可收左欄+
  多頁籤+固定 footer;變數化 --header-h/--footer-h/--rail-w;
  英文標籤=Title Case(操作員令「首字母英文大寫」)。
三頁籤(真值全在庫零發明):
  01 產出索引 Output Index(N=真掃 VRN 現役頁+存證 JSON+對帳
     runs;誠實計數)
  02 共識全景 Consensus Overview(Plotly:分析師數分佈+upside
     直方圖;plotly.js 內嵌自足零 CDN;缺=誠實降級)
  03 共識明細 Consensus Details(upside 降冪前 30 表)
徽章律:VRN Activate=引擎在位;Dual-Set Cross Validate=VRN 既有
啟用+交叉驗證流程(ACTIVATE_AND_CROSS_VALIDATE 冊在=✓ Ready;
缺=誠實灰);Connection=樞紐 ping 實測(online/offline)。
輸出:ui_support/VIA_UI_VRNControlTower_v0100.html(日更再生類)
用法:python3 VRN_ENG079_ControlTowerDashboard_v0100.py run | --selftest
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
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
DB_TW = (VIA / "functional modules" / "VDF" / "output_hub" / "mega"
         / "vdf_tw_market.duckdb")
UI = VIA / "supportive modules" / "ui_support"
OUT_UI = UI / "VIA_UI_VRNControlTower_v0100.html"
REP = VIA / "VIA_Reports"


def _plotly():
    try:
        import plotly.offline as po
        return po
    except Exception:
        return None


def _connect_ro(dbp):
    """唯讀連線三重試(批273 不卡斷律)"""
    import time
    import duckdb
    last = None
    for _ in range(3):
        try:
            return duckdb.connect(str(dbp), read_only=True)
        except Exception as exc:
            last = exc
            time.sleep(2)
    raise last


def gather() -> dict:
    """真值聚合(在庫+檔案系統真掃;缺=誠實 0/空)"""
    d = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
         "consensus": [], "n_consensus": 0, "sources": [],
         "outputs": [], "dual_set_ready": False}
    # 共識庫(誠實:表缺=空)
    if DB_TW.exists():
        try:
            c = _connect_ro(DB_TW)
            tabs = {r[0] for r in c.execute("SHOW TABLES").fetchall()}
            if "consensus_latest" in tabs:
                d["consensus"] = [
                    {"code": r[0], "tp": r[1],
                     "upside": round(float(r[2]) * 100, 1)
                     if r[2] is not None else None,
                     "n": r[3], "source": r[4]}
                    for r in c.execute(
                        "SELECT code, target_median, upside_pct, "
                        "n_analysts, source FROM consensus_latest "
                        "QUALIFY ROW_NUMBER() OVER (PARTITION BY code "
                        "ORDER BY n_analysts DESC NULLS LAST, source)=1"
                    ).fetchall()]
                d["n_consensus"] = len(d["consensus"])
                d["sources"] = sorted({r["source"]
                                       for r in d["consensus"]})
            c.close()
        except Exception:
            pass
    # Dual-Set Cross Validate 冊在位=Ready(VRN 既有啟用+交叉驗證流程)
    d["dual_set_ready"] = any(HERE.glob("*ACTIVATE_AND_CROSS_VALIDATE*"))
    # 產出索引 Output Index(真掃;誠實計數)
    idx = []
    for pat, kind in [
        ("VIA_UI_ReportCards_v*.html", "報告卡頁 Report Cards"),
        ("VIA_UI_ETFConsensusAnalysis_v*.html",
         "主動 ETF×共識檢視 Etf Consensus Review"),
        ("VIA_UI_RevenueConsensusAnalysis_v*.html",
         "月營收×共識檢視 Revenue Consensus Review"),
        ("VIA_UI_Shell_VRN_v*.html", "VRN 現況台 Shell"),
    ]:
        for f in sorted(UI.glob(pat)):
            idx.append({"kind": kind, "name": f.name,
                        "kb": f.stat().st_size // 1024})
    for sub, kind in [("vrn_reconcile_runs", "對帳存證 Reconcile Run"),
                      ("etf_consensus_analysis", "ETF 共識存證 Evidence"),
                      ("revenue_consensus", "營收共識存證 Evidence")]:
        p = REP / sub
        if p.is_dir():
            for f in sorted(p.glob("*.json"))[-8:]:
                idx.append({"kind": kind, "name": f.name,
                            "kb": max(1, f.stat().st_size // 1024)})
    for f in sorted((VIA / "functional modules" / "VRN").glob(
            "VRN_ENG0*_v0*.py")):
        idx.append({"kind": "現役引擎 Engine", "name": f.name,
                    "kb": max(1, f.stat().st_size // 1024)})
    d["outputs"] = idx
    return d


CSS = r"""
:root{--bg:#f4f6f8;--paper:#fff;--paper2:#f9fafb;--ink:#202833;
--ink2:#465365;--mut:#596778;--mut2:#5d6a7b;--line:#dfe4ea;
--soft:#eef3f6;--acc:#315f7d;--ok:#2f7652;--warn:#765418;--bad:#a64f46;
--header-h:48px;--footer-h:28px;--rail-w:236px;--radius:8px}
*{box-sizing:border-box;margin:0}
html,body{min-height:100%;background:var(--bg);color:var(--ink)}
body{font:11px/1.45 "Segoe UI","Noto Sans TC",system-ui,sans-serif;
padding:var(--header-h) 0 var(--footer-h)}
code,.mono{font-family:Consolas,"SFMono-Regular",ui-monospace,monospace}
a{color:var(--acc);text-decoration:none}
a:hover{text-decoration:underline}
.app-header{position:fixed;z-index:80;inset:0 0 auto 0;
height:var(--header-h);display:flex;align-items:center;gap:10px;
padding:0 14px;background:rgba(255,255,255,.97);
border-bottom:1px solid var(--line)}
.rail-toggle{min-height:30px;padding:4px 9px;border:1px solid var(--line);
border-radius:7px;background:var(--paper2);font-weight:700;
cursor:pointer;font:inherit;color:inherit}
.identity{display:flex;align-items:center;gap:8px;min-width:0}
.seal{width:27px;height:27px;display:grid;place-items:center;
background:#315f7d;color:#fff;border-radius:5px;
font:700 14px/1 "Noto Serif TC",serif;flex:none}
.product{font-size:12px;font-weight:800;letter-spacing:.025em;
white-space:nowrap}
.motto{font-size:9px;color:var(--mut);letter-spacing:.1em}
.header-meta{margin-left:auto;display:flex;align-items:center;gap:7px;
flex-wrap:wrap}
.badge{display:inline-flex;align-items:center;min-height:23px;
padding:2px 8px;border:1px solid var(--line);border-radius:999px;
background:var(--paper2);font-size:9.5px;font-weight:700;
color:var(--mut);white-space:nowrap}
.badge.ok{color:var(--ok);border-color:#b8d7c6;background:#f1f8f4}
.badge.bad{color:var(--bad);border-color:#e3c0bc;background:#fff5f3}
.badge.dot::before{content:"";width:7px;height:7px;border-radius:50%;
margin-right:5px;background:currentColor}
.shell{display:flex;min-height:calc(100vh - var(--header-h)
 - var(--footer-h))}
.rail{width:var(--rail-w);min-width:var(--rail-w);
background:var(--paper);border-right:1px solid var(--line);
padding:10px 0;transition:margin-left .25s}
body.railoff .rail{margin-left:calc(0px - var(--rail-w) - 1px)}
.navsec{font-size:8px;letter-spacing:.2em;color:var(--mut2);
font-weight:700;padding:9px 14px 3px}
.pad{padding:2px 14px 6px;font-size:10px;color:var(--mut)}
.pad b{color:var(--ink2)}
.nav a{display:block;padding:5px 14px;color:var(--ink2);font-size:11px}
.nav a:hover{background:var(--soft);text-decoration:none}
.main{flex:1;min-width:0;padding:12px 16px}
.tabs{display:flex;gap:2px;border-bottom:2px solid var(--ink);
margin-bottom:10px}
.tabs a{padding:6px 12px;border-radius:7px 7px 0 0;cursor:pointer;
color:var(--ink2);font-size:11px}
.tabs a.active{background:var(--soft);font-weight:700;color:var(--ink);
border-bottom:3px solid var(--acc)}
.page{display:none}.page.on{display:block}
.stats{display:grid;
grid-template-columns:repeat(auto-fit,minmax(126px,1fr));gap:8px;
margin-bottom:10px}
.stat{background:var(--paper);border:1px solid var(--line);
border-radius:var(--radius);padding:9px 12px}
.stat .n{font-size:clamp(17px,2vw,21px);font-weight:800;
font-variant-numeric:tabular-nums}
.stat .zh{font-size:10.5px;color:var(--ink2);margin-top:2px}
.stat .en{font-size:8px;letter-spacing:.14em;color:var(--mut2);
font-weight:700}
.card{background:var(--paper);border:1px solid var(--line);
border-radius:var(--radius);padding:10px 12px;margin-bottom:9px}
.card h3{font-size:11.5px}
.card h3 small{font-size:8px;letter-spacing:.14em;color:var(--mut2);
font-weight:700;margin-left:6px}
.chart{background:var(--paper);border:1px solid var(--line);
border-radius:var(--radius);padding:6px;margin-bottom:8px}
table{width:100%;border-collapse:collapse;font-size:10.5px}
th{text-align:left;font-size:8.5px;letter-spacing:.12em;
color:var(--mut2);border-bottom:1px solid var(--line);
padding:3px 6px 3px 0;font-weight:700}
td{border-bottom:1px solid var(--soft);padding:3px 6px 3px 0;
font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}
td.g{color:var(--ok);font-weight:600}td.r{color:var(--bad);
font-weight:600}
.wrap{overflow-x:auto}
.app-footer{position:fixed;z-index:80;inset:auto 0 0 0;
height:var(--footer-h);display:flex;align-items:center;gap:14px;
padding:0 14px;background:var(--paper);
border-top:1px solid var(--line);font-size:9px;color:var(--mut)}
@media(max-width:860px){.rail{position:fixed;left:0;
top:var(--header-h);bottom:var(--footer-h);z-index:70;
box-shadow:4px 0 18px rgba(32,40,51,.12)}
body.railoff .rail{margin-left:calc(0px - var(--rail-w) - 1px)}}
"""

JS = r"""
document.querySelectorAll(".tabs a").forEach((el,i)=>el.onclick=()=>{
 document.querySelectorAll(".page").forEach((p,j)=>
  p.classList.toggle("on",i===j));
 document.querySelectorAll(".tabs a").forEach((a,j)=>
  a.classList.toggle("active",i===j));
 window.dispatchEvent(new Event("resize"));});
document.getElementById("railbtn").onclick=()=>
 document.body.classList.toggle("railoff");
(async()=>{const b=document.getElementById("conn");
 try{const r=await(await fetch("http://127.0.0.1:8765/ping")).json();
  b.textContent="Connection Online · "+(r.v||"");
  b.className="badge dot ok";}
 catch(e){b.textContent="Connection Offline(打 via 帶起)";
  b.className="badge dot bad";}})();
const D=JSON.parse(document.getElementById("d").textContent);
if(window.Plotly){
 const L={font:{size:10,family:'"Segoe UI","Noto Sans TC",sans-serif'},
  paper_bgcolor:"#fff",plot_bgcolor:"#fff"};
 const ns=D.cons.map(r=>r.n).filter(n=>n!=null);
 const cnt={};ns.forEach(n=>cnt[n]=(cnt[n]||0)+1);
 const ks=Object.keys(cnt).map(Number).sort((a,b)=>a-b);
 Plotly.newPlot("c1",[{type:"bar",x:ks,y:ks.map(k=>cnt[k]),
  marker:{color:"#315f7d"},
  hovertemplate:"%{x} 位分析師:%{y} 檔<extra></extra>"}],
  Object.assign({},L,{height:300,margin:{l:46,r:16,t:8,b:38},
   xaxis:{title:{text:"分析師數 Analyst Count",font:{size:10}}},
   yaxis:{title:{text:"檔數 Stocks",font:{size:10}}}}),
  {displayModeBar:false,responsive:true});
 Plotly.newPlot("c2",[{type:"histogram",
  x:D.cons.map(r=>r.upside).filter(v=>v!=null),
  marker:{color:"#2f7652"},nbinsx:40,
  hovertemplate:"upside %{x}%:%{y} 檔<extra></extra>"}],
  Object.assign({},L,{height:300,margin:{l:46,r:16,t:8,b:38},
   xaxis:{title:{text:"共識上漲空間 Upside %",font:{size:10}},
    ticksuffix:"%"},
   yaxis:{title:{text:"檔數 Stocks",font:{size:10}}}}),
  {displayModeBar:false,responsive:true});
}
"""


def render(d: dict) -> str:
    po = _plotly()
    dual = ('<span class="badge ok">Dual-Set Cross Validate ✓ Ready'
            "</span>" if d["dual_set_ready"] else
            '<span class="badge">Dual-Set Cross Validate · 冊缺=誠實'
            "</span>")
    idx_rows = "".join(
        f'<tr><td>{html.escape(o["kind"])}</td>'
        f'<td class="mono">{html.escape(o["name"])}</td>'
        f'<td>{o["kb"]:,} KB</td></tr>' for o in d["outputs"]) or (
        '<tr><td colspan="3">產出索引空(誠實)</td></tr>')
    top = sorted((r for r in d["consensus"] if r["upside"] is not None),
                 key=lambda r: -r["upside"])[:30]
    det_rows = "".join(
        f'<tr><td class="mono">{html.escape(r["code"])}</td>'
        f'<td>{r["tp"] if r["tp"] is not None else "—"}</td>'
        f'<td class="{"g" if r["upside"] >= 0 else "r"}">'
        f'{r["upside"]:+.1f}%</td><td>{r["n"] or "—"}</td>'
        f'<td>{html.escape(str(r["source"]))}</td></tr>' for r in top) or (
        '<tr><td colspan="5">共識庫空(誠實;先跑 boot ⑦e)</td></tr>')
    n_hi = sum(1 for r in d["consensus"]
               if (r["n"] or 0) >= 10)
    if po is None:
        plotly_js = ""
        degrade = ('<div class="card">誠實降級:plotly 未安裝=僅表格'
                   "(pip install plotly 後重跑即出圖)</div>")
    else:
        plotly_js = "<script>" + po.get_plotlyjs() + "</script>"
        degrade = ""
    src_txt = "、".join(d["sources"]) or "無(候料)"
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA VRN 控制塔 Control Tower</title><style>{CSS}</style></head><body>
<header class="app-header">
<button id="railbtn" class="rail-toggle">◀▶ 面板</button>
<div class="identity"><span class="seal">觀</span>
<div><div class="product">VRN 控制塔 · Veritas Report Nova</div>
<div class="motto">Via Control Tower · Vrn Activate</div></div></div>
<div class="header-meta">
<span id="conn" class="badge dot">Connection …</span>
{dual}
<span class="badge ok">Honesty · 三態不假綠</span>
</div></header>
<div class="shell">
<aside class="rail">
<div class="navsec">參數 Params(唯讀)</div>
<div class="pad">共識庫 <b>{d["n_consensus"]}</b> 檔<br>
來源 <b>{html.escape(src_txt)}</b><br>
去重律 <b>每 Code 單源列</b>(分析師多者勝)<br>
產出索引 <b>{len(d["outputs"])}</b> 件(真掃)</div>
<div class="navsec">連結 Links</div>
<div class="nav">
<a href="VIA_UI_MasterControl_v0100.html">總控台 Master Control</a>
<a href="VIA_UI_Shell_VRN_v0100.html">VRN 現況台 Shell</a>
<a href="VIA_UI_ReportCards_v0100.html">報告卡 Report Cards</a>
<a href="VIA_UI_ETFConsensusAnalysis_v0100.html">主動 ETF×共識檢視</a>
<a href="VIA_UI_RevenueConsensusAnalysis_v0100.html">月營收×共識檢視</a>
</div></aside>
<main class="main">
<nav class="tabs">
<a class="active">產出索引 Output Index({len(d["outputs"])})</a>
<a>共識全景 Consensus Overview</a>
<a>共識明細 Consensus Details</a>
</nav>
<div class="stats">
<div class="stat"><div class="n">{d["n_consensus"]}</div>
<div class="zh">共識覆蓋</div><div class="en">Consensus Coverage</div></div>
<div class="stat"><div class="n">{n_hi}</div>
<div class="zh">分析師≥10</div><div class="en">Deep Coverage</div></div>
<div class="stat"><div class="n">{len(d["outputs"])}</div>
<div class="zh">產出索引</div><div class="en">Output Index</div></div>
<div class="stat"><div class="n">{len(d["sources"])}</div>
<div class="zh">來源(分欄不跨源)</div><div class="en">Sources</div></div>
</div>
{degrade}
<section class="page on"><div class="card">
<h3>產出索引<small>Output Index · 真掃零發明</small></h3>
<div class="wrap"><table><tr><th>類別 Kind</th><th>檔名 File</th>
<th>大小 Size</th></tr>{idx_rows}</table></div></div></section>
<section class="page">
<div class="chart"><div id="c1"></div></div>
<div class="chart"><div id="c2"></div></div></section>
<section class="page"><div class="card">
<h3>共識明細<small>Top 30 By Upside</small></h3>
<div class="wrap"><table><tr><th>代碼 Code</th><th>目標價中位 Tp</th>
<th>Upside</th><th>分析師 Analysts</th><th>來源 Source</th></tr>
{det_rows}</table></div></div></section>
</main></div>
<footer class="app-footer">
<span>VIA · Veritas Report Nova · Control Tower</span>
<span>產於 {d["ts"]}</span>
<span>來源分欄不跨源平均 · 零 CDN · 非投資建議</span>
</footer>
<script id="d" type="application/json">{json.dumps(
        {"cons": d["consensus"]}, ensure_ascii=False)}</script>
{plotly_js}
<script>{JS}</script></body></html>"""


def run(do_print: bool = True) -> int:
    d = gather()
    UI.mkdir(parents=True, exist_ok=True)
    OUT_UI.write_text(render(d), encoding="utf-8")
    if do_print:
        print(f"[VRN塔] 共識 {d['n_consensus']} 檔 · 產出索引 "
              f"{len(d['outputs'])} 件 · Dual-Set "
              f"{'Ready' if d['dual_set_ready'] else '冊缺=誠實'} · "
              f"{OUT_UI.name}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    rc = run(do_print=False)
    page = OUT_UI.read_text(encoding="utf-8")
    d = gather()
    chk("① 頁產出 rc0+模板五律(固定 header/footer+可收欄+頁籤)",
        rc == 0 and 'class="app-header"' in page
        and 'class="app-footer"' in page and "railoff" in page
        and 'class="tabs"' in page and "position:fixed" in page)
    chk("② 徽章律(Connection 實測+Dual-Set 冊判+Honesty)",
        'id="conn"' in page and "Dual-Set Cross Validate" in page
        and "Honesty" in page)
    chk("③ 產出索引真掃(≥8 件+誠實計數入頁)",
        len(d["outputs"]) >= 8
        and f'Output Index({len(d["outputs"])})' in page)
    chk("④ 共識真值(庫在=245 級;缺=誠實空不假)",
        (d["n_consensus"] > 100) == ("CNYES" in page.upper())
        or d["n_consensus"] == 0)
    chk("⑤ Plotly 儀表(內嵌或誠實降級)+零 CDN 外鏈",
        ("Plotly.newPlot" in page or "誠實降級" in page)
        and '<script src="http' not in page)
    chk("⑥ Title Case 英文+零網路+加速橋+誠實宣告",
        "Veritas Report Nova" in page and "Output Index" in page
        and "ACCEL-BRIDGE" in src and "誠實" in src
        and all(("import " + k) not in src
                for k in ("requests", "httpx")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== VRN 控制塔儀表板(VRN_ENG079)· 六檢自測(零外網)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
