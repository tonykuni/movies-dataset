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

import ast
import csv
import html
import importlib.util
import json
import math
import os
import py_compile
import re
import sys
import traceback
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any


VERSION = "VRN_FINANCIAL_DATA_CONFIRM_VERIFY_V06125"


# ==================================================================================================
# def 01_COMMON
# ==================================================================================================
def def_clean_text(x: Any) -> str:
    s = "" if x is None else str(x)
    s = s.replace("\u3000", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


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


def def_backup(path: Path, tag: str) -> str:
    backup = str(path) + f".bak_{tag}_" + datetime.now().strftime("%Y%m%d_%H%M%S")
    Path(backup).write_text(path.read_text(encoding="utf-8", errors="ignore"), encoding="utf-8")
    return backup


# ==================================================================================================
# def 02_PATCH_BRIDGE_DATE_CANDIDATE_NOISE
# ==================================================================================================
BRIDGE_DATE_REPLACEMENT = r'''
def def_extract_report_date_from_filename(filename: Any) -> dict:
    raw = Path(def_clean_text(filename)).name
    stem = re.sub(r"\.pdf$", "", raw, flags=re.I)

    def _fw_to_hw(x: Any) -> str:
        s = def_clean_text(x)
        out = []
        for ch in s:
            code = ord(ch)
            if code == 12288:
                out.append(" ")
            elif 65281 <= code <= 65374:
                out.append(chr(code - 65248))
            else:
                out.append(ch)
        return "".join(out)

    def _filename_tokens(x: Any) -> dict:
        st = re.sub(r"\.pdf$", "", Path(def_clean_text(x)).name, flags=re.I)
        norm = _fw_to_hw(st)
        norm = re.sub(r"[()（）\[\]【】{}<>〈〉《》,_，、;；:：|｜+＋=＝~～!！?？\\/]", " ", norm)
        norm = re.sub(r"[-–—_]", " ", norm)
        norm = re.sub(r"\s+", " ", norm).strip()

        digit_tokens = re.findall(r"(?<!\d)\d+(?!\d)", norm)
        english_tokens = re.findall(r"[A-Za-z]+", norm)
        chinese_tokens = re.findall(r"[\u4e00-\u9fff]+", norm)

        ticker_tokens = []
        date_tokens = []
        for t in digit_tokens:
            if TW_TICKER_REGEX.match(t):
                ticker_tokens.append(t)
            elif len(t) >= 5:
                date_tokens.append(t)

        return {
            "filename": Path(def_clean_text(x)).name,
            "stem": st,
            "normalized": norm,
            "digit_tokens": digit_tokens,
            "ticker_tokens": list(dict.fromkeys(ticker_tokens)),
            "date_tokens": list(dict.fromkeys(date_tokens)),
            "english_tokens": english_tokens,
            "chinese_tokens": chinese_tokens,
        }

    def _date_from_numeric_token(token: Any) -> list[str]:
        t = def_clean_text(token)
        out = []

        if re.fullmatch(r"20\d{6}", t):
            y, m, d = int(t[0:4]), int(t[4:6]), int(t[6:8])
            if 2000 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                out.append(f"{y:04d}-{m:02d}-{d:02d}")

        elif re.fullmatch(r"1\d{6}", t):
            roc_y, m, d = int(t[0:3]), int(t[3:5]), int(t[5:7])
            y = roc_y + 1911
            if 2000 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                out.append(f"{y:04d}-{m:02d}-{d:02d}")

        elif re.fullmatch(r"\d{6}", t):
            yy, m, d = int(t[0:2]), int(t[2:4]), int(t[4:6])
            y = 2000 + yy
            if 2020 <= y <= 2099 and 1 <= m <= 12 and 1 <= d <= 31:
                out.append(f"{y:04d}-{m:02d}-{d:02d}")

        elif re.fullmatch(r"20\d{4}", t):
            y, m = int(t[0:4]), int(t[4:6])
            if 2000 <= y <= 2099 and 1 <= m <= 12:
                out.append(f"{y:04d}-{m:02d}")

        return list(dict.fromkeys(out))

    tokens = _filename_tokens(raw)
    candidates = []
    occupied_digit_tokens = set()

    # Strong rule: date_tokens are parsed first. If a token is consumed as continuous date,
    # do not let loose separated regex re-parse inside that same continuous token.
    for tok in tokens.get("date_tokens", []):
        parsed = _date_from_numeric_token(tok)
        if parsed:
            candidates.extend(parsed)
            occupied_digit_tokens.add(tok)

    masked_stem = stem
    for tok in sorted(occupied_digit_tokens, key=len, reverse=True):
        masked_stem = re.sub(re.escape(tok), " " * len(tok), masked_stem)

    # Separated AD YYYY-MM-DD / YYYY_MM_DD / YYYY年MM月DD日 only after masking continuous date tokens.
    for m in re.finditer(r"(20\d{2})[-_/年.]+(0?[1-9]|1[0-2])[-_/月.]+(0?[1-9]|[12]\d|3[01])", masked_stem):
        y = int(m.group(1))
        mo = int(m.group(2))
        d = int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            candidates.append(f"{y:04d}-{mo:02d}-{d:02d}")

    # Separated ROC YYY-MM-DD.
    for m in re.finditer(r"(?<!\d)(1\d{2})[-_/年.]+(0?[1-9]|1[0-2])[-_/月.]+(0?[1-9]|[12]\d|3[01])(?!\d)", masked_stem):
        y = int(m.group(1)) + 1911
        mo = int(m.group(2))
        d = int(m.group(3))
        if 2000 <= y <= 2099 and 1 <= mo <= 12 and 1 <= d <= 31:
            candidates.append(f"{y:04d}-{mo:02d}-{d:02d}")

    # Separated omitted-century YY-MM-DD.
    for m in re.finditer(r"(?<!\d)(2[0-9])[-_/年.]+(0?[1-9]|1[0-2])[-_/月.]+(0?[1-9]|[12]\d|3[01])(?!\d)", masked_stem):
        y = 2000 + int(m.group(1))
        mo = int(m.group(2))
        d = int(m.group(3))
        if 2020 <= y <= 2099 and 1 <= mo <= 12 and 1 <= d <= 31:
            candidates.append(f"{y:04d}-{mo:02d}-{d:02d}")

    # Year-only fallback. Do not add year-only if full date already exists for same year.
    full_years = set(x[:4] for x in candidates if re.fullmatch(r"20\d{2}-\d{2}-\d{2}", x))
    for m in re.finditer(r"(?<!\d)(20\d{2})(?!\d)", masked_stem):
        y = m.group(1)
        if y not in full_years:
            candidates.append(y)

    candidates = list(dict.fromkeys(candidates))
    full_dates = [x for x in candidates if re.fullmatch(r"20\d{2}-\d{2}-\d{2}", x)]
    best = full_dates[0] if full_dates else (candidates[0] if candidates else "")

    return {
        "report_date": best,
        "report_date_candidates": candidates,
        "filename_tokens": tokens,
        "source": "BRIDGE_FILENAME_DATE_TOKENIZER_V06125" if candidates else "NONE",
    }
'''


def def_replace_function(text: str, func_name: str, new_func: str) -> tuple[str, bool]:
    pattern = re.compile(
        r"^def\s+" + re.escape(func_name) + r"\s*\(.*?\):\n"
        r"(?:(?:    .*\n)|(?:\s*\n))*",
        flags=re.M
    )
    m = pattern.search(text)
    if not m:
        return text.rstrip() + "\n\n" + new_func.rstrip() + "\n", False
    return text[:m.start()] + new_func.rstrip() + "\n\n" + text[m.end():], True


def def_patch_bridge_date_noise(bridge_path: Path) -> dict:
    row = {"file": str(bridge_path), "backup": "", "patched": "NO", "replace_found": "NO", "severity": "ERR", "error": ""}
    try:
        if not bridge_path.exists():
            row["error"] = "Bridge not found"
            return row
        text = bridge_path.read_text(encoding="utf-8", errors="ignore")
        row["backup"] = def_backup(bridge_path, "v06125_date_candidate_noise")
        text2, found = def_replace_function(text, "def_extract_report_date_from_filename", BRIDGE_DATE_REPLACEMENT)
        bridge_path.write_text(text2, encoding="utf-8")
        row["patched"] = "YES"
        row["replace_found"] = "YES" if found else "APPENDED"
        row["severity"] = "OK"
    except Exception:
        row["error"] = traceback.format_exc()
    return row


def def_smoke_date_noise(bridge_path: Path) -> list[dict]:
    rows = []
    try:
        mod = def_import_module(bridge_path)
        samples = [
            {"filename": "20251204兆豐個股報告-志強-KY(6768).pdf", "expected_date": "2025-12-04", "bad": "2025-01-02"},
            {"filename": "Daiwa-1319 20231011.pdf", "expected_date": "2023-10-11", "bad": "2023-01-01"},
            {"filename": "CLST-6669 20251001.pdf", "expected_date": "2025-10-01", "bad": "2025-01-00"},
            {"filename": "晶心科(6533,N,中立)-CTBC251208.pdf", "expected_date": "2025-12-08", "bad": ""},
            {"filename": "華南投顧-3017-奇鋐-1141202.pdf", "expected_date": "2025-12-02", "bad": ""},
        ]
        for s in samples:
            d = mod.def_extract_report_date_from_filename(s["filename"])
            cands = d.get("report_date_candidates", [])
            bad_absent = (not s["bad"]) or (s["bad"] not in cands)
            ok = d.get("report_date") == s["expected_date"] and bad_absent
            rows.append({
                "Status Lights": def_status_lights("OK" if ok else "ERR"),
                "Filename": s["filename"],
                "Extracted Date": d.get("report_date", ""),
                "Expected Date": s["expected_date"],
                "Candidates": " | ".join(cands),
                "Bad Candidate Must Be Absent": s["bad"],
                "Bad Candidate Absent": "YES" if bad_absent else "NO",
                "Severity": "OK" if ok else "ERR",
            })
    except Exception:
        rows.append({"Status Lights": def_status_lights("ERR"), "Filename": "IMPORT_FAIL", "Error": traceback.format_exc(), "Severity": "ERR"})
    return rows


# ==================================================================================================
# def 03_SOURCE_RESOLUTION
# ==================================================================================================
def def_find_latest_json(run_root: Path, keywords: list[str]) -> Path | None:
    files = []
    if not run_root.exists():
        return None
    for p in run_root.rglob("*.json"):
        s = str(p).lower()
        if all(k.lower() in s for k in keywords):
            files.append(p)
    files = sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)
    return files[0] if files else None


def def_find_latest_csv(run_root: Path, canonical_dir: Path) -> tuple[Path | None, str]:
    preferred_patterns = [
        "*vrn_financial_ssot_complete_trust_integration_v0608*.csv",
        "*vrn_broker_yfinance_consensus_join_v0607*.csv",
        "*vrn_name_short_financial_validation_v0606*.csv",
        "*vrn_financial_candidate_v0603.csv",
        "*vrn_financial_raw_first_rebind_v0600.csv",
        "*vrn_financial_active.csv",
    ]

    roots = [run_root, canonical_dir]
    for pat in preferred_patterns:
        hits = []
        for root in roots:
            if root and root.exists():
                hits.extend(root.rglob(pat))
        hits = sorted(hits, key=lambda x: x.stat().st_mtime, reverse=True)
        if hits:
            return hits[0], pat

    fallback = canonical_dir / "vrn_financial_active.csv"
    if fallback.exists():
        return fallback, "canonical_fallback"
    return None, ""


def def_load_latest_financial(run_root: Path, canonical_dir: Path) -> tuple[list[dict], dict]:
    csv_path, source_type = def_find_latest_csv(run_root, canonical_dir)
    rows = def_read_csv_any(csv_path) if csv_path else []
    meta = {"source_csv": str(csv_path) if csv_path else "", "source_type": source_type, "rows": len(rows)}
    return rows, meta


# ==================================================================================================
# def 04_FINANCIAL_VALIDATION
# ==================================================================================================
def def_float_or_none(x: Any):
    s = def_clean_text(x).replace(",", "").replace("%", "")
    if s == "" or s.lower() in ["nan", "none", "null"]:
        return None
    try:
        return float(s)
    except Exception:
        return None


def def_get_first(row: dict, keys: list[str]) -> str:
    for k in keys:
        if k in row and def_clean_text(row.get(k)):
            return def_clean_text(row.get(k))
    return ""


def def_year_from_row(row: dict) -> str:
    y = def_get_first(row, ["Year", "year", "Fiscal Year", "FiscalYear", "Period Year"])
    if re.fullmatch(r"\d{4}", y):
        return y
    period = def_get_first(row, ["Period", "period", "Date", "Report Period"])
    m = re.search(r"(20\d{2})", period)
    return m.group(1) if m else ""


def def_report_year(row: dict, bridge) -> str:
    rd = def_get_first(row, ["Report Date", "report_date", "ReportDate"])
    m = re.search(r"(20\d{2})", rd)
    if m:
        return m.group(1)

    fn = def_get_first(row, ["Filename", "filename", "Pdf", "PDF", "File"])
    if fn:
        try:
            d = bridge.def_extract_report_date_from_filename(fn)
            m = re.search(r"(20\d{2})", d.get("report_date", ""))
            if m:
                return m.group(1)
        except Exception:
            pass
    return ""


def def_period_ok(row: dict, bridge, window: int = 3) -> tuple[str, str]:
    ry = def_report_year(row, bridge)
    y = def_year_from_row(row)
    if not ry or not y:
        return "REVIEW", ""
    try:
        ryi = int(ry)
        yi = int(y)
        win = list(range(ryi - window, ryi + window + 1))
        return ("OK" if yi in win else "ERR", ",".join(str(v) for v in win))
    except Exception:
        return "REVIEW", ""


def def_validate_financial_rows(rows: list[dict], bridge) -> tuple[list[dict], list[dict], list[dict]]:
    ssot_index = bridge.def_build_financial_ssot_index()
    out = []
    review = []

    for idx, row in enumerate(rows, start=1):
        r = dict(row)
        raw = def_get_first(r, ["Data Raw", "Data", "Data Official En", "Account", "Item", "data_raw"])
        value_raw = def_get_first(r, ["Value Raw", "Value", "Value Numeric", "value_raw", "value_numeric"])
        filename = def_get_first(r, ["Filename", "filename", "Pdf", "PDF", "File"])
        ticker = def_get_first(r, ["Ticker", "ticker"])

        try:
            if not ticker and filename:
                ticker = bridge.def_extract_tw_ticker_from_filename(filename).get("ticker", "")
        except Exception:
            ticker = ""

        try:
            m = bridge.def_match_financial_account(raw, ssot_index)
        except Exception:
            m = {"SSOT Matched": "NO", "SSOT Score": 0, "SSOT Match Reason": "bridge match error"}

        val = def_float_or_none(value_raw)
        numeric_status = "OK" if val is not None else "REVIEW"

        p_ok, win = def_period_ok(r, bridge)

        ssot_matched = m.get("SSOT Matched", "NO")
        ssot_score = float(m.get("SSOT Score", 0) or 0)

        score = 0
        score += 35 if ssot_matched == "YES" else 0
        score += 25 if numeric_status == "OK" else 0
        score += 20 if p_ok == "OK" else (10 if p_ok == "REVIEW" else 0)
        score += 10 if filename else 0
        score += 10 if ticker else 0

        if score >= 85:
            band = "GREEN"
            sev = "OK"
        elif score >= 65:
            band = "YELLOW"
            sev = "WARN"
        else:
            band = "RED"
            sev = "ERR"

        nr = {
            "Status Lights": def_status_lights(sev),
            "Row ID": idx,
            "Filename": filename,
            "Ticker": ticker,
            "Report Year": def_report_year(r, bridge),
            "Year": def_year_from_row(r),
            "Expected Year Window": win,
            "Period Check": p_ok,
            "Data Raw": raw,
            "Category Official En": m.get("Category Official En", r.get("Category Official En", "")),
            "Data Official En": m.get("Data Official En", r.get("Data Official En", "")),
            "Value Raw": value_raw,
            "Value Numeric": "" if val is None else val,
            "Numeric Status": numeric_status,
            "SSOT Matched": ssot_matched,
            "SSOT Score": ssot_score,
            "SSOT Match Reason": m.get("SSOT Match Reason", ""),
            "Final Trust Score": score,
            "Final Trust Band": band,
            "Severity": sev,
        }
        out.append(nr)

        if sev != "OK":
            issue = []
            if ssot_matched != "YES":
                issue.append("SSOT_UNMATCHED")
            if numeric_status != "OK":
                issue.append("NUMERIC_REVIEW")
            if p_ok != "OK":
                issue.append("PERIOD_REVIEW")
            review.append({
                "Status Lights": def_status_lights(sev),
                "Filename": filename,
                "Ticker": ticker,
                "Year": nr["Year"],
                "Data Raw": raw,
                "Issue Type": " | ".join(issue),
                "Recommended Next Step": "Review table restore / SSOT alias / value parsing. No fake fill.",
                "Severity": sev,
            })

    # coverage by file/category
    grouped = defaultdict(lambda: {"found": set(), "rows": 0, "green": 0, "warn": 0, "err": 0})
    for r in out:
        key = (r.get("Filename", ""), r.get("Ticker", ""), r.get("Category Official En", ""))
        g = grouped[key]
        g["rows"] += 1
        if r.get("Data Official En"):
            g["found"].add(r.get("Data Official En"))
        if r.get("Severity") == "OK":
            g["green"] += 1
        elif r.get("Severity") == "WARN":
            g["warn"] += 1
        else:
            g["err"] += 1

    core = {
        "Income Statement": ["Revenue", "Gross Profit", "Operating Income", "Net Income", "EPS"],
        "Balance Sheet": ["Total Assets", "Total Liabilities", "Total Equity", "Cash And Cash Equivalents", "Current Assets", "Current Liabilities"],
        "Cash Flow Statement": ["Operating Cash Flow", "Investing Cash Flow", "Financing Cash Flow", "Net Change In Cash", "Capital Expenditure", "Ending Cash"],
        "Ratio Analysis": ["Gross Margin", "Operating Margin", "Net Margin", "ROE", "ROA", "Current Ratio"],
        "Per Share Analysis": ["EPS", "BVPS", "CFPS"],
        "Growth Ratio": ["Sales YoY", "EPS YoY"],
    }

    coverage = []
    for (fn, ticker, cat), g in grouped.items():
        if not cat:
            continue
        expected = core.get(cat, [])
        found = g["found"]
        if expected:
            hit = [x for x in expected if x in found]
            miss = [x for x in expected if x not in found]
            ratio = f"{len(hit)}/{len(expected)}"
            rate = round(100 * len(hit) / max(len(expected), 1), 2)
        else:
            ratio = f"{len(found)}/optional"
            rate = 100.0 if found else 0.0
            miss = []

        sev = "OK" if rate >= 60 else ("WARN" if rate >= 35 else "ERR")
        coverage.append({
            "Status Lights": def_status_lights(sev),
            "Filename": fn,
            "Ticker": ticker,
            "Category": cat,
            "Core Coverage": ratio,
            "Coverage Rate": rate,
            "Core Missing Items": " | ".join(miss),
            "Rows": g["rows"],
            "Green": g["green"],
            "Warn": g["warn"],
            "Err": g["err"],
            "Severity": sev,
        })

    return out, coverage, review


def def_add_sub_checks(validated: list[dict]) -> list[dict]:
    rows = []
    groups = defaultdict(list)
    for r in validated:
        groups[(r.get("Filename", ""), r.get("Ticker", ""), r.get("Year", ""))].append(r)

    def find_val(items, name):
        vals = [x.get("Value Numeric") for x in items if x.get("Data Official En") == name and x.get("Value Numeric") not in ["", None]]
        return float(vals[0]) if vals else None

    checks = [
        ("Balance Sheet", "Total Assets", ["Total Liabilities", "Total Equity"]),
        ("Income Statement", "Gross Profit", ["Revenue"]),
    ]

    for key, items in groups.items():
        fn, ticker, year = key
        total_assets = find_val(items, "Total Assets")
        total_liab = find_val(items, "Total Liabilities")
        total_equity = find_val(items, "Total Equity")
        if total_assets is not None and total_liab is not None and total_equity is not None:
            diff = abs(total_assets - total_liab - total_equity)
            denom = max(abs(total_assets), 1.0)
            ok = diff / denom <= 0.03
            rows.append({
                "Status Lights": def_status_lights("OK" if ok else "WARN"),
                "Filename": fn,
                "Ticker": ticker,
                "Year": year,
                "Check": "Total Assets = Total Liabilities + Total Equity",
                "Left Value": total_assets,
                "Right Value": total_liab + total_equity,
                "Diff": round(diff, 4),
                "Tolerance": "3%",
                "Severity": "OK" if ok else "WARN",
            })

    if not rows:
        rows.append({
            "Status Lights": def_status_lights("WARN"),
            "Filename": "",
            "Ticker": "",
            "Year": "",
            "Check": "Add/Sub",
            "Left Value": "",
            "Right Value": "",
            "Diff": "",
            "Tolerance": "3%",
            "Severity": "WARN",
            "Note": "Insufficient matching rows for add/sub validation.",
        })
    return rows


def def_division_checks(validated: list[dict]) -> list[dict]:
    rows = []
    groups = defaultdict(list)
    for r in validated:
        groups[(r.get("Filename", ""), r.get("Ticker", ""), r.get("Year", ""))].append(r)

    def find_val(items, name):
        vals = [x.get("Value Numeric") for x in items if x.get("Data Official En") == name and x.get("Value Numeric") not in ["", None]]
        return float(vals[0]) if vals else None

    for key, items in groups.items():
        fn, ticker, year = key
        revenue = find_val(items, "Revenue")
        gross_profit = find_val(items, "Gross Profit")
        gross_margin = find_val(items, "Gross Margin")
        if revenue not in [None, 0] and gross_profit is not None and gross_margin is not None:
            calc = gross_profit / revenue * 100
            diff = abs(calc - gross_margin)
            ok = diff <= 5.0
            rows.append({
                "Status Lights": def_status_lights("OK" if ok else "WARN"),
                "Filename": fn,
                "Ticker": ticker,
                "Year": year,
                "Check": "Gross Margin = Gross Profit / Revenue",
                "Calculated": round(calc, 4),
                "Reported": gross_margin,
                "Diff": round(diff, 4),
                "Tolerance": "5 pct points",
                "Severity": "OK" if ok else "WARN",
            })

    if not rows:
        rows.append({
            "Status Lights": def_status_lights("WARN"),
            "Filename": "",
            "Ticker": "",
            "Year": "",
            "Check": "Division",
            "Calculated": "",
            "Reported": "",
            "Diff": "",
            "Tolerance": "5 pct points",
            "Severity": "WARN",
            "Note": "Insufficient matching rows for division validation.",
        })
    return rows


# ==================================================================================================
# def 05_HTML
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
            cls = "left" if any(x in lc for x in ["file", "path", "error", "raw", "item", "step", "note", "candidate"]) else "center"
            cls = "right" if any(x in lc for x in ["value", "score", "rate", "rows", "green", "warn", "err", "diff"]) else cls
            tds.append(f"<td class='{cls}'>{html.escape(v)}</td>")
        trs.append("<tr>" + "".join(tds) + "</tr>")
    return f"<section class='card'><h2>{html.escape(title)}</h2><div class='table-wrap'><table><thead><tr>{th}</tr></thead><tbody>{''.join(trs)}</tbody></table></div></section>"


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
th{position:sticky;top:0;background:#132541;padding:10px;text-align:center;vertical-align:top}
td{padding:8px 10px;border-bottom:1px solid rgba(255,255,255,.08);vertical-align:top;text-align:center;max-width:820px;white-space:normal;word-break:break-word}
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
<head><meta charset="utf-8"><title>VRN Financial Data Confirm Verify v06125</title><style>{css}</style></head>
<body>
<header>
<h1>VRN · Financial Data Extraction Confirmation + Trust Verification v0.6.12.5</h1>
<div class="sub">date candidate noise fix · financial source resolution · SSOT rebind · numeric · period · add/sub · division · coverage</div>
</header>
{card_html}
<main>{body}</main>
<footer>Veritas Intelligence Analytics</footer>
</body>
</html>"""
    Path(path).write_text(doc, encoding="utf-8")


# ==================================================================================================
# def 06_MAIN
# ==================================================================================================
def def_main():
    if len(sys.argv) < 6:
        raise SystemExit("usage: py <ssot_unified> <bridge_module> <run_root> <canonical_dir> <run_dir>")

    ssot_unified = Path(sys.argv[1])
    bridge_path = Path(sys.argv[2])
    run_root = Path(sys.argv[3])
    canonical_dir = Path(sys.argv[4])
    run_dir = Path(sys.argv[5])
    run_dir.mkdir(parents=True, exist_ok=True)

    patch = def_patch_bridge_date_noise(bridge_path)
    ssot_check = def_compile_import(ssot_unified)
    bridge_check = def_compile_import(bridge_path)
    date_smoke = def_smoke_date_noise(bridge_path)

    bridge = def_import_module(bridge_path)

    financial_rows, source_meta = def_load_latest_financial(run_root, canonical_dir)
    validated, coverage, review = def_validate_financial_rows(financial_rows, bridge)
    addsub = def_add_sub_checks(validated)
    division = def_division_checks(validated)

    date_ok = all(r.get("Severity") == "OK" for r in date_smoke)
    bridge_ok = bridge_check.get("import") is True
    financial_exists = len(financial_rows) > 0
    red_rows = sum(1 for r in validated if r.get("Severity") == "ERR")
    green_rows = sum(1 for r in validated if r.get("Severity") == "OK")
    warn_rows = sum(1 for r in validated if r.get("Severity") == "WARN")
    coverage_err = sum(1 for r in coverage if r.get("Severity") == "ERR")

    system_pass = bool(bridge_ok and date_ok and financial_exists)
    operational_pass = bool(system_pass and red_rows == 0)

    overview = [
        {"Status Lights": def_status_lights("OK" if system_pass else "ERR"), "Gate": "SYSTEM_PASS", "Value": "YES" if system_pass else "NO", "Severity": "OK" if system_pass else "ERR"},
        {"Status Lights": def_status_lights("OK" if operational_pass else "WARN"), "Gate": "OPERATIONAL_PASS", "Value": "YES" if operational_pass else "REVIEW", "Severity": "OK" if operational_pass else "WARN"},
        {"Status Lights": def_status_lights("OK" if bridge_ok else "ERR"), "Gate": "BRIDGE_IMPORT", "Value": "YES" if bridge_ok else "NO", "Severity": "OK" if bridge_ok else "ERR"},
        {"Status Lights": def_status_lights("OK" if date_ok else "ERR"), "Gate": "DATE_CANDIDATE_NOISE_FIXED", "Value": "YES" if date_ok else "NO", "Severity": "OK" if date_ok else "ERR"},
        {"Status Lights": def_status_lights("OK" if financial_exists else "ERR"), "Gate": "FINANCIAL_SOURCE_ROWS", "Value": len(financial_rows), "Severity": "OK" if financial_exists else "ERR"},
        {"Status Lights": def_status_lights("OK"), "Gate": "FINANCIAL_SOURCE", "Value": source_meta.get("source_csv", ""), "Severity": "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "GREEN_ROWS", "Value": green_rows, "Severity": "OK"},
        {"Status Lights": def_status_lights("WARN" if warn_rows else "OK"), "Gate": "YELLOW_ROWS", "Value": warn_rows, "Severity": "WARN" if warn_rows else "OK"},
        {"Status Lights": def_status_lights("ERR" if red_rows else "OK"), "Gate": "RED_ROWS", "Value": red_rows, "Severity": "ERR" if red_rows else "OK"},
        {"Status Lights": def_status_lights("ERR" if coverage_err else "OK"), "Gate": "COVERAGE_ERR", "Value": coverage_err, "Severity": "ERR" if coverage_err else "OK"},
        {"Status Lights": def_status_lights("OK"), "Gate": "NO_CANONICAL_MUTATION", "Value": "YES", "Severity": "OK"},
    ]

    patch_rows = [
        {"Status Lights": def_status_lights(patch.get("severity")), "Target": "VIS_VRN_MasterRegistryBridge_v0611.py", **patch},
    ]

    html_path = str(run_dir / "VRN_Financial_Data_Confirm_Verify_v06125.html")
    json_path = str(run_dir / "vrn_financial_data_confirm_verify_v06125.json")
    overview_csv = str(run_dir / "vrn_v06125_overview.csv")
    date_csv = str(run_dir / "vrn_v06125_date_noise_smoke.csv")
    financial_csv = str(run_dir / "vrn_v06125_financial_validated.csv")
    coverage_csv = str(run_dir / "vrn_v06125_coverage.csv")
    review_csv = str(run_dir / "vrn_v06125_review_queue.csv")
    addsub_csv = str(run_dir / "vrn_v06125_addsub_checks.csv")
    division_csv = str(run_dir / "vrn_v06125_division_checks.csv")
    patch_csv = str(run_dir / "vrn_v06125_patch_matrix.csv")

    result = {
        "version": VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "system_pass": "YES" if system_pass else "NO",
        "operational_pass": "YES" if operational_pass else "REVIEW",
        "counts": {
            "System Pass": "YES" if system_pass else "NO",
            "Operational Pass": "YES" if operational_pass else "REVIEW",
            "Financial Rows": len(financial_rows),
            "Validated Rows": len(validated),
            "Green Rows": green_rows,
            "Yellow Rows": warn_rows,
            "Red Rows": red_rows,
            "Coverage Rows": len(coverage),
            "Review Rows": len(review),
        },
        "source": source_meta,
        "outputs": {
            "html": html_path,
            "json": json_path,
            "overview_csv": overview_csv,
            "date_csv": date_csv,
            "financial_csv": financial_csv,
            "coverage_csv": coverage_csv,
            "review_csv": review_csv,
            "addsub_csv": addsub_csv,
            "division_csv": division_csv,
            "patch_csv": patch_csv,
        },
        "policy": {
            "canonical_mutation": "NO",
            "stable_mutation": "NO",
            "preview_only": "YES",
            "no_fake_fill": "YES",
        },
    }

    def_write_csv(overview_csv, overview)
    def_write_csv(date_csv, date_smoke)
    def_write_csv(financial_csv, validated)
    def_write_csv(coverage_csv, coverage)
    def_write_csv(review_csv, review)
    def_write_csv(addsub_csv, addsub)
    def_write_csv(division_csv, division)
    def_write_csv(patch_csv, patch_rows)
    def_write_json(json_path, result)
    def_write_html(html_path, result, [
        ("01 Overview", overview),
        ("02 Date Candidate Noise Fix", date_smoke),
        ("03 Financial Data Validated", validated[:800]),
        ("04 Coverage Matrix", coverage),
        ("05 Review Queue", review),
        ("06 Add/Sub Checks", addsub),
        ("07 Division Checks", division),
        ("08 Patch Matrix", patch_rows),
    ])

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        def_main()
    except Exception:
        print(traceback.format_exc())
        raise