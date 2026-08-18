import json
from pathlib import Path
from datetime import datetime

db = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
backup_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_backup\\VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_EXECUTE_v0262_20260610_135958") if r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_backup\\VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_EXECUTE_v0262_20260610_135958" else Path("")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_FRED_CANONICAL_POST_MERGE_FINAL_AUDIT_SEAL_v0263_20260610_140303\\runtime\\vdf_fred_canonical_post_merge_final_audit_result_v0263.json")

canonical_csv = db / "VDF_Global_Macro.csv"
canonical_json = db / "VDF_Global_Macro.json"
canonical_parquet = db / "VDF_Global_Macro.parquet"
candidate_parquet = db / "VDF_Global_Macro_FRED_SmallScope_Candidate.parquet"
raw_parquet = db / "VDF_FRED_Raw_GlobalMacro_SmallScope.parquet"

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_CANONICAL_POST_MERGE_FINAL_AUDIT_SEAL_READY",
    "risk": "LOW",
    "policy": "Audit only. No fetch. No DB write.",
    "canonical_rows_csv": 0,
    "canonical_rows_json": 0,
    "canonical_rows_parquet": 0,
    "canonical_unique_keys": 0,
    "canonical_duplicate_keys": 0,
    "canonical_invalid_key_rows": 0,
    "candidate_rows": 0,
    "raw_rows": 0,
    "symbol_count": 0,
    "symbols": [],
    "backup_files_found": 0,
    "required_columns_missing": [],
    "checks": {}
}

try:
    import pandas as pd
except Exception as e:
    result["status"] = "VDF_FRED_CANONICAL_POST_MERGE_FINAL_AUDIT_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0)

required = ["symbol","date","value","source","unit","frequency","description"]

try:
    c_csv = pd.read_csv(canonical_csv)
    c_json = pd.read_json(canonical_json)
    c_parq = pd.read_parquet(canonical_parquet)
    candidate = pd.read_parquet(candidate_parquet)
    raw = pd.read_parquet(raw_parquet)

    result["canonical_rows_csv"] = int(len(c_csv))
    result["canonical_rows_json"] = int(len(c_json))
    result["canonical_rows_parquet"] = int(len(c_parq))
    result["candidate_rows"] = int(len(candidate))
    result["raw_rows"] = int(len(raw))

    result["required_columns_missing"] = [x for x in required if x not in c_parq.columns]

    x = c_parq.copy()
    for col in ["symbol","date"]:
        if col not in x.columns:
            x[col] = None

    x["symbol_key"] = x["symbol"].astype(str).str.strip()
    x["date_key"] = x["date"].astype(str).str.strip()

    invalid = x[
        (x["symbol_key"] == "") |
        (x["symbol_key"].str.lower().isin(["none","nan","nat"])) |
        (x["date_key"] == "") |
        (x["date_key"].str.lower().isin(["none","nan","nat"]))
    ]

    valid = x.drop(index=invalid.index)

    result["canonical_invalid_key_rows"] = int(len(invalid))
    result["canonical_unique_keys"] = int(valid[["symbol_key","date_key"]].drop_duplicates().shape[0])
    result["canonical_duplicate_keys"] = int(valid.duplicated(subset=["symbol_key","date_key"]).sum())
    result["symbols"] = sorted([str(v) for v in valid["symbol_key"].dropna().unique().tolist()])
    result["symbol_count"] = len(result["symbols"])

    if backup_dir.exists():
        for name in ["VDF_Global_Macro.csv","VDF_Global_Macro.json","VDF_Global_Macro.parquet"]:
            if (backup_dir / name).exists():
                result["backup_files_found"] += 1

    result["checks"] = {
        "row_counts_match": result["canonical_rows_csv"] == result["canonical_rows_json"] == result["canonical_rows_parquet"],
        "row_count_expected_1453": result["canonical_rows_parquet"] == 1453,
        "unique_keys_match_rows": result["canonical_unique_keys"] == result["canonical_rows_parquet"],
        "duplicates_zero": result["canonical_duplicate_keys"] == 0,
        "invalid_keys_zero": result["canonical_invalid_key_rows"] == 0,
        "symbol_count_min_5": result["symbol_count"] >= 5,
        "candidate_rows_expected_1452": result["candidate_rows"] == 1452,
        "raw_rows_expected_1509": result["raw_rows"] == 1509,
        "backup_three_files": result["backup_files_found"] == 3,
        "required_columns_ok": len(result["required_columns_missing"]) == 0
    }

    failed = [k for k,v in result["checks"].items() if not v]
    result["failed_checks"] = failed

    if failed:
        result["status"] = "VDF_FRED_CANONICAL_POST_MERGE_FINAL_AUDIT_SEAL_WITH_REVIEW"
        result["risk"] = "HIGH"
    else:
        result["status"] = "VDF_FRED_CANONICAL_POST_MERGE_FINAL_AUDIT_SEAL_READY"
        result["risk"] = "LOW"

except Exception as e:
    result["status"] = "VDF_FRED_CANONICAL_POST_MERGE_FINAL_AUDIT_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = str(e)

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "canonical_rows": result["canonical_rows_parquet"],
    "unique_keys": result["canonical_unique_keys"],
    "duplicate_keys": result["canonical_duplicate_keys"],
    "invalid_keys": result["canonical_invalid_key_rows"],
    "symbol_count": result["symbol_count"],
    "backup_files_found": result["backup_files_found"],
    "failed_checks": result.get("failed_checks", [])
}, ensure_ascii=False))
