import json
from pathlib import Path
from datetime import datetime
import pandas as pd

candidate_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_FREEZE_SEAL_v0280_20260611_020645\\artifacts\\VDF_AkShare_v0279_ReadinessFinalRows.csv")
quarantine_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_FREEZE_SEAL_v0280_20260611_020645\\artifacts\\VDF_AkShare_v0279_DuplicateQuarantineRows.csv")
canonical_list_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\runtime\\vdf_akshare_v0282_canonical_file_list.json")
insert_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_DryRun_InsertRows.csv")
update_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_DryRun_UpdateRows.csv")
unchanged_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_DryRun_UnchangedRows.csv")
conflict_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_DryRun_ConflictRows.csv")
candidate_copy_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_CandidateRows_Copy.csv")
quarantine_copy_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_DuplicateQuarantine_Copy.csv")
summary_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\plan\\VDF_AkShare_v0282_DryRunCompareSummary.json")
next_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\plan\\VDF_AkShare_v0283_BackupRollbackStagingPlan.json")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\runtime\\vdf_akshare_write_dryrun_compare_result_v0282.json")

for p in [insert_csv, update_csv, unchanged_csv, conflict_csv, candidate_copy_csv, quarantine_copy_csv, summary_json, next_gate_json, out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

def read_csv(p):
    try:
        return pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
    except Exception:
        return pd.read_csv(p, dtype=str).fillna("")

def read_json_records(p):
    try:
        obj = json.loads(Path(p).read_text(encoding="utf-8"))
        if isinstance(obj, list):
            return pd.DataFrame(obj).fillna("")
        if isinstance(obj, dict):
            if "data" in obj and isinstance(obj["data"], list):
                return pd.DataFrame(obj["data"]).fillna("")
            return pd.DataFrame([obj]).fillna("")
    except Exception:
        pass
    return pd.DataFrame()

candidate = read_csv(candidate_csv)
quarantine = read_csv(quarantine_csv)

for c in ["family","symbol","date","value","source","canonical_key"]:
    if c not in candidate.columns:
        candidate[c] = ""

candidate.to_csv(candidate_copy_csv, index=False, encoding="utf-8-sig")
quarantine.to_csv(quarantine_copy_csv, index=False, encoding="utf-8-sig")

canonical_files = json.loads(canonical_list_json.read_text(encoding="utf-8"))
existing_frames = []

for item in canonical_files:
    p = Path(item.get("path",""))
    if not p.exists():
        continue
    try:
        if p.suffix.lower() == ".csv":
            existing_frames.append(read_csv(p))
        elif p.suffix.lower() == ".json":
            existing_frames.append(read_json_records(p))
        elif p.suffix.lower() == ".parquet":
            try:
                existing_frames.append(pd.read_parquet(p).fillna("").astype(str))
            except Exception:
                pass
    except Exception:
        pass

if existing_frames:
    existing = pd.concat(existing_frames, ignore_index=True, sort=False).fillna("")
else:
    existing = pd.DataFrame()

for c in ["family","symbol","date","value","source","canonical_key"]:
    if c not in existing.columns:
        existing[c] = ""

if "canonical_key" not in existing.columns or existing.empty:
    existing_keys = set()
else:
    existing = existing.drop_duplicates(subset=["canonical_key"], keep="first").copy()
    existing_keys = set(existing["canonical_key"].astype(str).tolist())

candidate["_vdf_v0282_compare_policy"] = "DRYRUN_COMPARE_ONLY_NO_DB_WRITE"

insert_rows = []
update_rows = []
unchanged_rows = []
conflict_rows = []

existing_by_key = {}
if not existing.empty:
    for _, r in existing.iterrows():
        existing_by_key[str(r.get("canonical_key",""))] = r.to_dict()

for _, row in candidate.iterrows():
    r = row.to_dict()
    key = str(r.get("canonical_key",""))
    if not key:
        r["_vdf_v0282_delta_type"] = "conflict"
        r["_vdf_v0282_delta_reason"] = "empty_canonical_key"
        conflict_rows.append(r)
        continue

    if key not in existing_keys:
        r["_vdf_v0282_delta_type"] = "insert"
        r["_vdf_v0282_delta_reason"] = "key_not_found_in_existing"
        insert_rows.append(r)
    else:
        old = existing_by_key.get(key, {})
        old_value = str(old.get("value","")).strip()
        new_value = str(r.get("value","")).strip()
        old_symbol = str(old.get("symbol","")).strip()
        new_symbol = str(r.get("symbol","")).strip()
        old_date = str(old.get("date","")).strip()
        new_date = str(r.get("date","")).strip()
        old_source = str(old.get("source","")).strip()
        new_source = str(r.get("source","")).strip()

        if old_value == new_value and old_symbol == new_symbol and old_date == new_date and old_source == new_source:
            r["_vdf_v0282_delta_type"] = "unchanged"
            r["_vdf_v0282_delta_reason"] = "same_key_same_core_fields"
            unchanged_rows.append(r)
        else:
            r["_vdf_v0282_delta_type"] = "update"
            r["_vdf_v0282_delta_reason"] = "same_key_changed_core_fields"
            r["_vdf_v0282_existing_value"] = old_value
            r["_vdf_v0282_existing_symbol"] = old_symbol
            r["_vdf_v0282_existing_date"] = old_date
            r["_vdf_v0282_existing_source"] = old_source
            update_rows.append(r)

insert_df = pd.DataFrame(insert_rows)
update_df = pd.DataFrame(update_rows)
unchanged_df = pd.DataFrame(unchanged_rows)
conflict_df = pd.DataFrame(conflict_rows)

insert_df.to_csv(insert_csv, index=False, encoding="utf-8-sig")
update_df.to_csv(update_csv, index=False, encoding="utf-8-sig")
unchanged_df.to_csv(unchanged_csv, index=False, encoding="utf-8-sig")
conflict_df.to_csv(conflict_csv, index=False, encoding="utf-8-sig")

metrics = {
    "candidate_rows": int(len(candidate)),
    "duplicate_quarantine_rows": int(len(quarantine)),
    "existing_rows_loaded": int(len(existing)),
    "existing_files_loaded": int(len(existing_frames)),
    "insert_rows": int(len(insert_df)),
    "update_rows": int(len(update_df)),
    "unchanged_rows": int(len(unchanged_df)),
    "conflict_rows": int(len(conflict_df)),
    "db_write_enabled": False,
    "canonical_merge_enabled": False
}

if metrics["conflict_rows"] == 0 and metrics["candidate_rows"] > 0:
    status = "VDF_AKSHARE_WRITE_DRYRUN_COMPARE_READY"
    risk = "MEDIUM" if metrics["insert_rows"] > 0 or metrics["update_rows"] > 0 else "LOW"
    recommendation = "ALLOW_V0283_BACKUP_ROLLBACK_STAGING_PLAN_ONLY_NO_DB_WRITE"
    next_step = "v028.3 backup rollback staging plan only; no DB write"
else:
    status = "VDF_AKSHARE_WRITE_DRYRUN_COMPARE_BLOCKED"
    risk = "HIGH"
    recommendation = "BLOCK_V0283_UNTIL_DRYRUN_CONFLICTS_REPAIRED"
    next_step = "repair dry-run conflicts; no DB write"

summary = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "policy": {
        "dryrun_compare_only": True,
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "actual_write_allowed": False,
        "duplicate_quarantine_excluded": True
    },
    "metrics": metrics,
    "artifacts": {
        "insert_csv": str(insert_csv),
        "update_csv": str(update_csv),
        "unchanged_csv": str(unchanged_csv),
        "conflict_csv": str(conflict_csv),
        "candidate_copy_csv": str(candidate_copy_csv),
        "duplicate_quarantine_copy_csv": str(quarantine_copy_csv)
    },
    "recommendation": recommendation,
    "next_step": next_step
}
summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

next_gate = {
    "generated_at": datetime.now().isoformat(),
    "stage": "v028.3",
    "title": "Backup rollback staging plan only",
    "allowed": status == "VDF_AKSHARE_WRITE_DRYRUN_COMPARE_READY",
    "still_no_db_write": True,
    "still_no_canonical_merge": True,
    "required_before_any_future_write": [
        "full DATABASE backup",
        "target table snapshot",
        "staging table plan",
        "rollback plan",
        "post-write validation plan",
        "separate explicit write approval"
    ],
    "dryrun_metrics": metrics
}
next_gate_json.write_text(json.dumps(next_gate, ensure_ascii=False, indent=2), encoding="utf-8")

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "recommendation": recommendation,
    "metrics": metrics,
    "artifacts": summary["artifacts"] | {
        "summary_json": str(summary_json),
        "next_gate_json": str(next_gate_json)
    },
    "next_step": next_step
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
