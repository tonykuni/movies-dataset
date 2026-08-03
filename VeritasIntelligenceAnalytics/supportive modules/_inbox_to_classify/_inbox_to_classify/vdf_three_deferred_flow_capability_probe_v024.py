import json, importlib.util, os, sys
from pathlib import Path
from datetime import datetime

out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_THREE_DEFERRED_FLOW_SYNC_GATE_v024_20260610_123806\\runtime\\vdf_three_deferred_flow_capability_probe_result_v024.json")

packages = [
    "requests",
    "pandas",
    "pyarrow",
    "duckdb",
    "pandas_datareader",
    "fredapi",
    "akshare",
    "bs4",
    "lxml",
    "openpyxl",
]

items = []
for p in packages:
    spec = importlib.util.find_spec(p)
    items.append({"package": p, "available": spec is not None})

fred_keys = [
    "FRED_API_KEY",
    "VDF_FRED_API_KEY",
    "VIA_FRED_API_KEY"
]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_THREE_DEFERRED_FLOW_CAPABILITY_PROBE_READY",
    "risk": "LOW",
    "policy": "Local capability probe only. No API call. No data fetch.",
    "packages": items,
    "fred_api_key_exists": any(bool(os.environ.get(k, "").strip()) for k in fred_keys),
    "fred_api_key_sources_checked": fred_keys,
    "missing": [x["package"] for x in items if not x["available"]]
}

critical = ["requests", "pandas", "pyarrow", "duckdb"]
missing_critical = [x for x in critical if x in result["missing"]]

if missing_critical:
    result["status"] = "VDF_THREE_DEFERRED_FLOW_CAPABILITY_PROBE_WITH_REVIEW"
    result["risk"] = "HIGH"
elif len(result["missing"]) > 0 or not result["fred_api_key_exists"]:
    result["status"] = "VDF_THREE_DEFERRED_FLOW_CAPABILITY_PROBE_READY_WITH_DEFERRED_OPTIONALS"
    result["risk"] = "MEDIUM"

out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "missing": result["missing"],
    "fred_api_key_exists": result["fred_api_key_exists"]
}, ensure_ascii=False))
