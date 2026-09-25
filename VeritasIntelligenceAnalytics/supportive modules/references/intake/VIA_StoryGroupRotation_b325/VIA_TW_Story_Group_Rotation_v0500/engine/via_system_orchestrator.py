from __future__ import annotations

"""Strict orchestration for the v0.5 Taiwan story-group research pipeline.

This module performs no network fetch and fabricates no market result.  CLI
execution reads only supplied local point-in-time files, fails closed at every
contract boundary, and writes immutable dual-format runs.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd

try:
    from .via_active_etf_holdings_engine import def_build_active_etf_analysis
    from .via_append_only_io import def_write_run
    from .via_candidate49_adapter import def_prepare_candidate49, def_validation_cohort
    from .via_flow_transfer_matrix_engine import def_build_flow_transfer_outputs
    from .via_full_market_factor_engine import def_run_full_market_factor_pipeline
    from .via_fx_context_engine import (
        def_add_macro_context,
        def_foreign_flow_fx_residual,
        def_materialize_macro_asof,
        def_prepare_macro_factors,
    )
    from .via_group_flow_evidence_engine import (
        def_add_dynamic_flow_states,
        def_compute_group_flow_daily,
        def_prepare_stock_flow_panel,
    )
    from .via_group_validation_v0500 import GroupValidationConfig, def_run_group_validation
    from .via_hierarchical_group_index_engine import (
        HierarchicalIndexConfig,
        def_build_parallel_group_indices,
    )
    from .via_monthly_revenue_evidence_engine import (
        def_company_revenue_evidence,
        def_group_revenue_evidence,
        def_prepare_monthly_revenue,
    )
    from .via_pipeline_contract_bridge import (
        def_bridge_index_method,
        def_bridge_residual_lane,
        def_bridge_size_tiers_asof,
    )
    from .via_positioning_transition_engine import (
        def_build_positioning_transition_ledger,
        def_latest_positioning_transition_state,
    )
    from .via_pit_membership_engine import (
        def_materialize_membership_history,
        def_normalize_membership_events,
    )
    from .via_pit_rotation_backtest_engine import (
        BacktestConfig,
        def_compute_index_performance,
        def_run_multi_period_event_study,
        def_summarize_event_study,
    )
    from .via_size_bucket_history_engine import def_compute_quarterly_bucket_history
    from .via_stock_positioning_engine import (
        StockPositioningConfig,
        def_build_stock_positioning_outputs,
        def_map_evidence_to_story_groups,
    )
    from .via_time_utils import def_available_at_utc, def_local_calendar_date
    from .via_validation_consensus_engine import (
        ValidationConsensusConfig,
        def_build_membership_review_queue,
        def_reconcile_group_decisions,
        def_reconcile_member_roles,
    )
except ImportError:  # standalone import from the engine directory
    from via_active_etf_holdings_engine import def_build_active_etf_analysis
    from via_append_only_io import def_write_run
    from via_candidate49_adapter import def_prepare_candidate49, def_validation_cohort
    from via_flow_transfer_matrix_engine import def_build_flow_transfer_outputs
    from via_full_market_factor_engine import def_run_full_market_factor_pipeline
    from via_fx_context_engine import (
        def_add_macro_context,
        def_foreign_flow_fx_residual,
        def_materialize_macro_asof,
        def_prepare_macro_factors,
    )
    from via_group_flow_evidence_engine import (
        def_add_dynamic_flow_states,
        def_compute_group_flow_daily,
        def_prepare_stock_flow_panel,
    )
    from via_group_validation_v0500 import GroupValidationConfig, def_run_group_validation
    from via_hierarchical_group_index_engine import (
        HierarchicalIndexConfig,
        def_build_parallel_group_indices,
    )
    from via_monthly_revenue_evidence_engine import (
        def_company_revenue_evidence,
        def_group_revenue_evidence,
        def_prepare_monthly_revenue,
    )
    from via_pipeline_contract_bridge import (
        def_bridge_index_method,
        def_bridge_residual_lane,
        def_bridge_size_tiers_asof,
    )
    from via_positioning_transition_engine import (
        def_build_positioning_transition_ledger,
        def_latest_positioning_transition_state,
    )
    from via_pit_membership_engine import (
        def_materialize_membership_history,
        def_normalize_membership_events,
    )
    from via_pit_rotation_backtest_engine import (
        BacktestConfig,
        def_compute_index_performance,
        def_run_multi_period_event_study,
        def_summarize_event_study,
    )
    from via_size_bucket_history_engine import def_compute_quarterly_bucket_history
    from via_stock_positioning_engine import (
        StockPositioningConfig,
        def_build_stock_positioning_outputs,
        def_map_evidence_to_story_groups,
    )
    from via_time_utils import def_available_at_utc, def_local_calendar_date
    from via_validation_consensus_engine import (
        ValidationConsensusConfig,
        def_build_membership_review_queue,
        def_reconcile_group_decisions,
        def_reconcile_member_roles,
    )


ENGINE_ID = "VIA_STORY_GROUP_SYSTEM_ORCHESTRATOR_V0500"
ENGINE_VERSION = "0.5.0"
DEFAULT_WINDOWS = (60, 120, 240)
DEFAULT_FACTOR_LANES = ("LaggedCap", "LaggedETR")
DEFAULT_RESEARCH_START_DATE = "2024-01-01"
DEFAULT_WARMUP_START_DATE = "2023-01-01"
DEFAULT_EVALUATION_START_DATES = ("2024-01-01", "2025-01-01", "2026-01-01")
DEFAULT_FORWARD_HORIZONS = (1, 3, 5, 20)
REQUIRED_MARKET_AVAILABILITY_COLUMNS = (
    "MarketDataAvailableAt",
    "ForeignNetAmountAvailableAt",
    "InvestmentTrustNetAmountAvailableAt",
    "DealerNetAmountAvailableAt",
    "MarginBalanceValueAvailableAt",
    "ShortBalanceValueAvailableAt",
)


@dataclass(frozen=True)
class PipelineConfig:
    windows: tuple[int, ...] = DEFAULT_WINDOWS
    factor_lanes: tuple[str, ...] = DEFAULT_FACTOR_LANES
    validation_null_repeats_override: int | None = None
    output_root: str = "data/output"
    research_start_date: str = DEFAULT_RESEARCH_START_DATE
    warmup_start_date: str = DEFAULT_WARMUP_START_DATE
    evaluation_start_dates: tuple[str, ...] = DEFAULT_EVALUATION_START_DATES
    forward_horizons: tuple[int, ...] = DEFAULT_FORWARD_HORIZONS


def def_compact_repeated_text(frame: pd.DataFrame) -> pd.DataFrame:
    """Dictionary-encode repeated textual audit fields in place.

    Stock evidence deliberately carries rich provenance, but almost every
    textual value is repeated over many dates, tickers, lanes, or models.
    Object arrays otherwise retain a Python-object pointer for every cell and
    made the formal grid exceed practical memory.  Pandas categoricals retain
    the same values and serialize normally while storing one dictionary plus
    compact integer codes.  The blank category keeps downstream ``fillna('')``
    checks valid.
    """

    for column in frame.select_dtypes(include=["object", "string"]).columns:
        values = frame[column]
        non_null = values.dropna()
        inferred = pd.api.types.infer_dtype(non_null, skipna=True)
        if inferred not in {"string", "unicode", "bytes", "empty"}:
            continue
        unique_values = non_null.astype(object).unique().tolist()
        if "" not in unique_values:
            unique_values.append("")
        try:
            categories = sorted(unique_values)
        except TypeError:
            categories = unique_values
        frame[column] = pd.Categorical(values, categories=categories)
    return frame


def def_concat_compact_frames(parts: Iterable[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate dictionary-encoded chunks without expanding to objects."""

    chunks = [part for part in parts if part is not None]
    if not chunks:
        return pd.DataFrame()
    first_attrs = dict(chunks[0].attrs)
    categorical_columns = [
        column
        for column in chunks[0].columns
        if all(
            column in chunk.columns
            and isinstance(chunk[column].dtype, pd.CategoricalDtype)
            for chunk in chunks
        )
    ]
    for column in categorical_columns:
        categories: list[Any] = []
        for chunk in chunks:
            categories.extend(chunk[column].cat.categories.tolist())
        categories = list(dict.fromkeys(categories))
        try:
            categories = sorted(categories)
        except TypeError:
            pass
        for chunk in chunks:
            if chunk[column].cat.categories.tolist() != categories:
                chunk[column] = chunk[column].cat.set_categories(categories)
    result = pd.concat(chunks, ignore_index=True, sort=False, copy=False)
    result.attrs.update(first_attrs)
    return result


def def_validate_formal_pipeline_grid(config: PipelineConfig) -> None:
    """Fail closed on a model-grid or backtest-contract drift."""

    windows = tuple(config.windows)
    lanes = tuple(config.factor_lanes)
    if windows != DEFAULT_WINDOWS or any(type(value) is not int for value in windows):
        raise ValueError(
            "formal pipeline requires exactly the 60/120/240-day windows"
        )
    if lanes != DEFAULT_FACTOR_LANES or any(type(value) is not str for value in lanes):
        raise ValueError(
            "formal pipeline requires exactly LaggedCap and LaggedETR factor lanes"
        )

    research_start = _def_parse_canonical_config_date(
        config.research_start_date, "research_start_date"
    )
    warmup_start = _def_parse_canonical_config_date(
        config.warmup_start_date, "warmup_start_date"
    )
    if warmup_start >= research_start:
        raise ValueError("warmup_start_date must precede research_start_date")

    evaluation_starts = tuple(config.evaluation_start_dates)
    if not evaluation_starts:
        raise ValueError("evaluation_start_dates must not be empty")
    parsed_evaluation_starts = tuple(
        _def_parse_canonical_config_date(value, "evaluation_start_dates")
        for value in evaluation_starts
    )
    if len(set(parsed_evaluation_starts)) != len(parsed_evaluation_starts):
        raise ValueError("evaluation_start_dates must be unique")
    if parsed_evaluation_starts != tuple(sorted(parsed_evaluation_starts)):
        raise ValueError("evaluation_start_dates must be strictly increasing")
    if any(value < research_start for value in parsed_evaluation_starts):
        raise ValueError("evaluation_start_dates cannot precede research_start_date")

    horizons = tuple(config.forward_horizons)
    if not horizons or any(type(value) is not int or value <= 0 for value in horizons):
        raise ValueError("forward_horizons must be positive integer sessions")
    if horizons != tuple(sorted(set(horizons))):
        raise ValueError("forward_horizons must be unique and strictly increasing")
    null_repeats = config.validation_null_repeats_override
    if null_repeats is not None and (
        type(null_repeats) is not int or null_repeats <= 0
    ):
        raise ValueError("validation_null_repeats_override must be a positive integer")
    if not isinstance(config.output_root, str) or not config.output_root.strip():
        raise ValueError("output root must be a non-empty string")


def _def_parse_canonical_config_date(value: Any, field_name: str) -> pd.Timestamp:
    """Parse only canonical YYYY-MM-DD dates used by reproducible runs."""

    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a YYYY-MM-DD string")
    text = value.strip()
    try:
        parsed = pd.Timestamp(text)
    except (TypeError, ValueError) as error:
        raise ValueError(f"{field_name} contains an invalid date: {value!r}") from error
    if len(text) != 10 or parsed.strftime("%Y-%m-%d") != text or parsed.tz is not None:
        raise ValueError(f"{field_name} must use canonical YYYY-MM-DD format")
    return parsed.normalize()


def _def_config_sequence(
    raw_config: Mapping[str, Any],
    field_name: str,
    default: tuple[Any, ...],
) -> tuple[Any, ...]:
    value = raw_config.get(field_name, default)
    if isinstance(value, (str, bytes)) or not isinstance(value, (list, tuple)):
        raise ValueError(f"{field_name} must be a JSON array")
    return tuple(value)


def def_pipeline_config_from_mapping(raw_config: Mapping[str, Any]) -> PipelineConfig:
    """Build and validate the runtime contract from a JSON-like mapping."""

    output = raw_config.get("output", {})
    if not isinstance(output, Mapping):
        raise ValueError("output must be a JSON object")
    config = PipelineConfig(
        windows=_def_config_sequence(raw_config, "rolling_windows", DEFAULT_WINDOWS),
        factor_lanes=_def_config_sequence(
            raw_config, "residual_factor_lanes", DEFAULT_FACTOR_LANES
        ),
        research_start_date=raw_config.get(
            "research_start_date", DEFAULT_RESEARCH_START_DATE
        ),
        warmup_start_date=raw_config.get(
            "warmup_start_date", DEFAULT_WARMUP_START_DATE
        ),
        evaluation_start_dates=_def_config_sequence(
            raw_config,
            "evaluation_start_dates",
            DEFAULT_EVALUATION_START_DATES,
        ),
        forward_horizons=_def_config_sequence(
            raw_config, "forward_horizons", DEFAULT_FORWARD_HORIZONS
        ),
        validation_null_repeats_override=raw_config.get(
            "validation_null_repeats_override"
        ),
        output_root=output.get("root", "data/output"),
    )
    def_validate_formal_pipeline_grid(config)

    formal_grid = raw_config.get("formal_model_grid")
    if formal_grid is not None:
        if not isinstance(formal_grid, Mapping):
            raise ValueError("formal_model_grid must be a JSON object")
        declared_windows = _def_config_sequence(
            formal_grid, "windows", config.windows
        )
        declared_lanes = _def_config_sequence(
            formal_grid, "factor_lanes", config.factor_lanes
        )
        if declared_windows != config.windows or declared_lanes != config.factor_lanes:
            raise ValueError(
                "formal_model_grid drifts from rolling_windows/residual_factor_lanes"
            )
        expected_count = formal_grid.get(
            "expected_model_count", len(config.windows) * len(config.factor_lanes)
        )
        if type(expected_count) is not int or expected_count != (
            len(config.windows) * len(config.factor_lanes)
        ):
            raise ValueError("formal_model_grid expected_model_count is invalid")

    for section_name in ("size_classification", "stock_positioning"):
        section = raw_config.get(section_name)
        if section is None:
            continue
        if not isinstance(section, Mapping):
            raise ValueError(f"{section_name} must be a JSON object")
        if "windows" in section and _def_config_sequence(
            section, "windows", config.windows
        ) != config.windows:
            raise ValueError(f"{section_name}.windows drifts from rolling_windows")
    return config


def def_build_backtest_config(
    pipeline_config: PipelineConfig,
    snapshot: Any,
) -> BacktestConfig:
    """Pass the validated JSON-backed research grid into the backtest engine."""

    def_validate_formal_pipeline_grid(pipeline_config)
    snapshot_date = def_local_calendar_date(snapshot)
    if pd.isna(snapshot_date):
        raise ValueError("backtest snapshot is invalid")
    return BacktestConfig(
        start_date=pipeline_config.research_start_date,
        warmup_start_date=pipeline_config.warmup_start_date,
        end_date=snapshot_date.strftime("%Y-%m-%d"),
        windows=pipeline_config.windows,
        horizons=pipeline_config.forward_horizons,
        evaluation_start_dates=pipeline_config.evaluation_start_dates,
    )


def def_read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    raise ValueError(f"unsupported input format: {path}")


def def_load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def def_resolve_path(base_dir: Path, value: str) -> Path:
    candidate = Path(value)
    return candidate if candidate.is_absolute() else (base_dir / candidate).resolve()


def def_input_preflight(base_dir: Path, raw_config: Mapping[str, Any]) -> pd.DataFrame:
    local = raw_config.get("local_inputs", {})
    required_names = (
        "full_market_daily",
        "universe_history",
        "trading_calendar",
        "membership_events",
        "macro_vintages",
        "active_etf_holdings",
    )
    optional_reference_names = ("monthly_revenue",)
    rows: list[dict[str, Any]] = []
    for name in (*required_names, *optional_reference_names):
        configured = str(local.get(name, "")).strip()
        path = def_resolve_path(base_dir, configured) if configured else None
        required_for_core = name in required_names
        exists = bool(path and path.is_file())
        rows.append(
            {
                "InputName": name,
                "InputRole": (
                    "CORE_REQUIRED" if required_for_core else "OPTIONAL_POST_SIGNAL_REFERENCE"
                ),
                "ConfiguredPath": configured,
                "ResolvedPath": str(path) if path is not None else "",
                "Exists": exists,
                "PreflightStatus": (
                    "PASS"
                    if exists
                    else "BLOCKED_MISSING_INPUT"
                    if required_for_core
                    else "OPTIONAL_REFERENCE_NOT_AVAILABLE"
                ),
                "BlocksCorePipeline": bool(required_for_core and not exists),
            }
        )
    candidate_path = def_resolve_path(base_dir, str(raw_config["candidate_story_membership"]))
    rows.append(
        {
            "InputName": "candidate_story_membership",
            "InputRole": "CORE_REQUIRED_VALIDATION_COHORT",
            "ConfiguredPath": str(raw_config["candidate_story_membership"]),
            "ResolvedPath": str(candidate_path),
            "Exists": candidate_path.is_file(),
            "PreflightStatus": "PASS" if candidate_path.is_file() else "BLOCKED_MISSING_INPUT",
            "BlocksCorePipeline": not candidate_path.is_file(),
        }
    )
    return pd.DataFrame(rows)


def def_candidate49_preflight(
    candidate_path: Path,
    proposed_at: Any,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    candidate, audit = def_prepare_candidate49(def_read_table(candidate_path), proposed_at)
    audit_frame = pd.DataFrame([{**audit, "EngineId": ENGINE_ID, "EngineVersion": ENGINE_VERSION}])
    return candidate, audit_frame


def def_build_optional_revenue_reference(
    revenue_input: pd.DataFrame | Path | str | None,
    evidence_cutoff_at: Any,
    approved_history: pd.DataFrame,
    as_of_date: Any,
    *,
    opportunity_tickers: Iterable[Any] | None = None,
) -> dict[str, pd.DataFrame]:
    """Build post-opportunity revenue context without blocking the core run."""

    company_revenue = pd.DataFrame()
    group_revenue = pd.DataFrame()
    error_type = ""
    error_message = ""
    opportunity_set = (
        set()
        if opportunity_tickers is None
        else {
            str(value).strip().upper().removesuffix(".TW").removesuffix(".TWO")
            for value in opportunity_tickers
            if str(value).strip()
        }
    )
    reference_input_mode = (
        "DEFERRED_FILE"
        if isinstance(revenue_input, (Path, str))
        else "IN_MEMORY_FRAME"
        if isinstance(revenue_input, pd.DataFrame)
        else "NOT_CONFIGURED"
    )
    if not opportunity_set:
        status = "OPTIONAL_REFERENCE_WAITING_FOR_CORE_OPPORTUNITY"
    elif revenue_input is None or (
        isinstance(revenue_input, pd.DataFrame) and revenue_input.empty
    ):
        status = "OPTIONAL_REFERENCE_NOT_AVAILABLE_CORE_UNAFFECTED"
    else:
        try:
            raw_revenue = (
                def_read_table(Path(revenue_input))
                if isinstance(revenue_input, (Path, str))
                else revenue_input.copy()
            )
            if not isinstance(raw_revenue, pd.DataFrame):
                raise TypeError("monthly revenue reference must resolve to a DataFrame")
            if "Ticker" not in raw_revenue.columns:
                raise ValueError("monthly revenue missing required column: Ticker")
            normalized_tickers = (
                raw_revenue["Ticker"]
                .astype(str)
                .str.strip()
                .str.upper()
                .str.replace(r"\.TW(?:O)?$", "", regex=True)
            )
            raw_revenue = raw_revenue.loc[
                normalized_tickers.isin(opportunity_set)
            ].copy()
            if raw_revenue.empty:
                status = "OPTIONAL_REFERENCE_NO_MATCHING_OPPORTUNITY_DATA"
            else:
                revenue_prepared = def_prepare_monthly_revenue(raw_revenue)
                company_revenue = def_company_revenue_evidence(
                    revenue_prepared, evidence_cutoff_at
                )
                if company_revenue.empty:
                    status = "OPTIONAL_REFERENCE_NO_OBSERVABLE_OPPORTUNITY_DATA"
                else:
                    reference_membership = approved_history.copy()
                    if "Ticker" not in reference_membership.columns:
                        raise ValueError("membership missing required column: Ticker")
                    membership_tickers = (
                        reference_membership["Ticker"]
                        .astype(str)
                        .str.strip()
                        .str.upper()
                        .str.replace(r"\.TW(?:O)?$", "", regex=True)
                    )
                    reference_membership = reference_membership.loc[
                        membership_tickers.isin(opportunity_set)
                    ].copy()
                    group_revenue = def_group_revenue_evidence(
                        company_revenue, reference_membership, as_of_date
                    )
                    status = "PASS_OPTIONAL_POST_SIGNAL_REFERENCE"
        except Exception as error:  # reference data must never suppress core evidence
            status = "OPTIONAL_REFERENCE_INVALID_CORE_UNAFFECTED"
            company_revenue = pd.DataFrame()
            group_revenue = pd.DataFrame()
            error_type = type(error).__name__
            error_message = str(error)[:500]
    audit = pd.DataFrame(
        [
            {
                "AsOfDate": def_local_calendar_date(as_of_date),
                "EvidenceCutoffAt": def_available_at_utc(evidence_cutoff_at),
                "RevenueReferenceStatus": status,
                "ReferenceErrorType": error_type,
                "ReferenceErrorMessage": error_message,
                "ReferenceInputMode": reference_input_mode,
                "OpportunityTickerCount": len(opportunity_set),
                "ReferenceSelectionPolicy": (
                    "STRICT_CORE_POSITIONING_SEQUENCE_STAGE_3_OR_4_ONLY"
                ),
                "UsagePolicy": (
                    "POST_SIGNAL_FUNDAMENTAL_CONTEXT_ONLY_PROHIBITED_FROM_"
                    "CLASSIFICATION_ROLE_INDEX_WEIGHT_SIGNAL_AND_SELECTION"
                ),
                "CorePipelineBlocked": False,
            }
        ]
    )
    return {
        "reference_company_revenue_latest": company_revenue,
        "reference_group_revenue_latest": group_revenue,
        "reference_revenue_audit": audit,
    }


def def_merge_validation_membership(
    candidate: pd.DataFrame,
    approved_history: pd.DataFrame,
) -> pd.DataFrame:
    """Combine statistical candidates with approved members without promotion."""

    cohort = def_validation_cohort(candidate).copy()
    cohort["_Key"] = cohort["GroupId"].astype(str) + "|" + cohort["TickerBase"].astype(str)
    approved = approved_history.copy()
    if approved.empty:
        return cohort.drop(columns="_Key")
    approved["TickerBase"] = approved["Ticker"].astype(str).str.upper().str.replace(
        r"\.(TW|TWO)$", "", regex=True
    )
    approved["_Key"] = approved["GroupId"].astype(str) + "|" + approved["TickerBase"]
    lookup = approved.sort_values("ValidFrom").drop_duplicates("_Key", keep="last").set_index("_Key")
    matched = cohort["_Key"].isin(lookup.index)
    for index in cohort.index[matched]:
        source = lookup.loc[cohort.at[index, "_Key"]]
        cohort.at[index, "Decision"] = "APPROVED"
        cohort.at[index, "IndexEligible"] = True
        cohort.at[index, "ValidFrom"] = source["ValidFrom"]
        cohort.at[index, "ValidTo"] = source["ValidTo"]
        cohort.at[index, "KnownAt"] = source["KnownAt"]
    missing_approved = approved.loc[~approved["_Key"].isin(cohort["_Key"])].copy()
    if not missing_approved.empty:
        missing_approved["ValidationEligible"] = True
        missing_approved["IndexEligible"] = True
        missing_approved["ProposedAt"] = missing_approved["KnownAt"]
        cohort = pd.concat([cohort, missing_approved], ignore_index=True, sort=False)
    return cohort.drop(columns="_Key", errors="ignore")


def def_run_validation_grid(
    rolling_residuals: pd.DataFrame,
    validation_membership: pd.DataFrame,
    size_history: pd.DataFrame,
    as_of_date: Any,
    decision_at: Any,
    trading_calendar: Iterable[Any],
    pipeline_config: PipelineConfig = PipelineConfig(),
) -> dict[str, pd.DataFrame]:
    normalized_ticker = validation_membership["Ticker"].astype(str).str.upper().str.replace(
        r"\.(TW|TWO)$", "", regex=True
    )
    anchor_members = validation_membership.loc[normalized_ticker.eq("2330")].copy()
    model_membership = validation_membership.loc[~normalized_ticker.eq("2330")].copy()
    if model_membership.empty:
        raise ValueError("validation cohort has no non-2330 members after anchor isolation")
    if not anchor_members.empty:
        anchor_members["AnchorValidationStatus"] = (
            "ISOLATED_FROM_EX_2330_MARKET_ROLE_MODEL_NOT_A_FIFTH_ROLE"
        )
        anchor_members["RoleConsensus"] = pd.NA
        anchor_members["IndexComparisonEligible"] = False
    required_tickers = model_membership["Ticker"].dropna().unique()
    size_features_by_window: dict[int, pd.DataFrame] = {}
    for raw_window in pipeline_config.windows:
        window = int(raw_window)
        features = def_bridge_size_tiers_asof(
            size_history,
            as_of_date,
            window_days=window,
            required_tickers=required_tickers,
        )
        feature_windows = (
            set(
                pd.to_numeric(features["WindowDays"], errors="coerce")
                .dropna()
                .astype(int)
            )
            if "WindowDays" in features.columns
            else set()
        )
        ticker_base = (
            features.get("Ticker", pd.Series(dtype="object"))
            .astype(str)
            .str.upper()
            .str.replace(r"\.(TW|TWO)$", "", regex=True)
        )
        provenance_ready = (
            features.attrs.get("PointInTime") is True
            and features.attrs.get("TSMCExcluded") is True
            and feature_windows == {window}
            and not ticker_base.eq("2330").any()
        )
        if not provenance_ready:
            raise ValueError(
                "validation size descriptors cannot prove aligned point-in-time "
                f"full-market ex-2330 provenance for window_days={window}"
            )
        size_features_by_window[window] = features
    group_tables: list[pd.DataFrame] = []
    member_tables: list[pd.DataFrame] = []
    null_tables: list[pd.DataFrame] = []
    metadata_rows: list[dict[str, Any]] = []
    for factor_lane in pipeline_config.factor_lanes:
        for window in pipeline_config.windows:
            residual = def_bridge_residual_lane(
                rolling_residuals,
                factor_lane=factor_lane,
                window_days=window,
                as_of_date=as_of_date,
            )
            result = def_run_group_validation(
                residual,
                model_membership,
                as_of_date=as_of_date,
                decision_at=decision_at,
                trading_calendar=trading_calendar,
                match_features=size_features_by_window[int(window)],
                config=GroupValidationConfig(
                    windows=(window,),
                    null_repeats_override=pipeline_config.validation_null_repeats_override,
                ),
            )
            for table in (result.group_validation, result.member_roles, result.null_ledger):
                table["ResidualFactorLane"] = factor_lane
                table["ResidualBetaWindow"] = window
            group_tables.append(result.group_validation)
            member_tables.append(result.member_roles)
            null_tables.append(result.null_ledger)
            metadata_rows.append(
                {
                    **result.metadata,
                    "ResidualFactorLane": factor_lane,
                    "ResidualBetaWindow": window,
                }
            )
    group_validation = pd.concat(group_tables, ignore_index=True, sort=False)
    member_roles = pd.concat(member_tables, ignore_index=True, sort=False)
    null_ledger = pd.concat(null_tables, ignore_index=True, sort=False)
    group_consensus = def_reconcile_group_decisions(group_validation)
    member_consensus = def_reconcile_member_roles(member_roles, group_consensus)
    validation_size_features = pd.concat(
        [size_features_by_window[int(window)] for window in pipeline_config.windows],
        ignore_index=True,
        sort=False,
    )
    validation_size_features.attrs.update(
        {
            "PointInTime": True,
            "TSMCExcluded": True,
            "ComparisonUniverse": "TWSE_TPEX_COMMON_EQUITY_EX_2330",
            "Windows": tuple(int(window) for window in pipeline_config.windows),
            "WindowAlignmentPolicy": "MATCH_VALIDATION_WINDOW_EXACTLY",
        }
    )
    return {
        "group_validation": group_validation,
        "member_roles": member_roles,
        "validation_null_ledger": null_ledger,
        "validation_metadata": pd.DataFrame(metadata_rows),
        "group_validation_consensus": group_consensus,
        "member_role_consensus": member_consensus,
        "validation_size_features": validation_size_features,
        "tsmc_anchor_membership": anchor_members.reset_index(drop=True),
    }


def def_attach_active_etf_lane(
    market_daily: pd.DataFrame,
    etf_events: pd.DataFrame,
) -> pd.DataFrame:
    result = market_daily.copy()
    if etf_events.empty:
        result["ETFActiveValue"] = np.nan
        result["ETFActiveValueAvailableAt"] = pd.NaT
        return result
    if result.get("ETFActiveValue", pd.Series(dtype=float)).notna().any():
        raise ValueError("ETF active value is supplied twice; T86/ETF overlap cannot be reconciled")
    # A formal market schema may reserve the ETF columns as all-null placeholders.
    # Drop those placeholders before the evidence join so pandas cannot create
    # ambiguous ``_x``/``_y`` columns.
    result = result.drop(
        columns=["ETFActiveValue", "ETFActiveValueAvailableAt"], errors="ignore"
    )
    events = etf_events.copy()
    events["Date"] = events["EvidenceDate"].map(def_local_calendar_date)
    events["TickerBase"] = events["TickerBase"].astype(str)
    aggregated = (
        events.groupby(["Date", "TickerBase"], as_index=False)
        .agg(
            ETFActiveValue=("EstimatedActiveValue", lambda values: values.sum(min_count=1)),
            ETFActiveValueAvailableAt=("AvailableAt", "max"),
        )
    )
    result["Date"] = result["Date"].map(def_local_calendar_date)
    result["TickerBase"] = result["Ticker"].astype(str).str.upper().str.replace(
        r"\.(TW|TWO)$", "", regex=True
    )
    result = result.merge(aggregated, on=["Date", "TickerBase"], how="left", validate="many_to_one")
    return result.drop(columns="TickerBase")


def def_attach_pit_size_bucket(
    prepared_stock: pd.DataFrame,
    size_history: pd.DataFrame,
    *,
    window_days: int,
) -> pd.DataFrame:
    """Attach the last effective global ex-2330 cap tier to each stock-day.

    The lookup is backward-asof on ``EffectiveDate``.  A missing early tier is
    retained as missing so the positioning engine can HOLD instead of falling
    back to a fixed or whole-market peer definition.
    """

    required = {
        "Ticker",
        "EffectiveDate",
        "WindowDays",
        "MarketCapTier",
        "ClassificationStatus",
        "SnapshotDate",
        "ThresholdPolicy",
    }
    missing = sorted(required.difference(size_history.columns))
    if missing:
        raise ValueError(f"size_history missing stock-positioning fields: {missing}")
    if "SizeBucket" in prepared_stock.columns and prepared_stock["SizeBucket"].notna().any():
        raise ValueError("prepared_stock already contains a non-empty SizeBucket")

    left = prepared_stock.drop(columns="SizeBucket", errors="ignore").copy()
    left["Date"] = left["Date"].map(def_local_calendar_date)
    left["TickerBase"] = left["Ticker"].astype(str).str.upper().str.replace(
        r"\.(TW|TWO)$", "", regex=True
    )
    left["_PositioningRowOrder"] = np.arange(len(left))

    right = size_history.loc[
        pd.to_numeric(size_history["WindowDays"], errors="coerce").eq(int(window_days))
    ].copy()
    right["TickerBase"] = right["Ticker"].astype(str).str.upper().str.replace(
        r"\.(TW|TWO)$", "", regex=True
    )
    right["SizeBucketEffectiveDate"] = right["EffectiveDate"].map(
        def_local_calendar_date
    )
    right = right.loc[
        right["ClassificationStatus"].eq("PASS")
        & right["TickerBase"].ne("2330")
        & right["MarketCapTier"].isin(["SMALL", "MID", "LARGE"])
    ].copy()
    duplicate = right.duplicated(["TickerBase", "SizeBucketEffectiveDate"], keep=False)
    if duplicate.any():
        raise ValueError(
            "size_history has duplicate Ticker+EffectiveDate rows for positioning"
        )
    right = right[
        [
            "TickerBase",
            "SizeBucketEffectiveDate",
            "MarketCapTier",
            "SnapshotDate",
            "ThresholdPolicy",
        ]
    ].rename(
        columns={
            "MarketCapTier": "SizeBucket",
            "SnapshotDate": "SizeBucketSnapshotDate",
            "ThresholdPolicy": "SizeBucketThresholdPolicy",
        }
    )

    if right.empty:
        left["SizeBucket"] = pd.NA
        left["SizeBucketEffectiveDate"] = pd.NaT
        left["SizeBucketSnapshotDate"] = pd.NaT
        left["SizeBucketThresholdPolicy"] = pd.NA
    else:
        left = pd.merge_asof(
            left.sort_values(["Date", "TickerBase"], kind="stable"),
            right.sort_values(
                ["SizeBucketEffectiveDate", "TickerBase"], kind="stable"
            ),
            left_on="Date",
            right_on="SizeBucketEffectiveDate",
            by="TickerBase",
            direction="backward",
            allow_exact_matches=True,
        )
    left["SizeBucketWindowDays"] = int(window_days)
    left["SizeBucketLookupStatus"] = np.where(
        left["TickerBase"].eq("2330"),
        "ANCHOR_EXCLUDED",
        np.where(
            left["SizeBucket"].notna(),
            "PASS_PIT_DYNAMIC_GLOBAL_SIZE_BUCKET",
            "HOLD_NO_EFFECTIVE_SIZE_BUCKET",
        ),
    )
    result = (
        left.sort_values("_PositioningRowOrder", kind="stable")
        .drop(columns=["TickerBase", "_PositioningRowOrder"])
        .reset_index(drop=True)
    )
    result.attrs.update(prepared_stock.attrs)
    return result


def def_reconcile_stock_positioning_models(
    stock_evidence: pd.DataFrame,
    *,
    factor_lanes: Iterable[str] = DEFAULT_FACTOR_LANES,
) -> pd.DataFrame:
    """Require exact cap/ETR-factor agreement without averaging or voting."""

    required = {
        "Date",
        "Ticker",
        "EvidenceWindowDays",
        "DirectionalLane",
        "ResidualFactorLane",
        "ResidualBetaWindow",
        "FactorLane",
        "WindowDays",
        "ResidualSourceColumn",
        "EvidenceCategory",
        "PositioningSequencePhase",
        "PriceEvidenceBasis",
        "SignalTimingStatus",
        "SignalAvailableAt",
        "EffectiveDate",
        "AttentionETR",
        "DirectionalAmount",
    }
    missing = sorted(required.difference(stock_evidence.columns))
    if missing:
        raise ValueError(f"stock positioning evidence missing consensus fields: {missing}")
    expected = tuple(str(value) for value in factor_lanes)
    if len(expected) != len(DEFAULT_FACTOR_LANES) or set(expected) != set(
        DEFAULT_FACTOR_LANES
    ):
        raise ValueError(
            "stock consensus requires exactly LaggedCap and LaggedETR factor lanes"
        )
    keys = ["Date", "Ticker", "EvidenceWindowDays", "DirectionalLane"]
    if stock_evidence.empty:
        return pd.DataFrame(
            columns=[
                *keys,
                "FactorModelsExpected",
                "FactorModelsObserved",
                "FactorModelCount",
                "MarketUniverse",
                "TSMCExcluded",
                "ConsensusStatus",
                "ConsensusEvidenceCategory",
                "ConsensusPositioningSequencePhase",
                "EvidenceCategory",
                "PositioningSequencePhase",
                "SignalAvailableAt",
                "EffectiveDate",
                "ConsensusActionable",
                "AggregationPolicy",
                "TradeInstruction",
                "AttentionETR",
                "DirectionalAmount",
                *[f"{lane}PriceEvidenceValue" for lane in expected],
            ]
        )

    # Keep only consensus inputs.  Full model evidence can contain more than a
    # hundred audit columns, and copying that width per Python group was the
    # largest time/RSS cost in a 241-stock grid.
    source_columns = list(required)
    for optional in ("TSMCExcluded", "FullMarketGateStatus", "PriceEvidenceValue"):
        if optional in stock_evidence.columns and optional not in source_columns:
            source_columns.append(optional)
    work = stock_evidence[source_columns].copy()
    work["_ResidualLane"] = work["ResidualFactorLane"].astype("string").fillna("")
    work["_FactorLane"] = work["FactorLane"].astype("string").fillna("")
    work["_SourceColumn"] = work["ResidualSourceColumn"].astype("string").fillna("")
    work["_Window"] = pd.to_numeric(work["WindowDays"], errors="coerce")
    work["_BetaWindow"] = pd.to_numeric(
        work["ResidualBetaWindow"], errors="coerce"
    )
    integral_beta = work["_BetaWindow"].notna() & work["_BetaWindow"].mod(1).eq(0)
    beta_text = pd.Series("", index=work.index, dtype="string")
    beta_text.loc[integral_beta] = (
        work.loc[integral_beta, "_BetaWindow"].astype("int64").astype("string")
    )
    expected_source = (
        "Residual_" + work["_ResidualLane"] + "_" + beta_text + "D"
    )
    work["_ExpectedLane"] = work["_ResidualLane"].isin(expected)
    work["_ModelIdentityAligned"] = (
        work["_ResidualLane"].eq(work["_FactorLane"])
        & work["_Window"].eq(work["_BetaWindow"])
        & integral_beta
        & work["_SourceColumn"].eq(expected_source)
    )
    work["_WindowAligned"] = work["_BetaWindow"].eq(
        pd.to_numeric(work["EvidenceWindowDays"], errors="coerce")
    )
    work["_ResidualReady"] = work["PriceEvidenceBasis"].eq(
        "EX_TSMC_RESIDUAL_RETURN"
    )
    work["_Category"] = (
        work["EvidenceCategory"].astype("string").fillna("").str.strip()
    )
    work["_Phase"] = (
        work["PositioningSequencePhase"].astype("string").fillna("").str.strip()
    )
    work["_CategoryPresent"] = work["_Category"].ne("")
    work["_PhasePresent"] = work["_Phase"].ne("")
    work["_Signal"] = pd.to_datetime(
        work["SignalAvailableAt"], errors="coerce", utc=True
    )
    work["_Effective"] = pd.to_datetime(work["EffectiveDate"], errors="coerce")
    work["_TimingRowReady"] = (
        work["_Signal"].notna()
        & work["_Effective"].notna()
        & work["SignalTimingStatus"].eq(
            "PASS_NEXT_SESSION_AFTER_LATEST_REQUIRED_EVIDENCE"
        )
    )
    work["_Attention"] = pd.to_numeric(work["AttentionETR"], errors="coerce")
    work["_Directional"] = pd.to_numeric(
        work["DirectionalAmount"], errors="coerce"
    )
    ticker_base = (
        work["Ticker"]
        .astype("string")
        .fillna("")
        .str.strip()
        .str.upper()
        .str.replace(r"(?:\.TWO|\.TW)$", "", regex=True)
    )
    if "TSMCExcluded" in work.columns:
        exclusion_text = (
            work["TSMCExcluded"].astype("string").fillna("").str.strip().str.upper()
        )
        tsmc_excluded = exclusion_text.isin(("TRUE", "1", "YES", "Y"))
    else:
        tsmc_excluded = pd.Series(False, index=work.index)
    if "FullMarketGateStatus" in work.columns:
        full_market_gate = work["FullMarketGateStatus"].eq(
            "PASS_FULL_TWSE_TPEX_ORDINARY_STOCKS"
        )
    else:
        full_market_gate = pd.Series(False, index=work.index)
    work["_ProvenanceReady"] = (
        ticker_base.ne("")
        & ticker_base.ne("2330")
        & tsmc_excluded
        & full_market_gate
    )
    work["_One"] = np.int8(1)
    price_values = pd.to_numeric(
        work.get("PriceEvidenceValue", pd.Series(np.nan, index=work.index)),
        errors="coerce",
    )
    for lane in expected:
        work[f"_Price_{lane}"] = price_values.where(work["_ResidualLane"].eq(lane))

    work.sort_values([*keys, "_ResidualLane"], kind="stable", inplace=True)
    grouped = work.groupby(keys, sort=True, dropna=False, observed=True)
    aggregation: dict[str, tuple[str, str]] = {
        "FactorModelCount": ("_One", "sum"),
        "UniqueModelCount": ("_ResidualLane", "nunique"),
        "ExpectedModelRows": ("_ExpectedLane", "sum"),
        "ModelIdentityAligned": ("_ModelIdentityAligned", "all"),
        "WindowAligned": ("_WindowAligned", "all"),
        "ResidualReady": ("_ResidualReady", "all"),
        "CategoryPresent": ("_CategoryPresent", "all"),
        "CategoryCount": ("_Category", "nunique"),
        "FirstCategory": ("_Category", "first"),
        "PhasePresent": ("_PhasePresent", "all"),
        "PhaseCount": ("_Phase", "nunique"),
        "FirstPhase": ("_Phase", "first"),
        "TimingRowsReady": ("_TimingRowReady", "all"),
        "SignalMin": ("_Signal", "min"),
        "SignalMax": ("_Signal", "max"),
        "EffectiveMin": ("_Effective", "min"),
        "EffectiveMax": ("_Effective", "max"),
        "ProvenanceReady": ("_ProvenanceReady", "all"),
        "AttentionPresent": ("_Attention", "count"),
        "AttentionMin": ("_Attention", "min"),
        "AttentionMax": ("_Attention", "max"),
        "AttentionFirst": ("_Attention", "first"),
        "DirectionalPresent": ("_Directional", "count"),
        "DirectionalMin": ("_Directional", "min"),
        "DirectionalMax": ("_Directional", "max"),
        "DirectionalFirst": ("_Directional", "first"),
    }
    for lane in expected:
        aggregation[f"{lane}PriceEvidenceValue"] = (f"_Price_{lane}", "first")
    summary = grouped.agg(**aggregation).reset_index()

    complete_models = (
        summary["FactorModelCount"].eq(len(expected))
        & summary["UniqueModelCount"].eq(len(expected))
        & summary["ExpectedModelRows"].eq(len(expected))
    )
    model_identity_aligned = summary["ModelIdentityAligned"]
    aligned_window = summary["WindowAligned"]
    residual_ready = summary["ResidualReady"]
    category_exact = summary["CategoryPresent"] & summary["CategoryCount"].eq(1)
    phase_exact = summary["PhasePresent"] & summary["PhaseCount"].eq(1)
    invariants_exact = (
        summary["AttentionPresent"].eq(summary["FactorModelCount"])
        & summary["AttentionMin"].eq(summary["AttentionMax"])
        & summary["DirectionalPresent"].eq(summary["FactorModelCount"])
        & summary["DirectionalMin"].eq(summary["DirectionalMax"])
    )
    timing_exact = (
        summary["TimingRowsReady"]
        & summary["SignalMin"].eq(summary["SignalMax"])
        & summary["EffectiveMin"].eq(summary["EffectiveMax"])
    )
    summary["ConsensusStatus"] = np.select(
        [
            ~complete_models,
            ~summary["ProvenanceReady"],
            ~model_identity_aligned,
            ~aligned_window,
            ~residual_ready,
            ~category_exact | ~phase_exact,
            ~invariants_exact,
            ~timing_exact,
        ],
        [
            "HOLD_MISSING_FACTOR_MODEL",
            "HOLD_EX_TSMC_PROVENANCE_NOT_READY",
            "HOLD_RESIDUAL_MODEL_IDENTITY_MISMATCH",
            "HOLD_RESIDUAL_AND_EVIDENCE_WINDOW_MISMATCH",
            "HOLD_EX_TSMC_RESIDUAL_NOT_READY",
            "HOLD_FACTOR_MODEL_DISAGREEMENT",
            "HOLD_FACTOR_MODEL_INVARIANT_MISSING_OR_DISAGREEMENT",
            "HOLD_SIGNAL_TIMING_DISAGREEMENT_OR_MISSING",
        ],
        default="PASS_EXACT_FACTOR_MODEL_AGREEMENT",
    )
    passed = summary["ConsensusStatus"].eq("PASS_EXACT_FACTOR_MODEL_AGREEMENT")
    summary["ConsensusEvidenceCategory"] = summary["FirstCategory"].where(
        passed, summary["ConsensusStatus"]
    )
    summary["ConsensusPositioningSequencePhase"] = summary["FirstPhase"].where(
        passed, "HOLD_FACTOR_MODEL_CONSENSUS"
    )

    expected_observed = "|".join(sorted(expected))
    summary["FactorModelsObserved"] = expected_observed
    if (~complete_models).any():
        incomplete_keys = summary.loc[~complete_models, keys]
        incomplete_rows = work.merge(
            incomplete_keys, on=keys, how="inner", validate="many_to_one"
        )
        incomplete_observed = (
            incomplete_rows[[*keys, "_ResidualLane"]]
            .drop_duplicates()
            .sort_values([*keys, "_ResidualLane"], kind="stable")
            .groupby(keys, sort=False, dropna=False, observed=True)["_ResidualLane"]
            .agg("|".join)
            .rename("_Observed")
            .reset_index()
        )
        summary = summary.merge(
            incomplete_observed, on=keys, how="left", validate="one_to_one"
        )
        summary.loc[~complete_models, "FactorModelsObserved"] = summary.loc[
            ~complete_models, "_Observed"
        ]

    result = summary[keys].copy()
    result["FactorModelsExpected"] = "|".join(expected)
    result["FactorModelsObserved"] = summary["FactorModelsObserved"]
    result["FactorModelCount"] = summary["FactorModelCount"].astype(int)
    result["MarketUniverse"] = "TWSE_TPEX_COMMON_EQUITY_EX_2330"
    result["TSMCExcluded"] = True
    result["ConsensusStatus"] = summary["ConsensusStatus"]
    result["ConsensusEvidenceCategory"] = summary["ConsensusEvidenceCategory"]
    result["ConsensusPositioningSequencePhase"] = summary[
        "ConsensusPositioningSequencePhase"
    ]
    result["EvidenceCategory"] = result["ConsensusEvidenceCategory"]
    result["PositioningSequencePhase"] = result[
        "ConsensusPositioningSequencePhase"
    ]
    result["SignalAvailableAt"] = summary["SignalMin"].where(passed)
    result["EffectiveDate"] = summary["EffectiveMin"].where(passed)
    result["ConsensusActionable"] = passed & ~result[
        "ConsensusEvidenceCategory"
    ].astype("string").str.startswith("HOLD_")
    result["AggregationPolicy"] = (
        "EXACT_FACTOR_LANE_AGREEMENT_NO_AVERAGING_NO_VOTING_NO_SCORE"
    )
    result["TradeInstruction"] = False
    result["AttentionETR"] = summary["AttentionFirst"].where(invariants_exact)
    result["DirectionalAmount"] = summary["DirectionalFirst"].where(
        invariants_exact
    )
    for lane in expected:
        result[f"{lane}PriceEvidenceValue"] = summary[
            f"{lane}PriceEvidenceValue"
        ]
    return result.sort_values(keys, kind="stable").reset_index(drop=True)


def def_build_group_phase_daily(
    conserved_consensus_evidence: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize conserved stock phase breadth as a descriptive long table."""

    if conserved_consensus_evidence.empty:
        return pd.DataFrame()
    required = {
        "Date",
        "GroupId",
        "GroupName",
        "Ticker",
        "EvidenceWindowDays",
        "DirectionalLane",
        "ConsensusStatus",
        "ConsensusActionable",
        "ConsensusPositioningSequencePhase",
        "AllocationWeight",
        "AllocatedAttentionETR",
    }
    missing = sorted(required.difference(conserved_consensus_evidence.columns))
    if missing:
        raise ValueError(f"conserved consensus evidence missing group phase fields: {missing}")
    frame = conserved_consensus_evidence.loc[
        conserved_consensus_evidence["ConsensusStatus"].eq(
            "PASS_EXACT_FACTOR_MODEL_AGREEMENT"
        )
        & conserved_consensus_evidence["ConsensusActionable"].fillna(False)
    ].copy()
    if frame.empty:
        return pd.DataFrame()
    frame["AllocationWeight"] = pd.to_numeric(
        frame["AllocationWeight"], errors="coerce"
    )
    keys = [
        "Date",
        "GroupId",
        "GroupName",
        "EvidenceWindowDays",
        "DirectionalLane",
        "ConsensusPositioningSequencePhase",
    ]
    result = (
        frame.groupby(keys, as_index=False, dropna=False, observed=True)
        .agg(
            UniqueTickerCount=("Ticker", "nunique"),
            ConservedTickerExposure=("AllocationWeight", "sum"),
            AllocatedAttentionETR=(
                "AllocatedAttentionETR",
                lambda values: values.sum(min_count=1),
            ),
        )
    )
    result["Interpretation"] = (
        "DESCRIPTIVE_CONSERVED_PHASE_BREADTH_NOT_A_SCORE_RANK_OR_CAUSAL_CLAIM"
    )
    result["TradeInstruction"] = False
    return result.sort_values(keys, kind="stable").reset_index(drop=True)


def def_run_stock_positioning_grid(
    flow_panel: pd.DataFrame,
    rolling_residuals: pd.DataFrame,
    size_history: pd.DataFrame,
    approved_history: pd.DataFrame,
    trading_calendar: Iterable[Any],
    as_of_date: Any,
    evidence_cutoff_at: Any,
    pipeline_config: PipelineConfig = PipelineConfig(),
) -> dict[str, pd.DataFrame]:
    """Run aligned factor-lane × evidence-window stock positioning models."""

    collected: dict[str, list[pd.DataFrame]] = {
        "stock_positioning_daily_base": [],
        "stock_positioning_window_features": [],
        "stock_positioning_lane_evidence": [],
    }
    market_gate: pd.DataFrame | None = None
    audit_rows: list[dict[str, Any]] = []
    for window in pipeline_config.windows:
        # Keep only the current window's wide flow panel.  Retaining all three
        # window copies in a cache added no reuse once the loop advanced and
        # cost several gigabytes at full-universe scale.
        sized_panel = def_attach_pit_size_bucket(
            flow_panel, size_history, window_days=int(window)
        )
        for factor_lane in pipeline_config.factor_lanes:
            residual = def_bridge_residual_lane(
                rolling_residuals,
                factor_lane=factor_lane,
                window_days=int(window),
                as_of_date=as_of_date,
            )
            output = def_build_stock_positioning_outputs(
                sized_panel,
                trading_calendar,
                residual_returns=residual,
                as_of_date=as_of_date,
                config=StockPositioningConfig(windows=(int(window),)),
            )
            base = output["stock_daily_base"]
            evidence = output["stock_lane_evidence"]
            if base["Ticker"].astype(str).eq("2330").any():
                raise ValueError("TSMC entered the ex-2330 stock positioning model")
            expected_source = f"Residual_{factor_lane}_{int(window)}D"
            identity_ready = (
                base["FactorLane"].fillna("").eq(factor_lane)
                & pd.to_numeric(base["WindowDays"], errors="coerce").eq(int(window))
                & base["ResidualSourceColumn"].fillna("").eq(expected_source)
            )
            audit_rows.append(
                {
                    "ResidualFactorLane": factor_lane,
                    "ResidualBetaWindow": int(window),
                    "EvidenceWindowDays": int(window),
                    "ResidualSourceColumn": expected_source,
                    "StockDayRows": int(len(base)),
                    "EvidenceRows": int(len(evidence)),
                    "ResidualReadyRows": int(
                        base["PriceEvidenceBasis"].eq(
                            "EX_TSMC_RESIDUAL_RETURN"
                        ).sum()
                    ),
                    "ResidualIdentityReadyRows": int(identity_ready.sum()),
                    "MissingPITSizeBucketRows": int(
                        base["PeerDefinitionStatus"].eq(
                            "HOLD_SIZE_BUCKET_MISSING"
                        ).sum()
                    ),
                    "TSMCModelRows": 0,
                    "GridStatus": (
                        "PASS_ALIGNED_MODEL_GRID"
                        if evidence["EvidenceWindowDays"].eq(int(window)).all()
                        and identity_ready.all()
                        else "HOLD_WINDOW_OR_MODEL_IDENTITY_MISMATCH"
                    ),
                    "AggregationPolicy": "PARALLEL_MODELS_NO_SCORE",
                }
            )
            if market_gate is None:
                market_gate = output["market_gate_daily"].copy()
            source_map = {
                "stock_daily_base": "stock_positioning_daily_base",
                "stock_window_features": "stock_positioning_window_features",
                "stock_lane_evidence": "stock_positioning_lane_evidence",
            }
            for source, destination in source_map.items():
                table = output[source]
                table["ResidualFactorLane"] = factor_lane
                table["ResidualBetaWindow"] = int(window)
                collected[destination].append(def_compact_repeated_text(table))
            del output
        del sized_panel

    tables = {
        name: def_concat_compact_frames(parts)
        for name, parts in collected.items()
    }
    tables["stock_positioning_market_gate_daily"] = (
        def_compact_repeated_text(market_gate)
        if market_gate is not None
        else pd.DataFrame()
    )
    tables["stock_positioning_grid_audit"] = pd.DataFrame(audit_rows)

    # Membership allocation is independent of the residual model.  Map the
    # consolidated model evidence once instead of rebuilding identical PIT
    # allocations and merging one wide story table six times.
    model_story_mapping = def_map_evidence_to_story_groups(
        tables["stock_positioning_lane_evidence"], approved_history
    )
    tables["stock_positioning_raw_story_allocation"] = def_compact_repeated_text(
        model_story_mapping["raw_story_allocation"]
    )
    tables[
        "stock_positioning_conserved_story_allocation"
    ] = def_compact_repeated_text(
        model_story_mapping["conserved_story_allocation"]
    )
    tables["stock_positioning_raw_story_evidence"] = def_compact_repeated_text(
        model_story_mapping["raw_story_evidence"]
    )
    tables[
        "stock_positioning_conserved_story_evidence"
    ] = def_compact_repeated_text(
        model_story_mapping["conserved_story_evidence"]
    )
    del model_story_mapping

    consensus = def_reconcile_stock_positioning_models(
        tables["stock_positioning_lane_evidence"],
        factor_lanes=pipeline_config.factor_lanes,
    )
    consensus_mapping = def_map_evidence_to_story_groups(
        consensus, approved_history
    )
    tables["stock_positioning_model_consensus"] = def_compact_repeated_text(
        consensus
    )
    tables["stock_positioning_raw_consensus_story_evidence"] = (
        def_compact_repeated_text(consensus_mapping["raw_story_evidence"])
    )
    tables[
        "stock_positioning_conserved_consensus_story_evidence"
    ] = def_compact_repeated_text(consensus_mapping["conserved_story_evidence"])
    tables["stock_positioning_group_phase_daily"] = def_build_group_phase_daily(
        consensus_mapping["conserved_story_evidence"]
    )
    exact_consensus = consensus.loc[
        consensus["ConsensusStatus"].eq(
            "PASS_EXACT_FACTOR_MODEL_AGREEMENT"
        )
    ].copy()
    transition_ledger = def_build_positioning_transition_ledger(
        exact_consensus,
        trading_calendar,
        as_of=evidence_cutoff_at,
    )
    tables["stock_positioning_transition_ledger"] = transition_ledger
    tables["stock_positioning_transition_latest"] = (
        def_latest_positioning_transition_state(
            transition_ledger,
            trading_calendar,
            as_of=evidence_cutoff_at,
        )
    )
    if transition_ledger.empty:
        tables["stock_positioning_raw_transition_story_evidence"] = pd.DataFrame()
        tables[
            "stock_positioning_conserved_transition_story_evidence"
        ] = pd.DataFrame()
    else:
        transition_for_mapping = transition_ledger.rename(
            columns={"EvidenceDate": "Date"}
        )
        evidence_keys = [
            "Date",
            "Ticker",
            "EvidenceWindowDays",
            "DirectionalLane",
            "EffectiveDate",
        ]
        invariant_evidence = exact_consensus[
            [*evidence_keys, "AttentionETR", "DirectionalAmount"]
        ]
        transition_for_mapping = transition_for_mapping.merge(
            invariant_evidence,
            on=evidence_keys,
            how="left",
            validate="one_to_one",
        )
        transition_mapping = def_map_evidence_to_story_groups(
            transition_for_mapping, approved_history
        )
        tables[
            "stock_positioning_raw_transition_story_evidence"
        ] = transition_mapping["raw_story_evidence"]
        tables[
            "stock_positioning_conserved_transition_story_evidence"
        ] = transition_mapping["conserved_story_evidence"]
    return tables


def def_build_group_comparison_daily(
    index_long: pd.DataFrame,
    flow_states: pd.DataFrame,
    fx_adjusted_flow: pd.DataFrame,
) -> pd.DataFrame:
    index_values = index_long.pivot_table(
        index=["Date", "GroupId"], columns="Method", values="IndexLevel", aggfunc="first"
    ).reset_index()
    index_values.columns.name = None
    flow_columns = [
        column
        for column in flow_states.columns
        if column in {"Date", "GroupId"} or column not in index_values.columns
    ]
    result = index_values.merge(
        flow_states[flow_columns],
        on=["Date", "GroupId"],
        how="outer",
        validate="one_to_many",
    )
    fx_columns = [
        column
        for column in fx_adjusted_flow.columns
        if column.startswith("ForeignFlowFXResidual_") or column in {"Date", "GroupId"}
    ]
    if len(fx_columns) > 2:
        result = result.merge(
            fx_adjusted_flow[fx_columns],
            on=["Date", "GroupId"],
            how="left",
            validate="many_to_one",
        )
    result["ComparisonPolicy"] = "PRICE_ATTENTION_AND_DIRECTIONAL_LANES_NO_COMPOSITE"
    return result.sort_values(["GroupId", "Date"]).reset_index(drop=True)


def def_cap_dated_factor_output_asof(
    factor_output: Mapping[str, Any],
    snapshot: Any,
) -> dict[str, Any]:
    """Apply one immutable as-of boundary to every dated factor table.

    The factor engine may be run over a longer local input history than the
    requested publication snapshot.  Centralising the cut here prevents a new
    dated factor table from accidentally bypassing a hand-written list of
    downstream filters.
    """

    snapshot_date = def_local_calendar_date(snapshot)
    if pd.isna(snapshot_date):
        raise ValueError("snapshot is invalid")
    capped: dict[str, Any] = {}
    for name, value in factor_output.items():
        if not isinstance(value, pd.DataFrame) or "Date" not in value.columns:
            capped[name] = value
            continue
        local_dates = value["Date"].map(def_local_calendar_date)
        if local_dates.isna().any():
            raise ValueError(f"factor output {name} contains invalid Date rows")
        table = value.loc[local_dates.le(snapshot_date)].copy()
        table.attrs.update(value.attrs)
        capped[name] = table
    return capped


def def_latest_required_availability(
    frame: pd.DataFrame,
    columns: Iterable[str] = REQUIRED_MARKET_AVAILABILITY_COLUMNS,
) -> pd.Series:
    """Return each row's latest known core timestamp without forward filling."""

    required = tuple(columns)
    missing = sorted(set(required).difference(frame.columns))
    if missing:
        raise ValueError(f"core evidence missing availability columns: {missing}")
    parsed = pd.concat(
        [frame[column].map(def_available_at_utc).rename(column) for column in required],
        axis=1,
    )
    return parsed.max(axis=1)


def def_run_pipeline_frames(
    inputs: Mapping[str, Any],
    *,
    proposed_at: Any,
    as_of_date: Any | None = None,
    evidence_cutoff_at: Any | None = None,
    pipeline_config: PipelineConfig = PipelineConfig(),
) -> dict[str, pd.DataFrame]:
    def_validate_formal_pipeline_grid(pipeline_config)
    required = {
        "market_daily",
        "universe_history",
        "trading_calendar",
        "membership_events",
        "candidate49",
        "macro_vintages",
        "active_etf_holdings",
    }
    missing = sorted(required.difference(inputs))
    if missing:
        raise ValueError(f"pipeline frames missing inputs: {missing}")
    calendar_frame = inputs["trading_calendar"]
    if "Date" not in calendar_frame:
        raise ValueError("trading_calendar requires Date")
    calendar_dates = calendar_frame["Date"].map(def_local_calendar_date)
    if calendar_dates.isna().any() or calendar_dates.empty:
        raise ValueError("trading_calendar contains invalid or no sessions")
    calendar = pd.DatetimeIndex(calendar_dates).unique().sort_values()
    market = inputs["market_daily"].copy()
    if "Date" not in market:
        raise ValueError("market_daily requires Date")
    absent_availability = sorted(
        set(REQUIRED_MARKET_AVAILABILITY_COLUMNS).difference(market.columns)
    )
    if absent_availability:
        raise ValueError(f"market_daily missing PIT availability columns: {absent_availability}")
    if "IsLimitUpLocked" not in market or "IsLimitDownLocked" not in market:
        raise ValueError("market_daily requires point-in-time limit-up and limit-down lock flags")

    # Cap the raw market panel before any gate, factor or residual calculation.
    # A later malformed append must not change an earlier publication snapshot.
    if not market.empty:
        market_dates = market["Date"].map(def_local_calendar_date)
        if market_dates.isna().any():
            raise ValueError("market_daily contains invalid Date rows")
        warmup_start = pd.Timestamp(pipeline_config.warmup_start_date)
        market = market.loc[market_dates.ge(warmup_start)].copy()
        market_dates = market["Date"].map(def_local_calendar_date)
        if market.empty:
            raise ValueError("market_daily has no rows on or after warmup_start_date")
        if as_of_date is not None:
            requested_as_of = def_local_calendar_date(as_of_date)
            eligible_as_of_sessions = calendar[calendar <= requested_as_of]
            if not len(eligible_as_of_sessions):
                raise ValueError("as_of_date precedes the formal trading calendar")
            target_session = pd.Timestamp(eligible_as_of_sessions[-1])
            if not market_dates.eq(target_session).any():
                raise ValueError(
                    "market_daily is stale: the requested as-of trading session is missing"
                )
            market = market.loc[market_dates.le(target_session)].copy()
            if market.empty:
                raise ValueError("market_daily has no rows on or before as_of_date")

    factor_output = def_run_full_market_factor_pipeline(
        market,
        inputs["universe_history"],
        trading_calendar=calendar,
        windows=pipeline_config.windows,
    )
    latest_market_date = factor_output["validated_panel"]["Date"].max()
    snapshot = (
        min(def_local_calendar_date(as_of_date), latest_market_date)
        if as_of_date is not None
        else latest_market_date
    )
    factor_output = def_cap_dated_factor_output_asof(factor_output, snapshot)
    later_sessions = calendar[calendar > snapshot]
    if not len(later_sessions):
        raise ValueError("trading_calendar must include the next session after as_of_date")
    snapshot_market = factor_output["validated_panel"].loc[
        factor_output["validated_panel"]["Date"].eq(snapshot)
    ]
    decision_at = def_latest_required_availability(snapshot_market).max()
    if pd.isna(decision_at):
        raise ValueError("latest market evidence has no point-in-time availability")
    evidence_cutoff = (
        def_available_at_utc(evidence_cutoff_at)
        if evidence_cutoff_at is not None
        else decision_at
    )
    if pd.isna(evidence_cutoff):
        raise ValueError("evidence_cutoff_at is invalid")
    if evidence_cutoff < decision_at:
        raise ValueError("evidence_cutoff_at cannot precede latest market availability")
    if def_local_calendar_date(evidence_cutoff) > snapshot:
        raise ValueError("evidence_cutoff_at local date cannot exceed snapshot")

    normalized_events = def_normalize_membership_events(inputs["membership_events"], calendar)
    approved_history = def_materialize_membership_history(
        normalized_events,
        calendar,
        known_at=evidence_cutoff,
    )
    if approved_history.empty:
        raise ValueError("no approved PIT membership exists for index/flow publication")

    candidate, candidate_audit_dict = def_prepare_candidate49(inputs["candidate49"], proposed_at)
    candidate_audit = pd.DataFrame([candidate_audit_dict])
    validation_membership = def_merge_validation_membership(candidate, approved_history)
    size_history = def_compute_quarterly_bucket_history(factor_output["validated_panel"])
    validation = def_run_validation_grid(
        factor_output["rolling_residuals"],
        validation_membership,
        size_history,
        snapshot,
        decision_at,
        calendar,
        pipeline_config,
    )
    review_queue = def_build_membership_review_queue(
        validation["member_role_consensus"], validation_membership
    )

    index_output = def_build_parallel_group_indices(
        factor_output["weighted_panel"],
        approved_history,
        HierarchicalIndexConfig(require_pit_size_history=True),
        size_history=size_history,
    )
    index_long = def_bridge_index_method(index_output["index_long"])

    etf = def_build_active_etf_analysis(
        inputs["active_etf_holdings"],
        evidence_cutoff,
        membership=approved_history,
        trading_calendar=calendar,
    )
    market_with_etf = def_attach_active_etf_lane(
        factor_output["validated_panel"], etf["individual_holding_events"]
    )
    market_with_etf.attrs.update(factor_output["validated_panel"].attrs)
    flow_panel = def_prepare_stock_flow_panel(market_with_etf)
    stock_positioning = def_run_stock_positioning_grid(
        flow_panel,
        factor_output["rolling_residuals"],
        size_history,
        approved_history,
        calendar,
        snapshot,
        evidence_cutoff,
        pipeline_config,
    )
    group_flow = def_compute_group_flow_daily(flow_panel, approved_history)
    primary_price = index_output["index_long"].loc[
        index_output["index_long"]["Method"].eq("GI_HIER")
    ]
    flow_states = def_add_dynamic_flow_states(
        group_flow,
        primary_price,
        trading_calendar=calendar,
    )
    transfer = def_build_flow_transfer_outputs(flow_panel, approved_history)

    macro_prepared = def_prepare_macro_factors(inputs["macro_vintages"])
    market_decision_source = flow_panel[["Date"]].copy()
    market_decision_source["DecisionAt"] = def_latest_required_availability(
        flow_panel
    )
    market_decisions = (
        market_decision_source.groupby("Date", as_index=False)["DecisionAt"]
        .max()
    )
    macro_pit = def_add_macro_context(
        def_materialize_macro_asof(macro_prepared, market_decisions)
    )
    fx_adjusted = def_foreign_flow_fx_residual(group_flow, macro_pit)

    transition_latest = stock_positioning[
        "stock_positioning_transition_latest"
    ]
    opportunity_tickers = (
        transition_latest.loc[
            transition_latest["VerifiedPhase"].isin(
                [
                    "STABLE_POSITIONING_DURING_PRICE_PULLBACK_OR_SIDEWAYS_OBSERVED",
                    "PRICE_RESTART_AFTER_STABLE_POSITIONING_OBSERVED",
                ]
            ),
            "Ticker",
        ].drop_duplicates()
        if not transition_latest.empty
        else []
    )
    revenue_reference = def_build_optional_revenue_reference(
        inputs.get("monthly_revenue"),
        evidence_cutoff,
        approved_history,
        snapshot,
        opportunity_tickers=opportunity_tickers,
    )

    backtest_config = def_build_backtest_config(pipeline_config, snapshot)
    events = def_run_multi_period_event_study(flow_states, index_long, macro_pit, backtest_config)
    performance = def_compute_index_performance(
        index_long,
        macro_pit,
        factor_output["market_factors"],
        backtest_config,
    )
    event_summary = def_summarize_event_study(events) if not events.empty else pd.DataFrame()
    comparison = def_build_group_comparison_daily(
        index_output["index_long"], flow_states, fx_adjusted
    )
    tsmc_anchor_daily = factor_output["market_factors"][
        [
            "Date",
            "TSMCReturnSeparated",
            "TSMCETRSeparated",
            "TSMCMarketCapSeparated",
        ]
    ].copy()
    tsmc_anchor_daily["AnchorPolicy"] = (
        "REPORTED_SEPARATELY_EXCLUDED_FROM_MARKET_SIZE_AND_CROSS_GROUP_COMPARISON"
    )

    tables: dict[str, pd.DataFrame] = {
        "candidate49": candidate,
        "candidate49_audit": candidate_audit,
        "membership_history": approved_history,
        "full_market_gate_daily": factor_output["gate_daily"],
        "market_factors": factor_output["market_factors"],
        "tsmc_anchor_daily": tsmc_anchor_daily,
        "rolling_residuals": factor_output["rolling_residuals"],
        "size_history": size_history,
        "index_weights": index_output["weights"],
        "group_index_daily": index_long,
        "group_flow_daily": group_flow,
        "group_flow_states": flow_states,
        "rotation_associations": transfer["rotation_associations"],
        "macro_context_daily": macro_pit,
        "foreign_flow_fx_residual": fx_adjusted,
        "backtest_events": events,
        "backtest_event_summary": event_summary,
        "index_performance": performance,
        "membership_review_queue": review_queue,
        "group_comparison_daily": comparison,
    }
    for name, table in validation.items():
        tables[name] = table
    for name, table in etf.items():
        if isinstance(table, pd.DataFrame):
            tables[f"active_etf_{name}"] = table
    tables.update(revenue_reference)
    tables.update(stock_positioning)
    return tables


def def_run_pipeline_from_config(
    config_path: Path,
    *,
    proposed_at: Any,
    as_of_date: Any | None = None,
    evidence_cutoff_at: Any | None = None,
    write_output: bool = True,
) -> dict[str, Any]:
    raw_config = def_load_json(config_path)
    pipeline_config = def_pipeline_config_from_mapping(raw_config)
    base_dir = config_path.parent.parent
    preflight = def_input_preflight(base_dir, raw_config)
    if preflight["BlocksCorePipeline"].any():
        missing = preflight.loc[preflight["BlocksCorePipeline"], "InputName"].tolist()
        raise FileNotFoundError(f"real-data preflight blocked missing inputs: {missing}")
    local = raw_config["local_inputs"]
    input_names = {
        "full_market_daily",
        "universe_history",
        "trading_calendar",
        "membership_events",
        "macro_vintages",
        "active_etf_holdings",
        "monthly_revenue",
    }
    inputs = {}
    for name, value in local.items():
        if name not in input_names:
            continue
        path = def_resolve_path(base_dir, value)
        if path.is_file():
            # Revenue is an optional post-opportunity reference.  Preserve its
            # path so malformed reference data cannot interrupt the core run
            # before a strict stage-3/4 opportunity actually exists.
            inputs[name] = path if name == "monthly_revenue" else def_read_table(path)
    inputs["market_daily"] = inputs.pop("full_market_daily")
    inputs["candidate49"] = def_read_table(
        def_resolve_path(base_dir, raw_config["candidate_story_membership"])
    )
    tables = def_run_pipeline_frames(
        inputs,
        proposed_at=proposed_at,
        as_of_date=as_of_date,
        evidence_cutoff_at=evidence_cutoff_at,
        pipeline_config=pipeline_config,
    )
    manifest: dict[str, Any] | None = None
    if write_output:
        effective_as_of = as_of_date or max(
            pd.to_datetime(tables["group_index_daily"]["Date"])
        )
        manifest = def_write_run(
            tables,
            def_resolve_path(base_dir, pipeline_config.output_root),
            effective_as_of,
        )
    return {"Preflight": preflight, "Tables": tables, "Manifest": manifest}
