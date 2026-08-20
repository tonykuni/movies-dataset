from __future__ import annotations

import json
import html
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
RUN_DIR = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V7_QUANT_20260507_104041")

HTML_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V7_QUANT_20260507_104041\\VAP_Warehouse_V7_Quant_Intelligence_Report.html")
SUMMARY_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V7_QUANT_20260507_104041\\vap_warehouse_v7_quant_summary.json")
PAYLOAD_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V7_QUANT_20260507_104041\\vap_warehouse_v7_quant_payload.json")
MATRIX_CSV = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V7_QUANT_20260507_104041\\vap_warehouse_v7_quant_matrix.csv")
QUERY_PACK_SQL = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V7_QUANT_20260507_104041\\vap_warehouse_v7_quant_query_pack.sql")
REFRESH_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V7_QUANT_20260507_104041\\Invoke-VAP-Warehouse-V7-Quant-Refresh.ps1")
PYTHON_EXE = r"C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
BUILDER_PY = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V7_QUANT_20260507_104041\\vap_warehouse_v7_quant_builder.py")

ROLLING_WINDOWS = [20,60,120]
LEAD_LAG_DAYS = [-10,-5,-3,-1,0,1,3,5,10]


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


def def_prepare_price_data(price_df: pd.DataFrame) -> pd.DataFrame:
    if price_df is None or price_df.empty:
        return pd.DataFrame([{"status": "NO_PRICE_DATA"}])
    if "status" not in price_df.columns:
        return pd.DataFrame([{"status": "NO_STATUS_COLUMN"}])

    ok = price_df[price_df["status"].astype(str).str.upper() == "OK"].copy()
    if ok.empty:
        return pd.DataFrame([{"status": "NO_OK_PRICE_DATA"}])

    for col in ["ticker", "date"]:
        if col not in ok.columns:
            return pd.DataFrame([{"status": f"MISSING_{col.upper()}"}])

    ok["date"] = pd.to_datetime(ok["date"], errors="coerce")
    value_col = "adj_close" if "adj_close" in ok.columns else "close"
    ok["price"] = pd.to_numeric(ok.get(value_col), errors="coerce")
    ok = ok.dropna(subset=["ticker", "date", "price"])
    if ok.empty:
        return pd.DataFrame([{"status": "NO_VALID_PRICE_ROWS"}])

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


def def_calculate_rolling_correlation(norm_df: pd.DataFrame) -> pd.DataFrame:
    if norm_df is None or norm_df.empty or "daily_return" not in norm_df.columns:
        return pd.DataFrame([{"status": "PLAN_ONLY_NO_PRICE_DATA"}])
    if "ticker" not in norm_df.columns or "normalized_date" not in norm_df.columns:
        return pd.DataFrame([{"status": "PLAN_ONLY_MISSING_COLUMNS"}])
    if norm_df["ticker"].nunique() < 2:
        return pd.DataFrame([{"status": "PLAN_ONLY_NEED_AT_LEAST_2_TICKERS"}])

    piv = norm_df.pivot_table(index="normalized_date", columns="ticker", values="daily_return", aggfunc="last").sort_index()
    rows = []
    tickers = list(piv.columns)
    for i, left in enumerate(tickers):
        for right in tickers[i+1:]:
            for w in ROLLING_WINDOWS:
                s = piv[left].rolling(int(w)).corr(piv[right])
                last_valid = s.dropna()
                rows.append({
                    "corr_id": f"RCALC_{left.replace('.','_').replace('^','IDX')}_{right.replace('.','_').replace('^','IDX')}_{w}",
                    "left_ticker": left,
                    "right_ticker": right,
                    "window": int(w),
                    "last_corr": float(last_valid.iloc[-1]) if len(last_valid) else None,
                    "valid_points": int(len(last_valid)),
                    "method": "rolling_pearson_daily_return",
                    "status": "CALCULATED" if len(last_valid) else "INSUFFICIENT_DATA",
                })
    return pd.DataFrame(rows) if rows else pd.DataFrame([{"status": "NO_CORR_ROWS"}])


def def_calculate_lead_lag(norm_df: pd.DataFrame) -> pd.DataFrame:
    if norm_df is None or norm_df.empty or "daily_return" not in norm_df.columns:
        return pd.DataFrame([{"status": "PLAN_ONLY_NO_PRICE_DATA"}])
    if norm_df["ticker"].nunique() < 2:
        return pd.DataFrame([{"status": "PLAN_ONLY_NEED_AT_LEAST_2_TICKERS"}])

    piv = norm_df.pivot_table(index="normalized_date", columns="ticker", values="daily_return", aggfunc="last").sort_index()
    rows = []
    tickers = list(piv.columns)
    for leader in tickers:
        for follower in tickers:
            if leader == follower:
                continue
            for lag in LEAD_LAG_DAYS:
                pair = pd.concat([piv[leader].shift(int(lag)), piv[follower]], axis=1).dropna()
                if pair.empty:
                    corr = None
                    n = 0
                    status = "INSUFFICIENT_DATA"
                else:
                    corr = pair.iloc[:, 0].corr(pair.iloc[:, 1])
                    n = len(pair)
                    status = "CALCULATED" if pd.notnull(corr) else "INSUFFICIENT_DATA"
                rows.append({
                    "lag_id": f"LCALC_{leader.replace('.','_').replace('^','IDX')}_{follower.replace('.','_').replace('^','IDX')}_{lag}",
                    "leader": leader,
                    "follower": follower,
                    "lag_days": int(lag),
                    "lag_corr": float(corr) if pd.notnull(corr) else None,
                    "valid_points": int(n),
                    "join_key": "NormalizedDate",
                    "status": status,
                })
    return pd.DataFrame(rows) if rows else pd.DataFrame([{"status": "NO_LAG_ROWS"}])


def def_build_factor_plan(fetch_status_df: pd.DataFrame) -> pd.DataFrame:
    tickers = []
    if fetch_status_df is not None and not fetch_status_df.empty and "ticker" in fetch_status_df.columns:
        tickers = [str(x) for x in fetch_status_df["ticker"].dropna().tolist() if str(x).strip()]

    rows = [
        {"factor_id": "FACTOR_GLOBAL_RISK", "inputs_json": json.dumps([x for x in tickers if x in ["SPY", "NVDA", "^TNX"]], ensure_ascii=False), "method": "zscore_and_rolling_beta", "status": "PLAN_READY", "description": "Global risk proxy using SPY/NVDA/rate proxy."},
        {"factor_id": "FACTOR_TW_SEMI_CHAIN", "inputs_json": json.dumps([x for x in tickers if x.endswith(".TW") or x == "^TWII"], ensure_ascii=False), "method": "relative_strength_and_correlation_cluster", "status": "PLAN_READY", "description": "Taiwan semiconductor chain relationship plan."},
        {"factor_id": "FACTOR_RATE_EQUITY_PRESSURE", "inputs_json": json.dumps([x for x in tickers if x in ["^TNX", "SPY", "^TWII"]], ensure_ascii=False), "method": "lead_lag_rate_to_equity", "status": "PLAN_READY", "description": "Rate to equity pressure transmission plan."},
    ]
    return pd.DataFrame(rows)


def def_build_regime_plan() -> pd.DataFrame:
    rows = [
        {"regime_id": "REGIME_RISK_ON_OFF", "inputs": "rolling_corr + normalized_price + rate_proxy", "method": "threshold_and_cluster_ready", "status": "PLAN_READY"},
        {"regime_id": "REGIME_SEMI_LEADERSHIP", "inputs": "lead_lag + TW semi tickers + NVDA", "method": "leadership_rotation_ready", "status": "PLAN_READY"},
        {"regime_id": "REGIME_MACRO_PRESSURE", "inputs": "rate_proxy + equity_index + event_matrix", "method": "event_overlay_and_forward_fill_ready", "status": "PLAN_READY"},
    ]
    return pd.DataFrame(rows)


def def_write_query_pack() -> None:
    sql = """
-- VAP Warehouse V7 Quant Intelligence Query Pack

SELECT * FROM quant_normalized_returns_v7 LIMIT 200;
SELECT * FROM quant_rolling_correlation_v7 ORDER BY window, left_ticker, right_ticker;
SELECT * FROM quant_lead_lag_score_v7 WHERE lag_corr IS NOT NULL ORDER BY ABS(lag_corr) DESC LIMIT 100;
SELECT * FROM quant_factor_plan_v7;
SELECT * FROM quant_regime_plan_v7;
SELECT * FROM rolling_correlation_plan LIMIT 200;
SELECT * FROM lead_lag_plan LIMIT 200;
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
Write-Host "Refreshing VAP Warehouse V7 Quant Intelligence..." -ForegroundColor Cyan
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


def def_table_html(df: pd.DataFrame, cols: List[str], max_rows: int = 120) -> str:
    if df is None or df.empty:
        return "<thead><tr><th>EMPTY</th></tr></thead><tbody><tr><td>EMPTY</td></tr></tbody>"
    heads = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    trs = []
    for _, r in df.head(max_rows).iterrows():
        tds = "".join(f"<td>{html.escape(str(r.get(c,'')))}</td>" for c in cols)
        trs.append(f"<tr>{tds}</tr>")
    return f"<thead><tr>{heads}</tr></thead><tbody>{''.join(trs)}</tbody>"


def def_write_html(summary: Dict[str, Any], dfs: Dict[str, pd.DataFrame]) -> None:
    doc = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head><meta charset="utf-8"><title>VAP Warehouse V7 Quant Intelligence</title>
<style>
:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}
body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}
.wrap{{max-width:1780px;margin:0 auto;padding:14px}}.hero{{background:#fff;border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}.hero:before{{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}}h1{{font-size:20px;margin:0}}.sub{{font-family:Consolas,monospace;color:var(--muted);font-size:10px;margin-top:3px}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin-bottom:10px}}.kpi{{background:#fff;border:1px solid var(--bd);border-left:4px solid var(--green);border-radius:10px;padding:10px}}.k{{font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase}}.v{{font-family:Consolas,monospace;font-size:24px;font-weight:900}}.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;margin-bottom:10px}}table{{width:100%;border-collapse:collapse;font-size:10.5px}}th{{position:sticky;top:0;background:#eceae4;border-bottom:2px solid var(--bd);padding:7px;text-align:left}}td{{border-bottom:1px solid var(--bd);padding:6px;vertical-align:top}}code{{font-family:Consolas,monospace;font-size:10px;background:#eceae4;border:1px solid var(--bd);border-radius:5px;padding:1px 5px}}.badge{{display:inline-block;background:#d8ecd8;color:var(--green);padding:4px 8px;border-radius:999px;font-weight:900}}
</style></head>
<body><div class="wrap">
<div class="hero"><div class="heroIn"><div><h1>VAP Warehouse V7 Quant Intelligence</h1><div class="sub">VERITAS INTELLIGENCE ANALYTICS · Normalized Returns · Rolling Correlation · Lead-Lag Score · Factor / Regime Plan</div><div class="sub">Generated: {html.escape(summary.get('generated_at',''))}</div></div><div class="badge">V7 READY</div></div></div>
<div class="grid">
<div class="kpi"><div class="k">Price Rows</div><div class="v">{summary.get('price_rows')}</div></div>
<div class="kpi"><div class="k">Normalized</div><div class="v">{summary.get('normalized_rows')}</div></div>
<div class="kpi"><div class="k">Rolling Corr</div><div class="v">{summary.get('rolling_corr_rows')}</div></div>
<div class="kpi"><div class="k">Lead Lag</div><div class="v">{summary.get('lead_lag_rows')}</div></div>
<div class="kpi"><div class="k">Factors</div><div class="v">{summary.get('factor_rows')}</div></div>
<div class="kpi"><div class="k">Regimes</div><div class="v">{summary.get('regime_rows')}</div></div>
</div>
<div class="card"><b>DuckDB</b><br><code>{html.escape(summary.get('duckdb_path',''))}</code></div>
<div class="card"><b>Normalized Returns</b><div style="overflow:auto;max-height:420px"><table>{def_table_html(dfs['norm'], ['ticker','normalized_date','price','normalized_price','daily_return','log_return','source_status'])}</table></div></div>
<div class="card"><b>Rolling Correlation</b><div style="overflow:auto;max-height:420px"><table>{def_table_html(dfs['corr'], ['corr_id','left_ticker','right_ticker','window','last_corr','valid_points','status'])}</table></div></div>
<div class="card"><b>Lead-Lag Score</b><div style="overflow:auto;max-height:420px"><table>{def_table_html(dfs['lag'], ['lag_id','leader','follower','lag_days','lag_corr','valid_points','status'])}</table></div></div>
<div class="card"><b>Factor Plan</b><div style="overflow:auto;max-height:360px"><table>{def_table_html(dfs['factor'], ['factor_id','inputs_json','method','status','description'])}</table></div></div>
<div class="card"><b>Regime Plan</b><div style="overflow:auto;max-height:360px"><table>{def_table_html(dfs['regime'], ['regime_id','inputs','method','status'])}</table></div></div>
<div class="card"><b>Query Pack</b><br><code>{html.escape(str(QUERY_PACK_SQL))}</code></div>
<div class="card"><b>Refresh Launcher</b><br><code>{html.escape(str(REFRESH_PS1))}</code></div>
</div></body></html>"""
    HTML_PATH.write_text(doc, encoding="utf-8")


def main() -> int:
    for p in [BASE_ROOT, OUTPUT_ROOT, WAREHOUSE_ROOT, PARQUET_ROOT, RUN_DIR]:
        p.mkdir(parents=True, exist_ok=True)

    if not DUCKDB_PATH.exists():
        raise RuntimeError("DuckDB warehouse not found. Run V6 first.")

    con = duckdb.connect(str(DUCKDB_PATH))

    price_df = def_safe_table(con, "live_price_sample_v6")
    fetch_status_df = def_safe_table(con, "live_fetch_status_v6")

    norm_df = def_prepare_price_data(price_df)
    corr_df = def_calculate_rolling_correlation(norm_df)
    lag_df = def_calculate_lead_lag(norm_df)
    factor_df = def_build_factor_plan(fetch_status_df)
    regime_df = def_build_regime_plan()

    outputs = {
        "quant_normalized_returns_v7": norm_df,
        "quant_rolling_correlation_v7": corr_df,
        "quant_lead_lag_score_v7": lag_df,
        "quant_factor_plan_v7": factor_df,
        "quant_regime_plan_v7": regime_df,
    }

    for name, df in outputs.items():
        def_write_table(con, name, df)

    con.close()

    def_write_query_pack()
    def_write_refresh()

    summary = {
        "generated_at": def_now(),
        "run_dir": str(RUN_DIR),
        "duckdb_path": str(DUCKDB_PATH),
        "parquet_root": str(PARQUET_ROOT),
        "html_path": str(HTML_PATH),
        "summary_json": str(SUMMARY_JSON),
        "payload_json": str(PAYLOAD_JSON),
        "matrix_csv": str(MATRIX_CSV),
        "query_pack_sql": str(QUERY_PACK_SQL),
        "refresh_ps1": str(REFRESH_PS1),
        "price_rows": int(len(price_df)),
        "normalized_rows": int(len(norm_df)),
        "rolling_corr_rows": int(len(corr_df)),
        "lead_lag_rows": int(len(lag_df)),
        "factor_rows": int(len(factor_df)),
        "regime_rows": int(len(regime_df)),
        "tables_added": list(outputs.keys()),
        "parquet_files_added": [str(PARQUET_ROOT / f"{k}.parquet") for k in outputs.keys()],
    }

    payload = {"summary": summary}
    for name, df in outputs.items():
        payload[name] = df.to_dict(orient="records")

    def_write_json(SUMMARY_JSON, summary)
    def_write_json(PAYLOAD_JSON, payload)

    matrix = pd.DataFrame([{"table": k, "rows": len(v), "parquet": str(PARQUET_ROOT / f"{k}.parquet")} for k, v in outputs.items()])
    matrix.to_csv(MATRIX_CSV, index=False, encoding="utf-8-sig")

    def_write_html(summary, {
        "norm": norm_df,
        "corr": corr_df,
        "lag": lag_df,
        "factor": factor_df,
        "regime": regime_df,
    })

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
