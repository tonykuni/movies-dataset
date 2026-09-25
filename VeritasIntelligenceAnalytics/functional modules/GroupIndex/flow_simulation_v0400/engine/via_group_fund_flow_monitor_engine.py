from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from engine.dashboard_builder import def_build_dashboard_html
from engine.via_attention_share_engine import def_compute_attention_share
from engine.via_flowrot_candidate_intake import def_write_flowrot_candidate
from engine.via_dynamic_classification_engine import (
    def_compute_dynamic_classification,
    def_derive_dynamic_parameters,
    def_prepare_main_force,
)
from engine.via_rotation_backtest_engine import def_run_rotation_backtest
from engine.via_rotation_snapshot_engine import (
    def_append_rotation_snapshot,
    def_build_rotation_snapshot,
    def_extract_vdf_contract_summary,
    def_validate_rotation_source_contract,
    def_write_rotation_quality,
)
from engine.via_version_chain import def_build_candidate_version_chain, def_validate_candidate_groups


# =============================================================================
# PARAMETERS · all defaults are centralized here or in config/system_config.json
# =============================================================================
SYSTEM_ID = "VIA_TW_GROUP_FLOW_SIMULATION_SYSTEM"
VERSION = "0.4.0"
DEFAULT_CONFIG_PATH = "config/system_config.json"
DEFAULT_EXPECTED_GROUP_COUNT = 31
DEFAULT_ROLLING_WINDOWS = (1, 5, 20, 60, 120, 240)
DEFAULT_ROLE_WINDOWS = (20, 60)
DEFAULT_INDEX_BASE_VALUE = 100.0
DEFAULT_INDEX_WEIGHT_METHOD = "LAGGED_CLOSE_VOLUME_WEIGHT"
DEFAULT_NORMALIZED_DATE = "2026-01-02"
DEFAULT_PRICE_FORWARD_FILL_LIMIT = 3
DEFAULT_SIMULATION_MIN_OBSERVATIONS = 80
DEFAULT_SIMULATION_TRAIN_FRACTION = 0.75
DEFAULT_SIMULATION_RIDGE_ALPHA = 1.0
DEFAULT_SIMULATION_HORIZON_DAYS = 20
DEFAULT_UI_MAX_DATES = 180
DEFAULT_FLOW_SCALE = 100_000_000.0
TW_TICKER_REGEX = re.compile(r"^[1-9][0-9]{3}\.(?:TW|TWO)$", re.IGNORECASE)
DATE_COLUMN = "Date"
GROUP_KEYS = ["GroupId", "GroupName"]
FLOW_COMPONENTS = [
    "ForeignNetAmount",
    "InvestmentTrustNetAmount",
    "DealerNetAmount",
    "InstitutionalNetAmount",
    "MarginNetFlow",
    "ShortNetFlow",
    "ActiveETFFlowAmount",
    "MainForceNetAmount",
]
SIMULATION_FEATURES = [
    "InstitutionalFlowIntensity",
    "ActiveETFFlowIntensity",
    "CreditDeviation",
    "TurnoverShare",
    "InstitutionalSyncRate",
]


@dataclass(frozen=True)
class SystemConfig:
    system_id: str
    version: str
    data_mode: str
    expected_group_count: int
    enforce_group_count: bool
    normalized_date: str
    index_base_value: float
    index_weight_method: str
    rolling_windows: tuple[int, ...]
    role_windows: tuple[int, ...]
    price_forward_fill_limit: int
    flow_scale: float
    simulation_min_observations: int
    simulation_train_fraction: float
    simulation_ridge_alpha: float
    simulation_horizon_days: int
    ui_max_dates: int
    ui_card_dense_threshold_quantile: float
    candidate_source_file: str
    rotation_snapshot_source_file: str
    vdf_contract_source_file: str
    market_intelligence_registry_file: str
    method_thresholds_file: str
    input_files: dict[str, str]
    output_files: dict[str, str]
    scenarios: tuple[dict[str, Any], ...]


def def_utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def def_load_config(config_path: Path) -> SystemConfig:
    raw = json.loads(config_path.read_text(encoding="utf-8"))
    return SystemConfig(
        system_id=str(raw.get("system_id", SYSTEM_ID)),
        version=str(raw.get("version", VERSION)),
        data_mode=str(raw.get("data_mode", "REVIEW_REQUIRED")).upper(),
        expected_group_count=int(raw.get("expected_group_count", DEFAULT_EXPECTED_GROUP_COUNT)),
        enforce_group_count=bool(raw.get("enforce_group_count", True)),
        normalized_date=str(raw.get("normalized_date", DEFAULT_NORMALIZED_DATE)),
        index_base_value=float(raw.get("index_base_value", DEFAULT_INDEX_BASE_VALUE)),
        index_weight_method=str(raw.get("index_weight_method", DEFAULT_INDEX_WEIGHT_METHOD)).upper(),
        rolling_windows=tuple(int(value) for value in raw.get("rolling_windows", DEFAULT_ROLLING_WINDOWS)),
        role_windows=tuple(int(value) for value in raw.get("role_windows", DEFAULT_ROLE_WINDOWS)),
        price_forward_fill_limit=int(raw.get("price_forward_fill_limit", DEFAULT_PRICE_FORWARD_FILL_LIMIT)),
        flow_scale=float(raw.get("flow_scale", DEFAULT_FLOW_SCALE)),
        simulation_min_observations=int(
            raw.get("simulation_min_observations", DEFAULT_SIMULATION_MIN_OBSERVATIONS)
        ),
        simulation_train_fraction=float(
            raw.get("simulation_train_fraction", DEFAULT_SIMULATION_TRAIN_FRACTION)
        ),
        simulation_ridge_alpha=float(raw.get("simulation_ridge_alpha", DEFAULT_SIMULATION_RIDGE_ALPHA)),
        simulation_horizon_days=int(
            raw.get("simulation_horizon_days", DEFAULT_SIMULATION_HORIZON_DAYS)
        ),
        ui_max_dates=int(raw.get("ui_max_dates", DEFAULT_UI_MAX_DATES)),
        ui_card_dense_threshold_quantile=float(raw.get("ui_card_dense_threshold_quantile", 0.75)),
        candidate_source_file=str(
            raw.get(
                "candidate_source_file",
                "references/intake/3d616edd-3f96-44cf-9e5d-c885bf414120.html",
            )
        ),
        rotation_snapshot_source_file=str(
            raw.get(
                "rotation_snapshot_source_file",
                "ssot/VIA_Rotation_Snapshot_20260718_v0400.json",
            )
        ),
        vdf_contract_source_file=str(
            raw.get(
                "vdf_contract_source_file",
                "references/intake/32f56779-e9a8-45d5-8498-7517053f95a2.html",
            )
        ),
        market_intelligence_registry_file=str(
            raw.get(
                "market_intelligence_registry_file",
                "ssot/VIA_Market_Intelligence_Registry_Summary_v0400.json",
            )
        ),
        method_thresholds_file=str(
            raw.get("method_thresholds_file", "ssot/VIA_FLOWROT_Method_Thresholds_v0300.json")
        ),
        input_files=dict(raw["input_files"]),
        output_files=dict(raw["output_files"]),
        scenarios=tuple(raw.get("scenarios", [])),
    )


def def_resolve_path(project_root: Path, configured_path: str) -> Path:
    path = Path(configured_path)
    return path if path.is_absolute() else project_root / path


def def_read_table(path: Path) -> pd.DataFrame:
    candidates = [path]
    if not path.suffix:
        candidates.extend([path.with_suffix(".parquet"), path.with_suffix(".csv"), path.with_suffix(".json")])
    resolved = next((candidate for candidate in candidates if candidate.exists()), None)
    if resolved is None:
        raise FileNotFoundError(f"Input table not found: {path}")
    suffix = resolved.suffix.lower()
    if suffix == ".parquet":
        return pd.read_parquet(resolved)
    if suffix == ".csv":
        return pd.read_csv(resolved, encoding="utf-8-sig")
    if suffix == ".json":
        return pd.read_json(resolved)
    raise ValueError(f"Unsupported input format: {resolved}")


def def_require_columns(frame: pd.DataFrame, required: Iterable[str], table_name: str) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"{table_name} missing required columns: {missing}")


def def_to_bool(series: pd.Series, default: bool) -> pd.Series:
    if series.dtype == bool:
        return series.fillna(default)
    mapping = {
        "TRUE": True,
        "1": True,
        "YES": True,
        "Y": True,
        "COUNT": True,
        "FALSE": False,
        "0": False,
        "NO": False,
        "N": False,
        "DISPLAY_ONLY": False,
    }
    return series.map(lambda value: mapping.get(str(value).strip().upper(), default)).astype(bool)


def def_normalize_ticker(value: Any) -> str:
    ticker = str(value).strip().upper().replace(" ", "")
    if ticker.endswith(".TW.TW"):
        ticker = ticker[:-3]
    if ticker.endswith(".TWO.TWO"):
        ticker = ticker[:-4]
    return ticker


def def_check(
    ledger: list[dict[str, Any]],
    check_id: str,
    check: str,
    status: str,
    severity: str,
    finding_count: int,
    detail: str,
) -> None:
    ledger.append(
        {
            "CheckId": check_id,
            "Check": check,
            "Status": status,
            "Severity": severity,
            "FindingCount": int(finding_count),
            "Detail": detail,
        }
    )


def def_prepare_membership(
    membership: pd.DataFrame,
    config: SystemConfig,
    ledger: list[dict[str, Any]],
) -> pd.DataFrame:
    def_require_columns(membership, ["GroupId", "GroupName", "Ticker", "IndexEligible"], "membership")
    frame = membership.copy()
    frame["GroupId"] = frame["GroupId"].astype(str).str.strip()
    frame["GroupName"] = frame["GroupName"].astype(str).str.strip()
    frame["Ticker"] = frame["Ticker"].map(def_normalize_ticker)
    frame["IndexEligible"] = def_to_bool(frame["IndexEligible"], True)
    frame["FlowEligible"] = def_to_bool(
        frame["FlowEligible"] if "FlowEligible" in frame else frame["IndexEligible"], True
    )
    frame["DisplayOnly"] = def_to_bool(
        frame["DisplayOnly"] if "DisplayOnly" in frame else ~frame["IndexEligible"], False
    )
    frame["PrimaryEconomicIdentity"] = frame.get("PrimaryEconomicIdentity", frame["GroupName"]).astype(str)
    frame["Name"] = frame.get("Name", frame["Ticker"]).fillna(frame["Ticker"]).astype(str).str.strip()
    frame["Market"] = frame.get(
        "Market",
        frame["Ticker"].map(
            lambda ticker: "TWSE" if str(ticker).endswith(".TW") else (
                "TPEX" if str(ticker).endswith(".TWO") else "REVIEW"
            )
        ),
    ).fillna("REVIEW").astype(str).str.upper().str.strip()
    frame["UITier"] = frame.get("UITier", "STANDARD").astype(str).str.upper()
    frame["SourceVersion"] = frame.get("SourceVersion", "UNSPECIFIED").astype(str)
    frame["CandidateRole"] = frame.get("CandidateRole", "PEER").astype(str).str.upper()
    frame["MarketVerified"] = def_to_bool(
        frame["MarketVerified"] if "MarketVerified" in frame else pd.Series(False, index=frame.index),
        False,
    )
    frame["MarketSource"] = frame.get("MarketSource", "UNVERIFIED").astype(str)
    duplicate_count = int(frame.duplicated(["GroupId", "Ticker"], keep=False).sum())
    if duplicate_count:
        raise ValueError(f"membership contains {duplicate_count} duplicate GroupId+Ticker rows")
    group_count = int(frame["GroupId"].nunique())
    count_ok = not config.enforce_group_count or group_count == config.expected_group_count
    def_check(
        ledger,
        "SSOT001",
        "Expected group count",
        "PASS" if count_ok else "FAIL",
        "HARD",
        abs(group_count - config.expected_group_count),
        f"actual={group_count}; expected={config.expected_group_count}; mode={config.data_mode}",
    )
    frame["TickerReview"] = ~frame["Ticker"].str.match(TW_TICKER_REGEX)
    review_count = int(frame["TickerReview"].sum())
    def_check(
        ledger,
        "SSOT002",
        "Taiwan ticker syntax review",
        "PASS" if review_count == 0 else "REVIEW",
        "REVIEW",
        review_count,
        "Special tickers are retained for review and are never auto-deleted.",
    )
    unverified_market = int((~frame["MarketVerified"]).sum())
    def_check(
        ledger,
        "SSOT003",
        "Candidate market suffix evidence",
        "REVIEW" if unverified_market else "PASS",
        "REVIEW",
        unverified_market,
        "Unknown TWSE/TPEX suffixes remain REVIEW; fixture-only .TW fallback is never treated as verified.",
    )
    if not count_ok:
        raise ValueError(f"SSOT group count mismatch: actual={group_count}, expected={config.expected_group_count}")
    return frame.sort_values(["GroupId", "Ticker"]).reset_index(drop=True)


def def_prepare_price(
    price: pd.DataFrame,
    config: SystemConfig,
    ledger: list[dict[str, Any]],
) -> pd.DataFrame:
    def_require_columns(price, [DATE_COLUMN, "Ticker", "Adj_Close"], "price")
    frame = price.copy()
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    frame["Ticker"] = frame["Ticker"].map(def_normalize_ticker)
    for column in ["Adj_Close", "Volume", "TurnoverValue", "DayTradeTurnover", "MarketCap"]:
        if column not in frame:
            frame[column] = np.nan
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    invalid_dates = int(frame[DATE_COLUMN].isna().sum())
    if invalid_dates:
        raise ValueError(f"price contains {invalid_dates} invalid dates")
    duplicates = int(frame.duplicated([DATE_COLUMN, "Ticker"], keep=False).sum())
    if duplicates:
        raise ValueError(f"price contains {duplicates} duplicate Date+Ticker rows")
    frame = frame.sort_values(["Ticker", DATE_COLUMN]).reset_index(drop=True)
    raw_adj_missing = frame["Adj_Close"].isna()
    frame["Adj_Close"] = frame.groupby("Ticker", sort=False)["Adj_Close"].ffill(
        limit=config.price_forward_fill_limit
    )
    frame["AdjCloseFillFlag"] = raw_adj_missing & frame["Adj_Close"].notna()
    frame["Return"] = frame.groupby("Ticker", sort=False)["Adj_Close"].pct_change(fill_method=None)
    frame["LaggedMarketCap"] = frame.groupby("Ticker", sort=False)["MarketCap"].shift(1)
    def_check(
        ledger,
        "DATA001",
        "Adjusted Close limited forward-fill",
        "PASS",
        "INFO",
        int(frame["AdjCloseFillFlag"].sum()),
        f"limit={config.price_forward_fill_limit}; Volume and turnover were not filled.",
    )
    def_check(
        ledger,
        "DATA002",
        "Volume forward-fill prohibition",
        "PASS",
        "HARD",
        0,
        "Engine does not invoke fill operations on Volume or TurnoverValue.",
    )
    return frame


def def_compute_group_index(
    membership: pd.DataFrame,
    price: pd.DataFrame,
    config: SystemConfig,
    ledger: list[dict[str, Any]],
) -> pd.DataFrame:
    eligible = membership.loc[membership["IndexEligible"], GROUP_KEYS + ["Ticker"]]
    panel = eligible.merge(price, on="Ticker", how="inner", validate="many_to_many")
    if panel.empty:
        raise ValueError("No eligible membership rows matched price data")
    method = config.index_weight_method
    if method not in {"EQUAL_WEIGHT", "LAGGED_MARKET_CAP", "LAGGED_CLOSE_VOLUME_WEIGHT"}:
        raise ValueError(f"Unsupported index_weight_method: {method}")
    keys = [DATE_COLUMN, "GroupId", "GroupName"]
    if method == "EQUAL_WEIGHT":
        grouped = panel.groupby(keys, observed=True, sort=True)
        result = grouped["Return"].mean().rename("GroupReturn").reset_index()
        counts = grouped["Return"].count().rename("ConstituentCount").reset_index()
        result = result.merge(counts, on=keys, how="left")
        result["WeightFallback"] = False
    else:
        if method == "LAGGED_MARKET_CAP":
            panel["WeightNumerator"] = panel["LaggedMarketCap"].where(panel["LaggedMarketCap"] > 0)
            weight_detail = "lagged market cap"
        else:
            date_count = int(price[DATE_COLUMN].nunique())
            volume_window = int(np.clip(round(date_count * 0.025), 5, 10))
            weight_source = price.sort_values(["Ticker", DATE_COLUMN]).copy()
            weight_source["LaggedClose"] = weight_source.groupby("Ticker", sort=False)["Adj_Close"].shift(1)
            weight_source["LaggedVolume"] = weight_source.groupby("Ticker", sort=False)["Volume"].transform(
                lambda values: values.rolling(volume_window, min_periods=max(3, volume_window // 2)).median().shift(1)
            )
            weight_source["CloseVolumeWeight"] = weight_source["LaggedClose"] * weight_source["LaggedVolume"]
            panel = panel.drop(columns=["CloseVolumeWeight"], errors="ignore").merge(
                weight_source[[DATE_COLUMN, "Ticker", "CloseVolumeWeight"]],
                on=[DATE_COLUMN, "Ticker"],
                how="left",
                validate="many_to_one",
            )
            panel["WeightNumerator"] = panel["CloseVolumeWeight"].where(panel["CloseVolumeWeight"] > 0)
            weight_detail = f"lagged adjusted close x trailing {volume_window}D median volume"
        panel["WeightDenominator"] = panel.groupby(keys, observed=True)["WeightNumerator"].transform("sum")
        panel["EligibleCount"] = panel.groupby(keys, observed=True)["Return"].transform("count")
        panel["WeightFallback"] = panel["WeightDenominator"].isna() | (panel["WeightDenominator"] <= 0)
        panel["Weight"] = np.where(
            panel["WeightFallback"],
            1.0 / panel["EligibleCount"].replace(0, np.nan),
            panel["WeightNumerator"] / panel["WeightDenominator"],
        )
        panel["WeightedReturn"] = panel["Return"] * panel["Weight"]
        grouped = panel.groupby(keys, observed=True, sort=True)
        result = grouped["WeightedReturn"].sum(min_count=1).rename("GroupReturn").reset_index()
        counts = grouped["Return"].count().rename("ConstituentCount").reset_index()
        fallbacks = grouped["WeightFallback"].max().rename("WeightFallback").reset_index()
        result = result.merge(counts, on=keys).merge(fallbacks, on=keys)
    result = result.sort_values(["GroupId", DATE_COLUMN]).reset_index(drop=True)
    result["GroupReturn"] = result["GroupReturn"].replace([np.inf, -np.inf], np.nan)
    result["Wealth"] = result.groupby("GroupId", sort=False)["GroupReturn"].transform(
        lambda series: (1.0 + series.fillna(0.0)).cumprod()
    )
    normalized_date = pd.Timestamp(config.normalized_date)

    base_wealth: dict[str, float] = {}
    for group_id, group in result.groupby("GroupId", sort=False):
        eligible_base = group.loc[group[DATE_COLUMN] >= normalized_date, "Wealth"]
        base_wealth[str(group_id)] = float(
            eligible_base.iloc[0] if not eligible_base.empty else group["Wealth"].iloc[0]
        )
    result["GroupIndex"] = (
        config.index_base_value
        * result["Wealth"]
        / result["GroupId"].map(base_wealth).replace(0, np.nan)
    )
    result["WeightMethod"] = method
    result["NormalizedDate"] = normalized_date
    base_rows = result.loc[result[DATE_COLUMN] >= normalized_date].groupby("GroupId", sort=False).head(1)
    base_error = int((base_rows["GroupIndex"].sub(config.index_base_value).abs() > 1e-8).sum())
    def_check(
        ledger,
        "INDEX001",
        "Base-100 normalized index",
        "PASS" if base_error == 0 else "FAIL",
        "HARD",
        base_error,
        f"method={method}; normalized_date={config.normalized_date}; "
        + (weight_detail if method != "EQUAL_WEIGHT" else "equal weight"),
    )
    def_check(
        ledger,
        "INDEX002",
        "Index weight lookahead prohibition",
        "PASS",
        "HARD",
        0,
        "Close and volume weights are shifted by one trading day; missing weights fall back to equal weight.",
    )
    return result.drop(columns=["Wealth"])


def def_group_sum(frame: pd.DataFrame, keys: list[str], columns: list[str]) -> pd.DataFrame:
    grouped = frame.groupby(keys, observed=True, sort=True)
    output = grouped[columns].sum(min_count=1).reset_index()
    return output


def def_prepare_institutional(institutional: pd.DataFrame) -> pd.DataFrame:
    required = [DATE_COLUMN, "Ticker", "ForeignNetAmount", "InvestmentTrustNetAmount", "DealerNetAmount"]
    def_require_columns(institutional, required, "institutional")
    frame = institutional.copy()
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    frame["Ticker"] = frame["Ticker"].map(def_normalize_ticker)
    invalid_dates = int(frame[DATE_COLUMN].isna().sum())
    duplicates = int(frame.duplicated([DATE_COLUMN, "Ticker"], keep=False).sum())
    if invalid_dates or duplicates:
        raise ValueError(
            f"institutional source invalid: invalid_dates={invalid_dates}; "
            f"duplicate Date+Ticker rows={duplicates}"
        )
    for column in required[2:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["TickerInstitutionalNet"] = frame[required[2:]].sum(axis=1, min_count=1)
    sign_count = frame[required[2:]].notna().sum(axis=1)
    sign_balance = frame[required[2:]].gt(0).sum(axis=1).combine(
        frame[required[2:]].lt(0).sum(axis=1), max
    )
    frame["TickerInstitutionalSync"] = (sign_balance / sign_count.replace(0, np.nan)).clip(0.0, 1.0)
    return frame


def def_prepare_margin_short(margin_short: pd.DataFrame) -> pd.DataFrame:
    required = [DATE_COLUMN, "Ticker", "MarginBalanceValue", "ShortBalanceValue"]
    def_require_columns(margin_short, required, "margin_short")
    frame = margin_short.copy()
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    frame["Ticker"] = frame["Ticker"].map(def_normalize_ticker)
    invalid_dates = int(frame[DATE_COLUMN].isna().sum())
    duplicates = int(frame.duplicated([DATE_COLUMN, "Ticker"], keep=False).sum())
    if invalid_dates or duplicates:
        raise ValueError(
            f"margin_short source invalid: invalid_dates={invalid_dates}; "
            f"duplicate Date+Ticker rows={duplicates}"
        )
    for column in required[2:]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.sort_values(["Ticker", DATE_COLUMN]).reset_index(drop=True)
    if "MarginNetFlow" not in frame:
        frame["MarginNetFlow"] = frame.groupby("Ticker", sort=False)["MarginBalanceValue"].diff()
    if "ShortNetFlow" not in frame:
        frame["ShortNetFlow"] = frame.groupby("Ticker", sort=False)["ShortBalanceValue"].diff()
    frame["MarginNetFlow"] = pd.to_numeric(frame["MarginNetFlow"], errors="coerce")
    frame["ShortNetFlow"] = pd.to_numeric(frame["ShortNetFlow"], errors="coerce")
    return frame


def def_prepare_active_etf(active_etf: pd.DataFrame) -> pd.DataFrame:
    required = [DATE_COLUMN, "Ticker", "ETFId", "ActiveETFFlowAmount"]
    def_require_columns(active_etf, required, "active_etf_pcf")
    frame = active_etf.copy()
    frame[DATE_COLUMN] = pd.to_datetime(frame[DATE_COLUMN], errors="coerce")
    frame["Ticker"] = frame["Ticker"].map(def_normalize_ticker)
    frame["ETFId"] = frame["ETFId"].astype(str)
    invalid_dates = int(frame[DATE_COLUMN].isna().sum())
    duplicates = int(frame.duplicated([DATE_COLUMN, "Ticker", "ETFId"], keep=False).sum())
    if invalid_dates or duplicates:
        raise ValueError(
            f"active_etf_pcf source invalid: invalid_dates={invalid_dates}; "
            f"duplicate Date+Ticker+ETFId rows={duplicates}"
        )
    frame["ActiveETFFlowAmount"] = pd.to_numeric(frame["ActiveETFFlowAmount"], errors="coerce")
    return frame


def def_validate_real_data_gate(
    membership: pd.DataFrame,
    price: pd.DataFrame,
    institutional: pd.DataFrame,
    margin_short: pd.DataFrame,
    active_etf: pd.DataFrame,
    main_force: pd.DataFrame,
    config: SystemConfig,
    ledger: list[dict[str, Any]],
) -> None:
    if config.data_mode != "REAL_DATA":
        def_check(
            ledger,
            "GATE001",
            "Real-data activation boundary",
            "PASS",
            "HARD",
            0,
            f"data_mode={config.data_mode}; controlled output cannot be activated as real data.",
        )
        return
    fixture_marker = membership["SourceVersion"].str.contains("FIXTURE|DEMO", case=False, na=False)
    fixture_marker |= membership["PrimaryEconomicIdentity"].str.contains(
        "FIXTURE|DEMO", case=False, na=False
    )
    if fixture_marker.any():
        raise ValueError("REAL_DATA gate rejected fixture/demo membership markers")
    required_tickers = set(membership.loc[membership["FlowEligible"], "Ticker"])
    full_coverage_sources = {
        "price": price,
        "institutional": institutional,
        "margin_short": margin_short,
        "main_force": main_force,
    }
    coverage_findings: list[str] = []
    for source_name, source in full_coverage_sources.items():
        source_tickers = set(source["Ticker"].map(def_normalize_ticker))
        missing = required_tickers - source_tickers
        if missing:
            coverage_findings.append(f"{source_name}:missing={len(missing)}")
    active_etf_tickers = set(active_etf["Ticker"].map(def_normalize_ticker))
    if active_etf.empty or not required_tickers.intersection(active_etf_tickers):
        coverage_findings.append("active_etf_pcf:no eligible holdings")
    unique_dates = price[DATE_COLUMN].nunique()
    minimum_dates = max(config.simulation_min_observations + 1, max(config.role_windows) + 1)
    if unique_dates < minimum_dates:
        coverage_findings.append(f"price:dates={unique_dates}<{minimum_dates}")
    normalized_date = pd.Timestamp(config.normalized_date)
    if normalized_date < price[DATE_COLUMN].min() or normalized_date > price[DATE_COLUMN].max():
        coverage_findings.append("price:normalized_date outside available range")
    def_check(
        ledger,
        "GATE001",
        "Real-data source coverage",
        "PASS" if not coverage_findings else "FAIL",
        "HARD",
        len(coverage_findings),
        "; ".join(coverage_findings)
        if coverage_findings
        else "All required sources and eligible ticker coverage checks passed.",
    )
    if coverage_findings:
        raise ValueError("REAL_DATA gate failed closed: " + "; ".join(coverage_findings))


def def_rolling_robust_z(series: pd.Series, window: int = 60, minimum: int = 20) -> pd.Series:
    def def_last_robust_z(values: np.ndarray) -> float:
        clean = values[np.isfinite(values)]
        if clean.size < minimum:
            return np.nan
        median = float(np.median(clean))
        mad = float(np.median(np.abs(clean - median)))
        scale = 1.4826 * mad
        if not np.isfinite(scale) or scale <= 1e-12:
            return 0.0
        return float((clean[-1] - median) / scale)

    return series.rolling(window=window, min_periods=minimum).apply(def_last_robust_z, raw=True)


def def_compute_dynamic_flow_score(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    dimension_columns = [
        "FlowMomentum",
        "RealVolumeShare",
        "VolumeMomentum",
        "InstitutionalNetThrust",
        "ChipAccumulationHealth",
        "CreditDeviation",
    ]
    for column in dimension_columns:
        result[f"{column}Pct"] = result.groupby(DATE_COLUMN, sort=False)[column].rank(pct=True) * 100.0

    def def_weight_date(group: pd.DataFrame) -> pd.DataFrame:
        group = group.copy()
        dispersions: dict[str, float] = {}
        for column in dimension_columns:
            values = group[column].dropna().to_numpy(dtype=float)
            if values.size < 2:
                dispersions[column] = 0.0
                continue
            median = float(np.median(values))
            dispersions[column] = float(np.median(np.abs(values - median)))
        total = sum(dispersions.values())
        if total <= 1e-12:
            weights = {column: 1.0 / len(dimension_columns) for column in dimension_columns}
        else:
            weights = {column: value / total for column, value in dispersions.items()}
        score = np.zeros(len(group), dtype=float)
        denominator = np.zeros(len(group), dtype=float)
        for column in dimension_columns:
            values = group[f"{column}Pct"].to_numpy(dtype=float)
            valid = np.isfinite(values)
            score[valid] += values[valid] * weights[column]
            denominator[valid] += weights[column]
            group[f"Weight_{column}"] = weights[column]
        group["FlowScore"] = np.divide(score, denominator, out=np.full(len(group), np.nan), where=denominator > 0)
        return group

    scored_dates = [def_weight_date(group) for _, group in result.groupby(DATE_COLUMN, sort=False)]
    return pd.concat(scored_dates, ignore_index=True).sort_values(
        ["GroupId", DATE_COLUMN]
    ).reset_index(drop=True)


def def_compute_group_flow(
    membership: pd.DataFrame,
    price: pd.DataFrame,
    institutional: pd.DataFrame,
    margin_short: pd.DataFrame,
    active_etf: pd.DataFrame,
    main_force: pd.DataFrame,
    group_index: pd.DataFrame,
    config: SystemConfig,
    ledger: list[dict[str, Any]],
) -> pd.DataFrame:
    flow_members = membership.loc[membership["FlowEligible"], GROUP_KEYS + ["Ticker"]]
    price_join = flow_members.merge(
        price[[DATE_COLUMN, "Ticker", "TurnoverValue", "DayTradeTurnover"]], on="Ticker", how="inner"
    )
    turnover = def_group_sum(price_join, [DATE_COLUMN] + GROUP_KEYS, ["TurnoverValue", "DayTradeTurnover"])
    market_turnover = price.groupby(DATE_COLUMN, sort=True)["TurnoverValue"].sum(min_count=1).rename("MarketTurnover")
    market_real = price.assign(
        MarketRealTurnover=(price["TurnoverValue"] - price["DayTradeTurnover"]).where(
            price["TurnoverValue"].notna() & price["DayTradeTurnover"].notna()
        )
    ).groupby(DATE_COLUMN, sort=True)["MarketRealTurnover"].sum(min_count=1)
    turnover = turnover.merge(market_turnover.reset_index(), on=DATE_COLUMN, how="left").merge(
        market_real.reset_index(), on=DATE_COLUMN, how="left"
    )

    institution_join = flow_members.merge(def_prepare_institutional(institutional), on="Ticker", how="inner")
    institution = def_group_sum(
        institution_join,
        [DATE_COLUMN] + GROUP_KEYS,
        ["ForeignNetAmount", "InvestmentTrustNetAmount", "DealerNetAmount"],
    )
    breadth = institution_join.groupby([DATE_COLUMN] + GROUP_KEYS, observed=True)["TickerInstitutionalNet"].agg(
        InstitutionalFlowBreadth=lambda values: values.gt(0).mean(),
        FlowConcentration=lambda values: (
            values.abs().max() / values.abs().sum() if values.abs().sum() > 0 else np.nan
        ),
    ).reset_index()
    sync = institution_join.groupby([DATE_COLUMN] + GROUP_KEYS, observed=True)["TickerInstitutionalSync"].mean(
    ).rename("InstitutionalSyncRate").reset_index()
    institution = institution.merge(breadth, on=[DATE_COLUMN] + GROUP_KEYS, how="left").merge(
        sync, on=[DATE_COLUMN] + GROUP_KEYS, how="left"
    )

    margin_join = flow_members.merge(def_prepare_margin_short(margin_short), on="Ticker", how="inner")
    margin = def_group_sum(
        margin_join,
        [DATE_COLUMN] + GROUP_KEYS,
        ["MarginBalanceValue", "ShortBalanceValue", "MarginNetFlow", "ShortNetFlow"],
    )
    etf_join = flow_members.merge(def_prepare_active_etf(active_etf), on="Ticker", how="inner")
    etf = def_group_sum(etf_join, [DATE_COLUMN] + GROUP_KEYS, ["ActiveETFFlowAmount"])
    main_join = flow_members.merge(main_force, on="Ticker", how="inner")
    main = def_group_sum(
        main_join,
        [DATE_COLUMN] + GROUP_KEYS,
        ["MainForceNetAmount", "BranchConcentration"],
    )
    main_counts = main_join.groupby([DATE_COLUMN] + GROUP_KEYS, observed=True)["BranchConcentration"].count().rename(
        "BranchObservationCount"
    ).reset_index()
    main["BranchConcentration"] = main["BranchConcentration"] / main_counts["BranchObservationCount"].replace(0, np.nan)
    skeleton = group_index[[DATE_COLUMN] + GROUP_KEYS].drop_duplicates()
    frame = skeleton.merge(turnover, on=[DATE_COLUMN] + GROUP_KEYS, how="left")
    frame = frame.merge(institution, on=[DATE_COLUMN] + GROUP_KEYS, how="left")
    frame = frame.merge(margin, on=[DATE_COLUMN] + GROUP_KEYS, how="left")
    frame = frame.merge(etf, on=[DATE_COLUMN] + GROUP_KEYS, how="left")
    frame = frame.merge(main, on=[DATE_COLUMN] + GROUP_KEYS, how="left")
    frame["InstitutionalNetAmount"] = frame[
        ["ForeignNetAmount", "InvestmentTrustNetAmount", "DealerNetAmount"]
    ].sum(axis=1, min_count=1)
    frame["NonDayTradeTurnover"] = (frame["TurnoverValue"] - frame["DayTradeTurnover"]).where(
        frame["TurnoverValue"].notna() & frame["DayTradeTurnover"].notna()
    )
    frame["TurnoverShare"] = frame["TurnoverValue"] / frame["MarketTurnover"].replace(0, np.nan)
    frame["RealVolumeShare"] = frame["NonDayTradeTurnover"] / frame["MarketRealTurnover"].replace(0, np.nan)
    frame["InstitutionalFlowIntensity"] = frame["InstitutionalNetAmount"] / frame[
        "NonDayTradeTurnover"
    ].replace(0, np.nan)
    frame["MarginFlowIntensity"] = frame["MarginNetFlow"] / frame["NonDayTradeTurnover"].replace(0, np.nan)
    frame["ShortFlowIntensity"] = frame["ShortNetFlow"] / frame["NonDayTradeTurnover"].replace(0, np.nan)
    frame["ActiveETFFlowIntensity"] = frame["ActiveETFFlowAmount"] / frame[
        "NonDayTradeTurnover"
    ].replace(0, np.nan)
    frame["MainForceFlowIntensity"] = frame["MainForceNetAmount"] / frame[
        "NonDayTradeTurnover"
    ].replace(0, np.nan)
    frame = frame.sort_values(["GroupId", DATE_COLUMN]).reset_index(drop=True)
    for component in FLOW_COMPONENTS:
        for window in config.rolling_windows:
            frame[f"{component}_{window}D"] = frame.groupby("GroupId", sort=False)[component].transform(
                lambda values, size=window: values.rolling(size, min_periods=1).sum()
            )
        frame[f"{component}_YTD"] = frame.groupby(
            ["GroupId", frame[DATE_COLUMN].dt.year], sort=False
        )[component].cumsum()
        normalized_mask = frame[DATE_COLUMN] >= pd.Timestamp(config.normalized_date)
        normalized_values = frame[component].where(normalized_mask)
        frame[f"{component}_SinceNormalized"] = normalized_values.groupby(frame["GroupId"], sort=False).cumsum()
    date_count = int(frame[DATE_COLUMN].nunique())
    dynamic_medium = int(np.clip(round(date_count * 0.09), 15, 30))
    dynamic_long = int(np.clip(round(date_count * 0.27), 45, 90))
    momentum_raw = frame.groupby("GroupId", sort=False)["InstitutionalNetAmount"].transform(
        lambda values: values.rolling(dynamic_medium, min_periods=max(5, dynamic_medium // 2)).sum()
    ) + frame.groupby("GroupId", sort=False)["ActiveETFFlowAmount"].transform(
        lambda values: values.rolling(dynamic_medium, min_periods=max(5, dynamic_medium // 2)).sum()
    )
    credit_raw = frame.groupby("GroupId", sort=False)["MarginNetFlow"].transform(
        lambda values: values.rolling(dynamic_medium, min_periods=max(5, dynamic_medium // 2)).sum()
    ) - frame.groupby("GroupId", sort=False)["ShortNetFlow"].transform(
        lambda values: values.rolling(dynamic_medium, min_periods=max(5, dynamic_medium // 2)).sum()
    )
    frame["FlowMomentum"] = momentum_raw.groupby(frame["GroupId"], sort=False).transform(def_rolling_robust_z)
    frame["CreditDeviation"] = credit_raw.groupby(frame["GroupId"], sort=False).transform(def_rolling_robust_z)
    frame["VolumeMomentum"] = frame.groupby("GroupId", sort=False)["RealVolumeShare"].transform(
        lambda values: def_rolling_robust_z(values, window=dynamic_long, minimum=max(15, dynamic_long // 3))
    )
    frame["InstitutionalNetThrust"] = frame.groupby("GroupId", sort=False)["InstitutionalFlowIntensity"].transform(
        lambda values: def_rolling_robust_z(values, window=dynamic_long, minimum=max(15, dynamic_long // 3))
    )
    frame["ChipAccumulationHealth"] = (
        0.45 * frame["InstitutionalNetThrust"].clip(-4, 4)
        + 0.25 * frame["InstitutionalSyncRate"].fillna(0)
        + 0.20 * frame["InstitutionalFlowBreadth"].fillna(0)
        + 0.10 * frame["BranchConcentration"].fillna(0)
    )
    frame = def_compute_dynamic_flow_score(frame)
    missing_days = int(frame["InstitutionalNetAmount"].isna().sum())
    def_check(
        ledger,
        "FLOW001",
        "Missing daily flow retained",
        "PASS",
        "HARD",
        missing_days,
        "Missing institution, margin, short and ETF flow values are not forward-filled.",
    )
    def_check(
        ledger,
        "FLOW002",
        "Rolling and cumulative windows",
        "PASS",
        "INFO",
        0,
        f"windows={list(config.rolling_windows)}; plus YTD and SinceNormalized",
    )
    def_check(
        ledger,
        "FLOW003",
        "Dynamic real-volume and chip metrics",
        "PASS",
        "INFO",
        0,
        f"dynamic_medium={dynamic_medium}; dynamic_long={dynamic_long}; RVS excludes day-trade turnover; VMOM/thrust/health enabled",
    )
    return frame


def def_safe_corr(left: pd.Series, right: pd.Series) -> float:
    pair = pd.concat([left, right], axis=1).dropna()
    if len(pair) < 8 or pair.iloc[:, 0].std(ddof=0) <= 1e-12 or pair.iloc[:, 1].std(ddof=0) <= 1e-12:
        return np.nan
    return float(pair.iloc[:, 0].corr(pair.iloc[:, 1]))


def def_compute_member_roles(
    membership: pd.DataFrame,
    price: pd.DataFrame,
    group_index: pd.DataFrame,
    config: SystemConfig,
    ledger: list[dict[str, Any]],
) -> pd.DataFrame:
    output: list[dict[str, Any]] = []
    latest_price = price.sort_values(DATE_COLUMN).groupby("Ticker", sort=False).tail(max(config.role_windows))
    group_returns = group_index[[DATE_COLUMN, "GroupId", "GroupReturn"]]
    for group_id, members in membership.groupby("GroupId", sort=True):
        group_series = group_returns.loc[group_returns["GroupId"] == group_id, [DATE_COLUMN, "GroupReturn"]]
        metrics: list[dict[str, Any]] = []
        for member in members.itertuples(index=False):
            ticker_series = price.loc[price["Ticker"] == member.Ticker, [DATE_COLUMN, "Return", "TurnoverValue"]]
            pair = group_series.merge(ticker_series, on=DATE_COLUMN, how="inner").sort_values(DATE_COLUMN)
            lead_scores: list[float] = []
            lag_scores: list[float] = []
            same_scores: list[float] = []
            for window in config.role_windows:
                sample = pair.tail(window)
                same_scores.append(def_safe_corr(sample["Return"], sample["GroupReturn"]))
                lead_scores.append(def_safe_corr(sample["Return"], sample["GroupReturn"].shift(-1)))
                lag_scores.append(def_safe_corr(sample["Return"], sample["GroupReturn"].shift(1)))
            clean_lead = [value for value in lead_scores if np.isfinite(value)]
            clean_lag = [value for value in lag_scores if np.isfinite(value)]
            clean_same = [value for value in same_scores if np.isfinite(value)]
            recent = latest_price.loc[latest_price["Ticker"] == member.Ticker]
            recent_return = (
                float(recent["Adj_Close"].iloc[-1] / recent["Adj_Close"].iloc[0] - 1.0) if len(recent) >= 2 else np.nan
            )
            recent_turnover = float(recent["TurnoverValue"].median()) if recent["TurnoverValue"].notna().any() else np.nan
            metrics.append(
                {
                    "GroupId": group_id,
                    "GroupName": member.GroupName,
                    "Ticker": member.Ticker,
                    "Name": getattr(member, "Name", member.Ticker),
                    "Market": getattr(
                        member,
                        "Market",
                        "TWSE" if str(member.Ticker).endswith(".TW") else (
                            "TPEX" if str(member.Ticker).endswith(".TWO") else "REVIEW"
                        ),
                    ),
                    "PrimaryEconomicIdentity": member.PrimaryEconomicIdentity,
                    "IndexEligible": bool(member.IndexEligible),
                    "FlowEligible": bool(getattr(member, "FlowEligible", member.IndexEligible)),
                    "DisplayOnly": bool(getattr(member, "DisplayOnly", not member.IndexEligible)),
                    "SourceVersion": getattr(member, "SourceVersion", "UNSPECIFIED"),
                    "SameGroupScore": float(np.mean(clean_same)) if clean_same else np.nan,
                    "LeadScore": float(np.mean(clean_lead)) if clean_lead else np.nan,
                    "LagScore": float(np.mean(clean_lag)) if clean_lag else np.nan,
                    "LeadStable": bool(len(clean_lead) == len(config.role_windows) and min(clean_lead) > 0),
                    "LagStable": bool(len(clean_lag) == len(config.role_windows) and min(clean_lag) > 0),
                    "RecentReturn": recent_return,
                    "RecentTurnover": recent_turnover,
                }
            )
        group_frame = pd.DataFrame(metrics)
        group_frame["LeadAdvantage"] = group_frame["LeadScore"] - group_frame["LagScore"]
        group_frame["LagAdvantage"] = group_frame["LagScore"] - group_frame["LeadScore"]
        for column in ["LeadAdvantage", "LagAdvantage"]:
            values = group_frame[column].dropna().to_numpy(dtype=float)
            median = float(np.median(values)) if values.size else np.nan
            mad = float(np.median(np.abs(values - median))) if values.size else np.nan
            group_frame[f"Threshold_{column}"] = median + mad if np.isfinite(median) and np.isfinite(mad) else np.nan
        leader_mask = (
            group_frame["LeadStable"]
            & (group_frame["LeadAdvantage"] > group_frame["Threshold_LeadAdvantage"])
            & (group_frame["LeadScore"] > 0)
        )
        lagger_mask = (
            group_frame["LagStable"]
            & (group_frame["LagAdvantage"] > group_frame["Threshold_LagAdvantage"])
            & (group_frame["LagScore"] > 0)
        )
        group_frame["CompositeRole"] = "PEER"
        group_frame.loc[lagger_mask, "CompositeRole"] = "LAGGER"
        group_frame.loc[leader_mask, "CompositeRole"] = "LEADER"
        unresolved = group_frame[["LeadScore", "LagScore", "SameGroupScore"]].isna().all(axis=1)
        group_frame.loc[unresolved, "CompositeRole"] = "UNRESOLVED"
        confirmed_leader = bool(leader_mask.any())
        group_frame["GroupLeaderStatus"] = "CONFIRMED" if confirmed_leader else "NO_CONFIRMED_LEADER"
        group_frame["CompositeMembershipStatus"] = np.where(
            group_frame["IndexEligible"], "PASS", "DISPLAY_ONLY"
        )
        group_frame["ClassificationRoleCode"] = group_frame["CompositeRole"].map(
            {
                "LEADER": "A_LEADER",
                "PEER": "B_PEER",
                "LAGGER": "C_LAGGARD_EXCEPTION",
                "UNRESOLVED": "UNRESOLVED",
            }
        ).fillna("UNRESOLVED")
        group_frame["RoleStatus"] = np.select(
            [
                group_frame["CompositeRole"].eq("LAGGER"),
                group_frame["CompositeRole"].eq("UNRESOLVED"),
            ],
            ["dormant", "review"],
            default="active",
        )
        group_frame["IncludeInGroupIndex"] = (
            group_frame["IndexEligible"] & ~group_frame["CompositeRole"].eq("LAGGER")
        )
        group_frame["RoleEffectiveCycle"] = "NEXT_REBALANCE"
        group_frame["RoleEvidenceWindows"] = "/".join(f"{window}D" for window in config.role_windows)
        turnover_rank = group_frame["RecentTurnover"].rank(pct=True)
        return_rank = group_frame["RecentReturn"].rank(pct=True)
        group_frame["HotScore"] = (turnover_rank + return_rank) / 2.0 * 100.0
        output.extend(group_frame.to_dict(orient="records"))
    roles = pd.DataFrame(output)
    no_leader_count = int(
        roles.loc[roles["GroupLeaderStatus"] == "NO_CONFIRMED_LEADER", "GroupId"].nunique()
    )
    def_check(
        ledger,
        "ROLE001",
        "Leader is evidence-based and never forced",
        "PASS",
        "REVIEW",
        no_leader_count,
        "Groups without stable lead evidence emit NO_CONFIRMED_LEADER.",
    )
    lagger_contract_failure = (
        roles["CompositeRole"].eq("LAGGER")
        & (
            ~roles["ClassificationRoleCode"].eq("C_LAGGARD_EXCEPTION")
            | ~roles["RoleStatus"].eq("dormant")
            | roles["IncludeInGroupIndex"]
        )
    )
    role_contract_failures = int(lagger_contract_failure.sum())
    def_check(
        ledger,
        "ROLE002",
        "Classification role and next-rebalance policy",
        "PASS" if role_contract_failures == 0 else "FAIL",
        "HARD",
        role_contract_failures,
        "A/B/C role codes are evidence-based; C is dormant and excluded from the next rebalance.",
    )
    roles["AsOfDate"] = price[DATE_COLUMN].max()
    return roles


def def_rank_correlation(left: np.ndarray, right: np.ndarray) -> float:
    if len(left) < 3:
        return np.nan
    left_rank = pd.Series(left).rank(method="average").to_numpy(dtype=float)
    right_rank = pd.Series(right).rank(method="average").to_numpy(dtype=float)
    if np.std(left_rank) <= 1e-12 or np.std(right_rank) <= 1e-12:
        return np.nan
    return float(np.corrcoef(left_rank, right_rank)[0, 1])


def def_compute_flow_simulation(
    group_index: pd.DataFrame,
    group_flow: pd.DataFrame,
    config: SystemConfig,
    ledger: list[dict[str, Any]],
) -> pd.DataFrame:
    panel = group_index[[DATE_COLUMN] + GROUP_KEYS + ["GroupReturn", "GroupIndex"]].merge(
        group_flow[[DATE_COLUMN] + GROUP_KEYS + SIMULATION_FEATURES],
        on=[DATE_COLUMN] + GROUP_KEYS,
        how="inner",
    )
    panel = panel.sort_values(["GroupId", DATE_COLUMN]).reset_index(drop=True)
    panel["TargetNextReturn"] = panel.groupby("GroupId", sort=False)["GroupReturn"].shift(-1)
    rows: list[dict[str, Any]] = []
    for group_id, group in panel.groupby("GroupId", sort=True):
        sample = group.dropna(subset=SIMULATION_FEATURES + ["TargetNextReturn"]).copy()
        group_name = str(group["GroupName"].iloc[0])
        if len(sample) < config.simulation_min_observations:
            scenarios = config.scenarios or (
                {"scenario_id": "BASELINE", "label": "Baseline", "standardized_feature_shocks": {}},
            )
            for scenario in scenarios:
                rows.append(
                    {
                        "GroupId": group_id,
                        "GroupName": group_name,
                        "ScenarioId": str(scenario.get("scenario_id", "SCENARIO")),
                        "ScenarioLabel": str(
                            scenario.get("label", scenario.get("scenario_id", "Scenario"))
                        ),
                        "CalibrationStatus": "UNCALIBRATED_INSUFFICIENT_OBSERVATIONS",
                        "Observations": int(len(sample)),
                        "OOSObservations": 0,
                        "OOSRankIC": np.nan,
                        "OOSHitRate": np.nan,
                        "DynamicICThreshold": np.nan,
                        "DynamicHitThreshold": np.nan,
                        "PredictedDailyReturnShift": np.nan,
                        "SimulatedIndexAtHorizon": np.nan,
                        "Coefficients": "{}",
                    }
                )
            continue
        split = max(1, min(len(sample) - 1, int(len(sample) * config.simulation_train_fraction)))
        train = sample.iloc[:split]
        test = sample.iloc[split:]
        x_train = train[SIMULATION_FEATURES].to_numpy(dtype=float)
        y_train = train["TargetNextReturn"].to_numpy(dtype=float)
        mean = x_train.mean(axis=0)
        scale = x_train.std(axis=0)
        scale = np.where(scale <= 1e-12, 1.0, scale)
        z_train = (x_train - mean) / scale
        design = np.column_stack([np.ones(len(z_train)), z_train])
        penalty = np.eye(design.shape[1]) * config.simulation_ridge_alpha
        penalty[0, 0] = 0.0
        coefficients = np.linalg.pinv(design.T @ design + penalty) @ design.T @ y_train
        x_test = test[SIMULATION_FEATURES].to_numpy(dtype=float)
        z_test = (x_test - mean) / scale
        prediction = coefficients[0] + z_test @ coefficients[1:]
        actual = test["TargetNextReturn"].to_numpy(dtype=float)
        rank_ic = def_rank_correlation(prediction, actual)
        hit_rate = float(np.mean(np.sign(prediction) == np.sign(actual))) if len(actual) else np.nan
        ic_threshold = 1.96 / math.sqrt(max(len(actual), 1))
        hit_threshold = 0.5 + 0.5 / math.sqrt(max(len(actual), 1))
        valid = bool(
            len(actual) >= 20
            and (
                (np.isfinite(rank_ic) and rank_ic > ic_threshold)
                or (np.isfinite(hit_rate) and hit_rate > hit_threshold)
            )
        )
        calibration_status = "CALIBRATED_OOS_PASS" if valid else "NOT_VALID_OOS_GATE"
        coefficient_map = {feature: float(value) for feature, value in zip(SIMULATION_FEATURES, coefficients[1:])}
        scenarios = config.scenarios or (
            {"scenario_id": "BASELINE", "label": "Baseline", "standardized_feature_shocks": {}},
        )
        for scenario in scenarios:
            shocks = scenario.get("standardized_feature_shocks", {})
            shock_vector = np.array([float(shocks.get(feature, 0.0)) for feature in SIMULATION_FEATURES])
            return_shift = float(shock_vector @ coefficients[1:])
            horizon_value = config.index_base_value * (1.0 + return_shift) ** config.simulation_horizon_days
            rows.append(
                {
                    "GroupId": group_id,
                    "GroupName": group_name,
                    "ScenarioId": str(scenario.get("scenario_id", "SCENARIO")),
                    "ScenarioLabel": str(scenario.get("label", scenario.get("scenario_id", "Scenario"))),
                    "CalibrationStatus": calibration_status,
                    "Observations": int(len(sample)),
                    "OOSObservations": int(len(actual)),
                    "OOSRankIC": rank_ic,
                    "OOSHitRate": hit_rate,
                    "DynamicICThreshold": ic_threshold,
                    "DynamicHitThreshold": hit_threshold,
                    "PredictedDailyReturnShift": return_shift,
                    "SimulatedIndexAtHorizon": horizon_value,
                    "Coefficients": json.dumps(coefficient_map, ensure_ascii=False, sort_keys=True),
                }
            )
    simulation = pd.DataFrame(rows)
    calibrated = int(
        simulation.loc[simulation["ScenarioId"] == "BASELINE", "CalibrationStatus"].eq("CALIBRATED_OOS_PASS").sum()
    )
    total = int(simulation.loc[simulation["ScenarioId"] == "BASELINE", "GroupId"].nunique())
    def_check(
        ledger,
        "SIM001",
        "Flow Simulation OOS validation",
        "PASS" if calibrated > 0 else "REVIEW",
        "REVIEW",
        total - calibrated,
        f"calibrated_groups={calibrated}/{total}; thresholds are sample-size-derived.",
    )
    return simulation


def def_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: def_json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [def_json_value(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.strftime("%Y-%m-%d")
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if pd.isna(value):
        return None
    return value


def def_records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [{key: def_json_value(value) for key, value in row.items()} for row in frame.to_dict(orient="records")]


def def_write_dual_table(frame: pd.DataFrame, base_path: Path) -> dict[str, Any]:
    base_path.parent.mkdir(parents=True, exist_ok=True)
    export = frame.copy()
    for column in export.columns:
        if pd.api.types.is_datetime64_any_dtype(export[column]):
            export[column] = export[column].dt.strftime("%Y/%m/%d")
    csv_path = base_path.with_suffix(".csv")
    parquet_path = base_path.with_suffix(".parquet")
    export.to_csv(csv_path, index=False, encoding="utf-8-sig")
    parquet_status = "PASS"
    parquet_error = None
    try:
        export.to_parquet(parquet_path, index=False)
    except Exception as exc:
        parquet_status = "REVIEW_OPTIONAL_DEPENDENCY"
        parquet_error = f"{type(exc).__name__}: {exc}"
    return {
        "csv": str(csv_path),
        "parquet": str(parquet_path) if parquet_status == "PASS" else None,
        "parquet_status": parquet_status,
        "parquet_error": parquet_error,
        "rows": int(len(frame)),
    }


def def_hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def def_build_payload(
    membership: pd.DataFrame,
    group_index: pd.DataFrame,
    group_flow: pd.DataFrame,
    roles: pd.DataFrame,
    simulation: pd.DataFrame,
    group_validation: pd.DataFrame,
    backtest_daily: pd.DataFrame,
    backtest_summary: pd.DataFrame,
    dynamic_parameters: dict[str, Any],
    candidate_groups: pd.DataFrame,
    candidate_membership: pd.DataFrame,
    candidate_quality: dict[str, Any],
    version_chain: pd.DataFrame,
    rotation_snapshot: pd.DataFrame,
    rotation_quality: dict[str, Any],
    vdf_contract: dict[str, Any],
    market_intelligence_registry: dict[str, Any],
    method_thresholds: dict[str, Any],
    ledger: list[dict[str, Any]],
    config: SystemConfig,
) -> dict[str, Any]:
    dates = sorted(group_index[DATE_COLUMN].dropna().unique())[-config.ui_max_dates :]
    ui_index = group_index.loc[group_index[DATE_COLUMN].isin(dates)].copy()
    ui_flow = group_flow.loc[group_flow[DATE_COLUMN].isin(dates)].copy()
    group_summary = membership.groupby(GROUP_KEYS, observed=True).agg(
        ConstituentCount=("Ticker", "nunique"),
        IndexEligibleCount=("IndexEligible", "sum"),
        UITier=("UITier", "first"),
    ).reset_index()
    latest_flow = ui_flow.sort_values(DATE_COLUMN).groupby("GroupId", sort=False).tail(1)
    group_summary = group_summary.merge(
        latest_flow[[
            "GroupId",
            "FlowScore",
            "InstitutionalNetAmount",
            "TurnoverShare",
            "RealVolumeShare",
            "VolumeMomentum",
            "InstitutionalNetThrust",
            "ChipAccumulationHealth",
        ]],
        on="GroupId",
        how="left",
    )
    group_summary = group_summary.merge(
        group_validation[["GroupId", "ValidationStatus", "PCAAbsorption", "AverageCorrelation", "Coverage"]],
        on="GroupId",
        how="left",
    )
    return {
        "metadata": {
            "systemId": config.system_id,
            "version": config.version,
            "generatedAt": def_utc_now(),
            "dataStatus": config.data_mode,
            "expectedGroupCount": config.expected_group_count,
            "actualGroupCount": int(membership["GroupId"].nunique()),
            "normalizedDate": config.normalized_date,
            "indexBaseValue": config.index_base_value,
            "indexWeightMethod": config.index_weight_method,
            "rollingWindows": list(config.rolling_windows),
            "roleWindows": list(config.role_windows),
            "flowScale": config.flow_scale,
            "dynamicParameters": dynamic_parameters,
            "activationStatus": "FIXTURE_REGRESSION_ONLY_NOT_ACTIVATABLE",
            "candidateActivationStatus": "BLOCKED_CANDIDATE_49_NO_VALIDATED_INDEX",
            "rotationActivationStatus": "BLOCKED_T2_T3_PENDING_VDF_M3",
            "rotationSnapshotAsOf": rotation_quality["SnapshotAsOf"],
            "rotationRegistryDeclaredCount": rotation_quality["RegistryDeclaredGroupCount"],
            "rotationTrackedCount": rotation_quality["TrackedGroupCount"],
            "realDataRuntimeExecuted": False,
            "classificationPolicy": {
                "ssotMutation": "APPEND_ONLY_ERRATA",
                "roleAssignment": "EVIDENCE_BASED_NOT_FORCED",
                "laggardStatus": "DORMANT",
                "laggardIndexPolicy": "EXCLUDE_FROM_NEXT_REBALANCE",
                "effectiveCycle": "NEXT_REBALANCE",
                "humanXDecision": "APPEND_ONLY_EXCLUDE_PROPOSAL_OR_KEEP",
                "canonicalDelete": "PROHIBITED_IN_UI",
            },
        },
        "groups": def_records(group_summary),
        "groupIndex": def_records(ui_index),
        "groupFlow": def_records(ui_flow),
        "memberRoles": def_records(roles),
        "simulation": def_records(simulation),
        "groupValidation": def_records(group_validation),
        "backtestDaily": def_records(backtest_daily),
        "backtestSummary": def_records(backtest_summary),
        "candidateGroups": def_records(candidate_groups),
        "candidateMembership": def_records(candidate_membership),
        "candidateQuality": candidate_quality,
        "versionChain": def_records(version_chain),
        "rotationSnapshot": def_records(rotation_snapshot),
        "rotationQuality": rotation_quality,
        "vdfContract": vdf_contract,
        "marketIntelligenceRegistry": market_intelligence_registry,
        "methodThresholds": method_thresholds,
        "validation": [{key: def_json_value(value) for key, value in row.items()} for row in ledger],
    }


def def_run_system(config_path: Path) -> dict[str, Any]:
    config_path = config_path.resolve()
    project_root = config_path.parent.parent
    config = def_load_config(config_path)
    thresholds_path = def_resolve_path(project_root, config.method_thresholds_file)
    method_thresholds = json.loads(thresholds_path.read_text(encoding="utf-8"))
    threshold_map = {row["id"]: row["value"] for row in method_thresholds["controls"]}
    ledger: list[dict[str, Any]] = []
    inputs = {
        name: def_read_table(def_resolve_path(project_root, configured_path))
        for name, configured_path in config.input_files.items()
    }
    membership = def_prepare_membership(inputs["membership"], config, ledger)
    price = def_prepare_price(inputs["price"], config, ledger)
    institutional = def_prepare_institutional(inputs["institutional"])
    margin_short = def_prepare_margin_short(inputs["margin_short"])
    active_etf = def_prepare_active_etf(inputs["active_etf_pcf"])
    main_force = def_prepare_main_force(inputs["main_force"])
    def_validate_real_data_gate(
        membership,
        price,
        institutional,
        margin_short,
        active_etf,
        main_force,
        config,
        ledger,
    )
    group_index = def_compute_group_index(membership, price, config, ledger)
    group_flow = def_compute_group_flow(
        membership,
        price,
        institutional,
        margin_short,
        active_etf,
        main_force,
        group_index,
        config,
        ledger,
    )
    roles = def_compute_member_roles(membership, price, group_index, config, ledger)
    dynamic_parameters = def_derive_dynamic_parameters(price)
    dynamic_parameters["riskFreeRate"] = float(threshold_map["C-14"])
    dynamic_parameters["riskFreeEvidenceTier"] = str(method_thresholds["evidence_tier"])
    roles, group_validation = def_compute_dynamic_classification(
        membership,
        price,
        institutional,
        main_force,
        roles,
        dynamic_parameters,
        ledger,
    )
    simulation = def_compute_flow_simulation(group_index, group_flow, config, ledger)
    backtest_daily, backtest_summary = def_run_rotation_backtest(
        group_index,
        group_flow,
        dynamic_parameters,
        ledger,
    )
    candidate_source_path = def_resolve_path(project_root, config.candidate_source_file)
    candidate_group_source, candidate_membership, candidate_quality = def_write_flowrot_candidate(
        candidate_source_path,
        project_root / "data" / "input",
        project_root / "evidence",
    )
    candidate_groups = def_validate_candidate_groups(
        candidate_group_source,
        attention_min=float(threshold_map["C-03"]),
        leadership_min=float(threshold_map["C-04"]),
    )
    version_chain = def_build_candidate_version_chain(
        candidate_groups,
        asof_date=str(method_thresholds["asof"]),
        source_ref=candidate_source_path.name,
        parameters_digest=def_hash_file(thresholds_path),
    )
    rotation_source_path = def_resolve_path(project_root, config.rotation_snapshot_source_file)
    if not rotation_source_path.exists():
        raise FileNotFoundError(f"Rotation source attachment not found: {rotation_source_path}")
    rotation_snapshot, rotation_quality = def_build_rotation_snapshot(candidate_groups)
    rotation_source_validation = def_validate_rotation_source_contract(rotation_source_path, rotation_snapshot)
    rotation_quality.update(rotation_source_validation)
    rotation_quality["SourceFile"] = rotation_source_path.name
    rotation_quality["SourceSha256"] = def_hash_file(rotation_source_path)
    rotation_quality["SourceDatePolicy"] = "HISTORICAL_2026_07_18_NOT_CURRENT_STATE"
    rotation_quality["Declared29RegistryPolicy"] = "COUNT_ONLY_NO_REGISTRY_ROWS_MATERIALIZED"
    def_check(
        ledger,
        "ROTATION-01",
        "2026-07-18 five-state snapshot count contract",
        "PASS" if rotation_quality["StateCountsMatch"] else "FAIL",
        "HARD",
        0 if rotation_quality["StateCountsMatch"] else 1,
        f"tracked={rotation_quality['TrackedGroupCount']}; states={rotation_quality['StateCounts']}",
    )
    def_check(
        ledger,
        "ROTATION-02",
        "Historical-to-candidate taxonomy mapping",
        "REVIEW" if rotation_quality["UnmappedGroups"] else "PASS",
        "REVIEW",
        len(rotation_quality["UnmappedGroups"]),
        "unmapped=" + (" | ".join(rotation_quality["UnmappedGroups"]) or "none"),
    )
    def_check(
        ledger,
        "ROTATION-03",
        "Evidence boundary and M3 truth gate",
        "PASS",
        "HARD",
        0,
        "all rows remain SOURCE_REPORTED_T2_T3_UNVERIFIED; index use prohibited",
    )
    vdf_source_path = def_resolve_path(project_root, config.vdf_contract_source_file)
    vdf_contract = def_extract_vdf_contract_summary(vdf_source_path)
    vdf_contract["SourceSha256"] = def_hash_file(vdf_source_path)
    def_check(
        ledger,
        "VDF-CONTRACT-01",
        "VDF control-panel contract extraction",
        "PASS",
        "HARD",
        0,
        f"TWSE={vdf_contract['DeclaredTWSE']}; TPEX={vdf_contract['DeclaredTPEX']}; execution=0",
    )
    registry_path = def_resolve_path(project_root, config.market_intelligence_registry_file)
    market_intelligence_registry = json.loads(registry_path.read_text(encoding="utf-8"))
    category_total = sum(int(row["items"]) for row in market_intelligence_registry["categories"])
    if category_total != int(market_intelligence_registry["declared_item_count"]):
        raise ValueError(
            f"Market intelligence registry item mismatch: categories={category_total}; "
            f"declared={market_intelligence_registry['declared_item_count']}"
        )
    market_intelligence_registry["category_count"] = len(market_intelligence_registry["categories"])
    market_intelligence_registry["item_count"] = category_total
    market_intelligence_registry["source_file"] = registry_path.name
    market_intelligence_registry["source_sha256"] = def_hash_file(registry_path)
    def_check(
        ledger,
        "MI-REGISTRY-01",
        "Market intelligence registry aggregate contract",
        "PASS",
        "HARD",
        0,
        f"categories={market_intelligence_registry['category_count']}; items={category_total}",
    )
    attention_example_stock = pd.DataFrame(
        [
            {"Date": "2026-08-18", "Ticker": "2330.TW", "TurnoverValue": 600.0, "DayTradeTurnover": 88.0, "AssetType": "EQUITY", "DayTradeEvidenceTier": "ESTIMATED"},
            {"Date": "2026-08-18", "Ticker": "9999.TW", "TurnoverValue": 41.02, "DayTradeTurnover": 10.0, "AssetType": "EQUITY", "DayTradeEvidenceTier": "ESTIMATED"},
        ]
    )
    attention_example_market = pd.DataFrame(
        [
            {"Date": "2026-08-18", "Market": "TWSE", "GrossTurnoverValue": 4128.0, "DayTradeTurnoverValue": 1200.0},
            {"Date": "2026-08-18", "Market": "TPEX", "GrossTurnoverValue": 892.0, "DayTradeTurnoverValue": 206.0},
        ]
    )
    attention_example, attention_denominator_example = def_compute_attention_share(
        attention_example_stock,
        attention_example_market,
    )
    attention_example["EvidenceInterpretation"] = "ESTIMATED_EXAMPLE_NOT_RUNTIME"
    attention_denominator_example["EvidenceInterpretation"] = "ESTIMATED_EXAMPLE_NOT_RUNTIME"
    outputs: dict[str, Any] = {}
    outputs["group_index"] = def_write_dual_table(
        group_index, def_resolve_path(project_root, config.output_files["group_index"])
    )
    outputs["group_flow"] = def_write_dual_table(
        group_flow, def_resolve_path(project_root, config.output_files["group_flow"])
    )
    outputs["member_roles"] = def_write_dual_table(
        roles, def_resolve_path(project_root, config.output_files["member_roles"])
    )
    outputs["simulation"] = def_write_dual_table(
        simulation, def_resolve_path(project_root, config.output_files["simulation"])
    )
    outputs["group_validation"] = def_write_dual_table(
        group_validation, def_resolve_path(project_root, config.output_files["group_validation"])
    )
    outputs["backtest_daily"] = def_write_dual_table(
        backtest_daily, def_resolve_path(project_root, config.output_files["backtest_daily"])
    )
    outputs["backtest_summary"] = def_write_dual_table(
        backtest_summary, def_resolve_path(project_root, config.output_files["backtest_summary"])
    )
    outputs["candidate_groups"] = def_write_dual_table(
        candidate_groups, def_resolve_path(project_root, config.output_files["candidate_groups"])
    )
    outputs["candidate_membership"] = def_write_dual_table(
        candidate_membership, def_resolve_path(project_root, config.output_files["candidate_membership"])
    )
    outputs["version_chain"] = def_write_dual_table(
        version_chain, def_resolve_path(project_root, config.output_files["version_chain"])
    )
    outputs["rotation_snapshots"] = def_append_rotation_snapshot(
        rotation_snapshot,
        def_resolve_path(project_root, config.output_files["rotation_snapshots"]),
    )
    def_write_rotation_quality(rotation_quality, project_root / "evidence" / "rotation_snapshot_quality.json")
    (project_root / "evidence" / "vdf_contract_summary.json").write_text(
        json.dumps(vdf_contract, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    outputs["attention_share_example"] = def_write_dual_table(
        attention_example, project_root / "evidence" / "attention_share_example"
    )
    outputs["attention_denominator_example"] = def_write_dual_table(
        attention_denominator_example, project_root / "evidence" / "attention_denominator_example"
    )
    payload = def_build_payload(
        membership,
        group_index,
        group_flow,
        roles,
        simulation,
        group_validation,
        backtest_daily,
        backtest_summary,
        dynamic_parameters,
        candidate_groups,
        candidate_membership,
        candidate_quality,
        version_chain,
        rotation_snapshot,
        rotation_quality,
        vdf_contract,
        market_intelligence_registry,
        method_thresholds,
        ledger,
        config,
    )
    dashboard_path = def_resolve_path(project_root, config.output_files["dashboard"])
    dashboard_path.parent.mkdir(parents=True, exist_ok=True)
    dashboard_path.write_text(def_build_dashboard_html(payload), encoding="utf-8")
    outputs["dashboard"] = {"path": str(dashboard_path), "sha256": def_hash_file(dashboard_path)}
    hard_failures = sum(row["Status"] == "FAIL" and row["Severity"] == "HARD" for row in ledger)
    review_items = sum(row["Status"] in {"REVIEW", "WARN"} for row in ledger)
    if hard_failures:
        gate = "FAIL_CLOSED"
    elif config.data_mode == "REAL_DATA":
        gate = "READY_FOR_MANUAL_ACTIVATION_REVIEW"
    else:
        gate = "ROTATION_T2_T3_REVIEW_CANDIDATE_49_BLOCKED_FIXTURE_REGRESSION_PASS"
    summary = {
        "SystemId": config.system_id,
        "Version": config.version,
        "GeneratedAt": def_utc_now(),
        "Gate": gate,
        "DataMode": config.data_mode,
        "GroupCount": int(membership["GroupId"].nunique()),
        "MembershipRows": int(len(membership)),
        "PriceRows": int(len(price)),
        "GroupIndexRows": int(len(group_index)),
        "GroupFlowRows": int(len(group_flow)),
        "RoleRows": int(len(roles)),
        "SimulationRows": int(len(simulation)),
        "GroupValidationRows": int(len(group_validation)),
        "BacktestRows": int(len(backtest_daily)),
        "CandidateGroupCount": int(len(candidate_groups)),
        "CandidateMembershipRows": int(len(candidate_membership)),
        "CandidateDistinctTickers": int(candidate_membership["TickerCode"].nunique()),
        "CandidateIndexEligible": int(candidate_groups["ValidationStatus"].eq("PASS").sum()),
        "RotationRegistryDeclaredGroupCount": int(rotation_quality["RegistryDeclaredGroupCount"]),
        "RotationTrackedGroupCount": int(rotation_quality["TrackedGroupCount"]),
        "RotationStateCounts": rotation_quality["StateCounts"],
        "RotationM3T1Count": 0,
        "RotationIndexEligible": 0,
        "VDFContractFetcherExecution": int(vdf_contract["FetcherExecution"]),
        "MarketIntelligenceRegistryItems": int(category_total),
        "HardFailures": int(hard_failures),
        "ReviewItems": int(review_items),
        "CanonicalMutation": 0,
        "NetworkExecution": 0,
        "OrderExecution": 0,
        "RealDataRuntimeExecuted": config.data_mode == "REAL_DATA",
        "Outputs": outputs,
    }
    summary_path = def_resolve_path(project_root, config.output_files["run_summary"])
    ledger_path = def_resolve_path(project_root, config.output_files["validation_ledger"])
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    pd.DataFrame(ledger).to_csv(ledger_path, index=False, encoding="utf-8-sig")
    return summary


def def_parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VIA Taiwan Stock Group Classification And Flow Simulation System")
    parser.add_argument("command", choices=["fixture", "run", "all"], nargs="?", default="all")
    parser.add_argument("--config", default=DEFAULT_CONFIG_PATH)
    return parser.parse_args(argv)


def def_main(argv: list[str] | None = None) -> int:
    args = def_parse_args(argv)
    config_path = Path(args.config).resolve()
    project_root = config_path.parent.parent
    if args.command in {"fixture", "all"}:
        from engine.build_controlled_fixture import def_write_fixture

        counts = def_write_fixture(project_root / "data" / "input")
        print(f"def Fixture           : {counts}")
        if args.command == "fixture":
            return 0
    summary = def_run_system(config_path)
    print(f"def System            : {summary['SystemId']} v{summary['Version']}")
    print(f"def Gate              : {summary['Gate']}")
    print(f"def Groups            : {summary['GroupCount']}")
    print(f"def Hard Failures     : {summary['HardFailures']}")
    print(f"def Review Items      : {summary['ReviewItems']}")
    print(f"def Dashboard         : {summary['Outputs']['dashboard']['path']}")
    return 1 if summary["Gate"] == "FAIL_CLOSED" else 0


if __name__ == "__main__":
    raise SystemExit(def_main())
