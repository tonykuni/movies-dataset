# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-TST019 · test_VRN_OutputVerify · TEST =====
# AST 注入（只加註解，AST 不變）：類別 1 · 函式 15；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""Unit tests for VRN_OutputVerify v0100（輸出驗證與自動修正 · 2026-10-20 操作員「VRN-1 自動修正直到100%正確」）。"""
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
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine" / "VRN_OutputVerify_v0100.py"


# [VRN-ID] VRN-TST019-FNC001 · IO
def def_load():
    spec = importlib.util.spec_from_file_location("vrn_outputverify_test", str(ENGINE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


# [VRN-ID] VRN-TST019-FNC002 · LOGIC
def def_has(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


# [VRN-ID] VRN-TST019-CLS001 · CLASS
class def_OutputVerifyTests(unittest.TestCase):
    """每一筆輸出回原檔逐欄證明；能確定的才自動修正；證不出來不進輸出。"""

    # [VRN-ID] VRN-TST019-FNC003 · LOGIC
    @classmethod
    def setUpClass(cls):
        cls.V = def_load()

    # [VRN-ID] VRN-TST019-FNC004 · TEST
    def test_same_token_keeps_decimals_and_percent(self):
        V = self.V
        self.assertTrue(V.same_token("1,200", "1200"))
        self.assertTrue(V.same_token("(3,060)", "-3060"))
        self.assertFalse(V.same_token("6.1", "6.10"), "截斷的小數位不算同一個值")
        self.assertFalse(V.same_token("4.5%", "4.5"), "百分比和金額不是同一個值")

    # [VRN-ID] VRN-TST019-FNC005 · TEST
    def test_header_periods_split_quarters_from_annual(self):
        """KGI「季度 ∥ 年度」並排表頭：Mar/Jun/Sep/Dec-25A 是季、尾端逐年遞增的 Dec 是全年。"""
        got = self.V.header_periods("Mar-25A Jun-25A Sep-25A Dec-25A Mar-26A Dec-26F Dec-25A Dec-26F Dec-27F".split())
        self.assertEqual(got, [(2025, 1), (2025, 2), (2025, 3), (2025, 4), (2026, 1), (2026, 4), (2025, 0), (2026, 0), (2027, 0)])
        self.assertEqual(self.V.header_periods(["12/25", "12/26e", "1Q27E", "2026CT"]), [(2025, 0), (2026, 0), (2027, 1), (2026, 0)])

    # [VRN-ID] VRN-TST019-FNC006 · TEST
    def test_want_reads_the_rows_own_period(self):
        V = self.V
        self.assertEqual(V.want_of(2025, "2025-03", "FQ", "1Q25"), (2025, 1))
        self.assertEqual(V.want_of(2026, "", "FY", "2026F"), (2026, 0))
        self.assertIsNone(V.want_of(None, "", "", "T"), "期間字不明 → 不比（剔除）")

    # [VRN-ID] VRN-TST019-FNC007 · TEST
    def test_semantic_rejects_the_substring_mismaps(self):
        """資料庫引擎舊的子字串歸類：Net profit → TargetPrice、Cost of Sales → Revenue、Revenue 4.5% 當金額。"""
        V = self.V
        self.assertEqual(V.semantic("TargetPrice", "Net profit", "350")[0], False)
        self.assertEqual(V.semantic("Revenue", "Cost of Sales", "8,056")[0], False)
        self.assertEqual(V.semantic("Revenue", "Revenue", "4.5%")[0], False)
        self.assertEqual(V.semantic("GrossMargin", "Gross-profit margin", "22.9")[0], True)
        self.assertEqual(V.semantic("NetMargin", "Net income margin", "13.2")[0], True)

    # [VRN-ID] VRN-TST019-FNC008 · TEST
    def test_phone_numbers_are_not_year_headers(self):
        """「2022 2023 2024」表頭不是電話（晶心科：02220232024 是表頭拼出來的）。"""
        self.assertEqual(self.V._phones("百(萬元) 2022 2023 2024 2025F"), [])
        self.assertIn("0255691988", self.V._phones("台北市南港區 / (02) 5569-1988"))

    # [VRN-ID] VRN-TST019-FNC009 · TEST
    def test_half_line_numbers_are_the_same_row_only_when_nothing_else_claims_them(self):
        """凱基 3665 首頁：EV/EBITDA (x) 比它的數字低 4.6 pt，數字那一行左邊是分析師欄的人名（鄭宇宏）。"""
        V = self.V
        w = lambda t, x0, x1: {"text": t, "x0": x0, "x1": x1}  # noqa: E731
        lines = [{"y": 102.4, "h": 9.4, "words": [w("股價淨值比", 232, 274), w("(x)", 279, 292), w("10.4", 358, 373), w("8.3", 405, 416)]},
                 {"y": 95.3, "h": 8.5, "words": [w("鄭宇宏", 42, 68), w("38.0", 358, 373), w("25.1", 401, 416)]},
                 {"y": 90.7, "h": 8.1, "words": [w("EV/EBITDA", 232, 270), w("(x)", 275, 288)]},
                 {"y": 69.4, "h": 9.4, "words": [w("殖利率", 232, 257), w("(%)", 262, 275), w("0.6", 362, 373), w("0.8", 405, 416)]}]
        self.assertTrue(V.same_row(lines, 2, 1, 232, 358))
        self.assertFalse(V.same_row(lines, 2, 0, 232, 358), "數字那一行自己有科目 → 不是同一列")
        far = [dict(lines[0]), dict(lines[1], y=96.9), dict(lines[2], y=90.7), lines[3]]
        far[0]["y"] = 99.0
        self.assertFalse(V.same_row(far, 2, 1, 232, 358), "別的科目行離數字更近 → 不算")

    # [VRN-ID] VRN-TST019-FNC011 · TEST
    def test_section_rule_rejects_amounts_under_growth_or_percent_headings(self):
        """2026-10-20：MS 3661 第 10 頁 Growth(%) 底下的 Net profits 93.8、Margins (%) 底下的 Net Profit 12.4 都不是金額（段落標題借自 VRN-2）。"""
        V = self.V
        self.assertIs(V.section_semantic("NetIncome", "Growth(%)")[0], False)
        self.assertIs(V.section_semantic("NetIncome", "Margins (%)")[0], False)
        self.assertIs(V.section_semantic("Revenue", "QoQ Growth (%)")[0], False)
        self.assertIs(V.section_semantic("GrossMargin", "Margins (%)")[0], None, "比率科目在比率段落底下 → 不判")
        self.assertIs(V.section_semantic("NetIncome", "百萬元")[0], None, "混合單位 → 不判")
        self.assertIs(V.section_semantic("EPS", "每股盈餘 (NT$)")[0], None)
        self.assertIs(V.section_semantic("NetIncome", "P&L")[0], True)
        self.assertIs(V.section_semantic("NetIncome", "")[0], None)

    # [VRN-ID] VRN-TST019-FNC012 · TEST
    def test_label_unit_contradicts_an_amount_metric(self):
        """Codex PR #79 P1：Turnover (X) 是週轉率（倍數），19 份真報告 4 筆進了驗證過的營收；EPS (pre-tax) 不是 EPS。"""
        V = self.V
        self.assertIs(V.semantic("Revenue", "Turnover (X)", "0.4")[0], False)
        self.assertIs(V.semantic("Revenue", "Revenue (% YoY)", "12.0")[0], False)
        self.assertIs(V.semantic("EPS", "EPS (pre-tax)", "5.20")[0], False)
        self.assertIs(V.semantic("PER", "P/E (x)", "20.1")[0], True)
        self.assertIs(V.semantic("Revenue", "Revenue (NT$m)", "1,200")[0], True)

    # [VRN-ID] VRN-TST019-FNC013 · TEST
    def test_ticker_must_sit_in_a_ticker_position(self):
        """Codex PR #79 P2：四位數到處都是（年份 · 價格 · 表格值）。只認 2330.TW · 2330 TT · 6669TT · (3017) · 代號 2330。"""
        rx = self.V._ticker_rx
        for text in ("TSMC (2330.TW) Overweight", "Bloomberg 6669 TT revenue", "Wiwynn (6669TT- NT$3,300.00", "奇鋐(3017)",
                     "(2637.TW/2637 TT)", "股票代號：2330", "晶心科 (6533 TT) 中立"):
            tk = next(t for t in ("2330", "6669", "3017", "2637", "6533") if t in text)
            self.assertTrue(rx(tk).search(text), text)
        for tk, text in (("2025", "Revenue 2025 grew 31%"), ("1130", "Price NT$1130.0"), ("2330", "A 12330.TW peer"), ("2330", "電話 2330-1234")):
            self.assertFalse(rx(tk).search(text), text)

    # [VRN-ID] VRN-TST019-FNC014 · TEST
    def test_composite_summary_needs_ordered_runs_on_one_page(self):
        """Codex PR #79 P1：組合段落要切得成同一頁原文的連續片段；重排的字、跨頁拼的、沒上下文的數字 → 不過。"""
        V = self.V
        sq = V.squash
        p1 = sq("Demand trends for AI are strong with broader Analyst Jane Doe demand pickup and capacity likely to remain Price NT$1130.0")
        hays = [p1 + "\x00", sq("Margin outlook improves next year") + "\x00"]
        ok = V.tile_summary_text(sq("Demand trends for AI are strong with broader demand pickup and capacity Analyst Jane Doe"), hays)
        self.assertTrue(ok["ok"], ok)
        self.assertEqual(ok["page"], 1)
        self.assertFalse(V.tile_summary_text(sq("strong demand AI trends are with broader for pickup demand remain"), hays)["ok"], "重排")
        self.assertIn("不同頁", V.tile_summary_text(sq("Demand trends for AI are strong Margin outlook improves"), hays)["why"])
        self.assertIn("數字片段", V.tile_summary_text(sq("Demand trends for AI are strong with broader 1130 demand"), hays)["why"])

    # [VRN-ID] VRN-TST019-FNC015 · TEST
    @unittest.skipUnless(def_has("pandas") and def_has("pyarrow"), "pandas / pyarrow not installed")
    def test_table_written_again_without_parquet_keeps_no_old_parquet(self):
        """同一夾再寫一次、這一次寫不出 Parquet → 上一次的 Parquet 不能留著（_read_table 先讀 Parquet，會讀到舊值）。"""
        import tempfile
        from unittest import mock
        import pandas as pd
        V = self.V
        with tempfile.TemporaryDirectory() as td:
            folder = Path(td)
            self.assertTrue(V._write_table(folder, "t", [{"v": "old"}])["parquet"].endswith("t.parquet"))
            with mock.patch.object(pd.DataFrame, "to_parquet", side_effect=ImportError("no pyarrow")):
                info = V._write_table(folder, "t", [{"v": "new"}])
            self.assertIn("沒寫 Parquet", info["parquet"])
            self.assertFalse((folder / "t.parquet").exists())
            self.assertEqual(V._read_table(folder, "t")["v"].tolist(), ["new"])

    # [VRN-ID] VRN-TST019-FNC010 · TEST
    @unittest.skipUnless(def_has("fitz") and def_has("pandas") and def_has("pypdfium2") and def_has("pyarrow"), "PyMuPDF / pandas / pypdfium2 / pyarrow not installed")
    def test_selftest_known_answers(self):
        """引擎鎖的證明：畫一份已知答案的 PDF，對 · 錯期間 · 截斷 · 分組取到舊值 · 並排表 · 科目歸錯 · 原文沒有 · 期間不明 逐項對答案。"""
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = self.V.selftest()
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertNotIn("[FAIL]", buf.getvalue())
        self.assertNotIn("[SKIP]", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
