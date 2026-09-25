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
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_REAL_COMMIT_BACKUP_POSTCHECK_ROLLBACK_V061571"


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
    if s in ["OK", "PASS", "YES", "COMMITTED", "BACKUP_OK", "POSTCHECK_OK"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "APPROVAL_REQUIRED", "ROLLBACK_READY"]:
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


def def_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_strip_sql_comments(text: str) -> str:
    return "\n".join([line for line in text.splitlines() if not line.strip().startswith("--")])


def def_split_sql_statements(text: str) -> list[str]:
    text = def_strip_sql_comments(text)
    out: list[str] = []
    buf: list[str] = []
    in_single = False
    i = 0

    while i < len(text):
        ch = text[i]

        if ch == "'":
            buf.append(ch)
            if i + 1 < len(text) and text[i + 1] == "'":
                buf.append(text[i + 1])
                i += 2
                continue
            in_single = not in_single
            i += 1
            continue

        if ch == ";" and not in_single:
            stmt = "".join(buf).strip()
            if stmt:
                out.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    last = "".join(buf).strip()
    if last:
        out.append(last)

    return out


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


def def_sql_quote(x: str) -> str:
    return "'" + str(x).replace("'", "''") + "'"


# ==================================================================================================
# def 01_HTML_RENDERING
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
        tds: list[str] = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["path", "sql", "error", "reason", "next", "sha", "file", "script"]) else "center"
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


def def_write_html(path: Path, counts: dict, sections: list[tuple[str, list[dict], int | None]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:28px 36px;background:#2b0f12;border-bottom:1px solid #7f1d1d}
h1{margin:0;font-size:26px}.sub{color:#ffd6d6;margin-top:8px}
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

    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)

    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>VRN Real Commit v061571</title>
<style>{css}</style>
</head>
<body>
<header>
<h1>VRN · Real Commit With Backup + Postcheck + Rollback Pack v0.6.15.7.1</h1>
<div class="sub">real DB write after explicit YES FOR COMMIT · backup first · no SSOT mutation</div>
</header>
<div class="grid">{cards}</div>
<main>{body}</main>
<div class="footer">Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</div>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 02_DUCKDB_COMMIT
# ==================================================================================================
def def_table_exists(con: Any, target_table: str) -> bool:
    n = con.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE lower(table_name) = lower(?)
        """,
        [target_table],
    ).fetchone()[0]
    return int(n) > 0


def def_count_table(con: Any, target_table: str) -> int:
    if not def_table_exists(con, target_table):
        return 0
    return int(con.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[0])


def def_count_conflict_pk(con: Any, target_table: str, pk_list: list[str]) -> int:
    if not pk_list:
        return 0
    if not def_table_exists(con, target_table):
        return 0

    placeholders = ",".join(["?"] * len(pk_list))
    sql = f"SELECT COUNT(*) FROM {target_table} WHERE vrn_pk IN ({placeholders})"
    return int(con.execute(sql, pk_list).fetchone()[0])


def def_duplicate_pk_count(con: Any, target_table: str) -> int:
    if not def_table_exists(con, target_table):
        return 0

    sql = f"""
    SELECT COUNT(*)
    FROM (
        SELECT vrn_pk, COUNT(*) AS n
        FROM {target_table}
        GROUP BY vrn_pk
        HAVING COUNT(*) > 1
    ) x
    """
    return int(con.execute(sql).fetchone()[0])


def def_execute_real_commit(
    primary_db: Path,
    target_table: str,
    create_sql_path: Path,
    insert_sql_path: Path,
    simulation_rows: list[dict],
) -> dict:
    result = {
        "duckdb_import": False,
        "connect_ok": False,
        "table_exists_before": False,
        "row_count_before": 0,
        "conflict_pk_before": 0,
        "create_ok": False,
        "insert_ok": False,
        "row_count_inside_txn": 0,
        "row_delta_inside_txn": 0,
        "duplicate_pk_inside_txn": 0,
        "commit_executed": False,
        "row_count_after_commit": 0,
        "row_delta_after_commit": 0,
        "duplicate_pk_after_commit": 0,
        "error": "",
        "statements": [],
    }

    try:
        import duckdb  # type: ignore
        result["duckdb_import"] = True
    except Exception as e:
        result["error"] = f"duckdb import failed: {type(e).__name__}: {e}"
        return result

    con = None
    expected_rows = len(simulation_rows)
    pk_list = [def_get(r, ["vrn_pk"]) for r in simulation_rows if def_get(r, ["vrn_pk"])]

    try:
        con = duckdb.connect(str(primary_db), read_only=False)
        result["connect_ok"] = True

        result["table_exists_before"] = def_table_exists(con, target_table)
        result["row_count_before"] = def_count_table(con, target_table)
        result["conflict_pk_before"] = def_count_conflict_pk(con, target_table, pk_list)

        if result["conflict_pk_before"] != 0:
            result["error"] = f"PK conflict before insert: {result['conflict_pk_before']}"
            con.close()
            return result

        create_stmts = def_split_sql_statements(create_sql_path.read_text(encoding="utf-8"))
        insert_stmts = def_split_sql_statements(insert_sql_path.read_text(encoding="utf-8"))

        con.execute("BEGIN TRANSACTION;")
        result["statements"].append({"phase": "BEGIN", "status": "OK", "sql_head": "BEGIN TRANSACTION"})

        for stmt in create_stmts:
            con.execute(stmt)
            result["statements"].append({"phase": "CREATE", "status": "OK", "sql_head": stmt[:260]})
        result["create_ok"] = True

        for stmt in insert_stmts:
            con.execute(stmt)
            result["statements"].append({"phase": "INSERT", "status": "OK", "sql_head": stmt[:260]})
        result["insert_ok"] = True

        result["row_count_inside_txn"] = def_count_table(con, target_table)
        result["row_delta_inside_txn"] = int(result["row_count_inside_txn"]) - int(result["row_count_before"])
        result["duplicate_pk_inside_txn"] = def_duplicate_pk_count(con, target_table)

        if result["row_delta_inside_txn"] != expected_rows:
            con.execute("ROLLBACK;")
            result["statements"].append({"phase": "ROLLBACK", "status": "ROW_DELTA_MISMATCH", "sql_head": "ROLLBACK"})
            result["error"] = f"row delta mismatch inside txn: {result['row_delta_inside_txn']} expected {expected_rows}"
            con.close()
            return result

        if result["duplicate_pk_inside_txn"] != 0:
            con.execute("ROLLBACK;")
            result["statements"].append({"phase": "ROLLBACK", "status": "DUPLICATE_PK", "sql_head": "ROLLBACK"})
            result["error"] = f"duplicate pk inside txn: {result['duplicate_pk_inside_txn']}"
            con.close()
            return result

        con.execute("COMMIT;")
        result["commit_executed"] = True
        result["statements"].append({"phase": "COMMIT", "status": "OK", "sql_head": "COMMIT"})

        result["row_count_after_commit"] = def_count_table(con, target_table)
        result["row_delta_after_commit"] = int(result["row_count_after_commit"]) - int(result["row_count_before"])
        result["duplicate_pk_after_commit"] = def_duplicate_pk_count(con, target_table)

        con.close()

    except Exception as e:
        result["error"] = f"real commit failed: {type(e).__name__}: {e}\n{traceback.format_exc()}"
        try:
            if con is not None:
                con.execute("ROLLBACK;")
                con.close()
        except Exception:
            pass

    return result


# ==================================================================================================
# def 03_ROLLBACK_SCRIPT
# ==================================================================================================
def def_write_rollback_script(path: Path, primary_db: Path, backup_db: Path, rollback_sql: Path) -> None:
    code = f"""
& {{
    # def VRN Manual Rollback Script generated by v0.6.15.7.1
    # def Option A restores full DuckDB backup.
    # def Option B executes rollback SQL deletes.
    # def Default is full backup restore because it is safer after first commit.

    $ErrorActionPreference = "Continue"

    $PRIMARY_DUCKDB = "{str(primary_db)}"
    $BACKUP_DUCKDB  = "{str(backup_db)}"
    $ROLLBACK_SQL   = "{str(rollback_sql)}"

    Write-Host "==================================================================================================" -ForegroundColor Yellow
    Write-Host "def VRN Manual Rollback Script" -ForegroundColor Yellow
    Write-Host "==================================================================================================" -ForegroundColor Yellow
    Write-Host "[PRIMARY_DUCKDB] $PRIMARY_DUCKDB" -ForegroundColor Yellow
    Write-Host "[BACKUP_DUCKDB]  $BACKUP_DUCKDB" -ForegroundColor Yellow
    Write-Host "[ROLLBACK_SQL]   $ROLLBACK_SQL" -ForegroundColor Yellow

    Write-Host ""
    Write-Host "Default action: restore full backup over primary DB." -ForegroundColor Red
    Write-Host "This script will NOT run automatically unless you paste and execute it." -ForegroundColor Red

    if ((Test-Path -LiteralPath $PRIMARY_DUCKDB) -and (Test-Path -LiteralPath $BACKUP_DUCKDB)) {{
        $TS = Get-Date -Format "yyyyMMdd_HHmmss"
        $SafetyCopy = "$PRIMARY_DUCKDB.before_manual_rollback_$TS.bak"
        Copy-Item -LiteralPath $PRIMARY_DUCKDB -Destination $SafetyCopy -Force
        Copy-Item -LiteralPath $BACKUP_DUCKDB -Destination $PRIMARY_DUCKDB -Force
        Write-Host "[ROLLBACK_DONE] backup restored to primary DB." -ForegroundColor Green
        Write-Host "[SAFETY_COPY] $SafetyCopy" -ForegroundColor Green
    }} else {{
        Write-Host "[ROLLBACK_BLOCKED] Missing primary or backup DB." -ForegroundColor Red
    }}

    Write-Host "PowerShell session remains open." -ForegroundColor DarkGray
}}
"""
    path.write_text(code, encoding="utf-8")


# ==================================================================================================
# def 04_MAIN
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 8:
        raise SystemExit("usage: py <run_root> <run_dir> <primary_duckdb> <target_table> <approval_phrase> <required_phrase> <allow_sha_drift>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    primary_duckdb = Path(sys.argv[3])
    target_table = sys.argv[4]
    approval_phrase = sys.argv[5]
    required_phrase = sys.argv[6]
    allow_sha_drift = str(sys.argv[7]).lower() == "true"

    run_dir.mkdir(parents=True, exist_ok=True)

    if approval_phrase != required_phrase:
        raise RuntimeError("Approval phrase mismatch. Real commit blocked.")

    if not primary_duckdb.exists():
        raise RuntimeError(f"Primary DuckDB not found: {primary_duckdb}")

    commit_run = def_find_latest_dir(run_root, ["VRN_COMMIT_CANDIDATE_PACK_APPROVAL_GATE_V061570"])
    handover_run = def_find_latest_dir(run_root, ["VRN_FINAL_HANDOVER_COMMIT_BLOCKER_SEAL_V0615702"])
    integration_run = def_find_latest_dir(run_root, ["VRN_FINAL_INTEGRATION_GOVERNANCE_SEAL_V0615703"])
    schema_run = def_find_latest_dir(run_root, ["VRN_DB_SCHEMA_COMPATIBILITY_AUDIT_V06156971"])
    sim_run = def_find_latest_dir(run_root, ["VRN_WRITE_SIMULATOR_ROLLBACK_PLAN_V0615696"])

    if not commit_run:
        raise RuntimeError("Missing v061570 commit candidate pack.")
    if not handover_run:
        raise RuntimeError("Missing v0615702 final handover pack.")
    if not schema_run:
        raise RuntimeError("Missing v06156971 schema audit.")
    if not sim_run:
        raise RuntimeError("Missing v0615696 write simulator.")

    commit_json = def_read_json(commit_run / "vrn_commit_candidate_pack_approval_gate_v061570.json")
    handover_json = def_read_json(handover_run / "vrn_final_handover_commit_blocker_seal_v0615702.json")
    integration_json = def_read_json(integration_run / "vrn_final_integration_governance_seal_v0615703.json") if integration_run else {}

    commit_counts = commit_json.get("counts", {})
    handover_counts = handover_json.get("counts", {})
    integration_counts = integration_json.get("counts", {})

    sealed_insert_sql = Path(commit_json.get("outputs", {}).get("sealed_insert_sql", ""))
    sealed_rollback_sql = Path(commit_json.get("outputs", {}).get("sealed_rollback_sql", ""))
    sealed_write_ready_csv = Path(commit_json.get("outputs", {}).get("sealed_write_ready_csv", ""))

    create_sql = schema_run / "vrn_create_table_plan_only_v06156971.sql"
    simulation_rows_csv = sim_run / "vrn_write_simulation_rows_v0615696.csv"

    required_files = [
        sealed_insert_sql,
        sealed_rollback_sql,
        sealed_write_ready_csv,
        create_sql,
        simulation_rows_csv,
    ]

    missing_files = [str(p) for p in required_files if not p.exists()]
    if missing_files:
        raise RuntimeError("Missing required sealed files: " + " | ".join(missing_files))

    simulation_rows = [r for r in def_read_csv(simulation_rows_csv) if "empty_marker" not in r]
    write_ready_rows = [r for r in def_read_csv(sealed_write_ready_csv) if "empty_marker" not in r]

    expected_rows = 27

    precheck_rows = [
        {
            "Status Lights": def_light("OK" if commit_json.get("system_pass") else "ERR"),
            "Gate": "COMMIT_CANDIDATE_PACK_PASS",
            "Value": "YES" if commit_json.get("system_pass") else "NO",
            "Severity": "OK" if commit_json.get("system_pass") else "ERR",
        },
        {
            "Status Lights": def_light("OK" if handover_json.get("system_pass") else "ERR"),
            "Gate": "FINAL_HANDOVER_PASS",
            "Value": "YES" if handover_json.get("system_pass") else "NO",
            "Severity": "OK" if handover_json.get("system_pass") else "ERR",
        },
        {
            "Status Lights": def_light("OK" if integration_json.get("system_pass", True) else "ERR"),
            "Gate": "FINAL_INTEGRATION_PASS",
            "Value": "YES" if integration_json.get("system_pass", True) else "NO",
            "Severity": "OK" if integration_json.get("system_pass", True) else "ERR",
        },
        {
            "Status Lights": def_light("OK" if approval_phrase == required_phrase else "ERR"),
            "Gate": "APPROVAL_PHRASE_MATCH",
            "Value": approval_phrase,
            "Severity": "OK" if approval_phrase == required_phrase else "ERR",
        },
        {
            "Status Lights": def_light("OK" if len(simulation_rows) == expected_rows else "ERR"),
            "Gate": "SIMULATION_ROWS_27",
            "Value": len(simulation_rows),
            "Severity": "OK" if len(simulation_rows) == expected_rows else "ERR",
        },
        {
            "Status Lights": def_light("OK" if len(write_ready_rows) == expected_rows else "ERR"),
            "Gate": "WRITE_READY_ROWS_27",
            "Value": len(write_ready_rows),
            "Severity": "OK" if len(write_ready_rows) == expected_rows else "ERR",
        },
        {
            "Status Lights": def_light("OK" if commit_counts.get("Approval Ready") == "YES" else "ERR"),
            "Gate": "APPROVAL_READY_FROM_PACK",
            "Value": commit_counts.get("Approval Ready", ""),
            "Severity": "OK" if commit_counts.get("Approval Ready") == "YES" else "ERR",
        },
        {
            "Status Lights": def_light("OK" if handover_counts.get("Commit Blocker") == "ACTIVE" else "ERR"),
            "Gate": "COMMIT_BLOCKER_PREVIOUSLY_ACTIVE",
            "Value": handover_counts.get("Commit Blocker", ""),
            "Severity": "OK" if handover_counts.get("Commit Blocker") == "ACTIVE" else "ERR",
        },
    ]

    if any(r["Severity"] == "ERR" for r in precheck_rows):
        raise RuntimeError("Precheck failed. Real commit blocked.")

    approval_sha = handover_json.get("primary_sha_now", "")
    before_sha = def_sha256_file(primary_duckdb)

    sha_gate_ok = bool(before_sha) and (allow_sha_drift or not approval_sha or before_sha == approval_sha)

    if not sha_gate_ok:
        raise RuntimeError(
            "Primary DB SHA drift detected. Real commit blocked. "
            f"current={before_sha} approval={approval_sha}"
        )

    backup_db = run_dir / ("BACKUP_BEFORE_REAL_COMMIT_" + primary_duckdb.name)
    shutil.copy2(primary_duckdb, backup_db)
    backup_sha = def_sha256_file(backup_db)

    if backup_sha != before_sha:
        raise RuntimeError("Backup SHA mismatch. Real commit blocked.")

    exec_result = def_execute_real_commit(
        primary_db=primary_duckdb,
        target_table=target_table,
        create_sql_path=create_sql,
        insert_sql_path=sealed_insert_sql,
        simulation_rows=simulation_rows,
    )

    after_sha = def_sha256_file(primary_duckdb)

    expected_commit_ok = (
        exec_result.get("commit_executed") is True
        and exec_result.get("row_delta_after_commit") == expected_rows
        and exec_result.get("duplicate_pk_after_commit") == 0
        and not exec_result.get("error")
    )

    rollback_script = run_dir / "Rollback_VRN_Real_Commit_v061571.ps1"
    def_write_rollback_script(
        path=rollback_script,
        primary_db=primary_duckdb,
        backup_db=backup_db,
        rollback_sql=sealed_rollback_sql,
    )

    statement_rows = []
    for s in exec_result.get("statements", []):
        statement_rows.append({
            "Status Lights": def_light("OK"),
            "phase": s.get("phase", ""),
            "status": s.get("status", ""),
            "sql head": s.get("sql_head", ""),
            "Severity": "OK",
        })

    sha_rows = [
        {
            "Status Lights": def_light("OK"),
            "file": "primary before commit",
            "path": str(primary_duckdb),
            "sha256": before_sha,
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "file": "backup before commit",
            "path": str(backup_db),
            "sha256": backup_sha,
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK" if after_sha and after_sha != before_sha else "WARN"),
            "file": "primary after commit",
            "path": str(primary_duckdb),
            "sha256": after_sha,
            "Severity": "OK" if after_sha and after_sha != before_sha else "WARN",
        },
    ]

    error_rows = []
    if exec_result.get("error"):
        error_rows.append({
            "Status Lights": def_light("ERR"),
            "error": exec_result.get("error"),
            "Severity": "ERR",
        })

    gate_rows = [
        {
            "Status Lights": def_light("OK" if sha_gate_ok else "ERR"),
            "Gate": "PRIMARY_SHA_MATCH_APPROVAL",
            "Value": "YES" if sha_gate_ok else "NO",
            "Severity": "OK" if sha_gate_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if backup_sha == before_sha else "ERR"),
            "Gate": "BACKUP_CREATED_AND_VERIFIED",
            "Value": "YES" if backup_sha == before_sha else "NO",
            "Severity": "OK" if backup_sha == before_sha else "ERR",
        },
        {
            "Status Lights": def_light("OK" if exec_result.get("connect_ok") else "ERR"),
            "Gate": "PRIMARY_DB_CONNECT",
            "Value": "YES" if exec_result.get("connect_ok") else "NO",
            "Severity": "OK" if exec_result.get("connect_ok") else "ERR",
        },
        {
            "Status Lights": def_light("OK" if exec_result.get("conflict_pk_before") == 0 else "ERR"),
            "Gate": "PK_CONFLICT_BEFORE_INSERT",
            "Value": exec_result.get("conflict_pk_before"),
            "Severity": "OK" if exec_result.get("conflict_pk_before") == 0 else "ERR",
        },
        {
            "Status Lights": def_light("OK" if exec_result.get("create_ok") else "ERR"),
            "Gate": "CREATE_TABLE_EXECUTED",
            "Value": "YES" if exec_result.get("create_ok") else "NO",
            "Severity": "OK" if exec_result.get("create_ok") else "ERR",
        },
        {
            "Status Lights": def_light("OK" if exec_result.get("insert_ok") else "ERR"),
            "Gate": "INSERT_EXECUTED",
            "Value": "YES" if exec_result.get("insert_ok") else "NO",
            "Severity": "OK" if exec_result.get("insert_ok") else "ERR",
        },
        {
            "Status Lights": def_light("OK" if exec_result.get("row_delta_after_commit") == expected_rows else "ERR"),
            "Gate": "ROW_DELTA_AFTER_COMMIT",
            "Value": exec_result.get("row_delta_after_commit"),
            "Severity": "OK" if exec_result.get("row_delta_after_commit") == expected_rows else "ERR",
        },
        {
            "Status Lights": def_light("OK" if exec_result.get("duplicate_pk_after_commit") == 0 else "ERR"),
            "Gate": "DUPLICATE_PK_AFTER_COMMIT",
            "Value": exec_result.get("duplicate_pk_after_commit"),
            "Severity": "OK" if exec_result.get("duplicate_pk_after_commit") == 0 else "ERR",
        },
        {
            "Status Lights": def_light("OK" if expected_commit_ok else "ERR"),
            "Gate": "COMMIT_EXECUTED_AND_VERIFIED",
            "Value": "YES" if expected_commit_ok else "NO",
            "Severity": "OK" if expected_commit_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "SSOT_MUTATION",
            "Value": "NO",
            "Severity": "OK",
        },
    ]

    next_steps = [
        {
            "Status Lights": def_light("OK" if expected_commit_ok else "ERR"),
            "Next Step": "Open final report and verify row delta / duplicate PK / rollback script path.",
            "Reason": "This is now a real committed DB mutation if Final=PASS.",
            "Severity": "OK" if expected_commit_ok else "ERR",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "If later rollback is needed, run the generated rollback script manually.",
            "Reason": "Rollback script restores the full pre-commit DB backup.",
            "Severity": "WARN",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Do not patch SSOT alias candidates yet.",
            "Reason": "Alias governance remains second-confirmation only.",
            "Severity": "OK",
        },
    ]

    outputs = {
        "html": str(run_dir / "VRN_Real_Commit_Backup_Postcheck_Rollback_v061571.html"),
        "json": str(run_dir / "vrn_real_commit_backup_postcheck_rollback_v061571.json"),
        "precheck_csv": str(run_dir / "vrn_real_commit_precheck_v061571.csv"),
        "gate_csv": str(run_dir / "vrn_real_commit_gate_v061571.csv"),
        "sha_csv": str(run_dir / "vrn_real_commit_sha_v061571.csv"),
        "statement_log_csv": str(run_dir / "vrn_real_commit_statement_log_v061571.csv"),
        "error_csv": str(run_dir / "vrn_real_commit_errors_v061571.csv"),
        "next_steps_csv": str(run_dir / "vrn_real_commit_next_steps_v061571.csv"),
        "backup_db": str(backup_db),
        "rollback_script": str(rollback_script),
        "sealed_rollback_sql": str(sealed_rollback_sql),
    }

    def_write_csv(Path(outputs["precheck_csv"]), precheck_rows)
    def_write_csv(Path(outputs["gate_csv"]), gate_rows)
    def_write_csv(Path(outputs["sha_csv"]), sha_rows)
    def_write_csv(Path(outputs["statement_log_csv"]), statement_rows)
    def_write_csv(Path(outputs["error_csv"]), error_rows)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)

    counts = {
        "Final": "PASS" if expected_commit_ok else "REVIEW",
        "Approval": "YES FOR COMMIT",
        "Expected Rows": expected_rows,
        "Row Delta": exec_result.get("row_delta_after_commit"),
        "Duplicate PK": "PASS" if exec_result.get("duplicate_pk_after_commit") == 0 else "FAIL",
        "Commit": "YES" if exec_result.get("commit_executed") else "NO",
        "Backup": "PASS" if backup_sha == before_sha else "FAIL",
        "Rollback Script": "YES",
        "SSOT Mutation": "NO",
    }

    overview = [
        {
            "Status Lights": def_light("OK" if expected_commit_ok else "ERR"),
            "Gate": "REAL_COMMIT_PASS",
            "Value": "YES" if expected_commit_ok else "NO",
            "Severity": "OK" if expected_commit_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "APPROVAL_PHRASE",
            "Value": approval_phrase,
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK" if exec_result.get("commit_executed") else "ERR"),
            "Gate": "COMMIT_EXECUTED",
            "Value": "YES" if exec_result.get("commit_executed") else "NO",
            "Severity": "OK" if exec_result.get("commit_executed") else "ERR",
        },
        {
            "Status Lights": def_light("OK" if exec_result.get("row_delta_after_commit") == expected_rows else "ERR"),
            "Gate": "ROW_DELTA",
            "Value": exec_result.get("row_delta_after_commit"),
            "Severity": "OK" if exec_result.get("row_delta_after_commit") == expected_rows else "ERR",
        },
        {
            "Status Lights": def_light("OK" if exec_result.get("duplicate_pk_after_commit") == 0 else "ERR"),
            "Gate": "DUPLICATE_PK",
            "Value": exec_result.get("duplicate_pk_after_commit"),
            "Severity": "OK" if exec_result.get("duplicate_pk_after_commit") == 0 else "ERR",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "SSOT_MUTATION",
            "Value": "NO",
            "Severity": "OK",
        },
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": expected_commit_ok,
        "primary_duckdb": str(primary_duckdb),
        "target_table": target_table,
        "backup_db": str(backup_db),
        "before_sha": before_sha,
        "after_sha": after_sha,
        "counts": counts,
        "exec_result": exec_result,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Precheck", precheck_rows, None),
            ("03 Real Commit Gate", gate_rows, None),
            ("04 SHA / Backup", sha_rows, None),
            ("05 Statement Log", statement_rows, 500),
            ("06 Errors", error_rows, None),
            ("07 Next Steps", next_steps, None),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


# ==================================================================================================
# def 05_ENTRYPOINT
# ==================================================================================================
if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise