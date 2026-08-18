from __future__ import annotations

import csv
import html
import json
import re
import traceback
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import duckdb
import pandas as pd


# =============================================================================
# def PARAMETERS
# =============================================================================

BASE_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP")
INPUT_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_input")
OUTPUT_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output")
WAREHOUSE_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse")
RUN_DIR = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535")
DUCKDB_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\vap_intelligence.duckdb")
PARQUET_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\parquet")
HTML_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535\\VAP_Warehouse_V4_Intelligence_Report.html")
SUMMARY_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535\\vap_warehouse_v4_summary.json")
PAYLOAD_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535\\vap_warehouse_v4_payload.json")
MATRIX_CSV = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535\\vap_warehouse_v4_matrix.csv")
REFRESH_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535\\Invoke-VAP-Warehouse-V4-Refresh.ps1")
PYTHON_EXE = r"C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
BUILDER_PY = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535\\vap_warehouse_v4_builder.py")
MAX_SCAN_FILES = int("3000")


# =============================================================================
# def UTILITIES
# =============================================================================

def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_safe_text(path_value: Path) -> str:
    try:
        return path_value.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path_value.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def def_write_json(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def def_slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_]+", "_", str(value)).strip("_")[:100] or "item"


def def_read_duckdb_table(table_name: str) -> pd.DataFrame:
    if not DUCKDB_PATH.exists():
        return pd.DataFrame()
    try:
        con = duckdb.connect(str(DUCKDB_PATH), read_only=False)
        df = con.execute(f"SELECT * FROM {table_name}").fetchdf()
        con.close()
        return df
    except Exception:
        return pd.DataFrame()


def def_scan_files() -> List[Path]:
    allowed = {".html", ".htm", ".css", ".js", ".json", ".jsonl", ".csv", ".txt", ".parquet"}
    files: List[Path] = []
    for root in [INPUT_ROOT, BASE_ROOT]:
        if root.exists():
            for p in root.rglob("*"):
                if len(files) >= MAX_SCAN_FILES:
                    break
                if not p.is_file():
                    continue
                if p.suffix.lower() not in allowed:
                    continue
                sp = str(p).lower()
                if "_warehouse" in sp or "_output" in sp:
                    continue
                files.append(p)
    seen = set()
    out = []
    for p in files:
        s = str(p).lower()
        if s not in seen:
            seen.add(s)
            out.append(p)
    return out


def def_json_kind(path_value: Path) -> str:
    name = path_value.name.lower()
    text = def_safe_text(path_value).strip()
    if not text:
        return "JSON_EMPTY"
    try:
        payload = json.loads(text)
        if isinstance(payload, list):
            if "charts" in name or "chart" in name:
                return "CHART_REGISTRY_JSON"
            if "pages" in name or "page" in name:
                return "PAGE_CATALOG_JSON"
            if "registry" in name or "catalog" in name:
                return "REGISTRY_JSON"
            return "LIST_JSON_DATA"
        if isinstance(payload, dict):
            keys = {str(k).lower() for k in payload.keys()}
            if "charts" in keys:
                return "CHART_REGISTRY_JSON"
            if "pages" in keys:
                return "PAGE_CATALOG_JSON"
            if "components" in keys:
                return "COMPONENT_REGISTRY_JSON"
            if "theme" in keys or "tokens" in keys:
                return "VISUAL_TOKEN_JSON"
            return "DICT_JSON_DATA"
    except Exception:
        return "JSON_PARSE_WARN"
    return "JSON_DATA"


def def_normalize_asset_registry(asset_df: pd.DataFrame) -> pd.DataFrame:
    if asset_df.empty:
        return asset_df

    df = asset_df.copy()
    for col in ["file_name", "path", "taxonomy", "kind", "warning_reason", "best_template", "headers_json", "sample_json"]:
        if col not in df.columns:
            df[col] = ""

    for i, row in df.iterrows():
        file_name = str(row.get("file_name", ""))
        path_value = Path(str(row.get("path", "")))
        tax = str(row.get("taxonomy", ""))
        warn = str(row.get("warning_reason", ""))

        if file_name.lower().endswith(".json") and path_value.exists():
            jk = def_json_kind(path_value)
            if jk in ["CHART_REGISTRY_JSON", "PAGE_CATALOG_JSON", "REGISTRY_JSON", "COMPONENT_REGISTRY_JSON", "VISUAL_TOKEN_JSON"]:
                df.at[i, "taxonomy"] = jk
                df.at[i, "best_template"] = {
                    "CHART_REGISTRY_JSON": "VAP_TPL_CHART_REGISTRY_012",
                    "PAGE_CATALOG_JSON": "VAP_TPL_PAGE_CATALOG_013",
                    "REGISTRY_JSON": "VAP_TPL_REGISTRY_DATA_014",
                    "COMPONENT_REGISTRY_JSON": "VAP_TPL_COMPONENT_REGISTRY_015",
                    "VISUAL_TOKEN_JSON": "VAP_TPL_VISUAL_TOKEN_016",
                }.get(jk, "VAP_TPL_REGISTRY_DATA_014")
                df.at[i, "template_score"] = 88
                df.at[i, "warning_reason"] = ""

        if tax == "DATA_ASSET" and warn == "json_list" and file_name.lower() in ["charts.json", "pages.json"]:
            if "chart" in file_name.lower():
                df.at[i, "taxonomy"] = "CHART_REGISTRY_JSON"
                df.at[i, "best_template"] = "VAP_TPL_CHART_REGISTRY_012"
            else:
                df.at[i, "taxonomy"] = "PAGE_CATALOG_JSON"
                df.at[i, "best_template"] = "VAP_TPL_PAGE_CATALOG_013"
            df.at[i, "template_score"] = 88
            df.at[i, "warning_reason"] = ""

    return df


# =============================================================================
# def COMPONENT EXTRACTION
# =============================================================================

def def_detect_components_for_html(path_value: Path, asset_id: str) -> List[Dict[str, Any]]:
    text = def_safe_text(path_value)
    lower = text.lower()
    components: List[Dict[str, Any]] = []

    patterns = [
        ("NAVBAR", r"<nav|\bnavbar\b|\bnav\b"),
        ("SIDEBAR", r"sidebar|side-panel|left-panel|drawer"),
        ("WATCHLIST", r"watchlist|watch-list|觀察|自選"),
        ("PLOT_CARD", r"plot|chart|graph|plotly|newplot"),
        ("HEATMAP_BLOCK", r"heatmap|熱力"),
        ("EVENT_MATRIX", r"eventmatrix|event matrix|事件矩陣|timeline"),
        ("FLOATING_CONTROL", r"floating|float|fixed-control|control-panel|control center"),
        ("PROGRESS_BAR", r"progress|loading|bar"),
        ("KPI_CARD", r"kpi|metric|stat-card|score-card"),
        ("GRID_LAYOUT", r"grid-template|css grid|display:grid|grid"),
        ("HEADER_HERO", r"hero|header|topbar|visual lock|veritas intelligence analytics"),
    ]

    for comp_type, pat in patterns:
        hits = len(re.findall(pat, lower, flags=re.I))
        if hits > 0:
            components.append({
                "component_id": f"CMP_{asset_id}_{comp_type}",
                "asset_id": asset_id,
                "file_name": path_value.name,
                "path": str(path_value),
                "component_type": comp_type,
                "signal_count": hits,
                "confidence": min(100, 65 + hits * 5),
                "source": "HTML_SEMANTIC_SCAN",
            })

    return components


def def_build_component_registry(asset_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if asset_df.empty:
        return pd.DataFrame(rows)

    for _, row in asset_df.iterrows():
        path_value = Path(str(row.get("path", "")))
        asset_id = str(row.get("asset_id", def_slug(path_value.stem)))
        taxonomy = str(row.get("taxonomy", ""))
        if not path_value.exists():
            continue
        if taxonomy.startswith("HTML_") or path_value.suffix.lower() in [".html", ".htm"]:
            rows.extend(def_detect_components_for_html(path_value, asset_id))

    return pd.DataFrame(rows)


# =============================================================================
# def VISUAL TOKEN REGISTRY
# =============================================================================

def def_extract_visual_tokens_from_html(path_value: Path, asset_id: str) -> List[Dict[str, Any]]:
    text = def_safe_text(path_value)
    rows: List[Dict[str, Any]] = []

    token_patterns = [
        ("COLOR_HEX", r"#[0-9a-fA-F]{3,8}"),
        ("RADIUS", r"border-radius\s*:\s*[^;]+"),
        ("SHADOW", r"box-shadow\s*:\s*[^;]+"),
        ("FONT_FAMILY", r"font-family\s*:\s*[^;]+"),
        ("GRID_TEMPLATE", r"grid-template-columns\s*:\s*[^;]+"),
        ("ANIMATION", r"@keyframes|animation\s*:\s*[^;]+|transition\s*:\s*[^;]+"),
        ("SPACING", r"padding\s*:\s*[^;]+|margin\s*:\s*[^;]+|gap\s*:\s*[^;]+"),
        ("CSS_VARIABLE", r"--[A-Za-z0-9_-]+\s*:\s*[^;]+"),
    ]

    for token_type, pat in token_patterns:
        values = re.findall(pat, text, flags=re.I)
        unique = []
        seen = set()
        for v in values:
            sv = str(v).strip()
            if sv not in seen:
                seen.add(sv)
                unique.append(sv)
        for idx, val in enumerate(unique[:120], 1):
            rows.append({
                "token_id": f"VTK_{asset_id}_{token_type}_{idx:03d}",
                "asset_id": asset_id,
                "file_name": path_value.name,
                "token_type": token_type,
                "token_value": val[:500],
                "source": "HTML_CSS_SCAN",
            })

    return rows


def def_build_visual_token_registry(asset_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if asset_df.empty:
        return pd.DataFrame(rows)

    for _, row in asset_df.iterrows():
        path_value = Path(str(row.get("path", "")))
        asset_id = str(row.get("asset_id", def_slug(path_value.stem)))
        taxonomy = str(row.get("taxonomy", ""))
        if not path_value.exists():
            continue
        if taxonomy.startswith("HTML_") or path_value.suffix.lower() in [".html", ".htm"]:
            rows.extend(def_extract_visual_tokens_from_html(path_value, asset_id))

    return pd.DataFrame(rows)


# =============================================================================
# def SCHEMA INTELLIGENCE
# =============================================================================

def def_parse_headers(value: Any) -> List[str]:
    if value is None:
        return []
    s = str(value)
    if not s:
        return []
    try:
        if s.strip().startswith("["):
            parsed = json.loads(s)
            if isinstance(parsed, list):
                return [str(x) for x in parsed]
    except Exception:
        pass
    if "|" in s:
        return [x.strip() for x in s.split("|") if x.strip()]
    if "," in s:
        return [x.strip() for x in s.split(",") if x.strip()]
    return [s.strip()] if s.strip() else []


def def_schema_role(headers: List[str]) -> Dict[str, Any]:
    hs = {re.sub(r"[^a-z0-9]+", "_", str(h).lower()).strip("_") for h in headers}
    role = "UNKNOWN_SCHEMA"
    suggested = "VAP_TPL_SINGLE_LINE_001"

    date = bool(hs & {"date", "trade_date", "time", "datetime", "normalized_date"})
    price = bool(hs & {"close", "adj_close", "adjclose", "open", "high", "low", "price", "value", "index"})
    volume = bool(hs & {"volume", "vol", "turnover"})
    flow = bool(hs & {"flow", "net_buy", "net_amount", "foreign_net", "dealer_net"})
    technical = bool(hs & {"rsi", "macd", "kd", "k", "d", "ma", "ema", "bb", "bollinger"})
    xyz = {"x", "y", "z"} <= hs
    xy = {"x", "y"} <= hs

    if date and price and technical and volume:
        role = "PRICE_TA_VOLUME_SCHEMA"
        suggested = "VAP_TPL_STACK_TIMELINE_004"
    elif date and price and (volume or flow):
        role = "PRICE_FLOW_DUAL_AXIS_SCHEMA"
        suggested = "VAP_TPL_DUAL_AXIS_003"
    elif date and price:
        role = "PRICE_TIME_SERIES_SCHEMA"
        suggested = "VAP_TPL_SINGLE_LINE_001"
    elif date and flow:
        role = "FLOW_TIME_SERIES_SCHEMA"
        suggested = "VAP_TPL_SINGLE_BAR_002"
    elif xyz:
        role = "MATRIX_XYZ_SCHEMA"
        suggested = "VAP_TPL_HEATMAP_006"
    elif xy:
        role = "SCATTER_XY_SCHEMA"
        suggested = "VAP_TPL_SCATTER_005"
    elif len(headers) >= 5:
        role = "WIDE_TABLE_SCHEMA"
        suggested = "VAP_TPL_STACK_TIMELINE_004"

    return {
        "schema_role": role,
        "suggested_template": suggested,
        "has_date": date,
        "has_price": price,
        "has_volume": volume,
        "has_flow": flow,
        "has_technical": technical,
        "has_xy": xy,
        "has_xyz": xyz,
    }


def def_build_schema_registry(asset_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []
    if asset_df.empty:
        return pd.DataFrame(rows)

    for _, row in asset_df.iterrows():
        taxonomy = str(row.get("taxonomy", ""))
        if taxonomy.startswith("HTML_"):
            continue

        headers = def_parse_headers(row.get("headers_json", row.get("headers", "")))
        role = def_schema_role(headers)

        rows.append({
            "schema_id": f"SCH_{row.get('asset_id', '')}",
            "asset_id": row.get("asset_id", ""),
            "file_name": row.get("file_name", ""),
            "taxonomy": taxonomy,
            "header_count": len(headers),
            "headers_json": json.dumps(headers, ensure_ascii=False),
            **role,
        })

    return pd.DataFrame(rows)


# =============================================================================
# def ALIGNMENT POLICY
# =============================================================================

def def_build_alignment_policy_registry(asset_df: pd.DataFrame, schema_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    for _, row in schema_df.iterrows():
        headers = set(def_parse_headers(row.get("headers_json", "")))
        file_name = str(row.get("file_name", "")).lower()
        schema_role = str(row.get("schema_role", ""))

        market = "GENERIC"
        timezone_policy = "LOCAL_AS_IS"
        calendar_policy = "NO_CALENDAR_ALIGNMENT"
        fill_policy = "NO_FILL"

        if ".tw" in file_name or ".two" in file_name or "tw" in file_name or "taiwan" in file_name:
            market = "TAIWAN"
            timezone_policy = "ASIA_TAIPEI"
            calendar_policy = "TW_TRADING_DAY"
            fill_policy = "FORWARD_FILL_ALLOWED_FOR_MACRO_ONLY"
        elif "us" in file_name or "sp500" in file_name or "nasdaq" in file_name or "nyse" in file_name:
            market = "US"
            timezone_policy = "US_TO_TAIPEI_SHIFT_PLUS_1"
            calendar_policy = "US_TRADING_DAY_SHIFTED_TO_TW_VIEW"
            fill_policy = "FORWARD_FILL_ALLOWED"
        elif "macro" in file_name or "fred" in file_name or "tnx" in file_name:
            market = "MACRO"
            timezone_policy = "SOURCE_TIMEZONE_TO_TAIPEI"
            calendar_policy = "MACRO_CALENDAR_FORWARD_FILL"
            fill_policy = "FORWARD_FILL_ALLOWED"

        if schema_role in ["PRICE_TIME_SERIES_SCHEMA", "PRICE_FLOW_DUAL_AXIS_SCHEMA", "PRICE_TA_VOLUME_SCHEMA", "FLOW_TIME_SERIES_SCHEMA"]:
            alignable = True
        else:
            alignable = False

        rows.append({
            "alignment_id": f"ALN_{row.get('asset_id','')}",
            "asset_id": row.get("asset_id", ""),
            "file_name": row.get("file_name", ""),
            "schema_role": schema_role,
            "market": market,
            "alignable": alignable,
            "primary_timeline": "TW_TRADING_DATE",
            "timezone_policy": timezone_policy,
            "calendar_policy": calendar_policy,
            "fill_policy": fill_policy,
            "normalized_date_column": "NormalizedDate",
        })

    return pd.DataFrame(rows)


# =============================================================================
# def AUTO DASHBOARD COMPOSITION
# =============================================================================

def def_build_auto_dashboard_registry(asset_df: pd.DataFrame, component_df: pd.DataFrame, schema_df: pd.DataFrame) -> pd.DataFrame:
    rows: List[Dict[str, Any]] = []

    if asset_df.empty:
        return pd.DataFrame(rows)

    heatmaps = asset_df[asset_df["taxonomy"].astype(str).str.contains("HEATMAP", na=False)]
    duals = asset_df[asset_df["taxonomy"].astype(str).str.contains("DUAL_AXIS", na=False)]
    stacks = asset_df[asset_df["taxonomy"].astype(str).str.contains("STACK", na=False)]
    dashboards = asset_df[asset_df["taxonomy"].astype(str).str.contains("DASHBOARD", na=False)]
    candles = asset_df[asset_df["taxonomy"].astype(str).str.contains("CANDLE", na=False)]

    def pick(df: pd.DataFrame, n: int) -> List[str]:
        if df.empty:
            return []
        return [str(x) for x in df.head(n)["asset_id"].tolist()]

    compositions = [
        {
            "composition_id": "DASH_GLOBAL_MARKET_OVERVIEW",
            "name": "Global Market Overview",
            "layout_type": "WORLD_MAP_CENTER_GRID",
            "primary_assets_json": json.dumps(pick(heatmaps, 2) + pick(duals, 2) + pick(dashboards, 1), ensure_ascii=False),
            "component_slots_json": json.dumps(["HEADER_HERO", "WATCHLIST", "HEATMAP_BLOCK", "PLOT_CARD", "KPI_CARD"], ensure_ascii=False),
            "recommended_use": "全球 ETF / 資金流 / 區域熱力圖首頁",
            "confidence": 88,
        },
        {
            "composition_id": "DASH_PRICE_FLOW_ANALYTICS",
            "name": "Price + Flow Analytics",
            "layout_type": "DUAL_AXIS_PLUS_STACK",
            "primary_assets_json": json.dumps(pick(duals, 3) + pick(stacks, 2), ensure_ascii=False),
            "component_slots_json": json.dumps(["HEADER_HERO", "PLOT_CARD", "PLOT_CARD", "PROGRESS_BAR"], ensure_ascii=False),
            "recommended_use": "個股價格、量、法人、資金流雙軸分析",
            "confidence": 90,
        },
        {
            "composition_id": "DASH_TECHNICAL_TIMELINE",
            "name": "Technical Timeline",
            "layout_type": "VERTICAL_STACK_TIMELINE",
            "primary_assets_json": json.dumps(pick(candles, 3) + pick(stacks, 2), ensure_ascii=False),
            "component_slots_json": json.dumps(["HEADER_HERO", "PLOT_CARD", "PLOT_CARD", "EVENT_MATRIX"], ensure_ascii=False),
            "recommended_use": "K線、均線、布林、量能、技術指標堆圖",
            "confidence": 87,
        },
    ]

    rows.extend(compositions)
    return pd.DataFrame(rows)


# =============================================================================
# def IO / WAREHOUSE
# =============================================================================

def def_write_refresh() -> None:
    content = f"""#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = "{PYTHON_EXE}"
$Builder = "{BUILDER_PY}"
$Html = "{HTML_PATH}"
Write-Host ""
Write-Host "Refreshing VAP Warehouse V4..." -ForegroundColor Cyan
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


def def_write_table(con: duckdb.DuckDBPyConnection, name: str, df: pd.DataFrame) -> None:
    if df is None or df.empty:
        df = pd.DataFrame([{"_empty": True}])
    con.register("tmp_df", df)
    con.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM tmp_df")
    con.unregister("tmp_df")
    out = str(PARQUET_ROOT / f"{name}.parquet").replace("\\", "/")
    con.execute(f"COPY {name} TO '{out}' (FORMAT PARQUET)")


def def_write_csv(df: pd.DataFrame, path_value: Path) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path_value, index=False, encoding="utf-8-sig")


def def_write_html(summary: Dict[str, Any], component_df: pd.DataFrame, token_df: pd.DataFrame, schema_df: pd.DataFrame, alignment_df: pd.DataFrame, dashboard_df: pd.DataFrame) -> None:
    def table_html(df: pd.DataFrame, cols: List[str], max_rows: int = 300) -> str:
        if df.empty:
            return "<tr><td>EMPTY</td></tr>"
        trs = []
        for _, row in df.head(max_rows).iterrows():
            tds = "".join(f"<td>{html.escape(str(row.get(c,'')))}</td>" for c in cols)
            trs.append(f"<tr>{tds}</tr>")
        heads = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
        return f"<thead><tr>{heads}</tr></thead><tbody>{''.join(trs)}</tbody>"

    comp_cols = ["component_id", "file_name", "component_type", "signal_count", "confidence"]
    token_cols = ["token_id", "file_name", "token_type", "token_value"]
    schema_cols = ["schema_id", "file_name", "schema_role", "suggested_template", "header_count"]
    align_cols = ["alignment_id", "file_name", "schema_role", "market", "alignable", "timezone_policy", "calendar_policy"]
    dash_cols = ["composition_id", "name", "layout_type", "recommended_use", "confidence"]

    doc = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VAP Warehouse V4 Intelligence Report</title>
<style>
:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}
body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}
.wrap{{max-width:1780px;margin:0 auto;padding:14px}}
.hero{{background:var(--sf);border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}
.hero:before{{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}
.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}}
h1{{font-size:20px;margin:0}}.sub{{font-family:Consolas,monospace;color:var(--muted);font-size:10px;margin-top:3px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:8px;margin-bottom:10px}}
.kpi{{background:#fff;border:1px solid var(--bd);border-left:4px solid var(--blue);border-radius:10px;padding:10px}}.kpi.ok{{border-left-color:var(--green)}}.kpi.warn{{border-left-color:var(--amber)}}
.k{{font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase}}.v{{font-family:Consolas,monospace;font-size:24px;font-weight:900}}
.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;margin-bottom:10px}}
table{{width:100%;border-collapse:collapse;font-size:10.5px}}th{{position:sticky;top:0;background:#eceae4;border-bottom:2px solid var(--bd);padding:7px;text-align:left}}td{{border-bottom:1px solid var(--bd);padding:6px;vertical-align:top}}tr:hover{{background:rgba(76,120,168,.04)}}
code{{font-family:Consolas,monospace;font-size:10px;background:#eceae4;border:1px solid var(--bd);border-radius:5px;padding:1px 5px}}
</style>
</head>
<body><div class="wrap">
<div class="hero"><div class="heroIn"><div><h1>VAP Warehouse V4 Intelligence Report</h1><div class="sub">VERITAS INTELLIGENCE ANALYTICS · Component Registry · Visual Tokens · Schema Intelligence · Alignment · Auto Dashboard</div><div class="sub">Generated: {html.escape(summary.get('generated_at',''))}</div></div><div style="font-size:20px;color:var(--green);font-weight:900">V4 READY</div></div></div>
<div class="grid">
<div class="kpi ok"><div class="k">Assets</div><div class="v">{summary.get('assets',0)}</div></div>
<div class="kpi ok"><div class="k">Warnings</div><div class="v">{summary.get('warnings',0)}</div></div>
<div class="kpi ok"><div class="k">Components</div><div class="v">{summary.get('components',0)}</div></div>
<div class="kpi ok"><div class="k">Visual Tokens</div><div class="v">{summary.get('visual_tokens',0)}</div></div>
<div class="kpi ok"><div class="k">Schemas</div><div class="v">{summary.get('schemas',0)}</div></div>
<div class="kpi ok"><div class="k">Dashboards</div><div class="v">{summary.get('dashboards',0)}</div></div>
</div>
<div class="card"><b>DuckDB</b><br><code>{html.escape(summary.get('duckdb_path',''))}</code></div>
<div class="card"><b>ParquetRoot</b><br><code>{html.escape(summary.get('parquet_root',''))}</code></div>
<div class="card"><b>Auto Dashboard Composition</b><div style="overflow:auto;max-height:360px"><table>{table_html(dashboard_df, dash_cols)}</table></div></div>
<div class="card"><b>Schema Intelligence</b><div style="overflow:auto;max-height:460px"><table>{table_html(schema_df, schema_cols)}</table></div></div>
<div class="card"><b>Alignment Policy</b><div style="overflow:auto;max-height:460px"><table>{table_html(alignment_df, align_cols)}</table></div></div>
<div class="card"><b>Component Registry</b><div style="overflow:auto;max-height:560px"><table>{table_html(component_df, comp_cols)}</table></div></div>
<div class="card"><b>Visual Token Registry</b><div style="overflow:auto;max-height:560px"><table>{table_html(token_df, token_cols)}</table></div></div>
<div class="card"><b>Refresh Launcher</b><br><code>{html.escape(str(REFRESH_PS1))}</code></div>
</div></body></html>"""
    HTML_PATH.write_text(doc, encoding="utf-8")


def def_main() -> int:
    for p in [BASE_ROOT, INPUT_ROOT, OUTPUT_ROOT, WAREHOUSE_ROOT, RUN_DIR, PARQUET_ROOT]:
        p.mkdir(parents=True, exist_ok=True)

    asset_df = def_read_duckdb_table("asset_registry")
    if asset_df.empty:
        raise RuntimeError("asset_registry not found in DuckDB. Run VAP_DuckDB_Parquet_IntelligenceWarehouse_AllInOne.ps1 first.")

    asset_df = def_normalize_asset_registry(asset_df)
    component_df = def_build_component_registry(asset_df)
    token_df = def_build_visual_token_registry(asset_df)
    schema_df = def_build_schema_registry(asset_df)
    alignment_df = def_build_alignment_policy_registry(asset_df, schema_df)
    dashboard_df = def_build_auto_dashboard_registry(asset_df, component_df, schema_df)

    warnings = asset_df[asset_df["warning_reason"].fillna("") != ""].copy() if "warning_reason" in asset_df.columns else pd.DataFrame()

    con = duckdb.connect(str(DUCKDB_PATH))
    def_write_table(con, "asset_registry_v4", asset_df)
    def_write_table(con, "component_registry", component_df)
    def_write_table(con, "visual_token_registry", token_df)
    def_write_table(con, "schema_intelligence_registry", schema_df)
    def_write_table(con, "alignment_policy_registry", alignment_df)
    def_write_table(con, "auto_dashboard_registry", dashboard_df)
    def_write_table(con, "warning_assets_v4", warnings)
    con.close()

    summary = {
        "generated_at": def_now(),
        "run_dir": str(RUN_DIR),
        "duckdb_path": str(DUCKDB_PATH),
        "parquet_root": str(PARQUET_ROOT),
        "html_path": str(HTML_PATH),
        "payload_json": str(PAYLOAD_JSON),
        "matrix_csv": str(MATRIX_CSV),
        "refresh_ps1": str(REFRESH_PS1),
        "assets": int(len(asset_df)),
        "warnings": int(len(warnings)),
        "components": int(len(component_df)),
        "visual_tokens": int(len(token_df)),
        "schemas": int(len(schema_df)),
        "alignment_policies": int(len(alignment_df)),
        "dashboards": int(len(dashboard_df)),
        "tables_added": [
            "asset_registry_v4",
            "component_registry",
            "visual_token_registry",
            "schema_intelligence_registry",
            "alignment_policy_registry",
            "auto_dashboard_registry",
            "warning_assets_v4",
        ],
        "parquet_files_added": [
            str(PARQUET_ROOT / "asset_registry_v4.parquet"),
            str(PARQUET_ROOT / "component_registry.parquet"),
            str(PARQUET_ROOT / "visual_token_registry.parquet"),
            str(PARQUET_ROOT / "schema_intelligence_registry.parquet"),
            str(PARQUET_ROOT / "alignment_policy_registry.parquet"),
            str(PARQUET_ROOT / "auto_dashboard_registry.parquet"),
            str(PARQUET_ROOT / "warning_assets_v4.parquet"),
        ],
    }

    payload = {
        "summary": summary,
        "component_registry": component_df.to_dict(orient="records"),
        "visual_token_registry": token_df.head(1000).to_dict(orient="records"),
        "schema_intelligence_registry": schema_df.to_dict(orient="records"),
        "alignment_policy_registry": alignment_df.to_dict(orient="records"),
        "auto_dashboard_registry": dashboard_df.to_dict(orient="records"),
    }

    def_write_json(SUMMARY_JSON, summary)
    def_write_json(PAYLOAD_JSON, payload)
    asset_df.to_csv(MATRIX_CSV, index=False, encoding="utf-8-sig")
    def_write_refresh()
    def_write_html(summary, component_df, token_df, schema_df, alignment_df, dashboard_df)

    print(json.dumps(summary, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(def_main())
    except SystemExit as sx:
        if getattr(sx, "code", 0) not in (0, None):
            raise
    except BaseException:
        print(traceback.format_exc())
        raise
