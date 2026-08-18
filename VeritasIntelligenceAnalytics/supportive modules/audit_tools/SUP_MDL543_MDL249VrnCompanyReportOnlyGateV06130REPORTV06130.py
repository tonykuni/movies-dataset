# -*- coding: utf-8 -*-
from __future__ import annotations

import csv
import html
import json
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_COMPANY_REPORT_ONLY_GATE_V06130"


# ==================================================================================================
# def 01_COMMON
# ==================================================================================================
def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def def_norm_text(x: Any) -> str:
    s = def_clean_text(x).lower()
    s = re.sub(r"[()（）\[\]【】{}<>〈〉《》]", " ", s)
    s = re.sub(r"[\s　,，、;；:：|｜/／\\\-–—_+＋=＝~～!！?？.．]", "", s)
    return s


def def_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "YES", "PASS", "GREEN", "COMPANY_REPORT"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "REVIEW", "EXCLUDED", "NO_FINANCIAL_TABLE_DISCLOSED"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


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


def def_find_latest(run_root: Path, pattern: str) -> Path | None:
    hits = sorted(run_root.rglob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_first(row: dict, keys: list[str]) -> str:
    for k in keys:
        if k in row and def_clean_text(row.get(k)):
            return def_clean_text(row.get(k))
    return ""


# ==================================================================================================
# def 02_COMPANY_REPORT_GATE
# ==================================================================================================
def def_is_tw_ticker(ticker: str) -> bool:
    return bool(re.fullmatch(r"(?!202[1-9])(?!2030)[1-9]\d{3}", def_clean_text(ticker)))


def def_company_report_classify(row: dict) -> dict:
    filename = def_first(row, ["Filename"])
    ticker = def_first(row, ["Ticker", "Ticker Parsed"])
    broker = def_first(row, ["Broker"])
    name = def_first(row, ["Name"])
    ext = Path(filename).suffix.lower()

    fn = def_norm_text(filename)
    raw_fn = def_clean_text(filename)

    exclude_keywords = [
        "晨會", "晨間", "早報", "投資早報", "盤勢", "台股盤勢", "大盤",
        "當日新聞", "重要訊息評論", "公司訪談摘要",
        "日股", "港股", "美股", "海外投資", "海外商品",
        "期貨", "解盤", "大趨勢", "產業趨勢", "半導體產業趨勢",
        "hardwareinsights", "automation", "memory", "thermal", "thoughtsontpu",
        "aipcb", "ccl", "pcb", "gpu", "robot", "機器人",
        "第一場", "第二場", "第三場"
    ]

    include_keywords = [
        "個股報告", "初次評等", "訪談速報", "個股介紹", "memo",
        "買進", "中立", "未評等", "nr"
    ]

    has_ticker = def_is_tw_ticker(ticker)
    has_exclude = any(def_norm_text(k) in fn for k in exclude_keywords)
    has_include = any(def_norm_text(k) in fn for k in include_keywords)

    # def hard rules
    # def 1. 沒有四碼 ticker，不是個股報告
    if not has_ticker:
        return {
            "is_company_report": False,
            "report_scope": "EXCLUDED_NON_COMPANY",
            "reason": "NO_VALID_TW_TICKER",
        }

    # def 2. DOCX memo with ticker can be company memo
    if ext == ".docx" and has_ticker:
        return {
            "is_company_report": True,
            "report_scope": "COMPANY_MEMO",
            "reason": "DOCX_MEMO_WITH_VALID_TW_TICKER",
        }

    # def 3. 明確個股詞優先保留
    if has_include:
        return {
            "is_company_report": True,
            "report_scope": "COMPANY_REPORT",
            "reason": "COMPANY_KEYWORD_WITH_VALID_TW_TICKER",
        }

    # def 4. 若有排除詞且沒有個股詞，排除
    if has_exclude:
        return {
            "is_company_report": False,
            "report_scope": "EXCLUDED_MARKET_OR_SECTOR",
            "reason": "MARKET_SECTOR_THEME_KEYWORD",
        }

    # def 5. Broker + ticker + possible stock name: default keep
    if has_ticker and (broker or name):
        return {
            "is_company_report": True,
            "report_scope": "COMPANY_REPORT",
            "reason": "VALID_TW_TICKER_WITH_BROKER_OR_NAME",
        }

    # def 6. Ticker-only broker report, keep but mark weaker
    if has_ticker:
        return {
            "is_company_report": True,
            "report_scope": "COMPANY_REPORT_REVIEW",
            "reason": "VALID_TW_TICKER_FILENAME_ONLY",
        }

    return {
        "is_company_report": False,
        "report_scope": "EXCLUDED_UNKNOWN",
        "reason": "UNKNOWN",
    }


def def_recalibrate_validation(row: dict, company_info: dict) -> dict:
    r = dict(row)

    if company_info["is_company_report"]:
        r["Company Report Gate"] = "YES"
        r["Report Scope"] = company_info["report_scope"]
        r["Company Gate Reason"] = company_info["reason"]

        old_status = def_first(r, ["Validation Status"])
        db_rows = def_first(r, ["DB Ready Rows", "Db Ready Rows"])

        if db_rows and db_rows not in ["0", "0.00"]:
            r["Validation Status"] = old_status or "DB_READY"
            r["Severity"] = "OK" if old_status == "DB_READY" else def_first(r, ["Severity"]) or "WARN"
        else:
            # 個股報告但沒有 financial DB rows：保留在 company-only action queue
            r["Validation Status"] = "COMPANY_REPORT_NO_DB_READY_ROWS"
            r["Severity"] = "WARN"

        r["Status Lights"] = def_lights(r["Severity"])
    else:
        r["Company Report Gate"] = "NO"
        r["Report Scope"] = company_info["report_scope"]
        r["Company Gate Reason"] = company_info["reason"]
        r["Validation Status"] = "EXCLUDED_NOT_COMPANY_REPORT"
        r["Severity"] = "INFO"
        r["Status Lights"] = def_lights("WARN")

    return r


# ==================================================================================================
# def 03_HTML
# ==================================================================================================
def def_table_html(title: str, rows: list[dict]) -> str:
    if not rows:
        return f"<section class='card'><h2>{html.escape(title)}</h2><p>No rows.</p></section>"

    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)

    th = "".join(f"<th>{html.escape(str(c).replace('_', ' ').title())}</th>" for c in fields)
    body = []

    for r in rows:
        tds = []
        for c in fields:
            v = "" if r.get(c) is None else str(r.get(c, ""))
            lc = c.lower()
            cls = "center"
            if any(x in lc for x in ["filename", "name", "broker", "analyst", "status", "reason", "scope"]):
                cls = "left"
            if any(x in lc for x in ["price", "confidence", "rows", "table no"]):
                cls = "right"
            if "rate" in lc or "ticker" in lc:
                cls += " wrap"
            tds.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(tds) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
:root{--bg:#07111f;--panel:#0d1b2f;--panel2:#132541;--line:#1f3557;--text:#eef6ff;--muted:#9fb3c8;--accent:#42d9ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--text);font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:linear-gradient(135deg,#0d1b2f,#091525);border-bottom:1px solid var(--line);position:sticky;top:0;z-index:10}
h1{margin:0;font-size:24px}.sub{color:var(--muted);margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;padding:20px 32px}
.kpi{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.22)}
.v{font-size:26px;font-weight:800}.k{color:var(--muted);margin-top:4px}
main{padding:0 32px 32px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:78vh;border:1px solid var(--line);border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:var(--panel2);padding:10px;text-align:center;vertical-align:top;white-space:normal;word-break:break-word;max-width:180px;z-index:2}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;text-align:center;max-width:420px;white-space:normal;word-break:break-word;line-height:1.35}
td.left{text-align:left}
td.right{text-align:right;font-variant-numeric:tabular-nums}
td.wrap{white-space:normal;word-break:break-word}
tr:hover td{background:rgba(66,217,255,.07)}
footer{padding:18px 32px;color:var(--muted);border-top:1px solid var(--line)}
@media(max-width:900px){body{font-size:10px}main{padding:0 14px 20px}.grid{padding:14px;grid-template-columns:repeat(2,minmax(120px,1fr))}}
"""
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"

    body = "".join(def_table_html(t, r) for t, r in sections)

    doc = f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>VRN Company Report Only Gate v06130</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · Company Report Only Gate v0.6.13.0</h1>
<div class="sub">only individual stock reports · ticker-gated · market/sector/macro excluded · no canonical mutation</div>
</header>
{card_html}
<main>{body}</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    path.write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 04_MAIN
# ==================================================================================================
def def_main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("usage: py <run_root> <run_dir> <config_dir>")

    run_root = Path(sys.argv[1])
    run_dir = Path(sys.argv[2])
    config_dir = Path(sys.argv[3])
    run_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    source_csv = def_find_latest(run_root, "vrn_one_row_file_validation_matrix_v06129.csv")
    if not source_csv:
        raise RuntimeError("Cannot find vrn_one_row_file_validation_matrix_v06129.csv")

    rows = def_read_csv(source_csv)

    company_rows = []
    excluded_rows = []
    action_rows = []

    for row in rows:
        info = def_company_report_classify(row)
        nr = def_recalibrate_validation(row, info)

        if info["is_company_report"]:
            company_rows.append(nr)
            if nr["Validation Status"] in ["COMPANY_REPORT_NO_DB_READY_ROWS", "DB_READY_WITH_SPLIT_REVIEW"]:
                action_rows.append(nr)
        else:
            excluded_rows.append(nr)

    db_ready = [r for r in company_rows if def_first(r, ["DB Ready Rows", "Db Ready Rows"]) not in ["", "0", "0.00"]]
    no_db = [r for r in company_rows if r.get("Validation Status") == "COMPANY_REPORT_NO_DB_READY_ROWS"]

    overview = [
        {"Status Lights": def_lights("OK"), "Gate": "SOURCE_MATRIX", "Value": str(source_csv), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "TOTAL_ROWS_IN_V06129", "Value": len(rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "COMPANY_REPORT_ROWS", "Value": len(company_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "EXCLUDED_NON_COMPANY_ROWS", "Value": len(excluded_rows), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "DB_READY_COMPANY_REPORTS", "Value": len(db_ready), "Severity": "OK"},
        {"Status Lights": def_lights("WARN" if no_db else "OK"), "Gate": "COMPANY_REPORT_NO_DB_READY_ROWS", "Value": len(no_db), "Severity": "WARN" if no_db else "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_FAKE_FILL", "Value": "YES", "Severity": "OK"},
    ]

    html_path = run_dir / "VRN_Company_Report_Only_Gate_v06130.html"
    json_path = run_dir / "vrn_company_report_only_gate_v06130.json"
    overview_csv = run_dir / "vrn_v06130_overview.csv"
    company_csv = run_dir / "vrn_v06130_company_report_only_matrix.csv"
    excluded_csv = run_dir / "vrn_v06130_excluded_non_company_matrix.csv"
    action_csv = run_dir / "vrn_v06130_company_report_action_queue.csv"

    manifest_json = config_dir / "VRN_Company_Report_Only_Input_Manifest_v06130.json"
    manifest_csv = config_dir / "VRN_Company_Report_Only_Input_Manifest_v06130.csv"

    manifest_rows = []
    for r in company_rows:
        manifest_rows.append({
            "Filename": def_first(r, ["Filename"]),
            "Report Date": def_first(r, ["Report Date"]),
            "Ticker": def_first(r, ["Ticker"]),
            "Yfinance Ticker": def_first(r, ["Yfinance Ticker", "YFinance Ticker"]),
            "Bloomberg Ticker": def_first(r, ["Bloomberg Ticker"]),
            "Broker": def_first(r, ["Broker"]),
            "Name": def_first(r, ["Name"]),
            "Rating": def_first(r, ["Rating"]),
            "Target Price": def_first(r, ["Target Price"]),
            "Report Scope": def_first(r, ["Report Scope"]),
            "Company Gate Reason": def_first(r, ["Company Gate Reason"]),
            "Validation Status": def_first(r, ["Validation Status"]),
        })

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "source_matrix": str(source_csv),
        "counts": {
            "Source Rows": len(rows),
            "Company Reports": len(company_rows),
            "Excluded": len(excluded_rows),
            "DB Ready": len(db_ready),
            "No DB Ready": len(no_db),
            "Action Rows": len(action_rows),
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "overview_csv": str(overview_csv),
            "company_csv": str(company_csv),
            "excluded_csv": str(excluded_csv),
            "action_csv": str(action_csv),
            "manifest_json": str(manifest_json),
            "manifest_csv": str(manifest_csv),
        },
        "policy": {
            "only_company_report": "YES",
            "must_have_tw_ticker": "YES",
            "market_sector_macro_excluded": "YES",
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
            "no_fake_fill": "YES",
        },
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(company_csv, company_rows)
    def_write_csv(excluded_csv, excluded_rows)
    def_write_csv(action_csv, action_rows)
    def_write_csv(manifest_csv, manifest_rows)
    def_write_json(manifest_json, {"version": VERSION, "generated_at": result["generated_at"], "company_reports": manifest_rows})
    def_write_json(json_path, result)

    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Company Report Only Matrix", company_rows),
        ("03 Company Report Action Queue", action_rows),
        ("04 Excluded Non Company Reports", excluded_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise