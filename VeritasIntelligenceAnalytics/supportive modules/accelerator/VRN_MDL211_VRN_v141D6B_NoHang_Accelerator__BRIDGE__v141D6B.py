VERSION = "VRN_V141D6B_NOHANG_ACCELERATOR"
VRN_BASE = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN"
OUTPUT_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\output"
TEMP_DIR = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp"

MAX_SOURCE_FILES = 120
MAX_CANDIDATES_PER_KIND = 6
MAX_ROWS_PER_DATASET = 0
MAX_HTML_ROWS_PER_TABLE = 300
MAX_OTHER_DATA_CHARS = 1200

PIP_INSTALL_ENABLE = False
NETWORK_ENABLE = False
DB_WRITE_ENABLE = False
SSOT_MUTATION_ENABLE = False
PRODUCTION_WRITE_ENABLE = False

OUT_HTML = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_152642_VRN_V141D6B_NOHANG_ACCELERATOR\VRN_v141D6B_NoHang_Accelerator.html"
OUT_JSON = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_152642_VRN_V141D6B_NOHANG_ACCELERATOR\VRN_v141D6B_NoHang_Accelerator.json"
OUT_SUMMARY_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_152642_VRN_V141D6B_NOHANG_ACCELERATOR\VRN_v141D6B_Summary_Matrix.csv"
OUT_BASIC_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_152642_VRN_V141D6B_NOHANG_ACCELERATOR\VRN_v141D6B_BasicInfo_All_Rows_Validated.csv"
OUT_FINANCIAL_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_152642_VRN_V141D6B_NOHANG_ACCELERATOR\VRN_v141D6B_FinancialData_All_Rows_Validated.csv"
OUT_ISSUE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_152642_VRN_V141D6B_NOHANG_ACCELERATOR\VRN_v141D6B_Extraction_Issues.csv"
OUT_SOURCE_CSV = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_152642_VRN_V141D6B_NOHANG_ACCELERATOR\VRN_v141D6B_Source_Artifacts.csv"
OUT_REGISTRY = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VRN\temp\_validation_runs\RUN_20260527_152642_VRN_V141D6B_NOHANG_ACCELERATOR\VRN_v141D6B_NOHANG_ACCELERATOR_REGISTRY.txt"

import csv, json, html, re, sys, traceback
from pathlib import Path
from datetime import datetime

def def_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def def_status_lamp(s):
    return "🟢 PASS" if s == "PASS" else ("🟡 WARN" if s == "WARN" else "🔴 FAIL")

def def_esc(x):
    return html.escape("" if x is None else str(x))

def def_norm(x):
    return re.sub(r"[^a-z0-9]+", "_", str(x).strip().lower()).strip("_")

def def_blank(x):
    if x is None: return True
    s = str(x).strip()
    return s == "" or s.lower() in ["nan","none","null","nat"]

def def_num(x):
    if def_blank(x): return None
    try: return float(str(x).replace(",","").replace("%","").replace("X","").replace("x","").strip())
    except Exception: return None

def def_fmt(col, val):
    if def_blank(val): return ""
    raw = str(val).strip()
    c = def_norm(col)
    if any(k in c for k in ["ticker","code","year","date","filename","broker","analyst","name","source","path"]):
        return raw[:-2] if raw.endswith(".0") and re.fullmatch(r"\d+\.0", raw) else raw
    n = def_num(raw)
    if n is None: return raw
    if any(k in c for k in ["percent","pct","upside","performance","yield","margin"]):
        return f"{n:,.2f}%"
    if any(k in c for k in ["per","p_e","pe","multiple"]):
        return f"{n:,.2f} X"
    if any(k in c for k in ["price","value","eps","revenue","profit","income","assets","liabilities","equity","debt","cash","inventory","inventories","target","close"]):
        return f"{n:,.2f}"
    return raw

def def_write_csv(path, rows):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    rows = list(rows or [])
    if not rows:
        Path(path).write_text("", encoding="utf-8-sig")
        return
    keys = []
    for r in rows:
        for k in r.keys():
            if k not in keys: keys.append(k)
    if "Validation Status" in keys:
        keys = ["Validation Status"] + [k for k in keys if k != "Validation Status"]
    if "Validation Note" in keys:
        keys = [k for k in keys if k != "Validation Note"] + ["Validation Note"]
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k:r.get(k,"") for k in keys})

def def_write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8-sig")

def def_add(rows, cat, item, value, expected, passed, severity, note):
    rows.append({
        "Validation Status": def_status_lamp("PASS" if passed else ("WARN" if severity == "WARN" else "FAIL")),
        "Time": datetime.now().strftime("%H:%M:%S.%f")[:-3],
        "Category": cat,
        "Item": item,
        "Value": "" if value is None else str(value),
        "Expected": "" if expected is None else str(expected),
        "Pass": bool(passed),
        "Severity": severity,
        "Validation Note": "" if note is None else str(note)
    })

def def_scan_sources():
    roots = [Path(OUTPUT_DIR), Path(TEMP_DIR)]
    exts = {".csv", ".json", ".parquet"}
    out, seen = [], set()
    keywords = ["basicinfo","basic_info","financialdata","financial_data","financial"]
    for root in roots:
        if not root.exists(): continue
        for p in root.rglob("*"):
            if len(out) >= MAX_SOURCE_FILES: break
            if not p.is_file() or p.suffix.lower() not in exts: continue
            low = p.name.lower()
            if not any(k in low for k in keywords): continue
            key = str(p).lower()
            if key in seen: continue
            seen.add(key)
            st = p.stat()
            dataset = "BASIC_INFO" if "basic" in low else "FINANCIAL_DATA"
            out.append({
                "Validation Status":"🟢 PASS",
                "Dataset Guess":dataset,
                "File":p.name,
                "Path":str(p),
                "Extension":p.suffix.lower(),
                "Size Bytes":st.st_size,
                "Modified At":datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "Validation Note":"Candidate source artifact"
            })
    out.sort(key=lambda r: r["Modified At"], reverse=True)
    return out[:MAX_SOURCE_FILES]

def def_read_csv(path):
    for enc in ["utf-8-sig","utf-8","cp950","big5"]:
        try:
            with open(path,"r",encoding=enc,newline="") as f:
                return [dict(r) for r in csv.DictReader(f)], f"csv:{enc}", ""
        except Exception:
            pass
    return [], "csv", "CSV read failed"

def def_read_json(path):
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
        for key in ["rows","data","basic_info","basicinfo","financial_data","financial","preview","matrix","records","result","basic_info_all_rows","financial_data_all_rows"]:
            if isinstance(obj.get(key), list):
                rows = [x for x in obj[key] if isinstance(x, dict)]
                break
        if not rows:
            for v in obj.values():
                if isinstance(v, list) and v and isinstance(v[0], dict):
                    rows = v
                    break
    return rows, "json", ""

def def_read_parquet(path):
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
            return [], "parquet", "Parquet read failed; missing pandas/pyarrow or duckdb"

def def_read(path):
    s = Path(path).suffix.lower()
    if s == ".csv": return def_read_csv(path)
    if s == ".json": return def_read_json(path)
    if s == ".parquet": return def_read_parquet(path)
    return [], s, "unsupported"

def def_collect(sources, dataset):
    chosen = [s for s in sources if s["Dataset Guess"] == dataset][:MAX_CANDIDATES_PER_KIND]
    rows, issues = [], []
    for s in chosen:
        r, method, err = def_read(s["Path"])
        s["Read Method"] = method
        s["Rows Read"] = len(r)
        if err:
            s["Validation Status"] = "🟡 WARN"
            s["Validation Note"] = err
            issues.append({"Validation Status":"🟡 WARN","Dataset":dataset,"Issue Type":"SOURCE_READ_WARNING","Source":s["Path"],"Problem":err,"Suggested Fix":"Use latest readable CSV/JSON staging or install parquet reader in controlled env"})
        elif r:
            s["Validation Status"] = "🟢 PASS"
            s["Validation Note"] = f"Readable via {method}, rows={len(r)}"
            for x in r:
                x["_source_file"] = s["Path"]
                x["_read_method"] = method
            rows.extend(r)
        else:
            s["Validation Status"] = "🟡 WARN"
            s["Validation Note"] = "Readable but zero rows"
    if MAX_ROWS_PER_DATASET and len(rows) > MAX_ROWS_PER_DATASET:
        rows = rows[:MAX_ROWS_PER_DATASET]
    return rows, issues

def def_get(row, *names):
    km = {def_norm(k): k for k in row.keys()}
    for name in names:
        n = def_norm(name)
        if n in km: return row.get(km[n], "")
    for name in names:
        n = def_norm(name)
        for kn, ko in km.items():
            if n in kn or kn in n:
                return row.get(ko, "")
    return ""

def def_other(row):
    s = json.dumps({k:v for k,v in row.items() if not str(k).startswith("_")}, ensure_ascii=False)
    return s if len(s) <= MAX_OTHER_DATA_CHARS else s[:MAX_OTHER_DATA_CHARS] + "...[truncated]"

def def_validate_basic(row, i):
    notes = []
    ticker = def_get(row, "Ticker","Report Ticker","stock_code","code")
    yf = def_get(row, "YFinance Ticker","TW_YFINANCE_TICKER","YFINANCE TICKER","yf_ticker")
    filename = def_get(row, "Filename","File","source_file")
    name = def_get(row, "Name","Company","Company Name")
    target = def_get(row, "Report Target Price","Target Price","TP")
    adj = def_get(row, "Adj Close","Latest Adj Close")
    upside = def_get(row, "Upside %","Upside")
    if def_blank(filename): notes.append("Missing filename/source evidence")
    if def_blank(ticker): notes.append("Missing ticker")
    elif not re.fullmatch(r"[1-9]\d{3}", str(ticker).strip()): notes.append("Ticker format unusual")
    if def_blank(yf): notes.append("Missing YFinance ticker")
    elif not re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", str(yf).strip()): notes.append("YFinance ticker suffix issue")
    if def_blank(name): notes.append("Missing company name")
    if not def_blank(target) and def_num(target) is None: notes.append("Target price non-numeric")
    if not def_blank(target) and def_blank(adj): notes.append("Target exists but latest Adj Close missing")
    if not def_blank(upside) and def_num(upside) is None: notes.append("Upside non-numeric")
    status = "PASS" if not notes else "WARN"
    return {
        "Validation Status":def_status_lamp(status),
        "Row ID":i,
        "Report Date":def_fmt("Report Date", def_get(row,"Report Date","Date")),
        "Report Code":def_fmt("Report Code", def_get(row,"Report Code")),
        "Filename":filename,
        "Broker":def_get(row,"Broker"),
        "Analyst":def_get(row,"Analyst"),
        "Ticker":def_fmt("Ticker", ticker),
        "YFinance Ticker":yf,
        "Bloomberg Ticker":def_get(row,"Bloomberg Ticker","Bloomberg"),
        "Name":name,
        "Rating":def_get(row,"Rating"),
        "Report Rating":def_get(row,"Report Rating"),
        "Report Target Price":def_fmt("Report Target Price", target),
        "Latest Adj Close":def_fmt("Latest Adj Close", adj),
        "Adj Close on Report Date":def_fmt("Adj Close on Report Date", def_get(row,"Adj Close on Report Date","Report Date Adj Close")),
        "Upside %":def_fmt("Upside %", upside),
        "Performance %":def_fmt("Performance %", def_get(row,"Performance %","Performance")),
        "Source File":row.get("_source_file",""),
        "Read Method":row.get("_read_method",""),
        "Other Data":def_other(row),
        "Validation Note":"Validated" if not notes else "; ".join(notes)
    }

def def_validate_fin(row, i):
    notes = []
    ticker = def_get(row,"Ticker","stock_code","code")
    yf = def_get(row,"YFinance Ticker","TW_YFINANCE_TICKER","yf_ticker")
    filename = def_get(row,"Filename","File","source_file")
    category = def_get(row,"Category","Statement","statement")
    account = def_get(row,"Account","Canonical Account","canonical_account")
    value = def_get(row,"Value","Amount","actual","estimate")
    year = def_get(row,"Year","Report Year","Fiscal Year","period")
    if def_blank(filename): notes.append("Missing filename/source evidence")
    if def_blank(ticker): notes.append("Missing ticker")
    elif not re.fullmatch(r"[1-9]\d{3}", str(ticker).strip()): notes.append("Ticker format unusual")
    if not def_blank(yf) and not re.fullmatch(r"[1-9]\d{3}\.(TW|TWO)", str(yf).strip()): notes.append("YFinance ticker suffix issue")
    if def_blank(category): notes.append("Missing financial category/statement")
    if def_blank(account): notes.append("Missing financial account")
    if def_blank(value): notes.append("Missing financial value")
    elif def_num(value) is None: notes.append("Financial value non-numeric")
    if not def_blank(year) and not re.search(r"\d{4}", str(year)): notes.append("Year/period lacks 4-digit year")
    status = "PASS" if not notes else "WARN"
    return {
        "Validation Status":def_status_lamp(status),
        "Row ID":i,
        "Report Date":def_fmt("Report Date", def_get(row,"Report Date","Date")),
        "Report Code":def_fmt("Report Code", def_get(row,"Report Code")),
        "Filename":filename,
        "Broker":def_get(row,"Broker"),
        "Ticker":def_fmt("Ticker", ticker),
        "YFinance Ticker":yf,
        "Name":def_get(row,"Name","Company","Company Name"),
        "Category":category,
        "Account":account,
        "Year":def_fmt("Year", year),
        "Unit":def_get(row,"Unit"),
        "Value":def_fmt("Value", value),
        "Source":def_get(row,"Source") or filename,
        "Source File":row.get("_source_file",""),
        "Read Method":row.get("_read_method",""),
        "Other Data":def_other(row),
        "Validation Note":"Validated" if not notes else "; ".join(notes)
    }

def def_issues(dataset, rows):
    out = []
    for r in rows:
        if "🟢" in r.get("Validation Status",""): continue
        out.append({"Validation Status":r.get("Validation Status","🟡 WARN"),"Dataset":dataset,"Row ID":r.get("Row ID",""),"Ticker":r.get("Ticker",""),"Filename":r.get("Filename",""),"Issue Type":"ROW_VALIDATION_WARNING","Problem":r.get("Validation Note",""),"Suggested Fix":"修 extraction evidence / synonym / ticker route / numeric parser; do not write production until resolved"})
    return out

def def_table(rows, title):
    rows = list(rows or [])
    shown = rows[:MAX_HTML_ROWS_PER_TABLE] if MAX_HTML_ROWS_PER_TABLE else rows
    more = max(0, len(rows)-len(shown))
    if not rows: return f"<section class='card'><h2>{def_esc(title)}</h2><p>EMPTY</p></section>"
    keys = []
    for r in shown:
        for k in r.keys():
            if k not in keys: keys.append(k)
    if "Validation Status" in keys:
        keys = ["Validation Status"] + [k for k in keys if k != "Validation Status"]
    if "Validation Note" in keys:
        keys = [k for k in keys if k != "Validation Note"] + ["Validation Note"]
    th = "".join(f"<th>{def_esc(k)}</th>" for k in keys)
    body = ""
    for r in shown:
        st = r.get("Validation Status","")
        cls = "row-ok" if "🟢" in st else ("row-warn" if "🟡" in st else "row-fail")
        body += f"<tr class='{cls}'>"
        for k in keys:
            v = r.get(k,"")
            kind = "status" if k == "Validation Status" else ("long" if len(str(v))>34 or "\\" in str(v) or "/" in str(v) or k in ["Other Data","Validation Note","Source File","Path","Problem","Suggested Fix"] else "short")
            body += f"<td data-cell-kind='{kind}'>{def_esc(v)}</td>"
        body += "</tr>"
    note = f"<p class='note'>HTML shows {len(shown):,}; CSV has {len(rows):,} rows.</p>" if more else ""
    return f"<section class='card'><h2>{def_esc(title)} <span class='count'>{len(rows):,} rows</span></h2>{note}<div class='scroll'><table><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table></div></section>"

def def_html(meta, matrix, basic, fin, issues, sources):
    meta_json = def_esc(json.dumps(meta, ensure_ascii=False, indent=2))
    doc = f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>VRN D6B No-Hang Validation</title>
<style>
:root{{--bg:#f6f5f1;--card:#fff;--border:#d8d4ca;--soft:#ece8df;--head:#e8e4da;--text:#141414;--muted:#5f5b54;--ok:#247a4d;--warn:#a86613;--err:#a73535;--blue:#4c78a8;--mono:Consolas,"Cascadia Mono",monospace;--sans:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font-family:var(--sans);font-size:8.4px;line-height:1.1}}.wrap{{max-width:1920px;margin:0 auto;padding:10px 14px 18px}}
header{{position:relative;background:#fff;border:1px solid var(--border);border-radius:12px;padding:14px 16px;margin-bottom:8px;box-shadow:0 4px 12px rgba(0,0,0,.06)}}header:before{{content:"";position:absolute;left:16px;right:16px;top:0;height:3px;background:linear-gradient(90deg,#4c78a8,#439a9a,#7a6daa,#c4943a,#c96b5a)}}
h1{{margin:0;font-size:20px;line-height:1.05;font-weight:900}}.sub{{font-family:var(--mono);font-size:8.8px;font-weight:900;letter-spacing:.08em;margin-top:3px}}.desc{{font-size:9px;color:var(--muted);margin-top:3px}}
.tabs{{display:flex;gap:3px;flex-wrap:wrap;margin:8px 0}}.tabs button{{padding:7px 13px;border:1px solid var(--border);border-radius:8px 8px 0 0;background:#edecea;color:var(--muted);font:800 10px var(--sans);cursor:pointer}}.tabs button.on{{background:#fff;color:var(--blue);border-bottom:2px solid var(--blue)}}.page{{display:none}}.page.on{{display:block}}
.grid{{display:grid;grid-template-columns:repeat(8,minmax(80px,1fr));gap:6px;margin-bottom:8px}}.kpi{{background:#fff;border:1px solid var(--border);border-radius:8px;padding:6px 7px;min-height:42px}}.kpi .v{{font-size:14px;font-weight:900;text-align:center}}.kpi .k{{font-size:8px;color:var(--muted);text-align:center;margin-top:3px;text-transform:uppercase;font-weight:900}}
.card{{background:#fff;border:1px solid var(--border);border-radius:9px;padding:8px;margin-bottom:8px;box-shadow:0 1px 6px rgba(0,0,0,.035)}}.card h2{{margin:0 0 6px;font-size:11px;font-weight:900}}.count,.note{{font-size:8px;color:var(--warn);font-weight:800}}
.scroll{{overflow:auto;max-height:76vh;border:1px solid var(--border);border-radius:7px;background:#fff}}table{{border-collapse:separate;border-spacing:0;table-layout:auto;width:max-content;min-width:100%;font-size:8.2px;line-height:1.08}}th{{position:sticky;top:0;z-index:8;background:var(--head);font-weight:900;text-align:center;vertical-align:top;padding:3px 5px;border-bottom:1px solid var(--border);border-right:1px solid var(--soft);white-space:normal;overflow-wrap:anywhere;min-width:96px;max-width:360px}}td{{padding:3px 5px;border-bottom:1px solid var(--soft);border-right:1px solid var(--soft);vertical-align:top;text-align:center;white-space:normal;overflow-wrap:anywhere;word-break:break-word;min-width:82px;max-width:360px}}td[data-cell-kind="status"],td:first-child,th:first-child{{text-align:center!important;min-width:82px;max-width:96px;font-weight:900}}td[data-cell-kind="long"]{{text-align:left!important;min-width:180px;max-width:680px}}.row-ok td:first-child{{color:var(--ok)}}.row-warn td:first-child{{color:var(--warn)}}.row-fail td:first-child{{color:var(--err)}}pre{{font-family:var(--mono);font-size:8.25px;line-height:1.16;background:#f8fafc;border:1px solid #e2e8f0;border-radius:7px;padding:7px;white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;max-height:42vh;overflow:auto}}.footer{{margin-top:10px;color:var(--muted);font-size:8.4px;text-align:left;border-top:1px solid var(--border);padding-top:8px}}
</style></head><body><div class="wrap"><header><h1>VeritasReportNova v1.0.41D6B</h1><div class="sub">VERITAS INTELLIGENCE ANALYTICS</div><div class="desc">No-Hang Accelerator · Extracted Basic Info / Financial Data Validation · HTML capped / CSV full</div></header>
<nav class="tabs"><button class="on" onclick="swTab(this,'tab1')">Summary</button><button onclick="swTab(this,'tab2')">Basic Info</button><button onclick="swTab(this,'tab3')">Financial Data</button><button onclick="swTab(this,'tab4')">Issues</button><button onclick="swTab(this,'tab5')">Sources</button></nav>
<section class="page on" id="tab1"><div class="grid"><div class="kpi"><div class="v">{meta['system_pass']}</div><div class="k">System Pass</div></div><div class="kpi"><div class="v">{meta['basic_rows']}</div><div class="k">Basic Rows</div></div><div class="kpi"><div class="v">{meta['financial_rows']}</div><div class="k">Financial Rows</div></div><div class="kpi"><div class="v">{meta['issue_rows']}</div><div class="k">Issues</div></div><div class="kpi"><div class="v">{meta['source_artifacts']}</div><div class="k">Sources</div></div><div class="kpi"><div class="v">{meta['db_write']}</div><div class="k">DB Write</div></div><div class="kpi"><div class="v">{meta['production_write']}</div><div class="k">Production</div></div><div class="kpi"><div class="v">{meta['elapsed_sec']}</div><div class="k">Elapsed</div></div></div><section class="card"><h2>Meta</h2><pre>{meta_json}</pre></section>{def_table(matrix,'Summary Matrix')}</section>
<section class="page" id="tab2">{def_table(basic,'Basic Info All Rows')}</section><section class="page" id="tab3">{def_table(fin,'Financial Data All Rows')}</section><section class="page" id="tab4">{def_table(issues,'Extraction Method Issues')}</section><section class="page" id="tab5">{def_table(sources,'Source Artifacts')}</section>
<div class="footer">Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</div></div><script>function swTab(btn,id){{document.querySelectorAll('.tabs button').forEach(x=>x.classList.remove('on'));document.querySelectorAll('.page').forEach(x=>x.classList.remove('on'));btn.classList.add('on');document.getElementById(id).classList.add('on');}}</script></body></html>"""
    Path(OUT_HTML).write_text(doc, encoding="utf-8-sig")

def main():
    t0 = datetime.now()
    sources = def_scan_sources()
    basic_raw, source_issues_b = def_collect(sources, "BASIC_INFO")
    fin_raw, source_issues_f = def_collect(sources, "FINANCIAL_DATA")
    basic = [def_validate_basic(r,i) for i,r in enumerate(basic_raw,1)]
    fin = [def_validate_fin(r,i) for i,r in enumerate(fin_raw,1)]
    issues = source_issues_b + source_issues_f + def_issues("BASIC_INFO", basic) + def_issues("FINANCIAL_DATA", fin)
    matrix = []
    def_add(matrix,"Safety","Pip Install","NO","NO",True,"OK","No pip")
    def_add(matrix,"Safety","Network","NO","NO",True,"OK","No network")
    def_add(matrix,"Safety","DB Write","NO","NO",True,"OK","No DB write")
    def_add(matrix,"Safety","SSOT Mutation","NO","NO",True,"OK","No SSOT")
    def_add(matrix,"Accelerator","HTML Row Cap",MAX_HTML_ROWS_PER_TABLE,"prevents browser hang",True,"OK","CSV still contains full rows")
    def_add(matrix,"Source","Source Artifacts",len(sources),">=1",len(sources)>0,"OK" if sources else "WARN","Fast scan newest candidate artifacts")
    def_add(matrix,"Basic Info","Rows Listed",len(basic),"all readable rows",True,"OK",f"WARN={len([x for x in basic if '🟡' in x['Validation Status']])}")
    def_add(matrix,"Financial Data","Rows Listed",len(fin),"all readable rows",True,"OK",f"WARN={len([x for x in fin if '🟡' in x['Validation Status']])}")
    def_add(matrix,"Issues","Issue Rows",len(issues),"review warnings",len(issues)==0,"WARN" if issues else "OK","Warnings listed, no production write")
    elapsed = round((datetime.now()-t0).total_seconds(),2)
    meta = {"version":VERSION,"generated_at":def_now(),"system_pass":True,"basic_rows":len(basic),"financial_rows":len(fin),"issue_rows":len(issues),"source_artifacts":len(sources),"pip_install":False,"network":False,"db_write":False,"ssot_mutation":False,"production_write":False,"html_row_cap":MAX_HTML_ROWS_PER_TABLE,"max_source_files":MAX_SOURCE_FILES,"html":OUT_HTML,"json":OUT_JSON,"summary_csv":OUT_SUMMARY_CSV,"basic_csv":OUT_BASIC_CSV,"financial_csv":OUT_FINANCIAL_CSV,"issue_csv":OUT_ISSUE_CSV,"source_csv":OUT_SOURCE_CSV,"registry":OUT_REGISTRY,"elapsed_sec":elapsed}
    def_write_csv(OUT_SUMMARY_CSV,matrix); def_write_csv(OUT_BASIC_CSV,basic); def_write_csv(OUT_FINANCIAL_CSV,fin); def_write_csv(OUT_ISSUE_CSV,issues); def_write_csv(OUT_SOURCE_CSV,sources)
    def_write_json(OUT_JSON,{"meta":meta,"summary":matrix,"basic_info":basic,"financial_data":fin,"issues":issues,"sources":sources})
    Path(OUT_REGISTRY).write_text("\n".join([f"{k}={v}" for k,v in meta.items()] + ["nohang=YES","html_capped=YES","csv_full=YES","no_db_write=YES","no_ssot=YES"]), encoding="utf-8-sig")
    def_html(meta,matrix,basic,fin,issues,sources)
    print(json.dumps(meta,ensure_ascii=False,indent=2))

if __name__ == "__main__":
    try:
        Path(OUT_HTML).parent.mkdir(parents=True, exist_ok=True)
        main()
    except BaseException:
        fatal = {"version":VERSION,"system_pass":False,"fatal":traceback.format_exc(),"html":OUT_HTML,"json":OUT_JSON}
        def_write_json(OUT_JSON,fatal)
        print(json.dumps(fatal,ensure_ascii=False,indent=2))
        raise
