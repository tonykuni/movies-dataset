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
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_FINAL_INTEGRATION_GOVERNANCE_SEAL_V0615703"


# ==================================================================================================
# def 00_BASIC_UTILITIES
# ==================================================================================================
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
    if s in ["OK", "PASS", "YES", "SEALED", "READY", "FOUND", "ACTIVE"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "BLOCKED", "APPROVAL_REQUIRED", "OPTIONAL"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_find_latest_dir(root: Path, prefixes: list[str]) -> Path | None:
    if not root.exists():
        return None

    hits: list[Path] = []
    for prefix in prefixes:
        hits.extend([p for p in root.glob(prefix + "_*") if p.is_dir()])

    if not hits:
        return None

    return sorted(hits, key=lambda p: p.stat().st_mtime, reverse=True)[0]


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


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    if not rows:
        rows = [{"empty_marker": ""}]

    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_file_asset(label: str, path: Path, required: bool = True, role: str = "") -> dict:
    exists = path.exists()
    sev = "OK" if exists else ("ERR" if required else "WARN")

    return {
        "Status Lights": def_light(sev),
        "asset": label,
        "role": role,
        "path": str(path),
        "exists": "YES" if exists else "NO",
        "sha256": def_sha256_file(path),
        "required": "YES" if required else "NO",
        "Severity": sev,
    }


# ==================================================================================================
# def 01_HTML_RENDERING
# ==================================================================================================
def def_html_table(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields: list[str] = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(k))}</th>" for k in fields)

    trs: list[str] = []
    for r in rows:
        tds: list[str] = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["path", "asset", "role", "rule", "reason", "next", "description", "flow", "html", "json", "playbook"]) else "center"
            safe_v = html.escape(str(v)).replace(chr(10), "<br>")
            tds.append(f"<td class='{cls}'>{safe_v}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")

    return (
        f"<section class='card'>"
        f"<h2>{html.escape(title)}</h2>"
        f"<div class='table-wrap'>"
        f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"
        f"</div></section>"
    )


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:28px 36px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:26px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1300px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
.footer{padding:20px 34px;color:#9fb3c8}
"""
    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    )
    body = "".join(def_html_table(t, rows) for t, rows in sections)

    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>VRN Final Integration Governance Seal v0615703</title>
<style>{css}</style>
</head>
<body>
<header>
<h1>VRN · Final Integration Governance Seal + ReadOnly Ops Launcher v0.6.15.7.0.3</h1>
<div class="sub">integration governance only · no commit · no DB write · no canonical / SSOT mutation</div>
</header>
<div class="grid">{cards}</div>
<main>{body}</main>
<div class="footer">Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</div>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 02_PLAYBOOKS
# ==================================================================================================
def def_build_recovery_playbook(primary_duckdb: Path) -> str:
    return "\n".join([
        "# VRN Recovery / Rollback / Governance Playbook v0.6.15.7.0.3",
        "",
        "## Current State",
        "- System is sealed in read-only closeout state.",
        "- Commit blocker is ACTIVE.",
        "- No DB write has been executed by closeout / handover / governance runs.",
        "",
        "## Hard Blocker",
        "- Real DB commit requires exact phrase: YES FOR COMMIT",
        "- Without that phrase, only reports / indexes / validation / playbooks may be generated.",
        "",
        "## Primary DB",
        f"- Primary DuckDB: {primary_duckdb}",
        "",
        "## If Future Report Format Changes",
        "1. New report enters Compatibility Gate.",
        "2. Unknown broker / layout goes to staging queue.",
        "3. Do not update canonical until validation matrix passes.",
        "4. Do not patch SSOT unless alias candidates pass second-confirmation workflow.",
        "5. OCR remains targeted only, never default.",
        "",
        "## If Commit Is Requested Later",
        "1. Require exact user phrase: YES FOR COMMIT.",
        "2. Recompute current DB SHA256.",
        "3. Compare with approval pack SHA.",
        "4. Create fresh DB backup.",
        "5. Execute commit inside transaction.",
        "6. Verify inserted row count.",
        "7. Verify duplicate primary keys = 0.",
        "8. Commit only after all gates pass.",
        "9. Generate rollback SQL and post-commit report.",
        "",
        "## Do Not Touch",
        "- Quarantine rows.",
        "- Alias candidates.",
        "- No-match rows.",
        "- SSOT alias dictionary without second confirmation.",
    ])


def def_build_readonly_launcher(run_dir: Path, registry_rows: list[dict]) -> str:
    lines = [
        "# VRN ReadOnly Ops Launcher v0.6.15.7.0.3",
        "# Generated file. Safe launcher only. No DB write. No commit.",
        "$ErrorActionPreference = 'Continue'",
        "Write-Host 'VRN ReadOnly Ops Launcher · No Commit / No DB Write' -ForegroundColor Cyan",
        "",
        "$Reports = @(",
    ]

    for r in registry_rows:
        html_path = str(r.get("html path", "")).replace("'", "''")
        label = str(r.get("stage", "")).replace("'", "''")
        if html_path:
            lines.append("    @{ Stage = '" + label + "'; Html = '" + html_path + "' },")

    lines.extend([
        ")",
        "",
        "foreach ($r in $Reports) {",
        "    if ($r.Html -and (Test-Path -LiteralPath $r.Html)) {",
        "        Write-Host ('[OPEN] ' + $r.Stage + ' -> ' + $r.Html) -ForegroundColor Green",
        "        Start-Process $r.Html",
        "    } else {",
        "        Write-Host ('[MISS] ' + $r.Stage) -ForegroundColor Yellow",
        "    }",
        "}",
        "",
        "Write-Host 'PowerShell session remains open.' -ForegroundColor DarkGray",
    ])

    return "\n".join(lines)


# ==================================================================================================
# def 03_MAIN
# ==================================================================================================
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

    latest = {
        "Final Handover": (
            def_find_latest_dir(run_root, ["VRN_FINAL_HANDOVER_COMMIT_BLOCKER_SEAL_V0615702"]),
            "VRN_Final_Handover_Commit_Blocker_Seal_v0615702.html",
            "vrn_final_handover_commit_blocker_seal_v0615702.json",
        ),
        "Tri-Flow Closeout": (
            def_find_latest_dir(run_root, ["VRN_TRIFLOW_CLOSEOUT_SEAL_FINAL_OPS_CONSOLE_V0615701"]),
            "VRN_TriFlow_Closeout_Seal_Final_Ops_Console_v0615701.html",
            "vrn_triflow_closeout_seal_final_ops_console_v0615701.json",
        ),
        "Commit Candidate Pack": (
            def_find_latest_dir(run_root, ["VRN_COMMIT_CANDIDATE_PACK_APPROVAL_GATE_V061570"]),
            "VRN_Commit_Candidate_Pack_Approval_Gate_v061570.html",
            "vrn_commit_candidate_pack_approval_gate_v061570.json",
        ),
        "Primary TXN Rollback DryRun": (
            def_find_latest_dir(run_root, ["VRN_PRIMARY_DB_TRANSACTION_ROLLBACK_DRYRUN_V0615699"]),
            "VRN_Primary_DB_Transaction_Rollback_DryRun_v0615699.html",
            "vrn_primary_db_transaction_rollback_dryrun_v0615699.json",
        ),
        "Staging Copy Write DryRun": (
            def_find_latest_dir(run_root, ["VRN_STAGING_COPY_WRITE_DRYRUN_ROLLBACK_V06156981"]),
            "VRN_Staging_Copy_Write_DryRun_Rollback_v06156981.html",
            "vrn_staging_copy_write_dryrun_rollback_v06156981.json",
        ),
        "DB Schema Audit": (
            def_find_latest_dir(run_root, ["VRN_DB_SCHEMA_COMPATIBILITY_AUDIT_V06156971"]),
            "VRN_DB_Schema_Compatibility_Audit_v06156971.html",
            "vrn_db_schema_compatibility_audit_v06156971.json",
        ),
        "Write Simulator": (
            def_find_latest_dir(run_root, ["VRN_WRITE_SIMULATOR_ROLLBACK_PLAN_V0615696"]),
            "VRN_Write_Simulator_Rollback_Plan_v0615696.html",
            "vrn_write_simulator_rollback_plan_v0615696.json",
        ),
        "Final Staging Seal": (
            def_find_latest_dir(run_root, ["VRN_MISSING_LINK_FINAL_STAGING_SEAL_V0615695"]),
            "VRN_Missing_Link_Final_Staging_Seal_v0615695.html",
            "vrn_missing_link_final_staging_seal_v0615695.json",
        ),
    }

    final_handover_dir = latest["Final Handover"][0]
    final_handover_json = {}
    if final_handover_dir:
        final_handover_json = def_read_json(final_handover_dir / latest["Final Handover"][2])

    final_counts = final_handover_json.get("counts", {})
    final_pass = final_counts.get("Final") == "PASS"
    blocker_active = final_counts.get("Commit Blocker") == "ACTIVE"
    commit_no = final_counts.get("Commit") == "NO"
    db_no = final_counts.get("DB Write") == "NO"
    canonical_no = final_counts.get("Canonical") == "NO"
    ssot_no = final_counts.get("SSOT") == "NO"

    registry_rows: list[dict] = []
    for stage, (d, html_name, json_name) in latest.items():
        html_path = d / html_name if d else Path("")
        json_path = d / json_name if d else Path("")
        row = {
            "Status Lights": def_light("OK" if d else "ERR"),
            "stage": stage,
            "run dir": str(d) if d else "",
            "html path": str(html_path) if html_path.exists() else "",
            "json path": str(json_path) if json_path.exists() else "",
            "html exists": "YES" if html_path.exists() else "NO",
            "json exists": "YES" if json_path.exists() else "NO",
            "html sha256": def_sha256_file(html_path),
            "json sha256": def_sha256_file(json_path),
            "Severity": "OK" if d and html_path.exists() else "ERR",
        }
        registry_rows.append(row)

    supportive_assets = [
        def_file_asset(
            "supportive_module_final_index_html",
            supportive_dir / "VIS_Supportive_Module_Index.html",
            False,
            "Supportive module index",
        ),
        def_file_asset(
            "supportive_module_final_index_json",
            supportive_dir / "VIS_Supportive_Module_Index.json",
            False,
            "Supportive module index",
        ),
        def_file_asset(
            "new_report_compatibility_gate",
            supportive_dir / "VIS_VRN_NewReportCompatibilityGate_v01.py",
            False,
            "Future report format compatibility gate",
        ),
        def_file_asset(
            "adapter_registry",
            config_dir / "VIS_VRN_AdapterRegistry_v01.json",
            False,
            "Broker adapter registry",
        ),
        def_file_asset(
            "new_report_format_playbook",
            config_dir / "VIS_VRN_NewReport_Format_Playbook_v01.md",
            False,
            "Future report format playbook",
        ),
        def_file_asset(
            "primary_duckdb_current",
            primary_duckdb,
            True,
            "Primary DuckDB current state",
        ),
    ]

    governance_gates = [
        {
            "Status Lights": def_light("OK" if final_pass else "ERR"),
            "Gate": "FINAL_HANDOVER_PASS",
            "Value": "YES" if final_pass else "NO",
            "Severity": "OK" if final_pass else "ERR",
        },
        {
            "Status Lights": def_light("OK" if blocker_active else "ERR"),
            "Gate": "COMMIT_BLOCKER_ACTIVE",
            "Value": "YES" if blocker_active else "NO",
            "Severity": "OK" if blocker_active else "ERR",
        },
        {
            "Status Lights": def_light("OK" if commit_no else "ERR"),
            "Gate": "NO_COMMIT",
            "Value": "YES" if commit_no else "NO",
            "Severity": "OK" if commit_no else "ERR",
        },
        {
            "Status Lights": def_light("OK" if db_no else "ERR"),
            "Gate": "NO_DB_WRITE",
            "Value": "YES" if db_no else "NO",
            "Severity": "OK" if db_no else "ERR",
        },
        {
            "Status Lights": def_light("OK" if canonical_no else "ERR"),
            "Gate": "NO_CANONICAL_MUTATION",
            "Value": "YES" if canonical_no else "NO",
            "Severity": "OK" if canonical_no else "ERR",
        },
        {
            "Status Lights": def_light("OK" if ssot_no else "ERR"),
            "Gate": "NO_SSOT_MUTATION",
            "Value": "YES" if ssot_no else "NO",
            "Severity": "OK" if ssot_no else "ERR",
        },
        {
            "Status Lights": def_light("WARN"),
            "Gate": "REAL_COMMIT_UNLOCK_PHRASE",
            "Value": "YES FOR COMMIT",
            "Severity": "WARN",
        },
    ]

    future_flow = [
        {
            "Status Lights": def_light("OK"),
            "Flow": "New Report Intake",
            "Step": "Compatibility Gate",
            "Description": "Unknown broker or new layout must enter staging queue first.",
            "Mutation": "NO",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Flow": "Data Validation",
            "Step": "Table / Cell / Official Validation",
            "Description": "No canonical write until validation matrix passes.",
            "Mutation": "NO",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Flow": "Alias Governance",
            "Step": "Second Confirmation",
            "Description": "Alias candidates are not allowed to patch SSOT automatically.",
            "Mutation": "NO",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Flow": "Commit",
            "Step": "Manual Phrase Gate",
            "Description": "Only exact phrase YES FOR COMMIT unlocks real DB mutation script generation.",
            "Mutation": "BLOCKED",
            "Severity": "WARN",
        },
    ]

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

    recovery_playbook = run_dir / "VRN_RECOVERY_ROLLBACK_GOVERNANCE_PLAYBOOK_v0615703.md"
    recovery_playbook.write_text(def_build_recovery_playbook(primary_duckdb), encoding="utf-8")

    readonly_launcher = run_dir / "Invoke_VRN_ReadOnly_Ops_Launcher_v0615703.ps1"
    readonly_launcher.write_text(def_build_readonly_launcher(run_dir, registry_rows), encoding="utf-8")

    master_registry_json = run_dir / "VRN_MASTER_GOVERNANCE_REGISTRY_v0615703.json"
    master_registry_csv = run_dir / "VRN_MASTER_GOVERNANCE_REGISTRY_v0615703.csv"

    outputs = {
        "html": str(run_dir / "VRN_Final_Integration_Governance_Seal_v0615703.html"),
        "json": str(run_dir / "vrn_final_integration_governance_seal_v0615703.json"),
        "registry_csv": str(master_registry_csv),
        "registry_json": str(master_registry_json),
        "supportive_assets_csv": str(run_dir / "vrn_supportive_and_compatibility_assets_v0615703.csv"),
        "governance_gates_csv": str(run_dir / "vrn_governance_gates_v0615703.csv"),
        "future_flow_csv": str(run_dir / "vrn_future_new_report_flow_v0615703.csv"),
        "hard_rules_csv": str(run_dir / "vrn_final_integration_hard_rules_v0615703.csv"),
        "recovery_playbook": str(recovery_playbook),
        "readonly_launcher": str(readonly_launcher),
    }

    def_write_csv(master_registry_csv, registry_rows)
    def_write_csv(Path(outputs["supportive_assets_csv"]), supportive_assets)
    def_write_csv(Path(outputs["governance_gates_csv"]), governance_gates)
    def_write_csv(Path(outputs["future_flow_csv"]), future_flow)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)

    registry_obj = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "run_root": str(run_root),
        "primary_duckdb": str(primary_duckdb),
        "registry_rows": registry_rows,
        "supportive_assets": supportive_assets,
        "governance_gates": governance_gates,
        "future_flow": future_flow,
        "hard_rules": hard_rules,
        "outputs": outputs,
    }
    def_write_json(master_registry_json, registry_obj)

    all_required_registry_ok = all(r["Severity"] == "OK" for r in registry_rows)
    governance_ok = all(r["Severity"] in ["OK", "WARN"] for r in governance_gates)
    hard_rules_ok = all(r["Severity"] in ["OK", "WARN"] for r in hard_rules)

    final_pass = (
        final_pass
        and blocker_active
        and commit_no
        and db_no
        and canonical_no
        and ssot_no
        and all_required_registry_ok
        and governance_ok
        and hard_rules_ok
    )

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Reports Integrated": len(registry_rows),
        "Registry OK": "YES" if all_required_registry_ok else "NO",
        "Governance OK": "YES" if governance_ok else "NO",
        "Commit Blocker": "ACTIVE" if blocker_active else "MISSING",
        "Commit": "NO",
        "DB Write": "NO",
        "Canonical": "NO",
        "SSOT": "NO",
        "Approval Phrase": "YES FOR COMMIT",
    }

    overview = [
        {
            "Status Lights": def_light("OK" if final_pass else "WARN"),
            "Gate": "FINAL_INTEGRATION_GOVERNANCE_PASS",
            "Value": "YES" if final_pass else "REVIEW",
            "Severity": "OK" if final_pass else "WARN",
        },
        {
            "Status Lights": def_light("OK" if all_required_registry_ok else "ERR"),
            "Gate": "ALL_REQUIRED_REPORTS_INDEXED",
            "Value": "YES" if all_required_registry_ok else "NO",
            "Severity": "OK" if all_required_registry_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if blocker_active else "ERR"),
            "Gate": "COMMIT_BLOCKER_ACTIVE",
            "Value": "YES" if blocker_active else "NO",
            "Severity": "OK" if blocker_active else "ERR",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "NO_COMMIT",
            "Value": "YES",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "NO_DB_WRITE",
            "Value": "YES",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "NO_SSOT_MUTATION",
            "Value": "YES",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Gate": "REAL_COMMIT_REQUIRES",
            "Value": "YES FOR COMMIT",
            "Severity": "WARN",
        },
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview),
            ("02 Governance Gates", governance_gates),
            ("03 Master Report Registry", registry_rows),
            ("04 Supportive / Compatibility Assets", supportive_assets),
            ("05 Future New Report Flow", future_flow),
            ("06 Hard Rules", hard_rules),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


# ==================================================================================================
# def 04_ENTRYPOINT
# ==================================================================================================
if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise