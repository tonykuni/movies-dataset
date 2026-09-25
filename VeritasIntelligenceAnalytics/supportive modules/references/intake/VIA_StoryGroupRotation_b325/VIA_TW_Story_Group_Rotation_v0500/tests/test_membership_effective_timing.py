from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from engine.via_active_etf_holdings_engine import def_map_events_to_story_groups
from engine.via_flow_transfer_matrix_engine import (
    DIRECTIONAL_LANES,
    REQUIRED_FULL_MARKET_GATE_STATUS,
    def_build_flow_transfer_outputs,
)
from engine.via_hierarchical_group_index_engine import def_build_parallel_group_indices
from engine.via_pit_membership_engine import (
    REQUIRED_EVENT_COLUMNS,
    def_apply_approved_change_next_session,
    def_materialize_membership_history,
    def_validate_membership_event_chain,
)


class AppliedDateMembershipTimingTests(unittest.TestCase):
    @staticmethod
    def _membership_change() -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "GroupId": "G",
                    "GroupName": "G",
                    "Ticker": "1111.TW",
                    "ValidFrom": "2026-01-02",
                    "ValidTo": "2026-01-02",
                    "Decision": "APPROVED",
                },
                {
                    "GroupId": "G",
                    "GroupName": "G",
                    "Ticker": "2222.TW",
                    "ValidFrom": "2026-01-05",
                    "ValidTo": pd.NaT,
                    "Decision": "APPROVED",
                },
            ]
        )

    @staticmethod
    def _index_stock() -> pd.DataFrame:
        dates = pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"])
        rows: list[dict[str, object]] = []
        prices = {
            "1111.TW": (100.0, 90.0, 80.0),
            "2222.TW": (100.0, 110.0, 121.0),
            "2330.TW": (1000.0, 1010.0, 1020.0),
        }
        for ticker, path in prices.items():
            for date, price in zip(dates, path):
                rows.append(
                    {
                        "Date": date,
                        "Ticker": ticker,
                        "Adj_Close": price,
                        "FreeFloatMarketCap": price * 100.0,
                        "MarketCap": price * 120.0,
                        "ETR": price * 10.0,
                    }
                )
        return pd.DataFrame(rows)

    def test_index_uses_applied_date_membership_but_prior_session_weights(self) -> None:
        built = def_build_parallel_group_indices(
            self._index_stock(), self._membership_change()
        )
        self.assertEqual(built["quality"]["BadMembershipEffectiveTimingRows"], 0)
        weights = built["weights"]
        first_effective = weights.loc[
            weights["AppliedDate"].eq(pd.Timestamp("2026-01-05"))
            & weights["GroupId"].eq("G")
        ]

        self.assertEqual(set(first_effective["Ticker"]), {"2222"})
        self.assertNotIn("1111", set(first_effective["Ticker"]))
        self.assertTrue(
            first_effective["WeightDate"].eq(pd.Timestamp("2026-01-02")).all()
        )
        self.assertTrue(
            first_effective["MembershipAsOfDate"]
            .eq(pd.Timestamp("2026-01-05"))
            .all()
        )
        self.assertTrue(
            first_effective["MembershipAsOfDate"]
            .eq(first_effective["AppliedDate"])
            .all()
        )
        first_return = built["index_long"].loc[
            built["index_long"]["Date"].eq(pd.Timestamp("2026-01-05"))
            & built["index_long"]["GroupId"].eq("G")
            & built["index_long"]["Method"].eq("GI_EW")
        ].iloc[0]
        self.assertAlmostEqual(float(first_return["GroupReturn"]), 0.10)
        self.assertEqual(int(first_return["ConstituentCount"]), 1)

    def test_transfer_uses_applied_date_membership_with_prior_allocation_date(self) -> None:
        stock = self._index_stock().rename(columns={"ETR": "AttentionETR"})
        stock["LimitLockDataStatus"] = "PASS_LIMIT_LOCK_FLAGS"
        for lane in DIRECTIONAL_LANES:
            stock[lane] = np.where(stock["Ticker"].eq("2222.TW"), 2.0, -1.0)
        stock.attrs["FullMarketGateStatus"] = REQUIRED_FULL_MARKET_GATE_STATUS

        built = def_build_flow_transfer_outputs(stock, self._membership_change())
        self.assertEqual(built["quality"]["BadMembershipEffectiveTimingRows"], 0)
        ledger = built["conserved_ledger"]
        first_effective = ledger.loc[
            ledger["AppliedDate"].eq(pd.Timestamp("2026-01-05"))
        ]
        added = first_effective.loc[first_effective["Ticker"].eq("2222")].iloc[0]
        removed = first_effective.loc[first_effective["Ticker"].eq("1111")].iloc[0]

        self.assertEqual(added["GroupId"], "G")
        self.assertEqual(removed["GroupId"], "UNMAPPED")
        self.assertEqual(added["AllocationDate"], pd.Timestamp("2026-01-02"))
        self.assertEqual(added["MembershipAsOfDate"], pd.Timestamp("2026-01-05"))
        self.assertEqual(added["MembershipAsOfDate"], added["AppliedDate"])
        self.assertEqual(
            added["AllocationTiming"],
            "APPLIED_DATE_MEMBERSHIP_WITH_PRIOR_SESSION_ALLOCATION_INPUTS",
        )


class MembershipKnowledgeTimingTests(unittest.TestCase):
    def test_known_at_is_max_of_every_populated_knowledge_gate(self) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=5)
        change = {
            "EventType": "ADD",
            "GroupId": "G",
            "GroupName": "G",
            "Ticker": "1111.TW",
            "ApprovedAt": "2026-01-02 18:00+08:00",
            "RecordedAt": "2026-01-02 18:05+08:00",
            "KnownAt": "2026-01-02 18:10+08:00",
            "AvailableAt": "2026-01-02 18:15+08:00",
            "IngestedAt": "2026-01-02 18:20+08:00",
            "ValidFrom": "",
            "ValidTo": "",
            "SourceVersion": "TEST",
            "Reason": "knowledge-gate regression",
        }
        ledger = def_apply_approved_change_next_session(
            pd.DataFrame(columns=list(REQUIRED_EVENT_COLUMNS)), change, calendar
        )

        before_ingestion = def_materialize_membership_history(
            ledger, calendar, known_at="2026-01-02 18:19+08:00"
        )
        after_ingestion = def_materialize_membership_history(
            ledger, calendar, known_at="2026-01-02 18:20+08:00"
        )
        self.assertTrue(before_ingestion.empty)
        self.assertEqual(len(after_ingestion), 1)
        self.assertEqual(
            pd.Timestamp(after_ingestion.iloc[0]["KnownAt"]),
            pd.Timestamp("2026-01-02 18:20+08:00"),
        )

    def test_late_recording_prevents_backfilled_approval_from_being_visible(self) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=5)
        change = {
            "EventType": "ADD",
            "GroupId": "G",
            "GroupName": "G",
            "Ticker": "1111.TW",
            "ApprovedAt": "2026-01-02 18:00+08:00",
            "RecordedAt": "2026-01-06 09:00+08:00",
            "ValidFrom": "",
            "ValidTo": "",
            "SourceVersion": "TEST",
            "Reason": "late ledger ingestion",
        }
        ledger = def_apply_approved_change_next_session(
            pd.DataFrame(columns=list(REQUIRED_EVENT_COLUMNS)), change, calendar
        )
        self.assertTrue(
            def_materialize_membership_history(
                ledger, calendar, known_at="2026-01-05 23:59+08:00"
            ).empty
        )
        visible = def_materialize_membership_history(
            ledger, calendar, known_at="2026-01-06 09:00+08:00"
        )
        self.assertEqual(len(visible), 1)
        self.assertEqual(
            pd.Timestamp(visible.iloc[0]["KnownAt"]),
            pd.Timestamp("2026-01-06 09:00+08:00"),
        )

    def test_invalid_optional_knowledge_timestamp_fails_closed(self) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=5)
        change = {
            "EventType": "ADD",
            "GroupId": "G",
            "GroupName": "G",
            "Ticker": "1111.TW",
            "ApprovedAt": "2026-01-02 18:00+08:00",
            "RecordedAt": "2026-01-02 18:05+08:00",
            "AvailableAt": "not-a-timestamp",
            "ValidFrom": "",
            "ValidTo": "",
            "SourceVersion": "TEST",
            "Reason": "invalid knowledge gate",
        }
        with self.assertRaises(ValueError):
            def_apply_approved_change_next_session(
                pd.DataFrame(columns=list(REQUIRED_EVENT_COLUMNS)), change, calendar
            )

    def test_knowledge_fields_are_hash_bound_and_remove_closure_is_known_late(self) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=6)
        base = {
            "EventType": "ADD",
            "GroupId": "G",
            "GroupName": "G",
            "Ticker": "1111.TW",
            "ApprovedAt": "2026-01-02 18:00+08:00",
            "RecordedAt": "2026-01-02 18:05+08:00",
            "AvailableAt": "2026-01-02 18:10+08:00",
            "ValidFrom": "",
            "ValidTo": "",
            "SourceVersion": "TEST",
            "Reason": "initial add",
        }
        ledger = def_apply_approved_change_next_session(
            pd.DataFrame(columns=list(REQUIRED_EVENT_COLUMNS)), base, calendar
        )
        ledger = def_apply_approved_change_next_session(
            ledger,
            {
                **base,
                "EventType": "REMOVE",
                "ApprovedAt": "2026-01-05 18:00+08:00",
                "RecordedAt": "2026-01-07 09:00+08:00",
                "AvailableAt": "2026-01-05 18:10+08:00",
                "Reason": "late-recorded removal",
            },
            calendar,
        )

        before_recording = def_materialize_membership_history(
            ledger, calendar, known_at="2026-01-06 23:59+08:00"
        )
        complete_history = def_materialize_membership_history(ledger, calendar)
        self.assertTrue(pd.isna(before_recording.iloc[0]["ValidTo"]))
        self.assertEqual(
            pd.Timestamp(before_recording.iloc[0]["KnownAt"]),
            pd.Timestamp("2026-01-02 18:10+08:00"),
        )
        self.assertEqual(
            pd.Timestamp(complete_history.iloc[0]["KnownAt"]),
            pd.Timestamp("2026-01-07 09:00+08:00"),
        )

        tampered = ledger.copy()
        tampered.loc[0, "AvailableAt"] = "2026-01-02T18:11:00+08:00"
        with self.assertRaisesRegex(ValueError, "EventKnownAt|hash"):
            def_validate_membership_event_chain(tampered)


class ActiveETFMembershipTimingTests(unittest.TestCase):
    def test_event_story_mapping_uses_effective_date_not_evidence_date(self) -> None:
        membership = pd.DataFrame(
            [
                {
                    "GroupId": "CPO",
                    "GroupName": "CPO",
                    "Ticker": "1111.TW",
                    "ValidFrom": "2026-01-05",
                    "ValidTo": pd.NaT,
                    "Decision": "APPROVED",
                }
            ]
        )
        event = pd.DataFrame(
            [
                {
                    "EventId": "ETF-EVENT-1",
                    "ETFId": "00981A",
                    "TickerBase": "1111",
                    "EvidenceDate": "2026-01-02",
                    "EffectiveDate": "2026-01-05",
                    "RawDeltaShares": 10.0,
                    "FundScaleMechanicalQty": 0.0,
                    "ActiveQty": 10.0,
                    "RawDeltaValue": 100.0,
                    "FundScaleMechanicalValue": 0.0,
                    "EstimatedActiveValue": 100.0,
                }
            ]
        )

        mapped = def_map_events_to_story_groups(event, membership)
        conserved = mapped.loc[mapped["StoryView"].eq("CAPITAL_CONSERVED")]
        self.assertEqual(set(conserved["GroupId"]), {"CPO"})
        self.assertNotIn("UNMAPPED", set(mapped["GroupId"]))
        self.assertTrue(
            mapped["MembershipAsOfDate"].eq(pd.Timestamp("2026-01-05")).all()
        )
        self.assertTrue(mapped["MembershipDateSource"].eq("EffectiveDate").all())


if __name__ == "__main__":
    unittest.main()
