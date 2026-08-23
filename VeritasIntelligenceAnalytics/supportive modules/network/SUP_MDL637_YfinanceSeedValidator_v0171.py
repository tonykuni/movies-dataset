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
import csv, json, traceback
from pathlib import Path

db_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
result_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_YFINANCE_SEED_FINAL_SEAL_v0171_20260609_222206\\runtime\\vdf_yfinance_seed_validator_result_v0171.json")
targets = ["VDF_TW_PriceDaily","VDF_TW_IndexDaily","VDF_Global_FXRate","VDF_Global_Commodity","VDF_Global_Macro"]

result = {
    "status": "PENDING",
    "risk": "PENDING",
    "targets": [],
    "duckdb_available": False,
    "pyarrow_available": False,
    "errors": []
}

pd = None
duckdb = None
pyarrow = None

try:
    import pandas as pd
except Exception as e:
    result["errors"].append({"stage":"import_pandas","message":str(e)})

try:
    import duckdb
    result["duckdb_available"] = True
except Exception as e:
    result["errors"].append({"stage":"import_duckdb","message":str(e)})

try:
    import pyarrow
    result["pyarrow_available"] = True
except Exception as e:
    result["errors"].append({"stage":"import_pyarrow","message":str(e)})

try:
    duckdb_path = db_dir / "VDF_ACTIVE_SCHEMA.duckdb"
    con = None
    if duckdb is not None and duckdb_path.exists():
        con = duckdb.connect(str(duckdb_path), read_only=True)

    for table in targets:
        row = {
            "table_id": table,
            "csv_exists": False,
            "json_exists": False,
            "parquet_exists": False,
            "duckdb_table_exists": False,
            "csv_rows": 0,
            "json_rows": 0,
            "parquet_rows": 0,
            "duckdb_rows": 0,
            "status": "PENDING",
            "risk": "PENDING",
            "message": ""
        }

        csv_path = db_dir / f"{table}.csv"
        json_path = db_dir / f"{table}.json"
        parquet_path = db_dir / f"{table}.parquet"

        try:
            row["csv_exists"] = csv_path.exists()
            row["json_exists"] = json_path.exists()
            row["parquet_exists"] = parquet_path.exists()

            if row["csv_exists"]:
                with csv_path.open("r", encoding="utf-8-sig", newline="") as f:
                    reader = csv.reader(f)
                    rows = list(reader)
                row["csv_rows"] = max(len(rows) - 1, 0)

            if row["json_exists"]:
                with json_path.open("r", encoding="utf-8") as f:
                    j = json.load(f)
                row["json_rows"] = int(j.get("row_count", len(j.get("rows", [])) if isinstance(j.get("rows", []), list) else 0))

            if pd is not None and row["parquet_exists"]:
                try:
                    df = pd.read_parquet(parquet_path)
                    row["parquet_rows"] = int(len(df))
                except Exception as e:
                    row["message"] += f"Parquet read warning: {e}; "

            if con is not None:
                try:
                    count = con.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                    row["duckdb_table_exists"] = True
                    row["duckdb_rows"] = int(count)
                except Exception as e:
                    row["message"] += f"DuckDB read warning: {e}; "

            if row["csv_rows"] > 0 and row["json_rows"] > 0 and row["parquet_rows"] > 0:
                row["status"] = "OK_SEED_ROWS_VALIDATED"
                row["risk"] = "LOW"
            elif row["csv_rows"] > 0 and row["json_rows"] > 0:
                row["status"] = "WARN_PARQUET_READ_REVIEW"
                row["risk"] = "MEDIUM"
            else:
                row["status"] = "FAIL_SEED_ROWS_MISSING"
                row["risk"] = "HIGH"

        except Exception as e:
            row["status"] = "FAIL"
            row["risk"] = "HIGH"
            row["message"] += str(e)

        result["targets"].append(row)

    if con is not None:
        con.close()

    fail = sum(1 for x in result["targets"] if x["risk"] == "HIGH")
    warn = sum(1 for x in result["targets"] if x["risk"] == "MEDIUM")

    if fail:
        result["status"] = "VDF_YFINANCE_SEED_FINAL_SEAL_WITH_REVIEW"
        result["risk"] = "HIGH"
    elif warn:
        result["status"] = "VDF_YFINANCE_SEED_FINAL_SEAL_WITH_WARNINGS"
        result["risk"] = "MEDIUM"
    else:
        result["status"] = "VDF_YFINANCE_SEED_FINAL_SEAL_READY"
        result["risk"] = "LOW"

except Exception as e:
    result["status"] = "VDF_YFINANCE_SEED_FINAL_SEAL_FATAL"
    result["risk"] = "HIGH"
    result["errors"].append({"stage":"fatal","message":str(e),"traceback":traceback.format_exc()})

result_path.parent.mkdir(parents=True, exist_ok=True)
with result_path.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "targets": len(result["targets"]),
    "rows": sum(int(x.get("csv_rows", 0)) for x in result["targets"])
}, ensure_ascii=False))
