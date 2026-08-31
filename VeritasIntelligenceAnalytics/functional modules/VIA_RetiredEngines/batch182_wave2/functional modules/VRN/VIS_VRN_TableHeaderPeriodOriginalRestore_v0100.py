# -*- coding: utf-8 -*-
"""
VIS_VRN_TableHeaderPeriodOriginalRestore_v0100

Purpose:
- Restore table shape as close to original as possible.
- Grab possible header rows upward from table/candidate line.
- Handle merged-cell-like empty header cells by forward fill.
- Normalize period tokens into canonical forms:
  Annual: YYYY
  Quarter: 1Q25 / 2Q25 / 3Q25 / 4Q25
  Date: YYYY-MM-DD
- Preserve raw header and raw period separately.
- Output DB-ready long rows only after cross validation.

Safe flags:
- No DB write.
- No canonical write.
- No parser core rewrite.
- No delete.
"""

from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import re
from datetime import datetime
from typing import Any, Dict, List, Tuple


MONTH_MAP = {
    "jan": "01", "january": "01",
    "feb": "02", "february": "02",
    "mar": "03", "march": "03",
    "apr": "04", "april": "04",
    "may": "05",
    "jun": "06", "june": "06",
    "jul": "07", "july": "07",
    "aug": "08", "august": "08",
    "sep": "09", "sept": "09", "september": "09",
    "oct": "10", "october": "10",
    "nov": "11", "november": "11",
    "dec": "12", "december": "12",
}

ACCOUNT_KEYWORDS = [
    "revenue", "revenues", "sales", "net revenue", "revenue, net",
    "gross profit", "gross margin", "operating profit", "operating income",
    "ebitda", "ebit", "pretax", "pre-tax", "net profit", "net income",
    "eps", "營收", "收入", "營業收入", "毛利", "毛利率", "營業利益",
    "營益", "稅前", "稅後", "淨利", "每股", "每股盈餘"
]

NOISE_KEYWORDS = [
    "price target", "shr price", "52-week", "mkt cap", "avg daily",
    "rating", "disclosure", "analyst", "sector", "recommendation",
    "company name", "ticker", "market cap", "sh out"
]


def def_clean_space_v0100(x: Any) -> str:
    return re.sub(r"\s+", " ", str(x or "").strip())


def def_num_tokens_v0100(x: Any) -> List[str]:
    s = def_clean_space_v0100(x)
    return re.findall(r"\(?-?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?%?|-?\d+(?:\.\d+)?%?", s)


def def_is_noise_line_v0100(x: Any) -> bool:
    s = def_clean_space_v0100(x).lower()
    return any(k in s for k in NOISE_KEYWORDS)


def def_has_account_signal_v0100(x: Any) -> bool:
    s = def_clean_space_v0100(x).lower()
    return any(k.lower() in s for k in ACCOUNT_KEYWORDS)


def def_period_tokens_v0100(x: Any) -> List[Dict[str, str]]:
    text = def_clean_space_v0100(x)
    out: List[Dict[str, str]] = []
    claimed_spans: List[Tuple[int, int]] = []

    def _overlaps(a, b):
        for (s0, e0) in claimed_spans:
            if not (b <= s0 or a >= e0):
                return True
        return False

    # YYYY-MM-DD / YYYY/MM/DD
    for m in re.finditer(r"\b(20\d{2})[-/\.](\d{1,2})[-/\.](\d{1,2})\b", text):
        y, mo, d = m.group(1), int(m.group(2)), int(m.group(3))
        out.append({
            "raw": m.group(0),
            "normalized": f"{y}-{mo:02d}-{d:02d}",
            "type": "DATE",
            "forecast_flag": "",
        })
        claimed_spans.append((m.start(), m.end()))

    # Dec 2, 2025
    for m in re.finditer(r"\b([A-Za-z]{3,9})\.?\s+(\d{1,2}),\s*(20\d{2})\b", text):
        mo_raw = m.group(1).lower().strip(".")
        if mo_raw in MONTH_MAP:
            out.append({
                "raw": m.group(0),
                "normalized": f"{m.group(3)}-{MONTH_MAP[mo_raw]}-{int(m.group(2)):02d}",
                "type": "DATE",
                "forecast_flag": "",
            })
            claimed_spans.append((m.start(), m.end()))

    # 3Q25 / Q3 25 / 3Q2025 / FY3Q26
    quarter_patterns = [
        r"\b(?:FY)?([1-4])Q\s*([0-9]{2}|20[0-9]{2})(?:E|F|A)?\b",
        r"\b(?:FY)?Q([1-4])\s*([0-9]{2}|20[0-9]{2})(?:E|F|A)?\b",
    ]
    for pat in quarter_patterns:
        for m in re.finditer(pat, text, flags=re.I):
            if _overlaps(m.start(), m.end()):
                continue
            q = m.group(1)
            yy = m.group(2)
            yy2 = yy[-2:]
            suffix = ""
            raw = m.group(0)
            if re.search(r"[EF]$", raw, flags=re.I):
                suffix = raw[-1].upper()
            out.append({
                "raw": raw,
                "normalized": f"{q}Q{yy2}",
                "type": "QUARTER",
                "forecast_flag": suffix,
            })
            claimed_spans.append((m.start(), m.end()))

    # 2025 / 2025E / FY2025 / FY25 / 25E
    annual_patterns = [
        r"\b(?:FY|YE)?\s*(20[0-9]{2})(?:E|F|A)?\b",
        r"\bFY\s*([0-9]{2})(?:E|F|A)?\b",
    ]
    for pat in annual_patterns:
        for m in re.finditer(pat, text, flags=re.I):
            # FIX: do not re-claim a year already consumed by a DATE or QUARTER span,
            # otherwise a single "2025-03-31" yields both a DATE and a YEAR column,
            # over-counting period columns vs values.
            if _overlaps(m.start(), m.end()):
                continue
            raw = m.group(0)
            val = m.group(1)
            year = val if len(val) == 4 else "20" + val
            suffix = ""
            if re.search(r"[EF]$", raw, flags=re.I):
                suffix = raw[-1].upper()
            out.append({
                "raw": raw,
                "normalized": year,
                "type": "YEAR",
                "forecast_flag": suffix,
            })
            claimed_spans.append((m.start(), m.end()))

    # de-duplicate preserving order
    seen = set()
    dedup: List[Dict[str, str]] = []
    for r in out:
        key = (r["raw"], r["normalized"], r["type"])
        if key not in seen:
            dedup.append(r)
            seen.add(key)

    return dedup


def def_forward_fill_cells_v0100(cells: List[str]) -> List[str]:
    out = []
    last = ""
    for c in cells:
        cc = def_clean_space_v0100(c)
        if cc:
            last = cc
            out.append(cc)
        else:
            out.append(last)
    return out


def def_split_line_to_cells_v0100(line: str) -> List[str]:
    s = def_clean_space_v0100(line)
    if "|" in s:
        return [def_clean_space_v0100(x) for x in s.split("|")]
    if "\t" in s:
        return [def_clean_space_v0100(x) for x in s.split("\t")]
    # split by 2+ spaces if present
    parts = re.split(r"\s{2,}", s)
    if len(parts) > 1:
        return [def_clean_space_v0100(x) for x in parts if def_clean_space_v0100(x)]
    return [s]


def def_pick_header_lines_v0100(lines: List[str], row_index: int, up_lines: int = 8) -> List[Dict[str, Any]]:
    start = max(0, row_index - up_lines)
    candidates = []

    for i in range(start, row_index):
        raw = lines[i]
        s = def_clean_space_v0100(raw)
        if not s:
            continue

        periods = def_period_tokens_v0100(s)
        nums = def_num_tokens_v0100(s)
        score = 0

        if periods:
            score += 50
        if re.search(r"\b(FY|YE|Q[1-4]|[1-4]Q|20\d{2}|E|F)\b", s, flags=re.I):
            score += 20
        if len(nums) >= 2 and len(periods) == 0:
            score -= 15
        if def_is_noise_line_v0100(s):
            score -= 30
        if len(s) <= 120:
            score += 5

        if score > 0:
            candidates.append({
                "LineIndex": i,
                "RawHeaderLine": s,
                "HeaderScore": score,
                "PeriodTokens": periods,
                "Cells": def_forward_fill_cells_v0100(def_split_line_to_cells_v0100(s)),
            })

    return sorted(candidates, key=lambda x: x["HeaderScore"], reverse=True)


def def_restore_from_text_line_v0100(source_file: str, line_no: int, raw_line: str, context_lines: List[str], up_lines: int = 8) -> Dict[str, Any]:
    line_index = max(0, line_no - 1)
    header_candidates = def_pick_header_lines_v0100(context_lines, line_index, up_lines)

    line = def_clean_space_v0100(raw_line)
    numbers = def_num_tokens_v0100(line)
    periods_here = def_period_tokens_v0100(line)

    account = line
    if numbers:
        account = line.split(numbers[0])[0].strip(" -:：,，")

    if not account:
        account = "UNKNOWN_ACCOUNT"

    best_header = header_candidates[0] if header_candidates else None
    header_periods = []
    if best_header:
        for p in best_header.get("PeriodTokens", []):
            header_periods.append(p)

    all_periods = header_periods + periods_here

    # Keep only normalized period values for columns.
    period_norm = []
    seen = set()
    for p in all_periods:
        key = p["normalized"]
        if key not in seen:
            period_norm.append(p)
            seen.add(key)

    if len(period_norm) < len(numbers):
        # create generic sequence when header not enough; still preserve raw.
        for i in range(len(period_norm), len(numbers)):
            period_norm.append({
                "raw": "",
                "normalized": f"COL_{i+1}",
                "type": "UNKNOWN",
                "forecast_flag": "",
            })

    long_rows = []
    for i, val in enumerate(numbers):
        p = period_norm[i] if i < len(period_norm) else {"raw": "", "normalized": f"COL_{i+1}", "type": "UNKNOWN", "forecast_flag": ""}
        long_rows.append({
            "SourceFile": source_file,
            "LineNo": line_no,
            "AccountRaw": account,
            "HeaderRaw": best_header["RawHeaderLine"] if best_header else "",
            "HeaderScore": best_header["HeaderScore"] if best_header else 0,
            "PeriodRaw": p["raw"],
            "PeriodNormalized": p["normalized"],
            "PeriodType": p["type"],
            "ForecastFlag": p["forecast_flag"],
            "ValueRaw": val,
            "RestoreMode": "TEXT_RECORD_FALLBACK_HEADER_UPWARD",
            "DbWrite": False,
            "CanonicalWrite": False,
            "ParserCoreRewrite": False,
            "Delete": False,
        })

    validation = def_cross_validate_restored_v0100(line, header_candidates, long_rows)

    return {
        "HeaderCandidates": header_candidates,
        "LongRows": long_rows,
        "Validation": validation,
    }


def def_restore_from_pdfplumber_table_row_v0100(source_file: str, page: Any, table_index: Any, row_index: Any, raw_cells: str) -> Dict[str, Any]:
    cells = [def_clean_space_v0100(x) for x in str(raw_cells or "").split("|")]
    cells = def_forward_fill_cells_v0100(cells)

    header_cells = []
    value_cells = []
    account = cells[0] if cells else "UNKNOWN_ACCOUNT"

    for c in cells[1:]:
        if def_period_tokens_v0100(c):
            header_cells.append(c)
        elif def_num_tokens_v0100(c):
            value_cells.append(c)
        else:
            header_cells.append(c)

    periods = []
    for h in header_cells:
        periods.extend(def_period_tokens_v0100(h))

    nums = []
    for v in value_cells:
        nums.extend(def_num_tokens_v0100(v))

    if not nums:
        nums = def_num_tokens_v0100(raw_cells)

    long_rows = []
    for i, val in enumerate(nums):
        p = periods[i] if i < len(periods) else {"raw": "", "normalized": f"COL_{i+1}", "type": "UNKNOWN", "forecast_flag": ""}
        long_rows.append({
            "SourceFile": source_file,
            "Page": page,
            "TableIndex": table_index,
            "RowIndex": row_index,
            "AccountRaw": account,
            "HeaderRaw": " | ".join(header_cells),
            "HeaderScore": 80 if periods else 40,
            "PeriodRaw": p["raw"],
            "PeriodNormalized": p["normalized"],
            "PeriodType": p["type"],
            "ForecastFlag": p["forecast_flag"],
            "ValueRaw": val,
            "RestoreMode": "PDFPLUMBER_TABLE_ORIGINAL_SHAPE",
            "DbWrite": False,
            "CanonicalWrite": False,
            "ParserCoreRewrite": False,
            "Delete": False,
        })

    validation = def_cross_validate_restored_v0100(raw_cells, [], long_rows)

    return {
        "HeaderCandidates": [],
        "LongRows": long_rows,
        "Validation": validation,
    }


def def_cross_validate_restored_v0100(raw_line: str, header_candidates: List[Dict[str, Any]], long_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    risk = "GREEN"
    status = "PASS"
    score = 100

    if not long_rows:
        return {
            "Risk": "YELLOW",
            "Status": "NO_RESTORED_ROWS",
            "Score": 60,
            "Reason": "No values restored.",
        }

    header_known = sum(1 for r in long_rows if not str(r.get("PeriodNormalized", "")).startswith("COL_"))
    if header_known == 0:
        risk = "YELLOW"
        status = "HEADER_PERIOD_UNKNOWN"
        score -= 25

    if def_is_noise_line_v0100(raw_line):
        risk = "YELLOW"
        status = "NOISE_OR_MARKET_DATA_REVIEW"
        score -= 25

    if not def_has_account_signal_v0100(raw_line):
        risk = "YELLOW"
        status = "ACCOUNT_SIGNAL_WEAK_REVIEW"
        score -= 15

    if score < 70:
        risk = "YELLOW"

    return {
        "Risk": risk,
        "Status": status,
        "Score": max(0, score),
        "Reason": "",
    }


def def_self_check_v0100() -> Dict[str, Any]:
    sample_lines = [
        "Company Snapshot",
        "FY2024 2025E 2026F 3Q25",
        "Revenue, net (NT$ mn) 30,660 33,640 37,277 41,327",
    ]
    out = def_restore_from_text_line_v0100(
        "sample.pdf",
        3,
        sample_lines[2],
        sample_lines,
        2,
    )
    periods = [r["PeriodNormalized"] for r in out["LongRows"]]
    return {
        "hard_pass": "2024" in periods and "2025" in periods and "2026" in periods and len(out["LongRows"]) == 4,
        "periods": periods,
        "rows": len(out["LongRows"]),
        "safe": {
            "DbWrite": False,
            "CanonicalWrite": False,
            "ParserCoreRewrite": False,
            "Delete": False,
        },
    }


if __name__ == "__main__":
    print(def_self_check_v0100())
