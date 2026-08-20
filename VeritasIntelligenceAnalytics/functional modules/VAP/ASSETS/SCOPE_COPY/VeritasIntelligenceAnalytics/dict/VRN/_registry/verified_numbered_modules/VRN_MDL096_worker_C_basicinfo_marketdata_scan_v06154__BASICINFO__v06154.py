# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import os
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ").replace("\r", " ").replace("\n", " ")
    return re.sub(r"\s+", " ", s).strip()


def def_norm_key(x: Any) -> str:
    s = def_clean_text(x).lower()
    s = re.sub(r"[\\/:*?\"<>|()\[\]{}【】（）,，。．\s]+", "", s)
    return s


def def_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "READY", "YES", "PASS", "GREEN"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "PARTIAL", "YELLOW", "OPTIONAL"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


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


def def_write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r.keys():
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


def def_find_latest(root: Path, patterns: list[str]) -> Path | None:
    hits = []
    for pat in patterns:
        hits.extend(root.rglob(pat))
    hits = [p for p in hits if p.is_file()]
    hits = sorted(set(hits), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_table_html(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"
    fields = []
    for r in rows:
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    th = "".join(f"<th>{html.escape(str(c))}</th>" for c in fields)
    body = []
    for r in rows:
        cells = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            cls = "left" if any(x in c.lower() for x in ["file", "source", "path", "reason", "step", "status", "queue", "issue", "route"]) else "center"
            cells.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, title: str, subtitle: str, counts: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:14px;padding:20px 32px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px}
.v{font-size:26px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 32px 32px}
.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;white-space:normal}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;max-width:980px;white-space:normal;word-break:break-word}
td.left{text-align:left}td.center{text-align:center}
"""
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in counts.items()
    ) + "</div>"
    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>{html.escape(title)}</title><style>{css}</style></head>
<body><header><h1>{html.escape(title)}</h1><div class="sub">{html.escape(subtitle)}</div></header>{card_html}<main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_file_match(row: dict, filename: str, ticker: str) -> bool:
    fn = def_clean_text(row.get("Filename") or row.get("filename") or row.get("File") or row.get("file") or "")
    tk = def_clean_text(row.get("Ticker") or row.get("ticker") or row.get("stock_id") or row.get("Stock ID") or "")
    if filename and fn and def_norm_key(Path(filename).name) == def_norm_key(Path(fn).name):
        return True
    if ticker and tk and ticker == tk:
        return True
    return False


def def_now() -> str:
    return datetime.now().isoformat(timespec="seconds")
BROKER_CANON = {
    "daiwa": "DAIWA",
    "goldman": "GS",
    "goldman sachs": "GS",
    "gs": "GS",
    "jp": "JPM",
    "jpm": "JPM",
    "jp morgan": "JPM",
    "jpmorgan": "JPM",
    "morgan stanley": "MS",
    "ms": "MS",
    "huanan": "HuaNan",
    "華南": "HuaNan",
    "first": "FFHC",
    "第一": "FFHC",
    "president": "PSC",
    "統一": "PSC",
    "capital": "CSC",
    "群益": "CSC",
    "citi": "Citi",
    "ctbc": "CTBC",
    "clst": "CLST",
}


def def_norm_broker(x: Any) -> str:
    s = def_clean_text(x)
    k = s.lower()
    for raw, canon in BROKER_CANON.items():
        if raw in k:
            return canon
    return s


def def_main() -> None:
    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    enable_yfinance_refresh = str(sys.argv[3]).lower() in ["true", "1", "yes"]
    run_dir.mkdir(parents=True, exist_ok=True)

    master_csv = def_find_latest(run_root, [
        "VRN_YFINANCE_HEADER_CANONICAL_REFRESH_V06147_*/vrn_v06147_company_master_yfinance_canonical_refreshed.csv",
        "VRN_BROKER_ANALYST_ADAPTER_STRENGTHEN_V06146_*/vrn_v06146_company_master_broker_analyst_adapter_sealed.csv",
        "VRN_COMPANY_MASTER_ENRICH_VALIDATE_V06132_*/vrn_company_master*.csv",
    ])

    rows = []
    issues = []
    overview = []

    if not master_csv:
        overview.append({"Status Lights": def_lights("ERR"), "Gate": "MASTER_CSV_FOUND", "Value": "NO", "Severity": "ERR"})
    else:
        data = def_read_csv(master_csv)

        for r in data:
            fn = def_clean_text(r.get("Filename", ""))
            ticker = def_clean_text(r.get("Ticker", ""))
            yf = def_clean_text(r.get("YFinance Ticker") or r.get("YFinance Final Ticker") or "")
            broker_raw = def_clean_text(r.get("Broker", ""))
            broker = def_norm_broker(broker_raw)
            analyst = def_clean_text(r.get("Analyst", ""))
            report_date = def_clean_text(r.get("Report Date", ""))

            tfinance_cols = [k for k in r.keys() if k.lower().startswith("tfinance")]
            yfinance_cols = [k for k in r.keys() if k.lower().startswith("yfinance")]

            sev = "OK"
            status = []

            if tfinance_cols:
                sev = "WARN"
                status.append("TFINANCE_HEADER_LEGACY_EXISTS")

            if not yf:
                sev = "WARN"
                status.append("YFINANCE_TICKER_MISSING")

            if not broker:
                sev = "WARN"
                status.append("BROKER_MISSING")

            if broker_raw and broker_raw != broker:
                status.append(f"BROKER_NORMALIZED:{broker_raw}->{broker}")

            if "華南" in fn and broker != "HuaNan":
                sev = "WARN"
                status.append("HUANAN_BROKER_NOT_NORMALIZED")

            if "Memo" in fn or "memo" in fn or "訪談" in fn:
                analyst_status = "OPTIONAL_ANALYST_NOT_REQUIRED"
            else:
                analyst_status = "ANALYST_OK" if analyst else "ANALYST_REVIEW"

            if analyst_status == "ANALYST_REVIEW":
                sev = "WARN"

            rows.append({
                "Status Lights": def_lights(sev),
                "Filename": fn,
                "Report Date": report_date,
                "Ticker": ticker,
                "YFinance Ticker": yf,
                "Broker Raw": broker_raw,
                "Broker English Abbrev": broker,
                "Analyst": analyst,
                "Analyst Status": analyst_status,
                "YFinance Header Count": len(yfinance_cols),
                "TFinance Legacy Header Count": len(tfinance_cols),
                "YFinance Refresh Enabled": "YES" if enable_yfinance_refresh else "NO",
                "Validation Status": " | ".join(status) if status else "BASICINFO_MARKETDATA_OK",
                "Severity": sev,
            })

            if sev != "OK":
                issues.append(rows[-1])

        overview.extend([
            {"Status Lights": def_lights("OK"), "Gate": "MASTER_SOURCE", "Value": str(master_csv), "Severity": "OK"},
            {"Status Lights": def_lights("OK"), "Gate": "ROWS", "Value": len(rows), "Severity": "OK"},
            {"Status Lights": def_lights("WARN" if issues else "OK"), "Gate": "ISSUES", "Value": len(issues), "Severity": "WARN" if issues else "OK"},
            {"Status Lights": def_lights("OK"), "Gate": "YFINANCE_REFRESH_ENABLED", "Value": "YES" if enable_yfinance_refresh else "NO", "Severity": "OK"},
            {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        ])

    out_csv = run_dir / "flow_C_basicinfo_marketdata_matrix.csv"
    issue_csv = run_dir / "flow_C_basicinfo_marketdata_issues.csv"
    html_path = run_dir / "Flow_C_BasicInfo_MarketData_Scan_v06154.html"
    json_path = run_dir / "flow_C_basicinfo_marketdata_scan_v06154.json"

    def_write_csv(out_csv, rows)
    def_write_csv(issue_csv, issues)

    result = {
        "flow": "C_BASICINFO_MARKETDATA_SCAN",
        "generated_at": def_now(),
        "system_pass": True,
        "counts": {
            "Rows": len(rows),
            "Issues": len(issues),
            "YFinance Refresh": "YES" if enable_yfinance_refresh else "NO",
            "No Canonical Mutation": "YES",
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "matrix_csv": str(out_csv),
            "issue_csv": str(issue_csv),
        },
    }

    def_write_json(json_path, result)
    def_write_html(
        html_path,
        "Flow C · BasicInfo / Analyst / Broker / YFinance Scan v0.6.15.4",
        "broker English abbrev · analyst review · YFinance header canonical check · no canonical mutation",
        result["counts"],
        [("01 Overview", overview), ("02 BasicInfo MarketData Matrix", rows), ("03 Issues", issues)]
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise