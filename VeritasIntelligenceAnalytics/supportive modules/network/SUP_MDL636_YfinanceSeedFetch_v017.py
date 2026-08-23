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
import json, re, traceback
from pathlib import Path
from datetime import datetime

root = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics")
db_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
header_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_ssot\\VDF_DataScope_HeaderRegistry_SSOT.json")
plan_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_YFINANCE_SEED_FETCH_v017_20260609_221249\\registry\\VDF_YFinanceSeedFetch_TargetPlan_v017.json")
result_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_YFINANCE_SEED_FETCH_v017_20260609_221249\\runtime\\vdf_yfinance_seed_fetch_result_v017.json")
days = int("10")

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "PENDING",
    "risk": "PENDING",
    "days": days,
    "database_root": str(db_dir),
    "libs": {
        "yfinance": False,
        "pandas": False,
        "pyarrow": False,
        "duckdb": False
    },
    "outputs": [],
    "errors": []
}

def read_json(p):
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)

def safe_scalar(x):
    try:
        if hasattr(x, "item"):
            return x.item()
    except Exception:
        pass
    return x

def safe_float(x):
    try:
        x = safe_scalar(x)
        if x is None:
            return ""
        s = str(x)
        if s.lower() in ("nan", "nat", "none"):
            return ""
        return float(x)
    except Exception:
        return ""

def safe_int(x):
    try:
        x = safe_scalar(x)
        if x is None:
            return ""
        s = str(x)
        if s.lower() in ("nan", "nat", "none"):
            return ""
        return int(float(x))
    except Exception:
        return ""

def split_headers(x):
    return [h.strip() for h in str(x).split(",") if h.strip()]

def make_blank(headers):
    return {h: "" for h in headers}

pd = None
yf = None
duckdb = None
pyarrow_ok = False

try:
    import pandas as pd
    result["libs"]["pandas"] = True
except Exception as e:
    result["errors"].append({"stage":"import_pandas","message":str(e)})

try:
    import yfinance as yf
    result["libs"]["yfinance"] = True
except Exception as e:
    result["errors"].append({"stage":"import_yfinance","message":str(e)})

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
    if pd is None:
        raise RuntimeError("pandas is required for v017 seed fetch.")
    if yf is None:
        raise RuntimeError("yfinance is required for v017 seed fetch.")

    db_dir.mkdir(parents=True, exist_ok=True)

    header = read_json(header_path)
    plan = read_json(plan_path)

    tables = header.get("tables", [])
    table_map = {str(t.get("TableId","")).strip(): t for t in tables}
    targets = plan.get("targets", [])

    duckdb_path = db_dir / "VDF_ACTIVE_SCHEMA.duckdb"
    con = None
    if duckdb is not None:
        con = duckdb.connect(str(duckdb_path))

    for target in targets:
        table_id = str(target.get("TableId","")).strip()
        symbols = target.get("Symbols", [])
        kind = str(target.get("Kind","")).strip()
        table_meta = table_map.get(table_id)

        out = {
            "table_id": table_id,
            "symbols": symbols,
            "kind": kind,
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
            if not table_meta:
                out["status"] = "FAIL"
                out["risk"] = "HIGH"
                out["message"] = "Table metadata not found in Header Registry."
                result["outputs"].append(out)
                continue

            headers = split_headers(table_meta.get("Headers", ""))
            rows = []

            for symbol in symbols:
                hist = yf.download(symbol, period=f"{days}d", interval="1d", progress=False, auto_adjust=False, threads=False)
                if hist is None or len(hist) == 0:
                    out["message"] += f"No data returned for {symbol}; "
                    continue

                hist = hist.reset_index()

                for _, r in hist.iterrows():
                    row = make_blank(headers)

                    date_value = r.get("Date", "")
                    date_text = str(date_value)[:10]

                    if "ticker" in row:
                        row["ticker"] = symbol
                    if "symbol" in row:
                        row["symbol"] = symbol
                    if "pair" in row:
                        row["pair"] = symbol
                    if "index_code" in row:
                        row["index_code"] = symbol
                    if "code" in row:
                        row["code"] = symbol
                    if "date" in row:
                        row["date"] = date_text
                    if "source" in row:
                        row["source"] = "YFINANCE"
                    if "frequency" in row:
                        row["frequency"] = "DAILY"

                    if "open" in row:
                        row["open"] = safe_float(r.get("Open", ""))
                    if "high" in row:
                        row["high"] = safe_float(r.get("High", ""))
                    if "low" in row:
                        row["low"] = safe_float(r.get("Low", ""))
                    if "close" in row:
                        row["close"] = safe_float(r.get("Close", ""))
                    if "adj_close" in row:
                        row["adj_close"] = safe_float(r.get("Adj Close", ""))
                    if "volume" in row:
                        row["volume"] = safe_int(r.get("Volume", ""))
                    if "value" in row:
                        row["value"] = safe_float(r.get("Close", ""))
                    if "unit" in row:
                        row["unit"] = "INDEX_OR_PRICE"
                    if "description" in row:
                        row["description"] = f"YFinance seed: {symbol}"
                    if "name" in row and not row["name"]:
                        row["name"] = symbol

                    rows.append(row)

            df = pd.DataFrame(rows, columns=headers)

            csv_path = Path(out["csv"])
            json_path = Path(out["json"])
            parquet_path = Path(out["parquet"])

            df.to_csv(csv_path, index=False, encoding="utf-8-sig")

            with json_path.open("w", encoding="utf-8") as f:
                json.dump({
                    "table_id": table_id,
                    "symbols": symbols,
                    "kind": kind,
                    "headers": headers,
                    "row_count": int(len(df)),
                    "rows": df.fillna("").to_dict(orient="records"),
                    "status": "YFINANCE_SEED_FETCHED"
                }, f, ensure_ascii=False, indent=2)

            if pyarrow_ok:
                df.to_parquet(parquet_path, engine="pyarrow", index=False)

            if con is not None:
                col_defs = ", ".join([f'"{h}" VARCHAR' for h in headers])
                con.execute(f'CREATE OR REPLACE TABLE "{table_id}" ({col_defs});')
                if len(df) > 0:
                    df2 = df.astype(str)
                    con.register("df_tmp", df2)
                    con.execute(f'INSERT INTO "{table_id}" SELECT * FROM df_tmp;')
                    con.unregister("df_tmp")

            out["row_count"] = int(len(df))

            if len(df) > 0:
                out["status"] = "YFINANCE_SEED_FETCHED"
                out["risk"] = "LOW"
                out["message"] = out["message"] + "Seed rows fetched and written."
            else:
                out["status"] = "YFINANCE_SEED_EMPTY"
                out["risk"] = "MEDIUM"
                out["message"] = out["message"] + "No seed rows fetched."

            result["outputs"].append(out)

        except Exception as e:
            out["status"] = "FAIL"
            out["risk"] = "HIGH"
            out["message"] = str(e)
            result["outputs"].append(out)

    if con is not None:
        con.close()

    fail_count = sum(1 for x in result["outputs"] if x.get("risk") == "HIGH" or x.get("status") == "FAIL")
    warn_count = sum(1 for x in result["outputs"] if x.get("risk") == "MEDIUM")

    if fail_count:
        result["status"] = "VDF_YFINANCE_SEED_FETCH_WITH_REVIEW"
        result["risk"] = "HIGH"
    elif warn_count:
        result["status"] = "VDF_YFINANCE_SEED_FETCH_WITH_WARNINGS"
        result["risk"] = "MEDIUM"
    else:
        result["status"] = "VDF_YFINANCE_SEED_FETCH_READY"
        result["risk"] = "LOW"

except Exception as e:
    result["status"] = "VDF_YFINANCE_SEED_FETCH_FATAL"
    result["risk"] = "HIGH"
    result["errors"].append({
        "stage": "fatal",
        "message": str(e),
        "traceback": traceback.format_exc()
    })

result_path.parent.mkdir(parents=True, exist_ok=True)
with result_path.open("w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(json.dumps({
    "status": result["status"],
    "risk": result["risk"],
    "outputs": len(result.get("outputs", [])),
    "rows": sum(int(x.get("row_count", 0) or 0) for x in result.get("outputs", [])),
    "libs": result["libs"]
}, ensure_ascii=False))
