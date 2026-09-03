from __future__ import annotations

"""Focused fail-closed tests for the publication snapshot boundary."""

import unittest

import pandas as pd

from engine.via_system_orchestrator import def_run_pipeline_frames


class OrchestratorSnapshotContractTests(unittest.TestCase):
    def test_requested_trading_session_cannot_silently_fall_back_to_stale_market_data(
        self,
    ) -> None:
        market = pd.DataFrame(
            [
                {
                    "Date": "2026-01-02",
                    "Ticker": "2330.TW",
                    "MarketDataAvailableAt": "2026-01-02 14:30:00+08:00",
                    "ForeignNetAmountAvailableAt": "2026-01-02 18:00:00+08:00",
                    "InvestmentTrustNetAmountAvailableAt": "2026-01-02 18:00:00+08:00",
                    "DealerNetAmountAvailableAt": "2026-01-02 18:00:00+08:00",
                    "MarginBalanceValueAvailableAt": "2026-01-02 21:00:00+08:00",
                    "ShortBalanceValueAvailableAt": "2026-01-02 21:00:00+08:00",
                    "IsLimitUpLocked": False,
                    "IsLimitDownLocked": False,
                }
            ]
        )
        inputs = {
            "market_daily": market,
            "universe_history": pd.DataFrame(),
            "trading_calendar": pd.DataFrame(
                {"Date": ["2026-01-02", "2026-01-05", "2026-01-06"]}
            ),
            "membership_events": pd.DataFrame(),
            "candidate49": pd.DataFrame(),
            "macro_vintages": pd.DataFrame(),
            "active_etf_holdings": pd.DataFrame(),
        }

        with self.assertRaisesRegex(ValueError, "requested as-of trading session is missing"):
            def_run_pipeline_frames(
                inputs,
                proposed_at="2026-01-05 20:00:00+08:00",
                as_of_date="2026-01-05",
            )


if __name__ == "__main__":
    unittest.main()
