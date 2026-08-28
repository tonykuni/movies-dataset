#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

import VETF_ConsensusEnrichment_Adapter_v001 as engine


class ConsensusEnrichmentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.asof = date(2026, 6, 22)
        self.holdings = engine.normalize_holding_records([
            {
                "holding_date": "2026-06-21",
                "etf_code": "00981A",
                "ticker": "2330",
                "exchange": "TWSE",
                "isin": "TW0002330008",
                "company_name": "台積電",
                "weight": 20.0,
            },
            {
                "holding_date": "2026-06-22",
                "etf_code": "00981A",
                "ticker": "2330",
                "exchange": "TWSE",
                "isin": "TW0002330008",
                "company_name": "台積電",
                "weight": 23.1,
            },
        ])
        self.prices = engine.normalize_price_records([
            {
                "date": "2026-06-21",
                "ticker": "2330.TW",
                "isin": "TW0002330008",
                "company_name": "台積電",
                "adj_close": 100,
                "currency": "TWD",
            },
            {
                "date": "2026-06-22",
                "ticker": "2330.TW",
                "isin": "TW0002330008",
                "company_name": "台積電",
                "adj_close": 110,
                "currency": "TWD",
            },
            {
                "date": "2026-06-23",
                "ticker": "2330.TW",
                "isin": "TW0002330008",
                "company_name": "台積電",
                "adj_close": 120,
                "currency": "TWD",
            },
        ])
        self.factset = engine.normalize_consensus_records([
            {
                "snapshot_date": "2026-06-21",
                "ticker": "2330.TW",
                "provider_id": "FS-2330",
                "company_name": "台積電",
                "currency": "TWD",
                "target_low": 120,
                "target_mean": 150,
                "target_median": 145,
                "target_high": 180,
                "target_analyst_count": 30,
                "eps_n_mean": 5,
                "eps_n_median": 5.5,
                "eps_n1_mean": 6,
                "eps_n1_median": 6.2,
                "eps_n2_mean": 7,
                "eps_n2_median": 7.1,
                "eps_n_fiscal_year": 2026,
                "eps_n1_fiscal_year": 2027,
                "eps_n2_fiscal_year": 2028,
            },
            {
                "snapshot_date": "2026-06-23",
                "ticker": "2330.TW",
                "provider_id": "FS-2330",
                "company_name": "台積電",
                "currency": "TWD",
                "target_mean": 999,
                "eps_n_mean": 99,
            },
        ], "FACTSET")
        self.yfinance = engine.normalize_consensus_records([
            {
                "captured_at": "2026-06-22",
                "YFinance Ticker": "2330.TW",
                "company_name": "台積電",
                "provider_id": "YF-2330",
                "currency": "TWD",
                "targetLowPrice": 115,
                "targetMeanPrice": 148,
                "targetMedianPrice": 140,
                "targetHighPrice": 175,
                "numberOfAnalystOpinions": 25,
            }
        ], "YFINANCE")

    def enrich(self):
        return engine.enrich_holdings(
            self.holdings, self.prices, self.factset, self.yfinance, self.asof
        )

    def test_ticker_normalization_twse_and_tpex(self) -> None:
        self.assertEqual(engine.normalize_ticker("2330", "TWSE"), "2330.TW")
        self.assertEqual(engine.normalize_ticker("8069", "TPEX"), "8069.TWO")
        self.assertEqual(engine.normalize_ticker("2330.TW", "TWSE"), "2330.TW")

    def test_latest_holding_snapshot_per_etf(self) -> None:
        rows = engine.select_latest_holdings(self.holdings, self.asof)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["holding_date"], "2026-06-22")
        self.assertEqual(rows[0]["holding_weight"], 23.1)

    def test_price_asof_blocks_future_record(self) -> None:
        rows, _ = self.enrich()
        self.assertEqual(rows[0]["price_adj_close"], 110.0)
        self.assertEqual(rows[0]["price_date"], "2026-06-22")

    def test_factset_asof_blocks_future_consensus(self) -> None:
        rows, _ = self.enrich()
        self.assertEqual(rows[0]["fs_target_mean"], 150.0)
        self.assertEqual(rows[0]["fs_eps_n_mean"], 5.0)

    def test_yfinance_target_aliases_and_upside(self) -> None:
        rows, _ = self.enrich()
        self.assertEqual(rows[0]["yf_target_median"], 140.0)
        self.assertAlmostEqual(rows[0]["yf_target_median_upside_pct"], 27.27272727)

    def test_factset_forward_pe_n_n1_n2(self) -> None:
        rows, _ = self.enrich()
        self.assertEqual(rows[0]["fs_forward_pe_n"], 22.0)
        self.assertAlmostEqual(rows[0]["fs_forward_pe_n1"], 18.33333333)
        self.assertAlmostEqual(rows[0]["fs_forward_pe_n2"], 15.71428571)

    def test_legacy_explicit_year_eps_maps_to_n_n1_n2(self) -> None:
        records = engine.normalize_consensus_records([
            {
                "snapshot_date": "2026-06-22",
                "ticker": "2330.TW",
                "company_name": "台積電",
                "provider_id": "FS-2330",
                "EPS 2026 Mean": 5.0,
                "EPS 2026 Median": 5.1,
                "EPS 2027 Mean": 6.0,
                "EPS 2028 Mean": 7.0,
                "EPS 2028 Analyst Count": 24,
            }
        ], "FACTSET")
        self.assertEqual(records[0]["eps_n_mean"], 5.0)
        self.assertEqual(records[0]["eps_n1_mean"], 6.0)
        self.assertEqual(records[0]["eps_n2_mean"], 7.0)
        self.assertEqual(records[0]["eps_n_fiscal_year"], 2026)
        self.assertEqual(records[0]["eps_n2_analyst_count"], 24)
        self.assertEqual(
            records[0]["eps_horizon_mapping_method"],
            "INFERRED_FROM_EXPLICIT_FISCAL_YEAR_COLUMNS",
        )

    def test_negative_zero_and_missing_eps_fail_closed(self) -> None:
        self.assertEqual(engine.forward_pe(100, -2), (None, "NEGATIVE_EPS"))
        self.assertEqual(engine.forward_pe(100, 0), (None, "ZERO_EPS"))
        self.assertEqual(engine.forward_pe(100, None), (None, "MISSING_EPS"))

    def test_currency_mismatch_blocks_derived_values(self) -> None:
        factset = copy.deepcopy(self.factset)
        factset[0]["currency"] = "USD"
        rows, _ = engine.enrich_holdings(
            self.holdings, self.prices, factset, self.yfinance, self.asof
        )
        self.assertIsNone(rows[0]["fs_target_mean_upside_pct"])
        self.assertIn("PRICE_CURRENCY_MISMATCH", rows[0]["quality_flags"])

    def test_factset_and_yfinance_are_not_averaged(self) -> None:
        rows, _ = self.enrich()
        self.assertEqual(rows[0]["fs_target_mean"], 150.0)
        self.assertEqual(rows[0]["yf_target_mean"], 148.0)
        self.assertNotIn("target_mean", rows[0])

    def test_double_identity(self) -> None:
        passed, evidence = engine.identity_evidence(self.holdings[0])
        self.assertTrue(passed)
        self.assertIn("ticker", evidence)
        self.assertIn("isin", evidence)
        failed, _ = engine.identity_evidence({"ticker": "2330.TW"})
        self.assertFalse(failed)

    def test_provider_divergence_flag(self) -> None:
        yfinance = copy.deepcopy(self.yfinance)
        yfinance[0]["target_median"] = 250.0
        rows, _ = engine.enrich_holdings(
            self.holdings, self.prices, self.factset, yfinance, self.asof
        )
        self.assertIn("PROVIDER_DIVERGENCE", rows[0]["quality_flags"])

    def test_append_only_idempotency_and_conflict(self) -> None:
        rows, audit = self.enrich()
        original_parquet = engine.PARAMS["allow_optional_parquet"]
        original_duckdb = engine.PARAMS["allow_optional_duckdb"]
        engine.PARAMS["allow_optional_parquet"] = False
        engine.PARAMS["allow_optional_duckdb"] = False
        try:
            with tempfile.TemporaryDirectory() as folder:
                first = engine.write_outputs_append_only(folder, rows, audit)
                second = engine.write_outputs_append_only(folder, rows, audit)
                self.assertEqual(first["status"], "WRITTEN")
                self.assertEqual(second["status"], "SKIPPED_IDENTICAL")
                changed = copy.deepcopy(rows)
                changed[0]["price_adj_close"] = 999.0
                with self.assertRaises(FileExistsError):
                    engine.write_outputs_append_only(folder, changed, audit)
        finally:
            engine.PARAMS["allow_optional_parquet"] = original_parquet
            engine.PARAMS["allow_optional_duckdb"] = original_duckdb

    def test_canonical_gate_denied_by_default(self) -> None:
        with self.assertRaises(PermissionError):
            engine.validate_canonical_write_gate("canonical", None, None)

    def test_audit_coverage(self) -> None:
        rows, audit = self.enrich()
        self.assertEqual(audit["record_count"], 1)
        self.assertEqual(audit["coverage_pct"]["price"], 100.0)
        self.assertEqual(audit["coverage_pct"]["forward_pe_n2"], 100.0)

    def test_end_to_end_json_pipeline(self) -> None:
        original_parquet = engine.PARAMS["allow_optional_parquet"]
        original_duckdb = engine.PARAMS["allow_optional_duckdb"]
        engine.PARAMS["allow_optional_parquet"] = False
        engine.PARAMS["allow_optional_duckdb"] = False
        try:
            with tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                paths = {
                    "holdings": root / "holdings.json",
                    "prices": root / "prices.json",
                    "factset": root / "factset.json",
                    "yfinance": root / "yfinance.json",
                }
                raw_holdings = [{
                    "holding_date": "2026-06-22", "etf_code": "00981A",
                    "ticker": "2330", "exchange": "TWSE", "isin": "TW0002330008",
                    "company_name": "台積電", "weight": 23.1,
                }]
                raw_prices = [{
                    "date": "2026-06-22", "ticker": "2330.TW", "isin": "TW0002330008",
                    "company_name": "台積電", "adj_close": 110, "currency": "TWD",
                }]
                raw_factset = [{
                    "snapshot_date": "2026-06-22", "ticker": "2330.TW",
                    "provider_id": "FS-2330", "company_name": "台積電", "currency": "TWD",
                    "target_mean": 150, "eps_n_mean": 5, "eps_n1_mean": 6, "eps_n2_mean": 7,
                }]
                raw_yfinance = [{
                    "snapshot_date": "2026-06-22", "ticker": "2330.TW",
                    "provider_id": "YF-2330", "company_name": "台積電", "currency": "TWD",
                    "targetMeanPrice": 148,
                }]
                for name, payload in (
                    ("holdings", raw_holdings), ("prices", raw_prices),
                    ("factset", raw_factset), ("yfinance", raw_yfinance),
                ):
                    paths[name].write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
                result = engine.run_pipeline(
                    holdings_path=paths["holdings"], prices_path=paths["prices"],
                    factset_path=paths["factset"], yfinance_path=paths["yfinance"],
                    output_dir=root / "candidate", asof_value="2026-06-22",
                )
                self.assertEqual(result["write_result"]["status"], "WRITTEN")
                self.assertEqual(result["records"][0]["fs_forward_pe_n"], 22.0)
                run_dir = Path(result["write_result"]["run_dir"])
                self.assertTrue((run_dir / "manifest.json").exists())
                self.assertTrue((run_dir / "tw_active_etf_holdings_consensus_enriched.csv").exists())
                self.assertTrue((run_dir / "tw_active_etf_holdings_consensus_enriched.json").exists())
                self.assertEqual(result["audit"]["identity_issues"], [])
        finally:
            engine.PARAMS["allow_optional_parquet"] = original_parquet
            engine.PARAMS["allow_optional_duckdb"] = original_duckdb


if __name__ == "__main__":
    unittest.main(verbosity=2)
