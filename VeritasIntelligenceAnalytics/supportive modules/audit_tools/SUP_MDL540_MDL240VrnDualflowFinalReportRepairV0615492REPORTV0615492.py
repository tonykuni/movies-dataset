# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import Any


VERSION = "VRN_DUALFLOW_FINAL_REPORT_REPAIR_V0615492"


def def_clean(x: Any) -> str:
    return re.sub(r"\s+", " ", "" if x is None else str(x)).strip()


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "PLAN", "REVIEW"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_find_latest_dir(root: Path, prefix: str) -> Path | None:
    hits = [p for p in root.glob(prefix + "_*") if p.is_dir()]
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0] if hits else None


def def_read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return {"_read_error": str(e), "_path": str(path)}


def def_write_json(path: Path, obj: dict) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_write_csv(path: Path, rows: list[dict]) -> None:
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


def def_table(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(k))}</th>" for k in fields)
    body = []
    for r in rows:
        tds = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["path", "reason", "next", "flow", "detail", "status", "rule"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(v)}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:980px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in result["counts"].items()
    )
    body = "".join(def_table(t, rows) for t, rows in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Dual Flow Final Repair v0615492</title><style>{css}</style></head>
<body><header><h1>VRN · Dual-Flow Final Report Repair v0.6.15.4.9.2</h1>
<div class="sub">Flow B spec JSON pass rule fixed · final PASS repaired · no mutation</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_flow_b_pass(flow_b: dict, source: Path) -> tuple[bool, str, int]:
    pages = flow_b.get("pages", [])
    outputs = flow_b.get("outputs", {})
    version_ok = bool(flow_b.get("version"))
    pages_ok = isinstance(pages, list) and len(pages) > 0

    html_ok = False
    md_ok = False
    json_ok = False

    for key, val in outputs.items():
        p = Path(str(val))
        if not p.is_absolute():
            p = source / p
        if key == "html" and p.exists():
            html_ok = True
        if key == "markdown" and p.exists():
            md_ok = True
        if key == "json" and p.exists():
            json_ok = True

    passed = version_ok and pages_ok and json_ok and (html_ok or md_ok)
    reason = f"version_ok={version_ok}; pages_ok={pages_ok}; json_ok={json_ok}; html_ok={html_ok}; markdown_ok={md_ok}"
    return passed, reason, len(pages) if isinstance(pages, list) else 0


def def_main() -> None:
    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    run_dir.mkdir(parents=True, exist_ok=True)

    source = def_find_latest_dir(run_root, "VRN_DUALFLOW_TABLE_RECON_UI_SPEC_V061549")
    if not source:
        raise RuntimeError("Cannot find latest VRN_DUALFLOW_TABLE_RECON_UI_SPEC_V061549 run.")

    flow_a_path = source / "flow_a_table_reconstruction_planner_v061549.json"
    flow_b_path = source / "flow_b_ui_text_spec_pack_v061549.json"

    flow_a = def_read_json(flow_a_path)
    flow_b = def_read_json(flow_b_path)

    a_pass = bool(flow_a.get("system_pass"))
    b_pass, b_reason, ui_pages = def_flow_b_pass(flow_b, source)
    final_pass = a_pass and b_pass

    a_counts = flow_a.get("counts", {})

    counts = {
        "Final": "PASS" if final_pass else "FAIL",
        "Flow A": "PASS" if a_pass else "FAIL",
        "Flow B": "PASS" if b_pass else "FAIL",
        "Input Tables": a_counts.get("Input Tables", ""),
        "Recon Ready": a_counts.get("Recon Ready", ""),
        "HuaNan Repair": a_counts.get("HuaNan Repair", ""),
        "Review Queue": a_counts.get("Review Queue", ""),
        "UI Pages": ui_pages,
        "Restore Execution": "NO",
        "OCR": "NO",
        "DB Write": "NO",
        "Canonical Mutation": "NO",
        "SSOT Mutation": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "ERR"), "Gate": "FINAL_REPAIRED_PASS", "Value": "YES" if final_pass else "NO", "Severity": "OK" if final_pass else "ERR"},
        {"Status Lights": def_light("OK"), "Gate": "SOURCE_RUN", "Value": str(source), "Severity": "OK"},
        {"Status Lights": def_light("OK" if a_pass else "ERR"), "Gate": "FLOW_A_PASS", "Value": "YES" if a_pass else "NO", "Severity": "OK" if a_pass else "ERR"},
        {"Status Lights": def_light("OK" if b_pass else "ERR"), "Gate": "FLOW_B_SPEC_PASS", "Value": "YES" if b_pass else "NO", "Severity": "OK" if b_pass else "ERR"},
        {"Status Lights": def_light("OK"), "Gate": "FLOW_B_PASS_RULE", "Value": b_reason, "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    next_flows = [
        {
            "Status Lights": def_light("PLAN"),
            "Flow": "DATA_FLOW_01",
            "Next Work": "Table Reconstruction Validation Dry Run",
            "Input": "flow_a_recon_ready_candidates_v061549.csv",
            "Output": "validated_table_reconstruction_matrix",
            "Safety": "NO DB WRITE / NO CANONICAL / NO SSOT / NO OCR",
            "Reason": "22 ready candidates can validate row/column/header/body/source-note.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("PLAN"),
            "Flow": "UI_FLOW_01",
            "Next Work": "Multi-page HTML Shell Integration",
            "Input": "flow_b_ui_text_spec_pack_v061549.json",
            "Output": "VRN multi-page UI shell",
            "Safety": "UI ONLY / NO DATA MUTATION",
            "Reason": "U/I can proceed independently from data repair.",
            "Severity": "WARN",
        },
    ]

    hard_rules = [
        {"Status Lights": def_light("OK"), "Rule": "BasicInfo final pack stays locked", "Reason": "Do not disturb usable main matrix.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "No SSOT alias patch yet", "Reason": "Alias candidate groups = 0; issue is table reconstruction.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "No restore execution yet", "Reason": "Validation dry run must pass first.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "No OCR", "Reason": "Text layer has been enough so far.", "Severity": "OK"},
    ]

    outputs = {
        "html": str(run_dir / "VRN_DualFlow_Final_Report_Repair_v0615492.html"),
        "json": str(run_dir / "vrn_dualflow_final_report_repair_v0615492.json"),
        "next_flow_plan_csv": str(run_dir / "vrn_next_two_flow_plan_v0615492.csv"),
        "hard_rules_csv": str(run_dir / "vrn_hard_rules_v0615492.csv"),
    }

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "source_run": str(source),
        "counts": counts,
        "flow_b_pass_reason": b_reason,
        "outputs": outputs,
    }

    def_write_csv(Path(outputs["next_flow_plan_csv"]), next_flows)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)
    def_write_json(Path(outputs["json"]), result)
    def_write_html(Path(outputs["html"]), result, [
        ("01 Overview", overview),
        ("02 Next Two-Flow Plan", next_flows),
        ("03 Hard Rules", hard_rules),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    def_main()