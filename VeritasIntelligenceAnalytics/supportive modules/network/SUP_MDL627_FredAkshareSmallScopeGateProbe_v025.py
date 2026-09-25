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
import json, importlib.util, os
from pathlib import Path
from datetime import datetime

out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_AKSHARE_SMALL_SCOPE_SEED_GATE_v025_20260610_125014\\runtime\\vdf_fred_akshare_small_scope_gate_probe_result_v025.json")

required = ["requests","pandas","pyarrow","duckdb","fredapi","akshare"]
optional = ["pandas_datareader","polars","tenacity","requests_cache","openpyxl","bs4","lxml"]

packages = []
for p in required + optional:
    packages.append({"package": p, "available": importlib.util.find_spec(p) is not None})

fred_keys = ["FRED_API_KEY","VDF_FRED_API_KEY","VIA_FRED_API_KEY"]
fred_key_exists = any(bool(os.environ.get(k, "").strip()) for k in fred_keys)

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_AKSHARE_SMALL_SCOPE_SEED_GATE_READY",
    "risk": "LOW",
    "policy": "Gate only. No API call. No data fetch. No DB rewrite.",
    "packages": packages,
    "missing_required": [p["package"] for p in packages if p["package"] in required and not p["available"]],
    "missing_optional": [p["package"] for p in packages if p["package"] in optional and not p["available"]],
    "fred_api_key_exists": fred_key_exists,
    "fred_api_key_sources_checked": fred_keys,
    "fred_small_scope_symbols": ["GDP","CPIAUCSL","FEDFUNDS","DGS10","UNRATE"],
    "akshare_selector_symbols": ["BDI","IRON_ORE","COKING_COAL"]
}

if result["missing_required"]:
    result["status"] = "VDF_FRED_AKSHARE_SMALL_SCOPE_SEED_GATE_WITH_REVIEW"
    result["risk"] = "HIGH"
elif not fred_key_exists or result["missing_optional"]:
    result["status"] = "VDF_FRED_AKSHARE_SMALL_SCOPE_SEED_GATE_READY_WITH_OPTIONAL_REVIEW"
    result["risk"] = "MEDIUM"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "fred_api_key_exists": result["fred_api_key_exists"],
    "missing_required": result["missing_required"],
    "missing_optional": result["missing_optional"]
}, ensure_ascii=False))
