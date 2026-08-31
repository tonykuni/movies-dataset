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
import hashlib
import html
import json
import re
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_TRIFLOW_CLOSEOUT_SEAL_FINAL_OPS_CONSOLE_V0615701"


def def_clean(x: Any) -> str:
    s = "" if x is None else str(x)
    s = html.unescape(s)
    s = s.replace("\u3000", " ").replace("\r", "\n")
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def def_norm(x: Any) -> str:
    return re.sub(r"[\s_\-\/\(\)（）\[\]【】{}:：,，.。&+%]+", "", str(x or "").lower())


def def_light(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "PASS", "YES", "READY", "SEALED", "FOUND"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "APPROVAL_REQUIRED", "LOCKED_OUT", "NO_COMMIT"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_find_latest_dir(root: Path, prefixes: list[str]) -> Path | None:
    if not root.exists():
        return None
    hits = []
    for prefix in prefixes:
        hits.extend([p for p in root.glob(prefix + "_*") if p.is_dir()])
    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0] if hits else None


def def_sha256_file(path: Path) -> str:
    if not path.exists() or not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    for enc in ["utf-8", "utf-8-sig", "cp950", "big5"]:
        try:
            return json.loads(path.read_text(encoding=enc))
        except Exception:
            pass
    return {}


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


def def_file_asset(label: str, path: Path, required: bool = True) -> dict:
    exists = path.exists()
    sev = "OK" if exists else ("ERR" if required else "WARN")
    return {
        "Status Lights": def_light(sev),
        "asset": label,
        "path": str(path),
        "exists": "YES" if exists else "NO",
        "sha256": def_sha256_file(path),
        "required": "YES" if required else "NO",
        "Severity": sev,
    }


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


def def_flow_a_commit_approval(run_root: Path, run_dir: Path, primary_duckdb: Path) -> dict:
    commit_run = def_find_latest_dir(run_root, ["VRN_COMMIT_CANDIDATE_PACK_APPROVAL_GATE_V061570"])
    txn_run = def_find_latest_dir(run_root, ["VRN_PRIMARY_DB_TRANSACTION_ROLLBACK_DRYRUN_V0615699"])
    sim_run = def_find_latest_dir(run_root, ["VRN_WRITE_SIMULATOR_ROLLBACK_PLAN_V0615696"])
    seal_run = def_find_latest_dir(run_root, ["VRN_MISSING_LINK_FINAL_STAGING_SEAL_V0615695"])

    rows = []
    assets = []
    next_steps = []

    if not commit_run:
        rows.append({
            "Status Lights": def_light("ERR"),
            "Gate": "COMMIT_CANDIDATE_PACK_EXISTS",
            "Value": "NO",
            "Severity": "ERR",
        })
        return {"name": "Flow A Commit Approval Seal", "pass": False, "rows": rows, "assets": assets, "next_steps": next_steps}

    commit_json = def_read_json(commit_run / "vrn_commit_candidate_pack_approval_gate_v061570.json")
    counts = commit_json.get("counts", {})
    outputs = commit_json.get("outputs", {})

    primary_sha_now = def_sha256_file(primary_duckdb)
    approval_ready = counts.get("Approval Ready") == "YES"
    write_ready_ok = str(counts.get("Write Ready Rows")) == "27"
    previous_commit_no = counts.get("Previous Commit") == "NO"
    commit_this_run_no = counts.get("Commit This Run") == "NO"
    db_write_no = counts.get("DB Write This Run") == "NO"
    ssot_no = counts.get("SSOT Mutation") == "NO"

    sealed_insert = Path(outputs.get("sealed_insert_sql", ""))
    sealed_rollback = Path(outputs.get("sealed_rollback_sql", ""))
    sealed_write_ready = Path(outputs.get("sealed_write_ready_csv", ""))
    sealed_spec = Path(outputs.get("sealed_real_commit_spec", ""))

    assets = [
        def_file_asset("commit_run_json", commit_run / "vrn_commit_candidate_pack_approval_gate_v061570.json"),
        def_file_asset("commit_run_html", commit_run / "VRN_Commit_Candidate_Pack_Approval_Gate_v061570.html"),
        def_file_asset("sealed_insert_sql", sealed_insert),
        def_file_asset("sealed_rollback_sql", sealed_rollback),
        def_file_asset("sealed_write_ready_rows", sealed_write_ready),
        def_file_asset("sealed_real_commit_spec", sealed_spec),
        def_file_asset("primary_duckdb_current", primary_duckdb),
    ]

    gate_items = [
        ("APPROVAL_READY", "YES" if approval_ready else "NO", approval_ready),
        ("WRITE_READY_ROWS_27", counts.get("Write Ready Rows", ""), write_ready_ok),
        ("PREVIOUS_COMMIT_NO", counts.get("Previous Commit", ""), previous_commit_no),
        ("COMMIT_THIS_RUN_NO", counts.get("Commit This Run", ""), commit_this_run_no),
        ("DB_WRITE_THIS_RUN_NO", counts.get("DB Write This Run", ""), db_write_no),
        ("SSOT_MUTATION_NO", counts.get("SSOT Mutation", ""), ssot_no),
        ("PRIMARY_SHA_AVAILABLE", primary_sha_now[:16], bool(primary_sha_now)),
        ("SEALED_INSERT_EXISTS", "YES" if sealed_insert.exists() else "NO", sealed_insert.exists()),
        ("SEALED_ROLLBACK_EXISTS", "YES" if sealed_rollback.exists() else "NO", sealed_rollback.exists()),
    ]

    rows = [
        {
            "Status Lights": def_light("OK" if ok else "ERR"),
            "Gate": gate,
            "Value": value,
            "Severity": "OK" if ok else "ERR",
        }
        for gate, value, ok in gate_items
    ]

    next_steps = [
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Real commit remains blocked until exact phrase YES FOR COMMIT.",
            "Reason": "This closeout run is not a commit run.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Before any future commit, re-check primary SHA against approval pack.",
            "Reason": "Avoid writing onto changed DB state.",
            "Severity": "OK",
        },
    ]

    flow_pass = all(r["Severity"] == "OK" for r in rows) and all(a["Severity"] == "OK" for a in assets if a["required"] == "YES")
    return {
        "name": "Flow A Commit Approval Seal",
        "pass": flow_pass,
        "source_run": str(commit_run),
        "rows": rows,
        "assets": assets,
        "next_steps": next_steps,
    }


def def_flow_b_ops_console(run_root: Path, run_dir: Path) -> dict:
    run_patterns = [
        ("Commit Candidate Pack", "VRN_COMMIT_CANDIDATE_PACK_APPROVAL_GATE_V061570", "VRN_Commit_Candidate_Pack_Approval_Gate_v061570.html"),
        ("Primary TXN Rollback DryRun", "VRN_PRIMARY_DB_TRANSACTION_ROLLBACK_DRYRUN_V0615699", "VRN_Primary_DB_Transaction_Rollback_DryRun_v0615699.html"),
        ("Staging Copy DryRun", "VRN_STAGING_COPY_WRITE_DRYRUN_ROLLBACK_V06156981", "VRN_Staging_Copy_Write_DryRun_Rollback_v06156981.html"),
        ("Schema Compatibility Audit", "VRN_DB_SCHEMA_COMPATIBILITY_AUDIT_V06156971", "VRN_DB_Schema_Compatibility_Audit_v06156971.html"),
        ("Write Simulator", "VRN_WRITE_SIMULATOR_ROLLBACK_PLAN_V0615696", "VRN_Write_Simulator_Rollback_Plan_v0615696.html"),
        ("Final Staging Seal", "VRN_MISSING_LINK_FINAL_STAGING_SEAL_V0615695", "VRN_Missing_Link_Final_Staging_Seal_v0615695.html"),
        ("Supportive Module Index", "SUPPORTIVE_FINAL_INDEX_SEAL_V032", "Supportive_Final_Index_Seal_v032.html"),
    ]

    rows = []
    for label, prefix, html_name in run_patterns:
        latest = def_find_latest_dir(run_root, [prefix])
        html_path = latest / html_name if latest else Path("")
        rows.append({
            "Status Lights": def_light("OK" if latest else "WARN"),
            "Console Item": label,
            "Latest Run": str(latest) if latest else "",
            "HTML": str(html_path) if html_path.exists() else "",
            "Found": "YES" if latest else "NO",
            "Severity": "OK" if latest else "WARN",
        })

    console_html = run_dir / "VRN_Final_ReadOnly_Ops_Console_Index_v0615701.html"
    console_md = run_dir / "VRN_Final_ReadOnly_Ops_Console_Index_v0615701.md"

    md_lines = [
        "# VRN Final Read-Only Ops Console Index v0.6.15.7.0.1",
        "",
        "Mode: read-only index only. No DB write. No commit. No SSOT mutation.",
        "",
    ]
    for r in rows:
        md_lines.append(f"- {r['Console Item']}: {r['HTML'] or r['Latest Run'] or 'NOT FOUND'}")
    console_md.write_text("\n".join(md_lines), encoding="utf-8")

    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif}
header{padding:26px 34px;background:#0d1b2f;border-bottom:1px solid #1f3557}
main{padding:24px 34px}.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:14px 0}
a{color:#9fd3ff} .ok{color:#7ee787}.warn{color:#ffd166}
"""
    cards = []
    for r in rows:
        sev_class = "ok" if r["Severity"] == "OK" else "warn"
        link = f"<a href='file:///{html.escape(r['HTML'].replace(chr(92), '/'))}'>Open HTML</a>" if r["HTML"] else "No HTML"
        cards.append(f"<section class='card'><h2>{html.escape(r['Console Item'])}</h2><p class='{sev_class}'>{r['Found']}</p><p>{html.escape(r['Latest Run'])}</p><p>{link}</p></section>")
    console_html.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{css}</style></head><body><header><h1>VRN Final Read-Only Ops Console Index</h1><p>No commit · No DB write · No SSOT mutation</p></header><main>{''.join(cards)}</main></body></html>", encoding="utf-8")

    assets = [
        def_file_asset("ops_console_html", console_html),
        def_file_asset("ops_console_markdown", console_md),
    ]
    flow_pass = all(r["Severity"] in ["OK", "WARN"] for r in rows) and console_html.exists()
    return {
        "name": "Flow B ReadOnly Ops Console",
        "pass": flow_pass,
        "rows": rows,
        "assets": assets,
        "next_steps": [
            {
                "Status Lights": def_light("OK"),
                "Next Step": "Use this console as read-only operating index.",
                "Reason": "It links latest reports without changing data.",
                "Severity": "OK",
            }
        ],
    }


def def_flow_c_governance(run_root: Path, run_dir: Path, supportive_dir: Path, config_dir: Path) -> dict:
    seal_run = def_find_latest_dir(run_root, ["VRN_MISSING_LINK_FINAL_STAGING_SEAL_V0615695"])
    commit_run = def_find_latest_dir(run_root, ["VRN_COMMIT_CANDIDATE_PACK_APPROVAL_GATE_V061570"])

    quarantine = []
    alias = []
    no_match = []

    if seal_run:
        quarantine = [r for r in def_read_csv(seal_run / "vrn_quarantine_v0615695.csv") if "empty_marker" not in r]
        alias = [r for r in def_read_csv(seal_run / "vrn_alias_candidates_no_ssot_v0615695.csv") if "empty_marker" not in r]
        no_match = [r for r in def_read_csv(seal_run / "vrn_no_match_v0615695.csv") if "empty_marker" not in r]

    gate_module = supportive_dir / "VIS_VRN_NewReportCompatibilityGate_v01.py"
    adapter_registry = config_dir / "VIS_VRN_AdapterRegistry_v01.json"
    playbook = config_dir / "VIS_VRN_NewReport_Format_Playbook_v01.md"

    governance_rows = [
        {
            "Status Lights": def_light("OK"),
            "Governance Item": "quarantine_rows_locked_out",
            "Rows": len(quarantine),
            "Action": "KEEP_OUT_OF_CANONICAL",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Governance Item": "alias_candidates_no_ssot_patch",
            "Rows": len(alias),
            "Action": "SECOND_CONFIRMATION_REQUIRED",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Governance Item": "no_match_rows_locked_out",
            "Rows": len(no_match),
            "Action": "REVIEW_ONLY",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK" if gate_module.exists() else "WARN"),
            "Governance Item": "new_report_compatibility_gate",
            "Rows": "N/A",
            "Action": str(gate_module),
            "Severity": "OK" if gate_module.exists() else "WARN",
        },
        {
            "Status Lights": def_light("OK" if adapter_registry.exists() else "WARN"),
            "Governance Item": "adapter_registry",
            "Rows": "N/A",
            "Action": str(adapter_registry),
            "Severity": "OK" if adapter_registry.exists() else "WARN",
        },
        {
            "Status Lights": def_light("OK" if playbook.exists() else "WARN"),
            "Governance Item": "new_report_format_playbook",
            "Rows": "N/A",
            "Action": str(playbook),
            "Severity": "OK" if playbook.exists() else "WARN",
        },
    ]

    def_write_csv(run_dir / "FLOW_C_quarantine_locked_out_v0615701.csv", quarantine)
    def_write_csv(run_dir / "FLOW_C_alias_candidates_no_ssot_v0615701.csv", alias)
    def_write_csv(run_dir / "FLOW_C_no_match_locked_out_v0615701.csv", no_match)

    assets = [
        def_file_asset("new_report_compatibility_gate", gate_module, False),
        def_file_asset("adapter_registry", adapter_registry, False),
        def_file_asset("new_report_format_playbook", playbook, False),
        def_file_asset("flow_c_quarantine_csv", run_dir / "FLOW_C_quarantine_locked_out_v0615701.csv"),
        def_file_asset("flow_c_alias_csv", run_dir / "FLOW_C_alias_candidates_no_ssot_v0615701.csv"),
        def_file_asset("flow_c_no_match_csv", run_dir / "FLOW_C_no_match_locked_out_v0615701.csv"),
    ]

    flow_pass = bool(seal_run) and len(quarantine) == 4 and len(alias) == 52 and len(no_match) == 4
    return {
        "name": "Flow C Governance Lockout + Compatibility",
        "pass": flow_pass,
        "source_run": str(seal_run) if seal_run else "",
        "rows": governance_rows,
        "assets": assets,
        "next_steps": [
            {
                "Status Lights": def_light("OK"),
                "Next Step": "Alias candidates remain no-SSOT until second-confirmation workflow.",
                "Reason": "Do not pollute SSOT with value-only or ambiguous mappings.",
                "Severity": "OK",
            },
            {
                "Status Lights": def_light("OK"),
                "Next Step": "All future reports enter Compatibility Gate before final matrix.",
                "Reason": "Unknown broker/layout stays in staging.",
                "Severity": "OK",
            },
        ],
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
            cls = "left" if any(x in k.lower() for x in ["path", "html", "reason", "next", "asset", "run", "action"]) else "center"
            tds.append(f"<td class='{cls}'>{html.escape(str(v)).replace(chr(10), '<br>')}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
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
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1200px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    )
    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Tri-Flow Closeout Seal v0615701</title><style>{css}</style></head>
<body><header><h1>VRN · Tri-Flow Closeout Seal + Final Ops Console v0.6.15.7.0.1</h1>
<div class="sub">three flows parallel · no commit · no DB write · no canonical / SSOT mutation</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 7:
        raise SystemExit("usage: py <run_root> <run_dir> <primary_duckdb> <supportive_dir> <config_dir> <via_root>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    primary_duckdb = Path(sys.argv[3])
    supportive_dir = Path(sys.argv[4])
    config_dir = Path(sys.argv[5])
    via_root = Path(sys.argv[6])
    run_dir.mkdir(parents=True, exist_ok=True)

    flows = {}
    with ThreadPoolExecutor(max_workers=3) as ex:
        futures = {
            ex.submit(def_flow_a_commit_approval, run_root, run_dir, primary_duckdb): "A",
            ex.submit(def_flow_b_ops_console, run_root, run_dir): "B",
            ex.submit(def_flow_c_governance, run_root, run_dir, supportive_dir, config_dir): "C",
        }

        for fut in as_completed(futures):
            key = futures[fut]
            try:
                flows[key] = fut.result()
            except Exception as e:
                flows[key] = {
                    "name": f"Flow {key} ERROR",
                    "pass": False,
                    "rows": [{
                        "Status Lights": def_light("ERR"),
                        "Gate": "FLOW_EXCEPTION",
                        "Value": f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
                        "Severity": "ERR",
                    }],
                    "assets": [],
                    "next_steps": [],
                }

    flow_summary = []
    all_assets = []
    all_next_steps = []

    for key in ["A", "B", "C"]:
        f = flows.get(key, {})
        flow_summary.append({
            "Status Lights": def_light("OK" if f.get("pass") else "ERR"),
            "Flow": key,
            "Name": f.get("name", ""),
            "Pass": "YES" if f.get("pass") else "NO",
            "Source Run": f.get("source_run", ""),
            "Severity": "OK" if f.get("pass") else "ERR",
        })
        all_assets.extend(f.get("assets", []))
        all_next_steps.extend(f.get("next_steps", []))

    hard_rules = [
        {"Status Lights": def_light("OK"), "Rule": "NO_COMMIT", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_TABLE_CREATE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_INSERT", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_DELETE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("WARN"), "Rule": "REAL_COMMIT_REQUIRES_EXACT_PHRASE", "Value": "YES FOR COMMIT", "Severity": "WARN"},
    ]

    final_pass = all(f.get("pass") for f in flows.values()) and len(flows) == 3

    outputs = {
        "html": str(run_dir / "VRN_TriFlow_Closeout_Seal_Final_Ops_Console_v0615701.html"),
        "json": str(run_dir / "vrn_triflow_closeout_seal_final_ops_console_v0615701.json"),
        "flow_summary_csv": str(run_dir / "vrn_triflow_flow_summary_v0615701.csv"),
        "flow_a_gate_csv": str(run_dir / "vrn_flow_a_commit_approval_gate_v0615701.csv"),
        "flow_b_console_csv": str(run_dir / "vrn_flow_b_ops_console_index_v0615701.csv"),
        "flow_c_governance_csv": str(run_dir / "vrn_flow_c_governance_v0615701.csv"),
        "assets_csv": str(run_dir / "vrn_triflow_assets_manifest_v0615701.csv"),
        "hard_rules_csv": str(run_dir / "vrn_triflow_hard_rules_v0615701.csv"),
        "next_steps_csv": str(run_dir / "vrn_triflow_next_steps_v0615701.csv"),
    }

    def_write_csv(Path(outputs["flow_summary_csv"]), flow_summary)
    def_write_csv(Path(outputs["flow_a_gate_csv"]), flows["A"].get("rows", []))
    def_write_csv(Path(outputs["flow_b_console_csv"]), flows["B"].get("rows", []))
    def_write_csv(Path(outputs["flow_c_governance_csv"]), flows["C"].get("rows", []))
    def_write_csv(Path(outputs["assets_csv"]), all_assets)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)
    def_write_csv(Path(outputs["next_steps_csv"]), all_next_steps)

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Flow A": "PASS" if flows.get("A", {}).get("pass") else "FAIL",
        "Flow B": "PASS" if flows.get("B", {}).get("pass") else "FAIL",
        "Flow C": "PASS" if flows.get("C", {}).get("pass") else "FAIL",
        "Commit": "NO",
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
        "Approval Phrase Needed": "YES FOR COMMIT",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "WARN"), "Gate": "TRIFLOW_CLOSEOUT_PASS", "Value": "YES" if final_pass else "REVIEW", "Severity": "OK" if final_pass else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "NO_COMMIT", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_DB_WRITE", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "NO_SSOT_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_light("WARN"), "Gate": "MANUAL_COMMIT_APPROVAL_REQUIRED", "Value": "YES FOR COMMIT", "Severity": "WARN"},
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "counts": counts,
        "outputs": outputs,
        "primary_duckdb": str(primary_duckdb),
        "via_root": str(via_root),
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Flow Summary", flow_summary, None),
            ("03 Flow A Commit Approval Seal", flows["A"].get("rows", []), None),
            ("04 Flow B ReadOnly Ops Console Index", flows["B"].get("rows", []), None),
            ("05 Flow C Governance Lockout + Compatibility", flows["C"].get("rows", []), None),
            ("06 Assets Manifest", all_assets, 200),
            ("07 Hard Rules", hard_rules, None),
            ("08 Next Steps", all_next_steps, None),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise