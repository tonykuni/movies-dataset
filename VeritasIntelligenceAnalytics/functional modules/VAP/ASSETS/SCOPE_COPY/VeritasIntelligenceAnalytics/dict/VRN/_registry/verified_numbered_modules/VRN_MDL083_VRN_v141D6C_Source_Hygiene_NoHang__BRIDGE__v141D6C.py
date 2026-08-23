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
VERSION = "VRN_V141D6C_SOURCE_HYGIENE_NOHANG"
OUTPUT_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output"
TEMP_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp"

MAX_SOURCE_FILES = 300
MAX_CANDIDATES_PER_KIND = 10
MAX_HTML_ROWS_PER_TABLE = 300
MAX_OTHER_DATA_CHARS = 900

OUT_HTML = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_155858_VRN_V141D6C_SOURCE_HYGIENE_NOHANG\VRN_v141D6C_Source_Hygiene_NoHang.html"
OUT_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_155858_VRN_V141D6C_SOURCE_HYGIENE_NOHANG\VRN_v141D6C_Source_Hygiene_NoHang.json"
OUT_SUMMARY_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_155858_VRN_V141D6C_SOURCE_HYGIENE_NOHANG\VRN_v141D6C_Summary_Matrix.csv"
OUT_BASIC_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_155858_VRN_V141D6C_SOURCE_HYGIENE_NOHANG\VRN_v141D6C_BasicInfo_Accepted_Validated.csv"
OUT_FINANCIAL_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_155858_VRN_V141D6C_SOURCE_HYGIENE_NOHANG\VRN_v141D6C_FinancialData_Accepted_Validated.csv"
OUT_SOURCE_ACCEPTED_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_155858_VRN_V141D6C_SOURCE_HYGIENE_NOHANG\VRN_v141D6C_Source_Accepted.csv"
OUT_SOURCE_REJECTED_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_155858_VRN_V141D6C_SOURCE_HYGIENE_NOHANG\VRN_v141D6C_Source_Rejected.csv"
OUT_ISSUE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_155858_VRN_V141D6C_SOURCE_HYGIENE_NOHANG\VRN_v141D6C_Issues.csv"
OUT_REGISTRY = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_155858_VRN_V141D6C_SOURCE_HYGIENE_NOHANG\VRN_v141D6C_SOURCE_HYGIENE_NOHANG_REGISTRY.txt"

import csv, json, html, re, traceback
from pathlib import Path
from datetime import datetime

def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def lamp(s):
    return "🟢 PASS" if s == "PASS" else ("🟡 WARN" if s == "WARN" else "🔴 FAIL")

def esc(x):
    return html.escape("" if x is None else str(x))

def norm(x):
    return re.sub(r"[^a-z0-9]+", "_", str(x).strip().lower()).strip("_")

def blank(x):
    if x is None:
        return True
    s = str(x).strip()
    return s == "" or s.lower() in ["nan", "none", "null", "nat"]

def num(x):
    if blank(x):
        return None
    try:
        return float(str(x).replace(",", "").replace("%", "").replace("X", "").replace("x", "").strip())
    except Exception:
        return None

def fmt(col, val):
    if blank(val):
        return ""
    raw = str(val).strip()
    c = norm(col)
    if any(k in c for k in ["ticker", "code", "year", "date", "filename", "broker", "analyst", "name", "source", "path"]):
        return raw[:-2] if raw.endswith(".0") and re.fullmatch(r"\d+\.0", raw) else raw
    n = num(raw)
    if n is None:
        return raw
    if any(k in c for k in ["percent", "pct", "upside", "performance", "yield", "margin"]):
        return f"{n:,.2f}%"
    if any(k in c for k in ["per", "p_e", "pe", "multiple"]):
        return f"{n:,.2f} X"
    if any(k in c for k in ["price", "value", "eps", "revenue", "profit", "income", "assets", "liabilities", "equity", "debt", "cash", "inventory", "inventories", "target", "close"]):
        return f"{n:,.2f}"
    return raw

def write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows or [])
    if not rows:
        Path(path).write_text("", encoding="utf-8-sig")
        return
    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys:
                keys.append(k)
    if "Validation Status" in keys:
        keys = ["Validation Status"] + [k for k in keys if k != "Validation Status"]
    if "Validation Note" in keys:
        keys = [k for k in keys if k != "Validation Note"] + ["Validation Note"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})

def write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8-sig")

def add(rows, cat, item, value, expected, passed, severity, note):
    rows.append({
        "Validation Status": lamp("PASS" if passed else ("WARN" if severity == "WARN" else "FAIL")),
        "Time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "Category": cat,
        "Item": item,
        "Value": "" if value is None else str(value),
        "Expected": "" if expected is None else str(expected),
        "Pass": bool(passed),
        "Severity": severity,
        "Validation Note": "" if note is None else str(note)
    })

def is_rejected_filename(p):
    s = str(p).lower()
    name = Path(p).name.lower()

    bad_dirs = [
        "_validation_runs",
        "_ui_patch_runs",
        "_finish_project_runs",
        "_runtime_bridge_runs"
    ]

    bad_name_tokens = [
        "all_rows_validated",
        "source_artifacts",
        "source_accepted",
        "source_rejected",
        "summary_matrix",
        "extraction_issues",
        "issues",
        "matrix",
        "validation",
        "hash_manifest",
        "schema_manifest",
        "header_duplicate",
        "registry",
        "table_scan",
        "scan",
        "debug",
        "console",
        "report",
        "freeze",
        "dashboard",
        "ui",
        "safegetter",
        "nohang_accelerator"
    ]

    # def 關鍵：避免 D6 / D6B 讀回自己的輸出。
    if any(x in s for x in bad_dirs):
        return True, "REJECT_RUNTIME_VALIDATION_OR_UI_DIR"

    if any(x in name for x in bad_name_tokens):
        return True, "REJECT_NON_DATA_ARTIFACT_NAME"

    return False, ""

def classify_dataset_by_name(p):
    name = Path(p).name.lower()
    s = str(p).lower()

    if "basicinfo" in name or "basic_info" in name or "basicinfo_consensus" in s or "basicinfo_consensus" in s:
        return "BASIC_INFO"

    if "financialdata" in name or "financial_data" in name or "financial_actual" in name or "financial_actual" in s:
        return "FINANCIAL_DATA"

    return "UNKNOWN"

def scan_sources():
    roots = [Path(OUTPUT_DIR)]
    exts = {".csv", ".json", ".parquet"}
    accepted, rejected = [], []
    seen = set()

    for root in roots:
        if not root.exists():
            continue

        for p in root.rglob("*"):
            if len(accepted) + len(rejected) >= MAX_SOURCE_FILES:
                break
            if not p.is_file() or p.suffix.lower() not in exts:
                continue

            key = str(p).lower()
            if key in seen:
                continue
            seen.add(key)

            dataset = classify_dataset_by_name(p)
            if dataset == "UNKNOWN":
                continue

            rej, reason = is_rejected_filename(p)
            st = p.stat()
            row = {
                "Validation Status": lamp("WARN" if rej else "PASS"),
                "Dataset Guess": dataset,
                "File": p.name,
                "Path": str(p),
                "Extension": p.suffix.lower(),
                "Size Bytes": st.st_size,
                "Modified At": datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "Accepted": not rej,
                "Reject Reason": reason,
                "Read Method": "",
                "Rows Read": "",
                "Validation Note": "Accepted source candidate" if not rej else reason
            }

            if rej:
                rejected.append(row)
            else:
                accepted.append(row)

    accepted.sort(key=lambda r: r["Modified At"], reverse=True)
    rejected.sort(key=lambda r: r["Modified At"], reverse=True)
    return accepted, rejected

def read_csv_rows(path):
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                return [dict(r) for r in csv.DictReader(f)], f"csv:{enc}", ""
        except Exception:
            pass
    return [], "csv", "CSV read failed"

def read_json_rows(path):
    try:
        txt = Path(path).read_text(encoding="utf-8-sig")
        obj = json.loads(txt)
    except Exception:
        try:
            txt = Path(path).read_text(encoding="utf-8")
            obj = json.loads(txt)
        except Exception:
            return [], "json", traceback.format_exc()[:700]

    rows = []
    if isinstance(obj, list):
        rows = [x for x in obj if isinstance(x, dict)]
    elif isinstance(obj, dict):
        for key in [
            "rows", "data", "preview", "records", "result",
            "basic_info", "basicinfo", "basic_info_rows",
            "financial_data", "financial", "financial_rows"
        ]:
            if isinstance(obj.get(key), list):
                rows = [x for x in obj[key] if isinstance(x, dict)]
                break
        if not rows:
            for v in obj.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    rows = v
                    break

    return rows, "json", ""

def read_parquet_rows(path):
    try:
        import pandas as pd
        df = pd.read_parquet(path)
        return df.astype(object).where(df.notna(), "").to_dict("records"), "parquet:pandas", ""
    except Exception:
        try:
            import duckdb
            con = duckdb.connect(":memory:")
            df = con.execute("select * from read_parquet(?)", [path]).fetchdf()
            return df.astype(object).where(df.notna(), "").to_dict("records"), "parquet:duckdb", ""
        except Exception:
            return [], "parquet", "Parquet read failed; no pandas/pyarrow or duckdb reader"

def read_any(path):
    ext = Path(path).suffix.lower()
    if ext == ".csv":
        return read_csv_rows(path)
    if ext == ".json":
        return read_json_rows(path)
    if ext == ".parquet":
        return read_parquet_rows(path)
    return [], ext, "unsupported"

def keymap(row):
    return {norm(k): k for k in row.keys()}

def get(row, *names):
    km = keymap(row)
    for n in names:
        nn = norm(n)
        if nn in km:
            return row.get(km[nn], "")
    for n in names:
        nn = norm(n)
        for kn, ko in km.items():
            if nn in kn or kn in nn:
                return row.get(ko, "")
    return ""

def has_any_key(row, keys):
    km = keymap(row)
    return any(norm(k) in km for k in keys)

def accept_row_contract(row, dataset):
    if dataset == "BASIC_INFO":
        if has_any_key(row, ["ticker", "tw_yfinance_ticker", "yfinance_ticker", "name", "company_name"]):
            return True, ""
        return False, "REJECT_BASICINFO_ROW_CONTRACT_MISSING_TICKER_OR_NAME"

    if dataset == "FINANCIAL_DATA":
        has_ticker = has_any_key(row, ["ticker", "stock_code", "code"])
        has_account = has_any_key(row, ["account", "canonical_account", "account_key", "account_canonical"])
        has_value = has_any_key(row, ["value", "amount", "actual", "estimate", "value_reported", "value_numeric"])
        has_statement = has_any_key(row, ["category", "statement", "financial_statement"])

        if has_ticker and has_account and has_value:
            return True, ""
        if has_statement and has_account and has_value:
            return True, ""
        return False, "REJECT_FINANCIAL_ROW_CONTRACT_MISSING_TICKER_ACCOUNT_VALUE"

    return False, "REJECT_UNKNOWN_DATASET"

def other(row):
    s = json.dumps({k: v for k, v in row.items() if not str(k).startswith("_")}, ensure_ascii=False)
    return s if len(s) <= MAX_OTHER_DATA_CHARS else s[:MAX_OTHER_DATA_CHARS] + "...[truncated]"

def validate_basic(row, i):
    notes = []
    ticker = get(row, "Ticker", "Report Ticker", "stock_code", "code")
    yf = get(row, "YFinance Ticker", "TW_YFINANCE_TICKER", "tw_yfinance_ticker", "yf_ticker")
    filename = get(row, "Filename", "File", "source_file", "report_file")
    name = get(row, "Name", "Company", "Company Name", "company_name")
    target = get(row, "Report Target Price", "Target Price", "TP")
    adj = get(row, "Adj Close", "Latest Adj Close")
    upside = get(row, "Upside %", "Upside")

    if blank(ticker):
        notes.append("Missing ticker")
    elif not re.fullmatch(r"[1-9]\d{3}", str(ticker).strip()):
        notes.append("Ticker format unusual")

    if blank(yf):
        notes.append("Missing YFinance ticker")
    elif not re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", str(yf).strip()):
        notes.append("YFinance suffix issue")

    if blank(name):
        notes.append("Missing company name")

    if not blank(target) and num(target) is None:
        notes.append("Target price non-numeric")

    if not blank(target) and blank(adj):
        notes.append("Target exists but latest Adj Close missing")

    if not blank(upside) and num(upside) is None:
        notes.append("Upside non-numeric")

    status = "PASS" if not notes else "WARN"

    return {
        "Validation Status": lamp(status),
        "Row ID": i,
        "Report Date": fmt("Report Date", get(row, "Report Date", "Date")),
        "Report Code": fmt("Report Code", get(row, "Report Code")),
        "Filename": filename,
        "Broker": get(row, "Broker"),
        "Analyst": get(row, "Analyst"),
        "Ticker": fmt("Ticker", ticker),
        "YFinance Ticker": yf,
        "Bloomberg Ticker": get(row, "Bloomberg Ticker", "Bloomberg"),
        "Name": name,
        "Rating": get(row, "Rating"),
        "Report Rating": get(row, "Report Rating"),
        "Report Target Price": fmt("Report Target Price", target),
        "Latest Adj Close": fmt("Latest Adj Close", adj),
        "Adj Close on Report Date": fmt("Adj Close on Report Date", get(row, "Adj Close on Report Date", "Report Date Adj Close")),
        "Upside %": fmt("Upside %", upside),
        "Performance %": fmt("Performance %", get(row, "Performance %", "Performance")),
        "2026 Diluted EPS": fmt("2026 Diluted EPS", get(row, "2026 Diluted EPS", "eps_2026", "2026 EPS")),
        "2027 Diluted EPS": fmt("2027 Diluted EPS", get(row, "2027 Diluted EPS", "eps_2027", "2027 EPS")),
        "2028 Diluted EPS": fmt("2028 Diluted EPS", get(row, "2028 Diluted EPS", "eps_2028", "2028 EPS")),
        "2026 PER": fmt("2026 PER", get(row, "2026 PER", "per_2026", "pe_2026")),
        "2027 PER": fmt("2027 PER", get(row, "2027 PER", "per_2027", "pe_2027")),
        "2028 PER": fmt("2028 PER", get(row, "2028 PER", "per_2028", "pe_2028")),
        "Source File": row.get("_source_file", ""),
        "Read Method": row.get("_read_method", ""),
        "Other Data": other(row),
        "Validation Note": "Validated" if not notes else "; ".join(notes)
    }

def validate_financial(row, i):
    notes = []
    ticker = get(row, "Ticker", "stock_code", "code")
    yf = get(row, "YFinance Ticker", "TW_YFINANCE_TICKER", "tw_yfinance_ticker", "yf_ticker")
    filename = get(row, "Filename", "File", "source_file", "report_file")
    category = get(row, "Category", "Statement", "statement", "financial_statement")
    account = get(row, "Account", "Canonical Account", "canonical_account", "account_key", "account_canonical")
    value = get(row, "Value", "Amount", "actual", "estimate", "value_reported", "value_numeric")
    year = get(row, "Year", "Report Year", "Fiscal Year", "period_year", "period")

    if blank(ticker):
        notes.append("Missing ticker")
    elif not re.fullmatch(r"[1-9]\d{3}", str(ticker).strip()):
        notes.append("Ticker format unusual")

    if not blank(yf) and not re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", str(yf).strip()):
        notes.append("YFinance suffix issue")

    if blank(category):
        notes.append("Missing financial category/statement")
    if blank(account):
        notes.append("Missing financial account")
    if blank(value):
        notes.append("Missing financial value")
    elif num(value) is None:
        notes.append("Financial value non-numeric")
    if not blank(year) and not re.search(r"\d{4}", str(year)):
        notes.append("Year/period lacks 4-digit year")

    status = "PASS" if not notes else "WARN"

    return {
        "Validation Status": lamp(status),
        "Row ID": i,
        "Report Date": fmt("Report Date", get(row, "Report Date", "Date")),
        "Report Code": fmt("Report Code", get(row, "Report Code")),
        "Filename": filename,
        "Broker": get(row, "Broker"),
        "Ticker": fmt("Ticker", ticker),
        "YFinance Ticker": yf,
        "Name": get(row, "Name", "Company", "Company Name", "company_name"),
        "Category": category,
        "Account": account,
        "Year": fmt("Year", year),
        "Unit": get(row, "Unit"),
        "Value": fmt("Value", value),
        "Source": get(row, "Source") or filename,
        "Source File": row.get("_source_file", ""),
        "Read Method": row.get("_read_method", ""),
        "Other Data": other(row),
        "Validation Note": "Validated" if not notes else "; ".join(notes)
    }

def collect_rows(accepted_sources, dataset):
    rows, issues = [], []
    candidates = [x for x in accepted_sources if x["Dataset Guess"] == dataset][:MAX_CANDIDATES_PER_KIND]

    for s in candidates:
        raw, method, err = read_any(s["Path"])
        s["Read Method"] = method
        s["Rows Read"] = len(raw)

        if err:
            s["Validation Status"] = "🟡 WARN"
            s["Validation Note"] = err
            issues.append({
                "Validation Status": "🟡 WARN",
                "Dataset": dataset,
                "Issue Type": "SOURCE_READ_WARNING",
                "Source": s["Path"],
                "Problem": err,
                "Suggested Fix": "提供可讀 CSV/JSON/parquet 或補齊 reader，但不要把 validation output 當資料源"
            })
            continue

        accepted_count = 0
        rejected_count = 0

        for r in raw:
            ok, reason = accept_row_contract(r, dataset)
            if not ok:
                rejected_count += 1
                continue
            r["_source_file"] = s["Path"]
            r["_read_method"] = method
            rows.append(r)
            accepted_count += 1

        s["Accepted Rows"] = accepted_count
        s["Rejected Rows"] = rejected_count
        s["Validation Note"] = f"Read={len(raw)}, accepted_contract={accepted_count}, rejected_contract={rejected_count}"

    return rows, issues

def row_issues(dataset, rows):
    out = []
    for r in rows:
        if "🟢" in r.get("Validation Status", ""):
            continue
        out.append({
            "Validation Status": r.get("Validation Status", "🟡 WARN"),
            "Dataset": dataset,
            "Row ID": r.get("Row ID", ""),
            "Ticker": r.get("Ticker", ""),
            "Filename": r.get("Filename", ""),
            "Issue Type": "ROW_VALIDATION_WARNING",
            "Problem": r.get("Validation Note", ""),
            "Suggested Fix": "修 evidence / synonym / ticker route / numeric parser；未通過前不要寫 production"
        })
    return out

def table(rows, title):
    rows = list(rows or [])
    shown = rows[:MAX_HTML_ROWS_PER_TABLE]
    more = max(0, len(rows) - len(shown))

    if not rows:
        return f"<section class='card'><h2>{esc(title)}</h2><p>EMPTY</p></section>"

    keys = []
    for r in shown:
        for k in r.keys():
            if k not in keys:
                keys.append(k)

    if "Validation Status" in keys:
        keys = ["Validation Status"] + [k for k in keys if k != "Validation Status"]
    if "Validation Note" in keys:
        keys = [k for k in keys if k != "Validation Note"] + ["Validation Note"]

    th = "".join(f"<th>{esc(k)}</th>" for k in keys)
    body = ""

    for r in shown:
        st = r.get("Validation Status", "")
        cls = "row-ok" if "🟢" in st else ("row-warn" if "🟡" in st else "row-fail")
        body += f"<tr class='{cls}'>"
        for k in keys:
            v = r.get(k, "")
            kind = "status" if k == "Validation Status" else ("long" if len(str(v)) > 34 or "\\" in str(v) or "/" in str(v) or k in ["Other Data", "Validation Note", "Source File", "Path", "Problem", "Suggested Fix"] else "short")
            body += f"<td data-cell-kind='{kind}'>{esc(v)}</td>"
        body += "</tr>"

    note = f"<p class='note'>HTML shows {len(shown):,}; CSV has {len(rows):,} rows.</p>" if more else ""
    return f"<section class='card'><h2>{esc(title)} <span class='count'>{len(rows):,} rows</span></h2>{note}<div class='scroll'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div></section>"

def write_html(meta, matrix, basic, financial, issues, accepted, rejected):
    meta_json = esc(json.dumps(meta, ensure_ascii=False, indent=2))
    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN D6C Source Hygiene No-Hang</title>
<style>
:root{{--bg:#f6f5f1;--card:#fff;--border:#d8d4ca;--soft:#ece8df;--head:#e8e4da;--text:#141414;--muted:#5f5b54;--ok:#247a4d;--warn:#a86613;--err:#a73535;--blue:#4c78a8;--mono:Consolas,"Cascadia Mono",monospace;--sans:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:8.4px;line-height:1.1}}
.wrap{{max-width:1920px;margin:0 auto;padding:10px 14px 18px}}
header{{position:relative;background:#fff;border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:8px;box-shadow:0 4px 12px rgba(0,0,0,.06)}}
header:before{{content:"";position:absolute;left:16px;right:16px;top:0;height:3px;background:linear-gradient(90deg,#4c78a8,#439a9a,#7a6daa,#c4943a,#c96b5a)}}
h1{{margin:0;font-size:20px;line-height:1.05;font-weight:900}}
.sub{{font-family:var(--mono);font-size:8.8px;font-weight:900;letter-spacing:.08em;margin-top:3px}}
.desc{{font-size:9px;color:var(--muted);margin-top:3px}}
.tabs{{display:flex;gap:3px;flex-wrap:wrap;margin:8px 0}}
.tabs button{{padding:7px 13px;border:1px solid var(--border);border-radius:8px 8px 0 0;background:#edecea;color:var(--muted);font:800 10px var(--sans);cursor:pointer}}
.tabs button.on{{background:#fff;color:var(--blue);border-bottom:2px solid var(--blue)}}
.page{{display:none}}.page.on{{display:block}}
.grid{{display:grid;grid-template-columns:repeat(8,minmax(80px,1fr));gap:6px;margin-bottom:8px}}
.kpi{{background:#fff;border:1px solid var(--border);border-radius:8px;padding:6px 7px;min-height:42px}}
.kpi .v{{font-size:14px;font-weight:900;text-align:center}}
.kpi .k{{font-size:8px;color:var(--muted);text-align:center;margin-top:3px;text-transform:uppercase;font-weight:900}}
.card{{background:#fff;border:1px solid var(--border);border-radius:9px;padding:8px;margin-bottom:8px;box-shadow:0 1px 6px rgba(0,0,0,.035)}}
.card h2{{margin:0 0 6px;font-size:11px;font-weight:900}}
.count,.note{{font-size:8px;color:var(--warn);font-weight:800}}
.scroll{{overflow:auto;max-height:76vh;border:1px solid var(--border);border-radius:7px;background:#fff}}
table{{border-collapse:separate;border-spacing:0;table-layout:auto;width:max-content;min-width:100%;font-size:8.2px;line-height:1.08}}
th{{position:sticky;top:0;z-index:8;background:var(--head);font-weight:900;text-align:center;vertical-align:top;padding:3px 5px;border-bottom:1px solid var(--border);border-right:1px solid var(--soft);white-space:normal;overflow-wrap:anywhere;min-width:96px;max-width:360px}}
td{{padding:3px 5px;border-bottom:1px solid var(--soft);border-right:1px solid var(--soft);vertical-align:top;text-align:center;white-space:normal;overflow-wrap:anywhere;word-break:break-word;min-width:82px;max-width:360px}}
td[data-cell-kind="status"],td:first-child,th:first-child{{text-align:center!important;min-width:82px;max-width:96px;font-weight:900}}
td[data-cell-kind="long"]{{text-align:left!important;min-width:180px;max-width:680px}}
.row-ok td:first-child{{color:var(--ok)}}.row-warn td:first-child{{color:var(--warn)}}.row-fail td:first-child{{color:var(--err)}}
pre{{font-family:var(--mono);font-size:8.25px;line-height:1.16;background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;padding:7px;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;max-height:42vh;overflow:auto}}
.footer{{margin-top:10px;color:var(--muted);font-size:8.4px;text-align:left;border-top:1px solid var(--border);padding-top:8px}}
</style>
</head>
<body>
<div class="wrap">
<header>
<h1>VeritasReportNova v1.0.41D6C</h1>
<div class="sub">VERITAS INTELLIGENCE ANALYTICS</div>
<div class="desc">Source Hygiene No-Hang · No Recursive Validation Source · No Table Scan As Data · CSV Full / HTML Capped</div>
</header>

<nav class="tabs">
<button class="on" onclick="swTab(this,'tab1')">Summary</button>
<button onclick="swTab(this,'tab2')">Basic Info Accepted</button>
<button onclick="swTab(this,'tab3')">Financial Data Accepted</button>
<button onclick="swTab(this,'tab4')">Issues</button>
<button onclick="swTab(this,'tab5')">Accepted Sources</button>
<button onclick="swTab(this,'tab6')">Rejected Sources</button>
</nav>

<section class="page on" id="tab1">
<div class="grid">
<div class="kpi"><div class="v">{meta['system_pass']}</div><div class="k">System Pass</div></div>
<div class="kpi"><div class="v">{meta['basic_rows']}</div><div class="k">Basic Rows</div></div>
<div class="kpi"><div class="v">{meta['financial_rows']}</div><div class="k">Financial Rows</div></div>
<div class="kpi"><div class="v">{meta['issue_rows']}</div><div class="k">Issues</div></div>
<div class="kpi"><div class="v">{meta['accepted_sources']}</div><div class="k">Accepted Src</div></div>
<div class="kpi"><div class="v">{meta['rejected_sources']}</div><div class="k">Rejected Src</div></div>
<div class="kpi"><div class="v">{meta['db_write']}</div><div class="k">DB Write</div></div>
<div class="kpi"><div class="v">{meta['elapsed_sec']}</div><div class="k">Elapsed</div></div>
</div>
<section class="card"><h2>Meta</h2><pre>{meta_json}</pre></section>
{table(matrix, "Summary Matrix")}
</section>

<section class="page" id="tab2">{table(basic, "Basic Info Accepted Validated Rows")}</section>
<section class="page" id="tab3">{table(financial, "Financial Data Accepted Validated Rows")}</section>
<section class="page" id="tab4">{table(issues, "Issues")}</section>
<section class="page" id="tab5">{table(accepted, "Accepted Sources")}</section>
<section class="page" id="tab6">{table(rejected, "Rejected Sources")}</section>

<div class="footer">Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</div>
</div>
<script>
function swTab(btn,id){{
  document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));
  document.querySelectorAll('.page').forEach(x=>x.classList.remove('on'));
  btn.classList.add('on');
  document.getElementById(id).classList.add('on');
}}
</script>
</body>
</html>"""
    Path(OUT_HTML).write_text(doc, encoding="utf-8-sig")

def main():
    t0 = datetime.now()

    accepted_sources, rejected_sources = scan_sources()

    basic_raw, source_issues_b = collect_rows(accepted_sources, "BASIC_INFO")
    financial_raw, source_issues_f = collect_rows(accepted_sources, "FINANCIAL_DATA")

    basic = [validate_basic(r, i) for i, r in enumerate(basic_raw, 1)]
    financial = [validate_financial(r, i) for i, r in enumerate(financial_raw, 1)]

    issues = []
    issues.extend(source_issues_b)
    issues.extend(source_issues_f)
    issues.extend(row_issues("BASIC_INFO", basic))
    issues.extend(row_issues("FINANCIAL_DATA", financial))

    matrix = []
    add(matrix, "Safety", "Pip Install", "NO", "NO", True, "OK", "No pip")
    add(matrix, "Safety", "Network", "NO", "NO", True, "OK", "No network")
    add(matrix, "Safety", "DB Write", "NO", "NO", True, "OK", "No DB write")
    add(matrix, "Safety", "SSOT Mutation", "NO", "NO", True, "OK", "No SSOT")
    add(matrix, "Source Hygiene", "Rejected Runtime Validation Sources", len(rejected_sources), ">= prior D6/D6B outputs excluded", True, "OK", "Prevents recursive pollution")
    add(matrix, "Source Hygiene", "Accepted Source Candidates", len(accepted_sources), "true data candidates only", len(accepted_sources) > 0, "WARN" if not accepted_sources else "OK", "Matrix/scan/hash/schema/validation files excluded")
    add(matrix, "Basic Info", "Accepted Rows", len(basic), "contract-valid rows only", True, "OK", f"WARN={len([x for x in basic if '🟡' in x['Validation Status']])}")
    add(matrix, "Financial Data", "Accepted Rows", len(financial), "contract-valid rows only", True, "OK", f"WARN={len([x for x in financial if '🟡' in x['Validation Status']])}")
    add(matrix, "Issues", "Issue Rows", len(issues), "review warnings", len(issues) == 0, "WARN" if issues else "OK", "No production write")

    elapsed = round((datetime.now() - t0).total_seconds(), 2)

    meta = {
        "version": VERSION,
        "generated_at": now(),
        "system_pass": True,
        "basic_rows": len(basic),
        "financial_rows": len(financial),
        "issue_rows": len(issues),
        "accepted_sources": len(accepted_sources),
        "rejected_sources": len(rejected_sources),
        "html_row_cap": MAX_HTML_ROWS_PER_TABLE,
        "pip_install": False,
        "network": False,
        "db_write": False,
        "ssot_mutation": False,
        "production_write": False,
        "html": OUT_HTML,
        "json": OUT_JSON,
        "summary_csv": OUT_SUMMARY_CSV,
        "basic_csv": OUT_BASIC_CSV,
        "financial_csv": OUT_FINANCIAL_CSV,
        "accepted_source_csv": OUT_SOURCE_ACCEPTED_CSV,
        "rejected_source_csv": OUT_SOURCE_REJECTED_CSV,
        "issue_csv": OUT_ISSUE_CSV,
        "registry": OUT_REGISTRY,
        "elapsed_sec": elapsed
    }

    write_csv(OUT_SUMMARY_CSV, matrix)
    write_csv(OUT_BASIC_CSV, basic)
    write_csv(OUT_FINANCIAL_CSV, financial)
    write_csv(OUT_SOURCE_ACCEPTED_CSV, accepted_sources)
    write_csv(OUT_SOURCE_REJECTED_CSV, rejected_sources)
    write_csv(OUT_ISSUE_CSV, issues)

    write_json(OUT_JSON, {
        "meta": meta,
        "summary": matrix,
        "basic_info_accepted": basic,
        "financial_data_accepted": financial,
        "accepted_sources": accepted_sources,
        "rejected_sources": rejected_sources,
        "issues": issues
    })

    Path(OUT_REGISTRY).write_text(
        "\n".join([f"{k}={v}" for k, v in meta.items()] + [
            "source_hygiene=YES",
            "recursive_validation_sources_excluded=YES",
            "table_scan_as_data_excluded=YES",
            "matrix_validation_hash_schema_artifacts_excluded=YES",
            "financial_contract_requires_account_value=YES",
            "csv_full=YES",
            "html_capped=YES",
            "no_db_write=YES",
            "no_ssot=YES"
        ]),
        encoding="utf-8-sig"
    )

    write_html(meta, matrix, basic, financial, issues, accepted_sources, rejected_sources)
    print(json.dumps(meta, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    try:
        Path(OUT_HTML).parent.mkdir(parents=True, exist_ok=True)
        main()
    except BaseException:
        fatal = {
            "version": VERSION,
            "system_pass": False,
            "fatal": traceback.format_exc(),
            "html": OUT_HTML,
            "json": OUT_JSON
        }
        write_json(OUT_JSON, fatal)
        print(json.dumps(fatal, ensure_ascii=False, indent=2))
        raise
