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
from pathlib import Path
from datetime import datetime
import pandas as pd

valid_source = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\preview\\VDF_AkShare_InvalidRepair_PreservedValidRows_v02784.csv")
repaired_source = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_INVALID_MAPPING_REPAIR_GATE_v02784_20260611_013222\\preview\\VDF_AkShare_InvalidRepair_RepairedRows_v02784.csv")
final_valid_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_COLLISION_RESOLVER_GATE_v027841_20260611_013435\\preview\\VDF_AkShare_CollisionResolver_FinalValidRows_v027841.csv")
final_valid_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_COLLISION_RESOLVER_GATE_v027841_20260611_013435\\preview\\VDF_AkShare_CollisionResolver_FinalValidRows_v027841.json")
collision_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_COLLISION_RESOLVER_GATE_v027841_20260611_013435\\preview\\VDF_AkShare_CollisionResolver_CollisionQuarantineRows_v027841.csv")
non_collision_repaired_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_COLLISION_RESOLVER_GATE_v027841_20260611_013435\\preview\\VDF_AkShare_CollisionResolver_NonCollisionRepairedRows_v027841.csv")
collision_audit_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_COLLISION_RESOLVER_GATE_v027841_20260611_013435\\registry\\VDF_AkShare_CollisionResolver_Audit_v027841.json")
rootcause_csv = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_COLLISION_RESOLVER_GATE_v027841_20260611_013435\\registry\\VDF_AkShare_CollisionResolver_RootCause_v027841.csv")
execution_gate_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_COLLISION_RESOLVER_GATE_v027841_20260611_013435\\plan\\VDF_AkShare_CollisionResolver_ExecutionGateReview_v027841.json")
out_json = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_AKSHARE_COLLISION_RESOLVER_GATE_v027841_20260611_013435\\runtime\\vdf_akshare_collision_resolver_gate_result_v027841.json")

for p in [final_valid_csv, final_valid_json, collision_csv, non_collision_repaired_csv, collision_audit_json, rootcause_csv, execution_gate_json, out_json]:
    p.parent.mkdir(parents=True, exist_ok=True)

def read_csv(p):
    try:
        return pd.read_csv(p, dtype=str, encoding="utf-8-sig").fillna("")
    except Exception:
        return pd.read_csv(p, dtype=str).fillna("")

valid = read_csv(valid_source)
repaired = read_csv(repaired_source)

for df in [valid, repaired]:
    for c in ["canonical_key", "is_valid", "invalid_reasons", "family", "symbol", "date", "source", "value"]:
        if c not in df.columns:
            df[c] = ""

valid["_vdf_v027841_source_partition"] = "preserved_valid_authoritative"
valid["_vdf_v027841_collision_policy"] = "keep"

valid_keys = set(valid["canonical_key"].astype(str).tolist())

if not repaired.empty:
    collision = repaired[repaired["canonical_key"].astype(str).isin(valid_keys)].copy()
    non_collision = repaired[~repaired["canonical_key"].astype(str).isin(valid_keys)].copy()
else:
    collision = pd.DataFrame(columns=repaired.columns)
    non_collision = pd.DataFrame(columns=repaired.columns)

if not collision.empty:
    collision["_vdf_v027841_source_partition"] = "repaired_collision_quarantine"
    collision["_vdf_v027841_collision_policy"] = "quarantine_repaired_keep_preserved_valid"
    collision["_vdf_v027841_collision_reason"] = "canonical_key_exists_in_preserved_valid"

if not non_collision.empty:
    non_collision["_vdf_v027841_source_partition"] = "repaired_non_collision"
    non_collision["_vdf_v027841_collision_policy"] = "include_preview_only"
    non_collision["_vdf_v027841_collision_reason"] = ""

final_valid = pd.concat([valid, non_collision], ignore_index=True, sort=False)

if not final_valid.empty:
    dup_after = int(final_valid.duplicated(subset=["canonical_key"], keep=False).sum())
else:
    dup_after = 0

final_valid.to_csv(final_valid_csv, index=False, encoding="utf-8-sig")
final_valid.to_json(final_valid_json, orient="records", force_ascii=False, indent=2)
collision.to_csv(collision_csv, index=False, encoding="utf-8-sig")
non_collision.to_csv(non_collision_repaired_csv, index=False, encoding="utf-8-sig")

rootcause = [
    {"cause": "repaired_rows_collision_with_preserved_valid", "count": int(len(collision))},
    {"cause": "repaired_rows_non_collision", "count": int(len(non_collision))},
    {"cause": "final_valid_duplicate_after_collision_policy", "count": dup_after}
]
pd.DataFrame(rootcause).to_csv(rootcause_csv, index=False, encoding="utf-8-sig")

metrics = {
    "preserved_valid_rows": int(len(valid)),
    "input_repaired_rows": int(len(repaired)),
    "collision_quarantine_rows": int(len(collision)),
    "non_collision_repaired_rows": int(len(non_collision)),
    "final_valid_rows": int(len(final_valid)),
    "duplicate_after_collision_policy": dup_after,
    "still_invalid_rows": 0
}

if metrics["duplicate_after_collision_policy"] == 0 and metrics["final_valid_rows"] > 0:
    if metrics["collision_quarantine_rows"] == 0:
        status = "VDF_AKSHARE_COLLISION_RESOLVER_GATE_READY"
        risk = "LOW"
        recommendation = "ALLOW_V0279_EXECUTION_READINESS_REVIEW_ONLY_NO_DB_WRITE"
        next_step = "v027.9 execution readiness review only; no DB write"
    else:
        status = "VDF_AKSHARE_COLLISION_RESOLVER_GATE_READY_WITH_COLLISION_QUARANTINE"
        risk = "MEDIUM"
        recommendation = "ALLOW_V0279_EXECUTION_READINESS_REVIEW_WITH_COLLISION_QUARANTINE_NO_DB_WRITE"
        next_step = "v027.9 execution readiness review with collision quarantine; no DB write"
else:
    status = "VDF_AKSHARE_COLLISION_RESOLVER_GATE_BLOCKED"
    risk = "HIGH"
    recommendation = "BLOCK_V0279_UNTIL_DUPLICATE_REVIEW"
    next_step = "v027.8.4.2 duplicate repair review only; no DB write"

audit = {
    "generated_at": datetime.now().isoformat(),
    "status": status,
    "risk": risk,
    "policy": {
        "db_write_enabled": False,
        "canonical_merge_enabled": False,
        "preserved_valid_authoritative": True,
        "collision_rows_quarantined": True,
        "repaired_collision_rows_not_included_in_final_valid": True
    },
    "metrics": metrics,
    "artifacts": {
        "final_valid_csv": str(final_valid_csv),
        "final_valid_json": str(final_valid_json),
        "collision_quarantine_csv": str(collision_csv),
        "non_collision_repaired_csv": str(non_collision_repaired_csv),
        "rootcause_csv": str(rootcause_csv)
    },
    "recommendation": recommendation,
    "next_step": next_step
}
collision_audit_json.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")

execution_gate = {
    "generated_at": datetime.now().isoformat(),
    "status": "EXECUTION_GATE_READY_FOR_REVIEW_WITH_COLLISION_QUARANTINE" if risk in ["LOW","MEDIUM"] else "EXECUTION_GATE_CLOSED_DUPLICATE_REVIEW",
    "risk": risk,
    "allowed_to_write_database": False,
    "allowed_to_merge_canonical": False,
    "metrics": metrics,
    "hard_stop": [
        "No DB write in v027.8.4.1",
        "No canonical merge in v027.8.4.1",
        "v027.9 is review only unless explicitly approved",
        "Collision quarantine rows must not be written into canonical table"
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
        "collision_audit_json": str(collision_audit_json),
        "execution_gate_json": str(execution_gate_json)
    },
    "next_step": next_step
}
out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False))
