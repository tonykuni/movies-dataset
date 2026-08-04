import json, importlib.util, os
from pathlib import Path
from datetime import datetime

out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_FRED_AKSHARE_CAPABILITY_SEAL_v0241_20260610_124114\\runtime\\vdf_fred_akshare_capability_seal_probe_result_v0241.json")

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
    "requests_cache",
    "openpyxl"
]

items = []
for p in packages:
    spec = importlib.util.find_spec(p)
    items.append({"package": p, "available": spec is not None})

fred_keys = ["FRED_API_KEY", "VDF_FRED_API_KEY", "VIA_FRED_API_KEY"]
fred_key_exists = any(bool(os.environ.get(k, "").strip()) for k in fred_keys)

required = ["requests","pandas","pyarrow","duckdb","fredapi","akshare"]
missing_required = [x["package"] for x in items if x["package"] in required and not x["available"]]
missing_optional = [x["package"] for x in items if x["package"] not in required and not x["available"]]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_AKSHARE_CAPABILITY_SEAL_READY",
    "risk": "LOW",
    "policy": "Capability seal only. No API call. No data fetch. No DB rewrite.",
    "packages": items,
    "required_packages": required,
    "missing_required": missing_required,
    "missing_optional": missing_optional,
    "fred_api_key_exists": fred_key_exists,
    "fred_api_key_sources_checked": fred_keys
}

if missing_required:
    result["status"] = "VDF_FRED_AKSHARE_CAPABILITY_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
elif not fred_key_exists or missing_optional:
    result["status"] = "VDF_FRED_AKSHARE_CAPABILITY_SEAL_READY_WITH_OPTIONAL_REVIEW"
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
