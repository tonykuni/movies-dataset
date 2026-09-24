"""ADJ CLOSE basis (批729; operator 2026-09-24): "所有目標價及各前一日的價格都要換成 ADJ CLOSE,上漲空間都要用最新的 ADJ CLOSE".

The formula is the mother's L99 (ENG073 adj_quote); these tests pin that the second lineage asks it, on a temporary
market database (no real prices are stored in the repo), and that every miss keeps its own name."""

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

import hashlib
import importlib.util
import os
import sys
import tempfile
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine"
# day before the report 2025-08-22: close 129.00, adj 125.13 (factor 0.97); latest adj close 150.00 on 2026-09-23
PRICES = [("2025-08-20", "3706.TW", 128.0, 124.16), ("2025-08-21", "3706.TW", 129.0, 125.13),
          ("2025-08-22", "3706.TW", 130.0, 126.10), ("2026-09-23", "3706.TW", 150.0, 150.00),
          ("2025-08-21", "6147.TWO", 207.0, 207.0), ("2026-09-23", "6147.TWO", 214.5, 214.5),
          # 1294-like (批730): Yahoo re-adjusted the 2024-09-26 close to 95.7617 after later stock dividends;
          # the report page printed the traded 126.5
          ("2024-09-26", "1294.TWO", 95.7617, 87.532), ("2026-09-22", "1294.TWO", 80.0, 80.0)]


def def_load(name, filename):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ENGINE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def def_chars(lines):
    """Synthetic char dicts (pdfplumber shape) from (text, size) pairs (same shape as test_VRN_FirstPageEngine)."""
    chars, top = [], 60.0
    for text, size in lines:
        x = 50.0
        for ch in text:
            chars.append({"text": ch, "x0": x, "top": top, "size": size, "fontname": "Regular"})
            x += size * (1.0 if ord(ch) > 255 else 0.55)
        top += size * 1.8
    return chars


def def_page(tp="NT$168.0", code="3706"):
    return [("凱基證券投資顧問  KGI Securities Research", 9.5),
            ("神達(%s TT)  營運動能延續,評價仍具吸引力" % code, 19.5),
            ("報告日期:2025/08/22    Bloomberg %s TT    Yahoo %s.TW" % (code, code), 9.5),
            ("投資評等:買進    目標價:%s    收盤價:NT$129.0" % tp, 12.5),
            ("我們預估神達 2025 年稀釋 EPS 5.20 元。", 10.0), ("主要動能來自 AI 伺服器需求。", 10.0)]


@unittest.skipUnless(importlib.util.find_spec("duckdb"), "duckdb absent; the ADJ basis cannot be asked for")
class AdjBasisTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import duckdb
        cls.C = def_load("vrn_evidence_core_adj_test", "VRN_Evidence_Core.py")
        if cls.C.adj_engine()[0] is None:
            raise unittest.SkipTest("no ENG073 v0137+ in this tree: " + cls.C.adj_engine()[1])
        cls.tmp = tempfile.TemporaryDirectory()
        cls.db = str(Path(cls.tmp.name) / "market.duckdb")
        con = duckdb.connect(cls.db)
        con.execute("CREATE TABLE tw_daily_prices(date VARCHAR, ticker VARCHAR, close DOUBLE, adj_close DOUBLE)")
        con.executemany("INSERT INTO tw_daily_prices VALUES (?,?,?,?)", PRICES)
        con.close()

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def fpe(self):
        mod = def_load("via_vrn_first_page_engine_adj_test", "VIA_VRN_FirstPageEngine.py")
        if not hasattr(self.__class__, "_engine"):
            self.__class__._engine = mod.FirstPageEngine()
        self._engine.adj_db = self.db
        return self._engine

    # ── the core asks ENG073 and passes the answer on ─────────────────────────────────────
    def test_target_and_day_before_price_in_adj_terms_upside_on_the_latest_adj_close(self):
        q = self.C.adj_basis("3706", "2025-08-22", 168.0, db=self.db)
        self.assertEqual(q["state"], "ADJ_OK")
        self.assertAlmostEqual(q["adj_factor"], 0.97, places=6)
        self.assertEqual(q["target_price_adj"], 162.96)
        self.assertEqual((q["price_prev_close"], q["price_prev_adj"], q["price_prev_date"]), (129.0, 125.13, "2025-08-21"))
        self.assertEqual((q["price_latest_adj"], q["price_latest_date"]), (150.0, "2026-09-23"))
        self.assertEqual(q["upside_adj"], 8.6)
        self.assertTrue(q["engine"].startswith("VRN_ENG073_ReportStructuredDB_v"))

    def test_ticker_and_date_forms_are_normalised(self):
        for tk, rd in (("3706.TW", "20250822"), ("3706 TT", "2025/8/22"), (" 3706", "2025年8月22日")):
            q = self.C.adj_basis(tk, rd, "168", db=self.db)
            self.assertEqual((q["ticker"], q["report_date"], q["upside_adj"]), ("3706", "2025-08-22", 8.6), (tk, rd))

    def test_every_miss_has_its_own_name(self):
        self.assertEqual(self.C.adj_basis("3706", "2025-08-22", None, db=self.db)["state"], "ADJ_NO_TARGET")
        no_tp = self.C.adj_basis("3706", "2025-08-22", None, db=self.db)
        self.assertEqual(no_tp["price_prev_adj"], 125.13, "the day-before price is converted even without a target")
        self.assertEqual(self.C.adj_basis(None, "2025-08-22", 168.0, db=self.db)["state"], "ADJ_NO_KEY")
        self.assertEqual(self.C.adj_basis("3706", "not a date", 168.0, db=self.db)["state"], "ADJ_NO_KEY")
        absent = self.C.adj_basis("9999", "2025-08-22", 168.0, db=self.db)
        self.assertEqual(absent["state"], "ADJ_NO_FACTOR")
        self.assertIsNone(absent["upside_adj"])
        self.assertTrue(absent["why"], "the block reason is carried")
        # ENG073 v0137 counts the table live: this table HAS a listed (.TW) ticker, so the reason is about this code
        self.assertIn("這一檔不在", absent["why"])
        self.assertNotIn("上市所整個不在", absent["why"])
        missing = self.C.adj_basis("3706", "2025-08-22", 168.0, db=str(Path(self.tmp.name) / "none.duckdb"))
        self.assertEqual((missing["state"], missing["upside_adj"] if "upside_adj" in missing else None), ("ADJ_NO_DB", None))

    def test_the_lookup_never_writes_the_database(self):
        before = hashlib.sha256(Path(self.db).read_bytes()).hexdigest()
        for _ in range(3):
            self.C.adj_basis("3706", "2025-08-22", 168.0, db=self.db)
        self.assertEqual(hashlib.sha256(Path(self.db).read_bytes()).hexdigest(), before)
        self.assertFalse(Path(self.db + ".wal").exists())

    def test_the_resolver_honours_the_data_home_catalogue(self):
        old = os.environ.get("VIA_DB_VDF_TW_MARKET")
        os.environ["VIA_DB_VDF_TW_MARKET"] = self.db
        try:
            path, _ = self.C.adj_db()
            self.assertEqual(path, self.db)
            self.assertEqual(self.C.adj_basis("3706", "2025-08-22", 168.0)["upside_adj"], 8.6)
        finally:
            if old is None:
                os.environ.pop("VIA_DB_VDF_TW_MARKET", None)
            else:
                os.environ["VIA_DB_VDF_TW_MARKET"] = old

    def test_the_page_price_corrects_a_readjusted_yahoo_close(self):
        # 批730: with no exchange row for the day, the printed page price is the traded close -> the right factor
        q = self.C.adj_basis("1294", "2024-09-27", 150.0, db=self.db, page_price=126.5)
        self.assertEqual(q["adj_factor_basis"], "PAGE_PRICE")
        self.assertAlmostEqual(q["adj_factor"], 87.532 / 126.5, places=9)
        self.assertEqual(q["upside_adj"], round((round(150.0 * 87.532 / 126.5, 4) / 80.0 - 1) * 100, 1))
        self.assertEqual(q["upside_adj"], 29.7)
        plain = self.C.adj_basis("1294", "2024-09-27", 150.0, db=self.db)       # no page price: v0137's answer, named
        self.assertEqual((plain["adj_factor_basis"], plain["upside_adj"]), ("YAHOO_CLOSE", 71.4))

    def test_cli_answers_one_quote_and_names_a_miss(self):
        import contextlib
        import io
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = self.C.main(["adj", "3706", "2025-08-22", "168", "--db", self.db])
        self.assertEqual(rc, 0)
        self.assertIn("ADJ_OK", buf.getvalue())
        self.assertIn("162.96", buf.getvalue())
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.C.main(["adj", "3706"]), 2)
            self.assertEqual(self.C.main(["adj", "3706", "2025-08-22", "168", "--db", self.db + ".none"]), 2)

    # ── the first-page engine: upside = ADJ, the page arithmetic stays as evidence ─────────────
    def test_first_page_upside_is_on_the_latest_adj_close(self):
        out = self.fpe().run("KGI-3706 20250822.pdf", chars=def_chars(def_page()), official_market="TWSE")
        up = out["upside"]
        self.assertEqual((up["status"], up["basis"], up["upside_pct"]), ("DERIVED_ADJ", "ADJ_LATEST", 8.6))
        self.assertEqual((up["target_price_adj"], up["current_price"], up["price_date"]), (162.96, 150.0, "2026-09-23"))
        self.assertEqual((up["price_prev_adj"], up["page_price"], up["page_price_adj"]), (125.13, 129.0, 125.13))
        self.assertEqual(up["factor_basis"], "PAGE_PRICE", "no exchange table here: the printed price is the divisor")
        self.assertAlmostEqual(out["upside_page"]["upside_pct"], 30.23, places=2)
        self.assertNotIn("adjusted", out["upside_page"]["formula"], "the page arithmetic is not labelled adjusted")
        self.assertIn("上漲空間 8.6% (ADJ;最新 adj close 2026-09-23)", out["summary_four_points"]["points"][0]["text"])

    def test_a_foreign_currency_target_is_not_put_on_the_tw_adj_close(self):
        up = self.fpe().adj_upside("3706", "2025-08-22", 168.0, currency="USD", page_price=129.0)
        self.assertEqual((up["status"], up["state"], up["upside_pct"]), ("NO_ADJ", "ADJ_CURRENCY(USD)", None))

    def test_no_price_row_means_no_adj_upside_not_a_page_fallback(self):
        out = self.fpe().run("KGI-2330 20250822.pdf", chars=def_chars(def_page(code="2330")), official_market="TWSE")
        self.assertEqual((out["upside"]["status"], out["upside"]["state"]), ("NO_ADJ", "ADJ_NO_FACTOR"))
        self.assertIsNone(out["upside"]["upside_pct"])
        self.assertEqual(out["upside_page"]["status"], "DERIVED", "the page value is kept, labelled, not promoted")

    # ── the report database engine: UpsideDownsidePct is the ADJ upside ───────────────────────
    def test_database_columns_carry_the_adj_basis(self):
        try:
            db = def_load("vrn_report_db_adj_test", "VRN_Integrated_ReportDatabase_Engine.py")
        except Exception as exc:          # pandas / optional dependencies of the database engine
            self.skipTest("database engine not importable: %s" % exc)
        cols = db.adj_upside_columns("3706", "2025-08-22", 168.0, 129.0, db=self.db)
        self.assertEqual((cols["UpsideDownsidePct"], cols["UpsideBasis"], cols["UpsideState"]), (8.6, "ADJ_LATEST", "ADJ_OK"))
        self.assertEqual((cols["TargetPriceAdj"], cols["PrevCloseAdj"], cols["CurrentPriceAdj"]), (162.96, 125.13, 125.13))
        self.assertEqual((cols["LatestAdjClose"], cols["LatestAdjDate"]), (150.0, "2026-09-23"))
        self.assertEqual(cols["UpsidePagePct"], round((168.0 / 129.0 - 1) * 100, 4))
        self.assertTrue(set(cols) <= set(db.BASICINFO_COLUMNS), set(cols) - set(db.BASICINFO_COLUMNS))
        miss = db.adj_upside_columns("9999", "2025-08-22", 168.0, 129.0, db=self.db)
        self.assertEqual((miss["UpsideDownsidePct"], miss["UpsideState"]), ("", "ADJ_NO_FACTOR"))


if __name__ == "__main__":
    unittest.main()
