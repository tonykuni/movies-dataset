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
import json, hashlib
from pathlib import Path
from datetime import datetime
import pandas as pd

unique_source = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_v027842_20260611_013908\\preview\\VDF_AkShare_DuplicateRepair_UniqueFinalRows_v027842.csv")
quarantine_source = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_DUPLICATE_REPAIR_REVIEW_GATE_v027842_20260611_013908\\preview\\VDF_AkShare_DuplicateRepair_DuplicateQuarantineRows_v027842.csv")
final_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\preview\\VDF_AkShare_v0279_ReadinessFinalRows.csv")
final_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\preview\\VDF_AkShare_v0279_ReadinessFinalRows.json")
quarantine_copy_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\preview\\VDF_AkShare_v0279_DuplicateQuarantineRows.csv")
schema_audit_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\registry\\VDF_AkShare_v0279_SchemaAudit.csv")
key_audit_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\registry\\VDF_AkShare_v0279_KeyAudit.csv")
readiness_seal_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\plan\\VDF_AkShare_v0279_ExecutionReadinessSeal.json")
next_plan_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\plan\\VDF_AkShare_v0280_NextActionPlan.json")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\runtime\\vdf_akshare_execution_readiness_review_result_v0279.json")

for p in [final_csv, final_json, quarantine_copy_csv, schema_audit_csv, key_audit_csv, readiness_seal_json, next_plan_json, out_json]:
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

df = read_csv(unique_source)
q = read_csv(quarantine_source)

required = ["family","symbol","date","value","source","canonical_key","is_valid","invalid_reasons"]

for c in required:
    if c not in df.columns:
        df[c] = ""

schema_rows = []
for c in required:
    blank_count = int((df[c].astype(str).str.strip() == "").sum()) if c in df.columns else len(df)
    schema_rows.append({
        "field": c,
        "exists": c in df.columns,
        "blank_count": blank_count,
        "row_count": int(len(df)),
        "status": "OK" if c in df.columns and blank_count == 0 and c != "invalid_reasons" else ("OK_OPTIONAL_BLANK" if c == "invalid_reasons" else "WARN")
    })

duplicate_after = int(df.duplicated(subset=["canonical_key"], keep=False).sum()) if not df.empty else 0
still_invalid = int((df["is_valid"].astype(str).str.lower().isin(["false","0","no"])).sum()) if "is_valid" in df.columns else len(df)
empty_key = int((df["canonical_key"].astype(str).str.strip() == "").sum()) if "canonical_key" in df.columns else len(df)

key_audit = [
    {"metric":"unique_final_rows","value":int(len(df))},
    {"metric":"duplicate_quarantine_rows","value":int(len(q))},
    {"metric":"duplicate_after_review","value":duplicate_after},
    {"metric":"still_invalid_rows","value":still_invalid},
    {"metric":"empty_canonical_key_rows","value":empty_key}
]

df["_vdf_v0279_readiness_policy"] = "REVIEW_ONLY_NO_DB_WRITE_NO_CANONICAL_MERGE"
df["_vdf_v0279_source_stage"] = "v027842_unique_final"
q["_vdf_v0279_quarantine_policy"] = "DUPLICATE_QUARANTINE_NOT_CANONICAL_WRITE_ELIGIBLE"

df.to_csv(final_csv, index=False, encoding="utf-8-sig")
df.to_json(final_json, orient="records", force_ascii=False, indent=2)
q.to_csv(quarantine_copy_csv, index=False, encoding="utf-8-sig")
pd.DataFrame(schema_rows).to_csv(schema_audit_csv, index=False, encoding="utf-8-sig")
pd.DataFrame(key_audit).to_csv(key_audit_csv, index=False, encoding="utf-8-sig")

metrics = {
    "unique_final_rows": int(len(df)),
    "duplicate_quarantine_rows": int(len(q)),
    "duplicate_after_review": duplicate_after,
    "still_invalid_rows": still_invalid,
    "empty_canonical_key_rows": empty_key,
    "schema_warn_count": int(sum(1 for x in schema_rows if str(x["status"]).startswith("WARN")))
}

if metrics["unique_final_rows"] > 0 and metrics["duplicate_after_review"] == 0 and metrics["still_invalid_rows"] == 0 and metrics["empty_canonical_key_rows"] == 0:
    status = "VDF_AKSHARE_EXECUTION_READINESS_REVIEW_READY_WITH_QUARANTINE"
    risk = "MEDIUM" if metrics["duplicate_quarantine_rows"] > 0 else "LOW"
    recommendation = "ALLOW_V0280_FREEZE_SEAL_REVIEW_ONLY_NO_DB_WRITE"
    next_step = "v028.0 freeze seal review only; no DB write"
else:
    status = "VDF_AKSHARE_EXECUTION_READINESS_REVIEW_BLOCKED"
    risk = "HIGH"
    recommendation = "BLOCK_V0280_UNTIL_READINESS_DEFECTS_REPAIRED"
    next_step = "repair readiness defects; no DB write"

seal = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "policy": {
        "review_only": True,
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "freeze_seal_allowed_next": status.endswith("WITH_QUARANTINE") or status.endswith("READY"),
        "duplicate_quarantine_must_not_write": True
    },
    "metrics": metrics,
    "artifacts": {
        "readiness_final_csv": str(final_csv),
        "readiness_final_json": str(final_json),
        "duplicate_quarantine_csv": str(quarantine_copy_csv),
        "schema_audit_csv": str(schema_audit_csv),
        "key_audit_csv": str(key_audit_csv)
    },
    "hashes": {
        "readiness_final_csv_sha256": sha256_file(final_csv),
        "readiness_final_json_sha256": sha256_file(final_json),
        "duplicate_quarantine_csv_sha256": sha256_file(quarantine_copy_csv)
    },
    "recommendation": recommendation,
    "next_step": next_step
}
readiness_seal_json.write_text(json.dumps(seal, ensure_ascii=False, indent=2), encoding="utf-8")

next_plan = {
    "generated_at": datetime.now().isoformat(),
    "stage": "v028.0",
    "title": "Freeze seal review only",
    "allowed": status != "VDF_AKSHARE_EXECUTION_READINESS_REVIEW_BLOCKED",
    "rules": [
        "No DATABASE write",
        "No canonical merge",
        "Freeze readiness artifacts",
        "Preserve duplicate quarantine",
        "Only after user explicit approval may a later write-stage be designed"
    ],
    "inputs": {
        "readiness_final_csv": str(final_csv),
        "duplicate_quarantine_csv": str(quarantine_copy_csv),
        "readiness_seal_json": str(readiness_seal_json)
    }
}
next_plan_json.write_text(json.dumps(next_plan, ensure_ascii=False, indent=2), encoding="utf-8")

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "recommendation": recommendation,
    "metrics": metrics,
    "artifacts": seal["artifacts"] | {
        "readiness_seal_json": str(readiness_seal_json),
        "next_plan_json": str(next_plan_json)
    },
    "next_step": next_step
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
