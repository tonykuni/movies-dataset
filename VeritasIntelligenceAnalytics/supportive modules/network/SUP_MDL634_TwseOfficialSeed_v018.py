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
import csv, json, traceback, re, urllib.request
from pathlib import Path
from datetime import datetime

db_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
header_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_ssot\\VDF_DataScope_HeaderRegistry_SSOT.json")
plan_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_TWSE_OFFICIAL_SEED_v018_20260609_223313\\registry\\VDF_TWSEOfficialSeed_TargetPlan_v018.json")
result_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_TWSE_OFFICIAL_SEED_v018_20260609_223313\\runtime\\vdf_twse_official_seed_result_v018.json")

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "PENDING",
    "risk": "PENDING",
    "database_root": str(db_dir),
    "libs": {
        "pandas": False,
        "pyarrow": False,
        "duckdb": False,
        "requests": False
    },
    "outputs": [],
    "tpex_probe": {
        "status": "PENDING",
        "risk": "PENDING",
        "swagger": "https://www.tpex.org.tw/openapi/swagger.json",
        "paths_count": 0,
        "interesting_paths": [],
        "message": ""
    },
    "errors": []
}

pd = None
duckdb = None
pyarrow_ok = False
requests = None

try:
    import pandas as pd
    result["libs"]["pandas"] = True
except Exception as e:
    result["errors"].append({"stage":"import_pandas","message":str(e)})

try:
    import pyarrow
    result["libs"]["pyarrow"] = True
    pyarrow_ok = True
except Exception as e:
    result["errors"].append({"stage":"import_pyarrow","message":str(e)})

try:
    import duckdb
    result["libs"]["duckdb"] = True
except Exception as e:
    result["errors"].append({"stage":"import_duckdb","message":str(e)})

try:
    import requests
    result["libs"]["requests"] = True
except Exception as e:
    result["errors"].append({"stage":"import_requests","message":str(e)})

def read_json(p):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def fetch_json(url, timeout=30):
    if requests is not None:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": "VeritasDataForge/0.18"})
        r.raise_for_status()
        return r.json()
    req = urllib.request.Request(url, headers={"User-Agent": "VeritasDataForge/0.18"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8-sig")
    return json.loads(data)

def split_headers(x):
    return [h.strip() for h in str(x).split(",") if h.strip()]

def table_headers(header_registry, table_id):
    for t in header_registry.get("tables", []):
        if str(t.get("TableId", "")).strip() == table_id:
            return split_headers(t.get("Headers", ""))
    return []

def blank(headers):
    return {h: "" for h in headers}

def num_text(x):
    if x is None:
        return ""
    s = str(x).strip().replace(",", "")
    if s in ("", "--", "-", "N/A", "nan"):
        return ""
    return s

def twse_value(row, *keys):
    for k in keys:
        if k in row:
            return row.get(k, "")
    return ""

def normalize_equity_universe(raw, headers):
    rows = []
    for r in raw:
        code = str(twse_value(r, "Code", "證券代號", "公司代號")).strip()
        name = str(twse_value(r, "Name", "證券名稱", "公司簡稱")).strip()
        if not code:
            continue
        row = blank(headers)
        if "ticker" in row:
            row["ticker"] = code
        if "name" in row:
            row["name"] = name
        if "market" in row:
            row["market"] = "TWSE"
        if "security_type" in row:
            row["security_type"] = "LISTED"
        if "status" in row:
            row["status"] = "ACTIVE_SEED"
        rows.append(row)
    return rows

def normalize_trading_stats(raw, headers):
    rows = []
    today = datetime.now().strftime("%Y-%m-%d")
    for r in raw:
        code = str(twse_value(r, "Code", "證券代號")).strip()
        name = str(twse_value(r, "Name", "證券名稱")).strip()
        if not code:
            continue
        row = blank(headers)
        if "ticker" in row:
            row["ticker"] = code
        if "date" in row:
            row["date"] = today
        if "market_cap" in row:
            row["market_cap"] = num_text(twse_value(r, "MarketValue", "市值"))
        if "turnover_rate" in row:
            row["turnover_rate"] = num_text(twse_value(r, "TurnoverRate", "週轉率"))
        if "pe" in row:
            row["pe"] = num_text(twse_value(r, "PEratio", "本益比"))
        if "pb" in row:
            row["pb"] = num_text(twse_value(r, "PBratio", "股價淨值比"))
        if "dividend_yield" in row:
            row["dividend_yield"] = num_text(twse_value(r, "DividendYield", "殖利率"))
        rows.append(row)
    return rows

def normalize_index_daily(raw, headers):
    rows = []
    today = datetime.now().strftime("%Y-%m-%d")
    # MI_INDEX structure may vary. Store only rows whose text fields look like market/index records.
    for idx, r in enumerate(raw):
        text = json.dumps(r, ensure_ascii=False)
        if not any(k in text for k in ["發行量加權股價指數", "TAIEX", "大盤", "指數", "Index"]):
            if idx > 20:
                continue
        row = blank(headers)
        if "index_code" in row:
            row["index_code"] = "TWSE_MI_INDEX"
        if "date" in row:
            row["date"] = str(twse_value(r, "Date", "日期"))[:10] or today
        if "name" in row:
            row["name"] = str(twse_value(r, "Name", "指數", "Index", "Type"))[:80] or "TWSE MI_INDEX"
        if "close" in row:
            row["close"] = num_text(twse_value(r, "ClosingIndex", "Close", "收盤指數", "收盤價", "Value"))
        if "volume" in row:
            row["volume"] = num_text(twse_value(r, "TradeVolume", "成交股數", "Volume"))
        if "return_1d" in row:
            row["return_1d"] = num_text(twse_value(r, "Change", "漲跌點數", "漲跌"))
        rows.append(row)
        if len(rows) >= 20:
            break
    if not rows:
        row = blank(headers)
        if "index_code" in row:
            row["index_code"] = "TWSE_MI_INDEX"
        if "date" in row:
            row["date"] = today
        if "name" in row:
            row["name"] = "TWSE MI_INDEX raw seed"
        rows.append(row)
    return rows

try:
    db_dir.mkdir(parents=True, exist_ok=True)
    header = read_json(header_path)
    plan = read_json(plan_path)
    targets = plan.get("targets", [])

    duckdb_path = db_dir / "VDF_ACTIVE_SCHEMA.duckdb"
    con = None
    if duckdb is not None:
        con = duckdb.connect(str(duckdb_path))

    for target in targets:
        table_id = str(target.get("TableId", "")).strip()
        endpoint = str(target.get("Endpoint", "")).strip()
        adapter = str(target.get("Adapter", "")).strip()

        out = {
            "table_id": table_id,
            "adapter": adapter,
            "endpoint": endpoint,
            "status": "PENDING",
            "risk": "PENDING",
            "row_count": 0,
            "csv": str(db_dir / f"{table_id}.csv"),
            "json": str(db_dir / f"{table_id}.json"),
            "parquet": str(db_dir / f"{table_id}.parquet"),
            "duckdb": str(duckdb_path),
            "message": ""
        }

        try:
            headers = table_headers(header, table_id)
            if not headers:
                raise RuntimeError(f"Headers not found for {table_id}")

            raw = fetch_json(endpoint)
            if not isinstance(raw, list):
                raise RuntimeError(f"Endpoint did not return list JSON for {table_id}")

            if table_id == "VDF_TW_EquityUniverse":
                rows = normalize_equity_universe(raw, headers)
            elif table_id == "VDF_TW_TradingStats":
                rows = normalize_trading_stats(raw, headers)
            elif table_id == "VDF_TW_IndexDaily":
                rows = normalize_index_daily(raw, headers)
            else:
                rows = []

            if pd is not None:
                df = pd.DataFrame(rows, columns=headers)
                df.to_csv(out["csv"], index=False, encoding="utf-8-sig")
                with open(out["json"], "w", encoding="utf-8") as f:
                    json.dump({
                        "table_id": table_id,
                        "adapter": adapter,
                        "endpoint": endpoint,
                        "headers": headers,
                        "row_count": int(len(df)),
                        "rows": df.fillna("").to_dict(orient="records"),
                        "status": "TWSE_OFFICIAL_SEED_FETCHED"
                    }, f, ensure_ascii=False, indent=2)
                if pyarrow_ok:
                    df.to_parquet(out["parquet"], engine="pyarrow", index=False)
                if con is not None:
                    col_defs = ", ".join([f'"{h}" VARCHAR' for h in headers])
                    con.execute(f'CREATE OR REPLACE TABLE "{table_id}" ({col_defs});')
                    if len(df) > 0:
                        df2 = df.astype(str)
                        con.register("df_tmp", df2)
                        con.execute(f'INSERT INTO "{table_id}" SELECT * FROM df_tmp;')
                        con.unregister("df_tmp")
                out["row_count"] = int(len(df))
            else:
                with open(out["csv"], "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
                    writer.writerows(rows)
                with open(out["json"], "w", encoding="utf-8") as f:
                    json.dump({
                        "table_id": table_id,
                        "adapter": adapter,
                        "endpoint": endpoint,
                        "headers": headers,
                        "row_count": len(rows),
                        "rows": rows,
                        "status": "TWSE_OFFICIAL_SEED_FETCHED"
                    }, f, ensure_ascii=False, indent=2)
                out["row_count"] = len(rows)

            if out["row_count"] > 0:
                out["status"] = "TWSE_OFFICIAL_SEED_FETCHED"
                out["risk"] = "LOW"
                out["message"] = "Official TWSE seed rows fetched and written."
            else:
                out["status"] = "TWSE_OFFICIAL_SEED_EMPTY"
                out["risk"] = "MEDIUM"
                out["message"] = "Endpoint returned no normalized rows."

            result["outputs"].append(out)

        except Exception as e:
            out["status"] = "FAIL"
            out["risk"] = "HIGH"
            out["message"] = str(e)
            result["outputs"].append(out)

    # TPEX capability probe only.
    try:
        swagger = fetch_json("https://www.tpex.org.tw/openapi/swagger.json", timeout=30)
        paths = swagger.get("paths", {}) if isinstance(swagger, dict) else {}
        interesting = []
        for p in paths.keys():
            low = p.lower()
            if any(k in low for k in ["daily", "quote", "stk", "stock", "index", "tpex"]):
                interesting.append(p)
        result["tpex_probe"]["status"] = "TPEX_SWAGGER_PROBED"
        result["tpex_probe"]["risk"] = "LOW"
        result["tpex_probe"]["paths_count"] = len(paths)
        result["tpex_probe"]["interesting_paths"] = interesting[:80]
        result["tpex_probe"]["message"] = "TPEX swagger probed. No TPEX endpoint executed in v018."
    except Exception as e:
        result["tpex_probe"]["status"] = "TPEX_SWAGGER_PROBE_WARN"
        result["tpex_probe"]["risk"] = "MEDIUM"
        result["tpex_probe"]["message"] = str(e)

    if con is not None:
        con.close()

    fail_count = sum(1 for x in result["outputs"] if x.get("risk") == "HIGH")
    warn_count = sum(1 for x in result["outputs"] if x.get("risk") == "MEDIUM")
    if result["tpex_probe"]["risk"] == "MEDIUM":
        warn_count += 1

    if fail_count:
        result["status"] = "VDF_TWSE_OFFICIAL_SEED_WITH_REVIEW"
        result["risk"] = "HIGH"
    elif warn_count:
        result["status"] = "VDF_TWSE_OFFICIAL_SEED_WITH_WARNINGS"
        result["risk"] = "MEDIUM"
    else:
        result["status"] = "VDF_TWSE_OFFICIAL_SEED_READY"
        result["risk"] = "LOW"

except Exception as e:
    result["status"] = "VDF_TWSE_OFFICIAL_SEED_FATAL"
    result["risk"] = "HIGH"
    result["errors"].append({"stage":"fatal","message":str(e),"traceback":traceback.format_exc()})

result_path.parent.mkdir(parents=True, exist_ok=True)
with result_path.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "outputs": len(result.get("outputs", [])),
    "rows": sum(int(x.get("row_count", 0) or 0) for x in result.get("outputs", [])),
    "tpex_probe": result["tpex_probe"]["status"]
}, ensure_ascii=False))
