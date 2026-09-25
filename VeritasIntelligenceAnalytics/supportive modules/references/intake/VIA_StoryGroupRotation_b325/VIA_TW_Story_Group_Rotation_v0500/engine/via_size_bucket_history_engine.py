from __future__ import annotations

"""Independent market-cap and ETR tiers for the full Taiwan equity universe."""

# =============================================================================
# def 00 PARAMETERS — requested structural tiers and windows
# =============================================================================

from dataclasses import dataclass
import hashlib
import json

import numpy as np
import pandas as pd


ENGINE_ID = "VIA_SIZE_BUCKET_HISTORY_V0500"
ENGINE_VERSION = "0.5.0"
DEFAULT_WINDOWS = (60, 120, 240)
SIZE_LOWER_QUANTILE = 0.60
SIZE_UPPER_QUANTILE = 0.90
TSMC_BASE = "2330"


@dataclass(frozen=True)
class SizeBucketConfig:
    windows: tuple[int, ...] = DEFAULT_WINDOWS
    lower_quantile: float = SIZE_LOWER_QUANTILE
    upper_quantile: float = SIZE_UPPER_QUANTILE
    tsmc_ticker: str = TSMC_BASE


def def_ticker_base(value: object) -> str:
    text = str(value or "").strip().upper()
    return text.removesuffix(".TW").removesuffix(".TWO")


def def_prepare_size_panel(daily: pd.DataFrame) -> pd.DataFrame:
    daily = daily.copy()
    if "Exchange" not in daily.columns and "Market" in daily.columns:
        daily["Exchange"] = daily["Market"]
    required = {"Date", "Ticker", "Exchange", "MarketCap", "ETR"}
    missing = sorted(required.difference(daily.columns))
    if missing:
        raise ValueError(f"size panel missing required columns: {missing}")
    frame = daily.copy()
    frame["Date"] = pd.to_datetime(frame["Date"], errors="coerce").dt.normalize()
    frame["Ticker"] = frame["Ticker"].map(def_ticker_base)
    frame["MarketCap"] = pd.to_numeric(frame["MarketCap"], errors="coerce")
    frame["ETR"] = pd.to_numeric(frame["ETR"], errors="coerce")
    if "AssetType" not in frame:
        frame["AssetType"] = "EQUITY"
    invalid = frame["Date"].isna() | frame["Ticker"].eq("")
    if invalid.any():
        raise ValueError(f"size panel has {int(invalid.sum())} invalid keys")
    duplicate = frame.duplicated(["Date", "Ticker"], keep=False)
    if duplicate.any():
        raise ValueError(f"size panel has {int(duplicate.sum())} duplicate keys")
    ordinary = frame["AssetType"].fillna("").astype(str).str.upper().isin(
        {"COMMON_STOCK", "COMMON", "EQUITY", "STOCK", "ORDINARY_SHARE", "普通股"}
    )
    frame["UniverseEligible"] = ordinary & frame["Exchange"].astype(str).str.upper().isin(["TWSE", "TPEX"])
    return frame.sort_values(["Ticker", "Date"]).reset_index(drop=True)


def def_quarterly_snapshot_dates(calendar: pd.DatetimeIndex) -> list[pd.Timestamp]:
    dates = pd.DatetimeIndex(sorted(pd.unique(calendar))).normalize()
    if not len(dates):
        return []
    series = pd.Series(dates, index=dates)
    snapshots = series.groupby(dates.to_period("Q")).max().tolist()
    if pd.Timestamp(dates[-1]) not in snapshots:
        snapshots.append(pd.Timestamp(dates[-1]))
    return sorted(pd.Timestamp(value) for value in snapshots)


def def_next_session(calendar: pd.DatetimeIndex, date: pd.Timestamp) -> pd.Timestamp | pd.NaT:
    later = calendar[calendar > date]
    return pd.Timestamp(later[0]) if len(later) else pd.NaT


def def_bucket(value: float, lower: float, upper: float) -> str:
    if not np.isfinite(value):
        return "MISSING"
    if value >= upper:
        return "LARGE"
    if value >= lower:
        return "MID"
    return "SMALL"


def def_bucket_id(record: dict[str, object]) -> str:
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
    return "VIA-BKT-" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:20].upper()


def def_compute_quarterly_bucket_history(
    daily: pd.DataFrame,
    config: SizeBucketConfig = SizeBucketConfig(),
) -> pd.DataFrame:
    """Classify full-market ex-2330 tiers with strictly T-1 trailing data.

    Market-cap size and ETR liquidity are independent fields.  The P60/P90
    values are the user-requested structural three-bucket policy; their dollar
    cut-offs are recalculated from each point-in-time cross-section.
    """

    frame = def_prepare_size_panel(daily)
    calendar = pd.DatetimeIndex(sorted(frame["Date"].unique()))
    rows: list[dict[str, object]] = []
    tsmc = def_ticker_base(config.tsmc_ticker)
    for snapshot in def_quarterly_snapshot_dates(calendar):
        effective = def_next_session(calendar, snapshot)
        if pd.isna(effective):
            # The final observed session is only a preview until the next real
            # exchange session exists; it must not occupy an append-only key.
            continue
        prior = frame.loc[frame["Date"].le(snapshot) & frame["UniverseEligible"]].copy()
        if prior.empty:
            continue
        for window in config.windows:
            dates = sorted(prior["Date"].unique())[-window:]
            history = prior.loc[prior["Date"].isin(dates)]
            by_ticker = (
                history.groupby(["Ticker", "Exchange"], as_index=False)
                .agg(
                    RollingMarketCap=("MarketCap", "median"),
                    RollingETR=("ETR", "median"),
                    MarketCapObservations=("MarketCap", "count"),
                    ETRObservations=("ETR", "count"),
                )
            )
            comparison = by_ticker.loc[by_ticker["Ticker"].ne(tsmc)]
            cap_values = comparison["RollingMarketCap"].dropna()
            etr_values = comparison["RollingETR"].dropna()
            cap_lower = float(cap_values.quantile(config.lower_quantile)) if len(cap_values) else np.nan
            cap_upper = float(cap_values.quantile(config.upper_quantile)) if len(cap_values) else np.nan
            etr_lower = float(etr_values.quantile(config.lower_quantile)) if len(etr_values) else np.nan
            etr_upper = float(etr_values.quantile(config.upper_quantile)) if len(etr_values) else np.nan
            for _, member in by_ticker.iterrows():
                is_tsmc = member["Ticker"] == tsmc
                cap_tier = "ANCHOR_EXCLUDED" if is_tsmc else def_bucket(member["RollingMarketCap"], cap_lower, cap_upper)
                liquidity_tier = "ANCHOR_EXCLUDED" if is_tsmc else def_bucket(member["RollingETR"], etr_lower, etr_upper)
                status = (
                    "ANCHOR_REPORTED_SEPARATELY"
                    if is_tsmc
                    else (
                        "PASS"
                        if cap_tier != "MISSING" and liquidity_tier != "MISSING"
                        else "HOLD_MISSING_SIZE_OR_ETR"
                    )
                )
                record = {
                    "SnapshotDate": snapshot,
                    "EffectiveDate": effective,
                    "WindowDays": window,
                    "Ticker": member["Ticker"],
                    "Exchange": member["Exchange"],
                    "RollingMarketCap": member["RollingMarketCap"],
                    "RollingETR": member["RollingETR"],
                    "MarketCapTier": cap_tier,
                    "EffectiveTurnoverTier": liquidity_tier,
                    "MarketCapP60": cap_lower,
                    "MarketCapP90": cap_upper,
                    "ETRP60": etr_lower,
                    "ETRP90": etr_upper,
                    "MarketCapObservations": int(member["MarketCapObservations"]),
                    "ETRObservations": int(member["ETRObservations"]),
                    "ClassificationStatus": status,
                    "ThresholdPolicy": "POINT_IN_TIME_CROSS_SECTION_P60_P90_EX_2330",
                }
                record["BucketEventId"] = def_bucket_id(record)
                rows.append(record)
    return pd.DataFrame(rows).sort_values(["SnapshotDate", "WindowDays", "Ticker"]).reset_index(drop=True) if rows else pd.DataFrame()


def def_append_bucket_history(existing: pd.DataFrame, additions: pd.DataFrame) -> pd.DataFrame:
    """Idempotent append; conflicting events at the same key fail closed."""

    if existing.empty:
        return additions.copy().reset_index(drop=True)
    if additions.empty:
        return existing.copy().reset_index(drop=True)
    key = ["SnapshotDate", "WindowDays", "Ticker"]
    left = existing.copy()
    right = additions.copy()
    for frame in (left, right):
        frame["SnapshotDate"] = pd.to_datetime(frame["SnapshotDate"], errors="coerce").dt.normalize()
    overlap = left.merge(right, on=key, how="inner", suffixes=("_old", "_new"))
    if not overlap.empty:
        mismatch = overlap["BucketEventId_old"].ne(overlap["BucketEventId_new"])
        if mismatch.any():
            raise ValueError(f"append-only bucket conflict: {int(mismatch.sum())} keys")
    new_ids = set(left["BucketEventId"].astype(str))
    appended = pd.concat([left, right.loc[~right["BucketEventId"].astype(str).isin(new_ids)]], ignore_index=True)
    return appended.sort_values(key).reset_index(drop=True)
