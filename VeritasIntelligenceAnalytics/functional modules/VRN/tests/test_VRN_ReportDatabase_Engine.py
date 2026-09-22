# -*- coding: utf-8 -*-
"""Unit tests for VRN_Integrated_ReportDatabase_Engine v0101 (stdlib parts always run; pandas/pyarrow parts skip when absent)."""
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

import argparse
import contextlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE.parent / "engine" / "VRN_Integrated_ReportDatabase_Engine.py"
ORACLE = HERE.parent / "references" / "intake" / "VIA_SSOT_Additive_Audit_v0100" / "FILENAME_RESULTS.json"


def def_load():
    spec = importlib.util.spec_from_file_location("vrn_report_database_engine_test", str(ENGINE))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def def_has(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):
        return False


SAMPLE_TXT = """凱基證券投資顧問  KGI Securities Research
神達(3706 TT)  營運動能延續，評價仍具吸引力
報告日期：2025/08/22    Bloomberg 3706 TT    Yahoo 3706.TW
投資評等：買進    目標價：NT$168.0    收盤價：NT$129.0
分析師 王小明  analyst@example-research.com  (02)2181-8888
我們預估神達 2025 年稀釋 EPS 5.20 元，2026 年 6.10 元。
"""


class def_ReportDatabaseEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.db = def_load()
        cls.broker_alias = cls.db.load_broker_alias_ssot(None)
        cls.rating_alias = cls.db.load_rating_alias_ssot(None)

    def test_built_in_self_test_passes(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            self.db.run_self_test()

    def test_scan_accepts_pdf_docx_txt_and_images(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vrn-scan-") as temporary:
            root = Path(temporary)
            for name in ("a.pdf", "b.docx", "c.txt", "d.jpg", "e.xlsx", "sub/f.PDF"):
                path = root / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"x")
            names = [p.name for p in self.db.scan_input_files(root)]
        self.assertEqual(sorted(names), ["a.pdf", "b.docx", "c.txt", "d.jpg", "f.PDF"])

    def test_dates_follow_the_spec_table(self) -> None:
        db = self.db
        self.assertEqual(db.parse_date_any("1140122"), "2025-01-22")
        self.assertEqual(db.parse_date_any("2025/01/22"), "2025-01-22")
        self.assertEqual(db.parse_date_any("2026/09/11"), "2026-09-11", "two-digit day must not be cut to one digit")
        self.assertIsNone(db.parse_date_any("20250230"))
        self.assertIsNone(db.parse_date_any("926708"))
        self.assertEqual(db.parse_date_candidates_from_number_tokens(["006208"]), [])
        joined = db.parse_date_candidates_from_number_tokens(["20", "260131"])
        self.assertTrue(any(c["kind"] == "PREFIX_YYYYMMDD" and c["date"] == "2026-01-31" for c in joined))
        partial = db.parse_partial_dates_from_filename("主動式ETF籌碼追蹤-CTBC0915")
        self.assertEqual((partial[0]["month"], partial[0]["day"], partial[0]["status"]), (9, 15, "YEAR_MISSING"))

    def test_year_band_and_etf_are_not_tickers(self) -> None:
        db = self.db
        ti = db.tokenize_filename("第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf")
        cands = db.extract_filename_ticker_candidates(ti, {})
        self.assertEqual([c["ticker"] for c in cands if c["ticker"]], [])
        self.assertTrue(any(c.get("status") == "YEAR_BAND" for c in cands))
        ti = db.tokenize_filename("006208 元大台灣50.pdf")
        cands = db.extract_filename_ticker_candidates(ti, {})
        self.assertTrue(any(c.get("status") == "ETF_CANDIDATE" for c in cands))
        page = db.extract_text_ticker_candidates("報告日期 2026/09/15 神達(3706) 電話 (02)2181-8888 營收 1500 百萬", "first_page", {})
        self.assertEqual({c["ticker"] for c in page}, {"3706"})

    def test_broker_token_hit_beats_page_text_hit(self) -> None:
        db = self.db
        ti = db.tokenize_filename("第一場 2026年投資大趨勢 - 華南投顧 -1141201.pdf")
        broker, _, matches = db.match_broker_from_tokens_and_text(
            ti["chinese_tokens"], ti["english_tokens"], "HUANAN Securities Research 第一場", self.broker_alias)
        self.assertEqual(broker, "HUANAN", matches)
        ti = db.tokenize_filename("凱基投顧_2891 中信金_施志鴻_20260519.pdf")
        frags = db.company_fragments_after_ticker(ti["tokens"])
        broker, _, _ = db.match_broker_from_tokens_and_text(ti["chinese_tokens"], ti["english_tokens"], "", self.broker_alias, frags)
        self.assertEqual(broker, "KGI")
        broker, _, _ = db.match_broker_from_tokens_and_text([], [], "thermal systems and earnings", self.broker_alias)
        self.assertEqual(broker, "")
        self.assertEqual(db.canonical_broker_key("Morgan Stanley"), "MS")
        self.assertEqual(db.canonical_broker_key("JPMorgan"), "JPM")

    def test_rating_rules(self) -> None:
        db = self.db
        self.assertEqual(db.extract_rating("光焱(7728,Note)-CTBC260918", self.rating_alias)[0], "")
        self.assertEqual(db.extract_rating("瑞基(4171,NR_未評等)-CTBC251208", self.rating_alias)[0], "NOT_RATED")
        self.assertEqual(db.extract_rating("投資評等：OW", self.rating_alias)[0], "BUY")
        self.assertEqual(db.extract_rating("維持中立評等", self.rating_alias)[0], "HOLD")
        self.assertEqual(db.extract_rating("please address the new flow", self.rating_alias)[0], "")
        rating, matches = db.extract_rating("投資評等：強力買進", self.rating_alias)
        self.assertEqual(rating, "BUY")
        self.assertTrue(any(m.get("fine") == "STRONG_BUY" for m in matches))
        self.assertEqual(db.extract_rating_change("維持買進評等"), "MAINTAIN")

    def test_target_and_current_price(self) -> None:
        db = self.db
        self.assertEqual(db.extract_target_price("上漲空間 30.4% 目標價 NT$168 元"), 168.0)
        self.assertEqual(db.extract_target_price("12-month price target NT$1,250"), 1250.0)
        self.assertIsNone(db.extract_target_price("target price upside 25%"))
        self.assertEqual(db.extract_current_price("Target Price 168 收盤價 129"), 129.0)
        self.assertEqual(db.extract_target_price_scenarios("Base case 150, bull case 190 and bear case 110"),
                         {"BASE": 150.0, "BULL": 190.0, "BEAR": 110.0})
        self.assertEqual(db.calculate_upside_downside(168.0, 129.0), round((168.0 / 129.0 - 1) * 100, 4))

    def test_period_labels(self) -> None:
        db = self.db
        self.assertEqual((db.parse_period_label("12/24A")["FiscalYear"], db.parse_period_label("12/24A")["EstimateFlag"]), (2024, "Actual"))
        self.assertEqual((db.parse_period_label("FY2025")["FiscalYear"], db.parse_period_label("FY2025")["EstimateFlag"]), (2025, ""))
        self.assertEqual(db.parse_period_label("2025E")["EstimateFlag"], "Estimate")
        self.assertEqual((db.parse_period_label("2025.Q1")["FiscalYear"], db.parse_period_label("2025.Q1")["FiscalQuarter"]), (2025, "Q1"))
        self.assertEqual((db.parse_period_label("3Q26")["FiscalYear"], db.parse_period_label("3Q26")["FiscalQuarter"]), (2026, "Q3"))
        self.assertEqual(db.parse_period_label("Revenue")["FiscalYear"], None)

    def test_header_row_needs_period_cells(self) -> None:
        db = self.db
        rows = [["項目", "2024A", "2025E"], ["營收", "100", "120"], ["EPS", "3.1", "4.2"]]
        self.assertEqual(db.find_best_header_row(rows), 0)
        self.assertIsNone(db.find_best_header_row([["a", "b"], ["1", "2"]]))

    def test_tri_code_verdict(self) -> None:
        db = self.db
        fn = [{"ticker": "3706"}]
        self.assertEqual(db.tri_code_verdict(fn, [{"ticker": "3706", "kind": "bloomberg"}]), "PASS")
        self.assertEqual(db.tri_code_verdict(fn, [{"ticker": "2330", "kind": "yfinance"}]), "MISMATCH")
        self.assertEqual(db.tri_code_verdict(fn, []), "INSUFFICIENT_EVIDENCE")
        self.assertEqual(db.tri_code_verdict([], []), "N/A")

    @unittest.skipUnless(ORACLE.is_file(), "audit package absent")
    def test_all_106_oracle_filenames_agree(self) -> None:
        db = self.db
        rows = json.loads(ORACLE.read_text(encoding="utf-8-sig"))
        bad = []
        for row in rows:
            name = row["filename"]
            ti = db.tokenize_filename(name)
            cands = [c["ticker"] for c in db.extract_filename_ticker_candidates(ti, {}) if c["ticker"]]
            dates = db.parse_date_candidates_from_number_tokens(ti["number_tokens"])
            frags = db.company_fragments_after_ticker(ti["tokens"])
            broker, _, _ = db.match_broker_from_tokens_and_text(ti["chinese_tokens"], ti["english_tokens"], "", self.broker_alias, frags)
            got = ((cands or [""])[0], dates[0]["date"] if dates else "", broker or "")
            exp = ((row.get("ticker_candidates") or [""])[0], row.get("report_date") or "", (row.get("broker") or {}).get("value") or "")
            if got != exp:
                bad.append((name, got, exp))
        self.assertEqual(bad, [])

    def test_txt_extraction_is_stdlib(self) -> None:
        with tempfile.TemporaryDirectory(prefix="vrn-txt-") as temporary:
            path = Path(temporary) / "KGI-3706 20250822.txt"
            path.write_text(SAMPLE_TXT, encoding="utf-8")
            info = self.db.extract_document_text_and_zones(path)
        self.assertEqual(info["engine"], "text")
        self.assertIn("目標價", info["first_page_text"])

    def test_online_name_table_needs_consent(self) -> None:
        import os
        saved = os.environ.pop("VIA_NET", None)
        try:
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(self.db.fetch_exchange_name_table(True), {})
        finally:
            if saved is not None:
                os.environ["VIA_NET"] = saved

    @unittest.skipUnless(def_has("fitz"), "pymupdf not installed")
    def test_pdf_tables_fall_back_to_pymupdf_without_pdfplumber(self) -> None:
        import fitz  # type: ignore
        db = self.db
        with tempfile.TemporaryDirectory(prefix="vrn-fitz-") as temporary:
            pdf = Path(temporary) / "KGI-3706 20250822.pdf"
            doc = fitz.open()
            page = doc.new_page(width=595, height=842)
            rows = [["項目", "2024A", "2025E"], ["營收", "10,000", "12,000"], ["每股盈餘(元)", "4.10", "5.20"]]
            x0, top, widths, row_h = 50.0, 100.0, [150.0, 100.0, 100.0], 20.0
            for r_idx, row in enumerate(rows):
                x = x0
                for c_idx, cell in enumerate(row):
                    rect = fitz.Rect(x, top + r_idx * row_h, x + widths[c_idx], top + (r_idx + 1) * row_h)
                    page.draw_rect(rect, color=(0, 0, 0), width=0.7)
                    page.insert_text((x + 4, top + r_idx * row_h + 14), cell, fontname="china-t", fontsize=9.5)
                    x += widths[c_idx]
            doc.save(str(pdf))
            doc.close()
            saved = db.optional_import_pdfplumber
            db.optional_import_pdfplumber = lambda: None
            try:
                tables = db.extract_pdf_tables(pdf)
            finally:
                db.optional_import_pdfplumber = saved
        self.assertEqual(len(tables), 1)
        records = db.parse_financial_tables_to_records(tables, {"ReportID": "r", "FileID": "f"}, "RUN")
        eps = [r for r in records if r["MetricName"] == "EPS" and r["FiscalYear"] == 2025]
        self.assertEqual(len(eps), 1)
        self.assertAlmostEqual(eps[0]["Value"], 5.2)

    @unittest.skipUnless(def_has("pandas") and def_has("pyarrow"), "pandas/pyarrow not installed")
    def test_txt_batch_roundtrip_and_typed_parquet(self) -> None:
        db = self.db
        import pandas as pd  # type: ignore
        with tempfile.TemporaryDirectory(prefix="vrn-batch-") as temporary:
            root = Path(temporary)
            samples = root / "samples"
            samples.mkdir()
            (samples / "KGI-3706 20250822.txt").write_text(SAMPLE_TXT, encoding="utf-8")
            (samples / "MS-Memory 20251204.txt").write_text("Morgan Stanley Research\nMemory outlook\n報告日期：2025/12/04\n市場維持震盪，外資小幅減碼。\n", encoding="utf-8")
            args = argparse.Namespace(input=str(samples), output=str(root / "db"), ticker_ssot="", broker_ssot="", rating_ssot="",
                                      online_name_update=False, csv=True, json=True, duckdb=False, google_sheet="", google_credentials="",
                                      run_id="TEST_RUN", self_test=False)
            with contextlib.redirect_stdout(io.StringIO()):
                summary = db.process_batch(args)
            self.assertEqual(summary["ProcessedFiles"], 2)
            basic = json.loads((root / "db" / db.BASICINFO_JSON_NAME).read_text(encoding="utf-8"))
            by_name = {r["SourceFileName"]: r for r in basic}
            row = by_name["KGI-3706 20250822.txt"]
            self.assertEqual((row["TW_TICKER"], row["ReportDate"], row["Broker"], row["Rating"]), ("3706", "2025-08-22", "KGI", "BUY"))
            self.assertEqual(row["TargetPrice"], 168.0)
            self.assertEqual(row["CurrentPrice"], 129.0)
            self.assertEqual(row["TriCodeVerdict"], "PASS")
            self.assertEqual(row["ReportDateDisplay"], "2025/08/22")
            other = by_name["MS-Memory 20251204.txt"]
            self.assertEqual((other["TW_TICKER"], other["Broker"], other["Rating"]), ("", "MS", ""))
            frame = pd.read_parquet(root / "db" / db.BASICINFO_PARQUET_NAME)
            self.assertTrue(str(frame["TargetPrice"].dtype).startswith("float"))
            with contextlib.redirect_stdout(io.StringIO()):
                again = db.process_batch(args)
            self.assertEqual(again["BasicRows"], summary["BasicRows"], "ReportID upsert keeps one row per report")


if __name__ == "__main__":
    unittest.main()
