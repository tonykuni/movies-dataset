import json
import re
import sys
from pathlib import Path
from datetime import datetime

DB_DIR = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
STAGING_DIR = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_MOPS_MONTHLY_REVENUE_SEED_v022_20260609_233356\\staging")
RESULT_PATH = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_MOPS_MONTHLY_REVENUE_SEED_v022_20260609_233356\\runtime\\vdf_mops_monthly_revenue_seed_result_v022.json")
TARGETS = json.loads(r'''[{"market":"L","endpoint":"/opendata/t187ap05_L","output_name":"VDF_MOPS_Raw_MonthlyRevenue_Listed","intent":"Listed companies monthly revenue raw staging"},{"market":"O","endpoint":"/opendata/t187ap05_O","output_name":"VDF_MOPS_Raw_MonthlyRevenue_OTC","intent":"OTC companies monthly revenue raw staging"}]''')

BASES = [
    "https://openapi.twse.com.tw/v1",
    "https://openapi.twse.com.tw"
]

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "VDF_MOPS_MONTHLY_REVENUE_SEED_READY",
    "risk": "LOW",
    "policy": "MonthlyRevenue only. No CompanyProfile. No FinancialStatement. No FinancialRatio.",
    "targets": [],
    "canonical_rows": 0,
    "libs": {}
}

try:
    import requests
    result["libs"]["requests"] = True
except Exception as e:
    result["libs"]["requests"] = False
    result["status"] = "VDF_MOPS_MONTHLY_REVENUE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"requests missing: {e}"

try:
    import pandas as pd
    result["libs"]["pandas"] = True
except Exception as e:
    result["libs"]["pandas"] = False
    result["status"] = "VDF_MOPS_MONTHLY_REVENUE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pandas missing: {e}"

try:
    import pyarrow  # noqa
    result["libs"]["pyarrow"] = True
except Exception as e:
    result["libs"]["pyarrow"] = False
    result["status"] = "VDF_MOPS_MONTHLY_REVENUE_SEED_WITH_REVIEW"
    result["risk"] = "HIGH"
    result["error"] = f"pyarrow missing: {e}"

def pick(row, names):
    for n in names:
        if n in row and row.get(n) not in [None, ""]:
            return row.get(n)
    return ""

def clean_num(v):
    if v is None:
        return None
    s = str(v).strip().replace(",", "")
    s = s.replace("--", "").replace("－", "").replace("—", "")
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        m = re.search(r"-?\d+(\.\d+)?", s)
        if m:
            try:
                return float(m.group(0))
            except Exception:
                return None
    return None

def normalize_record(row, market):
    ticker = str(pick(row, ["公司代號","公司代號Code","公司代號 Code","公司代號　","公司代號 "])).strip()
    name = str(pick(row, ["公司名稱","公司名稱Name","公司名稱 Name","公司名稱　","公司名稱 "])).strip()
    industry = str(pick(row, ["產業別","產業別Industry","產業別 Industry"])).strip()

    yyyymm = str(pick(row, ["資料年月","年月","營收年月","出表日期"])).strip()
    report_date = str(pick(row, ["出表日期","公告日期","資料日期"])).strip()

    revenue = clean_num(pick(row, ["營業收入-當月營收","當月營收","單月營收","本月營收"]))
    mom = clean_num(pick(row, ["營業收入-上月比較增減(%)","上月比較增減(%)","月增率","MoM"]))
    yoy = clean_num(pick(row, ["營業收入-去年同月增減(%)","去年同月增減(%)","年增率","YoY"]))
    cum_revenue = clean_num(pick(row, ["累計營業收入-當月累計營收","當月累計營收","累計營收"]))
    cum_yoy = clean_num(pick(row, ["累計營業收入-去年累計增減(%)","去年累計增減(%)","累計年增率"]))

    return {
        "ticker": ticker,
        "yyyymm": yyyymm,
        "revenue": revenue,
        "mom": mom,
        "yoy": yoy,
        "cum_revenue": cum_revenue,
        "cum_yoy": cum_yoy,
        "name": name,
        "market": market,
        "industry": industry,
        "report_date": report_date,
        "source": "TWSE_OpenAPI_MOPS_MonthlyRevenue",
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

if result["libs"].get("requests") and result["libs"].get("pandas"):
    import requests
    import pandas as pd

    DB_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    headers = {
        "User-Agent": "VeritasDataForge/0.22 monthly-revenue seed; local research use",
        "Accept": "application/json,text/plain,*/*"
    }

    canonical_rows = []

    for target in TARGETS:
        endpoint = "/" + target["endpoint"].lstrip("/")
        output_name = target["output_name"]
        market = target["market"]

        item = {
            "market": market,
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
            result["status"] = "VDF_MOPS_MONTHLY_REVENUE_SEED_WITH_REVIEW"
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

        raw_df = pd.DataFrame(records)
        item["rows"] = int(len(raw_df))
        item["columns"] = [str(c) for c in raw_df.columns]

        raw_json = STAGING_DIR / f"{output_name}.raw.json"
        raw_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        raw_out_json = DB_DIR / f"{output_name}.json"
        raw_out_csv = DB_DIR / f"{output_name}.csv"
        raw_out_parquet = DB_DIR / f"{output_name}.parquet"

        raw_df.to_json(raw_out_json, force_ascii=False, orient="records", indent=2)
        raw_df.to_csv(raw_out_csv, index=False, encoding="utf-8-sig")
        raw_df.to_parquet(raw_out_parquet, index=False)

        item["json"] = str(raw_out_json)
        item["csv"] = str(raw_out_csv)
        item["parquet"] = str(raw_out_parquet)

        for row in records:
            if isinstance(row, dict):
                norm = normalize_record(row, market)
                if norm["ticker"] != "":
                    canonical_rows.append(norm)

        result["targets"].append(item)

    can_df = pd.DataFrame(canonical_rows)
    if len(can_df) > 0:
        desired = ["ticker","yyyymm","revenue","mom","yoy","cum_revenue","cum_yoy","name","market","industry","report_date","source","updated_at"]
        for c in desired:
            if c not in can_df.columns:
                can_df[c] = None
        can_df = can_df[desired]
        can_df = can_df.drop_duplicates(subset=["ticker","yyyymm","market"], keep="last")

        can_json = DB_DIR / "VDF_TW_MonthlyRevenue.json"
        can_csv = DB_DIR / "VDF_TW_MonthlyRevenue.csv"
        can_parquet = DB_DIR / "VDF_TW_MonthlyRevenue.parquet"

        can_df.to_json(can_json, force_ascii=False, orient="records", indent=2)
        can_df.to_csv(can_csv, index=False, encoding="utf-8-sig")
        can_df.to_parquet(can_parquet, index=False)

        result["canonical"] = {
            "json": str(can_json),
            "csv": str(can_csv),
            "parquet": str(can_parquet),
            "rows": int(len(can_df)),
            "columns": desired
        }
        result["canonical_rows"] = int(len(can_df))
    else:
        result["status"] = "VDF_MOPS_MONTHLY_REVENUE_SEED_WITH_REVIEW"
        result["risk"] = "HIGH"
        result["canonical"] = {"rows": 0, "error": "No canonical rows normalized"}

RESULT_PATH.parent.mkdir(parents=True, exist_ok=True)
with RESULT_PATH.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "targets": len(result["targets"]),
    "canonical_rows": result["canonical_rows"]
}, ensure_ascii=False))
