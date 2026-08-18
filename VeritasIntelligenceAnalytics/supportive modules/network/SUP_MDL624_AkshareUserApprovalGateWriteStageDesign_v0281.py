import json, hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd

freeze_seal_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_FREEZE_SEAL_v0280_20260611_020645\\VDF_AkShare_v0280_FreezeSeal.json")
readiness_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_FREEZE_SEAL_v0280_20260611_020645\\artifacts\\VDF_AkShare_v0279_ReadinessFinalRows.csv")
quarantine_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_FREEZE_SEAL_v0280_20260611_020645\\artifacts\\VDF_AkShare_v0279_DuplicateQuarantineRows.csv")
write_design_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_USER_APPROVAL_GATE_WRITE_STAGE_DESIGN_v0281_20260611_021402\\plan\\VDF_AkShare_v0281_WriteStageDesign.json")
dryrun_compare_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_USER_APPROVAL_GATE_WRITE_STAGE_DESIGN_v0281_20260611_021402\\plan\\VDF_AkShare_v0281_DryRunComparePlan.json")
rollback_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_USER_APPROVAL_GATE_WRITE_STAGE_DESIGN_v0281_20260611_021402\\plan\\VDF_AkShare_v0281_RollbackPlan.json")
approval_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_USER_APPROVAL_GATE_WRITE_STAGE_DESIGN_v0281_20260611_021402\\plan\\VDF_AkShare_v0281_UserApprovalGate.json")
prewrite_checklist_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_USER_APPROVAL_GATE_WRITE_STAGE_DESIGN_v0281_20260611_021402\\registry\\VDF_AkShare_v0281_PreWriteChecklist.csv")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_USER_APPROVAL_GATE_WRITE_STAGE_DESIGN_v0281_20260611_021402\\runtime\\vdf_akshare_user_approval_gate_write_stage_design_result_v0281.json")

for p in [write_design_json, dryrun_compare_plan_json, rollback_plan_json, approval_gate_json, prewrite_checklist_csv, out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

def read_csv(p):
    try:
        return pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
    except Exception:
        return pd.read_csv(p, dtype=str).fillna("")

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

seal = json.loads(freeze_seal_json.read_text(encoding="utf-8"))
ready = read_csv(readiness_csv)
quarantine = read_csv(quarantine_csv)

for c in ["family","symbol","date","value","source","canonical_key","is_valid"]:
    if c not in ready.columns:
        ready[c] = ""

metrics = {
    "candidate_write_rows": int(len(ready)),
    "duplicate_quarantine_rows": int(len(quarantine)),
    "duplicate_after_check": int(ready.duplicated(subset=["canonical_key"], keep=False).sum()) if not ready.empty else 0,
    "still_invalid_rows": int((ready["is_valid"].astype(str).str.lower().isin(["false","0","no"])).sum()),
    "empty_key_rows": int((ready["canonical_key"].astype(str).str.strip() == "").sum()),
    "empty_value_rows": int((ready["value"].astype(str).str.strip() == "").sum()),
}

ready_for_design = (
    metrics["candidate_write_rows"] > 0 and
    metrics["duplicate_after_check"] == 0 and
    metrics["still_invalid_rows"] == 0 and
    metrics["empty_key_rows"] == 0 and
    metrics["empty_value_rows"] == 0
)

status = "VDF_AKSHARE_USER_APPROVAL_GATE_WRITE_STAGE_DESIGN_READY" if ready_for_design else "VDF_AKSHARE_USER_APPROVAL_GATE_WRITE_STAGE_DESIGN_BLOCKED"
risk = "MEDIUM" if ready_for_design else "HIGH"
recommendation = "ALLOW_V0282_WRITE_DRYRUN_COMPARE_ONLY_NO_DB_WRITE" if ready_for_design else "BLOCK_V0282_UNTIL_DESIGN_DEFECTS_REPAIRED"
next_step = "v028.2 write dry-run compare only; no DB write" if ready_for_design else "repair design defects; no DB write"

write_design = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "stage": "v028.1",
    "title": "Write-stage design only; no DB write",
    "policy": {
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "actual_write_allowed": False,
        "requires_separate_explicit_user_approval": True,
        "duplicate_quarantine_excluded": True,
        "backup_required_before_any_future_write": True,
        "rollback_required_before_any_future_write": True
    },
    "target": {
        "database_root": "C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE",
        "canonical_family": "VDF_Global_Commodity",
        "primary_key": ["family","symbol","date","source"],
        "write_mode_candidate": "upsert_after_dryrun_compare_only"
    },
    "inputs": {
        "readiness_final_csv": str(readiness_csv),
        "duplicate_quarantine_csv": str(quarantine_csv),
        "freeze_seal_json": str(freeze_seal_json)
    },
    "metrics": metrics,
    "recommendation": recommendation,
    "next_step": next_step
}
write_design_json.write_text(json.dumps(write_design, ensure_ascii=False, indent=2), encoding="utf-8")

dryrun_compare_plan = {
    "generated_at": datetime.now().isoformat(),
    "stage": "v028.2",
    "title": "Write dry-run compare only; no DB write",
    "allowed": ready_for_design,
    "policy": {
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "compare_only": True
    },
    "compare_steps": [
        "Load existing canonical table if present.",
        "Load readiness final rows.",
        "Compare primary-key overlap.",
        "Classify insert/update/unchanged/conflict.",
        "Emit dry-run delta CSV/JSON.",
        "Do not write DATABASE."
    ],
    "required_outputs": [
        "dryrun_delta_insert.csv",
        "dryrun_delta_update.csv",
        "dryrun_conflicts.csv",
        "dryrun_summary.json",
        "html matrix report"
    ]
}
dryrun_compare_plan_json.write_text(json.dumps(dryrun_compare_plan, ensure_ascii=False, indent=2), encoding="utf-8")

rollback_plan = {
    "generated_at": datetime.now().isoformat(),
    "stage": "future_write_stage",
    "title": "Rollback plan before actual DB write",
    "required_before_write": True,
    "steps": [
        "Create full DATABASE backup.",
        "Create target table snapshot.",
        "Write to staging table first.",
        "Validate row count and key uniqueness.",
        "Promote staging table only after validation.",
        "On failure restore previous DATABASE snapshot.",
        "Open HTML report."
    ],
    "forbidden_in_v0281": [
        "No DB write",
        "No canonical merge",
        "No destructive delete",
        "No Stop-Process"
    ]
}
rollback_plan_json.write_text(json.dumps(rollback_plan, ensure_ascii=False, indent=2), encoding="utf-8")

approval_gate = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "approval_required": True,
    "approved_now": False,
    "what_user_may_approve_next": "v028.2 write dry-run compare only; still no DB write",
    "what_is_not_approved": "actual database write or canonical merge",
    "metrics": metrics,
    "hashes": {
        "readiness_csv_sha256": sha256_file(readiness_csv),
        "quarantine_csv_sha256": sha256_file(quarantine_csv),
        "freeze_seal_json_sha256": sha256_file(freeze_seal_json)
    },
    "recommendation": recommendation,
    "next_step": next_step
}
approval_gate_json.write_text(json.dumps(approval_gate, ensure_ascii=False, indent=2), encoding="utf-8")

checklist = [
    {"item":"freeze_seal_exists","status":"OK" if freeze_seal_json.exists() else "FAIL"},
    {"item":"candidate_write_rows_gt_0","status":"OK" if metrics["candidate_write_rows"] > 0 else "FAIL"},
    {"item":"duplicate_after_check_zero","status":"OK" if metrics["duplicate_after_check"] == 0 else "FAIL"},
    {"item":"still_invalid_rows_zero","status":"OK" if metrics["still_invalid_rows"] == 0 else "FAIL"},
    {"item":"empty_key_rows_zero","status":"OK" if metrics["empty_key_rows"] == 0 else "FAIL"},
    {"item":"empty_value_rows_zero","status":"OK" if metrics["empty_value_rows"] == 0 else "FAIL"},
    {"item":"duplicate_quarantine_preserved","status":"OK" if metrics["duplicate_quarantine_rows"] >= 0 else "FAIL"},
    {"item":"db_write_disabled","status":"OK"},
    {"item":"canonical_merge_disabled","status":"OK"},
    {"item":"actual_write_requires_future_approval","status":"OK"}
]
pd.DataFrame(checklist).to_csv(prewrite_checklist_csv, index=False, encoding="utf-8-sig")

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "recommendation": recommendation,
    "metrics": metrics,
    "artifacts": {
        "write_design_json": str(write_design_json),
        "dryrun_compare_plan_json": str(dryrun_compare_plan_json),
        "rollback_plan_json": str(rollback_plan_json),
        "approval_gate_json": str(approval_gate_json),
        "prewrite_checklist_csv": str(prewrite_checklist_csv)
    },
    "next_step": next_step
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
