"""The financial table the operator put on screen (批732; 2026-09-24, 20251128兆豐訪談速報-神達(3706).pdf page 4).

That 季度損益表 came out of the batch engine wrong three ways: the quarter headers 25Q1..25Q4(F) lost their year,
"(F)" was not read as a forecast, and the 營業成本 / 營業費用 rows were dropped for want of a metric.  The table is
rebuilt here from the numbers on the screen -- ground truth -- and read back through the same functions the batch
uses; every visible cell is checked, and the table has to add up the way the printed report does."""

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
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine"

# the visible cells of page 4 (NT$ million), exactly as printed; the 26Q1(F) column is covered on the screenshot
TABLE = [
    ("3706神達", "2024", "25Q1", "25Q2", "25Q3", "25Q4(F)", "2025(F)"),
    ("營業收入淨額", "61,360", "23,665", "26,624", "24,762", "34,667", "109,718"),
    ("營業成本", "53,991", "20,886", "23,770", "21,476", "30,472", "96,604"),
    ("營業毛利淨額", "7,368", "2,779", "2,854", "3,285", "4,195", "13,114"),
    ("營業費用", "5,585", "1,540", "1,602", "1,614", "2,080", "6,835"),
    ("營業淨利(損)", "1,784", "1,240", "1,253", "1,672", "2,115", "6,279"),
    ("營業外收支", "", "", "", "", "", ""),
    ("利息收入", "181", "30", "44", "26", "69", "170"),
]
PERIODS = {  # header -> (PeriodType, FiscalYear, FiscalQuarter, EstimateFlag)
    "2024": ("FY", 2024, "", ""), "25Q1": ("FQ", 2025, "Q1", ""), "25Q2": ("FQ", 2025, "Q2", ""),
    "25Q3": ("FQ", 2025, "Q3", ""), "25Q4(F)": ("FQ", 2025, "Q4", "Estimate"), "2025(F)": ("FY", 2025, "", "Estimate"),
}
METRICS = {"營業收入淨額": "Revenue", "營業成本": "COGS", "營業毛利淨額": "GrossProfit", "營業費用": "OperatingExpense",
           "營業淨利(損)": "OperatingProfit", "營業外收支": "NonOperatingIncome", "利息收入": "InterestIncome"}


def def_load(name, filename):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, ENGINE / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def def_table_pdf(path, rows=TABLE, pages=5, table_page=4):
    """A 5-page report with the table ruled on page 4, the way the broker prints it (one rectangle per cell)."""
    import fitz
    doc = fitz.open()
    for p in range(1, pages + 1):
        page = doc.new_page(width=595, height=842)
        page.insert_text((60, 50), "兆豐國際投顧 訪談速報", fontsize=12, fontname="china-t")
        if p != table_page:
            page.insert_text((60, 90), f"神達(3706) 第 {p} 頁 內文", fontsize=10, fontname="china-t")
            continue
        page.insert_text((250, 90), "財務報表", fontsize=14, fontname="china-t")
        page.insert_text((250, 115), "季度損益表", fontsize=12, fontname="china-t")
        page.insert_text((420, 130), "單位:新台幣百萬元", fontsize=8, fontname="china-t")
        x0, y0, w0, w, h = 40, 140, 110, 68, 20
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                left = x0 if c == 0 else x0 + w0 + (c - 1) * w
                rect = fitz.Rect(left, y0 + r * h, left + (w0 if c == 0 else w), y0 + (r + 1) * h)
                page.draw_rect(rect, color=(0, 0, 0), width=0.5)
                if cell:
                    page.insert_text((rect.x0 + 3, rect.y1 - 6), cell, fontsize=9, fontname="china-t")
    doc.save(str(path))
    doc.close()


def def_cells(records):
    return {(r["MetricName"], r["PeriodLabelRaw"]): r for r in records}


class HeaderAndLabelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = def_load("vrn_db_engine_fintable", "VRN_Integrated_ReportDatabase_Engine.py")

    def test_the_period_headers_of_that_table(self):
        for label, (kind, year, quarter, est) in PERIODS.items():
            p = self.db.parse_period_label(label)
            self.assertEqual((p["PeriodType"], p["FiscalYear"], p["FiscalQuarter"], p["EstimateFlag"]), (kind, year, quarter, est), label)
        self.assertEqual(self.db.parse_period_label("26Q1(F)")["FiscalYear"], 2026)

    def test_headers_read_before_read_the_same(self):
        for label, want in {"2024A": ("FY", 2024, "", "Actual"), "2025F": ("FY", 2025, "", "Estimate"),
                            "1Q25": ("FQ", 2025, "Q1", ""), "4Q25F": ("FQ", 2025, "Q4", "Estimate"),
                            "2025Q1": ("FQ", 2025, "Q1", ""), "25年第1季": ("FQ", 2025, "Q1", ""),
                            "12/24A": ("FY", 2024, "", "Actual"), "FY25": ("FY", 2025, "", ""), "TTM": ("TTM", None, "", ""),
                            "Q1": ("FQ", None, "Q1", ""), "25": ("FY", 2025, "", ""), "2025預估": ("FY", 2025, "", "Estimate")}.items():
            p = self.db.parse_period_label(label)
            self.assertEqual((p["PeriodType"], p["FiscalYear"], p["FiscalQuarter"], p["EstimateFlag"]), want, label)
        # a bare 3-digit number is not taken for a (ROC) year: data rows hold numbers like that
        self.assertIsNone(self.db.parse_period_label("113")["FiscalYear"])
        self.assertIsNone(self.db.parse_period_label("1,240")["FiscalYear"])

    def test_the_row_labels_of_that_table(self):
        for label, metric in METRICS.items():
            self.assertEqual(self.db.normalize_metric_name(label), metric, label)
        for label, metric in {"營業費用率": "OperatingExpenseRatio", "營業成本率": "COGSRatio", "毛利率": "GrossMargin",
                              "營業利益": "OperatingProfit", "稅後淨利": "NetIncome", "OPEX Ratio": "OperatingExpenseRatio"}.items():
            self.assertEqual(self.db.normalize_metric_name(label), metric, label)


class SharedPeriodDoorTest(unittest.TestCase):
    """One period parser for the VRN: both readers of this lineage ask the mother's VRN_ENG074 through the core."""

    @classmethod
    def setUpClass(cls):
        cls.core = def_load("vrn_engine_evidence_core", "VRN_Evidence_Core.py")
        cls.fp = def_load("vrn_first_page_fintable", "VIA_VRN_FirstPageEngine.py")

    def test_the_core_answers_with_eng074(self):
        mod, why = self.core.period_engine()
        self.assertIsNotNone(mod, why)
        self.assertTrue(why.startswith("VRN_ENG074_FinancialPages_v"), why)
        p = self.core.period_parts("25Q4(F)")
        self.assertEqual((p["period_type"], p["fiscal_year"], p["fiscal_quarter"], p["estimate"]), ("FQ", 2025, 4, "F"))
        self.assertIsNone(self.core.period_parts("113"), "a bare 3-digit number is left to the caller's rules")
        self.assertIsNone(self.core.period_parts("3706神達"))

    def test_without_eng074_the_door_says_nothing(self):
        with tempfile.TemporaryDirectory() as td:
            mod, why = self.core.period_engine(start=td)
            self.assertIsNone(mod)
            self.assertIn("VRN_ENG074_FinancialPages_v*.py", why)
            self.assertIsNone(self.core.period_parts("25Q4(F)", start=td))

    def test_the_first_page_reader_reads_that_header(self):
        cls = next(getattr(self.fp, n) for n in dir(self.fp) if hasattr(getattr(self.fp, n), "restore_period_header"))
        got = {r["raw"]: (r["period"], r["kind"]) for r in cls.restore_period_header(list(TABLE[0][1:]) + ["12/24A", "25E", "113"])}
        self.assertEqual(got, {"2024": ("2024", "actual"), "25Q1": ("2025-Q1", "actual"), "25Q2": ("2025-Q2", "actual"),
                               "25Q3": ("2025-Q3", "actual"), "25Q4(F)": ("2025-Q4", "forecast"), "2025(F)": ("2025", "forecast"),
                               "12/24A": ("2024-12", "actual"), "25E": ("2025", "estimate"), "113": (None, None)})


@unittest.skipUnless(importlib.util.find_spec("fitz") and importlib.util.find_spec("pdfplumber"), "PDF libraries absent")
class TableReadBackTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = def_load("vrn_db_engine_fintable", "VRN_Integrated_ReportDatabase_Engine.py")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.pdf = Path(cls.tmp.name) / "20251128兆豐訪談速報-神達(3706).pdf"
        def_table_pdf(cls.pdf)
        cls.records = cls.db.parse_financial_tables_to_records(cls.db.extract_pdf_tables(cls.pdf), {"ReportID": "R"}, "T")

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_every_visible_cell_is_read_right(self):
        cells = def_cells(self.records)
        header = TABLE[0]
        n = 0
        for row in TABLE[1:]:
            for label, printed in zip(header[1:], row[1:]):
                if not printed:
                    continue
                r = cells.get((METRICS[row[0]], label))
                self.assertIsNotNone(r, (row[0], label))
                kind, year, quarter, est = PERIODS[label]
                self.assertEqual((r["Value"], r["PeriodType"], r["FiscalYear"], r["FiscalQuarter"], r["EstimateFlag"], r["PageNumber"]),
                                 (float(printed.replace(",", "")), kind, year, quarter, est, 4), (row[0], label))
                self.assertEqual(r["ValidationStatus"], "PASS", (row[0], label))
                n += 1
        self.assertEqual(n, 36)
        self.assertEqual(len(self.records), 36, "the blank 營業外收支 row adds nothing")

    def test_the_table_adds_up(self):
        res = self.db.financial_identity_checks(self.records)
        # 6 columns x 2 identities + six flow items whose four 2025 quarters make 2025(F)
        self.assertEqual((res["checked"], res["passed"]), (18, 18), [self.db.identity_failure_text(f) for f in res["failed"]])
        self.assertEqual(res["periods_unclear"], 0)
        self.assertEqual(res["estimate_rows"], 12)

    def test_a_misread_table_is_named(self):
        shifted = [dict(r) for r in self.records]
        by_col = {}
        for r in shifted:
            if r["MetricName"] == "COGS":
                by_col[r["ColumnIndex"]] = r
        values = [by_col[c]["Value"] for c in sorted(by_col)]
        for c, v in zip(sorted(by_col), values[1:] + values[:1]):      # the cost row read one column off
            by_col[c]["Value"] = v
        res = self.db.financial_identity_checks(shifted)
        self.assertGreater(len(res["failed"]), 0)
        text = self.db.identity_failure_text(res["failed"][0])
        self.assertIn("毛利 = 營收 − 營業成本", text)
        self.assertIn("容許", text)

    def test_the_year_less_table_of_the_old_parser_is_counted(self):
        unclear = [dict(r, FiscalYear=None) if r["PeriodType"] == "FQ" else r for r in self.records]
        self.assertEqual(self.db.financial_identity_checks(unclear)["periods_unclear"], 24)


@unittest.skipUnless(importlib.util.find_spec("fitz") and importlib.util.find_spec("pdfplumber")
                     and importlib.util.find_spec("pandas") and importlib.util.find_spec("pyarrow"), "fitz / pandas / pyarrow absent")
class BatchPathTest(unittest.TestCase):
    def test_the_batch_writes_that_table_right(self):
        db = def_load("vrn_db_engine_fintable", "VRN_Integrated_ReportDatabase_Engine.py")
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "in"
            src.mkdir()
            def_table_pdf(src / "20251128兆豐訪談速報-神達(3706).pdf")
            out = Path(td) / "out"
            args = argparse.Namespace(input=str(src), output=str(out), ticker_ssot="", broker_ssot="", rating_ssot="",
                                      online_name_update=False, csv=False, json=True, duckdb=False, google_sheet="",
                                      google_credentials="", run_id="FIN732", self_test=False)
            db.process_batch(args)
            fin = json.loads((out / db.FINANCIALDATA_JSON_NAME).read_text(encoding="utf-8"))
        cells = def_cells(fin)
        self.assertEqual(cells[("COGS", "25Q4(F)")]["Value"], 30472.0)
        self.assertEqual((cells[("Revenue", "25Q1")]["FiscalYear"], cells[("Revenue", "25Q1")]["FiscalQuarter"]), (2025, "Q1"))
        self.assertEqual(cells[("OperatingProfit", "2025(F)")]["EstimateFlag"], "Estimate")
        res = db.financial_identity_checks(fin)
        self.assertEqual((res["checked"], res["passed"]), (18, 18))


def def_unruled_table_pdf(path, rows=TABLE, pages=8, table_page=6, width=595, x0=40, w0=110, w=68):
    """批733(Z195):the same table printed WITHOUT ruling lines -- labels left, numbers right-aligned under their headers,
    the way many broker reports print it -- on a later page (page 6 of 8, past the old four-page window)."""
    import fitz
    doc = fitz.open()
    for p in range(1, pages + 1):
        page = doc.new_page(width=width, height=842)
        page.insert_text((60, 50), "兆豐國際投顧 訪談速報", fontsize=12, fontname="china-t")
        if p != table_page:
            page.insert_text((60, 90), f"神達(3706) 第 {p} 頁 內文", fontsize=10, fontname="china-t")
            continue
        page.insert_text((250, 90), "財務報表", fontsize=14, fontname="china-t")
        page.insert_text((250, 115), "季度損益表", fontsize=12, fontname="china-t")
        for r, row in enumerate(rows):
            for c, cell in enumerate(row):
                if not cell:
                    continue
                if c == 0:
                    page.insert_text((x0, 150 + r * 18), cell, fontsize=9, fontname="china-t")
                    continue
                right = x0 + w0 + c * w - 6
                page.insert_text((right - fitz.get_text_length(cell, fontname="china-t", fontsize=9), 150 + r * 18),
                                 cell, fontsize=9, fontname="china-t")
    doc.save(str(path))
    doc.close()


def def_truth(rows=TABLE):
    header = rows[0]
    return {(METRICS[row[0]], label): printed for row in rows[1:] for label, printed in zip(header[1:], row[1:]) if printed}


@unittest.skipUnless(importlib.util.find_spec("fitz") and importlib.util.find_spec("pdfplumber"), "PDF libraries absent")
class UnruledTableTest(unittest.TestCase):
    """批733(Z195):工作站 105 份裡 7 份「no financial rows」—— 沒有框線的表。沒框線的表讀出來,一律要加得起來才入庫。"""

    @classmethod
    def setUpClass(cls):
        cls.db = def_load("vrn_db_engine_fintable", "VRN_Integrated_ReportDatabase_Engine.py")
        cls.core = def_load("vrn_engine_evidence_core", "VRN_Evidence_Core.py")
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def _read(self, pdf):
        tables = self.db.extract_document_tables(pdf)
        return tables, self.db.parse_financial_tables_to_records(tables, {"ReportID": "R", "FileID": "F"}, "T")

    def test_the_unruled_table_on_page_6_is_read_right(self):
        pdf = self.dir / "unruled_p6.pdf"
        def_unruled_table_pdf(pdf)
        tables, recs = self._read(pdf)
        self.assertEqual([(t["TableID"], t.get("Strategy")) for t in tables], [("P006_C001", "COLUMN_ALIGNED")])
        cells = def_cells(recs)
        for (metric, label), printed in def_truth().items():
            r = cells.get((metric, label))
            self.assertIsNotNone(r, (metric, label))
            kind, year, quarter, est = PERIODS[label]
            self.assertEqual((r["Value"], r["PeriodType"], r["FiscalYear"], r["FiscalQuarter"], r["EstimateFlag"], r["PageNumber"]),
                             (float(printed.replace(",", "")), kind, year, quarter, est, 6), (metric, label))
        self.assertEqual(len(recs), 36)
        res = self.db.financial_identity_checks(recs)
        self.assertEqual((res["checked"], res["passed"], res["periods_unclear"], res["estimate_rows"]), (18, 18, 0, 12))
        kept, rejected = self.db.gate_fallback_tables(tables, recs)
        self.assertEqual((len(kept), rejected), (36, []))

    def test_unnamed_header_columns_are_not_guessed(self):
        # a landscape page whose quarter headers are written Q1'25 (not a period form): only 2024 and 2025(F) are named
        rows = [tuple("Q%d'25" % int(h[3]) + ("(F)" if "(F)" in h else "") if "Q" in h else h for h in TABLE[0])] + TABLE[1:]
        pdf = self.dir / "unnamed_landscape.pdf"
        def_unruled_table_pdf(pdf, rows=rows, pages=3, table_page=2, width=1190, x0=40, w0=460, w=100)
        chars, _size = self.core.pdf_page_chars(str(pdf), 1)
        guard = self.core._unnamed_columns
        try:
            self.core._unnamed_columns = lambda *a, **k: 0           # what the reader did without the guard
            unguarded = self.core.column_tables(chars, 2)
        finally:
            self.core._unnamed_columns = guard
        wrong = def_cells(self.db.parse_financial_tables_to_records(unguarded, {"ReportID": "R"}, "T"))
        # without the guard the 25Q3 revenue lands under 2025(F) -- and that misread still adds up column by column
        self.assertEqual(wrong[("Revenue", "2025(F)")]["Value"], 24762.0)
        self.assertEqual(self.db.financial_identity_checks(list(wrong.values()))["failed"], [])
        self.assertEqual(self.core.column_tables(chars, 2), [], "with the guard: a header that does not name every column is not read")

    def test_a_table_that_does_not_add_up_is_not_stored(self):
        typo = [list(r) for r in TABLE]
        typo[3][1] = "7,468"                                      # gross profit 2024 printed (or read) 100 too high
        src = self.dir / "in_typo"
        src.mkdir()
        def_unruled_table_pdf(src / "20251128兆豐訪談速報-神達(3706).pdf", rows=[tuple(r) for r in typo])
        out = self.dir / "out_typo"
        args = argparse.Namespace(input=str(src), output=str(out), ticker_ssot="", broker_ssot="", rating_ssot="",
                                  online_name_update=False, csv=False, json=True, duckdb=False, google_sheet="",
                                  google_credentials="", run_id="FIN733", self_test=False)
        self.db.process_batch(args)
        fin = json.loads((out / self.db.FINANCIALDATA_JSON_NAME).read_text(encoding="utf-8"))
        basic = json.loads((out / self.db.BASICINFO_JSON_NAME).read_text(encoding="utf-8"))
        self.assertEqual([r for r in fin if r.get("TableID") == "P006_C001"], [], "the table that does not add up is left out")
        issues = " ".join(str(b.get("ValidationIssues") or "") for b in basic)
        self.assertIn("FIN_TABLE_REJECTED(P006_C001", issues)
        self.assertIn("毛利 = 營收 − 營業成本", issues)

    def test_the_header_forms_the_column_reader_now_knows(self):
        # 批733:年在前的季 / 半年 / 帶「年」的年,column reader 要認得(PERIOD_TOKEN_RX)、資料庫引擎要讀得對
        want = {"25Q1": ("FQ", 2025, "Q1", ""), "2025Q1": ("FQ", 2025, "Q1", ""), "25Q4(F)": ("FQ", 2025, "Q4", "Estimate"),
                "25Q4F": ("FQ", 2025, "Q4", "Estimate"), "25H1": ("FH", 2025, "H1", ""), "1H25": ("FH", 2025, "H1", ""),
                "2024年": ("FY", 2024, "", ""), "2025年(F)": ("FY", 2025, "", "Estimate"), "1Q25(F)": ("FQ", 2025, "Q1", "Estimate")}
        for token, (kind, year, sub, est) in want.items():
            self.assertTrue(self.core.PERIOD_TOKEN_RX.match(token), token)
            p = self.db.parse_period_label(token)
            self.assertEqual((p.get("PeriodType"), p.get("FiscalYear"), p.get("FiscalQuarter"), p.get("EstimateFlag")),
                             (kind, year, sub, est), token)
        for token in ("25Q5", "25H3", "61,360", "3706神達"):
            self.assertIsNone(self.core.PERIOD_TOKEN_RX.match(token), token)

    def test_a_ruled_table_is_not_read_twice(self):
        # the screenshot table is ruled and has no EPS row, so the column fallback also runs on its page; with the
        # quarter headers now read it would read the same table again (72 rows for 36 cells) -- the copy is left out
        pdf = self.dir / "ruled_p4.pdf"
        def_table_pdf(pdf)
        tables, recs = self._read(pdf)
        self.assertEqual([t.get("Strategy", "RULED") for t in tables if t.get("PageNumber") == 4], ["RULED"])
        self.assertEqual(len(recs), 36)

    def test_a_table_with_nothing_to_check_is_kept(self):
        eps_only = [("", "2024", "2025F", "2026F"), ("每股盈餘(元)", "12.35", "15.02", "17.44"), ("本益比(倍)", "18.2", "15.0", "12.9")]
        pdf = self.dir / "eps_only.pdf"
        def_unruled_table_pdf(pdf, rows=eps_only, pages=2, table_page=1)
        tables, recs = self._read(pdf)
        kept, rejected = self.db.gate_fallback_tables(tables, recs)
        self.assertEqual(rejected, [])
        self.assertEqual(len(kept), len(recs))
        self.assertIn(("EPS", "2026F"), {(r["MetricName"], r["PeriodLabelRaw"]) for r in kept})


if __name__ == "__main__":
    unittest.main()
