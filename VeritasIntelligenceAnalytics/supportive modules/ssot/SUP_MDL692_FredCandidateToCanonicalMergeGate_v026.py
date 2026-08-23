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

db = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_GATE_v026_20260610_132856\\runtime\\vdf_fred_candidate_to_canonical_merge_gate_result_v026.json")

candidate_path = db / "VDF_Global_Macro_FRED_SmallScope_Candidate.parquet"
canonical_path = db / "VDF_Global_Macro.parquet"

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_GATE_READY",
    "risk": "LOW",
    "policy": "Gate only. No merge. No DB rewrite.",
    "candidate_rows": 0,
    "canonical_exists": canonical_path.exists(),
    "canonical_rows": 0,
    "candidate_symbols": [],
    "candidate_symbol_count": 0,
    "duplicate_keys_in_candidate": 0,
    "overlap_keys_with_canonical": 0,
    "missing_candidate_columns": [],
    "merge_recommendation": "ALLOW_NEXT_STAGE_WITH_BACKUP"
}

try:
    import pandas as pd
    result["libs"] = {"pandas": True}
except Exception as e:
    result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_GATE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    raise SystemExit(0)

required = ["symbol","date","value","source","unit","frequency","description"]

if not candidate_path.exists():
    result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_GATE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["merge_recommendation"] = "BLOCK_MISSING_CANDIDATE"
else:
    c = pd.read_parquet(candidate_path)
    result["candidate_rows"] = int(len(c))
    result["candidate_columns"] = list(c.columns)
    result["missing_candidate_columns"] = [x for x in required if x not in c.columns]

    if "symbol" in c.columns:
        result["candidate_symbols"] = sorted([str(x) for x in c["symbol"].dropna().unique().tolist()])
        result["candidate_symbol_count"] = len(result["candidate_symbols"])

    if "symbol" in c.columns and "date" in c.columns:
        result["duplicate_keys_in_candidate"] = int(c.duplicated(subset=["symbol","date"]).sum())

    if result["candidate_rows"] <= 0 or result["candidate_symbol_count"] != 5 or result["missing_candidate_columns"] or result["duplicate_keys_in_candidate"] > 0:
        result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_GATE_WITH_REVIEW"
        result["risk"] = "HIGH"
        result["merge_recommendation"] = "BLOCK_SCHEMA_OR_DUPLICATE_REVIEW"

    if canonical_path.exists() and result["risk"] != "HIGH":
        k = pd.read_parquet(canonical_path)
        result["canonical_rows"] = int(len(k))
        result["canonical_columns"] = list(k.columns)

        if all(x in k.columns for x in ["symbol","date"]) and all(x in c.columns for x in ["symbol","date"]):
            c_keys = set(zip(c["symbol"].astype(str), c["date"].astype(str)))
            k_keys = set(zip(k["symbol"].astype(str), k["date"].astype(str)))
            result["overlap_keys_with_canonical"] = int(len(c_keys.intersection(k_keys)))

        result["risk"] = "MEDIUM"
        result["status"] = "VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_GATE_READY_WITH_EXISTING_CANONICAL"
        result["merge_recommendation"] = "ALLOW_NEXT_STAGE_WITH_BACKUP_AND_DEDUP"
    elif result["risk"] != "HIGH":
        result["merge_recommendation"] = "ALLOW_NEXT_STAGE_CREATE_CANONICAL_WITH_BACKUP_POLICY"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "candidate_rows": result["candidate_rows"],
    "candidate_symbol_count": result["candidate_symbol_count"],
    "canonical_exists": result["canonical_exists"],
    "canonical_rows": result["canonical_rows"],
    "overlap": result["overlap_keys_with_canonical"],
    "recommendation": result["merge_recommendation"]
}, ensure_ascii=False))
