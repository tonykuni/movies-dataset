#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
================================================================================
  VDF_MDL101_OutputManager.py
================================================================================
  VERITAS DATA FRAMEWORK · 共用 5 格式輸出函式庫
  Version    : 1.0.0R  |  Module ID : VDF-OM-CORE

  重建R(2026-08-12 操作員「完成全部」令):工作站正本候上傳;本檔依 MDL102/301/302
  之呼叫契約重建(整合去重:正本到件即讓位)。契約:
    OutputManager(base_dir, output_dir, duckdb_filename, enable_*=True, respect_cli_flags)
    .save(name, df) → {"rows": n, "outputs": [{"format","path","size_kb"}|{"format","error"}]}
    .status_summary() → {"format_counts": {fmt: n}, "tables": [...]}
    空 DataFrame → rows 0 · outputs [](誠實空,不落檔)。
  格式:Parquet · DuckDB(單檔多表)· CSV utf-8-sig(BOM)· JSON records · GSheet(stub,
  需 GSHEET_CREDENTIAL_PATH+ID 才啟用;未配置=誠實略過不佔列)。
================================================================================
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
import json
import os
import sys
from pathlib import Path

try:
    import pyarrow  # noqa: F401
    PYARROW_AVAILABLE = True
except ImportError:
    PYARROW_AVAILABLE = False
try:
    import duckdb
    DUCKDB_AVAILABLE = True
except ImportError:
    DUCKDB_AVAILABLE = False
try:
    import gspread  # noqa: F401
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False

GSHEET_CREDENTIAL_PATH = os.environ.get("GSHEET_CREDENTIAL_PATH", "")
GSHEET_ID = os.environ.get("GSHEET_ID", "")


class OutputManager:
    """5 格式統一輸出。誠實原則:失敗列 error 不拋斷;空表零輸出。"""

    def __init__(self, base_dir, output_dir="output", duckdb_filename="vdf.duckdb",
                 enable_parquet=True, enable_duckdb=True, enable_csv=True,
                 enable_json=True, enable_gsheet=False, respect_cli_flags=True):
        self.base_dir = Path(base_dir)
        self.output_dir = self.base_dir / output_dir
        self.duckdb_path = self.output_dir / duckdb_filename
        self.enable = {"parquet": enable_parquet and PYARROW_AVAILABLE,
                       "duckdb": enable_duckdb and DUCKDB_AVAILABLE,
                       "csv": enable_csv, "json": enable_json,
                       "gsheet": (enable_gsheet and GSPREAD_AVAILABLE
                                  and bool(GSHEET_CREDENTIAL_PATH and GSHEET_ID))}
        if respect_cli_flags:
            for fmt in list(self.enable):
                if ("--no-%s" % fmt) in sys.argv:
                    self.enable[fmt] = False
        self._log = []  # [(table, fmt)] 成功紀錄 → status_summary

    # ── 單表五格式 ───────────────────────────────────────────────────────
    def save(self, name, df):
        result = {"table": name, "rows": 0 if df is None else len(df), "outputs": []}
        if df is None or len(df) == 0:
            return result  # 誠實空:不落檔
        self.output_dir.mkdir(parents=True, exist_ok=True)

        def _rec(fmt, path=None, err=None):
            if err:
                result["outputs"].append({"format": fmt, "error": str(err)[:120]})
            else:
                result["outputs"].append({"format": fmt, "path": str(path),
                                          "size_kb": max(1, path.stat().st_size // 1024)})
                self._log.append((name, fmt))

        if self.enable["parquet"]:
            p = self.output_dir / ("%s.parquet" % name)
            try:
                df.to_parquet(p, index=False)
                _rec("parquet", p)
            except Exception as e:
                _rec("parquet", err=e)
        if self.enable["csv"]:
            p = self.output_dir / ("%s.csv" % name)
            try:
                df.to_csv(p, index=False, encoding="utf-8-sig")
                _rec("csv", p)
            except Exception as e:
                _rec("csv", err=e)
        if self.enable["json"]:
            p = self.output_dir / ("%s.json" % name)
            try:
                d2 = df.copy()
                for c in d2.columns:  # datetime → ISO 字串(JSON 可攜)
                    if str(d2[c].dtype).startswith(("datetime", "timedelta")):
                        d2[c] = d2[c].astype(str)
                p.write_text(json.dumps(d2.where(d2.notna(), None).to_dict("records"),
                                        ensure_ascii=False, default=str), encoding="utf-8")
                _rec("json", p)
            except Exception as e:
                _rec("json", err=e)
        if self.enable["duckdb"]:
            try:
                con = duckdb.connect(str(self.duckdb_path))
                con.register("_df", df)
                con.execute('CREATE OR REPLACE TABLE "%s" AS SELECT * FROM _df' % name)
                con.close()
                _rec("duckdb", self.duckdb_path)
            except Exception as e:
                _rec("duckdb", err=e)
        if self.enable["gsheet"]:
            _rec("gsheet", err="stub:需 GSHEET_CREDENTIAL_PATH+GSHEET_ID 實接")
        return result

    def status_summary(self):
        counts = {}
        for _t, f in self._log:
            counts[f] = counts.get(f, 0) + 1
        return {"format_counts": counts,
                "tables": sorted({t for t, _f in self._log}),
                "duckdb_path": str(self.duckdb_path)}


if __name__ == "__main__":
    print("VDF_MDL101_OutputManager v1.0.0R · pyarrow=%s duckdb=%s gspread=%s"
          % (PYARROW_AVAILABLE, DUCKDB_AVAILABLE, GSPREAD_AVAILABLE))
