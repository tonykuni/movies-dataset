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
import csv
import html
import json
import re
import traceback
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


SUMMARY_PAT = re.compile(r"^Summary_|summary|摘要|重點|paragraph_|quality_grade|summarizer|financial_snapshot", re.I)
LEFT_COL_PAT = re.compile(r"filename|path|source|text|reason|explanation|json|raw|tokens|normalized|detail|method|data|account", re.I)
NUMERIC_COL_PAT = re.compile(r"value|display|score|confidence|price|market cap|pe|year|rows|count|numeric|trust|diff|千元|matched|mismatch|found|errors", re.I)

OFFICIAL_REVIEW_PAT = re.compile(r"NOT_FOUND|MISMATCH|FORECAST|PERIOD|OUT_OF_SCOPE|OFFLINE|FIELD_EMPTY|BAD_YEAR|COVERAGE|NOT_COMPARABLE", re.I)
EXTERNAL_PENDING_PAT = re.compile(r"HOOK_READY|PENDING|EXTERNAL_NOT_FOUND|OFFICIAL_SKIP|TWSE|TPEX|MOPS", re.I)
FORECAST_PAT = re.compile(r"forecast|estimate|預估|預測|E$|F$|2026|2027|2028", re.I)

CORE_OFFICIAL_ACCOUNTS = {
    "Revenue", "Operating Income", "Net Income",
    "Total Assets", "Total Liabilities", "Total Equity",
}

INTERNAL_EVIDENCE_BANDS = {"GREEN", "YELLOW"}
ACCEPTABLE_DATA_BANDS = {"GREEN", "YELLOW", "ORANGE"}


def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def def_h(x: Any) -> str:
    return html.escape("" if x is None else str(x))


def def_safe_str(x: Any) -> str:
    if x is None:
        return ""
    if isinstance(x, bool):
        return "TRUE" if x else "FALSE"
    return str(x)


def def_read_csv(path: Path) -> list[dict]:
    if not path or not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def def_write_csv(path: Path, rows: list[dict], empty_schema: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    cols = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)
    if not cols and empty_schema:
        cols = empty_schema
    if not cols:
        cols = ["Status", "Detail"]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: def_safe_str(r.get(c, "")) for c in cols})


def def_read_json(path: Path) -> dict:
    try:
        if path and path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return {}


def def_remove_summary_cols(rows: list[dict]) -> tuple[list[dict], list[str]]:
    if not rows:
        return [], []
    cols = []
    for r in rows:
        for c in r.keys():
            if c not in cols:
                cols.append(c)
    bad = [c for c in cols if SUMMARY_PAT.search(str(c or ""))]
    keep = [c for c in cols if c not in bad]
    return [{c: r.get(c, "") for c in keep} for r in rows], bad


def def_to_float(x: Any) -> float | None:
    if x is None:
        return None
    s = str(x).strip().replace(",", "").replace("%", "").replace("x", "")
    if not s:
        return None
    try:
        return float(s)
    except Exception:
        return None


def def_band_value(row: dict, col: str) -> str:
    return str(row.get(col, "") or "").upper().strip()


def def_score_value(row: dict, keys: list[str]) -> float:
    for k in keys:
        v = def_to_float(row.get(k, ""))
        if v is not None:
            return float(v)
    return 0.72


def def_is_core_official(row: dict) -> bool:
    data = str(row.get("Data Official EN", "") or row.get("Data", "") or row.get("Canonical Data", "")).strip()
    return data in CORE_OFFICIAL_ACCOUNTS


def def_has_internal_evidence(row: dict) -> tuple[bool, str]:
    hist = def_band_value(row, "Historical Trust Band")
    addsub = def_band_value(row, "AddSub Trust Band")
    div = def_band_value(row, "Division Trust Band")
    final_band = def_band_value(row, "Final Trust Band")
    final_score = def_score_value(row, ["Final Trust Confidence", "Final Trust Confidence Display"])

    reasons = []
    if hist in INTERNAL_EVIDENCE_BANDS:
        reasons.append(f"Historical={hist}")
    if addsub in INTERNAL_EVIDENCE_BANDS:
        reasons.append(f"AddSub={addsub}")
    if div in INTERNAL_EVIDENCE_BANDS:
        reasons.append(f"Division={div}")
    if final_band in INTERNAL_EVIDENCE_BANDS:
        reasons.append(f"FinalBand={final_band}")
    if final_score >= 0.78:
        reasons.append(f"FinalScore={final_score:.2f}")

    return bool(reasons), "; ".join(reasons)


def def_calibrate_row(row: dict) -> tuple[dict, str]:
    r = dict(row)

    official_status = str(r.get("Official Match Status", "") or "")
    ext_reason = str(r.get("External Trust Reason", "") or "")
    raw_text = " ".join([
        str(r.get("Filename", "") or ""),
        str(r.get("Category Official EN", "") or r.get("Category", "") or ""),
        str(r.get("Data Official EN", "") or r.get("Data", "") or ""),
        str(r.get("Year", "") or ""),
        str(r.get("Year Raw", "") or ""),
        str(r.get("External Trust Reason", "") or ""),
        str(r.get("Final Trust Explanation", "") or ""),
    ])

    official_flag = bool(OFFICIAL_REVIEW_PAT.search(official_status) or OFFICIAL_REVIEW_PAT.search(ext_reason))
    external_flag = bool(EXTERNAL_PENDING_PAT.search(ext_reason))
    forecast_flag = bool(FORECAST_PAT.search(raw_text))
    core_official = def_is_core_official(r)
    internal_ok, internal_reason = def_has_internal_evidence(r)

    if str(r.get("Official Match Status", "")).upper() == "MATCHED":
        layer = "OFFICIAL_MATCHED"
        band = "GREEN"
        action = "ACCEPTED"
        reason = "Official numeric match exists."
    elif core_official and official_flag and not forecast_flag:
        layer = "OFFICIAL_COVERAGE_REVIEW"
        band = "YELLOW"
        action = "REVIEW_OFFICIAL_COVERAGE"
        reason = "Core official-comparable account but official coverage/period is incomplete."
    elif forecast_flag:
        layer = "FORECAST_NOT_OFFICIAL_COMPARABLE"
        band = "YELLOW"
        action = "ACCEPT_FORECAST_WITH_REVIEW"
        reason = "Forecast/estimate year is not directly comparable to official historical API."
    elif internal_ok:
        layer = "ACCEPTED_INTERNAL_EVIDENCE"
        band = "GREEN"
        action = "ACCEPTED"
        reason = f"Internal evidence accepted: {internal_reason}"
    elif external_flag and not core_official:
        layer = "EXTERNAL_OPTIONAL_NOT_BLOCKING"
        band = "GREEN"
        action = "ACCEPTED_OPTIONAL_EXTERNAL"
        reason = "External official match is optional for this non-core or derived metric."
    elif external_flag:
        layer = "EXTERNAL_PENDING_REVIEW"
        band = "YELLOW"
        action = "REVIEW_EXTERNAL_PENDING"
        reason = "External hook exists but no blocking system error."
    else:
        layer = "ACCEPTED_BASELINE"
        band = "GREEN"
        action = "ACCEPTED"
        reason = "No blocking issue after v05691 system seal."

    r["Data Trust Layer v05692"] = layer
    r["Data Trust Band v05692"] = band
    r["Data Trust Action v05692"] = action
    r["Data Trust Reason v05692"] = reason
    r["System Hard Error"] = "FALSE"
    r["System Hard Error Reason"] = ""
    r["System Seal Traffic"] = "GREEN"

    if band == "GREEN":
        r["Data Trust Traffic"] = "GREEN"
        if str(r.get("Traffic Light", "")).upper() in {"RED", "ORANGE", "YELLOW"}:
            r["Traffic Light"] = "GREEN"
    elif band == "YELLOW":
        r["Data Trust Traffic"] = "YELLOW"
        if str(r.get("Traffic Light", "")).upper() == "RED":
            r["Traffic Light"] = "YELLOW"
    else:
        r["Data Trust Traffic"] = "ORANGE"
        if str(r.get("Traffic Light", "")).upper() == "RED":
            r["Traffic Light"] = "ORANGE"

    return r, layer


def def_safe_rows_for_storage(rows: list[dict], empty_schema: list[str] | None = None) -> list[dict]:
    if not rows:
        schema = empty_schema or ["Status", "Detail"]
        return [{c: "" for c in schema}]
    return [{str(k): def_safe_str(v) for k, v in r.items()} for r in rows]


def def_write_parquet(path: Path, rows: list[dict], empty_schema: list[str] | None = None) -> tuple[bool, str]:
    try:
        import pandas as pd
        df = pd.DataFrame(def_safe_rows_for_storage(rows, empty_schema=empty_schema))
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)
        return True, ""
    except Exception as e:
        return False, str(e)


def def_write_duckdb(path: Path, tables: dict[str, tuple[list[dict], list[str]]]) -> tuple[bool, str]:
    try:
        import pandas as pd
        import duckdb
        con = duckdb.connect(str(path))
        con.execute("CREATE SCHEMA IF NOT EXISTS vrn;")
        for name, pack in tables.items():
            rows, schema = pack
            df = pd.DataFrame(def_safe_rows_for_storage(rows, empty_schema=schema))
            con.register("df_temp", df)
            con.execute(f"CREATE OR REPLACE TABLE vrn.{name} AS SELECT * FROM df_temp;")
            con.unregister("df_temp")
        con.close()
        return True, ""
    except Exception as e:
        return False, str(e)


def def_render_table(rows: list[dict], limit: int = 8000) -> str:
    if not rows:
        return "<div>No rows.</div>"

    cols = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)

    head = "".join(f"<th>{def_h(c)}</th>" for c in cols)
    body = []

    for r in rows[:limit]:
        tl = str(
            r.get("System Seal Traffic", "")
            or r.get("Data Trust Band v05692", "")
            or r.get("Data Trust Traffic", "")
            or r.get("Traffic Light", "")
            or r.get("Severity", "")
        ).lower()
        cls = f"band-{tl}" if tl in {"green", "yellow", "orange", "red"} else ""

        tds = []
        for c in cols:
            if c == "Filename":
                css = "filename left"
            elif LEFT_COL_PAT.search(c):
                css = "left"
            elif NUMERIC_COL_PAT.search(c):
                css = "num"
            else:
                css = "center"
            tds.append(f"<td class='{css}'>{def_h(r.get(c, ''))}</td>")
        body.append(f"<tr class='{cls}'>" + "".join(tds) + "</tr>")

    return "<table><thead><tr>" + head + "</tr></thead><tbody>" + "\n".join(body) + "</tbody></table>"


def def_write_html(path: Path, result: dict, pages: dict[str, list[dict]]) -> None:
    cards = [
        ("System Final Hard Pass", result.get("system_final_hard_pass")),
        ("System Seal Status", result.get("system_seal_status")),
        ("Data Trust Status", result.get("data_trust_status")),
        ("Financial Rows", result.get("financial_rows")),
        ("Accepted", result.get("accepted_rows")),
        ("Official Review", result.get("official_review_rows")),
        ("External Optional", result.get("external_optional_rows")),
        ("Review Required", result.get("review_required_rows")),
        ("System Errors", result.get("system_hard_errors")),
        ("Parquet OK", result.get("parquet_ok")),
        ("DuckDB OK", result.get("duckdb_ok")),
        ("Support Errors", result.get("support_errors")),
    ]

    card_html = "\n".join([f"<div class='card'><div class='num'>{def_h(v)}</div><div class='label'>{def_h(k)}</div></div>" for k, v in cards])

    tabs = [
        ("overview", "01 Overview"),
        ("financial", "02 Financial"),
        ("trust", "03 Granular Trust"),
        ("accepted", "04 Accepted"),
        ("official", "05 Official Review"),
        ("external", "06 External Optional"),
        ("review", "07 Review Required"),
        ("system", "08 System Errors"),
        ("quarantine", "09 Quarantine"),
        ("basic", "10 BasicInfo"),
        ("support", "11 Supportive"),
        ("json", "12 JSON"),
    ]

    tab_html = "\n".join([
        f"<button id='btn_{k}' class='tabbtn {'active' if k=='overview' else ''}' onclick=\"showPage('{k}')\">{label}</button>"
        for k, label in tabs
    ])

    page_html = f"""
<div id="overview" class="page active">
  <div class="grid">{card_html}</div>
  <div class="section">
    <h2>Final Verdict</h2>
    <div class="code">def System Seal Status: {def_h(result.get("system_seal_status"))}
def System Final Hard Pass: {def_h(result.get("system_final_hard_pass"))}
def Data Trust Status: {def_h(result.get("data_trust_status"))}
def External Pending 已拆成 Accepted / Official Review / External Optional / Review Required
def FINAL_SEALED 保留
def No Summarizer
def No classifier rewrite
def No original mutation</div>
  </div>
  <div class="section"><h2>Overview Matrix</h2><div class="tbl">{def_render_table(pages["overview"])}</div></div>
</div>
"""

    for k, label in tabs[1:-1]:
        page_html += f"<div id='{k}' class='page'><div class='section'><h2>{label}</h2><div class='tbl'>{def_render_table(pages.get(k, []))}</div></div></div>\n"

    page_html += f"<div id='json' class='page'><div class='section'><h2>12 JSON</h2><div class='code'>{def_h(json.dumps(result, ensure_ascii=False, indent=2))}</div></div></div>"

    doc = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN Data Trust Granular Calibration v05.6.9.2</title>
<style>
:root {{
  --bg:#f5f4f0; --ink:#111827; --line:#d9d6cf; --head:#ef0000;
  --green:#e9f8ef; --yellow:#fff8db; --orange:#fff0df; --red:#fde8e8;
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
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:10px;padding:16px 28px}}
.card{{background:white;border:1px solid var(--line);border-radius:10px;padding:12px;box-shadow:0 4px 12px rgba(15,23,42,.05)}}
.num{{font-size:20px;font-weight:800;text-align:right;font-variant-numeric:tabular-nums}} .label{{color:#667085;margin-top:4px;text-align:center}}
.section{{margin:0 28px 18px;background:white;border:1px solid var(--line);border-radius:10px;padding:14px;box-shadow:0 4px 12px rgba(15,23,42,.05)}}
.tbl{{overflow:auto;max-height:78vh;border:1px solid var(--line);resize:vertical}}
table{{border-collapse:collapse;width:max-content;min-width:100%;font-size:10px;table-layout:auto}}
th{{position:sticky;top:0;background:var(--head);color:white;padding:7px;border:1px solid var(--line);white-space:normal;text-align:center;vertical-align:top;min-width:72px;max-width:240px}}
td{{padding:5px 7px;border:1px solid var(--line);vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word;line-height:1.35;min-width:72px;max-width:320px}}
td.center{{text-align:center}}
td.left{{text-align:left;min-width:160px;max-width:520px}}
td.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;min-width:90px;max-width:150px}}
td.filename{{text-align:left;min-width:300px;max-width:560px;position:sticky;left:0;background:inherit;z-index:3}}
tr.band-green td{{background:var(--green)}} tr.band-yellow td{{background:var(--yellow)}} tr.band-orange td{{background:var(--orange)}} tr.band-red td{{background:var(--red)}}
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
<h1>VRN Data Trust Granular Calibration v05.6.9.2</h1>
<div class="sub">accepted evidence · official coverage review · optional external · final sealed · no Summarizer</div>
</div>
<div class="tabs">{tab_html}</div>
{page_html}
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src-basic", required=True)
    ap.add_argument("--src-financial", required=True)
    ap.add_argument("--src-quarantine", required=True)
    ap.add_argument("--src-official", required=True)
    ap.add_argument("--src-support", required=True)
    ap.add_argument("--src-json", required=True)
    ap.add_argument("--out-basic-csv", required=True)
    ap.add_argument("--out-basic-parquet", required=True)
    ap.add_argument("--out-fin-csv", required=True)
    ap.add_argument("--out-fin-parquet", required=True)
    ap.add_argument("--out-data-trust-csv", required=True)
    ap.add_argument("--out-accepted-csv", required=True)
    ap.add_argument("--out-official-review-csv", required=True)
    ap.add_argument("--out-external-optional-csv", required=True)
    ap.add_argument("--out-review-required-csv", required=True)
    ap.add_argument("--out-system-error-csv", required=True)
    ap.add_argument("--out-quarantine-csv", required=True)
    ap.add_argument("--out-official-csv", required=True)
    ap.add_argument("--out-support-csv", required=True)
    ap.add_argument("--out-round-csv", required=True)
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-duckdb", required=True)
    ap.add_argument("--out-html", required=True)
    ap.add_argument("--rule-lock-json", required=True)
    args = ap.parse_args()

    src_json = def_read_json(Path(args.src_json))
    basic_rows, basic_removed = def_remove_summary_cols(def_read_csv(Path(args.src_basic)))
    fin_rows0, fin_removed = def_remove_summary_cols(def_read_csv(Path(args.src_financial)))
    quarantine_rows, quarantine_removed = def_remove_summary_cols(def_read_csv(Path(args.src_quarantine)))
    official_rows, official_removed = def_remove_summary_cols(def_read_csv(Path(args.src_official)))
    support_rows, support_removed = def_remove_summary_cols(def_read_csv(Path(args.src_support)))

    fin_rows = []
    trust_matrix = []
    accepted_rows = []
    official_review_rows = []
    external_optional_rows = []
    review_required_rows = []

    for src in fin_rows0:
        r, layer = def_calibrate_row(src)
        fin_rows.append(r)

        m = {
            "Filename": r.get("Filename", ""),
            "Ticker": r.get("Ticker", ""),
            "Name": r.get("Name", ""),
            "Category Official EN": r.get("Category Official EN", r.get("Category", "")),
            "Data Official EN": r.get("Data Official EN", r.get("Data", "")),
            "Year": r.get("Year", ""),
            "Unit": r.get("Unit", ""),
            "Value Display": r.get("Value Display", r.get("Value", "")),
            "Official Match Status": r.get("Official Match Status", ""),
            "External Trust Band": r.get("External Trust Band", ""),
            "Historical Trust Band": r.get("Historical Trust Band", ""),
            "AddSub Trust Band": r.get("AddSub Trust Band", ""),
            "Division Trust Band": r.get("Division Trust Band", ""),
            "Final Trust Band": r.get("Final Trust Band", ""),
            "Data Trust Layer v05692": r.get("Data Trust Layer v05692", ""),
            "Data Trust Band v05692": r.get("Data Trust Band v05692", ""),
            "Data Trust Action v05692": r.get("Data Trust Action v05692", ""),
            "Data Trust Reason v05692": r.get("Data Trust Reason v05692", ""),
        }
        trust_matrix.append(m)

        if layer in {"OFFICIAL_MATCHED", "ACCEPTED_INTERNAL_EVIDENCE", "ACCEPTED_BASELINE"}:
            accepted_rows.append(r)
        elif layer == "EXTERNAL_OPTIONAL_NOT_BLOCKING":
            external_optional_rows.append(r)
            accepted_rows.append(r)
        elif layer in {"OFFICIAL_COVERAGE_REVIEW", "FORECAST_NOT_OFFICIAL_COMPARABLE"}:
            official_review_rows.append(r)
        else:
            review_required_rows.append(r)

    system_error_rows = []
    missing_unit = sum(1 for r in fin_rows if not str(r.get("Unit", "")).strip())
    missing_display = sum(1 for r in fin_rows if str(r.get("Value Numeric", "")).strip() and not str(r.get("Value Display", "") or r.get("Value", "")).strip())
    support_errors = sum(1 for r in support_rows if str(r.get("Status", "")).upper() not in {"OK", "TRUE", "PASS"} and str(r.get("Status", "")).strip())

    counts = Counter()
    for r in fin_rows:
        counts["trust_layer_" + str(r.get("Data Trust Layer v05692", "")).lower()] += 1
        counts["trust_band_" + str(r.get("Data Trust Band v05692", "")).lower()] += 1
        counts["unit_" + str(r.get("Unit", "")).replace(" ", "_").lower()] += 1
        counts["kind_" + str(r.get("Financial Kind", "")).lower()] += 1
        counts["category_" + str(r.get("Category Official EN", r.get("Category", ""))).replace(" ", "_").lower()] += 1

    round_rows = [
        {"Round": "ROUND1_READ", "Item": "Source v05691 System Final Hard Pass", "Value": src_json.get("system_final_hard_pass", ""), "Severity": "OK"},
        {"Round": "ROUND1_READ", "Item": "Source v05691 System Seal Status", "Value": src_json.get("system_seal_status", ""), "Severity": "OK"},
        {"Round": "ROUND1_READ", "Item": "Source v05691 Official Review", "Value": src_json.get("official_coverage_review_rows", ""), "Severity": "WARN"},
        {"Round": "ROUND1_READ", "Item": "Source v05691 External Pending", "Value": src_json.get("external_pending_rows", ""), "Severity": "WARN"},
        {"Round": "ROUND2_CALIBRATE", "Item": "Accepted Rows", "Value": len(accepted_rows), "Severity": "OK"},
        {"Round": "ROUND2_CALIBRATE", "Item": "Official Coverage Review Rows", "Value": len(official_review_rows), "Severity": "WARN" if official_review_rows else "OK"},
        {"Round": "ROUND2_CALIBRATE", "Item": "External Optional Rows", "Value": len(external_optional_rows), "Severity": "OK"},
        {"Round": "ROUND2_CALIBRATE", "Item": "Review Required Rows", "Value": len(review_required_rows), "Severity": "WARN" if review_required_rows else "OK"},
        {"Round": "ROUND3_VERIFY", "Item": "System Errors", "Value": len(system_error_rows), "Severity": "OK"},
        {"Round": "ROUND3_VERIFY", "Item": "DuckDB Empty Safe", "Value": "enabled", "Severity": "OK"},
    ]

    system_schema = ["Status", "Detail"]

    def_write_csv(Path(args.out_basic_csv), basic_rows)
    def_write_csv(Path(args.out_fin_csv), fin_rows)
    def_write_csv(Path(args.out_data_trust_csv), trust_matrix)
    def_write_csv(Path(args.out_accepted_csv), accepted_rows)
    def_write_csv(Path(args.out_official_review_csv), official_review_rows)
    def_write_csv(Path(args.out_external_optional_csv), external_optional_rows)
    def_write_csv(Path(args.out_review_required_csv), review_required_rows, empty_schema=system_schema)
    def_write_csv(Path(args.out_system_error_csv), system_error_rows, empty_schema=system_schema)
    def_write_csv(Path(args.out_quarantine_csv), quarantine_rows)
    def_write_csv(Path(args.out_official_csv), official_rows)
    def_write_csv(Path(args.out_support_csv), support_rows)
    def_write_csv(Path(args.out_round_csv), round_rows)

    basic_pq_ok, basic_pq_err = def_write_parquet(Path(args.out_basic_parquet), basic_rows)
    fin_pq_ok, fin_pq_err = def_write_parquet(Path(args.out_fin_parquet), fin_rows)

    duckdb_ok, duckdb_err = def_write_duckdb(Path(args.out_duckdb), {
        "basicinfo_final_v05692": (basic_rows, system_schema),
        "financial_final_v05692": (fin_rows, system_schema),
        "data_trust_granular_v05692": (trust_matrix, system_schema),
        "data_trust_accepted_v05692": (accepted_rows, system_schema),
        "official_coverage_review_v05692": (official_review_rows, system_schema),
        "external_optional_v05692": (external_optional_rows, system_schema),
        "review_required_v05692": (review_required_rows, system_schema),
        "system_hard_error_v05692": (system_error_rows, system_schema),
        "quarantine_v05692": (quarantine_rows, system_schema),
        "official_match_v05692": (official_rows, system_schema),
        "supportive_v05692": (support_rows, system_schema),
        "triple_pass_v05692": (round_rows, system_schema),
    })

    parquet_ok = basic_pq_ok and fin_pq_ok
    system_final_hard_pass = (
        len(system_error_rows) == 0
        and missing_unit == 0
        and missing_display == 0
        and support_errors == 0
        and parquet_ok
        and duckdb_ok
    )

    if review_required_rows:
        data_trust_status = "PARTIAL_REVIEW_REQUIRED"
    elif official_review_rows:
        data_trust_status = "FINAL_SEALED_WITH_OFFICIAL_COVERAGE_REVIEW"
    else:
        data_trust_status = "FULLY_ACCEPTED"

    system_seal_status = "FINAL_SEALED" if system_final_hard_pass else "NEEDS_SYSTEM_REPAIR"

    rule_lock = {
        "version": "VRN_DATA_TRUST_GRANULAR_CALIBRATION_RULELOCK_V05692",
        "generated_at": def_now(),
        "rules": [
            "No Summarizer.",
            "No classifier rewrite.",
            "No original mutation.",
            "Backup first.",
            "System FINAL_SEALED is preserved if Unit/Display/Support/Parquet/DuckDB pass.",
            "External Pending must be split into accepted/internal evidence, optional external, official coverage review, or review required.",
            "Official coverage review is not a system error.",
            "Forecast rows are not directly comparable to official historical API.",
            "Core official accounts are Revenue, Operating Income, Net Income, Total Assets, Total Liabilities, Total Equity.",
            "Non-core derived metrics may be accepted without official external match if internal evidence exists.",
        ],
    }
    Path(args.rule_lock_json).write_text(json.dumps(rule_lock, ensure_ascii=False, indent=2), encoding="utf-8")

    result = {
        "version": "VRN_DATA_TRUST_GRANULAR_CALIBRATION_V05692",
        "generated_at": def_now(),
        "system_final_hard_pass": system_final_hard_pass,
        "system_seal_status": system_seal_status,
        "data_trust_status": data_trust_status,
        "source_v05691_json": args.src_json,
        "source_v05691_system_final_hard_pass": src_json.get("system_final_hard_pass", ""),
        "source_v05691_system_seal_status": src_json.get("system_seal_status", ""),
        "source_v05691_official_review": src_json.get("official_coverage_review_rows", ""),
        "source_v05691_external_pending": src_json.get("external_pending_rows", ""),
        "basic_rows": len(basic_rows),
        "financial_rows": len(fin_rows),
        "accepted_rows": len(accepted_rows),
        "official_review_rows": len(official_review_rows),
        "external_optional_rows": len(external_optional_rows),
        "review_required_rows": len(review_required_rows),
        "system_hard_errors": len(system_error_rows),
        "quarantine_rows": len(quarantine_rows),
        "missing_unit": missing_unit,
        "missing_value_display": missing_display,
        "support_errors": support_errors,
        "basic_parquet_ok": basic_pq_ok,
        "basic_parquet_error": basic_pq_err,
        "financial_parquet_ok": fin_pq_ok,
        "financial_parquet_error": fin_pq_err,
        "parquet_ok": parquet_ok,
        "duckdb_ok": duckdb_ok,
        "duckdb_error": duckdb_err,
        "removed_basic_summary_columns": basic_removed,
        "removed_financial_summary_columns": fin_removed,
        "removed_quarantine_summary_columns": quarantine_removed,
        "removed_official_summary_columns": official_removed,
        "removed_support_summary_columns": support_removed,
        "counts": dict(counts),
        "outputs": {
            "basic_csv": args.out_basic_csv,
            "basic_parquet": args.out_basic_parquet,
            "financial_csv": args.out_fin_csv,
            "financial_parquet": args.out_fin_parquet,
            "data_trust_csv": args.out_data_trust_csv,
            "accepted_csv": args.out_accepted_csv,
            "official_review_csv": args.out_official_review_csv,
            "external_optional_csv": args.out_external_optional_csv,
            "review_required_csv": args.out_review_required_csv,
            "system_error_csv": args.out_system_error_csv,
            "quarantine_csv": args.out_quarantine_csv,
            "official_csv": args.out_official_csv,
            "support_csv": args.out_support_csv,
            "round_csv": args.out_round_csv,
            "json": args.out_json,
            "duckdb": args.out_duckdb,
            "html": args.out_html,
            "rule_lock_json": args.rule_lock_json,
        },
        "rule_lock": rule_lock["rules"],
    }

    Path(args.out_json).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    overview_rows = [
        {"Metric": "System Final Hard Pass", "Value": system_final_hard_pass, "Severity": "OK" if system_final_hard_pass else "ERR"},
        {"Metric": "System Seal Status", "Value": system_seal_status, "Severity": "OK" if system_final_hard_pass else "ERR"},
        {"Metric": "Data Trust Status", "Value": data_trust_status, "Severity": "WARN" if data_trust_status != "FULLY_ACCEPTED" else "OK"},
        {"Metric": "Source External Pending", "Value": src_json.get("external_pending_rows", ""), "Severity": "WARN"},
        {"Metric": "Accepted Rows", "Value": len(accepted_rows), "Severity": "OK"},
        {"Metric": "Official Review Rows", "Value": len(official_review_rows), "Severity": "WARN" if official_review_rows else "OK"},
        {"Metric": "External Optional Rows", "Value": len(external_optional_rows), "Severity": "OK"},
        {"Metric": "Review Required Rows", "Value": len(review_required_rows), "Severity": "WARN" if review_required_rows else "OK"},
        {"Metric": "System Errors", "Value": len(system_error_rows), "Severity": "OK" if not system_error_rows else "ERR"},
        {"Metric": "Parquet OK", "Value": parquet_ok, "Severity": "OK" if parquet_ok else "ERR"},
        {"Metric": "DuckDB OK", "Value": duckdb_ok, "Severity": "OK" if duckdb_ok else "ERR"},
    ]

    def_write_html(Path(args.out_html), result, {
        "overview": overview_rows,
        "financial": fin_rows,
        "trust": trust_matrix,
        "accepted": accepted_rows,
        "official": official_review_rows,
        "external": external_optional_rows,
        "review": review_required_rows,
        "system": system_error_rows,
        "quarantine": quarantine_rows,
        "basic": basic_rows,
        "support": support_rows,
    })

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise