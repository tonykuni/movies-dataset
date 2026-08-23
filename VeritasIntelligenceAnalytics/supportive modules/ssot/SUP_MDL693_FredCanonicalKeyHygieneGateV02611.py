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
preview_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_v0261_20260610_133556\\staging") if r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANDIDATE_TO_CANONICAL_MERGE_DRYRUN_v0261_20260610_133556\\staging" else Path("")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_CANONICAL_KEY_HYGIENE_GATE_v02611_20260610_133957\\runtime\\vdf_fred_canonical_key_hygiene_gate_result_v02611.json")

canonical_path = db / "VDF_Global_Macro.parquet"
candidate_path = db / "VDF_Global_Macro_FRED_SmallScope_Candidate.parquet"
preview_path = preview_dir / "VDF_Global_Macro_MERGE_PREVIEW_v0261.parquet"

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_CANONICAL_KEY_HYGIENE_GATE_READY",
    "risk": "LOW",
    "policy": "Hygiene gate only. No merge. No DB rewrite.",
    "canonical_rows": 0,
    "canonical_unique_keys": 0,
    "canonical_duplicate_keys": 0,
    "canonical_invalid_key_rows": 0,
    "candidate_rows": 0,
    "candidate_unique_keys": 0,
    "candidate_duplicate_keys": 0,
    "candidate_invalid_key_rows": 0,
    "preview_rows": 0,
    "preview_unique_keys": 0,
    "preview_duplicate_keys": 0,
    "overlap_keys": 0,
    "expected_preview_unique_rows": 0,
    "preview_arithmetic_ok": False,
    "recommendation": "UNKNOWN",
    "samples": {}
}

try:
    import pandas as pd
except Exception as e:
    result["status"] = "VDF_FRED_CANONICAL_KEY_HYGIENE_GATE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    raise SystemExit(0)

def load(path):
    if path.exists():
        return pd.read_parquet(path)
    return pd.DataFrame()

def key_stats(df, prefix):
    if df.empty:
        return set()

    for c in ["symbol","date"]:
        if c not in df.columns:
            df[c] = None

    df2 = df.copy()
    df2["symbol_key"] = df2["symbol"].astype(str).str.strip()
    df2["date_key"] = df2["date"].astype(str).str.strip()

    invalid = df2[
        (df2["symbol_key"] == "") |
        (df2["symbol_key"].str.lower().isin(["none","nan","nat"])) |
        (df2["date_key"] == "") |
        (df2["date_key"].str.lower().isin(["none","nan","nat"]))
    ]

    valid = df2.drop(index=invalid.index)
    keys = set(zip(valid["symbol_key"], valid["date_key"]))
    dup_count = int(valid.duplicated(subset=["symbol_key","date_key"]).sum())

    result[f"{prefix}_rows"] = int(len(df2))
    result[f"{prefix}_unique_keys"] = int(len(keys))
    result[f"{prefix}_duplicate_keys"] = dup_count
    result[f"{prefix}_invalid_key_rows"] = int(len(invalid))

    result["samples"][f"{prefix}_invalid_sample"] = invalid.head(20).astype(str).to_dict(orient="records")
    result["samples"][f"{prefix}_duplicate_sample"] = valid[valid.duplicated(subset=["symbol_key","date_key"], keep=False)].head(20).astype(str).to_dict(orient="records")

    return keys

canonical = load(canonical_path)
candidate = load(candidate_path)
preview = load(preview_path)

ck = key_stats(canonical, "canonical")
fk = key_stats(candidate, "candidate")
pk = key_stats(preview, "preview")

overlap = ck.intersection(fk)
result["overlap_keys"] = int(len(overlap))
result["expected_preview_unique_rows"] = int(len((ck - fk).union(fk)))
result["preview_arithmetic_ok"] = (result["preview_unique_keys"] == result["expected_preview_unique_rows"])

if result["candidate_rows"] <= 0 or result["candidate_unique_keys"] < 5:
    result["status"] = "VDF_FRED_CANONICAL_KEY_HYGIENE_GATE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["recommendation"] = "BLOCK_CANDIDATE_INVALID"
elif result["canonical_invalid_key_rows"] > 0 or result["canonical_duplicate_keys"] > 0:
    result["status"] = "VDF_FRED_CANONICAL_KEY_HYGIENE_GATE_READY_WITH_CANONICAL_KEY_REPAIR_REQUIRED"
    result["risk"] = "MEDIUM"
    result["recommendation"] = "RUN_V02612_CANONICAL_KEY_REPAIR_DRYRUN_BEFORE_REAL_MERGE"
elif not result["preview_arithmetic_ok"]:
    result["status"] = "VDF_FRED_CANONICAL_KEY_HYGIENE_GATE_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["recommendation"] = "BLOCK_PREVIEW_ARITHMETIC_MISMATCH"
else:
    result["recommendation"] = "ALLOW_V0262_REAL_MERGE_WITH_BACKUP"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "canonical_rows": result["canonical_rows"],
    "canonical_unique_keys": result["canonical_unique_keys"],
    "canonical_duplicate_keys": result["canonical_duplicate_keys"],
    "canonical_invalid_key_rows": result["canonical_invalid_key_rows"],
    "candidate_rows": result["candidate_rows"],
    "candidate_unique_keys": result["candidate_unique_keys"],
    "preview_rows": result["preview_rows"],
    "preview_unique_keys": result["preview_unique_keys"],
    "expected_preview_unique_rows": result["expected_preview_unique_rows"],
    "preview_arithmetic_ok": result["preview_arithmetic_ok"],
    "recommendation": result["recommendation"]
}, ensure_ascii=False))
