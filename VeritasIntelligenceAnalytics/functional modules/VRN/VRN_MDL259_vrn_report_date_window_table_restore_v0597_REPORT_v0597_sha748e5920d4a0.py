# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import re
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_REPORT_DATE_WINDOW_TABLE_RESTORE_V0597"


# ==================================================================================================
# def 01_CONFIG
# ==================================================================================================
def def_config() -> dict:
    via_root = Path(r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics")
    vrn_root = via_root / "module" / "VRN"
    run_root = vrn_root / "_vrn_operation_ui_runs"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = run_root / f"VRN_REPORT_DATE_WINDOW_TABLE_RESTORE_V0597_INNER_{ts}"

    return {
        "via_root": via_root,
        "vrn_root": vrn_root,
        "canonical_dir": vrn_root / "_vrn_canonical_active",
        "input_dir": vrn_root / "input",
        "run_root": run_root,
        "integrated_root": vrn_root / "_vrn_integrated_trust_runs",
        "run_dir": run_dir,
        "out_html": run_dir / "VRN_Report_Date_Window_Table_Restore_Verifier_v0597.html",
        "out_json": run_dir / "vrn_report_date_window_table_restore_v0597.json",
        "out_window_csv": run_dir / "vrn_report_date_year_window_v0597.csv",
        "out_pdf_table_csv": run_dir / "vrn_pdf_table_restore_matrix_v0597.csv",
        "out_financial_table_csv": run_dir / "vrn_annual_financial_table_candidates_v0597.csv",
        "out_db_period_csv": run_dir / "vrn_db_financial_period_window_matrix_v0597.csv",
        "out_restore_review_csv": run_dir / "vrn_table_restore_review_v0597.csv",
        "out_rule_lock_json": vrn_root / "config" / "VRN_Report_Date_Window_Table_Restore_RuleLock_v0597.json",
    }


# ==================================================================================================
# def 02_UTILITIES
# ==================================================================================================
def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def def_nonblank(x: Any) -> bool:
    return str(x or "").strip() not in ["", "nan", "None", "null", "undefined"]


def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    return re.sub(r"\s+", " ", s).strip()


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
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_first(row: dict, keys: list[str]) -> str:
    for k in keys:
        if def_nonblank(row.get(k, "")):
            return str(row.get(k)).strip()
    return ""


def def_norm_filename(x: Any) -> str:
    s = str(x or "").strip().replace("\\", "/").split("/")[-1]
    return re.sub(r"\.pdf$", "", s, flags=re.I).lower()


def def_ticker_from_text(x: Any) -> str:
    m = re.search(r"\b[1-9]\d{3}\b", str(x or ""))
    return m.group(0) if m else ""


def def_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if "ERR" in s or "RED" in s:
        return "🔴 INPUT  🔴 DB  🔴 TRUST"
    if "WARN" in s or "YELLOW" in s or "ORANGE" in s:
        return "🟢 INPUT  🟡 DB  🟡 TRUST"
    return "🟢 INPUT  🟢 DB  🟢 TRUST"


def def_parse_report_date(row: dict, filename: str = "") -> str:
    candidates = [
        def_first(row, ["Report Date", "Report Date Filename", "Report Date First Page", "Date"]),
        filename,
    ]

    for c in candidates:
        s = str(c or "")
        m = re.search(r"(20\d{2})[-/]?([01]\d)[-/]?([0-3]\d)", s)
        if m:
            return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

        m = re.search(r"\b(\d{3})([01]\d)([0-3]\d)\b", s)
        if m:
            y = int(m.group(1)) + 1911
            return f"{y:04d}-{m.group(2)}-{m.group(3)}"

        m = re.search(r"\b(\d{2})([01]\d)([0-3]\d)\b", s)
        if m:
            yy = int(m.group(1))
            y = 2000 + yy if yy <= 40 else 1900 + yy
            return f"{y:04d}-{m.group(2)}-{m.group(3)}"

    return ""


def def_report_year(report_date: str) -> int | None:
    m = re.search(r"(20\d{2}|19\d{2})", str(report_date or ""))
    return int(m.group(1)) if m else None


def def_year_window(report_date: str) -> list[int]:
    y = def_report_year(report_date)
    if y is None:
        return []
    return list(range(y - 3, y + 4))


def def_extract_years_from_text(text: str) -> list[int]:
    years = set()
    s = str(text or "")

    for m in re.finditer(r"\b(20\d{2}|19\d{2})\b", s):
        years.add(int(m.group(1)))

    # 民國年度 112 / 113 / 114 / 115 類型，限制合理範圍
    for m in re.finditer(r"(?<!\d)(10[0-9]|11[0-9]|12[0-9])(?!\d)", s):
        y = int(m.group(1)) + 1911
        if 2011 <= y <= 2049:
            years.add(y)

    # 26E / 2026E / FY26E
    for m in re.finditer(r"(?i)\b(?:FY)?(\d{2})E\b", s):
        yy = int(m.group(1))
        y = 2000 + yy if yy <= 40 else 1900 + yy
        years.add(y)

    return sorted(years)


def def_num_like_count(text: str) -> int:
    return len(re.findall(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?%?|[-+]?\d+\.\d+%?", str(text or "")))


def def_financial_keywords() -> list[str]:
    return [
        "revenue", "sales", "gross profit", "operating income", "operating profit", "net income",
        "eps", "margin", "roe", "roa", "assets", "liabilities", "equity", "cash flow",
        "inventory", "receivable", "capex", "free cash flow", "ebit", "ebitda",
        "營收", "收入", "毛利", "營業利益", "營業收入", "淨利", "每股盈餘", "毛利率",
        "營益率", "淨利率", "資產", "負債", "權益", "現金流", "存貨", "應收",
        "資本支出", "自由現金流", "損益", "資產負債", "比率", "每股"
    ]


def def_keyword_score(text: str) -> int:
    s = str(text or "").lower()
    return sum(1 for k in def_financial_keywords() if k.lower() in s)


def def_table_to_text(table: list[list[Any]]) -> str:
    parts = []
    for row in table or []:
        for cell in row or []:
            if cell is not None:
                parts.append(str(cell))
    return " ".join(parts)


def def_table_shape(table: list[list[Any]]) -> tuple[int, int]:
    rows = len(table or [])
    cols = max((len(r or []) for r in table or []), default=0)
    return rows, cols


def def_table_orientation(table: list[list[Any]]) -> str:
    if not table:
        return "UNKNOWN"
    rows, cols = def_table_shape(table)
    top = " ".join(str(c or "") for c in (table[0] if table else []))
    left = " ".join(str((r or [""])[0] or "") for r in table[: min(rows, 12)])
    top_years = len(def_extract_years_from_text(top))
    left_years = len(def_extract_years_from_text(left))
    if top_years >= 2 and top_years >= left_years:
        return "YEARS_AS_COLUMNS"
    if left_years >= 2 and left_years > top_years:
        return "YEARS_AS_ROWS"
    return "UNKNOWN"


def def_is_annual_financial_table(table: list[list[Any]], report_window: list[int]) -> dict:
    text = def_table_to_text(table)
    rows, cols = def_table_shape(table)
    years = def_extract_years_from_text(text)
    year_in_window = [y for y in years if y in report_window]
    kscore = def_keyword_score(text)
    nscore = def_num_like_count(text)
    orientation = def_table_orientation(table)

    # 年財務表通常至少有 2 個年份、2 個財務關鍵字、足夠數字、表格形狀不要太小
    is_candidate = (
        rows >= 3 and
        cols >= 3 and
        len(year_in_window) >= 2 and
        kscore >= 2 and
        nscore >= 6
    )

    restore_ok = (
        is_candidate and
        orientation in ["YEARS_AS_COLUMNS", "YEARS_AS_ROWS"] and
        rows >= 4 and
        cols >= 3
    )

    if restore_ok:
        severity = "OK"
    elif is_candidate:
        severity = "WARN"
    else:
        severity = "INFO"

    return {
        "is_candidate": is_candidate,
        "restore_ok": restore_ok,
        "years": years,
        "year_in_window": year_in_window,
        "keyword_score": kscore,
        "numeric_score": nscore,
        "orientation": orientation,
        "rows": rows,
        "cols": cols,
        "severity": severity,
    }


# ==================================================================================================
# def 03_SOURCE_RESOLUTION
# ==================================================================================================
def def_resolve_basic_source(cfg: dict) -> Path:
    p = cfg["canonical_dir"] / "vrn_basicinfo_active.csv"
    return p


def def_resolve_financial_source(cfg: dict) -> Path:
    p = cfg["canonical_dir"] / "vrn_financial_active.csv"
    return p


def def_pdf_index(input_dir: Path) -> dict:
    out = {}
    if not input_dir.exists():
        return out
    for p in input_dir.rglob("*.pdf"):
        out[def_norm_filename(p.name)] = p
    return out


def def_match_pdf_for_basic(row: dict, pdfs: dict) -> Path | None:
    fn = def_norm_filename(def_first(row, ["Filename", "File"]))
    if fn in pdfs:
        return pdfs[fn]

    ticker = def_first(row, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker"])
    for key, p in pdfs.items():
        if ticker and ticker in key:
            return p
    return None


# ==================================================================================================
# def 04_SCAN_PDF_TABLES
# ==================================================================================================
def def_scan_pdf_tables(basic_rows: list[dict], pdfs: dict) -> tuple[list[dict], list[dict], list[dict]]:
    pdf_table_rows = []
    financial_table_rows = []
    review_rows = []

    try:
        import pdfplumber
        pdfplumber_ok = True
        pdfplumber_error = ""
    except Exception as e:
        pdfplumber_ok = False
        pdfplumber_error = str(e)

    for b in basic_rows:
        filename = def_first(b, ["Filename", "File"])
        ticker = def_first(b, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker"])
        name = def_first(b, ["Name"])
        report_date = def_parse_report_date(b, filename)
        window = def_year_window(report_date)
        pdf = def_match_pdf_for_basic(b, pdfs)

        if not pdfplumber_ok:
            review_rows.append({
                "Status Lights": "🔴 INPUT  🔴 DB  🔴 TRUST",
                "Filename": filename,
                "Ticker": ticker,
                "Issue": "pdfplumber not available",
                "Detail": pdfplumber_error,
                "Severity": "ERR",
            })
            continue

        if not pdf:
            review_rows.append({
                "Status Lights": "🔴 INPUT  🔴 DB  🔴 TRUST",
                "Filename": filename,
                "Ticker": ticker,
                "Issue": "PDF not found in input",
                "Detail": "",
                "Severity": "ERR",
            })
            continue

        try:
            with pdfplumber.open(str(pdf)) as doc:
                table_count = 0
                candidate_count = 0
                restore_ok_count = 0

                for page_idx, page in enumerate(doc.pages, start=1):
                    tables = []
                    try:
                        tables = page.extract_tables() or []
                    except Exception:
                        tables = []

                    for table_idx, table in enumerate(tables, start=1):
                        table_count += 1
                        ev = def_is_annual_financial_table(table, window)
                        text = def_table_to_text(table)
                        years = ev["years"]
                        year_in_window = ev["year_in_window"]

                        row = {
                            "Status Lights": def_lights(ev["severity"]),
                            "Filename": filename,
                            "Ticker": ticker,
                            "Name": name,
                            "Report Date": report_date,
                            "Expected Year Window": ", ".join(str(y) for y in window),
                            "PDF": str(pdf),
                            "Page": page_idx,
                            "Table Index": table_idx,
                            "Rows": ev["rows"],
                            "Cols": ev["cols"],
                            "Years Found": ", ".join(str(y) for y in years),
                            "Years In Window": ", ".join(str(y) for y in year_in_window),
                            "Keyword Score": ev["keyword_score"],
                            "Numeric Score": ev["numeric_score"],
                            "Orientation": ev["orientation"],
                            "Annual Financial Candidate": ev["is_candidate"],
                            "Restore OK": ev["restore_ok"],
                            "Preview Text": text[:500],
                            "Severity": ev["severity"],
                        }
                        pdf_table_rows.append(row)

                        if ev["is_candidate"]:
                            candidate_count += 1
                            financial_table_rows.append(row)

                        if ev["restore_ok"]:
                            restore_ok_count += 1

                if table_count == 0:
                    review_rows.append({
                        "Status Lights": "🟢 INPUT  🟡 DB  🟡 TRUST",
                        "Filename": filename,
                        "Ticker": ticker,
                        "Issue": "No tables extracted from PDF",
                        "Detail": str(pdf),
                        "Severity": "WARN",
                    })
                elif candidate_count == 0:
                    review_rows.append({
                        "Status Lights": "🟢 INPUT  🟡 DB  🟡 TRUST",
                        "Filename": filename,
                        "Ticker": ticker,
                        "Issue": "No annual financial table candidate found",
                        "Detail": f"tables={table_count}, report_window={window}",
                        "Severity": "WARN",
                    })
                elif restore_ok_count == 0:
                    review_rows.append({
                        "Status Lights": "🟢 INPUT  🟡 DB  🟡 TRUST",
                        "Filename": filename,
                        "Ticker": ticker,
                        "Issue": "Annual financial table candidates exist but restore check weak",
                        "Detail": f"candidates={candidate_count}",
                        "Severity": "WARN",
                    })

        except Exception as e:
            review_rows.append({
                "Status Lights": "🔴 INPUT  🔴 DB  🔴 TRUST",
                "Filename": filename,
                "Ticker": ticker,
                "Issue": "PDF scan error",
                "Detail": str(e),
                "Severity": "ERR",
            })

    return pdf_table_rows, financial_table_rows, review_rows


# ==================================================================================================
# def 05_DB_PERIOD_WINDOW
# ==================================================================================================
def def_db_period_matrix(basic_rows: list[dict], fin_rows: list[dict]) -> tuple[list[dict], list[dict]]:
    fin_by_file = {}
    fin_by_ticker = {}

    for r in fin_rows:
        fn = def_norm_filename(def_first(r, ["Filename", "File", "Source File"]))
        tk = def_first(r, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker"])
        if fn:
            fin_by_file.setdefault(fn, []).append(r)
        if tk:
            fin_by_ticker.setdefault(tk, []).append(r)

    rows = []
    review = []

    for b in basic_rows:
        filename = def_first(b, ["Filename", "File"])
        fn_key = def_norm_filename(filename)
        ticker = def_first(b, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker"])
        name = def_first(b, ["Name"])
        report_date = def_parse_report_date(b, filename)
        window = def_year_window(report_date)

        frs = fin_by_file.get(fn_key, [])
        if not frs and ticker:
            frs = fin_by_ticker.get(ticker, [])

        years = sorted(set(y for r in frs for y in def_extract_years_from_text(def_first(r, ["Year", "Fiscal Year", "Time"]))))
        in_window = [y for y in years if y in window]
        out_window = [y for y in years if y not in window]

        missing_window = [y for y in window if y not in in_window]
        period_ok = len(in_window) >= min(3, len(window)) and len(out_window) == 0

        if period_ok:
            sev = "OK"
        elif len(in_window) >= 1:
            sev = "WARN"
        else:
            sev = "ERR"

        rows.append({
            "Status Lights": def_lights(sev),
            "Filename": filename,
            "Ticker": ticker,
            "Name": name,
            "Report Date": report_date,
            "Expected Year Window": ", ".join(str(y) for y in window),
            "DB Years Found": ", ".join(str(y) for y in years),
            "DB Years In Window": ", ".join(str(y) for y in in_window),
            "DB Years Out Of Window": ", ".join(str(y) for y in out_window),
            "Missing Window Years": ", ".join(str(y) for y in missing_window),
            "Financial Rows": len(frs),
            "Period Window OK": period_ok,
            "Severity": sev,
        })

        if sev != "OK":
            review.append({
                "Status Lights": def_lights(sev),
                "Filename": filename,
                "Ticker": ticker,
                "Issue": "DB financial years not fully aligned with Report Date ±3 years",
                "Expected Year Window": ", ".join(str(y) for y in window),
                "DB Years Found": ", ".join(str(y) for y in years),
                "Severity": sev,
            })

    return rows, review


def def_report_window_matrix(basic_rows: list[dict]) -> list[dict]:
    rows = []
    for b in basic_rows:
        filename = def_first(b, ["Filename", "File"])
        report_date = def_parse_report_date(b, filename)
        window = def_year_window(report_date)
        sev = "OK" if report_date and window else "ERR"
        rows.append({
            "Status Lights": def_lights(sev),
            "Filename": filename,
            "Ticker": def_first(b, ["Ticker", "Primary TW_TICKER", "Primary Tw Ticker"]),
            "Name": def_first(b, ["Name"]),
            "Report Date": report_date,
            "Report Year": def_report_year(report_date) or "",
            "Expected Data Period": ", ".join(str(y) for y in window),
            "Rule": "ReportYear -3 to ReportYear +3",
            "Severity": sev,
        })
    return rows


# ==================================================================================================
# def 06_HTML
# ==================================================================================================
def def_format_header(x: str) -> str:
    acr = {"DB", "API", "ID", "URL", "HTML", "JSON", "CSV", "SQL", "PDF", "SSOT", "TWD", "EPS"}
    out = []
    for p in str(x or "").replace("_", " ").split():
        u = p.upper()
        if u in acr:
            out.append(u)
        elif re.search(r"[\u4e00-\u9fff]", p):
            out.append(p)
        else:
            out.append(p[:1].upper() + p[1:].lower())
    return " ".join(out)


def def_cell_class(col: str, val: Any) -> str:
    c = col.lower()
    if col == "Status Lights":
        return "status"
    if any(k in c for k in ["filename", "file", "path", "source", "text", "preview", "detail", "issue", "pdf"]):
        return "left"
    if any(k in c for k in ["rows", "cols", "score", "count", "index"]):
        return "num"
    if len(str(val or "")) > 35:
        return "left"
    return "center"


def def_band(row: dict) -> str:
    s = str(row.get("Severity") or row.get("Status") or "").upper()
    if "ERR" in s or "RED" in s:
        return "red"
    if "WARN" in s or "YELLOW" in s or "ORANGE" in s:
        return "yellow"
    return "green"


def def_table(rows: list[dict], limit: int = 1800) -> str:
    if not rows:
        return "<div class='empty'>No rows.</div>"
    rows = rows[:limit]
    cols = []
    for r in rows:
        for k in r:
            if k not in cols:
                cols.append(k)
    if "Status Lights" in cols:
        cols = ["Status Lights"] + [c for c in cols if c != "Status Lights"]
    else:
        cols = ["Status Lights"] + cols

    th = "".join(f"<th>{def_h(def_format_header(c))}</th>" for c in cols)
    trs = []
    for r in rows:
        band = def_band(r)
        cells = []
        for c in cols:
            val = r.get(c, "")
            if c == "Status Lights" and not val:
                val = def_lights(r.get("Severity", "OK"))
            cls = def_cell_class(c, val)
            collapse = " collapse" if cls == "left" and len(str(val)) > 160 else ""
            cells.append(f"<td class='{cls}{collapse}'>{def_h(val)}</td>")
        trs.append(f"<tr class='{band}'>" + "".join(cells) + "</tr>")
    return "<table><thead><tr>" + th + "</tr></thead><tbody>" + "\n".join(trs) + "</tbody></table>"


def def_render_html(path: Path, result: dict, overview: list[dict], windows: list[dict], db_period: list[dict], pdf_tables: list[dict], fin_tables: list[dict], review: list[dict]) -> None:
    cards = [
        ("System Pass", result["system_pass"]),
        ("Reports", result["counts"]["reports"]),
        ("PDF Tables", result["counts"]["pdf_tables"]),
        ("Annual Candidates", result["counts"]["annual_financial_tables"]),
        ("Restore OK", result["counts"]["restore_ok_tables"]),
        ("DB Period OK", result["counts"]["db_period_ok"]),
        ("Review Rows", result["counts"]["review_rows"]),
        ("Preview Only", True),
    ]
    card_html = "".join(f"<div class='stat'><div class='n'>{def_h(v)}</div><div class='l'>{def_h(k)}</div></div>" for k, v in cards)

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN Report-Date Window Table Restore Verifier v05.9.7</title>
<style>
:root {{
  --bg:#f5f4f0;--sf:#fff;--sf2:#fafaf8;--bd:#dbd9d3;--bl:#4c78a8;--tl:#439a9a;--vi:#7a6daa;
  --gn:#5a9e6f;--gn-l:#cde8d5;--am:#c4943a;--am-l:#f5e2b8;--co:#c96b5a;--co-l:#f5d0c8;
  --i0:#1e1d1a;--i2:#6b6860;--i3:#9c9890;--mo:Consolas,monospace;--sa:"Segoe UI","Microsoft JhengHei",system-ui,sans-serif;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);font-family:var(--sa);font-size:11px;color:var(--i0)}}
.wrap{{max-width:1820px;margin:0 auto;padding:12px}}
.hdr{{background:var(--sf);border:1px solid var(--bd);border-radius:16px;padding:16px 18px;margin-bottom:10px;display:flex;gap:12px;position:relative;overflow:hidden}}
.hdr:before{{content:'';position:absolute;top:0;left:0;right:0;height:3px;background:linear-gradient(90deg,var(--bl),var(--tl),var(--vi),var(--am),var(--co))}}
.logo{{width:42px;height:42px;border-radius:12px;background:#1e3a5f;color:#8dcff0;display:flex;align-items:center;justify-content:center;font-weight:900;font-family:var(--mo)}}
.h1{{font-size:20px;font-weight:850}}.h1 span{{color:var(--bl)}}.sub{{font-size:10px;color:var(--i3);margin-top:2px}}
.tabs{{display:flex;gap:4px;margin-bottom:10px;flex-wrap:wrap}}
.tabs button{{border:1px solid var(--bd);background:var(--sf);border-radius:999px;padding:8px 14px;font-weight:750;font-size:11px;cursor:pointer;transition:.16s;color:var(--i2)}}
.tabs button:hover{{transform:translateY(-1px);box-shadow:0 8px 18px rgba(30,29,26,.08);border-color:var(--bl);color:var(--bl)}}
.tabs button.on{{background:var(--bl);border-color:var(--bl);color:white}}
.tabs button:active{{transform:scale(.94) translateY(1px);box-shadow:inset 0 2px 8px rgba(0,0,0,.18)}}
.page{{display:none}}.page.on{{display:block}}
.card{{background:var(--sf);border:1px solid var(--bd);border-radius:16px;margin-bottom:10px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.035)}}
.card h3{{margin:0;padding:10px 12px;background:var(--sf2);border-bottom:1px solid var(--bd);font-size:12px}}
.statgrid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:8px;margin-bottom:10px}}
.stat{{background:var(--sf);border:1px solid var(--bd);border-radius:14px;padding:10px;transition:.16s}}
.stat:hover{{transform:translateY(-2px) scale(1.01);box-shadow:0 12px 26px rgba(30,29,26,.10)}}
.stat .n{{text-align:right;font-family:var(--mo);font-size:20px;font-weight:900}}.stat .l{{text-align:center;color:var(--i3);font-size:9px;text-transform:uppercase}}
.tablewrap{{overflow:auto;max-height:76vh;border:1px solid var(--bd);border-radius:12px;resize:both;background:var(--sf)}}
table{{border-collapse:collapse;width:max-content;min-width:100%;font-size:10px;table-layout:auto}}
th{{position:sticky;top:0;z-index:2;background:#ef0000;color:#fff;padding:8px 9px;border:1px solid var(--bd);text-align:center;vertical-align:top;white-space:normal;overflow-wrap:anywhere}}
td{{padding:6px 8px;border:1px solid var(--bd);vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;max-width:880px;line-height:1.35;text-align:center}}
td.left{{text-align:left;min-width:260px;max-width:1020px}}
td.center{{text-align:center}}
td.num{{text-align:right;font-family:var(--mo);font-variant-numeric:tabular-nums;white-space:nowrap}}
td.status{{text-align:center;font-family:var(--mo);font-weight:900;white-space:nowrap;min-width:150px}}
td.collapse{{display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden}}
tr.green td{{background:linear-gradient(0deg,rgba(205,232,213,.84),rgba(255,255,255,.92))}}
tr.yellow td{{background:linear-gradient(0deg,rgba(245,226,184,.86),rgba(255,255,255,.92))}}
tr.red td{{background:linear-gradient(0deg,rgba(245,208,200,.9),rgba(255,255,255,.92))}}
pre{{background:#1e1d1a;color:#d1fae5;border-radius:10px;padding:12px;overflow:auto;white-space:pre-wrap}}
</style>
<script>
function tab(id){{
  document.querySelectorAll('.page').forEach(p=>p.classList.remove('on'));
  document.querySelectorAll('.tabs button').forEach(b=>b.classList.remove('on'));
  document.getElementById(id).classList.add('on');
  document.getElementById('b_'+id).classList.add('on');
  try{{ if(navigator.vibrate) navigator.vibrate(18); }}catch(e){{}}
}}
</script>
</head>
<body>
<div class="wrap">
  <div class="hdr">
    <div class="logo">VRN</div>
    <div>
      <div class="h1"><span>VeritasReportNova</span> Report-Date Window + PDF Table Restore Verifier <span style="font-size:12px;color:var(--i3)">v05.9.7</span></div>
      <div class="sub">ReportYear ±3 · all PDF tables · annual financial table detection · restore verification · DB period alignment</div>
    </div>
  </div>

  <div class="tabs">
    <button id="b_overview" class="on" onclick="tab('overview')">01 Overview</button>
    <button id="b_window" onclick="tab('window')">02 Report Date Window</button>
    <button id="b_db" onclick="tab('db')">03 DB Period</button>
    <button id="b_pdf" onclick="tab('pdf')">04 All PDF Tables</button>
    <button id="b_fin" onclick="tab('fin')">05 Annual Financial Tables</button>
    <button id="b_review" onclick="tab('review')">06 Review</button>
    <button id="b_json" onclick="tab('json')">07 JSON</button>
  </div>

  <div id="overview" class="page on"><div class="statgrid">{card_html}</div><div class="card"><h3>Overview Matrix</h3><div class="tablewrap">{def_table(overview)}</div></div></div>
  <div id="window" class="page"><div class="card"><h3>Report Date ±3 Year Window</h3><div class="tablewrap">{def_table(windows)}</div></div></div>
  <div id="db" class="page"><div class="card"><h3>DB Financial Period Window</h3><div class="tablewrap">{def_table(db_period)}</div></div></div>
  <div id="pdf" class="page"><div class="card"><h3>All PDF Tables Restore Matrix</h3><div class="tablewrap">{def_table(pdf_tables)}</div></div></div>
  <div id="fin" class="page"><div class="card"><h3>Annual Financial Table Candidates</h3><div class="tablewrap">{def_table(fin_tables)}</div></div></div>
  <div id="review" class="page"><div class="card"><h3>Restore / Period Review</h3><div class="tablewrap">{def_table(review)}</div></div></div>
  <div id="json" class="page"><div class="card"><h3>JSON</h3><pre>{def_h(json.dumps(result, ensure_ascii=False, indent=2))}</pre></div></div>
</div>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 07_MAIN
# ==================================================================================================
def def_main() -> None:
    cfg = def_config()
    cfg["run_dir"].mkdir(parents=True, exist_ok=True)

    basic_src = def_resolve_basic_source(cfg)
    fin_src = def_resolve_financial_source(cfg)

    basic_rows = def_read_csv(basic_src)
    fin_rows = def_read_csv(fin_src)
    pdfs = def_pdf_index(cfg["input_dir"])

    window_rows = def_report_window_matrix(basic_rows)
    db_period_rows, db_review_rows = def_db_period_matrix(basic_rows, fin_rows)
    pdf_table_rows, annual_table_rows, pdf_review_rows = def_scan_pdf_tables(basic_rows, pdfs)

    all_review = []
    all_review.extend(db_review_rows)
    all_review.extend(pdf_review_rows)

    restore_ok_count = sum(1 for r in annual_table_rows if str(r.get("Restore OK", "")).lower() == "true")
    db_period_ok_count = sum(1 for r in db_period_rows if str(r.get("Period Window OK", "")).lower() == "true")
    err_review = sum(1 for r in all_review if r.get("Severity") == "ERR")

    overview = [
        {"Status Lights": def_lights("OK" if basic_rows else "ERR"), "Gate": "BASIC_SOURCE", "Value": str(basic_src), "Severity": "OK" if basic_rows else "ERR"},
        {"Status Lights": def_lights("OK" if fin_rows else "ERR"), "Gate": "FINANCIAL_SOURCE", "Value": str(fin_src), "Severity": "OK" if fin_rows else "ERR"},
        {"Status Lights": def_lights("OK"), "Gate": "INPUT_PDF_COUNT", "Value": len(pdfs), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "REPORTS", "Value": len(basic_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "PDF_TABLES_EXTRACTED", "Value": len(pdf_table_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK" if annual_table_rows else "WARN"), "Gate": "ANNUAL_FINANCIAL_TABLE_CANDIDATES", "Value": len(annual_table_rows), "Severity": "OK" if annual_table_rows else "WARN"},
        {"Status Lights": def_lights("OK" if restore_ok_count else "WARN"), "Gate": "RESTORE_OK_TABLES", "Value": restore_ok_count, "Severity": "OK" if restore_ok_count else "WARN"},
        {"Status Lights": def_lights("OK" if db_period_ok_count == len(db_period_rows) else "WARN"), "Gate": "DB_PERIOD_OK_REPORTS", "Value": f"{db_period_ok_count}/{len(db_period_rows)}", "Severity": "OK" if db_period_ok_count == len(db_period_rows) else "WARN"},
        {"Status Lights": def_lights("ERR" if err_review else ("WARN" if all_review else "OK")), "Gate": "REVIEW_ROWS", "Value": len(all_review), "Severity": "ERR" if err_review else ("WARN" if all_review else "OK")},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": True, "Severity": "OK"},
    ]

    rule_lock = {
        "version": VERSION,
        "rules": [
            "Expected financial data period is ReportYear-3 through ReportYear+3.",
            "PDF table scanning covers all pages, not only first page.",
            "Annual financial table candidate requires year headers/rows, financial keywords, and numeric density.",
            "Table restore OK requires plausible orientation and sufficient table shape.",
            "Canonical financial DB is checked against report-date year window.",
            "This layer is read-only and does not mutate canonical/stable.",
        ],
    }
    def_write_json(cfg["out_rule_lock_json"], rule_lock)

    result = {
        "version": VERSION,
        "generated_at": def_now(),
        "system_pass": bool(basic_rows and fin_rows),
        "mode": "READ_ONLY_REPORT_DATE_WINDOW_TABLE_RESTORE_VERIFIER",
        "sources": {
            "basic_source": str(basic_src),
            "financial_source": str(fin_src),
            "input_dir": str(cfg["input_dir"]),
        },
        "counts": {
            "reports": len(basic_rows),
            "financial_rows": len(fin_rows),
            "input_pdfs": len(pdfs),
            "pdf_tables": len(pdf_table_rows),
            "annual_financial_tables": len(annual_table_rows),
            "restore_ok_tables": restore_ok_count,
            "db_period_ok": db_period_ok_count,
            "review_rows": len(all_review),
        },
        "outputs": {
            "html": str(cfg["out_html"]),
            "json": str(cfg["out_json"]),
            "report_window_csv": str(cfg["out_window_csv"]),
            "pdf_table_csv": str(cfg["out_pdf_table_csv"]),
            "annual_financial_table_csv": str(cfg["out_financial_table_csv"]),
            "db_period_csv": str(cfg["out_db_period_csv"]),
            "restore_review_csv": str(cfg["out_restore_review_csv"]),
            "rule_lock_json": str(cfg["out_rule_lock_json"]),
        },
    }

    def_write_csv(cfg["out_window_csv"], window_rows)
    def_write_csv(cfg["out_pdf_table_csv"], pdf_table_rows)
    def_write_csv(cfg["out_financial_table_csv"], annual_table_rows)
    def_write_csv(cfg["out_db_period_csv"], db_period_rows)
    def_write_csv(cfg["out_restore_review_csv"], all_review)
    def_write_json(cfg["out_json"], result)
    def_render_html(cfg["out_html"], result, overview, window_rows, db_period_rows, pdf_table_rows, annual_table_rows, all_review)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise