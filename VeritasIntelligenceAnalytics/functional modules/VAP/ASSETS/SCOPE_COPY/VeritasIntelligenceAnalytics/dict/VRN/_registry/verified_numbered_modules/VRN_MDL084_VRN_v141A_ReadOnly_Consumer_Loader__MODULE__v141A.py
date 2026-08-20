VIA_ROOT = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics"
VRN_ROOT = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN"
VDF_ROOT = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VeritasDataForge"
RUNS_ROOT = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs"
RUN_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_220104_VRN_V141A_READONLY_CONSUMER_LOADER"

MASTER_RELEASE_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_dashboard_release_index\VRN_Master_Dashboard_Release_Index.json"
MASTER_RELEASE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_dashboard_release_index\VRN_Master_Dashboard_Release_Index.csv"
SIDECAR_INDEX_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\registry_sidecar\VIA_RegistrySidecar_Dataset_Index.json"
PROD_DUCKDB = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VeritasDataForge\data\via.duckdb"

BASICINFO_ASSET_ID = r"VRN_DATASET_BASICINFO_CONSENSUS_V140G"
FINANCIAL_ASSET_ID = r"VDF_DATASET_VRN_FINANCIAL_ACTUAL_CANONICAL"
BASICINFO_TABLE = r"vrn_basicinfo_consensus"
FINANCIAL_TABLE = r"vrn_financial_actual_canonical"

EXPECTED_BASIC_ROWS = 1861
EXPECTED_BASIC_COLUMNS = 129
EXPECTED_FINANCIAL_ROWS = 27
EXPECTED_FINANCIAL_COLUMNS = 20
EXPECTED_JOIN_ROWS = 27

OUT_HTML = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_220104_VRN_V141A_READONLY_CONSUMER_LOADER\VRN_v141A_ReadOnly_Consumer_Loader.html"
OUT_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_220104_VRN_V141A_READONLY_CONSUMER_LOADER\VRN_v141A_ReadOnly_Consumer_Loader.json"
OUT_MATRIX_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_220104_VRN_V141A_READONLY_CONSUMER_LOADER\VRN_v141A_ReadOnly_Consumer_Loader_Matrix.csv"
OUT_CONSUMER_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_220104_VRN_V141A_READONLY_CONSUMER_LOADER\VRN_v141A_Consumer_Loader_Routes.csv"
OUT_SAMPLE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_220104_VRN_V141A_READONLY_CONSUMER_LOADER\VRN_v141A_Consumer_Loader_Sample.csv"
OUT_SCHEMA_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_220104_VRN_V141A_READONLY_CONSUMER_LOADER\VRN_v141A_Consumer_Loader_Schema.csv"
OUT_REGISTRY = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output\_route_lock_runs\RUN_20260526_220104_VRN_V141A_READONLY_CONSUMER_LOADER\VRN_v141A_READONLY_CONSUMER_LOADER_REGISTRY.txt"

DB_WRITE_ENABLE = False
SSOT_CORE_MUTATION_ENABLE = False
SIDECAR_MUTATION_ENABLE = False
NETWORK_ENABLE = False
SOURCE_PATCH_ENABLE = False

import csv
import hashlib
import html
import json
import traceback
from pathlib import Path
from datetime import datetime

def def_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def def_html_escape(x):
    return html.escape(str(x))

def def_sha256(path):
    p = Path(path)
    if not p.exists() or not p.is_file():
        return ""
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def def_sql_ident(x):
    return '"' + str(x).replace('"', '""') + '"'

def def_read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))

def def_write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8-sig")

def def_write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        Path(path).write_text("", encoding="utf-8-sig")
        return
    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def def_add_matrix(rows, page, gate, value, expected, passed, severity, message):
    rows.append({
        "Time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "Page": str(page),
        "Gate": str(gate),
        "Value": str(value),
        "Expected": str(expected),
        "Pass": bool(passed),
        "Severity": str(severity),
        "Message": str(message),
    })

def def_find_asset(datasets, asset_id):
    for d in datasets:
        if d.get("asset_id") == asset_id:
            return d
    return None

def def_table_exists(con, table_name):
    return con.execute(
        "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = ?",
        [table_name]
    ).fetchone()[0] > 0

def def_table_stats(con, table_name):
    if not def_table_exists(con, table_name):
        return {
            "table_name": table_name,
            "exists": False,
            "rows": 0,
            "columns": 0,
            "schema": [],
        }

    rows = con.execute(f"SELECT COUNT(*) FROM {def_sql_ident(table_name)}").fetchone()[0]
    columns = con.execute(
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name = ?",
        [table_name]
    ).fetchone()[0]

    schema_raw = con.execute(
        "SELECT ordinal_position, column_name, data_type FROM information_schema.columns WHERE table_name = ? ORDER BY ordinal_position",
        [table_name]
    ).fetchall()

    schema = [
        {
            "Table": table_name,
            "Ordinal": r[0],
            "ColumnName": r[1],
            "DataType": r[2],
        }
        for r in schema_raw
    ]

    return {
        "table_name": table_name,
        "exists": True,
        "rows": rows,
        "columns": columns,
        "schema": schema,
    }

def def_build_join_sample(con):
    sample_rows = []
    join_count = 0
    try:
        q_count = f"""
            SELECT COUNT(*)
            FROM {def_sql_ident(BASICINFO_TABLE)} b
            INNER JOIN {def_sql_ident(FINANCIAL_TABLE)} f
                ON CAST(b.ticker AS VARCHAR) = CAST(f.ticker AS VARCHAR)
        """
        join_count = con.execute(q_count).fetchone()[0]

        q_sample = f"""
            SELECT
                b.ticker,
                b.name,
                b.tw_yfinance_ticker,
                f.statement,
                f.period_year,
                f.account_key,
                f.account_canonical,
                f.value_mn_twd,
                f.source_file
            FROM {def_sql_ident(BASICINFO_TABLE)} b
            INNER JOIN {def_sql_ident(FINANCIAL_TABLE)} f
                ON CAST(b.ticker AS VARCHAR) = CAST(f.ticker AS VARCHAR)
            LIMIT 50
        """
        df = con.execute(q_sample).fetchdf()
        sample_rows = df.astype(str).to_dict("records")
    except Exception as e:
        sample_rows = [{"error": str(e)}]
    return join_count, sample_rows

def def_table(rows, title, max_rows=1000):
    if not rows:
        return f"<section class='card'><h2>{title}</h2><p>EMPTY</p></section>"
    keys = []
    for r in rows[:max_rows]:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    th = "".join(f"<th>{def_html_escape(str(k).replace('_',' '))}</th>" for k in keys)
    body = ""
    for r in rows[:max_rows]:
        body += "<tr>"
        for k in keys:
            v = r.get(k, "")
            kind = "long" if len(str(v)) > 36 or "\\" in str(v) or "/" in str(v) else "short"
            body += f"<td data-cell-kind='{kind}'>{def_html_escape(v)}</td>"
        body += "</tr>"
    return f"<section class='card'><h2>{title}</h2><div class='scroll'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div></section>"

def def_write_html(matrix, consumer_routes, sample_rows, schema_rows, meta):
    meta_json = def_html_escape(json.dumps(meta, ensure_ascii=False, indent=2))
    html_doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN v141A ReadOnly Consumer Loader</title>
<style>
:root{{--bg:#f6f5f1;--card:#fff;--border:#d8d4ca;--soft:#ece8df;--head:#e8e4da;--text:#141414;--muted:#5f5b54;--ok:#247a4d;--warn:#a86613;--err:#a73535}}
*{{box-sizing:border-box}}
html{{font-size:10px}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:"Segoe UI","Microsoft JhengHei",Arial,sans-serif;font-size:8.7px;line-height:1.12}}
header{{position:relative;padding:13px 20px 9px;background:#fff;border-bottom:1px solid var(--border)}}
header:before{{content:"";position:absolute;left:20px;right:20px;top:0;height:3px;background:linear-gradient(90deg,#e74c3c,#f39c12,#f1c40f,#2ecc71,#3498db,#9b59b6)}}
h1{{margin:0;font-size:20px;line-height:1.02;font-weight:850;letter-spacing:-.04em}}
h2{{margin:0 0 5px;font-size:10.5px;line-height:1.08;font-weight:850}}
.sub{{margin-top:4px;color:var(--muted);font-family:Consolas,"Cascadia Mono",monospace;font-size:8.4px}}
main{{padding:8px 12px 16px}}
.grid{{display:grid;grid-template-columns:repeat(8,minmax(62px,1fr));gap:5px;margin-bottom:7px}}
.kpi{{background:#fff;border:1px solid var(--border);border-radius:7px;padding:5px 6px;min-height:38px}}
.v{{font-size:13px;line-height:1.02;font-weight:850;text-align:center}}
.k{{color:var(--muted);font-size:8px;line-height:1.05;margin-top:2px;text-align:center}}
.ok{{color:var(--ok);font-weight:850}}.warn{{color:var(--warn);font-weight:850}}.err{{color:var(--err);font-weight:850}}
.card{{background:#fff;border:1px solid var(--border);border-radius:7px;padding:7px;margin-top:7px;box-shadow:0 1px 7px rgba(0,0,0,.028)}}
.scroll{{overflow:auto;max-height:78vh;border:1px solid var(--border);border-radius:6px;background:#fff}}
table{{border-collapse:collapse;table-layout:fixed;width:100%;min-width:1180px;font-size:8.45px;line-height:1.1}}
th{{position:sticky;top:0;z-index:3;background:var(--head);font-weight:850;text-align:center;vertical-align:top;padding:2px 4px;border-bottom:1px solid var(--border);border-right:1px solid var(--soft);white-space:normal;overflow-wrap:anywhere}}
td{{padding:2px 4px;border-bottom:1px solid var(--soft);border-right:1px solid var(--soft);vertical-align:top;text-align:center;white-space:normal;overflow-wrap:anywhere;height:auto}}
td[data-cell-kind="long"]{{text-align:left;word-break:break-word}}
pre{{font-family:Consolas,"Cascadia Mono",monospace;background:#f8fafc;border:1px solid #e2e8f0;border-radius:6px;padding:6px;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;font-size:8.4px;max-height:42vh;overflow:auto}}
</style>
</head>
<body>
<header>
<h1>VeritasReportNova v1.0.41A</h1>
<div class="sub">VERITAS INTELLIGENCE ANALYTICS</div>
<div class="sub">ReadOnly Consumer Loader · Master Release Index / Sidecar / DuckDB / Join Route</div>
</header>
<main>
<div class="grid">
<div class="kpi"><div class="v {'ok' if meta.get('system_pass') else 'err'}">{meta.get('system_pass')}</div><div class="k">System Pass</div></div>
<div class="kpi"><div class="v">{meta.get('consumer_ready_count')}</div><div class="k">Consumers</div></div>
<div class="kpi"><div class="v">{meta.get('basic_rows')}</div><div class="k">Basic Rows</div></div>
<div class="kpi"><div class="v">{meta.get('financial_rows')}</div><div class="k">Fin Rows</div></div>
<div class="kpi"><div class="v">{meta.get('join_rows')}</div><div class="k">Join Rows</div></div>
<div class="kpi"><div class="v">{meta.get('fail_count')}</div><div class="k">Fail</div></div>
<div class="kpi"><div class="v">{meta.get('db_write')}</div><div class="k">DB Write</div></div>
<div class="kpi"><div class="v">{meta.get('elapsed_sec')}</div><div class="k">Elapsed</div></div>
</div>
<section class="card"><h2>Meta</h2><pre>{meta_json}</pre></section>
{def_table(matrix, "Loader Matrix")}
{def_table(consumer_routes, "Consumer Routes")}
{def_table(sample_rows, "Join Sample")}
{def_table(schema_rows, "Schema")}
</main>
</body>
</html>"""
    Path(OUT_HTML).write_text(html_doc, encoding="utf-8-sig")

def def_main():
    t0 = datetime.now()
    Path(RUN_DIR).mkdir(parents=True, exist_ok=True)

    matrix = []
    consumer_routes = []
    schema_rows = []
    sample_rows = []

    def_add_matrix(matrix, "Safety", "DB_WRITE", DB_WRITE_ENABLE, False, DB_WRITE_ENABLE is False, "OK", "No DB write")
    def_add_matrix(matrix, "Safety", "SSOT_CORE_MUTATION", SSOT_CORE_MUTATION_ENABLE, False, SSOT_CORE_MUTATION_ENABLE is False, "OK", "No SSOT mutation")
    def_add_matrix(matrix, "Safety", "SIDECAR_MUTATION", SIDECAR_MUTATION_ENABLE, False, SIDECAR_MUTATION_ENABLE is False, "OK", "No sidecar mutation")
    def_add_matrix(matrix, "Safety", "NETWORK", NETWORK_ENABLE, False, NETWORK_ENABLE is False, "OK", "No network")
    def_add_matrix(matrix, "Safety", "SOURCE_PATCH", SOURCE_PATCH_ENABLE, False, SOURCE_PATCH_ENABLE is False, "OK", "No source patch")

    master_exists = Path(MASTER_RELEASE_JSON).exists()
    sidecar_exists = Path(SIDECAR_INDEX_JSON).exists()
    duckdb_exists = Path(PROD_DUCKDB).exists()

    def_add_matrix(matrix, "Input", "MasterReleaseJson", MASTER_RELEASE_JSON, "exists", master_exists, "OK" if master_exists else "ERR", "Master release index")
    def_add_matrix(matrix, "Input", "SidecarIndexJson", SIDECAR_INDEX_JSON, "exists", sidecar_exists, "OK" if sidecar_exists else "ERR", "Sidecar dataset index")
    def_add_matrix(matrix, "Input", "DuckDB", PROD_DUCKDB, "exists", duckdb_exists, "OK" if duckdb_exists else "ERR", "Production DuckDB")

    master = def_read_json(MASTER_RELEASE_JSON) if master_exists else {}
    sidecar = def_read_json(SIDECAR_INDEX_JSON) if sidecar_exists else {"datasets": []}
    datasets = sidecar.get("datasets", [])

    basic_asset = def_find_asset(datasets, BASICINFO_ASSET_ID)
    financial_asset = def_find_asset(datasets, FINANCIAL_ASSET_ID)

    basic_asset_ok = bool(basic_asset and basic_asset.get("table_name") == BASICINFO_TABLE)
    financial_asset_ok = bool(financial_asset and financial_asset.get("table_name") == FINANCIAL_TABLE)

    def_add_matrix(matrix, "Sidecar", "BasicInfoAsset", basic_asset_ok, True, basic_asset_ok, "OK" if basic_asset_ok else "ERR", BASICINFO_ASSET_ID)
    def_add_matrix(matrix, "Sidecar", "FinancialAsset", financial_asset_ok, True, financial_asset_ok, "OK" if financial_asset_ok else "ERR", FINANCIAL_ASSET_ID)

    import duckdb
    con = duckdb.connect(database=PROD_DUCKDB, read_only=True)

    basic_stats = def_table_stats(con, BASICINFO_TABLE)
    financial_stats = def_table_stats(con, FINANCIAL_TABLE)
    join_rows, sample_rows = def_build_join_sample(con)

    con.close()

    schema_rows.extend(basic_stats["schema"])
    schema_rows.extend(financial_stats["schema"])

    basic_ok = basic_stats["exists"] and basic_stats["rows"] == EXPECTED_BASIC_ROWS and basic_stats["columns"] == EXPECTED_BASIC_COLUMNS
    financial_ok = financial_stats["exists"] and financial_stats["rows"] == EXPECTED_FINANCIAL_ROWS and financial_stats["columns"] == EXPECTED_FINANCIAL_COLUMNS
    join_ok = join_rows >= EXPECTED_JOIN_ROWS

    def_add_matrix(matrix, "DuckDB", "BasicInfoTable", f"rows={basic_stats['rows']}; cols={basic_stats['columns']}", f"rows={EXPECTED_BASIC_ROWS}; cols={EXPECTED_BASIC_COLUMNS}", basic_ok, "OK" if basic_ok else "ERR", BASICINFO_TABLE)
    def_add_matrix(matrix, "DuckDB", "FinancialTable", f"rows={financial_stats['rows']}; cols={financial_stats['columns']}", f"rows={EXPECTED_FINANCIAL_ROWS}; cols={EXPECTED_FINANCIAL_COLUMNS}", financial_ok, "OK" if financial_ok else "ERR", FINANCIAL_TABLE)
    def_add_matrix(matrix, "DuckDB", "JoinRoute", join_rows, f">={EXPECTED_JOIN_ROWS}", join_ok, "OK" if join_ok else "ERR", "ticker join")

    freeze_index = master.get("freeze_index", "")
    freeze_ok = bool(freeze_index and Path(freeze_index).exists())
    def_add_matrix(matrix, "Release", "FreezeIndex", freeze_index, "exists", freeze_ok, "OK" if freeze_ok else "ERR", "Dashboard release index")

    consumer_routes = [
        {
            "Consumer": "Dashboard.ReleaseIndex",
            "InputType": "HTML",
            "Input": freeze_index,
            "Ready": freeze_ok,
            "Rows": "",
            "Columns": "",
            "ReadOnly": True,
        },
        {
            "Consumer": "VDF.BasicInfo.Table",
            "InputType": "DuckDB",
            "Input": f"{PROD_DUCKDB}::{BASICINFO_TABLE}",
            "Ready": basic_ok,
            "Rows": basic_stats["rows"],
            "Columns": basic_stats["columns"],
            "ReadOnly": True,
        },
        {
            "Consumer": "VDF.FinancialData.Table",
            "InputType": "DuckDB",
            "Input": f"{PROD_DUCKDB}::{FINANCIAL_TABLE}",
            "Ready": financial_ok,
            "Rows": financial_stats["rows"],
            "Columns": financial_stats["columns"],
            "ReadOnly": True,
        },
        {
            "Consumer": "VRN.BasicInfoFinancialJoin",
            "InputType": "DuckDBJoin",
            "Input": f"{BASICINFO_TABLE}.ticker = {FINANCIAL_TABLE}.ticker",
            "Ready": join_ok,
            "Rows": join_rows,
            "Columns": "",
            "ReadOnly": True,
        },
        {
            "Consumer": "Sidecar.DatasetIndex",
            "InputType": "JSON",
            "Input": SIDECAR_INDEX_JSON,
            "Ready": basic_asset_ok and financial_asset_ok,
            "Rows": len(datasets),
            "Columns": "",
            "ReadOnly": True,
        },
    ]

    def_write_csv(OUT_CONSUMER_CSV, consumer_routes)
    def_write_csv(OUT_SAMPLE_CSV, sample_rows)
    def_write_csv(OUT_SCHEMA_CSV, schema_rows)
    def_write_csv(OUT_MATRIX_CSV, matrix)

    fail_count = sum(1 for r in matrix if (not r["Pass"]) and r["Severity"] == "ERR")
    warn_count = sum(1 for r in matrix if (not r["Pass"]) and r["Severity"] == "WARN")
    consumer_ready_count = sum(1 for r in consumer_routes if r["Ready"])
    system_pass = fail_count == 0 and consumer_ready_count == len(consumer_routes)

    elapsed = round((datetime.now() - t0).total_seconds(), 2)

    meta = {
        "version": "VRN_V141A_READONLY_CONSUMER_LOADER",
        "generated_at": def_now(),
        "system_pass": system_pass,
        "master_release_json": MASTER_RELEASE_JSON,
        "sidecar_index_json": SIDECAR_INDEX_JSON,
        "production_duckdb": PROD_DUCKDB,
        "freeze_index": freeze_index,
        "consumer_ready_count": consumer_ready_count,
        "consumer_total": len(consumer_routes),
        "basic_rows": basic_stats["rows"],
        "basic_columns": basic_stats["columns"],
        "financial_rows": financial_stats["rows"],
        "financial_columns": financial_stats["columns"],
        "join_rows": join_rows,
        "sample_rows": len(sample_rows),
        "schema_rows": len(schema_rows),
        "fail_count": fail_count,
        "warn_count": warn_count,
        "consumer_csv": OUT_CONSUMER_CSV,
        "sample_csv": OUT_SAMPLE_CSV,
        "schema_csv": OUT_SCHEMA_CSV,
        "html": OUT_HTML,
        "json": OUT_JSON,
        "matrix_csv": OUT_MATRIX_CSV,
        "registry": OUT_REGISTRY,
        "db_write": DB_WRITE_ENABLE,
        "ssot_core_mutation": SSOT_CORE_MUTATION_ENABLE,
        "sidecar_mutation": SIDECAR_MUTATION_ENABLE,
        "network": NETWORK_ENABLE,
        "source_patch": SOURCE_PATCH_ENABLE,
        "elapsed_sec": elapsed,
    }

    def_write_json(OUT_JSON, {
        "meta": meta,
        "matrix": matrix,
        "consumer_routes": consumer_routes,
        "sample_rows": sample_rows,
        "schema": schema_rows,
    })

    registry = ["VRN_V141A_READONLY_CONSUMER_LOADER_REGISTRY"]
    for k, v in meta.items():
        registry.append(f"{k}={v}")
    registry += [
        "db_write=NO",
        "ssot_core_mutation=NO",
        "sidecar_mutation=NO",
        "network=NO",
        "source_patch=NO",
        "next=v141B_dashboard_landing_page_index",
    ]
    Path(OUT_REGISTRY).write_text("\n".join(registry), encoding="utf-8-sig")

    def_write_html(matrix, consumer_routes, sample_rows, schema_rows, meta)
    print(json.dumps(meta, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        def_main()
    except BaseException:
        fatal = {
            "version": "VRN_V141A_READONLY_CONSUMER_LOADER",
            "system_pass": False,
            "fatal": traceback.format_exc(),
            "run_dir": RUN_DIR,
        }
        Path(OUT_JSON).write_text(json.dumps(fatal, ensure_ascii=False, indent=2), encoding="utf-8-sig")
        print(json.dumps(fatal, ensure_ascii=False, indent=2))
        raise
