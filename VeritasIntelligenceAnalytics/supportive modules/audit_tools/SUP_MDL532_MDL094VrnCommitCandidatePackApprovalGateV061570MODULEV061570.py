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
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_COMMIT_CANDIDATE_PACK_APPROVAL_GATE_V061570"


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
    if s in ["OK", "PASS", "YES", "READY", "SEALED", "APPROVAL_READY"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "APPROVAL_REQUIRED", "LOCKED_OUT", "PACK_ONLY"]:
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
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


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


def def_file_row(label: str, path: Path, severity: str = "OK") -> dict:
    exists = path.exists()
    return {
        "Status Lights": def_light(severity if exists else "ERR"),
        "asset": label,
        "path": str(path),
        "exists": "YES" if exists else "NO",
        "sha256": def_sha256_file(path) if exists and path.is_file() else "",
        "Severity": severity if exists else "ERR",
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
            cls = "left" if any(x in k.lower() for x in ["path", "file", "sql", "reason", "step", "approval", "risk", "asset", "source"]) else "center"
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
.badge{display:inline-block;padding:4px 8px;border-radius:999px;background:#1f3557}
"""
    cards = "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    )
    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN Commit Candidate Pack Approval Gate v061570</title><style>{css}</style></head>
<body><header><h1>VRN · Commit Candidate Pack + Manual Approval Gate v0.6.15.7.0</h1>
<div class="sub">approval package only · no commit · no DB write · no canonical / SSOT mutation</div></header>
<div class="grid">{cards}</div><main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_build_real_commit_script_spec(target_table: str) -> str:
    return f"""# VRN Real Commit Script Specification - NOT EXECUTABLE IN THIS RUN

Required explicit approval phrase:
YES FOR COMMIT

Mandatory runtime checks:
1. Recompute primary DB SHA256 before commit.
2. Confirm it matches the SHA from v0615699 final primary DB state.
3. Create fresh backup in commit run directory.
4. Open DuckDB connection.
5. BEGIN TRANSACTION.
6. Execute CREATE TABLE IF NOT EXISTS {target_table}.
7. Execute exactly 27 INSERT statements from sealed SQL plan.
8. Verify inserted row count = 27.
9. Verify duplicate vrn_pk = 0.
10. COMMIT only after all gates pass.
11. Write post-commit SHA256.
12. Write rollback SQL and backup path into report.
13. Do not touch SSOT.
14. Do not include quarantine rows.
15. Do not include alias candidate rows.

Forbidden:
- No auto-commit before checks.
- No SSOT alias patch.
- No OCR.
- No restore of rejected rows.
- No delete except rollback script/manual recovery.
"""


def def_main() -> None:
    if len(sys.argv) < 5:
        raise SystemExit("usage: py <run_root> <run_dir> <primary_duckdb> <target_table>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    primary_duckdb = Path(sys.argv[3])
    target_table = sys.argv[4]
    run_dir.mkdir(parents=True, exist_ok=True)

    txn_run = def_find_latest_dir(run_root, ["VRN_PRIMARY_DB_TRANSACTION_ROLLBACK_DRYRUN_V0615699"])
    sim_run = def_find_latest_dir(run_root, ["VRN_WRITE_SIMULATOR_ROLLBACK_PLAN_V0615696"])
    seal_run = def_find_latest_dir(run_root, ["VRN_MISSING_LINK_FINAL_STAGING_SEAL_V0615695"])
    schema_run = def_find_latest_dir(run_root, ["VRN_DB_SCHEMA_COMPATIBILITY_AUDIT_V06156971"])
    staging_copy_run = def_find_latest_dir(run_root, ["VRN_STAGING_COPY_WRITE_DRYRUN_ROLLBACK_V06156981"])

    if not txn_run:
        raise RuntimeError("Missing prerequisite: v0615699 primary transaction rollback dry-run.")
    if not sim_run:
        raise RuntimeError("Missing prerequisite: v0615696 write simulator.")
    if not seal_run:
        raise RuntimeError("Missing prerequisite: v0615695 final staging seal.")
    if not primary_duckdb.exists():
        raise RuntimeError(f"Primary DuckDB not found: {primary_duckdb}")

    txn_json = def_read_json(txn_run / "vrn_primary_db_transaction_rollback_dryrun_v0615699.json")
    sim_json = def_read_json(sim_run / "vrn_write_simulator_rollback_plan_v0615696.json")
    seal_json = def_read_json(seal_run / "vrn_missing_link_final_staging_seal_v0615695.json")

    write_ready = [
        r for r in def_read_csv(seal_run / "vrn_write_ready_plan_only_rows_v0615695.csv")
        if "empty_marker" not in r
    ]
    quarantine = [
        r for r in def_read_csv(seal_run / "vrn_quarantine_v0615695.csv")
        if "empty_marker" not in r
    ]
    alias = [
        r for r in def_read_csv(seal_run / "vrn_alias_candidates_no_ssot_v0615695.csv")
        if "empty_marker" not in r
    ]
    no_match = [
        r for r in def_read_csv(seal_run / "vrn_no_match_v0615695.csv")
        if "empty_marker" not in r
    ]

    insert_sql_src = sim_run / "vrn_write_simulation_insert_plan_v0615696.sql"
    rollback_sql_src = sim_run / "vrn_write_simulation_rollback_plan_v0615696.sql"
    simulation_rows_src = sim_run / "vrn_write_simulation_rows_v0615696.csv"
    backup_db = Path(str(txn_json.get("outputs", {}).get("backup_db", ""))) if txn_json.get("outputs") else Path("")

    sealed_insert_sql = run_dir / "SEALED_COMMIT_CANDIDATE_insert_plan_v061570.sql"
    sealed_rollback_sql = run_dir / "SEALED_COMMIT_CANDIDATE_rollback_plan_v061570.sql"
    sealed_write_ready_csv = run_dir / "SEALED_COMMIT_CANDIDATE_write_ready_rows_v061570.csv"
    sealed_real_commit_spec = run_dir / "SEALED_REAL_COMMIT_SCRIPT_SPEC_v061570.md"

    shutil.copy2(insert_sql_src, sealed_insert_sql)
    shutil.copy2(rollback_sql_src, sealed_rollback_sql)
    def_write_csv(sealed_write_ready_csv, write_ready)
    sealed_real_commit_spec.write_text(def_build_real_commit_script_spec(target_table), encoding="utf-8")

    primary_sha_now = def_sha256_file(primary_duckdb)

    txn_counts = txn_json.get("counts", {})
    seal_counts = seal_json.get("counts", {})
    sim_counts = sim_json.get("counts", {})

    prereq_rows = [
        {"Status Lights": def_light("OK" if txn_json.get("system_pass") else "ERR"), "Prerequisite": "v0615699 primary transaction rollback dry-run", "Value": "PASS" if txn_json.get("system_pass") else "FAIL", "Path": str(txn_run), "Severity": "OK" if txn_json.get("system_pass") else "ERR"},
        {"Status Lights": def_light("OK" if sim_json.get("system_pass") else "ERR"), "Prerequisite": "v0615696 write simulator", "Value": "PASS" if sim_json.get("system_pass") else "FAIL", "Path": str(sim_run), "Severity": "OK" if sim_json.get("system_pass") else "ERR"},
        {"Status Lights": def_light("OK" if seal_json.get("system_pass") else "ERR"), "Prerequisite": "v0615695 final staging seal", "Value": "PASS" if seal_json.get("system_pass") else "FAIL", "Path": str(seal_run), "Severity": "OK" if seal_json.get("system_pass") else "ERR"},
        {"Status Lights": def_light("OK" if staging_copy_run else "WARN"), "Prerequisite": "v06156981 staging copy dry-run", "Value": "FOUND" if staging_copy_run else "NOT_FOUND", "Path": str(staging_copy_run) if staging_copy_run else "", "Severity": "OK" if staging_copy_run else "WARN"},
        {"Status Lights": def_light("OK" if schema_run else "WARN"), "Prerequisite": "v06156971 schema audit", "Value": "FOUND" if schema_run else "NOT_FOUND", "Path": str(schema_run) if schema_run else "", "Severity": "OK" if schema_run else "WARN"},
    ]

    commit_assets = [
        def_file_row("sealed_insert_sql_plan", sealed_insert_sql, "OK"),
        def_file_row("sealed_rollback_sql_plan", sealed_rollback_sql, "OK"),
        def_file_row("sealed_write_ready_rows_csv", sealed_write_ready_csv, "OK"),
        def_file_row("sealed_real_commit_script_spec", sealed_real_commit_spec, "OK"),
        def_file_row("primary_duckdb_current", primary_duckdb, "OK"),
    ]
    if backup_db and str(backup_db) != ".":
        commit_assets.append(def_file_row("backup_db_from_v0615699", backup_db, "OK" if backup_db.exists() else "WARN"))

    hard_rules = [
        {"Status Lights": def_light("OK"), "Rule": "NO_COMMIT_IN_THIS_RUN", "Value": "YES", "Reason": "This is approval package only.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_DB_WRITE_IN_THIS_RUN", "Value": "YES", "Reason": "No DuckDB connection is opened by this pack builder.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_SSOT_MUTATION", "Value": "YES", "Reason": "Alias candidates stay separate.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "QUARANTINE_LOCKED_OUT", "Value": len(quarantine), "Reason": "Not eligible for canonical write.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "ALIAS_CANDIDATES_LOCKED_OUT", "Value": len(alias), "Reason": "No SSOT patch without second confirmation.", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Rule": "NO_MATCH_LOCKED_OUT", "Value": len(no_match), "Reason": "Not eligible for canonical write.", "Severity": "OK"},
        {"Status Lights": def_light("WARN"), "Rule": "REAL_COMMIT_REQUIRES_EXACT_PHRASE", "Value": "YES FOR COMMIT", "Reason": "No accidental mutation.", "Severity": "WARN"},
    ]

    approval_gate = [
        {"Status Lights": def_light("WARN"), "Approval Item": "Manual phrase required", "Required Value": "YES FOR COMMIT", "Current Status": "NOT_PROVIDED", "Severity": "WARN"},
        {"Status Lights": def_light("OK"), "Approval Item": "Write-ready rows", "Required Value": "27", "Current Status": str(len(write_ready)), "Severity": "OK" if len(write_ready) == 27 else "ERR"},
        {"Status Lights": def_light("OK" if txn_counts.get("Commit") == "NO" else "ERR"), "Approval Item": "Previous transaction commit", "Required Value": "NO", "Current Status": str(txn_counts.get("Commit", "")), "Severity": "OK" if txn_counts.get("Commit") == "NO" else "ERR"},
        {"Status Lights": def_light("OK" if txn_counts.get("Primary Final SHA OK") == "YES" else "ERR"), "Approval Item": "Primary final SHA OK", "Required Value": "YES", "Current Status": str(txn_counts.get("Primary Final SHA OK", "")), "Severity": "OK" if txn_counts.get("Primary Final SHA OK") == "YES" else "ERR"},
        {"Status Lights": def_light("OK" if txn_counts.get("Rollback") == "PASS" else "ERR"), "Approval Item": "Rollback dry-run", "Required Value": "PASS", "Current Status": str(txn_counts.get("Rollback", "")), "Severity": "OK" if txn_counts.get("Rollback") == "PASS" else "ERR"},
        {"Status Lights": def_light("OK" if sim_counts.get("Duplicate PK") == "PASS" else "ERR"), "Approval Item": "Duplicate PK", "Required Value": "PASS", "Current Status": str(sim_counts.get("Duplicate PK", "")), "Severity": "OK" if sim_counts.get("Duplicate PK") == "PASS" else "ERR"},
    ]

    next_steps = [
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Only if you explicitly type YES FOR COMMIT, generate v0.6.15.7.1 real commit script.",
            "Reason": "v0.6.15.7.0 produced approval pack only and did not mutate DB.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Before real commit, re-check primary DB SHA equals current approval pack SHA.",
            "Reason": "Avoid committing onto changed DB state.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Keep quarantine / alias / no-match excluded.",
            "Reason": "They are explicitly outside the write-ready pack.",
            "Severity": "OK",
        },
    ]

    all_prereq_ok = all(r.get("Severity") == "OK" for r in prereq_rows[:3])
    approval_ready = (
        all_prereq_ok
        and len(write_ready) == 27
        and txn_counts.get("Commit") == "NO"
        and txn_counts.get("Primary Final SHA OK") == "YES"
        and txn_counts.get("Rollback") == "PASS"
        and sim_counts.get("Duplicate PK") == "PASS"
    )

    counts = {
        "Final": "PASS" if approval_ready else "REVIEW",
        "Approval Ready": "YES" if approval_ready else "NO",
        "Write Ready Rows": len(write_ready),
        "Quarantine Locked": len(quarantine),
        "Alias Locked": len(alias),
        "No Match Locked": len(no_match),
        "Previous Rollback": txn_counts.get("Rollback", ""),
        "Previous Commit": txn_counts.get("Commit", ""),
        "Primary SHA Now": primary_sha_now[:12],
        "Commit This Run": "NO",
        "DB Write This Run": "NO",
        "SSOT Mutation": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if approval_ready else "WARN"), "Gate": "COMMIT_CANDIDATE_PACK_PASS", "Value": "YES" if approval_ready else "REVIEW", "Severity": "OK" if approval_ready else "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "WRITE_READY_ROWS", "Value": len(write_ready), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SEALED_INSERT_SQL", "Value": str(sealed_insert_sql), "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SEALED_ROLLBACK_SQL", "Value": str(sealed_rollback_sql), "Severity": "OK"},
        {"Status Lights": def_light("WARN"), "Gate": "MANUAL_APPROVAL_REQUIRED", "Value": "YES FOR COMMIT", "Severity": "WARN"},
        {"Status Lights": def_light("OK"), "Gate": "COMMIT_THIS_RUN", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "DB_WRITE_THIS_RUN", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SSOT_MUTATION", "Value": "NO", "Severity": "OK"},
    ]

    outputs = {
        "html": str(run_dir / "VRN_Commit_Candidate_Pack_Approval_Gate_v061570.html"),
        "json": str(run_dir / "vrn_commit_candidate_pack_approval_gate_v061570.json"),
        "prereq_csv": str(run_dir / "vrn_commit_prerequisites_v061570.csv"),
        "approval_gate_csv": str(run_dir / "vrn_manual_approval_gate_v061570.csv"),
        "commit_assets_csv": str(run_dir / "vrn_commit_assets_manifest_v061570.csv"),
        "hard_rules_csv": str(run_dir / "vrn_commit_hard_rules_v061570.csv"),
        "next_steps_csv": str(run_dir / "vrn_commit_next_steps_v061570.csv"),
        "sealed_insert_sql": str(sealed_insert_sql),
        "sealed_rollback_sql": str(sealed_rollback_sql),
        "sealed_write_ready_csv": str(sealed_write_ready_csv),
        "sealed_real_commit_spec": str(sealed_real_commit_spec),
    }

    def_write_csv(Path(outputs["prereq_csv"]), prereq_rows)
    def_write_csv(Path(outputs["approval_gate_csv"]), approval_gate)
    def_write_csv(Path(outputs["commit_assets_csv"]), commit_assets)
    def_write_csv(Path(outputs["hard_rules_csv"]), hard_rules)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": approval_ready,
        "primary_duckdb": str(primary_duckdb),
        "primary_sha_now": primary_sha_now,
        "target_table": target_table,
        "source_runs": {
            "txn_run": str(txn_run),
            "sim_run": str(sim_run),
            "seal_run": str(seal_run),
            "schema_run": str(schema_run) if schema_run else "",
            "staging_copy_run": str(staging_copy_run) if staging_copy_run else "",
        },
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Prerequisites", prereq_rows, None),
            ("03 Manual Approval Gate", approval_gate, None),
            ("04 Commit Assets Manifest", commit_assets, None),
            ("05 Hard Rules", hard_rules, None),
            ("06 Next Steps", next_steps, None),
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