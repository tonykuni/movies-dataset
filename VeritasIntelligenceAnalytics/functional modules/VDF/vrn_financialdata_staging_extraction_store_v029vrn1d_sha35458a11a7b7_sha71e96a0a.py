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
import os, sys, json, re, hashlib, shutil
from datetime import datetime
import pandas as pd
import pyarrow.parquet as pq
import duckdb

project_root = sys.argv[1]
active_pointer_path = sys.argv[2]
basicinfo_parquet = sys.argv[3]
financial_db_parquet = sys.argv[4]
stage_financial_parquet = sys.argv[5]
audit_csv = sys.argv[6]
duckdb_path = sys.argv[7]
runtime_json = sys.argv[8]
dataflow_json = sys.argv[9]
write_duckdb = sys.argv[10].lower() == "true"

def now():
    return datetime.now().isoformat()

def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def write_json(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def sha1_text(s, n=40):
    return hashlib.sha1(str(s).encode("utf-8", "ignore")).hexdigest()[:n]

def safe_read_parquet(path):
    if not path or not os.path.exists(path):
        return pd.DataFrame()
    return pd.read_parquet(path).astype(str).fillna("")

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

def pick_col(df, names):
    cmap = {clean_name(c): c for c in df.columns}
    for n in names:
        k = clean_name(n)
        if k in cmap:
            return cmap[k]
    return ""

def extract_year(text):
    s = str(text or "")
    m = re.search(r"(20\d{2}|19\d{2})", s)
    if m:
        return m.group(1)
    m = re.search(r"\b(1[01]\d)\b", s)
    if m:
        return str(int(m.group(1)) + 1911)
    return ""

def extract_quarter(text):
    s = str(text or "")
    m = re.search(r"\bQ([1-4])\b|第?\s*([一二三四1234])\s*季", s, re.I)
    if not m:
        return ""
    q = m.group(1) or m.group(2)
    zh = {"一":"1","二":"2","三":"3","四":"4"}
    q = zh.get(q, q)
    return "Q" + str(q)

def normalize_number(x):
    s = str(x or "").strip()
    if not s:
        return ""
    s = s.replace(",", "").replace("％", "%").replace("NT$", "").replace("NTD", "").replace("新台幣", "")
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    s = re.sub(r"[^\d\.\-\+%]", "", s)
    if s.endswith("%"):
        s = s[:-1]
    try:
        v = float(s)
        if neg:
            v = -v
        return str(v)
    except Exception:
        return ""

def extract_numbers(text):
    s = str(text or "")
    # avoid pure years as value
    vals = []
    for m in re.finditer(r"(?<![A-Za-z0-9])[-+]?\(?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?%?(?![A-Za-z0-9])|(?<![A-Za-z0-9])[-+]?\d+(?:\.\d+)?%?(?![A-Za-z0-9])", s):
        raw = m.group(0)
        clean = raw.replace(",", "").replace("%", "").replace("(", "").replace(")", "")
        if clean in [str(y) for y in range(1990, 2035)]:
            continue
        num = normalize_number(raw)
        if num != "":
            vals.append((raw, num))
    return vals

def infer_statement(canonical):
    c = str(canonical or "").lower()
    if c in {"revenue","net_sales","gross_profit","operating_expense","selling_expense","admin_expense","r_and_d_expense","operating_income","pretax_income","tax_expense","net_income","eps"}:
        return "IS"
    if c in {"cash_and_equivalents","accounts_receivable","inventory","current_assets","ppe","total_assets","accounts_payable","current_liabilities","long_term_debt","total_liabilities","share_capital","retained_earnings","total_equity"}:
        return "BS"
    if c in {"cfo","capex","cfi","cff","fcf"}:
        return "CF"
    if c in {"gross_margin","operating_margin","net_margin","roe","roa","debt_ratio","current_ratio"}:
        return "RATIO"
    return ""

def value_unit(text, alias, canonical):
    s = str(text or "")
    if "%" in s or str(canonical).lower() in {"gross_margin","operating_margin","net_margin","roe","roa","debt_ratio","current_ratio"}:
        return "%"
    if re.search(r"\b(x|倍)\b", s, re.I):
        return "x"
    if re.search(r"EPS|每股", s, re.I):
        return "TWD/share"
    if re.search(r"百萬|mn|million", s, re.I):
        return "mn"
    if re.search(r"千元|thousand", s, re.I):
        return "thousand"
    return ""

def record_hash(row):
    keys = ["report_id","file_id","tw_ticker","fiscal_year","fiscal_quarter","statement","account_canonical","value","source_text_hash"]
    raw = "|".join(str(row.get(k,"")) for k in keys)
    return sha1_text(raw, 40)

pointer = read_json(active_pointer_path)
basic = safe_read_parquet(basicinfo_parquet)

report_text_path = pointer.get("latest_report_text_parquet", "")
ssot_tables = pointer.get("ssot_tables", {}) or {}
financial_alias_path = ssot_tables.get("financial_alias", "")
validation_rules_path = ssot_tables.get("validation_rules", "")

text_df = safe_read_parquet(report_text_path)
alias_df = safe_read_parquet(financial_alias_path)
rules_df = safe_read_parquet(validation_rules_path)

# Build BasicInfo lookup
basic_report_col = pick_col(basic, ["report_id"])
basic_file_col = pick_col(basic, ["file_id"])
basic_ticker_col = pick_col(basic, ["tw_ticker","ticker"])
basic_name_col = pick_col(basic, ["company_name","name"])
basic_broker_col = pick_col(basic, ["broker"])
basic_date_col = pick_col(basic, ["report_date"])

basic_by_report = {}
basic_by_file = {}
for _, r in basic.iterrows():
    item = {
        "report_id": r.get(basic_report_col, "") if basic_report_col else "",
        "file_id": r.get(basic_file_col, "") if basic_file_col else "",
        "tw_ticker": r.get(basic_ticker_col, "") if basic_ticker_col else "",
        "company_name": r.get(basic_name_col, "") if basic_name_col else "",
        "broker": r.get(basic_broker_col, "") if basic_broker_col else "",
        "report_date": r.get(basic_date_col, "") if basic_date_col else ""
    }
    if item["report_id"]:
        basic_by_report[item["report_id"]] = item
    if item["file_id"]:
        basic_by_file[item["file_id"]] = item

# Detect ReportText columns
text_col = pick_col(text_df, ["text","Text","line_text","content","sentence","cell_text","raw_text"])
report_col = pick_col(text_df, ["report_id"])
file_col = pick_col(text_df, ["file_id"])
page_col = pick_col(text_df, ["page","Page","page_no","PageNo"])
source_col = pick_col(text_df, ["source_path","path","pdf_path","file_path","filename","file_name"])

# Alias rows
aliases = []
for _, r in alias_df.iterrows():
    canonical = r.get("canonical","") or r.get("account_canonical","")
    alias = r.get("alias","") or r.get("account_alias","")
    statement = r.get("statement","") or infer_statement(canonical)
    if str(alias).strip() and str(canonical).strip():
        aliases.append({
            "canonical": str(canonical).strip(),
            "alias": str(alias).strip(),
            "statement": str(statement).strip()
        })

# Sort longest alias first to avoid short overmatch
aliases.sort(key=lambda x: len(x["alias"]), reverse=True)

target_cols = [
    "report_id","file_id","tw_ticker","company_name","broker","report_date",
    "period","fiscal_year","fiscal_quarter","statement",
    "account_canonical","account_alias","value","value_raw","unit","currency",
    "source_table_id","source_page","source_text","source_text_hash",
    "historical_check_confidence","historical_check",
    "add_sub_check_confidence","add_sub_check",
    "division_check_confidence","division_check",
    "final_trust_confidence","final_trust_band",
    "validation_status","source_stage","source_path","ingested_at","record_hash"
]

rows = []
scanned_text_rows = 0
matched_text_rows = 0

if text_col and not text_df.empty and aliases:
    for idx, tr in text_df.iterrows():
        txt = str(tr.get(text_col, "") or "")
        if len(txt.strip()) < 2:
            continue
        scanned_text_rows += 1

        # basic context
        rid = str(tr.get(report_col, "") if report_col else "")
        fid = str(tr.get(file_col, "") if file_col else "")
        bi = basic_by_report.get(rid) or basic_by_file.get(fid) or {}
        if not rid:
            rid = bi.get("report_id","")
        if not fid:
            fid = bi.get("file_id","")

        numbers = extract_numbers(txt)
        if not numbers:
            continue

        matched_alias = None
        for a in aliases:
            al = a["alias"]
            # For English aliases use word boundary-ish, for Chinese direct contains
            if re.search(r"[\u4e00-\u9fff]", al):
                ok = al in txt
            else:
                ok = re.search(r"(?<![A-Za-z])" + re.escape(al) + r"(?![A-Za-z])", txt, re.I) is not None
            if ok:
                matched_alias = a
                break

        if not matched_alias:
            continue

        matched_text_rows += 1
        year = extract_year(txt) or extract_year(bi.get("report_date",""))
        quarter = extract_quarter(txt)
        page = str(tr.get(page_col, "") if page_col else "")
        src = str(tr.get(source_col, "") if source_col else "")
        source_hash = sha1_text(txt, 24)

        # Conservative: use first non-year number. If line contains multiple values, create one row only at this stage.
        raw_value, norm_value = numbers[0]
        unit = value_unit(txt, matched_alias["alias"], matched_alias["canonical"])
        canonical = matched_alias["canonical"]
        statement = matched_alias["statement"] or infer_statement(canonical)

        row = {
            "report_id": rid,
            "file_id": fid,
            "tw_ticker": bi.get("tw_ticker",""),
            "company_name": bi.get("company_name",""),
            "broker": bi.get("broker",""),
            "report_date": bi.get("report_date",""),
            "period": (year + quarter) if year or quarter else "",
            "fiscal_year": year,
            "fiscal_quarter": quarter,
            "statement": statement,
            "account_canonical": canonical,
            "account_alias": matched_alias["alias"],
            "value": norm_value,
            "value_raw": raw_value,
            "unit": unit,
            "currency": "TWD",
            "source_table_id": "",
            "source_page": page,
            "source_text": txt[:1000],
            "source_text_hash": source_hash,
            "historical_check_confidence": "",
            "historical_check": "PENDING_AFTER_TABLE_STAGE",
            "add_sub_check_confidence": "",
            "add_sub_check": "PENDING_AFTER_TABLE_STAGE",
            "division_check_confidence": "",
            "division_check": "PENDING_AFTER_TABLE_STAGE",
            "final_trust_confidence": "0.60",
            "final_trust_band": "ORANGE",
            "validation_status": "STAGE_TEXT_EXTRACTED_REVIEW",
            "source_stage": "VRN_1D_REPORTTEXT_ALIAS_EXTRACTION",
            "source_path": src,
            "ingested_at": now()
        }
        row["record_hash"] = record_hash(row)
        rows.append(row)

stage_df = pd.DataFrame(rows, columns=target_cols)
if not stage_df.empty:
    stage_df = stage_df.astype(str).fillna("")
    stage_df = stage_df.drop_duplicates(subset=["record_hash"], keep="last").reset_index(drop=True)
else:
    stage_df = pd.DataFrame(columns=target_cols)

write_parquet_atomic(stage_df, stage_financial_parquet)

# Merge to database FinancialData
if os.path.exists(financial_db_parquet):
    old = safe_read_parquet(financial_db_parquet)
    merged = pd.concat([old, stage_df], ignore_index=True)
else:
    merged = stage_df.copy()

if not merged.empty:
    merged = merged.astype(str).fillna("")
    if "record_hash" in merged.columns:
        merged = merged.drop_duplicates(subset=["record_hash"], keep="last").reset_index(drop=True)
else:
    merged = pd.DataFrame(columns=target_cols)

write_parquet_atomic(merged, financial_db_parquet)

# Audit sample
os.makedirs(os.path.dirname(audit_csv), exist_ok=True)
stage_df.head(500).to_csv(audit_csv, index=False, encoding="utf-8-sig")

duckdb_status = "SKIPPED"
duckdb_basic_count = 0
duckdb_fin_count = 0
if write_duckdb:
    try:
        con = duckdb.connect(duckdb_path)
        con.execute("CREATE OR REPLACE TABLE StockReportBasicInfo AS SELECT * FROM read_parquet(?)", [basicinfo_parquet])
        con.execute("CREATE OR REPLACE TABLE StockReportFinancialData AS SELECT * FROM read_parquet(?)", [financial_db_parquet])
        con.execute("CREATE OR REPLACE VIEW vw_StockReportBasicInfo AS SELECT * FROM StockReportBasicInfo")
        con.execute("CREATE OR REPLACE VIEW vw_StockReportFinancialData AS SELECT * FROM StockReportFinancialData")
        duckdb_basic_count = con.execute("SELECT COUNT(*) FROM StockReportBasicInfo").fetchone()[0]
        duckdb_fin_count = con.execute("SELECT COUNT(*) FROM StockReportFinancialData").fetchone()[0]
        con.close()
        duckdb_status = "READY"
    except Exception as e:
        duckdb_status = "FAILED: " + str(e)

stage_dups = int(stage_df["record_hash"].duplicated().sum()) if not stage_df.empty and "record_hash" in stage_df.columns else 0
merged_dups = int(merged["record_hash"].duplicated().sum()) if not merged.empty and "record_hash" in merged.columns else 0

hard_blocks = 0
warnings = 0

tests = []
def add_test(name, status, value, message, path):
    tests.append({"name":name,"status":status,"value":str(value),"message":message,"path":path})

add_test("ReportText schema", "PASS" if text_col else "FAIL", text_col, "Auto-detected text column.", report_text_path)
add_test("Financial alias rows", "PASS" if len(aliases) > 0 else "FAIL", len(aliases), "FinancialAliasSSOT loaded.", financial_alias_path)
add_test("Text rows scanned", "PASS" if scanned_text_rows > 0 else "WARN", scanned_text_rows, "ReportText rows scanned.", report_text_path)
add_test("Matched text rows", "PASS" if matched_text_rows > 0 else "WARN", matched_text_rows, "Rows matched by financial aliases.", report_text_path)
add_test("Stage financial rows", "PASS" if len(stage_df) > 0 else "WARN", len(stage_df), "Stage financial rows extracted.", stage_financial_parquet)
add_test("Stage dedup", "PASS" if stage_dups == 0 else "FAIL", stage_dups, "Stage record_hash duplicates.", stage_financial_parquet)
add_test("Merged dedup", "PASS" if merged_dups == 0 else "FAIL", merged_dups, "Merged record_hash duplicates.", financial_db_parquet)
add_test("DuckDB financial count", "PASS" if duckdb_status == "READY" and duckdb_fin_count == len(merged) else "WARN", duckdb_fin_count, "DuckDB FinancialData serving count.", duckdb_path)

for t in tests:
    if t["status"] == "FAIL":
        hard_blocks += 1
    elif t["status"] == "WARN":
        warnings += 1

status = "VRN_1D_FINANCIALDATA_STAGING_READY"
risk = "LOW"
next_step = "Run 1D.1 table-geometry extraction if you need higher FinancialData coverage; canonical remains blocked."

if hard_blocks > 0:
    status = "VRN_1D_FINANCIALDATA_STAGING_REVIEW_REQUIRED"
    risk = "HIGH"
    next_step = "Fix hard blockers before proceeding."
elif warnings > 0:
    status = "VRN_1D_FINANCIALDATA_STAGING_READY_WITH_REVIEW"
    risk = "MEDIUM"
    next_step = "Proceed to 1D.1 table-geometry extraction for higher coverage; current text-alias extraction is staged and review-safe."

dataflow = {
    "generated_at": now(),
    "version": "v029.VRN.1D",
    "status": status,
    "risk": risk,
    "active_pointer": active_pointer_path,
    "basicinfo_parquet": basicinfo_parquet,
    "report_text_parquet": report_text_path,
    "financial_alias_parquet": financial_alias_path,
    "validation_rules_parquet": validation_rules_path,
    "stage_financial_parquet": stage_financial_parquet,
    "stockreport_financialdata_parquet": financial_db_parquet,
    "duckdb_path": duckdb_path,
    "json_role": "dataflow / runtime / control only",
    "parquet_role": "truth source / payload",
    "duckdb_role": "serving layer",
    "canonical_allowed": False,
    "counts": {
        "basicinfo_rows": len(basic),
        "reporttext_rows": len(text_df),
        "scanned_text_rows": scanned_text_rows,
        "matched_text_rows": matched_text_rows,
        "stage_financial_rows": len(stage_df),
        "financial_total_rows": len(merged),
        "alias_rows": len(aliases)
    },
    "tests": tests,
    "next_step": next_step
}
write_json(dataflow_json, dataflow)

runtime = {
    "generated_at": now(),
    "status": status,
    "risk": risk,
    "hard_blocks": hard_blocks,
    "warnings": warnings,
    "basicinfo_rows": len(basic),
    "reporttext_rows": len(text_df),
    "financial_alias_rows": len(aliases),
    "text_column": text_col,
    "scanned_text_rows": scanned_text_rows,
    "matched_text_rows": matched_text_rows,
    "financial_rows_extracted": len(stage_df),
    "financial_rows_total": len(merged),
    "stage_duplicates": stage_dups,
    "merged_duplicates": merged_dups,
    "duckdb_status": duckdb_status,
    "duckdb_basic_count": duckdb_basic_count,
    "duckdb_financial_count": duckdb_fin_count,
    "stage_financial_parquet": stage_financial_parquet,
    "stockreport_financialdata_parquet": financial_db_parquet,
    "audit_csv": audit_csv,
    "dataflow_json": dataflow_json,
    "tests": tests,
    "next_step": next_step
}
write_json(runtime_json, runtime)
print(json.dumps(runtime, ensure_ascii=False))
