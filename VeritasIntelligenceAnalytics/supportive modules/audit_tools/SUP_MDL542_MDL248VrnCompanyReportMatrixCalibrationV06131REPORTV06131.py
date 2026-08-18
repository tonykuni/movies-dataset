# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_COMPANY_REPORT_MATRIX_CALIBRATION_V06131"


# ==================================================================================================
# def 01_COMMON
# ==================================================================================================
def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    return re.sub(r"\s+", " ", s).strip()


def def_norm_text(x: Any) -> str:
    s = def_clean_text(x).lower()
    s = re.sub(r"[()（）\[\]【】{}<>〈〉《》]", " ", s)
    s = re.sub(r"[\s　,，、;；:：|｜/／\\\-–—_+＋=＝~～!！?？.．]", "", s)
    return s


def def_num(x: Any) -> float | None:
    s = def_clean_text(x).replace(",", "").replace("%", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


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


# ==================================================================================================
# def 02_RATE CALIBRATION
# ==================================================================================================
def def_parse_rate_cell(cell: Any) -> tuple[int, int]:
    s = def_clean_text(cell)
    m = re.search(r"([0-9,]+)\s*/\s*([0-9,]+)", s)
    if not m:
        return 0, 0
    hit = int(m.group(1).replace(",", ""))
    total = int(m.group(2).replace(",", ""))
    return hit, total


def def_rate_cell(hit: int, total: int) -> str:
    if total <= 0:
        return "0.00%\n0/0"
    hit2 = min(max(hit, 0), total)
    pct = hit2 / total * 100
    return f"{pct:,.2f}%\n{hit2:,}/{total:,}"


def def_calibrate_rate_fields(row: dict) -> dict:
    r = dict(row)
    rate_cols = [
        "Table Fetching Rate",
        "Income Statement Fetching Rate",
        "Balance Sheet Fetching Rate",
        "Cash Flow Statement Fetching Rate",
        "Ratio Analysis Fetching Rate",
        "Per Share Analysis Fetching Rate",
    ]
    for c in rate_cols:
        hit, total = def_parse_rate_cell(r.get(c, ""))
        r[c] = def_rate_cell(hit, total)
    return r


# ==================================================================================================
# def 03_NAME CALIBRATION
# ==================================================================================================
def def_extract_name_from_filename(filename: str, ticker: str, old_name: str) -> str:
    fn = Path(filename).stem
    fn = fn.replace("（", "(").replace("）", ")")
    fn = fn.replace("_", "-").replace("－", "-").replace("—", "-")

    # 國泰格式：】神達(3706 TT)-
    m = re.search(r"】\s*([^()\-\s]+)\s*\(\s*" + re.escape(ticker), fn)
    if m:
        return def_clean_text(m.group(1))

    # 晶心科(6533,N,中立)
    m = re.search(r"^([^()\-\s]+)\s*\(\s*" + re.escape(ticker), fn)
    if m:
        return def_clean_text(m.group(1))

    # 華南投顧-3017-奇鋐-1141202
    m = re.search(r"(?:^|[-\s])" + re.escape(ticker) + r"\s*[-]\s*([^-()（）,\s]+(?:-KY)?)", fn, flags=re.I)
    if m:
        cand = def_clean_text(m.group(1))
        cand = re.sub(r"-?memo$", "", cand, flags=re.I)
        return cand

    # 6933-AMAX-KY-個股介紹報告
    m = re.search(r"(?:^|[-\s])" + re.escape(ticker) + r"\s*[-]\s*([A-Za-z0-9]+(?:-KY)?)", fn, flags=re.I)
    if m:
        return def_clean_text(m.group(1))

    # 20250819兆豐個股報告-泓德能源(6873)
    m = re.search(r"[-]\s*([^-\s()（）]+)\s*\(\s*" + re.escape(ticker), fn)
    if m:
        return def_clean_text(m.group(1))

    bad_names = {
        "", "ky", "初次評等買進", "買進", "中立", "未評等", "memo",
        "Meta大砍元宇宙預算", "機器人概念受資金追捧"
    }

    if def_norm_text(old_name) in {def_norm_text(x) for x in bad_names}:
        return ""

    return old_name


def def_calibrate_name(row: dict) -> dict:
    r = dict(row)
    filename = def_first(r, ["Filename"])
    ticker = def_first(r, ["Ticker"])
    old_name = def_first(r, ["Name"])
    new_name = def_extract_name_from_filename(filename, ticker, old_name)
    r["Name Before Calibration"] = old_name
    r["Name"] = new_name
    r["Name Calibration"] = "FIXED" if new_name != old_name else "KEEP"
    return r


# ==================================================================================================
# def 04_VALIDATION CALIBRATION
# ==================================================================================================
def def_db_rows(row: dict) -> int:
    n = def_num(def_first(row, ["Db Ready Rows", "DB Ready Rows"]))
    return int(n or 0)


def def_split_rows(row: dict) -> int:
    n = def_num(def_first(row, ["Split Review Rows"]))
    return int(n or 0)


def def_table_no(row: dict) -> int:
    n = def_num(def_first(row, ["Table No."]))
    return int(n or 0)


def def_is_docx(row: dict) -> bool:
    fn = def_first(row, ["Filename"])
    return Path(fn).suffix.lower() == ".docx"


def def_calibrate_status(row: dict) -> dict:
    r = dict(row)

    db = def_db_rows(r)
    split = def_split_rows(r)
    table_no = def_table_no(r)
    is_docx = def_is_docx(r)

    if db > 0 and split == 0:
        status = "DB_READY"
        sev = "OK"
        next_step = "READY_FOR_DB_VIEW"
    elif db > 0 and split > 0:
        status = "DB_READY_WITH_SPLIT_REVIEW"
        sev = "WARN"
        next_step = "REVIEW_SPLIT_ROWS_ONLY"
    elif is_docx:
        status = "DOCX_COMPANY_MEMO_ROUTE_DOCX_EXTRACTOR"
        sev = "WARN"
        next_step = "ROUTE_DOCX_TABLE_TEXT_EXTRACTOR_IF_FINANCIAL_TABLE_EXISTS"
    elif table_no > 0:
        status = "ACTION_REQUIRED_TABLE_RESTORE"
        sev = "WARN"
        next_step = "RERUN_COMPANY_ONLY_PDF_TABLE_RESTORE"
    else:
        status = "NO_FINANCIAL_TABLE_DISCLOSED"
        sev = "INFO"
        next_step = "KEEP_BASICINFO_ONLY_NOT_FINANCIAL_ERROR"

    r["Validation Status Before Calibration"] = def_first(r, ["Validation Status"])
    r["Validation Status"] = status
    r["Recommended Next Step"] = next_step
    r["Severity"] = sev
    r["Status Lights"] = def_lights(sev)

    # confidence recalibration
    old_conf = def_num(def_first(r, ["Confidence"])) or 0.0
    if status == "DB_READY":
        conf = max(old_conf, 95.0)
    elif status == "DB_READY_WITH_SPLIT_REVIEW":
        conf = max(old_conf, 80.0)
    elif status == "NO_FINANCIAL_TABLE_DISCLOSED":
        conf = 75.0
    elif status == "DOCX_COMPANY_MEMO_ROUTE_DOCX_EXTRACTOR":
        conf = 65.0
    else:
        conf = max(old_conf, 45.0)

    r["Confidence"] = f"{conf:,.2f}"
    return r


# ==================================================================================================
# def 05_HTML
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
            if any(x in lc for x in ["filename", "broker", "analyst", "name", "status", "reason", "step"]):
                cls = "left"
            if any(x in lc for x in ["target price", "confidence", "table no", "rows"]):
                cls = "right"
            if "rate" in lc or "ticker" in lc:
                cls += " wrap"
            tds.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
:root{--bg:#07111f;--panel:#0d1b2f;--panel2:#132541;--line:#1f3557;--text:#eef6ff;--muted:#9fb3c8;--accent:#42d9ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:linear-gradient(135deg,#0d1b2f,#091525);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
h1{margin:0;font-size:24px}.sub{color:var(--muted);margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;padding:20px 32px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.22)}
.v{font-size:26px;font-weight:800}.k{color:var(--muted);margin-top:4px}
main{padding:0 32px 32px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:var(--panel2);padding:10px;text-align:center;vertical-align:top;white-space:normal;word-break:break-word;max-width:180px;z-index:2}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;text-align:center;max-width:420px;white-space:normal;word-break:break-word;line-height:1.35}
td.left{text-align:left}
td.right{text-align:right;font-variant-numeric:tabular-nums}
td.wrap{white-space:normal;word-break:break-word}
tr:hover td{background:rgba(66,217,255,.07)}
footer{padding:18px 32px;color:var(--muted);border-top:1px solid var(--line)}
@media(max-width:900px){body{font-size:10px}main{padding:0 14px 20px}.grid{padding:14px;grid-template-columns:repeat(2,minmax(120px,1fr))}}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"

    body = "".join(def_table_html(t, r) for t, r in sections)

    doc = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>VRN Company Report Matrix Calibration v06131</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · Company Report Matrix Calibration v0.6.13.1</h1>
<div class="sub">company-only · rate capped · name calibrated · action queue separated · no canonical mutation</div>
</header>
{card_html}
<main>{body}</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 06_MAIN
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("usage: py <run_root> <run_dir> <config_dir>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    config_dir = Path(sys.argv[3])
    run_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    source_csv = def_find_latest(run_root, "vrn_v06130_company_report_only_matrix.csv")
    if not source_csv:
        raise RuntimeError("Cannot find vrn_v06130_company_report_only_matrix.csv")

    source_rows = def_read_csv(source_csv)

    calibrated = []
    action = []
    db_ready = []
    no_financial_disclosed = []

    for row in source_rows:
        r = def_calibrate_rate_fields(row)
        r = def_calibrate_name(r)
        r = def_calibrate_status(r)

        calibrated.append(r)

        if r["Validation Status"] in [
            "ACTION_REQUIRED_TABLE_RESTORE",
            "DOCX_COMPANY_MEMO_ROUTE_DOCX_EXTRACTOR",
            "DB_READY_WITH_SPLIT_REVIEW",
        ]:
            action.append(r)

        if r["Validation Status"] == "DB_READY":
            db_ready.append(r)

        if r["Validation Status"] == "NO_FINANCIAL_TABLE_DISCLOSED":
            no_financial_disclosed.append(r)

    overview = [
        {"Status Lights": def_lights("OK"), "Gate": "SOURCE_COMPANY_MATRIX", "Value": str(source_csv), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "COMPANY_REPORT_ROWS", "Value": len(calibrated), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "DB_READY", "Value": len(db_ready), "Severity": "OK"},
        {"Status Lights": def_lights("WARN" if action else "OK"), "Gate": "ACTION_ROWS", "Value": len(action), "Severity": "WARN" if action else "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_FINANCIAL_TABLE_DISCLOSED", "Value": len(no_financial_disclosed), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "RATE_CAP_100_PERCENT", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NAME_CALIBRATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    html_path = run_dir / "VRN_Company_Report_Matrix_Calibration_v06131.html"
    json_path = run_dir / "vrn_company_report_matrix_calibration_v06131.json"
    overview_csv = run_dir / "vrn_v06131_overview.csv"
    calibrated_csv = run_dir / "vrn_v06131_company_report_calibrated_matrix.csv"
    action_csv = run_dir / "vrn_v06131_company_report_action_queue.csv"
    db_ready_csv = run_dir / "vrn_v06131_company_report_db_ready.csv"
    manifest_json = config_dir / "VRN_Company_Report_Only_Input_Manifest_v06131.json"
    manifest_csv = config_dir / "VRN_Company_Report_Only_Input_Manifest_v06131.csv"

    manifest_rows = []
    for r in calibrated:
        manifest_rows.append({
            "Filename": def_first(r, ["Filename"]),
            "Report Date": def_first(r, ["Report Date"]),
            "Broker": def_first(r, ["Broker"]),
            "Analyst": def_first(r, ["Analyst"]),
            "Ticker": def_first(r, ["Ticker"]),
            "Yfinance Ticker": def_first(r, ["Yfinance Ticker"]),
            "Bloomberg Ticker": def_first(r, ["Bloomberg Ticker"]),
            "Name": def_first(r, ["Name"]),
            "Rating": def_first(r, ["Rating"]),
            "Target Price": def_first(r, ["Target Price"]),
            "Validation Status": def_first(r, ["Validation Status"]),
            "Recommended Next Step": def_first(r, ["Recommended Next Step"]),
        })

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_csv": str(source_csv),
        "counts": {
            "Company Reports": len(calibrated),
            "DB Ready": len(db_ready),
            "Action Rows": len(action),
            "No Financial Table": len(no_financial_disclosed),
            "Name Fixed": sum(1 for r in calibrated if r.get("Name Calibration") == "FIXED"),
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "overview_csv": str(overview_csv),
            "calibrated_csv": str(calibrated_csv),
            "action_csv": str(action_csv),
            "db_ready_csv": str(db_ready_csv),
            "manifest_json": str(manifest_json),
            "manifest_csv": str(manifest_csv),
        },
        "policy": {
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
            "no_fake_fill": "YES",
            "rate_cap": "100%",
            "company_report_only": "YES",
        },
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(calibrated_csv, calibrated)
    def_write_csv(action_csv, action)
    def_write_csv(db_ready_csv, db_ready)
    def_write_csv(manifest_csv, manifest_rows)
    def_write_json(manifest_json, {"version": VERSION, "generated_at": result["generated_at"], "company_reports": manifest_rows})
    def_write_json(json_path, result)

    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Calibrated Company Report Matrix", calibrated),
        ("03 Action Queue", action),
        ("04 DB Ready Company Reports", db_ready),
        ("05 No Financial Table Disclosed", no_financial_disclosed),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise