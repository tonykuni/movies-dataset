from __future__ import annotations

import json
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import numpy as np
import pandas as pd

from engine.via_active_etf_holdings_engine import (
    def_build_active_etf_analysis,
    def_prepare_holdings_snapshots,
)
from engine.via_append_only_io import def_write_run
from engine.via_candidate49_adapter import def_prepare_candidate49
from engine.via_flow_transfer_matrix_engine import (
    REQUIRED_FULL_MARKET_GATE_STATUS,
    def_build_flow_transfer_outputs,
)
from engine.via_full_market_factor_engine import (
    FACTOR_WEIGHT_COLUMNS,
    TSMC_TICKER,
    def_active_ordinary_universe,
    def_build_ex_tsmc_market_factors,
    def_build_self_test_fixture,
    def_compute_t1_rolling_beta_residuals,
    def_prepare_universe_history,
    def_residual_lineage_values,
    def_run_full_market_factor_pipeline,
    def_validate_trading_session_coverage,
    def_validate_full_market_gate,
)
from engine.via_fx_context_engine import (
    def_add_macro_context,
    def_materialize_macro_asof,
    def_prepare_macro_factors,
)
from engine.via_group_flow_evidence_engine import (
    FlowEvidenceConfig,
    def_add_dynamic_flow_states,
    def_compute_group_flow_daily,
    def_prepare_stock_flow_panel,
)
from engine.via_hierarchical_group_index_engine import (
    HierarchicalIndexConfig,
    def_build_parallel_group_indices,
    def_build_synthetic_inputs as def_build_index_fixture,
)
from engine.via_monthly_revenue_evidence_engine import (
    def_company_revenue_evidence,
    def_materialize_revenue_asof,
    def_prepare_monthly_revenue,
)
from engine.via_pit_membership_engine import (
    REQUIRED_EVENT_COLUMNS,
    def_apply_approved_change_next_session,
    def_materialize_membership_asof,
    def_materialize_membership_history,
)
from engine.via_pipeline_contract_bridge import def_bridge_residual_lane
from engine.via_positioning_transition_engine import (
    EXACT_CONSENSUS_STATUS,
    EX_TSMC_UNIVERSE,
    ORDERED_PHASES,
    def_build_positioning_transition_ledger,
    def_latest_positioning_transition_state,
)
from engine.via_pit_rotation_backtest_engine import (
    BacktestConfig,
    def_compute_index_performance,
    def_prepare_risk_free,
    def_run_multi_horizon_event_study,
)
from engine.via_size_bucket_history_engine import (
    def_append_bucket_history,
    def_compute_quarterly_bucket_history,
)
from engine.via_stock_positioning_engine import (
    REQUIRED_RESIDUAL_UNIVERSE,
    StockPositioningConfig,
    def_build_stock_lane_evidence,
    def_build_stock_positioning_outputs,
    def_map_evidence_to_story_groups,
    def_prepare_residual_evidence,
)
from engine import via_system_orchestrator as system_orchestrator
from engine.via_validation_consensus_engine import (
    EXPECTED_FACTOR_LANES,
    EXPECTED_WINDOWS,
    def_build_membership_review_queue,
    def_reconcile_group_decisions,
    def_reconcile_member_roles,
)


HERE = Path(__file__).resolve()
GROUP_INDEX_ROOT = HERE.parents[2]
CANDIDATE49 = GROUP_INDEX_ROOT / "flow_simulation_v0400" / "data" / "input" / "candidate_membership_v21.csv"


def _official_risk_free(dates: pd.DatetimeIndex) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": dates,
            "Taiwan10YYield": 1.5,
            "AvailableAt": [f"{date:%Y-%m-%d} 17:00+08:00" for date in dates],
            "Source": "TPEx Government Bond Yield Curve",
            "SourceAuthority": "TAIPEI_EXCHANGE_TPEX",
            "SourceURL": "https://www.tpex.org.tw/zh-tw/bond/",
            "SourcePayloadHash": "a" * 64,
            "YieldUnit": "PERCENT",
            "InstrumentId": "TAIWAN_10Y_GOVERNMENT_BOND_YIELD",
            "OfficialSourceVerified": True,
        }
    )


class CandidateAndMembershipContractTests(unittest.TestCase):
    def test_candidate49_exact_shape_and_source_scores_are_quarantined(self) -> None:
        raw = pd.read_csv(CANDIDATE49)
        candidate, audit = def_prepare_candidate49(raw, "2026-09-02 18:00+08:00")

        self.assertEqual(audit["GroupCount"], 49)
        self.assertEqual(audit["MembershipRows"], 252)
        self.assertEqual(audit["DistinctTickers"], 241)
        self.assertEqual(audit["MultiGroupTickerCount"], 10)
        self.assertEqual(audit["BlockedRows"], 2)
        self.assertTrue(audit["DeclaredShapeMatches"])
        self.assertEqual(audit["CandidateRolesConsumedByRuntime"], 0)
        self.assertEqual(audit["IndexEligibleBeforeApproval"], 0)
        self.assertFalse(candidate["IndexEligible"].any())
        self.assertFalse(any("score" in column.lower() for column in candidate.columns))
        self.assertIn("CandidateRolePrior", candidate.columns)

    def test_membership_add_remove_is_next_session_and_future_invariant(self) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=8)
        ledger = pd.DataFrame(columns=list(REQUIRED_EVENT_COLUMNS))
        add = {
            "EventType": "ADD",
            "GroupId": "CPO",
            "GroupName": "CPO",
            "Ticker": "3081.TWO",
            "ApprovedAt": "2026-01-02 18:00+08:00",
            "RecordedAt": "2026-01-02 18:05+08:00",
            "ValidFrom": "",
            "ValidTo": "",
            "SourceVersion": "TEST",
            "Reason": "approved add",
            "ExposureShare": 0.7,
        }
        ledger = def_apply_approved_change_next_session(ledger, add, calendar)
        before_future_event = def_materialize_membership_asof(ledger, "2026-01-05", calendar)
        self.assertEqual(len(before_future_event), 1)
        self.assertEqual(before_future_event.iloc[0]["MembershipValidFrom"], pd.Timestamp("2026-01-05"))
        self.assertAlmostEqual(float(before_future_event.iloc[0]["ExposureShare"]), 0.7)
        self.assertTrue(
            def_materialize_membership_history(
                ledger,
                calendar,
                known_at="2026-01-02 17:00+08:00",
            ).empty
        )
        scheduled_add = def_materialize_membership_history(
            ledger,
            calendar,
            known_at="2026-01-02 19:00+08:00",
        )
        self.assertEqual(scheduled_add.iloc[0]["ValidFrom"], pd.Timestamp("2026-01-05"))

        remove = {
            **add,
            "EventType": "REMOVE",
            "ApprovedAt": "2026-01-06 18:00+08:00",
            "RecordedAt": "2026-01-06 18:05+08:00",
            "Reason": "approved remove",
        }
        ledger_with_future = def_apply_approved_change_next_session(ledger, remove, calendar)
        after_future_event = def_materialize_membership_asof(
            ledger_with_future, "2026-01-05", calendar
        )
        pd.testing.assert_frame_equal(before_future_event, after_future_event)
        self.assertEqual(
            len(def_materialize_membership_asof(ledger_with_future, "2026-01-06", calendar)),
            1,
        )
        self.assertTrue(
            def_materialize_membership_asof(ledger_with_future, "2026-01-07", calendar).empty
        )

        history = def_materialize_membership_history(ledger_with_future, calendar)
        self.assertEqual(history.iloc[0]["ValidFrom"], pd.Timestamp("2026-01-05"))
        self.assertEqual(history.iloc[0]["ValidTo"], pd.Timestamp("2026-01-06"))
        self.assertEqual(history.iloc[0]["HistoryViewStatus"], "DERIVED_FROM_APPEND_ONLY_EVENT_LEDGER")
        self.assertAlmostEqual(float(history.iloc[0]["ExposureShare"]), 0.7)
        scheduled_remove = def_materialize_membership_history(
            ledger_with_future,
            calendar,
            known_at="2026-01-06 19:00+08:00",
        )
        self.assertEqual(
            scheduled_remove.iloc[0]["ValidTo"], pd.Timestamp("2026-01-06")
        )

        invalid_share = {
            **add,
            "GroupId": "OTHER",
            "GroupName": "Other",
            "Ticker": "1112.TW",
            "ExposureShare": 1.01,
        }
        with self.assertRaisesRegex(ValueError, "ExposureShare"):
            def_apply_approved_change_next_session(
                pd.DataFrame(columns=list(REQUIRED_EVENT_COLUMNS)),
                invalid_share,
                calendar,
            )

    def test_keep_exposure_share_creates_a_new_effective_interval(self) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=6)
        add = {
            "EventType": "ADD",
            "GroupId": "CPO",
            "GroupName": "CPO",
            "Ticker": "1111.TW",
            "ApprovedAt": "2026-01-02 18:00+08:00",
            "ValidFrom": "",
            "ValidTo": "",
            "SourceVersion": "TEST",
            "Reason": "initial audited exposure",
            "ExposureShare": 0.7,
        }
        ledger = def_apply_approved_change_next_session(
            pd.DataFrame(columns=list(REQUIRED_EVENT_COLUMNS)), add, calendar
        )
        ledger = def_apply_approved_change_next_session(
            ledger,
            {
                **add,
                "EventType": "KEEP",
                "ApprovedAt": "2026-01-05 18:00+08:00",
                "Reason": "audited exposure revision",
                "ExposureShare": 0.4,
            },
            calendar,
        )

        before_keep = def_materialize_membership_asof(ledger, "2026-01-05", calendar)
        after_keep = def_materialize_membership_asof(ledger, "2026-01-06", calendar)
        self.assertAlmostEqual(float(before_keep.iloc[0]["ExposureShare"]), 0.7)
        self.assertAlmostEqual(float(after_keep.iloc[0]["ExposureShare"]), 0.4)

        history = def_materialize_membership_history(ledger, calendar)
        self.assertEqual(len(history), 2)
        prior, revised = history.sort_values("ValidFrom").reset_index(drop=True).iloc
        self.assertEqual(prior["ValidFrom"], pd.Timestamp("2026-01-05"))
        self.assertEqual(prior["ValidTo"], pd.Timestamp("2026-01-05"))
        self.assertAlmostEqual(float(prior["ExposureShare"]), 0.7)
        self.assertEqual(revised["ValidFrom"], pd.Timestamp("2026-01-06"))
        self.assertTrue(pd.isna(revised["ValidTo"]))
        self.assertAlmostEqual(float(revised["ExposureShare"]), 0.4)


class MarketFactorAndSizeTests(unittest.TestCase):
    def test_full_market_gate_tsmc_isolation_and_t_minus_one_factor_weights(self) -> None:
        daily, universe = def_build_self_test_fixture()
        daily = daily.loc[daily["Date"].isin(sorted(daily["Date"].unique())[:20])]
        validated, _, summary = def_validate_full_market_gate(daily, universe)
        validated.attrs.update(
            def_validate_trading_session_coverage(
                daily, pd.DatetimeIndex(sorted(daily["Date"].unique()))
            )
        )
        weighted, factors = def_build_ex_tsmc_market_factors(validated)
        residuals = def_compute_t1_rolling_beta_residuals(
            weighted, factors, windows=(5,), minimum_observation_ratio=0.6
        )
        unproven_stock_policy = weighted.copy()
        unproven_stock_policy.attrs.pop("UniverseVersionPolicy")
        with self.assertRaisesRegex(ValueError, "revision-aware|provenance"):
            def_compute_t1_rolling_beta_residuals(
                unproven_stock_policy,
                factors,
                windows=(5,),
                minimum_observation_ratio=0.6,
            )
        unproven_factor_cutoff = factors.copy()
        unproven_factor_cutoff.attrs.pop("UniverseKnowledgeCutoffPolicy")
        with self.assertRaisesRegex(ValueError, "revision-aware|provenance"):
            def_compute_t1_rolling_beta_residuals(
                weighted,
                unproven_factor_cutoff,
                windows=(5,),
                minimum_observation_ratio=0.6,
            )
        validation_lane = def_bridge_residual_lane(
            residuals,
            factor_lane="LaggedCap",
            window_days=5,
            as_of_date=residuals["Date"].max(),
        )

        self.assertEqual(summary["GateStatus"], REQUIRED_FULL_MARKET_GATE_STATUS)
        tsmc = weighted.loc[weighted["Ticker"].eq(TSMC_TICKER)]
        self.assertFalse(tsmc["FactorEligibleExTSMC"].any())
        self.assertFalse(residuals["Ticker"].str.startswith("2330").any())
        self.assertFalse(validation_lane["Ticker"].str.startswith("2330").any())
        self.assertEqual(validation_lane.attrs["FactorLane"], "LaggedCap")
        self.assertEqual(validation_lane.attrs["WindowDays"], 5)
        attrless_round_trip = residuals.copy()
        attrless_round_trip.attrs.clear()
        round_trip_lane = def_bridge_residual_lane(
            attrless_round_trip,
            factor_lane="LaggedCap",
            window_days=5,
        )
        pd.testing.assert_series_equal(
            validation_lane["ResidualReturn"],
            round_trip_lane["ResidualReturn"],
        )
        self.assertTrue(
            residuals["ResidualLineageSchema"].eq(
                "VIA_FULL_MARKET_RESIDUAL_LINEAGE_V2"
            ).all()
        )
        self.assertTrue(
            residuals["ResidualLineageUniverseVersionPolicy"].eq(
                "LATEST_RECORDED_REVISION_KNOWN_BY_SESSION_MARKET_DATA_CUTOFF"
            ).all()
        )
        self.assertTrue(
            residuals["ResidualLineageUniverseKnowledgeCutoffPolicy"].eq(
                "UNIVERSE_EVENT_KNOWN_AT_NOT_AFTER_SESSION_MARKET_DATA_AVAILABLE_AT"
            ).all()
        )
        stock_round_trip = validation_lane.copy()
        stock_round_trip.attrs.clear()
        self.assertEqual(
            len(def_prepare_residual_evidence(stock_round_trip)),
            len(stock_round_trip),
        )
        with tempfile.TemporaryDirectory() as temporary_directory:
            csv_path = Path(temporary_directory) / "rolling_residuals.csv"
            residuals.to_csv(csv_path, index=False)
            csv_round_trip = pd.read_csv(csv_path)
            csv_lane = def_bridge_residual_lane(
                csv_round_trip,
                factor_lane="LaggedCap",
                window_days=5,
            )
            self.assertEqual(
                len(def_prepare_residual_evidence(csv_lane)),
                len(csv_lane),
            )
        missing_revision_lineage = stock_round_trip.drop(
            columns=["ResidualLineageUniverseVersionPolicy"]
        )
        with self.assertRaisesRegex(
            ValueError, "ResidualLineageUniverseVersionPolicy"
        ):
            def_prepare_residual_evidence(missing_revision_lineage)
        forged_old_policy = stock_round_trip.copy()
        forged_old_policy[
            "ResidualLineageUniverseKnowledgeCutoffPolicy"
        ] = "UNIVERSE_KNOWN_AT_NOT_AFTER_LOCAL_DATE"
        lineage_columns = [
            column
            for column in forged_old_policy.columns
            if column.startswith("ResidualLineage")
            and column != "ResidualLineageId"
        ]
        forged_digest_fields = {
            column: (
                bool(forged_old_policy[column].iloc[0])
                if isinstance(
                    forged_old_policy[column].iloc[0], (bool, np.bool_)
                )
                else str(forged_old_policy[column].iloc[0])
            )
            for column in lineage_columns
        }
        forged_old_policy["ResidualLineageId"] = hashlib.sha256(
            json.dumps(
                forged_digest_fields,
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest().upper()
        with self.assertRaisesRegex(
            ValueError, "ResidualLineageUniverseKnowledgeCutoffPolicy"
        ):
            def_prepare_residual_evidence(forged_old_policy)
        attrs_only = residuals.drop(
            columns=[
                column
                for column in residuals.columns
                if column.startswith("ResidualLineage")
            ]
        ).copy()
        attrs_only.attrs.update(residuals.attrs)
        with self.assertRaisesRegex(ValueError, "row-level lineage"):
            def_bridge_residual_lane(
                attrs_only,
                factor_lane="LaggedCap",
                window_days=5,
            )
        contradictory = residuals.copy()
        contradictory["ResidualLineageMarketUniverse"] = "UNPROVEN_SUBSET"
        with self.assertRaisesRegex(ValueError, "lineage mismatch"):
            def_bridge_residual_lane(
                contradictory,
                factor_lane="LaggedCap",
                window_days=5,
            )
        status_mismatch = residuals.copy()
        pass_row = status_mismatch["BetaStatus_LaggedCap_5D"].eq("PASS")
        status_mismatch.loc[
            status_mismatch.index[pass_row][0], "Residual_LaggedCap_5D"
        ] = np.nan
        with self.assertRaisesRegex(ValueError, "status and residual value disagree"):
            def_bridge_residual_lane(
                status_mismatch,
                factor_lane="LaggedCap",
                window_days=5,
            )
        fractional_policy = residuals.copy()
        fractional_policy["BetaWindowPolicy_LaggedCap_5D"] = (
            "T_MINUS_1_ONLY;window=5;minimum=2.5"
        )
        with self.assertRaisesRegex(ValueError, "timing policy"):
            def_bridge_residual_lane(
                fractional_policy,
                factor_lane="LaggedCap",
                window_days=5,
            )
        fractional_observations = residuals.copy()
        fractional_observations["BetaObservations_LaggedCap_5D"] = 2.5
        with self.assertRaisesRegex(ValueError, "beta observations are invalid"):
            def_bridge_residual_lane(
                fractional_observations,
                factor_lane="LaggedCap",
                window_days=5,
            )
        impossible_chronology = residuals.copy()
        first_ticker_row = impossible_chronology.sort_values(
            ["Ticker", "Date"], kind="stable"
        ).index[0]
        impossible_chronology.loc[
            first_ticker_row,
            [
                "Residual_LaggedCap_5D",
                "BetaStatus_LaggedCap_5D",
                "BetaObservations_LaggedCap_5D",
            ],
        ] = [0.1, "PASS", 5]
        with self.assertRaisesRegex(ValueError, "provable prior-row history"):
            def_bridge_residual_lane(
                impossible_chronology,
                factor_lane="LaggedCap",
                window_days=5,
            )
        incomplete_residual = residuals.drop(
            residuals.index[
                residuals["Date"].eq(residuals["Date"].max())
                & residuals["Ticker"].eq("6488.TWO")
            ][0]
        )
        with self.assertRaisesRegex(
            ValueError, "complete ex-2330 daily universe|daily roster hash mismatch"
        ):
            def_bridge_residual_lane(
                incomplete_residual,
                factor_lane="LaggedCap",
                window_days=5,
            )
        substituted_roster = residuals.copy()
        substituted_roster.loc[
            substituted_roster["Ticker"].eq("1101.TW"), "Ticker"
        ] = "9999.TW"
        with self.assertRaisesRegex(ValueError, "daily roster hash mismatch"):
            def_bridge_residual_lane(
                substituted_roster,
                factor_lane="LaggedCap",
                window_days=5,
            )
        self.assertEqual(
            residuals["ResidualLineageSourceUniverse"].unique().tolist(),
            ["TWSE_TPEX_COMMON_EQUITY_WITH_2330_ANCHOR"],
        )
        for weight_column in FACTOR_WEIGHT_COLUMNS.values():
            self.assertTrue(tsmc[weight_column].isna().all())
        self.assertTrue(
            weighted.loc[weighted["Date"].eq(weighted["Date"].max()), list(FACTOR_WEIGHT_COLUMNS.values())]
            .sum()
            .pipe(lambda values: np.allclose(values.to_numpy(dtype=float), 1.0))
        )

        latest = residuals["Date"].max()
        baseline_beta = residuals.loc[residuals["Date"].eq(latest), "Beta_LaggedCap_5D"].to_numpy()
        mutated = weighted.copy()
        mutated.loc[mutated["Date"].eq(latest), "Return"] *= 100.0
        replay = def_compute_t1_rolling_beta_residuals(
            mutated, factors, windows=(5,), minimum_observation_ratio=0.6
        )
        replay_beta = replay.loc[replay["Date"].eq(latest), "Beta_LaggedCap_5D"].to_numpy()
        np.testing.assert_allclose(baseline_beta, replay_beta, equal_nan=True)

        incomplete = daily.loc[
            ~(
                daily["Date"].eq(daily["Date"].min())
                & daily["Ticker"].eq("6488.TWO")
            )
        ]
        with self.assertRaisesRegex(ValueError, "full TWSE/TPEX"):
            def_validate_full_market_gate(incomplete, universe)

        full_dates = pd.DatetimeIndex(sorted(daily["Date"].unique()))
        missing_session = daily.loc[daily["Date"].ne(full_dates[10])]
        with self.assertRaisesRegex(ValueError, "missing entire trading sessions"):
            def_validate_trading_session_coverage(missing_session, full_dates)

        delayed_market_data = daily.copy()
        delayed_market_data.loc[
            delayed_market_data.index[0], "MarketDataAvailableAt"
        ] = f"{full_dates[1]:%Y-%m-%d} 14:30:00+08:00"
        with self.assertRaisesRegex(ValueError, "available on its own session"):
            def_validate_full_market_gate(delayed_market_data, universe)

    def test_full_market_gate_blocks_observed_ticker_not_yet_known_in_roster(self) -> None:
        daily, universe = def_build_self_test_fixture()
        dates = pd.DatetimeIndex(sorted(daily["Date"].unique())[:5])
        daily = daily.loc[daily["Date"].isin(dates)].copy()
        universe = universe.copy()
        universe.loc[
            universe["Ticker"].eq("1101.TW"), "KnownAt"
        ] = f"{dates[0]:%Y-%m-%d} 18:00:00+08:00"

        _, quality, summary = def_validate_full_market_gate(
            daily, universe, fail_closed=False
        )
        first = quality.loc[quality["Date"].eq(dates[0])].iloc[0]
        self.assertEqual(int(first["UnexpectedObservedTickers"]), 1)
        self.assertEqual(first["UnexpectedTickerSample"], "1101.TW")
        self.assertEqual(summary["GateStatus"], "BLOCKED_FULL_MARKET_GATE")
        with self.assertRaisesRegex(
            ValueError, "UnexpectedObservedTickers.*1101[.]TW"
        ):
            def_validate_full_market_gate(daily, universe, fail_closed=True)

    def test_versioned_universe_revision_is_pit_and_future_append_is_invariant(self) -> None:
        daily, legacy = def_build_self_test_fixture()
        dates = pd.DatetimeIndex(sorted(daily["Date"].unique())[:12])
        daily = daily.loc[daily["Date"].isin(dates)].copy()
        versioned = legacy.copy()
        versioned["UniverseRecordId"] = "REC-" + versioned["Ticker"]
        versioned["RevisionId"] = "V1"
        versioned["RecordedAt"] = versioned["KnownAt"]
        versioned["RevisionAction"] = "UPSERT"

        baseline = def_run_full_market_factor_pipeline(
            daily,
            versioned,
            trading_calendar=dates,
            windows=(5,),
        )
        future_revision = versioned.loc[
            versioned["Ticker"].eq("1101.TW")
        ].iloc[[0]].copy()
        future_revision["RevisionId"] = "V2"
        # KnownAt is deliberately backdated; RecordedAt prevents the revision
        # and its future schema/payload from leaking into this replay.
        future_revision["KnownAt"] = f"{dates[0]:%Y-%m-%d} 08:00:00+08:00"
        future_revision["RecordedAt"] = f"{dates[-1] + pd.Timedelta(days=20):%Y-%m-%d} 09:00:00+08:00"
        future_revision["ValidTo"] = "NOT_A_DATE_YET"
        future_revision["FutureSchemaField"] = "introduced-after-cutoff"
        replay = def_run_full_market_factor_pipeline(
            daily,
            pd.concat([versioned, future_revision], ignore_index=True),
            trading_calendar=dates,
            windows=(5,),
        )

        for key in (
            "validated_panel",
            "gate_daily",
            "market_factors",
            "rolling_residuals",
        ):
            pd.testing.assert_frame_equal(baseline[key], replay[key])

        revised = versioned.loc[
            versioned["Ticker"].eq("1101.TW")
        ].iloc[[0]].copy()
        revised["RevisionId"] = "V2"
        revised["KnownAt"] = f"{dates[0]:%Y-%m-%d} 08:00:00+08:00"
        revised["RecordedAt"] = f"{dates[7]:%Y-%m-%d} 08:00:00+08:00"
        revised["ValidTo"] = dates[4]
        prepared = def_prepare_universe_history(
            pd.concat([versioned, revised], ignore_index=True)
        )
        before_revision = def_active_ordinary_universe(
            prepared,
            dates[6],
            knowledge_cutoff_at=f"{dates[6]:%Y-%m-%d} 14:30:00+08:00",
        )
        after_revision = def_active_ordinary_universe(
            prepared,
            dates[8],
            knowledge_cutoff_at=f"{dates[8]:%Y-%m-%d} 14:30:00+08:00",
        )
        self.assertIn("1101.TW", set(before_revision["Ticker"]))
        self.assertNotIn("1101.TW", set(after_revision["Ticker"]))

        overlapping_record = versioned.loc[
            versioned["Ticker"].eq("1101.TW")
        ].iloc[[0]].copy()
        overlapping_record["UniverseRecordId"] = "REC-1101-TW-DUPLICATE"
        prepared_overlap = def_prepare_universe_history(
            pd.concat([versioned, overlapping_record], ignore_index=True)
        )
        with self.assertRaisesRegex(ValueError, "multiple active universe records overlap"):
            def_active_ordinary_universe(
                prepared_overlap,
                dates[2],
                knowledge_cutoff_at=f"{dates[2]:%Y-%m-%d} 14:30:00+08:00",
            )

    def test_size_is_full_market_ex_tsmc_and_append_is_idempotent(self) -> None:
        dates = pd.to_datetime(["2026-03-30", "2026-03-31", "2026-04-01", "2026-04-02"])
        tickers = ["2330.TW", "1101.TW", "2308.TW", "6488.TWO"]
        rows = []
        for date_number, date in enumerate(dates):
            for ticker_number, ticker in enumerate(tickers, start=1):
                rows.append(
                    {
                        "Date": date,
                        "Ticker": ticker,
                        "Market": "TPEX" if ticker.endswith(".TWO") else "TWSE",
                        "AssetType": "COMMON_STOCK",
                        "MarketCap": ticker_number * 1_000 + date_number,
                        "ETR": ticker_number * 100 + date_number,
                    }
                )
        history = def_compute_quarterly_bucket_history(pd.DataFrame(rows))

        self.assertEqual(set(history["WindowDays"]), {60, 120, 240})
        anchor = history.loc[history["Ticker"].eq("2330")]
        self.assertTrue(anchor["MarketCapTier"].eq("ANCHOR_EXCLUDED").all())
        self.assertTrue(anchor["EffectiveTurnoverTier"].eq("ANCHOR_EXCLUDED").all())
        self.assertTrue((history["SnapshotDate"] < history["EffectiveDate"]).all())
        replay = def_append_bucket_history(history, history)
        pd.testing.assert_frame_equal(history, replay)


class FlowEvidenceTests(unittest.TestCase):
    @staticmethod
    def _stock_flow_fixture() -> pd.DataFrame:
        dates = pd.bdate_range("2026-01-02", periods=4)
        rows = []
        for position, date in enumerate(dates):
            for ticker, exchange, base_etr in (
                ("2330.TW", "TWSE", 1_000.0),
                ("1111.TW", "TWSE", 100.0),
                ("2222.TWO", "TPEX", 200.0),
            ):
                etr = 10.0 if ticker == "1111.TW" and position == 1 else base_etr
                rows.append(
                    {
                        "Date": date,
                        "Ticker": ticker,
                        "Exchange": exchange,
                        "AssetType": "COMMON_STOCK",
                        "TurnoverValue": etr + 20.0,
                        "DayTradeTurnoverValue": 20.0,
                        "Adj_Close": 100.0 + position,
                        "MarketDataAvailableAt": f"{date:%Y-%m-%d} 14:30+08:00",
                        "ForeignNetAmount": 5.0,
                        "ForeignNetAmountAvailableAt": f"{date:%Y-%m-%d} 17:00+08:00",
                        "InvestmentTrustNetAmount": 2.0,
                        "InvestmentTrustNetAmountAvailableAt": f"{date:%Y-%m-%d} 17:00+08:00",
                        "DealerNetAmount": 1.0,
                        "DealerNetAmountAvailableAt": f"{date:%Y-%m-%d} 17:00+08:00",
                        "MarginBalanceValue": 10.0 + position,
                        "MarginBalanceValueAvailableAt": f"{date:%Y-%m-%d} 18:00+08:00",
                        "ShortBalanceValue": 5.0 + position,
                        "ShortBalanceValueAvailableAt": f"{date:%Y-%m-%d} 18:00+08:00",
                        "ETFActiveValue": 3.0,
                        "ETFActiveValueAvailableAt": f"{date:%Y-%m-%d} 19:00+08:00",
                        "IsLimitUpLocked": ticker == "1111.TW" and position == 1,
                        "IsLimitDownLocked": False,
                    }
                )
        return pd.DataFrame(rows)

    def test_limit_lock_protection_partial_coverage_and_latest_availability(self) -> None:
        prepared = def_prepare_stock_flow_panel(self._stock_flow_fixture())
        locked = prepared.loc[
            prepared["Ticker"].eq("1111")
            & prepared["Date"].eq(pd.Timestamp("2026-01-05"))
        ].iloc[0]
        self.assertEqual(locked["ETR"], 10.0)
        self.assertEqual(locked["AttentionETR"], 100.0)
        self.assertEqual(
            locked["LimitLockAttentionPolicy"],
            "LIMIT_UP_USES_MAX_CURRENT_OR_PRIOR_SESSION_ETR",
        )

        membership = pd.DataFrame(
            [
                {"GroupId": "G", "GroupName": "G", "Ticker": "1111.TW", "Decision": "APPROVED"},
                {"GroupId": "BAD", "GroupName": "BAD", "Ticker": "9999.TW", "Decision": "APPROVED"},
            ]
        )
        daily = def_compute_group_flow_daily(prepared, membership)
        protected = daily.loc[
            daily["GroupId"].eq("G")
            & daily["Date"].eq(pd.Timestamp("2026-01-05"))
        ].iloc[0]
        self.assertEqual(protected["RawGroupETR"], 10.0)
        self.assertEqual(protected["GroupETR"], 100.0)
        self.assertEqual(protected["LimitUpProtectedMemberCount"], 1)
        self.assertEqual(
            daily.loc[daily["GroupId"].eq("BAD"), "GroupCoverageStatus"].iloc[0],
            "HOLD_PARTIAL_GROUP_MEMBER_COVERAGE",
        )
        self.assertTrue(daily.loc[daily["GroupId"].eq("BAD"), "AttentionShare"].isna().all())

        price = daily[["Date", "GroupId"]].copy()
        price["GroupReturn"] = 0.0
        price["IndexStatus"] = "PASS"
        calendar = pd.bdate_range("2026-01-02", periods=5)
        dynamic = def_add_dynamic_flow_states(
            daily,
            price,
            config=FlowEvidenceConfig(windows=(2,)),
            trading_calendar=calendar,
        )
        known = dynamic.loc[
            dynamic["GroupId"].eq("G")
            & dynamic["Date"].lt(dynamic["Date"].max())
        ]
        expected_local_hours = {
            "FOREIGN": 17,
            "DOMESTIC_EX_FOREIGN": 17,
            "ACTIVE_ETF": 19,
        }
        for lane, expected_hour in expected_local_hours.items():
            lane_times = known.loc[
                known["DirectionalLane"].eq(lane), "SignalAvailableAt"
            ]
            self.assertTrue(lane_times.notna().all())
            self.assertTrue(
                lane_times.dt.tz_convert("Asia/Taipei").dt.hour.eq(expected_hour).all()
            )
        self.assertEqual(
            set(dynamic["DirectionalLane"]),
            {"FOREIGN", "DOMESTIC_EX_FOREIGN", "ACTIVE_ETF"},
        )
        self.assertTrue(
            dynamic.loc[dynamic["GroupId"].eq("G"), "TradingCalendarStatus"]
            .eq("PASS_FORMAL_TRADING_CALENDAR_SUPPLIED")
            .all()
        )

    def test_direction_requires_economic_sign_not_only_relative_change(self) -> None:
        dates = pd.bdate_range("2026-01-02", periods=5)
        common = {
            "GroupId": "G",
            "GroupName": "G",
            "MemberCount": 1,
            "ComparisonMemberCountExTSMC": 1,
            "ObservedMemberCount": 1,
            "ETRCoveredMemberCount": 1,
            "GroupCoverageStatus": "PASS",
            "MarketCoverageStatus": "PASS",
            "LimitUpLockedCount": 0,
            "LimitLockUnknownCount": 0,
            "ForeignNetAmountCoverage": 1,
            "InstitutionalDomesticNetAmountCoverage": 1,
            "ETFActiveValueCoverage": 1,
        }

        def rows(direction: list[float], attention: list[float]) -> pd.DataFrame:
            output = []
            for date, flow, share in zip(dates, direction, attention, strict=True):
                output.append(
                    {
                        **common,
                        "Date": date,
                        "AttentionShare": share,
                        "ForeignNetAmount": flow,
                        "InstitutionalDomesticNetAmount": flow,
                        "InvestmentTrustNetAmount": flow,
                        "DealerNetAmount": flow,
                        "MarginFinancingChangeAmount": np.nan,
                        "ShortSellingChangeAmount": np.nan,
                        "ETFActiveValue": flow,
                        "GroupPriceReturn": 0.0,
                        "AttentionAvailableAt": f"{date:%Y-%m-%d} 14:30+08:00",
                        "ForeignNetAmountAvailableAt": f"{date:%Y-%m-%d} 17:00+08:00",
                        "InstitutionalDomesticNetAmountAvailableAt": f"{date:%Y-%m-%d} 17:00+08:00",
                        "ETFActiveValueAvailableAt": f"{date:%Y-%m-%d} 18:00+08:00",
                    }
                )
            return pd.DataFrame(output)

        negative_improving = def_add_dynamic_flow_states(
            rows([-10, -9, -8, -7, -6], [0.10, 0.11, 0.12, 0.13, 0.14]),
            config=FlowEvidenceConfig(windows=(4,)),
            trading_calendar=pd.bdate_range("2026-01-02", periods=6),
        )
        negative_target = negative_improving.loc[
            negative_improving["Date"].eq(dates[-2])
        ]
        self.assertFalse(
            negative_target["EarlyPositioningState_4D"]
            .eq("DIRECTIONAL_ACCUMULATION_WATCH")
            .any()
        )

        positive_slowing = def_add_dynamic_flow_states(
            rows([10, 9, 8, 7, 6], [0.14, 0.13, 0.12, 0.11, 0.10]),
            config=FlowEvidenceConfig(windows=(4,)),
            trading_calendar=pd.bdate_range("2026-01-02", periods=6),
        )
        positive_target = positive_slowing.loc[
            positive_slowing["Date"].eq(dates[-2])
        ]
        self.assertFalse(
            positive_target["EarlyExitState_4D"].eq("EARLY_EXIT_RISK").any()
        )

    def test_dynamic_states_are_lane_specific_and_fail_closed(self) -> None:
        dates = pd.bdate_range("2026-01-02", periods=5)
        # The formal calendar intentionally skips the next weekday to prove
        # that EffectiveDate is not inferred from weekday arithmetic.
        calendar = dates.append(pd.DatetimeIndex(["2026-01-12"]))
        rows: list[dict[str, object]] = []
        foreign = [1.0, 2.0, 3.0, 4.0, 5.0]
        domestic = [-1.0, -2.0, -3.0, -4.0, -5.0]
        active_etf = [1.0, 2.0, 3.0, np.nan, 5.0]
        for position, date in enumerate(dates):
            rows.append(
                {
                    "Date": date,
                    "GroupId": "G",
                    "GroupName": "G",
                    "MemberCount": 1,
                    "ComparisonMemberCountExTSMC": 1,
                    "ObservedMemberCount": 1,
                    "ETRCoveredMemberCount": 1,
                    "GroupCoverageStatus": "PASS",
                    "MarketCoverageStatus": "PASS",
                    "LimitUpLockedCount": 0,
                    "LimitLockUnknownCount": 0,
                    "AttentionShare": 0.10 + position * 0.01,
                    "AttentionAvailableAt": f"{date:%Y-%m-%d} 14:30+08:00",
                    "ForeignNetAmount": foreign[position],
                    "ForeignNetAmountCoverage": 1,
                    "ForeignNetAmountAvailableAt": f"{date:%Y-%m-%d} 17:00+08:00",
                    "InstitutionalDomesticNetAmount": domestic[position],
                    "InstitutionalDomesticNetAmountCoverage": 1,
                    "InstitutionalDomesticNetAmountAvailableAt": f"{date:%Y-%m-%d} 18:00+08:00",
                    "InvestmentTrustNetAmount": domestic[position] / 2.0,
                    "DealerNetAmount": domestic[position] / 2.0,
                    "MarginFinancingChangeAmount": np.nan,
                    "ShortSellingChangeAmount": np.nan,
                    "ETFActiveValue": active_etf[position],
                    "ETFActiveValueCoverage": 1 if position != 3 else 0,
                    "ETFActiveValueAvailableAt": (
                        f"{date:%Y-%m-%d} 19:00+08:00"
                        if position != 3
                        else pd.NaT
                    ),
                    "GroupPriceReturn": 0.05 - position * 0.01,
                }
            )
        source = pd.DataFrame(rows)
        dynamic = def_add_dynamic_flow_states(
            source,
            config=FlowEvidenceConfig(windows=(4,)),
            trading_calendar=calendar,
        )
        target = dynamic.loc[dynamic["Date"].eq(dates[3])].set_index(
            "DirectionalLane"
        )

        self.assertEqual(
            target.loc["FOREIGN", "EarlyPositioningState_4D"],
            "DIRECTIONAL_ACCUMULATION_WATCH",
        )
        self.assertEqual(
            target.loc["DOMESTIC_EX_FOREIGN", "EarlyPositioningState_4D"],
            "ATTENTION_EXPANSION_ONLY",
        )
        self.assertEqual(
            target.loc["ACTIVE_ETF", "EarlyPositioningState_4D"],
            "HOLD_INCOMPLETE_POINT_IN_TIME_EVIDENCE",
        )
        self.assertEqual(
            target.loc["ACTIVE_ETF", "DirectionalCoverageStatus"],
            "HOLD_PARTIAL_DIRECTIONAL_LANE_COVERAGE",
        )
        self.assertEqual(
            target.loc["FOREIGN", "EffectiveDate"], pd.Timestamp(dates[4])
        )
        final_foreign = dynamic.loc[
            dynamic["Date"].eq(dates[4])
            & dynamic["DirectionalLane"].eq("FOREIGN")
        ].iloc[0]
        self.assertEqual(final_foreign["EffectiveDate"], pd.Timestamp("2026-01-12"))
        self.assertEqual(
            target.loc["FOREIGN", "DecisionAggregationPolicy"],
            "SEPARATE_DIRECTIONAL_LANE_ROWS_NO_CROSS_LANE_ANY_OR_VOTE",
        )
        self.assertNotIn(
            "DIRECTIONAL_CONFLICT_NO_ACCUMULATION_CLAIM",
            set(target["EarlyPositioningState_4D"]),
        )

        missing_price = source.copy()
        missing_price.loc[
            missing_price["Date"].eq(dates[3]), "GroupPriceReturn"
        ] = np.nan
        price_hold = def_add_dynamic_flow_states(
            missing_price,
            config=FlowEvidenceConfig(windows=(4,)),
            trading_calendar=calendar,
        )
        price_target = price_hold.loc[price_hold["Date"].eq(dates[3])]
        self.assertTrue(
            price_target["EarlyPositioningState_4D"]
            .eq("HOLD_INCOMPLETE_POINT_IN_TIME_EVIDENCE")
            .all()
        )
        self.assertFalse(
            price_target["EarlyPositioningState_4D"]
            .eq("DIRECTIONAL_ACCUMULATION_WATCH")
            .any()
        )

        missing_time = source.copy()
        missing_time.loc[
            missing_time["Date"].eq(dates[3]),
            "ForeignNetAmountAvailableAt",
        ] = pd.NaT
        time_hold = def_add_dynamic_flow_states(
            missing_time,
            config=FlowEvidenceConfig(windows=(4,)),
            trading_calendar=calendar,
        )
        time_target = time_hold.loc[
            time_hold["Date"].eq(dates[3])
            & time_hold["DirectionalLane"].eq("FOREIGN")
        ].iloc[0]
        self.assertEqual(
            time_target["DirectionalCoverageStatus"],
            "HOLD_DIRECTIONAL_AVAILABLE_AT_MISSING",
        )
        self.assertEqual(
            time_target["EarlyPositioningState_4D"],
            "HOLD_INCOMPLETE_POINT_IN_TIME_EVIDENCE",
        )
        domestic_time_target = time_hold.loc[
            time_hold["Date"].eq(dates[3])
            & time_hold["DirectionalLane"].eq("DOMESTIC_EX_FOREIGN")
        ].iloc[0]
        self.assertEqual(
            domestic_time_target["DirectionalCoverageStatus"],
            "PASS_COMPLETE_DIRECTIONAL_LANE",
        )

        insufficient = dynamic.loc[dynamic["Date"].eq(dates[1])]
        self.assertTrue(
            insufficient["EarlyPositioningState_4D"]
            .eq("HOLD_INSUFFICIENT_ROLLING_HISTORY")
            .all()
        )

        no_calendar = def_add_dynamic_flow_states(
            source,
            config=FlowEvidenceConfig(windows=(4,)),
        )
        self.assertTrue(
            no_calendar["SignalTimingStatus"]
            .eq("HOLD_FORMAL_TRADING_CALENDAR_REQUIRED")
            .all()
        )
        self.assertFalse(
            no_calendar["EarlyPositioningState_4D"]
            .eq("DIRECTIONAL_ACCUMULATION_WATCH")
            .any()
        )

    def test_directional_value_without_available_at_is_removed(self) -> None:
        raw = self._stock_flow_fixture().head(1).copy()
        raw["ForeignNetAmountAvailableAt"] = pd.NaT
        prepared = def_prepare_stock_flow_panel(raw)
        self.assertTrue(prepared["ForeignNetAmount"].isna().all())
        self.assertEqual(
            prepared.iloc[0]["ForeignNetAmountTimeStatus"],
            "HOLD_VALUE_WITHOUT_AVAILABLE_AT",
        )


class ETFAndTransferTests(unittest.TestCase):
    def test_etf_and_transfer_use_same_conserved_multigroup_exposure(self) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=6)
        holdings = pd.DataFrame(
            [
                {
                    "ETFId": "00981A",
                    "PortfolioDate": "2026-01-02",
                    "AvailableAt": "2026-01-02 18:00+08:00",
                    "Ticker": "1111.TW",
                    "Shares": 100,
                    "Weight": 10,
                    "ETFUnitsOutstanding": 1000,
                    "Price": 50,
                    "SnapshotComplete": True,
                    "SourceHash": "S1",
                },
                {
                    "ETFId": "00981A",
                    "PortfolioDate": "2026-01-05",
                    "AvailableAt": "2026-01-05 18:00+08:00",
                    "Ticker": "1111.TW",
                    "Shares": 120,
                    "Weight": 11,
                    "ETFUnitsOutstanding": 1000,
                    "Price": 51,
                    "SnapshotComplete": True,
                    "SourceHash": "S2",
                },
            ]
        )
        membership = pd.DataFrame(
            [
                {"GroupId": "AI", "GroupName": "AI", "Ticker": "1111.TW", "Decision": "APPROVED", "ExposureShare": 0.75},
                {"GroupId": "COOL", "GroupName": "AI散熱", "Ticker": "1111.TW", "Decision": "APPROVED", "ExposureShare": 0.25},
            ]
        )
        prepared_holdings = def_prepare_holdings_snapshots(holdings)
        self.assertIn("WeightPct", prepared_holdings.columns)
        self.assertIn("ETFUnits", prepared_holdings.columns)
        etf = def_build_active_etf_analysis(
            holdings,
            "2026-01-06 00:00+08:00",
            membership=membership,
            trading_calendar=calendar,
        )
        mapped = etf["story_event_views"]
        conserved_event = mapped.loc[
            mapped["StoryView"].eq("CAPITAL_CONSERVED")
            & mapped["PortfolioDate"].eq(pd.Timestamp("2026-01-05"))
        ]
        fractions = conserved_event.set_index("GroupId")["AllocationFraction"]
        self.assertAlmostEqual(float(fractions["AI"]), 0.75)
        self.assertAlmostEqual(float(fractions["COOL"]), 0.25)
        self.assertEqual(etf["story_event_conservation"]["Status"], "PASS")

        stock_rows = []
        for date in calendar[:3]:
            for ticker, etr in (("1111.TW", 100.0), ("2222.TWO", 80.0), ("2330.TW", 1000.0)):
                stock_rows.append(
                    {
                        "Date": date,
                        "Ticker": ticker,
                        "AttentionETR": etr,
                        "LimitLockDataStatus": "PASS_LIMIT_LOCK_FLAGS",
                        "ForeignNetAmount": 1.0,
                        "InvestmentTrustNetAmount": 1.0,
                        "DealerNetAmount": 1.0,
                        "MarginFinancingChangeAmount": 1.0,
                        "ShortSellingChangeAmount": -1.0,
                        "ETFActiveValue": 1.0,
                    }
                )
        stock = pd.DataFrame(stock_rows)
        stock.attrs["FullMarketGateStatus"] = REQUIRED_FULL_MARKET_GATE_STATUS
        transfer = def_build_flow_transfer_outputs(stock, membership)
        ledger = transfer["conserved_ledger"]
        weights = ledger.loc[ledger["Ticker"].eq("1111")].groupby("GroupId")["AllocationWeight"].first()
        self.assertAlmostEqual(float(weights["AI"]), 0.75)
        self.assertAlmostEqual(float(weights["COOL"]), 0.25)
        self.assertEqual(transfer["quality"]["Status"], "PASS")
        self.assertTrue(
            np.allclose(
                ledger.groupby(["AppliedDate", "Ticker"])["AllocationWeight"].sum().to_numpy(),
                1.0,
            )
        )
        self.assertIn("UNMAPPED", set(ledger["GroupId"]))
        self.assertNotIn("2330", set(ledger["Ticker"]))

        no_provenance = stock.copy()
        no_provenance.attrs.clear()
        with self.assertRaisesRegex(ValueError, r"complete TWSE\+TPEX"):
            def_build_flow_transfer_outputs(no_provenance, membership)

    def test_transfer_holds_partial_etr_without_association_edges(self) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=4)
        rows = []
        for position, date in enumerate(calendar):
            for ticker, group_number in (("1111.TW", 1), ("2222.TWO", 2), ("2330.TW", 3)):
                attention_etr = float(100 * group_number + 10 * position)
                if ticker == "2222.TWO" and date == calendar[2]:
                    attention_etr = np.nan
                rows.append(
                    {
                        "Date": date,
                        "Ticker": ticker,
                        "AttentionETR": attention_etr,
                        "LimitLockDataStatus": "PASS_LIMIT_LOCK_FLAGS",
                        "ForeignNetAmount": (-1.0 if ticker == "1111.TW" else 1.0) * (position + 1),
                        "InvestmentTrustNetAmount": 1.0,
                        "DealerNetAmount": -1.0,
                        "MarginFinancingChangeAmount": 1.0,
                        "ShortSellingChangeAmount": -1.0,
                        "ETFActiveValue": 1.0,
                    }
                )
        stock = pd.DataFrame(rows)
        stock.attrs["FullMarketGateStatus"] = REQUIRED_FULL_MARKET_GATE_STATUS
        membership = pd.DataFrame(
            [
                {"GroupId": "G1", "GroupName": "G1", "Ticker": "1111.TW", "Decision": "APPROVED"},
                {"GroupId": "G2", "GroupName": "G2", "Ticker": "2222.TWO", "Decision": "APPROVED"},
            ]
        )

        first = def_build_flow_transfer_outputs(stock, membership)
        replay = def_build_flow_transfer_outputs(stock, membership)
        invalid_date = pd.Timestamp(calendar[2])
        invalid_view = first["conserved_view"].loc[
            first["conserved_view"]["Date"].eq(invalid_date)
        ]

        self.assertTrue(invalid_view["AttentionShare"].isna().all())
        self.assertTrue(
            invalid_view["ETRCoverageStatus"]
            .eq("HOLD_PARTIAL_OR_INVALID_ETR_COVERAGE")
            .all()
        )
        self.assertFalse(
            first["rotation_associations"]["Date"].eq(invalid_date).any()
        )
        # The following valid date must not calculate an attention-share
        # difference across the invalid coverage gap.
        next_date = pd.Timestamp(calendar[3])
        attention_edges = first["rotation_associations"].loc[
            first["rotation_associations"]["Lane"].eq("ETR_ATTENTION_SHARE_CHANGE")
        ]
        self.assertFalse(attention_edges["Date"].eq(next_date).any())
        self.assertEqual(
            first["quality"]["Status"],
            "HOLD_PARTIAL_OR_INVALID_ETR_COVERAGE",
        )
        self.assertEqual(first["quality"]["PartialOrInvalidETRCoverageDates"], 1)
        self.assertGreater(first["quality"]["HeldAttentionShareRows"], 0)
        self.assertEqual(first["quality"]["AssociationRowsOnHeldETRDates"], 0)
        self.assertEqual(
            first["quality"]["HeldETRCoverageDateList"],
            [invalid_date.strftime("%Y-%m-%d")],
        )
        pd.testing.assert_frame_equal(
            first["conserved_view"], replay["conserved_view"]
        )
        pd.testing.assert_frame_equal(
            first["rotation_associations"], replay["rotation_associations"]
        )

    def test_transfer_holds_one_directional_lane_with_partial_stock_coverage(self) -> None:
        dates = pd.bdate_range("2026-01-02", periods=4)
        rows = []
        for position, date in enumerate(dates):
            for ticker in ("1111.TW", "2222.TWO", "2330.TW"):
                foreign = 5.0 if ticker == "1111.TW" else -4.0
                if ticker == "2222.TWO" and date == dates[2]:
                    foreign = np.nan
                rows.append(
                    {
                        "Date": date,
                        "Ticker": ticker,
                        "AttentionETR": 100.0 + position,
                        "LimitLockDataStatus": "PASS_LIMIT_LOCK_FLAGS",
                        "ForeignNetAmount": foreign,
                    }
                )
        stock = pd.DataFrame(rows)
        stock.attrs["FullMarketGateStatus"] = REQUIRED_FULL_MARKET_GATE_STATUS
        membership = pd.DataFrame(
            [
                {
                    "GroupId": "G1",
                    "GroupName": "G1",
                    "Ticker": "1111.TW",
                    "Decision": "APPROVED",
                },
                {
                    "GroupId": "G2",
                    "GroupName": "G2",
                    "Ticker": "2222.TWO",
                    "Decision": "APPROVED",
                },
            ]
        )
        output = def_build_flow_transfer_outputs(stock, membership)
        invalid_date = pd.Timestamp(dates[2])
        view = output["conserved_view"].loc[
            output["conserved_view"]["Date"].eq(invalid_date)
        ]
        self.assertIn(
            "HOLD_PARTIAL_OR_INVALID_DIRECTIONAL_COVERAGE",
            set(view["ForeignNetAmountCoverageStatus"]),
        )
        foreign_edges = output["rotation_associations"].loc[
            output["rotation_associations"]["Lane"].eq("ForeignNetAmount")
        ]
        self.assertFalse(foreign_edges["Date"].eq(invalid_date).any())
        self.assertEqual(
            output["quality"]["Status"],
            "HOLD_PARTIAL_OR_INVALID_DIRECTIONAL_COVERAGE",
        )
        self.assertEqual(
            output["quality"]["HeldDirectionalLaneDateList"],
            [f"{invalid_date:%Y-%m-%d}|ForeignNetAmount"],
        )
        self.assertEqual(
            output["quality"]["AssociationRowsOnHeldDirectionalLaneDates"],
            0,
        )


class CoreBoundaryAndPositioningTests(unittest.TestCase):
    def test_factor_outputs_share_one_snapshot_boundary_and_preserve_provenance(self) -> None:
        dated = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"]),
                "Value": [1, 2, 3],
            }
        )
        dated.attrs["FullMarketGateStatus"] = REQUIRED_FULL_MARKET_GATE_STATUS
        undated = pd.DataFrame({"Status": ["PASS"]})
        summary = {"Status": "PASS"}
        capped = system_orchestrator.def_cap_dated_factor_output_asof(
            {
                "validated_panel": dated,
                "another_future_dated_table": dated.copy(),
                "quality": undated,
                "summary": summary,
            },
            "2026-01-05",
        )
        for name in ("validated_panel", "another_future_dated_table"):
            self.assertEqual(capped[name]["Date"].max(), pd.Timestamp("2026-01-05"))
            self.assertEqual(len(capped[name]), 2)
        self.assertEqual(
            capped["validated_panel"].attrs["FullMarketGateStatus"],
            REQUIRED_FULL_MARKET_GATE_STATUS,
        )
        self.assertIs(capped["quality"], undated)
        self.assertIs(capped["summary"], summary)

    def test_evidence_cutoff_local_date_cannot_exceed_snapshot(self) -> None:
        market_columns = [
            "Date",
            *system_orchestrator.REQUIRED_MARKET_AVAILABILITY_COLUMNS,
            "IsLimitUpLocked",
            "IsLimitDownLocked",
        ]
        inputs = {
            "market_daily": pd.DataFrame(columns=market_columns),
            "universe_history": pd.DataFrame(),
            "trading_calendar": pd.DataFrame(
                {"Date": ["2026-01-05", "2026-01-06"]}
            ),
            "membership_events": pd.DataFrame(),
            "candidate49": pd.DataFrame(),
            "macro_vintages": pd.DataFrame(),
            "active_etf_holdings": pd.DataFrame(),
        }
        factor_output = {
            "validated_panel": pd.DataFrame(
                {
                    "Date": [pd.Timestamp("2026-01-05")],
                    **{
                        column: ["2026-01-05 18:00+08:00"]
                        for column in system_orchestrator.REQUIRED_MARKET_AVAILABILITY_COLUMNS
                    },
                }
            )
        }
        with mock.patch.object(
            system_orchestrator,
            "def_run_full_market_factor_pipeline",
            return_value=factor_output,
        ):
            with self.assertRaisesRegex(
                ValueError, "local date cannot exceed snapshot"
            ):
                system_orchestrator.def_run_pipeline_frames(
                    inputs,
                    proposed_at="2026-01-05 18:00+08:00",
                    evidence_cutoff_at="2026-01-06 00:01+08:00",
                )

    def test_default_cutoff_uses_latest_core_availability_lane(self) -> None:
        frame = pd.DataFrame(
            {
                column: ["2026-01-05 18:00+08:00"]
                for column in system_orchestrator.REQUIRED_MARKET_AVAILABILITY_COLUMNS
            }
        )
        frame.loc[0, "InvestmentTrustNetAmountAvailableAt"] = (
            "2026-01-05 19:30+08:00"
        )
        latest = system_orchestrator.def_latest_required_availability(frame)
        self.assertEqual(latest.iloc[0], pd.Timestamp("2026-01-05 11:30:00+00:00"))

    def test_monthly_revenue_is_optional_and_cannot_block_core_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            local_inputs = {}
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
            candidate_path = root / "candidate.csv"
            candidate_path.touch()
            preflight = system_orchestrator.def_input_preflight(
                root,
                {
                    "local_inputs": local_inputs,
                    "candidate_story_membership": candidate_path.name,
                },
            )
            revenue = preflight.loc[preflight["InputName"].eq("monthly_revenue")].iloc[0]
            self.assertEqual(revenue["InputRole"], "OPTIONAL_POST_SIGNAL_REFERENCE")
            self.assertEqual(revenue["PreflightStatus"], "OPTIONAL_REFERENCE_NOT_AVAILABLE")
            self.assertFalse(bool(revenue["BlocksCorePipeline"]))
            self.assertFalse(preflight["BlocksCorePipeline"].any())

        market_columns = [
            "Date",
            *system_orchestrator.REQUIRED_MARKET_AVAILABILITY_COLUMNS,
            "IsLimitUpLocked",
            "IsLimitDownLocked",
        ]
        inputs = {
            "market_daily": pd.DataFrame(columns=market_columns),
            "universe_history": pd.DataFrame(),
            "trading_calendar": pd.DataFrame({"Date": ["2026-01-02"]}),
            "membership_events": pd.DataFrame(),
            "candidate49": pd.DataFrame(),
            "macro_vintages": pd.DataFrame(),
            "active_etf_holdings": pd.DataFrame(),
        }
        with mock.patch.object(
            system_orchestrator,
            "def_run_full_market_factor_pipeline",
            side_effect=RuntimeError("CORE_ENTRY_REACHED"),
        ):
            with self.assertRaisesRegex(RuntimeError, "CORE_ENTRY_REACHED"):
                system_orchestrator.def_run_pipeline_frames(
                    inputs,
                    proposed_at="2026-01-02 18:00+08:00",
                )

    def test_invalid_optional_revenue_returns_audit_without_core_block(self) -> None:
        reference = system_orchestrator.def_build_optional_revenue_reference(
            pd.DataFrame({"MalformedField": [1]}),
            "2026-01-05 20:00+08:00",
            pd.DataFrame(),
            "2026-01-05",
            opportunity_tickers=["1111"],
        )
        self.assertTrue(reference["reference_company_revenue_latest"].empty)
        self.assertTrue(reference["reference_group_revenue_latest"].empty)
        audit = reference["reference_revenue_audit"].iloc[0]
        self.assertEqual(
            audit["RevenueReferenceStatus"],
            "OPTIONAL_REFERENCE_INVALID_CORE_UNAFFECTED",
        )
        self.assertEqual(audit["ReferenceErrorType"], "ValueError")
        self.assertFalse(bool(audit["CorePipelineBlocked"]))
        self.assertIn("PROHIBITED_FROM_CLASSIFICATION", audit["UsagePolicy"])

        waiting = system_orchestrator.def_build_optional_revenue_reference(
            pd.DataFrame({"MalformedField": [1]}),
            "2026-01-05 20:00+08:00",
            pd.DataFrame(),
            "2026-01-05",
            opportunity_tickers=[],
        )
        waiting_audit = waiting["reference_revenue_audit"].iloc[0]
        self.assertEqual(
            waiting_audit["RevenueReferenceStatus"],
            "OPTIONAL_REFERENCE_WAITING_FOR_CORE_OPPORTUNITY",
        )
        self.assertEqual(waiting_audit["OpportunityTickerCount"], 0)
        self.assertFalse(bool(waiting_audit["CorePipelineBlocked"]))

        with tempfile.TemporaryDirectory() as temporary:
            malformed_path = Path(temporary) / "monthly_revenue.unsupported"
            malformed_path.touch()
            with mock.patch.object(
                system_orchestrator,
                "def_read_table",
                side_effect=AssertionError("optional revenue was read before opportunity"),
            ) as reader:
                waiting_from_path = (
                    system_orchestrator.def_build_optional_revenue_reference(
                        malformed_path,
                        "2026-01-05 20:00+08:00",
                        pd.DataFrame(),
                        "2026-01-05",
                        opportunity_tickers=[],
                    )
                )
            reader.assert_not_called()
            self.assertEqual(
                waiting_from_path["reference_revenue_audit"].iloc[0][
                    "RevenueReferenceStatus"
                ],
                "OPTIONAL_REFERENCE_WAITING_FOR_CORE_OPPORTUNITY",
            )

            invalid_file = system_orchestrator.def_build_optional_revenue_reference(
                malformed_path,
                "2026-01-05 20:00+08:00",
                pd.DataFrame(),
                "2026-01-05",
                opportunity_tickers=["1111"],
            )
            invalid_audit = invalid_file["reference_revenue_audit"].iloc[0]
            self.assertEqual(
                invalid_audit["RevenueReferenceStatus"],
                "OPTIONAL_REFERENCE_INVALID_CORE_UNAFFECTED",
            )
            self.assertEqual(invalid_audit["ReferenceInputMode"], "DEFERRED_FILE")
            self.assertFalse(bool(invalid_audit["CorePipelineBlocked"]))

    def test_optional_revenue_filters_to_opportunities_before_validation(self) -> None:
        revenue = pd.DataFrame(
            [
                {
                    "Ticker": "1111.TW",
                    "ReportMonth": "2025-12-01",
                    "AvailableAt": "2026-01-05 18:00+08:00",
                    "Revenue": 100.0,
                },
                {
                    "Ticker": "2222.TW",
                    "ReportMonth": "invalid-unrelated-row",
                    "AvailableAt": "invalid-unrelated-row",
                    "Revenue": -1.0,
                },
            ]
        )
        membership = pd.DataFrame(
            [
                {
                    "GroupId": "AI",
                    "GroupName": "AI",
                    "Ticker": "1111",
                    "ValidFrom": "2025-01-01",
                    "ValidTo": pd.NaT,
                    "Decision": "APPROVED",
                },
                {
                    "GroupId": "UNRELATED_GROUP",
                    "GroupName": "UNRELATED_GROUP",
                    "Ticker": "3333",
                    "ValidFrom": "2025-01-01",
                    "ValidTo": pd.NaT,
                    "Decision": "APPROVED",
                },
            ]
        )
        reference = system_orchestrator.def_build_optional_revenue_reference(
            revenue,
            "2026-01-05 20:00+08:00",
            membership,
            "2026-01-05",
            opportunity_tickers=["1111"],
        )
        self.assertEqual(
            reference["reference_revenue_audit"].iloc[0][
                "RevenueReferenceStatus"
            ],
            "PASS_OPTIONAL_POST_SIGNAL_REFERENCE",
        )
        self.assertEqual(
            reference["reference_company_revenue_latest"]["Ticker"].tolist(),
            ["1111"],
        )
        self.assertEqual(
            reference["reference_group_revenue_latest"]["GroupId"].tolist(),
            ["AI"],
        )

    def test_config_runner_defers_optional_revenue_file_read(self) -> None:
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
            revenue_path = root / "monthly_revenue.unsupported"
            revenue_path.touch()
            local_inputs["monthly_revenue"] = revenue_path.name
            candidate_path = root / "candidate.csv"
            candidate_path.touch()
            config_path = config_dir / "system_config.json"
            config_path.write_text(
                json.dumps(
                    {
                        "local_inputs": local_inputs,
                        "candidate_story_membership": candidate_path.name,
                        "rolling_windows": [60, 120, 240],
                        "residual_factor_lanes": ["LaggedCap", "LaggedETR"],
                    }
                ),
                encoding="utf-8",
            )
            loaded_paths: list[Path] = []

            def fake_read(path: Path) -> pd.DataFrame:
                loaded_paths.append(path)
                return pd.DataFrame()

            with mock.patch.object(
                system_orchestrator, "def_read_table", side_effect=fake_read
            ), mock.patch.object(
                system_orchestrator,
                "def_run_pipeline_frames",
                return_value={},
            ) as pipeline:
                system_orchestrator.def_run_pipeline_from_config(
                    config_path,
                    proposed_at="2026-01-05 20:00+08:00",
                    write_output=False,
                )

            self.assertNotIn(revenue_path.resolve(), loaded_paths)
            deferred_inputs = pipeline.call_args.args[0]
            self.assertEqual(
                deferred_inputs["monthly_revenue"], revenue_path.resolve()
            )

    def test_size_bucket_backward_asof_and_exact_two_model_consensus(self) -> None:
        prepared = pd.DataFrame(
            {
                "Date": pd.to_datetime(
                    [
                        "2026-01-05",
                        "2026-01-10",
                        "2026-01-15",
                        "2026-01-25",
                        "2026-01-25",
                        "2026-01-25",
                    ]
                ),
                "Ticker": [
                    "1111.TW",
                    "1111.TW",
                    "1111.TW",
                    "1111.TW",
                    "2222.TWO",
                    "2330.TW",
                ],
            }
        )
        prepared.attrs["FullMarketGateStatus"] = REQUIRED_FULL_MARKET_GATE_STATUS
        size_history = pd.DataFrame(
            [
                {
                    "Ticker": "1111.TW",
                    "EffectiveDate": "2026-01-10",
                    "WindowDays": 60,
                    "MarketCapTier": "MID",
                    "ClassificationStatus": "PASS",
                    "SnapshotDate": "2026-01-09",
                    "ThresholdPolicy": "ROLLING_P60_P90",
                },
                {
                    "Ticker": "1111.TW",
                    "EffectiveDate": "2026-01-20",
                    "WindowDays": 60,
                    "MarketCapTier": "LARGE",
                    "ClassificationStatus": "PASS",
                    "SnapshotDate": "2026-01-19",
                    "ThresholdPolicy": "ROLLING_P60_P90",
                },
                {
                    "Ticker": "1111.TW",
                    "EffectiveDate": "2026-01-30",
                    "WindowDays": 60,
                    "MarketCapTier": "SMALL",
                    "ClassificationStatus": "PASS",
                    "SnapshotDate": "2026-01-29",
                    "ThresholdPolicy": "ROLLING_P60_P90",
                },
            ]
        )
        sized = system_orchestrator.def_attach_pit_size_bucket(
            prepared, size_history, window_days=60
        )
        early = sized.loc[
            sized["Ticker"].eq("1111.TW")
            & sized["Date"].eq(pd.Timestamp("2026-01-05"))
        ].iloc[0]
        exact = sized.loc[
            sized["Ticker"].eq("1111.TW")
            & sized["Date"].eq(pd.Timestamp("2026-01-10"))
        ].iloc[0]
        between = sized.loc[
            sized["Ticker"].eq("1111.TW")
            & sized["Date"].eq(pd.Timestamp("2026-01-15"))
        ].iloc[0]
        latest = sized.loc[
            sized["Ticker"].eq("1111.TW")
            & sized["Date"].eq(pd.Timestamp("2026-01-25"))
        ].iloc[0]
        self.assertTrue(pd.isna(early["SizeBucket"]))
        self.assertEqual(early["SizeBucketLookupStatus"], "HOLD_NO_EFFECTIVE_SIZE_BUCKET")
        self.assertEqual(exact["SizeBucket"], "MID")
        self.assertEqual(between["SizeBucket"], "MID")
        self.assertEqual(latest["SizeBucket"], "LARGE")
        self.assertEqual(
            sized.loc[sized["Ticker"].eq("2222.TWO"), "SizeBucketLookupStatus"].iloc[0],
            "HOLD_NO_EFFECTIVE_SIZE_BUCKET",
        )
        self.assertEqual(
            sized.loc[sized["Ticker"].eq("2330.TW"), "SizeBucketLookupStatus"].iloc[0],
            "ANCHOR_EXCLUDED",
        )
        self.assertEqual(
            sized.attrs["FullMarketGateStatus"], REQUIRED_FULL_MARKET_GATE_STATUS
        )

        common = {
            "Date": pd.Timestamp("2026-01-25"),
            "Ticker": "1111",
            "EvidenceWindowDays": 60,
            "DirectionalLane": "FOREIGN",
            "ResidualBetaWindow": 60,
            "WindowDays": 60,
            "EvidenceCategory": "EARLY_POSITIONING_STABLE_BEFORE_PRICE",
            "PositioningSequencePhase": (
                "STABLE_POSITIONING_DURING_PRICE_PULLBACK_OR_SIDEWAYS_OBSERVED"
            ),
            "PriceEvidenceBasis": "EX_TSMC_RESIDUAL_RETURN",
            "SignalTimingStatus": "PASS_NEXT_SESSION_AFTER_LATEST_REQUIRED_EVIDENCE",
            "SignalAvailableAt": pd.Timestamp("2026-01-25 12:00:00+00:00"),
            "EffectiveDate": pd.Timestamp("2026-01-26"),
            "AttentionETR": 100.0,
            "DirectionalAmount": 5.0,
            "TSMCExcluded": True,
            "FullMarketGateStatus": "PASS_FULL_TWSE_TPEX_ORDINARY_STOCKS",
        }
        models = pd.DataFrame(
            [
                {
                    **common,
                    "ResidualFactorLane": lane,
                    "FactorLane": lane,
                    "ResidualSourceColumn": f"Residual_{lane}_60D",
                }
                for lane in ("LaggedCap", "LaggedETR")
            ]
        )
        consensus = system_orchestrator.def_reconcile_stock_positioning_models(models)
        row = consensus.iloc[0]
        self.assertEqual(row["FactorModelCount"], 2)
        self.assertEqual(row["ConsensusStatus"], "PASS_EXACT_FACTOR_MODEL_AGREEMENT")
        self.assertEqual(row["ConsensusEvidenceCategory"], common["EvidenceCategory"])
        self.assertTrue(bool(row["ConsensusActionable"]))
        self.assertFalse(any("score" in column.lower() for column in consensus.columns))

        wrong_window = models.copy()
        wrong_lane = wrong_window["ResidualFactorLane"].eq("LaggedETR")
        wrong_window.loc[wrong_lane, ["ResidualBetaWindow", "WindowDays"]] = 120
        wrong_window.loc[wrong_lane, "ResidualSourceColumn"] = "Residual_LaggedETR_120D"
        held_window = system_orchestrator.def_reconcile_stock_positioning_models(
            wrong_window
        )
        self.assertEqual(
            held_window.iloc[0]["ConsensusStatus"],
            "HOLD_RESIDUAL_AND_EVIDENCE_WINDOW_MISMATCH",
        )

        raw_price = models.copy()
        raw_price.loc[
            raw_price["ResidualFactorLane"].eq("LaggedETR"), "PriceEvidenceBasis"
        ] = "RAW_STOCK_RETURN_FALLBACK"
        held_basis = system_orchestrator.def_reconcile_stock_positioning_models(raw_price)
        self.assertEqual(
            held_basis.iloc[0]["ConsensusStatus"], "HOLD_EX_TSMC_RESIDUAL_NOT_READY"
        )

        missing_model = system_orchestrator.def_reconcile_stock_positioning_models(
            models.iloc[[0]]
        )
        self.assertEqual(
            missing_model.iloc[0]["ConsensusStatus"], "HOLD_MISSING_FACTOR_MODEL"
        )

        null_category = models.copy()
        null_category["EvidenceCategory"] = pd.NA
        held_null = system_orchestrator.def_reconcile_stock_positioning_models(
            null_category
        )
        self.assertEqual(
            held_null.iloc[0]["ConsensusStatus"],
            "HOLD_FACTOR_MODEL_DISAGREEMENT",
        )
        self.assertFalse(bool(held_null.iloc[0]["ConsensusActionable"]))

        missing_invariant = models.copy()
        missing_invariant.loc[
            missing_invariant["ResidualFactorLane"].eq("LaggedETR"),
            "AttentionETR",
        ] = np.nan
        held_invariant = system_orchestrator.def_reconcile_stock_positioning_models(
            missing_invariant
        )
        self.assertEqual(
            held_invariant.iloc[0]["ConsensusStatus"],
            "HOLD_FACTOR_MODEL_INVARIANT_MISSING_OR_DISAGREEMENT",
        )

        tsmc_models = models.copy()
        tsmc_models["Ticker"] = "2330.TW"
        held_tsmc = system_orchestrator.def_reconcile_stock_positioning_models(
            tsmc_models
        )
        self.assertEqual(
            held_tsmc.iloc[0]["ConsensusStatus"],
            "HOLD_EX_TSMC_PROVENANCE_NOT_READY",
        )

        with self.assertRaisesRegex(ValueError, "exactly LaggedCap and LaggedETR"):
            system_orchestrator.def_reconcile_stock_positioning_models(
                models,
                factor_lanes=("LaggedCap", "LaggedETR", "UnexpectedLane"),
            )
        with self.assertRaisesRegex(ValueError, "60/120/240"):
            system_orchestrator.def_validate_formal_pipeline_grid(
                system_orchestrator.PipelineConfig(windows=(60, 120))
            )

    def test_tsmc_membership_is_partitioned_from_four_role_validation(self) -> None:
        membership = pd.DataFrame(
            [
                {
                    "GroupId": "FOUNDRY",
                    "GroupName": "晶圓代工",
                    "Ticker": "2330.TW",
                },
                {
                    "GroupId": "FOUNDRY",
                    "GroupName": "晶圓代工",
                    "Ticker": "1111.TW",
                },
            ]
        )
        validation_result = SimpleNamespace(
            group_validation=pd.DataFrame(
                [
                    {
                        "SnapshotDate": pd.Timestamp("2026-01-05"),
                        "Window": 60,
                        "GroupId": "FOUNDRY",
                        "GroupName": "晶圓代工",
                        "GroupDecision": "PASS",
                        "EvidenceStatus": "READY",
                    }
                ]
            ),
            member_roles=pd.DataFrame(
                [
                    {
                        "SnapshotDate": pd.Timestamp("2026-01-05"),
                        "Window": 60,
                        "GroupId": "FOUNDRY",
                        "Ticker": "1111",
                        "Role": "PEER",
                        "EvidenceStatus": "READY",
                    }
                ]
            ),
            null_ledger=pd.DataFrame({"GroupId": ["FOUNDRY"]}),
            metadata={"Status": "PASS"},
        )
        size_feature = pd.DataFrame(
            {
                "Ticker": ["1111"],
                "Market": ["TWSE"],
                "SizeTier": ["MID"],
                "LiquidityTier": ["MID"],
                "TierEffectiveDate": [pd.Timestamp("2026-01-02")],
                "WindowDays": [60],
            }
        )
        size_feature.attrs.update({"PointInTime": True, "TSMCExcluded": True})
        size_bridge = mock.Mock(return_value=size_feature)
        validator = mock.Mock(return_value=validation_result)
        with mock.patch.object(
            system_orchestrator, "def_bridge_size_tiers_asof", size_bridge
        ), mock.patch.object(
            system_orchestrator,
            "def_bridge_residual_lane",
            return_value=pd.DataFrame(),
        ), mock.patch.object(
            system_orchestrator, "def_run_group_validation", validator
        ), mock.patch.object(
            system_orchestrator,
            "def_reconcile_group_decisions",
            return_value=pd.DataFrame(),
        ), mock.patch.object(
            system_orchestrator,
            "def_reconcile_member_roles",
            return_value=pd.DataFrame(),
        ):
            output = system_orchestrator.def_run_validation_grid(
                pd.DataFrame(),
                membership,
                pd.DataFrame(),
                "2026-01-05",
                "2026-01-05 18:00+08:00",
                pd.bdate_range("2026-01-02", periods=3),
                system_orchestrator.PipelineConfig(
                    windows=(60,),
                    factor_lanes=("LaggedCap",),
                    validation_null_repeats_override=2,
                ),
            )

        model_members = validator.call_args.args[1]
        self.assertEqual(model_members["Ticker"].tolist(), ["1111.TW"])
        self.assertNotIn("2330.TW", size_bridge.call_args.kwargs["required_tickers"])
        anchor = output["tsmc_anchor_membership"].iloc[0]
        self.assertEqual(anchor["Ticker"], "2330.TW")
        self.assertTrue(pd.isna(anchor["RoleConsensus"]))
        self.assertFalse(bool(anchor["IndexComparisonEligible"]))
        self.assertIn("NOT_A_FIFTH_ROLE", anchor["AnchorValidationStatus"])

    def test_validation_size_descriptors_align_to_each_residual_window(self) -> None:
        membership = pd.DataFrame(
            [
                {
                    "GroupId": "AI",
                    "GroupName": "AI",
                    "Ticker": ticker,
                }
                for ticker in ("1111.TW", "2222.TW", "3333.TWO")
            ]
        )
        size_windows_seen: list[int] = []
        validation_pairs_seen: list[tuple[str, int]] = []

        def size_bridge_side_effect(
            _history: pd.DataFrame,
            _as_of: object,
            *,
            window_days: int,
            required_tickers: object,
        ) -> pd.DataFrame:
            self.assertNotIn("2330.TW", set(required_tickers))
            size_windows_seen.append(int(window_days))
            features = pd.DataFrame(
                {
                    "Ticker": ["1111", "2222", "3333"],
                    "Market": ["TWSE", "TWSE", "TPEX"],
                    "SizeTier": ["LARGE", "MID", "SMALL"],
                    "LiquidityTier": ["MID", "SMALL", "LARGE"],
                    "TierEffectiveDate": [pd.Timestamp("2026-01-02")] * 3,
                    "WindowDays": [int(window_days)] * 3,
                }
            )
            features.attrs.update({"PointInTime": True, "TSMCExcluded": True})
            return features

        def residual_bridge_side_effect(
            _residuals: pd.DataFrame,
            *,
            factor_lane: str,
            window_days: int,
            as_of_date: object,
        ) -> pd.DataFrame:
            residual = pd.DataFrame(
                {
                    "Date": [pd.Timestamp(as_of_date)],
                    "Ticker": ["1111.TW"],
                    "ResidualReturn": [0.0],
                }
            )
            residual.attrs.update(
                {
                    "MarketUniverse": "TWSE_TPEX_COMMON_EQUITY_EX_2330",
                    "ResidualizationUniverse": "TWSE_TPEX_COMMON_EQUITY_EX_2330",
                    "TSMCExcluded": True,
                    "TSMCExcludedFromMarketFactor": True,
                    "PointInTime": True,
                    "FactorLane": factor_lane,
                    "WindowDays": int(window_days),
                }
            )
            return residual

        def validator_side_effect(
            residual: pd.DataFrame,
            _membership: pd.DataFrame,
            **kwargs: object,
        ) -> SimpleNamespace:
            config = kwargs["config"]
            window = int(config.windows[0])
            factor_lane = str(residual.attrs["FactorLane"])
            match_features = kwargs["match_features"]
            self.assertEqual(
                set(pd.to_numeric(match_features["WindowDays"]).astype(int)),
                {window},
            )
            self.assertTrue(bool(match_features.attrs["PointInTime"]))
            self.assertTrue(bool(match_features.attrs["TSMCExcluded"]))
            self.assertNotIn("2330", set(match_features["Ticker"]))
            self.assertEqual(
                residual.attrs["MarketUniverse"],
                "TWSE_TPEX_COMMON_EQUITY_EX_2330",
            )
            self.assertTrue(bool(residual.attrs["TSMCExcludedFromMarketFactor"]))
            self.assertEqual(int(residual.attrs["WindowDays"]), window)
            validation_pairs_seen.append((factor_lane, window))
            return SimpleNamespace(
                group_validation=pd.DataFrame(),
                member_roles=pd.DataFrame(),
                null_ledger=pd.DataFrame(),
                metadata={"Status": "PASS"},
            )

        with mock.patch.object(
            system_orchestrator,
            "def_bridge_size_tiers_asof",
            side_effect=size_bridge_side_effect,
        ), mock.patch.object(
            system_orchestrator,
            "def_bridge_residual_lane",
            side_effect=residual_bridge_side_effect,
        ), mock.patch.object(
            system_orchestrator,
            "def_run_group_validation",
            side_effect=validator_side_effect,
        ), mock.patch.object(
            system_orchestrator,
            "def_reconcile_group_decisions",
            return_value=pd.DataFrame(),
        ), mock.patch.object(
            system_orchestrator,
            "def_reconcile_member_roles",
            return_value=pd.DataFrame(),
        ):
            output = system_orchestrator.def_run_validation_grid(
                pd.DataFrame(),
                membership,
                pd.DataFrame(),
                "2026-01-05",
                "2026-01-05 18:00+08:00",
                pd.bdate_range("2026-01-02", periods=3),
            )

        self.assertEqual(size_windows_seen, [60, 120, 240])
        self.assertEqual(
            set(validation_pairs_seen),
            {
                (factor_lane, window)
                for factor_lane in ("LaggedCap", "LaggedETR")
                for window in (60, 120, 240)
            },
        )
        self.assertEqual(len(validation_pairs_seen), 6)
        size_output = output["validation_size_features"]
        self.assertEqual(set(size_output["WindowDays"]), {60, 120, 240})
        self.assertNotIn("2330", set(size_output["Ticker"]))
        self.assertEqual(
            size_output.attrs["ComparisonUniverse"],
            "TWSE_TPEX_COMMON_EQUITY_EX_2330",
        )
        self.assertEqual(
            size_output.attrs["WindowAlignmentPolicy"],
            "MATCH_VALIDATION_WINDOW_EXACTLY",
        )

    @staticmethod
    def _positioning_fixture() -> tuple[pd.DataFrame, pd.DataFrame, pd.DatetimeIndex]:
        dates = pd.bdate_range("2026-01-02", periods=12)
        stock_rows: list[dict[str, object]] = []
        residual_rows: list[dict[str, object]] = []
        tickers = (
            ("2330.TW", "TWSE"),
            ("1111.TW", "TWSE"),
            ("2222.TW", "TWSE"),
            ("3333.TWO", "TPEX"),
        )
        for date_number, date in enumerate(dates):
            for ticker_number, (ticker, exchange) in enumerate(tickers):
                latest = date_number == len(dates) - 1
                turnover = 2_000.0 if ticker_number == 0 else 1_000.0 + 100 * ticker_number
                foreign = (3.0, 2.0, 1.0, 0.5)[ticker_number]
                if latest and ticker == "1111.TW":
                    turnover = 2_200.0
                    foreign = 12.0
                stock_rows.append(
                    {
                        "Date": date,
                        "Ticker": ticker,
                        "Exchange": exchange,
                        "AssetType": "EQUITY",
                        "Adj_Close": 50.0 + date_number,
                        "TurnoverValue": turnover,
                        "DayTradeTurnoverValue": 0.2 * turnover,
                        "MarketDataAvailableAt": f"{date:%Y-%m-%d} 13:40+08:00",
                        "ForeignNetAmount": foreign,
                        "ForeignNetAmountAvailableAt": f"{date:%Y-%m-%d} 18:00+08:00",
                        "InvestmentTrustNetAmount": 0.5 * foreign,
                        "InvestmentTrustNetAmountAvailableAt": f"{date:%Y-%m-%d} 18:01+08:00",
                        "DealerNetAmount": 0.25 * foreign,
                        "DealerNetAmountAvailableAt": f"{date:%Y-%m-%d} 18:02+08:00",
                        "MarginBalanceValue": 100.0 + date_number,
                        "MarginBalanceValueAvailableAt": f"{date:%Y-%m-%d} 19:00+08:00",
                        "ShortBalanceValue": 20.0,
                        "ShortBalanceValueAvailableAt": f"{date:%Y-%m-%d} 19:00+08:00",
                        "ETFActiveValue": 0.2 * foreign,
                        "ETFActiveValueAvailableAt": f"{date:%Y-%m-%d} 20:00+08:00",
                        "IsLimitUpLocked": False,
                        "IsLimitDownLocked": False,
                        "SizeBucket": "SMALL",
                    }
                )
                if ticker_number:
                    residual = (-0.001, 0.0, 0.001)[ticker_number - 1]
                    if latest and ticker == "1111.TW":
                        residual = -0.004
                    beta_observations = min(date_number, 5)
                    beta_ready = beta_observations >= 4
                    residual_rows.append(
                        {
                            "Date": date,
                            "Ticker": ticker,
                            "Market": exchange,
                            "ResidualReturn": residual if beta_ready else np.nan,
                            "ResidualReturnAvailableAt": f"{date:%Y-%m-%d} 18:10+08:00",
                            "FactorLane": "LaggedETR",
                            "WindowDays": 5,
                            "ResidualSourceColumn": "Residual_LaggedETR_5D",
                            "ResidualModelStatus": (
                                "PASS"
                                if beta_ready
                                else "BLOCKED_INSUFFICIENT_T1_HISTORY"
                            ),
                            "ResidualWindowPolicy": "T_MINUS_1_ONLY;window=5;minimum=4",
                            "ResidualBetaObservations": beta_observations,
                            "ResidualUniverseExpectedTickerCount": 3,
                            "ResidualUniverseExpectedTWSECount": 2,
                            "ResidualUniverseExpectedTPEXCount": 1,
                            "ResidualUniverseRosterHash": hashlib.sha256(
                                (
                                    "TPEX|3333.TWO\nTWSE|1111.TW\n"
                                    "TWSE|2222.TW"
                                ).encode("utf-8")
                            )
                            .hexdigest()
                            .upper(),
                        }
                    )
        prepared = def_prepare_stock_flow_panel(pd.DataFrame(stock_rows))
        prepared.attrs.update(
            {
                "FullMarketGateStatus": REQUIRED_FULL_MARKET_GATE_STATUS,
                "FullMarketUniverse": "TWSE_TPEX_COMMON_EQUITY_WITH_2330_ANCHOR",
                "PointInTime": True,
            }
        )
        residuals = pd.DataFrame(residual_rows)
        residual_row_provenance = {
            **def_residual_lineage_values((5,)),
            "MarketUniverse": REQUIRED_RESIDUAL_UNIVERSE,
            "ResidualizationUniverse": REQUIRED_RESIDUAL_UNIVERSE,
            "TSMCExcluded": True,
            "TSMCExcludedFromMarketFactor": True,
            "PointInTime": True,
        }
        for column, value in residual_row_provenance.items():
            residuals[column] = value
        residuals.attrs.update(
            {
                **residual_row_provenance,
                "FactorLane": "LaggedETR",
                "WindowDays": 5,
                "ResidualSourceColumn": "Residual_LaggedETR_5D",
            }
        )
        attrless_residuals = residuals.copy()
        attrless_residuals.attrs.clear()
        prepared_attrless = def_prepare_residual_evidence(attrless_residuals)
        if len(prepared_attrless) != len(attrless_residuals):
            raise AssertionError("row-level residual lineage failed an attrs-free round trip")
        incomplete_attrless = attrless_residuals.drop(attrless_residuals.index[-1])
        try:
            def_prepare_residual_evidence(incomplete_attrless)
        except ValueError as error:
            if not any(
                text in str(error)
                for text in (
                    "complete ex-2330 daily universe",
                    "daily roster hash mismatch",
                )
            ):
                raise
        else:
            raise AssertionError("incomplete residual universe passed stock preparation")
        calendar = dates.append(pd.DatetimeIndex([dates[-1] + pd.offsets.BDay(1)]))
        return prepared, residuals, calendar

    def test_stock_positioning_sequence_is_price_volume_only_without_score_or_revenue(self) -> None:
        prepared, residuals, calendar = self._positioning_fixture()
        output = def_build_stock_positioning_outputs(
            prepared,
            calendar,
            residual_returns=residuals,
            as_of_date=calendar[-2],
            config=StockPositioningConfig(windows=(5,)),
        )
        missing_market_member = prepared.drop(
            prepared.index[
                prepared["Date"].eq(calendar[-2])
                & prepared["Ticker"].astype(str).str.startswith("2222")
            ][0]
        )
        missing_market_member.attrs.update(prepared.attrs)
        with self.assertRaisesRegex(ValueError, "daily rosters disagree"):
            def_build_stock_positioning_outputs(
                missing_market_member,
                calendar,
                residual_returns=residuals,
                as_of_date=calendar[-2],
                config=StockPositioningConfig(windows=(5,)),
            )
        evidence = output["stock_lane_evidence"]
        latest = evidence.loc[
            evidence["Date"].eq(calendar[-2])
            & evidence["Ticker"].eq("1111")
            & evidence["DirectionalLane"].eq("FOREIGN")
        ].iloc[0]

        self.assertEqual(latest["EvidenceCategory"], "EARLY_POSITIONING_STABLE_BEFORE_PRICE")
        self.assertEqual(
            latest["PositioningSequencePhase"],
            "STABLE_POSITIONING_DURING_PRICE_PULLBACK_OR_SIDEWAYS_OBSERVED",
        )
        self.assertEqual(latest["EffectiveDate"], calendar[-1])
        self.assertEqual(latest["AttentionInterpretation"], "NON_DIRECTIONAL_MARKET_ATTENTION")
        self.assertEqual(latest["PriceEvidenceBasis"], "EX_TSMC_RESIDUAL_RETURN")
        self.assertNotIn("2330", set(evidence["Ticker"]))

        # Every timestamp lane is required.  A missing peer-price timestamp
        # must fail closed instead of taking the maximum of the remaining
        # timestamps and making a partially timed observation actionable.
        missing_required_time = output["stock_window_features"].copy()
        target = (
            missing_required_time["Date"].eq(calendar[-2])
            & missing_required_time["Ticker"].eq("1111")
        )
        missing_required_time.loc[target, "PricePeerAvailableAt"] = pd.NaT
        retimed = def_build_stock_lane_evidence(missing_required_time, calendar)
        retimed_target = retimed.loc[
            retimed["Date"].eq(calendar[-2])
            & retimed["Ticker"].eq("1111")
            & retimed["DirectionalLane"].eq("FOREIGN")
        ].iloc[0]
        self.assertTrue(pd.isna(retimed_target["SignalAvailableAt"]))
        self.assertTrue(pd.isna(retimed_target["EffectiveDate"]))
        self.assertEqual(
            retimed_target["SignalTimingStatus"],
            "HOLD_MISSING_TIME_OR_NEXT_SESSION",
        )

        forbidden = [
            column
            for table in output.values()
            for column in table.columns
            if "score" in column.lower() or "revenue" in column.lower()
        ]
        self.assertEqual(forbidden, [])

    def test_transition_ledger_requires_order_resets_and_rejects_forbidden_inputs(self) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=12)

        def row(
            ticker: str,
            evidence_index: int,
            phase: str,
            category: str = "NO_CONVERGENT_EVIDENCE",
        ) -> dict[str, object]:
            evidence_date = calendar[evidence_index]
            return {
                "Date": evidence_date,
                "Ticker": ticker,
                "EvidenceWindowDays": 6,
                "DirectionalLane": "FOREIGN",
                "ConsensusStatus": EXACT_CONSENSUS_STATUS,
                "ConsensusEvidenceCategory": category,
                "ConsensusPositioningSequencePhase": phase,
                "SignalAvailableAt": pd.Timestamp(
                    f"{evidence_date:%Y-%m-%d} 14:30:00", tz="Asia/Taipei"
                ),
                "EffectiveDate": calendar[evidence_index + 1],
                "MarketUniverse": EX_TSMC_UNIVERSE,
                "TSMCExcluded": True,
            }

        source = pd.DataFrame(
            [
                row("1111", 0, ORDERED_PHASES[0]),
                row("1111", 1, ORDERED_PHASES[2]),  # stage 3 cannot skip stage 2
                row("1111", 2, ORDERED_PHASES[1]),
                row("1111", 3, ORDERED_PHASES[2]),
                row("1111", 4, ORDERED_PHASES[3]),
                row("2222", 0, ORDERED_PHASES[0]),
                row("2222", 1, ORDERED_PHASES[1]),
                row(
                    "2222",
                    2,
                    "EARLY_DISTRIBUTION_WHILE_PRICE_HOLDS_OBSERVED",
                    "EARLY_EXIT_BEFORE_PRICE_WEAKNESS",
                ),
            ]
        )
        ledger = def_build_positioning_transition_ledger(source, calendar)

        completed = ledger.loc[ledger["Ticker"].eq("1111")]
        self.assertEqual(completed.iloc[-1]["VerifiedPhase"], ORDERED_PHASES[3])
        self.assertTrue(bool(completed.iloc[-1]["SequenceComplete"]))
        jump = completed.loc[
            completed["ObservedConsensusPhase"].eq(ORDERED_PHASES[2])
        ].iloc[0]
        self.assertEqual(jump["TransitionStatus"], "HOLD_OUT_OF_ORDER_PHASE")
        self.assertEqual(jump["VerifiedPhase"], ORDERED_PHASES[0])
        self.assertFalse(bool(jump["ObservedPhaseAccepted"]))

        reset = ledger.loc[ledger["Ticker"].eq("2222")].iloc[-1]
        self.assertEqual(reset["VerifiedPhase"], "NO_ACTIVE_SEQUENCE")
        self.assertIn("DISTRIBUTION_OBSERVED", reset["ResetReason"])
        self.assertEqual(reset["TransitionStatus"], "PASS_OBSERVED_RESET")
        self.assertFalse(bool(reset["SequenceComplete"]))
        self.assertFalse(
            any(
                "score" in column.lower()
                or "revenue" in column.lower()
                or "營收" in column
                for column in ledger.columns
            )
        )

        for forbidden_column in ("CompositeScore", "RevenueYoY"):
            forbidden = source.iloc[[0]].copy()
            forbidden[forbidden_column] = 1.0
            with self.assertRaisesRegex(ValueError, "score or revenue"):
                def_build_positioning_transition_ledger(forbidden, calendar)

        tsmc = source.iloc[[0]].copy()
        tsmc["Ticker"] = "2330.TW"
        with self.assertRaisesRegex(ValueError, "ex-2330 provenance"):
            def_build_positioning_transition_ledger(tsmc, calendar)

        not_yet_effective = def_build_positioning_transition_ledger(
            source.iloc[[0]],
            calendar,
            as_of=source.iloc[0]["SignalAvailableAt"],
        )
        self.assertTrue(not_yet_effective.empty)

        stale_ledger = def_build_positioning_transition_ledger(
            source.iloc[[0]],
            calendar,
            as_of=pd.Timestamp(f"{calendar[-1]:%Y-%m-%d} 20:00", tz="Asia/Taipei"),
        )
        stale_latest = def_latest_positioning_transition_state(
            stale_ledger,
            calendar,
            as_of=pd.Timestamp(f"{calendar[-1]:%Y-%m-%d} 20:00", tz="Asia/Taipei"),
        ).iloc[0]
        self.assertEqual(stale_latest["VerifiedPhase"], "NO_ACTIVE_SEQUENCE")
        self.assertEqual(
            stale_latest["StateMaterializationStatus"],
            "RESET_EXPIRED_WITHOUT_NEW_EXACT_OBSERVATION",
        )
        self.assertEqual(stale_latest["ResetReason"], "EVIDENCE_WINDOW_EXPIRED")

    def test_story_mapping_does_not_multiply_same_effective_date(self) -> None:
        evidence = pd.DataFrame(
            [
                {
                    "Date": "2026-01-02",
                    "EffectiveDate": "2026-01-06",
                    "Ticker": "1111.TW",
                    "EvidenceWindowDays": 60,
                    "DirectionalLane": "FOREIGN",
                    "DirectionalAmount": 10.0,
                    "AttentionETR": 100.0,
                },
                {
                    "Date": "2026-01-05",
                    "EffectiveDate": "2026-01-06",
                    "Ticker": "1111.TW",
                    "EvidenceWindowDays": 60,
                    "DirectionalLane": "FOREIGN",
                    "DirectionalAmount": 20.0,
                    "AttentionETR": 200.0,
                },
            ]
        )
        membership = pd.DataFrame(
            [
                {
                    "GroupId": "AI",
                    "GroupName": "AI",
                    "Ticker": "1111.TW",
                    "ValidFrom": "2025-01-01",
                    "ValidTo": pd.NaT,
                    "Decision": "APPROVED",
                    "ExposureShare": 1.0,
                }
            ]
        )
        mapped = def_map_evidence_to_story_groups(evidence, membership)
        raw = mapped["raw_story_evidence"]
        conserved = mapped["conserved_story_evidence"]
        self.assertEqual(len(raw), 2)
        self.assertEqual(len(conserved), 2)
        self.assertEqual(raw["Date"].nunique(), 2)
        self.assertAlmostEqual(conserved["AllocatedDirectionalAmount"].sum(), 30.0)


class MacroRevenueAndBacktestTests(unittest.TestCase):
    def test_macro_vintage_risk_free_provenance_and_timezone(self) -> None:
        raw = pd.DataFrame(
            [
                {
                    "ObservationDate": "2026-01-01",
                    "AvailableAt": "2026-01-02 09:00",
                    "USDTWD": 31.0,
                    "DXY": 100.0,
                    "Taiwan10YYield": 1.4,
                    "Source": "TPEx Government Bond Yield Curve",
                    "SourceAuthority": "TAIPEI_EXCHANGE_TPEX",
                    "SourceURL": "https://www.tpex.org.tw/zh-tw/bond/",
                    "SourcePayloadHash": "a" * 64,
                    "YieldUnit": "PERCENT",
                    "InstrumentId": "TAIWAN_10Y_GOVERNMENT_BOND_YIELD",
                    "OfficialSourceVerified": True,
                },
                {
                    "ObservationDate": "2026-01-02",
                    "AvailableAt": "2026-01-02 10:00+08:00",
                    "USDTWD": 32.0,
                    "DXY": 101.0,
                    "Taiwan10YYield": 1.5,
                    "Source": "TPEx Government Bond Yield Curve",
                    "SourceAuthority": "TAIPEI_EXCHANGE_TPEX",
                    "SourceURL": "https://www.tpex.org.tw/zh-tw/bond/",
                    "SourcePayloadHash": "b" * 64,
                    "YieldUnit": "PERCENT",
                    "InstrumentId": "TAIWAN_10Y_GOVERNMENT_BOND_YIELD",
                    "OfficialSourceVerified": True,
                },
                {
                    "ObservationDate": "2026-01-01",
                    "AvailableAt": "2026-01-03 12:00+08:00",
                    "USDTWD": 30.0,
                    "DXY": 99.0,
                    "Taiwan10YYield": 1.3,
                    "Source": "TPEx Government Bond Yield Curve",
                    "SourceAuthority": "TAIPEI_EXCHANGE_TPEX",
                    "SourceURL": "https://www.tpex.org.tw/zh-tw/bond/",
                    "SourcePayloadHash": "c" * 64,
                    "YieldUnit": "PERCENT",
                    "InstrumentId": "TAIWAN_10Y_GOVERNMENT_BOND_YIELD",
                    "OfficialSourceVerified": True,
                },
            ]
        )
        prepared = def_prepare_macro_factors(raw)
        self.assertEqual(
            prepared.loc[prepared["USDTWD"].eq(31.0), "AvailableAt"].iloc[0],
            pd.Timestamp("2026-01-02 01:00:00+00:00"),
        )
        decisions = pd.DataFrame(
            [
                {"Date": "2026-01-02", "DecisionAt": "2026-01-02 18:00+08:00"},
                {"Date": "2026-01-03", "DecisionAt": "2026-01-03 20:00+08:00"},
            ]
        )
        pit = def_materialize_macro_asof(prepared, decisions)
        self.assertEqual(pit["USDTWD"].tolist(), [32.0, 32.0])
        with_context = def_add_macro_context(pit)
        self.assertTrue(with_context["Taiwan10YDailyRiskFree"].notna().all())

        unverified = raw.iloc[[0]].copy()
        unverified["OfficialSourceVerified"] = False
        unverified_context = def_add_macro_context(
            def_materialize_macro_asof(
                def_prepare_macro_factors(unverified),
                decisions.iloc[[0]],
            )
        )
        self.assertTrue(unverified_context["Taiwan10YDailyRiskFree"].isna().all())

    def test_monthly_revenue_is_point_in_time_and_multimonth_is_held(self) -> None:
        raw = pd.DataFrame(
            [
                {"Ticker": "1111.TW", "ReportMonth": "2025-01-01", "AvailableAt": "2025-02-10 18:00+08:00", "Revenue": 100.0, "ReportingPeriodMonths": 1},
                {"Ticker": "1111.TW", "ReportMonth": "2026-01-01", "AvailableAt": "2026-02-10 18:00+08:00", "Revenue": 120.0, "ReportingPeriodMonths": 1},
                {"Ticker": "1111.TW", "ReportMonth": "2026-01-01", "AvailableAt": "2026-02-12 18:00+08:00", "Revenue": 125.0, "ReportingPeriodMonths": 1},
                {"Ticker": "2222.TWO", "ReportMonth": "2026-01-01", "AvailableAt": "2026-02-10 18:00", "Revenue": 300.0, "ReportingPeriodMonths": 2},
            ]
        )
        prepared = def_prepare_monthly_revenue(raw)
        before = def_materialize_revenue_asof(prepared, "2026-02-11 00:00+08:00")
        first = before.loc[
            before["Ticker"].eq("1111")
            & before["ReportMonth"].eq(pd.Timestamp("2026-01-01"))
        ]
        self.assertEqual(float(first.iloc[0]["Revenue"]), 120.0)
        after = def_materialize_revenue_asof(prepared, "2026-02-13 00:00+08:00")
        revised = after.loc[
            after["Ticker"].eq("1111")
            & after["ReportMonth"].eq(pd.Timestamp("2026-01-01"))
        ]
        self.assertEqual(float(revised.iloc[0]["Revenue"]), 125.0)
        evidence = def_company_revenue_evidence(prepared, "2026-02-11 00:00+08:00")
        self.assertAlmostEqual(float(evidence.loc[evidence["Ticker"].eq("1111"), "RevenueYoY"].iloc[0]), 0.2)
        self.assertEqual(
            evidence.loc[evidence["Ticker"].eq("2222"), "ComparabilityStatus"].iloc[0],
            "HOLD_MULTI_MONTH_REPORTING_PERIOD",
        )

    def test_formal_index_requires_pit_size_and_backtest_blocks_held_level(self) -> None:
        stock, membership = def_build_index_fixture()
        formal = HierarchicalIndexConfig(require_pit_size_history=True)
        with self.assertRaisesRegex(ValueError, "requires quarterly point-in-time size history"):
            def_build_parallel_group_indices(stock, membership, formal)

        size_rows = []
        for ticker in stock["Ticker"].drop_duplicates():
            size_rows.append(
                {
                    "Ticker": ticker,
                    "EffectiveDate": stock["Date"].min(),
                    "WindowDays": 240,
                    "MarketCapTier": "LARGE" if ticker.startswith(("2", "3")) else "SMALL",
                }
            )
        built = def_build_parallel_group_indices(
            stock,
            membership,
            formal,
            size_history=pd.DataFrame(size_rows),
        )
        self.assertEqual(built["quality"]["Status"], "PASS")
        self.assertTrue((built["weights"]["WeightDate"] < built["weights"]["AppliedDate"]).all())

        dates = pd.bdate_range("2026-01-02", periods=5)
        index_daily = pd.DataFrame(
            {
                "Date": dates,
                "GroupId": "G",
                "IndexMethod": "GI_HIER",
                "IndexLevel": [100, 101, 102, 102, 104],
                "IndexStatus": ["PASS", "PASS", "HOLD_MISSING_MEMBER_RETURN", "PASS", "PASS"],
            }
        )
        signals = pd.DataFrame(
            [
                {
                    "Date": dates[0],
                    "GroupId": "G",
                    "DirectionalLane": "FOREIGN",
                    "SignalAvailableAt": "2026-01-02 18:00+08:00",
                    "EffectiveDate": dates[1],
                    "EarlyPositioningState_60D": "DIRECTIONAL_ACCUMULATION_WATCH",
                    "EarlyExitState_60D": "NO_EARLY_EXIT_EVIDENCE",
                }
            ]
        )
        events = def_run_multi_horizon_event_study(
            signals,
            index_daily,
            _official_risk_free(dates),
            BacktestConfig(
                start_date="2026-01-01",
                windows=(60,),
                horizons=(3,),
                evaluation_start_dates=("2026-01-01",),
            ),
        )
        self.assertEqual(events.iloc[0]["MaturityStatus"], "BLOCKED_INDEX_EVIDENCE")
        self.assertEqual(events.iloc[0]["DirectionalLane"], "FOREIGN")
        self.assertTrue(pd.isna(events.iloc[0]["RawForwardReturn"]))

    def test_backtest_end_date_prevents_post_cutoff_event_maturity(self) -> None:
        dates = pd.bdate_range("2026-01-02", periods=5)
        index_daily = pd.DataFrame(
            {
                "Date": dates,
                "GroupId": "G",
                "IndexMethod": "GI_HIER",
                "IndexLevel": [100.0, 101.0, 102.0, 150.0, 200.0],
                "IndexStatus": "PASS",
            }
        )
        signals = pd.DataFrame(
            [
                {
                    "Date": dates[0],
                    "GroupId": "G",
                    "SignalAvailableAt": "2026-01-02 18:00+08:00",
                    "EffectiveDate": dates[1],
                    "EarlyPositioningState_60D": "DIRECTIONAL_ACCUMULATION_WATCH",
                }
            ]
        )
        config = BacktestConfig(
            start_date="2026-01-01",
            end_date=dates[2].strftime("%Y-%m-%d"),
            windows=(60,),
            horizons=(1, 2),
            evaluation_start_dates=("2026-01-01",),
        )
        events = def_run_multi_horizon_event_study(
            signals,
            index_daily,
            _official_risk_free(dates),
            config,
        ).set_index("HorizonSessions")
        self.assertEqual(events.loc[1, "MaturityStatus"], "MATURED")
        self.assertEqual(events.loc[1, "ExitDate"], dates[2])
        self.assertEqual(events.loc[2, "MaturityStatus"], "UNMATURED")
        self.assertTrue(pd.isna(events.loc[2, "ExitDate"]))
        self.assertTrue(pd.isna(events.loc[2, "RawForwardReturn"]))

        performance = def_compute_index_performance(
            index_daily,
            _official_risk_free(dates),
            pd.DataFrame(
                {
                    "Date": dates,
                    "BenchmarkReturn": [0.0, 0.01, 0.01, 10.0, 10.0],
                }
            ),
            config,
        )
        row = performance.iloc[0]
        self.assertEqual(int(row["ObservationCount"]), 2)
        self.assertEqual(int(row["BenchmarkObservationCount"]), 2)
        self.assertAlmostEqual(float(row["TotalReturn"]), 0.02)
        self.assertEqual(row["EvaluationEnd"], dates[2])

    def test_backtest_preserves_parallel_directional_lanes(self) -> None:
        dates = pd.bdate_range("2026-01-02", periods=4)
        index_daily = pd.DataFrame(
            {
                "Date": dates,
                "GroupId": "G",
                "IndexMethod": "GI_HIER",
                "IndexLevel": [100.0, 101.0, 102.0, 103.0],
                "IndexStatus": "PASS",
            }
        )
        shared = {
            "Date": dates[0],
            "GroupId": "G",
            "SignalAvailableAt": "2026-01-02 18:00+08:00",
            "EffectiveDate": dates[1],
            "EarlyPositioningState_60D": "DIRECTIONAL_ACCUMULATION_WATCH",
        }
        signals = pd.DataFrame(
            [
                {**shared, "DirectionalLane": "FOREIGN"},
                {**shared, "DirectionalLane": "DOMESTIC_EX_FOREIGN"},
            ]
        )
        events = def_run_multi_horizon_event_study(
            signals,
            index_daily,
            _official_risk_free(dates),
            BacktestConfig(
                start_date="2026-01-01",
                end_date="2026-01-07",
                windows=(60,),
                horizons=(1,),
                evaluation_start_dates=("2026-01-01",),
            ),
        )
        self.assertEqual(len(events), 2)
        self.assertEqual(
            set(events["DirectionalLane"]),
            {"FOREIGN", "DOMESTIC_EX_FOREIGN"},
        )


class PersistenceAndConsensusTests(unittest.TestCase):
    def test_midwrite_failure_leaves_no_formal_or_staging_directory(self) -> None:
        tables = {
            "first": pd.DataFrame({"x": [1]}),
            "second": pd.DataFrame({"x": [2]}),
        }
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "runs"
            calls = 0

            def fail_second(frame: pd.DataFrame, stem: Path) -> tuple[Path, Path]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated write failure")
                csv_path = stem.with_suffix(".csv")
                parquet_path = stem.with_suffix(".parquet")
                csv_path.write_text("x\n1\n", encoding="utf-8")
                parquet_path.write_bytes(b"test")
                return csv_path, parquet_path

            with mock.patch(
                "engine.via_append_only_io.def_require_parquet_engine"
            ), mock.patch(
                "engine.via_append_only_io.def_write_dual_table",
                side_effect=fail_second,
            ):
                with self.assertRaisesRegex(OSError, "simulated write failure"):
                    def_write_run(tables, root, "2026-01-02")
            self.assertTrue(root.exists())
            self.assertEqual(list(root.iterdir()), [])

    def test_consensus_is_exact_agreement_without_score_or_auto_mutation(self) -> None:
        group_rows = []
        member_rows = []
        for window in EXPECTED_WINDOWS:
            for lane in EXPECTED_FACTOR_LANES:
                group_rows.append(
                    {
                        "SnapshotDate": "2026-01-05",
                        "Window": window,
                        "GroupId": "G",
                        "GroupName": "CPO",
                        "GroupDecision": "PASS",
                        "EvidenceStatus": "READY",
                        "ResidualFactorLane": lane,
                    }
                )
                member_rows.append(
                    {
                        "SnapshotDate": "2026-01-05",
                        "Window": window,
                        "GroupId": "G",
                        "Ticker": "1111",
                        "Role": "UNRELATED",
                        "EvidenceStatus": "READY",
                        "ResidualFactorLane": lane,
                    }
                )
        groups = def_reconcile_group_decisions(pd.DataFrame(group_rows))
        members = def_reconcile_member_roles(pd.DataFrame(member_rows), groups)
        queue = def_build_membership_review_queue(
            members,
            pd.DataFrame([{"GroupId": "G", "Ticker": "1111.TW", "IndexEligible": True}]),
        )
        self.assertTrue(groups["RobustGroupDecision"].eq("PASS").all())
        self.assertTrue(members["RoleConsensus"].eq("UNRELATED").all())
        self.assertEqual(queue.iloc[0]["ReviewAction"], "REMOVE_CANDIDATE")
        self.assertEqual(queue.iloc[0]["ReviewStatus"], "AWAITING_HUMAN_APPROVAL")
        self.assertFalse(bool(queue.iloc[0]["AutomaticCanonicalMutation"]))
        self.assertFalse(
            any(
                "score" in column.lower()
                for frame in (groups, members, queue)
                for column in frame.columns
            )
        )

        disagreement = pd.DataFrame(group_rows)
        mask = disagreement["ResidualFactorLane"].eq("LaggedETR") & disagreement["Window"].eq(60)
        disagreement.loc[mask, "GroupDecision"] = "FAIL"
        held = def_reconcile_group_decisions(disagreement)
        self.assertEqual(
            held.loc[held["Window"].eq(60), "RobustGroupDecision"].iloc[0],
            "HOLD",
        )

        missing_decision = pd.DataFrame(group_rows)
        missing_decision.loc[
            missing_decision["ResidualFactorLane"].eq("LaggedETR")
            & missing_decision["Window"].eq(60),
            "GroupDecision",
        ] = pd.NA
        held_missing_decision = def_reconcile_group_decisions(missing_decision)
        self.assertEqual(
            held_missing_decision.loc[
                held_missing_decision["Window"].eq(60), "GroupConsensusStatus"
            ].iloc[0],
            "HOLD_INVALID_OR_MISSING_GROUP_DECISION",
        )

        unexpected_group = pd.concat(
            [
                pd.DataFrame(group_rows),
                pd.DataFrame(
                    [
                        {
                            **group_rows[0],
                            "ResidualFactorLane": "UnexpectedLane",
                        }
                    ]
                ),
            ],
            ignore_index=True,
        )
        held_unexpected = def_reconcile_group_decisions(unexpected_group)
        self.assertEqual(
            held_unexpected.loc[
                held_unexpected["Window"].eq(60), "GroupConsensusStatus"
            ].iloc[0],
            "HOLD_UNEXPECTED_FACTOR_LANE",
        )

        missing_role = pd.DataFrame(member_rows)
        missing_role.loc[
            missing_role["ResidualFactorLane"].eq("LaggedETR")
            & missing_role["Window"].eq(60),
            "Role",
        ] = pd.NA
        held_missing_role = def_reconcile_member_roles(missing_role, groups)
        self.assertEqual(
            held_missing_role.loc[
                held_missing_role["Window"].eq(60), "RoleConsensusStatus"
            ].iloc[0],
            "HOLD_INVALID_OR_MISSING_MEMBER_ROLE",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
