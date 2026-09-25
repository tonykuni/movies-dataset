from __future__ import annotations

"""Point-in-time Taiwan FX/rate context for foreign-flow interpretation."""

# =============================================================================
# def 00 PARAMETERS — structural windows only
# =============================================================================

from dataclasses import dataclass
import re
from urllib.parse import urlparse

import numpy as np
import pandas as pd

try:
    from .via_time_utils import def_available_at_utc, def_local_calendar_date
except ImportError:  # standalone script/import from the engine directory
    from via_time_utils import def_available_at_utc, def_local_calendar_date


ENGINE_ID = "VIA_FX_CONTEXT_V0500"
ENGINE_VERSION = "0.5.0"
DEFAULT_WINDOWS = (60, 120, 240)
RISK_FREE_SOURCE_AUTHORITY = "TAIPEI_EXCHANGE_TPEX"
RISK_FREE_SOURCE_HOST = "tpex.org.tw"
RISK_FREE_INSTRUMENT_ID = "TAIWAN_10Y_GOVERNMENT_BOND_YIELD"
RISK_FREE_PROVENANCE_COLUMNS = {
    "Source",
    "SourceAuthority",
    "SourceURL",
    "SourcePayloadHash",
    "YieldUnit",
    "InstrumentId",
    "OfficialSourceVerified",
}
REQUIRED_MACRO_COLUMNS = RISK_FREE_PROVENANCE_COLUMNS | {
    "ObservationDate",
    "AvailableAt",
    "USDTWD",
    "DXY",
    "Taiwan10YYield",
}
SHA256_HEX_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class FXContextConfig:
    windows: tuple[int, ...] = DEFAULT_WINDOWS


def _is_official_tpex_url(value: object) -> bool:
    """Accept only HTTPS URLs whose actual host is TPEx.

    A matching hostname is provenance evidence supplied by the ingestion
    contract; it is not a cryptographic source signature.
    """

    try:
        parsed = urlparse(str(value).strip())
        host = (parsed.hostname or "").lower().rstrip(".")
        port = parsed.port
    except (TypeError, ValueError):
        return False
    return bool(
        parsed.scheme.lower() == "https"
        and (host == RISK_FREE_SOURCE_HOST or host.endswith(f".{RISK_FREE_SOURCE_HOST}"))
        and parsed.username is None
        and parsed.password is None
        and port in {None, 443}
    )


def def_official_taiwan_10y_provenance_mask(frame: pd.DataFrame) -> pd.Series:
    """Revalidate canonical TPEx Taiwan-10Y row evidence, fail closed.

    ``SourcePayloadHash`` is checked only as a SHA-256 digest-shaped integrity
    field.  It is deliberately not treated as a TPEx signature or proof that
    the named URL emitted the payload.
    """

    missing = sorted(RISK_FREE_PROVENANCE_COLUMNS.difference(frame.columns))
    if missing:
        raise ValueError(
            "risk-free input cannot prove official Taiwan 10Y provenance; "
            f"missing columns: {missing}"
        )
    verified_flag = frame["OfficialSourceVerified"].map(
        lambda value: value is True
        or str(value).strip().upper() in {"TRUE", "1", "YES", "Y", "PASS"}
    )
    source = frame["Source"].fillna("").astype(str).str.strip()
    authority = (
        frame["SourceAuthority"].fillna("").astype(str).str.strip().str.upper()
    )
    source_url = frame["SourceURL"].fillna("").astype(str).str.strip()
    payload_hash = frame["SourcePayloadHash"].fillna("").astype(str).str.strip()
    yield_unit = frame["YieldUnit"].fillna("").astype(str).str.strip().str.upper()
    instrument_id = (
        frame["InstrumentId"].fillna("").astype(str).str.strip().str.upper()
    )
    return pd.Series(
        source.ne("")
        & authority.eq(RISK_FREE_SOURCE_AUTHORITY)
        & source_url.map(_is_official_tpex_url)
        & payload_hash.map(lambda value: bool(SHA256_HEX_PATTERN.fullmatch(value)))
        & yield_unit.eq("PERCENT")
        & instrument_id.eq(RISK_FREE_INSTRUMENT_ID)
        & verified_flag,
        index=frame.index,
        dtype=bool,
    )


def def_prepare_macro_factors(raw: pd.DataFrame) -> pd.DataFrame:
    """Normalize publication vintages; never infer a missing availability time."""

    missing = sorted(REQUIRED_MACRO_COLUMNS.difference(raw.columns))
    if missing:
        raise ValueError(f"macro factor input missing required columns: {missing}")
    frame = raw.copy()
    frame["ObservationDate"] = frame["ObservationDate"].map(def_local_calendar_date)
    frame["AvailableAt"] = frame["AvailableAt"].map(def_available_at_utc)
    for column in ("USDTWD", "DXY", "Taiwan10YYield"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    invalid = frame["ObservationDate"].isna() | frame["AvailableAt"].isna()
    if invalid.any():
        raise ValueError(f"macro factor input has {int(invalid.sum())} invalid PIT timestamps")
    duplicate = frame.duplicated(["ObservationDate", "AvailableAt"], keep=False)
    if duplicate.any():
        raise ValueError(f"macro factor input has {int(duplicate.sum())} duplicate vintages")
    frame["Source"] = frame["Source"].fillna("").astype(str).str.strip()
    frame["SourceAuthority"] = (
        frame["SourceAuthority"].fillna("").astype(str).str.strip().str.upper()
    )
    frame["SourceURL"] = frame["SourceURL"].fillna("").astype(str).str.strip()
    frame["SourcePayloadHash"] = (
        frame["SourcePayloadHash"].fillna("").astype(str).str.strip().str.lower()
    )
    frame["YieldUnit"] = frame["YieldUnit"].fillna("").astype(str).str.strip().str.upper()
    frame["InstrumentId"] = frame["InstrumentId"].fillna("").astype(str).str.strip().str.upper()
    verified_provenance = def_official_taiwan_10y_provenance_mask(frame)
    payload_hash_valid = frame["SourcePayloadHash"].map(
        lambda value: bool(SHA256_HEX_PATTERN.fullmatch(value))
    )
    finite_yield = pd.Series(
        np.isfinite(frame["Taiwan10YYield"]), index=frame.index, dtype=bool
    )
    verified_risk_free = (
        finite_yield
        & verified_provenance
    )
    frame["SourcePayloadIntegrityStatus"] = np.where(
        payload_hash_valid,
        "SHA256_PAYLOAD_DIGEST_PRESENT_FORMAT_VALID_NOT_SOURCE_SIGNATURE",
        "HOLD_MISSING_OR_INVALID_SHA256_PAYLOAD_DIGEST",
    )
    frame["RiskFreeSourceStatus"] = np.where(
        verified_risk_free,
        "OFFICIAL_TAIWAN_10Y_POINT_IN_TIME",
        "HOLD_UNVERIFIED_OR_MISSING_TAIWAN_10Y_SOURCE",
    )
    return frame.sort_values(["AvailableAt", "ObservationDate"]).reset_index(drop=True)


def def_materialize_macro_asof(
    prepared: pd.DataFrame,
    decision_times: pd.DataFrame,
) -> pd.DataFrame:
    """Backward-asof macro values using actual publication timestamps.

    ``decision_times`` requires ``Date`` and ``DecisionAt``.  Staleness is
    disclosed; values are never joined from a future publication.
    """

    required = {"Date", "DecisionAt"}
    missing = sorted(required.difference(decision_times.columns))
    if missing:
        raise ValueError(f"decision times missing required columns: {missing}")
    left = decision_times.copy()
    left["Date"] = left["Date"].map(def_local_calendar_date)
    left["DecisionAt"] = left["DecisionAt"].map(def_available_at_utc)
    if left[["Date", "DecisionAt"]].isna().any(axis=1).any():
        raise ValueError("decision times contain invalid Date/DecisionAt values")
    right = prepared.copy()
    rows: list[dict[str, object]] = []
    for decision_row in left.sort_values("DecisionAt").to_dict(orient="records"):
        known = right.loc[right["AvailableAt"].le(decision_row["DecisionAt"])].copy()
        if not known.empty:
            known = (
                known.sort_values(["ObservationDate", "AvailableAt"])
                .drop_duplicates("ObservationDate", keep="last")
                .sort_values(["ObservationDate", "AvailableAt"])
            )
            vintage = known.iloc[-1].to_dict()
        else:
            vintage = {column: np.nan for column in right.columns}
            vintage["AvailableAt"] = pd.NaT
            vintage["ObservationDate"] = pd.NaT
        rows.append({**decision_row, **vintage})
    joined = pd.DataFrame(rows)
    if ((joined["AvailableAt"].notna()) & joined["AvailableAt"].gt(joined["DecisionAt"])).any():
        raise AssertionError("future macro vintage entered a point-in-time join")
    joined["MacroAgeDays"] = (
        joined["DecisionAt"] - joined["AvailableAt"]
    ).dt.total_seconds() / 86400.0
    joined["MacroPointInTimeStatus"] = np.where(
        joined["AvailableAt"].notna(), "PASS_BACKWARD_ASOF", "MISSING_PRIOR_MACRO_VINTAGE"
    )
    return joined.sort_values("Date").reset_index(drop=True)


def def_prior_median_state(series: pd.Series, window: int) -> pd.Series:
    minimum = max(2, int(np.sqrt(window)))
    prior = series.shift(1).rolling(window, min_periods=minimum).median()
    return pd.Series(
        np.select(
            [series.gt(prior), series.lt(prior), series.eq(prior) & prior.notna()],
            ["ABOVE_PRIOR_MEDIAN", "BELOW_PRIOR_MEDIAN", "AT_PRIOR_MEDIAN"],
            default="HOLD_INSUFFICIENT_HISTORY",
        ),
        index=series.index,
    )


def def_add_macro_context(
    pit_macro: pd.DataFrame,
    config: FXContextConfig = FXContextConfig(),
) -> pd.DataFrame:
    """Add separate USD/TWD, DXY and Taiwan-10Y states."""

    frame = pit_macro.sort_values("Date").copy()
    frame["USDTWDReturn"] = np.log(frame["USDTWD"].where(frame["USDTWD"].gt(0))).diff()
    frame["DXYReturn"] = np.log(frame["DXY"].where(frame["DXY"].gt(0))).diff()
    verified_yield = frame["Taiwan10YYield"].where(
        frame["RiskFreeSourceStatus"].eq("OFFICIAL_TAIWAN_10Y_POINT_IN_TIME")
    )
    frame["Taiwan10YDailyRiskFree"] = np.power(
        1.0 + verified_yield / 100.0,
        1.0 / 252.0,
    ) - 1.0
    for window in config.windows:
        frame[f"USDTWDState_{window}D"] = def_prior_median_state(frame["USDTWDReturn"], window)
        frame[f"DXYState_{window}D"] = def_prior_median_state(frame["DXYReturn"], window)
        frame[f"Taiwan10YState_{window}D"] = def_prior_median_state(frame["Taiwan10YYield"], window)
    frame["MacroCompositePolicy"] = "PROHIBITED_SEPARATE_CONTEXT_LANES"
    return frame


def def_foreign_flow_fx_residual(
    foreign_daily: pd.DataFrame,
    macro_daily: pd.DataFrame,
    config: FXContextConfig = FXContextConfig(),
) -> pd.DataFrame:
    """Estimate each current foreign-flow residual using coefficients through t-1."""

    required = {"Date", "GroupId", "ForeignNetAmount"}
    missing = sorted(required.difference(foreign_daily.columns))
    if missing:
        raise ValueError(f"foreign flow input missing required columns: {missing}")
    flow = foreign_daily.copy()
    flow["Date"] = pd.to_datetime(flow["Date"], errors="coerce").dt.normalize()
    macro_columns = ["Date", "USDTWDReturn", "DXYReturn"]
    joined = flow.merge(macro_daily[macro_columns], on="Date", how="left", validate="many_to_one")
    outputs: list[pd.DataFrame] = []
    for _, group in joined.groupby("GroupId", sort=True):
        group = group.sort_values("Date").copy()
        for window in config.windows:
            residual = pd.Series(np.nan, index=group.index, dtype=float)
            observations = pd.Series(0, index=group.index, dtype=int)
            for position in range(len(group)):
                training = group.iloc[max(0, position - window) : position][
                    ["ForeignNetAmount", "USDTWDReturn", "DXYReturn"]
                ].dropna()
                observations.iloc[position] = len(training)
                minimum = max(4, int(np.sqrt(window)))
                current = group.iloc[position]
                if len(training) < minimum or current[["ForeignNetAmount", "USDTWDReturn", "DXYReturn"]].isna().any():
                    continue
                x = training[["USDTWDReturn", "DXYReturn"]].to_numpy(dtype=float)
                x = np.column_stack([np.ones(len(x)), x])
                y = training["ForeignNetAmount"].to_numpy(dtype=float)
                beta = np.linalg.lstsq(x, y, rcond=None)[0]
                current_x = np.array([1.0, current["USDTWDReturn"], current["DXYReturn"]], dtype=float)
                residual.iloc[position] = float(current["ForeignNetAmount"] - current_x @ beta)
            group[f"ForeignFlowFXResidual_{window}D"] = residual
            group[f"ForeignFlowFXTrainingN_{window}D"] = observations
        outputs.append(group)
    result = pd.concat(outputs, ignore_index=True, sort=False) if outputs else pd.DataFrame()
    if not result.empty:
        result["FXAdjustmentStatus"] = "ROLLING_T_MINUS_1_OLS"
    return result
