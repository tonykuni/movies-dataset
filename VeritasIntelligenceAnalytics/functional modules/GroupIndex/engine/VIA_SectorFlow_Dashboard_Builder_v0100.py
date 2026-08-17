# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_SectorFlow_Dashboard_Builder_v0100.py

ALL-IN-ONE 多分頁儀表板產生器:讀取 SectorFlow v0100 + TradeBacktest v0100
的 evidence 實跑輸出,生成單一自足 HTML(JSON-DRIVEN,零外部資產依賴)。

分頁:總覽 / 鏈接指數 / 資金位移 / 輪動象限 / 交易回測 / 治理矩陣。

設計規範(dataviz 六檢通過):
- 漲跌極性對:上漲 #c9584a(紅)/ 下跌 #1f9e9e(青綠;台股慣例紅漲綠跌,
  青綠對紅在色覺障礙下 ΔE 11.8 可分,且方向/位置為第二編碼)。
- 四路資金 categorical(固定順序,不循環):外資 #3b6fc4 / 自營 #b57f1f
  / 投信 #0f9678 / 主力 #8f56c8(全六檢 PASS;堆疊段間 2px 留白)。
- 單軸原則:價量分層不共軸;每日資金與累積資金分列上下兩板。
- 資料皆來自受控 DGP 實跑 evidence,非實盤;右上常駐標示。
"""
from __future__ import annotations

from pathlib import Path
import datetime as dt
import json
import sys

import numpy as np
import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
RUN_MAIN = MODULE_DIR / "evidence" / "RUN_SECTORFLOW_V0100"
RUN_TRADE = MODULE_DIR / "evidence" / "RUN_SECTORFLOW_TRADE_V0100"
DEFAULT_OUT = MODULE_DIR.parent.parent / "VIA_Reports" / "VIA_SectorFlow_AllInOne_Dashboard_v0100.html"

VERSION = "0.1.00"
FLOW_TAIL_DAYS = 90     # 嵌入近 N 日資金流(控制檔案大小)
HEATMAP_DAYS = 40
RRG_TRAIL = 5


def r2(x) -> float:
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), 2)


def r4(x) -> float:
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else round(float(x), 4)


def def_build_payload() -> dict:
    chained = pd.read_csv(RUN_MAIN / "sector_chained_index_daily.csv", parse_dates=["Date"])
    flows = pd.read_csv(RUN_MAIN / "sector_flow_daily.csv", parse_dates=["Date"])
    backtest = pd.read_csv(RUN_MAIN / "backtest_summary.csv")
    reviews = pd.read_csv(RUN_MAIN / "review_roles.csv", parse_dates=["ReviewDate"])
    tests_f = pd.read_csv(RUN_MAIN / "test_validation_ledger.csv")
    phases_f = pd.read_csv(RUN_MAIN / "pipeline_phase_ledger.csv")
    repairs = pd.read_csv(RUN_MAIN / "repair_ledger.csv")
    summary_f = json.loads((RUN_MAIN / "run_summary.json").read_text("utf-8"))
    trade_bt = pd.read_csv(RUN_TRADE / "trade_backtest_summary.csv")
    trade_ledger = pd.read_csv(RUN_TRADE / "trade_ledger_main.csv", parse_dates=["EntryDate", "ExitDate"])
    equity = pd.read_csv(RUN_TRADE / "portfolio_equity_main.csv", parse_dates=["Date"])
    tests_b = pd.read_csv(RUN_TRADE / "trade_test_ledger.csv")
    summary_t = json.loads((RUN_TRADE / "trade_run_summary.json").read_text("utf-8"))

    groups = sorted(chained["Group"].unique().tolist())
    idx_dates = sorted(chained["Date"].unique().tolist())
    date_str = [d.strftime("%y-%m-%d") for d in idx_dates]

    # ---- 指數分頁:每群鏈接指數 + 實質成交額(億) ----
    flows_idx = flows.set_index(["Group", "Date"])
    index_map = {}
    for g in groups:
        sub = chained[chained["Group"] == g].sort_values("Date")
        turn = []
        smart = []
        for d in sub["Date"]:
            try:
                turn.append(r2(flows_idx.loc[(g, d), "GroupRealTurnover"] / 1e8))
                smart.append(r2(flows_idx.loc[(g, d), "SmartMoneyNet"] / 1e8))
            except KeyError:
                turn.append(None)
                smart.append(None)
        index_map[g] = {
            "px": [r2(v) for v in sub["ChainedIndex"]],
            "ret": [r4(v) for v in sub["BasketRet"]],
            "turn": turn,
            "flow": smart,
            "n": [int(v) for v in sub["ActiveCount"]],
        }

    # ---- 資金位移分頁:近 N 日四路資金 + 熱力圖矩陣 ----
    flow_dates = sorted(flows["Date"].unique().tolist())[-FLOW_TAIL_DAYS:]
    fset = flows[flows["Date"].isin(flow_dates)].sort_values(["Group", "Date"])
    flow_date_str = [d.strftime("%m-%d") for d in flow_dates]
    flow_map = {}
    for g in groups:
        sub = fset[fset["Group"] == g].set_index("Date").reindex(flow_dates)
        flow_map[g] = {
            "foreign": [r2(v / 1e8) if np.isfinite(v) else None for v in sub["ForeignNet"]],
            "dealer": [r2(v / 1e8) if np.isfinite(v) else None for v in sub["DealerNet"]],
            "trust": [r2(v / 1e8) if np.isfinite(v) else None for v in sub["TrustNet"]],
            "whale": [r2(v / 1e8) if np.isfinite(v) else None for v in sub["WhaleNet"]],
            "smart": [r2(v / 1e8) if np.isfinite(v) else None for v in sub["SmartMoneyNet"]],
            "velocity": [r4(v) for v in sub["CapitalVelocity3D"]],
            "state": [str(v) if isinstance(v, str) else "" for v in sub["MigrationState"]],
            "signal": [str(v) if isinstance(v, str) else "" for v in sub["StrategySignal"]],
        }
    heat_dates = flow_dates[-HEATMAP_DAYS:]
    heat = {
        "dates": [d.strftime("%m-%d") for d in heat_dates],
        "rows": [
            {"g": g, "v": [r4(v) for v in fset[(fset["Group"] == g) & (fset["Date"].isin(heat_dates))].sort_values("Date")["CapitalVelocity3D"]]}
            for g in groups
        ],
    }

    # ---- 輪動象限 RRG:FlowMom = InstPurityZ 橫截面 z;PriceMom = 20D 指數報酬橫截面 z ----
    rrg_trail_dates = sorted(flows["Date"].unique().tolist())[-RRG_TRAIL:]
    ret20 = {}
    for g in groups:
        sub = chained[chained["Group"] == g].sort_values("Date")
        px = sub["ChainedIndex"].to_numpy()
        dmap = dict(zip(sub["Date"], range(len(px))))
        ret20[g] = {d: (px[i] / px[max(0, i - 20)] - 1.0) for d, i in dmap.items()}
    rrg = []
    for g in groups:
        trail = []
        for d in rrg_trail_dates:
            day = flows[(flows["Date"] == d)]
            row = day[day["Group"] == g]
            if row.empty:
                continue
            fvals = day["InstPurityZ"].to_numpy(dtype=float)
            f_mu, f_sd = np.nanmean(fvals), np.nanstd(fvals) + 1e-9
            pv = np.array([ret20[gg].get(d, np.nan) for gg in groups], dtype=float)
            p_mu, p_sd = np.nanmean(pv), np.nanstd(pv) + 1e-9
            fz = (float(row["InstPurityZ"].iloc[0]) - f_mu) / f_sd
            pz = (ret20[g].get(d, np.nan) - p_mu) / p_sd
            if np.isfinite(fz) and np.isfinite(pz):
                trail.append([r2(np.clip(fz, -3, 3)), r2(np.clip(pz, -3, 3))])
        if trail:
            last_state = flow_map[g]["state"][-1] if flow_map[g]["state"] else ""
            rrg.append({"g": g, "trail": trail, "state": last_state})

    # ---- 交易回測分頁 ----
    bh_daily = chained.groupby("Date", as_index=False).agg(Ret=("BasketRet", "mean")).sort_values("Date")
    bh_equity = (1.0 + bh_daily["Ret"]).cumprod()
    eq_dates = [d.strftime("%y-%m-%d") for d in equity["Date"]]
    trades_rows = [
        {
            "g": t["Group"], "in": t["EntryDate"].strftime("%y-%m-%d"), "out": t["ExitDate"].strftime("%y-%m-%d"),
            "ret": r4(t["NetReturn"]), "why": t["ExitReason"],
        }
        for _, t in trade_ledger.sort_values("EntryDate").iterrows()
    ]

    # ---- 治理分頁 ----
    def ledger_rows(df: pd.DataFrame) -> list:
        return [
            {"id": r["TestID"], "name": r["TestName"], "status": r["Status"],
             "sev": r["Severity"], "ev": str(r["Evidence"])[:220]}
            for _, r in df.iterrows()
        ]

    latest_reviews = reviews.sort_values("ReviewDate").drop_duplicates("Ticker", keep="last")
    role_matrix = []
    for g in groups:
        sub = latest_reviews[latest_reviews["Group"] == g]
        vc = sub["Role"].value_counts().to_dict()
        role_matrix.append({
            "g": g, "L": int(vc.get("LEADER", 0)), "P": int(vc.get("PEER", 0)),
            "M": int(vc.get("MEMBER", 0)), "G": int(vc.get("LAGGARD", 0)),
            "F": int(vc.get("FALLBACK_ALL", 0)),
        })

    return {
        "meta": {
            "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "gate": summary_f.get("FinalGate", ""),
            "hard": summary_f.get("HardFailures", ""),
            "warn": summary_f.get("ReviewWarnings", ""),
            "tradeStatus": summary_t.get("Status", ""),
            "engineF": f"{summary_f.get('Engine')} v{summary_f.get('Version')}",
            "engineT": f"{summary_t.get('Engine')} v{summary_t.get('Version')}",
            "baseDate": summary_f.get("IndexBaseDate", ""),
        },
        "dates": date_str,
        "groups": groups,
        "index": index_map,
        "flowDates": flow_date_str,
        "flows": flow_map,
        "heat": heat,
        "rrg": rrg,
        "roles": role_matrix,
        "backtest": [
            {k: (r4(v) if isinstance(v, (int, float, np.floating)) and not isinstance(v, (bool, np.bool_)) else (bool(v) if isinstance(v, (bool, np.bool_)) else v)) for k, v in row.items()}
            for row in backtest.to_dict("records")
        ],
        "tradeBacktest": [
            {k: (r4(v) if isinstance(v, (int, float, np.floating)) and not isinstance(v, (bool, np.bool_)) else (bool(v) if isinstance(v, (bool, np.bool_)) else v)) for k, v in row.items()}
            for row in trade_bt.to_dict("records")
        ],
        "equity": {
            "dates": eq_dates,
            "strategy": [r4(v) for v in equity["Equity"]],
            "gross": [r4(v) for v in equity["GrossEquity"]],
            "bh": [r4(v) for v in bh_equity],
            "bhDates": [d.strftime("%y-%m-%d") for d in bh_daily["Date"]],
        },
        "trades": trades_rows,
        "gov": {
            "testsF": ledger_rows(tests_f),
            "testsB": ledger_rows(tests_b),
            "phases": [{"p": r["Phase"], "s": r["Status"], "d": str(r["Detail"])[:160]} for _, r in phases_f.iterrows()],
            "repairs": [{"id": r["RepairID"], "issue": r["Issue"], "fix": r["Repair"], "s": r["Status"]} for _, r in repairs.iterrows()],
        },
    }


HTML_TEMPLATE = r"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA · SectorFlow ALL-IN-ONE 儀表板</title>
<style>
:root{--bg:#f5f4f0;--sf:#fff;--ink:#1e1d1a;--sub:#6b6a66;--gr:#9c9890;--bd:#dbd9d3;
--up:#c9584a;--dn:#1f9e9e;--amber:#c4943a;--seal:#b5291a;
--fF:#3b6fc4;--fD:#b57f1f;--fT:#0f9678;--fW:#8f56c8}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);margin:0;padding:20px;
font-family:"DM Sans","Noto Sans TC","PingFang TC","Microsoft JhengHei",sans-serif;font-size:13px;line-height:1.5}
.wrap{max-width:1180px;margin:0 auto}
.eyebrow{font-family:"DM Mono",ui-monospace,monospace;font-size:11px;letter-spacing:2px;text-transform:uppercase;color:var(--sub)}
h1{font-family:"Syne","Noto Sans TC",sans-serif;font-weight:800;font-size:22px;margin:6px 0 2px}
h2{font-size:13.5px;margin:0 0 8px;font-weight:700}
.seal{display:inline-flex;width:30px;height:30px;align-items:center;justify-content:center;border-radius:7px;background:var(--seal);color:#fff;font-weight:900;margin-right:8px;vertical-align:middle}
.sub{color:var(--sub);font-size:12px}
.strip{height:6px;border-radius:2px;margin:12px 0;background:linear-gradient(90deg,#3b6fc4,#0f9678,#c4943a,#c9584a)}
.tabbar{display:flex;gap:6px;flex-wrap:wrap;margin:4px 0 12px}
.tb{cursor:pointer;border:1px solid var(--bd);border-radius:3px;padding:6px 14px;font-weight:700;user-select:none;font-size:12.5px;background:var(--sf)}
.tb.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.bar{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:8px}
.sb{cursor:pointer;border:1px solid var(--bd);border-radius:3px;padding:3px 10px;font-weight:600;user-select:none;font-size:11.5px;background:var(--sf)}
.sb.on{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.card{background:var(--sf);border:1px solid var(--bd);border-radius:8px;padding:12px;margin:10px 0}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px;margin:8px 0}
.kpi{background:var(--sf);border:1px solid var(--bd);border-radius:4px;padding:8px 12px;text-align:center}
.kpi .v{font-family:"DM Mono",ui-monospace,monospace;font-size:17px;font-weight:700;word-break:break-word}
.kpi .l{font-size:9px;color:var(--sub);text-transform:uppercase;letter-spacing:.5px}
table{width:100%;border-collapse:collapse;font-size:12px}
th,td{padding:5px 8px;border-bottom:1px solid #eceae2;text-align:left;white-space:nowrap}
th{font-size:9.5px;color:var(--sub);text-transform:uppercase;letter-spacing:.4px}
td.num,th.num{font-family:"DM Mono",ui-monospace,monospace;text-align:right}
.mono{font-family:"DM Mono",ui-monospace,monospace}
.scroll{overflow:auto;max-height:440px}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}
.pill{padding:1px 8px;border-radius:3px;font-family:"DM Mono",ui-monospace,monospace;font-size:10px;color:#fff;font-weight:700}
.foot{color:var(--gr);font-size:11px;border-top:1px solid var(--bd);padding-top:10px;margin-top:14px;line-height:1.7}
.tip{position:fixed;pointer-events:none;background:var(--ink);color:var(--bg);padding:6px 9px;border-radius:4px;
font-family:"DM Mono",ui-monospace,monospace;font-size:11px;display:none;z-index:9;white-space:pre;line-height:1.5}
.legend{display:flex;gap:14px;flex-wrap:wrap;font-size:11px;margin:4px 0 6px}
.legend span{display:inline-flex;align-items:center;gap:5px}
.sw{width:12px;height:12px;border-radius:3px;display:inline-block}
.evlab{font-family:"DM Mono",ui-monospace,monospace;font-size:9px;fill:#6b6a66}
section{display:none}section.on{display:block}
</style></head><body><div class="wrap">
<div class="eyebrow">VERITAS INTELLIGENCE · SECTORFLOW ALL-IN-ONE · JSON-DRIVEN · <b style="color:var(--amber)">CONTROLLED-DGP EVIDENCE(受控實跑,非實盤)</b></div>
<h1><span class="seal">流</span>台股族群資金流 × 鏈接指數 × 輪動 × 交易回測 — 全景儀表板</h1>
<div class="sub">上漲=<b style="color:var(--up)">紅</b>、下跌=<b style="color:var(--dn)">青綠</b>(台股慣例;方向/位置為第二編碼)。所有門檻為資料導出動態 Criteria。</div>
<div class="strip"></div>
<div class="tabbar" id="tabbar"></div>

<section id="sec-overview">
 <div class="kpis" id="ov-kpis"></div>
 <div class="card"><h2>方法回測(SectorFlow v0100 · 4 情境 × 2 種子)</h2>
  <div class="scroll"><table id="ov-bt"></table></div></div>
 <div class="card"><h2>半年定審角色矩陣(最新一期)</h2>
  <div class="scroll"><table id="ov-roles"></table></div></div>
</section>

<section id="sec-index">
 <div class="bar" id="idx-tabs"></div>
 <div class="card"><svg id="idx-chart" viewBox="0 0 1140 500" width="100%"></svg></div>
 <div class="card"><h2>全族群現況</h2><div class="scroll"><table id="idx-table"></table></div></div>
</section>

<section id="sec-flow">
 <div class="card"><h2>跨族群 3D 資金位移熱力圖(近 40 交易日)</h2>
  <div class="legend"><span><span class="sw" style="background:var(--up)"></span>吸金(位移 &gt; 0)</span>
   <span><span class="sw" style="background:#b9b6ae"></span>中性</span>
   <span><span class="sw" style="background:var(--dn)"></span>失血(位移 &lt; 0)</span></div>
  <div style="overflow:auto"><svg id="heat" width="1120"></svg></div></div>
 <div class="grid2">
 <div class="card"><h2>近 3 日四路主力淨流排行(億)</h2><svg id="rank" viewBox="0 0 540 420" width="100%"></svg></div>
 <div class="card"><h2 id="fd-title">族群四路資金明細</h2>
  <div class="bar" id="fd-tabs"></div>
  <div class="legend"><span><span class="sw" style="background:var(--fF)"></span>外資</span>
   <span><span class="sw" style="background:var(--fD)"></span>自營</span>
   <span><span class="sw" style="background:var(--fT)"></span>投信</span>
   <span><span class="sw" style="background:var(--fW)"></span>主力</span></div>
  <svg id="fd-chart" viewBox="0 0 540 330" width="100%"></svg></div>
 </div>
</section>

<section id="sec-rrg">
 <div class="grid2">
 <div class="card"><h2>RRG 輪動象限(FlowMom × PriceMom,近 5 日軌跡)</h2>
  <svg id="rrg" viewBox="0 0 540 540" width="100%" style="max-width:540px"></svg>
  <div class="sub" style="font-size:10px;margin-top:6px">點=當前位置,尾跡=近 5 日;橫軸=法人資金純度動能(橫截面 z),縱軸=20D 指數報酬動能(橫截面 z)。★Q2 資金領先價格=早期布局,⚠Q4 價強資金撤=出貨警戒。</div></div>
 <div class="card"><h2>象限對應動作</h2><div class="scroll"><table id="rrg-table"></table></div></div>
 </div>
</section>

<section id="sec-trade">
 <div class="kpis" id="tr-kpis"></div>
 <div class="card"><h2>權益曲線 — 策略(淨) vs Buy &amp; Hold(ROTATION 主測)</h2>
  <div class="legend"><span><span class="sw" style="background:var(--fF)"></span>策略(淨,T+1 含成本)</span>
   <span><span class="sw" style="background:#9c9890"></span>Buy &amp; Hold 全族群等權</span></div>
  <svg id="eq-chart" viewBox="0 0 1140 320" width="100%"></svg></div>
 <div class="grid2">
 <div class="card"><h2>各情境交易統計</h2><div class="scroll"><table id="tr-bt"></table></div></div>
 <div class="card"><h2>交易明細(主測)</h2><div class="scroll"><table id="tr-ledger"></table></div></div>
 </div>
</section>

<section id="sec-gov">
 <div class="card"><h2>SectorFlow 測試帳本(F01–F26)</h2><div class="scroll"><table id="gv-f"></table></div></div>
 <div class="grid2">
 <div class="card"><h2>TradeBacktest 測試帳本(B01–B09)</h2><div class="scroll"><table id="gv-b"></table></div></div>
 <div class="card"><h2>Repair Ledger(原設計缺陷修復)</h2><div class="scroll"><table id="gv-r"></table></div></div>
 </div>
 <div class="card"><h2>Pipeline Phases</h2><div class="scroll"><table id="gv-p"></table></div></div>
</section>

<div class="foot" id="foot"></div>
</div>
<div class="tip" id="tip"></div>
<script>
const D=__DATA_JSON__;
const UP="#c9584a",DN="#1f9e9e",GR="#9c9890",NEU="#b9b6ae";
const FLOWC={foreign:"#3b6fc4",dealer:"#b57f1f",trust:"#0f9678",whale:"#8f56c8"};
const FLOWN={foreign:"外資",dealer:"自營",trust:"投信",whale:"主力"};
const $=id=>document.getElementById(id);
const tip=$("tip");
function showTip(ev,txt){tip.style.display="block";tip.textContent=txt;
 const x=Math.min(ev.clientX+14,window.innerWidth-220),y=ev.clientY+14;
 tip.style.left=x+"px";tip.style.top=y+"px";}
function hideTip(){tip.style.display="none";}
function short(g){return g.replace(/^[A-Z] /,"");}
function stateLabel(s){return {INFLOW_EXPANDING:"吸金",STEALTH_ACCUMULATION:"投信偷買",OUTFLOW_DRAINING:"失血",RETAIL_WHALE_SPECULATION:"大戶投機",NEUTRAL_ROTATION:"中性"}[s]||s||"—";}
function sigPill(s){const m={DYNAMIC_BUY:["BUY",UP],DYNAMIC_SETUP:["SETUP","#3b6fc4"],DYNAMIC_EXIT:["EXIT",DN],HOLD:["HOLD","#9c9890"]};const p=m[s]||["—","#9c9890"];
 return `<span class="pill" style="background:${p[1]}">${p[0]}</span>`;}
function statusPill(s){const c=s==="PASS"?"#0f9678":(s==="WARN"?"#b57f1f":"#b5291a");return `<span class="pill" style="background:${c}">${s}</span>`;}

/* ---------- tabs ---------- */
const TABS=[["overview","總覽"],["index","鏈接指數"],["flow","資金位移"],["rrg","輪動象限"],["trade","交易回測"],["gov","治理矩陣"]];
let curTab="overview";
function renderTabs(){$("tabbar").innerHTML=TABS.map(t=>`<span class="tb ${t[0]===curTab?'on':''}" data-t="${t[0]}">${t[1]}</span>`).join("");
 document.querySelectorAll("#tabbar .tb").forEach(e=>e.onclick=()=>{curTab=e.dataset.t;renderTabs();
  document.querySelectorAll("section").forEach(s=>s.classList.remove("on"));
  $("sec-"+curTab).classList.add("on");});
 document.querySelectorAll("section").forEach(s=>s.classList.remove("on"));
 $("sec-"+curTab).classList.add("on");}

/* ---------- overview ---------- */
function kpi(v,l,c){return `<div class="kpi"><div class="v" style="${c?('color:'+c):''}">${v}</div><div class="l">${l}</div></div>`;}
function renderOverview(){
 const m=D.meta;
 const rot=D.tradeBacktest.filter(r=>r.Scenario==="ROTATION");
 const exp=rot.map(r=>r.Expectancy);
 $("ov-kpis").innerHTML=
  kpi(m.hard,"Hard Failures",m.hard===0?"#0f9678":"#b5291a")+
  kpi(m.warn,"Review Warnings","#b57f1f")+
  kpi(D.groups.length,"L1 Sectors")+
  kpi(D.backtest.length,"Backtest Runs")+
  kpi((exp.length?Math.max(...exp):0).toFixed(3),"最佳期望值/筆(ROTATION)",UP)+
  kpi("PASS","Final Gate","#0f9678");
 const cols=["Scenario","Seed","EventPrecision","EventRecall","FalseAlarmRate","RoleMacroF1","RawMedianWithinCorr","ResidualMedianWithinCorr","NaiveRebaseMaxGap","MacroHaltDays"];
 $("ov-bt").innerHTML="<thead><tr>"+cols.map(c=>`<th class="${typeof D.backtest[0][c]==='number'?'num':''}">${c}</th>`).join("")+"</tr></thead><tbody>"+
  D.backtest.map(r=>"<tr>"+cols.map(c=>{const v=r[c];return `<td class="${typeof v==='number'?'num':''}">${v===null?"—":(typeof v==='number'?v:String(v))}</td>`;}).join("")+"</tr>").join("")+"</tbody>";
 $("ov-roles").innerHTML="<thead><tr><th>族群</th><th class='num'>LEADER</th><th class='num'>PEER</th><th class='num'>MEMBER</th><th class='num'>LAGGARD(剔除)</th><th class='num'>FALLBACK</th></tr></thead><tbody>"+
  D.roles.map(r=>`<tr><td style="font-weight:700">${r.g}</td><td class="num" style="color:${UP}">${r.L}</td><td class="num">${r.P}</td><td class="num">${r.M}</td><td class="num" style="color:${DN}">${r.G}</td><td class="num">${r.F}</td></tr>`).join("")+"</tbody>";
}

/* ---------- index tab ---------- */
let curGroup=D.groups[0];
function renderIdxTabs(){$("idx-tabs").innerHTML=D.groups.map(g=>`<span class="sb ${g===curGroup?'on':''}" data-g="${g}">${short(g)}</span>`).join("");
 document.querySelectorAll("#idx-tabs .sb").forEach(e=>e.onclick=()=>{curGroup=e.dataset.g;renderIdxTabs();drawIndex();drawFlowDetail();});}
function drawIndex(){
 const I=D.index[curGroup],px=I.px,turn=I.turn,flow=I.flow,n=px.length;
 const W=1140,L=56,R=14,T=24,PB=280,VB=340,FT=360,FB=470;
 const vals=px.filter(v=>v!==null);
 const mn=Math.min(...vals),mx=Math.max(...vals),pad=(mx-mn)*0.08||1;
 const X=i=>L+(W-L-R)*i/(n-1),Y=p=>T+(PB-T)*(1-(p-mn+pad)/(mx-mn+2*pad));
 let s="";
 for(let g=0;g<=4;g++){const p=mn-pad+(mx-mn+2*pad)*g/4,y=Y(p);
  s+=`<line x1="${L}" y1="${y}" x2="${W-R}" y2="${y}" stroke="#eceae2"/><text x="${L-6}" y="${y+3}" text-anchor="end" class="evlab">${p.toFixed(0)}</text>`;}
 // 基期垂直參考線(2026-01-02 = 100)。
 const baseI=D.dates.indexOf(D.meta.baseDate.slice(2));
 if(baseI>=0){s+=`<line x1="${X(baseI)}" y1="${T}" x2="${X(baseI)}" y2="${FB}" stroke="#c4943a" stroke-dasharray="3 4"/>`;
  s+=`<text x="${X(baseI)+4}" y="${T+10}" class="evlab" style="fill:#c4943a">基期 ${D.meta.baseDate}=100</text>`;}
 // 中帶:實質成交額(獨立層)。
 const tv=turn.filter(v=>v!==null),vmax=tv.length?Math.max(...tv):1;
 for(let i=0;i<n;i++){if(turn[i]===null)continue;const up=i>0&&px[i]>=px[i-1];
  s+=`<rect x="${X(i)-0.7}" y="${VB-(turn[i]/vmax)*48}" width="1.4" height="${(turn[i]/vmax)*48}" fill="${up?UP:DN}" fill-opacity="0.45"/>`;}
 s+=`<text x="${L-6}" y="${VB-20}" text-anchor="end" class="evlab">量(億)</text>`;
 // 上帶:鏈接指數折線(紅漲青綠跌)。
 for(let i=1;i<n;i++){s+=`<line x1="${X(i-1)}" y1="${Y(px[i-1])}" x2="${X(i)}" y2="${Y(px[i])}" stroke="${px[i]>=px[i-1]?UP:DN}" stroke-width="1.6"/>`;}
 const last=px[n-1],chg=(last/px[n-2]-1)*100;
 s+=`<text x="${W-R}" y="${Y(last)-6}" text-anchor="end" class="mono" style="font-size:12px;font-weight:700;fill:${chg>=0?UP:DN}">${last.toFixed(1)} (${chg>=0?"+":""}${chg.toFixed(2)}%)</text>`;
 s+=`<text x="${L}" y="${T-8}" class="evlab">${curGroup} · 鏈接指數(錨定 ${D.meta.baseDate}=100,√實質成交額加權,剔除 LAGGARD) · 視窗 2025-01-02 → 今</text>`;
 // 下帶:現金流入流出(四路主力合計淨流,億;獨立座標,零軸置中)。
 const fv=flow.filter(v=>v!==null&&isFinite(v)).map(Math.abs);
 const fmax=fv.length?Math.max(0.5,quant(fv,0.99)):1;
 const fmid=(FT+FB)/2,fscale=(FB-FT)/2/fmax;
 s+=`<line x1="${L}" y1="${fmid}" x2="${W-R}" y2="${fmid}" stroke="#dbd9d3"/>`;
 s+=`<text x="${L-6}" y="${FT+8}" text-anchor="end" class="evlab">+${fmax.toFixed(0)}</text>`;
 s+=`<text x="${L-6}" y="${FB}" text-anchor="end" class="evlab">-${fmax.toFixed(0)}</text>`;
 s+=`<text x="${L+4}" y="${FT-6}" class="evlab">現金流入(紅,上)/流出(青綠,下) — 四路主力合計淨流(億,獨立座標)</text>`;
 for(let i=0;i<n;i++){const v=flow[i];if(v===null||!isFinite(v))continue;
  const h=Math.min(Math.abs(v)*fscale,(FB-FT)/2);
  if(v>=0)s+=`<rect x="${X(i)-0.7}" y="${fmid-h}" width="1.4" height="${Math.max(0.5,h)}" fill="${UP}" fill-opacity="0.8"/>`;
  else s+=`<rect x="${X(i)-0.7}" y="${fmid}" width="1.4" height="${Math.max(0.5,h)}" fill="${DN}" fill-opacity="0.8"/>`;}
 s+=`<rect id="idx-hover" x="${L}" y="${T}" width="${W-L-R}" height="${FB-T}" fill="transparent"/>`;
 $("idx-chart").innerHTML=s;
 const hov=$("idx-hover");
 hov.onmousemove=ev=>{const r=hov.getBoundingClientRect();
  const i=Math.max(0,Math.min(n-1,Math.round((ev.clientX-r.left)/r.width*(n-1))));
  showTip(ev,`${D.dates[i]}  ${curGroup}\n指數 ${px[i]===null?"—":px[i].toFixed(1)}   量 ${turn[i]===null?"—":turn[i].toFixed(1)}億\n資金淨流 ${flow[i]===null?"—":(flow[i]>=0?"+":"")+flow[i].toFixed(1)}億\n成分 ${I.n[i]} 檔   日報酬 ${(I.ret[i]*100).toFixed(2)}%`);};
 hov.onmouseleave=hideTip;
}
function renderIdxTable(){
 let h="<thead><tr><th>族群</th><th class='num'>指數</th><th class='num'>3D 漲跌%</th><th class='num'>3D 位移 pct-pt</th><th>資金狀態</th><th>訊號</th><th class='num'>成分檔數</th></tr></thead><tbody>";
 for(const g of D.groups){const I=D.index[g],px=I.px,n=px.length;
  const r3=(px[n-1]/px[Math.max(0,n-4)]-1)*100;
  const F=D.flows[g],fn=F.velocity.length;
  const vel=F.velocity[fn-1],st=F.state[fn-1],sg=F.signal[fn-1];
  h+=`<tr style="${g===curGroup?'background:#faf9f4':''}"><td style="font-weight:700">${g}</td><td class="num">${px[n-1].toFixed(1)}</td>`+
   `<td class="num" style="color:${r3>=0?UP:DN};font-weight:700">${r3>=0?"+":""}${r3.toFixed(2)}</td>`+
   `<td class="num" style="color:${(vel||0)>=0?UP:DN}">${vel===null?"—":(vel>=0?"+":"")+vel.toFixed(3)}</td>`+
   `<td>${stateLabel(st)}</td><td>${sigPill(sg)}</td><td class="num">${I.n[n-1]}</td></tr>`;}
 $("idx-table").innerHTML=h+"</tbody>";
}

/* ---------- flow tab ---------- */
function drawHeat(){
 const rows=D.heat.rows,dts=D.heat.dates,cw=Math.max(14,Math.floor(980/dts.length)),ch=22,L=170,T=20;
 const H=T+rows.length*ch+30;
 $("heat").setAttribute("height",H);
 const vals=rows.flatMap(r=>r.v).filter(v=>v!==null).map(Math.abs);
 const vmax=vals.length?Math.max(0.05,quant(vals,0.98)):1;
 let s="";
 dts.forEach((d,j)=>{if(j%5===0)s+=`<text x="${L+j*cw+cw/2}" y="${T-6}" text-anchor="middle" class="evlab">${d}</text>`;});
 rows.forEach((r,i)=>{
  s+=`<text x="${L-8}" y="${T+i*ch+ch/2+3}" text-anchor="end" style="font-size:10.5px;font-weight:600">${r.g}</text>`;
  r.v.forEach((v,j)=>{
   let fill=NEU,op=0.25;
   if(v!==null&&isFinite(v)){const t=Math.max(-1,Math.min(1,v/vmax));fill=t>=0?UP:DN;op=0.12+0.7*Math.abs(t);}
   s+=`<rect x="${L+j*cw}" y="${T+i*ch}" width="${cw-2}" height="${ch-2}" rx="2" fill="${fill}" fill-opacity="${op}" data-g="${r.g}" data-d="${dts[j]}" data-v="${v===null?"—":v}"/>`;});
 });
 $("heat").innerHTML=s;
 $("heat").querySelectorAll("rect").forEach(rc=>{
  rc.onmousemove=ev=>showTip(ev,`${rc.dataset.d}  ${rc.dataset.g}\n3D 位移 ${rc.dataset.v} pct-pt`);
  rc.onmouseleave=hideTip;});
}
function quant(a,q){const b=[...a].sort((x,y)=>x-y);return b[Math.min(b.length-1,Math.floor(q*b.length))];}
function drawRank(){
 const rank=D.groups.map(g=>{const F=D.flows[g],n=F.smart.length;
  let v=0;for(let i=Math.max(0,n-3);i<n;i++)v+=(F.smart[i]||0);return {g,v};}).sort((a,b)=>b.v-a.v);
 const W=540,L=150,R=60,bh=24,T=14;
 const vmax=Math.max(...rank.map(r=>Math.abs(r.v)))||1;
 const mid=L+(W-L-R)/2,half=(W-L-R)/2-6;
 let s=`<line x1="${mid}" y1="${T}" x2="${mid}" y2="${T+rank.length*bh}" stroke="#dbd9d3"/>`;
 rank.forEach((r,i)=>{const w=Math.abs(r.v)/vmax*half,y=T+i*bh;
  s+=`<text x="${L-6}" y="${y+bh/2+3}" text-anchor="end" style="font-size:10.5px;font-weight:600">${r.g}</text>`;
  s+=`<rect x="${r.v>=0?mid:mid-w}" y="${y+4}" width="${Math.max(1,w)}" height="${bh-9}" rx="3" fill="${r.v>=0?UP:DN}" data-g="${r.g}" data-v="${r.v.toFixed(1)}"/>`;
  const inside=w>half*0.72;
  const lx=r.v>=0?(inside?mid+w-4:mid+w+5):(inside?mid-w+4:mid-w-5);
  const anch=r.v>=0?(inside?'end':'start'):(inside?'start':'end');
  const fill=inside?'#fff':(r.v>=0?UP:DN);
  s+=`<text x="${lx}" y="${y+bh/2+3}" text-anchor="${anch}" class="mono" style="font-size:10px;fill:${fill}">${r.v>=0?"+":""}${r.v.toFixed(1)}</text>`;});
 $("rank").setAttribute("viewBox",`0 0 540 ${T+rank.length*bh+10}`);
 $("rank").innerHTML=s;
 $("rank").querySelectorAll("rect").forEach(rc=>{rc.onmousemove=ev=>showTip(ev,`${rc.dataset.g}\n近3日主力淨流 ${rc.dataset.v} 億`);rc.onmouseleave=hideTip;});
}
function renderFdTabs(){$("fd-tabs").innerHTML=D.groups.map(g=>`<span class="sb ${g===curGroup?'on':''}" data-g="${g}">${short(g)}</span>`).join("");
 document.querySelectorAll("#fd-tabs .sb").forEach(e=>e.onclick=()=>{curGroup=e.dataset.g;renderIdxTabs();renderFdTabs();drawIndex();drawFlowDetail();});}
function drawFlowDetail(){
 $("fd-title").textContent=`${curGroup} · 四路資金明細(近 ${D.flowDates.length} 日,億)`;
 renderFdTabs();
 const F=D.flows[curGroup],n=D.flowDates.length;
 const keys=["foreign","dealer","trust","whale"];
 const W=540,L=44,R=10,T=12,BB=196,CT=216,CB=316;
 let vmax=1;
 for(let i=0;i<n;i++){let p=0,q=0;keys.forEach(k=>{const v=F[k][i]||0;if(v>=0)p+=v;else q-=v;});vmax=Math.max(vmax,p,q);}
 const mid=(T+BB)/2,scale=(BB-T)/2/vmax,bw=Math.max(1.6,(W-L-R)/n-1.2);
 let s=`<line x1="${L}" y1="${mid}" x2="${W-R}" y2="${mid}" stroke="#dbd9d3"/>`;
 s+=`<text x="${L-5}" y="${T+6}" text-anchor="end" class="evlab">+${vmax.toFixed(0)}</text><text x="${L-5}" y="${BB}" text-anchor="end" class="evlab">-${vmax.toFixed(0)}</text>`;
 for(let i=0;i<n;i++){const x=L+(W-L-R)*i/n;let up=0,dnn=0;
  let tipTxt=D.flowDates[i];
  keys.forEach(k=>{const v=F[k][i]||0;const h=Math.abs(v)*scale;tipTxt+=`\n${FLOWN[k]} ${v>=0?"+":""}${v.toFixed(1)}`;
   if(v>=0){s+=`<rect x="${x}" y="${mid-up-h}" width="${bw}" height="${Math.max(0,h-1)}" fill="${FLOWC[k]}" data-i="${i}"/>`;up+=h;}
   else{s+=`<rect x="${x}" y="${mid+dnn+1}" width="${bw}" height="${Math.max(0,h-1)}" fill="${FLOWC[k]}" data-i="${i}"/>`;dnn+=h;}});
  s+=`<rect x="${x}" y="${T}" width="${bw+1}" height="${BB-T}" fill="transparent" data-tip="${encodeURIComponent(tipTxt)}"/>`;}
 // 下板:累積主力淨沉澱(獨立座標,不共軸)
 let cum=0;const cums=F.smart.map(v=>cum+= (v||0));
 const cmn=Math.min(0,...cums),cmx=Math.max(0,...cums),cpad=(cmx-cmn)*0.1||1;
 const CY=v=>CT+(CB-CT)*(1-(v-cmn+cpad)/(cmx-cmn+2*cpad));
 s+=`<line x1="${L}" y1="${CY(0)}" x2="${W-R}" y2="${CY(0)}" stroke="#eceae2"/>`;
 s+=`<text x="${L-5}" y="${CT+8}" text-anchor="end" class="evlab">${cmx.toFixed(0)}</text><text x="${L-5}" y="${CB}" text-anchor="end" class="evlab">${cmn.toFixed(0)}</text>`;
 for(let i=1;i<n;i++){const x1=L+(W-L-R)*(i-1)/n+bw/2,x2=L+(W-L-R)*i/n+bw/2;
  s+=`<line x1="${x1}" y1="${CY(cums[i-1])}" x2="${x2}" y2="${CY(cums[i])}" stroke="#1e1d1a" stroke-width="1.6"/>`;}
 s+=`<text x="${L+4}" y="${CT+10}" class="evlab">累積主力淨沉澱(億,獨立座標)</text>`;
 $("fd-chart").innerHTML=s;
 $("fd-chart").querySelectorAll("rect[data-tip]").forEach(rc=>{
  rc.onmousemove=ev=>showTip(ev,decodeURIComponent(rc.dataset.tip));rc.onmouseleave=hideTip;});
}

/* ---------- rrg tab ---------- */
function drawRRG(){
 const S=540,C=S/2,PAD=40;
 const XX=v=>C+(v/3)*(C-PAD),YY=v=>C-(v/3)*(C-PAD);
 let s=`<rect x="${C}" y="0" width="${C}" height="${C}" fill="${UP}" opacity="0.05"/>`+
  `<rect x="${C}" y="${C}" width="${C}" height="${C}" fill="#3b6fc4" opacity="0.05"/>`+
  `<rect x="0" y="${C}" width="${C}" height="${C}" fill="${DN}" opacity="0.05"/>`+
  `<rect x="0" y="0" width="${C}" height="${C}" fill="#c4943a" opacity="0.06"/>`+
  `<line x1="${C}" y1="${PAD}" x2="${C}" y2="${S-PAD}" stroke="#dbd9d3"/><line x1="${PAD}" y1="${C}" x2="${S-PAD}" y2="${C}" stroke="#dbd9d3"/>`+
  `<text x="${S-PAD+4}" y="52" text-anchor="end" class="evlab" style="font-weight:700;fill:${UP}">領先 LEADING</text>`+
  `<text x="${PAD}" y="52" class="evlab" style="font-weight:700;fill:#c4943a">轉弱 WEAKENING ⚠</text>`+
  `<text x="${PAD}" y="${S-52}" class="evlab" style="font-weight:700;fill:${DN}">落後 LAGGING</text>`+
  `<text x="${S-PAD+4}" y="${S-52}" text-anchor="end" class="evlab" style="font-weight:700;fill:#3b6fc4">改善 IMPROVING ★</text>`+
  `<text x="${C}" y="${S-8}" text-anchor="middle" class="evlab">法人資金純度動能 FlowMom →</text>`+
  `<text x="14" y="${C}" text-anchor="middle" transform="rotate(-90 14 ${C})" class="evlab">價格動能 PriceMom →</text>`;
 D.rrg.forEach(r=>{
  const t=r.trail,last=t[t.length-1];
  if(t.length>1){s+=`<path d="M ${t.map(p=>XX(p[0])+","+YY(p[1])).join(" L ")}" fill="none" stroke="#9c9890" stroke-width="1.3" opacity="0.55"/>`;}
  const q=(last[0]>=0&&last[1]>=0)?UP:(last[0]>=0?"#3b6fc4":(last[1]>=0?"#c4943a":DN));
  s+=`<circle cx="${XX(last[0])}" cy="${YY(last[1])}" r="6" fill="${q}" stroke="#fff" stroke-width="2" data-g="${r.g}" data-x="${last[0]}" data-y="${last[1]}"/>`;
  s+=`<text x="${XX(last[0])+9}" y="${YY(last[1])+4}" style="font-size:10.5px;font-weight:600">${short(r.g)}</text>`;});
 $("rrg").innerHTML=s;
 $("rrg").querySelectorAll("circle").forEach(c=>{c.onmousemove=ev=>showTip(ev,`${c.dataset.g}\nFlowMom ${c.dataset.x}  PriceMom ${c.dataset.y}`);c.onmouseleave=hideTip;});
 let h="<thead><tr><th>族群</th><th class='num'>(Flow, Price)</th><th>象限</th><th>動作</th></tr></thead><tbody>";
 D.rrg.slice().sort((a,b)=>b.trail[b.trail.length-1][0]-a.trail[a.trail.length-1][0]).forEach(r=>{
  const p=r.trail[r.trail.length-1],f=p[0],pm=p[1];
  let quad,act,col;
  if(f>=0&&pm>=0){quad="Q1 領先";act="主升段·續抱";col=UP;}
  else if(f>=0){quad="Q2 改善 ★";act="資金領先價格·早期布局";col="#3b6fc4";}
  else if(pm>=0){quad="Q4 轉弱 ⚠";act="價強資金撤·出貨警戒";col="#c4943a";}
  else{quad="Q3 落後";act="雙弱·迴避";col=DN;}
  h+=`<tr><td style="font-weight:700">${r.g}</td><td class="num">(${f>=0?"+":""}${f.toFixed(2)}, ${pm>=0?"+":""}${pm.toFixed(2)})</td>`+
   `<td><span class="pill" style="background:${col}">${quad}</span></td><td class="sub">${act}·${stateLabel(r.state)}</td></tr>`;});
 $("rrg-table").innerHTML=h+"</tbody>";
}

/* ---------- trade tab ---------- */
function renderTrade(){
 const rot=D.tradeBacktest.filter(r=>r.Scenario==="ROTATION");
 const tide=D.tradeBacktest.filter(r=>r.Scenario==="MARKET_TIDE");
 const wr=rot.length?rot.reduce((a,r)=>a+r.WinRate,0)/rot.length:0;
 $("tr-kpis").innerHTML=
  kpi((wr*100).toFixed(1)+"%","ROTATION 平均勝率",UP)+
  kpi(rot.length?Math.max(...rot.map(r=>r.Expectancy)).toFixed(3):"—","最佳期望值/筆")+
  kpi(tide.length?(Math.min(...tide.map(r=>r.MaxDrawdown))*100).toFixed(2)+"%":"—","TIDE 策略最大回撤",DN)+
  kpi(tide.length?(Math.min(...tide.map(r=>r.BHMaxDrawdown))*100).toFixed(1)+"%":"—","TIDE B&H 最大回撤")+
  kpi(D.trades.length,"主測交易筆數")+
  kpi("T+1","執行紀律(零同日前視)","#0f9678");
 // equity chart:兩序列同軸(皆為權益倍數)
 const E=D.equity,n=E.dates.length;
 const all=[...E.strategy,...E.bh].filter(v=>v!==null);
 const mn=Math.min(...all),mx=Math.max(...all),pad=(mx-mn)*0.1||0.01;
 const W=1140,L=52,R=14,T=18,B=290;
 const X=i=>L+(W-L-R)*i/(n-1),Y=v=>T+(B-T)*(1-(v-mn+pad)/(mx-mn+2*pad));
 let s="";
 for(let g=0;g<=4;g++){const v=mn-pad+(mx-mn+2*pad)*g/4,y=Y(v);
  s+=`<line x1="${L}" y1="${y}" x2="${W-R}" y2="${y}" stroke="#eceae2"/><text x="${L-6}" y="${y+3}" text-anchor="end" class="evlab">${v.toFixed(2)}</text>`;}
 const bhX=i=>L+(W-L-R)*i/(E.bh.length-1);
 for(let i=1;i<E.bh.length;i++){s+=`<line x1="${bhX(i-1)}" y1="${Y(E.bh[i-1])}" x2="${bhX(i)}" y2="${Y(E.bh[i])}" stroke="#9c9890" stroke-width="1.4" stroke-dasharray="4 3"/>`;}
 for(let i=1;i<n;i++){s+=`<line x1="${X(i-1)}" y1="${Y(E.strategy[i-1])}" x2="${X(i)}" y2="${Y(E.strategy[i])}" stroke="#3b6fc4" stroke-width="2"/>`;}
 s+=`<text x="${X(n-1)}" y="${Y(E.strategy[n-1])-8}" text-anchor="end" class="mono" style="font-size:11px;font-weight:700;fill:#3b6fc4">策略 ${((E.strategy[n-1]-1)*100).toFixed(1)}%</text>`;
 s+=`<text x="${bhX(E.bh.length-1)}" y="${Y(E.bh[E.bh.length-1])+14}" text-anchor="end" class="mono" style="font-size:11px;font-weight:700;fill:#6b6a66">B&amp;H ${((E.bh[E.bh.length-1]-1)*100).toFixed(1)}%</text>`;
 s+=`<rect id="eq-hover" x="${L}" y="${T}" width="${W-L-R}" height="${B-T}" fill="transparent"/>`;
 $("eq-chart").innerHTML=s;
 const hov=$("eq-hover");
 hov.onmousemove=ev=>{const r=hov.getBoundingClientRect();
  const i=Math.max(0,Math.min(n-1,Math.round((ev.clientX-r.left)/r.width*(n-1))));
  const j=Math.max(0,Math.min(E.bh.length-1,Math.round((ev.clientX-r.left)/r.width*(E.bh.length-1))));
  showTip(ev,`${E.dates[i]}\n策略 ${((E.strategy[i]-1)*100).toFixed(2)}%   B&H ${((E.bh[j]-1)*100).toFixed(2)}%`);};
 hov.onmouseleave=hideTip;
 const cols=["Scenario","Seed","Trades","WinRate","Expectancy","ProfitFactor","TotalReturn","MaxDrawdown","BHTotalReturn","BHMaxDrawdown","NullMedianExpectancy"];
 $("tr-bt").innerHTML="<thead><tr>"+cols.map(c=>`<th class="num">${c}</th>`).join("")+"</tr></thead><tbody>"+
  D.tradeBacktest.map(r=>"<tr>"+cols.map(c=>{let v=r[c];
   return `<td class="num">${v===null||v===undefined?"—":(typeof v==='number'?v:String(v))}</td>`;}).join("")+"</tr>").join("")+"</tbody>";
 $("tr-ledger").innerHTML="<thead><tr><th>族群</th><th>進場</th><th>出場</th><th class='num'>淨報酬%</th><th>出場原因</th></tr></thead><tbody>"+
  D.trades.map(t=>`<tr><td>${t.g}</td><td class="mono">${t.in}</td><td class="mono">${t.out}</td>`+
   `<td class="num" style="color:${t.ret>=0?UP:DN};font-weight:700">${(t.ret*100).toFixed(2)}</td><td class="sub">${t.why}</td></tr>`).join("")+"</tbody>";
}

/* ---------- governance tab ---------- */
function ledgerTable(rows){
 return "<thead><tr><th>ID</th><th>測試</th><th>狀態</th><th>級別</th><th>證據</th></tr></thead><tbody>"+
  rows.map(r=>`<tr><td class="mono">${r.id}</td><td style="font-weight:600">${r.name}</td><td>${statusPill(r.status)}</td>`+
   `<td class="mono" style="font-size:10px">${r.sev}</td><td class="sub" style="white-space:normal;font-size:10.5px">${r.ev}</td></tr>`).join("")+"</tbody>";
}
function renderGov(){
 $("gv-f").innerHTML=ledgerTable(D.gov.testsF);
 $("gv-b").innerHTML=ledgerTable(D.gov.testsB);
 $("gv-r").innerHTML="<thead><tr><th>ID</th><th>原設計問題</th><th>修復</th><th>狀態</th></tr></thead><tbody>"+
  D.gov.repairs.map(r=>`<tr><td class="mono">${r.id}</td><td style="white-space:normal">${r.issue}</td><td class="sub" style="white-space:normal">${r.fix}</td><td>${statusPill(r.s==="FIXED"?"PASS":r.s)}</td></tr>`).join("")+"</tbody>";
 $("gv-p").innerHTML="<thead><tr><th>Phase</th><th>狀態</th><th>Detail</th></tr></thead><tbody>"+
  D.gov.phases.map(p=>`<tr><td class="mono" style="font-weight:700">${p.p}</td><td>${statusPill(p.s)}</td><td class="sub" style="white-space:normal">${p.d}</td></tr>`).join("")+"</tbody>";
}

$("foot").innerHTML=`引擎:${D.meta.engineF} + ${D.meta.engineT} · Final Gate <b>${D.meta.gate}</b> · Trade Gate <b>${D.meta.tradeStatus}</b><br>`+
 `所有數字來自受控 DGP 實跑 evidence(SHA256 manifest 後驗),僅驗證方法邏輯,非實盤績效、非投資建議。`+
 `接真值:替換 def_generate_sector_panel 資料契約(Date×Ticker×AdjClose×Turnover×Daytrade×四路買賣超+宏觀七欄)。產生 ${D.meta.generated}`;

renderTabs();renderOverview();renderIdxTabs();drawIndex();renderIdxTable();
drawHeat();drawRank();drawFlowDetail();drawRRG();renderTrade();renderGov();
</script></body></html>
"""


def main() -> int:
    payload = def_build_payload()
    data_json = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    html = HTML_TEMPLATE.replace("__DATA_JSON__", data_json)
    DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUT.write_text(html, encoding="utf-8")
    size_kb = DEFAULT_OUT.stat().st_size / 1024
    print("=" * 80)
    print(f"VIA SectorFlow ALL-IN-ONE Dashboard Builder v{VERSION}")
    print("Output :", DEFAULT_OUT)
    print(f"Size   : {size_kb:.0f} KB")
    print("Tabs   : 總覽 / 鏈接指數 / 資金位移 / 輪動象限 / 交易回測 / 治理矩陣")
    print("Groups :", len(payload["groups"]), "| trades:", len(payload["trades"]),
          "| tests:", len(payload["gov"]["testsF"]) + len(payload["gov"]["testsB"]))
    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
