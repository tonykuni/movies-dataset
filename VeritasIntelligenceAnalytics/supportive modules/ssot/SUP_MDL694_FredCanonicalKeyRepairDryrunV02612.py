import json
from pathlib import Path
from datetime import datetime

db = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
staging = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_v02612_20260610_135521\\staging")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_v02612_20260610_135521\\runtime\\vdf_fred_canonical_key_repair_dryrun_result_v02612.json")
repair_report = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_v02612_20260610_135521\\registry\\VDF_FredCanonical_KeyRepairReport_v02612.json")

canonical_path = db / "VDF_Global_Macro.parquet"
candidate_path = db / "VDF_Global_Macro_FRED_SmallScope_Candidate.parquet"

repair_csv = staging / "VDF_Global_Macro_CANONICAL_KEY_REPAIR_PREVIEW_v02612.csv"
repair_json = staging / "VDF_Global_Macro_CANONICAL_KEY_REPAIR_PREVIEW_v02612.json"
repair_parquet = staging / "VDF_Global_Macro_CANONICAL_KEY_REPAIR_PREVIEW_v02612.parquet"

merge_csv = staging / "VDF_Global_Macro_MERGE_PREVIEW_AFTER_REPAIR_v02612.csv"
merge_json = staging / "VDF_Global_Macro_MERGE_PREVIEW_AFTER_REPAIR_v02612.json"
merge_parquet = staging / "VDF_Global_Macro_MERGE_PREVIEW_AFTER_REPAIR_v02612.parquet"

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_READY",
    "risk": "LOW",
    "policy": "Repair dry-run only. No canonical overwrite. Staging preview only.",
    "canonical_rows_before": 0,
    "canonical_unique_keys_before": 0,
    "canonical_duplicate_keys_before": 0,
    "canonical_rows_after_repair_preview": 0,
    "canonical_unique_keys_after_repair_preview": 0,
    "candidate_rows": 0,
    "candidate_unique_keys": 0,
    "merge_preview_rows": 0,
    "merge_preview_unique_keys": 0,
    "overlap_keys_after_repair": 0,
    "dropped_duplicate_rows_in_repair_preview": 0,
    "outputs": {},
    "recommendation": "UNKNOWN"
}

try:
    import pandas as pd
except Exception as e:
    result["status"] = "VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0)

required = ["symbol","date","value","source","unit","frequency","description"]

def normalize(df, tag):
    x = df.copy()
    for c in required:
        if c not in x.columns:
            x[c] = None
    x = x[required].copy()
    x["symbol"] = x["symbol"].astype(str).str.strip()
    x["date"] = x["date"].astype(str).str.strip()
    x["repair_source"] = tag
    x["repair_checked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return x

if not canonical_path.exists() or not candidate_path.exists():
    result["status"] = "VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["recommendation"] = "BLOCK_MISSING_SOURCE"
else:
    k0 = pd.read_parquet(canonical_path)
    c0 = pd.read_parquet(candidate_path)

    k = normalize(k0, "EXISTING_CANONICAL_REPAIR_PREVIEW")
    c = normalize(c0, "FRED_SMALL_SCOPE_CANDIDATE")

    valid_mask = ~(
        k["symbol"].isin(["", "None", "nan", "NaN", "NaT"]) |
        k["date"].isin(["", "None", "nan", "NaN", "NaT"])
    )
    invalid = k[~valid_mask].copy()
    valid = k[valid_mask].copy()

    result["canonical_rows_before"] = int(len(k))
    result["canonical_unique_keys_before"] = int(valid[["symbol","date"]].drop_duplicates().shape[0])
    result["canonical_duplicate_keys_before"] = int(valid.duplicated(subset=["symbol","date"]).sum())

    # Repair preview rule:
    # 1) invalid key rows are excluded from future canonical merge preview, but kept in report.
    # 2) duplicate keys keep last row.
    repaired = valid.drop_duplicates(subset=["symbol","date"], keep="last").copy()
    result["canonical_rows_after_repair_preview"] = int(len(repaired))
    result["canonical_unique_keys_after_repair_preview"] = int(repaired[["symbol","date"]].drop_duplicates().shape[0])
    result["dropped_duplicate_rows_in_repair_preview"] = int(len(valid) - len(repaired))

    result["candidate_rows"] = int(len(c))
    result["candidate_unique_keys"] = int(c[["symbol","date"]].drop_duplicates().shape[0])

    c_keys = set(zip(c["symbol"], c["date"]))
    r_keys = set(zip(repaired["symbol"], repaired["date"]))
    overlap = c_keys.intersection(r_keys)
    result["overlap_keys_after_repair"] = int(len(overlap))

    repaired_non_overlap = repaired[~repaired.apply(lambda r: (str(r["symbol"]), str(r["date"])) in c_keys, axis=1)]
    merge_preview = pd.concat([repaired_non_overlap, c], ignore_index=True)
    merge_preview = merge_preview.drop_duplicates(subset=["symbol","date"], keep="last")
    merge_preview = merge_preview.sort_values(["symbol","date"]).reset_index(drop=True)

    result["merge_preview_rows"] = int(len(merge_preview))
    result["merge_preview_unique_keys"] = int(merge_preview[["symbol","date"]].drop_duplicates().shape[0])

    staging.mkdir(parents=True, exist_ok=True)
    repaired.to_csv(repair_csv, index=False, encoding="utf-8-sig")
    repaired.to_json(repair_json, force_ascii=False, orient="records", indent=2)
    repaired.to_parquet(repair_parquet, index=False)

    merge_preview.to_csv(merge_csv, index=False, encoding="utf-8-sig")
    merge_preview.to_json(merge_json, force_ascii=False, orient="records", indent=2)
    merge_preview.to_parquet(merge_parquet, index=False)

    report = {
        "rule": "Repair dry-run only; keep last duplicate by symbol+date; invalid keys excluded from future merge preview but not deleted in DB.",
        "canonical_rows_before": result["canonical_rows_before"],
        "canonical_unique_keys_before": result["canonical_unique_keys_before"],
        "canonical_duplicate_keys_before": result["canonical_duplicate_keys_before"],
        "invalid_key_rows": int(len(invalid)),
        "invalid_key_sample": invalid.head(30).astype(str).to_dict(orient="records"),
        "duplicate_key_sample": valid[valid.duplicated(subset=["symbol","date"], keep=False)].head(30).astype(str).to_dict(orient="records"),
        "canonical_rows_after_repair_preview": result["canonical_rows_after_repair_preview"],
        "dropped_duplicate_rows_in_repair_preview": result["dropped_duplicate_rows_in_repair_preview"],
        "candidate_rows": result["candidate_rows"],
        "candidate_unique_keys": result["candidate_unique_keys"],
        "overlap_keys_after_repair": result["overlap_keys_after_repair"],
        "merge_preview_rows": result["merge_preview_rows"],
        "merge_preview_unique_keys": result["merge_preview_unique_keys"],
        "expected_merge_preview_rows": result["canonical_unique_keys_after_repair_preview"] + result["candidate_unique_keys"] - result["overlap_keys_after_repair"]
    }

    repair_report.parent.mkdir(parents=True, exist_ok=True)
    repair_report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    result["outputs"] = {
        "repair_preview_csv": str(repair_csv),
        "repair_preview_json": str(repair_json),
        "repair_preview_parquet": str(repair_parquet),
        "merge_preview_after_repair_csv": str(merge_csv),
        "merge_preview_after_repair_json": str(merge_json),
        "merge_preview_after_repair_parquet": str(merge_parquet),
        "repair_report": str(repair_report)
    }

    expected = result["canonical_unique_keys_after_repair_preview"] + result["candidate_unique_keys"] - result["overlap_keys_after_repair"]

    if result["candidate_unique_keys"] != result["candidate_rows"]:
        result["status"] = "VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_WITH_REVIEW"
        result["risk"] = "HIGH"
        result["recommendation"] = "BLOCK_CANDIDATE_DUPLICATES"
    elif result["merge_preview_rows"] != expected:
        result["status"] = "VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_WITH_REVIEW"
        result["risk"] = "HIGH"
        result["recommendation"] = "BLOCK_MERGE_PREVIEW_ARITHMETIC"
    else:
        result["status"] = "VDF_FRED_CANONICAL_KEY_REPAIR_DRYRUN_READY"
        result["risk"] = "LOW"
        result["recommendation"] = "ALLOW_V0262_REAL_MERGE_WITH_BACKUP_AND_REPAIR_RULE"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "canonical_rows_before": result["canonical_rows_before"],
    "canonical_unique_keys_before": result["canonical_unique_keys_before"],
    "canonical_duplicate_keys_before": result["canonical_duplicate_keys_before"],
    "canonical_rows_after_repair_preview": result["canonical_rows_after_repair_preview"],
    "candidate_rows": result["candidate_rows"],
    "merge_preview_rows": result["merge_preview_rows"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
