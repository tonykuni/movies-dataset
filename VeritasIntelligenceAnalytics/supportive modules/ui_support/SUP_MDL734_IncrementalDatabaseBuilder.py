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
import json
import os
import re
import sys
import hashlib
from pathlib import Path
from datetime import datetime

input_dir = Path(sys.argv[1])
output_dir = Path(sys.argv[2])
ledger_path = Path(sys.argv[3])
active_basic = Path(sys.argv[4])
active_fin = Path(sys.argv[5])
target_basic = Path(sys.argv[6])
target_fin = Path(sys.argv[7])
basic_csv = Path(sys.argv[8])
fin_csv = Path(sys.argv[9])
basic_json = Path(sys.argv[10])
fin_json = Path(sys.argv[11])
duckdb_path = Path(sys.argv[12])
google_plan = Path(sys.argv[13])
result_json = Path(sys.argv[14])
enable_csv = sys.argv[15].lower() == "true"
enable_json = sys.argv[16].lower() == "true"
enable_duckdb = sys.argv[17].lower() == "true"
enable_google = sys.argv[18].lower() == "true"

result = {
    "status": "INIT",
    "risk": "MEDIUM",
    "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "imports": {},
    "input_dir": str(input_dir),
    "output_dir": str(output_dir),
    "files": [],
    "basic": {},
    "financial": {},
    "ledger": {},
    "outputs": {},
    "warnings": [],
    "errors": []
}

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

try:
    import pandas as pd
    result["imports"]["pandas"] = True
except Exception as e:
    result["imports"]["pandas"] = False
    result["errors"].append("pandas_missing:" + str(e))
    result["status"] = "FAIL"
    result["risk"] = "HIGH"
    result_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    sys.exit(0)

try:
    import pyarrow
    result["imports"]["pyarrow"] = True
except Exception as e:
    result["imports"]["pyarrow"] = False
    result["errors"].append("pyarrow_missing:" + str(e))

try:
    import duckdb
    result["imports"]["duckdb"] = True
except Exception as e:
    result["imports"]["duckdb"] = False
    result["warnings"].append("duckdb_unavailable:" + str(e))

try:
    import fitz
    result["imports"]["pymupdf"] = True
except Exception as e:
    result["imports"]["pymupdf"] = False
    result["warnings"].append("pymupdf_unavailable:" + str(e))

try:
    import pdfplumber
    result["imports"]["pdfplumber"] = True
except Exception as e:
    result["imports"]["pdfplumber"] = False
    result["warnings"].append("pdfplumber_unavailable:" + str(e))

output_dir.mkdir(parents=True, exist_ok=True)
ledger_path.parent.mkdir(parents=True, exist_ok=True)

def load_df(path):
    if path.exists() and path.stat().st_size > 0:
        try:
            return pd.read_parquet(path)
        except Exception:
            try:
                return pd.read_csv(path, encoding="utf-8-sig")
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()

def broker_from_name(name):
    mapping = {
        "凱基": "凱基投顧",
        "KGI": "KGI",
        "GS": "Goldman Sachs",
        "Goldman": "Goldman Sachs",
        "MS": "Morgan Stanley",
        "Morgan": "Morgan Stanley",
        "Citi": "Citi",
        "Daiwa": "Daiwa",
        "CLSA": "CLSA",
        "JP": "J.P. Morgan",
        "UBS": "UBS",
        "Nomura": "Nomura",
        "Macquarie": "Macquarie"
    }
    for k, v in mapping.items():
        if k.lower() in name.lower():
            return v
    return ""

def ticker_from_name(name):
    m = re.search(r"(?<!\d)([1-9]\d{3})(?!\d)", name)
    return m.group(1) if m else ""

def date_from_name_or_mtime(path):
    n = path.name
    patterns = [
        r"(20\d{2})[-_./]?([01]\d)[-_./]?([0-3]\d)",
        r"([01]\d)[-_./]?([0-3]\d)[-_./]?(20\d{2})"
    ]
    for p in patterns:
        m = re.search(p, n)
        if m:
            try:
                if len(m.group(1)) == 4:
                    y, mo, d = m.group(1), m.group(2), m.group(3)
                else:
                    mo, d, y = m.group(1), m.group(2), m.group(3)
                return f"{int(y):04d}-{int(mo):02d}-{int(d):02d}"
            except Exception:
                pass
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
    except Exception:
        return ""

def company_guess(name, ticker):
    stem = Path(name).stem
    if ticker and ticker in stem:
        parts = re.split(r"[_\-\s]+", stem)
        for idx, p in enumerate(parts):
            if ticker in p and idx + 1 < len(parts):
                return parts[idx + 1]
    return ""

def extract_text_by_page(path, max_pages=12):
    pages = []
    if result["imports"].get("pdfplumber"):
        try:
            import pdfplumber
            with pdfplumber.open(path) as pdf:
                for i, page in enumerate(pdf.pages[:max_pages]):
                    try:
                        txt = page.extract_text() or ""
                    except Exception:
                        txt = ""
                    pages.append((i + 1, txt))
            return pages
        except Exception as e:
            result["warnings"].append(f"pdfplumber_failed:{path.name}:{e}")
    if result["imports"].get("pymupdf"):
        try:
            import fitz
            doc = fitz.open(path)
            for i in range(min(len(doc), max_pages)):
                try:
                    txt = doc[i].get_text("text") or ""
                except Exception:
                    txt = ""
                pages.append((i + 1, txt))
            return pages
        except Exception as e:
            result["warnings"].append(f"pymupdf_failed:{path.name}:{e}")
    return pages

def metric_candidates_from_text(text):
    keys = [
        "Revenue", "Revenues", "Net income", "Operating income", "Gross profit", "EPS",
        "Gross margin", "Operating margin", "Net margin", "Margins",
        "營業收入", "營收", "毛利率", "營業利益", "營利率", "淨利", "淨利率", "每股盈餘", "EPS"
    ]
    rows = []
    lines = [x.strip() for x in text.splitlines() if x.strip()]
    for line in lines:
        compact = re.sub(r"\s+", " ", line)
        if len(compact) < 6:
            continue
        hit = None
        for k in keys:
            if k.lower() in compact.lower():
                hit = k
                break
        if not hit:
            continue
        if not re.search(r"\d", compact):
            continue
        rows.append((hit, compact[:1000]))
    return rows

def ensure_columns(df, columns):
    for c in columns:
        if c not in df.columns:
            df[c] = ""
    return df[columns]

basic_cols = [
    "SourceFile", "SourcePath", "FileHash", "Ticker", "CompanyName", "Broker",
    "ReportDate", "FileSizeBytes", "ModifiedTime", "InputStatus", "ValidationStatus",
    "ValidationRisk", "IncrementalAction"
]

fin_cols = [
    "SourceFile", "Ticker", "Broker", "ReportDate", "Page", "TableIndex", "RowIndex", "ColumnIndex",
    "MetricRaw", "HeaderStack", "PeriodNormalized", "ValueRaw", "CoreMetric", "PeriodOk",
    "UsableForPromotionPreview", "ValidationStatus", "ValidationRisk", "TempOnly"
]

basic_existing = pd.concat([load_df(active_basic), load_df(target_basic)], ignore_index=True)
fin_existing = pd.concat([load_df(active_fin), load_df(target_fin)], ignore_index=True)

basic_existing = ensure_columns(basic_existing, basic_cols) if len(basic_existing.columns) else pd.DataFrame(columns=basic_cols)
fin_existing = ensure_columns(fin_existing, fin_cols) if len(fin_existing.columns) else pd.DataFrame(columns=fin_cols)

old_ledger = {}
if ledger_path.exists():
    try:
        old_ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    except Exception:
        old_ledger = {}

pdfs = sorted(input_dir.rglob("*.pdf")) if input_dir.exists() else []
new_ledger = dict(old_ledger)

basic_new = []
fin_new = []

for idx, p in enumerate(pdfs, start=1):
    try:
        h = sha256_file(p)
    except Exception as e:
        result["errors"].append(f"hash_failed:{p}:{e}")
        continue

    already = old_ledger.get(h, {}).get("processed", False)
    action = "SKIP_ALREADY_PROCESSED" if already else "NEW_OR_CHANGED"

    ticker = ticker_from_name(p.name)
    broker = broker_from_name(p.name)
    rdate = date_from_name_or_mtime(p)
    company = company_guess(p.name, ticker)
    mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")

    result["files"].append({
        "source_file": p.name,
        "path": str(p),
        "hash": h,
        "ticker": ticker,
        "broker": broker,
        "report_date": rdate,
        "incremental_action": action
    })

    basic_new.append({
        "SourceFile": p.name,
        "SourcePath": str(p),
        "FileHash": h,
        "Ticker": ticker,
        "CompanyName": company,
        "Broker": broker,
        "ReportDate": rdate,
        "FileSizeBytes": int(p.stat().st_size),
        "ModifiedTime": mtime,
        "InputStatus": "DISCOVERED",
        "ValidationStatus": "VALID_BASICINFO_CANDIDATE",
        "ValidationRisk": "GREEN" if ticker or broker or rdate else "YELLOW",
        "IncrementalAction": action
    })

    if not already:
        pages = extract_text_by_page(p)
        row_no = 0
        for page_no, text in pages:
            cands = metric_candidates_from_text(text)
            for metric, raw in cands:
                row_no += 1
                fin_new.append({
                    "SourceFile": p.name,
                    "Ticker": ticker,
                    "Broker": broker,
                    "ReportDate": rdate,
                    "Page": int(page_no),
                    "TableIndex": 0,
                    "RowIndex": int(row_no),
                    "ColumnIndex": 1,
                    "MetricRaw": metric,
                    "HeaderStack": raw,
                    "PeriodNormalized": "",
                    "ValueRaw": raw,
                    "CoreMetric": metric,
                    "PeriodOk": bool(re.search(r"(20\d{2}|[1-4]Q\d{2}|FY\d{2}|\d{4}E|\d{4}F)", raw)),
                    "UsableForPromotionPreview": True,
                    "ValidationStatus": "VALID_FINANCIAL_ROW_CANDIDATE",
                    "ValidationRisk": "GREEN",
                    "TempOnly": False
                })

    new_ledger[h] = {
        "processed": True,
        "source_file": p.name,
        "path": str(p),
        "ticker": ticker,
        "broker": broker,
        "report_date": rdate,
        "last_seen": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

basic_new_df = pd.DataFrame(basic_new, columns=basic_cols)
fin_new_df = pd.DataFrame(fin_new, columns=fin_cols)

basic_all = pd.concat([basic_existing, basic_new_df], ignore_index=True)
fin_all = pd.concat([fin_existing, fin_new_df], ignore_index=True)

if len(basic_all):
    basic_all = ensure_columns(basic_all, basic_cols)
    basic_all = basic_all.drop_duplicates(subset=["FileHash", "SourceFile"], keep="last").reset_index(drop=True)
else:
    basic_all = pd.DataFrame(columns=basic_cols)

if len(fin_all):
    fin_all = ensure_columns(fin_all, fin_cols)
    fin_all = fin_all.drop_duplicates(subset=["SourceFile", "Ticker", "Broker", "ReportDate", "Page", "RowIndex", "ColumnIndex", "MetricRaw", "ValueRaw"], keep="last").reset_index(drop=True)
else:
    fin_all = pd.DataFrame(columns=fin_cols)

# Mandatory parquet.
try:
    basic_all.to_parquet(target_basic, index=False)
except Exception as e:
    result["errors"].append("write_basic_parquet_failed:" + str(e))

try:
    fin_all.to_parquet(target_fin, index=False)
except Exception as e:
    result["errors"].append("write_financial_parquet_failed:" + str(e))

if enable_csv:
    try:
        basic_all.to_csv(basic_csv, index=False, encoding="utf-8-sig")
        fin_all.to_csv(fin_csv, index=False, encoding="utf-8-sig")
    except Exception as e:
        result["warnings"].append("csv_write_failed:" + str(e))

if enable_json:
    try:
        basic_all.to_json(basic_json, orient="records", force_ascii=False, indent=2)
        fin_all.to_json(fin_json, orient="records", force_ascii=False, indent=2)
    except Exception as e:
        result["warnings"].append("json_write_failed:" + str(e))

if enable_duckdb and result["imports"].get("duckdb"):
    try:
        import duckdb
        con = duckdb.connect(str(duckdb_path))
        con.register("basic_df", basic_all)
        con.register("fin_df", fin_all)
        con.execute("CREATE OR REPLACE TABLE StockReportBasicInfo AS SELECT * FROM basic_df")
        con.execute("CREATE OR REPLACE TABLE StockReportFinancialData AS SELECT * FROM fin_df")
        con.close()
    except Exception as e:
        result["warnings"].append("duckdb_write_failed:" + str(e))

if enable_google:
    plan = {
        "enabled": "PLAN_ONLY",
        "credential_required": True,
        "sheets": ["StockReportBasicInfo", "StockReportFinancialData"],
        "source_parquet": {
            "StockReportBasicInfo": str(target_basic),
            "StockReportFinancialData": str(target_fin)
        },
        "note": "Google Sheet output requires credentials and explicit upload workflow."
    }
    google_plan.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

ledger_path.write_text(json.dumps(new_ledger, ensure_ascii=False, indent=2), encoding="utf-8")

def validate_df(df):
    rows = int(len(df))
    cols = int(len(df.columns))
    dup = int(df.duplicated().sum()) if rows else 0
    total_cells = int(max(rows * max(cols, 1), 1))
    null_cells = int(df.isna().sum().sum()) if rows and cols else 0
    return {
        "rows": rows,
        "columns": cols,
        "duplicate_rows": dup,
        "duplicate_rate": float(dup / max(rows, 1)),
        "null_cells": null_cells,
        "total_cells": total_cells,
        "null_rate": float(null_cells / total_cells),
        "column_names": [str(x) for x in df.columns]
    }

result["basic"] = validate_df(basic_all)
result["financial"] = validate_df(fin_all)
result["ledger"] = {
    "old_entries": len(old_ledger),
    "new_entries": len(new_ledger),
    "input_pdf_count": len(pdfs),
    "new_basic_rows": int(len(basic_new_df)),
    "new_financial_rows": int(len(fin_new_df))
}
result["outputs"] = {
    "basic_parquet": str(target_basic),
    "financial_parquet": str(target_fin),
    "basic_csv": str(basic_csv) if enable_csv else "",
    "financial_csv": str(fin_csv) if enable_csv else "",
    "basic_json": str(basic_json) if enable_json else "",
    "financial_json": str(fin_json) if enable_json else "",
    "duckdb": str(duckdb_path) if enable_duckdb else "",
    "google_plan": str(google_plan) if enable_google else ""
}

fail = False
if not target_basic.exists() or target_basic.stat().st_size <= 0:
    fail = True
    result["errors"].append("mandatory_basic_parquet_missing_or_empty")
if not target_fin.exists() or target_fin.stat().st_size <= 0:
    fail = True
    result["errors"].append("mandatory_financial_parquet_missing_or_empty")
if result["basic"]["rows"] <= 0 or result["basic"]["columns"] <= 0:
    fail = True
    result["errors"].append("basic_table_empty_or_invalid")
if result["financial"]["rows"] <= 0 or result["financial"]["columns"] <= 0:
    fail = True
    result["errors"].append("financial_table_empty_or_invalid")

if fail:
    result["status"] = "VRN_INCREMENTAL_DB_WITH_REVIEW"
    result["risk"] = "HIGH"
elif result["warnings"]:
    result["status"] = "VRN_INCREMENTAL_DB_READY_WITH_WARNINGS"
    result["risk"] = "MEDIUM"
else:
    result["status"] = "VRN_INCREMENTAL_DB_READY"
    result["risk"] = "LOW"

result_json.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
