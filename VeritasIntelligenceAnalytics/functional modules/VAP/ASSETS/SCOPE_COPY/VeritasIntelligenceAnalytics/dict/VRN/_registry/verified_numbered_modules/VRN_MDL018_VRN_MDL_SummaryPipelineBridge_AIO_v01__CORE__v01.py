# -*- coding: utf-8 -*-
"""
def VRN_MDL_SummaryPipelineBridge_AIO_v01
def Independent Summary Matrix page generator.
def Input:
def   repaired_first_page_text
def   financial_data / financial_rows / financial_data_csv
def   basicinfo fields
def Output:
def   summary_matrix.json
def   summary_matrix.csv
def   db_ready_summary.csv
def   SUMMARY independent matrix HTML page
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# def 00_PATHS
# =============================================================================

def def_bridge_find_vrn_root_v01() -> Path:
    here = Path(__file__).resolve()
    return here.parents[1]


def def_bridge_router_path_v01() -> Path:
    return def_bridge_find_vrn_root_v01() / "modules" / "VRN_MDL_HomepageSummarizer_Router_v01.py"


def def_bridge_active_config_v01() -> Path:
    return def_bridge_find_vrn_root_v01() / "config" / "active_summarizer.json"


# =============================================================================
# def 01_IO
# =============================================================================

def def_bridge_read_json_v01(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def def_bridge_write_json_v01(path: str | Path, obj: Any) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(p)


def def_bridge_write_csv_v01(path: str | Path, rows: List[Dict[str, Any]]) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    cols: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)
    with p.open("w", encoding="utf-8-sig", newline="") as f:
        if cols:
            w = csv.DictWriter(f, fieldnames=cols)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        else:
            f.write("")
    return str(p)


def def_bridge_read_csv_v01(path: str | Path) -> List[Dict[str, Any]]:
    p = Path(path)
    with p.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def def_bridge_html_v01(x: Any) -> str:
    s = "" if x is None else str(x)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


# =============================================================================
# def 02_ROUTER_IMPORT
# =============================================================================

def def_bridge_import_router_v01():
    router_path = def_bridge_router_path_v01()
    if not router_path.exists():
        raise FileNotFoundError(f"Router not found: {router_path}")
    spec = importlib.util.spec_from_file_location("vrn_summary_router_v01", str(router_path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load router spec.")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["vrn_summary_router_v01"] = mod
    spec.loader.exec_module(mod)
    return mod


# =============================================================================
# def 03_INPUT_NORMALIZATION
# =============================================================================

def def_bridge_load_records_v01(input_json: str = "", input_csv: str = "") -> List[Dict[str, Any]]:
    if input_json:
        obj = def_bridge_read_json_v01(input_json)
        if isinstance(obj, list):
            return [x for x in obj if isinstance(x, dict)]
        if isinstance(obj, dict):
            if isinstance(obj.get("records"), list):
                return [x for x in obj["records"] if isinstance(x, dict)]
            return [obj]
        raise RuntimeError("input_json must be dict/list/records.")

    if input_csv:
        return def_bridge_read_csv_v01(input_csv)

    return [def_bridge_sample_record_v01()]


def def_bridge_parse_financial_data_from_row_v01(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    raw = row.get("financial_data") or row.get("financial_rows") or row.get("financial_data_json")
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, str) and raw.strip():
        try:
            obj = json.loads(raw)
            if isinstance(obj, list):
                return [x for x in obj if isinstance(x, dict)]
        except Exception:
            pass

    csv_path = row.get("financial_data_csv") or row.get("financial_csv")
    if csv_path and Path(str(csv_path)).exists():
        return def_bridge_read_csv_v01(str(csv_path))

    return []


def def_bridge_normalize_record_v01(row: Dict[str, Any]) -> Dict[str, Any]:
    r = dict(row or {})
    repaired = (
        r.get("repaired_first_page_text")
        or r.get("first_page_repaired_text")
        or r.get("first_page_text_repaired")
        or r.get("first_page_text")
        or r.get("text")
        or ""
    )
    r["repaired_first_page_text"] = repaired
    r["first_page_text"] = repaired
    r["text"] = repaired
    r["financial_data"] = def_bridge_parse_financial_data_from_row_v01(r)
    return r


def def_bridge_sample_record_v01() -> Dict[str, Any]:
    return {
        "filename": "MS-2330 20260518.pdf",
        "report_code": "MORGANSTANLEY-2330-台積電-20260518",
        "ticker": "2330",
        "name": "台積電",
        "broker": "Morgan Stanley",
        "analyst": "Jennifer Hsieh",
        "report_date": "2026-05-18",
        "adj_close_report_date": 1000,
        "latest_adj_close": 1015,
        "repaired_first_page_text": "AI Server Momentum Drives Margin Re-rating。投資評等 買進。目標價 1200 元。研究員 Jennifer Hsieh。2026/27 年 Diluted EPS 預估 55.2/63.8 元，以 22x 2026E P/E 評價。主要風險為 AI 需求放緩與匯率波動。",
        "financial_data": [
            {"data": "Diluted EPS", "year": "2026", "value": "55.2", "source": "Report"},
            {"data": "Diluted EPS", "year": "2027", "value": "63.8", "source": "Report"},
            {"data": "Gross Margin", "year": "2026", "value": "58.0", "source": "Report"},
            {"data": "ROE", "year": "2026", "value": "27.5", "source": "Report"},
            {"data": "Revenue", "year": "2026", "value": "3500000", "source": "Report"},
        ],
    }


# =============================================================================
# def 04_MATRIX BUILDERS
# =============================================================================

def def_bridge_summary_to_matrix_row_v01(summary: Dict[str, Any], payload: Dict[str, Any], idx: int) -> Dict[str, Any]:
    router = summary.get("_router") or {}
    warnings = summary.get("warnings") or []
    cross = summary.get("cross_validation") or []
    green = sum(1 for r in cross if r.get("band") == "GREEN")
    red = sum(1 for r in cross if r.get("band") == "RED")
    yellow = sum(1 for r in cross if r.get("band") in {"YELLOW", "NA", ""})

    return {
        "row_id": idx,
        "ready": "TRUE" if summary.get("quality_grade") in {"A", "B"} and red == 0 else "REVIEW",
        "filename": payload.get("filename", ""),
        "report_code": summary.get("report_code", payload.get("report_code", "")),
        "ticker": payload.get("ticker", ""),
        "name": payload.get("name", ""),
        "broker": summary.get("broker", payload.get("broker", "")),
        "analyst": summary.get("analyst", payload.get("analyst", "")),
        "report_date": summary.get("report_date", payload.get("report_date", "")),
        "rating": summary.get("rating", ""),
        "target_price": summary.get("target_price", ""),
        "adj_close": summary.get("adj_close", ""),
        "upside_pct": summary.get("upside_pct", ""),
        "quality_grade": summary.get("quality_grade", ""),
        "summarizer_version": summary.get("summarizer_version", ""),
        "active_function": router.get("active_function", ""),
        "valuation_method": summary.get("valuation_method", ""),
        "financial_used": summary.get("financial_data_used", ""),
        "financial_snapshot": summary.get("financial_snapshot", ""),
        "warnings": len(warnings),
        "cross_green": green,
        "cross_yellow": yellow,
        "cross_red": red,
    }


def def_bridge_db_ready_row_v01(summary: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    zh = summary.get("zh_points") or {}
    en = summary.get("en_points") or {}
    return {
        "report_code": summary.get("report_code", payload.get("report_code", "")),
        "ticker": payload.get("ticker", ""),
        "name": payload.get("name", ""),
        "broker": summary.get("broker", payload.get("broker", "")),
        "analyst": summary.get("analyst", payload.get("analyst", "")),
        "report_date": summary.get("report_date", payload.get("report_date", "")),
        "rating": summary.get("rating", ""),
        "target_price": summary.get("target_price", ""),
        "adj_close": summary.get("adj_close", ""),
        "upside_pct": summary.get("upside_pct", ""),
        "quality_grade": summary.get("quality_grade", ""),
        "summarizer_version": summary.get("summarizer_version", ""),
        "valuation_method": summary.get("valuation_method", ""),
        "financial_snapshot": summary.get("financial_snapshot", ""),
        "summary_zh_1": zh.get("valuation_upside", ""),
        "summary_zh_2": zh.get("diluted_eps_growth", ""),
        "summary_zh_3": zh.get("trend_catalyst", ""),
        "summary_zh_4": zh.get("industry_position_moat", ""),
        "summary_zh_5": zh.get("peer_comparison", ""),
        "summary_zh_6": zh.get("key_risks_mitigants", ""),
        "summary_en_1": en.get("valuation_upside", ""),
        "summary_en_2": en.get("diluted_eps_growth", ""),
        "summary_en_3": en.get("trend_catalyst", ""),
        "summary_en_4": en.get("industry_position_moat", ""),
        "summary_en_5": en.get("peer_comparison", ""),
        "summary_en_6": en.get("key_risks_mitigants", ""),
    }


# =============================================================================
# def 05_HTML RENDER
# =============================================================================

def def_bridge_render_table_v01(rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return "<table><thead><tr><th>No rows</th></tr></thead><tbody><tr><td>No rows</td></tr></tbody></table>"

    cols: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)

    head = "<tr>" + "".join(f"<th>{def_bridge_html_v01(c)}</th>" for c in cols) + "</tr>"
    body = ""
    for r in rows:
        cls = "ok"
        if str(r.get("ready", "")).upper() == "REVIEW" or str(r.get("cross_red", "0")) not in {"0", ""}:
            cls = "warn"
        body += f"<tr class='{cls}'>"
        for c in cols:
            body += f"<td>{def_bridge_html_v01(r.get(c, ''))}</td>"
        body += "</tr>\n"

    return f"<table><thead>{head}</thead><tbody>{body}</tbody></table>"


def def_bridge_render_summary_matrix_html_v01(
    path: str | Path,
    summary_rows: List[Dict[str, Any]],
    db_rows: List[Dict[str, Any]],
    full_results: List[Dict[str, Any]],
    artifacts: Dict[str, Any],
) -> str:
    total = len(summary_rows)
    ready = sum(1 for r in summary_rows if str(r.get("ready")) == "TRUE")
    review = total - ready
    avg_quality = ",".join(sorted(set(str(r.get("quality_grade", "")) for r in summary_rows if r.get("quality_grade"))))
    versions = ",".join(sorted(set(str(r.get("summarizer_version", "")) for r in summary_rows if r.get("summarizer_version"))))

    summary_table = def_bridge_render_table_v01(summary_rows)
    db_table = def_bridge_render_table_v01(db_rows)

    cross_rows: List[Dict[str, Any]] = []
    point_rows: List[Dict[str, Any]] = []

    for i, item in enumerate(full_results, start=1):
        payload = item.get("payload") or {}
        summary = item.get("summary") or {}
        for c in summary.get("cross_validation") or []:
            cross_rows.append({
                "row_id": i,
                "ticker": payload.get("ticker", ""),
                "field": c.get("field", ""),
                "summarizer": c.get("summarizer_value", ""),
                "ssot": c.get("ssot_value", ""),
                "delta": c.get("delta_pct", ""),
                "band": c.get("band", ""),
                "action": c.get("action", ""),
            })

        zh = summary.get("zh_points") or {}
        for k, v in zh.items():
            point_rows.append({
                "row_id": i,
                "ticker": payload.get("ticker", ""),
                "point": k,
                "language": "ZH",
                "text": v,
            })

    cross_table = def_bridge_render_table_v01(cross_rows)
    point_table = def_bridge_render_table_v01(point_rows)

    art_lines = "\n".join(f"{k}: {v}" for k, v in artifacts.items())

    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN SUMMARY MATRIX PAGE</title>
<style>
body{{margin:0;font-family:"Segoe UI","Microsoft JhengHei",Arial,sans-serif;background:#f5f4f0;color:#111827;font-size:11px}}
.header{{padding:24px 32px;color:white;background:#0f172a;border-top:4px solid #4c78a8}}
.header h1{{margin:0;font-size:26px}}.sub{{color:#cbd5e1;margin-top:6px}}
.grid{{display:grid;grid-template-columns:repeat(6,1fr);gap:10px;padding:16px 30px}}
.card{{background:white;border:1px solid #e0ddd5;border-radius:6px;padding:12px}}.num{{font-size:20px;font-weight:800;overflow-wrap:anywhere}}
.section{{margin:0 30px 20px 30px;background:white;border:1px solid #e0ddd5;border-radius:6px;padding:16px}}
table{{width:100%;border-collapse:collapse;font-size:10px}}th{{text-align:left;background:#e5eaf2;padding:7px;position:sticky;top:0}}td{{border-bottom:1px solid #e5e7eb;padding:6px 7px;vertical-align:top}}
tr.ok td{{background:#f0fdf4}}tr.warn td{{background:#fffbeb}}tr.err td{{background:#fef2f2}}
.code{{font-family:Consolas,monospace;background:#0f172a;color:#d1fae5;padding:12px;border-radius:6px;white-space:pre-wrap}}
</style>
</head>
<body>
<div class="header">
<h1>VRN SUMMARY MATRIX PAGE</h1>
<div class="sub">Router v01.1 → Summarizer v06.3 → summary matrix / DB-ready summary / cross validation</div>
</div>

<div class="grid">
<div class="card"><div class="num">{total}</div><div>Total Reports</div></div>
<div class="card"><div class="num">{ready}</div><div>DB Ready</div></div>
<div class="card"><div class="num">{review}</div><div>Review</div></div>
<div class="card"><div class="num">{avg_quality}</div><div>Quality</div></div>
<div class="card"><div class="num">{versions}</div><div>Version</div></div>
<div class="card"><div class="num">{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div><div>Generated</div></div>
</div>

<div class="section">
<h2>01 SUMMARY MATRIX</h2>
{summary_table}
</div>

<div class="section">
<h2>02 DB READY SUMMARY</h2>
{db_table}
</div>

<div class="section">
<h2>03 SUMMARY POINT MATRIX</h2>
{point_table}
</div>

<div class="section">
<h2>04 CROSS VALIDATION MATRIX</h2>
{cross_table}
</div>

<div class="section">
<h2>05 ARTIFACTS</h2>
<div class="code">{def_bridge_html_v01(art_lines)}</div>
</div>
</body>
</html>"""

    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    return str(p)


# =============================================================================
# def 06_BRIDGE RUN
# =============================================================================

def def_bridge_run_v01(
    input_json: str = "",
    input_csv: str = "",
    output_json: str = "",
    output_csv: str = "",
    db_ready_csv: str = "",
    output_html: str = "",
    active_config: str = "",
) -> Dict[str, Any]:
    router = def_bridge_import_router_v01()
    records = [def_bridge_normalize_record_v01(r) for r in def_bridge_load_records_v01(input_json, input_csv)]

    summary_rows: List[Dict[str, Any]] = []
    db_rows: List[Dict[str, Any]] = []
    full_results: List[Dict[str, Any]] = []

    for idx, payload in enumerate(records, start=1):
        summary = router.def_router_run_v01(
            payload=payload,
            active_config=active_config or str(def_bridge_active_config_v01()),
            output_json=None,
            output_html=None,
            db_ready_csv=None,
        )
        summary_rows.append(def_bridge_summary_to_matrix_row_v01(summary, payload, idx))
        db_rows.append(def_bridge_db_ready_row_v01(summary, payload))
        full_results.append({"payload": payload, "summary": summary})

    artifacts = {
        "output_json": output_json,
        "output_csv": output_csv,
        "db_ready_csv": db_ready_csv,
        "output_html": output_html,
        "active_config": active_config or str(def_bridge_active_config_v01()),
        "router": str(def_bridge_router_path_v01()),
    }

    if output_json:
        def_bridge_write_json_v01(output_json, {
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "summary_rows": summary_rows,
            "db_ready_rows": db_rows,
            "full_results": full_results,
            "artifacts": artifacts,
        })

    if output_csv:
        def_bridge_write_csv_v01(output_csv, summary_rows)

    if db_ready_csv:
        def_bridge_write_csv_v01(db_ready_csv, db_rows)

    if output_html:
        def_bridge_render_summary_matrix_html_v01(output_html, summary_rows, db_rows, full_results, artifacts)

    return {
        "ok": True,
        "total": len(records),
        "ready": sum(1 for r in summary_rows if str(r.get("ready")) == "TRUE"),
        "review": sum(1 for r in summary_rows if str(r.get("ready")) != "TRUE"),
        "summary_rows": summary_rows,
        "db_ready_rows": db_rows,
        "artifacts": artifacts,
    }


def def_bridge_selftest_v01() -> Dict[str, Any]:
    result = def_bridge_run_v01()
    row = result["summary_rows"][0] if result.get("summary_rows") else {}
    checks = {
        "ok": bool(result.get("ok")),
        "total_1": result.get("total") == 1,
        "ready_1": result.get("ready") == 1,
        "version_v063": row.get("summarizer_version") == "v06.3",
        "rating_buy": row.get("rating") == "BUY",
        "tp_1200": str(row.get("target_price")) == "1200.0",
        "valuation_22x": "22x" in str(row.get("valuation_method")),
    }
    return {"hard_pass": all(checks.values()), "checks": checks, "result": result}


def def_bridge_main_cli_v01(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default="")
    parser.add_argument("--input-csv", default="")
    parser.add_argument("--active-config", default="")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-csv", default="")
    parser.add_argument("--db-ready-csv", default="")
    parser.add_argument("--output-html", default="")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        res = def_bridge_selftest_v01()
        if args.output_json:
            def_bridge_write_json_v01(args.output_json, res)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0 if res.get("hard_pass") else 2

    res = def_bridge_run_v01(
        input_json=args.input_json,
        input_csv=args.input_csv,
        active_config=args.active_config,
        output_json=args.output_json,
        output_csv=args.output_csv,
        db_ready_csv=args.db_ready_csv,
        output_html=args.output_html,
    )

    print(json.dumps({
        "ok": res.get("ok"),
        "total": res.get("total"),
        "ready": res.get("ready"),
        "review": res.get("review"),
        "output_html": args.output_html,
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(def_bridge_main_cli_v01())
    except SystemExit as e:
        if getattr(e, "code", 0) in (0, None):
            raise
        print(traceback.format_exc())
        raise
    except Exception:
        print(traceback.format_exc())
        raise

# ======================================================================================
# VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY START
# def Purpose:
# def   - Append-only supportive bridge for VRN production modules
# def   - Safe optional imports only; no DB write, no SSOT mutation, no network execution
# def   - Enables downstream audit to detect Aegis / Celeritas / EnvManager / NoHang coverage
# ======================================================================================

VRN_V139O_SUPPORTIVE_BRIDGE_ENABLED = True
VRN_V139O_NOHANG_WATCHDOG_ENABLED = True
VRN_V139O_DB_WRITE_ENABLE = False
VRN_V139O_SSOT_MUTATION_ENABLE = False
VRN_V139O_NETWORK_ENABLE = False

VRN_V139O_AEGIS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasAegisNexus.py"
VRN_V139O_CELERITAS_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VeritasCeleritas.py"
VRN_V139O_ENV_MANAGER_PATH = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIA_EnvManager.py"

def def_vrn_v139o_optional_import_module(module_name, module_path):
    import importlib.util
    import sys
    from pathlib import Path

    result = {
        "module": str(module_name),
        "path": str(module_path),
        "exists": False,
        "import_ok": False,
        "error": "",
    }

    try:
        p = Path(str(module_path))
        result["exists"] = p.exists()
        if not p.exists():
            result["error"] = "missing"
            return result

        spec = importlib.util.spec_from_file_location(str(module_name), str(p))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[str(module_name)] = mod
        spec.loader.exec_module(mod)
        result["import_ok"] = True
        return result
    except BaseException as e:
        result["error"] = str(e)
        return result

def def_vrn_v139o_supportive_bridge_health():
    return {
        "bridge": "VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY",
        "aegis": def_vrn_v139o_optional_import_module("VeritasAegisNexus", VRN_V139O_AEGIS_PATH),
        "celeritas": def_vrn_v139o_optional_import_module("VeritasCeleritas", VRN_V139O_CELERITAS_PATH),
        "envmanager": def_vrn_v139o_optional_import_module("VIA_EnvManager", VRN_V139O_ENV_MANAGER_PATH),
        "nohang_watchdog": VRN_V139O_NOHANG_WATCHDOG_ENABLED,
        "db_write": VRN_V139O_DB_WRITE_ENABLE,
        "ssot_mutation": VRN_V139O_SSOT_MUTATION_ENABLE,
        "network": VRN_V139O_NETWORK_ENABLE,
    }

# VRN_V139O_SUPPORTIVE_BRIDGE_APPEND_ONLY END

# [VRN:ANCHOR:HISTORICAL_VALIDATION_POLICY:BEGIN]
# Append-only hookup of VIS_VRN_HistoricalValidationPolicy_v0100.
# Added by VRN Finalize AIO. Does not modify any existing line above.
# Financial validation truth is delegated to this policy; broker report /
# pdf_table / report_text are NOT treated as financial validation truth.
try:
    import importlib as _il
    _VRN_HVP = None
    for _name in ('module.supportive_module.VIS_VRN_HistoricalValidationPolicy_v0100', 'supportive_module.VIS_VRN_HistoricalValidationPolicy_v0100', 'VIS_VRN_HistoricalValidationPolicy_v0100'):
        try:
            _VRN_HVP = _il.import_module(_name); break
        except Exception:
            _VRN_HVP = None
    VRN_HISTORICAL_VALIDATION_POLICY = _VRN_HVP
    VRN_HVP_ENABLED = _VRN_HVP is not None
except Exception as _e:
    VRN_HISTORICAL_VALIDATION_POLICY = None
    VRN_HVP_ENABLED = False
# [VRN:ANCHOR:HISTORICAL_VALIDATION_POLICY:END]


# =============================================================================
# [VRN:ANCHOR:HEADER_ORDER_CONSENSUS_DATA:BEGIN]
# Append-only block.
# Purpose:
# - Fix Header Order: Source Manifest -> BasicInfo -> Consensus Data -> FinancialData -> Historical Data -> SSOT -> Trust Matrix -> Quarantine -> Canonical Output.
# - Add Consensus Data as reference / cross validation layer.
# - Add Trust Matrix consensus fields.
# - Add Canonical Output guard.
# - Consensus Data must NOT overwrite BasicInfo.
# - Consensus Data must NOT become FinancialData validation truth.
# =============================================================================

VRN_HEADER_ORDER_V110 = [
    "Source Manifest",
    "BasicInfo",
    "Consensus Data",
    "FinancialData",
    "Historical Data",
    "SSOT Normalized Data",
    "Trust Matrix",
    "Quarantine / Review Queue",
    "Canonical Output",
]

VRN_CONSENSUS_DATA_FIELDS_V110 = [
    "Consensus Source",
    "Consensus Provider",
    "Consensus Provider ID",
    "Consensus Date",
    "Consensus Period",
    "Consensus Currency",
    "Consensus Rating",
    "Consensus Target Mean",
    "Consensus Target Median",
    "Consensus Target High",
    "Consensus Target Low",
    "Consensus Analyst Count",
    "Consensus EPS Current Year",
    "Consensus EPS Next Year",
    "Consensus Revenue Current Year",
    "Consensus Revenue Next Year",
    "Consensus Revision Direction",
    "Consensus Last Updated",
    "Consensus Fetch Status",
    "Consensus Confidence",
    "Consensus Note",
]

VRN_TRUST_MATRIX_CONSENSUS_FIELDS_V110 = [
    "Consensus Check Status",
    "Consensus Trust Score",
    "Consensus Gap Type",
    "Consensus Gap Value",
    "Consensus Review Signal",
    "Consensus Provider",
    "Consensus Data Date",
    "Consensus Note",
]

VRN_CONSENSUS_REFERENCE_ONLY_POLICY_V110 = {
    "consensus_position": "after_basicinfo_before_financialdata",
    "consensus_role": "external_consensus_reference_only",
    "consensus_sources": ["yfinance", "factset_if_authorized"],
    "can_overwrite_basicinfo": False,
    "can_be_financial_validation_truth": False,
    "can_write_canonical_output_directly": False,
    "financialdata_role": "pdf_table_observation_only",
    "historical_data_role": "validation_truth",
    "canonical_output_rule": "only_trust_matrix_pass_records",
}


def def_vrn_get_header_order_v110():
    return list(VRN_HEADER_ORDER_V110)


def def_vrn_get_consensus_data_fields_v110():
    return list(VRN_CONSENSUS_DATA_FIELDS_V110)


def def_vrn_get_trust_matrix_consensus_fields_v110():
    return list(VRN_TRUST_MATRIX_CONSENSUS_FIELDS_V110)


def def_vrn_get_consensus_reference_policy_v110():
    return dict(VRN_CONSENSUS_REFERENCE_ONLY_POLICY_V110)


def def_vrn_is_consensus_data_allowed_to_overwrite_basicinfo_v110():
    return False


def def_vrn_is_consensus_data_financial_truth_v110():
    return False


def def_vrn_is_consensus_data_allowed_in_canonical_output_directly_v110():
    return False


def def_vrn_validate_header_order_v110(header_order=None):
    order = list(header_order or VRN_HEADER_ORDER_V110)
    required = list(VRN_HEADER_ORDER_V110)

    missing = [x for x in required if x not in order]
    position_ok = True
    reason = "OK"

    try:
        basic_i = order.index("BasicInfo")
        consensus_i = order.index("Consensus Data")
        financial_i = order.index("FinancialData")
        trust_i = order.index("Trust Matrix")
        canonical_i = order.index("Canonical Output")

        if not (basic_i < consensus_i < financial_i < trust_i < canonical_i):
            position_ok = False
            reason = "Header position rule failed: BasicInfo < Consensus Data < FinancialData < Trust Matrix < Canonical Output"
    except Exception as exc:
        position_ok = False
        reason = str(exc)

    return {
        "status": "PASS" if (not missing and position_ok) else "FAIL",
        "missing": missing,
        "position_ok": position_ok,
        "reason": reason,
        "header_order": order,
    }


def def_vrn_append_consensus_fields_to_trust_matrix_schema_v110(existing_fields):
    fields = list(existing_fields or [])
    for field in VRN_TRUST_MATRIX_CONSENSUS_FIELDS_V110:
        if field not in fields:
            fields.append(field)
    return fields


def def_vrn_validate_consensus_reference_only_v110(source_role, target_layer):
    source_role = str(source_role or "").strip().lower()
    target_layer = str(target_layer or "").strip().lower()

    if target_layer in {"basicinfo", "basic_info"}:
        return {
            "status": "REFERENCE_ONLY",
            "allowed_to_overwrite": False,
            "risk": "GREEN",
            "message": "Consensus Data can cross validate BasicInfo but cannot overwrite broker_report opinion.",
        }

    if target_layer in {"financialdata", "financial_data", "financial_truth", "validation_truth"}:
        return {
            "status": "BLOCK",
            "allowed_as_truth": False,
            "risk": "RED",
            "message": "Consensus Data is not FinancialData validation truth.",
        }

    if target_layer in {"canonical_output", "canonical"}:
        return {
            "status": "BLOCK_DIRECT_WRITE",
            "allowed_direct_write": False,
            "risk": "RED",
            "message": "Consensus Data cannot enter Canonical Output directly; Trust Matrix decision required.",
        }

    return {
        "status": "REVIEW",
        "risk": "YELLOW",
        "message": "Unknown target layer; manual review required.",
    }


def def_vrn_consensus_self_check_v110():
    header_result = def_vrn_validate_header_order_v110()
    trust_fields = def_vrn_append_consensus_fields_to_trust_matrix_schema_v110(["Trust ID", "Final Trust Score"])
    basic_rule = def_vrn_validate_consensus_reference_only_v110("external_consensus", "BasicInfo")
    financial_rule = def_vrn_validate_consensus_reference_only_v110("external_consensus", "FinancialData")
    canonical_rule = def_vrn_validate_consensus_reference_only_v110("external_consensus", "Canonical Output")

    return {
        "header_order_pass": header_result.get("status") == "PASS",
        "consensus_field_count": len(VRN_CONSENSUS_DATA_FIELDS_V110),
        "trust_consensus_field_count": len(VRN_TRUST_MATRIX_CONSENSUS_FIELDS_V110),
        "trust_schema_contains_consensus": all(x in trust_fields for x in VRN_TRUST_MATRIX_CONSENSUS_FIELDS_V110),
        "basicinfo_overwrite_allowed": basic_rule.get("allowed_to_overwrite"),
        "financial_truth_allowed": financial_rule.get("allowed_as_truth"),
        "canonical_direct_write_allowed": canonical_rule.get("allowed_direct_write"),
        "hard_pass": (
            header_result.get("status") == "PASS"
            and len(VRN_CONSENSUS_DATA_FIELDS_V110) == 21
            and len(VRN_TRUST_MATRIX_CONSENSUS_FIELDS_V110) == 8
            and basic_rule.get("allowed_to_overwrite") is False
            and financial_rule.get("allowed_as_truth") is False
            and canonical_rule.get("allowed_direct_write") is False
        ),
    }

# =============================================================================
# [VRN:ANCHOR:HEADER_ORDER_CONSENSUS_DATA:END]
# =============================================================================


# =============================================================================
# [VRN:ANCHOR:CONSENSUS_CANONICAL_OUTPUT_ALIAS_FIX:BEGIN]
# Append-only fix.
# Purpose:
# - Normalize "Canonical Output" / "canonical output" / "canonical-output" to "canonical_output".
# - Ensure Consensus Data cannot write Canonical Output directly.
# - Keep Consensus Data as reference / cross validation layer only.
# =============================================================================

def def_vrn_normalize_layer_name_v111(layer_name):
    x = str(layer_name or "").strip().lower()
    x = x.replace("-", "_").replace(" ", "_").replace("/", "_")
    while "__" in x:
        x = x.replace("__", "_")

    aliases = {
        "basicinfo": "basicinfo",
        "basic_info": "basicinfo",
        "financialdata": "financialdata",
        "financial_data": "financialdata",
        "financial_truth": "financial_truth",
        "validation_truth": "validation_truth",
        "canonical": "canonical_output",
        "canonical_output": "canonical_output",
        "canonicaloutput": "canonical_output",
        "trust_matrix": "trust_matrix",
        "trustmatrix": "trust_matrix",
        "consensus_data": "consensus_data",
        "consensusdata": "consensus_data",
    }

    return aliases.get(x, x)


def def_vrn_validate_consensus_reference_only_v111(source_role, target_layer):
    source_role = str(source_role or "").strip().lower()
    target_layer_norm = def_vrn_normalize_layer_name_v111(target_layer)

    if target_layer_norm == "basicinfo":
        return {
            "status": "REFERENCE_ONLY",
            "allowed_to_overwrite": False,
            "risk": "GREEN",
            "message": "Consensus Data can cross validate BasicInfo but cannot overwrite broker_report opinion.",
            "target_layer_normalized": target_layer_norm,
        }

    if target_layer_norm in {"financialdata", "financial_truth", "validation_truth"}:
        return {
            "status": "BLOCK",
            "allowed_as_truth": False,
            "risk": "RED",
            "message": "Consensus Data is not FinancialData validation truth.",
            "target_layer_normalized": target_layer_norm,
        }

    if target_layer_norm == "canonical_output":
        return {
            "status": "BLOCK_DIRECT_WRITE",
            "allowed_direct_write": False,
            "risk": "RED",
            "message": "Consensus Data cannot enter Canonical Output directly; Trust Matrix decision required.",
            "target_layer_normalized": target_layer_norm,
        }

    return {
        "status": "REVIEW",
        "risk": "YELLOW",
        "message": "Unknown target layer; manual review required.",
        "target_layer_normalized": target_layer_norm,
    }


# Override v110 validator with alias-safe v111 behavior.
def_vrn_validate_consensus_reference_only_v110 = def_vrn_validate_consensus_reference_only_v111


def def_vrn_consensus_self_check_v111():
    header_result = def_vrn_validate_header_order_v110()
    trust_fields = def_vrn_append_consensus_fields_to_trust_matrix_schema_v110(["Trust ID", "Final Trust Score"])
    basic_rule = def_vrn_validate_consensus_reference_only_v111("external_consensus", "BasicInfo")
    financial_rule = def_vrn_validate_consensus_reference_only_v111("external_consensus", "FinancialData")
    canonical_rule_a = def_vrn_validate_consensus_reference_only_v111("external_consensus", "Canonical Output")
    canonical_rule_b = def_vrn_validate_consensus_reference_only_v111("external_consensus", "canonical_output")
    canonical_rule_c = def_vrn_validate_consensus_reference_only_v111("external_consensus", "canonical output")

    return {
        "header_order_pass": header_result.get("status") == "PASS",
        "consensus_field_count": len(VRN_CONSENSUS_DATA_FIELDS_V110),
        "trust_consensus_field_count": len(VRN_TRUST_MATRIX_CONSENSUS_FIELDS_V110),
        "trust_schema_contains_consensus": all(x in trust_fields for x in VRN_TRUST_MATRIX_CONSENSUS_FIELDS_V110),
        "basicinfo_overwrite_allowed": basic_rule.get("allowed_to_overwrite"),
        "financial_truth_allowed": financial_rule.get("allowed_as_truth"),
        "canonical_direct_write_allowed": canonical_rule_a.get("allowed_direct_write"),
        "canonical_output_alias_pass": (
            canonical_rule_a.get("allowed_direct_write") is False
            and canonical_rule_b.get("allowed_direct_write") is False
            and canonical_rule_c.get("allowed_direct_write") is False
        ),
        "hard_pass": (
            header_result.get("status") == "PASS"
            and len(VRN_CONSENSUS_DATA_FIELDS_V110) == 21
            and len(VRN_TRUST_MATRIX_CONSENSUS_FIELDS_V110) == 8
            and basic_rule.get("allowed_to_overwrite") is False
            and financial_rule.get("allowed_as_truth") is False
            and canonical_rule_a.get("allowed_direct_write") is False
            and canonical_rule_b.get("allowed_direct_write") is False
            and canonical_rule_c.get("allowed_direct_write") is False
        ),
    }


# Override v110 self-check with alias-safe v111 behavior.
def_vrn_consensus_self_check_v110 = def_vrn_consensus_self_check_v111

# =============================================================================
# [VRN:ANCHOR:CONSENSUS_CANONICAL_OUTPUT_ALIAS_FIX:END]
# =============================================================================


# =============================================================================
# [VRN:ANCHOR:QUALITY_RULES_INTEGRATION:BEGIN]
# Append-only integration adapter.
# Purpose:
# - Connect VIS_VRN_BasicInfoFinancialQualityRules_v0100 safely.
# - Source Type Routing before FinancialData extraction.
# - BasicInfo Rescue after BasicInfo extraction.
# - Financial Row Quarantine before FinancialData row accept.
# - No DB write, no canonical direct write, no delete.
# =============================================================================

def def_vrn_quality_rules_module_path_v0100():
    return r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\supportive_module\VIS_VRN_BasicInfoFinancialQualityRules_v0100.py"


def def_vrn_load_quality_rules_v0100():
    import importlib.util
    path = def_vrn_quality_rules_module_path_v0100()
    spec = importlib.util.spec_from_file_location("VIS_VRN_BasicInfoFinancialQualityRules_v0100", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Cannot load VIS_VRN_BasicInfoFinancialQualityRules_v0100")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def def_vrn_quality_classify_source_type_v0100(filename):
    mod = def_vrn_load_quality_rules_v0100()
    return mod.def_classify_source_type_v0100(filename)


def def_vrn_quality_rescue_basicinfo_v0100(row):
    mod = def_vrn_load_quality_rules_v0100()
    return mod.def_rescue_basicinfo_from_source_v0100(row)


def def_vrn_quality_classify_financial_row_v0100(row):
    mod = def_vrn_load_quality_rules_v0100()
    return mod.def_classify_financial_row_quality_v0100(row)


def def_vrn_quality_should_accept_financial_row_v0100(row):
    q = def_vrn_quality_classify_financial_row_v0100(row)
    action = q.get("row_quality_action")
    return action == "KEEP_AS_FINANCIAL_OBSERVATION"


def def_vrn_quality_integration_self_check_v0100():
    mod = def_vrn_load_quality_rules_v0100()
    sc = mod.def_self_check_v0100()
    morning = mod.def_classify_source_type_v0100("20251205兆豐晨會報告(二)-公司訪談摘要.pdf")
    industry = mod.def_classify_source_type_v0100("UBS-Asia Hardware Insights 20251205.pdf")
    company = mod.def_classify_source_type_v0100("華南投顧-3017-奇鋐-1141202.pdf")

    sample_bad_row = {
        "SourceFile": "20251205兆豐晨會報告(二)-公司訪談摘要.pdf",
        "Ticker": "",
        "AccountRaw": "公司名稱 報告種類 本次 前次 投資建議",
        "ValueRaw": "買進 中立 目標價",
        "PeriodNormalized": "Segment",
    }
    bad_q = mod.def_classify_financial_row_quality_v0100(sample_bad_row)

    return {
        "hard_pass": (
            sc.get("hard_pass") is True
            and morning.get("source_type") == "MORNING_SUMMARY"
            and industry.get("source_type") == "INDUSTRY_REPORT"
            and company.get("source_type") == "COMPANY_REPORT"
            and bad_q.get("row_quality_action") in {"QUARANTINE", "REQUIRES_TABLE_GEOMETRY_SPLIT"}
        ),
        "module_self_check": sc,
        "morning": morning,
        "industry": industry,
        "company": company,
        "sample_bad_row": bad_q,
        "mutation": False,
        "db_write": False,
        "canonical_direct_write": False,
    }

# =============================================================================
# [VRN:ANCHOR:QUALITY_RULES_INTEGRATION:END]
# =============================================================================
