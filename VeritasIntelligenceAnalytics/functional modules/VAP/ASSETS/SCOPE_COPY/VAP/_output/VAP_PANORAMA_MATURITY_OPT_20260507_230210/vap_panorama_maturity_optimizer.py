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
import html
import re
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
RUN_DIR = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PANORAMA_MATURITY_OPT_20260507_230210")

HTML_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PANORAMA_MATURITY_OPT_20260507_230210\\VAP_Panorama_Maturity_Optimization_Report.html")
SUMMARY_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PANORAMA_MATURITY_OPT_20260507_230210\\vap_panorama_maturity_summary.json")
PAYLOAD_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PANORAMA_MATURITY_OPT_20260507_230210\\vap_panorama_maturity_payload.json")
MATRIX_CSV = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PANORAMA_MATURITY_OPT_20260507_230210\\vap_panorama_maturity_matrix.csv")
QUERY_PACK_SQL = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PANORAMA_MATURITY_OPT_20260507_230210\\vap_panorama_maturity_query_pack.sql")
NEXT_ACTIONS_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PANORAMA_MATURITY_OPT_20260507_230210\\Invoke-VAP-Next-Optimization-Actions.ps1")
REFRESH_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PANORAMA_MATURITY_OPT_20260507_230210\\Invoke-VAP-Panorama-Maturity-Refresh.ps1")
PYTHON_EXE = r"C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"
BUILDER_PY = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PANORAMA_MATURITY_OPT_20260507_230210\\vap_panorama_maturity_optimizer.py")


# =============================================================================
# def UTILITIES
# =============================================================================

def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_write_json(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


def def_read_json(path_value: Path, default=None):
    if default is None:
        default = {}
    try:
        if path_value.exists():
            return json.loads(path_value.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def def_safe_table(con: duckdb.DuckDBPyConnection, table_name: str) -> pd.DataFrame:
    try:
        return con.execute(f"SELECT * FROM {table_name}").fetchdf()
    except Exception:
        return pd.DataFrame()


def def_table_exists(con: duckdb.DuckDBPyConnection, table_name: str) -> bool:
    try:
        con.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
        return True
    except Exception:
        return False


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


def def_latest_run(pattern: str) -> Dict[str, Any]:
    dirs = sorted([p for p in OUTPUT_ROOT.glob(pattern) if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    if not dirs:
        return {"exists": False, "run_dir": "", "summary": {}, "summary_path": "", "html_path": ""}
    d = dirs[0]
    summaries = sorted(d.glob("*summary*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    htmls = sorted(d.glob("*.html"), key=lambda p: p.stat().st_mtime, reverse=True)
    sp = summaries[0] if summaries else Path("")
    hp = htmls[0] if htmls else Path("")
    return {
        "exists": True,
        "run_dir": str(d),
        "summary": def_read_json(sp, {}),
        "summary_path": str(sp) if summaries else "",
        "html_path": str(hp) if htmls else "",
    }


# =============================================================================
# def PANORAMA SCAN
# =============================================================================

def def_scan_versions() -> pd.DataFrame:
    specs = [
        ("V4_WAREHOUSE", "VAP_WAREHOUSE_V4_*"),
        ("V5_NEXT3", "VAP_WAREHOUSE_V5_NEXT3_*"),
        ("V6_WORKSTATION", "VAP_WAREHOUSE_V6_ALL_*"),
        ("V7_QUANT", "VAP_WAREHOUSE_V7_QUANT_*"),
        ("COMPLETION", "VAP_PROJECT_COMPLETION*"),
    ]
    rows = []
    for name, pattern in specs:
        r = def_latest_run(pattern)
        s = r.get("summary", {})
        rows.append({
            "version": name,
            "exists": r["exists"],
            "run_dir": r["run_dir"],
            "summary_path": r["summary_path"],
            "html_path": r["html_path"],
            "assets": s.get("assets", ""),
            "warnings": s.get("warnings", s.get("active_warnings", "")),
            "components": s.get("components", ""),
            "visual_tokens": s.get("visual_tokens", ""),
            "schemas": s.get("schemas", ""),
            "dashboards": s.get("dashboards", s.get("generated_dashboards", "")),
            "timelines": s.get("timelines", ""),
            "relations": s.get("relations", ""),
            "corr_plans": s.get("corr_plans", s.get("rolling_corr_rows", "")),
            "lag_plans": s.get("lag_plans", s.get("lead_lag_rows", "")),
            "price_rows": s.get("price_rows", s.get("live_price_rows", "")),
            "status_hint": s.get("status", "OK" if r["exists"] else "MISSING"),
        })
    return pd.DataFrame(rows)


def def_scan_duckdb() -> tuple[pd.DataFrame, Dict[str, int], Dict[str, bool]]:
    required = [
        "asset_registry_v4",
        "component_registry",
        "visual_token_registry",
        "schema_intelligence_registry",
        "alignment_policy_registry",
        "auto_dashboard_registry",
        "plot_dna_registry",
        "live_data_source_registry",
        "fetch_plan_registry",
        "live_fetch_status_v6",
        "dashboard_blueprint_registry",
        "generated_dashboard_registry",
        "timeline_alignment_registry",
        "cross_asset_relation_registry",
        "coaxis_policy_registry",
        "rolling_correlation_plan",
        "lead_lag_plan",
        "quant_normalized_returns_v7",
        "quant_rolling_correlation_v7",
        "quant_lead_lag_score_v7",
        "quant_factor_plan_v7",
        "quant_regime_plan_v7",
    ]

    rows = []
    counts = {}
    exists_map = {}
    if not DUCKDB_PATH.exists():
        for t in required:
            rows.append({"table": t, "exists": False, "rows": 0, "maturity_role": def_table_role(t)})
            counts[t] = 0
            exists_map[t] = False
        return pd.DataFrame(rows), counts, exists_map

    con = duckdb.connect(str(DUCKDB_PATH))
    for t in required:
        ex = def_table_exists(con, t)
        n = def_table_count(con, t) if ex else 0
        rows.append({"table": t, "exists": ex, "rows": n, "maturity_role": def_table_role(t)})
        counts[t] = n
        exists_map[t] = ex
    con.close()
    return pd.DataFrame(rows), counts, exists_map


def def_table_role(table: str) -> str:
    if table in ["asset_registry_v4", "plot_dna_registry"]:
        return "ASSET_INTELLIGENCE"
    if table in ["component_registry", "visual_token_registry"]:
        return "VISUAL_GOVERNANCE"
    if table in ["schema_intelligence_registry", "alignment_policy_registry"]:
        return "SCHEMA_ALIGNMENT"
    if table in ["auto_dashboard_registry", "dashboard_blueprint_registry", "generated_dashboard_registry"]:
        return "DASHBOARD_COMPOSITION"
    if table in ["live_data_source_registry", "fetch_plan_registry", "live_fetch_status_v6"]:
        return "LIVE_DATA_ENGINE"
    if table in ["timeline_alignment_registry", "cross_asset_relation_registry", "coaxis_policy_registry"]:
        return "TIMELINE_INTELLIGENCE"
    if table in ["rolling_correlation_plan", "lead_lag_plan", "quant_normalized_returns_v7", "quant_rolling_correlation_v7", "quant_lead_lag_score_v7", "quant_factor_plan_v7", "quant_regime_plan_v7"]:
        return "QUANT_INTELLIGENCE"
    return "OTHER"


def def_scan_parquet() -> pd.DataFrame:
    rows = []
    files = sorted(PARQUET_ROOT.glob("*.parquet")) if PARQUET_ROOT.exists() else []
    for p in files:
        rows.append({
            "file_name": p.name,
            "path": str(p),
            "size_bytes": p.stat().st_size,
            "table_guess": p.stem,
            "exists": True,
        })
    return pd.DataFrame(rows)


# =============================================================================
# def MATURITY
# =============================================================================

def def_score_layer(layer: str, counts: Dict[str, int], exists_map: Dict[str, bool]) -> Dict[str, Any]:
    score = 0
    max_score = 100
    evidence = []
    gap = []
    next_action = []

    def has(t, min_rows=1):
        return bool(exists_map.get(t, False)) and int(counts.get(t, 0)) >= min_rows

    if layer == "Asset Intelligence":
        checks = [
            ("asset_registry_v4", 30), ("plot_dna_registry", 25), ("schema_intelligence_registry", 20),
            ("asset_registry_v4_rows", 25)
        ]
        if has("asset_registry_v4"): score += 30; evidence.append("asset_registry_v4")
        else: gap.append("asset_registry_v4 missing")
        if has("plot_dna_registry"): score += 25; evidence.append("plot_dna_registry")
        else: gap.append("plot_dna_registry missing")
        if has("schema_intelligence_registry"): score += 20; evidence.append("schema_intelligence_registry")
        else: gap.append("schema_intelligence_registry missing")
        if counts.get("asset_registry_v4", 0) >= 100: score += 25; evidence.append("assets>=100")
        else: gap.append("asset count < 100")
        next_action.append("保持 V4 asset registry；開始接 live data 對應 schema。")

    elif layer == "Visual Governance":
        if has("component_registry"): score += 35; evidence.append("component_registry")
        else: gap.append("component_registry missing")
        if has("visual_token_registry"): score += 35; evidence.append("visual_token_registry")
        else: gap.append("visual_token_registry missing")
        if counts.get("visual_token_registry", 0) >= 1000: score += 20; evidence.append("visual tokens >= 1000")
        else: gap.append("visual tokens not rich enough")
        if counts.get("component_registry", 0) >= 100: score += 10; evidence.append("components >= 100")
        next_action.append("建立 visual token normalization：統一 color/radius/shadow/font/grid 命名。")

    elif layer == "Dashboard Composition":
        if has("dashboard_blueprint_registry"): score += 30; evidence.append("dashboard_blueprint_registry")
        else: gap.append("dashboard_blueprint_registry missing")
        if has("generated_dashboard_registry"): score += 30; evidence.append("generated_dashboard_registry")
        else: gap.append("generated_dashboard_registry missing")
        if has("auto_dashboard_registry"): score += 20; evidence.append("auto_dashboard_registry")
        else: gap.append("auto_dashboard_registry missing")
        if counts.get("generated_dashboard_registry", 0) >= 3: score += 20; evidence.append("generated dashboards >= 3")
        else: gap.append("generated dashboards < 3")
        next_action.append("將 generated dashboard 由 placeholder 升級為 Plotly data-bound dashboard。")

    elif layer == "Live Data Engine":
        if has("live_data_source_registry"): score += 25; evidence.append("live_data_source_registry")
        else: gap.append("live_data_source_registry missing")
        if has("fetch_plan_registry"): score += 25; evidence.append("fetch_plan_registry")
        else: gap.append("fetch_plan_registry missing")
        if has("live_fetch_status_v6"): score += 20; evidence.append("live_fetch_status_v6")
        else: gap.append("live_fetch_status_v6 missing")
        # live_price_sample_v6 may have 1 placeholder row
        live_price_rows = counts.get("live_price_sample_v6", 0)
        if live_price_rows > 10:
            score += 30
            evidence.append("live price data present")
        else:
            score += 5 if live_price_rows >= 1 else 0
            gap.append("live price data not active; EnableNetworkFetch remains disabled or data absent")
            next_action.append("重跑 V6，將 EnableNetworkFetch = $true，取得 yfinance 實價資料。")
        next_action.append("之後加入 TWSE/TPEX/FRED connector。")

    elif layer == "Timeline Intelligence":
        if has("timeline_alignment_registry"): score += 30; evidence.append("timeline_alignment_registry")
        else: gap.append("timeline_alignment_registry missing")
        if has("cross_asset_relation_registry"): score += 30; evidence.append("cross_asset_relation_registry")
        else: gap.append("cross_asset_relation_registry missing")
        if has("coaxis_policy_registry"): score += 25; evidence.append("coaxis_policy_registry")
        else: gap.append("coaxis_policy_registry missing")
        if has("alignment_policy_registry"): score += 15; evidence.append("alignment_policy_registry")
        next_action.append("將 timeline policy 套用到 actual fetched data，產生 NormalizedDate 實體資料。")

    elif layer == "Quant Intelligence":
        if has("rolling_correlation_plan"): score += 18; evidence.append("rolling_correlation_plan")
        else: gap.append("rolling_correlation_plan missing")
        if has("lead_lag_plan"): score += 18; evidence.append("lead_lag_plan")
        else: gap.append("lead_lag_plan missing")
        if has("quant_factor_plan_v7"): score += 18; evidence.append("quant_factor_plan_v7")
        else: gap.append("quant_factor_plan_v7 missing")
        if has("quant_regime_plan_v7"): score += 18; evidence.append("quant_regime_plan_v7")
        else: gap.append("quant_regime_plan_v7 missing")

        # If quant calc tables exist but only plan-only placeholder, still partial
        qcorr_rows = counts.get("quant_rolling_correlation_v7", 0)
        qlag_rows = counts.get("quant_lead_lag_score_v7", 0)
        qnorm_rows = counts.get("quant_normalized_returns_v7", 0)

        if qnorm_rows > 10 and qcorr_rows > 10 and qlag_rows > 10:
            score += 28
            evidence.append("actual quant calculation rows present")
        else:
            score += 6 if qnorm_rows >= 1 else 0
            gap.append("quant calculation is plan-only due to missing live price data")
            next_action.append("先啟用 V6 live fetch，再重跑 V7，讓 rolling correlation / lead-lag 從 plan-only 轉為 calculated。")

    return {
        "layer": layer,
        "score": min(100, score),
        "grade": def_grade(score),
        "evidence": " | ".join(evidence),
        "gaps": " | ".join(gap) if gap else "NONE",
        "next_action": " | ".join(next_action),
    }


def def_grade(score: int) -> str:
    if score >= 95:
        return "A+ COMPLETE"
    if score >= 85:
        return "A READY"
    if score >= 75:
        return "B+ NEAR_READY"
    if score >= 60:
        return "B FOUNDATION_READY"
    if score >= 40:
        return "C PARTIAL"
    return "D NEEDS_BUILD"


def def_build_maturity_matrix(counts: Dict[str, int], exists_map: Dict[str, bool]) -> pd.DataFrame:
    layers = [
        "Asset Intelligence",
        "Visual Governance",
        "Dashboard Composition",
        "Live Data Engine",
        "Timeline Intelligence",
        "Quant Intelligence",
    ]
    return pd.DataFrame([def_score_layer(x, counts, exists_map) for x in layers])


def def_build_optimization_backlog(maturity_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    priority = 1
    for _, r in maturity_df.sort_values("score").iterrows():
        score = int(r["score"])
        layer = str(r["layer"])
        gaps = str(r["gaps"])
        action = str(r["next_action"])
        if score < 95:
            rows.append({
                "priority": priority,
                "layer": layer,
                "score": score,
                "gap": gaps,
                "optimization_action": action,
                "risk": "LOW" if score >= 75 else "MEDIUM",
                "mode": "APPEND_ONLY_NO_DELETE",
            })
            priority += 1

    rows.append({
        "priority": priority,
        "layer": "Final Hardening",
        "score": 100,
        "gap": "Need final repeatable orchestration",
        "optimization_action": "建立 V8 master orchestrator：V6 live fetch → V7 quant → maturity optimizer → final completion seal。",
        "risk": "LOW",
        "mode": "APPEND_ONLY_NO_DELETE",
    })
    return pd.DataFrame(rows)


def def_build_next_action_commands() -> List[str]:
    return [
        "# 01. 啟用實價資料：打開 V6 腳本，將 EnableNetworkFetch = $true，重跑 V6",
        "# 02. 重跑 V7：產生 actual normalized returns / rolling correlation / lead-lag score",
        "# 03. 重跑本 maturity optimizer：確認 Live Data / Quant score 從 plan-only 提升",
        "# 04. 下一階段 V8：產生 Master Orchestrator，將 V6 → V7 → Optimizer 串成單鍵流程",
    ]


# =============================================================================
# def OUTPUT
# =============================================================================

def def_write_query_pack() -> None:
    sql = """
-- VAP Panorama Maturity Optimization Query Pack

SELECT * FROM panorama_maturity_matrix ORDER BY score DESC;
SELECT * FROM panorama_optimization_backlog ORDER BY priority;
SELECT * FROM panorama_duckdb_table_audit ORDER BY maturity_role, table;
SELECT * FROM panorama_version_audit ORDER BY version;
SELECT * FROM panorama_parquet_audit ORDER BY file_name;

-- Where quant is still plan-only
SELECT * FROM panorama_maturity_matrix
WHERE gaps LIKE '%plan-only%' OR gaps LIKE '%live price%';

-- Core quant tables
SELECT * FROM quant_normalized_returns_v7 LIMIT 50;
SELECT * FROM quant_rolling_correlation_v7 LIMIT 50;
SELECT * FROM quant_lead_lag_score_v7 LIMIT 50;
"""
    QUERY_PACK_SQL.write_text(sql.strip() + "\n", encoding="utf-8")


def def_write_next_actions_ps1(commands: List[str]) -> None:
    text = f"""#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "VAP Next Optimization Actions" -ForegroundColor Cyan
Write-Host "1) Open V6 script and set EnableNetworkFetch = `$true" -ForegroundColor Yellow
Write-Host "2) Re-run V6 to fetch live data" -ForegroundColor Yellow
Write-Host "3) Re-run V7 to calculate quant tables" -ForegroundColor Yellow
Write-Host "4) Re-run maturity optimizer to confirm score improvement" -ForegroundColor Yellow
Write-Host ""
Write-Host "Commands are guidance only. This file intentionally does not auto-edit your scripts." -ForegroundColor DarkGray
"""
    NEXT_ACTIONS_PS1.write_text(text, encoding="utf-8-sig")


def def_write_refresh() -> None:
    content = f"""#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"
$Python = "{PYTHON_EXE}"
$Builder = "{BUILDER_PY}"
$Html = "{HTML_PATH}"
Write-Host ""
Write-Host "Refreshing VAP Panorama Maturity Optimizer..." -ForegroundColor Cyan
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


def def_table_html(df: pd.DataFrame, cols: List[str], max_rows: int = 200) -> str:
    if df is None or df.empty:
        return "<thead><tr><th>EMPTY</th></tr></thead><tbody><tr><td>EMPTY</td></tr></tbody>"
    heads = "".join(f"<th>{html.escape(c)}</th>" for c in cols)
    trs = []
    for _, r in df.head(max_rows).iterrows():
        tds = "".join(f"<td>{html.escape(str(r.get(c,'')))}</td>" for c in cols)
        trs.append(f"<tr>{tds}</tr>")
    return f"<thead><tr>{heads}</tr></thead><tbody>{''.join(trs)}</tbody>"


def def_write_html(summary: Dict[str, Any], dfs: Dict[str, pd.DataFrame]) -> None:
    score = summary.get("overall_score", 0)
    grade = summary.get("overall_grade", "")
    action_items = "".join(f"<li><code>{html.escape(x)}</code></li>" for x in summary.get("next_action_commands", []))

    doc = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VAP Panorama Maturity Optimization Report</title>
<style>
:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}
body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}
.wrap{{max-width:1780px;margin:0 auto;padding:14px}}
.hero{{background:#fff;border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}
.hero:before{{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}
.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}}
h1{{font-size:20px;margin:0}}.sub{{font-family:Consolas,monospace;color:var(--muted);font-size:10px;margin-top:3px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin-bottom:10px}}
.kpi{{background:#fff;border:1px solid var(--bd);border-left:4px solid var(--green);border-radius:10px;padding:10px}}
.kpi.warn{{border-left-color:var(--amber)}}.kpi.blue{{border-left-color:var(--blue)}}
.k{{font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase}}.v{{font-family:Consolas,monospace;font-size:24px;font-weight:900}}
.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;margin-bottom:10px}}
table{{width:100%;border-collapse:collapse;font-size:10.5px}}th{{position:sticky;top:0;background:#eceae4;border-bottom:2px solid var(--bd);padding:7px;text-align:left}}td{{border-bottom:1px solid var(--bd);padding:6px;vertical-align:top}}tr:hover{{background:rgba(76,120,168,.04)}}
code{{font-family:Consolas,monospace;font-size:10px;background:#eceae4;border:1px solid var(--bd);border-radius:5px;padding:1px 5px}}
.badge{{display:inline-block;background:#d8ecd8;color:var(--green);padding:4px 8px;border-radius:999px;font-weight:900}}
.progress{{height:8px;background:#e3e0d8;border-radius:99px;overflow:hidden;margin-top:8px}}.bar{{height:100%;width:{score}%;background:linear-gradient(90deg,var(--blue),var(--teal),var(--green));animation:load 1s ease-out}}@keyframes load{{from{{width:0}}}}
</style>
</head>
<body><div class="wrap">
<div class="hero"><div class="heroIn"><div><h1>VAP Panorama Maturity Optimization Report</h1><div class="sub">VERITAS INTELLIGENCE ANALYTICS · 全景式成熟度分析 · Optimization Backlog · DuckDB / Parquet Seal</div><div class="sub">Generated: {html.escape(summary.get('generated_at',''))}</div></div><div class="badge">{html.escape(grade)}</div></div></div>
<div class="grid">
<div class="kpi blue"><div class="k">Overall Score</div><div class="v">{score}</div></div>
<div class="kpi"><div class="k">Grade</div><div class="v">{html.escape(grade.split()[0] if grade else '')}</div></div>
<div class="kpi"><div class="k">DuckDB Tables</div><div class="v">{summary.get('duckdb_tables',0)}</div></div>
<div class="kpi"><div class="k">Parquet Files</div><div class="v">{summary.get('parquet_files',0)}</div></div>
<div class="kpi warn"><div class="k">Backlog</div><div class="v">{summary.get('backlog_items',0)}</div></div>
</div>
<div class="card"><b>Dynamic Maturity Progress</b><div class="progress"><div class="bar"></div></div></div>
<div class="card"><b>Interpretation</b><p>{html.escape(summary.get('interpretation',''))}</p></div>
<div class="card"><b>Next Action Commands</b><ol>{action_items}</ol></div>
<div class="card"><b>Maturity Matrix</b><div style="overflow:auto;max-height:480px"><table>{def_table_html(dfs['maturity'], ['layer','score','grade','evidence','gaps','next_action'])}</table></div></div>
<div class="card"><b>Optimization Backlog</b><div style="overflow:auto;max-height:520px"><table>{def_table_html(dfs['backlog'], ['priority','layer','score','gap','optimization_action','risk','mode'])}</table></div></div>
<div class="card"><b>Version Audit</b><div style="overflow:auto;max-height:360px"><table>{def_table_html(dfs['versions'], ['version','exists','assets','warnings','components','visual_tokens','dashboards','corr_plans','lag_plans','price_rows','status_hint','run_dir'])}</table></div></div>
<div class="card"><b>DuckDB Table Audit</b><div style="overflow:auto;max-height:520px"><table>{def_table_html(dfs['duckdb'], ['table','exists','rows','maturity_role'])}</table></div></div>
<div class="card"><b>Parquet Audit</b><div style="overflow:auto;max-height:520px"><table>{def_table_html(dfs['parquet'], ['file_name','size_bytes','table_guess','exists'])}</table></div></div>
<div class="card"><b>Artifacts</b><br>
Query Pack: <code>{html.escape(str(QUERY_PACK_SQL))}</code><br>
Next Actions: <code>{html.escape(str(NEXT_ACTIONS_PS1))}</code><br>
Refresh: <code>{html.escape(str(REFRESH_PS1))}</code>
</div>
</div></body></html>"""
    HTML_PATH.write_text(doc, encoding="utf-8")


# =============================================================================
# def MAIN
# =============================================================================

def main() -> int:
    for p in [BASE_ROOT, OUTPUT_ROOT, WAREHOUSE_ROOT, PARQUET_ROOT, RUN_DIR]:
        p.mkdir(parents=True, exist_ok=True)

    versions = def_scan_versions()
    duckdb_audit, counts, exists_map = def_scan_duckdb()
    parquet_audit = def_scan_parquet()
    maturity = def_build_maturity_matrix(counts, exists_map)
    backlog = def_build_optimization_backlog(maturity)
    commands = def_build_next_action_commands()

    overall_score = int(round(maturity["score"].mean())) if not maturity.empty else 0
    overall_grade = def_grade(overall_score)

    if overall_score >= 85:
        interpretation = "系統成熟度已達可用/可擴充狀態。最大缺口不是架構，而是 Live Data 啟用後的實際 quant 計算。"
    elif overall_score >= 70:
        interpretation = "核心架構已成形，但仍有資料層或計算層待啟用。"
    else:
        interpretation = "系統仍在基礎建置階段，應先補齊缺少的核心 tables。"

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
        "next_actions_ps1": str(NEXT_ACTIONS_PS1),
        "refresh_ps1": str(REFRESH_PS1),
        "overall_score": overall_score,
        "overall_grade": overall_grade,
        "interpretation": interpretation,
        "duckdb_tables": int(len(duckdb_audit)),
        "parquet_files": int(len(parquet_audit)),
        "backlog_items": int(len(backlog)),
        "next_action_commands": commands,
    }

    payload = {
        "summary": summary,
        "versions": versions.to_dict(orient="records"),
        "duckdb_audit": duckdb_audit.to_dict(orient="records"),
        "parquet_audit": parquet_audit.to_dict(orient="records"),
        "maturity": maturity.to_dict(orient="records"),
        "backlog": backlog.to_dict(orient="records"),
    }

    if DUCKDB_PATH.exists():
        con = duckdb.connect(str(DUCKDB_PATH))
        def_write_table(con, "panorama_version_audit", versions)
        def_write_table(con, "panorama_duckdb_table_audit", duckdb_audit)
        def_write_table(con, "panorama_parquet_audit", parquet_audit)
        def_write_table(con, "panorama_maturity_matrix", maturity)
        def_write_table(con, "panorama_optimization_backlog", backlog)
        con.close()

    def_write_json(SUMMARY_JSON, summary)
    def_write_json(PAYLOAD_JSON, payload)

    maturity.to_csv(MATRIX_CSV, index=False, encoding="utf-8-sig")
    def_write_query_pack()
    def_write_next_actions_ps1(commands)
    def_write_refresh()
    def_write_html(summary, {
        "versions": versions,
        "duckdb": duckdb_audit,
        "parquet": parquet_audit,
        "maturity": maturity,
        "backlog": backlog,
    })

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
