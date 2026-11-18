# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST020 · test_VRN_PivotDB · TEST =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 12；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""Unit tests for VRN_PivotDB v0100（驗證過的還原表格 → 資料庫形式 PIVOT · 2026-10-20 操作員「還原後表格可改為資料庫形式 PIVOT」）。"""
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

import contextlib
import importlib.util
import io
import sqlite3
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine" / "VRN_PivotDB_v0100.py"


# [VRN-ID] VRN-TST020-FNC001 · IO
def def_load():
    spec = importlib.util.spec_from_file_location("vrn_pivotdb_test", str(ENGINE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# [VRN-ID] VRN-TST020-CLS001 · CLASS
class def_PivotDBTests(unittest.TestCase):
    """只收證實過的格；同格不同值留空列衝突；印的位數不同的同一個數取最細；SQLite 一定寫得出來。"""

    # [VRN-ID] VRN-TST020-FNC002 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.P = def_load()

    # [VRN-ID] VRN-TST020-FNC003 · LOGIC
    def fact(self, metric, fy, value, raw, table="T1", status="VERIFIED", fq="", ptype="FY", mraw=None):
        P = self.P
        return {"system": "VRN-1", "file": "a.pdf", "ticker": "2330", "broker": "B", "report_date": "2026-01-01", "page": "3", "table_id": table,
                "metric": metric, "metric_raw": mraw or metric, "unit": "NT$m", "period_key": P.period_key(fy, fq, ptype), "period_label": "",
                "period_type": ptype, "fiscal_year": str(fy), "fiscal_quarter": fq, "estimate_flag": "", "value": value, "value_raw": raw,
                "status": status, "note": "", "source_id": "%s%s%s" % (metric, fy, table)}

    # [VRN-ID] VRN-TST020-FNC004 · LOGIC
    def query(self, db, sql):
        con = sqlite3.connect(db)
        try:
            return con.execute(sql).fetchall()
        finally:
            con.close()

    # [VRN-ID] VRN-TST020-FNC005 · TEST
    def test_period_key_shapes(self):
        P = self.P
        self.assertEqual(P.period_key(2025, "", "FY"), "2025")
        self.assertEqual(P.period_key(2025, "2025-06", "FQ"), "2025-06")
        self.assertEqual(P.period_key(None, "", "TTM"), "")
        self.assertEqual(P.period_order("2025-03") < P.period_order("2025"), True)

    # [VRN-ID] VRN-TST020-FNC006 · TEST
    def test_half_ulp_follows_the_printed_digits(self):
        P = self.P
        self.assertEqual(P.half_ulp("4,458", 4458.0), 0.5)
        self.assertAlmostEqual(P.half_ulp("4,457.8", 4457.8), 0.05)
        self.assertEqual(P.half_ulp("4.5bn", 4500.0), 0.0)            # 原字和值對不上（換算過）→ 只認完全相同
        self.assertEqual(P.half_ulp("(12.30)", -12.3), 0.005)

    # [VRN-ID] VRN-TST020-FNC007 · TEST
    def test_precision_merge_and_conflict(self):
        P = self.P
        facts = [self.fact("NetIncome", 2025, 4458.0, "4,458"), self.fact("NetIncome", 2025, 4457.8, "4,457.8", table="T2"),
                 self.fact("OpIncome", 2025, 4458.0, "4,458"), self.fact("OpIncome", 2025, 4457.4, "4,457.4", table="T2"),
                 self.fact("Revenue", 2025, 99.0, "99", status="REJECTED")]
        with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
            s = P.build_pivot_db(facts, td)
            db = s["sqlite"]
            self.assertEqual(self.query(db, "SELECT \"2025\" FROM pivot_report_annual WHERE metric='NetIncome'"), [(4457.8,)])
            self.assertEqual(self.query(db, "SELECT \"2025\" FROM pivot_report_annual WHERE metric='OpIncome'"), [(None,)])
            self.assertEqual(self.query(db, "SELECT count(*) FROM conflicts"), [(1,)])
            self.assertEqual(self.query(db, "SELECT count(*) FROM precision_merges"), [(1,)])
            self.assertEqual(self.query(db, "SELECT count(*) FROM pivot_report_annual WHERE metric='Revenue'"), [(0,)])
            self.assertEqual(s["counts"]["facts"], 5)
            self.assertEqual(s["counts"]["kept"], 4)

    # [VRN-ID] VRN-TST020-FNC008 · TEST
    def test_printed_label_keeps_rows_apart(self):
        P = self.P
        facts = [self.fact("EPS", 2025, 6.1, "6.1", mraw="EPS (NT$)**"), self.fact("EPS", 2025, 6.3, "6.3", table="T2", mraw="EPS (NT$)§")]
        with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
            s = P.build_pivot_db(facts, td)
            self.assertEqual(s["counts"]["conflicts"], 0)
            self.assertEqual(s["counts"]["pivot_report_annual"], 2)

    # [VRN-ID] VRN-TST020-FNC009 · TEST
    def test_contract_mismatch_refuses_to_write(self):
        P = self.P
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(ValueError):
                P.build_pivot_db([{"file": "x"}], Path(td) / "out")
            self.assertFalse((Path(td) / "out").exists())

    # [VRN-ID] VRN-TST020-FNC010 · TEST
    def test_html_names_the_system_and_is_safe(self):
        P = self.P
        facts = [self.fact("Revenue", 2025, 1.0, "1", mraw="</script><b>x")]
        with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
            s = P.build_pivot_db(facts, td)
            page = Path(s["html"]).read_text(encoding="utf-8")
            self.assertIn("VRN-1 PIVOT 資料庫", page)
            self.assertEqual(page.count("</script>"), 2)

    # [VRN-ID] VRN-TST020-FNC012 · TEST
    def test_rebuild_without_parquet_or_duckdb_keeps_no_old_file(self):
        """同一夾（VRN-2 的 pivot 夾一直沿用）再建一次、這一次寫不出 Parquet 也沒有 duckdb → 夾裡不能留上一次的舊檔。"""
        import sys
        from unittest import mock
        try:
            import pandas as pd
        except ImportError:
            self.skipTest("pandas not installed")
        P = self.P
        with tempfile.TemporaryDirectory() as td, contextlib.redirect_stdout(io.StringIO()):
            out = Path(td)
            (out / "facts.parquet").write_bytes(b"old")                  # 上一次留下的舊檔
            (out / P.DUCK_NAME).write_bytes(b"old")
            with mock.patch.object(pd.DataFrame, "to_parquet", side_effect=ImportError("no pyarrow")), \
                    mock.patch.dict(sys.modules, {"duckdb": None}):      # None = import duckdb 會丟 ImportError
                s = P.build_pivot_db([self.fact("Revenue", 2025, 9.0, "9")], out)
            self.assertFalse((out / "facts.parquet").exists())
            self.assertFalse((out / P.DUCK_NAME).exists())
            self.assertEqual(s["duckdb"], "")
            self.assertTrue((out / "facts.csv").is_file())

    # [VRN-ID] VRN-TST020-FNC011 · TEST
    def test_selftest_passes(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.P.selftest(verbose=False), 0)


if __name__ == "__main__":
    unittest.main()
