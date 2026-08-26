# -*- coding: utf-8 -*-
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

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


VERSION = "VRN_FINANCIALDATA_TRIFLOW_STAGING_V06153"


def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "GREEN"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "PARTIAL", "QUEUE", "YELLOW"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_read_json(path: Path) -> Any:
    if not path.exists():
        return {}
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            pass
    return {}


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


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


def def_find_latest_json(run_root: Path, pattern: str) -> Path | None:
    hits = list(run_root.glob(pattern))
    hits = [p for p in hits if p.is_file() and p.suffix.lower() == ".json"]
    hits = sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_flatten_json_rows(obj: Any, source_name: str) -> list[dict]:
    rows = []

    def walk(x: Any, path: str):
        if isinstance(x, list):
            if x and all(isinstance(i, dict) for i in x):
                keyset = set()
                for i in x[:20]:
                    keyset.update(str(k).lower() for k in i.keys())
                if any(k in keyset for k in ["filename", "report date", "report_date", "ticker", "financial data", "financial_data", "validation status", "validation_status", "confidence"]):
                    for idx, item in enumerate(x):
                        item2 = dict(item)
                        item2["_json_path"] = path
                        item2["_row_index"] = idx
                        item2["_source_json_role"] = source_name
                        rows.append(item2)
            for idx, i in enumerate(x):
                walk(i, f"{path}[{idx}]")
        elif isinstance(x, dict):
            for k, v in x.items():
                walk(v, f"{path}.{k}" if path else str(k))

    walk(obj, "")
    return rows


def def_first(row: dict, names: list[str]) -> str:
    lower = {str(k).lower().replace("_", " ").strip(): k for k in row.keys()}
    for n in names:
        key = n.lower().replace("_", " ").strip()
        if key in lower:
            return def_clean_text(row.get(lower[key]))
    for k, v in row.items():
        kk = str(k).lower().replace("_", " ").strip()
        for n in names:
            if n.lower().replace("_", " ").strip() in kk:
                return def_clean_text(v)
    return ""


def def_pct(n: int, d: int) -> str:
    if d <= 0:
        return "0.00%\n0/0"
    return f"{(n / d) * 100:.2f}%\n{n}/{d}"


def def_input_manifest(input_dir: Path) -> list[dict]:
    rows = []
    if not input_dir.exists():
        return rows
    allow = {".pdf", ".docx", ".doc", ".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}
    for p in sorted(input_dir.iterdir(), key=lambda x: x.name.lower()):
        if p.is_file() and p.suffix.lower() in allow:
            rows.append({
                "filename": p.name,
                "path": str(p),
                "suffix": p.suffix.lower(),
                "size": p.stat().st_size,
                "mtime": datetime.fromtimestamp(p.stat().st_mtime).isoformat(timespec="seconds"),
            })
    return rows


def def_classify_company_report(filename: str) -> str:
    s = filename.lower()
    reject = ["大盤", "晨報", "日報", "週報", "市場", "策略", "產業"]
    positive = ["個股", "初次評等", "訪談", "memo", "ctbc", "daiwa", "gs-", "ms-", "jp-", "citi", "clst"]
    if any(x.lower() in s for x in reject) and not any(x.lower() in s for x in positive):
        return "NON_COMPANY_REVIEW"
    return "COMPANY_REPORT_CANDIDATE"


def def_extract_filename_ticker(filename: str) -> str:
    # 四碼 ticker；排除 2021~2030 年份
    nums = re.findall(r"(?<!\d)([1-9]\d{3})(?!\d)", filename)
    nums = [x for x in nums if not re.match(r"202[1-9]|2030", x)]
    return nums[-1] if nums else ""


def def_extract_filename_date(filename: str) -> str:
    # YYYYMMDD
    for m in re.findall(r"(?<!\d)(20\d{6})(?!\d)", filename):
        y, mo, d = int(m[:4]), int(m[4:6]), int(m[6:8])
        if 2000 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    # ROC YYYMMDD
    for m in re.findall(r"(?<!\d)(1\d{6})(?!\d)", filename):
        y, mo, d = int(m[:3]) + 1911, int(m[3:5]), int(m[5:7])
        if 2000 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    # omitted 20 YYMMDD
    for m in re.findall(r"(?<!\d)(\d{6})(?!\d)", filename):
        yy, mo, d = int(m[:2]), int(m[2:4]), int(m[4:6])
        y = 2000 + yy
        if 2020 <= y <= 2035 and 1 <= mo <= 12 and 1 <= d <= 31:
            return f"{y:04d}-{mo:02d}-{d:02d}"
    return ""


def def_flow_a_evidence_reuse(run_root: Path) -> tuple[list[dict], list[dict]]:
    source_patterns = {
        "v06148_basicinfo_financialdata_integrated": "**/vrn_basicinfo_financialdata_integrated_validate_v06148.json",
        "v06149_financialdata_final_evidence": "**/vrn_financialdata_final_evidence_selector_v06149.json",
        "v06150_confidence_calibrator": "**/vrn_financialdata_confidence_calibrator_v06150.json",
        "v06151_repair_router": "**/vrn_financialdata_repair_router_v06151.json",
        "v06152_decontamination_router": "**/vrn_evidence_source_decontamination_router_v06152.json",
    }

    source_rows = []
    evidence_rows = []

    for role, pat in source_patterns.items():
        p = def_find_latest_json(run_root, pat)
        source_rows.append({
            "Status Lights": def_light("OK" if p else "WARN"),
            "Source Role": role,
            "JSON": str(p) if p else "",
            "Found": "YES" if p else "NO",
            "Severity": "OK" if p else "WARN",
        })
        if p:
            obj = def_read_json(p)
            rows = def_flatten_json_rows(obj, role)
            for r in rows:
                filename = def_first(r, ["filename", "file", "report filename", "report_file"])
                ticker = def_first(r, ["ticker", "tw ticker", "TW_TICKER"])
                account = def_first(r, ["account", "financial account", "canonical account", "subject", "item"])
                value = def_first(r, ["value", "amount", "report value", "financial value"])
                validation = def_first(r, ["validation status", "validation_status", "status"])
                confidence = def_first(r, ["confidence", "final trust score", "trust score"])
                evidence_rows.append({
                    "Status Lights": def_light("OK"),
                    "Source Role": role,
                    "Source JSON": str(p),
                    "Filename": filename,
                    "Ticker": ticker,
                    "Account": account,
                    "Value": value,
                    "Validation Status": validation,
                    "Confidence": confidence,
                    "JSON Path": r.get("_json_path", ""),
                    "Severity": "OK",
                })

    clean_rows = []
    seen = set()
    for r in evidence_rows:
        key = (
            r.get("Filename", ""),
            r.get("Ticker", ""),
            r.get("Account", ""),
            r.get("Value", ""),
            r.get("Source Role", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        if r.get("Filename") or r.get("Ticker") or r.get("Account") or r.get("Value"):
            clean_rows.append(r)

    return source_rows, clean_rows


def def_flow_b_targeted_restore(input_dir: Path, target_files: list[str], evidence_rows: list[dict]) -> list[dict]:
    evidence_by_file = {}
    for r in evidence_rows:
        fn = r.get("Filename", "")
        if fn:
            evidence_by_file.setdefault(fn, 0)
            evidence_by_file[fn] += 1

    rows = []
    for name in target_files:
        p = input_dir / name
        existing_hits = evidence_by_file.get(name, 0)
        sev = "QUEUE"
        reason = "Targeted restore candidate. Reuse existing evidence first; restore only missing table/financial sections."
        if not p.exists():
            sev = "ERR"
            reason = "Input file missing."
        elif existing_hits > 0:
            sev = "WARN"
            reason = "Existing evidence found; targeted restore should only fill gaps, not overwrite."

        rows.append({
            "Status Lights": def_light(sev),
            "Filename": name,
            "Path": str(p),
            "Exists": "YES" if p.exists() else "NO",
            "Ticker From Filename": def_extract_filename_ticker(name),
            "Report Date From Filename": def_extract_filename_date(name),
            "Existing Evidence Rows": existing_hits,
            "Restore Scope": "TABLE_RESTORE + FINANCIAL_ROW_RECHECK + NO_CANONICAL_MUTATION",
            "Reason": reason,
            "Severity": sev,
        })
    return rows


def def_flow_c_reconcile(input_rows: list[dict], evidence_rows: list[dict]) -> list[dict]:
    by_file = {}
    for r in evidence_rows:
        fn = r.get("Filename", "")
        if fn:
            by_file.setdefault(fn, []).append(r)

    rows = []
    for item in input_rows:
        fn = item["filename"]
        report_type = def_classify_company_report(fn)
        ticker = def_extract_filename_ticker(fn)
        report_date = def_extract_filename_date(fn)
        ev = by_file.get(fn, [])

        fields = {
            "broker": 0,
            "analyst": 0,
            "yfinance": 0,
            "valuation": 0,
            "financial": 0,
        }

        joined = json.dumps(ev[:20], ensure_ascii=False).lower()
        if any(x in joined for x in ["broker", "gs", "jpm", "ms", "daiwa", "huanan", "兆豐", "ctbc"]):
            fields["broker"] = 1
        if any(x in joined for x in ["analyst", "研究員", "分析師"]):
            fields["analyst"] = 1
        if any(x in joined for x in ["yfinance", "adj close", "targetmeanprice", "beta"]):
            fields["yfinance"] = 1
        if any(x in joined for x in ["valuation", "per", "pbr", "本益比", "股價淨值比"]):
            fields["valuation"] = 1
        if ev:
            fields["financial"] = 1

        got = sum(fields.values())
        total = len(fields)
        sev = "OK" if got >= 3 and ev else ("WARN" if report_type == "COMPANY_REPORT_CANDIDATE" else "REVIEW")

        rows.append({
            "Status Lights": def_light(sev),
            "Report date": report_date,
            "filename": fn,
            "ticker": ticker,
            "company report gate": report_type,
            "evidence rows": len(ev),
            "BasicInfo field coverage": def_pct(got, total),
            "broker evidence": "YES" if fields["broker"] else "NO",
            "analyst evidence": "YES" if fields["analyst"] else "NO",
            "YFinance evidence": "YES" if fields["yfinance"] else "NO",
            "valuation evidence": "YES" if fields["valuation"] else "NO",
            "financial data evidence": "YES" if fields["financial"] else "NO",
            "validation status": "STAGING_READY" if sev == "OK" else "REVIEW_QUEUE",
            "Severity": sev,
        })

    return rows


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
        tds = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            cls = "left" if any(x in c.lower() for x in ["path", "json", "reason", "filename", "account"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict]]]) -> None:
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
    cards = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    ) + "</div>"
    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN FinancialData Tri-Flow Staging v0.6.15.3</title><style>{css}</style></head>
<body><header><h1>VRN · FinancialData Tri-Flow Staging v0.6.15.3</h1>
<div class="sub">Evidence reuse · targeted restore queue · BasicInfo/YFinance/Analyst/FinancialData reconcile · staging only</div></header>
{cards}<main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 7:
        raise SystemExit("usage: py <vrn_root> <run_root> <input_dir> <run_dir> <canonical_dir> <target_files_json>")

    vrn_root = Path(sys.argv[1])
    run_root = Path(sys.argv[2])
    input_dir = Path(sys.argv[3])
    run_dir = Path(sys.argv[4])
    canonical_dir = Path(sys.argv[5])
    target_files = json.loads(Path(sys.argv[6]).read_text(encoding="utf-8"))

    run_dir.mkdir(parents=True, exist_ok=True)

    input_rows = def_input_manifest(input_dir)
    source_rows, evidence_rows = def_flow_a_evidence_reuse(run_root)
    restore_rows = def_flow_b_targeted_restore(input_dir, target_files, evidence_rows)
    reconcile_rows = def_flow_c_reconcile(input_rows, evidence_rows)

    ready = [r for r in reconcile_rows if r.get("validation status") == "STAGING_READY"]
    review = [r for r in reconcile_rows if r.get("validation status") != "STAGING_READY"]
    restore_err = [r for r in restore_rows if r.get("Severity") == "ERR"]

    final_pass = len(restore_err) == 0

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "ERR"), "Gate": "TRIFLOW_STAGING_PASS", "Value": "YES" if final_pass else "NO", "Severity": "OK" if final_pass else "ERR"},
        {"Status Lights": def_light("OK"), "Gate": "INPUT_FILES", "Value": len(input_rows), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "EVIDENCE_ROWS_REUSED", "Value": len(evidence_rows), "Severity": "OK"},
        {"Status Lights": def_light("WARN" if review else "OK"), "Gate": "REVIEW_QUEUE_ROWS", "Value": len(review), "Severity": "WARN" if review else "OK"},
        {"Status Lights": def_light("OK"), "Gate": "TARGETED_RESTORE_QUEUE", "Value": len(restore_rows), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_NETWORK", "Value": "YES", "Severity": "OK"},
    ]

    next_steps = [
        {
            "Status Lights": def_light("OK"),
            "Next Step": "If restore queue has no missing file, run targeted table restore v0.6.15.4",
            "Reason": "Only queued gap files should be restored; do not rerun all input.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "After targeted restore, rerun BasicInfo + FinancialData final matrix",
            "Reason": "Use final evidence selector after table restore fills gaps.",
            "Severity": "WARN",
        },
    ]

    outputs = {
        "html": str(run_dir / "VRN_FinancialData_TriFlow_Staging_v06153.html"),
        "json": str(run_dir / "vrn_financialdata_triflow_staging_v06153.json"),
        "source_csv": str(run_dir / "flow_A_source_json_matrix_v06153.csv"),
        "evidence_csv": str(run_dir / "flow_A_reused_evidence_rows_v06153.csv"),
        "restore_csv": str(run_dir / "flow_B_targeted_restore_queue_v06153.csv"),
        "reconcile_csv": str(run_dir / "flow_C_basicinfo_financial_reconcile_v06153.csv"),
    }

    def_write_csv(Path(outputs["source_csv"]), source_rows)
    def_write_csv(Path(outputs["evidence_csv"]), evidence_rows)
    def_write_csv(Path(outputs["restore_csv"]), restore_rows)
    def_write_csv(Path(outputs["reconcile_csv"]), reconcile_rows)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "counts": {
            "Final": "PASS" if final_pass else "FAIL",
            "Input Files": len(input_rows),
            "Evidence Rows Reused": len(evidence_rows),
            "Staging Ready": len(ready),
            "Review Queue": len(review),
            "Targeted Restore Queue": len(restore_rows),
            "Missing Restore Files": len(restore_err),
            "No Canonical Mutation": "YES",
        },
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        result["counts"],
        [
            ("01 Overview", overview),
            ("02 Next Steps", next_steps),
            ("03 Flow A · Source JSON Matrix", source_rows),
            ("04 Flow A · Reused Evidence Rows", evidence_rows[:3000]),
            ("05 Flow B · Targeted Restore Queue", restore_rows),
            ("06 Flow C · BasicInfo + FinancialData Reconcile Matrix", reconcile_rows),
            ("07 Review Queue", review),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise
