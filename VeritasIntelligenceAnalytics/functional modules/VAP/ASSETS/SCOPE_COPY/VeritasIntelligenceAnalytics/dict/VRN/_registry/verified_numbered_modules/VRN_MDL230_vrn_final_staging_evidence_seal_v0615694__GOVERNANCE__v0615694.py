# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import re
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_FINAL_STAGING_EVIDENCE_SEAL_V0615694"


def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = html.unescape(s)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。&+%]+", "", str(x or "").lower())


def def_float(x: Any, default: Any = None) -> Any:
    s = def_clean(x).replace(",", "").replace("%", "")
    if s in ["", "-", "—", "–", "NA", "N/A", "nan", "None"]:
        return default
    try:
        return float(s)
    except Exception:
        return default


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "SEALED", "WRITE_READY"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "NEED_RUN", "LOCKED", "CANDIDATE_ONLY"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_find_latest_dir(root: Path, prefix: str) -> Path | None:
    if not root.exists():
        return None
    hits = [p for p in root.glob(prefix + "_*") if p.is_dir()]
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0] if hits else None


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5", "latin-1"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def def_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    for enc in ["utf-8", "utf-8-sig", "cp950", "big5"]:
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            pass
    return {}


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


def def_get(row: dict, aliases: list[str]) -> str:
    mp = {def_norm(k): k for k in row.keys()}
    for a in aliases:
        na = def_norm(a)
        if na in mp:
            return def_clean(row.get(mp[na]))
    for k in row.keys():
        nk = def_norm(k)
        for a in aliases:
            if def_norm(a) in nk:
                return def_clean(row.get(k))
    return ""


def def_validate_staging_row(row: dict) -> dict:
    reasons = []

    required = [
        "ticker",
        "source file",
        "statement",
        "period year",
        "account key",
        "official row label",
        "report value mn_twd",
        "official value raw",
        "official value scaled to mn_twd",
        "evidence route",
        "precision route",
        "evidence cache file",
    ]

    for col in required:
        if def_get(row, [col]) == "":
            reasons.append(f"missing_{col}")

    if def_get(row, ["db write"]).upper() != "NO":
        reasons.append("db_write_not_locked_no")

    if def_get(row, ["canonical mutation"]).upper() != "NO":
        reasons.append("canonical_mutation_not_locked_no")

    if def_get(row, ["ssot mutation"]).upper() != "NO":
        reasons.append("ssot_mutation_not_locked_no")

    if def_get(row, ["canonical write status"]) != "STAGING_ONLY_NO_WRITE":
        reasons.append("canonical_write_status_not_staging_only")

    if def_get(row, ["precision route"]) not in ["STRICT_LOCKED", ""]:
        reasons.append("precision_route_not_strict_locked")

    if def_get(row, ["evidence route"]) != "VALIDATED_ALIAS_AND_VALUE":
        reasons.append("evidence_route_not_validated_alias_and_value")

    rv = def_float(def_get(row, ["report value mn_twd"]), None)
    ov_mn = def_float(def_get(row, ["official value scaled to mn_twd"]), None)
    if rv is not None and ov_mn is not None:
        diff = abs(rv - ov_mn)
        base = max(abs(rv), abs(ov_mn), 1.0)
        rel = diff / base
        if rel > 0.005:
            reasons.append("scaled_value_rel_diff_over_0.5pct")
    else:
        diff = ""
        rel = ""

    sealed = len(reasons) == 0

    out = dict(row)
    out["seal route"] = "WRITE_READINESS_CANDIDATE" if sealed else "SEAL_REVIEW"
    out["seal reasons"] = " | ".join(reasons)
    out["seal abs diff mn_twd"] = diff
    out["seal rel diff mn_twd"] = rel
    out["write readiness"] = "READY_FOR_WRITE_PLAN_ONLY" if sealed else "NOT_READY"
    out["actual write executed"] = "NO"
    out["db write"] = "NO"
    out["canonical mutation"] = "NO"
    out["ssot mutation"] = "NO"
    out["Severity"] = "OK" if sealed else "WARN"
    out["Status Lights"] = def_light("OK" if sealed else "WARN")
    return out


def def_pack_integrity(name: str, rows: list[dict], expected_locked: bool = True) -> dict:
    bad_db = sum(1 for r in rows if def_get(r, ["db write"]).upper() not in ["", "NO"])
    bad_can = sum(1 for r in rows if def_get(r, ["canonical mutation"]).upper() not in ["", "NO"])
    bad_ssot = sum(1 for r in rows if def_get(r, ["ssot mutation"]).upper() not in ["", "NO"])
    sev = "OK" if bad_db == 0 and bad_can == 0 and bad_ssot == 0 else "ERR"
    return {
        "Status Lights": def_light(sev),
        "pack": name,
        "rows": len(rows),
        "bad db write flags": bad_db,
        "bad canonical mutation flags": bad_can,
        "bad ssot mutation flags": bad_ssot,
        "Severity": sev,
    }


def def_html_table(title: str, rows: list[dict], limit: int | None = None) -> str:
    if limit is not None:
        rows = rows[:limit]
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    th = "".join(f"<th>{html.escape(str(k))}</th>" for k in fields)
    trs = []
    for r in rows:
        tds = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["file", "account", "label", "route", "reason", "cache", "source", "status"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(str(v)).replace(chr(10), '<br>')}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:25px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1120px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    )
    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Final Staging Evidence Seal v0615694</title><style>{css}</style></head>
<body><header><h1>VRN · Final Staging Evidence Seal + Write-Readiness Report v0.6.15.6.9.4</h1>
<div class="sub">write-readiness report only · no DB / canonical / SSOT mutation</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 3:
        raise SystemExit("usage: py <run_root> <run_dir>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    run_dir.mkdir(parents=True, exist_ok=True)

    source = def_find_latest_dir(run_root, "VRN_FINAL_CANONICAL_STAGING_PACK_V0615693")
    if not source:
        source = None

    if source:
        source_json = def_read_json(source / "vrn_final_canonical_staging_pack_v0615693.json")
        staging = [r for r in def_read_csv(source / "vrn_final_canonical_staging_pack_v0615693.csv") if "empty_marker" not in r]
        quarantine = [r for r in def_read_csv(source / "vrn_final_quarantine_pack_v0615693.csv") if "empty_marker" not in r]
        alias = [r for r in def_read_csv(source / "vrn_final_alias_candidate_pack_no_ssot_v0615693.csv") if "empty_marker" not in r]
        no_match = [r for r in def_read_csv(source / "vrn_final_no_match_pack_v0615693.csv") if "empty_marker" not in r]
        source_mode = source_json.get("source_mode", "")
    else:
        staging = []
        quarantine = []
        alias = []
        no_match = []
        source_mode = "NEED_RUN_V0615693"

    sealed_rows = [def_validate_staging_row(r) for r in staging]
    write_ready = [r for r in sealed_rows if def_get(r, ["write readiness"]) == "READY_FOR_WRITE_PLAN_ONLY"]
    seal_review = [r for r in sealed_rows if def_get(r, ["write readiness"]) != "READY_FOR_WRITE_PLAN_ONLY"]

    integrity_rows = [
        def_pack_integrity("canonical_staging_pack", staging),
        def_pack_integrity("quarantine_pack", quarantine),
        def_pack_integrity("alias_candidate_pack_no_ssot", alias),
        def_pack_integrity("no_match_pack", no_match),
    ]

    reason_rows = []
    c = Counter()
    for r in seal_review:
        for reason in [x.strip() for x in def_get(r, ["seal reasons"]).split("|") if x.strip()]:
            c[reason] += 1
    for reason, n in c.most_common():
        reason_rows.append({
            "Status Lights": def_light("WARN"),
            "seal review reason": reason,
            "rows": n,
            "Severity": "WARN",
        })

    gate_rows = [
        {"Status Lights": def_light("OK" if source else "WARN"), "Gate": "SOURCE_V0615693_EXISTS", "Value": "YES" if source else "NO", "Severity": "OK" if source else "WARN"},
        {"Status Lights": def_light("OK" if write_ready else "WARN"), "Gate": "WRITE_READY_PLAN_ONLY_ROWS", "Value": len(write_ready), "Severity": "OK" if write_ready else "WARN"},
        {"Status Lights": def_light("WARN" if seal_review else "OK"), "Gate": "SEAL_REVIEW_ROWS", "Value": len(seal_review), "Severity": "WARN" if seal_review else "OK"},
        {"Status Lights": def_light("WARN" if quarantine else "OK"), "Gate": "QUARANTINE_REMAINS_ISOLATED", "Value": len(quarantine), "Severity": "WARN" if quarantine else "OK"},
        {"Status Lights": def_light("WARN" if alias else "OK"), "Gate": "ALIAS_CANDIDATES_REMAIN_NO_SSOT_PATCH", "Value": len(alias), "Severity": "WARN" if alias else "OK"},
        {"Status Lights": def_light("OK"), "Gate": "ACTUAL_WRITE_EXECUTED", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    next_steps = []
    if not source:
        next_steps.append({
            "Status Lights": def_light("WARN"),
            "Next Step": "Run v0.6.15.6.9.3 Final Canonical Staging Pack Builder first.",
            "Reason": "No v0615693 staging pack found.",
            "Severity": "WARN",
        })
    elif write_ready:
        next_steps.append({
            "Status Lights": def_light("WARN"),
            "Next Step": "Prepare DB/canonical write simulator with rollback plan, still dry-run.",
            "Reason": "Write-ready rows exist, but actual write still requires separate reversible simulator.",
            "Severity": "WARN",
        })
    else:
        next_steps.append({
            "Status Lights": def_light("WARN"),
            "Next Step": "Debug seal review rows before any write simulator.",
            "Reason": "No rows passed final evidence seal.",
            "Severity": "WARN",
        })

    next_steps.extend([
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Do not touch quarantine rows.",
            "Reason": "They are intentionally isolated.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Do not patch SSOT from alias pack yet.",
            "Reason": "Alias pack requires second-confirmation workflow.",
            "Severity": "OK",
        },
    ])

    outputs = {
        "html": str(run_dir / "VRN_Final_Staging_Evidence_Seal_v0615694.html"),
        "json": str(run_dir / "vrn_final_staging_evidence_seal_v0615694.json"),
        "write_ready_rows_csv": str(run_dir / "vrn_write_ready_plan_only_rows_v0615694.csv"),
        "seal_review_rows_csv": str(run_dir / "vrn_seal_review_rows_v0615694.csv"),
        "seal_review_reason_summary_csv": str(run_dir / "vrn_seal_review_reason_summary_v0615694.csv"),
        "pack_integrity_csv": str(run_dir / "vrn_pack_integrity_v0615694.csv"),
        "gate_matrix_csv": str(run_dir / "vrn_final_staging_evidence_gate_v0615694.csv"),
        "next_steps_csv": str(run_dir / "vrn_final_staging_evidence_next_steps_v0615694.csv"),
        "quarantine_passthrough_csv": str(run_dir / "vrn_quarantine_passthrough_v0615694.csv"),
        "alias_passthrough_csv": str(run_dir / "vrn_alias_passthrough_no_ssot_v0615694.csv"),
    }

    def_write_csv(Path(outputs["write_ready_rows_csv"]), write_ready)
    def_write_csv(Path(outputs["seal_review_rows_csv"]), seal_review)
    def_write_csv(Path(outputs["seal_review_reason_summary_csv"]), reason_rows)
    def_write_csv(Path(outputs["pack_integrity_csv"]), integrity_rows)
    def_write_csv(Path(outputs["gate_matrix_csv"]), gate_rows)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)
    def_write_csv(Path(outputs["quarantine_passthrough_csv"]), quarantine)
    def_write_csv(Path(outputs["alias_passthrough_csv"]), alias)

    integrity_ok = all(r.get("Severity") == "OK" for r in integrity_rows)
    final_pass = bool(source) and len(write_ready) > 0 and integrity_ok

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Source Mode": source_mode,
        "Canonical Staging Rows": len(staging),
        "Write Ready Plan Only": len(write_ready),
        "Seal Review": len(seal_review),
        "Quarantine": len(quarantine),
        "Alias Candidates": len(alias),
        "No Match": len(no_match),
        "Pack Integrity OK": "YES" if integrity_ok else "NO",
        "Actual Write": "NO",
        "DB Write": "NO",
        "Canonical Mutation": "NO",
        "SSOT Mutation": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "WARN"), "Gate": "FINAL_STAGING_EVIDENCE_SEAL_PASS", "Value": "YES" if final_pass else "REVIEW", "Severity": "OK" if final_pass else "WARN"},
        {"Status Lights": def_light("OK" if source else "WARN"), "Gate": "SOURCE_RUN", "Value": str(source) if source else "", "Severity": "OK" if source else "WARN"},
        {"Status Lights": def_light("OK" if write_ready else "WARN"), "Gate": "WRITE_READY_PLAN_ONLY_ROWS", "Value": len(write_ready), "Severity": "OK" if write_ready else "WARN"},
        {"Status Lights": def_light("OK" if integrity_ok else "ERR"), "Gate": "PACK_INTEGRITY_OK", "Value": "YES" if integrity_ok else "NO", "Severity": "OK" if integrity_ok else "ERR"},
        {"Status Lights": def_light("OK"), "Gate": "ACTUAL_WRITE_EXECUTED", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "source_run": str(source) if source else "",
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Gate Matrix", gate_rows, None),
            ("03 Next Steps", next_steps, None),
            ("04 Write Ready Rows - Plan Only", write_ready, 1000),
            ("05 Seal Review Rows", seal_review, 1000),
            ("06 Seal Review Reason Summary", reason_rows, None),
            ("07 Pack Integrity", integrity_rows, None),
            ("08 Quarantine Passthrough", quarantine, 1000),
            ("09 Alias Candidate Passthrough - No SSOT", alias, 1000),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        import traceback
        print(traceback.format_exc())
        raise