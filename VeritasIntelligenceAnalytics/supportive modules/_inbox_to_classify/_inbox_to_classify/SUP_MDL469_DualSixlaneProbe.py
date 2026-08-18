import os, sys, json, glob
from datetime import datetime

project_root = sys.argv[1]
vrn_db_root = sys.argv[2]
vdf_db_root = sys.argv[3]
out_json = sys.argv[4]

def now(): return datetime.now().isoformat()

def file_info(path):
    if not path or not os.path.exists(path):
        return {"exists": False, "path": path, "rows": 0, "size": 0}
    d = {"exists": True, "path": path, "rows": 0, "size": os.path.getsize(path)}
    try:
        import pyarrow.parquet as pq
        d["rows"] = pq.ParquetFile(path).metadata.num_rows
    except Exception as e:
        d["error"] = str(e)
    return d

def latest(pattern):
    files = glob.glob(pattern, recursive=True)
    files = [f for f in files if os.path.isfile(f)]
    if not files:
        return ""
    return max(files, key=os.path.getmtime)

def count_files(pattern):
    return len([f for f in glob.glob(pattern, recursive=True) if os.path.isfile(f)])

basic = os.path.join(vrn_db_root, "StockReportBasicInfo.parquet")
financial = os.path.join(vrn_db_root, "StockReportFinancialData.parquet")
duckdb_path = os.path.join(vrn_db_root, "VRN_StockReport.duckdb")

duck = {"exists": os.path.exists(duckdb_path), "path": duckdb_path, "basic_count": 0, "financial_count": 0, "status": "MISSING"}
if os.path.exists(duckdb_path):
    try:
        import duckdb
        con = duckdb.connect(duckdb_path)
        duck["basic_count"] = con.execute("SELECT COUNT(*) FROM StockReportBasicInfo").fetchone()[0]
        duck["financial_count"] = con.execute("SELECT COUNT(*) FROM StockReportFinancialData").fetchone()[0]
        con.close()
        duck["status"] = "READY"
    except Exception as e:
        duck["status"] = "ERROR"
        duck["error"] = str(e)

payload = {
    "generated_at": now(),
    "vrn": {
        "basic": file_info(basic),
        "financial": file_info(financial),
        "duckdb": duck,
        "latest_financial_1d_runtime": latest(os.path.join(project_root, "**", "VRN_FinancialDataStagingExtractionStore_Runtime_v029VRN1D.json")),
        "active_pointer": os.path.join(project_root, "dict", "VRN", "SSOT", "VRN_ACTIVE_STAGE_POINTER.json")
    },
    "vdf": {
        "parquet_count": count_files(os.path.join(project_root, "dict", "VDF", "**", "*.parquet")),
        "duckdb_count": count_files(os.path.join(project_root, "dict", "VDF", "**", "*.duckdb")),
        "db_count": count_files(os.path.join(project_root, "dict", "VDF", "**", "*.db")),
        "sqlite_count": count_files(os.path.join(project_root, "dict", "VDF", "**", "*.sqlite")),
        "latest_final_seal": latest(os.path.join(project_root, "**", "VIA_FinalOperationsSeal_Runtime_v02876.json")),
        "latest_daily_health": latest(os.path.join(project_root, "**", "VIA_DailyHealthNonThrowingMonitor_Runtime_v028754.json")),
        "latest_vdf_runtime_any": latest(os.path.join(project_root, "**", "*VDF*Runtime*.json")),
        "latest_veritasdataforge_runtime_any": latest(os.path.join(project_root, "**", "*VeritasDataForge*Runtime*.json")),
        "latest_dual_runtime": latest(os.path.join(project_root, "**", "*Dual*Runtime*.json"))
    }
}

with open(out_json, "w", encoding="utf-8") as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

print(json.dumps(payload, ensure_ascii=False))