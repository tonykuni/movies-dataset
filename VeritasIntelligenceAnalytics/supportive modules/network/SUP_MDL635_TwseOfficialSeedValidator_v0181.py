import json
from pathlib import Path
from datetime import datetime

db_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_TWSE_OFFICIAL_SEED_FINAL_SEAL_v0181_20260609_231824\\runtime\\vdf_twse_official_seed_validator_result_v0181.json")

targets = [
    {"table":"VDF_TW_EquityUniverse","expected":1362},
    {"table":"VDF_TW_TradingStats","expected":1078},
    {"table":"VDF_TW_IndexDaily","expected":20},
]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_TWSE_OFFICIAL_SEED_FINAL_SEAL_READY",
    "risk": "LOW",
    "targets": [],
    "total_rows": 0,
    "libs": {}
}

try:
    import pandas as pd
    result["libs"]["pandas"] = True
except Exception as e:
    result["libs"]["pandas"] = False
    result["status"] = "VDF_TWSE_OFFICIAL_SEED_FINAL_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"

try:
    import pyarrow  # noqa
    result["libs"]["pyarrow"] = True
except Exception as e:
    result["libs"]["pyarrow"] = False
    result["status"] = "VDF_TWSE_OFFICIAL_SEED_FINAL_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pyarrow missing: {e}"

try:
    import duckdb
    result["libs"]["duckdb"] = True
except Exception as e:
    result["libs"]["duckdb"] = False

if result["libs"].get("pandas") and result["libs"].get("pyarrow"):
    import pandas as pd
    for t in targets:
        p = db_dir / f'{t["table"]}.parquet'
        item = {"table": t["table"], "path": str(p), "exists": p.exists(), "rows": 0, "expected": t["expected"], "ok": False}
        if p.exists():
            df = pd.read_parquet(p)
            item["rows"] = int(len(df))
            item["columns"] = list(df.columns)
            item["ok"] = item["rows"] >= int(t["expected"])
            result["total_rows"] += item["rows"]
        result["targets"].append(item)

    if result["total_rows"] < 2460 or any(not x["ok"] for x in result["targets"]):
        result["status"] = "VDF_TWSE_OFFICIAL_SEED_FINAL_SEAL_WITH_REVIEW"
        result["risk"] = "HIGH"

duck = db_dir / "VDF_ACTIVE_SCHEMA.duckdb"
result["duckdb_path"] = str(duck)
result["duckdb_exists"] = duck.exists()

out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps({"status": result["status"], "risk": result["risk"], "rows": result["total_rows"]}, ensure_ascii=False))
