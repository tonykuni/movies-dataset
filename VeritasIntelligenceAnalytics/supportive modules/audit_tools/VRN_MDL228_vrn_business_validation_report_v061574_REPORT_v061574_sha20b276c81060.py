# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import hashlib
import html
import json
import math
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_BUSINESS_VALIDATION_REPORT_V061574"


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
    if s in ["OK", "PASS", "YES", "VALIDATED", "READONLY_OK"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "CHECK"]:
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


def def_to_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        s = str(x).replace(",", "").strip()
        if s == "" or s.lower() in ["nan", "none", "null"]:
            return None
        v = float(s)
        if math.isnan(v) or math.isinf(v):
            return None
        return v
    except Exception:
        return None


def def_to_int(x: Any) -> int | None:
    try:
        if x is None:
            return None
        s = str(x).strip()
        if s == "":
            return None
        return int(float(s))
    except Exception:
        return None


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
        sev = str(r.get("Severity", "OK")).upper()
        tr_cls = "warnrow" if sev == "WARN" else ("errrow" if sev == "ERR" else "")
        tds: list[str] = []
        for k in fields:
            v = "" if r.get(k) is None else str(r.get(k, ""))
            cls = "left" if any(x in k.lower() for x in ["path", "file", "reason", "source", "account", "label", "evidence", "note", "review"]) else "center"
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
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:1400px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
.warnrow{background:rgba(255,209,102,.08)}
.errrow{background:rgba(255,80,80,.10)}
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
<title>VRN Business Validation Report v061574</title>
<style>{css}</style>
</head>
<body>
<header>
<h1>VRN · FinancialData Business Validation Report v0.6.15.7.4</h1>
<div class="sub">read-only business validation · committed rows review · no DB write · no SSOT mutation</div>
</header>
<div class="grid">{cards}</div>
<main>{body}</main>
<div class="footer">Veritas Intelligence Analytics │ AI-Augmented Investment Intelligence for Smarter Decisions and Deeper Insight</div>
</body>
</html>
"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 02_DB_READONLY
# ==================================================================================================
def def_read_committed_rows(primary_db: Path, target_table: str) -> dict:
    result = {
        "duckdb_import": False,
        "readonly_connect": False,
        "table_exists": False,
        "rows": [],
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

        table_exists = int(con.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE lower(table_name) = lower(?)
            """,
            [target_table],
        ).fetchone()[0]) > 0

        result["table_exists"] = table_exists

        if table_exists:
            df = con.execute(
                f"""
                SELECT
                    vrn_pk,
                    ticker,
                    source_file,
                    statement,
                    period_year,
                    account_key,
                    account_canonical,
                    account_raw,
                    official_row_label,
                    value_mn_twd,
                    report_value_mn_twd,
                    unit,
                    confidence,
                    evidence_route,
                    precision_route,
                    evidence_cache_file,
                    evidence_table_index,
                    evidence_row_index,
                    evidence_col_index,
                    created_at
                FROM {target_table}
                ORDER BY ticker, statement, period_year, account_key, vrn_pk
                """
            ).fetchdf()
            result["rows"] = df.astype(str).to_dict("records")

        con.close()

    except Exception as e:
        result["error"] = f"readonly query failed: {type(e).__name__}: {e}\n{traceback.format_exc()}"

    return result


# ==================================================================================================
# def 03_BUSINESS_RULES
# ==================================================================================================
def def_classify_row(row: dict) -> dict:
    ticker = def_clean(row.get("ticker"))
    statement = def_clean(row.get("statement"))
    year = def_to_int(row.get("period_year"))
    account_key = def_clean(row.get("account_key"))
    account_canonical = def_clean(row.get("account_canonical"))
    account_raw = def_clean(row.get("account_raw"))
    official_label = def_clean(row.get("official_row_label"))
    value = def_to_float(row.get("value_mn_twd"))
    report_value = def_to_float(row.get("report_value_mn_twd"))
    confidence = def_to_float(row.get("confidence"))
    unit = def_clean(row.get("unit"))
    source_file = def_clean(row.get("source_file"))

    reasons: list[str] = []
    severity = "OK"

    if not ticker:
        reasons.append("missing ticker")
    if not statement:
        reasons.append("missing statement")
    if year is None:
        reasons.append("missing period_year")
    if not account_key:
        reasons.append("missing account_key")
    if not account_canonical:
        reasons.append("missing account_canonical")
    if value is None:
        reasons.append("missing value_mn_twd")
    if confidence is None:
        reasons.append("missing confidence")
    if not source_file:
        reasons.append("missing source_file")

    if ticker and not re.match(r"^[1-9]\d{3}$", ticker):
        reasons.append("ticker not Taiwan 4-digit code")

    if year is not None and (year < 2015 or year > 2035):
        reasons.append("period_year outside normal range")

    if value is not None and abs(value) > 10_000_000:
        reasons.append("value magnitude extremely large; manual check")

    if value is not None and value == 0:
        reasons.append("zero value; check if valid")

    if confidence is not None and confidence < 0.8:
        reasons.append("confidence below 0.8")

    if unit and "mn" not in unit.lower() and "百萬" not in unit and "twd" not in unit.lower():
        reasons.append("unit not clearly mn TWD")

    if report_value is not None and value is not None:
        if abs(report_value - value) > max(1.0, abs(value) * 0.02):
            reasons.append("report_value differs from value over tolerance")

    if reasons:
        severity = "WARN"
    if any(x.startswith("missing") for x in reasons):
        severity = "ERR"

    return {
        "Status Lights": def_light(severity),
        "ticker": ticker,
        "statement": statement,
        "period_year": year if year is not None else "",
        "account_key": account_key,
        "account_canonical": account_canonical,
        "account_raw": account_raw,
        "official_row_label": official_label,
        "value_mn_twd": value if value is not None else "",
        "report_value_mn_twd": report_value if report_value is not None else "",
        "unit": unit,
        "confidence": confidence if confidence is not None else "",
        "source_file": source_file,
        "evidence_route": def_clean(row.get("evidence_route")),
        "precision_route": def_clean(row.get("precision_route")),
        "vrn_pk": def_clean(row.get("vrn_pk")),
        "Review Reason": " | ".join(reasons) if reasons else "OK",
        "Severity": severity,
    }


def def_build_summaries(validated_rows: list[dict]) -> tuple[list[dict], list[dict], list[dict], list[dict]]:
    by_ticker: dict[str, dict] = {}
    by_statement: dict[str, dict] = {}
    by_year: dict[str, dict] = {}
    by_source: dict[str, dict] = {}

    for r in validated_rows:
        ticker = def_clean(r.get("ticker"))
        statement = def_clean(r.get("statement"))
        year = def_clean(r.get("period_year"))
        source = def_clean(r.get("source_file"))
        sev = def_clean(r.get("Severity"))

        for key, store, label in [
            (ticker, by_ticker, "ticker"),
            (statement, by_statement, "statement"),
            (year, by_year, "period_year"),
            (source, by_source, "source_file"),
        ]:
            if key not in store:
                store[key] = {
                    "Status Lights": def_light("OK"),
                    label: key,
                    "rows": 0,
                    "ok": 0,
                    "warn": 0,
                    "err": 0,
                    "Severity": "OK",
                }
            store[key]["rows"] += 1
            if sev == "OK":
                store[key]["ok"] += 1
            elif sev == "WARN":
                store[key]["warn"] += 1
            elif sev == "ERR":
                store[key]["err"] += 1

            if store[key]["err"] > 0:
                store[key]["Severity"] = "ERR"
                store[key]["Status Lights"] = def_light("ERR")
            elif store[key]["warn"] > 0:
                store[key]["Severity"] = "WARN"
                store[key]["Status Lights"] = def_light("WARN")

    return (
        list(by_ticker.values()),
        list(by_statement.values()),
        list(by_year.values()),
        list(by_source.values()),
    )


def def_main() -> None:
    if len(sys.argv) < 6:
        raise SystemExit("usage: py <run_root> <run_dir> <primary_duckdb> <target_table> <expected_rows>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    primary_db = Path(sys.argv[3])
    target_table = sys.argv[4]
    expected_rows = int(sys.argv[5])
    run_dir.mkdir(parents=True, exist_ok=True)

    production_lock_run = def_find_latest_dir(run_root, ["VRN_FINAL_PRODUCTION_LOCK_REGISTRY_V061573"])
    post_commit_run = def_find_latest_dir(run_root, ["VRN_POST_COMMIT_PRODUCTION_SEAL_V0615721"])

    production_json = {}
    if production_lock_run:
        production_json = def_read_json(production_lock_run / "vrn_final_production_lock_registry_v061573.json")

    post_json = {}
    if post_commit_run:
        post_json = def_read_json(post_commit_run / "vrn_post_commit_production_seal_v0615721.json")

    db_result = def_read_committed_rows(primary_db, target_table)
    raw_rows = db_result.get("rows", [])

    validated_rows = [def_classify_row(r) for r in raw_rows]
    review_rows = [r for r in validated_rows if r.get("Severity") in ["WARN", "ERR"]]
    err_rows = [r for r in validated_rows if r.get("Severity") == "ERR"]
    warn_rows = [r for r in validated_rows if r.get("Severity") == "WARN"]

    by_ticker, by_statement, by_year, by_source = def_build_summaries(validated_rows)

    row_count_ok = len(validated_rows) == expected_rows
    readonly_ok = bool(db_result.get("readonly_connect"))
    table_ok = bool(db_result.get("table_exists"))
    no_err = len(err_rows) == 0

    # Business validation PASS means technical extraction rows are usable for manual review.
    # WARN rows do not fail the seal; they are expected business review items.
    final_pass = readonly_ok and table_ok and row_count_ok and no_err

    gate_rows = [
        {
            "Status Lights": def_light("OK" if production_json.get("system_pass", False) else "WARN"),
            "Gate": "SOURCE_PRODUCTION_LOCK_PASS",
            "Value": "YES" if production_json.get("system_pass", False) else "UNKNOWN",
            "Severity": "OK" if production_json.get("system_pass", False) else "WARN",
        },
        {
            "Status Lights": def_light("OK" if post_json.get("system_pass", False) else "WARN"),
            "Gate": "SOURCE_POST_COMMIT_SEAL_PASS",
            "Value": "YES" if post_json.get("system_pass", False) else "UNKNOWN",
            "Severity": "OK" if post_json.get("system_pass", False) else "WARN",
        },
        {
            "Status Lights": def_light("OK" if readonly_ok else "ERR"),
            "Gate": "READONLY_CONNECT",
            "Value": "YES" if readonly_ok else "NO",
            "Severity": "OK" if readonly_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if table_ok else "ERR"),
            "Gate": "TARGET_TABLE_EXISTS",
            "Value": "YES" if table_ok else "NO",
            "Severity": "OK" if table_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if row_count_ok else "ERR"),
            "Gate": "ROW_COUNT_EXPECTED",
            "Value": f"{len(validated_rows)} / {expected_rows}",
            "Severity": "OK" if row_count_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if no_err else "ERR"),
            "Gate": "NO_MISSING_CORE_FIELDS",
            "Value": "YES" if no_err else "NO",
            "Severity": "OK" if no_err else "ERR",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "DB_WRITE_THIS_RUN",
            "Value": "NO",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "SSOT_MUTATION",
            "Value": "NO",
            "Severity": "OK",
        },
    ]

    error_rows = []
    if db_result.get("error"):
        error_rows.append({
            "Status Lights": def_light("ERR"),
            "error": db_result.get("error"),
            "Severity": "ERR",
        })

    next_steps = [
        {
            "Status Lights": def_light("OK" if final_pass else "ERR"),
            "Next Step": "Business owner should review WARN rows, if any.",
            "Reason": "WARN means content check, not system failure.",
            "Severity": "OK" if final_pass else "ERR",
        },
        {
            "Status Lights": def_light("OK"),
            "Next Step": "Keep this report as the 27-row business validation pack.",
            "Reason": "It is readable by ticker / statement / year / account / value.",
            "Severity": "OK",
        },
        {
            "Status Lights": def_light("WARN"),
            "Next Step": "Rollback only if business owner rejects committed rows.",
            "Reason": "Rollback uses pre-commit DB backup from v0615711.",
            "Severity": "WARN",
        },
    ]

    outputs = {
        "html": str(run_dir / "VRN_FinancialData_Business_Validation_Report_v061574.html"),
        "json": str(run_dir / "vrn_financialdata_business_validation_report_v061574.json"),
        "validated_csv": str(run_dir / "vrn_financialdata_business_validation_rows_v061574.csv"),
        "review_csv": str(run_dir / "vrn_financialdata_business_review_rows_v061574.csv"),
        "gate_csv": str(run_dir / "vrn_business_validation_gate_v061574.csv"),
        "ticker_summary_csv": str(run_dir / "vrn_business_validation_by_ticker_v061574.csv"),
        "statement_summary_csv": str(run_dir / "vrn_business_validation_by_statement_v061574.csv"),
        "year_summary_csv": str(run_dir / "vrn_business_validation_by_year_v061574.csv"),
        "source_summary_csv": str(run_dir / "vrn_business_validation_by_source_v061574.csv"),
        "error_csv": str(run_dir / "vrn_business_validation_errors_v061574.csv"),
        "next_steps_csv": str(run_dir / "vrn_business_validation_next_steps_v061574.csv"),
    }

    def_write_csv(Path(outputs["validated_csv"]), validated_rows)
    def_write_csv(Path(outputs["review_csv"]), review_rows)
    def_write_csv(Path(outputs["gate_csv"]), gate_rows)
    def_write_csv(Path(outputs["ticker_summary_csv"]), by_ticker)
    def_write_csv(Path(outputs["statement_summary_csv"]), by_statement)
    def_write_csv(Path(outputs["year_summary_csv"]), by_year)
    def_write_csv(Path(outputs["source_summary_csv"]), by_source)
    def_write_csv(Path(outputs["error_csv"]), error_rows)
    def_write_csv(Path(outputs["next_steps_csv"]), next_steps)

    counts = {
        "Final": "PASS" if final_pass else "REVIEW",
        "Rows": len(validated_rows),
        "Expected": expected_rows,
        "Review Rows": len(review_rows),
        "ERR Rows": len(err_rows),
        "WARN Rows": len(warn_rows),
        "Tickers": len([x for x in {r.get("ticker") for r in validated_rows} if x]),
        "Statements": len([x for x in {r.get("statement") for r in validated_rows} if x]),
        "Years": len([x for x in {r.get("period_year") for r in validated_rows} if x]),
        "DB Write": "NO",
        "SSOT": "NO",
    }

    overview = [
        {
            "Status Lights": def_light("OK" if final_pass else "ERR"),
            "Gate": "BUSINESS_VALIDATION_PASS",
            "Value": "YES" if final_pass else "NO",
            "Severity": "OK" if final_pass else "ERR",
        },
        {
            "Status Lights": def_light("OK" if row_count_ok else "ERR"),
            "Gate": "ROW_COUNT",
            "Value": f"{len(validated_rows)} / {expected_rows}",
            "Severity": "OK" if row_count_ok else "ERR",
        },
        {
            "Status Lights": def_light("OK" if no_err else "ERR"),
            "Gate": "ERR_ROWS",
            "Value": len(err_rows),
            "Severity": "OK" if no_err else "ERR",
        },
        {
            "Status Lights": def_light("WARN" if warn_rows else "OK"),
            "Gate": "WARN_ROWS",
            "Value": len(warn_rows),
            "Severity": "WARN" if warn_rows else "OK",
        },
        {
            "Status Lights": def_light("OK"),
            "Gate": "DB_WRITE_THIS_RUN",
            "Value": "NO",
            "Severity": "OK",
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
        "system_pass": final_pass,
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
            ("02 Business Validation Gate", gate_rows, None),
            ("03 Rows for Manual Business Review", validated_rows, None),
            ("04 Review Queue WARN/ERR Only", review_rows, None),
            ("05 Summary by Ticker", by_ticker, None),
            ("06 Summary by Statement", by_statement, None),
            ("07 Summary by Year", by_year, None),
            ("08 Summary by Source File", by_source, None),
            ("09 Errors", error_rows, None),
            ("10 Next Steps", next_steps, None),
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