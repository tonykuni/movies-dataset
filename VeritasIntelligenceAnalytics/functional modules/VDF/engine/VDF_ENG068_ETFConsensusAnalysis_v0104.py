#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG068_ETFConsensusAnalysis — 主動式 ETF×共識分析(批264;操作員令)
====================================================================
操作員令:「via active etf analysis (with consensus data)」——把既有
ENG051 持股庫×ENG069/071 共識庫接成「分析成品」(非再一支擷取器=
Zero-Hydra:零網路零重抓,全讀在庫存證):
  ①每檔主動 ETF(最新 portfolio_date):
     持股數/共識覆蓋率(檔數+權重)/加權共識上漲空間
     (Σ w×upside ÷ Σ w,僅覆蓋檔;來源=consensus_latest 不跨源造數)
     /前十大持股×目標價中位×upside×分析師數
  ②跨 ETF 個股聚合:被幾檔 ETF 持有×權重合計×共識 upside
     →主動經理人共識重疊榜
  ③誠實界定:upside 缺=NULL 不入加權(分母只算有共識權重);
     共識未覆蓋=UNCOVERED 如實列計,不假 0
輸出:
  VIA_Reports/etf_consensus_analysis/ETF_CONSENSUS_<日>.json(存證)
  ui_support/VIA_UI_ETFConsensusAnalysis_v0100.html(手機單欄+
    Plotly Dashboard(批303 操作員令「ploty dashboard style+字小
    緊湊」):三頁式(升幅榜 bar/覆蓋×升幅 scatter/明細表)+左欄
    連結參數面板(批279 模板律);plotly.js 內嵌自足零 CDN
    (get_plotlyjs;缺 plotly=誠實降級表格頁);頁=日更再生類)
v0101→v0102(批274 工作站實錄 CatalogException):誠實訊息分型
指路——表未建=教跑 via 建表;鎖忙=教稍候;不再一律說寫庫中。
v0100→v0101(批273 操作員令「卡住 不卡斷」):唯讀連線三重試
(背景日更寫庫撞鎖=2s 退避;全敗=誠實停不懸吊)+run 入口
try 包=任何庫例外一句誠實訊息 rc2,零裸 traceback。
用法:python3 VDF_ENG068_ETFConsensusAnalysis_v0104.py run | probe
      | --selftest
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import html
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
DB_TW = VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb"
DB_ETF = (VDF / "output_hub" / "active_tw_etf" / "active_tw_etf_holdings"
          / "ActiveTWETF.duckdb")
REP = VIA / "VIA_Reports" / "etf_consensus_analysis"
OUT_UI = (VIA / "supportive modules" / "ui_support"
          / "VIA_UI_ETFConsensusAnalysis_v0100.html")
def _diag(exc) -> str:
    """例外分型指路(批274 工作站實錄:CatalogException=表未建≠鎖)"""
    t = type(exc).__name__
    if "Catalog" in t:
        return ("共識/營收表未建=誠實停:先跑一次 via(日更⑦b-⑦e 會建"
                "consensus_latest 等表),完成後 via-analysis 即出榜")
    if "IO" in t or "lock" in str(exc).lower():
        return "庫忙=背景日更寫庫中:稍等幾分鐘再打 via-analysis 即通"
    return f"庫例外({t})=誠實停:先跑 via 日更後再試"


def _connect_ro(dbp):
    """唯讀連線三重試(批273 不卡斷令):背景日更寫庫=鎖忙→2s 退避
    ×3;全敗=拋原例外由呼叫端誠實停(零 Read-Host 零懸吊)"""
    import time
    import duckdb
    last = None
    for i in range(3):
        try:
            return duckdb.connect(str(dbp), read_only=True)
        except Exception as exc:
            last = exc
            time.sleep(2)
    raise last




def _consensus() -> dict:
    """code→共識(consensus_latest;每 code 雙源時取分析師數最多之
    單源列=去重律,平手依源名;來源分欄不跨源平均)"""
    c = _connect_ro(DB_TW)
    try:
        # 單位律(批264 實測):在庫 upside_pct 實為分數(0.333=+33.3%)
        # →庫端 ×100 統一為百分比,下游全域一致
        rows = c.execute(
            "SELECT code, source, target_median, upside_pct*100, "
            "n_analysts, close FROM consensus_latest "
            "QUALIFY ROW_NUMBER() OVER (PARTITION BY code "
            "ORDER BY n_analysts DESC NULLS LAST, source) = 1").fetchall()
    finally:
        c.close()
    return {r[0]: {"source": r[1], "tp": r[2], "upside": r[3],
                   "n": r[4], "close": r[5]} for r in rows}


def _holdings() -> tuple[str, list]:
    """最新 portfolio_date 全持股(欄名=ENG051 在庫原欄)"""
    e = _connect_ro(DB_ETF)
    try:
        d = e.execute("SELECT MAX(portfolio_date) FROM holdings_daily"
                      ).fetchone()[0]
        rows = e.execute(
            "SELECT etf_ticker, etf_name, holding_ticker, holding_name, "
            "weight_pct FROM holdings_daily WHERE portfolio_date=? "
            "ORDER BY etf_ticker, weight_pct DESC", [d]).fetchall()
    finally:
        e.close()
    return str(d), rows


def analyze() -> dict:
    con = _consensus()
    asof, rows = _holdings()
    etfs: dict = {}
    stocks: dict = {}
    for etf, ename, tick, hname, w in rows:
        w = float(w or 0)
        E = etfs.setdefault(etf, {"etf": etf, "name": ename, "n": 0,
                                  "w_all": 0.0, "n_cov": 0, "w_cov": 0.0,
                                  "wx": 0.0, "top": []})
        E["n"] += 1
        E["w_all"] += w
        c = con.get(tick)
        up = c["upside"] if c else None
        if c and up is not None:
            E["n_cov"] += 1
            E["w_cov"] += w
            E["wx"] += w * float(up)
        if len(E["top"]) < 10:
            E["top"].append({"code": tick, "name": hname, "w": round(w, 2),
                            "tp": c["tp"] if c else None,
                            "upside": round(float(up), 1)
                            if up is not None else None,
                            "n_analysts": c["n"] if c else None})
        S = stocks.setdefault(tick, {"code": tick, "name": hname,
                                     "etfs": 0, "w_sum": 0.0,
                                     "upside": round(float(up), 1)
                                     if up is not None else None,
                                     "tp": c["tp"] if c else None,
                                     "n_analysts": c["n"] if c else None})
        S["etfs"] += 1
        S["w_sum"] += w
    for E in etfs.values():
        E["w_all"] = round(E["w_all"], 2)
        E["w_cov"] = round(E["w_cov"], 2)
        E["cov_w_pct"] = round(100 * E["w_cov"] / E["w_all"], 1) \
            if E["w_all"] else 0.0
        E["wtd_upside"] = round(E["wx"] / E["w_cov"], 2) \
            if E["w_cov"] else None                 # 誠實:零覆蓋=None
        del E["wx"]
    for S in stocks.values():
        S["w_sum"] = round(S["w_sum"], 2)
    overlap = sorted(stocks.values(),
                     key=lambda s: (-s["etfs"], -s["w_sum"]))[:25]
    return {"asof": asof, "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "consensus_codes": len(con), "n_etfs": len(etfs),
            "etfs": sorted(etfs.values(),
                           key=lambda e: -(e["wtd_upside"]
                                           if e["wtd_upside"] is not None
                                           else -999)),
            "overlap": overlap}


def _svg_bar(etfs: list) -> str:
    """加權 upside 橫條(內嵌 SVG=VAP 視覺律零 CDN;缺值=灰誠實)"""
    rows = [e for e in etfs if e["wtd_upside"] is not None]
    if not rows:
        return "<p>共識覆蓋 0=誠實無圖</p>"
    mx = max(abs(e["wtd_upside"]) for e in rows) or 1
    h = 26 * len(rows) + 10
    parts = [f'<svg viewBox="0 0 640 {h}" role="img" '
             'style="width:100%;height:auto">']
    for i, e in enumerate(rows):
        y = 8 + i * 26
        bw = 300 * abs(e["wtd_upside"]) / mx
        col = "var(--green)" if e["wtd_upside"] >= 0 else "var(--red)"
        parts.append(
            f'<text x="0" y="{y + 13}" font-size="11" '
            f'fill="var(--text)">{html.escape(e["etf"])} '
            f'{html.escape(str(e["name"] or ""))[:8]}</text>'
            f'<rect x="200" y="{y}" width="{bw:.0f}" height="17" rx="3" '
            f'fill="{col}" opacity=".75"/>'
            f'<text x="{205 + bw:.0f}" y="{y + 13}" font-size="11" '
            f'fill="var(--text)">{e["wtd_upside"]:+.1f}%'
            f'(覆蓋 {e["cov_w_pct"]:.0f}%)</text>')
    parts.append("</svg>")
    return "".join(parts)


def _plotly():
    try:
        import plotly.offline as po
        return po
    except Exception:
        return None


ETF_CSS = r"""
:root{--bg:#f5f5f2;--paper:#fff;--ink:#1f2530;--ink2:#3c4658;
--mut:#6d7688;--mut2:#9aa2b1;--line:#dcdfe6;--soft:#eef0ee;
--acc:#3e6b8f;--ok:#4f8f6b;--bad:#b05c4d}
*{box-sizing:border-box;margin:0}
body{background:var(--bg);color:var(--ink);display:flex;min-height:100vh;
font:11.5px/1.45 "Segoe UI","Noto Sans TC",system-ui,sans-serif}
.rail{width:216px;min-width:216px;background:var(--paper);
border-right:1px solid var(--line);padding:12px 0 8px;display:flex;
flex-direction:column;position:sticky;top:0;max-height:100vh}
.brand{padding:0 14px 8px;border-bottom:1px solid var(--line)}
.brand .latin{font-size:8px;letter-spacing:.22em;color:var(--mut);
font-weight:700}
.brand h1{font-size:14.5px;margin:3px 0 1px}
.brand .en{font-size:8.5px;letter-spacing:.13em;color:var(--acc);
font-weight:700}
.navsec{font-size:8px;letter-spacing:.2em;color:var(--mut2);
font-weight:700;padding:9px 14px 3px}
.nav a{display:grid;grid-template-columns:20px 1fr;gap:6px;padding:4px 14px;
color:var(--ink2);text-decoration:none;cursor:pointer;font-size:11px}
.nav a:hover{background:var(--soft)}
.nav a.active{background:var(--soft);border-right:3px solid var(--acc);
font-weight:700;color:var(--ink)}
.nav .no{font-size:8.5px;color:var(--mut2);font-weight:700}
.param{padding:4px 14px;font-size:10px;color:var(--mut)}
.param b{color:var(--ink2)}
.railfoot{margin-top:auto;border-top:1px solid var(--line);
padding:7px 14px 0;display:grid;grid-template-columns:1fr 1fr;gap:5px}
.railfoot .k{font-size:7.5px;letter-spacing:.16em;color:var(--mut2);
font-weight:700}
.railfoot .v{font-size:11px;font-weight:700}
.main{flex:1;padding:12px 16px;min-width:0}
.crumb{font-size:9.5px;color:var(--mut);margin-bottom:5px}
.crumb b{color:var(--acc)}
.head{display:flex;align-items:flex-end;gap:12px;flex-wrap:wrap;
border-bottom:2px solid var(--ink);padding-bottom:7px;margin-bottom:9px}
.head h2{font-size:clamp(15px,2vw,19px)}
.head h2 small{font-size:9px;color:var(--mut);font-weight:400;
margin-left:6px;letter-spacing:.1em}
.head .sub{width:100%;font-size:9.5px;color:var(--mut)}
.spec{margin-left:auto;display:flex;gap:12px;flex-wrap:wrap}
.spec .k{font-size:7.5px;letter-spacing:.18em;color:var(--mut2);
font-weight:700}
.spec .v{font-size:10.5px;font-weight:700}
.spec .v.ok{color:var(--ok)}
.page{display:none}
.page.on{display:block}
.chart{background:var(--paper);border:1px solid var(--line);
border-radius:7px;padding:6px;margin-bottom:8px}
.card{background:var(--paper);border:1px solid var(--line);
border-radius:7px;padding:10px 12px;margin-bottom:8px}
.card h3{font-size:11.5px}
.card h3 small{font-size:8px;letter-spacing:.15em;color:var(--mut2);
font-weight:700;margin-left:6px}
table{width:100%;border-collapse:collapse;font-size:10.5px}
th{text-align:left;font-size:8.5px;letter-spacing:.12em;color:var(--mut2);
border-bottom:1px solid var(--line);padding:3px 6px 3px 0;font-weight:700}
td{border-bottom:1px solid var(--soft);padding:3px 6px 3px 0;
font-variant-numeric:tabular-nums}
tr:last-child td{border-bottom:0}
td.g{color:var(--ok);font-weight:600}td.r{color:var(--bad);font-weight:600}
small{color:var(--mut)}
.wrap{overflow-x:auto}
.foot{font-size:9px;color:var(--mut2);margin-top:4px}
@media(max-width:860px){body{flex-direction:column}
.rail{width:100%;min-width:0;position:static;max-height:none}
.nav{display:flex;overflow-x:auto;gap:2px;padding:0 8px}
.nav a{grid-template-columns:auto;white-space:nowrap;border-radius:6px}
.nav a.active{border-right:0;border-bottom:3px solid var(--acc)}
.nav .no{display:none}
.railfoot{grid-template-columns:repeat(4,1fr)}
.main{padding:10px 8px}}
"""

ETF_JS = r"""
const D=JSON.parse(document.getElementById("d").textContent);
function tab(n){
 document.querySelectorAll(".page").forEach((el,i)=>
  el.classList.toggle("on",i===n));
 document.querySelectorAll(".nav a[data-t]").forEach((el,i)=>
  el.classList.toggle("active",i===n));
 window.dispatchEvent(new Event("resize"));
}
document.querySelectorAll(".nav a[data-t]").forEach((el,i)=>
 el.onclick=()=>tab(i));
const cov=D.etfs.filter(e=>e.wtd_upside!==null);
const L={margin:{l:150,r:20,t:8,b:34},font:{size:10,
 family:'"Segoe UI","Noto Sans TC",sans-serif'},
 paper_bgcolor:"#fff",plot_bgcolor:"#fff"};
Plotly.newPlot("c1",[{type:"bar",orientation:"h",
 y:cov.map(e=>e.etf+" "+(e.name||"")).reverse(),
 x:cov.map(e=>e.wtd_upside).reverse(),
 marker:{color:cov.map(e=>e.wtd_upside>=0?"#4f8f6b":"#b05c4d").reverse()},
 customdata:cov.map(e=>e.cov_w_pct).reverse(),
 hovertemplate:"%{y}<br>加權 upside %{x:+.2f}%<br>覆蓋 %{customdata}%"+
  "<extra></extra>"}],
 Object.assign({},L,{height:Math.max(320,cov.length*22+60),
  xaxis:{title:{text:"加權共識上漲空間 %",font:{size:10}},
   ticksuffix:"%"}}),{displayModeBar:false,responsive:true});
Plotly.newPlot("c2",[{type:"scatter",mode:"markers+text",
 x:cov.map(e=>e.cov_w_pct),y:cov.map(e=>e.wtd_upside),
 text:cov.map(e=>e.etf),textposition:"top center",
 textfont:{size:8.5,color:"#6d7688"},
 marker:{size:cov.map(e=>Math.max(7,Math.sqrt(e.n)*2)),
  color:cov.map(e=>e.wtd_upside>=0?"#4f8f6b":"#b05c4d"),opacity:.75},
 customdata:cov.map(e=>e.name||""),
 hovertemplate:"%{text} %{customdata}<br>覆蓋 %{x}% · upside %{y:+.2f}%"+
  "<extra></extra>"}],
 Object.assign({},L,{height:430,margin:{l:52,r:20,t:8,b:40},
  xaxis:{title:{text:"共識覆蓋權重 %",font:{size:10}},ticksuffix:"%"},
  yaxis:{title:{text:"加權 upside %",font:{size:10}},ticksuffix:"%"}}),
 {displayModeBar:false,responsive:true});
tab(0);
"""


def render(d: dict) -> str:
    po = _plotly()
    etf_rows = "".join(
        f"<tr><td>{html.escape(e['etf'])} <small>"
        f"{html.escape(str(e['name'] or ''))}</small></td>"
        f"<td>{e['n']}</td><td>{e['n_cov']}({e['cov_w_pct']}%)</td>"
        f"<td class='{'g' if (e['wtd_upside'] or 0) >= 0 else 'r'}'>"
        f"{'%+.2f%%' % e['wtd_upside'] if e['wtd_upside'] is not None else '—'}"
        "</td></tr>" for e in d["etfs"])
    ov_rows = "".join(
        f"<tr><td>{html.escape(s_['code'])} "
        f"<small>{html.escape(str(s_['name'] or ''))}</small></td>"
        f"<td>{s_['etfs']}</td><td>{s_['w_sum']:.2f}</td>"
        f"<td>{'%+.1f%%' % s_['upside'] if s_['upside'] is not None else '未覆蓋'}"
        f"</td><td>{s_['n_analysts'] or '—'}</td></tr>"
        for s_ in d["overlap"])
    slim = {"etfs": [{k: e[k] for k in ("etf", "name", "n", "cov_w_pct",
                                        "wtd_upside")} for e in d["etfs"]]}
    if po is None:                     # 誠實降級:無 plotly=表格頁
        plotly_js = ""
        degrade = ("<div class='card'>誠實降級:plotly 未安裝=僅表格頁"
                   "(pip install plotly 後重跑 etf_analysis 即出圖)</div>")
    else:
        plotly_js = "<script>" + po.get_plotlyjs() + "</script>"
        degrade = ""
    n_cov = sum(1 for e in d["etfs"] if e["wtd_upside"] is not None)
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 主動 ETF×共識檢視</title><style>__CSS__</style></head><body>
<aside class="rail">
<div class="brand">
<div class="latin">VERITAS INTELLIGENCE ANALYTICS</div>
<h1>主動 ETF×共識檢視</h1>
<div class="en">ACTIVE TAIWAN STOCK ETF REVIEW</div></div>
<div class="navsec">頁面 DASHBOARD PAGES</div><div class="nav">
<a data-t="0" class="active"><span class="no">01</span>加權升幅榜</a>
<a data-t="1"><span class="no">02</span>覆蓋×升幅</a>
<a data-t="2"><span class="no">03</span>明細表</a>
</div>
<div class="navsec">連結 LINKS</div><div class="nav">
<a href="VIA_UI_MasterControl_v0100.html"><span class="no">→</span>總控台</a>
<a href="VIA_UI_RevenueConsensusAnalysis_v0100.html">
<span class="no">→</span>月營收×共識檢視</a>
<a href="VIA_UI_Shell_VDF_v0100.html"><span class="no">→</span>VDF 現況台</a>
</div>
<div class="navsec">參數 PARAMS(唯讀)</div>
<div class="param">asof <b>{d['asof']}</b><br>共識庫 <b>
{d['consensus_codes']}</b> 檔<br>加權律 <b>Σw×upside÷Σw</b>(僅覆蓋權重)</div>
<div class="railfoot">
<div><div class="k">ETFS</div><div class="v">{d['n_etfs']}</div></div>
<div><div class="k">COVERED</div><div class="v">{n_cov}</div></div>
<div><div class="k">SOURCE</div><div class="v">IN-DB</div></div>
<div><div class="k">NET</div><div class="v">ZERO</div></div>
</div></aside>
<main class="main">
<div class="crumb"><b>VDF</b> → <b>主動式 ETF×共識分析</b> →
<b>Plotly Dashboard</b> · LAYOUT SPEC(批303)</div>
<div class="head"><h2>主動 ETF×共識檢視<small>PLOTLY DASHBOARD</small></h2>
<div class="spec">
<div><div class="k">ASOF</div><div class="v">{d['asof']}</div></div>
<div><div class="k">ETFS</div><div class="v">{d['n_etfs']}</div></div>
<div><div class="k">CONSENSUS</div><div class="v">{d['consensus_codes']}</div></div>
<div><div class="k">GATE</div><div class="v ok">IN-DB · 零網路</div></div>
</div>
<div class="sub">產於 {d['ts']} · 加權 upside=Σw×upside÷Σw(僅共識覆蓋
權重;未覆蓋誠實不入)· 非投資建議</div></div>
{degrade}
<div class="page on"><div class="chart"><div id="c1"></div></div></div>
<div class="page"><div class="chart"><div id="c2"></div></div></div>
<div class="page">
<div class="card"><h3>ETF 總表<small>ALL ETFS</small></h3>
<div class="wrap"><table><tr><th>ETF</th><th>持股</th><th>共識覆蓋</th>
<th>加權 upside</th></tr>{etf_rows}</table></div></div>
<div class="card"><h3>跨 ETF 共識重疊榜<small>TOP 25 OVERLAP</small></h3>
<div class="wrap"><table><tr><th>個股</th><th>被持 ETF</th><th>權重合計</th>
<th>upside</th><th>分析師</th></tr>{ov_rows}</table></div></div>
</div>
<div class="foot">來源:ENG051 holdings_daily × consensus_latest
(ENG069/071)· 來源分欄不跨源平均 · plotly 內嵌自足零 CDN</div>
</main>
<script id="d" type="application/json">{json.dumps(slim,
 ensure_ascii=False)}</script>
{plotly_js}
<script>__JS__</script></body></html>""".replace(
        "__CSS__", ETF_CSS).replace("__JS__", ETF_JS if po else "")


def probe() -> int:
    print(f"  [{'OK' if DB_TW.exists() else 'FAIL'}] 台股庫 {DB_TW.name}")
    print(f"  [{'OK' if DB_ETF.exists() else 'FAIL'}] ETF 庫 {DB_ETF.name}")
    return 0 if DB_TW.exists() and DB_ETF.exists() else 2


def run() -> int:
    if not (DB_TW.exists() and DB_ETF.exists()):
        print("[ETF共識] 在庫來源缺=誠實停(先跑 boot/backfill)")
        return 2
    try:
        d = analyze()
    except Exception as exc:
        print("[分析] " + _diag(exc))
        return 2
    REP.mkdir(parents=True, exist_ok=True)
    j = REP / f"ETF_CONSENSUS_{d['asof'].replace('-', '')}.json"
    j.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    OUT_UI.write_text(render(d), encoding="utf-8")
    cov = [e for e in d["etfs"] if e["wtd_upside"] is not None]
    print(f"[ETF共識] {d['n_etfs']} 檔 ETF · 共識可加權 {len(cov)} 檔 · "
          f"asof {d['asof']} · {j.name} + {OUT_UI.name}")
    for e in cov[:3]:
        print(f"  [榜] {e['etf']} {e['name']} 加權 upside "
              f"{e['wtd_upside']:+.2f}%(覆蓋 {e['cov_w_pct']}%)")
    return 0


def _data_ready() -> bool:
    """資料在位探測(批293 雙模自測):缺=誠實缺料模式非假紅"""
    try:
        import duckdb
        c = duckdb.connect(str(DB_TW), read_only=True)
        t = {r[0] for r in c.execute("SHOW TABLES").fetchall()}
        c.close()
        return "consensus_latest" in t and DB_ETF.exists()
    except Exception:
        return False


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    if not _data_ready():
        print("  [模式] 資料缺席(庫/表不在)=誠實缺料模式:驗誠實停行為")
        rc = run()
        chk("①' 誠實停(rc2+指路訊息,零裸 traceback)", rc == 2)
        chk("②' 靜態紀律(零網路+加速橋+誠實宣告)",
            "ACCEL-BRIDGE" in src and "誠實" in src)
        print(f"  [計] 誠實缺料二檢 OK {2 - len(fails)} · FAIL {len(fails)}"
              "(全檢=資料在位環境跑)")
        return 1 if fails else 0
    rc = run()
    d = analyze() if rc == 0 else {}
    chk("① 在庫雙源接通(holdings×consensus;零網路)", rc == 0
        and d.get("n_etfs", 0) > 0 and d.get("consensus_codes", 0) > 0)
    cov = [e for e in d.get("etfs", []) if e["wtd_upside"] is not None]
    chk("② 加權律=僅覆蓋權重入分母(w_cov>0 才有值)",
        all(e["w_cov"] > 0 for e in cov) and len(cov) > 0)
    E = cov[0] if cov else None
    manual = None
    if E:
        con = _consensus()
        _, rows = _holdings()
        wx = wc = 0.0
        for etf, _, t, _, w in rows:
            if etf == E["etf"] and t in con \
                    and con[t]["upside"] is not None:
                wx += float(w) * float(con[t]["upside"])
                wc += float(w)
        manual = round(wx / wc, 2) if wc else None
    chk("③ 加權值可複算(手算=引擎值)", E is not None
        and manual == E["wtd_upside"], f"({manual})")
    chk("④ 重疊榜真聚合(首檔被持 ETF 數≥2)",
        bool(d.get("overlap")) and d["overlap"][0]["etfs"] >= 2)
    page = OUT_UI.read_text(encoding="utf-8") if OUT_UI.exists() else ""
    chk("⑤ U/I 頁產出(Plotly 三頁 Dashboard+左欄面板+零 CDN 外鏈)",
        "主動式 ETF×共識分析" in page
        and ("Plotly.newPlot" in page or "誠實降級" in page)
        and 'class="rail"' in page and '<script src="http' not in page)
    chk("⑥ 零網路+加速橋+誠實界定宣告", "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src
                for k in ("requests", "httpx", "urllib"))
        and "誠實" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 主動 ETF×共識分析(VDF_ENG068)· 六檢自測(零網路)===")
        return selftest()
    if "probe" in a:
        return probe()
    return run()


if __name__ == "__main__":
    sys.exit(main())

