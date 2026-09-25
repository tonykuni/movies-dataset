# -*- coding: utf-8 -*-
"""
VIS_VRN_TableGeometryReconstructor_v0101

Enhanced supportive-only table reconstruction module.

Fixes:
1. Multi-account rows with embedded values in AccountRaw.
2. Morning summary / industry / no ticker fragments are routed to quarantine, not production fail.
3. Value-only / header-only rows are treated as route fragments.
4. Unknown account is review, not parser failure, when values are reconstructable.

No DB write.
No canonical write.
No parser core rewrite.
No delete.
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
from typing import Any, Dict, List, Tuple


CANONICAL_ACCOUNT_ALIAS = {
    "營收": "Revenue",
    "營業收入": "Revenue",
    "營業收入淨額": "Revenue",
    "Revenues": "Revenue",
    "Revenue": "Revenue",
    "Revenues (NT$m)": "Revenue",
    "Revenues (US$ in mn)": "Revenue_USD",
    "Revenues (NT$ in bn)": "Revenue_TWD_BN",

    "營業成本": "Cost Of Revenue",
    "營業毛利": "Gross Profit",
    "營業毛利淨額": "Gross Profit",
    "毛利": "Gross Profit",
    "GP": "Gross Profit",
    "Gross profit": "Gross Profit",
    "Gross Profit": "Gross Profit",

    "營業利益": "Operating Income",
    "營利": "Operating Income",
    "OP": "Operating Income",
    "Operating profit": "Operating Income",
    "Operating Profit": "Operating Income",
    "Operating Income": "Operating Income",

    "Non-op profit": "Non Operating Income",
    "Pre-tax profit": "Pretax Income",
    "稅前獲利": "Pretax Income",
    "稅前淨利": "Pretax Income",
    "PBT": "Pretax Income",

    "稅後純益": "Net Income",
    "稅後淨利": "Net Income",
    "淨利": "Net Income",
    "Net profit": "Net Income",
    "Net income": "Net Income",
    "Net Income": "Net Income",

    "每股盈餘": "EPS",
    "每股盈餘 (元)": "EPS",
    "EPS": "EPS",
    "EPS (NT$)": "EPS",

    "毛利率": "Gross Margin",
    "毛利率 (%)": "Gross Margin",
    "Gross margin": "Gross Margin",
    "營利率": "Operating Margin",
    "營利率 (%)": "Operating Margin",
    "OP margin": "Operating Margin",
    "營業利益率": "Operating Margin",
    "淨利率": "Net Margin",
    "淨利率 (%)": "Net Margin",

    "Tax": "Tax",
    "- Tax rate": "Tax Rate",

    "ROE (%)": "ROE",
    "PER (X)": "PER",
    "PBR (X)": "PBR",

    "流動資產": "Current Assets",
    "流動負債": "Current Liabilities",
    "現金及約當現金": "Cash And Equivalents",
    "總資產": "Total Assets",
    "總負債": "Total Liabilities",
    "股東權益": "Shareholders Equity",
}

ACCOUNT_PATTERNS = [
    "Revenues \\(US\\$ in mn\\)",
    "Revenues \\(NT\\$ in bn\\)",
    "Revenues \\(NT\\$m\\)",
    "Revenue",
    "Revenues",
    "Gross profit",
    "Gross Profit",
    "Gross margin",
    "Operating profit",
    "Operating Profit",
    "OP margin",
    "Non-op profit",
    "Pre-tax profit",
    "Net profit",
    "Net income",
    "Net Income",
    "EPS \\(NT\\$\\)",
    "Tax",
    "- Tax rate",
    "GP",
    "OP",

    "營業收入淨額",
    "營業收入",
    "營業成本",
    "營業毛利淨額",
    "營業毛利",
    "營業利益",
    "稅前獲利",
    "稅前淨利",
    "稅後純益",
    "稅後淨利",
    "每股盈餘 \\(元\\)",
    "每股盈餘",
    "每股現金 股利\\(元\\)",
    "每股現 金 股利\\(元\\)",
    "毛利率 \\(\\%\\)",
    "營利率 \\(\\%\\)",
    "淨利率 \\(\\%\\)",
    "ROE \\(\\%\\)",
    "PER \\(X\\)",
    "PBR \\(X\\)",
    "毛利率",
    "營利率",
    "淨利率",
    "營收",
    "毛利",
    "淨利",

    "流動資產",
    "流動負債",
    "現金及約當現金",
    "總資產",
    "總負債",
    "股東權益",
]

PERIOD_ONLY_RE = re.compile(r"^(?:20\d{2}|20\d{2}\(F\)|\d{2}Q[1-4]|Q[1-4]|FY\d*|本 次|前 次|會計 年度|公司名稱)$", re.I)

NUM_TOKEN_RE = re.compile(
    r"""
    (?:
        \(?-?\d{1,3}(?:,\d{3})+(?:\.\d+)?\)?
        |
        \(?-?\d+(?:\.\d+)?\)?
        |
        -{1}
    )
    (?:\s*(?:%|ppts|ppt|x|X))?
    """,
    re.VERBOSE,
)


def def_normalize_space_v0101(x: Any) -> str:
    return re.sub(r"\s+", " ", str(x or "").strip())


def def_is_route_only_source_v0101(source_file: Any, ticker: Any) -> bool:
    src = str(source_file or "")
    t = str(ticker or "").strip()

    if t:
        return False

    patterns = [
        "晨會", "晨会", "Morning", "Hardware Insights", "Industry",
        "產業", "钢铁", "鋼鐵", "Asia Hardware", "UBS-Asia",
        "公司訪談摘要", "訪談摘要"
    ]

    return any(p.lower() in src.lower() for p in patterns)


def def_is_period_or_header_fragment_v0101(account_raw: Any, value_raw: Any) -> bool:
    a = def_normalize_space_v0101(account_raw)
    v = def_normalize_space_v0101(value_raw)

    if PERIOD_ONLY_RE.match(a):
        return True

    if a in {"(NT$m)", "- QoQ / YoY", "本 次", "前 次", "會計 年度", "公司名稱"}:
        return True

    if not NUM_TOKEN_RE.search(a) and v in {"UBSe", "Actual", "報告種類", "逢低買進", "買進", "前 次", "區間操作"}:
        return True

    return False


def def_find_value_tokens_v0101(x: Any) -> List[str]:
    text = def_normalize_space_v0101(x)
    return [m.group(0).strip() for m in NUM_TOKEN_RE.finditer(text)]


def def_clean_number_v0101(x: str) -> str:
    s = str(x or "").strip()
    if s in {"", "-", "—"}:
        return ""
    s = s.replace(",", "")
    s = s.replace(" ", "")
    negative = False
    if s.startswith("(") and ")" in s and "%" not in s and "ppts" not in s:
        negative = True
    s = s.replace("(", "").replace(")", "")
    unit = ""
    for u in ["ppts", "ppt", "%", "x", "X"]:
        if s.endswith(u):
            unit = u
            s = s[: -len(u)]
            break
    if negative and not s.startswith("-"):
        s = "-" + s
    return s + unit


def def_value_type_v0101(x: str) -> str:
    s = str(x or "")
    if "ppts" in s or "ppt" in s:
        return "PPTS"
    if "%" in s:
        return "PERCENT"
    if s in {"", "-"}:
        return "EMPTY"
    return "NUMBER"


def def_account_hits_v0101(text: Any) -> List[Tuple[int, int, str]]:
    src = def_normalize_space_v0101(text)
    hits: List[Tuple[int, int, str]] = []

    for pat in ACCOUNT_PATTERNS:
        for m in re.finditer(pat, src, flags=re.IGNORECASE):
            hits.append((m.start(), m.end(), m.group(0).strip()))

    hits = sorted(hits, key=lambda x: (x[0], -(x[1] - x[0])))

    dedup: List[Tuple[int, int, str]] = []
    occupied: List[Tuple[int, int]] = []

    for start, end, label in hits:
        overlap = False
        for os, oe in occupied:
            if not (end <= os or start >= oe):
                overlap = True
                break
        if not overlap:
            dedup.append((start, end, label))
            occupied.append((start, end))

    return dedup


def def_split_accounts_v0101(account_raw: Any) -> List[str]:
    text = def_normalize_space_v0101(account_raw)
    if not text:
        return []

    hits = def_account_hits_v0101(text)
    if hits:
        return [h[2] for h in hits]

    # fallback: label before first numeric
    m = NUM_TOKEN_RE.search(text)
    if m:
        label = text[: m.start()].strip()
        return [label] if label else []

    return [text]


def def_values_from_account_and_value_v0101(account_raw: Any, value_raw: Any) -> List[str]:
    # v0101 important fix:
    # values embedded in AccountRaw must not be dropped.
    a_vals = def_find_value_tokens_v0101(account_raw)
    v_vals = def_find_value_tokens_v0101(value_raw)

    # If AccountRaw is a normal account label with no embedded values, use ValueRaw only.
    if not a_vals:
        return v_vals

    # If AccountRaw contains account labels plus first values, use both.
    # This fixes rows like "營收 353,483 3 毛利 16,765 ..."
    if v_vals:
        return a_vals + v_vals

    return a_vals


def def_canonical_account_v0101(account: Any) -> str:
    a = def_normalize_space_v0101(account)
    if a in CANONICAL_ACCOUNT_ALIAS:
        return CANONICAL_ACCOUNT_ALIAS[a]

    a2 = a.replace("(%)", "").strip()
    if a2 in CANONICAL_ACCOUNT_ALIAS:
        return CANONICAL_ACCOUNT_ALIAS[a2]

    for k, v in CANONICAL_ACCOUNT_ALIAS.items():
        if k.lower() == a.lower():
            return v

    return "UNKNOWN_ACCOUNT"


def def_group_values_v0101(values: List[str], account_count: int) -> Tuple[List[List[str]], str, float]:
    if account_count <= 0:
        return [], "NO_ACCOUNT", 0.0

    if not values:
        return [[] for _ in range(account_count)], "NO_VALUES", 0.0

    n = len(values)

    if account_count == 1:
        return [values], "ONE_ACCOUNT_ALL_VALUES", 0.92

    if n % account_count == 0:
        width = n // account_count
        return [values[i * width : (i + 1) * width] for i in range(account_count)], "EVEN_SPLIT", 0.92

    width = max(1, n // account_count)
    groups: List[List[str]] = []
    pos = 0

    for i in range(account_count):
        if i == account_count - 1:
            groups.append(values[pos:])
        else:
            groups.append(values[pos : pos + width])
            pos += width

    return groups, "UNEVEN_SPLIT_REVIEW", 0.70


def def_reconstruct_financial_issue_row_v0101(row: Dict[str, Any]) -> Dict[str, Any]:
    source_file = row.get("SourceFile", "")
    ticker = row.get("Ticker", "")
    account_raw = row.get("AccountRaw") or row.get("Account Raw") or ""
    value_raw = row.get("ValueRaw") or row.get("Value Raw") or ""
    issue_type = row.get("IssueType") or row.get("Issue Type") or ""

    route_only = def_is_route_only_source_v0101(source_file, ticker)
    fragment = def_is_period_or_header_fragment_v0101(account_raw, value_raw)

    if fragment:
        return {
            "risk": "ROUTE",
            "account_count": 0,
            "value_count": len(def_find_value_tokens_v0101(value_raw)),
            "reconstructed_rows": [],
            "quarantine_rows": [{
                "SourceFile": source_file,
                "SourcePage": row.get("SourcePage", ""),
                "Ticker": ticker,
                "IssueType": issue_type,
                "AccountRaw": account_raw,
                "ValueRaw": value_raw,
                "QuarantineReason": "HEADER_OR_VALUE_FRAGMENT",
                "RouteOnly": route_only,
                "DbWrite": False,
                "CanonicalWrite": False,
                "ParserCoreRewrite": False,
            }],
            "split_mode": "ROUTE_FRAGMENT",
            "confidence": 0.95,
        }

    accounts = def_split_accounts_v0101(account_raw)
    values = def_values_from_account_and_value_v0101(account_raw, value_raw)

    groups, split_mode, split_conf = def_group_values_v0101(values, len(accounts))

    rows: List[Dict[str, Any]] = []

    for ai, account in enumerate(accounts):
        vals = groups[ai] if ai < len(groups) else []
        canonical = def_canonical_account_v0101(account)

        for vi, val in enumerate(vals, start=1):
            rows.append({
                "SourceFile": source_file,
                "SourcePage": row.get("SourcePage", ""),
                "Ticker": ticker,
                "FiscalYear": row.get("FiscalYear", ""),
                "PeriodNormalized": row.get("PeriodNormalized", ""),
                "AccountRawOriginal": account_raw,
                "ValueRawOriginal": value_raw,
                "AccountSplitIndex": ai + 1,
                "AccountRawSplit": account,
                "AccountCanonical": canonical,
                "ValueSeq": vi,
                "ValueRawSplit": val,
                "ValueClean": def_clean_number_v0101(val),
                "ValueType": def_value_type_v0101(val),
                "IssueType": issue_type,
                "ReconstructionMode": split_mode,
                "ReconstructionConfidence": split_conf,
                "RouteOnly": route_only,
                "ValidationStatus": "ROUTE_REVIEW" if route_only else ("RECONSTRUCTED_REVIEW" if split_conf < 0.8 or canonical == "UNKNOWN_ACCOUNT" else "RECONSTRUCTED_READY"),
                "DbWrite": False,
                "CanonicalWrite": False,
                "ParserCoreRewrite": False,
            })

    quarantine: List[Dict[str, Any]] = []

    if not rows:
        quarantine.append({
            "SourceFile": source_file,
            "SourcePage": row.get("SourcePage", ""),
            "Ticker": ticker,
            "IssueType": issue_type,
            "AccountRaw": account_raw,
            "ValueRaw": value_raw,
            "QuarantineReason": "NO_RECONSTRUCTED_ROWS",
            "RouteOnly": route_only,
            "DbWrite": False,
            "CanonicalWrite": False,
            "ParserCoreRewrite": False,
        })

    risk = "GREEN"

    if route_only:
        risk = "ROUTE"
    elif not rows:
        risk = "YELLOW"
    elif split_conf < 0.8 or any(r["AccountCanonical"] == "UNKNOWN_ACCOUNT" for r in rows):
        risk = "YELLOW"

    return {
        "risk": risk,
        "account_count": len(accounts),
        "value_count": len(values),
        "reconstructed_rows": rows,
        "quarantine_rows": quarantine,
        "split_mode": split_mode,
        "confidence": split_conf,
    }


def def_markdown_table_v0101(rows: List[Dict[str, Any]], max_cols: int = 12) -> str:
    if not rows:
        return ""

    source = rows[0].get("SourceFile", "")
    page = rows[0].get("SourcePage", "")
    title = f"### {source} · Page {page}".strip()

    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for r in rows:
        key = r.get("AccountRawSplit", "")
        grouped.setdefault(key, []).append(r)

    max_len = max(len(v) for v in grouped.values())
    max_len = min(max_len, max_cols)

    header = ["Account", "Canonical"] + [f"V{i}" for i in range(1, max_len + 1)]
    lines = [title, "", "| " + " | ".join(header) + " |", "| " + " | ".join(["---"] * len(header)) + " |"]

    for account, vals in grouped.items():
        canonical = vals[0].get("AccountCanonical", "")
        cells = [account, canonical]
        for i in range(max_len):
            cells.append(vals[i].get("ValueClean", "") if i < len(vals) else "")
        lines.append("| " + " | ".join(str(x) for x in cells) + " |")

    return "\n".join(lines)


def def_self_check_v0101() -> Dict[str, Any]:
    sample = {
        "SourceFile": "sample.pdf",
        "SourcePage": "2",
        "Ticker": "1476",
        "AccountRaw": "營收 353,483 3 毛利 16,765 營業利益 3,543 稅前獲利 3,276 稅後淨利 331 每股盈餘 (元) 0.02",
        "ValueRaw": "61,614 (2.2) 11.5 334,244 5.8 26,382",
        "FiscalYear": "2026",
        "PeriodNormalized": "FY",
        "IssueType": "MERGED_MULTI_ACCOUNT_ROW | MALFORMED_OR_MERGED_VALUE",
    }

    out = def_reconstruct_financial_issue_row_v0101(sample)

    return {
        "hard_pass": out["risk"] in {"GREEN", "YELLOW", "ROUTE"} and out["account_count"] >= 6 and len(out["reconstructed_rows"]) >= 6,
        "risk": out["risk"],
        "account_count": out["account_count"],
        "rows": len(out["reconstructed_rows"]),
        "mode": out["split_mode"],
        "db_write": False,
        "canonical_write": False,
        "parser_core_rewrite": False,
        "delete": False,
    }


if __name__ == "__main__":
    print(def_self_check_v0101())
