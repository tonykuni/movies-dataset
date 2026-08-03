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


VERSION = "VRN_FINANCIALDATA_REPAIR_ROUTER_V06151"


def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def def_norm_key(x: Any) -> str:
    s = def_clean_text(x).lower()
    s = re.sub(r"[\\/:*?\"<>|()\[\]{}【】（）,，。．\s]+", "", s)
    return s


def def_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "READY", "PASS", "YES"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "PARTIAL", "REVIEW", "OPTIONAL"]:
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
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_find_latest(root: Path, patterns: list[str]) -> Path | None:
    hits = []
    for pat in patterns:
        hits.extend(root.rglob(pat))
    hits = [p for p in hits if p.is_file()]
    hits = sorted(set(hits), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_is_target_status(status: str) -> bool:
    s = def_clean_text(status).upper()
    return s.startswith("REPAIR_REQUIRED") or s.startswith("PARTIAL_FINANCIALDATA")


def def_is_optional_status(status: str) -> bool:
    return "OPTIONAL_NO_DISCLOSED_FINANCIAL_TABLE" in def_clean_text(status).upper()


def def_file_tokens(filename: str) -> set[str]:
    base = Path(filename).name
    parts = re.split(r"[\s\-_()（）【】\[\],，.。]+", base)
    toks = set()
    for p in parts:
        p = def_clean_text(p)
        if p:
            toks.add(p)
            toks.add(def_norm_key(p))
    return toks


def def_row_matches_target(row: dict, filename: str, ticker: str) -> bool:
    fn = def_clean_text(row.get("Filename") or row.get("filename") or row.get("File") or row.get("file") or "")
    tk = def_clean_text(row.get("Ticker") or row.get("ticker") or row.get("stock_id") or row.get("Stock ID") or "")
    if ticker and tk and ticker == tk:
        return True
    if filename and fn:
        return def_norm_key(Path(filename).name) == def_norm_key(Path(fn).name)
    return False


def def_scan_csv_sources(run_root: Path, target_rows: list[dict]) -> tuple[list[dict], dict]:
    source_files = []
    for p in run_root.rglob("*.csv"):
        name = p.name.lower()
        if any(k in name for k in [
            "financial", "table", "coverage", "action", "basic", "matrix",
            "candidate", "restored", "quarantine", "review", "validated"
        ]):
            source_files.append(p)

    source_files = sorted(set(source_files), key=lambda x: x.stat().st_mtime, reverse=True)

    evidence_rows = []
    index = {}

    for p in source_files[:220]:
        rows = def_read_csv(p)
        if not rows:
            continue

        cols = set(rows[0].keys())
        col_text = " ".join(cols).lower()

        source_type = "OTHER"
        if "pdf table" in p.name.lower() or "table_inventory" in p.name.lower() or "table" in col_text:
            source_type = "TABLE_EVIDENCE"
        if "financial" in p.name.lower() or "category official" in col_text or "data official" in col_text:
            source_type = "FINANCIAL_EVIDENCE"
        if "review" in p.name.lower() or "quarantine" in p.name.lower():
            source_type = "REVIEW_OR_QUARANTINE"
        if "basic" in p.name.lower():
            source_type = "BASICINFO_EVIDENCE"

        for t in target_rows:
            filename = def_clean_text(t.get("Filename", ""))
            ticker = def_clean_text(t.get("Ticker", ""))
            matched_count = 0
            financial_like = 0
            table_like = 0
            quarantine_like = 0
            years = set()
            cats = set()

            for r in rows:
                if not def_row_matches_target(r, filename, ticker):
                    continue

                matched_count += 1
                if source_type == "FINANCIAL_EVIDENCE":
                    financial_like += 1
                if source_type == "TABLE_EVIDENCE":
                    table_like += 1
                if source_type == "REVIEW_OR_QUARANTINE":
                    quarantine_like += 1

                y = def_clean_text(r.get("Year") or r.get("year") or r.get("Financial Years") or "")
                if y:
                    for yy in re.findall(r"20\d{2}", y):
                        years.add(yy)

                c = def_clean_text(
                    r.get("Category Official En") or
                    r.get("Category Official EN") or
                    r.get("Category") or
                    r.get("Financial Categories") or
                    ""
                )
                if c:
                    for cc in c.split("|"):
                        cc = def_clean_text(cc)
                        if cc:
                            cats.add(cc)

            if matched_count:
                key = f"{ticker}|{def_norm_key(filename)}"
                rec = {
                    "Filename": filename,
                    "Ticker": ticker,
                    "Source Type": source_type,
                    "Source File": str(p),
                    "Rows Matched": matched_count,
                    "Financial-Like Rows": financial_like,
                    "Table-Like Rows": table_like,
                    "Quarantine-Like Rows": quarantine_like,
                    "Years Found": " | ".join(sorted(years)),
                    "Categories Found": " | ".join(sorted(cats)),
                    "Source MTime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                }
                evidence_rows.append(rec)
                index.setdefault(key, []).append(rec)

    return evidence_rows, index


def def_route_target(t: dict, evidence_index: dict) -> dict:
    filename = def_clean_text(t.get("Filename", ""))
    ticker = def_clean_text(t.get("Ticker", ""))
    key = f"{ticker}|{def_norm_key(filename)}"
    ev = evidence_index.get(key, [])

    table_rows = sum(int(e.get("Table-Like Rows", 0) or 0) for e in ev)
    financial_rows = sum(int(e.get("Financial-Like Rows", 0) or 0) for e in ev)
    quarantine_rows = sum(int(e.get("Quarantine-Like Rows", 0) or 0) for e in ev)

    status = def_clean_text(t.get("Validation Status", ""))
    confidence = def_clean_text(t.get("Confidence", ""))

    if def_is_optional_status(status):
        route = "OPTIONAL_NO_FINANCIAL_REPAIR"
        next_step = "Do not extract financial table unless user requires memo/report note financial section."
        severity = "WARN"
    elif financial_rows > 0 and table_rows > 0:
        route = "REUSE_EXISTING_FINANCIAL_AND_TABLE_EVIDENCE"
        next_step = "Run targeted join repair: use existing table/financial rows, fix source selector, year window, and SSOT alias only."
        severity = "WARN"
    elif table_rows > 0 and financial_rows == 0:
        route = "TABLE_EXISTS_NOT_CONVERTED_TO_FINANCIAL"
        next_step = "Run targeted financial converter on existing restored table evidence; do not re-fetch PDF first."
        severity = "WARN"
    elif quarantine_rows > 0 and financial_rows == 0:
        route = "QUARANTINE_RESCUE_REQUIRED"
        next_step = "Inspect quarantine reason; rescue only rows passing ReportDate ±3, SSOT alias, numeric sanity, and table context."
        severity = "WARN"
    else:
        route = "TARGETED_TABLE_RESTORE_REQUIRED"
        next_step = "Run targeted table restore for this file only; include first page tables and all PDF tables; then validate."
        severity = "WARN"

    return {
        "Status Lights": def_lights(severity),
        "Filename": filename,
        "Ticker": ticker,
        "Broker": t.get("Broker", ""),
        "Analyst": t.get("Analyst", ""),
        "Report Date": t.get("Report Date", ""),
        "YFinance Ticker": t.get("YFinance Ticker", ""),
        "Bloomberg Ticker": t.get("Bloomberg Ticker", ""),
        "Name": t.get("Name", ""),
        "Current Status": status,
        "Confidence": confidence,
        "Evidence Sources": len(ev),
        "Table Evidence Rows": table_rows,
        "Financial Evidence Rows": financial_rows,
        "Quarantine Evidence Rows": quarantine_rows,
        "Repair Route": route,
        "Recommended Next Step": next_step,
        "Severity": severity,
    }


def def_table_html(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(c))}</th>" for c in fields)
    body = []
    for r in rows:
        cells = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            cls = "left" if any(x in c.lower() for x in ["filename", "source", "reason", "step", "route", "status"]) else "center"
            cells.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;padding:20px 32px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:26px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 32px 32px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;white-space:normal}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:900px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"

    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN FinancialData Repair Router v06151</title><style>{css}</style></head>
<body><header><h1>VRN · FinancialData Repair Router + Evidence Reuse Audit v0.6.15.1</h1>
<div class="sub">panoramic evidence reuse · targeted repair route · no PDF re-fetch · no canonical mutation</div></header>
{card_html}<main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("usage: py <run_root> <run_dir> <input_dir>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    input_dir = Path(sys.argv[3])
    run_dir.mkdir(parents=True, exist_ok=True)

    source_matrix = def_find_latest(run_root, [
        "VRN_FINANCIALDATA_CONFIDENCE_CALIBRATOR_V06150_*/vrn_v06150_financialdata_calibrated_matrix.csv"
    ])
    if not source_matrix:
        raise RuntimeError("Cannot find v06150 calibrated matrix.")

    matrix = def_read_csv(source_matrix)
    target_rows = [r for r in matrix if def_is_target_status(r.get("Validation Status", ""))]
    optional_rows = [r for r in matrix if def_is_optional_status(r.get("Validation Status", ""))]

    evidence_rows, evidence_index = def_scan_csv_sources(run_root, target_rows)
    route_rows = [def_route_target(r, evidence_index) for r in target_rows]
    optional_route_rows = [def_route_target(r, evidence_index) for r in optional_rows]

    reuse_rows = [r for r in route_rows if r["Repair Route"] == "REUSE_EXISTING_FINANCIAL_AND_TABLE_EVIDENCE"]
    convert_rows = [r for r in route_rows if r["Repair Route"] == "TABLE_EXISTS_NOT_CONVERTED_TO_FINANCIAL"]
    quarantine_rows = [r for r in route_rows if r["Repair Route"] == "QUARANTINE_RESCUE_REQUIRED"]
    restore_rows = [r for r in route_rows if r["Repair Route"] == "TARGETED_TABLE_RESTORE_REQUIRED"]

    overview = [
        {"Status Lights": def_lights("OK"), "Gate": "SOURCE_MATRIX", "Value": str(source_matrix), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "TARGET_REPAIR_OR_PARTIAL_FILES", "Value": len(target_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "OPTIONAL_FILES", "Value": len(optional_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "EVIDENCE_ROWS_FOUND", "Value": len(evidence_rows), "Severity": "OK"},
        {"Status Lights": def_lights("WARN"), "Gate": "REUSE_EXISTING_EVIDENCE", "Value": len(reuse_rows), "Severity": "WARN"},
        {"Status Lights": def_lights("WARN"), "Gate": "TABLE_EXISTS_NOT_FINANCIAL", "Value": len(convert_rows), "Severity": "WARN"},
        {"Status Lights": def_lights("WARN"), "Gate": "QUARANTINE_RESCUE", "Value": len(quarantine_rows), "Severity": "WARN"},
        {"Status Lights": def_lights("WARN"), "Gate": "TARGETED_TABLE_RESTORE", "Value": len(restore_rows), "Severity": "WARN"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_PDF_REFETCH", "Value": "YES", "Severity": "OK"},
    ]

    route_csv = run_dir / "vrn_v06151_financialdata_repair_router.csv"
    evidence_csv = run_dir / "vrn_v06151_evidence_reuse_scan.csv"
    optional_csv = run_dir / "vrn_v06151_optional_no_financial_route.csv"
    html_path = run_dir / "VRN_FinancialData_Repair_Router_v06151.html"
    json_path = run_dir / "vrn_financialdata_repair_router_v06151.json"

    def_write_csv(route_csv, route_rows)
    def_write_csv(evidence_csv, evidence_rows)
    def_write_csv(optional_csv, optional_route_rows)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": True,
        "source_matrix": str(source_matrix),
        "counts": {
            "Targets": len(target_rows),
            "Optional": len(optional_rows),
            "Evidence Rows": len(evidence_rows),
            "Reuse Existing": len(reuse_rows),
            "Convert Existing Table": len(convert_rows),
            "Quarantine Rescue": len(quarantine_rows),
            "Targeted Restore": len(restore_rows),
            "No Canonical Mutation": "YES",
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "repair_router_csv": str(route_csv),
            "evidence_scan_csv": str(evidence_csv),
            "optional_route_csv": str(optional_csv),
        },
        "rules": [
            "Reuse old evidence before any new extraction.",
            "If table rows exist but financial rows do not, run converter first, not full PDF extraction.",
            "If quarantine rows exist, inspect quarantine reasons and rescue only validated rows.",
            "If no evidence exists, targeted table restore is allowed for that file only.",
            "No canonical mutation and no fake fill.",
        ],
    }

    def_write_json(json_path, result)
    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Repair Router", route_rows),
        ("03 Reuse Existing Evidence First", reuse_rows),
        ("04 Existing Table Needs Financial Converter", convert_rows),
        ("05 Quarantine Rescue Required", quarantine_rows),
        ("06 Targeted Table Restore Required", restore_rows),
        ("07 Optional No Financial Repair", optional_route_rows),
        ("08 Evidence Source Scan", evidence_rows[:2000]),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise