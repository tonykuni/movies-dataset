import csv, json, os, re, sys, time, traceback
from pathlib import Path
from datetime import datetime

fetch_plan_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_PRODUCTION_FETCH_CONTROLLER_v016_20260609_220337\\registry\\VDF_ProductionFetchPlan_v016.json")
db_dir = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\DATABASE")
result_path = Path(r"C:\\Users\\tonyk\\Downloads\\VeritasIntelligenceAnalytics\\dict\\VDF\\_active\\VDF_PRODUCTION_FETCH_CONTROLLER_v016_20260609_220337\\runtime\\vdf_production_fetch_result_v016.json")
mode = "probe"
enable_network = "False".lower() == "true"

result = {
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "status": "PENDING",
    "risk": "PENDING",
    "mode": mode,
    "enable_network": enable_network,
    "database_root": str(db_dir),
    "libs": {
        "pandas": False,
        "pyarrow": False,
        "duckdb": False,
        "yfinance": False,
        "akshare": False,
        "requests": False
    },
    "outputs": [],
    "errors": []
}

def safe_table_name(x):
    return re.sub(r"[^0-9A-Za-z_]+", "_", str(x).strip())

def split_headers(x):
    return list(dict.fromkeys([h.strip() for h in str(x).split(",") if h.strip()]))

pd = None
pa = None
pq = None
duckdb = None
yf = None
akshare = None
requests = None

try:
    import pandas as pd
    result["libs"]["pandas"] = True
except Exception as e:
    result["errors"].append({"stage":"import_pandas","message":str(e)})

try:
    import pyarrow as pa
    import pyarrow.parquet as pq
    result["libs"]["pyarrow"] = True
except Exception as e:
    result["errors"].append({"stage":"import_pyarrow","message":str(e)})

try:
    import duckdb
    result["libs"]["duckdb"] = True
except Exception as e:
    result["errors"].append({"stage":"import_duckdb","message":str(e)})

try:
    import yfinance as yf
    result["libs"]["yfinance"] = True
except Exception as e:
    result["errors"].append({"stage":"import_yfinance","message":str(e)})

try:
    import akshare
    result["libs"]["akshare"] = True
except Exception as e:
    result["errors"].append({"stage":"import_akshare","message":str(e)})

try:
    import requests
    result["libs"]["requests"] = True
except Exception as e:
    result["errors"].append({"stage":"import_requests","message":str(e)})

try:
    db_dir.mkdir(parents=True, exist_ok=True)

    with fetch_plan_path.open("r", encoding="utf-8") as f:
        plan = json.load(f)

    tables = plan.get("tables", [])
    if not tables:
        raise RuntimeError("Fetch plan has no tables.")

    duckdb_path = db_dir / "VDF_ACTIVE_SCHEMA.duckdb"
    con = None
    if duckdb is not None:
        con = duckdb.connect(str(duckdb_path))

    for item in tables:
        table_id = safe_table_name(item.get("TableId"))
        headers = split_headers(item.get("Headers"))
        adapter = str(item.get("Adapter", "")).strip()
        source = str(item.get("Source", "")).strip()
        status = "PLANNED"
        risk = "LOW"
        message = ""
        rows_written = 0

        csv_path = db_dir / f"{table_id}.csv"
        json_path = db_dir / f"{table_id}.json"
        parquet_path = db_dir / f"{table_id}.parquet"

        data_rows = []

        if mode == "probe" or not enable_network:
            status = "PROBE_READY_NO_NETWORK"
            message = "Fetch controller ready. Network fetch not executed."
        elif mode == "fetch-seed" and enable_network:
            # Conservative seed fetch: only fetch safe public yfinance-style samples where applicable.
            # Other official TWSE/MOPS/FRED/AKShare adapters remain planned for dedicated adapter modules.
            try:
                if yf is not None and ("YFINANCE" in source.upper() or adapter.startswith("YFINANCE")):
                    # Minimal seed examples. This is intentionally small to avoid hang/rate issues.
                    sample_symbols = {
                        "VDF_TW_PriceDaily": "2330.TW",
                        "VDF_TW_IndexDaily": "^TWII",
                        "VDF_Global_FXRate": "USDTWD=X",
                        "VDF_Global_Commodity": "GC=F",
                        "VDF_Global_Macro": "^TNX"
                    }
                    symbol = sample_symbols.get(table_id)
                    if symbol:
                        hist = yf.download(symbol, period="5d", interval="1d", progress=False, auto_adjust=False)
                        if hist is not None and len(hist) > 0:
                            hist = hist.reset_index()
                            for _, r in hist.iterrows():
                                row = {h: "" for h in headers}
                                if "ticker" in row:
                                    row["ticker"] = symbol
                                if "symbol" in row:
                                    row["symbol"] = symbol
                                if "pair" in row:
                                    row["pair"] = symbol
                                if "index_code" in row:
                                    row["index_code"] = symbol
                                if "date" in row:
                                    row["date"] = str(r.get("Date", ""))[:10]
                                if "open" in row:
                                    row["open"] = str(r.get("Open", ""))
                                if "high" in row:
                                    row["high"] = str(r.get("High", ""))
                                if "low" in row:
                                    row["low"] = str(r.get("Low", ""))
                                if "close" in row:
                                    row["close"] = str(r.get("Close", ""))
                                if "adj_close" in row:
                                    row["adj_close"] = str(r.get("Adj Close", ""))
                                if "volume" in row:
                                    row["volume"] = str(r.get("Volume", ""))
                                if "source" in row:
                                    row["source"] = "YFINANCE"
                                if "value" in row and "close" not in headers:
                                    row["value"] = str(r.get("Close", ""))
                                data_rows.append(row)
                            status = "FETCH_SEED_OK"
                            message = f"Seed fetched via yfinance: {symbol}"
                        else:
                            status = "WARN"
                            risk = "MEDIUM"
                            message = f"No seed rows returned from yfinance: {symbol}"
                    else:
                        status = "PLANNED_ADAPTER_NOT_EXECUTED"
                        message = "No conservative seed symbol mapped for this table."
                else:
                    status = "PLANNED_ADAPTER_NOT_EXECUTED"
                    message = "Adapter requires dedicated source module or missing optional library."
            except Exception as e:
                status = "WARN"
                risk = "MEDIUM"
                message = f"Seed fetch warning: {e}"

        # Always preserve schema even if no rows.
        try:
            if pd is not None:
                df = pd.DataFrame(data_rows, columns=headers)
                rows_written = int(len(df))
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                with json_path.open("w", encoding="utf-8") as f:
                    json.dump({
                        "table_id": table_id,
                        "headers": headers,
                        "rows": data_rows,
                        "row_count": rows_written,
                        "status": status,
                        "message": message
                    }, f, ensure_ascii=False, indent=2)
                if pa is not None and pq is not None:
                    df.to_parquet(parquet_path, engine="pyarrow", index=False)
                if con is not None:
                    col_defs = ", ".join([f'"{h}" VARCHAR' for h in headers])
                    con.execute(f'CREATE OR REPLACE TABLE "{table_id}" ({col_defs});')
                    if rows_written > 0:
                        con.register("df_tmp", df)
                        con.execute(f'INSERT INTO "{table_id}" SELECT * FROM df_tmp;')
                        con.unregister("df_tmp")
            else:
                with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    for row in data_rows:
                        writer.writerow([row.get(h, "") for h in headers])
                with json_path.open("w", encoding="utf-8") as f:
                    json.dump({
                        "table_id": table_id,
                        "headers": headers,
                        "rows": data_rows,
                        "row_count": len(data_rows),
                        "status": status,
                        "message": message
                    }, f, ensure_ascii=False, indent=2)

            result["outputs"].append({
                "table_id": table_id,
                "adapter": adapter,
                "source": source,
                "status": status,
                "risk": risk,
                "row_count": rows_written,
                "csv": str(csv_path),
                "json": str(json_path),
                "parquet": str(parquet_path),
                "duckdb": str(duckdb_path),
                "message": message
            })
        except Exception as e:
            result["outputs"].append({
                "table_id": table_id,
                "adapter": adapter,
                "source": source,
                "status": "FAIL",
                "risk": "HIGH",
                "row_count": rows_written,
                "csv": str(csv_path),
                "json": str(json_path),
                "parquet": str(parquet_path),
                "duckdb": str(duckdb_path),
                "message": str(e)
            })

    if con is not None:
        con.close()

    fail_count = sum(1 for x in result["outputs"] if x.get("status") == "FAIL")
    warn_count = sum(1 for x in result["outputs"] if x.get("risk") == "MEDIUM")

    if fail_count:
        result["status"] = "VDF_PRODUCTION_FETCH_CONTROLLER_WITH_REVIEW"
        result["risk"] = "HIGH"
    elif warn_count:
        result["status"] = "VDF_PRODUCTION_FETCH_CONTROLLER_WITH_WARNINGS"
        result["risk"] = "MEDIUM"
    else:
        result["status"] = "VDF_PRODUCTION_FETCH_CONTROLLER_READY"
        result["risk"] = "LOW"

except Exception as e:
    result["status"] = "VDF_PRODUCTION_FETCH_CONTROLLER_FATAL"
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
    "mode": result["mode"],
    "enable_network": result["enable_network"]
}, ensure_ascii=False))
