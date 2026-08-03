# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
import csv
import html
import importlib.util
import json
import py_compile
import re
import sys
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_FINANCIAL_RESCUE_SSOT_ALIAS_V06126"


# ==================================================================================================
# def 01_COMMON
# ==================================================================================================
def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = s.replace("不", "不")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def def_norm_key(x: Any) -> str:
    s = def_clean_text(x).lower()
    s = s.replace("不", "不")
    s = re.sub(r"[\s　%％()（）\[\]【】{}<>〈〉《》,，、;；:：|｜/／\\\-–—_+＋=＝~～!！?？.．]", "", s)
    return s


def def_status_lights(sev: str) -> str:
    s = str(sev or "").upper()
    if s in ["OK", "YES", "PASS", "GREEN", "N/A", "QUARANTINE_OK"]:
        return "🟢 INPUT 🟢 DB 🟢 TRUST"
    if s in ["WARN", "YELLOW", "REVIEW", "PARTIAL"]:
        return "🟢 INPUT 🟡 DB 🟡 TRUST"
    return "🔴 INPUT 🔴 DB 🔴 TRUST"


def def_float_or_none(x: Any):
    s = def_clean_text(x)
    if not s or s.lower() in ["nan", "none", "null"]:
        return None
    nums = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?%?|-?\d+(?:\.\d+)?%?", s)
    if len(nums) != 1:
        return None
    try:
        return float(nums[0].replace(",", "").replace("%", ""))
    except Exception:
        return None


def def_numeric_tokens(x: Any) -> list[str]:
    s = def_clean_text(x)
    return re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?%?|-?\d+(?:\.\d+)?%?", s)


def def_get(row: dict, keys: list[str]) -> str:
    for k in keys:
        if k in row and def_clean_text(row.get(k)):
            return def_clean_text(row.get(k))
    return ""


def def_write_json(path: str | Path, obj: Any) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def def_write_csv(path: str | Path, rows: list[dict]) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        rows = [{"empty_marker": ""}]
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with Path(path).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def def_read_csv_any(path: str | Path) -> list[dict]:
    p = Path(path)
    if not p.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            with p.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            continue
    return []


def def_import_module(path: str | Path):
    p = Path(path)
    spec = importlib.util.spec_from_file_location(p.stem, str(p))
    mod = importlib.util.module_from_spec(spec)
    if spec and spec.loader:
        spec.loader.exec_module(mod)
        return mod
    raise RuntimeError(f"cannot import module: {p}")


def def_compile_import(path: str | Path) -> dict:
    p = Path(path)
    out = {"path": str(p), "exists": p.exists(), "ast": False, "compile": False, "import": False, "error": ""}
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
        ast.parse(text)
        out["ast"] = True
        py_compile.compile(str(p), doraise=True)
        out["compile"] = True
        def_import_module(p)
        out["import"] = True
    except Exception:
        out["error"] = traceback.format_exc()
    return out


# ==================================================================================================
# def 02_RESCUE_RULES
# ==================================================================================================
def def_rescue_alias_rules() -> list[dict]:
    return [
        # Balance Sheet
        {"category": "Balance Sheet", "official": "Long Term Investments", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["長期投資合計", "長期投資", "採用權益法之投資", "長期股權投資"]},
        {"category": "Balance Sheet", "official": "Short Term Borrowings", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["短期借款", "短期銀行借款", "短借", "一年內到期借款"]},
        {"category": "Balance Sheet", "official": "Non Current Liabilities", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["長期負債合計", "非流動負債合計", "長期負債", "非流動負債"]},
        {"category": "Balance Sheet", "official": "Capital Surplus", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["資本公積", "資本公積合計"]},
        {"category": "Balance Sheet", "official": "Other Equity", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["其他權益", "其他權益項目"]},
        {"category": "Balance Sheet", "official": "Total Equity", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["權益總額", "權益總計", "股東權益總計", "權益總額 分配後", "母公司業主權益", "歸屬於母公司業主之權益"]},
        {"category": "Balance Sheet", "official": "Total Liabilities", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["負債總額", "負債總計", "負債總額 分配後"]},
        {"category": "Balance Sheet", "official": "Total Assets", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["資產總額", "資產總計", "資產合計"]},
        {"category": "Balance Sheet", "official": "Property Plant And Equipment", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["不動產廠房及設備", "不動產、廠房及設備", "不動產、廠房設備", "固定資產", "固定資產淨額", "PPE"]},
        {"category": "Balance Sheet", "official": "Intangible Assets", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["無形資產", "無形資產合計"]},
        {"category": "Balance Sheet", "official": "Other Assets", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["其他資產", "其他非流動資產", "其它非流動資產"]},

        # Income / Cash Flow
        {"category": "Income Statement", "official": "Depreciation And Amortization", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["折舊及攤提", "折舊及攤銷", "折舊攤銷", "D&A"]},
        {"category": "Income Statement", "official": "Profit Before Tax", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["稅前純益", "稅前淨利", "稅前利益"]},
        {"category": "Cash Flow Statement", "official": "Operating Cash Flow", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["營業活動現金", "營業活動現金流量", "營業活動之淨現金流入出"]},
        {"category": "Cash Flow Statement", "official": "Investing Cash Flow", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["投資活動現金", "投資活動現金流量", "長期投資變動"]},
        {"category": "Cash Flow Statement", "official": "Financing Cash Flow", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["籌資活動現金", "融資活動之淨現金流入出", "融資活動之淨現金流入(出)", "其他籌資活動現金流量"]},
        {"category": "Cash Flow Statement", "official": "Net Change In Cash", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["本期現金與約當現金增加數", "淨現金流量", "現金增加數"]},
        {"category": "Cash Flow Statement", "official": "Beginning Cash", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["期初現金", "期初現金與約當現金餘額"]},
        {"category": "Cash Flow Statement", "official": "Ending Cash", "unit": "mn TWD", "kind": "accounting_account", "aliases": ["期末現金", "期末現金與約當現金餘額"]},

        # Ratio
        {"category": "Ratio Analysis", "official": "Debt To Asset Ratio", "unit": "%", "kind": "ratio_analysis", "aliases": ["負債占資產比率", "負債比率", "負債資產比"]},
        {"category": "Ratio Analysis", "official": "Quick Ratio", "unit": "%", "kind": "ratio_analysis", "aliases": ["速動比率", "速動比率%"]},
        {"category": "Ratio Analysis", "official": "Interest Coverage Ratio", "unit": "x", "kind": "ratio_analysis", "aliases": ["利息保障倍數"]},
        {"category": "Ratio Analysis", "official": "Accounts Receivable Turnover", "unit": "x", "kind": "ratio_analysis", "aliases": ["應收款項週轉率", "應收帳款週轉率"]},
        {"category": "Ratio Analysis", "official": "Days Sales Outstanding", "unit": "days", "kind": "ratio_analysis", "aliases": ["平均收現日數", "應收帳款收現日數"]},
        {"category": "Ratio Analysis", "official": "Accounts Payable Turnover", "unit": "x", "kind": "ratio_analysis", "aliases": ["應付款項週轉率", "應付帳款週轉率"]},
        {"category": "Ratio Analysis", "official": "Days Inventory Outstanding", "unit": "days", "kind": "ratio_analysis", "aliases": ["平均銷貨日數", "存貨銷售日數"]},
        {"category": "Ratio Analysis", "official": "Fixed Asset Turnover", "unit": "x", "kind": "ratio_analysis", "aliases": ["不動產廠房及設備週轉率", "不動產、廠房及設備週轉率", "固定資產週轉率"]},
        {"category": "Ratio Analysis", "official": "Total Asset Turnover", "unit": "x", "kind": "ratio_analysis", "aliases": ["總資產週轉率"]},
    ]


def def_build_rescue_index() -> dict:
    idx = {}
    for item in def_rescue_alias_rules():
        terms = [item["official"]] + item.get("aliases", [])
        for t in terms:
            idx[def_norm_key(t)] = item
    return idx


def def_is_non_financial_noise(data_raw: str) -> tuple[bool, str]:
    s = def_clean_text(data_raw)
    k = def_norm_key(s)
    noise_keywords = [
        "融資餘額", "融券餘額", "張數", "借券", "三大法人", "外資", "投信", "自營商",
        "電子電腦及週邊設備", "產業別", "股價", "成交量", "均價", "技術指標"
    ]
    if any(def_norm_key(x) in k for x in noise_keywords):
        return True, "NON_FINANCIAL_MARKET_OR_HEADER_ROW"
    if re.fullmatch(r"[一二三四五六七八九十]+", s):
        return True, "MONTH_OR_HEADER_TOKEN"
    if re.fullmatch(r"\(?百萬元\)?|\(?千元\)?|\(?mn\)?|\(?ntd\)?", s.lower()):
        return True, "UNIT_ONLY_ROW"
    return False, ""


def def_rescue_match(data_raw: str, old_category: str = "", old_official: str = "") -> dict:
    idx = def_build_rescue_index()
    k = def_norm_key(data_raw)

    if k in idx:
        item = idx[k]
        return {
            "matched": "YES",
            "category": item["category"],
            "official": item["official"],
            "unit": item["unit"],
            "kind": item["kind"],
            "score": 100,
            "reason": "v06126 exact rescue alias",
        }

    for key, item in idx.items():
        if key and (key in k or k in key):
            return {
                "matched": "YES",
                "category": item["category"],
                "official": item["official"],
                "unit": item["unit"],
                "kind": item["kind"],
                "score": 82,
                "reason": "v06126 partial rescue alias",
            }

    return {
        "matched": "NO",
        "category": old_category,
        "official": old_official,
        "unit": "",
        "kind": "",
        "score": 0,
        "reason": "not found in rescue alias",
    }


# ==================================================================================================
# def 03_WRITE_SUPPORT_MODULE
# ==================================================================================================
def def_write_rescue_support_module(module_path: Path, json_path: Path) -> dict:
    rules = def_rescue_alias_rules()
    payload = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "rules": rules,
        "policy": {
            "append_only": "YES",
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
            "usage": "preview rescue layer for Financial Data validation",
        },
    }
    def_write_json(json_path, payload)

    code = f'''# -*- coding: utf-8 -*-
# Auto-generated by {VERSION}
# Role: VIS / VRN Financial Rescue Rules
# Policy: append-only support module; no canonical mutation.

from __future__ import annotations
import re
from typing import Any

VERSION = "{VERSION}"
RESCUE_RULES = {repr(rules)}

def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\\u3000", " ").replace("不", "不")
    return re.sub(r"\\s+", " ", s).strip()

def def_norm_key(x: Any) -> str:
    s = def_clean_text(x).lower()
    return re.sub(r"[\\s　%％()（）\\[\\]【】{{}}<>〈〉《》,，、;；:：|｜/／\\\\\\-–—_+＋=＝~～!！?？.．]", "", s)

def def_get_rescue_rules_v06126():
    return list(RESCUE_RULES)

def def_build_rescue_index_v06126():
    idx = {{}}
    for item in RESCUE_RULES:
        for t in [item.get("official", "")] + list(item.get("aliases", [])):
            idx[def_norm_key(t)] = item
    return idx

def def_match_financial_rescue_v06126(data_raw: Any):
    idx = def_build_rescue_index_v06126()
    k = def_norm_key(data_raw)
    if k in idx:
        item = idx[k]
        return {{"matched": "YES", "category": item["category"], "official": item["official"], "unit": item["unit"], "kind": item["kind"], "score": 100, "reason": "exact rescue alias"}}
    for key, item in idx.items():
        if key and (key in k or k in key):
            return {{"matched": "YES", "category": item["category"], "official": item["official"], "unit": item["unit"], "kind": item["kind"], "score": 82, "reason": "partial rescue alias"}}
    return {{"matched": "NO", "score": 0, "reason": "not found"}}
'''
    module_path.parent.mkdir(parents=True, exist_ok=True)
    module_path.write_text(code, encoding="utf-8")
    chk = def_compile_import(module_path)
    return {"module": str(module_path), "json": str(json_path), **chk}


# ==================================================================================================
# def 04_SOURCE_RESOLUTION
# ==================================================================================================
def def_find_latest_v06125_json(run_root: Path) -> Path | None:
    hits = sorted(run_root.rglob("vrn_financial_data_confirm_verify_v06125.json"), key=lambda x: x.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_find_latest_v06125_validated(run_root: Path) -> Path | None:
    hits = sorted(run_root.rglob("vrn_v06125_financial_validated.csv"), key=lambda x: x.stat().st_mtime, reverse=True)
    return hits[0] if hits else None


def def_scan_report_date_evidence(run_root: Path) -> dict:
    evidence = defaultdict(Counter)
    for p in run_root.rglob("*.csv"):
        if p.name.lower().startswith("vrn_v06125"):
            continue
        rows = def_read_csv_any(p)
        if not rows:
            continue
        for r in rows[:5000]:
            fn = def_get(r, ["Filename", "filename", "Pdf", "PDF", "File"])
            rd = def_get(r, ["Report Date", "report_date", "ReportDate", "Filename Report Date Parsed"])
            if fn and re.fullmatch(r"20\d{2}-\d{2}-\d{2}", rd):
                evidence[Path(fn).name][rd] += 1

    out = {}
    for fn, c in evidence.items():
        if c:
            out[fn] = c.most_common(1)[0][0]
    return out


# ==================================================================================================
# def 05_RESCUE_APPLY
# ==================================================================================================
def def_apply_rescue(rows: list[dict], report_date_evidence: dict) -> tuple[list[dict], list[dict], list[dict]]:
    rescued = []
    quarantine = []
    review = []

    for r in rows:
        nr = dict(r)
        fn = def_get(nr, ["Filename"])
        raw = def_get(nr, ["Data Raw"])
        old_cat = def_get(nr, ["Category Official En"])
        old_official = def_get(nr, ["Data Official En"])

        is_noise, q_reason = def_is_non_financial_noise(raw)
        if is_noise:
            nr["Rescue Action"] = "QUARANTINE"
            nr["Quarantine Reason"] = q_reason
            nr["Severity"] = "OK"
            nr["Status Lights"] = def_status_lights("QUARANTINE_OK")
            quarantine.append(nr)
            continue

        # Report date evidence rescue
        if not def_get(nr, ["Report Year"]) and fn:
            rd = report_date_evidence.get(Path(fn).name, "")
            if rd:
                nr["Report Date Evidence"] = rd
                nr["Report Year"] = rd[:4]
                nr["Report Year Rescue"] = "YES_FROM_EVIDENCE_REGISTRY"
            else:
                nr["Report Year Rescue"] = "NO_EVIDENCE_FOUND"

        # Multi-value row mark
        value_raw = def_get(nr, ["Value Raw"])
        nums = def_numeric_tokens(value_raw)
        if len(nums) > 1:
            nr["Value Split Required"] = "YES"
            nr["Value Numeric Candidates"] = " | ".join(nums)
            # 不假填，不直接選一個；但從 RED 降為 WARN，交給下一輪 table coordinate split。
            nr["Numeric Status"] = "SPLIT_REVIEW"

        m = def_rescue_match(raw, old_cat, old_official)
        if m["matched"] == "YES" and (not old_official or def_get(nr, ["SSOT Matched"]) != "YES"):
            nr["Category Official En Before Rescue"] = old_cat
            nr["Data Official En Before Rescue"] = old_official
            nr["Category Official En"] = m["category"]
            nr["Data Official En"] = m["official"]
            nr["Unit Rescued"] = m["unit"]
            nr["Financial Kind Rescued"] = m["kind"]
            nr["SSOT Matched"] = "YES"
            nr["SSOT Score"] = m["score"]
            nr["SSOT Match Reason"] = m["reason"]
            nr["Rescue Action"] = "SSOT_ALIAS_RESCUE"
        elif not nr.get("Rescue Action"):
            nr["Rescue Action"] = "KEEP_OR_REVIEW"

        # Unit rescue
        unit = def_get(nr, ["Unit Rescued", "Unit"])
        if not unit:
            data_key = def_norm_key(raw)
            if "比率" in raw or "%" in raw:
                unit = "%"
            elif "週轉率" in raw or "倍數" in raw or "次" in raw:
                unit = "x"
            elif "日數" in raw:
                unit = "days"
            elif def_get(nr, ["Category Official En"]) in ["Income Statement", "Balance Sheet", "Cash Flow Statement"]:
                unit = "mn TWD"
        nr["Unit Final"] = unit

        # Re-score
        numeric_ok = def_get(nr, ["Numeric Status"]) == "OK"
        split_review = def_get(nr, ["Numeric Status"]) == "SPLIT_REVIEW"
        ssot_ok = def_get(nr, ["SSOT Matched"]) == "YES"
        period_ok = def_get(nr, ["Period Check"]) == "OK" or bool(def_get(nr, ["Report Year"]))
        ticker_ok = bool(def_get(nr, ["Ticker"]))

        score = 0
        score += 35 if ssot_ok else 0
        score += 25 if numeric_ok else (15 if split_review else 0)
        score += 20 if period_ok else 0
        score += 10 if ticker_ok else 0
        score += 10 if unit else 0

        if score >= 85:
            band = "GREEN"
            sev = "OK"
        elif score >= 65:
            band = "YELLOW"
            sev = "WARN"
        else:
            band = "RED"
            sev = "ERR"

        nr["Final Trust Score Before Rescue"] = def_get(r, ["Final Trust Score"])
        nr["Final Trust Band Before Rescue"] = def_get(r, ["Final Trust Band"])
        nr["Final Trust Score"] = score
        nr["Final Trust Band"] = band
        nr["Severity"] = sev
        nr["Status Lights"] = def_status_lights(sev)

        rescued.append(nr)

        if sev != "OK":
            issues = []
            if not ssot_ok:
                issues.append("SSOT_ALIAS_STILL_MISSING")
            if not numeric_ok:
                issues.append("VALUE_SPLIT_OR_NUMERIC_REVIEW")
            if not period_ok:
                issues.append("REPORT_DATE_EVIDENCE_MISSING")
            review.append({
                "Status Lights": def_status_lights(sev),
                "Filename": fn,
                "Ticker": def_get(nr, ["Ticker"]),
                "Data Raw": raw,
                "Issue Type": " | ".join(issues),
                "Recommended Next Step": "If still RED after alias rescue, rerun table coordinate restore for this file/table only. No fake fill.",
                "Severity": sev,
            })

    return rescued, quarantine, review


def def_coverage(rows: list[dict]) -> list[dict]:
    core = {
        "Income Statement": ["Revenue", "Gross Profit", "Operating Income", "Net Income", "EPS"],
        "Balance Sheet": ["Total Assets", "Total Liabilities", "Total Equity", "Cash And Cash Equivalents", "Current Assets", "Current Liabilities"],
        "Cash Flow Statement": ["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow", "Net Change In Cash", "Capital Expenditure", "Ending Cash"],
        "Ratio Analysis": ["Gross Margin", "Operating Margin", "Net Margin", "ROE", "ROA", "Current Ratio"],
        "Per Share Analysis": ["EPS", "BVPS", "CFPS"],
    }

    grouped = defaultdict(set)
    rowcount = defaultdict(int)
    errcount = defaultdict(int)
    for r in rows:
        fn = def_get(r, ["Filename"])
        ticker = def_get(r, ["Ticker"])
        cat = def_get(r, ["Category Official En"])
        off = def_get(r, ["Data Official En"])
        if not cat:
            continue
        key = (fn, ticker, cat)
        rowcount[key] += 1
        if off:
            grouped[key].add(off)
        if def_get(r, ["Severity"]) == "ERR":
            errcount[key] += 1

    out = []
    for (fn, ticker, cat), found in grouped.items():
        expected = core.get(cat, [])
        if expected:
            hit = [x for x in expected if x in found]
            miss = [x for x in expected if x not in found]
            rate = round(100 * len(hit) / max(len(expected), 1), 2)
            ratio = f"{len(hit)}/{len(expected)}"
        else:
            rate = 100.0
            ratio = f"{len(found)}/optional"
            miss = []

        sev = "OK" if rate >= 60 and errcount[(fn, ticker, cat)] == 0 else ("WARN" if rate >= 35 else "ERR")
        out.append({
            "Status Lights": def_status_lights(sev),
            "Filename": fn,
            "Ticker": ticker,
            "Category": cat,
            "Core Coverage": ratio,
            "Coverage Rate": rate,
            "Core Missing Items": " | ".join(miss),
            "Rows": rowcount[(fn, ticker, cat)],
            "Err Rows": errcount[(fn, ticker, cat)],
            "Severity": sev,
        })
    return out


# ==================================================================================================
# def 06_HTML
# ==================================================================================================
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
            cls = "left" if any(x in lc for x in ["file", "raw", "reason", "step", "issue", "path", "alias"]) else "center"
            cls = "right" if any(x in lc for x in ["score", "rows", "rate", "count"]) else cls
            tds.append(f"<td class='{cls}'>{html.escape(v)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


def def_write_html(path: str | Path, result: dict, sections: list[tuple[str, list[dict]]]) -> None:
    css = """
body{margin:0;background:#07111f;color:#eef6ff;font-family:Segoe UI,'Microsoft JhengHei',Arial,sans-serif;font-size:12px}
header{padding:24px 32px;background:#0d1b2f;border-bottom:1px solid #1f3557;position:sticky;top:0;z-index:10}
h1{margin:0;font-size:24px}.sub{color:#9fb3c8;margin-top:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:14px;padding:20px 32px}
.kpi{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;padding:16px;box-shadow:0 10px 28px rgba(0,0,0,.22)}
.v{font-size:26px;font-weight:800}.k{color:#9fb3c8}
main{padding:0 32px 32px}.card{background:#0d1b2f;border:1px solid #1f3557;border-radius:18px;margin:18px 0;padding:18px}
.table-wrap{overflow:auto;max-height:76vh;border:1px solid #1f3557;border-radius:14px}
table{border-collapse:collapse;min-width:100%;width:max-content}
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;vertical-align:top}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;text-align:center;max-width:860px;white-space:normal;word-break:break-word}
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
<head><meta charset="utf-8"><title>VRN Financial Rescue SSOT Alias v06126</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · Financial Data Rescue + SSOT Alias Completion v0.6.12.6</h1>
<div class="sub">not re-extract PDF · alias rescue · non-financial quarantine · report date evidence · trust recalibration · no canonical mutation</div>
</header>
{card_html}
<main>{body}</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    Path(path).write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 07_MAIN
# ==================================================================================================
def def_main():
    if len(sys.argv) < 7:
        raise SystemExit("usage: py <run_root> <bridge_module> <rescue_module> <rescue_json> <run_dir> <canonical_dir>")

    run_root = Path(sys.argv[1])
    bridge_module = Path(sys.argv[2])
    rescue_module = Path(sys.argv[3])
    rescue_json = Path(sys.argv[4])
    run_dir = Path(sys.argv[5])
    canonical_dir = Path(sys.argv[6])
    run_dir.mkdir(parents=True, exist_ok=True)

    source_json = def_find_latest_v06125_json(run_root)
    source_csv = def_find_latest_v06125_validated(run_root)
    source_rows = def_read_csv_any(source_csv) if source_csv else []

    support_status = def_write_rescue_support_module(rescue_module, rescue_json)
    bridge_status = def_compile_import(bridge_module)

    date_evidence = def_scan_report_date_evidence(run_root)
    rescued, quarantine, review = def_apply_rescue(source_rows, date_evidence)
    coverage = def_coverage(rescued)

    green = sum(1 for r in rescued if r.get("Severity") == "OK")
    yellow = sum(1 for r in rescued if r.get("Severity") == "WARN")
    red = sum(1 for r in rescued if r.get("Severity") == "ERR")
    cov_err = sum(1 for r in coverage if r.get("Severity") == "ERR")
    rescued_alias = sum(1 for r in rescued if r.get("Rescue Action") == "SSOT_ALIAS_RESCUE")
    split_rows = sum(1 for r in rescued if r.get("Value Split Required") == "YES")

    system_pass = bool(source_rows and support_status.get("import") and bridge_status.get("import"))
    operational_pass = bool(system_pass and red == 0 and cov_err == 0)

    overview = [
        {"Status Lights": def_status_lights("OK" if system_pass else "ERR"), "Gate": "SYSTEM_PASS", "Value": "YES" if system_pass else "NO", "Severity": "OK" if system_pass else "ERR"},
        {"Status Lights": def_status_lights("OK" if operational_pass else "WARN"), "Gate": "OPERATIONAL_PASS", "Value": "YES" if operational_pass else "REVIEW", "Severity": "OK" if operational_pass else "WARN"},
        {"Status Lights": def_status_lights("OK"), "Gate": "SOURCE_CSV", "Value": str(source_csv) if source_csv else "", "Severity": "OK" if source_csv else "ERR"},
        {"Status Lights": def_status_lights("OK"), "Gate": "SOURCE_ROWS", "Value": len(source_rows), "Severity": "OK" if source_rows else "ERR"},
        {"Status Lights": def_status_lights("OK"), "Gate": "RESCUE_ALIAS_ROWS", "Value": rescued_alias, "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "QUARANTINE_ROWS", "Value": len(quarantine), "Severity": "OK"},
        {"Status Lights": def_status_lights("WARN" if split_rows else "OK"), "Gate": "VALUE_SPLIT_REQUIRED_ROWS", "Value": split_rows, "Severity": "WARN" if split_rows else "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "GREEN_ROWS", "Value": green, "Severity": "OK"},
        {"Status Lights": def_status_lights("WARN" if yellow else "OK"), "Gate": "YELLOW_ROWS", "Value": yellow, "Severity": "WARN" if yellow else "OK"},
        {"Status Lights": def_status_lights("ERR" if red else "OK"), "Gate": "RED_ROWS", "Value": red, "Severity": "ERR" if red else "OK"},
        {"Status Lights": def_status_lights("ERR" if cov_err else "OK"), "Gate": "COVERAGE_ERR", "Value": cov_err, "Severity": "ERR" if cov_err else "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    support_rows = [
        {"Status Lights": def_status_lights("OK" if support_status.get("import") else "ERR"), "Module": "VIS_VRN_FinancialRescueRules_v06126.py", **support_status},
        {"Status Lights": def_status_lights("OK" if bridge_status.get("import") else "ERR"), "Module": "VIS_VRN_MasterRegistryBridge_v0611.py", **bridge_status},
    ]

    html_path = str(run_dir / "VRN_Financial_Rescue_SSOT_Alias_v06126.html")
    json_path = str(run_dir / "vrn_financial_rescue_ssot_alias_v06126.json")
    overview_csv = str(run_dir / "vrn_v06126_overview.csv")
    rescued_csv = str(run_dir / "vrn_v06126_financial_rescued.csv")
    quarantine_csv = str(run_dir / "vrn_v06126_quarantine.csv")
    coverage_csv = str(run_dir / "vrn_v06126_coverage.csv")
    review_csv = str(run_dir / "vrn_v06126_review_queue.csv")
    support_csv = str(run_dir / "vrn_v06126_support.csv")

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": "YES" if system_pass else "NO",
        "operational_pass": "YES" if operational_pass else "REVIEW",
        "source_json": str(source_json) if source_json else "",
        "source_csv": str(source_csv) if source_csv else "",
        "counts": {
            "System Pass": "YES" if system_pass else "NO",
            "Operational Pass": "YES" if operational_pass else "REVIEW",
            "Source Rows": len(source_rows),
            "Green Rows": green,
            "Yellow Rows": yellow,
            "Red Rows": red,
            "Coverage Err": cov_err,
            "Alias Rescued": rescued_alias,
            "Quarantine": len(quarantine),
            "Split Review": split_rows,
        },
        "outputs": {
            "html": html_path,
            "json": json_path,
            "overview_csv": overview_csv,
            "rescued_csv": rescued_csv,
            "quarantine_csv": quarantine_csv,
            "coverage_csv": coverage_csv,
            "review_csv": review_csv,
            "support_csv": support_csv,
            "rescue_module": str(rescue_module),
            "rescue_json": str(rescue_json),
        },
        "policy": {
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
            "preview_only": "YES",
            "no_fake_fill": "YES",
        },
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(rescued_csv, rescued)
    def_write_csv(quarantine_csv, quarantine)
    def_write_csv(coverage_csv, coverage)
    def_write_csv(review_csv, review)
    def_write_csv(support_csv, support_rows)
    def_write_json(json_path, result)
    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Rescued Financial Data", rescued[:900]),
        ("03 Quarantine", quarantine),
        ("04 Coverage", coverage),
        ("05 Review Queue", review),
        ("06 Supportive", support_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise