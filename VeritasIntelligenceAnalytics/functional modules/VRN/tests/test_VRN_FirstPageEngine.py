# -*- coding: utf-8 -*-
"""Unit tests for VIA_VRN_FirstPageEngine v0102 (stdlib only; PDF/DOCX paths are exercised by the auto-test loop)."""
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

import importlib.util
import json
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine" / "VIA_VRN_FirstPageEngine.py"
ORACLE = HERE.parent / "references" / "intake" / "VIA_SSOT_Additive_Audit_v0100" / "FILENAME_RESULTS.json"


def def_load():
    spec = importlib.util.spec_from_file_location("via_vrn_first_page_engine_test", str(ENGINE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def def_chars(lines):
    """Synthetic char dicts (pdfplumber shape) from (text, size) pairs."""
    chars = []
    top = 60.0
    for text, size in lines:
        x = 50.0
        for ch in text:
            chars.append({"text": ch, "x0": x, "top": top, "size": size, "fontname": "Regular"})
            x += size * (1.0 if ord(ch) > 255 else 0.55)
        top += size * 1.8
    return chars


class def_FirstPageEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = def_load()
        cls.engine = cls.module.FirstPageEngine()
        cls.tf = cls.engine.tf

    # ---- dates ------------------------------------------------------------------------
    def test_numeric_dates_follow_the_spec_table(self) -> None:
        tf = self.tf
        self.assertEqual(tf.numtoken_to_date("20250122"), "2025-01-22")
        self.assertEqual(tf.numtoken_to_date("1140122"), "2025-01-22")     # ROC 114
        self.assertEqual(tf.numtoken_to_date("250122"), "2025-01-22")
        self.assertIsNone(tf.numtoken_to_date("20250230"), "impossible calendar date")
        self.assertIsNone(tf.numtoken_to_date("926708"))
        self.assertEqual(tf.to_display("2025-01-22"), "2025/01/22")

    def test_parse_filename_protects_fragments(self) -> None:
        p = self.tf.parse_filename("凱基_神達3706 TT_初次評等_(20)260131_TargetPrice 168.pdf")
        self.assertEqual(p["tickers"], ["3706"])
        self.assertEqual(p["dates"], ["2026-01-31"])
        self.assertEqual(p["tricodes"][0]["platform"], "bloomberg")
        p = self.tf.parse_filename("第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf")
        self.assertEqual(p["tickers"], [])
        self.assertEqual(p["year_band"], ["2026"])
        self.assertEqual(p["dates"], ["2025-12-01"])
        p = self.tf.parse_filename("主動式ETF籌碼追蹤-CTBC0915.pdf")
        self.assertEqual(p["dates"], [])
        self.assertEqual(p["partial_dates"][0]["status"], "YEAR_MISSING")
        self.assertEqual((p["partial_dates"][0]["month"], p["partial_dates"][0]["day"]), (9, 15))
        p = self.tf.parse_filename("926708.jpg")
        self.assertEqual((p["tickers"], p["dates"]), ([], []))
        self.assertIn("926708", p["unclassified_numbers"])
        p = self.tf.parse_filename("006208 元大台灣50 20250122.pdf")
        self.assertEqual(p["etf"], ["006208"])
        self.assertEqual(p["dates"], ["2025-01-22"])
        p = self.tf.parse_filename("群益3Q26論壇_MIC_物理AI趨勢.pdf")
        self.assertEqual(p["quarters"][0]["period"], "2026-Q3")
        self.assertEqual(p["tickers"], [])
        p = self.tf.parse_filename("3014TT-20231005.pdf")
        self.assertEqual(p["tickers"], ["3014"])
        p = self.tf.parse_filename("2330.TW 台積電 2025-01-22.pdf")
        self.assertEqual(p["tricodes"][0]["market"], "TWSE")
        self.assertEqual(p["dates"], ["2025-01-22"])

    # ---- brokers ----------------------------------------------------------------------
    def test_company_fragment_after_the_code_is_not_the_broker(self) -> None:
        f = self.engine._filename_fields("凱基投顧_2891 中信金_施志鴻_20260519.pdf")
        self.assertEqual(f["broker"], "KGI")
        self.assertIn("中信金", f["parse"]["company_fragments"])
        f = self.engine._filename_fields("3653健策凱基投顧 向子慧 (3).txt")
        self.assertEqual(f["broker"], "KGI")
        f = self.engine._filename_fields("GFHK - Apple update 20260915.pdf")
        self.assertNotEqual(f["broker"], "GF", "GFHK stays unverified")
        f = self.engine._filename_fields("第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf")
        self.assertEqual(f["broker"], "HUANAN", "longest alias wins over 第一")

    def test_ascii_aliases_need_letter_boundaries(self) -> None:
        brd = self.engine.brd
        self.assertIsNone(brd.broker_normalize("thermal systems and earnings settings"))
        self.assertEqual(brd.broker_normalize("MS-1590 20251202"), "MS")
        self.assertEqual(brd.broker_normalize("260910_ms_iphone"), "MS")
        self.assertEqual(brd.broker_normalize("CLST-6669"), "CLSA")

    @unittest.skipUnless(ORACLE.is_file(), "audit package absent")
    def test_all_106_oracle_filenames_agree(self) -> None:
        rows = json.loads(ORACLE.read_text(encoding="utf-8-sig"))
        bad = []
        for row in rows:
            f = self.engine._filename_fields(row["filename"])
            exp = ((row.get("ticker_candidates") or [""])[0], row.get("report_date") or "", (row.get("broker") or {}).get("value") or "")
            got = (f["ticker"] or "", f["date"] or "", f["broker"] or "")
            if got != exp:
                bad.append((row["filename"], got, exp))
        self.assertEqual(bad, [])
        self.assertEqual(len(rows), 106)

    # ---- ratings ----------------------------------------------------------------------
    def test_rating_structures_short_codes_and_actions(self) -> None:
        brd = self.engine.brd
        self.assertIsNone(brd.validate_rating("光焱(7728,Note)-CTBC260918")["canonical"], "Note is a label, not NOT_RATED")
        self.assertEqual(brd.validate_rating("瑞基(4171,NR_未評等)-CTBC251208")["canonical"], "NOT_RATED")
        self.assertEqual(brd.validate_rating("晶心科(6533,N,中立)-CTBC251208")["canonical"], "HOLD")
        self.assertEqual(brd.validate_rating("啟碁(6285,OW_增加持股)-CTBC260915")["canonical"], "BUY")
        r = brd.validate_rating("維持中立評等，目標價 100 元")
        self.assertEqual((r["canonical"], r["action"]), ("HOLD", "MAINTAIN"))
        r = brd.validate_rating("投資評等：強力買進")
        self.assertEqual(r["canonical"], "BUY")
        self.assertEqual(brd.rating_matches("強力買進 target")[0]["fine"], "STRONG_BUY")
        self.assertIsNone(brd.rating_normalize("B"), "a single letter needs a rating structure")
        self.assertEqual(brd.rating_normalize("B", in_rating_field=True), "BUY")
        self.assertIsNone(brd.rating_normalize("please address the new flow"), "add/ew/ow inside words never match")

    def test_body_prose_is_only_a_hint_and_phone_numbers_are_not_tickers(self) -> None:
        lines = [("市場觀察家 週報", 18.0), ("報告日期：2026/09/15", 9.5),
                 ("分析師 王小明  analyst@example-research.com  (02)2181-8888", 8.5),
                 ("外資期貨淨部位小幅減碼，成交量能仍有支撐。", 10.0), ("資金流向 address 記憶體與散熱族群。", 10.0)]
        out = self.engine.run("20260916 市場觀察家.pdf", chars=def_chars(lines))
        self.assertEqual(out["ticker"]["ticker"], "")
        self.assertIsNone(out["rating"]["canonical"])
        self.assertEqual(out["rating"]["body_hint"], "SELL")
        self.assertEqual(out["report_date"], "2026-09-16", "filename date wins over the page date")
        self.assertEqual(out["report_date_source"], "FILENAME")
        self.assertEqual(out["page_date"], "2026-09-15")
        out = self.engine.run("市場觀察家.pdf", chars=def_chars(lines))
        self.assertEqual((out["report_date"], out["report_date_source"]), ("2026-09-15", "PAGE"))

    def test_stock_first_page_end_to_end(self) -> None:
        lines = [("凱基證券投資顧問  KGI Securities Research", 9.5),
                 ("神達(3706 TT)  營運動能延續，評價仍具吸引力", 19.5),
                 ("報告日期：2025/08/22    Bloomberg 3706 TT    Yahoo 3706.TW", 9.5),
                 ("投資評等：買進    目標價：NT$168.0    收盤價：NT$129.0", 12.5),
                 ("我們預估神達 2025 年稀釋 EPS 5.20 元。", 10.0), ("主要動能來自 AI 伺服器需求。", 10.0)]
        out = self.engine.run("KGI-3706 20250822.pdf", chars=def_chars(lines), official_market="TWSE")
        self.assertEqual(out["ticker"]["ticker"], "3706")
        self.assertEqual(out["rating"]["canonical"], "BUY")
        self.assertEqual(out["target_prices"]["primary"], 168.0)
        self.assertEqual(out["current_price"], 129.0)
        self.assertEqual(out["broker"], "KGI")
        self.assertEqual(out["tri_code"]["verdict"], "PASS")
        self.assertEqual(out["xv_filename_vs_page"]["verdict"], "PASS")
        self.assertEqual(out["upside"]["status"], "DERIVED")
        self.assertAlmostEqual(out["upside"]["upside_pct"], 30.23, places=2)
        self.assertTrue(out["summary_four_points"]["header"].startswith("神達(3706.TW)-") or "3706.TW" in out["summary_four_points"]["header"])
        self.assertIn("目標價 168.0", out["summary_four_points"]["points"][0]["text"])

    # ---- prices -----------------------------------------------------------------------
    def test_target_price_context_and_scenarios(self) -> None:
        fv = self.engine.fv
        self.assertEqual(fv.extract_target_price("上漲空間 30.4% 目標價 NT$168 元"), 168.0)
        self.assertEqual(fv.extract_target_price("Target Price (NT$) 1,250"), 1250.0)
        self.assertIsNone(fv.extract_target_price("target price upside 25%"))
        prices = fv.extract_target_prices("Base case NT$150, bull case 190, bear case 110; 目標價 150 元")
        self.assertEqual(prices["scenarios"], {"BASE": 150.0, "BULL": 190.0, "BEAR": 110.0})
        self.assertEqual(prices["primary"], 150.0)
        self.assertEqual(fv.extract_current_price("Target Price 168 收盤價 129"), 129.0)
        self.assertIsNone(fv.extract_current_price("Target Price 168"))

    def test_upside_needs_a_comparable_basis(self) -> None:
        price = self.engine.price
        self.assertEqual(price.upside_checked(130.0, 100.0)["upside_pct"], 30.0)
        self.assertEqual(price.upside_checked(130.0, 100.0, target_currency="USD")["status"], "BASIS_MISMATCH")
        self.assertEqual(price.upside_checked(None, 100.0)["status"], "UNDISCLOSED")

    # ---- cross checks and financial identities ---------------------------------------
    def test_tri_code_verdicts(self) -> None:
        tf = self.tf
        self.assertEqual(tf.cross_check("2330", yf="2330.TW", bbg="2330 TT")["verdict"], "PASS")
        self.assertEqual(tf.cross_check("2330", yf="2454.TW")["verdict"], "MISMATCH")
        self.assertEqual(tf.cross_check("2330", yf="2330.TWO", official_market="TWSE")["verdict"], "MARKET_MISMATCH")
        self.assertEqual(tf.cross_check("2330")["verdict"], "INSUFFICIENT_EVIDENCE")
        xv = self.engine.xv
        self.assertEqual(xv.tri_code("2330", [{"core": "2330"}])["verdict"], "PASS")
        self.assertEqual(xv.tri_code("", [])["verdict"], "N/A")

    def test_financial_identities_use_spec_tolerances(self) -> None:
        fin = self.engine.fin
        self.assertEqual(fin.balance_sheet(1000.0, 600.0, 400.004)["verdict"], "PASS")
        self.assertEqual(fin.balance_sheet(1000.0, 600.0, 380.0)["verdict"], "FAIL")
        self.assertEqual(fin.gross_profit(1000.0, 620.0, 380.0)["verdict"], "PASS")
        self.assertEqual(fin.margin(380.0, 1000.0, 38.0)["verdict"], "PASS")
        self.assertEqual(fin.diluted_eps(5200.0, 1000.0, 5.2)["verdict"], "PASS")
        self.assertEqual(fin.annual_equals_quarters(100.0, [25.0, 25.0, 25.0, 25.0])["verdict"], "PASS")
        self.assertEqual(fin.annual_equals_quarters(100.0, [25.0, 25.0, 25.0, 25.0], flow_item=False)["verdict"], "N/A")
        yoy = fin.historical_yoy([(2024, -10.0), (2025, 5.0)])
        self.assertEqual(yoy[0]["note"], "NEGATIVE_BASE")

    def test_nlp_repair_never_touches_numbers(self) -> None:
        nlp = self.engine.nlp
        self.assertEqual(nlp.repair_text("growth 10- 20% and EPS -2.5 (1,234)"), "growth 10- 20% and EPS -2.5 (1,234)")
        self.assertEqual(nlp.repair_text("semi- conductor demand"), "semiconductor demand")
        self.assertEqual(nlp.split_sentences("營收成長。EPS 2.5 元。Outlook remains strong. Next year"),
                         ["營收成長。", "EPS 2.5 元。", "Outlook remains strong.", "Next year"])

    def test_period_headers(self) -> None:
        cells = self.engine.tg.restore_period_header(["12/24A", "12/25E", "FY2026", "1Q25", "2025.Q1", "n/a"])
        self.assertEqual([c["period"] for c in cells], ["2024-12", "2025-12", "2026", "2025-Q1", "2025-Q1", None])
        self.assertEqual(cells[1]["kind"], "estimate")

    def test_cli_filename_mode(self) -> None:
        import contextlib
        import io
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            code = self.module.main(["--filename", "GS-2317 20251205.pdf", "--no-knowledge"])
        self.assertEqual(code, 0)
        payload = json.loads(buffer.getvalue())
        self.assertEqual(payload["ticker"]["ticker"], "2317")
        self.assertEqual(payload["report_date_display"], "2025/12/05")


if __name__ == "__main__":
    unittest.main()
