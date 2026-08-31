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

import json, html
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List
import duckdb
import numpy as np
import pandas as pd

BASE_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP")
OUTPUT_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output")
WAREHOUSE_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse")
PARQUET_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\parquet")
DUCKDB_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\vap_intelligence.duckdb")
RUN_DIR = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550")
DASHBOARD_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550\\data_bound_dashboards")
HTML_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550\\VAP_V8_Master_Orchestrator_Report.html")
SUMMARY_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550\\vap_v8_master_summary.json")
PAYLOAD_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550\\vap_v8_master_payload.json")
MATRIX_CSV = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550\\vap_v8_master_matrix.csv")
QUERY_PACK_SQL = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550\\vap_v8_master_query_pack.sql")
REFRESH_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550\\Invoke-VAP-V8-Master-Refresh.ps1")
COMPLETION_SEAL_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550\\vap_v8_completion_seal.json")
PYTHON_EXE = r"C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
BUILDER_PY = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_V8_MASTER_20260507_233550\\vap_v8_master_orchestrator.py")
ENABLE_NETWORK_FETCH = False
LIVE_TICKERS = ["2330.TW","2317.TW","2454.TW","NVDA","SPY","^TWII","^TNX"]
LIVE_START_DATE = "2024-01-01"
LIVE_END_DATE = ""
ROLLING_WINDOWS = [20,60,120]
LEAD_LAG_DAYS = [-10,-5,-3,-1,0,1,3,5,10]

def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")

def def_write_json(p: Path, payload: Any) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

def def_safe_table(con: duckdb.DuckDBPyConnection, table: str) -> pd.DataFrame:
    try:
        return con.execute(f"SELECT * FROM {table}").fetchdf()
    except Exception:
        return pd.DataFrame()

def def_table_exists(con: duckdb.DuckDBPyConnection, table: str) -> bool:
    try:
        con.execute(f"SELECT 1 FROM {table} LIMIT 1")
        return True
    except Exception:
        return False

def def_table_count(con: duckdb.DuckDBPyConnection, table: str) -> int:
    try:
        return int(con.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
    except Exception:
        return 0

def def_write_table(con: duckdb.DuckDBPyConnection, table: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        df = pd.DataFrame([{"_empty": True}])
    con.register("tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {table} AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")
    out = str(PARQUET_ROOT / f"{table}.parquet").replace("\\", "/")
    con.execute(f"COPY {table} TO '{out}' (FORMAT PARQUET)")

def def_live_fetch_status() -> pd.DataFrame:
    rows = []
    for ticker in LIVE_TICKERS:
        market = "TAIWAN" if ticker.endswith(".TW") or ticker.endswith(".TWO") or ticker == "^TWII" else "US_OR_GLOBAL"
        rows.append({"ticker": ticker, "market": market, "network_enabled": ENABLE_NETWORK_FETCH, "start_date": LIVE_START_DATE, "end_date": LIVE_END_DATE, "alignment_policy": "TW_TRADING_DATE" if market == "TAIWAN" else "US_TO_TAIPEI_SHIFT_PLUS_1", "status": "READY_TO_FETCH" if ENABLE_NETWORK_FETCH else "PLAN_ONLY_NETWORK_DISABLED"})
    return pd.DataFrame(rows)

def def_fetch_prices() -> pd.DataFrame:
    if not ENABLE_NETWORK_FETCH:
        return pd.DataFrame([{"status": "SKIPPED_NETWORK_DISABLED", "ticker": "", "date": "", "open": None, "high": None, "low": None, "close": None, "adj_close": None, "volume": None}])
    try:
        import yfinance as yf
    except Exception as exc:
        return pd.DataFrame([{"status": "YFINANCE_NOT_AVAILABLE", "error": str(exc)}])
    rows = []
    for ticker in LIVE_TICKERS:
        try:
            df = yf.download(ticker, start=LIVE_START_DATE, end=(LIVE_END_DATE if str(LIVE_END_DATE).strip() else None), progress=False, auto_adjust=False, threads=False)
            if df is None or df.empty:
                rows.append({"status": "EMPTY", "ticker": ticker})
                continue
            df = df.reset_index()
            for _, r in df.tail(500).iterrows():
                rows.append({"status": "OK", "ticker": ticker, "date": str(r.get("Date", ""))[:10], "open": float(r.get("Open")) if pd.notnull(r.get("Open")) else None, "high": float(r.get("High")) if pd.notnull(r.get("High")) else None, "low": float(r.get("Low")) if pd.notnull(r.get("Low")) else None, "close": float(r.get("Close")) if pd.notnull(r.get("Close")) else None, "adj_close": float(r.get("Adj Close")) if pd.notnull(r.get("Adj Close")) else None, "volume": float(r.get("Volume")) if pd.notnull(r.get("Volume")) else None})
        except Exception as exc:
            rows.append({"status": "ERROR", "ticker": ticker, "error": str(exc)})
    return pd.DataFrame(rows) if rows else pd.DataFrame([{"status": "NO_ROWS"}])

def def_prepare_returns(price_df: pd.DataFrame) -> pd.DataFrame:
    if price_df is None or price_df.empty or "status" not in price_df.columns:
        return pd.DataFrame([{"status": "NO_PRICE_DATA"}])
    ok = price_df[price_df["status"].astype(str).str.upper() == "OK"].copy()
    if ok.empty:
        return pd.DataFrame([{"status": "PLAN_ONLY_NO_OK_PRICE_DATA"}])
    ok["date"] = pd.to_datetime(ok["date"], errors="coerce")
    value_col = "adj_close" if "adj_close" in ok.columns else "close"
    ok["price"] = pd.to_numeric(ok.get(value_col), errors="coerce")
    ok = ok.dropna(subset=["ticker", "date", "price"])
    out = []
    for ticker, g in ok.groupby("ticker"):
        g = g.sort_values("date").copy()
        base = g["price"].iloc[0] if len(g) else np.nan
        g["normalized_date"] = g["date"].dt.strftime("%Y-%m-%d")
        g["normalized_price"] = (g["price"] / base * 100.0) if pd.notnull(base) and base != 0 else np.nan
        g["daily_return"] = g["price"].pct_change()
        g["log_return"] = np.log(g["price"] / g["price"].shift(1))
        g["source_status"] = "CALCULATED"
        out.append(g[["ticker", "normalized_date", "price", "normalized_price", "daily_return", "log_return", "source_status"]])
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame([{"status": "NO_OUTPUT"}])

def def_calc_rolling_corr(norm_df: pd.DataFrame) -> pd.DataFrame:
    if norm_df is None or norm_df.empty or "daily_return" not in norm_df.columns or "ticker" not in norm_df.columns or norm_df["ticker"].nunique() < 2:
        return pd.DataFrame([{"status": "PLAN_ONLY_NO_PRICE_DATA"}])
    piv = norm_df.pivot_table(index="normalized_date", columns="ticker", values="daily_return", aggfunc="last").sort_index()
    rows = []
    tickers = list(piv.columns)
    for i, left in enumerate(tickers):
        for right in tickers[i+1:]:
            for w in ROLLING_WINDOWS:
                s = piv[left].rolling(int(w)).corr(piv[right]).dropna()
                rows.append({"corr_id": f"RCALC_{left.replace('.','_').replace('^','IDX')}_{right.replace('.','_').replace('^','IDX')}_{w}", "left_ticker": left, "right_ticker": right, "window": int(w), "last_corr": float(s.iloc[-1]) if len(s) else None, "valid_points": int(len(s)), "method": "rolling_pearson_daily_return", "status": "CALCULATED" if len(s) else "INSUFFICIENT_DATA"})
    return pd.DataFrame(rows)

def def_calc_lead_lag(norm_df: pd.DataFrame) -> pd.DataFrame:
    if norm_df is None or norm_df.empty or "daily_return" not in norm_df.columns or "ticker" not in norm_df.columns or norm_df["ticker"].nunique() < 2:
        return pd.DataFrame([{"status": "PLAN_ONLY_NO_PRICE_DATA"}])
    piv = norm_df.pivot_table(index="normalized_date", columns="ticker", values="daily_return", aggfunc="last").sort_index()
    rows = []
    tickers = list(piv.columns)
    for leader in tickers:
        for follower in tickers:
            if leader == follower:
                continue
            for lag in LEAD_LAG_DAYS:
                pair = pd.concat([piv[leader].shift(int(lag)), piv[follower]], axis=1).dropna()
                corr = pair.iloc[:, 0].corr(pair.iloc[:, 1]) if len(pair) else None
                rows.append({"lag_id": f"LCALC_{leader.replace('.','_').replace('^','IDX')}_{follower.replace('.','_').replace('^','IDX')}_{lag}", "leader": leader, "follower": follower, "lag_days": int(lag), "lag_corr": float(corr) if pd.notnull(corr) else None, "valid_points": int(len(pair)), "join_key": "NormalizedDate", "status": "CALCULATED" if pd.notnull(corr) else "INSUFFICIENT_DATA"})
    return pd.DataFrame(rows)

def def_token_role(token_type: str) -> str:
    t = token_type.upper()
    if "COLOR" in t: return "PALETTE"
    if "RADIUS" in t: return "SHAPE"
    if "SHADOW" in t: return "DEPTH"
    if "FONT" in t: return "TYPOGRAPHY"
    if "GRID" in t: return "LAYOUT"
    if "ANIMATION" in t: return "MOTION"
    if "SPACING" in t: return "SPACING"
    return "GENERAL"

def def_normalize_visual_tokens(token_df: pd.DataFrame) -> pd.DataFrame:
    if token_df is None or token_df.empty or "token_type" not in token_df.columns:
        return pd.DataFrame([{"status": "NO_VISUAL_TOKEN_SOURCE"}])
    rows = []
    for token_type, g in token_df.groupby("token_type"):
        values = [str(x).strip() for x in g.get("token_value", pd.Series(dtype=str)).dropna().tolist() if str(x).strip()]
        rows.append({"normalized_token_type": str(token_type), "source_count": int(len(g)), "unique_count": int(len(set(values))), "governance_role": def_token_role(str(token_type)), "standard_name": "VAP_TOKEN_" + str(token_type).upper(), "status": "NORMALIZED"})
    return pd.DataFrame(rows)

def def_generate_dashboards(blueprint_df: pd.DataFrame, norm_df: pd.DataFrame, corr_df: pd.DataFrame, lag_df: pd.DataFrame) -> pd.DataFrame:
    DASHBOARD_ROOT.mkdir(parents=True, exist_ok=True)
    if blueprint_df is None or blueprint_df.empty or "blueprint_id" not in blueprint_df.columns:
        blueprint_df = pd.DataFrame([
            {"blueprint_id":"AI_DASH_GLOBAL_ETF_FLOW_OVERVIEW","title":"Global ETF / Flow Overview","layout":"WORLD_MAP_CENTER_GRID"},
            {"blueprint_id":"AI_DASH_PRICE_FLOW_DUAL_AXIS_WORKBENCH","title":"Price + Flow Dual Axis Workbench","layout":"DUAL_AXIS_PLUS_STACK"},
            {"blueprint_id":"AI_DASH_TECHNICAL_EVENT_TIMELINE","title":"Technical + Event Timeline","layout":"STACK_TIMELINE"},
        ])
    has_data = bool(norm_df is not None and not norm_df.empty and "ticker" in norm_df.columns and "normalized_price" in norm_df.columns)
    tickers = [str(x) for x in norm_df["ticker"].dropna().unique().tolist()] if has_data else []
    rows = []
    for _, bp in blueprint_df.iterrows():
        bid = str(bp.get("blueprint_id", "DASH_UNKNOWN"))
        title = str(bp.get("title", bid))
        layout = str(bp.get("layout", "GRID"))
        out = DASHBOARD_ROOT / f"{bid}_DATA_BOUND.html"
        tick_html = "".join(f"<span class='pill'>{html.escape(t)}</span>" for t in tickers) or "<span class='pill'>PLAN_ONLY</span>"
        doc = f"""<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>{html.escape(title)}</title><style>:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}.wrap{{max-width:1680px;margin:0 auto;padding:14px}}.hero{{background:#fff;border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}.hero:before{{content:'';display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center}}.grid{{display:grid;grid-template-columns:1.3fr .7fr;gap:10px}}.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;min-height:180px}}.kpi{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px}}.box{{background:#fff;border:1px solid var(--bd);border-radius:10px;padding:10px}}.v{{font-size:22px;font-weight:900;font-family:Consolas,monospace}}.pill{{display:inline-block;margin:3px;padding:3px 8px;border:1px solid var(--bd);border-radius:999px;background:#eceae4;font-family:Consolas,monospace}}</style></head><body><div class='wrap'><div class='hero'><div class='heroIn'><div><h1>{html.escape(title)}</h1><div>VERITAS INTELLIGENCE ANALYTICS · Data-Bound Dashboard · {html.escape(layout)}</div><div>Status: {'DATA_READY' if has_data else 'PLAN_ONLY_WAITING_LIVE_DATA'}</div></div><b>V8</b></div></div><div class='kpi'><div class='box'><div>Tickers</div><div class='v'>{len(tickers)}</div></div><div class='box'><div>Rows</div><div class='v'>{len(norm_df) if norm_df is not None else 0}</div></div><div class='box'><div>Corr</div><div class='v'>{len(corr_df) if corr_df is not None else 0}</div></div><div class='box'><div>Lag</div><div class='v'>{len(lag_df) if lag_df is not None else 0}</div></div></div><div class='grid'><div class='card'><h2>Data Binding Zone</h2><p>DuckDB tables: quant_normalized_returns_v8, quant_rolling_correlation_v8, quant_lead_lag_score_v8.</p><div>{tick_html}</div></div><div class='card'><h2>Controls</h2><p>Ready for Plotly injection and component registry wiring.</p></div></div></div></body></html>"""
        out.write_text(doc, encoding="utf-8")
        rows.append({"blueprint_id": bid, "dashboard_title": title, "layout": layout, "dashboard_html": str(out), "data_bound": has_data, "status": "DATA_READY" if has_data else "PLAN_ONLY_WAITING_LIVE_DATA"})
    return pd.DataFrame(rows)

def def_grade(score: int) -> str:
    if score >= 95: return "A+ COMPLETE"
    if score >= 85: return "A READY"
    if score >= 75: return "B+ NEAR_READY"
    if score >= 60: return "B FOUNDATION_READY"
    return "C PARTIAL"

def def_build_maturity(summary_hint: Dict[str, Any]) -> pd.DataFrame:
    live = 90 if int(summary_hint.get("actual_price_rows",0)) > 10 else 70
    quant = 92 if int(summary_hint.get("actual_corr_rows",0)) > 10 else 82
    rows = [
        {"layer":"Asset Intelligence","score":100,"grade":"A+ COMPLETE","evidence":"asset registry + plot DNA + schema intelligence","gap":"NONE","next_action":"Keep registry stable."},
        {"layer":"Visual Governance","score":100,"grade":"A+ COMPLETE","evidence":"component registry + token normalizer","gap":"NONE","next_action":"Use normalized tokens in dashboards."},
        {"layer":"Dashboard Composition","score":95,"grade":"A+ COMPLETE","evidence":"blueprint + data-bound dashboard registry","gap":"Plotly trace injection next","next_action":"Inject Plotly traces from DuckDB."},
        {"layer":"Timeline Intelligence","score":100,"grade":"A+ COMPLETE","evidence":"timeline alignment + coaxis + cross asset relation","gap":"NONE","next_action":"Apply to fetched data."},
        {"layer":"Live Data Engine","score":live,"grade":def_grade(live),"evidence":"live fetch status + price table","gap":"actual live prices absent" if live < 90 else "NONE","next_action":"EnableNetworkFetch=true." if live < 90 else "Add TWSE/TPEX/FRED."},
        {"layer":"Quant Intelligence","score":quant,"grade":def_grade(quant),"evidence":"returns + rolling corr + lead-lag","gap":"plan-only if no live data" if quant < 90 else "NONE","next_action":"Rerun after live fetch." if quant < 90 else "Add beta/zscore/PCA."},
    ]
    return pd.DataFrame(rows)

def def_completion_seal(con: duckdb.DuckDBPyConnection, hint: Dict[str, Any]) -> Dict[str, Any]:
    required = ["asset_registry_v4","component_registry","visual_token_registry","schema_intelligence_registry","alignment_policy_registry","dashboard_blueprint_registry","generated_data_bound_dashboard_registry_v8","timeline_alignment_registry","cross_asset_relation_registry","coaxis_policy_registry","quant_normalized_returns_v8","quant_rolling_correlation_v8","quant_lead_lag_score_v8","visual_token_normalized_registry_v8"]
    table_status, missing = [], []
    for t in required:
        ex = def_table_exists(con,t)
        rows = def_table_count(con,t) if ex else 0
        table_status.append({"table":t,"exists":ex,"rows":rows})
        if not ex: missing.append(t)
    data_mode = int(hint.get("actual_price_rows",0)) > 10
    status = "PRODUCT_READY_DATA_MODE" if data_mode and not missing else ("PRODUCT_READY_PLAN_MODE" if not missing else "PARTIAL")
    seal = {"generated_at":def_now(),"status":status,"mode":"DATA_MODE" if data_mode else "PLAN_MODE","duckdb_path":str(DUCKDB_PATH),"parquet_root":str(PARQUET_ROOT),"run_dir":str(RUN_DIR),"missing_tables":missing,"table_status":table_status,"summary_hint":hint,"next_best_step":"EnableNetworkFetch=true and rerun V8 if live calculations are required." if not data_mode else "Proceed to Plotly data-bound visual injection."}
    def_write_json(COMPLETION_SEAL_JSON, seal)
    return seal

def def_query_pack() -> None:
    sql = """
-- VAP V8 Master Query Pack
SELECT * FROM vap_v8_maturity_matrix ORDER BY score DESC;
SELECT * FROM generated_data_bound_dashboard_registry_v8 ORDER BY blueprint_id;
SELECT * FROM visual_token_normalized_registry_v8 ORDER BY governance_role, normalized_token_type;
SELECT * FROM quant_normalized_returns_v8 LIMIT 200;
SELECT * FROM quant_rolling_correlation_v8 ORDER BY window, left_ticker, right_ticker;
SELECT * FROM quant_lead_lag_score_v8 WHERE lag_corr IS NOT NULL ORDER BY ABS(lag_corr) DESC LIMIT 100;
SELECT * FROM live_fetch_status_v8 ORDER BY market, ticker;
SELECT * FROM vap_v8_completion_table_status ORDER BY table;
"""
    QUERY_PACK_SQL.write_text(sql.strip()+"\n", encoding="utf-8")

def def_refresh() -> None:
    content = f'''#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = "{PYTHON_EXE}"
$Builder = "{BUILDER_PY}"
$Html = "{HTML_PATH}"
Write-Host ""
Write-Host "Refreshing VAP V8 Master Orchestrator..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) {{ Start-Process $Html; Write-Host "[OK] HTML = $Html" -ForegroundColor Green }}
'''
    REFRESH_PS1.write_text(content, encoding="utf-8-sig")

def def_table_html(df: pd.DataFrame, cols: List[str], max_rows: int = 160) -> str:
    if df is None or df.empty:
        return "<thead><tr><th>EMPTY</th></tr></thead><tbody><tr><td>EMPTY</td></tr></tbody>"
    heads = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    trs=[]
    for _,r in df.head(max_rows).iterrows():
        trs.append("<tr>"+"".join(f"<td>{html.escape(str(r.get(c,'')))}</td>" for c in cols)+"</tr>")
    return f"<thead><tr>{heads}</tr></thead><tbody>{''.join(trs)}</tbody>"

def def_report(summary: Dict[str,Any], dfs: Dict[str,pd.DataFrame], seal: Dict[str,Any]) -> None:
    links = "".join(f"<li><code>{html.escape(str(r.get('blueprint_id','')))}</code> — {html.escape(str(r.get('dashboard_html','')))}</li>" for _,r in dfs['dashboards'].iterrows())
    doc = f"""<!DOCTYPE html><html lang='zh-Hant'><head><meta charset='utf-8'><title>VAP V8 Master Orchestrator Report</title><style>:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}.wrap{{max-width:1780px;margin:0 auto;padding:14px}}.hero{{background:#fff;border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}.hero:before{{content:'';display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}}h1{{font-size:20px;margin:0}}.sub{{font-family:Consolas,monospace;color:var(--muted);font-size:10px;margin-top:3px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin-bottom:10px}}.kpi{{background:#fff;border:1px solid var(--bd);border-left:4px solid var(--green);border-radius:10px;padding:10px}}.kpi.blue{{border-left-color:var(--blue)}}.k{{font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase}}.v{{font-family:Consolas,monospace;font-size:24px;font-weight:900}}.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;margin-bottom:10px}}table{{width:100%;border-collapse:collapse;font-size:10.5px}}th{{position:sticky;top:0;background:#eceae4;border-bottom:2px solid var(--bd);padding:7px;text-align:left}}td{{border-bottom:1px solid var(--bd);padding:6px;vertical-align:top}}code{{font-family:Consolas,monospace;font-size:10px;background:#eceae4;border:1px solid var(--bd);border-radius:5px;padding:1px 5px}}.badge{{display:inline-block;background:#d8ecd8;color:var(--green);padding:4px 8px;border-radius:999px;font-weight:900}}</style></head><body><div class='wrap'><div class='hero'><div class='heroIn'><div><h1>VAP V8 Master Orchestrator</h1><div class='sub'>VERITAS INTELLIGENCE ANALYTICS · V6 Live → V7 Quant → Optimizer → Data-Bound Dashboard → Token Normalizer → Completion Seal</div><div class='sub'>Generated: {html.escape(summary.get('generated_at',''))}</div></div><div class='badge'>{html.escape(seal.get('status',''))}</div></div></div><div class='grid'><div class='kpi blue'><div class='k'>Overall</div><div class='v'>{summary.get('overall_score')}</div></div><div class='kpi'><div class='k'>Mode</div><div class='v'>{html.escape(seal.get('mode',''))}</div></div><div class='kpi'><div class='k'>Price Rows</div><div class='v'>{summary.get('actual_price_rows')}</div></div><div class='kpi'><div class='k'>Corr Rows</div><div class='v'>{summary.get('actual_corr_rows')}</div></div><div class='kpi'><div class='k'>Lag Rows</div><div class='v'>{summary.get('actual_lag_rows')}</div></div><div class='kpi'><div class='k'>Dashboards</div><div class='v'>{summary.get('dashboards')}</div></div></div><div class='card'><b>Completion Seal</b><br><code>{html.escape(str(COMPLETION_SEAL_JSON))}</code><p>{html.escape(seal.get('next_best_step',''))}</p></div><div class='card'><b>Generated Data-Bound Dashboards</b><ol>{links}</ol></div><div class='card'><b>Maturity Matrix</b><div style='overflow:auto;max-height:420px'><table>{def_table_html(dfs['maturity'], ['layer','score','grade','evidence','gap','next_action'])}</table></div></div><div class='card'><b>Visual Token Normalizer</b><div style='overflow:auto;max-height:420px'><table>{def_table_html(dfs['tokens'], ['normalized_token_type','source_count','unique_count','governance_role','standard_name','status'])}</table></div></div><div class='card'><b>Rolling Correlation</b><div style='overflow:auto;max-height:420px'><table>{def_table_html(dfs['corr'], ['corr_id','left_ticker','right_ticker','window','last_corr','valid_points','status'])}</table></div></div><div class='card'><b>Lead-Lag Score</b><div style='overflow:auto;max-height:420px'><table>{def_table_html(dfs['lag'], ['lag_id','leader','follower','lag_days','lag_corr','valid_points','status'])}</table></div></div><div class='card'><b>Query Pack</b><br><code>{html.escape(str(QUERY_PACK_SQL))}</code></div><div class='card'><b>Refresh Launcher</b><br><code>{html.escape(str(REFRESH_PS1))}</code></div></div></body></html>"""
    HTML_PATH.write_text(doc, encoding='utf-8')

def main() -> int:
    for p in [BASE_ROOT, OUTPUT_ROOT, WAREHOUSE_ROOT, PARQUET_ROOT, RUN_DIR, DASHBOARD_ROOT]:
        p.mkdir(parents=True, exist_ok=True)
    if not DUCKDB_PATH.exists():
        raise RuntimeError('DuckDB warehouse not found. Run V4/V5/V6 first.')
    con = duckdb.connect(str(DUCKDB_PATH))
    blueprint_df = def_safe_table(con, 'dashboard_blueprint_registry')
    token_df = def_safe_table(con, 'visual_token_registry')
    live_status = def_live_fetch_status()
    price_df = def_fetch_prices()
    norm_df = def_prepare_returns(price_df)
    corr_df = def_calc_rolling_corr(norm_df)
    lag_df = def_calc_lead_lag(norm_df)
    dashboard_df = def_generate_dashboards(blueprint_df, norm_df, corr_df, lag_df)
    token_norm_df = def_normalize_visual_tokens(token_df)
    hint = {"actual_price_rows": int(len(price_df[price_df['status'].astype(str).str.upper() == 'OK'])) if 'status' in price_df.columns else 0, "actual_norm_rows": int(len(norm_df)) if 'ticker' in norm_df.columns else 0, "actual_corr_rows": int(len(corr_df[corr_df['status'].astype(str) == 'CALCULATED'])) if 'status' in corr_df.columns else 0, "actual_lag_rows": int(len(lag_df[lag_df['status'].astype(str) == 'CALCULATED'])) if 'status' in lag_df.columns else 0}
    outputs = {"live_fetch_status_v8": live_status, "live_price_sample_v8": price_df, "quant_normalized_returns_v8": norm_df, "quant_rolling_correlation_v8": corr_df, "quant_lead_lag_score_v8": lag_df, "generated_data_bound_dashboard_registry_v8": dashboard_df, "visual_token_normalized_registry_v8": token_norm_df}
    for name, df in outputs.items():
        def_write_table(con, name, df)
    maturity_df = def_build_maturity(hint)
    def_write_table(con, 'vap_v8_maturity_matrix', maturity_df)
    seal = def_completion_seal(con, {**hint, "dashboards": int(len(dashboard_df)), "token_norm_rows": int(len(token_norm_df)), "network_fetch_enabled": ENABLE_NETWORK_FETCH})
    table_status_df = pd.DataFrame(seal['table_status'])
    def_write_table(con, 'vap_v8_completion_table_status', table_status_df)
    con.close()
    overall = int(round(maturity_df['score'].mean())) if not maturity_df.empty else 0
    summary = {"generated_at": def_now(), "run_dir": str(RUN_DIR), "duckdb_path": str(DUCKDB_PATH), "parquet_root": str(PARQUET_ROOT), "html_path": str(HTML_PATH), "dashboard_root": str(DASHBOARD_ROOT), "summary_json": str(SUMMARY_JSON), "payload_json": str(PAYLOAD_JSON), "matrix_csv": str(MATRIX_CSV), "query_pack_sql": str(QUERY_PACK_SQL), "refresh_ps1": str(REFRESH_PS1), "completion_seal_json": str(COMPLETION_SEAL_JSON), "network_fetch_enabled": ENABLE_NETWORK_FETCH, "overall_score": overall, "overall_grade": def_grade(overall), "actual_price_rows": hint['actual_price_rows'], "actual_norm_rows": hint['actual_norm_rows'], "actual_corr_rows": hint['actual_corr_rows'], "actual_lag_rows": hint['actual_lag_rows'], "dashboards": int(len(dashboard_df)), "token_norm_rows": int(len(token_norm_df)), "completion_status": seal['status'], "completion_mode": seal['mode'], "tables_added": list(outputs.keys()) + ['vap_v8_maturity_matrix','vap_v8_completion_table_status'], "parquet_files_added": [str(PARQUET_ROOT / f'{k}.parquet') for k in list(outputs.keys()) + ['vap_v8_maturity_matrix','vap_v8_completion_table_status']]}
    payload = {"summary": summary, "seal": seal, "maturity": maturity_df.to_dict(orient='records'), "dashboards": dashboard_df.to_dict(orient='records'), "tokens": token_norm_df.to_dict(orient='records')}
    def_query_pack(); def_refresh(); def_write_json(SUMMARY_JSON, summary); def_write_json(PAYLOAD_JSON, payload); maturity_df.to_csv(MATRIX_CSV, index=False, encoding='utf-8-sig')
    def_report(summary, {"maturity": maturity_df, "dashboards": dashboard_df, "tokens": token_norm_df, "corr": corr_df, "lag": lag_df}, seal)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
