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
import hashlib
from pathlib import Path
from datetime import datetime

preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\preview\\VDF_AkShare_CanonicalPreview_v0277.csv")
preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\preview\\VDF_AkShare_CanonicalPreview_v0277.json")
mapping_rules_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\registry\\VDF_AkShare_CanonicalMappingRules_v0277.json")
readiness_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANONICAL_MAPPING_GATE_v0277_20260610_220358\\registry\\VDF_AkShare_MergeReadinessGate_v0277.json")
db_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
dryrun_preview_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_v0278_20260610_220705\\preview\\VDF_AkShare_CandidateToCanonicalDryRunPreview_v0278.json")
dryrun_preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_v0278_20260610_220705\\preview\\VDF_AkShare_CandidateToCanonicalDryRunPreview_v0278.csv")
dryrun_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_v0278_20260610_220705\\registry\\VDF_AkShare_CandidateToCanonicalDryRunAudit_v0278.json")
execution_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_v0278_20260610_220705\\registry\\VDF_AkShare_MergeExecutionGate_v0278.json")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_v0278_20260610_220705\\runtime\\vdf_akshare_candidate_to_canonical_dryrun_result_v0278.json")

CANONICAL_FILES = {
    "VDF_Global_Commodity": [
        "VDF_Global_Commodity.csv",
        "VDF_Global_Commodity.json",
        "VDF_Global_Commodity.parquet"
    ]
}

KEY_COLS = ["canonical_family", "symbol", "date", "source", "value"]

def sha256_text(s):
    return hashlib.sha256(str(s).encode("utf-8")).hexdigest()[:16]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_READY",
    "risk": "LOW",
    "policy": "Dry-run only. No DATABASE write. No canonical merge.",
    "preview_rows": 0,
    "canonical_existing_rows": 0,
    "dryrun_rows_after_merge": 0,
    "new_candidate_rows": 0,
    "overlap_rows": 0,
    "duplicate_key_rows_in_preview": 0,
    "invalid_key_rows": 0,
    "canonical_files_detected": [],
    "canonical_files_missing": [],
    "recommendation": "UNKNOWN"
}

try:
    import pandas as pd

    if not preview_csv.exists():
        raise RuntimeError("Canonical preview CSV missing.")
    if not preview_json.exists():
        raise RuntimeError("Canonical preview JSON missing.")
    if not mapping_rules_json.exists():
        raise RuntimeError("Mapping rules JSON missing.")
    if not readiness_json.exists():
        raise RuntimeError("Readiness JSON missing.")

    preview = pd.read_csv(preview_csv).astype(str).fillna("")
    result["preview_rows"] = int(len(preview))

    required = ["canonical_family","symbol","date","value","source"]
    missing_required = [c for c in required if c not in preview.columns]

    if missing_required:
        raise RuntimeError("Preview missing required columns: " + ",".join(missing_required))

    invalid = preview[
        (preview["symbol"].astype(str).str.strip() == "") |
        (preview["value"].astype(str).str.strip() == "") |
        (preview["source"].astype(str).str.strip() == "")
    ]
    result["invalid_key_rows"] = int(len(invalid))

    key_cols_available = [c for c in KEY_COLS if c in preview.columns]
    preview["_vdf_dryrun_key"] = preview[key_cols_available].astype(str).agg("|".join, axis=1)
    result["duplicate_key_rows_in_preview"] = int(preview.duplicated(subset=["_vdf_dryrun_key"], keep=False).sum())

    existing_frames = []
    for fam, names in CANONICAL_FILES.items():
        found_any = False
        for name in names:
            p = db_dir / name
            if p.exists():
                found_any = True
                result["canonical_files_detected"].append(str(p))
                try:
                    if p.suffix.lower() == ".csv":
                        df = pd.read_csv(p).astype(str).fillna("")
                    elif p.suffix.lower() == ".json":
                        df = pd.read_json(p).astype(str).fillna("")
                    elif p.suffix.lower() == ".parquet":
                        df = pd.read_parquet(p).astype(str).fillna("")
                    else:
                        continue
                    if len(df) > 0:
                        if "canonical_family" not in df.columns:
                            df["canonical_family"] = fam
                        existing_frames.append(df)
                    break
                except Exception:
                    continue
        if not found_any:
            for name in names:
                result["canonical_files_missing"].append(str(db_dir / name))

    if existing_frames:
        existing = pd.concat(existing_frames, ignore_index=True)
        result["canonical_existing_rows"] = int(len(existing))

        for c in required:
            if c not in existing.columns:
                existing[c] = ""

        existing["_vdf_dryrun_key"] = existing[key_cols_available].astype(str).agg("|".join, axis=1)
        existing_keys = set(existing["_vdf_dryrun_key"].tolist())
        preview["_vdf_overlap_existing"] = preview["_vdf_dryrun_key"].apply(lambda x: x in existing_keys)
        result["overlap_rows"] = int(preview["_vdf_overlap_existing"].sum())
        new_preview = preview[preview["_vdf_overlap_existing"] == False].copy()
    else:
        existing = pd.DataFrame()
        preview["_vdf_overlap_existing"] = False
        new_preview = preview.copy()

    result["new_candidate_rows"] = int(len(new_preview))
    result["dryrun_rows_after_merge"] = int(result["canonical_existing_rows"] + result["new_candidate_rows"])

    preview["_vdf_dryrun_action"] = preview["_vdf_overlap_existing"].apply(lambda x: "SKIP_EXISTING_KEY" if x else "ADD_CANDIDATE")
    preview["_vdf_dryrun_policy"] = "DRYRUN_ONLY_NO_DATABASE_WRITE"
    preview["_vdf_dryrun_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    preview_for_export = preview.drop(columns=["_vdf_dryrun_key"], errors="ignore")

    dryrun_preview_csv.parent.mkdir(parents=True, exist_ok=True)
    preview_for_export.to_csv(dryrun_preview_csv, index=False, encoding="utf-8-sig")

    dryrun_preview_json.parent.mkdir(parents=True, exist_ok=True)
    preview_for_export.to_json(dryrun_preview_json, orient="records", force_ascii=False, indent=2)

    audit = {
        "generated_at": result["generated_at"],
        "policy": result["policy"],
        "preview_rows": result["preview_rows"],
        "canonical_existing_rows": result["canonical_existing_rows"],
        "new_candidate_rows": result["new_candidate_rows"],
        "overlap_rows": result["overlap_rows"],
        "dryrun_rows_after_merge": result["dryrun_rows_after_merge"],
        "duplicate_key_rows_in_preview": result["duplicate_key_rows_in_preview"],
        "invalid_key_rows": result["invalid_key_rows"],
        "canonical_files_detected": result["canonical_files_detected"],
        "canonical_files_missing": result["canonical_files_missing"],
        "dryrun_preview_csv": str(dryrun_preview_csv),
        "dryrun_preview_json": str(dryrun_preview_json)
    }

    dryrun_audit_json.parent.mkdir(parents=True, exist_ok=True)
    dryrun_audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

    execution_gate = {
        "generated_at": result["generated_at"],
        "status": "READY_FOR_V0279_EXECUTION_GATE_REVIEW",
        "risk": "MEDIUM",
        "allowed_to_write_database_now": False,
        "allowed_to_merge_canonical_now": False,
        "preview_rows": result["preview_rows"],
        "new_candidate_rows": result["new_candidate_rows"],
        "overlap_rows": result["overlap_rows"],
        "invalid_key_rows": result["invalid_key_rows"],
        "duplicate_key_rows_in_preview": result["duplicate_key_rows_in_preview"],
        "next_step": "v027.9 AkShare canonical merge execution gate review; no DB write",
        "required_before_real_write": [
            "backup canonical target files",
            "review v027.8 dry-run rows",
            "confirm canonical key policy",
            "create v027.9 execution gate review",
            "only v028 may write after final explicit gate"
        ]
    }

    if result["preview_rows"] <= 0:
        result["status"] = "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_WITH_REPAIR_REQUIRED"
        result["risk"] = "HIGH"
        result["recommendation"] = "BLOCK_NO_PREVIEW_ROWS"
        execution_gate["status"] = "BLOCK_NO_PREVIEW_ROWS"
        execution_gate["risk"] = "HIGH"
    elif result["invalid_key_rows"] > 0:
        result["status"] = "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_READY_WITH_KEY_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V0279_EXECUTION_GATE_REVIEW_WITH_KEY_REVIEW_NO_DB_WRITE"
        execution_gate["status"] = "READY_WITH_KEY_REVIEW"
        execution_gate["risk"] = "MEDIUM"
    elif result["duplicate_key_rows_in_preview"] > 0:
        result["status"] = "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_READY_WITH_DEDUP_REVIEW"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V0279_EXECUTION_GATE_REVIEW_WITH_DEDUP_REVIEW_NO_DB_WRITE"
        execution_gate["status"] = "READY_WITH_DEDUP_REVIEW"
        execution_gate["risk"] = "MEDIUM"
    else:
        result["status"] = "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_READY"
        result["risk"] = "LOW"
        result["recommendation"] = "ALLOW_V0279_CANONICAL_MERGE_EXECUTION_GATE_REVIEW_ONLY_NO_DB_WRITE"
        execution_gate["status"] = "READY_FOR_V0279_EXECUTION_GATE_REVIEW"
        execution_gate["risk"] = "LOW"

    execution_gate_json.parent.mkdir(parents=True, exist_ok=True)
    execution_gate_json.write_text(json.dumps(execution_gate, ensure_ascii=False, indent=2), encoding="utf-8")

except Exception as e:
    result["status"] = "VDF_AKSHARE_CANDIDATE_TO_CANONICAL_DRYRUN_WITH_REPAIR_REQUIRED"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_DRYRUN_REPAIR_INPUTS"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "preview_rows": result["preview_rows"],
    "canonical_existing_rows": result["canonical_existing_rows"],
    "new_candidate_rows": result["new_candidate_rows"],
    "overlap_rows": result["overlap_rows"],
    "dryrun_rows_after_merge": result["dryrun_rows_after_merge"],
    "invalid_key_rows": result["invalid_key_rows"],
    "duplicate_key_rows_in_preview": result["duplicate_key_rows_in_preview"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
