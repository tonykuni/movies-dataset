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

readiness_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\preview\\VDF_AkShare_v0279_ReadinessFinalRows.csv")
quarantine_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_EXECUTION_READINESS_REVIEW_v0279_20260611_020210\\preview\\VDF_AkShare_v0279_DuplicateQuarantineRows.csv")
manifest_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_FREEZE_SEAL_REVIEW_v0280_20260611_020645\\registry\\VDF_AkShare_v0280_FrozenArtifactManifest.json")
freeze_seal_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_FREEZE_SEAL_REVIEW_v0280_20260611_020645\\plan\\VDF_AkShare_v0280_FreezeSeal.json")
freeze_seal_copy_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_FREEZE_SEAL_v0280_20260611_020645\\VDF_AkShare_v0280_FreezeSeal.json")
freeze_index_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_AKSHARE_FREEZE_SEAL_v0280_20260611_020645\\VDF_AkShare_v0280_FreezeIndex.json")
next_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_FREEZE_SEAL_REVIEW_v0280_20260611_020645\\plan\\VDF_AkShare_v0281_NextGatePlan.json")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_FREEZE_SEAL_REVIEW_v0280_20260611_020645\\runtime\\vdf_akshare_freeze_seal_review_result_v0280.json")

for p in [freeze_seal_json, freeze_seal_copy_json, freeze_index_json, next_gate_json, out_json]:
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

r = read_csv(readiness_csv)
q = read_csv(quarantine_csv)

for c in ["canonical_key","is_valid","family","symbol","date","value","source"]:
    if c not in r.columns:
        r[c] = ""

metrics = {
    "readiness_final_rows": int(len(r)),
    "duplicate_quarantine_rows": int(len(q)),
    "duplicate_after_freeze_check": int(r.duplicated(subset=["canonical_key"], keep=False).sum()) if not r.empty else 0,
    "still_invalid_rows": int((r["is_valid"].astype(str).str.lower().isin(["false","0","no"])).sum()) if "is_valid" in r.columns else len(r),
    "empty_canonical_key_rows": int((r["canonical_key"].astype(str).str.strip() == "").sum()) if "canonical_key" in r.columns else len(r),
    "empty_value_rows": int((r["value"].astype(str).str.strip() == "").sum()) if "value" in r.columns else len(r)
}

status = "VDF_AKSHARE_FREEZE_SEAL_REVIEW_READY_WITH_QUARANTINE"
risk = "MEDIUM"
recommendation = "ALLOW_V0281_USER_APPROVAL_GATE_FOR_WRITE_STAGE_DESIGN_NO_DB_WRITE"

if metrics["readiness_final_rows"] <= 0 or metrics["duplicate_after_freeze_check"] > 0 or metrics["still_invalid_rows"] > 0 or metrics["empty_canonical_key_rows"] > 0:
    status = "VDF_AKSHARE_FREEZE_SEAL_REVIEW_BLOCKED"
    risk = "HIGH"
    recommendation = "BLOCK_V0281_UNTIL_FREEZE_DEFECTS_REPAIRED"

artifact_manifest = json.loads(Path(manifest_json).read_text(encoding="utf-8"))

seal = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "policy": {
        "freeze_only": True,
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "duplicate_quarantine_preserved": True,
        "write_stage_requires_explicit_user_approval": True
    },
    "metrics": metrics,
    "hashes": {
        "readiness_final_csv_sha256": sha256_file(readiness_csv),
        "duplicate_quarantine_csv_sha256": sha256_file(quarantine_csv)
    },
    "artifact_manifest": artifact_manifest,
    "recommendation": recommendation,
    "next_step": "v028.1 user approval gate for write-stage design only; no DB write" if risk != "HIGH" else "repair freeze defects; no DB write"
}

freeze_seal_json.write_text(json.dumps(seal, ensure_ascii=False, indent=2), encoding="utf-8")
freeze_seal_copy_json.write_text(json.dumps(seal, ensure_ascii=False, indent=2), encoding="utf-8")

freeze_index = {
    "generated_at": datetime.now().isoformat(),
    "title": "VDF AkShare Freeze Seal v028.0",
    "status": status,
    "risk": risk,
    "readiness_final_rows": metrics["readiness_final_rows"],
    "duplicate_quarantine_rows": metrics["duplicate_quarantine_rows"],
    "seal": str(freeze_seal_copy_json),
    "policy": seal["policy"]
}
freeze_index_json.write_text(json.dumps(freeze_index, ensure_ascii=False, indent=2), encoding="utf-8")

next_gate = {
    "generated_at": datetime.now().isoformat(),
    "stage": "v028.1",
    "title": "User approval gate for write-stage design only",
    "allowed": risk != "HIGH",
    "still_no_db_write": True,
    "still_no_canonical_merge": True,
    "required_user_approval_before_write_stage": True,
    "candidate_write_inputs": {
        "readiness_final_rows": metrics["readiness_final_rows"],
        "duplicate_quarantine_rows": metrics["duplicate_quarantine_rows"]
    },
    "rules": [
        "v028.1 may design write-stage only; no write.",
        "duplicate quarantine must remain excluded.",
        "write-stage must create backup, dry-run compare, and rollback plan.",
        "actual DB write requires separate explicit approval."
    ]
}
next_gate_json.write_text(json.dumps(next_gate, ensure_ascii=False, indent=2), encoding="utf-8")

result = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "recommendation": recommendation,
    "metrics": metrics,
    "artifacts": {
        "freeze_seal_json": str(freeze_seal_json),
        "freeze_seal_copy_json": str(freeze_seal_copy_json),
        "freeze_index_json": str(freeze_index_json),
        "next_gate_json": str(next_gate_json)
    },
    "next_step": seal["next_step"]
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
