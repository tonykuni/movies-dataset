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
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_EVIDENCE_SOURCE_DECONTAMINATION_ROUTER_V06152"


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


def def_is_summary_pollution(path: Path) -> bool:
    name = path.name.lower()
    bad = [
        "action_queue",
        "calibrated_matrix",
        "repair_router",
        "overview",
        "summary",
        "manifest",
        "coverage_calibration",
        "confidence_calibrator",
        "one_row",
        "company_report_matrix",
        "final_seal",
        "broker",
        "yfinance",
        "basicinfo_financialdata_integrated",
    ]
    return any(x in name for x in bad)


def def_source_kind(path: Path, cols: set[str]) -> str:
    name = path.name.lower()
    col = " ".join(cols).lower()

    if def_is_summary_pollution(path):
        return "SUMMARY_POLLUTION_EXCLUDED"

    if "pdf_table_inventory" in name or ("pdf page" in col and "pdf table index" in col):
        return "REAL_TABLE_INVENTORY"

    if "restored_financial_candidate" in name or (
        "restore rule" in col and "restore confidence" in col
    ):
        return "REAL_RESTORED_TABLE_ROWS"

    if "financial_candidate" in name or (
        "category official" in col and "data official" in col and "value numeric" in col
    ):
        return "REAL_FINANCIAL_CANDIDATE_ROWS"

    if "clean_validation" in name or (
        "historical validation" in col and "division validation" in col and "financial rows validated" not in col
    ):
        return "REAL_VALIDATED_FINANCIAL_ROWS"

    if "review" in name or "quarantine" in name:
        return "REAL_REVIEW_QUARANTINE_ROWS"

    if "vrn_financial_active" in name or "canonical" in str(path).lower():
        return "CANONICAL_FINANCIAL_ACTIVE"

    return "OTHER_EXCLUDED"


def def_row_matches_target(row: dict, filename: str, ticker: str) -> bool:
    fn = def_clean_text(row.get("Filename") or row.get("filename") or row.get("File") or row.get("file") or "")
    tk = def_clean_text(row.get("Ticker") or row.get("ticker") or row.get("stock_id") or row.get("Stock ID") or "")

    if filename and fn:
        if def_norm_key(Path(filename).name) == def_norm_key(Path(fn).name):
            return True

    if ticker and tk and ticker == tk:
        return True

    return False


def def_scan_sources(run_root: Path, canonical_dir: Path, targets: list[dict]) -> tuple[list[dict], dict]:
    files = []

    for root in [run_root, canonical_dir]:
        if root.exists():
            files.extend(root.rglob("*.csv"))

    files = sorted(set([p for p in files if p.is_file()]), key=lambda p: p.stat().st_mtime, reverse=True)

    evidence_rows = []
    index = {}

    for p in files[:500]:
        rows = def_read_csv(p)
        if not rows:
            continue

        cols = set(rows[0].keys())
        kind = def_source_kind(p, cols)

        for t in targets:
            filename = def_clean_text(t.get("Filename", ""))
            ticker = def_clean_text(t.get("Ticker", ""))
            key = f"{ticker}|{def_norm_key(filename)}"

            matched = 0
            years = set()
            cats = set()
            data_items = set()

            for r in rows:
                if not def_row_matches_target(r, filename, ticker):
                    continue

                matched += 1

                for k in ["Year", "year", "Financial Year", "financial_year", "Financial Years"]:
                    y = def_clean_text(r.get(k, ""))
                    for yy in re.findall(r"20\d{2}", y):
                        years.add(yy)

                for k in ["Category Official En", "Category Official EN", "Category", "Financial Categories"]:
                    c = def_clean_text(r.get(k, ""))
                    for cc in re.split(r"\|", c):
                        cc = def_clean_text(cc)
                        if cc:
                            cats.add(cc)

                for k in ["Data Official En", "Data Official EN", "Data Raw", "Account", "Item", "data_official_en"]:
                    d = def_clean_text(r.get(k, ""))
                    if d:
                        data_items.add(d)

            if matched:
                rec = {
                    "Filename": filename,
                    "Ticker": ticker,
                    "Evidence Kind": kind,
                    "Source File": str(p),
                    "Rows Matched": matched,
                    "Years Found": " | ".join(sorted(years)),
                    "Categories Found": " | ".join(sorted(cats)),
                    "Data Items Sample": " | ".join(sorted(list(data_items))[:20]),
                    "Source MTime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
                    "Included": "YES" if kind.startswith("REAL_") or kind.startswith("CANONICAL") else "NO",
                }
                evidence_rows.append(rec)
                index.setdefault(key, []).append(rec)

    return evidence_rows, index


def def_route_target(t: dict, evidence_index: dict) -> dict:
    filename = def_clean_text(t.get("Filename", ""))
    ticker = def_clean_text(t.get("Ticker", ""))
    key = f"{ticker}|{def_norm_key(filename)}"
    ev_all = evidence_index.get(key, [])
    ev = [e for e in ev_all if e.get("Included") == "YES"]

    summary_pollution = sum(int(e.get("Rows Matched", 0) or 0) for e in ev_all if e.get("Included") != "YES")
    table_rows = sum(int(e.get("Rows Matched", 0) or 0) for e in ev if e.get("Evidence Kind") in ["REAL_TABLE_INVENTORY", "REAL_RESTORED_TABLE_ROWS"])
    financial_rows = sum(int(e.get("Rows Matched", 0) or 0) for e in ev if e.get("Evidence Kind") in ["REAL_FINANCIAL_CANDIDATE_ROWS", "REAL_VALIDATED_FINANCIAL_ROWS", "CANONICAL_FINANCIAL_ACTIVE"])
    quarantine_rows = sum(int(e.get("Rows Matched", 0) or 0) for e in ev if e.get("Evidence Kind") == "REAL_REVIEW_QUARANTINE_ROWS")

    kinds = sorted(set(e.get("Evidence Kind", "") for e in ev))
    status = def_clean_text(t.get("Validation Status", ""))

    if "OPTIONAL_NO_DISCLOSED_FINANCIAL_TABLE" in status.upper():
        route = "OPTIONAL_NO_FINANCIAL_REPAIR"
        next_step = "No financial repair needed unless memo/visit report explicitly discloses table."
        severity = "WARN"
    elif financial_rows > 0 and table_rows > 0:
        route = "REAL_REUSE_ROW_LEVEL_EVIDENCE"
        next_step = "Run join repair using only included row-level evidence; fix source selector/year window/SSOT alias."
        severity = "WARN"
    elif table_rows > 0 and financial_rows == 0:
        route = "TABLE_EXISTS_CONVERTER_REQUIRED"
        next_step = "Run table-to-financial converter using restored/table inventory rows; no PDF re-fetch."
        severity = "WARN"
    elif quarantine_rows > 0 and table_rows == 0 and financial_rows == 0:
        route = "QUARANTINE_RESCUE_REQUIRED"
        next_step = "Inspect quarantine context; rescue only rows passing numeric/year/SSOT/table-context checks."
        severity = "WARN"
    elif summary_pollution > 0 and not ev:
        route = "ONLY_SUMMARY_EVIDENCE_CONTAMINATED"
        next_step = "Previous router was polluted by summary CSV; run targeted restore or locate raw row-level source."
        severity = "WARN"
    else:
        route = "TARGETED_TABLE_RESTORE_REQUIRED"
        next_step = "No reliable row-level evidence found; targeted restore this file only."
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
        "Confidence": t.get("Confidence", ""),
        "Included Evidence Sources": len(ev),
        "Excluded Summary Pollution Rows": summary_pollution,
        "Real Table Rows": table_rows,
        "Real Financial Rows": financial_rows,
        "Real Quarantine Rows": quarantine_rows,
        "Evidence Kinds": " | ".join(kinds),
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
            cls = "left" if any(x in c.lower() for x in ["filename", "source", "route", "step", "status", "items", "kinds"]) else "center"
            cells.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;padding:20px 32px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:26px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 32px 32px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;white-space:normal}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:980px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"

    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Evidence Source Decontamination Router v06152</title><style>{css}</style></head>
<body><header><h1>VRN · Evidence Source Decontamination Router v0.6.15.2</h1>
<div class="sub">summary pollution removed · row-level evidence only · no PDF re-fetch · no canonical mutation</div></header>
{card_html}<main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("usage: py <run_root> <canonical_dir> <run_dir>")

    run_root = Path(sys.argv[1])
    canonical_dir = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    run_dir.mkdir(parents=True, exist_ok=True)

    source_matrix = def_find_latest(run_root, [
        "VRN_FINANCIALDATA_CONFIDENCE_CALIBRATOR_V06150_*/vrn_v06150_financialdata_calibrated_matrix.csv"
    ])
    if not source_matrix:
        raise RuntimeError("Cannot find v06150 calibrated matrix.")

    matrix = def_read_csv(source_matrix)
    target_rows = [r for r in matrix if def_is_target_status(r.get("Validation Status", ""))]
    optional_rows = [r for r in matrix if def_is_optional_status(r.get("Validation Status", ""))]
    all_rows = target_rows + optional_rows

    evidence_rows, evidence_index = def_scan_sources(run_root, canonical_dir, all_rows)
    route_rows = [def_route_target(r, evidence_index) for r in target_rows]
    optional_route_rows = [def_route_target(r, evidence_index) for r in optional_rows]

    reuse = [r for r in route_rows if r["Repair Route"] == "REAL_REUSE_ROW_LEVEL_EVIDENCE"]
    convert = [r for r in route_rows if r["Repair Route"] == "TABLE_EXISTS_CONVERTER_REQUIRED"]
    quarantine = [r for r in route_rows if r["Repair Route"] == "QUARANTINE_RESCUE_REQUIRED"]
    contaminated = [r for r in route_rows if r["Repair Route"] == "ONLY_SUMMARY_EVIDENCE_CONTAMINATED"]
    restore = [r for r in route_rows if r["Repair Route"] == "TARGETED_TABLE_RESTORE_REQUIRED"]

    overview = [
        {"Status Lights": def_lights("OK"), "Gate": "SOURCE_MATRIX", "Value": str(source_matrix), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "TARGET_FILES", "Value": len(target_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "OPTIONAL_FILES", "Value": len(optional_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "EVIDENCE_ROWS_SCANNED", "Value": len(evidence_rows), "Severity": "OK"},
        {"Status Lights": def_lights("WARN"), "Gate": "REAL_REUSE_ROW_LEVEL_EVIDENCE", "Value": len(reuse), "Severity": "WARN"},
        {"Status Lights": def_lights("WARN"), "Gate": "TABLE_EXISTS_CONVERTER_REQUIRED", "Value": len(convert), "Severity": "WARN"},
        {"Status Lights": def_lights("WARN"), "Gate": "QUARANTINE_RESCUE_REQUIRED", "Value": len(quarantine), "Severity": "WARN"},
        {"Status Lights": def_lights("WARN"), "Gate": "ONLY_SUMMARY_EVIDENCE_CONTAMINATED", "Value": len(contaminated), "Severity": "WARN"},
        {"Status Lights": def_lights("WARN"), "Gate": "TARGETED_TABLE_RESTORE_REQUIRED", "Value": len(restore), "Severity": "WARN"},
        {"Status Lights": def_lights("OK"), "Gate": "SUMMARY_POLLUTION_EXCLUDED", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    route_csv = run_dir / "vrn_v06152_decontaminated_repair_router.csv"
    evidence_csv = run_dir / "vrn_v06152_decontaminated_evidence_scan.csv"
    html_path = run_dir / "VRN_Evidence_Source_Decontamination_Router_v06152.html"
    json_path = run_dir / "vrn_evidence_source_decontamination_router_v06152.json"

    def_write_csv(route_csv, route_rows)
    def_write_csv(evidence_csv, evidence_rows)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": True,
        "source_matrix": str(source_matrix),
        "counts": {
            "Targets": len(target_rows),
            "Optional": len(optional_rows),
            "Evidence Rows": len(evidence_rows),
            "Real Reuse": len(reuse),
            "Convert Existing Table": len(convert),
            "Quarantine Rescue": len(quarantine),
            "Summary Contaminated": len(contaminated),
            "Targeted Restore": len(restore),
            "No Canonical Mutation": "YES",
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "router_csv": str(route_csv),
            "evidence_csv": str(evidence_csv),
        },
        "rules": [
            "Action queue / calibrated matrix / router / summary CSV are excluded from row-level evidence.",
            "Only real restored table rows, financial candidate rows, clean validation rows, quarantine rows, and canonical financial rows count.",
            "No PDF re-fetch at this stage.",
            "No canonical mutation and no fake fill.",
        ],
    }

    def_write_json(json_path, result)
    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Decontaminated Repair Router", route_rows),
        ("03 Real Reuse Row-Level Evidence", reuse),
        ("04 Table Exists Converter Required", convert),
        ("05 Quarantine Rescue Required", quarantine),
        ("06 Summary Evidence Contaminated", contaminated),
        ("07 Targeted Table Restore Required", restore),
        ("08 Optional No Financial Repair", optional_route_rows),
        ("09 Decontaminated Evidence Scan", evidence_rows[:3000]),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise