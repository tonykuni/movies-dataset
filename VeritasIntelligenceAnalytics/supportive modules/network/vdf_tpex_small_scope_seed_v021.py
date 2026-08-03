import json
import sys
from pathlib import Path
from datetime import datetime

DB_DIR = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
STAGING_DIR = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_TPEX_SMALL_SCOPE_SEED_v021_20260609_232145\\staging")
RESULT_PATH = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_TPEX_SMALL_SCOPE_SEED_v021_20260609_232145\\runtime\\vdf_tpex_small_scope_seed_result_v021.json")
TARGETS = json.loads(r'''[{"endpoint":"/tpex_securities","output_name":"VDF_TPEX_Raw_Securities","intent":"TPEX listed securities raw staging"},{"endpoint":"/tpex_mainboard_daily_close_quotes","output_name":"VDF_TPEX_Raw_MainboardDailyCloseQuotes","intent":"TPEX mainboard daily close quotes raw staging"}]''')

BASES = [
    "https://www.tpex.org.tw/openapi/v1",
    "https://www.tpex.org.tw/openapi"
]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_TPEX_SMALL_SCOPE_SEED_READY",
    "risk": "LOW",
    "policy": "Only two TPEX endpoints. Add-only raw outputs. No TWSE canonical overwrite.",
    "targets": [],
    "total_rows": 0,
    "libs": {}
}

try:
    import requests
    result["libs"]["requests"] = True
except Exception as e:
    result["libs"]["requests"] = False
    result["status"] = "VDF_TPEX_SMALL_SCOPE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"requests missing: {e}"

try:
    import pandas as pd
    result["libs"]["pandas"] = True
except Exception as e:
    result["libs"]["pandas"] = False
    result["status"] = "VDF_TPEX_SMALL_SCOPE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"

try:
    import pyarrow  # noqa
    result["libs"]["pyarrow"] = True
except Exception as e:
    result["libs"]["pyarrow"] = False
    result["status"] = "VDF_TPEX_SMALL_SCOPE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pyarrow missing: {e}"

if result["libs"].get("requests") and result["libs"].get("pandas"):
    import requests
    import pandas as pd

    DB_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "VeritasDataForge/0.21 small-scope seed; local research use",
        "Accept": "application/json,text/plain,*/*"
    }

    for target in TARGETS:
        endpoint = target["endpoint"].strip()
        endpoint = "/" + endpoint.lstrip("/")
        output_name = target["output_name"]

        item = {
            "endpoint": endpoint,
            "output_name": output_name,
            "intent": target.get("intent", ""),
            "status": "NOT_FETCHED",
            "risk": "MEDIUM",
            "url": "",
            "rows": 0,
            "columns": [],
            "error": ""
        }

        data = None
        last_error = ""

        for base in BASES:
            url = base.rstrip("/") + endpoint
            item["url"] = url
            try:
                r = requests.get(url, headers=headers, timeout=30)
                if r.status_code != 200:
                    last_error = f"HTTP {r.status_code}: {r.text[:200]}"
                    continue
                try:
                    data = r.json()
                except Exception:
                    txt = r.text.strip()
                    if not txt:
                        last_error = "empty response"
                        continue
                    data = json.loads(txt)
                item["status"] = "FETCH_OK"
                item["risk"] = "LOW"
                break
            except Exception as e:
                last_error = str(e)

        if item["status"] != "FETCH_OK":
            item["status"] = "FETCH_FAIL"
            item["risk"] = "HIGH"
            item["error"] = last_error
            result["targets"].append(item)
            result["status"] = "VDF_TPEX_SMALL_SCOPE_SEED_WITH_REVIEW"
            result["risk"] = "HIGH"
            continue

        if isinstance(data, dict):
            if "data" in data and isinstance(data["data"], list):
                records = data["data"]
            elif "result" in data and isinstance(data["result"], list):
                records = data["result"]
            else:
                records = [data]
        elif isinstance(data, list):
            records = data
        else:
            records = [{"raw": str(data)}]

        df = pd.DataFrame(records)
        if len(df.columns) == 0:
            df = pd.DataFrame([{"raw": json.dumps(data, ensure_ascii=False)}])

        item["rows"] = int(len(df))
        item["columns"] = [str(c) for c in df.columns]
        result["total_rows"] += item["rows"]

        raw_json = STAGING_DIR / f"{output_name}.raw.json"
        raw_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        out_json = DB_DIR / f"{output_name}.json"
        out_csv = DB_DIR / f"{output_name}.csv"
        out_parquet = DB_DIR / f"{output_name}.parquet"

        df.to_json(out_json, force_ascii=False, orient="records", indent=2)
        df.to_csv(out_csv, index=False, encoding="utf-8-sig")
        try:
            df.to_parquet(out_parquet, index=False)
            item["parquet"] = str(out_parquet)
        except Exception as e:
            item["status"] = "FETCH_OK_PARQUET_WARN"
            item["risk"] = "MEDIUM"
            item["error"] = f"parquet write warning: {e}"
            result["status"] = "VDF_TPEX_SMALL_SCOPE_SEED_READY_WITH_WARNINGS"
            result["risk"] = "MEDIUM"

        item["json"] = str(out_json)
        item["csv"] = str(out_csv)
        result["targets"].append(item)

    if result["total_rows"] <= 0:
        result["status"] = "VDF_TPEX_SMALL_SCOPE_SEED_WITH_REVIEW"
        result["risk"] = "HIGH"

RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
with RESULT_PATH.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "targets": len(result["targets"]),
    "rows": result["total_rows"]
}, ensure_ascii=False))
