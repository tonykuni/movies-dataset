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
import os, sys, json, re, glob, hashlib, shutil
from datetime import datetime
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb

project_root = sys.argv[1]
active_pointer_path = sys.argv[2]
extra_inventory_json = sys.argv[3]
database_root = sys.argv[4]
runtime_json = sys.argv[5]
dataflow_json = sys.argv[6]
basic_out = sys.argv[7]
financial_out = sys.argv[8]
duckdb_out = sys.argv[9]
write_duckdb = sys.argv[10].lower() == "true"
run_root = sys.argv[11]

def now():
    return datetime.now().isoformat()

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def safe_read_parquet(path):
    if not path or not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_parquet(path)

def write_parquet_atomic(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    df.to_parquet(tmp, index=False, compression="zstd")
    if os.path.exists(path):
        bak = path + ".bak_" + datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(path, bak)
    os.replace(tmp, path)

def clean_name(x):
    return re.sub(r"[^a-z0-9]+", "_", str(x or "").strip().lower()).strip("_")

def colmap(df):
    return {clean_name(c): c for c in df.columns}

def first_col(df, candidates):
    cm = colmap(df)
    for c in candidates:
        k = clean_name(c)
        if k in cm:
            return cm[k]
    return None

def get_series(df, candidates, default=""):
    c = first_col(df, candidates)
    if c is None:
        return pd.Series([default] * len(df), index=df.index, dtype="object")
    return df[c].fillna("").astype(str)

def sha1_text(s, n=20):
    return hashlib.sha1(str(s).encode("utf-8", "ignore")).hexdigest()[:n]

def record_hash(row, keys):
    raw = "|".join(str(row.get(k, "")) for k in keys)
    return sha1_text(raw, 40)

def extract_ticker_from_text(text):
    # 四碼，第一碼不可 0；2021~2030 先視為 year guard，不直接當 ticker
    if not text:
        return ""
    candidates = re.findall(r"(?<!\d)([1-9]\d{3})(?!\d)", str(text))
    for t in candidates:
        if t in [str(y) for y in range(2021, 2031)]:
            continue
        return t
    return ""

def dedup_df(df, subset=None):
    if df.empty:
        return df
    df = df.copy()
    df = df.astype(str).fillna("")
    if subset:
        valid = [c for c in subset if c in df.columns]
        if valid:
            return df.drop_duplicates(subset=valid, keep="last").reset_index(drop=True)
    return df.drop_duplicates(keep="last").reset_index(drop=True)

def normalize_basicinfo(df, source_path, source_stage):
    target_cols = [
        "report_id","file_id","report_date","report_code","broker","analyst",
        "tw_ticker","tw_yfinance_ticker","tw_bloomberg_ticker","company_name",
        "rating","target_price","last_adj_close","last_data_date",
        "yf_consensus_tp_low","yf_consensus_tp_mean","yf_consensus_tp_median","yf_consensus_tp_high",
        "yf_rating_breakdown","yf_analyst_count_breakdown",
        "validation_status","source_path","source_stage","ingested_at","record_hash"
    ]
    if df.empty:
        return pd.DataFrame(columns=target_cols)

    out = pd.DataFrame(index=df.index)
    out["report_id"] = get_series(df, ["report_id","ReportID","Report Id"])
    out["file_id"] = get_series(df, ["file_id","FileID","File Id"])
    out["report_date"] = get_series(df, ["report_date","Report Date","date","as_of_date"])
    out["report_code"] = get_series(df, ["report_code","Report Code","code"])
    out["broker"] = get_series(df, ["broker","Broker","source_broker"])
    out["analyst"] = get_series(df, ["analyst","Analyst"])
    out["tw_ticker"] = get_series(df, ["tw_ticker","ticker","Ticker","TW_TICKER"])
    out["tw_yfinance_ticker"] = get_series(df, ["tw_yfinance_ticker","YFinance Ticker","yf_ticker","yfinance_ticker"])
    out["tw_bloomberg_ticker"] = get_series(df, ["tw_bloomberg_ticker","Bloomberg Ticker","bloomberg_ticker"])
    out["company_name"] = get_series(df, ["company_name","Name","name","公司名稱","公司簡稱"])
    out["rating"] = get_series(df, ["rating","Rating","投資評等"])
    out["target_price"] = get_series(df, ["target_price","Target Price","TP","目標價"])
    out["last_adj_close"] = get_series(df, ["last_adj_close","Last Adj Close","YFinance Latest Adj Close"])
    out["last_data_date"] = get_series(df, ["last_data_date","Last Data Date"])
    out["yf_consensus_tp_low"] = get_series(df, ["yf_consensus_tp_low","YFinance Consensus Target Price Low","YF Consensus TP Low"])
    out["yf_consensus_tp_mean"] = get_series(df, ["yf_consensus_tp_mean","YFinance Consensus Target Price Mean","YF Consensus TP Mean"])
    out["yf_consensus_tp_median"] = get_series(df, ["yf_consensus_tp_median","YFinance Consensus Target Price Median","YF Consensus TP Median"])
    out["yf_consensus_tp_high"] = get_series(df, ["yf_consensus_tp_high","YFinance Consensus Target Price High","YF Consensus TP High"])
    out["yf_rating_breakdown"] = get_series(df, ["yf_rating_breakdown","YFinance Rating Breakdown"])
    out["yf_analyst_count_breakdown"] = get_series(df, ["yf_analyst_count_breakdown","YFinance Analyst Count Breakdown"])
    out["validation_status"] = get_series(df, ["validation_status","Validation Status"])

    # derive ticker from filename/path if empty
    path_s = get_series(df, ["path","source_path","pdf_path","filename","file_name","Filename"])
    for i in out.index:
        if not out.at[i, "tw_ticker"]:
            out.at[i, "tw_ticker"] = extract_ticker_from_text(path_s.at[i])
        if not out.at[i, "report_id"]:
            raw = "|".join([out.at[i,"file_id"], path_s.at[i], out.at[i,"tw_ticker"], out.at[i,"report_date"], out.at[i,"broker"]])
            out.at[i, "report_id"] = sha1_text(raw, 20)
        if not out.at[i, "tw_bloomberg_ticker"] and out.at[i, "tw_ticker"]:
            out.at[i, "tw_bloomberg_ticker"] = out.at[i, "tw_ticker"] + " TT"
        if not out.at[i, "validation_status"]:
            out.at[i, "validation_status"] = "STAGE_READY"

    out["source_path"] = source_path
    out["source_stage"] = source_stage
    out["ingested_at"] = now()
    out["record_hash"] = out.apply(lambda r: record_hash(r, ["report_id","file_id","tw_ticker","report_date","broker","rating","target_price"]), axis=1)

    out = out[target_cols]
    out = dedup_df(out, ["record_hash"])
    return out

def find_financial_candidates(project_root, exclude_paths):
    pats = [
        "**/*StockReportFinancialData*.parquet",
        "**/*ReportFinancial*.parquet",
        "**/*FinancialData*.parquet",
        "**/*financial_validated*.parquet",
        "**/*FinancialMatrix*.parquet"
    ]
    out = []
    for pat in pats:
        out.extend(glob.glob(os.path.join(project_root, pat), recursive=True))
    cleaned = []
    for p in out:
        lp = p.lower()
        if any(os.path.abspath(p) == os.path.abspath(x) for x in exclude_paths if x):
            continue
        if any(x in lp for x in ["financialaccountaliasssot", "financialvalidationrulesssot", "ssot", "runtime", "matrix_v029ssot"]):
            continue
        if os.path.exists(p) and p not in cleaned:
            cleaned.append(p)
    return sorted(cleaned, key=lambda x: os.path.getmtime(x), reverse=True)

def normalize_financialdata(frames):
    target_cols = [
        "report_id","file_id","tw_ticker","company_name","broker","report_date",
        "period","fiscal_year","fiscal_quarter","statement",
        "account_canonical","account_alias","value","unit","currency",
        "source_table_id","source_page",
        "historical_check_confidence","historical_check",
        "add_sub_check_confidence","add_sub_check",
        "division_check_confidence","division_check",
        "final_trust_confidence","final_trust_band",
        "validation_status","source_stage","source_path","ingested_at","record_hash"
    ]
    if not frames:
        return pd.DataFrame(columns=target_cols)

    rows = []
    for df, source_path in frames:
        if df.empty:
            continue
        d = pd.DataFrame(index=df.index)
        d["report_id"] = get_series(df, ["report_id","ReportID","Report Id"])
        d["file_id"] = get_series(df, ["file_id","FileID","File Id"])
        d["tw_ticker"] = get_series(df, ["tw_ticker","ticker","Ticker","TW_TICKER"])
        d["company_name"] = get_series(df, ["company_name","Name","name"])
        d["broker"] = get_series(df, ["broker","Broker"])
        d["report_date"] = get_series(df, ["report_date","Report Date"])
        d["period"] = get_series(df, ["period","Period"])
        d["fiscal_year"] = get_series(df, ["fiscal_year","Year","year"])
        d["fiscal_quarter"] = get_series(df, ["fiscal_quarter","Quarter","quarter"])
        d["statement"] = get_series(df, ["statement","Category","category"])
        d["account_canonical"] = get_series(df, ["account_canonical","Canonical Data","canonical_data","canonical","Data"])
        d["account_alias"] = get_series(df, ["account_alias","Data","raw_account","label"])
        d["value"] = get_series(df, ["value","Value","Value Numeric","value_numeric"])
        d["unit"] = get_series(df, ["unit","Unit"])
        d["currency"] = get_series(df, ["currency","Currency"])
        d["source_table_id"] = get_series(df, ["source_table_id","table_id","TableID"])
        d["source_page"] = get_series(df, ["source_page","page","Page"])
        d["historical_check_confidence"] = get_series(df, ["historical_check_confidence","Historical Check Confidence"])
        d["historical_check"] = get_series(df, ["historical_check","Historical Check"])
        d["add_sub_check_confidence"] = get_series(df, ["add_sub_check_confidence","Add/Sub Check Confidence"])
        d["add_sub_check"] = get_series(df, ["add_sub_check","Add/Sub Check"])
        d["division_check_confidence"] = get_series(df, ["division_check_confidence","Division Check Confidence"])
        d["division_check"] = get_series(df, ["division_check","Division Check"])
        d["final_trust_confidence"] = get_series(df, ["final_trust_confidence","Final Trust Confidence"])
        d["final_trust_band"] = get_series(df, ["final_trust_band","Final Trust Band"])
        d["validation_status"] = get_series(df, ["validation_status","Validation Status"])
        d["source_stage"] = "FINANCIAL_CANDIDATE"
        d["source_path"] = source_path
        d["ingested_at"] = now()

        for i in d.index:
            if not d.at[i,"tw_ticker"]:
                d.at[i,"tw_ticker"] = extract_ticker_from_text(str(d.at[i,"source_path"]))
            if not d.at[i,"report_id"]:
                raw = "|".join([d.at[i,"file_id"], d.at[i,"tw_ticker"], d.at[i,"report_date"], d.at[i,"broker"]])
                d.at[i,"report_id"] = sha1_text(raw, 20)
            if not d.at[i,"validation_status"]:
                d.at[i,"validation_status"] = "STAGE_READY"

        d["record_hash"] = d.apply(lambda r: record_hash(r, ["report_id","tw_ticker","fiscal_year","fiscal_quarter","statement","account_canonical","value","unit"]), axis=1)
        rows.append(d[target_cols])

    if not rows:
        return pd.DataFrame(columns=target_cols)

    out = pd.concat(rows, ignore_index=True)
    out = dedup_df(out, ["record_hash"])
    return out

def incremental_merge(existing_path, new_df, subset):
    if os.path.exists(existing_path):
        old = safe_read_parquet(existing_path)
        merged = pd.concat([old, new_df], ignore_index=True)
    else:
        merged = new_df.copy()
    merged = dedup_df(merged, subset)
    return merged

def dedup_ssot_tables(pointer, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    results = []
    tables = pointer.get("ssot_tables", {}) or {}
    for name, path in tables.items():
        if not path or not os.path.exists(path):
            results.append({"name":name,"status":"MISSING","path":path,"rows_in":0,"rows_out":0})
            continue
        try:
            df = pd.read_parquet(path).astype(str).fillna("")
            rows_in = len(df)
            df2 = dedup_df(df)
            rows_out = len(df2)
            out_path = os.path.join(out_dir, f"{name}_dedup.parquet")
            df2.to_parquet(out_path, index=False, compression="zstd")
            results.append({"name":name,"status":"DEDUPED","path":path,"out_path":out_path,"rows_in":rows_in,"rows_out":rows_out})
        except Exception as e:
            results.append({"name":name,"status":"ERROR","path":path,"error":str(e),"rows_in":0,"rows_out":0})
    return results

pointer = read_json(active_pointer_path)
extra_inventory = read_json(extra_inventory_json)

basic_candidate = pointer.get("latest_basic_info_parquet","")
text_candidate = pointer.get("latest_report_text_parquet","")
table_allowed = bool(pointer.get("table_staging_allowed", False))
canonical_allowed = bool(pointer.get("canonical_allowed", False))

ssot_dedup_dir = os.path.join(database_root, "_ssot_dedup")
ssot_dedup_results = dedup_ssot_tables(pointer, ssot_dedup_dir)

# Build BasicInfo output
basic_src = safe_read_parquet(basic_candidate)
basic_new = normalize_basicinfo(basic_src, basic_candidate, "VRN_ACTIVE_POINTER_BASICINFO")
basic_final = incremental_merge(basic_out, basic_new, ["record_hash"])
write_parquet_atomic(basic_final, basic_out)

# Build FinancialData output
financial_candidates = find_financial_candidates(project_root, [financial_out])
frames = []
for p in financial_candidates[:20]:
    try:
        frames.append((safe_read_parquet(p), p))
    except Exception:
        pass

financial_new = normalize_financialdata(frames)
financial_pending_reason = ""
if financial_new.empty:
    financial_pending_reason = "No existing FinancialData parquet candidate found. StockReportFinancialData schema created and waits for VRN 1D table extraction staging."

financial_final = incremental_merge(financial_out, financial_new, ["record_hash"])
write_parquet_atomic(financial_final, financial_out)

# Audit CSV samples only
audit_dir = os.path.join(run_root, "audit")
os.makedirs(audit_dir, exist_ok=True)
basic_final.head(300).to_csv(os.path.join(audit_dir, "StockReportBasicInfo_AuditSample.csv"), index=False, encoding="utf-8-sig")
financial_final.head(300).to_csv(os.path.join(audit_dir, "StockReportFinancialData_AuditSample.csv"), index=False, encoding="utf-8-sig")

# JSON dataflow manifest
tests = []
def add_test(name, status, value, path, message):
    tests.append({"name":name,"status":status,"value":value,"path":path,"message":message})

# Parquet tests
try:
    b_rows = pq.ParquetFile(basic_out).metadata.num_rows
    add_test("Parquet BasicInfo Readback", "PASS" if b_rows == len(basic_final) else "WARN", b_rows, basic_out, "BasicInfo parquet readback count.")
except Exception as e:
    add_test("Parquet BasicInfo Readback", "FAIL", str(e), basic_out, "BasicInfo parquet readback failed.")

try:
    f_rows = pq.ParquetFile(financial_out).metadata.num_rows
    add_test("Parquet FinancialData Readback", "PASS" if f_rows == len(financial_final) else "WARN", f_rows, financial_out, "FinancialData parquet readback count.")
except Exception as e:
    add_test("Parquet FinancialData Readback", "FAIL", str(e), financial_out, "FinancialData parquet readback failed.")

# Hash uniqueness tests
basic_dup = int(basic_final["record_hash"].duplicated().sum()) if "record_hash" in basic_final.columns and not basic_final.empty else 0
financial_dup = int(financial_final["record_hash"].duplicated().sum()) if "record_hash" in financial_final.columns and not financial_final.empty else 0
add_test("BasicInfo Incremental Dedup", "PASS" if basic_dup == 0 else "FAIL", basic_dup, basic_out, "record_hash duplicates in BasicInfo.")
add_test("FinancialData Incremental Dedup", "PASS" if financial_dup == 0 else "FAIL", financial_dup, financial_out, "record_hash duplicates in FinancialData.")

duckdb_status = "SKIPPED"
duckdb_tests = []
if write_duckdb:
    try:
        con = duckdb.connect(duckdb_out)
        con.execute("CREATE OR REPLACE TABLE StockReportBasicInfo AS SELECT * FROM read_parquet(?)", [basic_out])
        con.execute("CREATE OR REPLACE TABLE StockReportFinancialData AS SELECT * FROM read_parquet(?)", [financial_out])
        con.execute("CREATE OR REPLACE VIEW vw_StockReportBasicInfo AS SELECT * FROM StockReportBasicInfo")
        con.execute("CREATE OR REPLACE VIEW vw_StockReportFinancialData AS SELECT * FROM StockReportFinancialData")
        bc = con.execute("SELECT COUNT(*) FROM StockReportBasicInfo").fetchone()[0]
        fc = con.execute("SELECT COUNT(*) FROM StockReportFinancialData").fetchone()[0]
        con.close()
        duckdb_status = "READY"
        duckdb_tests.append({"name":"DuckDB BasicInfo Count","status":"PASS" if bc == len(basic_final) else "WARN","value":bc})
        duckdb_tests.append({"name":"DuckDB FinancialData Count","status":"PASS" if fc == len(financial_final) else "WARN","value":fc})
    except Exception as e:
        duckdb_status = "FAILED"
        duckdb_tests.append({"name":"DuckDB Build","status":"FAIL","value":str(e)})

for t in duckdb_tests:
    add_test(t["name"], t["status"], t["value"], duckdb_out, "DuckDB serving layer test.")

hard_blocks = sum(1 for t in tests if t["status"] == "FAIL")
warnings = sum(1 for t in tests if t["status"] == "WARN")
status = "VRN_STOCKREPORT_INCREMENTAL_OUTPUT_READY"
risk = "LOW"

if hard_blocks > 0:
    status = "VRN_STOCKREPORT_INCREMENTAL_OUTPUT_REVIEW_REQUIRED"
    risk = "HIGH"
elif financial_pending_reason or warnings > 0 or not canonical_allowed:
    status = "VRN_STOCKREPORT_INCREMENTAL_OUTPUT_READY_WITH_REVIEW"
    risk = "MEDIUM"

dataflow = {
    "generated_at": now(),
    "version": "v029.SSOT.1D",
    "status": status,
    "risk": risk,
    "json_role": "dataflow manifest / runtime / control-plane only",
    "parquet_role": "truth source / payload storage",
    "duckdb_role": "serving layer, rebuildable from parquet",
    "active_pointer": active_pointer_path,
    "table_staging_allowed": table_allowed,
    "canonical_allowed": canonical_allowed,
    "basic_candidate": basic_candidate,
    "text_candidate": text_candidate,
    "financial_candidates": financial_candidates[:20],
    "financial_pending_reason": financial_pending_reason,
    "outputs": {
        "StockReportBasicInfo.parquet": basic_out,
        "StockReportFinancialData.parquet": financial_out,
        "VRN_StockReport.duckdb": duckdb_out if write_duckdb else ""
    },
    "counts": {
        "basicinfo_new_rows": len(basic_new),
        "basicinfo_total_rows": len(basic_final),
        "financialdata_new_rows": len(financial_new),
        "financialdata_total_rows": len(financial_final),
        "ssot_dedup_tables": len(ssot_dedup_results)
    },
    "tests": tests,
    "ssot_dedup_results": ssot_dedup_results,
    "extra_inventory": extra_inventory
}
write_json(dataflow_json, dataflow)

runtime = {
    "generated_at": now(),
    "status": status,
    "risk": risk,
    "hard_blocks": hard_blocks,
    "warnings": warnings,
    "basicinfo_rows": len(basic_final),
    "basicinfo_new_rows": len(basic_new),
    "financialdata_rows": len(financial_final),
    "financialdata_new_rows": len(financial_new),
    "financial_pending_reason": financial_pending_reason,
    "duckdb_status": duckdb_status,
    "duckdb_path": duckdb_out if write_duckdb else "",
    "basicinfo_parquet": basic_out,
    "financialdata_parquet": financial_out,
    "dataflow_json": dataflow_json,
    "ssot_dedup_dir": ssot_dedup_dir,
    "financial_candidates_count": len(financial_candidates),
    "tests": tests,
    "next_step": "Run VRN 1D table extraction staging to populate StockReportFinancialData if financial rows are pending. Do not canonical promote yet."
}
write_json(runtime_json, runtime)
print(json.dumps(runtime, ensure_ascii=False))