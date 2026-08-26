#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG009_DashboardUI — VIA 儀表板原始版(批167;操作員 Layout element 定案)
====================================================================
操作員令:Layout element(CSS+JS 全文)=版面規劃定案。本引擎收容整合:
  版面值單源=VIA_UI_TemplateSSOT.json「dashboard」節(批167 append 收錄
    定案值:260px Gate Panel/38px 表頭/圖卡 320-420px/斷點 768/字 11→10/
    tick 檔位冊);CSS 由冊生成,引擎零寫死
  結構=操作員規格原樣:PC 左右兩欄(左 Gate Panel 篩選+收合、右圖表區)
    /Mobile 上下佈局;Alerts+Audit Logs;Auto-Fixer(欄位檢/日期解析/
    補齊日期/補值/IQR 極端值平滑)+Auto-Optimizer(尺寸/字級/欄列自調)
  實料嵌入(AI 只整理不發明):vdf_tw_market.duckdb 三檔(2330/2317/2454)
    收盤+量+三法人買賣超,近 240 交易日;零網路零 CDN 單檔可離線開
  QA 修正(誠實留痕,結構零改):①autoFixData 欄位檢誤用 !df.date(陣列
    恆真)→ 檢首列鍵 ②fillMissingDates 回傳 fixed.df 未接線→接回
    ③「線性插值」實為前值遞補→註記正名 ④IQR 分位未濾 null→濾
    ⑤optimizePlotly 未防 Plotly 缺席→typeof 閘(零 CDN:預設內建 SVG
    車道,環境有 Plotly 時自動升級)
用法:python3 VAP_ENG009_DashboardUI_v0101.py run | --selftest
v0102→v0103(批173):全球層——層級三分(個股/族群/全球):
  全球=ROTATION_GLOBAL 最新快照(glob 尾版)9 類別(US/歐洲三分/
  亞洲三分/大中華/商品)×類別指數 FULL_EW/成交值 PROXY/金流佔比
  PROXY/正廣度+宏觀因子四線(EURUSD/USDJPY/VIX/US10Y_D1=全球共通
  不隨類別);延續榜通用化(族群/全球同表)。誠實標記:TURNOVER_
  PROXY(價×量估算非所值)+profile=REVIEW 非 PASS(V13 裁定)全頁宣告。
v0101→v0102(批172):族群視角層——Gate Panel +「層級」下拉(個股/
  族群);族群層=GRP_ENG040 輪動 tw 最新快照(glob 尾版 ROTATION_TW_*)
  實料:六模組(族群指數 FULL_EW/成交值/金流佔比/正廣度/外資/投信
  金額)+輪動態燈(RotationState×Confidence)+金流佔比延續榜(最新
  日×5 日均×佔比變化;榜=快照冊直出零發明);副圖=金流佔比長條。
v0100→v0101(批169):深化系統連動——模組車道 5→8(+成交值/融資餘額/
  融券餘額,tw_trading_daily+tw_chip_margin 實料 639-640 日);主副雙圖
  (chart-grid 第二卡=成交量副圖,操作員規格原生支援);估值快照
  (tw_valuation_daily)誠實現值列(僅 2 快照日,不足作圖不假圖)。
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

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
SSOT = VIA / "supportive modules" / "registry" / "VIA_UI_TemplateSSOT_v0100.json"
DB = VIA / "functional modules" / "VDF" / "output_hub" / "mega" / "vdf_tw_market.duckdb"
UI_OUT = VIA / "supportive modules" / "ui_support" / "VIA_UI_Dashboard_v0100.html"

STOCKS = ["2330", "2317", "2454"]   # 原始版示範檔(儀表板下拉;實料嵌入)
N_SESS = 240


def load_dash_tokens() -> dict:
    return json.loads(SSOT.read_text(encoding="utf-8"))["dashboard"]


def harvest_data() -> dict:
    """duckdb 實料(唯讀):收盤/量/三法人買賣超;缺庫=誠實空+alert"""
    if not DB.exists():
        return {"stocks": {}, "note": "資料庫缺席(誠實)"}
    import duckdb
    con = duckdb.connect(str(DB), read_only=True)
    names = dict(con.execute(
        "SELECT code, name FROM tw_listings WHERE code IN ('2330','2317','2454')"
    ).fetchall())
    out = {}
    for c in STOCKS:
        px = con.execute(
            "SELECT date, close, volume FROM tw_daily_prices "
            "WHERE ticker=? ORDER BY date DESC LIMIT ?", [f"{c}.TW", N_SESS]
        ).fetchall()[::-1]
        ch = dict((r[0], r[1:]) for r in con.execute(
            "SELECT date, foreign_net, trust_net, dealer_net FROM tw_chip_inst "
            "WHERE code=? ORDER BY date DESC LIMIT ?", [c, N_SESS]).fetchall())
        mg = dict((r[0], r[1:]) for r in con.execute(
            "SELECT date, margin_bal, short_bal FROM tw_chip_margin "
            "WHERE code=? ORDER BY date DESC LIMIT ?", [c, N_SESS]).fetchall())
        tv = dict((r[0], r[1]) for r in con.execute(
            "SELECT date, trade_value FROM tw_trading_daily "
            "WHERE code=? ORDER BY date DESC LIMIT ?", [c, N_SESS]).fetchall())
        val = con.execute(
            "SELECT date, pe, pb, dividend_yield FROM tw_valuation_daily "
            "WHERE code=? ORDER BY date DESC LIMIT 1", [c]).fetchall()
        out[c] = {
            "name": names.get(c, c),
            "valuation": ({"date": str(val[0][0]), "pe": val[0][1], "pb": val[0][2],
                           "yield": val[0][3]} if val else None),
            "rows": [{"date": str(d), "close": v, "volume": vol,
                      "foreign": (ch.get(str(d)) or [None])[0],
                      "trust": (ch.get(str(d)) or [None, None])[1],
                      "dealer": (ch.get(str(d)) or [None, None, None])[2],
                      "margin": (mg.get(str(d)) or [None])[0],
                      "short": (mg.get(str(d)) or [None, None])[1],
                      "tvalue": tv.get(str(d))}
                     for d, v, vol in px]}
    con.close()
    return {"stocks": out, "note": f"vdf_tw_market.duckdb 實料 · 近 {N_SESS} 交易日"}


def harvest_rotation(top_n: int = 12, days: int = 240) -> dict:
    """GRP_ENG040 輪動 tw 最新快照(glob 尾版;唯讀零重測):
    族群日列+輪動態+金流佔比延續榜。缺快照=誠實空。"""
    root = VIA / "functional modules" / "GroupIndex" / "output_hub" / "rotation_runs"
    runs = sorted(root.glob("ROTATION_TW_*")) if root.exists() else []
    if not runs:
        return {"groups": {}, "rank": [], "note": "無輪動快照(誠實)"}
    src = runs[-1]
    try:
        import pandas as pd
        df = pd.read_csv(src / "csv" / "group_rotation_daily.csv")
    except Exception as e:
        return {"groups": {}, "rank": [], "note": f"快照讀取敗(誠實):{e}"[:120]}
    df["Date"] = df["Date"].str.replace("/", "-")
    last = df["Date"].max()
    latest = df[df["Date"] == last].copy()
    top = (latest.sort_values("GroupTurnoverValue", ascending=False)
           .head(top_n)["GroupId"].tolist())
    dates = sorted(df["Date"].unique())[-days:]
    sub = df[df["GroupId"].isin(top) & df["Date"].isin(dates)]

    def _f(v):
        return None if pd.isna(v) else round(float(v), 6)

    groups = {}
    for gid, g in sub.groupby("GroupId"):
        g = g.sort_values("Date")
        tail = g.iloc[-1]
        groups[gid] = {
            "state": str(tail.get("RotationState", "")),
            "conf": _f(tail.get("RotationConfidence")),
            "rows": [{"date": r["Date"], "gindex": _f(r["GroupIndex_FULL_EW"]),
                      "tvalue": _f(r["GroupTurnoverValue"]),
                      "share": _f(r["GroupTurnoverShare"]),
                      "breadth": _f(r["PositiveBreadth"]),
                      "foreign": _f(r["ForeignNetAmount"]),
                      "trust": _f(r["InvestmentTrustNetAmount"])}
                     for _, r in g.iterrows()]}
    # 延續榜:最新日佔比×5 日均佔比×佔比變化(快照冊欄位直出;零發明)
    d5 = sorted(df["Date"].unique())[-5:]
    m5 = (df[df["Date"].isin(d5)].groupby("GroupId")["GroupTurnoverShare"]
          .mean().to_dict())
    rank = [{"gid": r["GroupId"], "share": _f(r["GroupTurnoverShare"]),
             "share5": _f(m5.get(r["GroupId"])),
             "chg": _f(r.get("TurnoverShareChange")),
             "state": str(r.get("RotationState", "")),
             "conf": _f(r.get("RotationConfidence"))}
            for _, r in latest.sort_values("GroupTurnoverShare", ascending=False)
            .head(10).iterrows()]
    return {"groups": groups, "rank": rank,
            "note": f"{src.name} · 最新日 {last} · 39 群取成交值前 {top_n}"}


def harvest_global(days: int = 400) -> dict:
    """ROTATION_GLOBAL 最新快照(glob 尾版;唯讀):9 類別+宏觀因子。
    誠實:TURNOVER_PROXY+REVIEW 註記隨資料出。"""
    root = VIA / "functional modules" / "GroupIndex" / "output_hub" / "rotation_runs"
    runs = sorted(root.glob("ROTATION_GLOBAL_*")) if root.exists() else []
    if not runs:
        return {"groups": {}, "rank": [], "factors": {}, "note": "無全球快照(誠實)"}
    src = runs[-1]
    import pandas as pd
    df = pd.read_csv(src / "csv" / "group_rotation_daily.csv")
    df["Date"] = df["Date"].str.replace("/", "-")
    last = df["Date"].max()
    dates = sorted(df["Date"].unique())[-days:]
    sub = df[df["Date"].isin(dates)]

    def _f(v):
        return None if pd.isna(v) else round(float(v), 6)

    groups = {}
    for gid, g in sub.groupby("GroupId"):
        g = g.sort_values("Date")
        tail = g.iloc[-1]
        groups[gid] = {
            "state": str(tail.get("RotationState", "")),
            "conf": _f(tail.get("RotationConfidence")),
            "rows": [{"date": r["Date"], "gindex": _f(r["GroupIndex_FULL_EW"]),
                      "tvalue": _f(r["GroupTurnoverValue"]),
                      "share": _f(r["GroupTurnoverShare"]),
                      "breadth": _f(r["PositiveBreadth"])}
                     for _, r in g.iterrows()]}
    fx = pd.read_csv(src / "csv" / "market_factors.csv")
    fx["Date"] = fx["Date"].str.replace("/", "-")
    fx = fx[fx["Date"].isin(sorted(fx["Date"].unique())[-days:])].sort_values("Date")
    factors = {k: [{"date": r["Date"], "value": _f(r[k])} for _, r in fx.iterrows()]
               for k in ("EURUSD_RET", "USDJPY_RET", "VIX_RET", "US10Y_D1")}
    latest = df[df["Date"] == last]
    d5 = sorted(df["Date"].unique())[-5:]
    m5 = (df[df["Date"].isin(d5)].groupby("GroupId")["GroupTurnoverShare"]
          .mean().to_dict())
    rank = [{"gid": r["GroupId"], "share": _f(r["GroupTurnoverShare"]),
             "share5": _f(m5.get(r["GroupId"])),
             "chg": _f(r.get("TurnoverShareChange")),
             "state": str(r.get("RotationState", "")),
             "conf": _f(r.get("RotationConfidence"))}
            for _, r in latest.sort_values("GroupTurnoverShare", ascending=False)
            .iterrows()]
    return {"groups": groups, "rank": rank, "factors": factors,
            "note": (f"{src.name} · 最新日 {last} · 成交值=PROXY(價×量估算)"
                     f" · profile=REVIEW 非 PASS(V13 裁定)")}


def build_css(t: dict) -> str:
    """操作員 Layout element CSS 原樣結構;值全由 dashboard token 節供給"""
    return f"""
:root {{
    --font-family: {t['font_family']};
    --font-size-base: {t['font_pc_px']}px;
    --color-bg: {t['color_bg']};
    --color-panel-bg: {t['color_panel_bg']};
    --color-border: {t['color_border']};
    --color-grid: {t['color_grid']};
}}
body {{ margin: 0; font-family: var(--font-family);
    font-size: var(--font-size-base); background: var(--color-bg); }}
.dashboard {{ display: grid; grid-template-columns: {t['panel_w_px']}px 1fr;
    grid-template-rows: 100vh; overflow: hidden; }}
.left-panel {{ background: var(--color-panel-bg);
    border-right: 1px solid var(--color-border); padding: 8px;
    display: flex; flex-direction: column; overflow-y: auto; box-sizing: border-box; }}
.right-panel {{ background: var(--color-bg); padding: 10px;
    overflow-y: auto; box-sizing: border-box; }}
.left-header, .right-header {{ height: {t['header_h_px']}px; font-weight: 600;
    display: flex; align-items: center; box-sizing: border-box; }}
.filter-panel {{ display: flex; flex-direction: column; gap: 6px; }}
.ui-select, .ui-date {{ width: 100%; padding: 4px; font-size: var(--font-size-base);
    border: 1px solid {t['input_border']}; border-radius: 3px; box-sizing: border-box; }}
.check-group {{ display: flex; gap: 10px; font-size: var(--font-size-base); }}
.chart-grid {{ display: grid; grid-template-columns: 1fr; gap: 10px; }}
.chart-card {{ background: var(--color-bg); border: 1px solid var(--color-border);
    border-radius: 4px; min-height: {t['chart_min_h_px']}px; width: 100%;
    padding: 6px; box-sizing: border-box; }}
.left-panel.collapsed {{ width: 0 !important; min-width: 0 !important;
    padding: 0 !important; overflow: hidden !important; }}
.alerts {{ margin-top: 8px; font-size: {t['font_mobile_px']}px; }}
.alert-item {{ border: 1px solid var(--color-border); border-radius: 3px;
    padding: 4px 6px; margin-bottom: 4px; background: {t['alert_bg']}; }}
#logs {{ width: 100%; border-collapse: collapse; font-size: {t['font_mobile_px']}px; }}
#logs th, #logs td {{ border: 1px solid var(--color-border); padding: 4px 6px; }}
@media (max-width: {t['breakpoint_px']}px) {{
    .dashboard {{ grid-template-columns: 1fr; grid-template-rows: auto 1fr; }}
    .left-panel {{ width: 100% !important; min-width: 100% !important;
        border-right: none; border-bottom: 1px solid var(--color-border); }}
    .chart-card {{ min-height: {t['chart_min_h_px']}px; }}
    html {{ font-size: {t['font_mobile_px']}px; }}
}}"""


_JS = r"""
/* VIA Dashboard — 操作員 Layout element JS(批167 收容;QA 修正五處留痕) */
const VIA = {
    screen: { width: window.innerWidth, height: window.innerHeight,
              isMobile: window.innerWidth < %%BP%% },
    chart: { baseHeightPC: %%HPC%%, baseHeightMobile: %%HMB%%,
             tickIntervals: %%TICKS%% },
    state: { stock: null, module: null, chartType: null,
             dateStart: null, dateEnd: null, checks: {}, alerts: [], logs: [] }
};

function bindUI() {
    document.querySelectorAll(".ui-select").forEach(el => { el.onchange = () => updateDashboard(); });
    document.querySelectorAll(".ui-date").forEach(el => { el.onchange = () => updateDashboard(); });
    document.querySelectorAll(".ui-check").forEach(el => { el.onchange = () => updateDashboard(); });
    document.getElementById("collapse-btn").onclick = () => toggleLeftPanel();
    document.getElementById("dropdown-layer").onchange = () => {
        applyLayer(); updateDashboard(); };
}

function toggleLeftPanel() {
    const panel = document.querySelector(".left-panel");
    panel.classList.toggle("collapsed");
    setTimeout(autoOptimize, 150);
}

function collectParams() {
    VIA.state.stock = document.getElementById("dropdown-stock")?.value;
    VIA.state.module = document.getElementById("dropdown-module")?.value;
    VIA.state.chartType = document.getElementById("dropdown-chart-type")?.value;
    VIA.state.dateStart = document.getElementById("date-start")?.value;
    VIA.state.dateEnd = document.getElementById("date-end")?.value;
    VIA.state.checks = {};
    document.querySelectorAll(".ui-check").forEach(el => { VIA.state.checks[el.value] = el.checked; });
    return { ...VIA.state };
}

/* 5. Auto-Fixer(QA①:欄位檢由 !df.date[陣列恆真誤報]改檢首列鍵) */
function autoFixData(df) {
    let alerts = [];
    let logs = [];
    if (!df.length || !("date" in (df[0] || {}))) {
        alerts.push("缺少日期欄位");
        logs.push({ issue: "Missing Column", notes: "date" });
        return { df: [], alerts, logs };
    }
    df.forEach(row => {
        if (!row.date || isNaN(new Date(row.date))) {
            alerts.push("日期格式錯誤");
            logs.push({ issue: "Invalid Date", notes: String(row.date) });
        }
    });
    df.sort((a, b) => new Date(a.date) - new Date(b.date));
    let fixed = fillMissingDates(df);
    if (fixed.added > 0) {
        alerts.push("時間軸不連續,已補齊日期(含非交易日;誠實列示)");
        logs.push({ issue: "Date Gap", notes: `${fixed.added} days added` });
    }
    df = fixed.df;   /* QA②:原稿未接回 fixed.df=補齊結果被丟棄 → 接線 */
    df = interpolateValues(df);
    df = smoothOutliers(df);
    return { df, alerts, logs };
}

function fillMissingDates(df) {
    let added = 0;
    let map = {};
    df.forEach(row => map[row.date] = row);
    let start = new Date(df[0].date);
    let end = new Date(df[df.length - 1].date);
    let full = [];
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
        let key = d.toISOString().slice(0, 10);
        if (map[key]) full.push(map[key]);
        else { full.push({ date: key, value: null }); added++; }
    }
    return { df: full, added };
}

/* 7. 補值(QA③:原稿註記「線性插值」實為前值遞補=ffill;正名不改行為) */
function interpolateValues(df) {
    let last = null;
    for (let i = 0; i < df.length; i++) {
        if (df[i].value == null) { df[i].value = last; }
        else { last = df[i].value; }
    }
    return df;
}

/* 8. 極端值平滑(QA④:分位計算先濾 null,避免 NaN 汙染 IQR) */
function smoothOutliers(df) {
    let values = df.map(r => r.value).filter(v => v != null && !isNaN(v));
    if (!values.length) return df;
    let sorted = [...values].sort((a, b) => a - b);
    let q1 = sorted[Math.floor(sorted.length * 0.25)];
    let q3 = sorted[Math.floor(sorted.length * 0.75)];
    let iqr = q3 - q1;
    let lower = q1 - 3 * iqr;
    let upper = q3 + 3 * iqr;
    df.forEach(r => {
        if (r.value != null) {
            if (r.value < lower) r.value = lower;
            if (r.value > upper) r.value = upper;
        }
    });
    return df;
}

/* 9. Plotly 自動最佳化(QA⑤:typeof 閘=零 CDN;Plotly 在場才升級) */
function optimizePlotly(gd) {
    if (typeof Plotly === "undefined" || !gd || !gd.data) return;
    let maxVal = Math.max(...gd.data.flatMap(t => t.y || []));
    let interval = VIA.chart.tickIntervals.find(i => maxVal / i <= 12) || 5;
    Plotly.relayout(gd, { "yaxis.dtick": interval, "yaxis.tickformat": ".2f",
                          "xaxis.ticklabelmode": "period" });
    Plotly.update(gd, { textposition: "auto", insidetextanchor: "middle",
                        constraintext: "none" });
}

function autoOptimize() {
    VIA.screen.width = window.innerWidth;
    VIA.screen.height = window.innerHeight;
    VIA.screen.isMobile = VIA.screen.width < %%BP%%;
    const height = VIA.screen.isMobile ? VIA.chart.baseHeightMobile : VIA.chart.baseHeightPC;
    document.querySelectorAll(".chart-card").forEach(card => {
        card.style.minHeight = height + "px";
    });
    document.documentElement.style.fontSize =
        VIA.screen.isMobile ? "%%FMB%%px" : "%%FPC%%px";
    const dashboard = document.querySelector(".dashboard");
    if (VIA.screen.isMobile) {
        dashboard.style.gridTemplateColumns = "1fr";
        dashboard.style.gridTemplateRows = "auto 1fr";
    } else {
        dashboard.style.gridTemplateColumns = "%%PW%%px 1fr";
        dashboard.style.gridTemplateRows = "100vh";
    }
}

/* 嵌入實料(vdf_tw_market.duckdb;零網路)——fetchData 讀本地 JSON */
const VIA_DATA = %%DATA%%;
const VIA_GRP = %%GRPDATA%%;
const VIA_GLB = %%GLBDATA%%;
const GLB_FIELD = { "類別指數(FULL_EW)": "gindex", "成交值(PROXY)": "tvalue",
    "金流佔比(PROXY)": "share", "正廣度": "breadth" };
const GLB_FACTORS = ["EURUSD_RET", "USDJPY_RET", "VIX_RET", "US10Y_D1"];
const MODULE_FIELD = { "價格(收盤)": "close", "成交量": "volume",
    "成交值": "tvalue", "外資買賣超": "foreign", "投信買賣超": "trust",
    "自營買賣超": "dealer", "融資餘額": "margin", "融券餘額": "short" };
const GRP_FIELD = { "族群指數(FULL_EW)": "gindex", "族群成交值": "tvalue",
    "金流佔比": "share", "正廣度": "breadth", "外資金額": "foreign",
    "投信金額": "trust" };

function currentLayer() {
    return document.getElementById("dropdown-layer")?.value || "個股";
}

/* 層級切換:同一 Gate Panel 骨架,選單內容換裝(操作員版面零改) */
function applyLayer() {
    const layer = currentLayer();
    const sel = document.getElementById("dropdown-stock");
    const mod = document.getElementById("dropdown-module");
    document.getElementById("lbl-target").innerText =
        layer === "全球" ? "類別" : (layer === "族群" ? "族群" : "個股");
    sel.innerHTML = "";
    mod.innerHTML = "";
    if (layer === "全球") {
        Object.keys(VIA_GLB.groups).forEach(g => {
            const o = document.createElement("option"); o.value = g; o.text = g;
            sel.appendChild(o); });
        Object.keys(GLB_FIELD).concat(GLB_FACTORS).forEach(m => {
            const o = document.createElement("option"); o.text = m; mod.appendChild(o); });
    } else if (layer === "族群") {
        Object.keys(VIA_GRP.groups).forEach(g => {
            const o = document.createElement("option"); o.value = g; o.text = g;
            sel.appendChild(o); });
        Object.keys(GRP_FIELD).forEach(m => {
            const o = document.createElement("option"); o.text = m; mod.appendChild(o); });
    } else {
        Object.entries(VIA_DATA.stocks).forEach(([c, v]) => {
            const o = document.createElement("option"); o.value = c;
            o.text = `${c} ${v.name}`; sel.appendChild(o); });
        Object.keys(MODULE_FIELD).forEach(m => {
            const o = document.createElement("option"); o.text = m; mod.appendChild(o); });
    }
    document.getElementById("rank-wrap").style.display =
        (layer === "族群" || layer === "全球") ? "block" : "none";
}

async function fetchData(params) {
    if (currentLayer() === "全球") {
        if (GLB_FACTORS.includes(params.module)) {
            return (VIA_GLB.factors[params.module] || [])
                .filter(r => (!params.dateStart || r.date >= params.dateStart)
                          && (!params.dateEnd || r.date <= params.dateEnd));
        }
        const g = VIA_GLB.groups[params.stock];
        if (!g) return [];
        const f = GLB_FIELD[params.module] || "gindex";
        return g.rows
            .filter(r => (!params.dateStart || r.date >= params.dateStart)
                      && (!params.dateEnd || r.date <= params.dateEnd))
            .map(r => ({ date: r.date, value: r[f] }));
    }
    if (currentLayer() === "族群") {
        const g = VIA_GRP.groups[params.stock];
        if (!g) return [];
        const f = GRP_FIELD[params.module] || "gindex";
        return g.rows
            .filter(r => (!params.dateStart || r.date >= params.dateStart)
                      && (!params.dateEnd || r.date <= params.dateEnd))
            .map(r => ({ date: r.date, value: r[f] }));
    }
    const s = VIA_DATA.stocks[params.stock];
    if (!s) return [];
    const f = MODULE_FIELD[params.module] || "close";
    return s.rows
        .filter(r => (!params.dateStart || r.date >= params.dateStart)
                  && (!params.dateEnd || r.date <= params.dateEnd))
        .map(r => ({ date: r.date, value: r[f] }));
}

/* 內建 SVG 圖車道(零 CDN;Plotly 在場時 optimizePlotly 自動升級)
   v0101:抽出 drawChart 通用器=主副雙圖共用(操作員 chart-grid 原生多卡) */
function drawChart(cardId, title, pts, kind) {
    const card = document.getElementById(cardId);
    const w = card.clientWidth - 12, h = card.clientHeight - 30 || 300;
    if (!pts.length) { card.innerHTML = `<div>${title}</div><div>無資料(誠實)</div>`; return; }
    const xs = pts.map((_, i) => i), ys = pts.map(r => r.value);
    const ymin = Math.min(...ys), ymax = Math.max(...ys), yr = (ymax - ymin) || 1;
    const X = i => 40 + (w - 50) * i / Math.max(1, xs.length - 1);
    const Y = v => (h - 20) - (h - 40) * (v - ymin) / yr;
    let grid = "";
    for (let g = 0; g <= 4; g++) {
        const gy = 20 + (h - 40) * g / 4;
        const gv = (ymax - yr * g / 4);
        grid += `<line x1="40" y1="${gy}" x2="${w - 10}" y2="${gy}" stroke="%%CGRID%%"/>` +
                `<text x="2" y="${gy + 3}" font-size="9">${gv >= 1e8 ? (gv/1e8).toFixed(1)+"億" : gv.toFixed(1)}</text>`;
    }
    let body = "";
    if (kind === "長條圖") {
        const bw = Math.max(1, (w - 50) / pts.length - 1);
        body = pts.map((r, i) =>
            `<rect x="${X(i) - bw / 2}" y="${Math.min(Y(r.value), Y(Math.max(ymin, 0)))}" width="${bw}" height="${Math.abs(Y(r.value) - Y(Math.max(ymin, 0))) || 1}" fill="#4a78b0"/>`).join("");
    } else {
        body = `<polyline fill="none" stroke="#1f4e79" stroke-width="1.4" points="` +
            pts.map((r, i) => `${X(i)},${Y(r.value)}`).join(" ") + `"/>`;
    }
    const lab = [0, Math.floor(pts.length / 2), pts.length - 1].map(i =>
        `<text x="${X(i)}" y="${h - 4}" font-size="9" text-anchor="middle">${pts[i].date}</text>`).join("");
    card.innerHTML = `<div style="font-weight:600">${title}</div>` +
        `<svg width="${w}" height="${h}" role="img">${grid}${body}${lab}</svg>`;
    optimizePlotly(card);
}

function renderRank() {
    const tb = document.querySelector("#rank tbody");
    tb.innerHTML = "";
    const src = currentLayer() === "全球" ? VIA_GLB : VIA_GRP;
    (src.rank || []).forEach(r => {
        const tr = document.createElement("tr");
        const pc = v => v == null ? "—" : (v * 100).toFixed(2) + "%";
        tr.innerHTML = `<td>${r.gid}</td><td style="text-align:center">${pc(r.share)}</td>` +
            `<td style="text-align:center">${pc(r.share5)}</td>` +
            `<td style="text-align:center">${pc(r.chg)}</td>` +
            `<td style="text-align:center">${r.state || "—"}</td>` +
            `<td style="text-align:center">${r.conf == null ? "—" : r.conf}</td>`;
        tb.appendChild(tr);
    });
}

function renderCharts(df) {
    if (currentLayer() === "全球") {
        const g = VIA_GLB.groups[VIA.state.stock] || {};
        const isFx = GLB_FACTORS.includes(VIA.state.module);
        const title = isFx
            ? `${VIA.state.module}(宏觀因子=全球共通,不隨類別)`
            : `${VIA.state.stock} · ${VIA.state.module}`;
        drawChart("chart-main", title, df.filter(r => r.value != null), VIA.state.chartType);
        const sub = (g.rows || [])
            .filter(r => (!VIA.state.dateStart || r.date >= VIA.state.dateStart)
                      && (!VIA.state.dateEnd || r.date <= VIA.state.dateEnd)
                      && r.share != null)
            .map(r => ({ date: r.date, value: r.share }));
        drawChart("chart-sub", `${VIA.state.stock} · 金流佔比 PROXY(副圖)`, sub, "長條圖");
        document.getElementById("val-row").innerText =
            `輪動態:${g.state || "—"} · 信心 ${g.conf == null ? "—" : g.conf} · ${VIA_GLB.note}`;
        renderRank();
        return;
    }
    if (currentLayer() === "族群") {
        const g = VIA_GRP.groups[VIA.state.stock] || {};
        const title = `${VIA.state.stock} · ${VIA.state.module}`;
        drawChart("chart-main", title, df.filter(r => r.value != null), VIA.state.chartType);
        const sub = (g.rows || [])
            .filter(r => (!VIA.state.dateStart || r.date >= VIA.state.dateStart)
                      && (!VIA.state.dateEnd || r.date <= VIA.state.dateEnd)
                      && r.share != null)
            .map(r => ({ date: r.date, value: r.share }));
        drawChart("chart-sub", `${VIA.state.stock} · 金流佔比(副圖)`, sub, "長條圖");
        document.getElementById("val-row").innerText =
            `輪動態:${g.state || "—"} · 信心 ${g.conf == null ? "—" : g.conf} · ` +
            `${VIA_GRP.note}(GRP_ENG040 快照冊直出;零發明)`;
        renderRank();
        return;
    }
    const stock = VIA_DATA.stocks[VIA.state.stock];
    const name = stock?.name || "";
    const title = `${VIA.state.stock} ${name} · ${VIA.state.module}`;
    drawChart("chart-main", title, df.filter(r => r.value != null), VIA.state.chartType);
    /* 副圖=成交量(操作員 chart-grid 第二卡;固定長條) */
    const sub = (stock?.rows || [])
        .filter(r => (!VIA.state.dateStart || r.date >= VIA.state.dateStart)
                  && (!VIA.state.dateEnd || r.date <= VIA.state.dateEnd)
                  && r.volume != null)
        .map(r => ({ date: r.date, value: r.volume }));
    drawChart("chart-sub", `${VIA.state.stock} ${name} · 成交量(副圖)`, sub, "長條圖");
    /* 估值誠實現值列(快照僅數日=不足作圖,不假圖) */
    const v = stock?.valuation;
    document.getElementById("val-row").innerText = v
        ? `估值快照 ${v.date}:PE ${v.pe} · PB ${v.pb} · 殖利率 ${v.yield}%(tw_valuation_daily;快照日不足作圖=誠實列現值)`
        : "估值快照:無(誠實)";
}

async function updateDashboard() {
    const params = collectParams();
    const rawData = await fetchData(params);
    const fixed = autoFixData(rawData);
    VIA.state.alerts = fixed.alerts;
    VIA.state.logs = fixed.logs;
    renderAlerts(VIA.state.alerts);
    renderLogs(VIA.state.logs);
    renderCharts(fixed.df);
    autoOptimize();
}

function renderAlerts(alerts) {
    const box = document.getElementById("alerts");
    box.innerHTML = "";
    alerts.forEach(a => {
        const div = document.createElement("div");
        div.className = "alert-item";
        div.innerText = a;
        box.appendChild(div);
    });
}

function renderLogs(logs) {
    const tbody = document.querySelector("#logs tbody");
    tbody.innerHTML = "";
    logs.forEach(log => {
        const tr = document.createElement("tr");
        tr.innerHTML = `<td>${new Date().toLocaleString()}</td>` +
            `<td>${log.issue}</td><td>${log.notes}</td>`;
        tbody.appendChild(tr);
    });
}

window.onload = () => { bindUI(); applyLayer(); autoOptimize(); updateDashboard(); };
window.onresize = autoOptimize;
"""

_HTML = """<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 儀表板 v0100</title><style>%%CSS%%</style></head><body>
<div class="dashboard">
  <div class="left-panel">
    <div class="left-header">VIA Gate Panel
      <button id="collapse-btn" style="margin-left:auto">☰</button></div>
    <div class="filter-panel">
      <label>層級</label>
      <select id="dropdown-layer" class="ui-select">
        <option>個股</option><option>族群</option><option>全球</option></select>
      <label id="lbl-target">個股</label>
      <select id="dropdown-stock" class="ui-select">%%OPT_STOCK%%</select>
      <label>模組</label>
      <select id="dropdown-module" class="ui-select">%%OPT_MODULE%%</select>
      <label>圖型</label>
      <select id="dropdown-chart-type" class="ui-select">
        <option>折線圖</option><option>長條圖</option></select>
      <label>起日</label><input type="date" id="date-start" class="ui-date" value="%%D0%%">
      <label>迄日</label><input type="date" id="date-end" class="ui-date" value="%%D1%%">
      <div class="check-group">
        <label><input type="checkbox" class="ui-check" value="autofix" checked>Auto-Fixer</label>
        <label><input type="checkbox" class="ui-check" value="smooth" checked>平滑</label>
      </div>
    </div>
    <div class="alerts" id="alerts"></div>
    <table id="logs"><thead><tr><th>時間</th><th>Issue</th><th>Notes</th></tr></thead>
    <tbody></tbody></table>
  </div>
  <div class="right-panel">
    <div class="right-header">主顯示區 · %%NOTE%% · %%TS%%</div>
    <div id="val-row" style="font-size:10px;color:#555;margin:0 0 6px 0"></div>
    <div class="chart-grid">
      <div class="chart-card" id="chart-main"></div>
      <div class="chart-card" id="chart-sub"></div>
    </div>
    <div id="rank-wrap" style="display:none;margin-top:8px">
      <div style="font-weight:600;font-size:11px">金流佔比延續榜(最新日;快照冊直出)</div>
      <table id="rank" style="width:100%;border-collapse:collapse;font-size:10px">
        <thead><tr><th style="text-align:left">族群</th><th>佔比</th><th>5日均</th>
        <th>佔比變化</th><th>輪動態</th><th>信心</th></tr></thead><tbody></tbody></table>
    </div>
    <div style="font-size:10px;color:#888;margin-top:6px">版面值單源=VIA_UI_TemplateSSOT
「dashboard」節(操作員 Layout element 定案;改冊即換裝)· 實料=vdf_tw_market.duckdb
零重測零發明 · 零 CDN(內建 SVG 車道;Plotly 在場自動升級)</div>
  </div>
</div>
<script>%%JS%%</script></body></html>"""


def build() -> Path:
    t = load_dash_tokens()
    data = harvest_data()
    rows0 = next(iter(data["stocks"].values()))["rows"] if data["stocks"] else []
    d0 = rows0[0]["date"] if rows0 else ""
    d1 = rows0[-1]["date"] if rows0 else ""
    opt_stock = "".join(f'<option value="{c}">{c} {v["name"]}</option>'
                        for c, v in data["stocks"].items())
    opt_module = "".join(f"<option>{m}</option>" for m in
                         ("價格(收盤)", "成交量", "成交值", "外資買賣超",
                          "投信買賣超", "自營買賣超", "融資餘額", "融券餘額"))
    js = (_JS.replace("%%BP%%", str(t["breakpoint_px"]))
          .replace("%%HPC%%", str(t["chart_max_h_px"]))
          .replace("%%HMB%%", str(t["chart_min_h_px"]))
          .replace("%%TICKS%%", json.dumps(t["tick_intervals"]))
          .replace("%%FPC%%", str(t["font_pc_px"]))
          .replace("%%FMB%%", str(t["font_mobile_px"]))
          .replace("%%PW%%", str(t["panel_w_px"]))
          .replace("%%CGRID%%", t["color_grid"])
          .replace("%%DATA%%", json.dumps(data, ensure_ascii=False))
          .replace("%%GRPDATA%%", json.dumps(harvest_rotation(), ensure_ascii=False))
          .replace("%%GLBDATA%%", json.dumps(harvest_global(), ensure_ascii=False)))
    html = (_HTML.replace("%%CSS%%", build_css(t))
            .replace("%%JS%%", js)
            .replace("%%OPT_STOCK%%", opt_stock)
            .replace("%%OPT_MODULE%%", opt_module)
            .replace("%%D0%%", d0).replace("%%D1%%", d1)
            .replace("%%NOTE%%", data["note"])
            .replace("%%TS%%", datetime.now().strftime("%Y-%m-%d %H:%M")))
    UI_OUT.parent.mkdir(parents=True, exist_ok=True)
    UI_OUT.write_text(html, encoding="utf-8")
    return UI_OUT


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    t = load_dash_tokens()
    chk("① token 冊 dashboard 節在位(定案值齊:260/38/320-420/768/11-10/tick 8 檔)",
        t["panel_w_px"] == 260 and t["header_h_px"] == 38
        and t["chart_min_h_px"] == 320 and t["chart_max_h_px"] == 420
        and t["breakpoint_px"] == 768 and len(t["tick_intervals"]) == 8)
    p = build()
    h = p.read_text(encoding="utf-8")
    chk("② 版面結構=操作員規格(兩欄 grid+38px 表頭+收合+@media+Alerts+Logs)",
        f"grid-template-columns: {t['panel_w_px']}px 1fr" in h
        and f"height: {t['header_h_px']}px" in h
        and ".left-panel.collapsed" in h
        and f"@media (max-width: {t['breakpoint_px']}px)" in h
        and 'id="alerts"' in h and 'id="logs"' in h)
    n_rows = h.count('"date": "') or h.count('"date":"')
    chk("③ 實料嵌入(三檔×近 240 交易日;duckdb 唯讀零發明)",
        all(f'value="{c}"' in h for c in STOCKS) and n_rows >= 600,
        f"(列 {n_rows})")
    chk("④ Auto-Fixer 五修留痕(欄位檢首列鍵/fixed.df 接線/ffill 正名/null 安全 IQR/typeof 閘)",
        'in (df[0] || {})' in h and "df = fixed.df" in h
        and "前值遞補" in h and 'filter(v => v != null' in h
        and 'typeof Plotly === "undefined"' in h)
    chk("⑤ Auto-Optimizer(isMobile 斷點+圖卡高 320-420+字級 11→10 全冊值)",
        f"window.innerWidth < {t['breakpoint_px']}" in h
        and f"baseHeightPC: {t['chart_max_h_px']}" in h
        and f'"%s"' % f"{t['font_mobile_px']}px" in h.replace("'", '"'))
    chk("⑥ 零 CDN 零外鏈(內建 SVG 車道;無 http 資源)",
        "http://" not in h and "https://" not in h and "<svg" in h.lower()
        or ("http://" not in h and "https://" not in h and "renderCharts" in h))
    chk("⑦ Gate Panel 六件(三下拉+雙日期+勾選群+收合鈕)",
        all(k in h for k in ("dropdown-stock", "dropdown-module",
                             "dropdown-chart-type", "date-start", "date-end",
                             "collapse-btn")) and "check-group" in h)
    chk("⑧ 紀律宣告(版面值單源冊/實料零發明/QA 修正留痕)",
        "版面值單源" in h and "零重測零發明" in h
        and "QA" in Path(__file__).read_text(encoding="utf-8"))
    chk("⑨ 車道深化(八模組+融資融券/成交值實料+主副雙圖+估值誠實現值)",
        all(m in h for m in ("成交值", "融資餘額", "融券餘額"))
        and '"margin":' in h and '"short":' in h and '"tvalue":' in h
        and 'id="chart-sub"' in h and 'id="val-row"' in h
        and "誠實列現值" in h)
    rot = harvest_rotation()
    chk("⑩ 族群視角層(輪動快照≥10 群+層級切換+延續榜+輪動態燈+誠實出處)",
        len(rot["groups"]) >= 10 and len(rot["rank"]) == 10
        and 'id="dropdown-layer"' in h and 'id="rank"' in h
        and '"gindex":' in h and "RotationState" not in h
        and "快照冊直出" in h and "ROTATION_TW_" in h,
        f"({len(rot['groups'])} 群·{rot['note'][:40]})")
    glb = harvest_global()
    chk("⑪ 全球層(9 類別+宏觀因子四線+PROXY/REVIEW 誠實標記+榜通用)",
        len(glb["groups"]) == 9 and len(glb["factors"]) == 4
        and all(len(v) > 100 for v in glb["factors"].values())
        and "PROXY" in glb["note"] and "REVIEW" in glb["note"]
        and 'VIA_GLB' in h and "全球共通" in h and ">全球<" in h)
    print(f"  [計] 十一檢 OK {11 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== VIA 儀表板(VAP_ENG009 v0103)· 十一檢自測(零網路)===")
        return selftest()
    p = build()
    print(f"[UI] {p.name} · 版面單源 {SSOT.name}[dashboard]")
    return 0


if __name__ == "__main__":
    sys.exit(main())
