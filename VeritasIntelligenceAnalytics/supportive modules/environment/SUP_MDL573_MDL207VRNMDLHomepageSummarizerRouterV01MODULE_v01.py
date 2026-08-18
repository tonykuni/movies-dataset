# -*- coding: utf-8 -*-
"""
def VRN_MDL_HomepageSummarizer_Router_v01
def Router for active VRN homepage summarizer.
def Reads config/active_summarizer.json.
def Loads active module dynamically.
def Sends repaired_first_page_text + financial_data to active summarizer.
def Outputs summary_json, summary_html, and db_ready_summary.csv.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# def 00_PATHS
# =============================================================================

def def_router_find_vrn_root_v01() -> Path:
    here = Path(__file__).resolve()
    # ...\VRN\modules\this.py -> VRN
    return here.parents[1]


def def_router_default_active_config_v01() -> Path:
    return def_router_find_vrn_root_v01() / "config" / "active_summarizer.json"


# =============================================================================
# def 01_IO
# =============================================================================

def def_router_read_json_v01(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8"))


def def_router_write_json_v01(path: str | Path, obj: Any) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return str(p)


def def_router_html_escape_v01(value: Any) -> str:
    s = "" if value is None else str(value)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def def_router_get_v01(obj: Dict[str, Any], key: str, default: Any = "") -> Any:
    if not isinstance(obj, dict):
        return default
    return obj.get(key, default)


# =============================================================================
# def 02_ACTIVE_MODULE
# =============================================================================

def def_router_load_active_config_v01(active_config: str | Path | None = None) -> Dict[str, Any]:
    config_path = Path(active_config) if active_config else def_router_default_active_config_v01()
    cfg = def_router_read_json_v01(config_path)
    cfg["_active_config_path"] = str(config_path)
    return cfg


def def_router_resolve_module_path_v01(cfg: Dict[str, Any]) -> Path:
    module_path = cfg.get("module_path") or cfg.get("path")
    if not module_path:
        raise RuntimeError("active_summarizer.json missing module_path")
    p = Path(module_path)
    if not p.exists():
        raise FileNotFoundError(f"active summarizer module not found: {p}")
    return p


def def_router_import_module_from_path_v01(path: str | Path):
    p = Path(path)
    module_name = "vrn_active_summarizer_" + p.stem
    spec = importlib.util.spec_from_file_location(module_name, str(p))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot create import spec: {p}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = mod
    spec.loader.exec_module(mod)
    return mod







def def_router_find_summarize_function_v01(mod: Any):
    # v01.5: prefer v06.7 pre-extracted report date priority first.
    candidates = [
        "def_summarize_homepage_v067",
        "def_summarize_homepage_v066",
        "def_summarize_homepage_v065",
        "def_summarize_homepage_v064",
        "def_summarize_homepage_v063",
        "def_summarize_homepage_v062",
        "def_summarize_homepage_v061",
        "def_summarize_homepage_v06",
        "def_summarize_homepage",
        "summarize",
    ]
    for name in candidates:
        fn = getattr(mod, name, None)
        if callable(fn):
            return name, fn
    raise RuntimeError("No callable summarize function found in active summarizer module.")







# =============================================================================
# def 03_PAYLOAD_CONTRACT
# =============================================================================

def def_router_normalize_payload_v01(payload: Dict[str, Any]) -> Dict[str, Any]:
    p = dict(payload or {})

    repaired = (
        p.get("repaired_first_page_text")
        or p.get("first_page_repaired_text")
        or p.get("first_page_text_repaired")
        or p.get("first_page_text")
        or p.get("text")
        or ""
    )

    p["repaired_first_page_text"] = repaired
    p["first_page_text"] = repaired
    p["text"] = repaired

    if "financial_data" not in p:
        if "financial_rows" in p:
            p["financial_data"] = p.get("financial_rows")
        else:
            p["financial_data"] = []

    return p


def def_router_validate_payload_v01(payload: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    if not payload.get("repaired_first_page_text"):
        warnings.append("RED_REVIEW: repaired_first_page_text missing.")
    if not payload.get("financial_data") and not payload.get("financial_data_csv"):
        warnings.append("RED_REVIEW: financial_data missing.")
    if not payload.get("ticker"):
        warnings.append("YELLOW_REVIEW: ticker missing.")
    if not payload.get("report_date"):
        warnings.append("YELLOW_REVIEW: report_date missing.")
    return warnings


# =============================================================================
# def 04_OUTPUT
# =============================================================================

def def_router_build_db_ready_row_v01(summary: Dict[str, Any], payload: Dict[str, Any], cfg: Dict[str, Any]) -> Dict[str, Any]:
    zh = summary.get("zh_points") or {}
    en = summary.get("en_points") or {}

    row = {
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
        "summarizer_version": summary.get("summarizer_version", cfg.get("version", "")),
        "valuation_method": summary.get("valuation_method", ""),
        "financial_snapshot": summary.get("financial_snapshot", ""),
        "warning_count": len(summary.get("warnings") or []),
        "zh_valuation_upside": zh.get("valuation_upside", ""),
        "zh_diluted_eps_growth": zh.get("diluted_eps_growth", ""),
        "zh_trend_catalyst": zh.get("trend_catalyst", ""),
        "zh_industry_position_moat": zh.get("industry_position_moat", ""),
        "zh_peer_comparison": zh.get("peer_comparison", ""),
        "zh_key_risks_mitigants": zh.get("key_risks_mitigants", ""),
        "en_valuation_upside": en.get("valuation_upside", ""),
        "en_diluted_eps_growth": en.get("diluted_eps_growth", ""),
        "en_trend_catalyst": en.get("trend_catalyst", ""),
        "en_industry_position_moat": en.get("industry_position_moat", ""),
        "en_peer_comparison": en.get("peer_comparison", ""),
        "en_key_risks_mitigants": en.get("key_risks_mitigants", ""),
    }
    return row


def def_router_write_db_ready_csv_v01(path: str | Path, rows: List[Dict[str, Any]]) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        p.write_text("", encoding="utf-8-sig")
        return str(p)

    cols: List[str] = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)

    with p.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return str(p)


def def_router_render_html_v01(summary: Dict[str, Any], payload: Dict[str, Any], cfg: Dict[str, Any], out_html: str | Path) -> str:
    zh = summary.get("zh_points") or {}
    en = summary.get("en_points") or {}
    cross = summary.get("cross_validation") or []
    warnings = summary.get("warnings") or []

    def rows_for_points(points: Dict[str, Any]) -> str:
        html = ""
        for k, v in points.items():
            html += f"<tr><td>{def_router_html_escape_v01(k)}</td><td>{def_router_html_escape_v01(v)}</td></tr>\n"
        return html

    cross_rows = ""
    for r in cross:
        band = str(r.get("band", ""))
        cls = "ok" if band == "GREEN" else ("warn" if band in {"YELLOW", "NA", ""} else "err")
        cross_rows += (
            f"<tr class='{cls}'>"
            f"<td>{def_router_html_escape_v01(r.get('field'))}</td>"
            f"<td>{def_router_html_escape_v01(r.get('summarizer_value'))}</td>"
            f"<td>{def_router_html_escape_v01(r.get('ssot_value'))}</td>"
            f"<td>{def_router_html_escape_v01(r.get('delta_pct'))}</td>"
            f"<td>{def_router_html_escape_v01(r.get('band'))}</td>"
            f"<td>{def_router_html_escape_v01(r.get('action'))}</td>"
            f"</tr>\n"
        )

    warn_html = "".join(f"<li>{def_router_html_escape_v01(w)}</li>" for w in warnings) or "<li>None</li>"

    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VRN Summarizer Router Output</title>
<style>
body{{margin:0;font-family:"Segoe UI","Microsoft JhengHei",Arial,sans-serif;background:#f5f4f0;color:#111827;font-size:12px}}
.header{{padding:24px 32px;color:white;background:#0f172a;border-top:4px solid #4c78a8}}
.header h1{{margin:0;font-size:25px}}.sub{{color:#cbd5e1;margin-top:6px}}
.grid{{display:grid;grid-template-columns:repeat(8,1fr);gap:10px;padding:16px 30px}}
.card{{background:white;border:1px solid #e0ddd5;border-radius:6px;padding:12px}}.num{{font-size:19px;font-weight:800;overflow-wrap:anywhere}}
.section{{margin:0 30px 20px 30px;background:white;border:1px solid #e0ddd5;border-radius:6px;padding:16px}}
table{{width:100%;border-collapse:collapse;font-size:11px}}th{{text-align:left;background:#e5eaf2;padding:7px}}td{{border-bottom:1px solid #e5e7eb;padding:6px 7px;vertical-align:top}}
tr.ok td{{background:#f0fdf4}}tr.warn td{{background:#fffbeb}}tr.err td{{background:#fef2f2}}
.code{{font-family:Consolas,monospace;background:#0f172a;color:#d1fae5;padding:12px;border-radius:6px;white-space:pre-wrap;max-height:430px;overflow:auto}}
</style>
</head>
<body>
<div class="header">
<h1>VRN Summarizer Router Output</h1>
<div class="sub">active_config → active summarizer → summary_json / summary_html / db_ready_summary</div>
</div>

<div class="grid">
<div class="card"><div class="num">{def_router_html_escape_v01(summary.get('quality_grade'))}</div><div>Quality</div></div>
<div class="card"><div class="num">{def_router_html_escape_v01(summary.get('rating'))}</div><div>Rating</div></div>
<div class="card"><div class="num">{def_router_html_escape_v01(summary.get('target_price'))}</div><div>TP</div></div>
<div class="card"><div class="num">{def_router_html_escape_v01(summary.get('upside_pct'))}%</div><div>Upside</div></div>
<div class="card"><div class="num">{def_router_html_escape_v01(summary.get('summarizer_version', cfg.get('version')))}</div><div>Version</div></div>
<div class="card"><div class="num">{def_router_html_escape_v01(summary.get('valuation_method'))}</div><div>Valuation</div></div>
<div class="card"><div class="num">{def_router_html_escape_v01(summary.get('financial_data_used'))}</div><div>Financial Used</div></div>
<div class="card"><div class="num">{len(warnings)}</div><div>Warnings</div></div>
</div>

<div class="section">
<h2>01 Header</h2>
<div class="code">Report Code: {def_router_html_escape_v01(summary.get('report_code'))}
Ticker: {def_router_html_escape_v01(payload.get('ticker'))}
Name: {def_router_html_escape_v01(payload.get('name'))}
Broker: {def_router_html_escape_v01(summary.get('broker', payload.get('broker')))}
Analyst: {def_router_html_escape_v01(summary.get('analyst', payload.get('analyst')))}
Report Date: {def_router_html_escape_v01(summary.get('report_date', payload.get('report_date')))}
Valuation: {def_router_html_escape_v01(summary.get('valuation_method'))}
Financial Snapshot: {def_router_html_escape_v01(summary.get('financial_snapshot'))}</div>
</div>

<div class="section">
<h2>02 ZH Points</h2>
<table><thead><tr><th>Point</th><th>Text</th></tr></thead><tbody>{rows_for_points(zh)}</tbody></table>
</div>

<div class="section">
<h2>03 EN Points</h2>
<table><thead><tr><th>Point</th><th>Text</th></tr></thead><tbody>{rows_for_points(en)}</tbody></table>
</div>

<div class="section">
<h2>04 Cross Validation</h2>
<table><thead><tr><th>Field</th><th>Summarizer</th><th>SSoT</th><th>Delta</th><th>Band</th><th>Action</th></tr></thead><tbody>{cross_rows}</tbody></table>
</div>

<div class="section">
<h2>05 Warnings</h2>
<ul>{warn_html}</ul>
</div>
</body>
</html>"""

    p = Path(out_html)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(html, encoding="utf-8")
    return str(p)


# =============================================================================
# def 05_ROUTER_MAIN
# =============================================================================

def def_router_run_v01(
    payload: Dict[str, Any],
    active_config: str | Path | None = None,
    output_json: str | Path | None = None,
    output_html: str | Path | None = None,
    db_ready_csv: str | Path | None = None,
) -> Dict[str, Any]:
    cfg = def_router_load_active_config_v01(active_config)
    module_path = def_router_resolve_module_path_v01(cfg)
    mod = def_router_import_module_from_path_v01(module_path)
    fn_name, fn = def_router_find_summarize_function_v01(mod)

    normalized = def_router_normalize_payload_v01(payload)
    router_warnings = def_router_validate_payload_v01(normalized)

    summary = fn(normalized)
    if not isinstance(summary, dict):
        raise RuntimeError("active summarizer returned non-dict result")

    summary["_router"] = {
        "router_version": "v01",
        "active_config": cfg.get("_active_config_path", ""),
        "active_module": str(module_path),
        "active_function": fn_name,
        "router_warnings": router_warnings,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
    }

    if router_warnings:
        existing = list(summary.get("warnings") or [])
        for w in router_warnings:
            if w not in existing:
                existing.append(w)
        summary["warnings"] = existing

    if output_json:
        def_router_write_json_v01(output_json, summary)

    if output_html:
        def_router_render_html_v01(summary, normalized, cfg, output_html)

    if db_ready_csv:
        row = def_router_build_db_ready_row_v01(summary, normalized, cfg)
        def_router_write_db_ready_csv_v01(db_ready_csv, [row])

    return summary


def def_router_selftest_v01() -> Dict[str, Any]:
    sample = {
        "filename": "MS-2330 20260518.pdf",
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

    summary = def_router_run_v01(sample)
    checks = {
        "rating_buy": summary.get("rating") == "BUY",
        "tp_1200": summary.get("target_price") == 1200.0,
        "upside_20": summary.get("upside_pct") == 20.0,
        "financial_used": bool(summary.get("financial_data_used")),
        "valuation_22x": "22x" in str(summary.get("valuation_method")),
        "version_v063": summary.get("summarizer_version") == "v06.3",
        "router_attached": "_router" in summary,
    }
    return {"hard_pass": all(checks.values()), "checks": checks, "summary": summary}


def def_router_main_cli_v01(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", default="")
    parser.add_argument("--active-config", default="")
    parser.add_argument("--output-json", default="")
    parser.add_argument("--output-html", default="")
    parser.add_argument("--db-ready-csv", default="")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args(argv)

    if args.selftest:
        result = def_router_selftest_v01()
        if args.output_json:
            def_router_write_json_v01(args.output_json, result)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("hard_pass") else 2

    if not args.input_json:
        raise SystemExit("--input-json required unless --selftest")

    payload = def_router_read_json_v01(args.input_json)
    summary = def_router_run_v01(
        payload=payload,
        active_config=args.active_config or None,
        output_json=args.output_json or None,
        output_html=args.output_html or None,
        db_ready_csv=args.db_ready_csv or None,
    )
    print(json.dumps({
        "ok": True,
        "quality_grade": summary.get("quality_grade"),
        "rating": summary.get("rating"),
        "target_price": summary.get("target_price"),
        "upside_pct": summary.get("upside_pct"),
        "summarizer_version": summary.get("summarizer_version"),
        "active_function": summary.get("_router", {}).get("active_function"),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(def_router_main_cli_v01())
    except BaseException:
        print(traceback.format_exc())
        raise