import argparse
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


ENGINE_PATH = Path(__file__).resolve().parents[1] / "VIA_FinMind_TW_Flow_Engine.py"
sys.path.insert(0, str(ENGINE_PATH.parent))
SPEC = importlib.util.spec_from_file_location("finmind_engine", ENGINE_PATH)
ENGINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ENGINE)


class EngineTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.connection = ENGINE.open_database(self.root)
        ENGINE.initialize_database(self.connection)

    def tearDown(self):
        self.connection.close()
        self.tempdir.cleanup()

    def test_normalize_ticker(self):
        self.assertEqual(ENGINE.normalize_ticker("2330.TW"), "2330")
        self.assertEqual(ENGINE.normalize_ticker("8069.two"), "8069")
        with self.assertRaises(ValueError):
            ENGINE.normalize_ticker("../token")

    def test_dataset_selection_for_latest_branch_run(self):
        original = dict(ENGINE.ENABLED_DATASETS)
        try:
            selected = ENGINE.configure_enabled_datasets(
                "TaiwanStockTradingDailyReport,TaiwanStockTradingDailyReportSecIdAgg"
            )
            self.assertEqual(len(selected), 2)
            self.assertTrue(ENGINE.ENABLED_DATASETS["TaiwanStockTradingDailyReport"])
            self.assertFalse(ENGINE.ENABLED_DATASETS["TaiwanStockPrice"])
        finally:
            ENGINE.ENABLED_DATASETS.update(original)

    def test_task_plan_standard_and_sponsorpro(self):
        tickers = ["2330", "2317"]
        trading_dates = ["2026-05-04", "2026-05-05"]
        completed = set()

        standard = ENGINE.count_pending_tasks(
            ENGINE.iter_all_tasks(
                self.connection, tickers, trading_dates,
                "2026-05-04", "2026-05-05", "standard",
            ),
            completed,
        )
        sponsorpro = ENGINE.count_pending_tasks(
            ENGINE.iter_all_tasks(
                self.connection, tickers, trading_dates,
                "2026-05-04", "2026-05-05", "sponsorpro",
            ),
            completed,
        )
        self.assertEqual(standard["TaiwanStockTradingDailyReport"], 4)
        self.assertEqual(sponsorpro["TaiwanStockTradingDailyReport"], 2)
        self.assertEqual(standard["TaiwanStockTradingDailyReportSecIdAgg"], 2)
        self.assertEqual(standard["TaiwanStockBlockTrade"], 2)
        self.assertEqual(standard["TaiwanStockIndustryChainMoneyFlow"], 2)
        self.assertEqual(standard["TaiwanStockPrice"], 2)
        self.assertEqual(standard["TaiwanStockInstitutionalInvestorsBuySellWide"], 2)
        self.assertEqual(standard["TaiwanStockMarginPurchaseShortSale"], 2)
        self.assertEqual(standard["TaiwanStockDayTrading"], 2)

    def test_hybrid_plans_official_latest_before_finmind(self):
        tasks = ENGINE.iter_all_tasks(
            self.connection,
            ["2330", "8069"],
            ["2026-08-27", "2026-08-28"],
            "2026-08-27",
            "2026-08-28",
            "standard",
            "full_history",
            "hybrid",
        )
        first_four = [next(tasks) for _ in range(4)]
        self.assertTrue(all(task["endpoint"] == "official" for task in first_four))
        self.assertEqual(
            {task["dataset"] for task in first_four},
            set(ENGINE.OFFICIAL_LATEST_DATASETS),
        )

    def test_official_latest_coverage_leaves_only_history_gap(self):
        ENGINE.merge_range_coverage(
            self.connection,
            "TaiwanStockBlockTrade",
            "2330",
            "2026-08-28",
            "2026-08-28",
        )
        gaps = ENGINE.get_uncovered_ranges(
            self.connection,
            "TaiwanStockBlockTrade",
            "2330",
            "2026-08-01",
            "2026-08-28",
        )
        self.assertEqual(gaps, [("2026-08-01", "2026-08-27")])

    def test_official_task_runs_without_finmind_quota_and_writes_coverage(self):
        task = next(ENGINE.iter_official_latest_tasks(
            ["2330"], "2026-08-28", "2026-08-01"
        ))
        original = ENGINE.def_fetch_official_dataset
        ENGINE.def_fetch_official_dataset = lambda *args, **kwargs: [{
            "date": "2026-08-28", "stock_id": "2330",
            "HoldingSharesLevel": "1-999", "people": 10,
            "percent": 0.01, "unit": 2000,
            "source_provider": "TDCC", "source_mode": "official_open_data",
            "source_dataset": "TDCC_OPEN_DATA_1-5",
        }]
        try:
            result = ENGINE.execute_tasks(
                self.connection, None, [task], ["2330"], set(),
                {"remaining": 0, "api_request_limit": 1, "user_count": 0},
                self.root, "OFFICIAL_TEST",
                {"checkpoint_batch_size": 25, "circuit_breaker": None},
                object(),
            )
        finally:
            ENGINE.def_fetch_official_dataset = original
        self.assertEqual(result["official_request_count"], 1)
        self.assertEqual(result["finmind_request_count"], 0)
        self.assertEqual(
            ENGINE.get_uncovered_ranges(
                self.connection, task["dataset"], "2330",
                "2026-08-28", "2026-08-28",
            ),
            [],
        )

    def test_official_failure_does_not_claim_coverage(self):
        task = next(ENGINE.iter_official_latest_tasks(
            ["2330"], "2026-08-28", "2026-08-01"
        ))
        original = ENGINE.def_fetch_official_dataset
        ENGINE.def_fetch_official_dataset = lambda *args, **kwargs: (_ for _ in ()).throw(
            ENGINE.OfficialSourceError("synthetic failure")
        )
        try:
            result = ENGINE.execute_tasks(
                self.connection, None, [task], ["2330"], set(),
                {"remaining": 0, "api_request_limit": 1, "user_count": 0},
                self.root, "OFFICIAL_FAIL_TEST",
                {"checkpoint_batch_size": 25, "circuit_breaker": None},
                object(),
            )
        finally:
            ENGINE.def_fetch_official_dataset = original
        self.assertEqual(result["official_failures"], 1)
        self.assertEqual(
            ENGINE.get_uncovered_ranges(
                self.connection, task["dataset"], "2330",
                "2026-08-28", "2026-08-28",
            ),
            [("2026-08-28", "2026-08-28")],
        )

    def test_source_policy_keeps_schema_sensitive_data_on_finmind(self):
        self.assertEqual(
            ENGINE.DATA_SOURCE_POLICY["TaiwanStockInstitutionalInvestorsBuySellWide"],
            "finmind_api_schema_consistent",
        )
        self.assertEqual(
            ENGINE.DATA_SOURCE_POLICY["TaiwanStockDayTrading"],
            "finmind_api_schema_consistent",
        )

    def test_known_missing_date_is_not_planned(self):
        tasks = list(ENGINE.iter_all_tasks(
            self.connection,
            ["2330"],
            ["2023-01-11", "2023-01-18"],
            "2023-01-01",
            "2023-01-18",
            "standard",
        ))
        raw_branch = [task for task in tasks if task["dataset"] == "TaiwanStockTradingDailyReport"]
        self.assertEqual(len(raw_branch), 1)
        self.assertEqual(raw_branch[0]["params"]["date"], "2023-01-18")

    def test_daily_tasks_are_newest_first(self):
        tasks = list(ENGINE.iter_all_tasks(
            self.connection,
            ["2330"],
            ["2026-05-04", "2026-05-05"],
            "2026-05-04",
            "2026-05-05",
            "standard",
        ))
        raw_branch = [task for task in tasks if task["dataset"] == "TaiwanStockTradingDailyReport"]
        self.assertEqual(
            [task["params"]["date"] for task in raw_branch],
            ["2026-05-05", "2026-05-04"],
        )
        latest_government_bank = next(
            index for index, task in enumerate(tasks)
            if task["dataset"] == "TaiwanStockGovernmentBankBuySell"
            and task["params"]["start_date"] == "2026-05-05"
        )
        older_raw_branch = next(
            index for index, task in enumerate(tasks)
            if task["dataset"] == "TaiwanStockTradingDailyReport"
            and task["params"]["date"] == "2026-05-04"
        )
        self.assertLess(latest_government_bank, older_raw_branch)

    def test_current_range_uses_incremental_coverage(self):
        for dataset in (
            "TaiwanStockTradingDailyReportSecIdAgg",
            "TaiwanStockBlockTrade",
        ):
            ENGINE.merge_range_coverage(
                self.connection, dataset, "2330", "2026-05-04", "2026-05-04"
            )
        tasks = list(ENGINE.iter_all_tasks(
            self.connection,
            ["2330"],
            ["2026-05-04", "2026-05-05"],
            "2026-05-04",
            "2026-05-05",
            "standard",
        ))
        range_tasks = [
            task for task in tasks
            if task["dataset"] in {
                "TaiwanStockTradingDailyReportSecIdAgg", "TaiwanStockBlockTrade"
            }
        ]
        self.assertEqual(len(range_tasks), 2)
        self.assertTrue(all(
            task["params"]["start_date"] == "2026-05-05"
            for task in range_tasks
        ))
        self.assertTrue(all(task["cursor_end"] == "2026-05-05" for task in range_tasks))

    def test_range_windows_are_yearly_and_newest_first(self):
        windows = list(ENGINE.iter_reverse_year_windows(
            "TaiwanStockBlockTrade",
            ["2023-01-03", "2023-12-29", "2024-01-02", "2024-12-31"],
            "2023-01-01",
            "2024-12-31",
        ))
        self.assertEqual(windows, [
            ("2024-01-01", "2024-12-31"),
            ("2023-01-01", "2023-12-31"),
        ])

    def test_larger_range_modes_reduce_request_count(self):
        tickers = ["2330", "2317"]
        trading_dates = [
            "2023-01-03", "2023-12-29", "2024-01-02", "2024-12-31",
            "2025-01-02", "2025-12-31", "2026-01-02", "2026-08-28",
        ]

        def range_request_count(mode):
            tasks = ENGINE.iter_all_tasks(
                self.connection, tickers, trading_dates,
                "2023-01-01", "2026-08-29", "sponsorpro", mode,
            )
            return sum(
                task["dataset"] in {
                    "TaiwanStockTradingDailyReportSecIdAgg", "TaiwanStockBlockTrade"
                }
                for task in tasks
            )

        self.assertEqual(range_request_count("calendar_year"), 16)
        self.assertEqual(range_request_count("two_year"), 8)
        self.assertEqual(range_request_count("full_history"), 4)

    def test_two_year_mode_finishes_latest_window_across_datasets_first(self):
        tasks = ENGINE.iter_all_tasks(
            self.connection,
            ["2330"],
            ["2023-01-03", "2024-12-31", "2025-01-02", "2026-08-28"],
            "2023-01-01",
            "2026-08-29",
            "sponsorpro",
            "two_year",
        )
        range_order = [
            (task["dataset"], task["params"]["end_date"])
            for task in tasks
            if task["dataset"] in {
                "TaiwanStockTradingDailyReportSecIdAgg", "TaiwanStockBlockTrade"
            }
        ]
        self.assertEqual(range_order, [
            ("TaiwanStockTradingDailyReportSecIdAgg", "2026-08-28"),
            ("TaiwanStockBlockTrade", "2026-08-28"),
            ("TaiwanStockTradingDailyReportSecIdAgg", "2024-12-31"),
            ("TaiwanStockBlockTrade", "2024-12-31"),
        ])

    def test_range_coverage_merges_adjacent_windows(self):
        ENGINE.merge_range_coverage(
            self.connection, "TaiwanStockBlockTrade", "2330",
            "2023-01-01", "2024-12-31",
        )
        ENGINE.merge_range_coverage(
            self.connection, "TaiwanStockBlockTrade", "2330",
            "2025-01-01", "2026-08-28",
        )
        rows = self.connection.execute(
            """SELECT range_start, range_end FROM range_coverage
               WHERE dataset = 'TaiwanStockBlockTrade' AND entity_id = '2330'"""
        ).fetchall()
        self.assertEqual(rows, [("2023-01-01", "2026-08-28")])

    def test_quota_estimate(self):
        estimate = ENGINE.estimate_quota_time(
            1200,
            {"api_request_limit": 600, "user_count": 0, "remaining": 600},
        )
        self.assertAlmostEqual(estimate["estimated_hours_at_full_rate"], 2.0)
        self.assertGreaterEqual(estimate["quota_windows"], 2)

    def test_upsert_is_idempotent(self):
        first = [{
            "date": "2026-05-04", "stock_id": "2330", "bank_name": "A",
            "buy_amount": 10, "sell_amount": 5, "buy": 2, "sell": 1,
        }]
        second = [{
            "date": "2026-05-04", "stock_id": "2330", "bank_name": "A",
            "buy_amount": 20, "sell_amount": 5, "buy": 3, "sell": 1,
        }]
        ENGINE.upsert_rows(self.connection, "TaiwanStockGovernmentBankBuySell", first)
        ENGINE.upsert_rows(self.connection, "TaiwanStockGovernmentBankBuySell", second)
        result = self.connection.execute(
            "SELECT COUNT(*), MAX(buy_amount) FROM tw_stock_government_bank_buy_sell"
        ).fetchone()
        self.assertEqual(result, (1, 20.0))

    def test_cursor_moves_even_for_empty_range(self):
        ENGINE.update_cursor(
            self.connection, "TaiwanStockBlockTrade", "2330", "2026-05-05"
        )
        self.assertEqual(
            ENGINE.get_cursor(self.connection, "TaiwanStockBlockTrade", "2330"),
            "2026-05-05",
        )

    def test_exports_have_no_extension_and_csv_bom(self):
        ENGINE.upsert_rows(self.connection, "TaiwanStockIndustryChainMoneyFlow", [{
            "date": "2026-05-04", "industry": "半導體", "sub_industry": "IC設計",
            "stock_count": 2, "trading_volume": 1000,
            "trading_money": 500000, "trading_money_pct": 3.5,
        }])
        exports = ENGINE.export_all_tables(self.connection, self.root)
        target = exports["TaiwanStockIndustryChainMoneyFlow"]
        parquet_path = Path(target["parquet"])
        csv_path = Path(target["csv"])
        self.assertEqual(parquet_path.suffix, "")
        self.assertEqual(csv_path.suffix, "")
        self.assertEqual(csv_path.read_bytes()[:3], b"\xef\xbb\xbf")
        self.assertIn("2026/05/04", csv_path.read_text(encoding="utf-8-sig"))

    def test_atomic_checkpoint_file(self):
        checkpoint = ENGINE.durable_checkpoint(
            self.connection,
            self.root,
            "TEST_RUN",
            25,
            100,
            0,
            "date=2026-05-05",
            "running",
        )
        self.assertTrue(checkpoint.exists())
        content = checkpoint.read_text(encoding="utf-8")
        self.assertIn('"request_count": 25', content)
        self.assertFalse(checkpoint.with_name(checkpoint.name + ".tmp").exists())

    def test_supportive_runtime_loads_celeritas_and_aegis(self):
        package_root = Path(__file__).resolve().parents[1]
        runtime = ENGINE.initialize_supportive_runtime(
            str(package_root / "VeritasCeleritas.py"),
            str(package_root / "VeritasAegisNexus.py"),
        )
        report = ENGINE.supportive_runtime_report(runtime)
        self.assertTrue(report["enabled"])
        self.assertEqual(report["circuit_breaker_state"], "CLOSED")
        self.assertFalse(report["safety_policy"]["proxy_rotation"])
        self.assertFalse(report["safety_policy"]["token_rotation"])

    def test_keyboard_interrupt_keeps_checkpoint(self):
        task = ENGINE.make_task(
            "TaiwanStockIndustryChainMoneyFlow",
            "data",
            {"dataset": "TaiwanStockIndustryChainMoneyFlow", "start_date": "2026-05-05"},
            "date=2026-05-05",
        )
        original = ENGINE.fetch_task_rows_guarded
        ENGINE.fetch_task_rows_guarded = lambda *args, **kwargs: (_ for _ in ()).throw(KeyboardInterrupt())
        try:
            result = ENGINE.execute_tasks(
                self.connection,
                None,
                [task],
                ["2330"],
                set(),
                {"remaining": 100, "api_request_limit": 100, "user_count": 0},
                self.root,
                "INTERRUPT_TEST",
                {"checkpoint_batch_size": 25, "circuit_breaker": None},
            )
        finally:
            ENGINE.fetch_task_rows_guarded = original
        self.assertTrue(result["interrupted"])
        checkpoint = self.root / ENGINE.AUDIT_DIRECTORY / ENGINE.CHECKPOINT_FILENAME
        self.assertTrue(checkpoint.exists())
        self.assertIn('"state": "interrupted"', checkpoint.read_text(encoding="utf-8"))

    def test_codex_nexus_contains_interactive_finmind_route(self):
        nexus_path = Path(__file__).resolve().parents[1] / "Invoke-VeritasCodexNexus.ps1"
        content = nexus_path.read_text(encoding="utf-8-sig")
        self.assertIn("'FinMind'", content)
        self.assertIn("interactive = $true", content)
        self.assertIn("--celeritas-path", content)
        self.assertIn("--aegis-path", content)
        self.assertIn("AnalyzeCapitalCircle", content)
        self.assertIn("CapitalCircleEnginePath", content)
        self.assertIn("$_ -ne 'FinMind'", content)


if __name__ == "__main__":
    unittest.main(verbosity=2)
