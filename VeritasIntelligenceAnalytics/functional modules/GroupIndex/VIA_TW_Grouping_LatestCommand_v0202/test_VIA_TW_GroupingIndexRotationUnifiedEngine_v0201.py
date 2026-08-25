from __future__ import annotations

# =============================================================================
# def 00 PARAMETERS
# =============================================================================

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent
ENGINE_PATH = PROJECT_ROOT / "VIA_TW_GroupingIndexRotationUnifiedEngine_v0201.py"
MEMBERSHIP_PATH = PROJECT_ROOT / "VIA_ThreeList_CanonicalMembershipInput_v0100.csv"
EVIDENCE_ROOT = PROJECT_ROOT / "RUN_FINAL_V0201"


# =============================================================================
# def 01 FIXTURES
# =============================================================================


@pytest.fixture(scope="session")
def engine():
    spec = importlib.util.spec_from_file_location("via_v0201", ENGINE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="session")
def membership(engine):
    return engine.def_load_membership(MEMBERSHIP_PATH)


@pytest.fixture(scope="session")
def small_method_run(engine, membership):
    subset = engine.def_backtest_membership_subset(membership)
    config = engine.EngineConfig(
        membership_path=MEMBERSHIP_PATH,
        write_outputs=False,
        demo=True,
        demo_observations=120,
        max_classification_snapshots=3,
        max_lag_search_cap=4,
        permutation_shift_cap=7,
        null_group_repeats_cap=3,
    )
    raw, truth = engine.def_generate_demo_inputs(
        subset,
        120,
        config.random_seed + engine.def_stable_seed("ROTATION_TEST"),
        "ROTATION",
    )
    prices = engine.def_standardize_price_data(raw, subset, config)
    features = engine.def_compute_stock_features(prices)
    factors = engine.def_load_market_factors(prices, config)
    validity, roles, criteria, correlations = engine.def_run_point_in_time_classification(
        features, subset, factors, config
    )
    indices = engine.def_build_group_indices(features, subset, roles, config)
    return {
        "config": config,
        "membership": subset,
        "truth": truth,
        "prices": prices,
        "features": features,
        "factors": factors,
        "validity": validity,
        "roles": roles,
        "criteria": criteria,
        "correlations": correlations,
        "indices": indices,
    }


# =============================================================================
# def 02 SSOT / INPUT GOVERNANCE
# =============================================================================


def test_membership_scope_and_primary_key(membership):
    assert len(membership) == 238
    assert membership["GroupId"].nunique() == 39
    assert membership["Ticker"].nunique() == 238
    assert not membership.duplicated(["Dimension", "GroupId", "Ticker", "ValidFrom"]).any()
    assert membership["CountingFlag"].eq("COUNT").all()


def test_ticker_market_suffix(engine):
    assert engine.def_normalize_ticker("2330", "TWSE") == "2330.TW"
    assert engine.def_normalize_ticker("6488", "TPEX") == "6488.TWO"
    assert engine.def_normalize_ticker("2330.TW", "TWSE") == "2330.TW"


def test_raw_close_is_fail_closed(engine, membership):
    row = membership.iloc[[0]]
    raw = pd.DataFrame(
        {"Date": ["2026-01-02"], "Ticker": [row.iloc[0]["Ticker"]], "Close": [100.0]}
    )
    with pytest.raises(ValueError, match="Adjusted Close is required"):
        engine.def_standardize_price_data(raw, row, engine.EngineConfig(write_outputs=False))


def test_volume_and_flow_are_not_forward_filled(engine, membership):
    row = membership.iloc[[0]]
    ticker = row.iloc[0]["Ticker"]
    raw = pd.DataFrame(
        {
            "Date": pd.bdate_range("2026-01-02", periods=3),
            "Ticker": [ticker] * 3,
            "Adj_Close": [100.0, 101.0, 102.0],
            "Volume": [100.0, np.nan, 300.0],
            "Turnover": [10_000.0, 20_000.0, 30_000.0],
            "DayTradeTurnover": [1_000.0, np.nan, 3_000.0],
        }
    )
    standardized = engine.def_standardize_price_data(
        raw, row, engine.EngineConfig(write_outputs=False)
    )
    assert pd.isna(standardized.loc[1, "Volume"])
    assert pd.isna(standardized.loc[1, "NonDayTradeTurnover"])


# =============================================================================
# def 03 CLASSIFICATION / POINT-IN-TIME / INDEX TESTS
# =============================================================================


def test_point_in_time_roles_take_effect_next_session(small_method_run):
    roles = small_method_run["roles"]
    assert not roles.empty
    assert (roles["EffectiveDate"] > roles["SnapshotDate"]).all()


def test_membership_validity_is_separate_from_role_separability(small_method_run):
    validity = small_method_run["validity"]
    assert {"MembershipValidity", "RoleSeparability"}.issubset(validity.columns)
    assert (
        validity["MembershipValidity"].str.startswith("VALID", na=False)
        & validity["RoleSeparability"].eq("UNRESOLVED")
    ).any()


def test_temporal_devil_validation_fields_exist(small_method_run):
    validity = small_method_run["validity"]
    required = {
        "SnapshotMembershipValidity",
        "PersistentPositiveEvidenceCount",
        "ValidityPersistenceRate",
        "NullMaxMedianCorrelation",
        "NullMaxPositiveRatio",
        "NullMaxPC1Absorption",
    }
    assert required.issubset(validity.columns)


def test_dynamic_roles_do_not_mislabel_low_coherence_as_laggard(small_method_run):
    roles = small_method_run["roles"]
    invalid = roles.loc[~roles["MembershipStatus"].str.startswith("VALID", na=False)]
    assert invalid["DynamicRole"].ne("TRUE_LAGGARD").all()


def test_multi_index_types_and_base_100(small_method_run):
    indices = small_method_run["indices"]
    assert not indices.empty
    assert "FULL_EW" in set(indices["IndexType"])
    assert "CORE_EW" in set(indices["IndexType"])
    bases = indices.sort_values("Date").groupby(["GroupId", "IndexType"]).first()["GroupIndex"]
    assert np.allclose(bases, 100.0)


def test_true_laggard_is_preserved_in_dedicated_index():
    roles = pd.read_csv(EVIDENCE_ROOT / "csv" / "role_snapshots.csv", encoding="utf-8-sig")
    indices = pd.read_csv(EVIDENCE_ROOT / "csv" / "group_indices_daily.csv", encoding="utf-8-sig")
    laggard_groups = set(roles.loc[roles["DynamicRole"].eq("TRUE_LAGGARD"), "GroupId"])
    emitted_groups = set(indices.loc[indices["IndexType"].eq("LAGGARD_EW"), "GroupId"])
    assert laggard_groups
    assert laggard_groups.issubset(emitted_groups)


def test_role_based_indices_do_not_predate_role_effective_date():
    roles = pd.read_csv(EVIDENCE_ROOT / "csv" / "role_snapshots.csv", encoding="utf-8-sig")
    indices = pd.read_csv(EVIDENCE_ROOT / "csv" / "group_indices_daily.csv", encoding="utf-8-sig")
    roles["EffectiveDate"] = pd.to_datetime(roles["EffectiveDate"])
    indices["Date"] = pd.to_datetime(indices["Date"])
    first_effective = roles.dropna(subset=["EffectiveDate"]).groupby("GroupId")["EffectiveDate"].min()
    role_indices = indices.loc[indices["PointInTimeRole"].astype(str).str.lower().eq("true")]
    first_index = role_indices.groupby("GroupId")["Date"].min()
    common = first_index.index.intersection(first_effective.index)
    assert (first_index.loc[common] >= first_effective.loc[common]).all()


# =============================================================================
# def 04 ADVERSARIAL / BACKTEST / STATIC AUDIT
# =============================================================================


def test_controlled_backtest_rejects_market_tide_and_detects_true_groups():
    backtest = pd.read_csv(
        EVIDENCE_ROOT / "csv" / "controlled_backtest_summary.csv", encoding="utf-8-sig"
    )
    market_tide = backtest.loc[backtest["Scenario"].eq("MARKET_TIDE")].iloc[0]
    assert int(market_tide["FalsePositive"]) == 0
    positive = backtest.loc[backtest["Scenario"].ne("MARKET_TIDE")]
    assert positive["TruePositive"].gt(0).all()
    assert positive["FalsePositive"].eq(0).all()


def test_market_tide_raw_correlation_is_neutralized_in_residual_space(engine, membership):
    subset = engine.def_backtest_membership_subset(membership)
    config = engine.EngineConfig(
        write_outputs=False,
        demo=True,
        demo_observations=120,
        max_classification_snapshots=3,
        max_lag_search_cap=4,
        permutation_shift_cap=7,
        null_group_repeats_cap=3,
    )
    raw, _ = engine.def_generate_demo_inputs(
        subset,
        120,
        config.random_seed + engine.def_stable_seed("MARKET_TIDE_TEST"),
        "MARKET_TIDE",
    )
    prices = engine.def_standardize_price_data(raw, subset, config)
    features = engine.def_compute_stock_features(prices)
    factors = engine.def_load_market_factors(prices, config)
    validity, _, _, _ = engine.def_run_point_in_time_classification(
        features, subset, factors, config
    )
    latest = validity.sort_values("SnapshotDate").drop_duplicates("GroupId", keep="last")
    assert latest["RawMedianWithinCorrelation"].median() > latest["ResidualMedianWithinCorrelation"].median()
    assert not latest["MembershipValidity"].str.startswith("VALID", na=False).any()


def test_no_prohibited_fixed_market_thresholds(engine):
    audit = engine.def_ast_fixed_threshold_audit(ENGINE_PATH)
    assert audit.empty


def test_operational_features_have_no_future_columns():
    features = pd.read_csv(
        EVIDENCE_ROOT / "csv" / "stock_price_volume_features.csv",
        nrows=5,
        encoding="utf-8-sig",
    )
    assert not any("future" in column.lower() for column in features.columns)


# =============================================================================
# def 05 UI / OUTPUT / REPRODUCIBILITY
# =============================================================================


def test_ui_contract_and_html_assets_are_complete():
    contract = json.loads((EVIDENCE_ROOT / "ui_contract.json").read_text("utf-8"))
    assert {"metadata", "groupIndex", "groupFlow", "classification", "validation", "dynamicCriteria"}.issubset(contract)
    assert contract["metadata"]["orderExecution"] == 0
    heatmap_index = pd.read_csv(EVIDENCE_ROOT / "heatmap_index.csv", encoding="utf-8-sig")
    assert len(heatmap_index) == 39
    for relative in heatmap_index["HeatmapPath"]:
        assert (EVIDENCE_ROOT / "plots" / "heatmaps" / relative).exists()
    assert (EVIDENCE_ROOT / "index.html").exists()


def test_validation_has_no_hard_failure():
    validation = pd.read_csv(
        EVIDENCE_ROOT / "csv" / "validation_ledger.csv", encoding="utf-8-sig"
    )
    assert not validation["Status"].eq("FAIL").any()
    assert validation.loc[validation["CheckId"].eq("V16_SYNTHETIC_BOUNDARY"), "Status"].eq("HOLD").all()


def test_sha256_manifest_integrity():
    manifest = json.loads((EVIDENCE_ROOT / "SHA256_MANIFEST.json").read_text("utf-8"))
    assert manifest
    for relative, expected in manifest.items():
        path = EVIDENCE_ROOT / relative
        assert path.exists(), relative
        digest = hashlib.sha256(path.read_bytes()).hexdigest().upper()
        assert digest == expected


def test_manifest_disables_network_orders_and_canonical_mutation():
    manifest = json.loads((EVIDENCE_ROOT / "manifest.json").read_text("utf-8"))
    assert manifest["order_execution"] == 0
    assert manifest["network_execution"] == 0
    assert manifest["canonical_mutation"] == 0
    assert manifest["evidence_boundary"] == "CONTROLLED_DGP_NOT_LIVE_CONFIRMED"


def test_demo_generation_is_reproducible(engine, membership):
    subset = engine.def_backtest_membership_subset(membership)
    left, left_truth = engine.def_generate_demo_inputs(subset, 80, 123456, "ROTATION")
    right, right_truth = engine.def_generate_demo_inputs(subset, 80, 123456, "ROTATION")
    pd.testing.assert_frame_equal(left, right)
    pd.testing.assert_frame_equal(left_truth, right_truth)
