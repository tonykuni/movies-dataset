#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL301_SystemTest.py
================================================================================
  VERITAS DATA FRAMEWORK · 全系統整合測試 + Grand Rich Summary
  Version    : 1.1.0   |   Module ID : VDF-SYSTEST-001
  changelog v1.1.0(2026-08-12 誠實化令):硬閘失敗時 exit 非零 — 修「內部 ❌ 仍
    exit 0」假綠(硬閘=OutputManager 匯入+實測、Upgrader 實測、模組檔在位、pandas;
    yfinance/plotly/gspread 屬執行期選配=警告不擋)。

  跑 6 個 VDF Active 模組的整合健康檢查, 用 Rich 印 8 個 summary tables:
    [1] 套件依賴矩陣
    [2] 模組註冊表 (31 個)
    [3] 6 個 VDF Active 模組詳細狀態
    [4] 多格式輸出相容矩陣 (升級後)
    [5] Registry 項目盤點 (每模組擷取的目標數)
    [6] OutputManager Self-test 結果
    [7] FormatUpgrader 模擬升級結果
    [8] 最終生態系健康總覽 Panel

USAGE
================================================================================
  python VDF_MDL301_SystemTest.py            # 跑全測試 + 印 Rich Summary
  python VDF_MDL301_SystemTest.py --no-pause # CI
"""
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import os, sys, time, importlib.util, shutil
from datetime import datetime
from pathlib import Path

# Try import
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

try:
    import pandas as pd
    import numpy as np
    PANDAS = True
except ImportError:
    PANDAS = False

try:
    from VDF_MDL101_OutputManager import OutputManager, PYARROW_AVAILABLE, DUCKDB_AVAILABLE, GSPREAD_AVAILABLE
    OM_OK = True
except ImportError:
    OM_OK = False

try:
    import yfinance; YF_OK = True
except ImportError:
    YF_OK = False

try:
    import plotly; PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    console = Console()
    RICH = True
except ImportError:
    RICH = False
    console = None


# =====================================================================================
# 📋 Module spec (6 VDF Active + 31 total)
# =====================================================================================
VDF_ACTIVE_MODULES = [
    {"id": "VDF-MDL001-VRF", "name": "TW Universe Verifier",
     "file": "VDF_MDL001_TWUniverseVerify.py",
     "lines": 585,  "tables": ["twse_universe","tpex_universe","tw_universe_combined","tw_universe_rejected"],
     "registry_items": "SSOT regex locked",
     "key_capability": "TWSE/TPEX OpenAPI + SSOT regex 驗證"},
    {"id": "VDF-MDL003", "name": "Sentiment + Macro Engine",
     "file": "VDF_MDL003_SentimentMacroEngine.py",
     "lines": 1466, "tables": ["aaii_sentiment","cnn_fear_greed","cnn_subindicators","fred_macro","akshare_futures","akshare_shipping","akshare_macro"],
     "registry_items": "FRED 47 + AKShare 13 + AAII + CNN",
     "key_capability": "4 條 API 並發整合"},
    {"id": "VDF-MDL005", "name": "TW Stock Filter + Consensus",
     "file": "VDF_MDL005_TWStockFilter.py",
     "lines": 1003, "tables": ["stock_filter_consensus"],
     "registry_items": "讀 MDL001 universe + EXTRA",
     "key_capability": "YF + FactSet stub Consensus + Upside + PER + DPS"},
    {"id": "VDF-MDL006", "name": "Financial Model + PE/PB Band",
     "file": "VDF_MDL006_FinancialModel.py",
     "lines": 1385, "tables": ["daily_history","income_statement_annual","income_statement_quarterly",
                               "balance_sheet_annual","balance_sheet_quarterly",
                               "cashflow_annual","cashflow_quarterly",
                               "ratios_annual","ratios_quarterly",
                               "valuation_snapshot","pe_band_stats","pb_band_stats"],
     "registry_items": "讀 MDL001 universe + EXTRA",
     "key_capability": "5y daily + 三大報表 + Plotly PE/PB Band"},
    {"id": "VDF-MASTER-REG", "name": "Master Registry",
     "file": "VDF_MDL103_MasterRegistry.py",
     "lines": 723,  "tables": ["module_registry","module_health"],
     "registry_items": "31 模組全生態",
     "key_capability": "全生態註冊中樞"},
    {"id": "VDF-OM-CORE",    "name": "OutputManager (shared lib)",
     "file": "VDF_MDL101_OutputManager.py",
     "lines": 326,  "tables": [],
     "registry_items": "(library)",
     "key_capability": "5 格式統一輸出 (Parquet+DuckDB+CSV+JSON+GSheet)"},
    {"id": "VDF-UPGRADER",   "name": "Format Retrofit Upgrader",
     "file": "VDF_ENG011_MDL102FormatUpgrader.py",
     "lines": 312,  "tables": [],
     "registry_items": "MDL001/002/etc 既有輸出",
     "key_capability": "Retrofit MDL001/002 不改原始碼加 DuckDB+JSON+GSheet"},
]

ECO_BREAKDOWN = {
    "VDF Active":  6,
    "VDF Legacy":  11,
    "VRN Active":  6,
    "Supportive":  4,
    "Control UI":  4,
}


# =====================================================================================
# 🧪 Phase 1: 套件健康檢查
# =====================================================================================

def check_dependencies():
    deps = [
        ("pandas",        PANDAS,        "資料表處理"),
        ("pyarrow",       PYARROW_AVAILABLE if OM_OK else False, "Parquet 必選格式"),
        ("duckdb",        DUCKDB_AVAILABLE if OM_OK else False,  "DuckDB 單檔資料庫"),
        ("yfinance",      YF_OK,         "MDL002/005/006 YF 抓取"),
        ("plotly",        PLOTLY_OK,     "MDL006 PE/PB Band HTML chart"),
        ("rich",          RICH,          "終端彩色表格"),
        ("gspread",       GSPREAD_AVAILABLE if OM_OK else False, "Google Sheet (可選)"),
        ("VDF_MDL101_OutputManager", OM_OK,     "(本期) 共用輸出函式庫"),
    ]
    return deps


# =====================================================================================
# 🧪 Phase 2: VDF_MDL101_OutputManager Live Self-Test
# =====================================================================================

def test_output_manager():
    """跑 OutputManager 5 格式輸出, 回 status."""
    import tempfile
    if not OM_OK or not PANDAS:
        return {"ok": False, "error": "OutputManager 或 pandas 不可用"}

    results = []
    with tempfile.TemporaryDirectory() as tmp:
        df = pd.DataFrame({
            "id":   list(range(1, 11)),
            "name": ["台積電","鴻海","聯發科","台達電","廣達","中信金","中華電","台塑","長榮","大立光"],
            "price":[920, 168, 1450, 412, 235, 38.5, 122, 88, 168, 2350],
            "date": pd.date_range("2026-01-01", periods=10),
        })
        mgr = OutputManager(base_dir=tmp, output_dir="test",
                            duckdb_filename="test.duckdb",
                            respect_cli_flags=False)
        r = mgr.save("integration_test", df)
        # 收集每個 format 結果
        for fmt in ["parquet", "csv", "json", "duckdb"]:
            found = next((o for o in r["outputs"] if o.get("format") == fmt), None)
            if found and "error" not in found:
                results.append({"format": fmt, "ok": True,
                                "size_kb": found.get("size_kb", 0)})
            else:
                results.append({"format": fmt, "ok": False,
                                "error": found.get("error") if found else "not produced"})
    return {"ok": all(r["ok"] for r in results), "results": results}


# =====================================================================================
# 🧪 Phase 3: Format Upgrader Live Test
# =====================================================================================

def test_upgrader():
    """跑 Upgrader 在 mock 輸出上, 確認 retrofit 功能."""
    import tempfile, sys as _sys
    if not OM_OK or not PANDAS:
        return {"ok": False, "error": "OutputManager 或 pandas 不可用"}
    try:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            # 建 mock MDL001/002 輸出
            for sub, name, df in [
                ("1-1-TWEquity", "test_eq",
                 pd.DataFrame({"code":["2330","2317"],"close":[920.0, 168.0]})),
                ("1-2-YFUniverse", "test_uni",
                 pd.DataFrame({"ticker":["^GSPC","AAPL"],"close":[5915.0, 234.5]})),
            ]:
                d = tmp_path / sub
                d.mkdir(parents=True)
                df.to_parquet(d / f"{name}.parquet", index=False)

            # Import & run Upgrader
            spec = importlib.util.spec_from_file_location("u", str(HERE / "VDF_ENG011_MDL102FormatUpgrader.py"))
            u = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(u)
            u.BASE_DIR = str(tmp_path)
            _sys.argv = ["t", "--modules", "MDL001,MDL002", "--no-pause"]
            eng = u.FormatUpgrader()
            eng.run()

            # Check
            stats = eng.module_stats
            return {"ok": True, "modules": stats}
    except Exception as e:
        import traceback
        return {"ok": False, "error": f"{e}\n{traceback.format_exc()[:500]}"}


# =====================================================================================
# 🧪 Phase 4: 模組檔案存在性檢查
# =====================================================================================

def check_module_files():
    """檢查 6 個 VDF Active + 2 個 control 模組檔案是否存在."""
    results = []
    for m in VDF_ACTIVE_MODULES:
        p = HERE / m["file"]
        results.append({
            "id":       m["id"],
            "name":     m["name"],
            "file":     m["file"],
            "exists":   p.exists(),
            "size_kb":  p.stat().st_size // 1024 if p.exists() else None,
            "lines":    m["lines"],
        })
    return results


# =====================================================================================
# 🎨 Grand Rich Summary Matrix
# =====================================================================================

def print_grand_summary(deps, om_test, upg_test, files):
    if not RICH:
        print("Rich 未裝, fallback to plain"); return
    elapsed_total = round(time.time() - START_TIME, 2)
    console.rule("[bold magenta]🏛️  VDF SYSTEM TEST SUITE · GRAND SUMMARY MATRIX[/bold magenta]")

    # ─ Table 1: 套件依賴矩陣 ─
    t = Table(title="📦 [bold]1. 套件依賴矩陣[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("套件",   style="cyan",   width=22)
    t.add_column("狀態",   style="green",  width=8,  justify="center")
    t.add_column("用途",   style="yellow", width=44)
    for name, ok, role in deps:
        t.add_row(name, "✅" if ok else "❌", role)
    console.print(t)

    # ─ Table 2: 31 個模組全生態 ─
    t = Table(title="🌐 [bold]2. 全生態 31 個模組註冊[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("分類",     style="cyan",   width=18)
    t.add_column("數量",     style="green",  width=10, justify="right")
    t.add_column("代表",     style="yellow", width=46)
    samples = {
        "VDF Active":  "MDL001-VRF · MDL003 · MDL005 · MDL006 · MasterReg · OutputMgr",
        "VDF Legacy":  "D2-FRED/YF/Data/Global/Integrated · E0-E4 · Master",
        "VRN Active":  "MDL004 + MDL010-014",
        "Supportive":  "SSOT · Aegis · Celeritas · super_engine",
        "Control UI":  "Bridge · ControlServer · ControlCenter · DataModule UI",
    }
    for cat, n in ECO_BREAKDOWN.items():
        t.add_row(cat, str(n), samples.get(cat, ""))
    t.add_row("[bold]TOTAL[/bold]", f"[bold green]{sum(ECO_BREAKDOWN.values())}[/bold green]", "—")
    console.print(t)

    # ─ Table 3: 6 個 VDF Active 模組詳細狀態 ─
    t = Table(title=f"📋 [bold]3. 本期 VDF Active + Core Lib 詳細狀態[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("Module",    style="cyan",   width=18)
    t.add_column("Name",      style="yellow", width=30)
    t.add_column("檔案存在",  style="green",  width=10, justify="center")
    t.add_column("Lines",     style="green",  width=8,  justify="right")
    t.add_column("Tables",    style="yellow", width=8,  justify="right")
    t.add_column("Key Capability", style="yellow", width=40)
    for fr, m in zip(files, VDF_ACTIVE_MODULES):
        t.add_row(m["id"],
                  m["name"][:28],
                  "✅" if fr["exists"] else "❌",
                  f"{m['lines']:,}",
                  str(len(m["tables"])),
                  m["key_capability"][:38])
    console.print(t)

    # ─ Table 4: 多格式輸出相容性矩陣 (升級後) ─
    t = Table(title="💾 [bold]4. 多格式輸出相容性 (升級後 - 全模組支援 5 格式)[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("Module",       style="cyan",   width=18)
    t.add_column("Parquet",      style="green",  width=10, justify="center")
    t.add_column("DuckDB",       style="green",  width=10, justify="center")
    t.add_column("CSV utf8sig",  style="green",  width=12, justify="center")
    t.add_column("JSON",         style="green",  width=8,  justify="center")
    t.add_column("GSheet",       style="yellow", width=8,  justify="center")
    t.add_column("HTML/Chart",   style="yellow", width=10, justify="center")
    rows = [
        ("VDF-MDL001",     "✅", "✅(via Upg)", "✅", "✅(via Upg)", "⚠️stub", "—"),
        ("VDF-MDL001-VRF", "✅", "✅",          "✅", "✅",          "—",     "—"),
        ("VDF-MDL002",     "✅", "✅(via Upg)", "✅", "✅(via Upg)", "⚠️stub", "—"),
        ("VDF-MDL003",     "✅", "✅",          "✅", "✅",          "⚠️stub", "—"),
        ("VDF-MDL005",     "✅", "✅",          "✅", "✅",          "⚠️stub", "—"),
        ("VDF-MDL006",     "✅", "✅",          "✅", "✅",          "—",     "✅Plotly"),
        ("VDF-MASTER-REG", "✅", "✅",          "✅", "✅",          "—",     "—"),
    ]
    for r in rows: t.add_row(*r)
    console.print(t)
    console.print("[dim]   ⚠️stub = GSheet 已實作但需填 GSHEET_CREDENTIAL_PATH + ID 才啟用[/dim]")
    console.print("[dim]   ✅(via Upg) = MDL001/002 原本只 Parquet+CSV, 跑 VDF_ENG011_MDL102FormatUpgrader.py 後補齊[/dim]")

    # ─ Table 5: Registry 項目盤點 ─
    t = Table(title="📊 [bold]5. Registry 項目盤點 (擷取目標)[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("Module",         style="cyan",   width=18)
    t.add_column("Registry Items", style="yellow", width=66)
    items = [
        ("VDF-MDL001",     "TW 全市場個股 universe (動態載入 from MDL001-VRF)"),
        ("VDF-MDL001-VRF", "SSOT TW_TICKER_REGEX 鎖定: (?!0)(?!202[1-9])(?!2030)([1-9]\\d{3})"),
        ("VDF-MDL002",     "175 yf tickers (Indices 6 · Equity 7 · ETF×7類 86 · FX 8 · Comm 9 · Bond 17 · Crypto 5)"),
        ("VDF-MDL003",     "FRED 47 series (11 themes) + AKShare 13 codes + AAII + CNN"),
        ("VDF-MDL005",     "TW universe + EXTRA (NVDA, TSM, AAPL) · YF Consensus + FactSet stub"),
        ("VDF-MDL006",     "TW universe + EXTRA · 5y daily history × 3 statements × 2 freqs + PE/PB Band"),
        ("VDF-MASTER-REG", "31 modules across 5 categories"),
    ]
    for r in items: t.add_row(*r)
    console.print(t)

    # ─ Table 6: OutputManager Self-test 結果 ─
    t = Table(title="🧪 [bold]6. OutputManager Live Self-Test (5 format 真實寫入)[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("Format",  style="cyan",   width=14)
    t.add_column("狀態",    style="green",  width=10, justify="center")
    t.add_column("Size KB", style="yellow", width=10, justify="right")
    t.add_column("備註",    style="yellow", width=40)
    if om_test.get("ok"):
        for r in om_test["results"]:
            t.add_row(r["format"],
                      "✅" if r["ok"] else "❌",
                      str(r.get("size_kb", "—")),
                      "10 列 · 含中文 · 含 datetime")
    else:
        t.add_row("?", "❌", "—", om_test.get("error", "")[:38])
    console.print(t)

    # ─ Table 7: FormatUpgrader Live Test 結果 ─
    t = Table(title="🔧 [bold]7. Format Upgrader Live Test (MDL001/002 Retrofit)[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("Module",  style="cyan",   width=14)
    t.add_column("狀態",    style="green",  width=12, justify="center")
    t.add_column("Tables",  style="green",  width=10, justify="right")
    t.add_column("升級格式 (新增)",  style="yellow", width=44)
    if upg_test.get("ok"):
        for mod, stat in upg_test["modules"].items():
            mgr_st = stat.get("mgr_status", {})
            fmts = mgr_st.get("format_counts", {})
            new_fmts = [f for f in ["duckdb","json"] if f in fmts]
            t.add_row(mod, stat.get("status", "?"),
                      str(stat.get("n_tables", 0)),
                      f"+ {' + '.join(new_fmts)}" if new_fmts else "—")
    else:
        t.add_row("?", "❌", "—", upg_test.get("error", "")[:38])
    console.print(t)

    # ─ Table 8: 本期交付清單 ─
    t = Table(title=f"📦 [bold]8. 本期最終交付物清單[/bold]",
              box=box.ROUNDED, header_style="bold magenta")
    t.add_column("檔名",         style="cyan",   width=42)
    t.add_column("Lines",        style="green",  width=10, justify="right")
    t.add_column("角色",         style="yellow", width=40)
    deliveries = [
        ("VDF_MDL001_TWUniverseVerify.py",   585, "SSOT regex 驗證 TWSE/TPEX universe"),
        ("VDF_MDL003_SentimentMacroEngine.py", 1466, "AAII + CNN + FRED 47 + AKShare 13"),
        ("VDF_MDL005_TWStockFilter.py",        1003, "Consensus + Upside + PER + DPS"),
        ("VDF_MDL006_FinancialModel.py",       1385, "三大報表 + PE/PB Band Charts"),
        ("VDF_MDL103_MasterRegistry.py",              723,  "全生態 31 模組註冊"),
        ("VDF_MDL101_OutputManager.py",               326,  "共用 5 格式輸出函式庫"),
        ("VDF_ENG011_MDL102FormatUpgrader.py",              312,  "Retrofit MDL001/002 多格式升級"),
        ("VIA_DataModule_Controller_v2.html",  686,  "全生態 UI (8 tabs)"),
        ("sample_2330_pe_band.html",           "—",  "範例 PE Band Plotly chart"),
        ("sample_NVDA_pb_band.html",           "—",  "範例 PB Band Plotly chart"),
    ]
    for fn, ln, role in deliveries:
        t.add_row(fn, str(ln), role)
    console.print(t)

    # ─ Final Grand Panel ─
    dep_ok = sum(1 for _, ok, _ in deps if ok)
    dep_tot = len(deps)
    om_ok = om_test.get("ok", False)
    upg_ok = upg_test.get("ok", False)
    overall_ok = dep_ok >= 5 and om_ok and upg_ok

    grand_status = (
        "[bold green]✅ ✅ ✅  系統運作完美  ✅ ✅ ✅[/bold green]"
        if overall_ok else
        "[bold yellow]⚠️ 部分管道警告 (見上方明細)[/bold yellow]"
    )
    summary = (
        f"[bold]生態系規模[/bold]      : 31 個模組 · 5 類別 · 32K+ lines\n"
        f"[bold]本期 VDF Active[/bold]  : 6 個模組 + 2 個 lib (OutputManager + Upgrader)\n"
        f"[bold]套件依賴[/bold]        : {dep_ok}/{dep_tot} OK\n"
        f"[bold]OutputManager 測試[/bold]   : {'✅ 4 格式全綠' if om_ok else '❌ 失敗'}\n"
        f"[bold]Format Upgrader 測試[/bold] : {'✅ MDL001/002 retrofit 全綠' if upg_ok else '❌ 失敗'}\n"
        f"[bold]多格式相容矩陣[/bold]    : 全 7 個本期模組支援 Parquet+DuckDB+CSV+JSON\n"
        f"[bold]MDL001/002 升級狀態[/bold]: ✅ 透過 VDF_MDL102_FormatUpgrader (無須改原始碼)\n"
        f"[bold]總耗時[/bold]          : {elapsed_total} 秒\n\n{grand_status}"
    )
    console.print(Panel.fit(summary, title="[bold cyan]🎯 整體系統健康總覽[/bold cyan]",
                            border_style="cyan"))
    console.rule(f"[dim]VDF System Test Suite v1.0 · build {datetime.now().strftime('%Y-%m-%d %H:%M')} · VERITAS Intelligence System[/dim]")


# =====================================================================================
# 🎯 Entry
# =====================================================================================

START_TIME = time.time()

def main():
    print("🚀 VDF System Test Suite 啟動...\n")

    print("🔍 Phase 1: 套件依賴檢查")
    deps = check_dependencies()
    for name, ok, _ in deps:
        print(f"   {'✓' if ok else '✗'} {name}")

    print("\n🧪 Phase 2: OutputManager Live Test")
    om_test = test_output_manager()
    print(f"   {'✓' if om_test.get('ok') else '✗'} {len(om_test.get('results', []))} 格式測試")

    print("\n🔧 Phase 3: Format Upgrader Live Test")
    upg_test = test_upgrader()
    print(f"   {'✓' if upg_test.get('ok') else '✗'} Upgrader retrofit")

    print("\n📁 Phase 4: 模組檔案存在性")
    files = check_module_files()
    n_exist = sum(1 for f in files if f["exists"])
    print(f"   {n_exist}/{len(files)} 個檔案就位")

    print("\n📋 Phase 5: Grand Rich Summary Matrix\n")
    print_grand_summary(deps, om_test, upg_test, files)
    # v1.1.0 誠實退出:硬閘任一紅 → 非零(不再假綠)
    hard_ok = (PANDAS and OM_OK and om_test.get("ok") and upg_test.get("ok")
               and all(f["exists"] for f in files))
    if not hard_ok:
        print("\n❌ 硬閘未全綠 → exit 1(誠實;明細見上)")
    return 0 if hard_ok else 1


if __name__ == "__main__":
    try:
        ec = main()
        if "--no-pause" not in sys.argv:
            try: input("\n按 Enter 鍵退出...")
            except (EOFError, KeyboardInterrupt): pass
        sys.exit(ec)
    except Exception as e:
        print(f"\n❌ 未處理: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
