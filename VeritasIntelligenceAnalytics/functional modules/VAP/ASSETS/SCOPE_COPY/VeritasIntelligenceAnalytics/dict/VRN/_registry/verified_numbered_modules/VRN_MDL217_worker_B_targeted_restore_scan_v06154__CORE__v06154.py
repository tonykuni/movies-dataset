# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


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
    if s in ["OK", "READY", "YES", "PASS", "GREEN"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "PARTIAL", "YELLOW", "OPTIONAL"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_read_csv(path: Path) -> list[dict]:
    if not path or not path.exists():
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_find_latest(root: Path, patterns: list[str]) -> Path | None:
    hits = []
    for pat in patterns:
        hits.extend(root.rglob(pat))
    hits = [p for p in hits if p.is_file()]
    hits = sorted(set(hits), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


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
            cls = "left" if any(x in c.lower() for x in ["file", "source", "path", "reason", "step", "status", "queue", "issue", "route"]) else "center"
            cells.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, title: str, subtitle: str, counts: dict, sections: list[tuple[str, list[dict]]]) -> None:
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
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:980px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    ) + "</div>"
    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>{css}</style></head>
<body><header><h1>{html.escape(title)}</h1><div class="sub">{html.escape(subtitle)}</div></header>{card_html}<main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_file_match(row: dict, filename: str, ticker: str) -> bool:
    fn = def_clean_text(row.get("Filename") or row.get("filename") or row.get("File") or row.get("file") or "")
    tk = def_clean_text(row.get("Ticker") or row.get("ticker") or row.get("stock_id") or row.get("Stock ID") or "")
    if filename and fn and def_norm_key(Path(filename).name) == def_norm_key(Path(fn).name):
        return True
    if ticker and tk and ticker == tk:
        return True
    return False


def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")
def def_probe_pdf_tables(pdf_path: Path) -> dict:
    out = {
        "Probe Available": "NO",
        "Pages": "",
        "Tables Found": "",
        "Probe Error": "",
    }
    try:
        import pdfplumber
        out["Probe Available"] = "YES"
        table_count = 0
        page_count = 0
        with pdfplumber.open(str(pdf_path)) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                try:
                    tables = page.extract_tables() or []
                    table_count += len(tables)
                except Exception:
                    pass
        out["Pages"] = page_count
        out["Tables Found"] = table_count
    except Exception as e:
        out["Probe Error"] = str(e)
    return out


def def_main() -> None:
    run_root = Path(sys.argv[1])
    input_dir = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    enable_pdf_probe = str(sys.argv[4]).lower() in ["true", "1", "yes"]
    run_dir.mkdir(parents=True, exist_ok=True)

    router_csv = def_find_latest(run_root, [
        "VRN_EVIDENCE_SOURCE_DECONTAMINATION_ROUTER_V06152_*/vrn_v06152_decontaminated_repair_router.csv"
    ])

    queue = []
    overview = []

    if not router_csv:
        overview.append({"Status Lights": def_lights("ERR"), "Gate": "ROUTER_CSV_FOUND", "Value": "NO", "Severity": "ERR"})
    else:
        router = def_read_csv(router_csv)
        targets = [r for r in router if def_clean_text(r.get("Repair Route")) == "TARGETED_TABLE_RESTORE_REQUIRED"]

        input_files = {def_norm_key(p.name): p for p in input_dir.glob("*") if p.is_file()}

        for r in targets:
            fn = def_clean_text(r.get("Filename"))
            matched_path = ""
            if def_norm_key(Path(fn).name) in input_files:
                matched_path = str(input_files[def_norm_key(Path(fn).name)])
            else:
                for p in input_files.values():
                    if def_clean_text(r.get("Ticker")) and def_clean_text(r.get("Ticker")) in p.name:
                        matched_path = str(p)
                        break

            probe = {}
            if enable_pdf_probe and matched_path and matched_path.lower().endswith(".pdf"):
                probe = def_probe_pdf_tables(Path(matched_path))
            else:
                probe = {"Probe Available": "SKIP", "Pages": "", "Tables Found": "", "Probe Error": ""}

            sev = "OK" if matched_path else "WARN"
            queue.append({
                "Status Lights": def_lights(sev),
                "Filename": fn,
                "Ticker": r.get("Ticker", ""),
                "Name": r.get("Name", ""),
                "Input Path Found": matched_path,
                "Probe Available": probe.get("Probe Available", ""),
                "Pages": probe.get("Pages", ""),
                "Tables Found": probe.get("Tables Found", ""),
                "Probe Error": probe.get("Probe Error", ""),
                "Recommended Next Step": "Run targeted high-DPI conversion + all-table restore for this file only.",
                "Severity": sev,
            })

        overview.extend([
            {"Status Lights": def_lights("OK"), "Gate": "SOURCE_ROUTER", "Value": str(router_csv), "Severity": "OK"},
            {"Status Lights": def_lights("WARN"), "Gate": "TARGETED_RESTORE_FILES", "Value": len(targets), "Severity": "WARN"},
            {"Status Lights": def_lights("OK"), "Gate": "PDF_PROBE_ENABLED", "Value": "YES" if enable_pdf_probe else "NO", "Severity": "OK"},
            {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        ])

    out_csv = run_dir / "flow_B_targeted_restore_queue.csv"
    html_path = run_dir / "Flow_B_Targeted_Restore_Scan_v06154.html"
    json_path = run_dir / "flow_B_targeted_restore_scan_v06154.json"

    def_write_csv(out_csv, queue)

    result = {
        "flow": "B_TARGETED_RESTORE_SCAN",
        "generated_at": def_now(),
        "system_pass": True,
        "counts": {
            "Targeted Files": len(queue),
            "No Canonical Mutation": "YES",
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "queue_csv": str(out_csv),
        },
    }

    def_write_json(json_path, result)
    def_write_html(
        html_path,
        "Flow B · Targeted Restore Scan v0.6.15.4",
        "targeted restore queue only · optional pdfplumber table probe · no canonical mutation",
        result["counts"],
        [("01 Overview", overview), ("02 Targeted Restore Queue", queue)]
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise