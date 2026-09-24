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


if __name__ == "__main__":
    unittest.main()
