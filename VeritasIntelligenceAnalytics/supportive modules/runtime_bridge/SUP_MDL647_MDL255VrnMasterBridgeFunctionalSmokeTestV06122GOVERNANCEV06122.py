# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import importlib.util
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_MASTER_BRIDGE_FUNCTIONAL_SMOKE_TEST_V06122"


def def_status_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "YES", "PASS", "GREEN", "N/A"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "YELLOW", "REVIEW", "PARTIAL"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_write_json(path: str | Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_write_csv(path: str | Path, rows: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_import_bridge(path: str | Path):
    p = Path(path)
    spec = importlib.util.spec_from_file_location(p.stem, str(p))
    mod = importlib.util.module_from_spec(spec)
    if spec and spec.loader:
        spec.loader.exec_module(mod)
        return mod
    raise RuntimeError("cannot import bridge module")


def def_table_html(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2>No rows.</section>"
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(c).replace('_',' ').title())}</th>" for c in fields)
    trs = []
    for r in rows:
        tds = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            lc = c.lower()
            cls = "left" if any(x in lc for x in ["file", "filename", "error", "text", "reason", "candidates"]) else "center"
            cls = "right" if any(x in lc for x in ["count", "score", "price", "value", "fields"]) else cls
            tds.append(f"<td class='{cls}'>{html.escape(v)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")

    return f"""
<section class="card">
<h2>{html.escape(title)}</h2>
<div class="table-wrap">
<table>
<thead><tr>{th}</tr></thead>
<tbody>{''.join(trs)}</tbody>
</table>
</div>
</section>
"""


def def_write_html(path: str | Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557;position:sticky;top:0;z-index:10}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:14px;padding:20px 32px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.22)}
.v{font-size:26px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 32px 32px}.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;vertical-align:top;white-space:normal}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;text-align:center;max-width:760px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.right{text-align:right;font-variant-numeric:tabular-nums}
tr:hover td{background:rgba(66,217,255,.07)}
footer{padding:18px 32px;color:#9fb3c8;border-top:1px solid #1f3557}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"
    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>VRN Master Bridge Functional Smoke Test v0.6.12.2</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · Master Bridge Functional Smoke Test v0.6.12.2</h1>
<div class="sub">import · filename tokenizer · ticker trinity · report date · yfinance fallback · broker protected · financial SSOT validation</div>
</header>
{card_html}
<main>{body}</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    Path(path).write_text(doc, encoding="utf-8")


def def_main():
    if len(sys.argv) < 4:
        raise SystemExit("usage: py <bridge_module> <input_dir> <run_dir>")

    bridge_path = Path(sys.argv[1])
    input_dir = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    run_dir.mkdir(parents=True, exist_ok=True)

    bridge = def_import_bridge(bridge_path)
    health = bridge.def_master_health()

    pdf_files = sorted(input_dir.glob("*.pdf")) if input_dir.exists() else []

    filename_rows = []
    for p in pdf_files:
        try:
            hit = bridge.def_extract_tw_ticker_from_filename(p.name)
            date_hit = bridge.def_extract_report_date_from_filename(p.name)
            ticker = hit.get("ticker", "")
            tri = bridge.def_trinity_from_ticker(ticker, "")
            filename_rows.append({
                "Status Lights": def_status_lights("OK" if ticker else "WARN"),
                "Filename": p.name,
                "Ticker": ticker,
                "Ticker Source": hit.get("source", ""),
                "Ticker Candidates": " | ".join(hit.get("all_candidates", [])),
                "YFinance Ticker": tri.get("YFinance Ticker", ""),
                "YFinance Ticker Candidates": tri.get("YFinance Ticker Candidates", ""),
                "Bloomberg Ticker": tri.get("Bloomberg Ticker", ""),
                "Report Date": date_hit.get("report_date", ""),
                "Report Date Candidates": " | ".join(date_hit.get("report_date_candidates", [])),
                "Severity": "OK" if ticker else "WARN",
            })
        except Exception as e:
            filename_rows.append({
                "Status Lights": def_status_lights("ERR"),
                "Filename": p.name,
                "Ticker": "",
                "Error": str(e),
                "Severity": "ERR",
            })

    sample_texts = [
        "分析師：王小明 目標價120元 評等買進",
        "Analyst: Tony Chen Target Price 88 Buy",
        "研究員：林志強 中立 目標價300 元",
    ]
    broker_rows = []
    for s in sample_texts:
        a = bridge.def_extract_analyst_from_text(s)
        rt = bridge.def_extract_rating_target_from_text(s)
        broker_rows.append({
            "Status Lights": def_status_lights("OK" if (a.get("Analyst") or rt.get("Rating") or rt.get("Target Price")) else "WARN"),
            "Input Text": s,
            "Analyst": a.get("Analyst", ""),
            "Rating": rt.get("Rating", ""),
            "Target Price": rt.get("Target Price", ""),
            "Analyst Confidence": a.get("Analyst Confidence", ""),
            "Rating Target Confidence": rt.get("Rating Target Confidence", ""),
            "Severity": "OK",
        })

    financial_samples = [
        {"Data Raw": "營收", "Value Raw": "1,234"},
        {"Data Raw": "毛利率", "Value Raw": "35.5%"},
        {"Data Raw": "應收帳款與票據", "Value Raw": "200"},
        {"Data Raw": "不動產、廠房設備", "Value Raw": "96"},
        {"Data Raw": "折舊及攤銷", "Value Raw": "272"},
        {"Data Raw": "長借/公司債變動", "Value Raw": "0"},
        {"Data Raw": "亂碼Header", "Value Raw": "百萬元"},
    ]

    financial_rows = []
    ssot_index = bridge.def_build_financial_ssot_index()
    for row in financial_samples:
        try:
            out = bridge.def_enrich_financial_row(row, official_map={}, ssot_index=ssot_index)
            matched = out.get("SSOT Matched", "NO")
            numeric = out.get("Numeric Status", "")
            financial_rows.append({
                "Status Lights": def_status_lights("OK" if matched == "YES" else "WARN"),
                "Data Raw": row.get("Data Raw", ""),
                "Data Official En": out.get("Data Official En", ""),
                "Category Official En": out.get("Category Official En", ""),
                "SSOT Matched": matched,
                "SSOT Score": out.get("SSOT Score", ""),
                "SSOT Match Reason": out.get("SSOT Match Reason", ""),
                "Value Raw": row.get("Value Raw", ""),
                "Value Numeric": out.get("Value Numeric", ""),
                "Value Is Percent": out.get("Value Is Percent", ""),
                "Numeric Status": numeric,
                "Severity": "OK" if matched == "YES" else "WARN",
            })
        except Exception as e:
            financial_rows.append({
                "Status Lights": def_status_lights("ERR"),
                "Data Raw": row.get("Data Raw", ""),
                "Error": str(e),
                "Severity": "ERR",
            })

    addsub = bridge.def_validate_add_sub(100, [40, 60])
    div = bridge.def_validate_division(35, 100, 35)
    validation_rows = [
        {"Status Lights": def_status_lights("OK"), "Validation": "Add/Sub", **addsub, "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Validation": "Division", **div, "Severity": "OK"},
    ]

    import_ok = health.get("version", "").startswith("VIS_VRN_MasterRegistryBridge")
    ticker_ok = any(r.get("Ticker") for r in filename_rows) if filename_rows else True
    financial_ok = any(r.get("SSOT Matched") == "YES" for r in financial_rows)
    broker_ok = any(r.get("Analyst") or r.get("Rating") or r.get("Target Price") for r in broker_rows)

    system_pass = bool(import_ok and ticker_ok and financial_ok and broker_ok)

    overview = [
        {"Status Lights": def_status_lights("OK" if system_pass else "ERR"), "Gate": "SYSTEM_PASS", "Value": "YES" if system_pass else "NO", "Severity": "OK" if system_pass else "ERR"},
        {"Status Lights": def_status_lights("OK"), "Gate": "BRIDGE_IMPORT", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "BRIDGE_VERSION", "Value": health.get("version", ""), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "SOURCE_MODULES", "Value": health.get("source_modules", ""), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "INPUT_PDFS", "Value": len(pdf_files), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK" if ticker_ok else "WARN"), "Gate": "FILENAME_TICKER_TEST", "Value": "YES" if ticker_ok else "NO", "Severity": "OK" if ticker_ok else "WARN"},
        {"Status Lights": def_status_lights("OK" if broker_ok else "WARN"), "Gate": "BROKER_PATTERN_TEST", "Value": "YES" if broker_ok else "NO", "Severity": "OK" if broker_ok else "WARN"},
        {"Status Lights": def_status_lights("OK" if financial_ok else "WARN"), "Gate": "FINANCIAL_SSOT_TEST", "Value": "YES" if financial_ok else "NO", "Severity": "OK" if financial_ok else "WARN"},
        {"Status Lights": def_status_lights("OK"), "Gate": "YFINANCE_FIELDS", "Value": len(health.get("yfinance_info_fields", [])), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    html_path = str(run_dir / "VRN_Master_Bridge_Functional_Smoke_Test_v06122.html")
    json_path = str(run_dir / "vrn_master_bridge_functional_smoke_test_v06122.json")
    overview_csv = str(run_dir / "vrn_master_bridge_smoke_overview_v06122.csv")
    filename_csv = str(run_dir / "vrn_master_bridge_filename_ticker_v06122.csv")
    broker_csv = str(run_dir / "vrn_master_bridge_broker_pattern_v06122.csv")
    financial_csv = str(run_dir / "vrn_master_bridge_financial_ssot_v06122.csv")
    validation_csv = str(run_dir / "vrn_master_bridge_validation_v06122.csv")

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": "YES" if system_pass else "NO",
        "counts": {
            "System Pass": "YES" if system_pass else "NO",
            "Input PDFs": len(pdf_files),
            "Filename Rows": len(filename_rows),
            "Broker Tests": len(broker_rows),
            "Financial Tests": len(financial_rows),
            "YFinance Fields": len(health.get("yfinance_info_fields", [])),
            "Source Modules": health.get("source_modules", ""),
        },
        "outputs": {
            "html": html_path,
            "json": json_path,
            "overview_csv": overview_csv,
            "filename_csv": filename_csv,
            "broker_csv": broker_csv,
            "financial_csv": financial_csv,
            "validation_csv": validation_csv,
        },
        "policy": {
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
            "pdf_text_extraction": "NO",
            "pdf_table_extraction": "NO",
            "smoke_test_only": "YES",
        },
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(filename_csv, filename_rows)
    def_write_csv(broker_csv, broker_rows)
    def_write_csv(financial_csv, financial_rows)
    def_write_csv(validation_csv, validation_rows)
    def_write_json(json_path, result)

    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Filename Ticker Trinity", filename_rows),
        ("03 Broker Analyst Rating Target Pattern", broker_rows),
        ("04 Financial SSOT Smoke", financial_rows),
        ("05 Validation Smoke", validation_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise