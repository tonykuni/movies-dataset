from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

import numpy as np
import pandas as pd

from engine import via_system_orchestrator as orchestrator
from engine.via_fx_context_engine import def_prepare_macro_factors
from engine.via_pit_rotation_backtest_engine import def_prepare_risk_free


OFFICIAL_URL = "https://www.tpex.org.tw/zh-tw/bond/"


def _official_row(**changes: object) -> dict[str, object]:
    row: dict[str, object] = {
        "ObservationDate": "2026-01-02",
        "AvailableAt": "2026-01-02 17:00+08:00",
        "USDTWD": 31.5,
        "DXY": 100.0,
        "Taiwan10YYield": 1.5,
        "Source": "TPEx Government Bond Yield Curve",
        "SourceAuthority": "TAIPEI_EXCHANGE_TPEX",
        "SourceURL": OFFICIAL_URL,
        "SourcePayloadHash": "a" * 64,
        "YieldUnit": "PERCENT",
        "InstrumentId": "TAIWAN_10Y_GOVERNMENT_BOND_YIELD",
        "OfficialSourceVerified": True,
    }
    row.update(changes)
    return row


class OfficialRiskFreeContractTests(unittest.TestCase):
    def test_macro_source_contract_rejects_authority_url_and_hash_spoofs(self) -> None:
        valid = def_prepare_macro_factors(pd.DataFrame([_official_row()])).iloc[0]
        self.assertEqual(
            valid["RiskFreeSourceStatus"],
            "OFFICIAL_TAIWAN_10Y_POINT_IN_TIME",
        )
        self.assertIn(
            "NOT_SOURCE_SIGNATURE", valid["SourcePayloadIntegrityStatus"]
        )

        for changes in (
            {"SourceAuthority": "UNVERIFIED_VENDOR"},
            {"SourceURL": "https://www.tpex.org.tw.attacker.example/yield"},
            {"SourceURL": "http://www.tpex.org.tw/zh-tw/bond/"},
            {"SourcePayloadHash": "not-a-sha256-digest"},
            {"Taiwan10YYield": np.inf},
        ):
            with self.subTest(changes=changes):
                held = def_prepare_macro_factors(
                    pd.DataFrame([_official_row(**changes)])
                ).iloc[0]
                self.assertEqual(
                    held["RiskFreeSourceStatus"],
                    "HOLD_UNVERIFIED_OR_MISSING_TAIWAN_10Y_SOURCE",
                )

    def test_caller_supplied_status_cannot_bypass_source_revalidation(self) -> None:
        spoofed = _official_row(
            SourceAuthority="UNVERIFIED_VENDOR",
            RiskFreeSourceStatus="OFFICIAL_TAIWAN_10Y_POINT_IN_TIME",
        )
        spoofed["Date"] = spoofed.pop("ObservationDate")
        prepared = def_prepare_risk_free(pd.DataFrame([spoofed]))
        self.assertEqual(
            prepared.iloc[0]["RiskFreeSourceStatus"],
            "HOLD_UNVERIFIED_OR_MISSING_TAIWAN_10Y_SOURCE",
        )
        self.assertTrue(np.isnan(prepared.iloc[0]["DailyRiskFree"]))

        missing_evidence = pd.DataFrame(
            [
                {
                    "Date": "2026-01-02",
                    "AvailableAt": "2026-01-02 17:00+08:00",
                    "Taiwan10YYield": 1.5,
                    "RiskFreeSourceStatus": "OFFICIAL_TAIWAN_10Y_POINT_IN_TIME",
                }
            ]
        )
        with self.assertRaisesRegex(ValueError, "cannot prove official Taiwan 10Y"):
            def_prepare_risk_free(missing_evidence)

        nonfinite = _official_row(Taiwan10YYield=np.inf)
        nonfinite["Date"] = nonfinite.pop("ObservationDate")
        with self.assertRaisesRegex(ValueError, "must be finite"):
            def_prepare_risk_free(pd.DataFrame([nonfinite]))


class OptionalRevenueGateTests(unittest.TestCase):
    def test_none_opportunity_set_waits_without_reading_or_processing_market(self) -> None:
        with mock.patch.object(
            orchestrator,
            "def_read_table",
            side_effect=AssertionError("revenue reader must stay behind opportunity gate"),
        ) as reader, mock.patch.object(
            orchestrator,
            "def_prepare_monthly_revenue",
            side_effect=AssertionError("revenue processor must stay behind opportunity gate"),
        ) as processor:
            result = orchestrator.def_build_optional_revenue_reference(
                Path("monthly_revenue.unsupported"),
                "2026-01-05 20:00+08:00",
                pd.DataFrame(),
                "2026-01-05",
                opportunity_tickers=None,
            )

        reader.assert_not_called()
        processor.assert_not_called()
        self.assertTrue(result["reference_company_revenue_latest"].empty)
        self.assertTrue(result["reference_group_revenue_latest"].empty)
        audit = result["reference_revenue_audit"].iloc[0]
        self.assertEqual(
            audit["RevenueReferenceStatus"],
            "OPTIONAL_REFERENCE_WAITING_FOR_CORE_OPPORTUNITY",
        )
        self.assertEqual(audit["OpportunityTickerCount"], 0)
        self.assertEqual(
            audit["ReferenceSelectionPolicy"],
            "STRICT_CORE_POSITIONING_SEQUENCE_STAGE_3_OR_4_ONLY",
        )


class JsonBacktestGridContractTests(unittest.TestCase):
    def test_nondefault_json_dates_and_horizons_reach_backtest_config(self) -> None:
        raw = {
            "rolling_windows": [60, 120, 240],
            "residual_factor_lanes": ["LaggedCap", "LaggedETR"],
            "research_start_date": "2025-02-03",
            "warmup_start_date": "2024-07-01",
            "evaluation_start_dates": ["2025-02-03", "2026-02-03"],
            "forward_horizons": [2, 7, 13],
        }
        pipeline = orchestrator.def_pipeline_config_from_mapping(raw)
        backtest = orchestrator.def_build_backtest_config(
            pipeline, "2026-08-31"
        )
        self.assertEqual(backtest.start_date, "2025-02-03")
        self.assertEqual(backtest.warmup_start_date, "2024-07-01")
        self.assertEqual(
            backtest.evaluation_start_dates, ("2025-02-03", "2026-02-03")
        )
        self.assertEqual(backtest.horizons, (2, 7, 13))
        self.assertEqual(backtest.end_date, "2026-08-31")

    def test_config_runner_parses_nondefault_json_grid(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            config_dir = root / "config"
            config_dir.mkdir()
            local_inputs: dict[str, str] = {}
            for name in (
                "full_market_daily",
                "universe_history",
                "trading_calendar",
                "membership_events",
                "macro_vintages",
                "active_etf_holdings",
            ):
                path = root / f"{name}.csv"
                path.touch()
                local_inputs[name] = path.name
            candidate = root / "candidate.csv"
            candidate.touch()
            config_path = config_dir / "system_config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "local_inputs": local_inputs,
                        "candidate_story_membership": candidate.name,
                        "rolling_windows": [60, 120, 240],
                        "residual_factor_lanes": ["LaggedCap", "LaggedETR"],
                        "research_start_date": "2025-01-15",
                        "warmup_start_date": "2024-03-01",
                        "evaluation_start_dates": ["2025-01-15"],
                        "forward_horizons": [2, 8],
                    }
                ),
                encoding="utf-8",
            )

            with mock.patch.object(
                orchestrator, "def_read_table", return_value=pd.DataFrame()
            ), mock.patch.object(
                orchestrator, "def_run_pipeline_frames", return_value={}
            ) as pipeline_runner:
                orchestrator.def_run_pipeline_from_config(
                    config_path,
                    proposed_at="2026-08-31 20:00+08:00",
                    write_output=False,
                )

        parsed = pipeline_runner.call_args.kwargs["pipeline_config"]
        self.assertEqual(parsed.research_start_date, "2025-01-15")
        self.assertEqual(parsed.warmup_start_date, "2024-03-01")
        self.assertEqual(parsed.evaluation_start_dates, ("2025-01-15",))
        self.assertEqual(parsed.forward_horizons, (2, 8))

    def test_nondefault_warmup_date_caps_factor_input(self) -> None:
        availability = {
            column: "2025-01-03 18:00+08:00"
            for column in orchestrator.REQUIRED_MARKET_AVAILABILITY_COLUMNS
        }
        market = pd.DataFrame(
            [
                {
                    "Date": "2024-12-31",
                    **availability,
                    "IsLimitUpLocked": False,
                    "IsLimitDownLocked": False,
                },
                {
                    "Date": "2025-01-03",
                    **availability,
                    "IsLimitUpLocked": False,
                    "IsLimitDownLocked": False,
                },
            ]
        )
        inputs = {
            "market_daily": market,
            "universe_history": pd.DataFrame(),
            "trading_calendar": pd.DataFrame(
                {"Date": ["2024-12-31", "2025-01-03", "2025-01-06"]}
            ),
            "membership_events": pd.DataFrame(),
            "candidate49": pd.DataFrame(),
            "macro_vintages": pd.DataFrame(),
            "active_etf_holdings": pd.DataFrame(),
        }
        config = orchestrator.PipelineConfig(
            research_start_date="2025-01-03",
            warmup_start_date="2025-01-02",
            evaluation_start_dates=("2025-01-03",),
        )

        def inspect_market(
            received: pd.DataFrame,
            *_: object,
            **__: object,
        ) -> dict[str, pd.DataFrame]:
            self.assertEqual(received["Date"].tolist(), ["2025-01-03"])
            raise RuntimeError("WARMUP_CAP_OBSERVED")

        with mock.patch.object(
            orchestrator,
            "def_run_full_market_factor_pipeline",
            side_effect=inspect_market,
        ), self.assertRaisesRegex(RuntimeError, "WARMUP_CAP_OBSERVED"):
            orchestrator.def_run_pipeline_frames(
                inputs,
                proposed_at="2025-01-03 20:00+08:00",
                pipeline_config=config,
            )

    def test_invalid_or_drifting_json_grid_fails_closed(self) -> None:
        base = {
            "rolling_windows": [60, 120, 240],
            "residual_factor_lanes": ["LaggedCap", "LaggedETR"],
            "research_start_date": "2024-01-01",
            "warmup_start_date": "2023-01-01",
            "evaluation_start_dates": ["2024-01-01"],
            "forward_horizons": [1, 3, 5, 20],
        }
        invalid_variants = (
            {"rolling_windows": [60, 120, 120]},
            {"warmup_start_date": "2024-01-01"},
            {"evaluation_start_dates": ["2024-01-01", "2024-01-01"]},
            {"forward_horizons": [1, 0, 5]},
            {"forward_horizons": [1, 1, 5]},
            {"forward_horizons": [1, 3.5, 5]},
            {
                "formal_model_grid": {
                    "windows": [60, 120, 240],
                    "factor_lanes": ["LaggedETR", "LaggedCap"],
                    "expected_model_count": 6,
                }
            },
            {"stock_positioning": {"windows": [60, 120]}},
        )
        for change in invalid_variants:
            with self.subTest(change=change), self.assertRaises(ValueError):
                orchestrator.def_pipeline_config_from_mapping({**base, **change})


if __name__ == "__main__":
    unittest.main()
