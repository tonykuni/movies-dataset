# -*- coding: utf-8 -*-
from __future__ import annotations

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


VERSION = "VRN_FINAL_CONTROL_CENTER_V061575"


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
    if s in ["OK", "PASS", "YES", "SEALED", "READY", "FOUND", "PRODUCTION_READY"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "OPTIONAL", "MANUAL"]:
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


def def_asset(label: str, path: Path, role: str, required: bool = True) -> dict:
    exists = path.exists()
    sev = "OK" if exists else ("ERR" if required else "WARN")

    return {
        "Status Lights": def_light(sev),
        "Asset": label,
        "Role": role,
        "Path": str(path),
        "Exists": "YES" if exists else "NO",
        "SHA256": def_sha256_file(path),
        "Required": "YES" if required else "NO",
        "Severity": sev,
    }


# ==================================================================================================
# def 01_HTML
# ==================================================================================================
def def_html_table(title: str, rows: list[dict], limit: int | None = None) -> str:
    if limit is not None:
        rows = rows[:limit]

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
        sev = str(r.get("Severity", "OK")).upper()
        tr_cls = "warnrow" if sev == "WARN" else ("errrow" if sev == "ERR" else "")
        tds: list[str] = []

        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["path", "asset", "role", "rule", "reason", "next", "flow", "description", "html", "json", "sha"]) else "center"
            safe_v = html.escape(str(v)).replace(chr(10), "<br>")
            tds.append(f"<td class='{cls}'>{safe_v}</td>")

        trs.append(f"<tr class='{tr_cls}'>" + "".join(tds) + "</tr>")

    return (
        f"<section class='card'>"
        f"<h2>{html.escape(title)}</h2>"
        f"<div class='table-wrap'>"
        f"<table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table>"
        f"</div></section>"
    )


def def_write_control_center_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:30px 38px;background:linear-gradient(135deg,#0d1b2f,#102a43);border-bottom:1px solid #1f3557}
h1{margin:0;font-size:28px;letter-spacing:.2px}.sub{color:#9fb3c8;margin-top:10px;font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(185px,1fr));gap:14px;padding:22px 34px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.18)}
.v{font-size:25px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 34px 34px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:18px;margin:18px 0;box-shadow:0 10px 28px rgba(0,0,0,.14)}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;z-index:2}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1500px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
.warnrow{background:rgba(255,209,102,.08)}
.errrow{background:rgba(255,80,80,.10)}
.footer{padding:20px 34px;color:#9fb3c8}
a{color:#9fd3ff;text-decoration:none}
a:hover{text-decoration:underline}
"""
    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    )

    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)

    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>VRN Production Home v061575</title>
<style>{css}</style>
</head>
<body>
<header>
<h1>VRN · Production Home + Future Compatibility Gate v0.6.15.7.5</h1>
<div class="sub">production sealed · future reports must enter compatibility gate · read-only control center · no DB write in this run</div>
</header>
<div class="grid">{cards}</div>
<main>{body}</main>
<div class="footer">Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</div>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


def def_build_launcher(path: Path, assets: list[dict]) -> None:
    lines = [
        "& {",
        "    # def VRN Production ReadOnly Launcher v0.6.15.7.5",
        "    # def Opens final VRN reports and future compatibility assets only.",
        "    # def No DB write / no canonical mutation / no SSOT mutation.",
        "    $ErrorActionPreference = 'Continue'",
        "    Write-Host 'VRN Production ReadOnly Launcher · No DB Write' -ForegroundColor Cyan",
        "",
    ]

    for a in assets:
        p = str(a.get("Path", ""))
        label = str(a.get("Asset", ""))
        if p and Path(p).exists() and p.lower().endswith((".html", ".md", ".json", ".csv")):
            p2 = p.replace("'", "''")
            label2 = label.replace("'", "''")
            lines.append(f"    Write-Host '[OPEN] {label2}' -ForegroundColor Green")
            lines.append(f"    Start-Process '{p2}'")
            lines.append("")

    lines.extend([
        "    Write-Host 'PowerShell session remains open.' -ForegroundColor DarkGray",
        "}",
    ])

    path.write_text("\n".join(lines), encoding="utf-8")


def def_build_future_intake_playbook(path: Path, target_table: str) -> None:
    lines = [
        "# VRN Future New Report Intake Playbook v0.6.15.7.5",
        "",
        "## Final Production State",
        f"- Canonical table: `{target_table}`",
        "- Current VRN state: PRODUCTION SEALED",
        "- New reports must not bypass Compatibility Gate.",
        "",
        "## Required Flow",
        "1. New Report enters Compatibility Gate.",
        "2. Broker / format / layout is checked by Adapter Registry.",
        "3. Unknown broker or unknown layout goes to staging queue.",
        "4. Extract BasicInfo / FinancialData in staging only.",
        "5. Run table / cell / official validation.",
        "6. Run business validation report.",
        "7. Build commit candidate pack.",
        "8. Manual approval required before DB mutation.",
        "9. Run production commit only after approval.",
        "10. Run post-commit read-only audit.",
        "",
        "## Hard Rules",
        "- Unknown broker / new layout = staging only.",
        "- Alias candidates = no SSOT patch until second-confirmation.",
        "- OCR = targeted only, never default.",
        "- Canonical write = only after validation pass.",
        "- Rollback = only if business owner rejects committed rows.",
        "- Existing production-sealed rows must not be silently overwritten.",
        "",
        "## What Not To Do",
        "- Do not patch SSOT directly from alias candidates.",
        "- Do not write to DuckDB during discovery.",
        "- Do not run rollback unless business owner rejects committed data.",
        "- Do not downgrade the production seal without a written reason.",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# ==================================================================================================
# def 02_MAIN
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 8:
        raise SystemExit("usage: py <run_root> <run_dir> <primary_duckdb> <target_table> <supportive_dir> <config_dir> <via_root>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    primary_duckdb = Path(sys.argv[3])
    target_table = sys.argv[4]
    supportive_dir = Path(sys.argv[5])
    config_dir = Path(sys.argv[6])
    via_root = Path(sys.argv[7])
    run_dir.mkdir(parents=True, exist_ok=True)

    # ----------------------------------------------------------------------------------------------
    # def Locate latest final reports
    # ----------------------------------------------------------------------------------------------
    business_run = def_find_latest_dir(run_root, ["VRN_BUSINESS_VALIDATION_REPORT_V061574"])
    production_run = def_find_latest_dir(run_root, ["VRN_FINAL_PRODUCTION_LOCK_REGISTRY_V061573"])
    post_commit_run = def_find_latest_dir(run_root, ["VRN_POST_COMMIT_PRODUCTION_SEAL_V0615721"])
    commit_run = def_find_latest_dir(run_root, ["VRN_REAL_COMMIT_ARGFIX_BACKUP_POSTCHECK_V0615711"])
    governance_run = def_find_latest_dir(run_root, ["VRN_FINAL_INTEGRATION_GOVERNANCE_SEAL_V0615703"])
    handover_run = def_find_latest_dir(run_root, ["VRN_FINAL_HANDOVER_COMMIT_BLOCKER_SEAL_V0615702"])

    if not business_run:
        raise RuntimeError("Missing v061574 business validation report. Run business validation before final home.")
    if not production_run:
        raise RuntimeError("Missing v061573 production lock registry.")

    business_json = def_read_json(business_run / "vrn_financialdata_business_validation_report_v061574.json")
    production_json = def_read_json(production_run / "vrn_final_production_lock_registry_v061573.json")
    post_json = def_read_json(post_commit_run / "vrn_post_commit_production_seal_v0615721.json") if post_commit_run else {}
    commit_json = def_read_json(commit_run / "vrn_real_commit_argfix_backup_postcheck_rollback_v0615711.json") if commit_run else {}

    business_counts = business_json.get("counts", {})
    production_counts = production_json.get("counts", {})
    post_counts = post_json.get("counts", {})
    commit_counts = commit_json.get("counts", {})
    commit_outputs = commit_json.get("outputs", {})

    backup_db = Path(commit_outputs.get("backup_db", ""))
    rollback_script = Path(commit_outputs.get("rollback_script", ""))
    sealed_rollback_sql = Path(commit_outputs.get("sealed_rollback_sql", ""))

    production_ready = (
        production_counts.get("Final") == "PASS"
        and production_counts.get("Production Ready") == "YES"
        and str(production_counts.get("Committed Rows")) == "27"
        and production_counts.get("Duplicate PK") == "PASS"
        and production_counts.get("Schema") == "PASS"
        and production_counts.get("Backup") == "YES"
        and production_counts.get("Rollback Script") == "YES"
        and production_counts.get("SSOT Mutation") == "NO"
    )

    business_ready = (
        business_counts.get("Final") == "PASS"
        and str(business_counts.get("Rows")) == "27"
        and str(business_counts.get("Expected")) == "27"
        and str(business_counts.get("Review Rows")) == "0"
        and str(business_counts.get("ERR Rows")) == "0"
        and str(business_counts.get("WARN Rows")) == "0"
        and business_counts.get("DB Write") == "NO"
        and business_counts.get("SSOT") == "NO"
    )

    primary_sha = def_sha256_file(primary_duckdb)

    # ----------------------------------------------------------------------------------------------
    # def Assets
    # ----------------------------------------------------------------------------------------------
    assets = [
        def_asset("Business Validation HTML", business_run / "VRN_FinancialData_Business_Validation_Report_v061574.html", "Final 27-row business validation", True),
        def_asset("Business Validation JSON", business_run / "vrn_financialdata_business_validation_report_v061574.json", "Final business validation data", True),
        def_asset("Production Lock HTML", production_run / "VRN_Final_Production_Lock_Registry_v061573.html", "Final production seal", True),
        def_asset("Production Lock JSON", production_run / "vrn_final_production_lock_registry_v061573.json", "Final production seal data", True),
        def_asset("Post Commit Production Seal HTML", post_commit_run / "VRN_PostCommit_Production_Seal_v0615721.html" if post_commit_run else Path(""), "Read-only post-commit proof", True),
        def_asset("Real Commit HTML", commit_run / "VRN_Real_Commit_ArgFix_Backup_Postcheck_Rollback_v0615711.html" if commit_run else Path(""), "Real commit proof", True),
        def_asset("Pre-Commit Backup DB", backup_db, "Backup for rollback", True),
        def_asset("Rollback Script", rollback_script, "Manual rollback only if business owner rejects committed rows", True),
        def_asset("Sealed Rollback SQL", sealed_rollback_sql, "Row-level rollback SQL evidence", True),
        def_asset("Primary DuckDB", primary_duckdb, "Production database", True),
        def_asset("New Report Compatibility Gate", supportive_dir / "VIS_VRN_NewReportCompatibilityGate_v01.py", "Future format gate", False),
        def_asset("Adapter Registry", config_dir / "VIS_VRN_AdapterRegistry_v01.json", "Future broker/layout adapter registry", False),
        def_asset("New Report Format Playbook", config_dir / "VIS_VRN_NewReport_Format_Playbook_v01.md", "Future report playbook", False),
        def_asset("Supportive Module Index HTML", supportive_dir / "VIS_Supportive_Module_Index.html", "Supportive module registry", False),
        def_asset("Final Integration Governance HTML", governance_run / "VRN_Final_Integration_Governance_Seal_v0615703.html" if governance_run else Path(""), "Final governance", False),
        def_asset("Final Handover HTML", handover_run / "VRN_Final_Handover_Commit_Blocker_Seal_v0615702.html" if handover_run else Path(""), "Final handover", False),
    ]

    # ----------------------------------------------------------------------------------------------
    # def Gates
    # ----------------------------------------------------------------------------------------------
    gates = [
        {"Status Lights": def_light("OK" if production_ready else "ERR"), "Gate": "PRODUCTION_READY", "Value": "YES" if production_ready else "NO", "Severity": "OK" if production_ready else "ERR"},
        {"Status Lights": def_light("OK" if business_ready else "ERR"), "Gate": "BUSINESS_VALIDATION_READY", "Value": "YES" if business_ready else "NO", "Severity": "OK" if business_ready else "ERR"},
        {"Status Lights": def_light("OK"), "Gate": "COMMITTED_ROWS", "Value": production_counts.get("Committed Rows", ""), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "BUSINESS_ROWS", "Value": business_counts.get("Rows", ""), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "REVIEW_ROWS", "Value": business_counts.get("Review Rows", ""), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "ERR_ROWS", "Value": business_counts.get("ERR Rows", ""), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "WARN_ROWS", "Value": business_counts.get("WARN Rows", ""), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "ROLLBACK_REQUIRED", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "DB_WRITE_THIS_RUN", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SSOT_MUTATION_THIS_RUN", "Value": "NO", "Severity": "OK"},
    ]

    # ----------------------------------------------------------------------------------------------
    # def Future Flow
    # ----------------------------------------------------------------------------------------------
    future_flow = [
        {"Status Lights": def_light("OK"), "Flow": "01 New Report", "Rule": "New report enters Compatibility Gate first", "Mutation": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Flow": "02 Adapter Registry", "Rule": "Broker/layout must be known or staged", "Mutation": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Flow": "03 Staging Extraction", "Rule": "Unknown format stays staging only", "Mutation": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Flow": "04 Validation", "Rule": "Table/cell/official/business validation required", "Mutation": "NO", "Severity": "OK"},
        {"Status Lights": def_light("WARN"), "Flow": "05 Commit Candidate", "Rule": "Manual approval required before DB write", "Mutation": "BLOCKED UNTIL APPROVED", "Severity": "WARN"},
        {"Status Lights": def_light("OK"), "Flow": "06 Post-Commit Audit", "Rule": "Read-only audit after real commit", "Mutation": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Flow": "07 SSOT", "Rule": "Alias candidates require second-confirmation", "Mutation": "NO AUTO PATCH", "Severity": "OK"},
    ]

    hard_rules = [
        {"Status Lights": def_light("OK"), "Rule": "STOP_VRN_REPAIR", "Value": "YES", "Reason": "VRN is production sealed.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "ROLLBACK_REQUIRED", "Value": "NO", "Reason": "Business validation has zero ERR/WARN/review rows.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_SSOT_PATCH", "Value": "YES", "Reason": "SSOT mutation not needed.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "FUTURE_REPORT_GATE_FIRST", "Value": "YES", "Reason": "Prevent new layout from polluting canonical table.", "Severity": "OK"},
        {"Status Lights": def_light("WARN"), "Rule": "ROLLBACK_ONLY_IF_REJECTED", "Value": "MANUAL ONLY", "Reason": "Rollback is insurance, not a current task.", "Severity": "WARN"},
    ]

    next_steps = [
        {"Status Lights": def_light("OK"), "Next Step": "Stop VRN repair work.", "Reason": "Production and business validation are sealed.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Next Step": "Use VRN_PRODUCTION_HOME.html as final entry point.", "Reason": "It centralizes reports, rollback, future-gate policy.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Next Step": "Move next active work to VDF / VAP / supportive_module.", "Reason": "VRN is complete.", "Severity": "OK"},
        {"Status Lights": def_light("WARN"), "Next Step": "For future report formats, never bypass Compatibility Gate.", "Reason": "Preserve canonical quality.", "Severity": "WARN"},
    ]

    # ----------------------------------------------------------------------------------------------
    # def Output files
    # ----------------------------------------------------------------------------------------------
    production_home = run_dir / "VRN_PRODUCTION_HOME_v061575.html"
    production_json = run_dir / "vrn_production_home_v061575.json"
    production_registry_csv = run_dir / "vrn_production_home_registry_v061575.csv"
    future_playbook = run_dir / "VRN_FUTURE_REPORT_COMPATIBILITY_GATE_PLAYBOOK_v061575.md"
    readonly_launcher = run_dir / "Invoke_VRN_Production_ReadOnly_Launcher_v061575.ps1"

    def_build_future_intake_playbook(future_playbook, target_table)
    assets.append(def_asset("Future Report Compatibility Gate Playbook v061575", future_playbook, "Future intake policy", True))

    def_build_launcher(readonly_launcher, assets)
    assets.append(def_asset("VRN Production ReadOnly Launcher v061575", readonly_launcher, "One-click read-only launcher", True))

    assets_ok = all(a["Severity"] in ["OK", "WARN"] for a in assets)
    gates_ok = all(g["Severity"] in ["OK", "WARN"] for g in gates)
    final_pass = production_ready and business_ready and assets_ok and gates_ok

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "VRN Status": "PRODUCTION SEALED" if final_pass else "REVIEW",
        "Committed Rows": production_counts.get("Committed Rows", ""),
        "Business Rows": business_counts.get("Rows", ""),
        "Review Rows": business_counts.get("Review Rows", ""),
        "ERR Rows": business_counts.get("ERR Rows", ""),
        "WARN Rows": business_counts.get("WARN Rows", ""),
        "Rollback Required": "NO",
        "Future Gate": "ON",
        "DB Write This Run": "NO",
        "SSOT Mutation": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "ERR"), "Gate": "VRN_FINAL_CONTROL_CENTER_PASS", "Value": "YES" if final_pass else "NO", "Severity": "OK" if final_pass else "ERR"},
        {"Status Lights": def_light("OK" if production_ready else "ERR"), "Gate": "PRODUCTION_READY", "Value": "YES" if production_ready else "NO", "Severity": "OK" if production_ready else "ERR"},
        {"Status Lights": def_light("OK" if business_ready else "ERR"), "Gate": "BUSINESS_VALIDATION_READY", "Value": "YES" if business_ready else "NO", "Severity": "OK" if business_ready else "ERR"},
        {"Status Lights": def_light("OK"), "Gate": "ROLLBACK_REQUIRED", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "FUTURE_GATE_POLICY", "Value": "ON", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "DB_WRITE_THIS_RUN", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SSOT_MUTATION_THIS_RUN", "Value": "NO", "Severity": "OK"},
    ]

    outputs = {
        "html": str(production_home),
        "json": str(production_json),
        "registry_csv": str(production_registry_csv),
        "assets_csv": str(run_dir / "vrn_control_center_assets_v061575.csv"),
        "gates_csv": str(run_dir / "vrn_control_center_gates_v061575.csv"),
        "future_flow_csv": str(run_dir / "vrn_future_report_flow_v061575.csv"),
        "hard_rules_csv": str(run_dir / "vrn_final_hard_rules_v061575.csv"),
        "next_steps_csv": str(run_dir / "vrn_final_next_steps_v061575.csv"),
        "future_playbook": str(future_playbook),
        "readonly_launcher": str(readonly_launcher),
    }

    def_write_csv(Path(outputs["registry_csv"]), assets)
    def_write_csv(Path(outputs["assets_csv"]), assets)
    def_write_csv(Path(outputs["gates_csv"]), gates)
    def_write_csv(Path(outputs["future_flow_csv"]), future_flow)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "primary_duckdb": str(primary_duckdb),
        "primary_sha_now": primary_sha,
        "target_table": target_table,
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(production_json, result)
    def_write_control_center_html(
        production_home,
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Final Gates", gates, None),
            ("03 Production / Rollback / Report Assets", assets, None),
            ("04 Future New Report Compatibility Flow", future_flow, None),
            ("05 Hard Rules", hard_rules, None),
            ("06 Next Steps", next_steps, None),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


# ==================================================================================================
# def 03_ENTRYPOINT
# ==================================================================================================
if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise