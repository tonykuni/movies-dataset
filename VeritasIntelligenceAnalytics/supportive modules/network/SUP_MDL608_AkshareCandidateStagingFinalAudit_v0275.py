import json
import hashlib
from pathlib import Path
from datetime import datetime

manifest_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\registry\\VDF_AkShare_CandidateSeedManifest_v0274.json")
staging_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\staging")
seed_result_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_SMALL_SCOPE_CANDIDATE_SEED_STAGING_v0274_20260610_145643\\runtime\\vdf_akshare_candidate_seed_staging_result_v0274.json")
candidate_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_v0275_20260610_150853\\registry\\VDF_AkShare_CandidateIntegrityAudit_v0275.json")
quarantine_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_v0275_20260610_150853\\registry\\VDF_AkShare_QuarantineAudit_v0275.json")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_v0275_20260610_150853\\runtime\\vdf_akshare_candidate_staging_final_audit_result_v0275.json")

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_READY",
    "risk": "LOW",
    "policy": "Final seal candidate staging only. No DATABASE write. No canonical merge.",
    "manifest_exists": False,
    "staging_dir_exists": False,
    "candidate_tables": {},
    "candidate_files_checked": 0,
    "candidate_rows_total": 0,
    "csv_json_parquet_groups": 0,
    "missing_files": [],
    "quarantine_notes": {},
    "seed_result": {},
    "recommendation": "UNKNOWN"
}

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

try:
    import pandas as pd

    if not manifest_path.exists():
        raise RuntimeError("Candidate manifest missing.")
    if not staging_dir.exists():
        raise RuntimeError("Candidate staging dir missing.")
    if not seed_result_path.exists():
        raise RuntimeError("Candidate seed result missing.")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    seed_result = json.loads(seed_result_path.read_text(encoding="utf-8"))

    result["manifest_exists"] = True
    result["staging_dir_exists"] = True
    result["seed_result"] = {
        "status": seed_result.get("status"),
        "risk": seed_result.get("risk"),
        "seed_plan_count": seed_result.get("seed_plan_count"),
        "attempt_count": seed_result.get("attempt_count"),
        "success_count": seed_result.get("success_count"),
        "fail_count": seed_result.get("fail_count"),
        "timeout_count": seed_result.get("timeout_count"),
        "total_rows_staged": seed_result.get("total_rows_staged"),
        "recommendation": seed_result.get("recommendation")
    }

    items = manifest.get("manifest_items", [])
    audit_items = []

    for item in items:
        table = item.get("target_table", "")
        expected_rows = int(item.get("rows") or 0)
        paths = {
            "csv": item.get("csv", ""),
            "json": item.get("json", ""),
            "parquet": item.get("parquet", "")
        }

        table_audit = {
            "target_table": table,
            "expected_rows": expected_rows,
            "csv_rows": None,
            "json_rows": None,
            "parquet_rows": None,
            "hashes": {},
            "all_files_exist": True,
            "row_counts_match": False,
            "risk": "LOW"
        }

        for ext, path_s in paths.items():
            if not path_s:
                if ext == "parquet":
                    continue
                result["missing_files"].append(f"{table}.{ext}")
                table_audit["all_files_exist"] = False
                table_audit["risk"] = "HIGH"
                continue

            p = Path(path_s)
            if not p.exists():
                result["missing_files"].append(str(p))
                table_audit["all_files_exist"] = False
                table_audit["risk"] = "HIGH"
                continue

            result["candidate_files_checked"] += 1
            table_audit["hashes"][ext] = sha256_file(p)

            if ext == "csv":
                df = pd.read_csv(p)
                table_audit["csv_rows"] = int(len(df))
            elif ext == "json":
                df = pd.read_json(p)
                table_audit["json_rows"] = int(len(df))
            elif ext == "parquet":
                df = pd.read_parquet(p)
                table_audit["parquet_rows"] = int(len(df))

        row_values = [
            table_audit.get("csv_rows"),
            table_audit.get("json_rows"),
            table_audit.get("parquet_rows")
        ]
        row_values = [x for x in row_values if x is not None]

        table_audit["row_counts_match"] = len(row_values) > 0 and len(set(row_values)) == 1 and row_values[0] == expected_rows

        if not table_audit["row_counts_match"]:
            table_audit["risk"] = "HIGH"

        result["candidate_tables"][table] = expected_rows
        result["candidate_rows_total"] += expected_rows
        result["csv_json_parquet_groups"] += 1
        audit_items.append(table_audit)

    quarantine = []
    for r in manifest.get("run_rows", []):
        if r.get("status") != "OK_STAGED":
            quarantine.append({
                "function": r.get("function"),
                "selected_category": r.get("selected_category"),
                "target_table": r.get("target_table"),
                "status": r.get("status"),
                "risk": r.get("risk"),
                "error": r.get("error")
            })

    result["quarantine_notes"] = {
        "quarantine_count": len(quarantine),
        "quarantine": quarantine
    }

    candidate_audit_json.parent.mkdir(parents=True, exist_ok=True)
    candidate_audit_json.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "policy": result["policy"],
        "candidate_tables": result["candidate_tables"],
        "candidate_rows_total": result["candidate_rows_total"],
        "audit_items": audit_items
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    quarantine_audit_json.parent.mkdir(parents=True, exist_ok=True)
    quarantine_audit_json.write_text(json.dumps({
        "generated_at": result["generated_at"],
        "policy": "Quarantine failed/timeout candidate seed functions. They must not enter canonical merge.",
        "quarantine_notes": result["quarantine_notes"]
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    failed_audits = [x for x in audit_items if x.get("risk") == "HIGH"]

    if result["candidate_rows_total"] <= 0:
        result["status"] = "VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_WITH_REVIEW"
        result["risk"] = "HIGH"
        result["recommendation"] = "BLOCK_NO_CANDIDATE_ROWS"
    elif failed_audits or result["missing_files"]:
        result["status"] = "VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_WITH_REVIEW"
        result["risk"] = "HIGH"
        result["recommendation"] = "BLOCK_CANDIDATE_FILE_OR_ROWCOUNT_MISMATCH"
    elif result["quarantine_notes"]["quarantine_count"] > 0:
        result["status"] = "VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_READY_WITH_QUARANTINE_NOTES"
        result["risk"] = "MEDIUM"
        result["recommendation"] = "ALLOW_V0276_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_ONLY"
    else:
        result["status"] = "VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_READY"
        result["risk"] = "LOW"
        result["recommendation"] = "ALLOW_V0276_CANDIDATE_TO_CANONICAL_MERGE_GATE_REVIEW_ONLY"

except Exception as e:
    result["status"] = "VDF_AKSHARE_CANDIDATE_STAGING_FINAL_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = str(e)
    result["recommendation"] = "BLOCK_FINAL_SEAL_REPAIR_CANDIDATE_STAGING"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "candidate_rows_total": result["candidate_rows_total"],
    "candidate_tables": result["candidate_tables"],
    "candidate_files_checked": result["candidate_files_checked"],
    "quarantine_count": result.get("quarantine_notes", {}).get("quarantine_count", 0),
    "missing_files": result["missing_files"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
