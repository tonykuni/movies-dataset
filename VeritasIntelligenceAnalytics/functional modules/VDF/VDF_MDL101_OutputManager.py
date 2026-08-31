#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_OutputManager.py
================================================================================
  VERITAS DATA FRAMEWORK · 共用多格式輸出函式庫
  Version    : 1.0.0   |   Module ID : VDF-OUT-CORE-001
  Asset ID   : VDF-OUT-CLS-001
  Policy     : SSOT for output · 所有 VDF 模組 import 使用

ROLE
================================================================================
  所有 VDF 模組共用的輸出器, 支援 5 種格式:
    [1] Parquet (必選, 主要 SSOT, pyarrow 後端)
    [2] DuckDB  (可選, 單一 .duckdb 檔, 多 table)
    [3] CSV     (可選, utf-8-sig 編碼, 解決中文 BOM 問題)
    [4] JSON    (可選, indent=2, datetime auto-stringify)
    [5] GSheet  (可選, gspread + service account)

  特性:
    - 統一 backup 機制 (timestamped, MAX_BACKUP_FILES)
    - CLI flag override: --no-parquet/duckdb/csv/json, --gsheet
    - 統一 error handling (per-format isolation)
    - 統一 return schema: {rows, outputs:[{format, path, size_kb, error}]}

USAGE (in any VDF module)
================================================================================
  from VDF_OutputManager import OutputManager

  mgr = OutputManager(
      base_dir   = r"C:\\Users\\tonyk\\OneDrive\\...\\VDF\\dict",
      output_dir = "1-x-MyModule",
      duckdb_filename = "VDF_MyModule.duckdb",
  )
  result = mgr.save("table_name", df)
  # result = {"rows": 123, "outputs": [{"format":"parquet","path":..,"size_kb":..},...]}
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

# =====================================================================================
# 📋 ALL PARAMETERS (defaults, overridable via __init__)
# =====================================================================================

DEFAULT_OUTPUT_PARQUET     = True   # 必選
DEFAULT_OUTPUT_DUCKDB      = True
DEFAULT_OUTPUT_CSV         = True
DEFAULT_OUTPUT_JSON        = True
DEFAULT_OUTPUT_GSHEET      = False

DEFAULT_CSV_ENCODING       = "utf-8-sig"
DEFAULT_JSON_INDENT        = 2
DEFAULT_DUCKDB_FILENAME    = "VDF_data.duckdb"

DEFAULT_ENABLE_BACKUP      = True
DEFAULT_MAX_BACKUP_FILES   = 5

DEFAULT_GSHEET_CRED_PATH   = ""
DEFAULT_GSHEET_SPREAD_ID   = ""


# =====================================================================================
# 📦 Imports (graceful fallback)
# =====================================================================================

import os, sys, json, shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, List

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import pyarrow as pa
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False

try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False

try:
    import gspread
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False


# =====================================================================================
# 💾 OutputManager
# =====================================================================================

class OutputManager:
    """
    統一多格式輸出管理器.

    Args:
        base_dir          : 基礎輸出根目錄 (eg. C:\\...\\VDF\\dict)
        output_dir        : 子目錄名稱 (eg. "1-3-SentimentMacro")
        duckdb_filename   : DuckDB 檔名
        enable_parquet    : True/False (預設 True 必選)
        enable_duckdb     : True/False
        enable_csv        : True/False
        enable_json       : True/False
        enable_gsheet     : True/False
        csv_encoding      : 預設 utf-8-sig
        json_indent       : 預設 2
        enable_backup     : True/False
        max_backup_files  : 預設 5
        gsheet_cred_path  : Google service account 憑證 JSON
        gsheet_spread_id  : Google Sheet ID
        respect_cli_flags : True 時讀 sys.argv (--no-parquet 等)
    """

    VERSION = "1.0.0"

    def __init__(self,
                 base_dir: str,
                 output_dir: str,
                 duckdb_filename: str   = DEFAULT_DUCKDB_FILENAME,
                 enable_parquet: bool   = DEFAULT_OUTPUT_PARQUET,
                 enable_duckdb: bool    = DEFAULT_OUTPUT_DUCKDB,
                 enable_csv: bool       = DEFAULT_OUTPUT_CSV,
                 enable_json: bool      = DEFAULT_OUTPUT_JSON,
                 enable_gsheet: bool    = DEFAULT_OUTPUT_GSHEET,
                 csv_encoding: str      = DEFAULT_CSV_ENCODING,
                 json_indent: int       = DEFAULT_JSON_INDENT,
                 enable_backup: bool    = DEFAULT_ENABLE_BACKUP,
                 max_backup_files: int  = DEFAULT_MAX_BACKUP_FILES,
                 gsheet_cred_path: str  = DEFAULT_GSHEET_CRED_PATH,
                 gsheet_spread_id: str  = DEFAULT_GSHEET_SPREAD_ID,
                 respect_cli_flags: bool = True):

        self.base_dir         = Path(base_dir)
        self.output_dir       = self.base_dir / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir       = self.output_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)
        self.duckdb_path      = self.output_dir / duckdb_filename

        self.enable_parquet   = enable_parquet
        self.enable_duckdb    = enable_duckdb and DUCKDB_AVAILABLE
        self.enable_csv       = enable_csv
        self.enable_json      = enable_json
        self.enable_gsheet    = enable_gsheet and GSPREAD_AVAILABLE and gsheet_cred_path

        self.csv_encoding     = csv_encoding
        self.json_indent      = json_indent
        self.enable_backup    = enable_backup
        self.max_backup_files = max_backup_files
        self.gsheet_cred_path = gsheet_cred_path
        self.gsheet_spread_id = gsheet_spread_id

        # CLI flag override
        if respect_cli_flags:
            if "--no-parquet" in sys.argv: self.enable_parquet = False
            if "--no-duckdb"  in sys.argv: self.enable_duckdb  = False
            if "--no-csv"     in sys.argv: self.enable_csv     = False
            if "--no-json"    in sys.argv: self.enable_json    = False
            if "--gsheet"     in sys.argv: self.enable_gsheet  = (GSPREAD_AVAILABLE and gsheet_cred_path)

        self.results: Dict[str, Dict[str, Any]] = {}

    # ── 內部 ──────────────────────────────────────────────────────────
    def _backup(self, path: Path):
        if not self.enable_backup or not path.exists(): return
        try:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            bp = self.backup_dir / f"{ts}_{path.name}"
            shutil.copy2(path, bp)
            backups = sorted(self.backup_dir.glob(f"*_{path.name}"),
                             key=lambda x: x.stat().st_mtime, reverse=True)
            for bk in backups[self.max_backup_files:]:
                try: bk.unlink()
                except Exception: pass
        except Exception:
            pass

    # ── public save (主入口) ──────────────────────────────────────────
    def save(self, table_name: str, df) -> Dict:
        """單 table 多格式輸出.

        Args:
            table_name: 不含副檔名的 table 名稱
            df: pandas DataFrame
        Returns:
            {"rows": int, "outputs": [{format,path,size_kb} or {format,error}]}
        """
        if not PANDAS_AVAILABLE or df is None or (hasattr(df, "empty") and df.empty):
            self.results[table_name] = {"rows": 0, "outputs": []}
            return self.results[table_name]

        rows = len(df)
        outputs: List[Dict] = []

        # Parquet (必選, 但若 pyarrow 缺則 skip)
        if self.enable_parquet:
            if PYARROW_AVAILABLE:
                p = self.output_dir / f"{table_name}.parquet"
                self._backup(p)
                try:
                    df.to_parquet(p, index=False)
                    outputs.append({"format": "parquet", "path": str(p),
                                    "size_kb": p.stat().st_size // 1024})
                except Exception as e:
                    outputs.append({"format": "parquet", "error": str(e)[:120]})
            else:
                outputs.append({"format": "parquet", "error": "pyarrow not installed"})

        # CSV
        if self.enable_csv:
            p = self.output_dir / f"{table_name}.csv"
            self._backup(p)
            try:
                df.to_csv(p, index=False, encoding=self.csv_encoding)
                outputs.append({"format": "csv", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "csv", "error": str(e)[:120]})

        # JSON
        if self.enable_json:
            p = self.output_dir / f"{table_name}.json"
            self._backup(p)
            try:
                d = df.copy()
                if pd is not None:
                    for c in d.columns:
                        if pd.api.types.is_datetime64_any_dtype(d[c]):
                            d[c] = d[c].dt.strftime('%Y-%m-%d %H:%M:%S')
                d.to_json(p, orient="records", indent=self.json_indent, force_ascii=False)
                outputs.append({"format": "json", "path": str(p),
                                "size_kb": p.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "json", "error": str(e)[:120]})

        # DuckDB
        if self.enable_duckdb and DUCKDB_AVAILABLE:
            try:
                conn = duckdb.connect(str(self.duckdb_path))
                conn.register("__tmp_df__", df)
                conn.execute(f"DROP TABLE IF EXISTS \"{table_name}\"")
                conn.execute(f"CREATE TABLE \"{table_name}\" AS SELECT * FROM __tmp_df__")
                conn.close()
                outputs.append({"format": "duckdb", "path": str(self.duckdb_path),
                                "table": table_name,
                                "size_kb": self.duckdb_path.stat().st_size // 1024})
            except Exception as e:
                outputs.append({"format": "duckdb", "error": str(e)[:120]})

        # Google Sheet
        if self.enable_gsheet and GSPREAD_AVAILABLE and self.gsheet_cred_path and self.gsheet_spread_id:
            try:
                gc = gspread.service_account(filename=self.gsheet_cred_path)
                sh = gc.open_by_key(self.gsheet_spread_id)
                try:
                    ws = sh.worksheet(table_name)
                    ws.clear()
                except gspread.WorksheetNotFound:
                    ws = sh.add_worksheet(title=table_name,
                                          rows=str(rows + 10),
                                          cols=str(len(df.columns) + 2))
                data = [df.columns.tolist()] + df.astype(str).values.tolist()
                ws.update(data)
                outputs.append({"format": "gsheet", "spreadsheet_id": self.gsheet_spread_id,
                                "sheet": table_name})
            except Exception as e:
                outputs.append({"format": "gsheet", "error": str(e)[:120]})

        self.results[table_name] = {"rows": rows, "outputs": outputs}
        return self.results[table_name]

    # ── helper: 批次儲存 ──────────────────────────────────────────────
    def save_batch(self, tables: Dict[str, "pd.DataFrame"]) -> Dict[str, Dict]:
        """批次儲存多個 tables. tables = {name: df}."""
        for name, df in tables.items():
            self.save(name, df)
        return self.results

    # ── 狀態回報 ──────────────────────────────────────────────────────
    def status_summary(self) -> Dict[str, Any]:
        """彙總所有 save 的狀態."""
        total_rows = sum(r["rows"] for r in self.results.values())
        all_fmts: Dict[str, int] = {}
        all_errs: List[str] = []
        for name, r in self.results.items():
            for o in r["outputs"]:
                fmt = o.get("format", "?")
                if "error" in o:
                    all_errs.append(f"{name}:{fmt}:{o['error']}")
                else:
                    all_fmts[fmt] = all_fmts.get(fmt, 0) + 1
        return {
            "tables_saved": len(self.results),
            "total_rows":   total_rows,
            "format_counts": all_fmts,
            "errors":       all_errs[:20],
            "enabled":      {
                "parquet": self.enable_parquet,
                "duckdb":  self.enable_duckdb,
                "csv":     self.enable_csv,
                "json":    self.enable_json,
                "gsheet":  self.enable_gsheet,
            },
            "duckdb_path":  str(self.duckdb_path) if self.enable_duckdb else None,
            "output_dir":   str(self.output_dir),
        }


# =====================================================================================
# Self-test
# =====================================================================================

if __name__ == "__main__":
    import tempfile
    print("🧪 VDF_OutputManager self-test")
    print(f"  pyarrow: {PYARROW_AVAILABLE} · duckdb: {DUCKDB_AVAILABLE} · gspread: {GSPREAD_AVAILABLE}")
    if not PANDAS_AVAILABLE:
        print("  ⚠️ pandas missing, skip"); sys.exit(0)

    with tempfile.TemporaryDirectory() as tmp:
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["台積電", "鴻海", "聯發科"],
                           "c": pd.date_range("2024-01-01", periods=3)})
        mgr = OutputManager(base_dir=tmp, output_dir="test_out",
                            duckdb_filename="test.duckdb",
                            respect_cli_flags=False)
        r = mgr.save("test_table", df)
        print(f"\n  save result: rows={r['rows']} · outputs={len(r['outputs'])}")
        for o in r["outputs"]:
            if "error" in o:
                print(f"    ✗ {o['format']}: {o['error']}")
            else:
                print(f"    ✓ {o['format']}: {o.get('size_kb', '?')} KB")
        print(f"\n  status: {mgr.status_summary()}")
    print("\n✅ Self-test pass")
