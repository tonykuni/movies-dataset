from __future__ import annotations

import unittest

import pandas as pd

from engine.via_active_etf_holdings_engine import def_build_active_etf_analysis


class ActiveETFStoryTSMCIsolationTests(unittest.TestCase):
    def test_every_formal_dataframe_is_capped_at_exact_evidence_cutoff(
        self,
    ) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=8)
        cutoff = pd.Timestamp("2026-01-05 18:30+08:00")
        raw = pd.DataFrame(
            [
                {
                    "ETFId": "00981A",
                    "PortfolioDate": "2026-01-02",
                    "AvailableAt": "2026-01-02 18:00+08:00",
                    "Ticker": "1111.TW",
                    "Shares": 100.0,
                    "WeightPct": 10.0,
                    "ETFUnits": 1_000.0,
                    "AUM": 1_000_000.0,
                    "Price": 50.0,
                    "IsComplete": True,
                    "SourcePayloadHash": "KNOWN_SNAPSHOT",
                },
                {
                    "ETFId": "00981A",
                    "PortfolioDate": "2026-01-05",
                    "AvailableAt": "2026-01-05 18:00+08:00",
                    "Ticker": "1111.TW",
                    "Shares": 120.0,
                    "WeightPct": 12.0,
                    "ETFUnits": 1_000.0,
                    "AUM": 1_000_000.0,
                    "Price": 50.0,
                    "IsComplete": True,
                    "SourcePayloadHash": "KNOWN_SNAPSHOT_2",
                },
                # A late correction to an already-known portfolio date.  Its
                # own AvailableAt is after the formal evidence cutoff, so none
                # of its raw or derived values may be published yet.
                {
                    "ETFId": "00981A",
                    "PortfolioDate": "2026-01-05",
                    "AvailableAt": "2026-01-06 18:00+08:00",
                    "Ticker": "1111.TW",
                    "Shares": 9_999.0,
                    "WeightPct": 99.0,
                    "ETFUnits": 1_000.0,
                    "AUM": 1_000_000.0,
                    "Price": 50.0,
                    "IsComplete": True,
                    "SourcePayloadHash": "FUTURE_LATE_REVISION",
                },
                {
                    "ETFId": "009A01",
                    "PortfolioDate": "2026-01-06",
                    "AvailableAt": "2026-01-06 19:00+08:00",
                    "Ticker": "9999.TW",
                    "Shares": 7_777.0,
                    "WeightPct": 77.0,
                    "ETFUnits": 1_000.0,
                    "AUM": 1_000_000.0,
                    "Price": 50.0,
                    "IsComplete": True,
                    "SourcePayloadHash": "FUTURE_ONLY_SNAPSHOT",
                },
            ]
        )
        membership = pd.DataFrame(
            [
                {
                    "GroupId": "KNOWN_STORY",
                    "GroupName": "已知故事",
                    "Ticker": "1111.TW",
                    "Decision": "APPROVED",
                },
                {
                    "GroupId": "FUTURE_STORY",
                    "GroupName": "未來故事",
                    "Ticker": "9999.TW",
                    "Decision": "APPROVED",
                },
            ]
        )

        analysis = def_build_active_etf_analysis(
            raw,
            cutoff,
            membership=membership,
            trading_calendar=calendar,
        )
        cutoff_utc = cutoff.tz_convert("UTC")

        for name, table in analysis.items():
            if not isinstance(table, pd.DataFrame):
                continue
            for column in table.columns:
                if not column.endswith("AvailableAt"):
                    continue
                timestamps = pd.to_datetime(table[column], errors="coerce", utc=True)
                self.assertTrue(
                    timestamps.dropna().le(cutoff_utc).all(),
                    f"{name}.{column} crossed the exact evidence cutoff",
                )
            serialized = table.astype(str)
            for forbidden in (
                "FUTURE_LATE_REVISION",
                "FUTURE_ONLY_SNAPSHOT",
                "009A01",
                "9999",
                "FUTURE_STORY",
            ):
                self.assertFalse(
                    serialized.apply(
                        lambda column: column.str.contains(
                            forbidden, regex=False, na=False
                        )
                    ).any().any(),
                    f"{name} leaked {forbidden}",
                )

        prepared = analysis["prepared_snapshots"]
        self.assertEqual(set(prepared["SourcePayloadHash"]), {"KNOWN_SNAPSHOT", "KNOWN_SNAPSHOT_2"})
        current = analysis["latest_holdings_by_etf"].iloc[0]
        self.assertEqual(float(current["Shares"]), 120.0)
        event = analysis["individual_holding_events"].loc[
            analysis["individual_holding_events"]["PortfolioDate"].eq(
                pd.Timestamp("2026-01-05")
            )
        ].iloc[0]
        self.assertEqual(float(event["ActiveQty"]), 20.0)

    def test_story_outputs_exclude_2330_but_full_fund_audit_and_anchor_keep_it(
        self,
    ) -> None:
        calendar = pd.bdate_range("2026-01-02", periods=5)
        rows: list[dict[str, object]] = []
        snapshots = (
            ("2026-01-02", "2026-01-02 18:00+08:00", "S1", 100, 1_000),
            ("2026-01-05", "2026-01-05 18:00+08:00", "S2", 120, 1_100),
        )
        for portfolio_date, available_at, source_hash, other_shares, tsmc_shares in snapshots:
            rows.extend(
                [
                    {
                        "ETFId": "00981A",
                        "PortfolioDate": portfolio_date,
                        "AvailableAt": available_at,
                        "Ticker": "1111.TW",
                        "Shares": other_shares,
                        "WeightPct": 10.0,
                        "ETFUnits": 1_000,
                        "AUM": 10_000_000,
                        "Price": 50.0,
                        "IsComplete": True,
                        "SourcePayloadHash": source_hash,
                    },
                    {
                        "ETFId": "00981A",
                        "PortfolioDate": portfolio_date,
                        "AvailableAt": available_at,
                        "Ticker": "2330.TW",
                        "Shares": tsmc_shares,
                        "WeightPct": 50.0,
                        "ETFUnits": 1_000,
                        "AUM": 10_000_000,
                        "Price": 1_000.0,
                        "IsComplete": True,
                        "SourcePayloadHash": source_hash,
                    },
                ]
            )
        membership = pd.DataFrame(
            [
                {
                    "GroupId": "OTHER_STORY",
                    "GroupName": "其他故事",
                    "Ticker": "1111.TW",
                    "Decision": "APPROVED",
                },
                {
                    "GroupId": "TSMC_ONLY_STORY",
                    "GroupName": "台積電錨群",
                    "Ticker": "2330.TW",
                    "Decision": "APPROVED",
                },
                {
                    "GroupId": "OTHER_STORY",
                    "GroupName": "其他故事",
                    "Ticker": "2330.TW",
                    "Decision": "APPROVED",
                },
            ]
        )

        analysis = def_build_active_etf_analysis(
            pd.DataFrame(rows),
            "2026-01-06 00:00+08:00",
            membership=membership,
            trading_calendar=calendar,
        )

        # Source-grain audit tables remain the complete ETF portfolio.
        self.assertIn(
            "2330",
            set(analysis["latest_holdings_by_etf"]["TickerBase"]),
        )
        self.assertIn(
            "2330",
            set(analysis["individual_holding_events"]["TickerBase"]),
        )

        # Every published story/group comparison is strictly ex-2330.
        self.assertNotIn("2330", set(analysis["story_event_views"]["TickerBase"]))
        self.assertNotIn("2330", set(analysis["story_holding_views"]["TickerBase"]))
        self.assertNotIn(
            "TSMC_ONLY_STORY",
            set(analysis["group_event_consensus"]["GroupId"]),
        )
        self.assertNotIn(
            "TSMC_ONLY_STORY",
            set(analysis["group_exposure"]["GroupId"]),
        )
        for key in (
            "story_event_views",
            "story_holding_views",
            "group_event_consensus",
            "group_exposure",
        ):
            comparison = analysis[key]
            self.assertTrue(
                comparison["ComparisonUniverse"]
                .eq("ACTIVE_ETF_HOLDINGS_EX_2330")
                .all(),
                key,
            )
            self.assertTrue(comparison["TSMCExcluded"].all(), key)
        current_story_event = analysis["group_event_consensus"].loc[
            analysis["group_event_consensus"]["EvidenceDate"].eq(
                pd.Timestamp("2026-01-05")
            )
            & analysis["group_event_consensus"]["StoryView"].eq("STORY_FULL")
            & analysis["group_event_consensus"]["GroupId"].eq("OTHER_STORY")
        ].iloc[0]
        self.assertAlmostEqual(
            float(current_story_event["AllocatedActiveQtySum"]), 20.0
        )
        current_story_exposure = analysis["group_exposure"].loc[
            analysis["group_exposure"]["StoryView"].eq("STORY_FULL")
            & analysis["group_exposure"]["GroupId"].eq("OTHER_STORY")
        ].iloc[0]
        self.assertEqual(int(current_story_exposure["HoldingCount"]), 1)
        self.assertAlmostEqual(
            float(current_story_exposure["AllocatedWeightPctSum"]), 10.0
        )

        # The anchor remains inspectable at both current-holding and event grain.
        for key in (
            "tsmc_anchor_latest_holdings",
            "tsmc_anchor_holding_events",
            "tsmc_anchor_security_consensus",
            "tsmc_anchor_story_event_audit",
            "tsmc_anchor_story_holding_audit",
        ):
            anchor = analysis[key]
            self.assertFalse(anchor.empty, key)
            self.assertTrue(anchor["TickerBase"].eq("2330").all(), key)
            self.assertTrue(
                anchor["AnchorPolicy"]
                .eq(
                    "REPORTED_SEPARATELY_EXCLUDED_FROM_STORY_AND_"
                    "CROSS_GROUP_COMPARISON"
                )
                .all(),
                key,
            )

        # Existing conservation remains a full-fund audit, while an additional
        # comparison-scope check proves the ex-2330 slice also conserves.
        self.assertEqual(analysis["story_event_conservation"]["Status"], "PASS")
        self.assertEqual(
            analysis["story_event_conservation"]["EventCount"],
            analysis["individual_holding_events"]["EventId"].nunique(),
        )
        self.assertEqual(
            analysis["story_event_comparison_conservation"]["Status"], "PASS"
        )
        self.assertEqual(analysis["story_holding_conservation"]["Status"], "PASS")
        self.assertEqual(
            analysis["story_holding_conservation"]["HoldingCount"],
            analysis["latest_holdings_by_etf"]
            .groupby(["SnapshotId", "TickerBase"])
            .ngroups,
        )
        self.assertEqual(
            analysis["story_holding_comparison_conservation"]["Status"], "PASS"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
