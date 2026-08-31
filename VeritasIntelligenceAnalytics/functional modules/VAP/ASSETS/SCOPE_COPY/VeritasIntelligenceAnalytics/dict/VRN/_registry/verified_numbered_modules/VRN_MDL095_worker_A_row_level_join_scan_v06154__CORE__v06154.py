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
def def_main() -> None:
    run_root = Path(sys.argv[1])
    canonical_dir = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    run_dir.mkdir(parents=True, exist_ok=True)

    router_csv = def_find_latest(run_root, [
        "VRN_EVIDENCE_SOURCE_DECONTAMINATION_ROUTER_V06152_*/vrn_v06152_decontaminated_repair_router.csv"
    ])

    overview = []
    joined_rows = []
    issue_rows = []

    if not router_csv:
        overview.append({"Status Lights": def_lights("ERR"), "Gate": "ROUTER_CSV_FOUND", "Value": "NO", "Severity": "ERR"})
    else:
        router = def_read_csv(router_csv)
        reuse = [r for r in router if def_clean_text(r.get("Repair Route")) == "REAL_REUSE_ROW_LEVEL_EVIDENCE"]
        restore = [r for r in router if def_clean_text(r.get("Repair Route")) == "TARGETED_TABLE_RESTORE_REQUIRED"]

        source_files = []
        for root in [run_root, canonical_dir]:
            if root.exists():
                source_files.extend(root.rglob("*.csv"))

        bad_names = ["action_queue", "calibrated_matrix", "repair_router", "overview", "summary", "manifest", "confidence_calibrator", "broker", "yfinance"]
        source_files = [p for p in source_files if p.is_file() and not any(b in p.name.lower() for b in bad_names)]
        source_files = sorted(set(source_files), key=lambda p: p.stat().st_mtime, reverse=True)[:500]

        for base in reuse:
            filename = def_clean_text(base.get("Filename"))
            ticker = def_clean_text(base.get("Ticker"))
            found = 0
            for p in source_files:
                rows = def_read_csv(p)
                if not rows:
                    continue
                for r in rows:
                    if not def_file_match(r, filename, ticker):
                        continue
                    item = def_clean_text(r.get("Data Official En") or r.get("Data Raw") or r.get("Account") or r.get("Item") or "")
                    val = def_clean_text(r.get("Value Numeric") or r.get("Value") or r.get("value") or "")
                    year = def_clean_text(r.get("Year") or r.get("year") or "")
                    cat = def_clean_text(r.get("Category Official En") or r.get("Category") or "")
                    if item or val or cat:
                        found += 1
                        joined_rows.append({
                            "Status Lights": def_lights("OK" if item and val else "WARN"),
                            "Filename": filename,
                            "Ticker": ticker,
                            "Name": base.get("Name", ""),
                            "Report Date": base.get("Report Date", ""),
                            "Category": cat,
                            "Year": year,
                            "Financial Item": item,
                            "Value": val,
                            "Source File": str(p),
                            "Validation Status": "ROW_LEVEL_EVIDENCE_FOUND" if item and val else "ROW_LEVEL_EVIDENCE_PARTIAL",
                            "Severity": "OK" if item and val else "WARN",
                        })
                    if found >= 500:
                        break
                if found >= 500:
                    break

            if found == 0:
                issue_rows.append({
                    "Status Lights": def_lights("WARN"),
                    "Filename": filename,
                    "Ticker": ticker,
                    "Issue": "NO_ROW_LEVEL_EVIDENCE_JOINED",
                    "Recommended Next Step": "Move to targeted restore or inspect source matching keys.",
                    "Severity": "WARN",
                })

        overview.extend([
            {"Status Lights": def_lights("OK"), "Gate": "SOURCE_ROUTER", "Value": str(router_csv), "Severity": "OK"},
            {"Status Lights": def_lights("OK"), "Gate": "REUSE_FILES", "Value": len(reuse), "Severity": "OK"},
            {"Status Lights": def_lights("WARN"), "Gate": "TARGETED_RESTORE_FILES_PASSTHROUGH", "Value": len(restore), "Severity": "WARN"},
            {"Status Lights": def_lights("OK"), "Gate": "SOURCE_FILES_SCANNED", "Value": len(source_files), "Severity": "OK"},
            {"Status Lights": def_lights("OK"), "Gate": "JOINED_ROWS", "Value": len(joined_rows), "Severity": "OK"},
            {"Status Lights": def_lights("WARN" if issue_rows else "OK"), "Gate": "JOIN_ISSUES", "Value": len(issue_rows), "Severity": "WARN" if issue_rows else "OK"},
            {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        ])

    out_csv = run_dir / "flow_A_row_level_join_scan_rows.csv"
    issue_csv = run_dir / "flow_A_row_level_join_issues.csv"
    html_path = run_dir / "Flow_A_Row_Level_Join_Scan_v06154.html"
    json_path = run_dir / "flow_A_row_level_join_scan_v06154.json"

    def_write_csv(out_csv, joined_rows)
    def_write_csv(issue_csv, issue_rows)

    result = {
        "flow": "A_ROW_LEVEL_JOIN_SCAN",
        "generated_at": def_now(),
        "system_pass": True,
        "counts": {
            "Joined Rows": len(joined_rows),
            "Issues": len(issue_rows),
            "No Canonical Mutation": "YES",
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "joined_csv": str(out_csv),
            "issue_csv": str(issue_csv),
        },
    }

    def_write_json(json_path, result)
    def_write_html(
        html_path,
        "Flow A · Row-Level Evidence Join Scan v0.6.15.4",
        "reuse existing row-level evidence only · no canonical mutation",
        result["counts"],
        [("01 Overview", overview), ("02 Joined Rows", joined_rows[:3000]), ("03 Issues", issue_rows)]
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise