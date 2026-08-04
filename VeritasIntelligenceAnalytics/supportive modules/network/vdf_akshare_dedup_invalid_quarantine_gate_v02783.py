import json
from pathlib import Path
from datetime import datetime
import pandas as pd

preview_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_NARROW_SOURCE_FILELIST_CANONICALIZER_v027822_20260611_004445\\preview\\VDF_AkShare_NarrowSource_ContractDryRunPreview_Canonicalizer_v027822.csv")
valid_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\preview\\VDF_AkShare_DedupGate_ValidRows_v02783.csv")
invalid_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\preview\\VDF_AkShare_DedupGate_InvalidQuarantineRows_v02783.csv")
duplicate_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\preview\\VDF_AkShare_DedupGate_DuplicateRows_v02783.csv")
deduped_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\preview\\VDF_AkShare_DedupGate_DedupedValidRows_v02783.csv")
deduped_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\preview\\VDF_AkShare_DedupGate_DedupedValidRows_v02783.json")
rootcause_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\registry\\VDF_AkShare_DedupGate_InvalidRootCause_v02783.csv")
dedup_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\registry\\VDF_AkShare_DedupGate_Audit_v02783.json")
quarantine_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\plan\\VDF_AkShare_InvalidQuarantineRepairPlan_v02783.json")
execution_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\plan\\VDF_AkShare_PostDedupExecutionGateReview_v02783.json")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_v02783_20260611_012926\\runtime\\vdf_akshare_dedup_invalid_quarantine_gate_result_v02783.json")

for p in [valid_csv, invalid_csv, duplicate_csv, deduped_csv, deduped_json, rootcause_csv, dedup_audit_json, quarantine_plan_json, execution_gate_json, out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(preview_csv, dtype=str, encoding="utf-8-sig").fillna("")

for col in ["family", "symbol", "date", "value", "source", "canonical_key", "is_valid", "invalid_reasons"]:
    if col not in df.columns:
        df[col] = ""

def truthy(x):
    return str(x).strip().lower() in {"true","1","yes","y"}

valid_df = df[df["is_valid"].map(truthy)].copy()
invalid_df = df[~df["is_valid"].map(truthy)].copy()

if not valid_df.empty:
    dup_mask = valid_df.duplicated(subset=["canonical_key"], keep=False)
    duplicate_df = valid_df[dup_mask].copy()
    deduped_df = valid_df.drop_duplicates(subset=["canonical_key"], keep="first").copy()
else:
    duplicate_df = pd.DataFrame(columns=df.columns)
    deduped_df = valid_df.copy()

valid_df.to_csv(valid_csv, index=False, encoding="utf-8-sig")
invalid_df.to_csv(invalid_csv, index=False, encoding="utf-8-sig")
duplicate_df.to_csv(duplicate_csv, index=False, encoding="utf-8-sig")
deduped_df.to_csv(deduped_csv, index=False, encoding="utf-8-sig")
deduped_df.to_json(deduped_json, orient="records", force_ascii=False, indent=2)

causes = []
for cause in ["symbol_blank","date_blank_or_unparseable","value_blank_or_non_numeric","source_blank"]:
    if invalid_df.empty:
        cnt = 0
    else:
        cnt = int(invalid_df["invalid_reasons"].astype(str).str.contains(cause, regex=False).sum())
    causes.append({"cause": cause, "count": cnt})
causes.append({"cause": "duplicate_key_valid_rows", "count": int(len(duplicate_df))})
pd.DataFrame(causes).to_csv(rootcause_csv, index=False, encoding="utf-8-sig")

metrics = {
    "input_rows": int(len(df)),
    "valid_rows": int(len(valid_df)),
    "invalid_quarantine_rows": int(len(invalid_df)),
    "duplicate_rows": int(len(duplicate_df)),
    "deduped_valid_rows": int(len(deduped_df)),
    "invalid_after": int(len(invalid_df)),
    "duplicate_after": int(len(duplicate_df))
}

if metrics["duplicate_after"] == 0 and metrics["valid_rows"] > 0 and metrics["invalid_after"] == 0:
    status = "VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_READY"
    risk = "LOW"
    recommendation = "ALLOW_V0279_EXECUTION_READINESS_REVIEW_ONLY_NO_DB_WRITE"
elif metrics["duplicate_after"] == 0 and metrics["valid_rows"] > 0 and metrics["invalid_after"] > 0:
    status = "VDF_AKSHARE_DEDUP_GATE_READY_WITH_INVALID_QUARANTINE"
    risk = "MEDIUM"
    recommendation = "ALLOW_V02784_INVALID_MAPPING_REPAIR_GATE_NO_DB_WRITE"
elif metrics["valid_rows"] > 0:
    status = "VDF_AKSHARE_DEDUP_GATE_READY_WITH_DEDUP_REVIEW"
    risk = "MEDIUM"
    recommendation = "ALLOW_V027831_DEDUP_REPAIR_GATE_NO_DB_WRITE"
else:
    status = "VDF_AKSHARE_DEDUP_INVALID_QUARANTINE_GATE_BLOCKED"
    risk = "HIGH"
    recommendation = "BLOCK_NEXT_UNTIL_SOURCE_MAPPING_REVIEW"

audit = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "policy": {
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "invalid_rows_quarantined": True,
        "dedup_preview_only": True
    },
    "metrics": metrics,
    "artifacts": {
        "valid_csv": str(valid_csv),
        "invalid_quarantine_csv": str(invalid_csv),
        "duplicate_csv": str(duplicate_csv),
        "deduped_valid_csv": str(deduped_csv),
        "deduped_valid_json": str(deduped_json),
        "rootcause_csv": str(rootcause_csv)
    },
    "recommendation": recommendation,
    "next_step": "v027.8.4 invalid mapping repair gate only; no DB write" if metrics["invalid_after"] > 0 else "v027.9 execution readiness review only; no DB write"
}
dedup_audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

quarantine_plan = {
    "generated_at": datetime.now().isoformat(),
    "status": "INVALID_QUARANTINE_REPAIR_PLAN_READY" if metrics["invalid_after"] > 0 else "NO_INVALID_REPAIR_REQUIRED",
    "risk": "MEDIUM" if metrics["invalid_after"] > 0 else "LOW",
    "invalid_rows": metrics["invalid_after"],
    "repair_order": [
        "Inspect invalid_quarantine_csv.",
        "Group by invalid_reasons.",
        "Fix value/date mapping only; do not change valid rows.",
        "Re-run v027.8.4 invalid mapping repair gate.",
        "Only then run v027.9 execution readiness review."
    ],
    "policy": {
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "preserve_valid_rows": True
    }
}
quarantine_plan_json.write_text(json.dumps(quarantine_plan, ensure_ascii=False, indent=2), encoding="utf-8")

execution_gate = {
    "generated_at": datetime.now().isoformat(),
    "status": "EXECUTION_GATE_CLOSED_INVALID_QUARANTINE" if metrics["invalid_after"] > 0 else ("EXECUTION_GATE_READY_FOR_REVIEW" if metrics["duplicate_after"] == 0 and metrics["valid_rows"] > 0 else "EXECUTION_GATE_CLOSED_DEDUP_REVIEW"),
    "risk": risk,
    "allowed_to_write_database": False,
    "allowed_to_merge_canonical": False,
    "metrics": metrics,
    "hard_stop": [
        "No DB write in v027.8.3",
        "No canonical merge in v027.8.3",
        "Execution readiness requires invalid_after=0 and duplicate_after=0"
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
        "dedup_audit_json": str(dedup_audit_json),
        "quarantine_plan_json": str(quarantine_plan_json),
        "execution_gate_json": str(execution_gate_json)
    },
    "next_step": audit["next_step"]
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
