#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG119_StartTestRegister_v0101 — 四張矩陣，一頁 HTML。

引擎、錯誤、輸入、結果摘要。燈號在第一欄。
字級偏小。不重跑自測，不擷取，不改同義字冊。
跳出用 os.startfile；這台沒有視窗時只寫檔。
"""
from __future__ import annotations

import html
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[2]
OUT = VIA / "VIA_Reports" / "vdf_system" / "VDF_Matrix_v0101.html"

# Last measured selftest, this session. rc 0 green, rc 2 yellow, rc 1 red, rc 3 yellow, no door yellow.
MEASURED = [
    ("GREEN", "VDF_ENG045_OutputHub", "0101", "0", "7/7"),
    ("GREEN", "VDF_ENG047_USMacroDetailFetcher", "0101", "0", "8/8"),
    ("GREEN", "VDF_ENG050_OrderFetch", "0101", "0", "10/10"),
    ("GREEN", "VDF_ENG051_ActiveTWETF_Holdings", "0103", "0", "selftest"),
    ("GREEN", "VDF_ENG052_MegaFetch", "0103", "0", "10/10"),
    ("GREEN", "VDF_ENG053_ParamEngineMap", "0102", "0", "11/11"),
    ("RED", "VDF_ENG054_TWDailyBackfill", "0108", "1", "rc 1"),
    ("GREEN", "VDF_ENG055_OmniFetch", "0118", "0", "16/16"),
    ("GREEN", "VDF_ENG056_ChipBackfill", "0104", "0", "11/11"),
    ("GREEN", "VDF_ENG057_TradingValueBackfill", "0107", "0", "16/16"),
    ("YELLOW", "VDF_ENG058_IndustryUnifiedMap", "0102", "2", "NODATA"),
    ("GREEN", "VDF_ENG059_EstimateBands", "0101", "0", "7/7"),
    ("YELLOW", "VDF_ENG060_AdjPriceLayer", "0107", "2", "NODATA"),
    ("YELLOW", "VDF_ENG061_FeatureStore", "0105", "2", "NODATA"),
    ("YELLOW", "VDF_ENG062_GroupFeatureLayer", "0104", "2", "NODATA"),
    ("GREEN", "VDF_ENG063_MonthlyRevenue", "0107", "0", "10/10"),
    ("GREEN", "VDF_ENG064_HistoryBackfill", "0112", "0", "10/10"),
    ("GREEN", "VDF_ENG065_DbImport", "0101", "0", "9/9"),
    ("GREEN", "VDF_ENG066_GlobalUniverse", "0102", "0", "8/8"),
    ("GREEN", "VDF_ENG067_ConsensusEnrichment", "0100", "0", "10/10"),
    ("GREEN", "VDF_ENG068_ETFConsensusAnalysis", "0106", "0", "缺料檢通過"),
    ("GREEN", "VDF_ENG069_RevenueConsensusAnalysis", "0109", "0", "缺料檢通過"),
    ("GREEN", "VDF_ENG070_GroupClassificationIndex", "0112", "0", "缺料檢通過"),
    ("YELLOW", "VDF_ENG071_GroupBacktest", "0101", "2", "存證缺"),
    ("RED", "VDF_ENG072_StoryRotationBridge", "0103", "1", "七輸入檔未產出"),
    ("GREEN", "VDF_ENG073_DataArchitecture", "0101", "0", "10/10"),
    ("GREEN", "VDF_ENG074_FredMacroSSOT", "0103", "0", "18/18"),
    ("GREEN", "VDF_ENG075_MonthlyRevenueBackfill", "0103", "0", "10/10"),
    ("GREEN", "VDF_ENG076_ETFRevenueMomentum", "0102", "0", "8/8"),
    ("GREEN", "VDF_ENG077_ActiveETFUniverse", "0101", "0", "8/8"),
    ("GREEN", "VDF_ENG078_ActiveETFHoldingsHistory", "0110", "0", "30/30"),
    ("GREEN", "VDF_ENG079_LocalDbConsolidate", "0103", "0", "16/16"),
    ("GREEN", "VDF_ENG081_UniverseAlign", "0102", "0", "13/13"),
    ("RED", "VDF_ENG082_FinStatements", "0105", "1", "22 檢 3 失敗"),
    ("GREEN", "VDF_ENG085_VatetfBridge", "0105", "0", "12/12"),
    ("YELLOW", "VDF_ENG086_QuantGuardOneBridge", "0101", "3", "此境未裝"),
    ("GREEN", "VDF_ENG087_MarketListGovernance", "0104", "0", "7/7"),
    ("RED", "VDF_ENG088_ConsensusFusionBridge", "0103", "1", "7 檢 2 失敗"),
    ("GREEN", "VDF_ENG089_IncrementalFetchGate", "0106", "0", "24/24"),
    ("GREEN", "VDF_ENG090_DataCoverageGate", "0106", "0", "27/27"),
    ("GREEN", "VDF_ENG091_VdfAuditGate", "0100", "0", "11/11"),
    ("GREEN", "VDF_ENG092_TWFlowsAdjConsensus", "0100", "0", "14/14"),
    ("GREEN", "VDF_ENG093_LaunchConsole", "0103", "0", "13/13"),
    ("YELLOW", "VDF_ENG094_ActiveETFActivity", "0100", "NO_DOOR", "無 --selftest"),
    ("YELLOW", "VDF_ENG095_InstrumentIdentity", "0100", "NO_DOOR", "無 --selftest"),
    ("YELLOW", "VDF_ENG096_ActiveETFMeasures", "0100", "NO_DOOR", "無 --selftest"),
    ("YELLOW", "VDF_ENG097_GlobalETFFlow", "0100", "NO_DOOR", "無 --selftest"),
    ("YELLOW", "VDF_ENG098_SameDayAlign", "0100", "NO_DOOR", "無 --selftest"),
    ("YELLOW", "VDF_ENG099_IndexSameDay", "0100", "NO_DOOR", "無 --selftest"),
    ("YELLOW", "VDF_ENG100_FinStatementQuery", "0101", "NO_DOOR", "無 --selftest"),
    ("YELLOW", "VDF_ENG101_SourceProbe", "0100", "NO_DOOR", "無 --selftest"),
    ("YELLOW", "VDF_ENG102_SourceLane", "0101", "NO_DOOR", "無 --selftest"),
    ("YELLOW", "VDF_ENG103_ListingName", "0100", "NO_DOOR", "無 --selftest"),
    ("GREEN", "VDF_ENG109_USMacroList", "0100", "0", "OK"),
    ("GREEN", "VDF_ENG110_AKShareProbe", "0102", "0", "OK"),
    ("GREEN", "VDF_ENG110_USMacroProbe", "0101", "0", "OK"),
    ("GREEN", "VDF_ENG110_USMacroTree", "0100", "0", "OK"),
    ("GREEN", "VDF_ENG111_USMacroAgency", "0100", "0", "OK"),
    ("GREEN", "VDF_ENG112_FedMore", "0100", "0", "OK"),
    ("GREEN", "VDF_ENG113_MacroMethod", "0101", "0", "OK"),
    ("GREEN", "VDF_ENG114_PmiPair", "0100", "0", "OK"),
    ("GREEN", "VDF_ENG115_SentimentFetch", "0101", "0", "OK"),
    ("GREEN", "VDF_ENG116_AAIIWorkbook", "0101", "0", "OK"),
    ("YELLOW", "VDF_ENG117_ForwardVintage", "0101", "NO_DOOR", "門在 ForwardVintageDoor"),
    ("GREEN", "VDF_ENG117_ForwardVintageDoor", "0100", "0", "OK"),
    ("GREEN", "VDF_ENG118_ExportDesk", "0100", "0", "OK"),
    ("YELLOW", "VDF_ENG118_TWMarket", "0100", "NO_DOOR", "無 --selftest"),
    ("GREEN", "VDF_MDL002_YFinanceFetchingEngine", "0100", "2", "NODATA"),
    ("GREEN", "VDF_MDL003_SentimentMacroEngine", "0100", "2", "NODATA"),
    ("GREEN", "VDF_MDL004_TWFullMarketEngine", "0100", "0", "9/9"),
    ("YELLOW", "VDF_MDL006_FinancialModel", "0100", "2", "NODATA"),
    ("GREEN", "VDF_SystemManager", "0107", "0", "拒絕無標記"),
    ("YELLOW", "VDF_InjectAccelNetBridges", "0104", "NO_DOOR", "無 --selftest"),
    ("GREEN", "vdf_input_matrix", "0100", "0", "13/13"),
]

INPUTS = [
    ("GREEN", "vdf.verb.start", "start / 啟動 / via-vdf-start", "狀態", "不擷取"),
    ("GREEN", "vdf.verb.test", "test / 測試 / selftest", "--selftest", "不擷取"),
    ("GREEN", "vdf.verb.register", "register / 註冊", "只寫本 SSOT", "不改同義字冊"),
    ("RED", "deny", "talib / registry-sync --apply", "拒絕", "不執行"),
]


def _esc(text) -> str:
    return html.escape(str(text), quote=True)


def _rows(items, keys) -> str:
    body = []
    for item in items:
        cells = [f'<td class="lamp {item[0]}">{item[0]}</td>']
        cells += [f"<td>{_esc(item[i])}</td>" for i in range(1, keys)]
        body.append("<tr>" + "".join(cells) + "</tr>")
    return "\n".join(body)


def page() -> Path:
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for row in MEASURED:
        counts[row[0]] += 1
    # MDL002 and MDL003 were rc 2. Fix lamps that I marked GREEN by mistake for rc 2.
    fixed = []
    for lamp, fam, ver, rc, note in MEASURED:
        if rc == "2" and lamp == "GREEN":
            lamp = "YELLOW"
        fixed.append((lamp, fam, ver, rc, note))
    counts = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for row in fixed:
        counts[row[0]] += 1
    errors = [row for row in fixed if row[0] != "GREEN"]
    summary = [
        ("GREEN", "通過", counts["GREEN"], "rc 0"),
        ("YELLOW", "缺料或無門", counts["YELLOW"], "rc 2 / 3 / NO_DOOR"),
        ("RED", "自測失敗", counts["RED"], "rc 1"),
        ("GREEN", "家族", len(fixed), "尾版各一"),
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        """<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VDF 矩陣</title>
<style>
body { margin: 12px 16px; background: #f4f5f6; color: #1c1e21; font: 11px/1.35 "Segoe UI", "Noto Sans TC", sans-serif; }
h1 { font-size: 13px; font-weight: 600; margin: 0 0 2px; }
p.meta { margin: 0 0 10px; color: #5c6370; }
h2 { font-size: 11px; font-weight: 600; margin: 12px 0 4px; letter-spacing: 0.02em; }
table { width: 100%; border-collapse: collapse; background: #fff; margin: 0 0 8px; }
th, td { border: 1px solid #d5d8de; padding: 2px 6px; text-align: left; vertical-align: top; word-break: break-word; }
th { background: #e8eaee; font-weight: 600; }
td.lamp { width: 58px; font-weight: 650; letter-spacing: 0.03em; }
td.GREEN { color: #0d6b38; }
td.YELLOW { color: #8a5a00; }
td.RED { color: #9d1c1c; }
</style>
</head>
<body>
<h1>VDF 矩陣</h1>
<p class="meta">BY RICH · 上次自測 · 不重跑 · 不擷取 · 燈號在第一欄</p>
<h2>結果矩陣摘要</h2>
<table>
<thead><tr><th>燈</th><th>項</th><th>數</th><th>意思</th></tr></thead>
<tbody>
"""
        + _rows(summary, 4)
        + """
</tbody></table>
<h2>錯誤矩陣</h2>
<table>
<thead><tr><th>燈</th><th>家族</th><th>版</th><th>rc</th><th>說明</th></tr></thead>
<tbody>
"""
        + _rows(errors, 5)
        + """
</tbody></table>
<h2>輸入矩陣</h2>
<table>
<thead><tr><th>燈</th><th>動詞</th><th>同義字</th><th>做什麼</th><th>邊界</th></tr></thead>
<tbody>
"""
        + _rows(INPUTS, 5)
        + """
</tbody></table>
<h2>引擎矩陣</h2>
<table>
<thead><tr><th>燈</th><th>家族</th><th>版</th><th>rc</th><th>說明</th></tr></thead>
<tbody>
"""
        + _rows(fixed, 5)
        + """
</tbody></table>
</body>
</html>
""",
        encoding="utf-8",
    )
    return OUT


def open_page(path: Path) -> bool:
    try:
        if hasattr(os, "startfile"):
            os.startfile(path)  # Windows
            return True
    except OSError:
        return False
    return False


def main() -> int:
    path = page()
    opened = open_page(path)
    print(path)
    print("opened" if opened else "written")
    return 0


def selftest() -> int:
    path = page()
    text = path.read_text(encoding="utf-8")
    ok = (
        path.is_file()
        and "結果矩陣摘要" in text
        and "錯誤矩陣" in text
        and "輸入矩陣" in text
        and "引擎矩陣" in text
        and text.find("<td class=\"lamp") < text.find("VDF_ENG045")
        and "BY RICH" in text
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
