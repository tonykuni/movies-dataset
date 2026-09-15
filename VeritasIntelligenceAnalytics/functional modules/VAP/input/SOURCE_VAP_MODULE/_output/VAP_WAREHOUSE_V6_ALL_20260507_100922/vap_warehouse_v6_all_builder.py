from __future__ import annotations

import json
import html
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

import duckdb
import pandas as pd


# =============================================================================
# def PARAMETERS
# =============================================================================

BASE_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP")
OUTPUT_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output")
WAREHOUSE_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse")
PARQUET_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\parquet")
DUCKDB_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\vap_intelligence.duckdb")
RUN_DIR = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V6_ALL_20260507_100922")
DASHBOARD_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V6_ALL_20260507_100922\\dashboards")

HTML_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V6_ALL_20260507_100922\\VAP_Warehouse_V6_Workstation_Report.html")
SUMMARY_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V6_ALL_20260507_100922\\vap_warehouse_v6_summary.json")
PAYLOAD_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V6_ALL_20260507_100922\\vap_warehouse_v6_payload.json")
MATRIX_CSV = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V6_ALL_20260507_100922\\vap_warehouse_v6_matrix.csv")
QUERY_PACK_SQL = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V6_ALL_20260507_100922\\vap_warehouse_v6_query_pack.sql")
REFRESH_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V6_ALL_20260507_100922\\Invoke-VAP-Warehouse-V6-Refresh.ps1")
PYTHON_EXE = r"C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
BUILDER_PY = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V6_ALL_20260507_100922\\vap_warehouse_v6_all_builder.py")

ENABLE_NETWORK_FETCH = False
LIVE_TICKERS = ["2330.TW","2317.TW","2454.TW","NVDA","SPY","^TWII","^TNX"]
LIVE_START_DATE = "2024-01-01"
LIVE_END_DATE = ""
ROLLING_WINDOWS = [20,60,120]
LEAD_LAG_DAYS = [-10,-5,-3,-1,0,1,3,5,10]


# =============================================================================
# def UTILITIES
# =============================================================================

def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_write_json(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def def_safe_table(con: duckdb.DuckDBPyConnection, table_name: str) -> pd.DataFrame:
    try:
        return con.execute(f"SELECT * FROM {table_name}").fetchdf()
    except Exception:
        return pd.DataFrame()


def def_write_table(con: duckdb.DuckDBPyConnection, table_name: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        df = pd.DataFrame([{"_empty": True}])
    con.register("tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")
    out = str(PARQUET_ROOT / f"{table_name}.parquet").replace("\\", "/")
    con.execute(f"COPY {table_name} TO '{out}' (FORMAT PARQUET)")


# =============================================================================
# def LIVE FETCH
# =============================================================================

def def_build_live_fetch_status() -> pd.DataFrame:
    rows = []
    for ticker in LIVE_TICKERS:
        market = "TAIWAN" if ticker.endswith(".TW") or ticker.endswith(".TWO") or ticker == "^TWII" else "US_OR_GLOBAL"
        rows.append({
            "ticker": ticker,
            "market": market,
            "enabled_network_fetch": ENABLE_NETWORK_FETCH,
            "start_date": LIVE_START_DATE,
            "end_date": LIVE_END_DATE,
            "status": "PLANNED_NETWORK_DISABLED" if not ENABLE_NETWORK_FETCH else "READY",
            "alignment_policy": "TW_TRADING_DATE" if market == "TAIWAN" else "US_TO_TAIPEI_SHIFT_PLUS_1",
        })
    return pd.DataFrame(rows)


def def_fetch_yfinance_prices() -> pd.DataFrame:
    if not ENABLE_NETWORK_FETCH:
        return pd.DataFrame([{
            "status": "SKIPPED_NETWORK_DISABLED",
            "ticker": "",
            "date": "",
            "open": None,
            "high": None,
            "low": None,
            "close": None,
            "adj_close": None,
            "volume": None,
        }])

    try:
        import yfinance as yf
    except Exception as exc:
        return pd.DataFrame([{"status": "YFINANCE_NOT_AVAILABLE", "error": str(exc)}])

    rows = []
    for ticker in LIVE_TICKERS:
        try:
            df = yf.download(
                ticker,
                start=LIVE_START_DATE,
                end=(LIVE_END_DATE if str(LIVE_END_DATE).strip() else None),
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            if df is None or df.empty:
                rows.append({"status": "EMPTY", "ticker": ticker})
                continue
            df = df.reset_index()
            for _, r in df.tail(260).iterrows():
                rows.append({
                    "status": "OK",
                    "ticker": ticker,
                    "date": str(r.get("Date", ""))[:10],
                    "open": float(r.get("Open")) if pd.notnull(r.get("Open")) else None,
                    "high": float(r.get("High")) if pd.notnull(r.get("High")) else None,
                    "low": float(r.get("Low")) if pd.notnull(r.get("Low")) else None,
                    "close": float(r.get("Close")) if pd.notnull(r.get("Close")) else None,
                    "adj_close": float(r.get("Adj Close")) if pd.notnull(r.get("Adj Close")) else None,
                    "volume": float(r.get("Volume")) if pd.notnull(r.get("Volume")) else None,
                })
        except Exception as exc:
            rows.append({"status": "ERROR", "ticker": ticker, "error": str(exc)})
    return pd.DataFrame(rows)


# =============================================================================
# def DASHBOARD GENERATOR
# =============================================================================

def def_generate_dashboard_html(blueprint_df: pd.DataFrame) -> pd.DataFrame:
    DASHBOARD_ROOT.mkdir(parents=True, exist_ok=True)
    rows = []

    if blueprint_df.empty or "_empty" in blueprint_df.columns:
        blueprint_df = pd.DataFrame([
            {
                "blueprint_id": "AI_DASH_PLACEHOLDER",
                "title": "VAP Placeholder Dashboard",
                "layout": "GRID_PLACEHOLDER",
                "confidence": 60,
                "status": "PLACEHOLDER",
            }
        ])

    for _, bp in blueprint_df.iterrows():
        bid = str(bp.get("blueprint_id", "DASH_UNKNOWN"))
        title = str(bp.get("title", bid))
        layout = str(bp.get("layout", "GRID"))
        conf = str(bp.get("confidence", ""))
        out = DASHBOARD_ROOT / f"{bid}.html"

        doc = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>{html.escape(title)}</title>
<style>
:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}
body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}
.wrap{{max-width:1680px;margin:0 auto;padding:14px}}
.hero{{background:#fff;border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}
.hero:before{{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}
.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center}}
.grid{{display:grid;grid-template-columns:1.2fr .8fr;gap:10px}}.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;min-height:180px}}
.kpi{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:10px}}.box{{background:#fff;border:1px solid var(--bd);border-radius:10px;padding:10px}}.v{{font-size:22px;font-weight:900;font-family:Consolas,monospace}}
</style>
</head>
<body>
<div class="wrap">
<div class="hero"><div class="heroIn"><div><h1>{html.escape(title)}</h1><div>VERITAS INTELLIGENCE ANALYTICS · Auto-generated from dashboard_blueprint_registry</div><div>Layout: {html.escape(layout)} · Confidence: {html.escape(conf)}</div></div><b>READY</b></div></div>
<div class="kpi"><div class="box"><div>Blueprint</div><div class="v">{html.escape(bid[-8:])}</div></div><div class="box"><div>Layout</div><div class="v">AUTO</div></div><div class="box"><div>State</div><div class="v">OK</div></div><div class="box"><div>Mode</div><div class="v">V6</div></div></div>
<div class="grid"><div class="card"><h2>Main Plot Zone</h2><p>Ready for Plotly / dual-axis / stack timeline injection.</p></div><div class="card"><h2>Watchlist / Controls</h2><p>Ready for component registry wiring.</p></div></div>
</div>
</body>
</html>"""
        out.write_text(doc, encoding="utf-8")
        rows.append({
            "blueprint_id": bid,
            "dashboard_title": title,
            "layout": layout,
            "dashboard_html": str(out),
            "status": "GENERATED",
        })

    return pd.DataFrame(rows)


# =============================================================================
# def CROSS-ASSET CORRELATION
# =============================================================================

def def_build_normalized_series(price_df: pd.DataFrame) -> pd.DataFrame:
    if price_df.empty or "status" not in price_df.columns:
        return pd.DataFrame([{"status": "NO_PRICE_DATA"}])
    ok = price_df[price_df["status"].astype(str) == "OK"].copy()
    if ok.empty:
        return pd.DataFrame([{"status": "NO_OK_PRICE_DATA"}])
    ok["date"] = pd.to_datetime(ok["date"], errors="coerce")
    ok["value"] = pd.to_numeric(ok.get("adj_close", ok.get("close")), errors="coerce")
    ok = ok.dropna(subset=["date", "value"])
    out = []
    for ticker, g in ok.groupby("ticker"):
        g = g.sort_values("date").copy()
        base = g["value"].iloc[0] if len(g) else None
        if base and base != 0:
            g["normalized_value"] = g["value"] / base * 100
        else:
            g["normalized_value"] = None
        g["normalized_date"] = g["date"].dt.strftime("%Y-%m-%d")
        out.append(g[["ticker", "normalized_date", "value", "normalized_value"]])
    return pd.concat(out, ignore_index=True) if out else pd.DataFrame([{"status": "NO_NORMALIZED_SERIES"}])


def def_build_rolling_correlation_plan(fetch_status_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    tickers = [str(x) for x in fetch_status_df.get("ticker", pd.Series(dtype=str)).dropna().unique().tolist() if str(x).strip()]
    for i, left in enumerate(tickers):
        for right in tickers[i+1:]:
            for w in ROLLING_WINDOWS:
                rows.append({
                    "corr_id": f"CORR_{left.replace('.','_').replace('^','IDX')}_{right.replace('.','_').replace('^','IDX')}_{w}",
                    "left_ticker": left,
                    "right_ticker": right,
                    "window": int(w),
                    "method": "pearson",
                    "status": "READY_WITH_LIVE_DATA" if ENABLE_NETWORK_FETCH else "PLAN_ONLY_NETWORK_DISABLED",
                })
    return pd.DataFrame(rows) if rows else pd.DataFrame([{"status": "NO_TICKERS"}])


def def_build_lead_lag_plan(fetch_status_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    tickers = [str(x) for x in fetch_status_df.get("ticker", pd.Series(dtype=str)).dropna().unique().tolist() if str(x).strip()]
    for left in tickers:
        for right in tickers:
            if left == right:
                continue
            for lag in LEAD_LAG_DAYS:
                rows.append({
                    "lag_id": f"LAG_{left.replace('.','_').replace('^','IDX')}_{right.replace('.','_').replace('^','IDX')}_{lag}",
                    "leader": left,
                    "follower": right,
                    "lag_days": int(lag),
                    "join_key": "NormalizedDate",
                    "status": "READY_WITH_LIVE_DATA" if ENABLE_NETWORK_FETCH else "PLAN_ONLY_NETWORK_DISABLED",
                })
    return pd.DataFrame(rows) if rows else pd.DataFrame([{"status": "NO_TICKERS"}])


# =============================================================================
# def IO
# =============================================================================

def def_write_query_pack() -> None:
    sql = """
-- VAP Warehouse V6 Query Pack

SELECT * FROM generated_dashboard_registry ORDER BY blueprint_id;
SELECT * FROM live_fetch_status_v6 ORDER BY market, ticker;
SELECT * FROM live_price_sample_v6 LIMIT 100;
SELECT * FROM normalized_price_series_v6 LIMIT 100;
SELECT * FROM rolling_correlation_plan ORDER BY window, left_ticker, right_ticker;
SELECT * FROM lead_lag_plan ORDER BY leader, follower, lag_days;
SELECT * FROM dashboard_blueprint_registry ORDER BY confidence DESC;
SELECT * FROM cross_asset_relation_registry;
SELECT * FROM coaxis_policy_registry ORDER BY priority DESC;
"""
    QUERY_PACK_SQL.write_text(sql.strip() + "\n", encoding="utf-8")


def def_write_refresh() -> None:
    content = f"""#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = "{PYTHON_EXE}"
$Builder = "{BUILDER_PY}"
$Html = "{HTML_PATH}"
Write-Host ""
Write-Host "Refreshing VAP Warehouse V6..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) {{
    Start-Process $Html
    Write-Host "[OK] HTML = $Html" -ForegroundColor Green
}} else {{
    Write-Host "[ERR] HTML not found: $Html" -ForegroundColor Red
}}
"""
    REFRESH_PS1.write_text(content, encoding="utf-8-sig")


def def_table_html(df: pd.DataFrame, cols: List[str], max_rows: int = 80) -> str:
    if df is None or df.empty:
        return "<thead><tr><th>EMPTY</th></tr></thead><tbody><tr><td>EMPTY</td></tr></tbody>"
    heads = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    trs = []
    for _, r in df.head(max_rows).iterrows():
        tds = "".join(f"<td>{html.escape(str(r.get(c,'')))}</td>" for c in cols)
        trs.append(f"<tr>{tds}</tr>")
    return f"<thead><tr>{heads}</tr></thead><tbody>{''.join(trs)}</tbody>"


def def_write_html(summary: Dict[str, Any], dfs: Dict[str, pd.DataFrame]) -> None:
    generated_links = ""
    if "dashboards" in dfs and not dfs["dashboards"].empty:
        for _, r in dfs["dashboards"].iterrows():
            generated_links += f"<li><code>{html.escape(str(r.get('blueprint_id','')))}</code> — {html.escape(str(r.get('dashboard_html','')))}</li>"

    doc = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><title>VAP Warehouse V6 Workstation</title>
<style>
:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}
body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}
.wrap{{max-width:1780px;margin:0 auto;padding:14px}}.hero{{background:#fff;border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}.hero:before{{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}}h1{{font-size:20px;margin:0}}.sub{{font-family:Consolas,monospace;color:var(--muted);font-size:10px;margin-top:3px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin-bottom:10px}}.kpi{{background:#fff;border:1px solid var(--bd);border-left:4px solid var(--green);border-radius:10px;padding:10px}}.k{{font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase}}.v{{font-family:Consolas,monospace;font-size:24px;font-weight:900}}.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;margin-bottom:10px}}table{{width:100%;border-collapse:collapse;font-size:10.5px}}th{{position:sticky;top:0;background:#eceae4;border-bottom:2px solid var(--bd);padding:7px;text-align:left}}td{{border-bottom:1px solid var(--bd);padding:6px;vertical-align:top}}code{{font-family:Consolas,monospace;font-size:10px;background:#eceae4;border:1px solid var(--bd);border-radius:5px;padding:1px 5px}}.badge{{display:inline-block;background:#d8ecd8;color:var(--green);padding:4px 8px;border-radius:999px;font-weight:900}}
</style></head>
<body><div class="wrap">
<div class="hero"><div class="heroIn"><div><h1>VAP Warehouse V6 Workstation</h1><div class="sub">VERITAS INTELLIGENCE ANALYTICS · Live Fetch · Dashboard Generator · Rolling Corr / Lead-Lag</div><div class="sub">Generated: {html.escape(summary.get('generated_at',''))}</div></div><div class="badge">V6 READY</div></div></div>
<div class="grid">
<div class="kpi"><div class="k">Network</div><div class="v">{summary.get('network_fetch_enabled')}</div></div>
<div class="kpi"><div class="k">Dashboards</div><div class="v">{summary.get('generated_dashboards')}</div></div>
<div class="kpi"><div class="k">Fetch Rows</div><div class="v">{summary.get('live_price_rows')}</div></div>
<div class="kpi"><div class="k">Corr Plans</div><div class="v">{summary.get('corr_plans')}</div></div>
<div class="kpi"><div class="k">Lag Plans</div><div class="v">{summary.get('lag_plans')}</div></div>
</div>
<div class="card"><b>DuckDB</b><br><code>{html.escape(summary.get('duckdb_path',''))}</code></div>
<div class="card"><b>Generated Dashboards</b><ol>{generated_links}</ol></div>
<div class="card"><b>Live Fetch Status</b><div style="overflow:auto;max-height:360px"><table>{def_table_html(dfs['fetch_status'], ['ticker','market','enabled_network_fetch','status','alignment_policy'])}</table></div></div>
<div class="card"><b>Generated Dashboard Registry</b><div style="overflow:auto;max-height:360px"><table>{def_table_html(dfs['dashboards'], ['blueprint_id','dashboard_title','layout','dashboard_html','status'])}</table></div></div>
<div class="card"><b>Rolling Correlation Plan</b><div style="overflow:auto;max-height:420px"><table>{def_table_html(dfs['corr'], ['corr_id','left_ticker','right_ticker','window','method','status'])}</table></div></div>
<div class="card"><b>Lead-Lag Plan</b><div style="overflow:auto;max-height:420px"><table>{def_table_html(dfs['lag'], ['lag_id','leader','follower','lag_days','join_key','status'])}</table></div></div>
<div class="card"><b>Query Pack</b><br><code>{html.escape(str(QUERY_PACK_SQL))}</code></div>
<div class="card"><b>Refresh Launcher</b><br><code>{html.escape(str(REFRESH_PS1))}</code></div>
</div></body></html>"""
    HTML_PATH.write_text(doc, encoding="utf-8")


# =============================================================================
# def MAIN
# =============================================================================

def main() -> int:
    for p in [BASE_ROOT, OUTPUT_ROOT, WAREHOUSE_ROOT, PARQUET_ROOT, RUN_DIR, DASHBOARD_ROOT]:
        p.mkdir(parents=True, exist_ok=True)

    if not DUCKDB_PATH.exists():
        raise RuntimeError("DuckDB warehouse not found. Run V4/V5 first.")

    con = duckdb.connect(str(DUCKDB_PATH))

    blueprint_df = def_safe_table(con, "dashboard_blueprint_registry")
    fetch_status = def_build_live_fetch_status()
    price_df = def_fetch_yfinance_prices()
    normalized = def_build_normalized_series(price_df)
    dashboards = def_generate_dashboard_html(blueprint_df)
    corr_plan = def_build_rolling_correlation_plan(fetch_status)
    lag_plan = def_build_lead_lag_plan(fetch_status)

    outputs = {
        "live_fetch_status_v6": fetch_status,
        "live_price_sample_v6": price_df,
        "normalized_price_series_v6": normalized,
        "generated_dashboard_registry": dashboards,
        "rolling_correlation_plan": corr_plan,
        "lead_lag_plan": lag_plan,
    }

    for table_name, df in outputs.items():
        def_write_table(con, table_name, df)

    con.close()

    def_write_query_pack()
    def_write_refresh()

    summary = {
        "generated_at": def_now(),
        "run_dir": str(RUN_DIR),
        "duckdb_path": str(DUCKDB_PATH),
        "parquet_root": str(PARQUET_ROOT),
        "html_path": str(HTML_PATH),
        "dashboard_root": str(DASHBOARD_ROOT),
        "summary_json": str(SUMMARY_JSON),
        "payload_json": str(PAYLOAD_JSON),
        "matrix_csv": str(MATRIX_CSV),
        "query_pack_sql": str(QUERY_PACK_SQL),
        "refresh_ps1": str(REFRESH_PS1),
        "network_fetch_enabled": ENABLE_NETWORK_FETCH,
        "generated_dashboards": int(len(dashboards)),
        "live_price_rows": int(len(price_df)),
        "normalized_rows": int(len(normalized)),
        "corr_plans": int(len(corr_plan)),
        "lag_plans": int(len(lag_plan)),
        "tables_added": list(outputs.keys()),
        "parquet_files_added": [str(PARQUET_ROOT / f"{k}.parquet") for k in outputs.keys()],
    }

    payload = {"summary": summary}
    for k, df in outputs.items():
        payload[k] = df.to_dict(orient="records")

    def_write_json(SUMMARY_JSON, summary)
    def_write_json(PAYLOAD_JSON, payload)

    matrix = pd.DataFrame([{"table": k, "rows": len(v), "parquet": str(PARQUET_ROOT / f"{k}.parquet")} for k, v in outputs.items()])
    matrix.to_csv(MATRIX_CSV, index=False, encoding="utf-8-sig")

    def_write_html(summary, {
        "fetch_status": fetch_status,
        "dashboards": dashboards,
        "corr": corr_plan,
        "lag": lag_plan,
    })

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
