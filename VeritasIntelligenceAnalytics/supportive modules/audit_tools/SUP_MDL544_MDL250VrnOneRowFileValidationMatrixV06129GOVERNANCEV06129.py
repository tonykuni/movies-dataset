# -*- coding: utf-8 -*-
from __future__ import annotations
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

import csv
import html
import json
import re
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_ONE_ROW_FILE_VALIDATION_MATRIX_V06129"


# ==================================================================================================
# def 01_COMMON
# ==================================================================================================
def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").replace("不", "不")
    return re.sub(r"\s+", " ", s).strip()


def def_norm_text(x: Any) -> str:
    s = def_clean_text(x).lower()
    s = re.sub(r"[()（）\[\]【】{}<>〈〉《》]", " ", s)
    s = re.sub(r"[\s　,，、;；:：|｜/／\\\-–—_+＋=＝~～!！?？.．]", "", s)
    return s


def def_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "YES", "PASS", "GREEN", "DB_READY"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "YELLOW", "INFO", "NO_FINANCIAL_TABLE_DISCLOSED"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def def_write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_find_latest(run_root: Path, pattern: str) -> Path | None:
    hits = sorted(run_root.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_first(row: dict, keys: list[str]) -> str:
    for k in keys:
        if k in row and def_clean_text(row.get(k)):
            return def_clean_text(row.get(k))
    return ""


def def_num(x: Any) -> float | None:
    s = def_clean_text(x).replace(",", "").replace("%", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def def_int_fmt(x: Any) -> str:
    n = def_num(x)
    if n is None:
        return ""
    return f"{int(round(n)):,}"


def def_float_fmt(x: Any) -> str:
    n = def_num(x)
    if n is None:
        return ""
    return f"{n:,.2f}"


def def_rate_display(hit: int, total: int) -> str:
    if total <= 0:
        return "0.00%\n0/0"
    pct = hit / total * 100
    return f"{pct:,.2f}%\n{hit:,}/{total:,}"


# ==================================================================================================
# def 02_FILENAME TOKENIZER
# ==================================================================================================
def def_tokenize_filename(name: str) -> dict:
    stem = Path(name).stem
    normalized = stem
    normalized = normalized.replace("（", "(").replace("）", ")")
    normalized = normalized.replace("－", "-").replace("—", "-").replace("_", " ")
    normalized = re.sub(r"[()\[\]【】{}<>〈〉《》,，、;；:：|｜/／\\]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    digit_tokens = re.findall(r"\d+", normalized)
    ticker_tokens = []
    date_tokens = []
    date_candidates = []

    def parse_date_token(tok: str) -> str:
        if len(tok) == 8 and tok[:2] in ["19", "20"]:
            y = int(tok[:4]); m = int(tok[4:6]); d = int(tok[6:8])
            if 1990 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
        if len(tok) == 7:
            y = int(tok[:3]) + 1911; m = int(tok[3:5]); d = int(tok[5:7])
            if 1990 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
        if len(tok) == 6:
            y = 2000 + int(tok[:2]); m = int(tok[2:4]); d = int(tok[4:6])
            if 2000 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
        return ""

    for tok in digit_tokens:
        dt = parse_date_token(tok)
        if dt:
            date_tokens.append(tok)
            date_candidates.append(dt)
        elif len(tok) == 4 and re.fullmatch(r"(?!202[1-9])(?!2030)[1-9]\d{3}", tok):
            ticker_tokens.append(tok)

    return {
        "ticker": ticker_tokens[0] if ticker_tokens else "",
        "report_date": date_candidates[0] if date_candidates else "",
        "ticker_tokens": ticker_tokens,
        "date_tokens": date_tokens,
        "digit_tokens": digit_tokens,
    }


def def_yfinance_ticker(ticker: str) -> str:
    if not ticker:
        return ""
    return f"{ticker}.TW\n{ticker}.TWO"


def def_bloomberg_ticker(ticker: str) -> str:
    return f"{ticker} TT" if ticker else ""


# ==================================================================================================
# def 03_DATA INDEX
# ==================================================================================================
def def_index_rows_by_filename_and_ticker(rows: list[dict]) -> tuple[dict, dict]:
    by_file = defaultdict(list)
    by_ticker = defaultdict(list)
    for r in rows:
        fn = def_first(r, ["Filename", "filename"])
        tk = def_first(r, ["Ticker", "ticker", "Ticker Parsed"])
        if fn:
            by_file[def_norm_text(Path(fn).name)].append(r)
        if tk:
            by_ticker[tk].append(r)
    return by_file, by_ticker


def def_match_rows(filename: str, ticker: str, by_file: dict, by_ticker: dict) -> list[dict]:
    rows = []
    k = def_norm_text(Path(filename).name)
    if k in by_file:
        rows.extend(by_file[k])
    if not rows and ticker and ticker in by_ticker:
        rows.extend(by_ticker[ticker])
    return rows


def def_extract_basic_fields(filename: str, ticker: str, matched_final: list[dict], reconcile_row: dict) -> dict:
    broker = ""
    analyst = ""
    name = ""
    rating = ""
    target = ""

    for r in matched_final:
        broker = broker or def_first(r, ["Broker", "broker"])
        analyst = analyst or def_first(r, ["Analyst", "analyst"])
        name = name or def_first(r, ["Name", "name"])
        rating = rating or def_first(r, ["Rating", "rating", "Broker Rating"])
        target = target or def_first(r, ["Target Price", "target_price", "Broker Target Price"])

    # Filename fallback for broker
    fn = Path(filename).name
    if not broker:
        if "兆豐" in fn:
            broker = "兆豐"
        elif "華南" in fn:
            broker = "華南投顧"
        elif "國泰" in fn:
            broker = "國泰證期"
        elif fn.startswith("GS-"):
            broker = "GS"
        elif fn.startswith("MS-"):
            broker = "MS"
        elif fn.startswith("JP-"):
            broker = "JP"
        elif fn.startswith("Citi-"):
            broker = "Citi"
        elif fn.startswith("Daiwa-"):
            broker = "Daiwa"
        elif fn.startswith("CLST-"):
            broker = "CLST"
        elif "CTBC" in fn:
            broker = "CTBC"

    # Filename fallback for name
    if not name:
        m = re.search(r"[\-\(（]([一-龥A-Za-z][一-龥A-Za-z0-9\-KYky]+)[\-\(（,_，]", fn)
        if m:
            cand = def_clean_text(m.group(1))
            if not re.fullmatch(r"\d+", cand) and len(cand) <= 18:
                name = cand

    # Filename / title fallback for rating
    if not rating:
        if "買進" in fn:
            rating = "買進"
        elif "中立" in fn:
            rating = "中立"
        elif "未評等" in fn or "NR" in fn:
            rating = "未評等"

    return {
        "Broker": broker,
        "Analyst": analyst,
        "Name": name,
        "Rating": rating,
        "Target Price": target,
    }


# ==================================================================================================
# def 04_RATE CALCULATION
# ==================================================================================================
CORE_ITEMS = {
    "Income Statement": ["Revenue", "Gross Profit", "Operating Income", "Net Income", "EPS"],
    "Balance Sheet": ["Total Assets", "Total Liabilities", "Total Equity", "Cash And Cash Equivalents", "Current Assets", "Current Liabilities"],
    "Cash Flow Statement": ["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow", "Net Change In Cash", "Capital Expenditure", "Ending Cash"],
    "Ratio Analysis": ["Gross Margin", "Operating Margin", "Net Margin", "ROE", "ROA", "Current Ratio"],
    "Per Share Analysis": ["EPS", "BVPS", "CFPS"],
}


def def_category_rate(matched_final: list[dict], category: str) -> tuple[int, int]:
    expected = CORE_ITEMS.get(category, [])
    if not expected:
        return 0, 0
    found = set()
    for r in matched_final:
        cat = def_first(r, ["Category Official En", "Category"])
        data = def_first(r, ["Data Official En", "Data"])
        if cat == category and data:
            found.add(data)
    hit = len([x for x in expected if x in found])
    return hit, len(expected)


def def_table_fetching_rate(matched_final: list[dict], table_inventory_rows: list[dict], filename: str, ticker: str) -> tuple[int, int]:
    # hit = DB ready table count proxy by unique category/year groups
    hit_groups = set()
    for r in matched_final:
        cat = def_first(r, ["Category Official En", "Category"])
        year = def_first(r, ["Year"])
        if cat and year:
            hit_groups.add((cat, year))

    # total = PDF table inventory count if available, else max(hit, 1 if no rows)
    total = 0
    fn_norm = def_norm_text(Path(filename).name)
    for r in table_inventory_rows:
        fn = def_first(r, ["Filename", "filename", "Pdf", "PDF", "File"])
        tk = def_first(r, ["Ticker", "ticker"])
        if (fn and def_norm_text(Path(fn).name) == fn_norm) or (ticker and tk == ticker):
            total += 1

    if total <= 0:
        total = max(len(hit_groups), 0)

    hit = len(hit_groups)
    return hit, total


def def_confidence(matched_final: list[dict], split_review_rows: int, action_warn: bool) -> tuple[str, str]:
    if not matched_final:
        return "0.00", "REVIEW"

    scores = []
    for r in matched_final:
        s = def_num(def_first(r, ["Final Trust Score"]))
        if s is not None:
            scores.append(s)

    base = sum(scores) / len(scores) if scores else 75.0
    if split_review_rows > 0:
        base -= 5
    if action_warn:
        base -= 10
    base = max(0.0, min(100.0, base))

    if base >= 85:
        return f"{base:,.2f}", "DB_READY"
    if base >= 65:
        return f"{base:,.2f}", "REVIEW"
    return f"{base:,.2f}", "ACTION_REQUIRED"


# ==================================================================================================
# def 05_MATRIX BUILD
# ==================================================================================================
def def_build_matrix(input_dir: Path, run_root: Path) -> tuple[list[dict], list[dict], dict]:
    final_csv = def_find_latest(run_root, "vrn_v06127_financial_db_ready_preview.csv")
    reconcile_csv = def_find_latest(run_root, "vrn_v06128_input_file_reconcile.csv")
    action_csv = def_find_latest(run_root, "vrn_v06128_action_queue.csv")
    table_inventory_csv = def_find_latest(run_root, "vrn_pdf_table_inventory_v0603.csv")

    final_rows = def_read_csv(final_csv) if final_csv else []
    reconcile_rows = def_read_csv(reconcile_csv) if reconcile_csv else []
    action_rows = def_read_csv(action_csv) if action_csv else []
    table_inventory_rows = def_read_csv(table_inventory_csv) if table_inventory_csv else []

    final_by_file, final_by_ticker = def_index_rows_by_filename_and_ticker(final_rows)
    rec_by_file, rec_by_ticker = def_index_rows_by_filename_and_ticker(reconcile_rows)

    action_set = set()
    for r in action_rows:
        fn = def_first(r, ["Filename"])
        if fn:
            action_set.add(def_norm_text(Path(fn).name))

    files = []
    for ext in ["*.pdf", "*.docx"]:
        files.extend(sorted(input_dir.glob(ext), key=lambda p: p.name.lower()))

    matrix = []

    for p in files:
        tok = def_tokenize_filename(p.name)
        ticker = tok["ticker"]
        report_date = tok["report_date"]

        matched_final = def_match_rows(p.name, ticker, final_by_file, final_by_ticker)
        matched_reconcile = def_match_rows(p.name, ticker, rec_by_file, rec_by_ticker)
        rec0 = matched_reconcile[0] if matched_reconcile else {}

        if not report_date:
            report_date = def_first(rec0, ["Report Date Parsed", "Report Date"])

        basic = def_extract_basic_fields(p.name, ticker, matched_final, rec0)

        db_rows = len(matched_final)
        split_review_rows = 0
        for r in matched_final:
            if def_first(r, ["Value Split Required"]).upper() == "YES":
                split_review_rows += 1

        table_hit, table_total = def_table_fetching_rate(matched_final, table_inventory_rows, p.name, ticker)

        income_hit, income_total = def_category_rate(matched_final, "Income Statement")
        balance_hit, balance_total = def_category_rate(matched_final, "Balance Sheet")
        cash_hit, cash_total = def_category_rate(matched_final, "Cash Flow Statement")
        ratio_hit, ratio_total = def_category_rate(matched_final, "Ratio Analysis")
        per_hit, per_total = def_category_rate(matched_final, "Per Share Analysis")

        has_action = def_norm_text(p.name) in action_set
        confidence, validation_status = def_confidence(matched_final, split_review_rows, has_action)

        if db_rows == 0:
            validation_status = "NO_DB_READY_ROWS"
            sev = "WARN"
            confidence = "0.00"
        elif split_review_rows > 0:
            validation_status = "DB_READY_WITH_SPLIT_REVIEW"
            sev = "WARN"
        else:
            validation_status = "DB_READY"
            sev = "OK"

        row = {
            "Status Lights": def_lights(sev),
            "Report Date": report_date,
            "Filename": p.name,
            "Broker": basic["Broker"],
            "Analyst": basic["Analyst"],
            "Ticker": ticker,
            "Yfinance Ticker": def_yfinance_ticker(ticker),
            "Bloomberg Ticker": def_bloomberg_ticker(ticker),
            "Name": basic["Name"],
            "Rating": basic["Rating"],
            "Target Price": basic["Target Price"],
            "Table No.": def_int_fmt(table_total),
            "Table Fetching Rate": def_rate_display(table_hit, table_total),
            "Income Statement Fetching Rate": def_rate_display(income_hit, income_total),
            "Balance Sheet Fetching Rate": def_rate_display(balance_hit, balance_total),
            "Cash Flow Statement Fetching Rate": def_rate_display(cash_hit, cash_total),
            "Ratio Analysis Fetching Rate": def_rate_display(ratio_hit, ratio_total),
            "Per Share Analysis Fetching Rate": def_rate_display(per_hit, per_total),
            "Confidence": confidence,
            "Validation Status": validation_status,
            "DB Ready Rows": def_int_fmt(db_rows),
            "Split Review Rows": def_int_fmt(split_review_rows),
            "Severity": sev,
        }
        matrix.append(row)

    meta = {
        "final_csv": str(final_csv) if final_csv else "",
        "reconcile_csv": str(reconcile_csv) if reconcile_csv else "",
        "action_csv": str(action_csv) if action_csv else "",
        "table_inventory_csv": str(table_inventory_csv) if table_inventory_csv else "",
        "input_files": len(files),
        "db_ready_files": sum(1 for r in matrix if def_num(r["DB Ready Rows"]) and def_num(r["DB Ready Rows"]) > 0),
        "warn_files": sum(1 for r in matrix if r["Severity"] == "WARN"),
    }

    return matrix, action_rows, meta


# ==================================================================================================
# def 06_HTML
# ==================================================================================================
def def_table_html(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(c).replace('_', ' ').title())}</th>" for c in fields)

    body = []
    for r in rows:
        tds = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            lc = c.lower()
            cls = "center"

            if any(x in lc for x in ["filename", "analyst", "name", "broker", "status"]):
                cls = "left"
            if any(x in lc for x in ["target price", "confidence", "table no", "rows"]):
                cls = "right"
            if "rate" in lc or "ticker" in lc:
                cls += " wrap"

            tds.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")

        body.append("<tr>" + "".join(tds) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, matrix_rows: list[dict], action_rows: list[dict]) -> None:
    css = """
:root{
  --bg:#07111f;--panel:#0d1b2f;--panel2:#132541;--line:#1f3557;--text:#eef6ff;--muted:#9fb3c8;
  --ok:#38d996;--warn:#f6c85f;--err:#ff6b6b;--accent:#42d9ff;
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:linear-gradient(135deg,#0d1b2f,#091525);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
h1{margin:0;font-size:24px;letter-spacing:.2px}.sub{color:var(--muted);margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;padding:20px 32px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.22)}
.v{font-size:26px;font-weight:800}.k{color:var(--muted);margin-top:4px}
main{padding:0 32px 32px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:18px;margin:18px 0;padding:18px}
.card h2{margin:0 0 14px 0}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{
  position:sticky;top:0;background:var(--panel2);padding:10px;text-align:center;vertical-align:top;
  white-space:normal;word-break:break-word;max-width:180px;z-index:2
}
td{
  padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;text-align:center;
  max-width:360px;white-space:normal;word-break:break-word;line-height:1.35
}
td.left{text-align:left}
td.right{text-align:right;font-variant-numeric:tabular-nums}
td.wrap{white-space:normal;word-break:break-word}
tr:hover td{background:rgba(66,217,255,.07)}
footer{padding:18px 32px;color:var(--muted);border-top:1px solid var(--line)}
@media(max-width:1100px){
  body{font-size:11px}
  td{max-width:260px;padding:7px}
  th{max-width:150px;padding:8px}
}
@media(max-width:760px){
  body{font-size:10px}
  header{padding:18px}
  main{padding:0 14px 20px}
  .grid{padding:14px;grid-template-columns:repeat(2,minmax(120px,1fr))}
  td{max-width:220px}
}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"

    doc = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>VRN One Row File Validation Matrix v06129</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · One Row File Validation Matrix v0.6.12.9</h1>
<div class="sub">report date · broker · analyst · ticker triad · table fetching rate · financial category fetching rate · confidence · validation status</div>
</header>
{card_html}
<main>
{def_table_html("01 One Row File Validation Matrix", matrix_rows)}
{def_table_html("02 Action Queue From v06128", action_rows)}
</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 07_MAIN
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("usage: py <input_dir> <run_root> <run_dir>")

    input_dir = Path(sys.argv[1])
    run_root = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    run_dir.mkdir(parents=True, exist_ok=True)

    matrix_rows, action_rows, meta = def_build_matrix(input_dir, run_root)

    ok_files = sum(1 for r in matrix_rows if r["Severity"] == "OK")
    warn_files = sum(1 for r in matrix_rows if r["Severity"] == "WARN")
    err_files = sum(1 for r in matrix_rows if r["Severity"] == "ERR")

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "counts": {
            "Input Files": len(matrix_rows),
            "DB Ready Files": ok_files,
            "Warn Files": warn_files,
            "Err Files": err_files,
            "Final CSV": "YES" if meta.get("final_csv") else "NO",
            "Reconcile CSV": "YES" if meta.get("reconcile_csv") else "NO",
        },
        "sources": meta,
        "policy": {
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
            "no_fake_fill": "YES",
            "format": "percent with two decimals plus hit/total, e.g. 33.33% 10/30",
        },
    }

    html_path = run_dir / "VRN_One_Row_File_Validation_Matrix_v06129.html"
    json_path = run_dir / "vrn_one_row_file_validation_matrix_v06129.json"
    matrix_csv = run_dir / "vrn_one_row_file_validation_matrix_v06129.csv"
    action_csv = run_dir / "vrn_one_row_file_validation_action_queue_v06129.csv"

    result["outputs"] = {
        "html": str(html_path),
        "json": str(json_path),
        "matrix_csv": str(matrix_csv),
        "action_csv": str(action_csv),
    }

    def_write_csv(matrix_csv, matrix_rows)
    def_write_csv(action_csv, action_rows)
    def_write_json(json_path, result)
    def_write_html(html_path, result, matrix_rows, action_rows)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise