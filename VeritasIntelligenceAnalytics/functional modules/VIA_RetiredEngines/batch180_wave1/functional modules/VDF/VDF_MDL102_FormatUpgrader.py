#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL102_FormatUpgrader.py
================================================================================
  VERITAS DATA FRAMEWORK · 多格式 Retrofit Upgrader
  Version    : 1.0.0   |   Module ID : VDF-UPG-001

ROLE
================================================================================
  把任何 VDF 模組的既有 Parquet / CSV 輸出, 用 VDF_MDL101_OutputManager 重新處理:
    既有 (Parquet+CSV) → 補上 (DuckDB+JSON+GSheet)

  支援 MDL001 / MDL002 等 legacy 模組無需改動原始程式碼即可升級.

  策略:
    1. 掃描各模組輸出目錄 (1-1-MDL001 / 1-2-MDL002 等)
    2. 讀每個 .parquet (優先) 或 .csv (fallback)
    3. 用 VDF_MDL101_OutputManager.save() 重寫所有 5 格式
    4. 產 Rich Summary 顯示前後對比

USAGE
================================================================================
  python VDF_MDL102_FormatUpgrader.py                       # 升級全部 MDL
  python VDF_MDL102_FormatUpgrader.py --modules MDL001,MDL002  # 限定模組
  python VDF_MDL102_FormatUpgrader.py --dryrun              # 不寫, 只報告
  python VDF_MDL102_FormatUpgrader.py --no-pause            # CI 模式
"""
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

# =====================================================================================
# 📋 ALL PARAMETERS
# =====================================================================================

BASE_DIR           = r"C:\Users\tonyk\OneDrive\VeritasIntelligenceAnalytics\module\VDF\dict"

# 各 MDL 輸出目錄對應 (含 DuckDB 檔名)
MODULE_OUTPUT_MAP = {
    "MDL001":     {"output_dir": "1-1-TWEquity",       "duckdb_filename": "VDF_MDL001_TWEquity.duckdb"},
    "MDL001-VRF": {"output_dir": "1-0-TWUniverse",     "duckdb_filename": "VDF_MDL001_TWUniverse.duckdb"},
    "MDL002":     {"output_dir": "1-2-YFUniverse",     "duckdb_filename": "VDF_MDL002_YFUniverse.duckdb"},
    "MDL003":     {"output_dir": "1-4-SentimentMacro", "duckdb_filename": "VDF_MDL003_SentimentMacro.duckdb"},
    "MDL004":     {"output_dir": "1-4-TWFullMarket",   "duckdb_filename": "VDF_MDL004_TWFullMarket.duckdb"},
    "MDL005":     {"output_dir": "1-5-TWStockFilter",  "duckdb_filename": "VDF_MDL005_TWStockFilter.duckdb"},
    "MDL006":     {"output_dir": "1-6-FinancialModel", "duckdb_filename": "VDF_MDL006_FinancialModel.duckdb"},
    "MDL007":     {"output_dir": "1-7-SSOTResolver",   "duckdb_filename": "VDF_MDL007_SSOTResolver.duckdb"},
}

# 預設啟用全 5 格式
OUTPUT_PARQUET     = True
OUTPUT_DUCKDB      = True
OUTPUT_CSV         = True
OUTPUT_JSON        = True
OUTPUT_GSHEET      = False

# Skip patterns (不升級這些檔)
SKIP_FILE_PATTERNS = ["backup", "_temp_", "_old_"]


# =====================================================================================
# 📦 Imports
# =====================================================================================

import os, sys, json, time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

# Import OutputManager
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from VDF_MDL101_OutputManager import OutputManager, PYARROW_AVAILABLE, DUCKDB_AVAILABLE
    OUTPUT_MGR_AVAILABLE = True
except ImportError:
    OUTPUT_MGR_AVAILABLE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich import box
    console = Console()
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    console = None


# =====================================================================================
# 🎯 FormatUpgrader Engine
# =====================================================================================

class FormatUpgrader:
    """掃描 MDL 輸出目錄, 用 OutputManager 重新處理."""
    VERSION = "1.0.0"

    def __init__(self):
        self.base_dir = Path(BASE_DIR)
        self.dryrun   = "--dryrun" in sys.argv
        self.modules  = list(MODULE_OUTPUT_MAP.keys())
        # CLI override
        for i, a in enumerate(sys.argv):
            if a == "--modules" and i+1 < len(sys.argv):
                self.modules = [m.strip().upper() for m in sys.argv[i+1].split(",") if m.strip()]
        self.start_time   = time.time()
        self.results: List[Dict] = []   # per-table
        self.module_stats: Dict[str, Dict] = {}

    def show_header(self):
        info = (
            f"[bold]VDF Format Upgrader · v{self.VERSION}[/bold]\n\n"
            f"📁 Base dir   : {self.base_dir}\n"
            f"🎯 Modules    : {', '.join(self.modules)}\n"
            f"🧪 Mode       : {'DRY-RUN (不寫檔)' if self.dryrun else 'LIVE (寫 4-5 format)'}\n"
            f"📦 Formats    : Parquet={OUTPUT_PARQUET} · DuckDB={OUTPUT_DUCKDB} · CSV={OUTPUT_CSV} · JSON={OUTPUT_JSON} · GSheet={OUTPUT_GSHEET}"
        )
        if RICH_AVAILABLE:
            console.print(Panel(info, title="[bold blue]🔧 VDF Format Upgrader[/bold blue]", border_style="blue"))
        else:
            print(info)

    def _scan_module(self, mdl_key: str) -> Dict:
        """掃描單一 module 的輸出目錄."""
        cfg = MODULE_OUTPUT_MAP.get(mdl_key)
        if not cfg:
            return {"mdl": mdl_key, "status": "UNKNOWN", "tables": []}

        mod_dir = self.base_dir / cfg["output_dir"]
        if not mod_dir.exists():
            return {"mdl": mdl_key, "status": "DIR_NOT_FOUND",
                    "path": str(mod_dir), "tables": []}

        # 找所有 .parquet (優先) + .csv (補, 若沒 parquet)
        parquets = {p.stem: p for p in mod_dir.glob("*.parquet")
                     if not any(s in p.stem for s in SKIP_FILE_PATTERNS)}
        csvs     = {p.stem: p for p in mod_dir.glob("*.csv")
                     if not any(s in p.stem for s in SKIP_FILE_PATTERNS)
                     and p.stem not in parquets}

        tables = list(parquets.items()) + list(csvs.items())
        return {
            "mdl":     mdl_key,
            "status":  "FOUND" if tables else "EMPTY",
            "path":    str(mod_dir),
            "n_parquet": len(parquets),
            "n_csv":     len(csvs),
            "tables":  tables,
        }

    def _upgrade_table(self, mdl_key: str, table_name: str,
                       source_path: Path, mgr: OutputManager) -> Dict:
        """讀 1 個 parquet/csv, 用 OutputManager 重寫."""
        if not PANDAS_AVAILABLE:
            return {"table": table_name, "rows": 0, "error": "pandas missing"}

        try:
            if source_path.suffix == ".parquet":
                df = pd.read_parquet(source_path)
            elif source_path.suffix == ".csv":
                df = pd.read_csv(source_path, encoding="utf-8-sig")
            else:
                return {"table": table_name, "rows": 0, "error": f"unsupported {source_path.suffix}"}
        except Exception as e:
            return {"table": table_name, "rows": 0, "error": f"read fail: {str(e)[:100]}"}

        if df is None or df.empty:
            return {"table": table_name, "rows": 0, "error": "empty DataFrame"}

        if self.dryrun:
            return {"table": table_name, "rows": len(df), "outputs": [], "dryrun": True}

        save_result = mgr.save(table_name, df)
        return {
            "table":   table_name,
            "rows":    save_result["rows"],
            "outputs": save_result["outputs"],
            "source":  str(source_path.name),
        }

    def run(self) -> int:
        try:
            self.show_header()
            print(f"\n🔍 步驟 1/3: 掃描 {len(self.modules)} 個 module 輸出目錄")
            scans = [self._scan_module(m) for m in self.modules]
            for s in scans:
                ico = "✓" if s["status"] == "FOUND" else ("⚠" if s["status"] == "EMPTY" else "✗")
                n_p = s.get("n_parquet", 0); n_c = s.get("n_csv", 0)
                print(f"   {ico} {s['mdl']:<12} {s['status']:<14}  ({n_p}p + {n_c}c)  {s.get('path','')}")

            print(f"\n🔧 步驟 2/3: 升級各 table 多格式 (dryrun={self.dryrun})")
            for scan in scans:
                if scan["status"] != "FOUND":
                    self.module_stats[scan["mdl"]] = {"status": scan["status"],
                                                      "n_tables": 0, "details": []}
                    continue

                cfg = MODULE_OUTPUT_MAP[scan["mdl"]]
                if not OUTPUT_MGR_AVAILABLE:
                    print(f"   ✗ {scan['mdl']}: VDF_MDL101_OutputManager not importable, skip")
                    continue

                mgr = OutputManager(
                    base_dir         = str(self.base_dir),
                    output_dir       = cfg["output_dir"],
                    duckdb_filename  = cfg["duckdb_filename"],
                    enable_parquet   = OUTPUT_PARQUET,
                    enable_duckdb    = OUTPUT_DUCKDB,
                    enable_csv       = OUTPUT_CSV,
                    enable_json      = OUTPUT_JSON,
                    enable_gsheet    = OUTPUT_GSHEET,
                    respect_cli_flags= True,
                )
                tables_upgraded = []
                for tbl_name, src_path in scan["tables"]:
                    res = self._upgrade_table(scan["mdl"], tbl_name, src_path, mgr)
                    tables_upgraded.append(res)
                    self.results.append({"mdl": scan["mdl"], **res})
                self.module_stats[scan["mdl"]] = {
                    "status":    "UPGRADED" if not self.dryrun else "DRYRUN",
                    "n_tables":  len(tables_upgraded),
                    "details":   tables_upgraded,
                    "mgr_status": mgr.status_summary(),
                }
                # console feedback
                n_ok = sum(1 for r in tables_upgraded if not r.get("error"))
                print(f"   ✓ {scan['mdl']}: {n_ok}/{len(tables_upgraded)} tables 升級")

            print(f"\n📋 步驟 3/3: Rich Summary Matrix")
            self._print_rich_summary()

            elapsed = round(time.time() - self.start_time, 2)
            print(f"\n🎉 完成! 耗時 {elapsed}s")
            return 0
        except Exception as e:
            print(f"\n❌ 錯誤: {e}")
            import traceback; traceback.print_exc()
            return 1

    def _print_rich_summary(self):
        if not RICH_AVAILABLE: return
        console.rule("[bold cyan]🔧 VDF Format Upgrader · Upgrade Summary[/bold cyan]")

        # ─ Table 1: Module-level 升級狀態 ─
        t = Table(title="📦 [bold]Module 升級狀態[/bold]", box=box.ROUNDED, header_style="bold magenta")
        t.add_column("Module",    style="cyan",   width=14)
        t.add_column("狀態",      style="green",  width=14)
        t.add_column("輸出目錄",   style="yellow", width=38)
        t.add_column("Tables",    style="green",  width=10, justify="right")
        t.add_column("總列數",     style="green",  width=12, justify="right")
        t.add_column("檔案輸出",   style="yellow", width=24)
        for mdl in self.modules:
            stat = self.module_stats.get(mdl, {})
            cfg = MODULE_OUTPUT_MAP.get(mdl, {})
            details = stat.get("details", [])
            total_rows = sum(d.get("rows", 0) for d in details)
            mgr_st = stat.get("mgr_status", {})
            fmt_cnts = mgr_st.get("format_counts", {})
            fmt_str = " · ".join(f"{k}×{v}" for k, v in fmt_cnts.items()) or "—"
            st = stat.get("status", "—")
            st_color = "green" if st in ("UPGRADED",) else ("yellow" if st == "DRYRUN" else "red")
            t.add_row(mdl, f"[{st_color}]{st}[/{st_color}]",
                      cfg.get("output_dir", "?"),
                      str(stat.get("n_tables", 0)),
                      f"{total_rows:,}",
                      fmt_str)
        console.print(t)

        # ─ Table 2: Per-table 升級明細 ─
        if self.results:
            t = Table(title="📊 [bold]各 Table 升級明細[/bold]", box=box.ROUNDED, header_style="bold magenta")
            t.add_column("MDL",      style="cyan",   width=12)
            t.add_column("Table",    style="yellow", width=28)
            t.add_column("Source",   style="yellow", width=12)
            t.add_column("列數",     style="green",  width=10, justify="right")
            t.add_column("Parquet",  style="yellow", width=8,  justify="center")
            t.add_column("CSV",      style="yellow", width=8,  justify="center")
            t.add_column("JSON",     style="yellow", width=8,  justify="center")
            t.add_column("DuckDB",   style="yellow", width=8,  justify="center")
            t.add_column("GSheet",   style="yellow", width=8,  justify="center")
            for r in self.results:
                if r.get("error"):
                    t.add_row(r["mdl"], r["table"][:26], "—", "0",
                              "✗", "✗", "✗", "✗", "✗")
                else:
                    outputs = r.get("outputs", [])
                    fmts = {o.get("format"): ("✅" if "error" not in o else "❌")
                            for o in outputs}
                    src = r.get("source", "?")
                    src_short = src[-12:] if len(src) > 12 else src
                    t.add_row(r["mdl"], r["table"][:26], src_short, f"{r['rows']:,}",
                              fmts.get("parquet", "—"),
                              fmts.get("csv", "—"),
                              fmts.get("json", "—"),
                              fmts.get("duckdb", "—"),
                              fmts.get("gsheet", "—"))
            console.print(t)

        # ─ Final panel ─
        n_upg = sum(1 for s in self.module_stats.values() if s.get("status") == "UPGRADED")
        n_nf  = sum(1 for s in self.module_stats.values() if s.get("status") == "DIR_NOT_FOUND")
        total_tables = sum(s.get("n_tables", 0) for s in self.module_stats.values())
        total_rows = sum(d.get("rows", 0) for s in self.module_stats.values() for d in s.get("details", []))
        summary = (
            f"[bold]Modules upgraded[/bold]   : {n_upg} / {len(self.modules)}\n"
            f"[bold]Modules not found[/bold]  : {n_nf}\n"
            f"[bold]Tables upgraded[/bold]    : {total_tables}\n"
            f"[bold]Total rows[/bold]         : {total_rows:,}\n"
            f"[bold]Mode[/bold]               : {'DRYRUN' if self.dryrun else 'LIVE'}\n\n"
            f"[bold green]✅ Format Upgrade 完成[/bold green]"
        )
        console.print(Panel.fit(summary, title="[bold cyan]🎯 整體升級結果[/bold cyan]",
                                border_style="cyan"))


# =====================================================================================
# 🎯 Entry
# =====================================================================================

def main():
    print("🚀 VDF Format Upgrader 啟動...")
    eng = FormatUpgrader()
    return eng.run()


if __name__ == "__main__":
    try:
        ec = main()
        if "--no-pause" not in sys.argv:
            try: input("\n按 Enter 鍵退出...")
            except (EOFError, KeyboardInterrupt): pass
        sys.exit(ec)
    except KeyboardInterrupt:
        print("\n⚠️ 中斷"); sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未處理: {e}")
        sys.exit(1)
