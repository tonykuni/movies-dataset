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
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_FRED_SMALL_SCOPE_FINAL_SEAL_v0252_20260610_130808\\runtime\\vdf_fred_small_scope_final_validator_result_v0252.json")

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_SMALL_SCOPE_FINAL_SEAL_READY",
    "risk": "LOW",
    "raw_rows": 0,
    "candidate_rows": 0,
    "symbols": [],
    "symbol_count": 0,
    "libs": {}
}

try:
    import pandas as pd
    result["libs"]["pandas"] = True
except Exception as e:
    result["libs"]["pandas"] = False
    result["status"] = "VDF_FRED_SMALL_SCOPE_FINAL_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"

try:
    import pyarrow  # noqa
    result["libs"]["pyarrow"] = True
except Exception as e:
    result["libs"]["pyarrow"] = False
    result["status"] = "VDF_FRED_SMALL_SCOPE_FINAL_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pyarrow missing: {e}"

if result["risk"] != "HIGH":
    import pandas as pd

    raw = db / "VDF_FRED_Raw_GlobalMacro_SmallScope.parquet"
    candidate = db / "VDF_Global_Macro_FRED_SmallScope_Candidate.parquet"

    if raw.exists():
        rdf = pd.read_parquet(raw)
        result["raw_rows"] = int(len(rdf))
        result["raw_columns"] = list(rdf.columns)

    if candidate.exists():
        cdf = pd.read_parquet(candidate)
        result["candidate_rows"] = int(len(cdf))
        result["candidate_columns"] = list(cdf.columns)
        if "symbol" in cdf.columns:
            result["symbols"] = sorted([str(x) for x in cdf["symbol"].dropna().unique().tolist()])
            result["symbol_count"] = len(result["symbols"])

    required = ["symbol","date","value","source","unit","frequency","description"]
    missing_cols = [c for c in required if c not in result.get("candidate_columns", [])]
    result["missing_candidate_columns"] = missing_cols

    if result["raw_rows"] <= 0 or result["candidate_rows"] <= 0 or result["symbol_count"] != 5 or missing_cols:
        result["status"] = "VDF_FRED_SMALL_SCOPE_FINAL_SEAL_WITH_REVIEW"
        result["risk"] = "HIGH"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "raw_rows": result["raw_rows"],
    "candidate_rows": result["candidate_rows"],
    "symbol_count": result["symbol_count"]
}, ensure_ascii=False))
