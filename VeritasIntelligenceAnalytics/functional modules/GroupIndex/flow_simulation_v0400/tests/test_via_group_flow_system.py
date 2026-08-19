from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from engine.build_controlled_fixture import def_write_fixture
from engine.via_classification_intake import SOURCE_HTML_NAME, def_extract_candidate_membership
from engine.via_attention_share_engine import def_compute_attention_share, def_compute_group_attention_score
from engine.via_flowrot_candidate_intake import (
    CANDIDATE_SOURCE_NAME,
    def_extract_flowrot_candidate,
    def_validate_flowrot_candidate,
)
from engine.via_dynamic_classification_engine import (
    def_compute_dynamic_classification,
    def_derive_dynamic_parameters,
    def_prepare_main_force,
)
from engine.via_group_fund_flow_monitor_engine import (
    SIMULATION_FEATURES,
    def_compute_flow_simulation,
    def_compute_group_index,
    def_compute_member_roles,
    def_load_config,
    def_prepare_membership,
    def_prepare_price,
    def_run_system,
)
from engine.via_version_chain import (
    EVIDENCE_STRENGTH,
    def_build_candidate_version_chain,
    def_validate_candidate_groups,
    def_weakest_evidence,
)
from engine.via_statistical_validation_engine import (
    def_ccf_lag_spectrum,
    def_pca_absorption_rate,
    def_validate_leader_follower,
)
from engine.via_rotation_snapshot_engine import (
    EXPECTED_STATE_COUNTS,
    def_append_rotation_snapshot,
    def_build_rotation_snapshot,
    def_extract_vdf_contract_summary,
    def_validate_rotation_source_contract,
    def_validate_transition_history,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


class TestVIAGroupFlowSystem(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temporary = tempfile.TemporaryDirectory(prefix="via_group_flow_")
        cls.root = Path(cls.temporary.name)
        (cls.root / "config").mkdir(parents=True)
        (cls.root / "ssot").mkdir(parents=True)
        (cls.root / "references" / "intake").mkdir(parents=True)
        shutil.copy2(
            PROJECT_ROOT / "ssot" / "VIA_FLOWROT_Method_Thresholds_v0300.json",
            cls.root / "ssot" / "VIA_FLOWROT_Method_Thresholds_v0300.json",
        )
        shutil.copy2(
            PROJECT_ROOT / "references" / "intake" / CANDIDATE_SOURCE_NAME,
            cls.root / "references" / "intake" / CANDIDATE_SOURCE_NAME,
        )
        for source_name in [
            "32f56779-e9a8-45d5-8498-7517053f95a2.html",
            "貼上的 Markdown (1)(20260819-142001).md",
        ]:
            shutil.copy2(
                PROJECT_ROOT / "references" / "intake" / source_name,
                cls.root / "references" / "intake" / source_name,
            )
        shutil.copy2(
            PROJECT_ROOT / "ssot" / "VIA_Market_Intelligence_Registry_Summary_v0400.json",
            cls.root / "ssot" / "VIA_Market_Intelligence_Registry_Summary_v0400.json",
        )
        shutil.copy2(
            PROJECT_ROOT / "ssot" / "VIA_Rotation_Snapshot_20260718_v0400.json",
            cls.root / "ssot" / "VIA_Rotation_Snapshot_20260718_v0400.json",
        )
        def_write_fixture(cls.root / "data" / "input")
        raw_config = json.loads((PROJECT_ROOT / "config" / "system_config.json").read_text(encoding="utf-8"))
        cls.config_path = cls.root / "config" / "system_config.json"
        cls.config_path.write_text(json.dumps(raw_config, ensure_ascii=False, indent=2), encoding="utf-8")
        cls.config = def_load_config(cls.config_path)
        cls.summary = def_run_system(cls.config_path)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def test_controlled_fixture_gate_and_exact_group_contract(self) -> None:
        self.assertEqual(
            self.summary["Gate"],
            "ROTATION_T2_T3_REVIEW_CANDIDATE_49_BLOCKED_FIXTURE_REGRESSION_PASS",
        )
        self.assertEqual(self.summary["GroupCount"], 31)
        self.assertEqual(self.summary["MembershipRows"], 149)
        self.assertEqual(self.summary["HardFailures"], 0)
        self.assertFalse(self.summary["RealDataRuntimeExecuted"])

    def test_base_100_is_exact_on_first_eligible_normalization_date(self) -> None:
        index = pd.read_csv(self.root / "data" / "output" / "group_index_daily.csv", encoding="utf-8-sig")
        index["Date"] = pd.to_datetime(index["Date"], format="%Y/%m/%d")
        base = index.loc[index["Date"] >= pd.Timestamp(self.config.normalized_date)].groupby("GroupId").head(1)
        self.assertEqual(len(base), 31)
        np.testing.assert_allclose(base["GroupIndex"].to_numpy(), np.full(31, 100.0), atol=1e-10)

    def test_volume_is_never_forward_filled(self) -> None:
        raw = pd.DataFrame(
            {
                "Date": ["2026-01-02", "2026-01-05"],
                "Ticker": ["2330.TW", "2330.TW"],
                "Adj_Close": [100.0, np.nan],
                "Volume": [5000.0, np.nan],
                "TurnoverValue": [500000.0, np.nan],
            }
        )
        prepared = def_prepare_price(raw, self.config, [])
        self.assertEqual(prepared.loc[1, "Adj_Close"], 100.0)
        self.assertTrue(pd.isna(prepared.loc[1, "Volume"]))
        self.assertTrue(pd.isna(prepared.loc[1, "TurnoverValue"]))

    def test_group_index_is_invariant_to_future_price_mutation(self) -> None:
        membership_raw = pd.read_csv(self.root / "data" / "input" / "membership.csv", encoding="utf-8-sig")
        price_raw = pd.read_csv(self.root / "data" / "input" / "price.csv", encoding="utf-8-sig")
        membership = def_prepare_membership(membership_raw, self.config, [])
        price = def_prepare_price(price_raw, self.config, [])
        original = def_compute_group_index(membership, price, self.config, [])
        cutoff = pd.Timestamp("2026-05-01")
        mutated_price = price.copy()
        future = mutated_price["Date"] >= cutoff
        mutated_price.loc[future, "Adj_Close"] *= 7.0
        mutated_price["Return"] = mutated_price.groupby("Ticker", sort=False)["Adj_Close"].pct_change(fill_method=None)
        mutated = def_compute_group_index(membership, mutated_price, self.config, [])
        left = original.loc[original["Date"] < cutoff, ["Date", "GroupId", "GroupIndex"]]
        right = mutated.loc[mutated["Date"] < cutoff, ["Date", "GroupId", "GroupIndex"]]
        pd.testing.assert_frame_equal(left.reset_index(drop=True), right.reset_index(drop=True))

    def test_oos_coefficients_do_not_change_when_only_late_test_features_change(self) -> None:
        index = pd.read_csv(self.root / "data" / "output" / "group_index_daily.csv", encoding="utf-8-sig")
        flow = pd.read_csv(self.root / "data" / "output" / "group_flow_daily.csv", encoding="utf-8-sig")
        index["Date"] = pd.to_datetime(index["Date"], format="%Y/%m/%d")
        flow["Date"] = pd.to_datetime(flow["Date"], format="%Y/%m/%d")
        group_id = str(index["GroupId"].iloc[0])
        one_index = index.loc[index["GroupId"] == group_id].copy()
        one_flow = flow.loc[flow["GroupId"] == group_id].copy()
        baseline = def_compute_flow_simulation(one_index, one_flow, self.config, [])
        late_dates = set(one_flow.sort_values("Date").tail(10)["Date"])
        mutated_flow = one_flow.copy()
        mask = mutated_flow["Date"].isin(late_dates)
        mutated_flow.loc[mask, SIMULATION_FEATURES] = mutated_flow.loc[mask, SIMULATION_FEATURES] * 25.0 + 3.0
        mutated = def_compute_flow_simulation(one_index, mutated_flow, self.config, [])
        original_coefficients = baseline.loc[baseline["ScenarioId"] == "BASELINE", "Coefficients"].iloc[0]
        mutated_coefficients = mutated.loc[mutated["ScenarioId"] == "BASELINE", "Coefficients"].iloc[0]
        self.assertEqual(original_coefficients, mutated_coefficients)

    def test_leader_is_not_forced_without_evidence(self) -> None:
        dates = pd.bdate_range("2026-01-02", periods=70)
        membership = pd.DataFrame(
            {
                "GroupId": ["G"],
                "GroupName": ["Flat Group"],
                "Ticker": ["2330.TW"],
                "PrimaryEconomicIdentity": ["Flat"],
                "IndexEligible": [True],
            }
        )
        price = pd.DataFrame(
            {
                "Date": dates,
                "Ticker": "2330.TW",
                "Adj_Close": 100.0,
                "Return": 0.0,
                "TurnoverValue": 1_000_000.0,
            }
        )
        group_index = pd.DataFrame(
            {"Date": dates, "GroupId": "G", "GroupName": "Flat Group", "GroupReturn": 0.0}
        )
        roles = def_compute_member_roles(membership, price, group_index, self.config, [])
        self.assertEqual(roles.loc[0, "GroupLeaderStatus"], "NO_CONFIRMED_LEADER")
        self.assertNotEqual(roles.loc[0, "CompositeRole"], "LEADER")

    def test_flow_windows_and_date_formats_are_contract_compliant(self) -> None:
        flow_path = self.root / "data" / "output" / "group_flow_daily.csv"
        flow = pd.read_csv(flow_path, encoding="utf-8-sig")
        for suffix in ["1D", "5D", "20D", "60D", "120D", "240D", "YTD", "SinceNormalized"]:
            self.assertIn(f"InstitutionalNetAmount_{suffix}", flow.columns)
        self.assertTrue(flow["Date"].str.fullmatch(r"\d{4}/\d{2}/\d{2}").all())

    def test_dashboard_contract(self) -> None:
        path = self.root / "data" / "output" / "VIA_TW_Group_Flow_Simulation_System_v0400.html"
        html = path.read_text(encoding="utf-8")
        for required in [
            '"actualGroupCount":31',
            'id="normalizedDate"',
            'id="cumulative"',
            'id="collapse"',
            'id="viewClassification"',
            'id="classificationPanel"',
            'id="roleFilter"',
            'id="leaderFilter"',
            'data-open-flow=',
            "A_LEADER",
            "B_PEER",
            "C_LAGGARD_EXCEPTION",
            "APPEND_ONLY_ERRATA",
            "NEXT_REBALANCE",
            ".primary-chart{height:240px}",
            ".secondary-chart{height:160px}",
            "ctx.globalAlpha=.6",
            "Controlled Fixture",
            "VIA_CLASSIFICATION_REVIEW_V0400",
            "EXCLUDE_PROPOSED",
            "APPEND_ONLY_REVIEW_DECISIONS",
            'id="viewBacktest"',
            'id="viewParameters"',
            "LAGGED_CLOSE_VOLUME_WEIGHT",
            'id="viewPipeline"',
            'id="pipelinePanel"',
            "四段管線 · 一條版本鏈",
            "M-1A Attention Share",
            "candidateGroups",
            "versionChain",
            'id="viewRotation"',
            'id="rotationPanel"',
            "rotationSnapshot",
            "SOURCE_REPORTED_T2_T3_UNVERIFIED",
            "Historical Snapshot",
            "VDF 擷取契約 · 未執行",
            "14 類 · 77 列市場情報登錄",
        ]:
            self.assertIn(required, html)
        self.assertNotIn('<script src="http', html.lower())
        self.assertNotIn('<link href="http', html.lower())

    def test_classification_role_contract_and_next_rebalance_policy(self) -> None:
        roles = pd.read_csv(
            self.root / "data" / "output" / "member_roles_latest.csv",
            encoding="utf-8-sig",
        )
        required = {
            "Name",
            "Market",
            "ClassificationRoleCode",
            "RoleStatus",
            "IncludeInGroupIndex",
            "RoleEffectiveCycle",
            "RoleEvidenceWindows",
        }
        self.assertTrue(required.issubset(set(roles.columns)))
        laggers = roles.loc[roles["CompositeRole"] == "LAGGER"]
        self.assertGreater(len(laggers), 0)
        self.assertTrue(laggers["ClassificationRoleCode"].eq("C_LAGGARD_EXCEPTION").all())
        self.assertTrue(laggers["RoleStatus"].eq("dormant").all())
        self.assertTrue((~laggers["IncludeInGroupIndex"].astype(bool)).all())
        self.assertTrue(roles["RoleEffectiveCycle"].eq("NEXT_REBALANCE").all())
        self.assertTrue(roles["RoleEvidenceWindows"].eq("20D/60D").all())

    def test_classification_ui_uses_same_payload_as_flow_monitor(self) -> None:
        path = self.root / "data" / "output" / "VIA_TW_Group_Flow_Simulation_System_v0400.html"
        html = path.read_text(encoding="utf-8")
        self.assertEqual(html.count("const DATA="), 1)
        self.assertIn("const indexMap=byGroup(DATA.groupIndex)", html)
        self.assertIn("roleMap=byGroup(DATA.memberRoles)", html)
        self.assertIn("查看資金流", html)

    def test_attachment_candidate_intake_is_exact_and_append_only(self) -> None:
        reference = PROJECT_ROOT / "references" / "intake"
        membership, quality = def_extract_candidate_membership(reference / SOURCE_HTML_NAME, reference)
        self.assertEqual(quality["GroupCount"], 31)
        self.assertEqual(quality["MembershipRows"], 149)
        self.assertEqual(quality["DistinctTickers"], 148)
        self.assertEqual(quality["MultiGroupTickerCount"], 1)
        self.assertEqual(quality["DuplicateGroupTickerRows"], 0)
        self.assertEqual(quality["CanonicalMutation"], 0)
        self.assertSetEqual(set(membership["CandidateRole"]), {"LEADER", "PEER", "LAGGARD"})

    def test_flowrot_49_candidate_is_exact_and_preserves_conflict(self) -> None:
        source = PROJECT_ROOT / "references" / "intake" / CANDIDATE_SOURCE_NAME
        groups, members, quality = def_extract_flowrot_candidate(source)
        def_validate_flowrot_candidate(groups, members, quality)
        self.assertEqual(quality["GroupCount"], 49)
        self.assertEqual(quality["MembershipRows"], 252)
        self.assertEqual(quality["DistinctTickers"], 241)
        self.assertEqual(quality["RoleCounts"], {"LEADER": 63, "PEER": 126, "LAGGARD": 63})
        self.assertEqual(quality["MarketCounts"], {"TWSE": 190, "TPEX": 62})
        self.assertEqual(quality["DuplicateGroupTickerRows"], 1)
        conflict = members.loc[members["VerificationIssue"] != ""]
        self.assertEqual(set(conflict["TickerCode"]), {"6116"})
        self.assertEqual(set(conflict["Name"]), {"彩晶", "瀚宇彩晶"})
        self.assertEqual(
            set(groups.loc[groups["InputIntegrityStatus"] != "PASS", "GroupName"]),
            {"面板"},
        )

    def test_candidate_49_index_gate_is_zero(self) -> None:
        result = pd.read_csv(
            self.root / "data" / "output" / "candidate_group_validation_v21.csv",
            encoding="utf-8-sig",
        )
        self.assertEqual(len(result), 49)
        self.assertEqual(int(result["ValidationStatus"].eq("PASS").sum()), 0)
        self.assertTrue(result["IndexGenerationStatus"].eq("BLOCKED").all())
        self.assertEqual(
            set(result.loc[result["ValidationStatus"] == "BLOCKED_VDF_REQUIRED", "GroupName"]),
            {"半導體設備", "資安/系統整合", "觀光餐飲", "ASIC 設計服務"},
        )

    def test_rotation_snapshot_exact_five_state_contract(self) -> None:
        candidate = pd.read_csv(
            self.root / "data" / "output" / "candidate_group_validation_v21.csv",
            encoding="utf-8-sig",
        )
        snapshot, quality = def_build_rotation_snapshot(candidate)
        self.assertEqual(len(snapshot), 18)
        self.assertEqual(quality["RegistryDeclaredGroupCount"], 29)
        self.assertEqual(quality["StateCounts"], EXPECTED_STATE_COUNTS)
        self.assertTrue(quality["StateCountsMatch"])
        self.assertTrue(snapshot["EvidenceTier"].eq("SOURCE_REPORTED_T2_T3_UNVERIFIED").all())
        self.assertTrue(snapshot["IndexUseStatus"].eq("PROHIBITED_UNTIL_T1_AND_VALIDATE_PASS").all())
        self.assertTrue(snapshot["CanonicalMutation"].eq(0).all())
        source_validation = def_validate_rotation_source_contract(
            PROJECT_ROOT / "ssot" / "VIA_Rotation_Snapshot_20260718_v0400.json",
            snapshot,
        )
        self.assertTrue(source_validation["SourceRuntimeMatch"])
        self.assertEqual(source_validation["SourceRowsValidated"], 18)
        self.assertEqual(source_validation["SourceProvenance"], "USER_PROVIDED_MESSAGE_2026-08-19")

    def test_rotation_taxonomy_mapping_preserves_split_and_unmapped_review(self) -> None:
        candidate = pd.read_csv(
            self.root / "data" / "output" / "candidate_group_validation_v21.csv",
            encoding="utf-8-sig",
        )
        snapshot, quality = def_build_rotation_snapshot(candidate)
        self.assertEqual(quality["UnmappedGroups"], ["石英/頻率元件"])
        pcb = snapshot.loc[snapshot["TrackedGroupName"] == "PCB"].iloc[0]
        self.assertEqual(pcb["CandidateMappingStatus"], "SPLIT_PARENT")
        self.assertEqual(len(pcb["Candidate49Targets"].split(" | ")), 4)
        memory = snapshot.loc[snapshot["TrackedGroupName"] == "記憶體封測/模組"].iloc[0]
        self.assertEqual(memory["CandidateMappingStatus"], "CROSS_GROUP_ALIAS")

    def test_rotation_append_only_is_idempotent_and_rejects_rewrite(self) -> None:
        candidate = pd.read_csv(
            self.root / "data" / "output" / "candidate_group_validation_v21.csv",
            encoding="utf-8-sig",
        )
        snapshot, _ = def_build_rotation_snapshot(candidate)
        base = self.root / "data" / "output" / "rotation_append_contract"
        first = def_append_rotation_snapshot(snapshot, base)
        second = def_append_rotation_snapshot(snapshot, base)
        self.assertEqual(first["appended"], 18)
        self.assertEqual(second["appended"], 0)
        changed = snapshot.copy()
        changed.loc[changed["TrackedGroupName"] == "重電", "State"] = "EBB"
        with self.assertRaisesRegex(ValueError, "Append-only conflict"):
            def_append_rotation_snapshot(changed, base)

    def test_rotation_state_machine_blocks_illegal_jump(self) -> None:
        history = pd.DataFrame(
            [
                {"TrackedGroupName": "X", "AsOfDate": "2026-07-18", "State": "DORMANT"},
                {"TrackedGroupName": "X", "AsOfDate": "2026-07-25", "State": "OVERHEAT"},
            ]
        )
        findings = def_validate_transition_history(history)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["Status"], "BLOCKED_ILLEGAL_STATE_TRANSITION")

    def test_vdf_control_panel_is_contract_only_not_runtime(self) -> None:
        source = PROJECT_ROOT / "references" / "intake" / "32f56779-e9a8-45d5-8498-7517053f95a2.html"
        summary = def_extract_vdf_contract_summary(source)
        self.assertEqual(summary["DeclaredTWSE"], 1200)
        self.assertEqual(summary["DeclaredTPEX"], 647)
        self.assertEqual(summary["DeclaredTaiwanTotal"], 1847)
        self.assertEqual(summary["FetcherExecution"], 0)
        self.assertEqual(summary["NetworkExecution"], 0)
        self.assertEqual(summary["CanonicalMutation"], 0)

    def test_market_intelligence_registry_contract_totals_77(self) -> None:
        registry = json.loads(
            (PROJECT_ROOT / "ssot" / "VIA_Market_Intelligence_Registry_Summary_v0400.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(len(registry["categories"]), 14)
        self.assertEqual(sum(row["items"] for row in registry["categories"]), 77)
        self.assertEqual(registry["runtime_value_policy"], "NEEDS_FETCH_NO_FABRICATION")

    def test_run_summary_keeps_29_31_49_and_evidence_boundaries_separate(self) -> None:
        self.assertEqual(self.summary["RotationRegistryDeclaredGroupCount"], 29)
        self.assertEqual(self.summary["RotationTrackedGroupCount"], 18)
        self.assertEqual(self.summary["GroupCount"], 31)
        self.assertEqual(self.summary["CandidateGroupCount"], 49)
        self.assertEqual(self.summary["RotationM3T1Count"], 0)
        self.assertEqual(self.summary["RotationIndexEligible"], 0)
        self.assertEqual(self.summary["VDFContractFetcherExecution"], 0)
        self.assertEqual(self.summary["MarketIntelligenceRegistryItems"], 77)

    def test_attention_share_exact_double_deduction_and_tsmc_special_case(self) -> None:
        stock = pd.DataFrame(
            [
                {"Date": "2026-08-18", "Ticker": "2330.TW", "TurnoverValue": 600.0, "DayTradeTurnover": 88.0},
                {"Date": "2026-08-18", "Ticker": "9999.TW", "TurnoverValue": 41.02, "DayTradeTurnover": 10.0},
                {"Date": "2026-08-18", "Ticker": "0050.TW", "TurnoverValue": 100.0, "DayTradeTurnover": 20.0, "AssetType": "ETF"},
            ]
        )
        stock.loc[stock["AssetType"].isna(), "AssetType"] = "EQUITY"
        market = pd.DataFrame(
            [
                {"Date": "2026-08-18", "Market": "TWSE", "GrossTurnoverValue": 4128.0, "DayTradeTurnoverValue": 1200.0},
                {"Date": "2026-08-18", "Market": "TPEX", "GrossTurnoverValue": 892.0, "DayTradeTurnoverValue": 206.0},
            ]
        )
        result, denominator = def_compute_attention_share(stock, market)
        self.assertAlmostEqual(float(denominator.loc[0, "NetDenominator"]), 3102.0)
        ordinary = result.loc[result["Ticker"] == "9999.TW"].iloc[0]
        self.assertAlmostEqual(float(ordinary["AttentionShareRaw"]), 0.01)
        tsmc = result.loc[result["Ticker"] == "2330.TW"].iloc[0]
        self.assertTrue(pd.isna(tsmc["AttentionShareRaw"]))
        self.assertAlmostEqual(float(tsmc["TSMCBothMarketShare"]), 512.0 / 3614.0)
        etf = result.loc[result["Ticker"] == "0050.TW"].iloc[0]
        self.assertEqual(etf["AttentionStatus"], "EXCLUDED_NON_EQUITY")

    def test_attention_share_blocks_when_tpex_is_missing(self) -> None:
        stock = pd.DataFrame(
            [{"Date": "2026-08-18", "Ticker": "2330.TW", "TurnoverValue": 600.0, "DayTradeTurnover": 88.0}]
        )
        market = pd.DataFrame(
            [{"Date": "2026-08-18", "Market": "TWSE", "GrossTurnoverValue": 4128.0, "DayTradeTurnoverValue": 1200.0}]
        )
        result, denominator = def_compute_attention_share(stock, market)
        self.assertEqual(denominator.loc[0, "DenominatorStatus"], "BLOCKED_INCOMPLETE_BOTH_MARKETS_OR_TSMC")
        self.assertTrue(result["AttentionShareRaw"].isna().all())

    def test_group_attention_score_dedupes_same_group_ticker(self) -> None:
        dates = pd.bdate_range("2026-01-02", periods=20)
        attention = pd.DataFrame(
            [
                {"Date": date, "Ticker": ticker, "AttentionShareRaw": value, "AttentionStatus": "PASS"}
                for date in dates
                for ticker, value in [("A.TW", 0.10), ("B.TW", 0.20)]
            ]
        )
        membership = pd.DataFrame(
            {
                "GroupName": ["G1", "G1", "G2"],
                "Ticker": ["A.TW", "A.TW", "B.TW"],
            }
        )
        scored = def_compute_group_attention_score(attention, membership)
        latest = scored.loc[scored["Date"] == dates[-1]].set_index("GroupName")
        self.assertAlmostEqual(float(latest.loc["G1", "AttentionShareRaw"]), 0.10)
        self.assertAlmostEqual(float(latest.loc["G1", "AttentionScorePct"]), 0.50)
        self.assertAlmostEqual(float(latest.loc["G2", "AttentionScorePct"]), 1.00)

    def test_statistical_engine_detects_known_two_day_lead_without_lag_snooping(self) -> None:
        generator = np.random.default_rng(731)
        innovations = generator.normal(0, 1, 260)
        leader = np.zeros(260)
        for index in range(1, len(leader)):
            leader[index] = 0.82 * leader[index - 1] + innovations[index]
        follower = np.r_[generator.normal(0, 0.2, 2), leader[:-2] + generator.normal(0, 0.12, 258)]
        peer = 0.75 * leader + generator.normal(0, 0.35, 260)
        returns = pd.DataFrame({"LEADER": leader, "FOLLOWER": follower, "PEER": peer})
        pca = def_pca_absorption_rate(returns)
        self.assertEqual(pca["Status"], "PASS")
        self.assertGreater(float(pca["PCAAbsorption"]), 0.40)
        spectrum = def_ccf_lag_spectrum(leader, follower, max_lag=5)
        self.assertEqual(int(spectrum.loc[spectrum["Correlation"].idxmax(), "Lag"]), 2)
        validated = def_validate_leader_follower(
            returns,
            "LEADER",
            "FOLLOWER",
            permutations=200,
        )
        self.assertEqual(validated["ValidationStatus"], "PASS")
        self.assertEqual(validated["CCFPermutation"]["DetectedLag"], 2)
        self.assertLess(validated["CCFPermutation"]["PValue"], 0.05)
        self.assertEqual(validated["CCFPermutation"]["MultipleLagCorrection"], "MAX_OVER_LAGS")

    def test_evidence_chain_can_only_stay_same_or_degrade(self) -> None:
        self.assertEqual(def_weakest_evidence("PROXY", "MEASURED"), "PROXY")
        groups, _, _ = def_extract_flowrot_candidate(
            PROJECT_ROOT / "references" / "intake" / CANDIDATE_SOURCE_NAME
        )
        validated = def_validate_candidate_groups(groups, attention_min=0.80, leadership_min=0.75)
        chain = def_build_candidate_version_chain(
            validated,
            asof_date="2026-08-18",
            source_ref=CANDIDATE_SOURCE_NAME,
            parameters_digest="TEST",
        )
        strength = chain["InheritedEvidenceTier"].map(EVIDENCE_STRENGTH).tolist()
        self.assertEqual(strength, sorted(strength))
        self.assertEqual(chain.loc[chain["Stage"] == "INDEX", "Status"].iloc[0], "BLOCKED")
        self.assertEqual(chain.loc[chain["Stage"] == "INDEX", "BlockReason"].iloc[0], "VALIDATE_NOT_PASS")

    def test_backtest_uses_configured_risk_free_rate(self) -> None:
        summary = pd.read_csv(
            self.root / "data" / "output" / "rotation_backtest_summary.csv",
            encoding="utf-8-sig",
        )
        self.assertAlmostEqual(float(summary.loc[0, "RiskFreeRate"]), 0.0215)
        self.assertEqual(summary.loc[0, "RiskFreeEvidenceTier"], "SOURCE_REPORTED_SOURCED_UNVERIFIED")

    def test_walk_forward_backtest_uses_prior_signal_date(self) -> None:
        daily = pd.read_csv(self.root / "data" / "output" / "rotation_backtest_daily.csv", encoding="utf-8-sig")
        signal = pd.to_datetime(daily["SignalDate"], format="%Y/%m/%d")
        realized = pd.to_datetime(daily["Date"], format="%Y/%m/%d")
        self.assertTrue((signal < realized).all())
        self.assertTrue(daily["TransactionCost"].ge(0).all())
        self.assertIn("StrategyNetReturn", daily.columns)

    def test_dynamic_size_uses_lagged_market_cap(self) -> None:
        membership_raw = pd.read_csv(self.root / "data" / "input" / "membership.csv", encoding="utf-8-sig")
        price_raw = pd.read_csv(self.root / "data" / "input" / "price.csv", encoding="utf-8-sig")
        institutional = pd.read_csv(self.root / "data" / "input" / "institutional.csv", encoding="utf-8-sig")
        institutional["Date"] = pd.to_datetime(institutional["Date"])
        main_force = def_prepare_main_force(pd.read_csv(self.root / "data" / "input" / "main_force.csv", encoding="utf-8-sig"))
        membership = def_prepare_membership(membership_raw, self.config, [])
        price = def_prepare_price(price_raw, self.config, [])
        index = def_compute_group_index(membership, price, self.config, [])
        core_roles = def_compute_member_roles(membership, price, index, self.config, [])
        params = def_derive_dynamic_parameters(price)
        base, _ = def_compute_dynamic_classification(membership, price, institutional, main_force, core_roles, params, [])
        mutated_raw = price_raw.copy()
        latest = pd.to_datetime(mutated_raw["Date"]).max()
        mutated_raw.loc[pd.to_datetime(mutated_raw["Date"]) == latest, "MarketCap"] *= 1000.0
        mutated_price = def_prepare_price(mutated_raw, self.config, [])
        mutated, _ = def_compute_dynamic_classification(membership, mutated_price, institutional, main_force, core_roles, params, [])
        pd.testing.assert_series_equal(
            base.sort_values(["GroupId", "Ticker"])["SizeTier"].reset_index(drop=True),
            mutated.sort_values(["GroupId", "Ticker"])["SizeTier"].reset_index(drop=True),
        )

    def test_main_force_is_not_inferred_when_source_is_missing(self) -> None:
        membership = def_prepare_membership(
            pd.read_csv(self.root / "data" / "input" / "membership.csv", encoding="utf-8-sig"),
            self.config,
            [],
        )
        price = def_prepare_price(
            pd.read_csv(self.root / "data" / "input" / "price.csv", encoding="utf-8-sig"),
            self.config,
            [],
        )
        institutional = pd.read_csv(self.root / "data" / "input" / "institutional.csv", encoding="utf-8-sig")
        institutional["Date"] = pd.to_datetime(institutional["Date"])
        missing_source = pd.read_csv(self.root / "data" / "input" / "main_force.csv", encoding="utf-8-sig")
        missing_source[["MainForceNetAmount", "BranchConcentration"]] = np.nan
        main_force = def_prepare_main_force(missing_source)
        index = def_compute_group_index(membership, price, self.config, [])
        core_roles = def_compute_member_roles(membership, price, index, self.config, [])
        roles, _ = def_compute_dynamic_classification(
            membership,
            price,
            institutional,
            main_force,
            core_roles,
            def_derive_dynamic_parameters(price),
            [],
        )
        self.assertTrue(roles["MainForceControlScore"].isna().all())
        self.assertFalse(roles["CapitalControlStyle"].eq("MAIN_FORCE").any())

    def test_real_data_mode_rejects_fixture_markers(self) -> None:
        raw_config = json.loads(self.config_path.read_text(encoding="utf-8"))
        raw_config["data_mode"] = "REAL_DATA"
        real_config = self.root / "config" / "real_rejection_test.json"
        real_config.write_text(json.dumps(raw_config, ensure_ascii=False, indent=2), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "rejected fixture/demo"):
            def_run_system(real_config)


if __name__ == "__main__":
    unittest.main()
