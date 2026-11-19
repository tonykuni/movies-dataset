#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Split the five shared VDF numbers and print the input / class / group / API matrix.

Old files keep their names. The new number lives only in this table.
  py -3 VDF_MDL026_InputApiMatrix_v0100.py
  py -3 VDF_MDL026_InputApiMatrix_v0100.py selftest
"""
from __future__ import annotations

import sys
from pathlib import Path

# Copied from VDF_ENG090_DataCoverageGate_v0106 MACRO_CANDIDATES. The engine still owns that list.
MACRO = [
    ("CN_PMI", "中國 PMI", "macro_china_pmi, macro_china_pmi_yearly"),
    ("CN_CPI", "中國 CPI", "macro_china_cpi, macro_china_cpi_monthly"),
    ("CN_PPI", "中國 PPI", "macro_china_ppi, macro_china_ppi_yearly"),
    ("CN_GDP", "中國 GDP", "macro_china_gdp, macro_china_gdp_yearly"),
    ("CN_M2", "中國貨幣供給", "macro_china_money_supply"),
    ("CN_TRADE", "中國進出口", "macro_china_trade_balance, macro_china_exports_yoy"),
    ("US_CPI", "美國 CPI", "macro_usa_cpi_monthly, macro_usa_core_cpi_monthly"),
    ("US_PMI", "美國 ISM PMI", "macro_usa_ism_pmi, macro_usa_ism_non_pmi"),
    ("US_NFP", "美國非農", "macro_usa_non_farm"),
    ("US_UNEMP", "美國失業率", "macro_usa_unemployment_rate"),
    ("US_GDP", "美國 GDP", "macro_usa_gdp_monthly"),
    ("US_RATE", "美國聯邦基金利率", "macro_bank_usa_interest_rate"),
    ("TW_CPI", "台灣 CPI", "macro_taiwan_cpi"),
    ("TW_GDP", "台灣 GDP", "macro_taiwan_gdp"),
    ("TW_EXPORT", "台灣出口年增", "macro_taiwan_export_yoy"),
    ("GLOBAL_OIL", "原油", "macro_info_ws, energy_oil_hist"),
]

# file, old number, new number, class, group, input, api, gap
SPLIT = [
    ("VDF_ENG110_AKShareProbe_v0103.py", "ENG110", "ENG110", "探針", "MACRO", "AKShare 函式名", "AKSHARE", "不取代 FRED"),
    ("VDF_ENG110_USMacroProbe_v0102.py", "ENG110", "ENG241", "探針", "US_MACRO", "FRED series id · 財政部現金餘額", "FRED · GOV", "要 FRED_API_KEY"),
    ("VDF_ENG110_USMacroTree_v0100.py", "ENG110", "ENG242", "門", "US_MACRO", "流程冊 JSON", "不出網", ""),
    ("VDF_ENG117_ForwardVintage_v0103.py", "ENG117", "ENG117", "對齊", "INTL", "vintage 日期鍵", "本地", ""),
    ("VDF_ENG117_ForwardVintageDoor_v0101.py", "ENG117", "ENG243", "門", "INTL", "雜湊鎖", "不出網", ""),
    ("VDF_ENG118_ExportDesk_v0100.py", "ENG118", "ENG118", "輸出", "全群", "庫存切片", "本地 DuckDB", ""),
    ("VDF_ENG118_TWMarket_v0100.py", "ENG118", "ENG244", "名單", "TW_MARKET", "上市與上櫃代碼", "GOV TWSE · TPEX", "未送進 MDL014"),
    ("VDF_ENG240_DataScopeMatrix_v0100.py", "ENG240", "ENG240", "矩陣", "全群", "FetchGroups 冊", "只讀", ""),
    ("VDF_ENG240_SP500SectorWeight_v0100.py", "ENG240", "ENG245", "擷取", "US_SECTOR", "SPDR 收盤 · SPY 權重錨", "YFINANCE", "漂移權重，不是官方歷史，不是 13F"),
    ("VDF_MDL014_ThreeCodeUniverse_v0101.py", "MDL014", "MDL014", "名單", "TW_STOCK", "四碼 · .TW/.TWO · Bloomberg TT", "冊 · YFINANCE 後綴", "不自己打 OpenAPI"),
    ("VDF_MDL014_WorkstationSync_v0103.py", "MDL014", "MDL025", "工作樹", "無", "git 接點", "不出網", ""),
]


def rows() -> list[dict]:
    out = []
    for file, old, new, kind, group, feed, api, gap in SPLIT:
        if file.startswith("VDF_ENG110_AKShare"):
            for gid, zh, fns in MACRO:
                out.append({"file": file, "old": old, "new": new, "kind": kind, "group": gid, "input": fns, "api": api, "gap": gap, "zh": zh})
            continue
        out.append({"file": file, "old": old, "new": new, "kind": kind, "group": group, "input": feed, "api": api, "gap": gap, "zh": ""})
    return out


def families() -> list[dict]:
    keys = ("file", "old", "new", "kind", "group", "input", "api", "gap")
    return [dict(zip(keys, item)) for item in SPLIT]


def open_gaps() -> list[dict]:
    return [row for row in families() if row["gap"] and row["gap"] not in ("不取代 FRED",)]


def render() -> str:
    head = "新號     舊號     分類   分群          輸入                                          API                 缺口"
    lines = [head, "-" * len(head)]
    for row in rows():
        group = row["group"] if not row["zh"] else row["group"] + " " + row["zh"]
        lines.append("%-8s %-8s %-4s %-14s %-45s %-18s %s" % (
            row["new"], row["old"], row["kind"], group[:14], row["input"][:45], row["api"][:18], row["gap"]))
    gaps = open_gaps()
    lines.append("families=%d rows=%d open_gaps=%d" % (len(SPLIT), len(rows()), len(gaps)))
    return "\n".join(lines)


def audit(folder: Path | None = None) -> list[str]:
    fails = []
    seen = {}
    for row in families():
        if row["new"] in seen and seen[row["new"]] != row["file"]:
            fails.append("new id reused %s" % row["new"])
        seen[row["new"]] = row["file"]
    olds = {}
    for row in families():
        olds.setdefault(row["old"], set()).add(row["file"])
    if sorted(k for k, v in olds.items() if len(v) > 1) != ["ENG110", "ENG117", "ENG118", "ENG240", "MDL014"]:
        fails.append("old collisions")
    if not any(row["input"] == "macro_usa_cpi_monthly, macro_usa_core_cpi_monthly" for row in rows()):
        fails.append("cpi row")
    if not any(row["new"] == "ENG244" and "MDL014" in row["gap"] for row in families()):
        fails.append("join gap")
    if folder and folder.is_dir():
        names = {path.name for path in folder.rglob("VDF_*.py")}
        for row in families():
            if row["file"] not in names:
                fails.append("missing " + row["file"])
    return fails


def selftest() -> int:
    fails = audit(Path(__file__).resolve().parent)
    text = render()
    if "ENG241" not in text or "ENG245" not in text or "MDL025" not in text:
        fails.append("text")
    if len(rows()) != len(MACRO) + len(SPLIT) - 1:
        fails.append("row count %s" % len(rows()))
    if fails:
        print("[FAIL] " + "; ".join(fails))
        return 1
    print("[OK] split 5 numbers into 11 ids · rows %d · open gaps kept" % len(rows()))
    print(text)
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["selftest"]:
        return selftest()
    print(render(), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
