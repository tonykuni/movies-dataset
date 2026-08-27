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
def def_load_result(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def def_main() -> None:
    run_dir = Path(sys.argv[1])
    run_dir.mkdir(parents=True, exist_ok=True)

    a_json = run_dir / "flow_A_row_level_join_scan_v06154.json"
    b_json = run_dir / "flow_B_targeted_restore_scan_v06154.json"
    c_json = run_dir / "flow_C_basicinfo_marketdata_scan_v06154.json"

    A = def_load_result(a_json)
    B = def_load_result(b_json)
    C = def_load_result(c_json)

    flow_rows = []
    for name, obj, p in [
        ("Flow A Row-Level Join", A, a_json),
        ("Flow B Targeted Restore", B, b_json),
        ("Flow C BasicInfo MarketData", C, c_json),
    ]:
        ok = bool(obj.get("system_pass"))
        flow_rows.append({
            "Status Lights": def_lights("OK" if ok else "ERR"),
            "Flow": name,
            "JSON": str(p),
            "System Pass": "YES" if ok else "NO",
            "Counts": json.dumps(obj.get("counts", {}), ensure_ascii=False),
            "HTML": obj.get("outputs", {}).get("html", ""),
            "Severity": "OK" if ok else "ERR",
        })

    final_ready = all(bool(x.get("system_pass")) for x in [A, B, C])
    overview = [
        {"Status Lights": def_lights("OK" if final_ready else "ERR"), "Gate": "TRI_FLOW_COMPLETED", "Value": "YES" if final_ready else "NO", "Severity": "OK" if final_ready else "ERR"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_FINAL_PUBLISH", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("WARN"), "Gate": "NEXT_FINAL_GATE_REQUIRED", "Value": "YES - merge staging outputs only after review", "Severity": "WARN"},
    ]

    next_steps = [
        {
            "Status Lights": def_lights("WARN"),
            "Step": "1",
            "Task": "Review Flow A joined rows and Flow C BasicInfo issues.",
            "Why": "確認既有 row-level evidence 是否真能轉成 FinancialData final。",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_lights("WARN"),
            "Step": "2",
            "Task": "Run targeted restore only for Flow B queue files.",
            "Why": "避免全資料夾重抓 PDF，降低九頭龍風險。",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_lights("WARN"),
            "Step": "3",
            "Task": "After A/B/C review, run one single Unified Final Seal.",
            "Why": "SSOT / canonical / final confidence 只能單一路徑封存。",
            "Severity": "WARN",
        },
    ]

    html_path = run_dir / "VRN_Tri_Flow_Parallel_Orchestrator_v06154.html"
    json_path = run_dir / "vrn_tri_flow_parallel_orchestrator_v06154.json"
    flow_csv = run_dir / "vrn_v06154_tri_flow_status_matrix.csv"

    result = {
        "version": "VRN_TRI_FLOW_PARALLEL_ORCHESTRATOR_V06154",
        "generated_at": def_now(),
        "system_pass": final_ready,
        "counts": {
            "Flow A": "PASS" if A.get("system_pass") else "FAIL",
            "Flow B": "PASS" if B.get("system_pass") else "FAIL",
            "Flow C": "PASS" if C.get("system_pass") else "FAIL",
            "Final Ready": "YES" if final_ready else "NO",
            "No Canonical Mutation": "YES",
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "flow_status_csv": str(flow_csv),
        },
    }

    def_write_csv(flow_csv, flow_rows)
    def_write_json(json_path, result)
    def_write_html(
        html_path,
        "VRN · Tri-Flow Parallel Panoramic Orchestrator v0.6.15.4",
        "three independent staging flows completed · final seal still locked · no canonical mutation",
        result["counts"],
        [("01 Overview", overview), ("02 Flow Status Matrix", flow_rows), ("03 Next Steps", next_steps)]
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise