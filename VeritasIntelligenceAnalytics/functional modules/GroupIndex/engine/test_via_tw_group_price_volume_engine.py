from __future__ import annotations

import unittest
from pathlib import Path

import numpy as np
import pandas as pd

import VIA_TW_Group_PriceVolume_Volatility_Engine_v0100 as engine


class TestVIATWGroupPriceVolumeEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.config = engine.EngineConfig(
            relation_window=60,
            min_observations=60,
            min_group_members=3,
            walk_forward_train_days=120,
            walk_forward_test_days=20,
            walk_forward_step_days=20,
            strict=False,
            write_outputs=False,
        )
        prices, ssot = engine.def_make_synthetic_inputs(cls.config)
        cls.prices = prices
        cls.ssot = ssot
        cls.result = engine.def_run_from_frames(
            prices,
            ssot,
            cls.config,
            synthetic_mode=True,
        )

    def test_uploaded_ssot_counts_and_primary_ownership(self) -> None:
        workbook = (
            Path(__file__).resolve().parents[1]
            / "upload"
            / "383f6e59-fc5b-4aed-867e-909f3201ac23.xlsx"
        )
        if not workbook.exists():
            self.skipTest("Uploaded SSOT workbook is not present in this environment")
        ssot = engine.def_load_group_ssot(workbook)
        self.assertEqual(
            engine.def_ssot_summary(ssot),
            {
                "l1_count": 14,
                "l2_count": 77,
                "membership_rows": 378,
                "unique_tickers": 301,
                "cross_group_tickers": 60,
                "market_locked_rows": 185,
                "market_pending_rows": 193,
            },
        )
        primary_counts = ssot.groupby("Ticker")["Ownership"].apply(
            lambda values: int(values.eq("PRIMARY").sum())
        )
        self.assertTrue(primary_counts.eq(1).all())

    def test_ticker_suffix_uses_twse_and_tpex_market(self) -> None:
        self.assertEqual(engine.def_normalize_ticker("2330", "上市"), "2330.TW")
        self.assertEqual(engine.def_normalize_ticker("6488", "上櫃"), "6488.TWO")
        self.assertEqual(engine.def_normalize_ticker("2330.TW", "上市"), "2330.TW")

    def test_low_comovement_is_never_relabelled_lagger(self) -> None:
        roles = self.result.role_classification
        reviewed = roles.loc[roles["MembershipStatus"].ne("PASS")]
        self.assertTrue(reviewed["TimingRole"].ne("LAGGER").all())
        self.assertTrue({"LEADER", "PEER", "LAGGER"}.issubset(set(roles["TimingRole"])))
        self.assertTrue(
            roles.loc[roles["TimingRole"].eq("LAGGER"), "Interpretation"]
            .eq("TIMING_LAG_NOT_POOR_PERFORMANCE")
            .all()
        )

    def test_group_index_starts_at_100_and_excludes_lagger(self) -> None:
        group_index = self.result.group_index
        self.assertFalse(group_index.empty)
        bases = group_index.sort_values("Date").groupby("GroupId").first()["GroupIndex"]
        self.assertTrue(np.allclose(bases, 100.0))
        eligible = self.result.role_classification.loc[
            self.result.role_classification["IndexEligible"]
        ]
        self.assertTrue(eligible["TimingRole"].isin(["LEADER", "PEER"]).all())

    def test_volume_and_non_day_trade_turnover_are_not_imputed(self) -> None:
        ssot = self.ssot.iloc[[0]].copy()
        ticker = ssot.iloc[0]["Ticker"]
        raw = pd.DataFrame(
            {
                "Date": pd.bdate_range("2024-01-02", periods=3),
                "Ticker": [ticker] * 3,
                "Adj_Open": [99.0, 100.0, 101.0],
                "Adj_High": [101.0, 102.0, 103.0],
                "Adj_Low": [98.0, 99.0, 100.0],
                "Adj_Close": [100.0, 101.0, 102.0],
                "Volume": [100.0, np.nan, 300.0],
                "Turnover": [10_000.0, 20_000.0, 30_000.0],
                "DayTradeTurnover": [1_000.0, np.nan, 3_000.0],
            }
        )
        standardized = engine.def_standardize_price_data(raw, ssot, self.config)
        self.assertTrue(pd.isna(standardized.loc[1, "Volume"]))
        self.assertTrue(pd.isna(standardized.loc[1, "NonDayTradeTurnover"]))
        features = engine.def_compute_stock_features(standardized, self.config)
        self.assertTrue(pd.isna(features.loc[1, "Volume"]))
        self.assertTrue(pd.isna(features.loc[1, "OBV"]))

    def test_raw_close_cannot_replace_adjusted_close(self) -> None:
        ssot = self.ssot.iloc[[0]].copy()
        raw = pd.DataFrame(
            {
                "Date": ["2024-01-02"],
                "Ticker": [ssot.iloc[0]["Ticker"]],
                "Close": [100.0],
                "Volume": [1000.0],
            }
        )
        with self.assertRaisesRegex(ValueError, "Adjusted Close is required"):
            engine.def_standardize_price_data(raw, ssot, self.config)

    def test_validation_has_no_fail_and_walk_forward_is_purged(self) -> None:
        self.assertTrue(self.result.validation_gates["Status"].ne("FAIL").all())
        self.assertFalse(self.result.walk_forward_validation.empty)
        self.assertTrue(
            self.result.walk_forward_validation["PurgeDays"].eq(max(self.config.lead_lags)).all()
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
