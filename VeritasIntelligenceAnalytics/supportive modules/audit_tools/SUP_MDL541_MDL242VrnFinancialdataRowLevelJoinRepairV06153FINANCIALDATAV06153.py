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


VERSION = "VRN_FINANCIALDATA_ROW_LEVEL_JOIN_REPAIR_V06153"


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
    if s in ["OK", "READY", "PASS", "YES"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "PARTIAL", "REVIEW", "OPTIONAL"]:
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
        for k in r.keys():
            if k not in fields:
                fields.append(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_find_latest(root: Path, patterns: list[str]) -> Path | None:
    hits = []
    for pat in patterns:
        hits.extend(root.rglob(pat))
    hits = [p for p in hits if p.is_file()]
    hits = sorted(set(hits), key=lambda p: p.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_to_float(x: Any) -> float | None:
    s = def_clean_text(x)
    if not s:
        return None
    s = s.replace(",", "").replace("%", "")
    s = re.sub(r"[^\d\.\-\(\)]", "", s)
    if not s:
        return None
    neg = False
    if s.startswith("(") and s.endswith(")"):
        neg = True
        s = s[1:-1]
    try:
        v = float(s)
        return -v if neg else v
    except Exception:
        return None


def def_fmt_num(x: Any) -> str:
    v = def_to_float(x)
    if v is None:
        return ""
    return f"{v:,.2f}"


def def_fmt_pct(num: int, den: int) -> str:
    if den <= 0:
        return "0.00%\n0/0"
    return f"{(num / den * 100):.2f}%\n{num:,}/{den:,}"


def def_row_id(row: dict) -> str:
    return "|".join([
        def_norm_key(row.get("Filename") or row.get("filename") or ""),
        def_clean_text(row.get("Ticker") or row.get("ticker") or ""),
        def_clean_text(row.get("Year") or row.get("year") or row.get("Financial Year") or ""),
        def_norm_key(row.get("Category Official En") or row.get("Category") or ""),
        def_norm_key(row.get("Data Official En") or row.get("Data Raw") or row.get("Account") or row.get("Item") or ""),
        def_clean_text(row.get("Value") or row.get("Value Numeric") or row.get("value") or ""),
    ])


def def_match_file(row: dict, filename: str, ticker: str) -> bool:
    fn = def_clean_text(row.get("Filename") or row.get("filename") or row.get("File") or row.get("file") or "")
    tk = def_clean_text(row.get("Ticker") or row.get("ticker") or row.get("stock_id") or row.get("Stock ID") or "")
    if filename and fn and def_norm_key(Path(filename).name) == def_norm_key(Path(fn).name):
        return True
    if ticker and tk and ticker == tk:
        return True
    return False


def def_source_kind(path: Path, cols: set[str]) -> str:
    name = path.name.lower()
    col = " ".join(cols).lower()

    bad = [
        "action_queue",
        "calibrated_matrix",
        "repair_router",
        "overview",
        "summary",
        "manifest",
        "coverage_calibration",
        "confidence_calibrator",
        "one_row",
        "company_report_matrix",
        "final_seal",
        "broker",
        "yfinance",
        "basicinfo_financialdata_integrated",
        "decontaminated_repair_router",
        "decontaminated_evidence_scan",
    ]
    if any(x in name for x in bad):
        return "SUMMARY_EXCLUDED"

    if "pdf_table_inventory" in name or ("table" in name and "inventory" in name):
        return "REAL_TABLE_INVENTORY"

    if "restored_financial_candidate" in name:
        return "REAL_RESTORED_TABLE_ROWS"

    if "financial_candidate" in name and "review" not in name:
        return "REAL_FINANCIAL_CANDIDATE_ROWS"

    if "financialdata" in name and ("clean" in name or "validated" in name):
        return "REAL_VALIDATED_FINANCIAL_ROWS"

    if "review" in name or "quarantine" in name:
        return "REAL_REVIEW_QUARANTINE_ROWS"

    if "canonical" in str(path).lower() or "active" in name:
        return "CANONICAL_FINANCIAL_ACTIVE"

    if "financial" in name and ("data official" in col or "category official" in col):
        return "REAL_FINANCIAL_CANDIDATE_ROWS"

    return "OTHER_EXCLUDED"


def def_extract_year(row: dict) -> str:
    for k in ["Year", "year", "Financial Year", "financial_year", "Fiscal Year"]:
        s = def_clean_text(row.get(k, ""))
        m = re.search(r"(20\d{2})", s)
        if m:
            return m.group(1)
    for v in row.values():
        s = def_clean_text(v)
        m = re.search(r"\b(20\d{2})\b", s)
        if m:
            return m.group(1)
    return ""


def def_extract_category(row: dict) -> str:
    for k in ["Category Official En", "Category Official EN", "Category", "Financial Category", "category"]:
        s = def_clean_text(row.get(k, ""))
        if s:
            return s
    return ""


def def_extract_data_item(row: dict) -> str:
    for k in ["Data Official En", "Data Official EN", "Data Raw", "Account", "Item", "Line Item", "data_official_en"]:
        s = def_clean_text(row.get(k, ""))
        if s:
            return s
    return ""


def def_extract_value(row: dict) -> str:
    for k in ["Value Numeric", "Value", "value", "Amount", "Data Value", "data_value"]:
        s = def_clean_text(row.get(k, ""))
        if def_to_float(s) is not None:
            return s
    return ""


def def_confidence(base: dict, kind: str, has_year: bool, has_category: bool, has_item: bool, has_value: bool) -> float:
    score = 20.0
    if kind == "CANONICAL_FINANCIAL_ACTIVE":
        score += 20
    if kind == "REAL_VALIDATED_FINANCIAL_ROWS":
        score += 30
    if kind == "REAL_FINANCIAL_CANDIDATE_ROWS":
        score += 22
    if kind == "REAL_RESTORED_TABLE_ROWS":
        score += 18
    if has_year:
        score += 10
    if has_category:
        score += 10
    if has_item:
        score += 10
    if has_value:
        score += 10
    if def_clean_text(base.get("Report Date", "")):
        score += 4
    if def_clean_text(base.get("YFinance Ticker", "")):
        score += 2
    if def_clean_text(base.get("Name", "")):
        score += 2
    return min(score, 99.0)


def def_validation_status(conf: float, has_value: bool, has_item: bool, has_year: bool) -> str:
    if conf >= 80 and has_value and has_item and has_year:
        return "READY_ROW_LEVEL_JOINED"
    if conf >= 65 and has_value and has_item:
        return "PARTIAL_YEAR_OR_CONTEXT_REVIEW"
    if has_value:
        return "REVIEW_VALUE_ONLY"
    return "REPAIR_REQUIRED_NO_VALUE"


def def_scan_row_level_sources(run_root: Path, canonical_dir: Path) -> list[tuple[Path, str, list[dict]]]:
    files = []
    for root in [run_root, canonical_dir]:
        if root.exists():
            files.extend(root.rglob("*.csv"))

    files = sorted(set([p for p in files if p.is_file()]), key=lambda p: p.stat().st_mtime, reverse=True)
    out = []

    for p in files[:600]:
        rows = def_read_csv(p)
        if not rows:
            continue
        kind = def_source_kind(p, set(rows[0].keys()))
        if kind.startswith("REAL_") or kind.startswith("CANONICAL"):
            out.append((p, kind, rows))
    return out


def def_build_join_rows(router_rows: list[dict], source_rows: list[tuple[Path, str, list[dict]]]) -> tuple[list[dict], list[dict]]:
    joined = []
    alias_candidates = []
    seen = set()

    for base in router_rows:
        if def_clean_text(base.get("Repair Route")) != "REAL_REUSE_ROW_LEVEL_EVIDENCE":
            continue

        filename = def_clean_text(base.get("Filename"))
        ticker = def_clean_text(base.get("Ticker"))

        for path, kind, rows in source_rows:
            for r in rows:
                if not def_match_file(r, filename, ticker):
                    continue

                year = def_extract_year(r)
                category = def_extract_category(r)
                item = def_extract_data_item(r)
                value = def_extract_value(r)

                has_year = bool(year)
                has_category = bool(category)
                has_item = bool(item)
                has_value = def_to_float(value) is not None

                if not (has_item or has_value or category):
                    continue

                rid = "|".join([def_norm_key(filename), ticker, year, def_norm_key(category), def_norm_key(item), def_clean_text(value), kind])
                if rid in seen:
                    continue
                seen.add(rid)

                conf = def_confidence(base, kind, has_year, has_category, has_item, has_value)
                status = def_validation_status(conf, has_value, has_item, has_year)

                row = {
                    "Status Lights": def_lights("OK" if status.startswith("READY") else "WARN"),
                    "Filename": filename,
                    "Report Date": base.get("Report Date", ""),
                    "Broker": base.get("Broker", ""),
                    "Analyst": base.get("Analyst", ""),
                    "Ticker": ticker,
                    "YFinance Ticker": base.get("YFinance Ticker", ""),
                    "Bloomberg Ticker": base.get("Bloomberg Ticker", ""),
                    "Name": base.get("Name", ""),
                    "Evidence Kind": kind,
                    "Year": year,
                    "Category": category,
                    "Financial Item": item,
                    "Value": def_fmt_num(value),
                    "Source File": str(path),
                    "Confidence": f"{conf:.2f}",
                    "Validation Status": status,
                    "Severity": "OK" if status.startswith("READY") else "WARN",
                }
                joined.append(row)

                raw_item = def_clean_text(r.get("Data Raw") or r.get("Account") or r.get("Item") or "")
                official_item = def_clean_text(r.get("Data Official En") or r.get("Data Official EN") or "")
                if raw_item and official_item and def_norm_key(raw_item) != def_norm_key(official_item):
                    alias_candidates.append({
                        "Status Lights": def_lights("WARN"),
                        "Filename": filename,
                        "Ticker": ticker,
                        "Raw Alias Candidate": raw_item,
                        "Mapped Official Item": official_item,
                        "Evidence Kind": kind,
                        "Source File": str(path),
                        "Recommended Action": "Review for SSOT alias append-only update only after numeric validation.",
                        "Severity": "WARN",
                    })

    return joined, alias_candidates


def def_category_coverage(joined: list[dict], router_rows: list[dict]) -> list[dict]:
    core = {
        "Income Statement": ["Revenue", "Gross Profit", "Operating Income", "Net Income", "Diluted EPS"],
        "Balance Sheet": ["Total Assets", "Total Liabilities", "Total Equity", "Cash And Cash Equivalents", "Current Assets", "Current Liabilities"],
        "Cash Flow Statement": ["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow", "Capital Expenditure", "Ending Cash", "Free Cash Flow"],
        "Ratio Analysis": ["Gross Margin", "Operating Margin", "Net Margin", "ROE", "ROA", "Current Ratio"],
        "Per Share Analysis": ["Diluted EPS", "BVPS", "CFPS"],
    }

    by_file = {}
    for r in joined:
        key = (r.get("Filename", ""), r.get("Ticker", ""))
        by_file.setdefault(key, []).append(r)

    out = []
    for base in router_rows:
        if def_clean_text(base.get("Repair Route")) != "REAL_REUSE_ROW_LEVEL_EVIDENCE":
            continue

        key = (base.get("Filename", ""), base.get("Ticker", ""))
        rows = by_file.get(key, [])
        item_text = " | ".join([def_clean_text(x.get("Financial Item", "")) for x in rows]).lower()
        cat_text = " | ".join([def_clean_text(x.get("Category", "")) for x in rows]).lower()

        for cat, items in core.items():
            found = 0
            missing = []
            for item in items:
                if item.lower() in item_text:
                    found += 1
                else:
                    missing.append(item)

            disclosed = cat.lower() in cat_text or found > 0
            if not disclosed:
                continue

            den = len(items)
            pct = found / den if den else 0
            sev = "OK" if pct >= 0.70 else "WARN"
            out.append({
                "Status Lights": def_lights(sev),
                "Filename": base.get("Filename", ""),
                "Ticker": base.get("Ticker", ""),
                "Name": base.get("Name", ""),
                "Category": cat,
                "Fetching Rate": def_fmt_pct(found, den),
                "Found Items": found,
                "Total Core Items": den,
                "Missing Items": " | ".join(missing),
                "Validation Status": "CATEGORY_READY" if pct >= 0.70 else "CATEGORY_PARTIAL_REVIEW",
                "Severity": sev,
            })

    return out


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
            cls = "left" if any(x in c.lower() for x in ["filename", "source", "item", "status", "alias", "action", "missing"]) else "center"
            cells.append(f"<td class='{cls}'>{html.escape(v).replace(chr(10), '<br>')}</td>")
        body.append("<tr>" + "".join(cells) + "</tr>")

    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(body)}</tbody></table></div></section>"


def def_write_html(path: Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px;padding:20px 32px}
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
    cards = result.get("counts", {})
    card_html = "<div class='grid'>" + "".join(
        f"<div class='kpi'><div class='v'>{html.escape(str(v))}</div><div class='k'>{html.escape(str(k))}</div></div>"
        for k, v in cards.items()
    ) + "</div>"

    body = "".join(def_table_html(t, r) for t, r in sections)
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><title>VRN FinancialData Row-Level Join Repair v06153</title><style>{css}</style></head>
<body><header><h1>VRN · FinancialData Row-Level Evidence Join Repair v0.6.15.3</h1>
<div class="sub">reuse clean evidence · rebuild financial matrix · targeted restore queue separated · no canonical mutation</div></header>
{card_html}<main>{body}</main></body></html>"""
    path.write_text(doc, encoding="utf-8")


def def_main() -> None:
    if len(sys.argv) < 4:
        raise SystemExit("usage: py <run_root> <canonical_dir> <run_dir>")

    run_root = Path(sys.argv[1])
    canonical_dir = Path(sys.argv[2])
    run_dir = Path(sys.argv[3])
    run_dir.mkdir(parents=True, exist_ok=True)

    router_csv = def_find_latest(run_root, [
        "VRN_EVIDENCE_SOURCE_DECONTAMINATION_ROUTER_V06152_*/vrn_v06152_decontaminated_repair_router.csv"
    ])
    if not router_csv:
        raise RuntimeError("Cannot find v06152 decontaminated repair router csv.")

    router_rows = def_read_csv(router_csv)
    reuse_rows = [r for r in router_rows if def_clean_text(r.get("Repair Route")) == "REAL_REUSE_ROW_LEVEL_EVIDENCE"]
    restore_rows = [r for r in router_rows if def_clean_text(r.get("Repair Route")) == "TARGETED_TABLE_RESTORE_REQUIRED"]
    optional_rows = [r for r in router_rows if def_clean_text(r.get("Repair Route")) == "OPTIONAL_NO_FINANCIAL_REPAIR"]

    sources = def_scan_row_level_sources(run_root, canonical_dir)
    joined, alias_candidates = def_build_join_rows(reuse_rows, sources)
    coverage = def_category_coverage(joined, reuse_rows)

    ready_rows = [r for r in joined if def_clean_text(r.get("Validation Status")).startswith("READY")]
    partial_rows = [r for r in joined if not def_clean_text(r.get("Validation Status")).startswith("READY")]

    overview = [
        {"Status Lights": def_lights("OK"), "Gate": "SOURCE_ROUTER", "Value": str(router_csv), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "REUSE_FILES", "Value": len(reuse_rows), "Severity": "OK"},
        {"Status Lights": def_lights("WARN"), "Gate": "TARGETED_RESTORE_FILES", "Value": len(restore_rows), "Severity": "WARN"},
        {"Status Lights": def_lights("WARN"), "Gate": "OPTIONAL_FILES", "Value": len(optional_rows), "Severity": "WARN"},
        {"Status Lights": def_lights("OK"), "Gate": "ROW_LEVEL_SOURCES", "Value": len(sources), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "JOINED_FINANCIAL_ROWS", "Value": len(joined), "Severity": "OK"},
        {"Status Lights": def_lights("OK"), "Gate": "READY_JOINED_ROWS", "Value": len(ready_rows), "Severity": "OK"},
        {"Status Lights": def_lights("WARN"), "Gate": "PARTIAL_REVIEW_ROWS", "Value": len(partial_rows), "Severity": "WARN"},
        {"Status Lights": def_lights("WARN"), "Gate": "SSOT_ALIAS_CANDIDATES", "Value": len(alias_candidates), "Severity": "WARN"},
        {"Status Lights": def_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    joined_csv = run_dir / "vrn_v06153_financialdata_joined_rows.csv"
    ready_csv = run_dir / "vrn_v06153_ready_financialdata_rows.csv"
    partial_csv = run_dir / "vrn_v06153_partial_review_financialdata_rows.csv"
    coverage_csv = run_dir / "vrn_v06153_category_fetching_rate.csv"
    restore_csv = run_dir / "vrn_v06153_targeted_restore_queue.csv"
    alias_csv = run_dir / "vrn_v06153_ssot_alias_candidates.csv"
    html_path = run_dir / "VRN_FinancialData_Row_Level_Join_Repair_v06153.html"
    json_path = run_dir / "vrn_financialdata_row_level_join_repair_v06153.json"

    def_write_csv(joined_csv, joined)
    def_write_csv(ready_csv, ready_rows)
    def_write_csv(partial_csv, partial_rows)
    def_write_csv(coverage_csv, coverage)
    def_write_csv(restore_csv, restore_rows)
    def_write_csv(alias_csv, alias_candidates)

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": True,
        "source_router": str(router_csv),
        "counts": {
            "Reuse Files": len(reuse_rows),
            "Targeted Restore": len(restore_rows),
            "Optional": len(optional_rows),
            "Joined Rows": len(joined),
            "Ready Rows": len(ready_rows),
            "Partial Rows": len(partial_rows),
            "Alias Candidates": len(alias_candidates),
            "No Canonical Mutation": "YES",
        },
        "outputs": {
            "html": str(html_path),
            "json": str(json_path),
            "joined_csv": str(joined_csv),
            "ready_csv": str(ready_csv),
            "partial_csv": str(partial_csv),
            "coverage_csv": str(coverage_csv),
            "targeted_restore_csv": str(restore_csv),
            "alias_candidates_csv": str(alias_csv),
        },
        "rules": [
            "Use row-level evidence only.",
            "Separate targeted restore queue from join repair.",
            "Do not mutate canonical.",
            "Do not fake fill.",
            "SSOT alias candidates are review-only until numeric validation passes.",
        ],
    }

    def_write_json(json_path, result)
    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Ready Joined FinancialData Rows", ready_rows[:3000]),
        ("03 Partial Review FinancialData Rows", partial_rows[:3000]),
        ("04 Category Fetching Rate", coverage),
        ("05 Targeted Restore Queue", restore_rows),
        ("06 SSOT Alias Candidates Review Only", alias_candidates[:1000]),
        ("07 All Joined FinancialData Rows", joined[:5000]),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise