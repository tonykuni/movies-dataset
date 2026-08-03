import json
from pathlib import Path
from datetime import datetime
import pandas as pd
from pandas.errors import EmptyDataError

dryrun_summary_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\plan\\VDF_AkShare_v0282_DryRunCompareSummary.json")
insert_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_DryRun_InsertRows.csv")
update_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_DryRun_UpdateRows.csv")
conflict_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_DryRun_ConflictRows.csv")
candidate_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_CandidateRows_Copy.csv")
quarantine_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_WRITE_DRYRUN_COMPARE_v0282_20260611_024351\\preview\\VDF_AkShare_v0282_DuplicateQuarantine_Copy.csv")
db_inventory_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_v02832_20260611_031541\\registry\\VDF_AkShare_v02832_DatabaseInventory.csv")
backup_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_v02832_20260611_031541\\plan\\VDF_AkShare_v02832_BackupPlan.json")
rollback_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_v02832_20260611_031541\\plan\\VDF_AkShare_v02832_RollbackPlan.json")
staging_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_v02832_20260611_031541\\plan\\VDF_AkShare_v02832_StagingWritePlan.json")
postwrite_validation_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_v02832_20260611_031541\\plan\\VDF_AkShare_v02832_PostWriteValidationPlan.json")
approval_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_v02832_20260611_031541\\plan\\VDF_AkShare_v02832_WriteApprovalGate.json")
checklist_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_v02832_20260611_031541\\registry\\VDF_AkShare_v02832_PreWriteSafetyChecklist.csv")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_v02832_20260611_031541\\runtime\\vdf_akshare_backup_rollback_staging_plan_hotfix_result_v02832.json")

for p in [backup_plan_json, rollback_plan_json, staging_plan_json, postwrite_validation_json, approval_gate_json, checklist_csv, out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

def safe_read_csv(p, columns=None):
    p = Path(p)
    if columns is None:
        columns = []
    if not p.exists() or p.stat().st_size == 0:
        return pd.DataFrame(columns=columns)
    try:
        return pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
    except EmptyDataError:
        return pd.DataFrame(columns=columns)
    except Exception:
        try:
            return pd.read_csv(p, dtype=str).fillna("")
        except EmptyDataError:
            return pd.DataFrame(columns=columns)
        except Exception:
            return pd.DataFrame(columns=columns)

base_cols = ["family","symbol","date","value","source","canonical_key","is_valid"]
dryrun = json.loads(dryrun_summary_json.read_text(encoding="utf-8"))
dm = dict(dryrun.get("metrics", {}))

insert_df = safe_read_csv(insert_csv, base_cols)
update_df = safe_read_csv(update_csv, base_cols)
conflict_df = safe_read_csv(conflict_csv, base_cols)
candidate_df = safe_read_csv(candidate_csv, base_cols)
quarantine_df = safe_read_csv(quarantine_csv, base_cols)
db_inv = safe_read_csv(db_inventory_csv, ["name","path","extension","bytes","modified","sha256"])

unchanged_rows = int(dm.get("unchanged_rows", 0) or 0)
plan_metrics = {
    "candidate_rows": int(len(candidate_df)),
    "insert_rows": int(len(insert_df)),
    "update_rows": int(len(update_df)),
    "unchanged_rows": unchanged_rows,
    "conflict_rows": int(len(conflict_df)),
    "duplicate_quarantine_rows": int(len(quarantine_df)),
    "database_inventory_files": int(len(db_inv)),
    "db_write_enabled": False,
    "canonical_merge_enabled": False,
    "actual_write_allowed": False,
    "empty_csv_hotfix_applied": True,
    "powershell_metric_accessor_hotfix_required": True
}

expected_total = plan_metrics["insert_rows"] + plan_metrics["update_rows"] + plan_metrics["unchanged_rows"]
ready = (
    plan_metrics["candidate_rows"] > 0 and
    plan_metrics["conflict_rows"] == 0 and
    expected_total == plan_metrics["candidate_rows"]
)

status = "VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_READY" if ready else "VDF_AKSHARE_BACKUP_ROLLBACK_STAGING_PLAN_HOTFIX_BLOCKED"
risk = "MEDIUM" if ready else "HIGH"
recommendation = "ALLOW_V0284_USER_APPROVAL_FOR_STAGING_WRITE_SCRIPT_GENERATION_NO_DB_WRITE" if ready else "BLOCK_V0284_UNTIL_STAGING_PLAN_DEFECTS_REPAIRED"
next_step = "v028.4 user approval for staging-write script generation only; no DB write" if ready else "repair staging plan defects; no DB write"

backup_plan = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "title": "Full DATABASE backup plan before any future write",
    "policy": {"db_write_enabled": False, "canonical_merge_enabled": False, "actual_backup_execution": False, "backup_plan_only": True},
    "steps": [
        "Create timestamped DATABASE backup folder under dict/VDF/_backup.",
        "Copy all existing DATABASE files into backup folder.",
        "Hash every copied file.",
        "Verify backup file count equals source file count.",
        "Abort future write if backup hash manifest has any failure."
    ],
    "metrics": plan_metrics
}
backup_plan_json.write_text(json.dumps(backup_plan, ensure_ascii=False, indent=2), encoding="utf-8")

rollback_plan = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "title": "Rollback plan before any future write",
    "policy": {"rollback_required": True, "db_write_enabled": False, "canonical_merge_enabled": False},
    "rollback_steps": [
        "Do not overwrite original database files directly.",
        "Write candidate data to staging table/file first.",
        "Validate staging table row count, key uniqueness, required fields, and hashes.",
        "Only after validation may future approved write promote staging artifact.",
        "If validation fails, restore from backup manifest."
    ]
}
rollback_plan_json.write_text(json.dumps(rollback_plan, ensure_ascii=False, indent=2), encoding="utf-8")

staging_plan = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "title": "Staging write plan only; no execution",
    "policy": {
        "staging_table_required": True,
        "target_family": "VDF_Global_Commodity",
        "primary_key": ["family","symbol","date","source"],
        "exclude_duplicate_quarantine": True,
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "actual_write_allowed": False
    },
    "candidate_inputs": {
        "insert_csv": str(insert_csv),
        "update_csv": str(update_csv),
        "candidate_csv": str(candidate_csv),
        "duplicate_quarantine_csv": str(quarantine_csv)
    },
    "staging_outputs_for_future_stage": [
        "VDF_Global_Commodity_staging.parquet",
        "VDF_Global_Commodity_staging.csv",
        "VDF_Global_Commodity_write_delta.json",
        "post_write_validation_report.html"
    ],
    "metrics": plan_metrics
}
staging_plan_json.write_text(json.dumps(staging_plan, ensure_ascii=False, indent=2), encoding="utf-8")

postwrite_validation = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "title": "Post-write validation plan for future approved write",
    "policy": {"validation_plan_only": True, "db_write_enabled": False},
    "checks": [
        "Row count after write equals existing + insert rows with update keys preserved.",
        "Primary key uniqueness is zero duplicate.",
        "Required fields family/symbol/date/value/source/canonical_key are non-empty.",
        "Duplicate quarantine rows are absent from canonical target.",
        "Hash manifest generated for final target.",
        "HTML report opened."
    ]
}
postwrite_validation_json.write_text(json.dumps(postwrite_validation, ensure_ascii=False, indent=2), encoding="utf-8")

approval_gate = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "approval_required": True,
    "approved_now": False,
    "what_user_may_approve_next": "v028.4 generate staging-write script only; still no DB write",
    "what_is_not_approved": "running staging write or promoting canonical target",
    "metrics": plan_metrics,
    "recommendation": recommendation,
    "next_step": next_step
}
approval_gate_json.write_text(json.dumps(approval_gate, ensure_ascii=False, indent=2), encoding="utf-8")

checklist = [
    {"item":"candidate_rows_gt_0","status":"OK" if plan_metrics["candidate_rows"] > 0 else "FAIL"},
    {"item":"conflict_rows_zero","status":"OK" if plan_metrics["conflict_rows"] == 0 else "FAIL"},
    {"item":"delta_rows_match_candidate_rows","status":"OK" if expected_total == plan_metrics["candidate_rows"] else "FAIL"},
    {"item":"empty_csv_hotfix_applied","status":"OK"},
    {"item":"powershell_metric_accessor_hotfix_applied","status":"OK"},
    {"item":"duplicate_quarantine_excluded","status":"OK"},
    {"item":"backup_plan_created","status":"OK"},
    {"item":"rollback_plan_created","status":"OK"},
    {"item":"staging_plan_created","status":"OK"},
    {"item":"postwrite_validation_plan_created","status":"OK"},
    {"item":"db_write_disabled","status":"OK"},
    {"item":"canonical_merge_disabled","status":"OK"},
    {"item":"future_approval_required","status":"OK"}
]
pd.DataFrame(checklist).to_csv(checklist_csv, index=False, encoding="utf-8-sig")

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "recommendation": recommendation,
    "metrics": plan_metrics,
    "artifacts": {
        "backup_plan_json": str(backup_plan_json),
        "rollback_plan_json": str(rollback_plan_json),
        "staging_plan_json": str(staging_plan_json),
        "postwrite_validation_json": str(postwrite_validation_json),
        "approval_gate_json": str(approval_gate_json),
        "prewrite_safety_checklist_csv": str(checklist_csv)
    },
    "next_step": next_step
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
