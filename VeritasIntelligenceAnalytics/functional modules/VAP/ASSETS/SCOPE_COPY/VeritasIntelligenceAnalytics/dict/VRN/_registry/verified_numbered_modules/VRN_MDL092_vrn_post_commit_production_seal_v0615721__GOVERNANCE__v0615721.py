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


VERSION = "VRN_POST_COMMIT_PRODUCTION_SEAL_V0615721"


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
    if s in ["OK", "PASS", "YES", "SEALED", "PRODUCTION_READY"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW"]:
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
            cls = "left" if any(x in k.lower() for x in ["path", "reason", "sql", "column", "table", "sha", "script", "file", "source"]) else "center"
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
    body = "".join(def_html_table(t, rows, lim) for t, rows, lim in sections)

    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>VRN Post-Commit Production Seal v0615721</title>
<style>{css}</style>
</head>
<body>
<header>
<h1>VRN · Post-Commit ReadOnly Audit + Production Seal v0.6.15.7.2.1</h1>
<div class="sub">read-only post-commit validation · no DB write · no canonical / SSOT mutation</div>
</header>
<div class="grid">{cards}</div>
<main>{body}</main>
<div class="footer">Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</div>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


def def_expected_columns() -> list[str]:
    return [
        "vrn_pk",
        "ticker",
        "source_file",
        "statement",
        "period_year",
        "account_key",
        "account_canonical",
        "account_raw",
        "official_row_label",
        "value_mn_twd",
        "report_value_mn_twd",
        "unit",
        "confidence",
        "evidence_route",
        "precision_route",
        "evidence_cache_file",
        "evidence_table_index",
        "evidence_row_index",
        "evidence_col_index",
        "created_at",
    ]


def def_readonly_db_audit(primary_db: Path, target_table: str) -> dict:
    result = {
        "duckdb_import": False,
        "readonly_connect": False,
        "table_exists": False,
        "row_count": 0,
        "duplicate_pk": 0,
        "null_pk": 0,
        "schema_rows": [],
        "sample_rows": [],
        "error": "",
    }

    try:
        import duckdb  # type: ignore
        result["duckdb_import"] = True
    except Exception as e:
        result["error"] = f"duckdb import failed: {type(e).__name__}: {e}"
        return result

    try:
        con = duckdb.connect(str(primary_db), read_only=True)
        result["readonly_connect"] = True

        result["table_exists"] = int(con.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE lower(table_name) = lower(?)
            """,
            [target_table],
        ).fetchone()[0]) > 0

        if result["table_exists"]:
            result["row_count"] = int(con.execute(f"SELECT COUNT(*) FROM {target_table}").fetchone()[0])

            result["duplicate_pk"] = int(con.execute(
                f"""
                SELECT COUNT(*)
                FROM (
                    SELECT vrn_pk, COUNT(*) AS n
                    FROM {target_table}
                    GROUP BY vrn_pk
                    HAVING COUNT(*) > 1
                ) x
                """
            ).fetchone()[0])

            result["null_pk"] = int(con.execute(
                f"SELECT COUNT(*) FROM {target_table} WHERE vrn_pk IS NULL OR trim(vrn_pk) = ''"
            ).fetchone()[0])

            cols = con.execute(
                """
                SELECT column_name, data_type, is_nullable, ordinal_position
                FROM information_schema.columns
                WHERE lower(table_name) = lower(?)
                ORDER BY ordinal_position
                """,
                [target_table],
            ).fetchall()

            result["schema_rows"] = [
                {
                    "Status Lights": def_light("OK"),
                    "column": c[0],
                    "data_type": c[1],
                    "is_nullable": c[2],
                    "ordinal": c[3],
                    "Severity": "OK",
                }
                for c in cols
            ]

            sample = con.execute(
                f"""
                SELECT *
                FROM {target_table}
                ORDER BY created_at DESC, ticker, statement, period_year, account_key
                LIMIT 50
                """
            ).fetchdf()

            result["sample_rows"] = sample.astype(str).to_dict("records")

        con.close()

    except Exception as e:
        result["error"] = f"readonly audit failed: {type(e).__name__}: {e}\n{traceback.format_exc()}"

    return result


def def_main() -> None:
    if len(sys.argv) < 6:
        raise SystemExit("usage: py <run_root> <run_dir> <primary_duckdb> <target_table> <expected_rows>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    primary_db = Path(sys.argv[3])
    target_table = sys.argv[4]
    expected_rows = int(sys.argv[5])
    run_dir.mkdir(parents=True, exist_ok=True)

    commit_run = def_find_latest_dir(run_root, [
        "VRN_REAL_COMMIT_ARGFIX_BACKUP_POSTCHECK_V0615711",
        "VRN_REAL_COMMIT_BACKUP_POSTCHECK_ROLLBACK_V061571",
    ])

    if not commit_run:
        raise RuntimeError("Missing latest real commit run.")

    commit_json_path = commit_run / "vrn_real_commit_argfix_backup_postcheck_rollback_v0615711.json"
    if not commit_json_path.exists():
        commit_json_path = commit_run / "vrn_real_commit_backup_postcheck_rollback_v061571.json"

    commit_json = def_read_json(commit_json_path)
    commit_counts = commit_json.get("counts", {})
    outputs_in = commit_json.get("outputs", {})

    backup_db = Path(outputs_in.get("backup_db", ""))
    rollback_script = Path(outputs_in.get("rollback_script", ""))
    sealed_rollback_sql = Path(outputs_in.get("sealed_rollback_sql", ""))

    db_result = def_readonly_db_audit(primary_db, target_table)

    actual_columns = {def_norm(r.get("column")) for r in db_result.get("schema_rows", [])}
    expected_cols = def_expected_columns()

    schema_compare = []
    for col in expected_cols:
        ok = def_norm(col) in actual_columns
        schema_compare.append({
            "Status Lights": def_light("OK" if ok else "ERR"),
            "expected_column": col,
            "exists": "YES" if ok else "NO",
            "Severity": "OK" if ok else "ERR",
        })

    gate_rows = [
        {"Status Lights": def_light("OK" if commit_counts.get("Final") == "PASS" else "ERR"), "Gate": "SOURCE_REAL_COMMIT_PASS", "Value": commit_counts.get("Final", ""), "Severity": "OK" if commit_counts.get("Final") == "PASS" else "ERR"},
        {"Status Lights": def_light("OK" if commit_counts.get("Commit") == "YES" else "ERR"), "Gate": "SOURCE_COMMIT_YES", "Value": commit_counts.get("Commit", ""), "Severity": "OK" if commit_counts.get("Commit") == "YES" else "ERR"},
        {"Status Lights": def_light("OK" if db_result.get("duckdb_import") else "ERR"), "Gate": "DUCKDB_IMPORT", "Value": "YES" if db_result.get("duckdb_import") else "NO", "Severity": "OK" if db_result.get("duckdb_import") else "ERR"},
        {"Status Lights": def_light("OK" if db_result.get("readonly_connect") else "ERR"), "Gate": "READONLY_CONNECT", "Value": "YES" if db_result.get("readonly_connect") else "NO", "Severity": "OK" if db_result.get("readonly_connect") else "ERR"},
        {"Status Lights": def_light("OK" if db_result.get("table_exists") else "ERR"), "Gate": "TARGET_TABLE_EXISTS", "Value": "YES" if db_result.get("table_exists") else "NO", "Severity": "OK" if db_result.get("table_exists") else "ERR"},
        {"Status Lights": def_light("OK" if db_result.get("row_count", 0) >= expected_rows else "ERR"), "Gate": "ROW_COUNT_AT_LEAST_EXPECTED", "Value": db_result.get("row_count", 0), "Severity": "OK" if db_result.get("row_count", 0) >= expected_rows else "ERR"},
        {"Status Lights": def_light("OK" if db_result.get("duplicate_pk", 999) == 0 else "ERR"), "Gate": "DUPLICATE_PK", "Value": db_result.get("duplicate_pk", ""), "Severity": "OK" if db_result.get("duplicate_pk", 999) == 0 else "ERR"},
        {"Status Lights": def_light("OK" if db_result.get("null_pk", 999) == 0 else "ERR"), "Gate": "NULL_OR_EMPTY_PK", "Value": db_result.get("null_pk", ""), "Severity": "OK" if db_result.get("null_pk", 999) == 0 else "ERR"},
        {"Status Lights": def_light("OK" if backup_db.exists() else "ERR"), "Gate": "BACKUP_DB_EXISTS", "Value": str(backup_db), "Severity": "OK" if backup_db.exists() else "ERR"},
        {"Status Lights": def_light("OK" if rollback_script.exists() else "ERR"), "Gate": "ROLLBACK_SCRIPT_EXISTS", "Value": str(rollback_script), "Severity": "OK" if rollback_script.exists() else "ERR"},
        {"Status Lights": def_light("OK" if sealed_rollback_sql.exists() else "ERR"), "Gate": "SEALED_ROLLBACK_SQL_EXISTS", "Value": str(sealed_rollback_sql), "Severity": "OK" if sealed_rollback_sql.exists() else "ERR"},
        {"Status Lights": def_light("OK"), "Gate": "DB_WRITE_THIS_AUDIT", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SSOT_MUTATION", "Value": "NO", "Severity": "OK"},
    ]

    error_rows = []
    if db_result.get("error"):
        error_rows.append({
            "Status Lights": def_light("ERR"),
            "error": db_result.get("error"),
            "Severity": "ERR",
        })

    schema_ok = all(r["Severity"] == "OK" for r in schema_compare)
    gate_ok = all(r["Severity"] == "OK" for r in gate_rows)
    final_pass = schema_ok and gate_ok and not error_rows

    next_steps = [
        {
            "Status Lights": def_light("OK" if final_pass else "ERR"),
            "Next Step": "Seal VRN as post-commit production ready.",
            "Reason": "Read-only audit confirms committed table, row count, PK, schema, backup, rollback file.",
            "Severity": "OK" if final_pass else "ERR",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Do not patch SSOT alias candidates yet.",
            "Reason": "Alias governance remains separate second-confirmation workflow.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Rollback only if business validation later rejects committed rows.",
            "Reason": "Rollback script restores pre-commit backup DB.",
            "Severity": "WARN",
        },
    ]

    outputs = {
        "html": str(run_dir / "VRN_PostCommit_Production_Seal_v0615721.html"),
        "json": str(run_dir / "vrn_post_commit_production_seal_v0615721.json"),
        "gate_csv": str(run_dir / "vrn_post_commit_gate_v0615721.csv"),
        "schema_csv": str(run_dir / "vrn_post_commit_schema_v0615721.csv"),
        "schema_compare_csv": str(run_dir / "vrn_post_commit_schema_compare_v0615721.csv"),
        "sample_csv": str(run_dir / "vrn_post_commit_sample_rows_v0615721.csv"),
        "error_csv": str(run_dir / "vrn_post_commit_errors_v0615721.csv"),
        "next_steps_csv": str(run_dir / "vrn_post_commit_next_steps_v0615721.csv"),
    }

    def_write_csv(Path(outputs["gate_csv"]), gate_rows)
    def_write_csv(Path(outputs["schema_csv"]), db_result.get("schema_rows", []))
    def_write_csv(Path(outputs["schema_compare_csv"]), schema_compare)
    def_write_csv(Path(outputs["sample_csv"]), db_result.get("sample_rows", []))
    def_write_csv(Path(outputs["error_csv"]), error_rows)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Source Commit": commit_counts.get("Commit", ""),
        "ReadOnly Connect": "YES" if db_result.get("readonly_connect") else "NO",
        "Table Exists": "YES" if db_result.get("table_exists") else "NO",
        "Row Count": db_result.get("row_count", 0),
        "Duplicate PK": "PASS" if db_result.get("duplicate_pk", 999) == 0 else "FAIL",
        "Null PK": db_result.get("null_pk", ""),
        "Schema": "PASS" if schema_ok else "FAIL",
        "Backup": "YES" if backup_db.exists() else "NO",
        "Rollback Script": "YES" if rollback_script.exists() else "NO",
        "DB Write This Audit": "NO",
        "SSOT Mutation": "NO",
    }

    overview = [
        {"Status Lights": def_light("OK" if final_pass else "ERR"), "Gate": "POST_COMMIT_PRODUCTION_SEAL_PASS", "Value": "YES" if final_pass else "NO", "Severity": "OK" if final_pass else "ERR"},
        {"Status Lights": def_light("OK" if db_result.get("table_exists") else "ERR"), "Gate": "TARGET_TABLE_EXISTS", "Value": "YES" if db_result.get("table_exists") else "NO", "Severity": "OK" if db_result.get("table_exists") else "ERR"},
        {"Status Lights": def_light("OK" if db_result.get("row_count", 0) >= expected_rows else "ERR"), "Gate": "ROW_COUNT", "Value": db_result.get("row_count", 0), "Severity": "OK" if db_result.get("row_count", 0) >= expected_rows else "ERR"},
        {"Status Lights": def_light("OK" if db_result.get("duplicate_pk", 999) == 0 else "ERR"), "Gate": "DUPLICATE_PK", "Value": db_result.get("duplicate_pk", ""), "Severity": "OK" if db_result.get("duplicate_pk", 999) == 0 else "ERR"},
        {"Status Lights": def_light("OK" if schema_ok else "ERR"), "Gate": "SCHEMA_COMPARE", "Value": "PASS" if schema_ok else "FAIL", "Severity": "OK" if schema_ok else "ERR"},
        {"Status Lights": def_light("OK" if backup_db.exists() else "ERR"), "Gate": "BACKUP_DB_EXISTS", "Value": "YES" if backup_db.exists() else "NO", "Severity": "OK" if backup_db.exists() else "ERR"},
        {"Status Lights": def_light("OK" if rollback_script.exists() else "ERR"), "Gate": "ROLLBACK_SCRIPT_EXISTS", "Value": "YES" if rollback_script.exists() else "NO", "Severity": "OK" if rollback_script.exists() else "ERR"},
        {"Status Lights": def_light("OK"), "Gate": "DB_WRITE_THIS_AUDIT", "Value": "NO", "Severity": "OK"},
        {"Status Lights": def_light("OK"), "Gate": "SSOT_MUTATION", "Value": "NO", "Severity": "OK"},
    ]

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": final_pass,
        "source_commit_run": str(commit_run),
        "primary_duckdb": str(primary_db),
        "target_table": target_table,
        "counts": counts,
        "outputs": outputs,
    }

    def_write_json(Path(outputs["json"]), result)
    def_write_html(
        Path(outputs["html"]),
        counts,
        [
            ("01 Overview", overview, None),
            ("02 Post-Commit Gate", gate_rows, None),
            ("03 Schema Compare", schema_compare, None),
            ("04 Actual Schema", db_result.get("schema_rows", []), None),
            ("05 Sample Rows", db_result.get("sample_rows", []), 50),
            ("06 Errors", error_rows, None),
            ("07 Next Steps", next_steps, None),
        ],
    )

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise