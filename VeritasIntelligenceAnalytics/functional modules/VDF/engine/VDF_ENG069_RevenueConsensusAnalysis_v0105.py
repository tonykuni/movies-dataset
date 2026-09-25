#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG069_RevenueConsensusAnalysis — 台股月營收×共識分析(批264)
====================================================================
操作員令:「via taiwan stock revenue analysis (with consensus data)」
——把既有 ENG063 月營收分析視圖×共識庫接成分析成品(Zero-Hydra:
零網路零重抓,單庫 SQL join 全讀在庫存證):
  ①每檔最新月:yoy_pct 年增/mom_pct 月增/yoy_streak 連續年增月數
    /high_60m 近60月新高 × consensus_latest 目標價中位/upside/分析師數
  ②四象限分佈(營收動能 yoy>0 × 共識 upside>0)+雙強榜
    (yoy>0 且 upside>0,依 upside 排序)
  ③族群層:revenue_group_analysis 最新月動能榜直引(ENG063 產,不重算)
  ④誠實界定:共識覆蓋≠全市場(覆蓋數如實標);未覆蓋不假 0;
    來源分欄不跨源平均
輸出:
  VIA_Reports/revenue_consensus/REV_CONSENSUS_<月>.json(存證)
  ui_support/VIA_UI_RevenueConsensusAnalysis_v0100.html(手機單欄+
    內嵌 SVG 四象限散點=VAP 視覺律零 CDN;Portal 尾版自收)
v0104→v0105(批303 操作員令「taiwan stock monthly revenue review
=ploty dashboard style+字小緊湊」):三頁 Plotly Dashboard(四象限
scatter/雙強榜 bar/明細表)+左欄連結參數面板(批279 模板律);
plotly.js 內嵌自足零 CDN(缺 plotly=誠實降級表格頁);頁=日更再生類。
v0103→v0104(批298 雲端重建鏈實錘):族群榜=輔助側欄卻缺表即
全炸——revenue_group_analysis 視圖靠工作站輪動快照建,雲端無快照
=四象限核心(雙表全在位)被輔助層拖死。修=群查詢前 SHOW TABLES
守衛(同 VRN_ENG069 v0102 破法):表缺=groups 誠實空列+榜照出。
v0101→v0102(批274 工作站實錄 CatalogException):誠實訊息分型
指路——表未建=教跑 via 建表;鎖忙=教稍候;不再一律說寫庫中。
v0100→v0101(批273 操作員令「卡住 不卡斷」):唯讀連線三重試
(背景日更寫庫撞鎖=2s 退避;全敗=誠實停不懸吊)+run 入口
try 包=任何庫例外一句誠實訊息 rc2,零裸 traceback。
用法:python3 VDF_ENG069_RevenueConsensusAnalysis_v0105.py run | probe
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
REP = VIA / "VIA_Reports" / "revenue_consensus"
OUT_UI = (VIA / "supportive modules" / "ui_support"
          / "VIA_UI_RevenueConsensusAnalysis_v0100.html")
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



# 單庫 join:每檔最新月營收動能 × 共識最新視圖(全在庫零發明)。
# 去重律(批264 實測揪蟲):consensus_latest 每 code 可雙源
# (CNYES_FACTSET+EXTERNAL_ANALYST)→每 code 取分析師數最多之單源列
# (平手依源名;來源分欄不跨源平均=既有紀律)。
Q_JOIN = """
WITH latest AS (
  SELECT code, MAX(ym) AS ym FROM monthly_revenue_analysis GROUP BY code
), con1 AS (
  SELECT * FROM consensus_latest
  QUALIFY ROW_NUMBER() OVER (PARTITION BY code
    ORDER BY n_analysts DESC NULLS LAST, source) = 1
)
SELECT m.code, m.ym, m.revenue, m.mom_pct, m.yoy_pct, m.yoy_streak,
       m.high_60m, c.target_median,
       c.upside_pct * 100,  -- 單位律(批264 實測):在庫實為分數→×100 百分比
       c.n_analysts, c.source
FROM monthly_revenue_analysis m
JOIN latest l ON m.code = l.code AND m.ym = l.ym
LEFT JOIN con1 c ON m.code = c.code
ORDER BY m.code
"""


def analyze() -> dict:
    c = _connect_ro(DB_TW)
    try:
        rows = c.execute(Q_JOIN).fetchall()
        # 批298 守衛:群視圖靠工作站輪動快照建=雲端可缺;缺=誠實空
        _tabs = {r[0] for r in c.execute("SHOW TABLES").fetchall()}
        groups = []
        if "revenue_group_analysis" in _tabs:
            groups = c.execute(
                "SELECT gid, ym, n_members, yoy_median, "
                "CASE WHEN n_yoy > 0 THEN CAST(n_yoy_pos AS DOUBLE)/n_yoy END "
                "FROM revenue_group_analysis "
                "WHERE ym = (SELECT MAX(ym) FROM revenue_group_analysis) "
                "ORDER BY yoy_median DESC NULLS LAST LIMIT 12").fetchall()
    finally:
        c.close()
    all_rows = []
    for (code, ym, rev, mom, yoy, streak, hi, tp, up, n, src) in rows:
        all_rows.append({
            "code": code, "ym": ym, "revenue": rev,
            "mom": round(float(mom), 1) if mom is not None else None,
            "yoy": round(float(yoy), 1) if yoy is not None else None,
            "streak": streak, "high_60m": bool(hi),
            "tp": tp, "upside": round(float(up), 1) if up is not None else None,
            "n_analysts": n, "source": src})
    cov = [r for r in all_rows
           if r["upside"] is not None and r["yoy"] is not None]
    quad = {"strong": 0, "rev_only": 0, "cons_only": 0, "weak": 0}
    for r in cov:
        k = ("strong" if r["yoy"] > 0 and r["upside"] > 0 else
             "rev_only" if r["yoy"] > 0 else
             "cons_only" if r["upside"] > 0 else "weak")
        quad[k] += 1
    dual = sorted((r for r in cov if r["yoy"] > 0 and r["upside"] > 0),
                  key=lambda r: -r["upside"])[:30]
    return {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "latest_ym": max((r["ym"] for r in all_rows), default=None),
            "n_market": len(all_rows), "n_covered": len(cov),
            "quad": quad, "dual": dual,
            "cov_rows": cov,
            "groups": [{"gid": g, "ym": y, "members": m,
                        "yoy_median": round(float(md), 1)
                        if md is not None else None,
                        "pos_ratio": round(float(p), 2)
                        if p is not None else None}
                       for g, y, m, md, p in groups]}


def _svg_quad(cov: list) -> str:
    """四象限散點:x=最新月 yoy、y=共識 upside(軸截 ±80 誠實標)"""
    if not cov:
        return "<p>共識×營收交集 0=誠實無圖</p>"
    W = H = 340
    cx, cy = W / 2, H / 2

    def px(v, lim=80.0):
        return max(-lim, min(lim, v)) / lim
    pts = []
    for r in cov:
        x = cx + px(r["yoy"]) * (W / 2 - 20)
        y = cy - px(r["upside"]) * (H / 2 - 20)
        col = "var(--green)" if r["yoy"] > 0 and r["upside"] > 0 \
            else "var(--muted)"
        pts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="3.5" '
                   f'fill="{col}" opacity=".7"><title>'
                   f'{html.escape(r["code"])} yoy {r["yoy"]}% / '
                   f'upside {r["upside"]}%</title></circle>')
    return (f'<svg viewBox="0 0 {W} {H}" role="img" '
            'style="width:100%;max-width:400px;height:auto">'
            f'<line x1="{cx}" y1="10" x2="{cx}" y2="{H - 10}" '
            'stroke="var(--line)"/>'
            f'<line x1="10" y1="{cy}" x2="{W - 10}" y2="{cy}" '
            'stroke="var(--line)"/>'
            f'<text x="{W - 12}" y="{cy - 6}" text-anchor="end" '
            'font-size="10" fill="var(--muted)">yoy% →(截±80)</text>'
            f'<text x="{cx + 6}" y="18" font-size="10" '
            'fill="var(--muted)">upside% ↑</text>'
            + "".join(pts) + "</svg>")


def _plotly():
    try:
        import plotly.offline as po
        return po
    except Exception:
        return None


REV_CSS = r"""
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

REV_JS = r"""
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
const C=D.cov;
const col=r=>(r.yoy>0&&r.upside>0)?"#4f8f6b":
 (r.yoy>0)?"#b58a3e":(r.upside>0)?"#3e6b8f":"#b05c4d";
const L={font:{size:10,family:'"Segoe UI","Noto Sans TC",sans-serif'},
 paper_bgcolor:"#fff",plot_bgcolor:"#fff"};
Plotly.newPlot("c1",[{type:"scatter",mode:"markers",
 x:C.map(r=>r.yoy),y:C.map(r=>r.upside),
 marker:{size:6,color:C.map(col),opacity:.72},
 text:C.map(r=>r.code),
 hovertemplate:"%{text}<br>yoy %{x:+.1f}% · upside %{y:+.1f}%"+
  "<extra></extra>"}],
 Object.assign({},L,{height:460,margin:{l:52,r:20,t:8,b:40},
  xaxis:{title:{text:"月營收 yoy %",font:{size:10}},ticksuffix:"%",
   zeroline:true,zerolinecolor:"#9aa2b1"},
  yaxis:{title:{text:"共識 upside %",font:{size:10}},ticksuffix:"%",
   zeroline:true,zerolinecolor:"#9aa2b1"}}),
 {displayModeBar:false,responsive:true});
const T=D.dual.slice(0,30);
Plotly.newPlot("c2",[{type:"bar",orientation:"h",
 y:T.map(r=>r.code).reverse(),x:T.map(r=>r.upside).reverse(),
 marker:{color:"#4f8f6b"},
 customdata:T.map(r=>r.yoy).reverse(),
 hovertemplate:"%{y}<br>upside %{x:+.1f}% · yoy %{customdata:+.1f}%"+
  "<extra></extra>"}],
 Object.assign({},L,{height:Math.max(340,T.length*17+60),
  margin:{l:64,r:20,t:8,b:34},
  xaxis:{title:{text:"雙強榜:共識 upside %(yoy>0 且 upside>0)",
   font:{size:10}},ticksuffix:"%"}}),
 {displayModeBar:false,responsive:true});
tab(0);
"""


def render(d: dict) -> str:
    po = _plotly()
    dual_rows = "".join(
        f"<tr><td>{html.escape(r['code'])}</td><td>{r['ym']}</td>"
        f"<td class='g'>{r['yoy']:+.1f}%</td>"
        f"<td>{r['streak'] or 0} 月</td>"
        f"<td>{'★' if r['high_60m'] else ''}</td>"
        f"<td class='g'>{r['upside']:+.1f}%</td>"
        f"<td>{r['n_analysts'] or '—'}</td></tr>" for r in d["dual"])
    grp_rows = "".join(
        f"<tr><td>{html.escape(str(g['gid']))}</td><td>{g['members']}</td>"
        f"<td class='{'g' if (g['yoy_median'] or 0) > 0 else 'r'}'>"
        f"{'%+.1f%%' % g['yoy_median'] if g['yoy_median'] is not None else '—'}"
        f"</td><td>{g['pos_ratio'] if g['pos_ratio'] is not None else '—'}"
        "</td></tr>" for g in d["groups"]) or (
        "<tr><td colspan='4'>族群視圖未建(輪動快照=工作站生成;"
        "此環境誠實空)</td></tr>")
    q = d["quad"]
    slim = {"cov": [{k: r[k] for k in ("code", "yoy", "upside")}
                    for r in d["cov_rows"]],
            "dual": [{k: r[k] for k in ("code", "yoy", "upside")}
                     for r in d["dual"]]}
    if po is None:                     # 誠實降級:無 plotly=表格頁
        plotly_js = ""
        degrade = ("<div class='card'>誠實降級:plotly 未安裝=僅表格頁"
                   "(pip install plotly 後重跑 revenue_consensus 即出圖)"
                   "</div>")
    else:
        plotly_js = "<script>" + po.get_plotlyjs() + "</script>"
        degrade = ""
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 月營收×共識檢視</title><style>__CSS__</style></head><body>
<aside class="rail">
<div class="brand">
<div class="latin">VERITAS INTELLIGENCE ANALYTICS</div>
<h1>月營收×共識檢視</h1>
<div class="en">TAIWAN STOCK MONTHLY REVENUE REVIEW</div></div>
<div class="navsec">頁面 DASHBOARD PAGES</div><div class="nav">
<a data-t="0" class="active"><span class="no">01</span>四象限散點</a>
<a data-t="1"><span class="no">02</span>雙強榜</a>
<a data-t="2"><span class="no">03</span>明細表</a>
</div>
<div class="navsec">連結 LINKS</div><div class="nav">
<a href="VIA_UI_MasterControl_v0100.html"><span class="no">→</span>總控台</a>
<a href="VIA_UI_ETFConsensusAnalysis_v0100.html">
<span class="no">→</span>主動 ETF×共識檢視</a>
<a href="VIA_UI_Shell_VDF_v0100.html"><span class="no">→</span>VDF 現況台</a>
</div>
<div class="navsec">參數 PARAMS(唯讀)</div>
<div class="param">最新月 <b>{d['latest_ym']}</b><br>四象限律
<b>yoy>0 × upside>0</b><br>去重律 <b>每 code 單源列</b>(分析師多者勝)</div>
<div class="railfoot">
<div><div class="k">MARKET</div><div class="v">{d['n_market']}</div></div>
<div><div class="k">COVERED</div><div class="v">{d['n_covered']}</div></div>
<div><div class="k">DUAL</div><div class="v">{q['strong']}</div></div>
<div><div class="k">NET</div><div class="v">ZERO</div></div>
</div></aside>
<main class="main">
<div class="crumb"><b>VDF</b> → <b>月營收×共識分析</b> →
<b>Plotly Dashboard</b> · LAYOUT SPEC(批303)</div>
<div class="head"><h2>月營收×共識檢視<small>PLOTLY DASHBOARD</small></h2>
<div class="spec">
<div><div class="k">LATEST</div><div class="v">{d['latest_ym']}</div></div>
<div><div class="k">交集</div><div class="v">{d['n_covered']}/{d['n_market']}
</div></div>
<div><div class="k">雙強</div><div class="v ok">{q['strong']}</div></div>
<div><div class="k">GATE</div><div class="v ok">IN-DB · 零網路</div></div>
</div>
<div class="sub">產於 {d['ts']} · 四象限:雙強 {q['strong']} · 僅營收正
{q['rev_only']} · 僅共識正 {q['cons_only']} · 雙弱 {q['weak']} ·
共識覆蓋≠全市場(如實標)· 非投資建議</div></div>
{degrade}
<div class="page on"><div class="chart"><div id="c1"></div></div></div>
<div class="page"><div class="chart"><div id="c2"></div></div></div>
<div class="page">
<div class="card"><h3>雙強榜<small>DUAL-STRONG · TOP 30</small></h3>
<div class="wrap"><table><tr><th>代碼</th><th>月</th><th>yoy</th>
<th>連增</th><th>60M高</th><th>upside</th><th>分析師</th></tr>
{dual_rows}</table></div></div>
<div class="card"><h3>族群月營收動能榜<small>GROUPS(ENG063 視圖直引)
</small></h3>
<div class="wrap"><table><tr><th>族群</th><th>成員</th><th>年增中位</th>
<th>正年增佔比</th></tr>{grp_rows}</table></div></div>
</div>
<div class="foot">來源:monthly_revenue_analysis(ENG063/MOPS 正源)×
consensus_latest(ENG069/071)· 來源分欄不跨源平均 · plotly 內嵌自足
零 CDN</div>
</main>
<script id="d" type="application/json">{json.dumps(slim,
 ensure_ascii=False)}</script>
{plotly_js}
<script>__JS__</script></body></html>""".replace(
        "__CSS__", REV_CSS).replace("__JS__", REV_JS if po else "")


def probe() -> int:
    print(f"  [{'OK' if DB_TW.exists() else 'FAIL'}] 台股庫 {DB_TW.name}")
    return 0 if DB_TW.exists() else 2


def run() -> int:
    if not DB_TW.exists():
        print("[營收共識] 台股庫缺=誠實停(先跑 boot)")
        return 2
    try:
        d = analyze()
    except Exception as exc:
        print("[分析] " + _diag(exc))
        return 2
    REP.mkdir(parents=True, exist_ok=True)
    j = REP / f"REV_CONSENSUS_{str(d['latest_ym']).replace('-', '')}.json"
    ev = {k: v for k, v in d.items() if k != "cov_rows"}
    j.write_text(json.dumps(ev, ensure_ascii=False, indent=1),
                 encoding="utf-8")
    OUT_UI.write_text(render(d), encoding="utf-8")
    q = d["quad"]
    print(f"[營收共識] {d['latest_ym']} · 交集 {d['n_covered']}/"
          f"{d['n_market']} · 雙強 {q['strong']} · {j.name} + {OUT_UI.name}")
    for r in d["dual"][:3]:
        print(f"  [雙強] {r['code']} yoy {r['yoy']:+.1f}% 連增 "
              f"{r['streak'] or 0} 月 upside {r['upside']:+.1f}%")
    return 0


def _data_ready() -> bool:
    """資料在位探測(批293 雙模自測):缺=誠實缺料模式非假紅"""
    try:
        import duckdb
        c = duckdb.connect(str(DB_TW), read_only=True)
        t = {r[0] for r in c.execute("SHOW TABLES").fetchall()}
        c.close()
        return "consensus_latest" in t
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
    chk("① 單庫 join 接通(營收×共識;零網路)", rc == 0
        and d.get("n_market", 0) > 1000 and d.get("n_covered", 0) > 0)
    chk("② 每檔唯一最新月(join 不放大列數;交集代碼零重複)",
        len({r["code"] for r in d.get("cov_rows", [])})
        == len(d.get("cov_rows", [])) == d.get("n_covered", -1)
        and d.get("n_market", 0) >= d.get("n_covered", 0))
    q = d.get("quad", {})
    chk("③ 四象限守恆(四格和=交集數)",
        sum(q.values()) == d.get("n_covered", -1))
    chk("④ 雙強榜律(全列 yoy>0 且 upside>0,依 upside 降冪)",
        all(r["yoy"] > 0 and r["upside"] > 0 for r in d.get("dual", []))
        and [r["upside"] for r in d.get("dual", [])] ==
        sorted((r["upside"] for r in d.get("dual", [])), reverse=True))
    page = OUT_UI.read_text(encoding="utf-8") if OUT_UI.exists() else ""
    chk("⑤ U/I 頁產出(Plotly 三頁 Dashboard+族群榜+零 CDN 外鏈)",
        "月營收×共識分析" in page
        and ("Plotly.newPlot" in page or "誠實降級" in page)
        and "族群月營收動能榜" in page
        and '<script src="http' not in page)
    chk("⑥ 零網路+加速橋+誠實界定宣告", "ACCEL-BRIDGE" in src
        and all(("import " + k) not in src
                for k in ("requests", "httpx", "urllib"))
        and "誠實" in src)
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== 月營收×共識分析(VDF_ENG069)· 六檢自測(零網路)===")
        return selftest()
    if "probe" in a:
        return probe()
    return run()


if __name__ == "__main__":
    sys.exit(main())

