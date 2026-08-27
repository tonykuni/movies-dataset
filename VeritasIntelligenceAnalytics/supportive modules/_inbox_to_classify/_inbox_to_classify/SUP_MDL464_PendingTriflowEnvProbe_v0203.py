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
import json, os, importlib.util, sys
from pathlib import Path
from datetime import datetime

result_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_PENDING_TRIFLOW_EXECUTION_GATE_v0203_20260609_230242\\runtime\\vdf_pending_triflow_env_probe_result_v0203.json")

packages = [
    "requests",
    "pandas",
    "polars",
    "pyarrow",
    "duckdb",
    "pandas_datareader",
    "fredapi",
    "akshare",
    "tenacity",
    "requests_cache"
]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "python": sys.executable,
    "packages": {},
    "fred_api_key_exists": bool(os.environ.get("FRED_API_KEY")),
    "fred_api_key_value_not_printed": True,
    "symbol_map_draft": {
        "FRED": [
            {"symbol":"DGS10","table":"VDF_Global_Macro","description":"US 10-year Treasury constant maturity"},
            {"symbol":"DFF","table":"VDF_Global_Macro","description":"Effective federal funds rate"},
            {"symbol":"CPIAUCSL","table":"VDF_Global_Macro","description":"US CPI"},
            {"symbol":"UNRATE","table":"VDF_Global_Macro","description":"US unemployment rate"},
            {"symbol":"INDPRO","table":"VDF_Global_Macro","description":"US industrial production"}
        ],
        "AKSHARE": [
            {"symbol":"BDI","table":"VDF_Global_Freight","description":"Baltic Dry Index if local akshare source supports it"},
            {"symbol":"commodity_futures","table":"VDF_Global_Commodity","description":"Commodity futures candidate source"}
        ]
    }
}

for pkg in packages:
    result["packages"][pkg] = importlib.util.find_spec(pkg) is not None

missing = [k for k,v in result["packages"].items() if not v]
critical_missing = [k for k in ["requests","pandas","pyarrow","duckdb"] if not result["packages"].get(k)]

if critical_missing:
    result["status"] = "FRED_AKSHARE_ENV_WITH_REVIEW"
    result["risk"] = "HIGH"
elif missing:
    result["status"] = "FRED_AKSHARE_ENV_READY_WITH_OPTIONAL_LIB_REVIEW"
    result["risk"] = "MEDIUM"
else:
    result["status"] = "FRED_AKSHARE_ENV_READY"
    result["risk"] = "LOW"

result_path.parent.mkdir(parents=True, exist_ok=True)
with result_path.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps({"status":result["status"],"risk":result["risk"],"fred_api_key_exists":result["fred_api_key_exists"],"missing":missing}, ensure_ascii=False))
