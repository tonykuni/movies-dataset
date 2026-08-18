# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import re
import sys
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_FLOW_A_TABLE_RECONSTRUCTION_PLANNER_V061549"


def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_flat_text(x: Any) -> str:
    return re.sub(r"\s+", " ", def_clean_text(x)).strip()


def def_norm_key(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。]+", "", str(x or "").lower())


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "PLAN"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "QUEUE", "EXCLUDED"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_find_latest_dir(root: Path, prefix: str) -> Path | None:
    hits = [p for p in root.glob(prefix + "_*") if p.is_dir()]
    hits = sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


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


def def_get(row: dict, aliases: list[str]) -> str:
    mp = {def_norm_key(k): k for k in row.keys()}
    for a in aliases:
        nk = def_norm_key(a)
        if nk in mp:
            return def_clean_text(row.get(mp[nk]))
    for k in row.keys():
        nk = def_norm_key(k)
        for a in aliases:
            if def_norm_key(a) in nk:
                return def_clean_text(row.get(k))
    return ""


def def_int(x: Any, default: int = 0) -> int:
    try:
        return int(float(str(x).replace(",", "").replace("%", "").strip()))
    except Exception:
        return default


def def_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(str(x).replace(",", "").replace("%", "").strip())
    except Exception:
        return default


def def_classify_statement_type(preview: str, category: str) -> str:
    blob = (preview + " " + category).lower()

    if any(x.lower() in blob for x in ["balance sheet", "資產負債表", "資產總計", "流動資產", "cash & equivalents"]):
        return "BALANCE_SHEET"
    if any(x.lower() in blob for x in ["income statement", "profit & loss", "損益表", "營業收入", "營業毛利", "營業利益"]):
        return "INCOME_STATEMENT"
    if any(x.lower() in blob for x in ["cashflow", "cash flow", "現金流量表", "營業活動之淨現金流", "capex"]):
        return "CASH_FLOW"
    if any(x.lower() in blob for x in ["ratio analysis", "dupont", "roe", "roa", "毛利率", "營益率", "淨利率"]):
        return "RATIO_ANALYSIS"
    if any(x.lower() in blob for x in ["eps", "每股盈餘", "各季eps"]):
        return "PER_SHARE_ANALYSIS"
    if any(x.lower() in blob for x in ["eva", "valuation", "per", "pbr", "target price", "目標價", "本益比", "股價淨值比"]):
        return "VALUATION_EXCLUDED"
    return "UNCLASSIFIED_FINANCIAL_TABLE"


def def_route_table(row: dict, min_score: int, min_rows: int, min_cols: int) -> dict:
    r = dict(row)

    filename = def_get(row, ["filename"])
    preview = def_get(row, ["preview"])
    category = def_get(row, ["categories"])
    strategy = def_get(row, ["strategy"])
    rows = def_int(def_get(row, ["rows"]))
    cols = def_int(def_get(row, ["cols"]))
    qscore = def_int(def_get(row, ["quality score"]))
    hscore = def_int(def_get(row, ["header score"]))
    source_score = def_int(def_get(row, ["source score"]))
    density = def_float(def_get(row, ["density"]))

    statement_type = def_classify_statement_type(preview, category)

    route = "RECON_REVIEW_QUEUE"
    reason = []

    if statement_type == "VALUATION_EXCLUDED":
        route = "RECON_EXCLUDE_VALUATION_TABLE"
        reason.append("valuation table is excluded from FinancialData canonical transform")

    elif rows <= 2:
        route = "RECON_SKIP_HEADER_ONLY"
        reason.append("table has too few body rows; likely header-only or section marker")

    elif qscore >= min_score and rows >= min_rows and cols >= min_cols and hscore >= 1:
        route = "RECON_READY_CANDIDATE"
        reason.append("quality/shape/header passed")

    elif "華南" in filename and strategy == "text" and cols >= 15:
        route = "RECON_HUANAN_SPLIT_COLUMN_REPAIR_CANDIDATE"
        reason.append("HuaNan wide split-column table requires column merge repair")

    elif hscore == 0:
        route = "RECON_HEADER_LOSS_REVIEW"
        reason.append("missing header evidence")

    elif qscore < min_score:
        route = "RECON_LOW_QUALITY_REVIEW"
        reason.append("quality score below threshold")

    else:
        route = "RECON_REVIEW_QUEUE"
        reason.append("requires manual/next dry-run validation")

    sev = "OK" if route in ["RECON_READY_CANDIDATE", "RECON_EXCLUDE_VALUATION_TABLE", "RECON_SKIP_HEADER_ONLY"] else "WARN"

    r["Status Lights"] = def_light(sev)
    r["statement type"] = statement_type
    r["reconstruction route"] = route
    r["reconstruction reason"] = " | ".join(reason)
    r["reconstruction action"] = "PLAN_ONLY_VALIDATE_ROWS_COLS_HEADERS_BODY_SOURCE_NOTE"
    r["restore execution"] = "NO"
    r["db write"] = "NO"
    r["canonical mutation"] = "NO"
    r["Severity"] = sev
    return r


def def_table_html(title: str, rows: list[dict], limit: int | None = None) -> str:
    if limit is not None:
        rows = rows[:limit]
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
        tds = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            cls = "left" if any(x in c.lower() for x in ["filename", "preview", "reason", "route", "statement", "hits"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    note = "" if limit is None else f"<p class='note'>Showing first {limit:,} rows. Full CSV exported.</p>"
    return f"<section class='card'><h2>{html.escape(title)}</h2>{note}<div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;padding:20px 32px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:26px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 32px 32px}.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;margin:18px 0;padding:18px}
.note{color:#9fb3c8}.table-wrap{overflow:auto;max-height:78vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;white-space:normal}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1180px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    ) + "</div>"
    body = "".join(def_table_html(t, r, lim) for t, r, lim in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>Flow A Table Reconstruction Planner</title><style>{css}</style></head>
<body><header><h1>VRN · Flow A Table Reconstruction Planner v0.6.15.4.9</h1>
<div class="sub">table candidates · reconstruction route · no restore · no DB write</div></header>{cards}<main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    min_score = int(sys.argv[3])
    min_rows = int(sys.argv[4])
    min_cols = int(sys.argv[5])

    source_run = def_find_latest_dir(run_root, "VRN_TARGETED_TABLE_EXTRACTION_DRYRUN_V061548")
    if not source_run:
        raise RuntimeError("Cannot find latest VRN_TARGETED_TABLE_EXTRACTION_DRYRUN_V061548 run.")

    rows = [r for r in def_read_csv(source_run / "table_candidate_matrix_v061548.csv") if "empty_marker" not in r]
    classified = [def_route_table(r, min_score, min_rows, min_cols) for r in rows]

    ready = [r for r in classified if def_get(r, ["reconstruction route"]) == "RECON_READY_CANDIDATE"]
    huanan = [r for r in classified if def_get(r, ["reconstruction route"]) == "RECON_HUANAN_SPLIT_COLUMN_REPAIR_CANDIDATE"]
    excluded = [r for r in classified if def_get(r, ["reconstruction route"]) in ["RECON_EXCLUDE_VALUATION_TABLE", "RECON_SKIP_HEADER_ONLY"]]
    review = [r for r in classified if def_get(r, ["Severity"]).upper() != "OK"]

    route_summary = []
    for k, v in sorted(Counter(def_get(r, ["reconstruction route"]) for r in classified).items(), key=lambda x: (-x[1], x[0])):
        sev = "OK" if k in ["RECON_READY_CANDIDATE", "RECON_EXCLUDE_VALUATION_TABLE", "RECON_SKIP_HEADER_ONLY"] else "WARN"
        route_summary.append({"Status Lights": def_light(sev), "Route": k, "Rows": v, "Severity": sev})

    stmt_summary = []
    for k, v in sorted(Counter(def_get(r, ["statement type"]) for r in classified).items(), key=lambda x: (-x[1], x[0])):
        stmt_summary.append({"Status Lights": def_light("OK"), "Statement Type": k, "Rows": v, "Severity": "OK"})

    outputs = {
        "html": str(run_dir / "FlowA_Table_Reconstruction_Planner_v061549.html"),
        "json": str(run_dir / "flow_a_table_reconstruction_planner_v061549.json"),
        "classified_csv": str(run_dir / "flow_a_classified_table_candidates_v061549.csv"),
        "ready_csv": str(run_dir / "flow_a_recon_ready_candidates_v061549.csv"),
        "huanan_csv": str(run_dir / "flow_a_huanan_split_column_repair_candidates_v061549.csv"),
        "excluded_csv": str(run_dir / "flow_a_excluded_or_header_only_v061549.csv"),
        "review_csv": str(run_dir / "flow_a_reconstruction_review_queue_v061549.csv"),
        "route_summary_csv": str(run_dir / "flow_a_route_summary_v061549.csv"),
        "statement_summary_csv": str(run_dir / "flow_a_statement_summary_v061549.csv"),
    }

    def_write_csv(Path(outputs["classified_csv"]), classified)
    def_write_csv(Path(outputs["ready_csv"]), ready)
    def_write_csv(Path(outputs["huanan_csv"]), huanan)
    def_write_csv(Path(outputs["excluded_csv"]), excluded)
    def_write_csv(Path(outputs["review_csv"]), review)
    def_write_csv(Path(outputs["route_summary_csv"]), route_summary)
    def_write_csv(Path(outputs["statement_summary_csv"]), stmt_summary)

    counts = {
        "Flow A": "PASS",
        "Input Tables": len(rows),
        "Recon Ready": len(ready),
        "HuaNan Repair": len(huanan),
        "Excluded/Header Only": len(excluded),
        "Review Queue": len(review),
        "Restore Execution": "NO",
        "DB Write": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK"), "Gate": "FLOW_A_PASS", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SOURCE_RUN", "Value": str(source_run), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_RESTORE_EXECUTION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    def_write_html(Path(outputs["html"]), counts, [
        ("01 Overview", overview, None),
        ("02 Reconstruction Route Summary", route_summary, None),
        ("03 Statement Type Summary", stmt_summary, None),
        ("04 Reconstruction Ready Candidates", ready, 1000),
        ("05 HuaNan Split Column Repair Candidates", huanan, 1000),
        ("06 Reconstruction Review Queue", review, 1000),
        ("07 Excluded / Header Only", excluded, 1000),
    ])

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": True,
        "source_run": str(source_run),
        "counts": counts,
        "outputs": outputs,
    }
    def_write_json(Path(outputs["json"]), result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise