#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL006_FinancialModel.py
================================================================================
  VERITAS DATA FRAMEWORK · Financial Model + PE/PB Band
  Version    : 1.0.0R  |  Module ID : VDF-MDL006

  重建R(2026-08-12「完成全部」令;工作站正本候上傳,到件即讓位)。
  5y daily + 三大報表×2頻 + 比率 + 估值快照 + PE/PB Band(統計表+Plotly 內嵌 HTML
  圖,零 CDN)。12 表 → 1-6-FinancialModel;圖 → charts/。資料源 yfinance;
  不可用=誠實中止不偽造。
================================================================================
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from VDF_MDL101_OutputManager import OutputManager

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

BASE_DIR = str(Path(__file__).parent / "db")

STMTS = [("income_statement", "income_stmt", "quarterly_income_stmt"),
         ("balance_sheet", "balance_sheet", "quarterly_balance_sheet"),
         ("cashflow", "cashflow", "quarterly_cashflow")]


def _cli_tickers():
    if "--tickers" in sys.argv:
        i = sys.argv.index("--tickers")
        if i + 1 < len(sys.argv):
            return [t.strip() for t in sys.argv[i + 1].split(",") if t.strip()]
    return ["2330"]


def _sym(code):
    return code + ".TW" if code.isdigit() else code


def _melt_stmt(df, ticker):
    """報表(列=項目,欄=期間)→ 長格式 ticker/period/item/value。"""
    rows = []
    if df is None or len(df) == 0:
        return rows
    for period in df.columns:
        pstr = str(getattr(period, "date", lambda: period)())
        for item in df.index:
            v = df.loc[item, period]
            try:
                v = float(v)
            except (TypeError, ValueError):
                continue
            rows.append({"ticker": ticker, "period": pstr,
                         "item": str(item), "value": v})
    return rows


def _pick(df_long, ticker, item):
    vals = [r["value"] for r in df_long
            if r["ticker"] == ticker and r["item"] == item]
    return vals[0] if vals else None


def _band_stats(series, ticker, kind):
    s = series.dropna()
    if len(s) == 0:
        return None
    q = s.quantile
    return {"ticker": ticker, "kind": kind, "n": int(len(s)),
            "min": float(s.min()), "p25": float(q(0.25)),
            "median": float(q(0.5)), "p75": float(q(0.75)),
            "max": float(s.max()), "current": float(s.iloc[-1])}


def _band_chart(dates, close, denom, ticker, kind, out_dir):
    """PE/PB Band:價格線 + 分位帶(denom×分位)。Plotly 內嵌零 CDN。"""
    ratio = close / denom
    st = _band_stats(ratio, ticker, kind)
    if st is None:
        return None
    fig = go.Figure()
    for lv, lab in (("min", "min"), ("p25", "P25"), ("median", "中位"),
                    ("p75", "P75"), ("max", "max")):
        fig.add_trace(go.Scatter(x=list(dates), y=[st[lv] * denom] * len(dates),
                                 mode="lines", name="%s %s=%.1f" % (kind.upper(), lab, st[lv]),
                                 line={"dash": "dot", "width": 1}))
    fig.add_trace(go.Scatter(x=list(dates), y=list(close), mode="lines",
                             name="Close", line={"width": 2}))
    fig.update_layout(title="%s %s Band" % (ticker, kind.upper()),
                      height=520, template="plotly_white")
    out = out_dir / ("%s_%s_band.html" % (ticker.replace(".", "_"), kind))
    fig.write_html(str(out), include_plotlyjs=True)  # 內嵌=單檔自足零 CDN
    return out, st


class FinancialModelEngine:
    def __init__(self):
        self.save_results = {}
        self.charts_saved = []

    def run(self):
        if not PANDAS_AVAILABLE:
            print("❌ pandas 未裝,中止")
            return 2
        if not YFINANCE_AVAILABLE or yf is None:
            print("❌ yfinance 不可用 — 誠實中止(pip install yfinance)")
            return 1
        codes = _cli_tickers()
        base = Path(BASE_DIR)
        chart_dir = base / "1-6-FinancialModel" / "charts"
        chart_dir.mkdir(parents=True, exist_ok=True)
        tabs = {"daily_history": [], "valuation_snapshot": [],
                "pe_band_stats": [], "pb_band_stats": [],
                "ratios_annual": [], "ratios_quarterly": []}
        for s, _a, _q in STMTS:
            tabs[s + "_annual"] = []
            tabs[s + "_quarterly"] = []
        errs = []
        for code in codes:
            sym = _sym(code)
            try:
                t = yf.Ticker(sym)
                info = t.info or {}
                hist = t.history(period="5y", interval="1d")
                h = hist.reset_index().rename(columns={"index": "date", "Date": "date"})
                h["ticker"] = code
                tabs["daily_history"] += h.to_dict("records")
                for s, attr_a, attr_q in STMTS:
                    tabs[s + "_annual"] += _melt_stmt(getattr(t, attr_a), code)
                    tabs[s + "_quarterly"] += _melt_stmt(getattr(t, attr_q), code)
                for freq in ("annual", "quarterly"):
                    isl = tabs["income_statement_" + freq]
                    bsl = tabs["balance_sheet_" + freq]
                    rev = _pick(isl, code, "Total Revenue")
                    gp = _pick(isl, code, "Gross Profit")
                    ni = _pick(isl, code, "Net Income")
                    eq = _pick(bsl, code, "Stockholders Equity")
                    ta = _pick(bsl, code, "Total Assets")
                    tabs["ratios_" + freq].append({
                        "ticker": code,
                        "gross_margin": (gp / rev) if gp and rev else None,
                        "net_margin": (ni / rev) if ni and rev else None,
                        "roe": (ni / eq) if ni and eq else None,
                        "roa": (ni / ta) if ni and ta else None,
                        "equity_ratio": (eq / ta) if eq and ta else None})
                tabs["valuation_snapshot"].append({
                    "ticker": code, "name": info.get("shortName"),
                    "currency": info.get("currency"),
                    "price": info.get("currentPrice"),
                    "eps_trailing": info.get("trailingEps"),
                    "eps_forward": info.get("forwardEps"),
                    "per_trailing": info.get("trailingPE"),
                    "per_forward": info.get("forwardPE"),
                    "book_value": info.get("bookValue"),
                    "pb": info.get("priceToBook"),
                    "ps": info.get("priceToSalesTrailing12Months"),
                    "ev_ebitda": info.get("enterpriseToEbitda"),
                    "dps": info.get("dividendRate"),
                    "dividend_yield": info.get("dividendYield"),
                    "market_cap": info.get("marketCap")})
                dates = h["date"] if "date" in h else h.iloc[:, 0]
                close = h["Close"]
                if PLOTLY_AVAILABLE:
                    eps = info.get("trailingEps")
                    if eps:
                        r = _band_chart(dates, close, float(eps), code, "pe", chart_dir)
                        if r:
                            self.charts_saved.append(str(r[0]))
                            tabs["pe_band_stats"].append(r[1])
                    bv = info.get("bookValue")
                    if bv:
                        r = _band_chart(dates, close, float(bv), code, "pb", chart_dir)
                        if r:
                            self.charts_saved.append(str(r[0]))
                            tabs["pb_band_stats"].append(r[1])
                else:
                    errs.append("plotly 未裝 — band 圖誠實略過")
            except Exception as e:
                errs.append("%s:%s" % (sym, str(e)[:80]))
        mgr = OutputManager(base_dir=BASE_DIR, output_dir="1-6-FinancialModel",
                            duckdb_filename="VDF_MDL006_FinancialModel.duckdb")
        for name, rows in tabs.items():
            self.save_results[name] = mgr.save(name, pd.DataFrame(rows))
        tot = sum(r["rows"] for r in self.save_results.values())
        print("MDL006:%d 表 · %s 列 · %d charts · errors=%d"
              % (len(self.save_results), "{:,}".format(tot),
                 len(self.charts_saved), len(errs)))
        for e in errs[:5]:
            print("   ⚠ %s" % e)
        return 0 if tot > 0 else 1


if __name__ == "__main__":
    ec = FinancialModelEngine().run()
    if "--no-pause" not in sys.argv:
        try:
            input("\n按 Enter 鍵退出...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(ec)
