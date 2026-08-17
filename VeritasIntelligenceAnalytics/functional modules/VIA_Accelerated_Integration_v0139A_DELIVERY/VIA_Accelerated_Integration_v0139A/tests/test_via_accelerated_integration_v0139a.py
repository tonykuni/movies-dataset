from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import pandas as pd

from engine.via_domain_engine_v0139a import (
    HydraRiskError,
    def_build_fixture_frames,
    def_build_stock_group_classification,
    def_compute_flow_simulation,
    def_compute_group_index,
    def_compute_monthly_revenue_analysis,
    def_normalize_prices,
    def_run_pipeline,
    def_validate_vap_visual_lock,
)


class ViaAcceleratedIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frames = def_build_fixture_frames()

    def test_price_fill_uses_previous_price_but_not_previous_volume(self) -> None:
        prices = self.frames["prices"].iloc[:3].copy()
        prices.loc[1, "Adj Close"] = None
        prices.loc[1, "Volume"] = None
        normalized = def_normalize_prices(prices)
        self.assertEqual(normalized.loc[1, "Adj Close"], normalized.loc[0, "Adj Close"])
        self.assertEqual(normalized.loc[1, "Volume"], 0.0)
        self.assertTrue(bool(normalized.loc[1, "Volume Was Missing"]))

    def test_classification_builds_unique_group_keys(self) -> None:
        output = def_build_stock_group_classification(self.frames["classification"])
        self.assertEqual(len(output), 4)
        self.assertEqual(output["Ticker"].nunique(), 4)
        self.assertTrue(output["Group Key"].str.len().gt(0).all())

    def test_classification_hydra_fails_closed(self) -> None:
        bad = pd.concat(
            [
                self.frames["classification"],
                pd.DataFrame(
                    [
                        {
                            "Ticker": "2330.TW",
                            "Name": "台積電",
                            "Sector": "Conflicting Sector",
                            "Industry": "Foundry",
                            "Theme": "AI Infrastructure",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        with self.assertRaises(HydraRiskError):
            def_build_stock_group_classification(bad)

    def test_group_index_begins_at_base_100(self) -> None:
        output = def_compute_group_index(
            self.frames["prices"], self.frames["classification"]
        )
        first_values = output.groupby("Group")["Group Index"].first()
        self.assertTrue((first_values == 100.0).all())
        self.assertFalse(output["Group Index"].isna().any())

    def test_market_cap_index_uses_governed_lagged_weights(self) -> None:
        output = def_compute_group_index(
            self.frames["prices"],
            self.frames["classification"],
            weighting="market_cap",
        )
        self.assertEqual(set(output["Weighting"]), {"market_cap"})
        self.assertTrue((output.groupby("Group")["Group Index"].first() == 100.0).all())

    def test_monthly_revenue_has_yoy_after_twelve_months(self) -> None:
        detail, group = def_compute_monthly_revenue_analysis(
            self.frames["revenue"], self.frames["classification"]
        )
        later = detail[detail["Revenue Month"] >= pd.Timestamp("2026-01-01")]
        self.assertTrue(later["Revenue YoY Pct"].notna().all())
        self.assertTrue(group["Monthly Revenue"].gt(0).all())

    def test_flow_simulation_generates_signal_and_oos_proxy(self) -> None:
        daily, summary = def_compute_flow_simulation(
            self.frames["flows"],
            self.frames["prices"],
            self.frames["classification"],
        )
        self.assertTrue(set(daily["Flow Signal"]).issubset({"BUY_PROXY", "SELL_PROXY", "NEUTRAL"}))
        self.assertIn("Next Group Return", daily.columns)
        self.assertEqual(summary["Sector"].nunique(), 4)

    def test_end_to_end_fixture_uat_writes_evidence_html_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = def_run_pipeline(
                self.frames, Path(temporary_directory), require_parquet=False
            )
            self.assertEqual(result.error_count, 0)
            self.assertEqual(result.hydra_count, 0)
            self.assertEqual(result.canonical_runtime_executions, 0)
            self.assertEqual(result.network_used, 0)
            self.assertEqual(def_validate_vap_visual_lock(Path(result.html_path)), [])
            self.assertTrue(Path(result.manifest_path).is_file())
            evidence = json.loads(Path(result.evidence_path).read_text(encoding="utf-8"))
            self.assertEqual(evidence["analysis_rounds"], 3)
            self.assertEqual(evidence["final_gate"], result.gate)
            self.assertEqual(len(evidence["components"]), 5)


if __name__ == "__main__":
    unittest.main()
