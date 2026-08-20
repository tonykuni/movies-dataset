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
RUN_DIR = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V5_NEXT3_20260506_230931")
HTML_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V5_NEXT3_20260506_230931\\VAP_Warehouse_V5_Next3_Report.html")
SUMMARY_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V5_NEXT3_20260506_230931\\vap_warehouse_v5_next3_summary.json")
PAYLOAD_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V5_NEXT3_20260506_230931\\vap_warehouse_v5_next3_payload.json")
MATRIX_CSV = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V5_NEXT3_20260506_230931\\vap_warehouse_v5_next3_matrix.csv")
QUERY_PACK_SQL = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V5_NEXT3_20260506_230931\\vap_warehouse_v5_next3_query_pack.sql")
REFRESH_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V5_NEXT3_20260506_230931\\Invoke-VAP-Warehouse-V5-Next3-Refresh.ps1")
PYTHON_EXE = r"C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
BUILDER_PY = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V5_NEXT3_20260506_230931\\vap_warehouse_v5_next3_builder.py")

ENABLE_NETWORK_FETCH = false
LIVE_TICKERS = ["2330.TW","2317.TW","2454.TW","NVDA","SPY","^TWII","^TNX"]
LIVE_START_DATE = "2024-01-01"
LIVE_END_DATE = ""


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


def def_table_count(con: duckdb.DuckDBPyConnection, table_name: str) -> int:
    try:
        return int(con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
    except Exception:
        return 0


def def_write_table(con: duckdb.DuckDBPyConnection, table_name: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        df = pd.DataFrame([{"_empty": True}])
    con.register("tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {table_name} AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")
    out = str(PARQUET_ROOT / f"{table_name}.parquet").replace("\\", "/")
    con.execute(f"COPY {table_name} TO '{out}' (FORMAT PARQUET)")


def def_bool_series(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([False] * len(df))
    return df[col].fillna(False).astype(bool)


# =============================================================================
# def PROCESS 1 · LIVE DATA ENGINE
# =============================================================================

def def_build_live_data_source_registry() -> pd.DataFrame:
    rows = [
        {
            "source_id": "SRC_YFINANCE_GLOBAL_PRICE",
            "source_name": "yfinance",
            "domain": "global_price",
            "enabled": ENABLE_NETWORK_FETCH,
            "network_required": True,
            "default_start_date": LIVE_START_DATE,
            "default_end_date": LIVE_END_DATE,
            "output_table": "live_price_sample",
            "notes": "Stocks, ETFs, indices, rates proxy. Network disabled by default for safety.",
        },
        {
            "source_id": "SRC_TWSE_OFFICIAL",
            "source_name": "TWSE",
            "domain": "taiwan_equity_market",
            "enabled": False,
            "network_required": True,
            "default_start_date": LIVE_START_DATE,
            "default_end_date": LIVE_END_DATE,
            "output_table": "twse_market_future",
            "notes": "Future connector target: TWSE official daily/chip/market data.",
        },
        {
            "source_id": "SRC_TPEX_OFFICIAL",
            "source_name": "TPEX",
            "domain": "taiwan_otc_market",
            "enabled": False,
            "network_required": True,
            "default_start_date": LIVE_START_DATE,
            "default_end_date": LIVE_END_DATE,
            "output_table": "tpex_market_future",
            "notes": "Future connector target: TPEX official daily/chip/market data.",
        },
        {
            "source_id": "SRC_FRED_MACRO",
            "source_name": "FRED",
            "domain": "macro",
            "enabled": False,
            "network_required": True,
            "default_start_date": LIVE_START_DATE,
            "default_end_date": LIVE_END_DATE,
            "output_table": "macro_series_future",
            "notes": "Future connector target: macro/rates/credit/liquidity indicators.",
        },
    ]
    return pd.DataFrame(rows)


def def_build_fetch_plan_registry(source_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for ticker in LIVE_TICKERS:
        if ticker.endswith(".TW") or ticker.endswith(".TWO") or ticker == "^TWII":
            market = "TAIWAN"
            alignment_policy = "TW_TRADING_DATE"
        elif ticker.startswith("^") or ticker in ["SPY", "QQQ", "NVDA"]:
            market = "US_OR_GLOBAL"
            alignment_policy = "US_TO_TAIPEI_SHIFT_PLUS_1"
        else:
            market = "GLOBAL"
            alignment_policy = "SOURCE_AS_IS"

        rows.append({
            "fetch_id": f"FETCH_{ticker.replace('.', '_').replace('^','IDX_')}",
            "source_id": "SRC_YFINANCE_GLOBAL_PRICE",
            "ticker": ticker,
            "market": market,
            "start_date": LIVE_START_DATE,
            "end_date": LIVE_END_DATE,
            "enabled": ENABLE_NETWORK_FETCH,
            "alignment_policy": alignment_policy,
            "price_policy": "ADJUSTED_PRICE_FOR_EQUITY_WHEN_AVAILABLE",
            "output_table": "live_price_sample",
            "status": "PLANNED_NETWORK_DISABLED" if not ENABLE_NETWORK_FETCH else "READY_TO_FETCH",
        })
    return pd.DataFrame(rows)


def def_try_fetch_yfinance(fetch_df: pd.DataFrame) -> pd.DataFrame:
    if not ENABLE_NETWORK_FETCH:
        return pd.DataFrame([{
            "fetch_status": "SKIPPED_NETWORK_DISABLED",
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
        return pd.DataFrame([{"fetch_status": "YFINANCE_NOT_INSTALLED", "error": str(exc)}])

    rows: List[Dict[str, Any]] = []
    for _, r in fetch_df.iterrows():
        if not bool(r.get("enabled", False)):
            continue
        ticker = str(r["ticker"])
        try:
            df = yf.download(
                ticker,
                start=str(r["start_date"]),
                end=(str(r["end_date"]) if str(r["end_date"]).strip() else None),
                progress=False,
                auto_adjust=False,
                threads=False,
            )
            if df is None or df.empty:
                rows.append({"fetch_status": "EMPTY", "ticker": ticker})
                continue
            df = df.reset_index().tail(20)
            for _, x in df.iterrows():
                rows.append({
                    "fetch_status": "OK",
                    "ticker": ticker,
                    "date": str(x.get("Date", ""))[:10],
                    "open": float(x.get("Open")) if pd.notnull(x.get("Open")) else None,
                    "high": float(x.get("High")) if pd.notnull(x.get("High")) else None,
                    "low": float(x.get("Low")) if pd.notnull(x.get("Low")) else None,
                    "close": float(x.get("Close")) if pd.notnull(x.get("Close")) else None,
                    "adj_close": float(x.get("Adj Close")) if pd.notnull(x.get("Adj Close")) else None,
                    "volume": float(x.get("Volume")) if pd.notnull(x.get("Volume")) else None,
                })
        except Exception as exc:
            rows.append({"fetch_status": "ERROR", "ticker": ticker, "error": str(exc)})
    return pd.DataFrame(rows) if rows else pd.DataFrame([{"fetch_status": "NO_ENABLED_FETCH"}])


# =============================================================================
# def PROCESS 2 · AI DASHBOARD COMPOSER
# =============================================================================

def def_build_dashboard_blueprints(asset_df: pd.DataFrame, component_df: pd.DataFrame, schema_df: pd.DataFrame, token_df: pd.DataFrame) -> pd.DataFrame:
    if asset_df.empty:
        return pd.DataFrame([{"blueprint_id": "EMPTY", "status": "NO_ASSETS"}])

    def pick_assets(mask: pd.Series, n: int) -> list:
        try:
            return asset_df[mask].head(n)["asset_id"].astype(str).tolist()
        except Exception:
            return []

    taxonomy = asset_df["taxonomy"].astype(str) if "taxonomy" in asset_df.columns else pd.Series([""] * len(asset_df))

    heatmap_assets = pick_assets(taxonomy.str.contains("HEATMAP", case=False, na=False), 4)
    dual_axis_assets = pick_assets(taxonomy.str.contains("DUAL_AXIS", case=False, na=False), 4)
    stack_assets = pick_assets(taxonomy.str.contains("STACK", case=False, na=False), 4)
    candle_assets = pick_assets(taxonomy.str.contains("CANDLE", case=False, na=False), 4)
    dashboard_assets = pick_assets(taxonomy.str.contains("DASHBOARD", case=False, na=False), 4)
    event_assets = pick_assets(taxonomy.str.contains("EVENT", case=False, na=False), 4)

    component_types = []
    if not component_df.empty and "component_type" in component_df.columns:
        component_types = component_df["component_type"].astype(str).value_counts().head(12).index.tolist()

    token_palette = []
    if not token_df.empty and "token_type" in token_df.columns and "token_value" in token_df.columns:
        color_df = token_df[token_df["token_type"].astype(str) == "COLOR_HEX"].head(12)
        token_palette = color_df["token_value"].astype(str).tolist()

    rows = [
        {
            "blueprint_id": "AI_DASH_GLOBAL_ETF_FLOW_OVERVIEW",
            "title": "Global ETF / Flow Overview",
            "layout": "WORLD_MAP_CENTER_GRID_PLUS_HEATMAP",
            "primary_assets_json": json.dumps(heatmap_assets + dashboard_assets + dual_axis_assets, ensure_ascii=False),
            "component_slots_json": json.dumps(["HEADER_HERO", "WATCHLIST", "HEATMAP_BLOCK", "PLOT_CARD", "KPI_CARD", "GRID_LAYOUT"], ensure_ascii=False),
            "visual_tokens_json": json.dumps(token_palette, ensure_ascii=False),
            "composer_prompt": "Compose a professional future-style global market dashboard with world-map center, regional ETF heatmap, flows, and compact KPI cards.",
            "confidence": 92,
            "status": "READY",
        },
        {
            "blueprint_id": "AI_DASH_PRICE_FLOW_DUAL_AXIS_WORKBENCH",
            "title": "Price + Flow Dual Axis Workbench",
            "layout": "DUAL_AXIS_PLUS_SIDE_WATCHLIST",
            "primary_assets_json": json.dumps(dual_axis_assets + stack_assets, ensure_ascii=False),
            "component_slots_json": json.dumps(["HEADER_HERO", "WATCHLIST", "PLOT_CARD", "PLOT_CARD", "PROGRESS_BAR"], ensure_ascii=False),
            "visual_tokens_json": json.dumps(token_palette, ensure_ascii=False),
            "composer_prompt": "Compose a dual-axis analytics workbench for price, volume, institutional flow, and timeline overlays.",
            "confidence": 94,
            "status": "READY",
        },
        {
            "blueprint_id": "AI_DASH_TECHNICAL_EVENT_TIMELINE",
            "title": "Technical + Event Timeline",
            "layout": "VERTICAL_STACK_TIMELINE_WITH_EVENT_MATRIX",
            "primary_assets_json": json.dumps(candle_assets + stack_assets + event_assets, ensure_ascii=False),
            "component_slots_json": json.dumps(["HEADER_HERO", "PLOT_CARD", "PLOT_CARD", "EVENT_MATRIX", "KPI_CARD"], ensure_ascii=False),
            "visual_tokens_json": json.dumps(token_palette, ensure_ascii=False),
            "composer_prompt": "Compose a technical analysis timeline with candlestick, MA, Bollinger, volume lanes, and event matrix overlays.",
            "confidence": 91,
            "status": "READY",
        },
    ]
    return pd.DataFrame(rows)


def def_build_composer_recommendations(blueprint_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    for _, r in blueprint_df.iterrows():
        rows.append({
            "recommendation_id": "REC_" + str(r.get("blueprint_id", "")),
            "blueprint_id": r.get("blueprint_id", ""),
            "priority": "HIGH" if int(r.get("confidence", 0)) >= 92 else "MEDIUM",
            "next_action": "GENERATE_HTML_DASHBOARD_FROM_BLUEPRINT",
            "human_review_required": False,
            "implementation_mode": "RULE_BASED_READY_AI_PROMPT_ATTACHED",
            "prompt": r.get("composer_prompt", ""),
        })
    return pd.DataFrame(rows)


# =============================================================================
# def PROCESS 3 · CROSS-ASSET TIMELINE INTELLIGENCE
# =============================================================================

def def_build_timeline_alignment_registry(schema_df: pd.DataFrame, alignment_df: pd.DataFrame, fetch_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    if not alignment_df.empty:
        for _, r in alignment_df.iterrows():
            rows.append({
                "timeline_id": "TL_" + str(r.get("asset_id", "")),
                "asset_id": r.get("asset_id", ""),
                "file_name": r.get("file_name", ""),
                "market": r.get("market", "GENERIC"),
                "primary_timeline": r.get("primary_timeline", "TW_TRADING_DATE"),
                "timezone_policy": r.get("timezone_policy", "LOCAL_AS_IS"),
                "calendar_policy": r.get("calendar_policy", "NO_CALENDAR_ALIGNMENT"),
                "fill_policy": r.get("fill_policy", "NO_FILL"),
                "normalized_date_column": r.get("normalized_date_column", "NormalizedDate"),
                "coaxis_ready": bool(r.get("alignable", False)),
                "source": "EXISTING_ALIGNMENT_POLICY",
            })

    for _, r in fetch_df.iterrows():
        rows.append({
            "timeline_id": "TL_FETCH_" + str(r.get("fetch_id", "")),
            "asset_id": str(r.get("fetch_id", "")),
            "file_name": str(r.get("ticker", "")),
            "market": r.get("market", "GLOBAL"),
            "primary_timeline": "TW_TRADING_DATE",
            "timezone_policy": r.get("alignment_policy", "SOURCE_AS_IS"),
            "calendar_policy": "FETCHED_SERIES_TO_WAREHOUSE_CALENDAR",
            "fill_policy": "FORWARD_FILL_ALLOWED_FOR_MACRO_ONLY",
            "normalized_date_column": "NormalizedDate",
            "coaxis_ready": True,
            "source": "LIVE_FETCH_PLAN",
        })

    return pd.DataFrame(rows)


def def_build_cross_asset_relation_registry(timeline_df: pd.DataFrame) -> pd.DataFrame:
    if timeline_df.empty:
        return pd.DataFrame([{"relation_id": "EMPTY", "status": "NO_TIMELINES"}])

    rows: List[Dict[str, Any]] = []
    ready = timeline_df[timeline_df["coaxis_ready"].fillna(False).astype(bool)].head(80)
    markets = ready["market"].astype(str).unique().tolist() if "market" in ready.columns else []

    relation_templates = [
        ("REL_TW_US_MACRO", "TAIWAN", "US_OR_GLOBAL", "US +1 Taipei day alignment for co-axis comparison"),
        ("REL_PRICE_FLOW", "TAIWAN", "TAIWAN", "Price and chip/flow same trading date alignment"),
        ("REL_MACRO_RISK", "MACRO", "GLOBAL", "Macro forward-fill into asset timeline"),
    ]

    for rid, left_market, right_market, desc in relation_templates:
        rows.append({
            "relation_id": rid,
            "left_market": left_market,
            "right_market": right_market,
            "description": desc,
            "alignment_rule": "NORMALIZED_DATE_JOIN",
            "lag_policy": "ALLOW_LEAD_LAG_SCAN",
            "correlation_policy": "ROLLING_CORRELATION_READY",
            "status": "READY_RULE",
        })

    return pd.DataFrame(rows)


def def_build_coaxis_policy_registry() -> pd.DataFrame:
    rows = [
        {
            "policy_id": "COAXIS_TW_BASE",
            "base_market": "TAIWAN",
            "date_column": "NormalizedDate",
            "calendar": "TW_TRADING_DAY",
            "rule": "Taiwan assets remain on local trade date.",
            "priority": 100,
        },
        {
            "policy_id": "COAXIS_US_PLUS_1",
            "base_market": "US_OR_GLOBAL",
            "date_column": "NormalizedDate",
            "calendar": "US_TRADING_DAY_SHIFTED_TO_TW_VIEW",
            "rule": "US market data shifts +1 Taipei calendar day for Taiwan investor perspective.",
            "priority": 95,
        },
        {
            "policy_id": "COAXIS_MACRO_FFILL",
            "base_market": "MACRO",
            "date_column": "NormalizedDate",
            "calendar": "MACRO_FORWARD_FILL",
            "rule": "Macro series forward-filled to trading calendar; never backfill future data.",
            "priority": 90,
        },
        {
            "policy_id": "COAXIS_EVENT_MATRIX",
            "base_market": "EVENTS",
            "date_column": "NormalizedDate",
            "calendar": "EVENT_DATE",
            "rule": "Events appear as vertical markers or event matrix lanes.",
            "priority": 85,
        },
    ]
    return pd.DataFrame(rows)


# =============================================================================
# def QUERY PACK / REFRESH / HTML
# =============================================================================

def def_write_query_pack() -> None:
    sql = """
-- VAP Warehouse V5 Next3 Query Pack
-- VERITAS INTELLIGENCE ANALYTICS

-- 01 Live Data Sources
SELECT * FROM live_data_source_registry ORDER BY source_id;

-- 02 Fetch Plans
SELECT * FROM fetch_plan_registry ORDER BY market, ticker;

-- 03 AI Dashboard Blueprints
SELECT blueprint_id, title, layout, confidence, status
FROM dashboard_blueprint_registry
ORDER BY confidence DESC;

-- 04 Composer Recommendations
SELECT *
FROM dashboard_composer_recommendations
ORDER BY priority DESC, blueprint_id;

-- 05 Timeline Alignment
SELECT market, timezone_policy, calendar_policy, COUNT(*) AS n
FROM timeline_alignment_registry
GROUP BY market, timezone_policy, calendar_policy
ORDER BY n DESC;

-- 06 Cross Asset Relations
SELECT *
FROM cross_asset_relation_registry
ORDER BY relation_id;

-- 07 Coaxis Policies
SELECT *
FROM coaxis_policy_registry
ORDER BY priority DESC;

-- 08 Visual Token Summary
SELECT token_type, COUNT(*) AS n
FROM visual_token_registry
GROUP BY token_type
ORDER BY n DESC;

-- 09 Component Summary
SELECT component_type, COUNT(*) AS n, AVG(confidence) AS avg_confidence
FROM component_registry
GROUP BY component_type
ORDER BY n DESC;
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
Write-Host "Refreshing VAP Warehouse V5 Next3..." -ForegroundColor Cyan
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


def def_table_html(df: pd.DataFrame, cols: List[str], max_rows: int = 100) -> str:
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
<head>
<meta charset="utf-8">
<title>VAP Warehouse V5 Next3 Report</title>
<style>
:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}
body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}
.wrap{{max-width:1780px;margin:0 auto;padding:14px}}
.hero{{background:var(--sf);border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}
.hero:before{{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}
.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}}
h1{{font-size:20px;margin:0}}.sub{{font-family:Consolas,monospace;color:var(--muted);font-size:10px;margin-top:3px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin-bottom:10px}}
.kpi{{background:#fff;border:1px solid var(--bd);border-left:4px solid var(--green);border-radius:10px;padding:10px}}
.k{{font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase}}.v{{font-family:Consolas,monospace;font-size:24px;font-weight:900}}
.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;margin-bottom:10px}}
table{{width:100%;border-collapse:collapse;font-size:10.5px}}th{{position:sticky;top:0;background:#eceae4;border-bottom:2px solid var(--bd);padding:7px;text-align:left}}td{{border-bottom:1px solid var(--bd);padding:6px;vertical-align:top}}tr:hover{{background:rgba(76,120,168,.04)}}
code{{font-family:Consolas,monospace;font-size:10px;background:#eceae4;border:1px solid var(--bd);border-radius:5px;padding:1px 5px}}
.badge{{display:inline-block;background:#d8ecd8;color:var(--green);padding:4px 8px;border-radius:999px;font-weight:900}}
</style>
</head>
<body>
<div class="wrap">
<div class="hero"><div class="heroIn"><div><h1>VAP Warehouse V5 · Next 3 Processes</h1><div class="sub">VERITAS INTELLIGENCE ANALYTICS · Live Data Engine · AI Dashboard Composer · Cross-Asset Timeline Intelligence</div><div class="sub">Generated: {html.escape(summary.get('generated_at',''))}</div></div><div class="badge">V5 READY</div></div></div>

<div class="grid">
<div class="kpi"><div class="k">Live Sources</div><div class="v">{summary.get('live_sources',0)}</div></div>
<div class="kpi"><div class="k">Fetch Plans</div><div class="v">{summary.get('fetch_plans',0)}</div></div>
<div class="kpi"><div class="k">Blueprints</div><div class="v">{summary.get('blueprints',0)}</div></div>
<div class="kpi"><div class="k">Recommendations</div><div class="v">{summary.get('recommendations',0)}</div></div>
<div class="kpi"><div class="k">Timelines</div><div class="v">{summary.get('timelines',0)}</div></div>
<div class="kpi"><div class="k">Relations</div><div class="v">{summary.get('relations',0)}</div></div>
</div>

<div class="card"><b>DuckDB</b><br><code>{html.escape(summary.get('duckdb_path',''))}</code></div>
<div class="card"><b>ParquetRoot</b><br><code>{html.escape(summary.get('parquet_root',''))}</code></div>
<div class="card"><b>Query Pack</b><br><code>{html.escape(summary.get('query_pack_sql',''))}</code></div>
<div class="card"><b>Refresh Launcher</b><br><code>{html.escape(summary.get('refresh_ps1',''))}</code></div>

<div class="card"><b>Process 1 · Live Data Source Registry</b><div style="overflow:auto;max-height:360px"><table>{def_table_html(dfs['live_sources'], ['source_id','source_name','domain','enabled','network_required','output_table','notes'])}</table></div></div>
<div class="card"><b>Process 1 · Fetch Plan Registry</b><div style="overflow:auto;max-height:360px"><table>{def_table_html(dfs['fetch_plans'], ['fetch_id','ticker','market','enabled','alignment_policy','status'])}</table></div></div>
<div class="card"><b>Process 2 · AI Dashboard Blueprints</b><div style="overflow:auto;max-height:420px"><table>{def_table_html(dfs['blueprints'], ['blueprint_id','title','layout','confidence','status'])}</table></div></div>
<div class="card"><b>Process 2 · Composer Recommendations</b><div style="overflow:auto;max-height:420px"><table>{def_table_html(dfs['recommendations'], ['recommendation_id','blueprint_id','priority','next_action','implementation_mode'])}</table></div></div>
<div class="card"><b>Process 3 · Timeline Alignment Registry</b><div style="overflow:auto;max-height:520px"><table>{def_table_html(dfs['timeline'], ['timeline_id','file_name','market','timezone_policy','calendar_policy','fill_policy','coaxis_ready','source'])}</table></div></div>
<div class="card"><b>Process 3 · Cross-Asset Relations</b><div style="overflow:auto;max-height:360px"><table>{def_table_html(dfs['relations'], ['relation_id','left_market','right_market','description','alignment_rule','lag_policy','correlation_policy','status'])}</table></div></div>
<div class="card"><b>Process 3 · Coaxis Policies</b><div style="overflow:auto;max-height:360px"><table>{def_table_html(dfs['coaxis'], ['policy_id','base_market','date_column','calendar','rule','priority'])}</table></div></div>

</div>
</body>
</html>"""
    HTML_PATH.write_text(doc, encoding="utf-8")


# =============================================================================
# def MAIN
# =============================================================================

def def_main() -> int:
    for p in [BASE_ROOT, OUTPUT_ROOT, WAREHOUSE_ROOT, PARQUET_ROOT, RUN_DIR]:
        p.mkdir(parents=True, exist_ok=True)

    if not DUCKDB_PATH.exists():
        raise RuntimeError("DuckDB warehouse not found. Run VAP Warehouse V4 first.")

    con = duckdb.connect(str(DUCKDB_PATH))

    asset_df = def_safe_table(con, "asset_registry_v4")
    component_df = def_safe_table(con, "component_registry")
    token_df = def_safe_table(con, "visual_token_registry")
    schema_df = def_safe_table(con, "schema_intelligence_registry")
    alignment_df = def_safe_table(con, "alignment_policy_registry")

    live_sources = def_build_live_data_source_registry()
    fetch_plans = def_build_fetch_plan_registry(live_sources)
    live_price_sample = def_try_fetch_yfinance(fetch_plans)

    blueprints = def_build_dashboard_blueprints(asset_df, component_df, schema_df, token_df)
    recommendations = def_build_composer_recommendations(blueprints)

    timeline = def_build_timeline_alignment_registry(schema_df, alignment_df, fetch_plans)
    relations = def_build_cross_asset_relation_registry(timeline)
    coaxis = def_build_coaxis_policy_registry()

    outputs = {
        "live_data_source_registry": live_sources,
        "fetch_plan_registry": fetch_plans,
        "live_price_sample": live_price_sample,
        "dashboard_blueprint_registry": blueprints,
        "dashboard_composer_recommendations": recommendations,
        "timeline_alignment_registry": timeline,
        "cross_asset_relation_registry": relations,
        "coaxis_policy_registry": coaxis,
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
        "summary_json": str(SUMMARY_JSON),
        "payload_json": str(PAYLOAD_JSON),
        "matrix_csv": str(MATRIX_CSV),
        "query_pack_sql": str(QUERY_PACK_SQL),
        "refresh_ps1": str(REFRESH_PS1),
        "network_fetch_enabled": ENABLE_NETWORK_FETCH,
        "live_sources": int(len(live_sources)),
        "fetch_plans": int(len(fetch_plans)),
        "blueprints": int(len(blueprints)),
        "recommendations": int(len(recommendations)),
        "timelines": int(len(timeline)),
        "relations": int(len(relations)),
        "coaxis_policies": int(len(coaxis)),
        "tables_added": list(outputs.keys()),
        "parquet_files_added": [str(PARQUET_ROOT / f"{k}.parquet") for k in outputs.keys()],
    }

    payload = {"summary": summary}
    for table_name, df in outputs.items():
        payload[table_name] = df.to_dict(orient="records")

    def_write_json(SUMMARY_JSON, summary)
    def_write_json(PAYLOAD_JSON, payload)

    matrix_rows = []
    for table_name, df in outputs.items():
        matrix_rows.append({"table": table_name, "rows": len(df), "parquet": str(PARQUET_ROOT / f"{table_name}.parquet")})
    pd.DataFrame(matrix_rows).to_csv(MATRIX_CSV, index=False, encoding="utf-8-sig")

    def_write_html(summary, {
        "live_sources": live_sources,
        "fetch_plans": fetch_plans,
        "blueprints": blueprints,
        "recommendations": recommendations,
        "timeline": timeline,
        "relations": relations,
        "coaxis": coaxis,
    })

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(def_main())
