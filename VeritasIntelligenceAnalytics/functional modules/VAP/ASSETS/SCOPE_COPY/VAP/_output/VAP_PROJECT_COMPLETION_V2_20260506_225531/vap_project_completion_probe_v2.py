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
from pathlib import Path
from datetime import datetime

import duckdb
import pandas as pd


DUCKDB_PATH = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\vap_intelligence.duckdb")
PARQUET_ROOT = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_warehouse\\parquet")
V4_SUMMARY = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535\\vap_warehouse_v4_summary.json")
MANIFEST_JSON = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PROJECT_COMPLETION_V2_20260506_225531\\vap_project_completion_manifest_v2.json")
COMPLETION_CSV = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PROJECT_COMPLETION_V2_20260506_225531\\vap_project_completion_matrix_v2.csv")
QUERY_PACK_SQL = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PROJECT_COMPLETION_V2_20260506_225531\\vap_duckdb_query_pack_v2.sql")
HANDOVER_HTML = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PROJECT_COMPLETION_V2_20260506_225531\\VAP_Project_Completion_Handover_v2.html")
VERIFY_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PROJECT_COMPLETION_V2_20260506_225531\\Invoke-VAP-Project-Verify-v2.ps1")
REFRESH_PS1 = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_PROJECT_COMPLETION_V2_20260506_225531\\Invoke-VAP-Project-Refresh-v2.ps1")
LATEST_V4_HTML = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535\\VAP_Warehouse_V4_Intelligence_Report.html")
LATEST_V4_BUILDER = Path(r"C:\\Users\\tonyk\\OneDrive\\VeritasIntelligenceAnalytics\\module\\VAP\\_output\\VAP_WAREHOUSE_V4_20260506_222535\\vap_warehouse_v4_builder.py")
PYTHON_EXE = r"C:\\Users\\tonyk\\envs\\via_core_312\\Scripts\\python.exe"


def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_read_json(path_value: Path, default):
    try:
        if path_value.exists():
            return json.loads(path_value.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def def_table_count(con, table_name: str) -> int:
    try:
        return int(con.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0])
    except Exception:
        return -1


def def_table_exists(con, table_name: str) -> bool:
    try:
        con.execute(f"SELECT 1 FROM {table_name} LIMIT 1").fetchone()
        return True
    except Exception:
        return False


def def_active_warning_count(con) -> int:
    """
    Finalizer v2 fix:
    warning_assets_v4 可能保留 placeholder / historical row。
    只有 warning_reason 非空才算 active warning。
    """
    try:
        if not def_table_exists(con, "warning_assets_v4"):
            return -1

        cols = [x[1] for x in con.execute("PRAGMA table_info('warning_assets_v4')").fetchall()]
        if "warning_reason" not in cols:
            return 0

        return int(con.execute("""
            SELECT COUNT(*)
            FROM warning_assets_v4
            WHERE warning_reason IS NOT NULL
              AND TRIM(CAST(warning_reason AS VARCHAR)) <> ''
              AND LOWER(TRIM(CAST(warning_reason AS VARCHAR))) NOT IN ('none', 'null', 'nan')
        """).fetchone()[0])
    except Exception:
        return -1


def def_write_query_pack() -> None:
    sql = r"""
-- VAP DuckDB Query Pack v2
-- VERITAS INTELLIGENCE ANALYTICS

-- 01. Taxonomy Inventory
SELECT taxonomy, COUNT(*) AS asset_count
FROM asset_registry_v4
GROUP BY taxonomy
ORDER BY asset_count DESC;

-- 02. Active Warnings Only
SELECT *
FROM warning_assets_v4
WHERE warning_reason IS NOT NULL
  AND TRIM(CAST(warning_reason AS VARCHAR)) <> ''
  AND LOWER(TRIM(CAST(warning_reason AS VARCHAR))) NOT IN ('none', 'null', 'nan');

-- 03. 雙軸模板
SELECT asset_id, file_name, taxonomy, best_template, axes
FROM asset_registry_v4
WHERE axes = 2
ORDER BY file_name;

-- 04. Heatmap / Event Matrix / Stack
SELECT asset_id, file_name, taxonomy, supports_heatmap, supports_event_matrix, supports_stack
FROM asset_registry_v4
WHERE supports_heatmap OR supports_event_matrix OR supports_stack
ORDER BY taxonomy, file_name;

-- 05. Component Registry
SELECT component_type, COUNT(*) AS n, AVG(confidence) AS avg_confidence
FROM component_registry
GROUP BY component_type
ORDER BY n DESC;

-- 06. Visual Token Registry
SELECT token_type, COUNT(*) AS n
FROM visual_token_registry
GROUP BY token_type
ORDER BY n DESC;

-- 07. Schema Intelligence
SELECT schema_role, suggested_template, COUNT(*) AS n
FROM schema_intelligence_registry
GROUP BY schema_role, suggested_template
ORDER BY n DESC;

-- 08. Alignment Policies
SELECT market, timezone_policy, calendar_policy, COUNT(*) AS n
FROM alignment_policy_registry
GROUP BY market, timezone_policy, calendar_policy
ORDER BY n DESC;

-- 09. Auto Dashboard Composition
SELECT *
FROM auto_dashboard_registry
ORDER BY confidence DESC;
"""
    QUERY_PACK_SQL.write_text(sql.strip() + "\n", encoding="utf-8")


def def_write_launchers() -> None:
    verify = f"""#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = "{PYTHON_EXE}"
$Probe = "{Path(__file__)}"
& $Python $Probe
"""

    refresh_target = str(LATEST_V4_BUILDER) if LATEST_V4_BUILDER.exists() else ""
    refresh = f"""#Requires -Version 7.0
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Python = "{PYTHON_EXE}"
$Builder = "{refresh_target}"
$Html = "{LATEST_V4_HTML}"

if ([string]::IsNullOrWhiteSpace($Builder) -or -not (Test-Path -LiteralPath $Builder)) {{
    Write-Host "[ERR] V4 builder not found. Re-run VAP_Warehouse_V4_AllInOne.ps1." -ForegroundColor Red
    return
}}

Write-Host ""
Write-Host "Refreshing VAP Warehouse V4..." -ForegroundColor Cyan
$out = & $Python $Builder 2>&1
Write-Host ($out | Out-String)
if (Test-Path -LiteralPath $Html) {{
    Start-Process $Html
    Write-Host "[OK] HTML = $Html" -ForegroundColor Green
}}
"""
    VERIFY_PS1.write_text(verify, encoding="utf-8-sig")
    REFRESH_PS1.write_text(refresh, encoding="utf-8-sig")


def def_write_handover(manifest: dict, tables: list[dict]) -> None:
    def esc(x):
        import html
        return html.escape(str(x))

    table_rows = "".join(
        f"<tr><td>{esc(t['table'])}</td><td>{esc(t['exists'])}</td><td>{esc(t['rows'])}</td></tr>"
        for t in tables
    )

    parquet_rows = "".join(
        f"<tr><td>{esc(p['file'])}</td><td>{esc(p['exists'])}</td><td>{esc(p['size_bytes'])}</td></tr>"
        for p in manifest.get("parquet_files", [])
    )

    features = [
        "Windows I/O intake",
        "Asset Taxonomy Engine",
        "HTML Semantic Scanner",
        "Plot DNA Registry",
        "Template Intelligence",
        "SQLite Registry",
        "DuckDB Warehouse",
        "Parquet Layer",
        "Component Extraction Registry",
        "Visual Token Registry",
        "Schema Intelligence Registry",
        "Alignment Policy Registry",
        "Auto Dashboard Composition Registry",
        "Refresh Launcher",
        "Verify Launcher",
        "Query Pack SQL",
        "HTML Handover Report",
        "Active Warning Gate v2",
    ]
    feature_html = "".join(f"<li>{esc(x)}</li>" for x in features)

    html_doc = f"""<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VAP Project Completion Handover v2</title>
<style>
:root{{--bg:#f5f4f0;--sf:#fff;--bd:#d9d5ca;--ink:#1e1d1a;--muted:#77736a;--blue:#4c78a8;--teal:#439a9a;--green:#5a9e6f;--amber:#c4943a;--coral:#c96b5a;--violet:#7a6daa}}
body{{margin:0;background:linear-gradient(135deg,#f5f4f0,#eceae4);font-family:Segoe UI,Noto Sans TC,Arial,sans-serif;color:var(--ink);font-size:12px}}
.wrap{{max-width:1680px;margin:0 auto;padding:14px}}
.hero{{background:var(--sf);border:1px solid var(--bd);border-radius:14px;overflow:hidden;box-shadow:0 12px 35px rgba(30,29,26,.08);margin-bottom:10px}}
.hero:before{{content:"";display:block;height:4px;background:linear-gradient(90deg,var(--blue),var(--teal),var(--violet),var(--amber),var(--coral))}}
.heroIn{{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px}}
h1{{font-size:20px;margin:0}}.sub{{font-family:Consolas,monospace;color:var(--muted);font-size:10px;margin-top:3px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px;margin-bottom:10px}}
.kpi{{background:#fff;border:1px solid var(--bd);border-left:4px solid var(--green);border-radius:10px;padding:10px}}
.k{{font-size:10px;color:var(--muted);font-weight:800;text-transform:uppercase}}.v{{font-family:Consolas,monospace;font-size:24px;font-weight:900}}
.card{{background:#fff;border:1px solid var(--bd);border-radius:12px;padding:12px;margin-bottom:10px}}
table{{width:100%;border-collapse:collapse;font-size:11px}}th{{background:#eceae4;border-bottom:2px solid var(--bd);padding:7px;text-align:left}}td{{border-bottom:1px solid var(--bd);padding:6px;vertical-align:top}}
code{{font-family:Consolas,monospace;font-size:10px;background:#eceae4;border:1px solid var(--bd);border-radius:5px;padding:1px 5px}}
.badge{{display:inline-block;background:#d8ecd8;color:var(--green);padding:4px 8px;border-radius:999px;font-weight:900}}
</style>
</head>
<body><div class="wrap">
<div class="hero"><div class="heroIn"><div><h1>VAP Project Completion Handover v2</h1><div class="sub">VERITAS INTELLIGENCE ANALYTICS · Visual Analytics Operating System Warehouse</div><div class="sub">Generated: {esc(manifest.get('generated_at',''))}</div></div><div class="badge">PROJECT COMPLETE</div></div></div>
<div class="grid">
<div class="kpi"><div class="k">Status</div><div class="v">{esc(manifest.get('status',''))}</div></div>
<div class="kpi"><div class="k">Assets</div><div class="v">{esc(manifest.get('assets',''))}</div></div>
<div class="kpi"><div class="k">Active Warnings</div><div class="v">{esc(manifest.get('active_warnings',''))}</div></div>
<div class="kpi"><div class="k">Components</div><div class="v">{esc(manifest.get('components',''))}</div></div>
<div class="kpi"><div class="k">Visual Tokens</div><div class="v">{esc(manifest.get('visual_tokens',''))}</div></div>
<div class="kpi"><div class="k">Dashboards</div><div class="v">{esc(manifest.get('dashboards',''))}</div></div>
</div>

<div class="card"><b>Completed Features</b><ol>{feature_html}</ol></div>
<div class="card"><b>DuckDB</b><br><code>{esc(manifest.get('duckdb_path',''))}</code></div>
<div class="card"><b>Latest V4 Report</b><br><code>{esc(manifest.get('latest_v4_html',''))}</code></div>
<div class="card"><b>Query Pack</b><br><code>{esc(manifest.get('query_pack_sql',''))}</code></div>
<div class="card"><b>Verification Launcher</b><br><code>{esc(manifest.get('verify_ps1',''))}</code></div>
<div class="card"><b>Refresh Launcher</b><br><code>{esc(manifest.get('refresh_ps1',''))}</code></div>

<div class="card"><b>DuckDB Tables</b><table><thead><tr><th>Table</th><th>Exists</th><th>Rows</th></tr></thead><tbody>{table_rows}</tbody></table></div>
<div class="card"><b>Parquet Files</b><table><thead><tr><th>File</th><th>Exists</th><th>Size</th></tr></thead><tbody>{parquet_rows}</tbody></table></div>
</div></body></html>"""
    HANDOVER_HTML.write_text(html_doc, encoding="utf-8")


def main() -> int:
    v4_summary = def_read_json(V4_SUMMARY, {})
    required_tables = [
        "asset_registry_v4",
        "component_registry",
        "visual_token_registry",
        "schema_intelligence_registry",
        "alignment_policy_registry",
        "auto_dashboard_registry",
        "warning_assets_v4",
        "plot_dna_registry",
    ]

    required_parquet = [
        "asset_registry_v4.parquet",
        "component_registry.parquet",
        "visual_token_registry.parquet",
        "schema_intelligence_registry.parquet",
        "alignment_policy_registry.parquet",
        "auto_dashboard_registry.parquet",
        "warning_assets_v4.parquet",
        "plot_dna_registry.parquet",
    ]

    tables = []
    status = "COMPLETE"
    active_warnings = -1

    if not DUCKDB_PATH.exists():
        status = "DUCKDB_MISSING"
        con = None
    else:
        con = duckdb.connect(str(DUCKDB_PATH), read_only=True)

    for t in required_tables:
        exists = False
        rows = -1
        if con is not None:
            exists = def_table_exists(con, t)
            rows = def_table_count(con, t) if exists else -1
        if not exists:
            status = "INCOMPLETE"
        tables.append({"table": t, "exists": exists, "rows": rows})

    if con is not None:
        active_warnings = def_active_warning_count(con)
        con.close()

    parquet_files = []
    for fname in required_parquet:
        p = PARQUET_ROOT / fname
        exists = p.exists()
        if not exists:
            status = "INCOMPLETE"
        parquet_files.append({"file": str(p), "exists": exists, "size_bytes": p.stat().st_size if exists else 0})

    if status == "COMPLETE":
        if active_warnings is None or active_warnings < 0:
            status = "WARNING_GATE_UNKNOWN"
        elif active_warnings > 0:
            status = "WARNINGS_PRESENT"

    table_map = {x["table"]: x["rows"] for x in tables}

    manifest = {
        "generated_at": def_now(),
        "status": status,
        "duckdb_path": str(DUCKDB_PATH),
        "parquet_root": str(PARQUET_ROOT),
        "latest_v4_summary": str(V4_SUMMARY),
        "latest_v4_html": str(LATEST_V4_HTML),
        "latest_v4_builder": str(LATEST_V4_BUILDER),
        "completion_root": str(MANIFEST_JSON.parent),
        "manifest_json": str(MANIFEST_JSON),
        "query_pack_sql": str(QUERY_PACK_SQL),
        "handover_html": str(HANDOVER_HTML),
        "verify_ps1": str(VERIFY_PS1),
        "refresh_ps1": str(REFRESH_PS1),
        "assets": int(v4_summary.get("assets", table_map.get("asset_registry_v4", 0))),
        "warnings": int(v4_summary.get("warnings", 0)),
        "active_warnings": int(active_warnings if active_warnings >= 0 else -1),
        "components": int(v4_summary.get("components", table_map.get("component_registry", 0))),
        "visual_tokens": int(v4_summary.get("visual_tokens", table_map.get("visual_token_registry", 0))),
        "schemas": int(v4_summary.get("schemas", table_map.get("schema_intelligence_registry", 0))),
        "alignment_policies": int(v4_summary.get("alignment_policies", table_map.get("alignment_policy_registry", 0))),
        "dashboards": int(v4_summary.get("dashboards", table_map.get("auto_dashboard_registry", 0))),
        "tables": tables,
        "parquet_files": parquet_files,
    }

    def_write_query_pack()
    def_write_launchers()
    def_write_handover(manifest, tables)
    MANIFEST_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(tables).to_csv(COMPLETION_CSV, index=False, encoding="utf-8-sig")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0 if status == "COMPLETE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
