import json
import os
from pathlib import Path
from datetime import datetime, timedelta

DB_DIR = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
STAGING_DIR = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_SMALL_SCOPE_SEED_v0251_20260610_130027\\staging")
OUT = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_FRED_SMALL_SCOPE_SEED_v0251_20260610_130027\\runtime\\vdf_fred_small_scope_seed_result_v0251.json")

SYMBOLS = [
    {"symbol":"GDP","description":"US Gross Domestic Product","unit":"USD","frequency":"Quarterly"},
    {"symbol":"CPIAUCSL","description":"US Consumer Price Index","unit":"Index","frequency":"Monthly"},
    {"symbol":"FEDFUNDS","description":"Federal Funds Effective Rate","unit":"Percent","frequency":"Monthly"},
    {"symbol":"DGS10","description":"10-Year Treasury Constant Maturity Rate","unit":"Percent","frequency":"Daily"},
    {"symbol":"UNRATE","description":"US Unemployment Rate","unit":"Percent","frequency":"Monthly"}
]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_FRED_SMALL_SCOPE_SEED_READY",
    "risk": "LOW",
    "policy": "FRED 5 symbols. Last 5 years. Candidate/raw only. No canonical overwrite.",
    "symbols": [],
    "raw_rows": 0,
    "candidate_rows": 0,
    "libs": {},
    "outputs": {}
}

try:
    import requests
    result["libs"]["requests"] = True
except Exception as e:
    result["libs"]["requests"] = False
    result["status"] = "VDF_FRED_SMALL_SCOPE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"requests missing: {e}"

try:
    import pandas as pd
    result["libs"]["pandas"] = True
except Exception as e:
    result["libs"]["pandas"] = False
    result["status"] = "VDF_FRED_SMALL_SCOPE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"

try:
    import pyarrow  # noqa
    result["libs"]["pyarrow"] = True
except Exception as e:
    result["libs"]["pyarrow"] = False
    result["status"] = "VDF_FRED_SMALL_SCOPE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pyarrow missing: {e}"

try:
    import duckdb  # noqa
    result["libs"]["duckdb"] = True
except Exception as e:
    result["libs"]["duckdb"] = False
    result["status"] = "VDF_FRED_SMALL_SCOPE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"duckdb missing: {e}"

key_names = ["FRED_API_KEY","VDF_FRED_API_KEY","VIA_FRED_API_KEY"]
api_key = ""
api_key_source = ""
for k in key_names:
    v = os.environ.get(k, "").strip()
    if v:
        api_key = v
        api_key_source = k
        break

result["fred_api_key_exists"] = bool(api_key)
result["fred_api_key_source"] = api_key_source

if not api_key:
    result["status"] = "VDF_FRED_SMALL_SCOPE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = "FRED API key missing."

if result["risk"] != "HIGH":
    import requests
    import pandas as pd

    DB_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    start_date = (datetime.now() - timedelta(days=365*5 + 10)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    raw_records = []
    candidate_records = []

    for item in SYMBOLS:
        symbol = item["symbol"]
        url = "https://api.stlouisfed.org/fred/series/observations"
        params = {
            "series_id": symbol,
            "api_key": api_key,
            "file_type": "json",
            "observation_start": start_date,
            "observation_end": end_date
        }

        sym_result = {
            "symbol": symbol,
            "status": "NOT_RUN",
            "risk": "MEDIUM",
            "rows": 0,
            "error": "",
            "description": item["description"]
        }

        try:
            r = requests.get(url, params=params, timeout=30)
            sym_result["http_status"] = r.status_code

            if r.status_code != 200:
                sym_result["status"] = "FETCH_FAIL"
                sym_result["risk"] = "HIGH"
                sym_result["error"] = r.text[:300]
                result["status"] = "VDF_FRED_SMALL_SCOPE_SEED_WITH_REVIEW"
                result["risk"] = "HIGH"
                result["symbols"].append(sym_result)
                continue

            payload = r.json()
            raw_path = STAGING_DIR / f"FRED_{symbol}_raw.json"
            raw_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

            observations = payload.get("observations", [])
            sym_result["rows"] = len(observations)
            sym_result["status"] = "FETCH_OK"
            sym_result["risk"] = "LOW"
            sym_result["raw_json"] = str(raw_path)

            for obs in observations:
                raw_records.append({
                    "symbol": symbol,
                    "date": obs.get("date"),
                    "value": obs.get("value"),
                    "realtime_start": obs.get("realtime_start"),
                    "realtime_end": obs.get("realtime_end"),
                    "source": "FRED",
                    "description": item["description"],
                    "unit": item["unit"],
                    "frequency": item["frequency"],
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })

                val = obs.get("value")
                try:
                    val2 = None if val in [None, "", "."] else float(val)
                except Exception:
                    val2 = None

                if val2 is not None:
                    candidate_records.append({
                        "symbol": symbol,
                        "date": obs.get("date"),
                        "value": val2,
                        "source": "FRED",
                        "unit": item["unit"],
                        "frequency": item["frequency"],
                        "description": item["description"]
                    })

            result["symbols"].append(sym_result)

        except Exception as e:
            sym_result["status"] = "FETCH_EXCEPTION"
            sym_result["risk"] = "HIGH"
            sym_result["error"] = str(e)
            result["status"] = "VDF_FRED_SMALL_SCOPE_SEED_WITH_REVIEW"
            result["risk"] = "HIGH"
            result["symbols"].append(sym_result)

    raw_df = pd.DataFrame(raw_records)
    can_df = pd.DataFrame(candidate_records)

    raw_json = DB_DIR / "VDF_FRED_Raw_GlobalMacro_SmallScope.json"
    raw_csv = DB_DIR / "VDF_FRED_Raw_GlobalMacro_SmallScope.csv"
    raw_parquet = DB_DIR / "VDF_FRED_Raw_GlobalMacro_SmallScope.parquet"

    can_json = DB_DIR / "VDF_Global_Macro_FRED_SmallScope_Candidate.json"
    can_csv = DB_DIR / "VDF_Global_Macro_FRED_SmallScope_Candidate.csv"
    can_parquet = DB_DIR / "VDF_Global_Macro_FRED_SmallScope_Candidate.parquet"

    raw_df.to_json(raw_json, force_ascii=False, orient="records", indent=2)
    raw_df.to_csv(raw_csv, index=False, encoding="utf-8-sig")
    raw_df.to_parquet(raw_parquet, index=False)

    desired = ["symbol","date","value","source","unit","frequency","description"]
    for c in desired:
        if c not in can_df.columns:
            can_df[c] = None
    can_df = can_df[desired]
    can_df = can_df.drop_duplicates(subset=["symbol","date"], keep="last")

    can_df.to_json(can_json, force_ascii=False, orient="records", indent=2)
    can_df.to_csv(can_csv, index=False, encoding="utf-8-sig")
    can_df.to_parquet(can_parquet, index=False)

    result["raw_rows"] = int(len(raw_df))
    result["candidate_rows"] = int(len(can_df))
    result["outputs"] = {
        "raw_json": str(raw_json),
        "raw_csv": str(raw_csv),
        "raw_parquet": str(raw_parquet),
        "candidate_json": str(can_json),
        "candidate_csv": str(can_csv),
        "candidate_parquet": str(can_parquet)
    }

    if result["candidate_rows"] <= 0:
        result["status"] = "VDF_FRED_SMALL_SCOPE_SEED_WITH_REVIEW"
        result["risk"] = "HIGH"
        result["error"] = "Candidate rows are zero."

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "raw_rows": result["raw_rows"],
    "candidate_rows": result["candidate_rows"],
    "symbols": len(result["symbols"])
}, ensure_ascii=False))
