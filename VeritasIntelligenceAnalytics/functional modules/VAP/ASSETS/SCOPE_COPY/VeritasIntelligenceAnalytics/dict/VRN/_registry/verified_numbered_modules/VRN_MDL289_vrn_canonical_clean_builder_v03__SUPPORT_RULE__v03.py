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

import csv
import html
import json
import re
import sys
from pathlib import Path
from datetime import datetime


VRN_ROOT = Path(sys.argv[1])
SOURCE_BASIC = Path(sys.argv[2]) if sys.argv[2] else Path("")
SOURCE_FINANCIAL = Path(sys.argv[3]) if sys.argv[3] else Path("")
CANONICAL_DIR = Path(sys.argv[4])
OUT_JSON = Path(sys.argv[5])


YFINANCE_DISPLAY_COLUMNS = [
    "YFinance Target Mean Price",
    "YFinance Target Median Price",
    "YFinance Target High Price",
    "YFinance Target Low Price",
    "YFinance Recommendation Key",
    "YFinance Recommendation Mean",
    "YFinance Number Of Analyst Opinions",
    "YFinance Consensus Source",
    "YFinance Consensus Trust",
    "YFinance Consensus Fetched At",
]


FINAL_GATE_COLUMNS = [
    "Final Gate Status",
    "Final Gate DB Ready",
    "Final Gate Company Report",
    "Market",
    "Final Gate Company Reason",
    "Filename",
    "Source Text",
    "Method",
    "Confidence",
    "DB Ready",
    "PDF Pages",
    "Text Length",
    "Blocks Length",
    "Table Count",
    "Report Date Filename",
    "Report Date First Page",
    "Broker Raw Matched",
    "Split Required",
    "Final Gate Positive Signal",
] + YFINANCE_DISPLAY_COLUMNS


FINANCIAL_CATEGORY_ORDER = {
    "損益表": 1,
    "INCOME_STATEMENT": 1,
    "Income Statement": 1,
    "資產負債表": 2,
    "BALANCE_SHEET": 2,
    "Balance Sheet": 2,
    "現金流量表": 3,
    "CASH_FLOW": 3,
    "Cash Flow": 3,
    "比率分析": 4,
    "RATIO_ANALYSIS": 4,
    "Ratio Analysis": 4,
    "每股分析": 5,
    "PER_SHARE_ANALYSIS": 5,
    "Per Share Analysis": 5,
}


def is_summary_column(name: str) -> bool:
    n = str(name or "")
    return bool(
        re.search(r"^Summary_", n)
        or re.search(r"^(Summary|summary|SUMMARY)$", n)
        or re.search(r"摘要|重點|結論", n)
        or re.search(r"zh_points|en_points|paragraph_|quality_grade|warning|warnings|summary_mode|summarizer_version|financial_snapshot", n)
    )


def read_csv(path: Path) -> list[dict]:
    if not path or not path.exists():
        return []
    for enc in ["utf-8-sig", "utf-8", "cp950", "big5"]:
        try:
            with path.open("r", encoding=enc, newline="") as f:
                return list(csv.DictReader(f))
        except Exception:
            pass
    return []


def write_csv(path: Path, rows: list[dict], columns: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if columns is None:
        cols = []
        for r in rows:
            for k in r.keys():
                if k not in cols:
                    cols.append(k)
        columns = cols
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in columns})


def get_first(row: dict, names: list[str]) -> str:
    for n in names:
        if n in row and row.get(n) not in [None, ""]:
            return str(row.get(n))
    return ""


def normalize_basic_row(row: dict) -> dict:
    out = dict(row)

    # Ensure canonical YFinance display fields exist, but never overwrite BASICINFO report opinion fields.
    source_map = {
        "YFinance Target Mean Price": ["YFinance Target Mean Price", "yfinance_target_mean_price"],
        "YFinance Target Median Price": ["YFinance Target Median Price", "yfinance_target_median_price"],
        "YFinance Target High Price": ["YFinance Target High Price", "yfinance_target_high_price"],
        "YFinance Target Low Price": ["YFinance Target Low Price", "yfinance_target_low_price"],
        "YFinance Recommendation Key": ["YFinance Recommendation Key", "yfinance_recommendation_key"],
        "YFinance Recommendation Mean": ["YFinance Recommendation Mean", "yfinance_recommendation_mean"],
        "YFinance Number Of Analyst Opinions": ["YFinance Number Of Analyst Opinions", "yfinance_number_of_analyst_opinions"],
        "YFinance Consensus Source": ["YFinance Consensus Source", "yfinance_consensus_source"],
        "YFinance Consensus Trust": ["YFinance Consensus Trust", "yfinance_consensus_trust"],
        "YFinance Consensus Fetched At": ["YFinance Consensus Fetched At", "yfinance_consensus_fetched_at"],
    }

    for dst, aliases in source_map.items():
        out[dst] = get_first(row, aliases)

    if not out.get("YFinance Consensus Trust"):
        out["YFinance Consensus Trust"] = "REFERENCE_ONLY"

    return out


def clean_rows_drop_summary(rows: list[dict]) -> tuple[list[dict], list[str]]:
    if not rows:
        return [], []
    cols = []
    for r in rows:
        for k in r.keys():
            if k not in cols:
                cols.append(k)
    summary_cols = [c for c in cols if is_summary_column(c)]
    keep_cols = [c for c in cols if c not in summary_cols]
    clean = []
    for r in rows:
        clean.append({c: r.get(c, "") for c in keep_cols})
    return clean, summary_cols


def guess_fin_category(row: dict) -> str:
    raw = get_first(row, ["Category", "category", "Statement Group", "statement_group", "Statement", "statement"])
    data = get_first(row, ["Data", "data", "Account", "account", "Item", "item"])

    if raw in FINANCIAL_CATEGORY_ORDER:
        return raw

    text = f"{raw} {data}".lower()

    if re.search(r"revenue|sales|gross|operating income|net income|eps|營收|毛利|營業利益|稅後|淨利", text):
        return "損益表"
    if re.search(r"asset|liabilit|equity|inventory|receivable|資產|負債|權益|存貨|應收", text):
        return "資產負債表"
    if re.search(r"cash flow|operating cash|capex|free cash|現金流|營業活動|投資活動|籌資活動|資本支出", text):
        return "現金流量表"
    if re.search(r"roe|roa|margin|ratio|debt|turnover|毛利率|營益率|淨利率|負債比|週轉", text):
        return "比率分析"
    if re.search(r"eps|bps|dps|per share|每股|每股盈餘|每股淨值", text):
        return "每股分析"

    return raw or "未分類"


def normalize_financial_rows(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        m = dict(r)
        cat = guess_fin_category(r)
        m["Category"] = cat
        m["Statement Group"] = cat

        # Add verification confidence columns if missing.
        vc = get_first(r, ["Verification Confidence", "verification_confidence", "Confidence", "confidence"])
        m.setdefault("Historical Data Confidence", get_first(r, ["Historical Data Confidence", "historical_confidence"]) or vc)
        m.setdefault("Add/Sub Check Confidence", get_first(r, ["Add/Sub Check Confidence", "add_sub_confidence", "addsub_confidence"]) or vc)
        m.setdefault("Division Check Confidence", get_first(r, ["Division Check Confidence", "division_confidence", "div_confidence"]) or vc)

        out.append(m)

    def key(x):
        fn = get_first(x, ["Filename", "Filemame", "filename", "source_file"])
        cat = x.get("Category", "")
        t = get_first(x, ["Time", "time", "Year", "year", "Date", "date"])
        data = get_first(x, ["Data", "data", "Account", "account", "Item", "item"])
        return (fn, FINANCIAL_CATEGORY_ORDER.get(cat, 999), str(t), str(data))

    return sorted(out, key=key)


def main():
    CANONICAL_DIR.mkdir(parents=True, exist_ok=True)

    basic_raw = read_csv(SOURCE_BASIC)
    fin_raw = read_csv(SOURCE_FINANCIAL)

    basic_clean, basic_summary_cols = clean_rows_drop_summary(basic_raw)
    basic_clean = [normalize_basic_row(r) for r in basic_clean]

    # Ensure YFinance display columns exist in BASICINFO output.
    basic_cols = []
    for r in basic_clean:
        for k in r.keys():
            if k not in basic_cols:
                basic_cols.append(k)
    for c in YFINANCE_DISPLAY_COLUMNS:
        if c not in basic_cols:
            basic_cols.append(c)

    # Keep final gate columns present and near end if they exist; do not drop original BASICINFO columns.
    for c in FINAL_GATE_COLUMNS:
        if c not in basic_cols:
            basic_cols.append(c)

    fin_clean, fin_summary_cols = clean_rows_drop_summary(fin_raw)
    fin_clean = normalize_financial_rows(fin_clean)

    fin_cols = []
    for r in fin_clean:
        for k in r.keys():
            if k not in fin_cols:
                fin_cols.append(k)

    for c in ["Category", "Statement Group", "Historical Data Confidence", "Add/Sub Check Confidence", "Division Check Confidence"]:
        if c not in fin_cols:
            fin_cols.append(c)

    basic_out = CANONICAL_DIR / "vrn_basicinfo_canonical_no_summary.csv"
    fin_out = CANONICAL_DIR / "vrn_financial_data_canonical_no_summary.csv"

    write_csv(basic_out, basic_clean, basic_cols)
    write_csv(fin_out, fin_clean, fin_cols)

    manifest = {
        "version": "VRN_ACTIVE_DATA_MANIFEST_V03",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "basicinfo_canonical_no_summary": str(basic_out),
        "financial_canonical_no_summary": str(fin_out),
        "source_basicinfo": str(SOURCE_BASIC),
        "source_financial": str(SOURCE_FINANCIAL),
        "basic_rows": len(basic_clean),
        "financial_rows": len(fin_clean),
        "basic_summary_columns_removed": basic_summary_cols,
        "financial_summary_columns_removed": fin_summary_cols,
        "rule_lock": [
            "canonical clean files outrank old final_gate_overlay",
            "summary columns removed from active outputs",
            "historical run scripts are archived evidence, not active pipeline",
            "YFinance reference fields use YFinance prefix",
            "BASICINFO report opinion fields are protected"
        ]
    }

    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()