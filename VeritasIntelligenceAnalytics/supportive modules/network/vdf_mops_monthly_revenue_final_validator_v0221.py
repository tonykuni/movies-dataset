import json
from pathlib import Path
from datetime import datetime

db = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
out = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_freeze\\VDF_MOPS_MONTHLY_REVENUE_FINAL_SEAL_v0221_20260609_234646\\runtime\\vdf_mops_monthly_revenue_final_validator_result_v0221.json")

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_MOPS_MONTHLY_REVENUE_FINAL_SEAL_READY_WITH_OTC_DEFERRED",
    "risk": "MEDIUM",
    "canonical_rows": 0,
    "listed_raw_rows": 0,
    "otc_raw_rows": 0,
    "otc_status": "DEFERRED_ENDPOINT_REVIEW",
    "libs": {}
}

try:
    import pandas as pd
    result["libs"]["pandas"] = True
except Exception as e:
    result["libs"]["pandas"] = False
    result["status"] = "VDF_MOPS_MONTHLY_REVENUE_FINAL_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"

try:
    import pyarrow  # noqa
    result["libs"]["pyarrow"] = True
except Exception as e:
    result["libs"]["pyarrow"] = False
    result["status"] = "VDF_MOPS_MONTHLY_REVENUE_FINAL_SEAL_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pyarrow missing: {e}"

if result["libs"].get("pandas") and result["libs"].get("pyarrow"):
    import pandas as pd

    canonical = db / "VDF_TW_MonthlyRevenue.parquet"
    listed = db / "VDF_MOPS_Raw_MonthlyRevenue_Listed.parquet"
    otc = db / "VDF_MOPS_Raw_MonthlyRevenue_OTC.parquet"

    if canonical.exists():
        df = pd.read_parquet(canonical)
        result["canonical_rows"] = int(len(df))
        result["canonical_columns"] = list(df.columns)

    if listed.exists():
        df = pd.read_parquet(listed)
        result["listed_raw_rows"] = int(len(df))
        result["listed_raw_columns"] = list(df.columns)

    if otc.exists():
        df = pd.read_parquet(otc)
        result["otc_raw_rows"] = int(len(df))
        result["otc_status"] = "EXISTS"
    else:
        result["otc_raw_rows"] = 0
        result["otc_status"] = "DEFERRED_ENDPOINT_REVIEW"

    if result["canonical_rows"] <= 0 or result["listed_raw_rows"] <= 0:
        result["status"] = "VDF_MOPS_MONTHLY_REVENUE_FINAL_SEAL_WITH_REVIEW"
        result["risk"] = "HIGH"

out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "canonical_rows": result["canonical_rows"],
    "listed_raw_rows": result["listed_raw_rows"],
    "otc_status": result["otc_status"]
}, ensure_ascii=False))
