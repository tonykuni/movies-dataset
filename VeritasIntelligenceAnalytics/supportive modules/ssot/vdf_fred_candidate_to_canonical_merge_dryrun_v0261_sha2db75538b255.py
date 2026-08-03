import json
from pathlib import Path
from datetime import datetime

db = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
staging = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_v0261_20260610_133556\\staging")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_v0261_20260610_133556\\runtime\\vdf_fred_candidate_to_canonical_merge_dryrun_result_v0261.json")
dedup_out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_v0261_20260610_133556\\registry\\VDF_FredCandidateToCanonical_DedupReport_v0261.json")

candidate_path = db / "VDF_Global_Macro_FRED_SmallScope_Candidate.parquet"
canonical_path = db / "VDF_Global_Macro.parquet"

preview_csv = staging / "VDF_Global_Macro_MERGE_PREVIEW_v0261.csv"
preview_json = staging / "VDF_Global_Macro_MERGE_PREVIEW_v0261.json"
preview_parquet = staging / "VDF_Global_Macro_MERGE_PREVIEW_v0261.parquet"

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_READY",
    "risk": "LOW",
    "policy": "Dry-run only. No canonical overwrite. Preview written to staging only.",
    "candidate_rows": 0,
    "canonical_exists": canonical_path.exists(),
    "canonical_rows": 0,
    "preview_rows": 0,
    "added_rows": 0,
    "replaced_rows": 0,
    "duplicate_candidate_keys": 0,
    "overlap_keys": 0,
    "symbols": [],
    "symbol_count": 0,
    "outputs": {}
}

try:
    import pandas as pd
except Exception as e:
    result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0)

required = ["symbol","date","value","source","unit","frequency","description"]

if not candidate_path.exists():
    result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = "Candidate parquet missing."
else:
    c = pd.read_parquet(candidate_path)
    result["candidate_rows"] = int(len(c))

    for col in required:
        if col not in c.columns:
            c[col] = None

    c = c[required].copy()
    c["symbol"] = c["symbol"].astype(str)
    c["date"] = c["date"].astype(str)
    c["merge_source"] = "FRED_SMALL_SCOPE_CANDIDATE"
    c["merge_run"] = "v0261_dryrun"
    c["merge_checked_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    result["duplicate_candidate_keys"] = int(c.duplicated(subset=["symbol","date"]).sum())
    c = c.drop_duplicates(subset=["symbol","date"], keep="last")

    if canonical_path.exists():
        k = pd.read_parquet(canonical_path)
        result["canonical_rows"] = int(len(k))

        for col in required:
            if col not in k.columns:
                k[col] = None

        k = k[required].copy()
        k["symbol"] = k["symbol"].astype(str)
        k["date"] = k["date"].astype(str)
        k["merge_source"] = "EXISTING_CANONICAL"
        k["merge_run"] = "existing"
        k["merge_checked_at"] = ""

        c_keys = set(zip(c["symbol"], c["date"]))
        k_keys = set(zip(k["symbol"], k["date"]))
        overlap = c_keys.intersection(k_keys)
        result["overlap_keys"] = int(len(overlap))

        k_non_overlap = k[~list(zip(k["symbol"], k["date"])).__iter__()] if False else k[~k.apply(lambda r: (str(r["symbol"]), str(r["date"])) in c_keys, axis=1)]
        result["replaced_rows"] = int(len(k) - len(k_non_overlap))
        result["added_rows"] = int(len(c) - result["replaced_rows"])

        preview = pd.concat([k_non_overlap, c], ignore_index=True)
    else:
        preview = c
        result["added_rows"] = int(len(c))
        result["replaced_rows"] = 0

    preview = preview.drop_duplicates(subset=["symbol","date"], keep="last")
    preview = preview.sort_values(["symbol","date"]).reset_index(drop=True)

    result["preview_rows"] = int(len(preview))
    result["symbols"] = sorted([str(x) for x in preview["symbol"].dropna().unique().tolist()])
    result["symbol_count"] = len(result["symbols"])

    staging.mkdir(parents=True, exist_ok=True)
    preview.to_csv(preview_csv, index=False, encoding="utf-8-sig")
    preview.to_json(preview_json, force_ascii=False, orient="records", indent=2)
    preview.to_parquet(preview_parquet, index=False)

    dedup = {
        "candidate_rows_before_dedup": result["candidate_rows"],
        "duplicate_candidate_keys": result["duplicate_candidate_keys"],
        "canonical_rows": result["canonical_rows"],
        "overlap_keys": result["overlap_keys"],
        "added_rows_estimated": result["added_rows"],
        "replaced_rows_estimated": result["replaced_rows"],
        "preview_rows": result["preview_rows"],
        "dedup_key": ["symbol","date"],
        "write_policy_future": "backup canonical first, then replace by symbol+date"
    }

    dedup_out.parent.mkdir(parents=True, exist_ok=True)
    dedup_out.write_text(json.dumps(dedup, ensure_ascii=False, indent=2), encoding="utf-8")

    result["outputs"] = {
        "preview_csv": str(preview_csv),
        "preview_json": str(preview_json),
        "preview_parquet": str(preview_parquet),
        "dedup_report": str(dedup_out)
    }

    if result["preview_rows"] <= 0 or result["symbol_count"] < 5:
        result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_WITH_REVIEW"
        result["risk"] = "HIGH"
    elif result["canonical_exists"]:
        result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_READY_WITH_BACKUP_REQUIRED"
        result["risk"] = "MEDIUM"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "candidate_rows": result["candidate_rows"],
    "canonical_rows": result["canonical_rows"],
    "preview_rows": result["preview_rows"],
    "overlap_keys": result["overlap_keys"],
    "added_rows": result["added_rows"],
    "replaced_rows": result["replaced_rows"]
}, ensure_ascii=False))
