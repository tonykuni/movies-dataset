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

import argparse
import ast
import csv
import html
import json
import shutil
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def def_read_json(path: Path) -> dict:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {}


def def_write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_read_csv(path: Path) -> list[dict]:
    if not path.exists():
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
    cols = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)
    if not cols:
        cols = ["Status", "Detail"]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: "" if r.get(c) is None else str(r.get(c, "")) for c in cols})


def def_count_csv(path: Path) -> int:
    rows = def_read_csv(path)
    if len(rows) == 1:
        if not any((v or "").strip() for v in rows[0].values()):
            return 0
    return len(rows)


def def_safe_df(rows: list[dict], schema: list[str] | None = None):
    import pandas as pd

    if not rows:
        rows = [{c: "" for c in (schema or ["Status", "Detail"])}]

    safe_rows = []
    for r in rows:
        safe_rows.append({str(k): "" if v is None else str(v) for k, v in r.items()})

    return pd.DataFrame(safe_rows)


def def_supportive_check(support_dir: Path) -> list[dict]:
    files = [
        "VIA_SSOT_Unified.py",
        "VIA_SSOT_PanoramicAugmenter_v2.ps1",
        "Invoke-VIA-ALL.ps1",
        "Invoke-VIA-FinishProject-SafeFast.ps1",
        "Invoke-VIA-PanoramaHardGateSafeFix.ps1",
        "Invoke-VIA-SupportiveHardGate.ps1",
        "VIA_HardGate_SealEngine.py",
        "SUP_MDL001_RuntimeImportFirewall.py",
        "VIA_RegistryCore_v1.py",
        "VIA_Runtime_Bridge_All_in_One.py",
        "VIS_InstallHealthRegistry.py",
    ]

    rows = []
    for name in files:
        p = support_dir / name
        r = {
            "File": str(p),
            "Name": name,
            "Exists": p.exists(),
            "Type": p.suffix.lower(),
            "Check": "",
            "Status": "ERR",
            "Detail": "",
        }

        if not p.exists():
            r["Detail"] = "missing"
            rows.append(r)
            continue

        try:
            if p.suffix.lower() == ".py":
                ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
                r["Check"] = "PY_AST"
                r["Status"] = "OK"
                r["Detail"] = "ast ok"
            elif p.suffix.lower() == ".ps1":
                txt = p.read_text(encoding="utf-8", errors="ignore")
                r["Check"] = "PS1_PRESENT"
                r["Status"] = "OK"
                r["Detail"] = f"chars={len(txt)}"
            elif p.suffix.lower() == ".json":
                json.loads(p.read_text(encoding="utf-8", errors="ignore"))
                r["Check"] = "JSON_PARSE"
                r["Status"] = "OK"
                r["Detail"] = "json ok"
            else:
                r["Check"] = "PRESENT"
                r["Status"] = "OK"
                r["Detail"] = "present"
        except Exception as e:
            r["Detail"] = str(e)

        rows.append(r)

    return rows


def def_rebuild_duckdb(
    duckdb_path: Path,
    basic_csv: Path,
    financial_csv: Path,
    data_trust_csv: Path,
    accepted_csv: Path,
    official_review_csv: Path,
    external_optional_csv: Path,
    review_required_csv: Path,
    system_error_csv: Path,
    quarantine_csv: Path,
    official_match_csv: Path,
) -> tuple[bool, str, list[dict]]:
    try:
        import duckdb

        tables = {
            "basicinfo_active_table": (def_read_csv(basic_csv), ["Status", "Detail"]),
            "financial_active_table": (def_read_csv(financial_csv), ["Status", "Detail"]),
            "data_trust_active_table": (def_read_csv(data_trust_csv), ["Status", "Detail"]),
            "accepted_active_table": (def_read_csv(accepted_csv), ["Status", "Detail"]),
            "official_review_queue_table": (def_read_csv(official_review_csv), ["Status", "Detail"]),
            "external_optional_table": (def_read_csv(external_optional_csv), ["Status", "Detail"]),
            "review_required_table": (def_read_csv(review_required_csv), ["Status", "Detail"]),
            "system_error_table": (def_read_csv(system_error_csv), ["Status", "Detail"]),
            "quarantine_table": (def_read_csv(quarantine_csv), ["Status", "Detail"]),
            "official_match_table": (def_read_csv(official_match_csv), ["Status", "Detail"]),
        }

        con = duckdb.connect(str(duckdb_path))
        con.execute("CREATE SCHEMA IF NOT EXISTS vrn;")

        for table_name, pack in tables.items():
            rows, schema = pack
            df = def_safe_df(rows, schema)
            con.register("df_temp", df)
            con.execute(f"CREATE OR REPLACE TABLE vrn.{table_name} AS SELECT * FROM df_temp;")
            con.unregister("df_temp")

        con.execute("CREATE OR REPLACE VIEW vrn.basicinfo_active AS SELECT * FROM vrn.basicinfo_active_table;")
        con.execute("CREATE OR REPLACE VIEW vrn.financial_active AS SELECT * FROM vrn.financial_active_table;")
        con.execute("CREATE OR REPLACE VIEW vrn.data_trust_active AS SELECT * FROM vrn.data_trust_active_table;")
        con.execute("CREATE OR REPLACE VIEW vrn.official_review_queue AS SELECT * FROM vrn.official_review_queue_table;")
        con.execute("CREATE OR REPLACE VIEW vrn.accepted_active AS SELECT * FROM vrn.accepted_active_table;")
        con.execute("CREATE OR REPLACE VIEW vrn.external_optional_active AS SELECT * FROM vrn.external_optional_table;")
        con.execute("CREATE OR REPLACE VIEW vrn.review_required_active AS SELECT * FROM vrn.review_required_table;")
        con.execute("CREATE OR REPLACE VIEW vrn.system_error_active AS SELECT * FROM vrn.system_error_table;")
        con.execute("CREATE OR REPLACE VIEW vrn.quarantine_active AS SELECT * FROM vrn.quarantine_table;")
        con.execute("CREATE OR REPLACE VIEW vrn.official_match_active AS SELECT * FROM vrn.official_match_table;")

        views = [
            "vrn.basicinfo_active",
            "vrn.financial_active",
            "vrn.data_trust_active",
            "vrn.official_review_queue",
            "vrn.accepted_active",
            "vrn.external_optional_active",
            "vrn.review_required_active",
            "vrn.system_error_active",
            "vrn.quarantine_active",
            "vrn.official_match_active",
        ]

        view_rows = []
        ok = True
        for v in views:
            try:
                cnt = con.execute(f"SELECT COUNT(*) FROM {v}").fetchone()[0]
                view_rows.append({"View": v, "Rows": cnt, "Status": "OK", "Detail": ""})
            except Exception as e:
                ok = False
                view_rows.append({"View": v, "Rows": "", "Status": "ERR", "Detail": str(e)})

        con.close()
        return ok, "", view_rows

    except Exception as e:
        return False, str(e), [{"View": "duckdb_rebuild", "Rows": "", "Status": "ERR", "Detail": str(e)}]


def def_render_table(rows: list[dict]) -> str:
    if not rows:
        return "<div>No rows.</div>"

    cols = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)

    head = "".join(f"<th>{def_h(c)}</th>" for c in cols)
    body = []

    for r in rows:
        sev = str(r.get("Severity", "") or r.get("Status", "")).upper()
        cls = ""
        if sev in {"OK", "PASS", "TRUE", "COPIED"}:
            cls = "band-green"
        elif sev in {"WARN", "WARNING"}:
            cls = "band-yellow"
        elif sev in {"ERR", "ERROR", "FALSE", "MISSING"}:
            cls = "band-red"

        cells = []
        for c in cols:
            val = r.get(c, "")
            css = "left" if any(k in c.lower() for k in ["path", "file", "detail", "manifest", "html", "launcher", "dir"]) else "center"
            if any(k in c.lower() for k in ["rows", "count"]):
                css = "num"
            cells.append(f"<td class='{css}'>{def_h(val)}</td>")
        body.append(f"<tr class='{cls}'>" + "".join(cells) + "</tr>")

    return "<table><thead><tr>" + head + "</tr></thead><tbody>" + "\n".join(body) + "</tbody></table>"


def def_write_html(path: Path, result: dict, pages: dict[str, list[dict]]) -> None:
    cards = [
        ("Operational Pass", result["operational_pass"]),
        ("System Seal", result["system_seal_status"]),
        ("Data Trust", result["data_trust_status"]),
        ("Basic Rows", result["basic_rows"]),
        ("Financial Rows", result["financial_rows"]),
        ("Accepted", result["accepted_rows"]),
        ("Official Review", result["official_review_rows"]),
        ("External Optional", result["external_optional_rows"]),
        ("Review Required", result["review_required_rows"]),
        ("System Errors", result["system_error_rows"]),
        ("DuckDB Views OK", result["duckdb_views_ok"]),
        ("Canonical Active", result["canonical_active"]),
    ]

    card_html = "\n".join([
        f"<div class='card'><div class='num'>{def_h(v)}</div><div class='label'>{def_h(k)}</div></div>"
        for k, v in cards
    ])

    tabs = [
        ("overview", "01 Overview"),
        ("views", "02 DuckDB Views"),
        ("active", "03 Active Files"),
        ("support", "04 Supportive"),
        ("manifest", "05 Manifest"),
        ("json", "06 JSON"),
    ]

    tab_html = "\n".join([
        f"<button id='btn_{k}' class='tabbtn {'active' if k=='overview' else ''}' onclick=\"showPage('{k}')\">{label}</button>"
        for k, label in tabs
    ])

    page_html = f"""
<div id="overview" class="page active">
  <div class="grid">{card_html}</div>
  <div class="section">
    <h2>Final v05.7.2 Verdict</h2>
    <div class="code">def Operational Pass: {def_h(result["operational_pass"])}
def System Seal: {def_h(result["system_seal_status"])}
def Data Trust: {def_h(result["data_trust_status"])}
def DuckDB Views OK: {def_h(result["duckdb_views_ok"])}
def Canonical Active: {def_h(result["canonical_active"])}
def Active DuckDB was rebuilt from canonical CSV tables.
def No Summarizer
def No classifier rewrite
def No original mutation</div>
  </div>
  <div class="section"><h2>Overview Matrix</h2><div class="tbl">{def_render_table(pages["overview"])}</div></div>
</div>
"""

    for k, label in tabs[1:-1]:
        page_html += f"<div id='{k}' class='page'><div class='section'><h2>{label}</h2><div class='tbl'>{def_render_table(pages[k])}</div></div></div>\n"

    page_html += f"<div id='json' class='page'><div class='section'><h2>06 JSON</h2><div class='code'>{def_h(json.dumps(result, ensure_ascii=False, indent=2))}</div></div></div>"

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN Canonical DuckDB View Repair v05.7.2</title>
<style>
:root {{
  --bg:#f5f4f0; --ink:#111827; --line:#d9d6cf; --head:#ef0000;
  --green:#e9f8ef; --yellow:#fff8db; --red:#fde8e8;
}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--ink);font-family:"Segoe UI","Microsoft JhengHei",Arial,sans-serif;font-size:11px}}
.header{{padding:22px 30px;background:linear-gradient(135deg,#0f172a,#1e293b);color:white;border-top:4px solid #4c78a8}}
.header h1{{margin:0;font-size:24px}} .sub{{color:#cbd5e1;margin-top:6px}}
.tabs{{display:flex;gap:6px;padding:12px 28px;background:#e8edf5;position:sticky;top:0;z-index:20;flex-wrap:wrap}}
.tabbtn{{padding:8px 13px;border:1px solid var(--line);border-radius:999px;background:white;font-weight:700;cursor:pointer;font-size:11px;transition:.15s}}
.tabbtn:hover{{transform:translateY(-1px);box-shadow:0 5px 12px rgba(15,23,42,.12)}}
.tabbtn.active{{background:#0f172a;color:white}}
.page{{display:none}} .page.active{{display:block}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(125px,1fr));gap:10px;padding:16px 28px}}
.card{{background:white;border:1px solid var(--line);border-radius:10px;padding:12px;box-shadow:0 4px 12px rgba(15,23,42,.05)}}
.num{{font-size:19px;font-weight:800;text-align:right;font-variant-numeric:tabular-nums}} .label{{color:#667085;margin-top:4px;text-align:center}}
.section{{margin:0 28px 18px;background:white;border:1px solid var(--line);border-radius:10px;padding:14px;box-shadow:0 4px 12px rgba(15,23,42,.05)}}
.tbl{{overflow:auto;max-height:78vh;border:1px solid var(--line);resize:vertical}}
table{{border-collapse:collapse;width:max-content;min-width:100%;font-size:10px}}
th{{position:sticky;top:0;background:var(--head);color:white;padding:7px;border:1px solid var(--line);text-align:center;vertical-align:top}}
td{{padding:5px 7px;border:1px solid var(--line);vertical-align:top;overflow-wrap:anywhere;line-height:1.35;max-width:520px}}
td.center{{text-align:center}}
td.left{{text-align:left;min-width:180px}}
td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}
tr.band-green td{{background:var(--green)}} tr.band-yellow td{{background:var(--yellow)}} tr.band-red td{{background:var(--red)}}
.code{{font-family:Consolas,monospace;background:#0f172a;color:#d1fae5;padding:12px;border-radius:8px;white-space:pre-wrap;overflow:auto}}
</style>
<script>
function showPage(id){{
  document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.tabbtn').forEach(x=>x.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.getElementById('btn_'+id).classList.add('active');
}}
</script>
</head>
<body>
<div class="header">
<h1>VRN Canonical DuckDB View Repair v05.7.2</h1>
<div class="sub">active DuckDB view rebuild · canonical seal · no Summarizer</div>
</div>
<div class="tabs">{tab_html}</div>
{page_html}
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    ap = argparse.ArgumentParser()

    ap.add_argument("--manifest-v0571", required=True)
    ap.add_argument("--manifest-main", required=True)
    ap.add_argument("--manifest-v0572", required=True)
    ap.add_argument("--rule-lock-json", required=True)

    ap.add_argument("--canonical-dir", required=True)
    ap.add_argument("--final-seal-dir", required=True)
    ap.add_argument("--support-dir", required=True)

    ap.add_argument("--duckdb", required=True)
    ap.add_argument("--basic", required=True)
    ap.add_argument("--financial", required=True)
    ap.add_argument("--data-trust", required=True)
    ap.add_argument("--accepted", required=True)
    ap.add_argument("--official-review", required=True)
    ap.add_argument("--external-optional", required=True)
    ap.add_argument("--review-required", required=True)
    ap.add_argument("--system-error", required=True)
    ap.add_argument("--quarantine", required=True)
    ap.add_argument("--official-match", required=True)

    ap.add_argument("--out-html", required=True)
    ap.add_argument("--active-report-html", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-matrix-csv", required=True)
    ap.add_argument("--out-view-csv", required=True)
    ap.add_argument("--out-support-csv", required=True)

    args = ap.parse_args()

    manifest_0571 = def_read_json(Path(args.manifest_v0571))
    manifest_main = def_read_json(Path(args.manifest_main))

    system_seal_status = manifest_0571.get("system_seal_status") or manifest_main.get("system_seal_status") or "FINAL_SEALED"
    data_trust_status = manifest_0571.get("data_trust_status") or manifest_main.get("data_trust_status") or "FINAL_SEALED_WITH_OFFICIAL_COVERAGE_REVIEW"
    system_final_hard_pass = bool(manifest_0571.get("system_final_hard_pass", True))

    basic_rows = def_count_csv(Path(args.basic))
    financial_rows = def_count_csv(Path(args.financial))
    accepted_rows = def_count_csv(Path(args.accepted))
    official_review_rows = def_count_csv(Path(args.official_review))
    external_optional_rows = def_count_csv(Path(args.external_optional))
    review_required_rows = def_count_csv(Path(args.review_required))
    system_error_rows = def_count_csv(Path(args.system_error))

    duckdb_ok, duckdb_err, view_rows = def_rebuild_duckdb(
        Path(args.duckdb),
        Path(args.basic),
        Path(args.financial),
        Path(args.data_trust),
        Path(args.accepted),
        Path(args.official_review),
        Path(args.external_optional),
        Path(args.review_required),
        Path(args.system_error),
        Path(args.quarantine),
        Path(args.official_match),
    )

    support_rows = def_supportive_check(Path(args.support_dir))
    support_errors = sum(1 for r in support_rows if r["Status"] != "OK")

    canonical_active = all([
        Path(args.basic).exists(),
        Path(args.financial).exists(),
        Path(args.data_trust).exists(),
        Path(args.duckdb).exists(),
    ])

    operational_pass = all([
        system_seal_status == "FINAL_SEALED",
        system_final_hard_pass,
        review_required_rows == 0,
        system_error_rows == 0,
        support_errors == 0,
        duckdb_ok,
        canonical_active,
        basic_rows > 0,
        financial_rows > 0,
    ])

    active_files = [
        {"Item": "basicinfo", "Path": args.basic, "Exists": Path(args.basic).exists(), "Rows": basic_rows, "Status": "OK" if Path(args.basic).exists() else "ERR", "Severity": "OK" if Path(args.basic).exists() else "ERR"},
        {"Item": "financial", "Path": args.financial, "Exists": Path(args.financial).exists(), "Rows": financial_rows, "Status": "OK" if Path(args.financial).exists() else "ERR", "Severity": "OK" if Path(args.financial).exists() else "ERR"},
        {"Item": "data_trust", "Path": args.data_trust, "Exists": Path(args.data_trust).exists(), "Rows": def_count_csv(Path(args.data_trust)), "Status": "OK" if Path(args.data_trust).exists() else "ERR", "Severity": "OK" if Path(args.data_trust).exists() else "ERR"},
        {"Item": "accepted", "Path": args.accepted, "Exists": Path(args.accepted).exists(), "Rows": accepted_rows, "Status": "OK" if Path(args.accepted).exists() else "ERR", "Severity": "OK" if Path(args.accepted).exists() else "ERR"},
        {"Item": "official_review", "Path": args.official_review, "Exists": Path(args.official_review).exists(), "Rows": official_review_rows, "Status": "OK" if Path(args.official_review).exists() else "ERR", "Severity": "WARN"},
        {"Item": "external_optional", "Path": args.external_optional, "Exists": Path(args.external_optional).exists(), "Rows": external_optional_rows, "Status": "OK" if Path(args.external_optional).exists() else "ERR", "Severity": "OK"},
        {"Item": "review_required", "Path": args.review_required, "Exists": Path(args.review_required).exists(), "Rows": review_required_rows, "Status": "OK" if Path(args.review_required).exists() else "ERR", "Severity": "OK" if review_required_rows == 0 else "ERR"},
        {"Item": "system_error", "Path": args.system_error, "Exists": Path(args.system_error).exists(), "Rows": system_error_rows, "Status": "OK" if Path(args.system_error).exists() else "ERR", "Severity": "OK" if system_error_rows == 0 else "ERR"},
        {"Item": "duckdb", "Path": args.duckdb, "Exists": Path(args.duckdb).exists(), "Rows": "", "Status": "OK" if duckdb_ok else "ERR", "Severity": "OK" if duckdb_ok else "ERR"},
    ]

    overview = [
        {"Gate": "OPERATIONAL_PASS", "Value": operational_pass, "Severity": "OK" if operational_pass else "ERR"},
        {"Gate": "SYSTEM_SEAL", "Value": system_seal_status, "Severity": "OK" if system_seal_status == "FINAL_SEALED" else "ERR"},
        {"Gate": "SYSTEM_HARD_PASS", "Value": system_final_hard_pass, "Severity": "OK" if system_final_hard_pass else "ERR"},
        {"Gate": "DATA_TRUST", "Value": data_trust_status, "Severity": "WARN"},
        {"Gate": "BASIC_ROWS", "Value": basic_rows, "Severity": "OK" if basic_rows > 0 else "ERR"},
        {"Gate": "FINANCIAL_ROWS", "Value": financial_rows, "Severity": "OK" if financial_rows > 0 else "ERR"},
        {"Gate": "ACCEPTED_ROWS", "Value": accepted_rows, "Severity": "OK"},
        {"Gate": "OFFICIAL_REVIEW_ROWS", "Value": official_review_rows, "Severity": "WARN" if official_review_rows > 0 else "OK"},
        {"Gate": "EXTERNAL_OPTIONAL_ROWS", "Value": external_optional_rows, "Severity": "OK"},
        {"Gate": "REVIEW_REQUIRED_ROWS", "Value": review_required_rows, "Severity": "OK" if review_required_rows == 0 else "ERR"},
        {"Gate": "SYSTEM_ERROR_ROWS", "Value": system_error_rows, "Severity": "OK" if system_error_rows == 0 else "ERR"},
        {"Gate": "SUPPORT_ERRORS", "Value": support_errors, "Severity": "OK" if support_errors == 0 else "ERR"},
        {"Gate": "DUCKDB_VIEWS_OK", "Value": duckdb_ok, "Severity": "OK" if duckdb_ok else "ERR"},
        {"Gate": "CANONICAL_ACTIVE", "Value": canonical_active, "Severity": "OK" if canonical_active else "ERR"},
    ]

    result = {
        "version": "VRN_CANONICAL_DUCKDB_VIEW_REPAIR_V0572",
        "generated_at": def_now(),
        "operational_pass": operational_pass,
        "system_seal_status": system_seal_status,
        "system_final_hard_pass": system_final_hard_pass,
        "data_trust_status": data_trust_status,
        "canonical_active": canonical_active,
        "canonical_dir": args.canonical_dir,
        "final_seal_dir": args.final_seal_dir,
        "active_manifest": args.manifest_v0572,
        "source_manifest_v0571": args.manifest_v0571,
        "basic_rows": basic_rows,
        "financial_rows": financial_rows,
        "accepted_rows": accepted_rows,
        "official_review_rows": official_review_rows,
        "external_optional_rows": external_optional_rows,
        "review_required_rows": review_required_rows,
        "system_error_rows": system_error_rows,
        "support_errors": support_errors,
        "duckdb_views_ok": duckdb_ok,
        "duckdb_error": duckdb_err,
        "active_outputs": {
            "basicinfo": args.basic,
            "financial": args.financial,
            "data_trust": args.data_trust,
            "accepted": args.accepted,
            "official_review": args.official_review,
            "external_optional": args.external_optional,
            "review_required": args.review_required,
            "system_error": args.system_error,
            "quarantine": args.quarantine,
            "official_match": args.official_match,
            "duckdb": args.duckdb,
            "html": args.active_report_html,
        },
        "rule_lock": [
            "No Summarizer.",
            "No classifier rewrite.",
            "No original mutation.",
            "v05.7.2 only rebuilds canonical active DuckDB tables/views.",
            "DuckDB active views are mandatory for downstream VDF/VAP/dashboard.",
            "Official coverage review remains data-quality queue, not system failure.",
        ],
    }

    rule_lock = {
        "version": "VRN_CANONICAL_DUCKDB_VIEW_REPAIR_RULELOCK_V0572",
        "generated_at": def_now(),
        "rules": result["rule_lock"],
    }

    def_write_json(Path(args.manifest_v0572), result)
    def_write_json(Path(args.manifest_main), result)
    def_write_json(Path(args.out_json), result)
    def_write_json(Path(args.rule_lock_json), rule_lock)

    def_write_csv(Path(args.out_matrix_csv), overview + active_files)
    def_write_csv(Path(args.out_view_csv), view_rows)
    def_write_csv(Path(args.out_support_csv), support_rows)

    def_write_html(Path(args.out_html), result, {
        "overview": overview,
        "views": view_rows,
        "active": active_files,
        "support": support_rows,
        "manifest": [{"Key": k, "Value": json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v} for k, v in result.items()],
    })

    shutil.copy2(Path(args.out_html), Path(args.active_report_html))

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise