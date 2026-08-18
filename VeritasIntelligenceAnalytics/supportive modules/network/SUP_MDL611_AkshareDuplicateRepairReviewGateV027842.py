import json
from pathlib import Path
from datetime import datetime
import pandas as pd

source_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_COLLISION_RESOLVER_GATE_v027841_20260611_013435\\preview\\VDF_AkShare_CollisionResolver_FinalValidRows_v027841.csv")
unique_final_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_v027842_20260611_013908\\preview\\VDF_AkShare_DuplicateRepair_UniqueFinalRows_v027842.csv")
unique_final_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_v027842_20260611_013908\\preview\\VDF_AkShare_DuplicateRepair_UniqueFinalRows_v027842.json")
duplicate_quarantine_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_v027842_20260611_013908\\preview\\VDF_AkShare_DuplicateRepair_DuplicateQuarantineRows_v027842.csv")
duplicate_groups_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_v027842_20260611_013908\\registry\\VDF_AkShare_DuplicateRepair_DuplicateGroups_v027842.csv")
duplicate_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_v027842_20260611_013908\\registry\\VDF_AkShare_DuplicateRepair_Audit_v027842.json")
execution_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_v027842_20260611_013908\\plan\\VDF_AkShare_DuplicateRepair_ExecutionGateReview_v027842.json")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_v027842_20260611_013908\\runtime\\vdf_akshare_duplicate_repair_review_gate_result_v027842.json")

for p in [unique_final_csv, unique_final_json, duplicate_quarantine_csv, duplicate_groups_csv, duplicate_audit_json, execution_gate_json, out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

def read_csv(p):
    try:
        return pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
    except Exception:
        return pd.read_csv(p, dtype=str).fillna("")

df = read_csv(source_csv)

for c in ["canonical_key","family","symbol","date","source","value"]:
    if c not in df.columns:
        df[c] = ""

df["_vdf_v027842_original_order"] = range(1, len(df) + 1)

def priority(row):
    part = str(row.get("_vdf_v027841_source_partition", ""))
    repair_status = str(row.get("_vdf_v02784_repair_status", ""))
    policy = str(row.get("_vdf_v027841_collision_policy", ""))

    # Preserve original valid rows over repaired rows.
    if "preserved_valid" in part:
        return 100
    if "preserved" in repair_status:
        return 90
    if "repaired" in repair_status:
        return 50
    if "include_preview" in policy:
        return 40
    return 10

df["_vdf_v027842_keep_priority"] = df.apply(priority, axis=1)

# Sort so authoritative rows come first per key.
sort_cols = ["canonical_key", "_vdf_v027842_keep_priority", "_vdf_v027842_original_order"]
df_sorted = df.sort_values(
    by=sort_cols,
    ascending=[True, False, True],
    kind="mergesort"
).copy()

dup_group_sizes = df_sorted.groupby("canonical_key", dropna=False).size().reset_index(name="group_count")
dup_groups = dup_group_sizes[dup_group_sizes["group_count"] > 1].copy()

df_sorted["_vdf_v027842_is_duplicate_group"] = df_sorted["canonical_key"].isin(set(dup_groups["canonical_key"].astype(str)))
df_sorted["_vdf_v027842_rank_in_key"] = df_sorted.groupby("canonical_key").cumcount() + 1

unique_final = df_sorted[df_sorted["_vdf_v027842_rank_in_key"] == 1].copy()
duplicate_quarantine = df_sorted[df_sorted["_vdf_v027842_rank_in_key"] > 1].copy()

unique_final["_vdf_v027842_duplicate_policy"] = "keep_authoritative_first_per_canonical_key"
duplicate_quarantine["_vdf_v027842_duplicate_policy"] = "duplicate_quarantine_not_for_canonical_write"

duplicate_after = int(unique_final.duplicated(subset=["canonical_key"], keep=False).sum()) if not unique_final.empty else 0

unique_final.to_csv(unique_final_csv, index=False, encoding="utf-8-sig")
unique_final.to_json(unique_final_json, orient="records", force_ascii=False, indent=2)
duplicate_quarantine.to_csv(duplicate_quarantine_csv, index=False, encoding="utf-8-sig")
dup_groups.to_csv(duplicate_groups_csv, index=False, encoding="utf-8-sig")

metrics = {
    "input_rows": int(len(df)),
    "duplicate_group_count": int(len(dup_groups)),
    "duplicate_quarantine_rows": int(len(duplicate_quarantine)),
    "unique_final_rows": int(len(unique_final)),
    "duplicate_after_repair_review": duplicate_after,
    "still_invalid_rows": int((unique_final.get("is_valid", pd.Series(dtype=str)).astype(str).str.lower().isin(["false","0","no"])).sum()) if "is_valid" in unique_final.columns else 0
}

if metrics["unique_final_rows"] > 0 and metrics["duplicate_after_repair_review"] == 0 and metrics["still_invalid_rows"] == 0:
    if metrics["duplicate_quarantine_rows"] == 0:
        status = "VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_READY"
        risk = "LOW"
        recommendation = "ALLOW_V0279_EXECUTION_READINESS_REVIEW_ONLY_NO_DB_WRITE"
        next_step = "v027.9 execution readiness review only; no DB write"
    else:
        status = "VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_READY_WITH_DUPLICATE_QUARANTINE"
        risk = "MEDIUM"
        recommendation = "ALLOW_V0279_EXECUTION_READINESS_REVIEW_WITH_DUPLICATE_QUARANTINE_NO_DB_WRITE"
        next_step = "v027.9 execution readiness review with duplicate quarantine; no DB write"
else:
    status = "VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_BLOCKED"
    risk = "HIGH"
    recommendation = "BLOCK_V0279_UNTIL_FINAL_VALID_REVIEW"
    next_step = "v027.8.4.3 final valid review only; no DB write"

audit = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "policy": {
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "keep_first_per_canonical_key": True,
        "preserved_valid_priority": True,
        "duplicate_rows_quarantined": True
    },
    "metrics": metrics,
    "artifacts": {
        "unique_final_csv": str(unique_final_csv),
        "unique_final_json": str(unique_final_json),
        "duplicate_quarantine_csv": str(duplicate_quarantine_csv),
        "duplicate_groups_csv": str(duplicate_groups_csv)
    },
    "recommendation": recommendation,
    "next_step": next_step
}
duplicate_audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

execution_gate = {
    "generated_at": datetime.now().isoformat(),
    "status": "EXECUTION_GATE_READY_FOR_REVIEW_WITH_DUPLICATE_QUARANTINE" if risk in ["LOW","MEDIUM"] else "EXECUTION_GATE_CLOSED_FINAL_VALID_REVIEW",
    "risk": risk,
    "allowed_to_write_database": False,
    "allowed_to_merge_canonical": False,
    "metrics": metrics,
    "hard_stop": [
        "No DB write in v027.8.4.2",
        "No canonical merge in v027.8.4.2",
        "v027.9 is review only unless explicitly approved",
        "Duplicate quarantine rows must not be written into canonical table"
    ],
    "recommendation": recommendation
}
execution_gate_json.write_text(json.dumps(execution_gate, ensure_ascii=False, indent=2), encoding="utf-8")

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "recommendation": recommendation,
    "metrics": metrics,
    "artifacts": audit["artifacts"] | {
        "duplicate_audit_json": str(duplicate_audit_json),
        "execution_gate_json": str(execution_gate_json)
    },
    "next_step": next_step
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
