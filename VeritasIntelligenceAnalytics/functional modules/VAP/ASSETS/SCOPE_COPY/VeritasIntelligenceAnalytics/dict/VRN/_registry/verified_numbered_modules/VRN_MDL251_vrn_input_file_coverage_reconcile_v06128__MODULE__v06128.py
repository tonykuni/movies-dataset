# -*- coding: utf-8 -*-
from __future__ import annotations

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


VERSION = "VRN_INPUT_FILE_COVERAGE_RECONCILE_V06128"


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
    if s in ["OK", "YES", "PASS", "GREEN"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "YELLOW", "INFO"]:
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
        # YYYYMMDD
        if len(tok) == 8 and tok[:2] in ["19", "20"]:
            y = int(tok[:4]); m = int(tok[4:6]); d = int(tok[6:8])
            if 1990 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
        # ROC YYYMMDD, e.g. 1141202 => 2025-12-02
        if len(tok) == 7 and tok[:3].isdigit():
            y = int(tok[:3]) + 1911; m = int(tok[3:5]); d = int(tok[5:7])
            if 1990 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                return f"{y:04d}-{m:02d}-{d:02d}"
        # YYMMDD omitted 20, e.g. 251208 => 2025-12-08
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

    report_date = date_candidates[0] if date_candidates else ""
    ticker = ticker_tokens[0] if ticker_tokens else ""

    return {
        "filename_normalized": normalized,
        "digit_tokens": " | ".join(digit_tokens),
        "ticker_tokens": " | ".join(ticker_tokens),
        "date_tokens": " | ".join(date_tokens),
        "ticker": ticker,
        "report_date": report_date,
        "date_candidates": " | ".join(date_candidates),
    }


def def_yfinance_candidates(ticker: str) -> str:
    if not ticker:
        return ""
    return f"{ticker}.TW | {ticker}.TWO"


def def_bloomberg_ticker(ticker: str) -> str:
    return f"{ticker} TT" if ticker else ""


# ==================================================================================================
# def 03_HTML
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
            if any(x in lc for x in ["file", "path", "reason", "items", "tokens", "candidate", "queue"]):
                cls = "left"
            if any(x in lc for x in ["rows", "count", "score", "rate"]):
                cls = "right"
            tds.append(f"<td class='{cls}'>{html.escape(v)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557;position:sticky;top:0;z-index:10}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;padding:20px 32px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.22)}
.v{font-size:26px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 32px 32px}.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;vertical-align:top}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;text-align:center;max-width:900px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.right{text-align:right;font-variant-numeric:tabular-nums}
tr:hover td{background:rgba(66,217,255,.07)}
footer{padding:18px 32px;color:#9fb3c8;border-top:1px solid #1f3557}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"
    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>VRN Input File Coverage Reconcile v06128</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · Input File Coverage Reconcile v0.6.12.8</h1>
<div class="sub">input file list · final financial DB-ready coverage · ticker/date tokenizer · no canonical mutation</div>
</header>
{card_html}
<main>{body}</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 04_MAIN
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("usage: py <input_dir> <run_root> <run_dir>")

    input_dir = Path(sys.argv[1])
    run_root = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    run_dir.mkdir(parents=True, exist_ok=True)

    final_json = def_find_latest(run_root, "vrn_financial_final_seal_v06127.json")
    final_csv = def_find_latest(run_root, "vrn_v06127_financial_db_ready_preview.csv")
    coverage_csv = def_find_latest(run_root, "vrn_v06127_coverage.csv")
    improvement_csv = def_find_latest(run_root, "vrn_v06127_coverage_improvement_queue.csv")

    final_rows = def_read_csv(final_csv) if final_csv else []
    coverage_rows = def_read_csv(coverage_csv) if coverage_csv else []
    improvement_rows = def_read_csv(improvement_csv) if improvement_csv else []

    db_by_ticker = defaultdict(list)
    db_by_filename_norm = defaultdict(list)

    for r in final_rows:
        fn = def_first(r, ["Filename"])
        ticker = def_first(r, ["Ticker"])
        if ticker:
            db_by_ticker[ticker].append(r)
        if fn:
            db_by_filename_norm[def_norm_text(Path(fn).name)].append(r)

    input_files = []
    for ext in ["*.pdf", "*.docx"]:
        input_files.extend(sorted(input_dir.glob(ext)))

    file_rows = []
    action_rows = []

    for p in sorted(input_files, key=lambda x: x.name.lower()):
        tok = def_tokenize_filename(p.name)
        ticker = tok["ticker"]
        report_date = tok["report_date"]
        ext = p.suffix.lower().replace(".", "").upper()

        matched = []
        if ticker and ticker in db_by_ticker:
            matched = db_by_ticker[ticker]
        if not matched:
            matched = db_by_filename_norm.get(def_norm_text(p.name), [])

        years = sorted(set(def_first(r, ["Year"]) for r in matched if def_first(r, ["Year"])))
        cats = sorted(set(def_first(r, ["Category Official En"]) for r in matched if def_first(r, ["Category Official En"])))
        data_items = sorted(set(def_first(r, ["Data Official En"]) for r in matched if def_first(r, ["Data Official En"])))

        split_rows = sum(1 for r in matched if def_first(r, ["Value Split Required"]).upper() == "YES")
        final_alias_rows = sum(1 for r in matched if def_first(r, ["Final Seal Action"]).startswith("FINAL_ALIAS"))
        db_ready_rows = len(matched)

        if db_ready_rows > 0:
            sev = "OK"
            decision = "DB_READY_FINANCIAL_ROWS_FOUND"
            next_step = "Keep. Financial rows are DB-ready. Split review rows may require human audit only if source table shows merged cells."
        else:
            if ext == "DOCX":
                sev = "WARN"
                decision = "DOCX_OR_MEMO_NOT_FINANCIAL_TABLE_SEALED"
                next_step = "If this memo contains financial tables, route DOCX table extractor; otherwise keep as BasicInfo / note document."
            else:
                sev = "WARN"
                decision = "NO_DB_READY_FINANCIAL_ROWS_FOUND"
                next_step = "Check PDF table inventory. If report has annual financial table, rerun table restore; if not disclosed, mark no-financial-table."

        row = {
            "Status Lights": def_lights(sev),
            "Filename": p.name,
            "Extension": ext,
            "Ticker Parsed": ticker,
            "YFinance Ticker Candidates": def_yfinance_candidates(ticker),
            "Bloomberg Ticker": def_bloomberg_ticker(ticker),
            "Report Date Parsed": report_date,
            "Digit Tokens": tok["digit_tokens"],
            "Ticker Tokens": tok["ticker_tokens"],
            "Date Tokens": tok["date_tokens"],
            "DB Ready Rows": db_ready_rows,
            "Years": " | ".join(years),
            "Categories": " | ".join(cats),
            "Data Items Count": len(data_items),
            "Final Alias Rows": final_alias_rows,
            "Split Review Rows": split_rows,
            "Decision": decision,
            "Recommended Next Step": next_step,
            "Severity": sev,
        }
        file_rows.append(row)

        if sev != "OK" or split_rows > 0:
            ar = dict(row)
            ar["Action Type"] = "SPLIT_REVIEW" if split_rows > 0 else decision
            action_rows.append(ar)

    coverage_by_file = []
    for r in coverage_rows:
        sev = def_first(r, ["Severity"]) or "OK"
        nr = dict(r)
        nr["Status Lights"] = def_lights(sev)
        coverage_by_file.append(nr)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "final_json": str(final_json) if final_json else "",
        "final_csv": str(final_csv) if final_csv else "",
        "coverage_csv": str(coverage_csv) if coverage_csv else "",
        "improvement_csv": str(improvement_csv) if improvement_csv else "",
        "counts": {
            "Input Files": len(input_files),
            "PDF/DOCX Audited": len(file_rows),
            "Files With DB Rows": sum(1 for r in file_rows if int(r["DB Ready Rows"]) > 0),
            "Files Without DB Rows": sum(1 for r in file_rows if int(r["DB Ready Rows"]) == 0),
            "DB Ready Rows": len(final_rows),
            "Action Rows": len(action_rows),
            "Coverage Improvement": len(improvement_rows),
        },
        "policy": {
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
            "no_fake_fill": "YES",
            "note": "File without DB-ready financial rows is not automatically an error. It becomes action only when financial table is disclosed but not restored.",
        },
    }

    overview = [
        {"Status Lights": def_lights("OK"), "Gate": "FINAL_JSON", "Value": result["final_json"], "Severity": "OK" if final_json else "ERR"},
        {"Status Lights": def_lights("OK"), "Gate": "FINAL_DB_READY_CSV", "Value": result["final_csv"], "Severity": "OK" if final_csv else "ERR"},
        {"Status Lights": def_lights("OK"), "Gate": "INPUT_FILES", "Value": len(input_files), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "DB_READY_ROWS", "Value": len(final_rows), "Severity": "OK"},
        {"Status Lights": def_lights("WARN" if action_rows else "OK"), "Gate": "ACTION_ROWS", "Value": len(action_rows), "Severity": "WARN" if action_rows else "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_FAKE_FILL", "Value": "YES", "Severity": "OK"},
    ]

    html_path = run_dir / "VRN_Input_File_Coverage_Reconcile_v06128.html"
    json_path = run_dir / "vrn_input_file_coverage_reconcile_v06128.json"
    overview_csv = run_dir / "vrn_v06128_overview.csv"
    file_csv = run_dir / "vrn_v06128_input_file_reconcile.csv"
    action_csv = run_dir / "vrn_v06128_action_queue.csv"
    coverage_out_csv = run_dir / "vrn_v06128_coverage_recheck.csv"

    result["outputs"] = {
        "html": str(html_path),
        "json": str(json_path),
        "overview_csv": str(overview_csv),
        "file_csv": str(file_csv),
        "action_csv": str(action_csv),
        "coverage_csv": str(coverage_out_csv),
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(file_csv, file_rows)
    def_write_csv(action_csv, action_rows)
    def_write_csv(coverage_out_csv, coverage_by_file)
    def_write_json(json_path, result)
    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Input File Reconcile", file_rows),
        ("03 Action Queue", action_rows),
        ("04 Coverage Recheck", coverage_by_file),
        ("05 v06127 Coverage Improvement Queue", improvement_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise