import json
from pathlib import Path
from datetime import datetime

db = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
repair_preview_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_v02612_20260610_135521\\staging")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_EXECUTE_v0262_20260610_135958\\runtime\\vdf_fred_candidate_to_canonical_merge_execute_result_v0262.json")

preview = repair_preview_dir / "VDF_Global_Macro_MERGE_PREVIEW_AFTER_REPAIR_v02612.parquet"
canonical_csv = db / "VDF_Global_Macro.csv"
canonical_json = db / "VDF_Global_Macro.json"
canonical_parquet = db / "VDF_Global_Macro.parquet"

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_EXECUTE_READY",
    "risk": "LOW",
    "policy": "Write canonical from repair merge preview after verified backup.",
    "preview_rows": 0,
    "written_rows_csv": 0,
    "written_rows_json": 0,
    "written_rows_parquet": 0,
    "unique_keys": 0,
    "duplicate_keys": 0,
    "invalid_key_rows": 0,
    "symbols": [],
    "symbol_count": 0,
    "outputs": {}
}

try:
    import pandas as pd
except Exception as e:
    result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_EXECUTE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0)

required = ["symbol","date","value","source","unit","frequency","description"]

if not preview.exists():
    result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_EXECUTE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = "Merge preview after repair missing."
else:
    df = pd.read_parquet(preview)
    result["preview_rows"] = int(len(df))

    for c in required:
        if c not in df.columns:
            df[c] = None

    df = df[required].copy()
    df["symbol"] = df["symbol"].astype(str).str.strip()
    df["date"] = df["date"].astype(str).str.strip()

    invalid = df[
        (df["symbol"] == "") |
        (df["symbol"].str.lower().isin(["none","nan","nat"])) |
        (df["date"] == "") |
        (df["date"].str.lower().isin(["none","nan","nat"]))
    ]

    result["invalid_key_rows"] = int(len(invalid))

    df = df.drop(index=invalid.index)
    df = df.drop_duplicates(subset=["symbol","date"], keep="last")
    df = df.sort_values(["symbol","date"]).reset_index(drop=True)

    result["unique_keys"] = int(df[["symbol","date"]].drop_duplicates().shape[0])
    result["duplicate_keys"] = int(df.duplicated(subset=["symbol","date"]).sum())
    result["symbols"] = sorted([str(x) for x in df["symbol"].dropna().unique().tolist()])
    result["symbol_count"] = len(result["symbols"])

    if len(df) <= 0 or result["duplicate_keys"] > 0 or result["symbol_count"] < 5:
        result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_EXECUTE_WITH_REVIEW"
        result["risk"] = "HIGH"
        result["error"] = "Final canonical validation failed before write."
    else:
        df.to_csv(canonical_csv, index=False, encoding="utf-8-sig")
        df.to_json(canonical_json, force_ascii=False, orient="records", indent=2)
        df.to_parquet(canonical_parquet, index=False)

        result["written_rows_csv"] = int(len(pd.read_csv(canonical_csv)))
        result["written_rows_json"] = int(len(pd.read_json(canonical_json)))
        result["written_rows_parquet"] = int(len(pd.read_parquet(canonical_parquet)))
        result["outputs"] = {
            "canonical_csv": str(canonical_csv),
            "canonical_json": str(canonical_json),
            "canonical_parquet": str(canonical_parquet)
        }

        if not (result["written_rows_csv"] == result["written_rows_json"] == result["written_rows_parquet"] == len(df)):
            result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_EXECUTE_WITH_REVIEW"
            result["risk"] = "HIGH"
            result["error"] = "Post-write row count mismatch."

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "written_rows_csv": result["written_rows_csv"],
    "written_rows_json": result["written_rows_json"],
    "written_rows_parquet": result["written_rows_parquet"],
    "unique_keys": result["unique_keys"],
    "duplicate_keys": result["duplicate_keys"],
    "symbol_count": result["symbol_count"]
}, ensure_ascii=False))
