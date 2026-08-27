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
import csv, json, os, re, sys, traceback
from pathlib import Path

registry_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_ssot\\VDF_DataScope_HeaderRegistry_SSOT.json")
db_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
result_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_ACTIVE_READER_USERTEST_v014_20260609_215513\\runtime\\vdf_build_database_skeleton_result_v014.json")

result = {
    "status": "PENDING",
    "risk": "PENDING",
    "database_root": str(db_dir),
    "pyarrow_available": False,
    "pandas_available": False,
    "duckdb_available": False,
    "outputs": [],
    "errors": []
}

try:
    db_dir.mkdir(parents=True, exist_ok=True)

    with registry_path.open("r", encoding="utf-8") as f:
        registry = json.load(f)

    tables = registry.get("tables", [])
    if not tables:
        raise RuntimeError("No tables found in header registry.")

    pd = None
    pa = None
    pq = None
    duckdb = None

    try:
        import pandas as pd
        result["pandas_available"] = True
    except Exception as e:
        result["errors"].append({"stage": "import_pandas", "message": str(e)})

    try:
        import pyarrow as pa
        import pyarrow.parquet as pq
        result["pyarrow_available"] = True
    except Exception as e:
        result["errors"].append({"stage": "import_pyarrow", "message": str(e)})

    try:
        import duckdb
        result["duckdb_available"] = True
    except Exception as e:
        result["errors"].append({"stage": "import_duckdb", "message": str(e)})

    duckdb_path = db_dir / "VDF_ACTIVE_SCHEMA.duckdb"

    con = None
    if duckdb is not None:
        con = duckdb.connect(str(duckdb_path))

    for t in tables:
        table_id = str(t.get("TableId", "")).strip()
        headers_text = str(t.get("Headers", "")).strip()
        if not table_id or not headers_text:
            result["outputs"].append({
                "table_id": table_id,
                "status": "FAIL",
                "message": "Missing TableId or Headers."
            })
            continue

        safe_table = re.sub(r"[^0-9A-Za-z_]+", "_", table_id)
        headers = [h.strip() for h in headers_text.split(",") if h.strip()]
        headers = list(dict.fromkeys(headers))

        csv_path = db_dir / f"{safe_table}.csv"
        json_path = db_dir / f"{safe_table}.json"
        parquet_path = db_dir / f"{safe_table}.parquet"

        row_result = {
            "table_id": safe_table,
            "headers": headers,
            "csv": str(csv_path),
            "json": str(json_path),
            "parquet": str(parquet_path),
            "duckdb": str(duckdb_path),
            "csv_status": "PENDING",
            "json_status": "PENDING",
            "parquet_status": "SKIPPED",
            "duckdb_status": "SKIPPED",
            "status": "PENDING",
            "message": ""
        }

        try:
            with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
            row_result["csv_status"] = "OK"
        except Exception as e:
            row_result["csv_status"] = "FAIL"
            row_result["message"] += f"CSV fail: {e}; "

        try:
            with json_path.open("w", encoding="utf-8") as f:
                json.dump({
                    "table_id": safe_table,
                    "headers": headers,
                    "rows": [],
                    "status": "SCHEMA_ONLY_EMPTY"
                }, f, ensure_ascii=False, indent=2)
            row_result["json_status"] = "OK"
        except Exception as e:
            row_result["json_status"] = "FAIL"
            row_result["message"] += f"JSON fail: {e}; "

        if pd is not None and pa is not None and pq is not None:
            try:
                df = pd.DataFrame(columns=headers)
                df.to_parquet(parquet_path, engine="pyarrow", index=False)
                row_result["parquet_status"] = "OK"
            except Exception as e:
                row_result["parquet_status"] = "FAIL"
                row_result["message"] += f"Parquet fail: {e}; "

        if con is not None:
            try:
                col_defs = ", ".join([f'"{h}" VARCHAR' for h in headers])
                con.execute(f'CREATE OR REPLACE TABLE "{safe_table}" ({col_defs});')
                row_result["duckdb_status"] = "OK"
            except Exception as e:
                row_result["duckdb_status"] = "FAIL"
                row_result["message"] += f"DuckDB fail: {e}; "

        hard_fails = [row_result["csv_status"], row_result["json_status"]]
        if "FAIL" in hard_fails:
            row_result["status"] = "FAIL"
        elif row_result["parquet_status"] == "FAIL" or row_result["duckdb_status"] == "FAIL":
            row_result["status"] = "WARN"
        else:
            row_result["status"] = "OK"

        result["outputs"].append(row_result)

    if con is not None:
        con.close()

    fail_count = sum(1 for x in result["outputs"] if x.get("status") == "FAIL")
    warn_count = sum(1 for x in result["outputs"] if x.get("status") == "WARN")

    if fail_count:
        result["status"] = "VDF_DATABASE_SKELETON_WITH_REVIEW"
        result["risk"] = "HIGH"
    elif warn_count:
        result["status"] = "VDF_DATABASE_SKELETON_WITH_WARNINGS"
        result["risk"] = "MEDIUM"
    else:
        result["status"] = "VDF_DATABASE_SKELETON_READY"
        result["risk"] = "LOW"

except Exception as e:
    result["status"] = "VDF_DATABASE_SKELETON_FATAL"
    result["risk"] = "HIGH"
    result["errors"].append({
        "stage": "fatal",
        "message": str(e),
        "traceback": traceback.format_exc()
    })

result_path.parent.mkdir(parents=True, exist_ok=True)
with result_path.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "outputs": len(result.get("outputs", [])),
    "pyarrow_available": result.get("pyarrow_available"),
    "duckdb_available": result.get("duckdb_available")
}, ensure_ascii=False))
