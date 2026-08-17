from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd


# =============================================================================
# def 00. PARAMETERS / SSOT CONSTANTS
# =============================================================================

ENGINE_ID = "VIA_ACCELERATED_INTEGRATION_ENGINE_V0139A"
ENGINE_VERSION = "v0139A"
SCHEMA_VERSION = "VIA_ACCELERATED_INTEGRATION_RUN_V1"
DEFAULT_INDEX_BASE = 100.0
DEFAULT_FLOW_SHORT_WINDOW = 3
DEFAULT_FLOW_LONG_WINDOW = 5
DEFAULT_OUTPUT_DATE_FORMAT = "%Y/%m/%d"
DEFAULT_CHART_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_REQUIRED_CODES = ("2330.TW", "2317.TW", "2603.TW", "1101.TW")
COMPONENT_IDS = (
    "VIA_VAP_Integration_Update_Engine_v0139A",
    "VIA_Flow_Simulation_Engine_v0139A",
    "VIA_TW_Stock_Group_Classification_Engine_v0139A",
    "VIA_TW_Group_Index_Engine_v0139A",
    "VIA_TW_Monthly_Revenue_Analysis_Engine_v0139A",
)
VAP_REQUIRED_TOKENS = (
    "VERITAS INTELLIGENCE ANALYTICS",
    "DISCIPLINA • PRUDENTIA • INTEGRITAS",
    "AI-Powered Research & Decision Intelligence Platform",
    "MODULE",
    "ENGINE",
    "FUNCTION LIB",
    "OTHERS",
    "Flow Simulation",
    "Group Index",
    "Monthly Revenue",
)

PRICE_ALIASES = {
    "date": "Date",
    "ticker": "Ticker",
    "adj close": "Adj Close",
    "adj_close": "Adj Close",
    "adjusted close": "Adj Close",
    "volume": "Volume",
    "market cap": "Market Cap",
    "market_cap": "Market Cap",
}
CLASSIFICATION_ALIASES = {
    "ticker": "Ticker",
    "name": "Name",
    "sector": "Sector",
    "industry": "Industry",
    "theme": "Theme",
    "taxonomy version": "Taxonomy Version",
    "taxonomy_version": "Taxonomy Version",
}
FLOW_ALIASES = {
    "date": "Date",
    "ticker": "Ticker",
    "foreign net": "Foreign Net",
    "foreign_net": "Foreign Net",
    "investment trust net": "Investment Trust Net",
    "investment_trust_net": "Investment Trust Net",
    "dealer net": "Dealer Net",
    "dealer_net": "Dealer Net",
}
REVENUE_ALIASES = {
    "ticker": "Ticker",
    "revenue month": "Revenue Month",
    "revenue_month": "Revenue Month",
    "monthly revenue": "Monthly Revenue",
    "monthly_revenue": "Monthly Revenue",
}
VAP_PALETTE = (
    "#16324F",
    "#287271",
    "#D4A72C",
    "#A63D40",
    "#5C677D",
    "#7A9E9F",
    "#B56576",
    "#6B705C",
)


# =============================================================================
# def 01. DATA TYPES
# =============================================================================


class ContractError(ValueError):
    """Raised when a governed input contract is violated."""


class HydraRiskError(RuntimeError):
    """Raised when multiple semantic owners are detected for one identity."""


@dataclass(frozen=True)
class WriteResult:
    stem: str
    csv_path: str
    csv_rows: int
    parquet_path: str | None
    parquet_rows: int
    parquet_status: str


@dataclass(frozen=True)
class PipelineResult:
    gate: str
    run_dir: str
    html_path: str
    evidence_path: str
    manifest_path: str
    error_count: int
    hydra_count: int
    unit_pass: int
    canonical_runtime_executions: int
    network_used: int


# =============================================================================
# def 02. GENERIC HELPERS
# =============================================================================


def def_utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def def_slug(value: Any) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value).strip())
    return text.strip("_") or "UNKNOWN"


def def_sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def def_sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def def_atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=str(path.parent)
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding=encoding, newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def def_atomic_write_json(path: Path, payload: Mapping[str, Any]) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n"
    def_atomic_write_text(path, content)


def def_normalize_columns(
    frame: pd.DataFrame, aliases: Mapping[str, str]
) -> pd.DataFrame:
    renamed = {}
    for column in frame.columns:
        normalized = re.sub(r"\s+", " ", str(column).strip()).lower()
        renamed[column] = aliases.get(normalized, str(column).strip())
    return frame.rename(columns=renamed).copy()


def def_require_columns(
    frame: pd.DataFrame, required: Sequence[str], dataset_name: str
) -> None:
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ContractError(
            f"{dataset_name} missing required columns: {', '.join(missing)}"
        )


def def_normalize_ticker(value: Any) -> str:
    ticker = str(value).strip().upper()
    if re.fullmatch(r"\d{4}", ticker):
        return f"{ticker}.TW"
    if re.fullmatch(r"\d{4}\.(TW|TWO)", ticker):
        return ticker
    if ticker in {"^TWII", "^GSPC", "^TNX"}:
        return ticker
    raise ContractError(f"Unsupported ticker identity: {value!r}")


def def_read_table(path: Path, declared_format: str | None = None) -> pd.DataFrame:
    if not path.is_file():
        raise FileNotFoundError(path)
    data_format = (declared_format or path.suffix.lstrip(".")).lower()
    if data_format in {"csv", "txt"}:
        return pd.read_csv(path, encoding="utf-8-sig")
    if data_format in {"parquet", "pq"}:
        return pd.read_parquet(path)
    raise ContractError(f"Unsupported table format: {data_format or '<none>'}")


def def_format_csv_dates(frame: pd.DataFrame) -> pd.DataFrame:
    output = frame.copy()
    for column in output.columns:
        if pd.api.types.is_datetime64_any_dtype(output[column]):
            output[column] = output[column].dt.strftime(DEFAULT_OUTPUT_DATE_FORMAT)
    return output


def def_write_dual_table(
    frame: pd.DataFrame,
    output_dir: Path,
    stem: str,
    require_parquet: bool,
) -> WriteResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / f"{stem}.csv"
    parquet_path = output_dir / f"{stem}.parquet"
    csv_frame = def_format_csv_dates(frame)
    csv_text = csv_frame.to_csv(index=False, lineterminator="\n")
    def_atomic_write_text(csv_path, csv_text, encoding="utf-8-sig")

    parquet_status = "PASS"
    parquet_rows = len(frame)
    written_parquet: str | None = str(parquet_path)
    try:
        frame.to_parquet(parquet_path, index=False)
    except (ImportError, ModuleNotFoundError) as error:
        parquet_status = f"HOLD_DEPENDENCY:{type(error).__name__}"
        parquet_rows = 0
        written_parquet = None
        if require_parquet:
            raise ContractError(
                "Parquet output requires pyarrow or fastparquet in the governed Python environment"
            ) from error

    return WriteResult(
        stem=stem,
        csv_path=str(csv_path),
        csv_rows=len(frame),
        parquet_path=written_parquet,
        parquet_rows=parquet_rows,
        parquet_status=parquet_status,
    )


def def_safe_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    return number if math.isfinite(number) else default


# =============================================================================
# def 03. INPUT NORMALIZATION
# =============================================================================


def def_normalize_prices(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = def_normalize_columns(frame, PRICE_ALIASES)
    def_require_columns(normalized, ("Date", "Ticker", "Adj Close", "Volume"), "Price")
    normalized["Date"] = pd.to_datetime(normalized["Date"], errors="coerce")
    normalized["Ticker"] = normalized["Ticker"].map(def_normalize_ticker)
    normalized["Adj Close"] = pd.to_numeric(normalized["Adj Close"], errors="coerce")
    normalized["Volume"] = pd.to_numeric(normalized["Volume"], errors="coerce")
    normalized = normalized.sort_values(["Ticker", "Date"], kind="stable")
    normalized["Adj Close"] = normalized.groupby("Ticker")["Adj Close"].ffill()
    normalized["Volume Was Missing"] = normalized["Volume"].isna()
    normalized["Volume"] = normalized["Volume"].fillna(0.0)
    if "Market Cap" in normalized.columns:
        normalized["Market Cap"] = pd.to_numeric(
            normalized["Market Cap"], errors="coerce"
        )
        normalized["Market Cap"] = normalized.groupby("Ticker")["Market Cap"].ffill()
    invalid = normalized[
        normalized["Date"].isna()
        | normalized["Adj Close"].isna()
        | (normalized["Adj Close"] <= 0)
    ]
    if not invalid.empty:
        raise ContractError(f"Price contains {len(invalid)} invalid governed rows")
    return normalized.drop_duplicates(["Date", "Ticker"], keep="last").reset_index(drop=True)


def def_normalize_classification(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = def_normalize_columns(frame, CLASSIFICATION_ALIASES)
    def_require_columns(normalized, ("Ticker", "Sector", "Industry"), "Classification")
    normalized["Ticker"] = normalized["Ticker"].map(def_normalize_ticker)
    normalized["Sector"] = normalized["Sector"].fillna("Unclassified").astype(str).str.strip()
    normalized["Industry"] = normalized["Industry"].fillna("Unclassified").astype(str).str.strip()
    if "Theme" not in normalized.columns:
        normalized["Theme"] = "Unclassified"
    if "Name" not in normalized.columns:
        normalized["Name"] = normalized["Ticker"]
    if "Taxonomy Version" not in normalized.columns:
        normalized["Taxonomy Version"] = ENGINE_VERSION
    identity_columns = ["Ticker", "Sector", "Industry", "Theme", "Taxonomy Version"]
    unique_rows = normalized[identity_columns].drop_duplicates()
    conflicts = unique_rows.groupby("Ticker").size()
    conflicts = conflicts[conflicts > 1]
    if not conflicts.empty:
        raise HydraRiskError(
            "Classification Hydra risk for ticker(s): " + ", ".join(conflicts.index)
        )
    return normalized.drop_duplicates("Ticker", keep="last").reset_index(drop=True)


def def_normalize_flows(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = def_normalize_columns(frame, FLOW_ALIASES)
    def_require_columns(normalized, ("Date", "Ticker"), "Flow")
    normalized["Date"] = pd.to_datetime(normalized["Date"], errors="coerce")
    normalized["Ticker"] = normalized["Ticker"].map(def_normalize_ticker)
    flow_columns = ("Foreign Net", "Investment Trust Net", "Dealer Net")
    for column in flow_columns:
        if column not in normalized.columns:
            normalized[column] = 0.0
        normalized[column] = pd.to_numeric(normalized[column], errors="coerce").fillna(0.0)
    if normalized["Date"].isna().any():
        raise ContractError("Flow contains invalid Date values")
    return normalized.drop_duplicates(["Date", "Ticker"], keep="last").reset_index(drop=True)


def def_normalize_revenue(frame: pd.DataFrame) -> pd.DataFrame:
    normalized = def_normalize_columns(frame, REVENUE_ALIASES)
    def_require_columns(
        normalized, ("Ticker", "Revenue Month", "Monthly Revenue"), "Monthly Revenue"
    )
    normalized["Ticker"] = normalized["Ticker"].map(def_normalize_ticker)
    normalized["Revenue Month"] = pd.to_datetime(
        normalized["Revenue Month"], errors="coerce"
    ).dt.to_period("M").dt.to_timestamp()
    normalized["Monthly Revenue"] = pd.to_numeric(
        normalized["Monthly Revenue"], errors="coerce"
    )
    invalid = normalized[
        normalized["Revenue Month"].isna()
        | normalized["Monthly Revenue"].isna()
        | (normalized["Monthly Revenue"] < 0)
    ]
    if not invalid.empty:
        raise ContractError(f"Monthly Revenue contains {len(invalid)} invalid rows")
    return normalized.drop_duplicates(
        ["Ticker", "Revenue Month"], keep="last"
    ).reset_index(drop=True)


# =============================================================================
# def 04. CLASSIFICATION / GROUP INDEX ENGINE
# =============================================================================


def def_build_stock_group_classification(frame: pd.DataFrame) -> pd.DataFrame:
    classified = def_normalize_classification(frame)
    classified["Display Name"] = (
        classified["Name"].astype(str) + " (" + classified["Ticker"] + ")"
    )
    classified["Group Key"] = (
        classified["Sector"].map(def_slug) + "__" + classified["Industry"].map(def_slug)
    )
    return classified[
        [
            "Ticker",
            "Display Name",
            "Sector",
            "Industry",
            "Theme",
            "Group Key",
            "Taxonomy Version",
        ]
    ].sort_values(["Sector", "Industry", "Ticker"], kind="stable").reset_index(drop=True)


def def_compute_group_index(
    prices: pd.DataFrame,
    classification: pd.DataFrame,
    group_column: str = "Sector",
    weighting: str = "equal",
    base_value: float = DEFAULT_INDEX_BASE,
) -> pd.DataFrame:
    price_frame = def_normalize_prices(prices)
    class_frame = def_build_stock_group_classification(classification)
    if group_column not in class_frame.columns:
        raise ContractError(f"Unsupported group column: {group_column}")
    merged = price_frame.merge(
        class_frame[["Ticker", group_column]], on="Ticker", how="left", validate="many_to_one"
    )
    merged[group_column] = merged[group_column].fillna("Unclassified")
    merged = merged.sort_values([group_column, "Ticker", "Date"], kind="stable")
    merged["Return"] = merged.groupby("Ticker")["Adj Close"].pct_change()

    if weighting == "equal":
        daily = (
            merged.groupby(["Date", group_column], as_index=False)["Return"]
            .mean()
            .rename(columns={"Return": "Group Return"})
        )
    elif weighting == "market_cap":
        if "Market Cap" not in merged.columns:
            raise ContractError("Market-cap weighting requires Market Cap")
        merged["Lagged Market Cap"] = merged.groupby("Ticker")["Market Cap"].shift(1)
        merged["Weighted Return Numerator"] = (
            merged["Return"] * merged["Lagged Market Cap"]
        )
        grouped = merged.groupby(["Date", group_column], as_index=False).agg(
            Numerator=("Weighted Return Numerator", "sum"),
            Denominator=("Lagged Market Cap", "sum"),
        )
        grouped["Group Return"] = np.where(
            grouped["Denominator"] > 0,
            grouped["Numerator"] / grouped["Denominator"],
            np.nan,
        )
        daily = grouped[["Date", group_column, "Group Return"]]
    else:
        raise ContractError(f"Unsupported weighting method: {weighting}")

    daily = daily.sort_values([group_column, "Date"], kind="stable")
    daily["Group Return"] = daily["Group Return"].fillna(0.0)
    daily["Group Index"] = daily.groupby(group_column)["Group Return"].transform(
        lambda series: base_value * (1.0 + series).cumprod()
    )
    first_rows = daily.groupby(group_column, sort=False).head(1).index
    daily.loc[first_rows, "Group Index"] = base_value
    daily["Weighting"] = weighting
    return daily.rename(columns={group_column: "Group"}).reset_index(drop=True)


# =============================================================================
# def 05. MONTHLY REVENUE ENGINE
# =============================================================================


def def_compute_monthly_revenue_analysis(
    revenue: pd.DataFrame,
    classification: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    revenue_frame = def_normalize_revenue(revenue)
    class_frame = def_build_stock_group_classification(classification)
    output = revenue_frame.merge(
        class_frame[["Ticker", "Sector", "Industry"]],
        on="Ticker",
        how="left",
        validate="many_to_one",
    )
    output[["Sector", "Industry"]] = output[["Sector", "Industry"]].fillna(
        "Unclassified"
    )
    output = output.sort_values(["Ticker", "Revenue Month"], kind="stable")
    output["Revenue MoM Pct"] = output.groupby("Ticker")["Monthly Revenue"].pct_change() * 100

    prior_year = output[["Ticker", "Revenue Month", "Monthly Revenue"]].copy()
    prior_year["Revenue Month"] = prior_year["Revenue Month"] + pd.DateOffset(years=1)
    prior_year = prior_year.rename(columns={"Monthly Revenue": "Prior Year Revenue"})
    output = output.merge(
        prior_year,
        on=["Ticker", "Revenue Month"],
        how="left",
        validate="one_to_one",
    )
    output["Revenue YoY Pct"] = (
        output["Monthly Revenue"] / output["Prior Year Revenue"] - 1.0
    ) * 100
    output["Revenue 3M Average"] = output.groupby("Ticker")["Monthly Revenue"].transform(
        lambda series: series.rolling(3, min_periods=1).mean()
    )
    output["Revenue YoY Acceleration Ppt"] = output.groupby("Ticker")[
        "Revenue YoY Pct"
    ].diff()
    output["Revenue Momentum Score"] = (
        output["Revenue YoY Pct"].fillna(0.0).clip(-100, 100) * 0.6
        + output["Revenue MoM Pct"].fillna(0.0).clip(-100, 100) * 0.25
        + output["Revenue YoY Acceleration Ppt"].fillna(0.0).clip(-100, 100) * 0.15
    )

    group = (
        output.groupby(["Revenue Month", "Sector"], as_index=False)["Monthly Revenue"]
        .sum()
        .sort_values(["Sector", "Revenue Month"], kind="stable")
    )
    group["Group Revenue MoM Pct"] = group.groupby("Sector")["Monthly Revenue"].pct_change() * 100
    group_prior = group[["Revenue Month", "Sector", "Monthly Revenue"]].copy()
    group_prior["Revenue Month"] = group_prior["Revenue Month"] + pd.DateOffset(years=1)
    group_prior = group_prior.rename(columns={"Monthly Revenue": "Prior Year Group Revenue"})
    group = group.merge(
        group_prior,
        on=["Revenue Month", "Sector"],
        how="left",
        validate="one_to_one",
    )
    group["Group Revenue YoY Pct"] = (
        group["Monthly Revenue"] / group["Prior Year Group Revenue"] - 1.0
    ) * 100
    return output.reset_index(drop=True), group.reset_index(drop=True)


# =============================================================================
# def 06. FLOW SIMULATION ENGINE
# =============================================================================


def def_compute_flow_simulation(
    flows: pd.DataFrame,
    prices: pd.DataFrame,
    classification: pd.DataFrame,
    short_window: int = DEFAULT_FLOW_SHORT_WINDOW,
    long_window: int = DEFAULT_FLOW_LONG_WINDOW,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if short_window < 1 or long_window <= short_window:
        raise ContractError("Flow windows require 1 <= short_window < long_window")
    flow_frame = def_normalize_flows(flows)
    price_frame = def_normalize_prices(prices)
    class_frame = def_build_stock_group_classification(classification)
    flow_columns = ["Foreign Net", "Investment Trust Net", "Dealer Net"]
    flow_frame["Institutional Net"] = flow_frame[flow_columns].sum(axis=1)
    merged = flow_frame.merge(
        price_frame[["Date", "Ticker", "Adj Close", "Volume"]],
        on=["Date", "Ticker"],
        how="left",
        validate="one_to_one",
    ).merge(
        class_frame[["Ticker", "Sector"]],
        on="Ticker",
        how="left",
        validate="many_to_one",
    )
    merged["Sector"] = merged["Sector"].fillna("Unclassified")
    merged["Traded Value Proxy"] = merged["Adj Close"].fillna(0.0) * merged["Volume"].fillna(0.0)
    merged["Flow Participation"] = np.where(
        merged["Traded Value Proxy"].abs() > 0,
        merged["Institutional Net"] / merged["Traded Value Proxy"].abs(),
        0.0,
    )
    daily = (
        merged.groupby(["Date", "Sector"], as_index=False)
        .agg(
            Institutional_Net=("Institutional Net", "sum"),
            Traded_Value_Proxy=("Traded Value Proxy", "sum"),
        )
        .sort_values(["Sector", "Date"], kind="stable")
    )
    daily["Flow Participation"] = np.where(
        daily["Traded_Value_Proxy"].abs() > 0,
        daily["Institutional_Net"] / daily["Traded_Value_Proxy"].abs(),
        0.0,
    )
    daily["Flow Short"] = daily.groupby("Sector")["Flow Participation"].transform(
        lambda series: series.rolling(short_window, min_periods=1).mean()
    )
    daily["Flow Long"] = daily.groupby("Sector")["Flow Participation"].transform(
        lambda series: series.rolling(long_window, min_periods=1).mean()
    )
    daily["Flow Score"] = daily["Flow Short"] - daily["Flow Long"]
    daily["Flow Signal"] = np.select(
        [daily["Flow Score"] > 0, daily["Flow Score"] < 0],
        ["BUY_PROXY", "SELL_PROXY"],
        default="NEUTRAL",
    )

    group_index = def_compute_group_index(price_frame, class_frame, "Sector", "equal")
    group_index = group_index.sort_values(["Group", "Date"], kind="stable")
    group_index["Next Group Return"] = group_index.groupby("Group")["Group Return"].shift(-1)
    daily = daily.merge(
        group_index[["Date", "Group", "Next Group Return"]],
        left_on=["Date", "Sector"],
        right_on=["Date", "Group"],
        how="left",
        validate="one_to_one",
    ).drop(columns=["Group"])
    daily["Hit"] = np.where(
        daily["Next Group Return"].isna() | (daily["Flow Signal"] == "NEUTRAL"),
        np.nan,
        np.where(
            ((daily["Flow Signal"] == "BUY_PROXY") & (daily["Next Group Return"] > 0))
            | ((daily["Flow Signal"] == "SELL_PROXY") & (daily["Next Group Return"] < 0)),
            1.0,
            0.0,
        ),
    )
    summary = (
        daily.groupby("Sector", as_index=False)
        .agg(
            Observations=("Date", "count"),
            Actionable_Signals=("Hit", "count"),
            Hit_Rate=("Hit", "mean"),
            Mean_Flow_Score=("Flow Score", "mean"),
        )
        .sort_values("Mean_Flow_Score", ascending=False, kind="stable")
    )
    return daily.reset_index(drop=True), summary.reset_index(drop=True)


# =============================================================================
# def 07. VAP HTML RENDERER
# =============================================================================


def def_svg_group_index(group_index: pd.DataFrame, width: int = 760, height: int = 230) -> str:
    if group_index.empty:
        return '<div class="empty">No Group Index Data</div>'
    plot_left, plot_top, plot_right, plot_bottom = 44, 16, width - 16, height - 34
    dates = sorted(pd.to_datetime(group_index["Date"]).dropna().unique())
    date_positions = {value: index for index, value in enumerate(dates)}
    values = pd.to_numeric(group_index["Group Index"], errors="coerce").dropna()
    if values.empty:
        return '<div class="empty">No Group Index Values</div>'
    y_min, y_max = float(values.min()), float(values.max())
    if y_min == y_max:
        y_min -= 1.0
        y_max += 1.0

    def def_x(value: Any) -> float:
        index = date_positions[pd.Timestamp(value).to_datetime64()]
        denominator = max(len(dates) - 1, 1)
        return plot_left + (plot_right - plot_left) * index / denominator

    def def_y(value: float) -> float:
        return plot_bottom - (plot_bottom - plot_top) * (value - y_min) / (y_max - y_min)

    lines = []
    legend = []
    for position, (group, frame) in enumerate(group_index.groupby("Group", sort=True)):
        color = VAP_PALETTE[position % len(VAP_PALETTE)]
        points = " ".join(
            f"{def_x(date_value):.1f},{def_y(def_safe_float(index_value)):.1f}"
            for date_value, index_value in frame.sort_values("Date")[["Date", "Group Index"]].itertuples(
                index=False, name=None
            )
        )
        lines.append(
            f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2" />'
        )
        legend.append(
            f'<span class="legend-item"><i style="background:{color}"></i>{html.escape(str(group))}</span>'
        )
    return (
        '<div class="legend">' + "".join(legend) + "</div>"
        + f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Group Index">'
        + f'<line x1="{plot_left}" y1="{plot_bottom}" x2="{plot_right}" y2="{plot_bottom}" class="axis" />'
        + f'<line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bottom}" class="axis" />'
        + "".join(lines)
        + f'<text x="4" y="{plot_top + 8}" class="axis-label">{y_max:.1f}</text>'
        + f'<text x="4" y="{plot_bottom}" class="axis-label">{y_min:.1f}</text>'
        + "</svg>"
    )


def def_table_html(frame: pd.DataFrame, limit: int = 12) -> str:
    if frame.empty:
        return '<div class="empty">No Data</div>'
    shown = def_format_csv_dates(frame.head(limit)).copy()
    for column in shown.columns:
        if pd.api.types.is_float_dtype(shown[column]):
            shown[column] = shown[column].map(
                lambda value: "" if pd.isna(value) else f"{float(value):,.3f}"
            )
    return shown.to_html(index=False, border=0, classes="matrix", escape=True)


def def_render_vap_html(
    output_path: Path,
    group_index: pd.DataFrame,
    flow_daily: pd.DataFrame,
    flow_summary: pd.DataFrame,
    revenue_group: pd.DataFrame,
    evidence: Mapping[str, Any],
) -> None:
    latest_flow = flow_daily.sort_values("Date").groupby("Sector", as_index=False).tail(1)
    latest_revenue = revenue_group.sort_values("Revenue Month").groupby(
        "Sector", as_index=False
    ).tail(1)
    gate = html.escape(str(evidence.get("final_gate", "UNKNOWN")))
    generated = html.escape(str(evidence.get("generated_utc", "")))
    document = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA Accelerated Integration · {ENGINE_VERSION}</title>
<style>
:root{{--navy:#102A43;--cream:#F7F3E8;--ink:#17212B;--muted:#637083;--teal:#287271;--gold:#D4A72C;--red:#A63D40;--line:#D9D4C8;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--cream);color:var(--ink);font-family:Inter,"Noto Sans TC",Arial,sans-serif;font-size:12px}}
.shell{{max-width:1480px;margin:auto;padding:18px}} header{{display:grid;grid-template-columns:70px 1fr auto;gap:14px;align-items:center;border-bottom:2px solid var(--navy);padding-bottom:12px}}
.seal{{width:56px;height:56px;border:2px solid var(--red);color:var(--red);display:grid;place-items:center;font:700 27px "Noto Serif TC",serif}}
.brand h1{{font-size:20px;letter-spacing:.09em;margin:0;color:var(--navy)}} .latin{{font-size:10px;letter-spacing:.16em;color:var(--red);margin-top:4px}} .tag{{font-size:11px;color:var(--muted);margin-top:3px}}
.meta{{font:10px "DM Mono",monospace;text-align:right}} .gate{{display:inline-block;padding:5px 8px;border:1px solid var(--teal);color:var(--teal);font-weight:700;max-width:440px;overflow-wrap:anywhere}}
.grid{{display:grid;grid-template-columns:repeat(12,1fr);gap:10px;margin-top:12px}} .panel{{background:#FFFEFA;border:1px solid var(--line);border-radius:7px;padding:11px;min-width:0}}
.span-8{{grid-column:span 8}} .span-4{{grid-column:span 4}} .span-6{{grid-column:span 6}} .span-12{{grid-column:span 12}}
.panel h2{{font-size:12px;letter-spacing:.08em;margin:0 0 8px;color:var(--navy);text-transform:uppercase}} .panel p{{margin:5px 0;color:var(--muted)}}
.matrix{{width:100%;border-collapse:collapse;table-layout:fixed}} .matrix th,.matrix td{{padding:5px;border-bottom:1px solid #E6E2D8;text-align:left;vertical-align:top;overflow-wrap:anywhere;word-break:break-word}}
.matrix th{{font-size:10px;color:#fff;background:var(--navy)}} .matrix td{{font-size:10px}} .legend{{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:4px}} .legend-item{{font-size:9px}} .legend-item i{{display:inline-block;width:8px;height:8px;margin-right:3px}}
.axis{{stroke:#A7AFB8;stroke-width:1}} .axis-label{{font:9px "DM Mono",monospace;fill:#637083}} svg{{width:100%;height:auto;background:#fff}}
.sections{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px}} .section-chip{{border-left:3px solid var(--gold);padding:7px;background:#F8F6F0}} .section-chip b{{display:block;color:var(--navy);font-size:10px}}
.empty{{padding:20px;text-align:center;color:var(--muted)}} footer{{margin-top:12px;font:9px "DM Mono",monospace;color:var(--muted)}}
@media(max-width:900px){{.span-8,.span-4,.span-6{{grid-column:span 12}} header{{grid-template-columns:56px 1fr}} .meta{{grid-column:1/-1;text-align:left}} .sections{{grid-template-columns:1fr 1fr}}}}
</style>
</head>
<body><div class="shell">
<header><div class="seal">理</div><div class="brand"><h1>VERITAS INTELLIGENCE ANALYTICS</h1><div class="latin">DISCIPLINA • PRUDENTIA • INTEGRITAS</div><div class="tag">AI-Powered Research &amp; Decision Intelligence Platform</div></div><div class="meta"><div class="gate">{gate}</div><div>{generated}</div></div></header>
<main class="grid">
<section class="panel span-8"><h2>Group Index · Adjusted Close · Base 100</h2>{def_svg_group_index(group_index)}</section>
<section class="panel span-4"><h2>Flow Simulation · Latest Signal</h2>{def_table_html(latest_flow[["Date","Sector","Flow Score","Flow Signal"]] if not latest_flow.empty else latest_flow, 20)}</section>
<section class="panel span-6"><h2>Flow Simulation · Out-Of-Sample Proxy</h2>{def_table_html(flow_summary, 20)}</section>
<section class="panel span-6"><h2>Monthly Revenue · Group Analysis</h2>{def_table_html(latest_revenue, 20)}</section>
<section class="panel span-12"><h2>Controlled Integration Matrix</h2><div class="sections"><div class="section-chip"><b>MODULE</b>VAP / VDF / Flow Simulation</div><div class="section-chip"><b>ENGINE</b>Five Canonical Candidate Owners</div><div class="section-chip"><b>FUNCTION LIB</b>Adjusted Price / Classification / Revenue / Flow</div><div class="section-chip"><b>OTHERS</b>SSOT / Hydra / SHA / Rollback</div></div></section>
</main><footer>Network Used: 0 · Canonical Runtime Executions: 0 · Visual Palette: Navy / Teal / Gold / Red · Rainbow And Jet Palettes Prohibited</footer>
</div></body></html>"""
    def_atomic_write_text(output_path, document)


def def_validate_vap_visual_lock(path: Path) -> list[str]:
    content = html.unescape(path.read_text(encoding="utf-8"))
    return [token for token in VAP_REQUIRED_TOKENS if token not in content]


# =============================================================================
# def 08. FIXTURE / ORCHESTRATION
# =============================================================================


def def_build_fixture_frames() -> dict[str, pd.DataFrame]:
    tickers = list(DEFAULT_REQUIRED_CODES)
    dates = pd.bdate_range("2026-01-02", periods=12)
    price_rows: list[dict[str, Any]] = []
    flow_rows: list[dict[str, Any]] = []
    for ticker_index, ticker in enumerate(tickers):
        base = 80.0 + ticker_index * 40.0
        for date_index, date in enumerate(dates):
            direction = 1.0 if ticker_index % 2 == 0 else -0.45
            price_rows.append(
                {
                    "Date": date,
                    "Ticker": ticker,
                    "Adj Close": base + date_index * direction + (date_index % 3) * 0.2,
                    "Volume": 1_000_000 + ticker_index * 120_000 + date_index * 8_000,
                    "Market Cap": (base + date_index * direction) * (1_000_000_000 + ticker_index * 100_000_000),
                }
            )
            flow_rows.append(
                {
                    "Date": date,
                    "Ticker": ticker,
                    "Foreign Net": (ticker_index + 1) * (date_index - 4) * 100_000,
                    "Investment Trust Net": (5 - ticker_index) * (date_index - 6) * 20_000,
                    "Dealer Net": ((date_index % 4) - 1.5) * 15_000,
                }
            )
    classification = pd.DataFrame(
        [
            {"Ticker": "2330.TW", "Name": "台積電", "Sector": "Semiconductor", "Industry": "Foundry", "Theme": "AI Infrastructure"},
            {"Ticker": "2317.TW", "Name": "鴻海", "Sector": "Electronics", "Industry": "EMS", "Theme": "AI Server"},
            {"Ticker": "2603.TW", "Name": "長榮", "Sector": "Shipping", "Industry": "Container", "Theme": "Global Trade"},
            {"Ticker": "1101.TW", "Name": "台泥", "Sector": "Materials", "Industry": "Cement", "Theme": "Infrastructure"},
        ]
    )
    revenue_rows: list[dict[str, Any]] = []
    months = pd.date_range("2025-01-01", periods=15, freq="MS")
    for ticker_index, ticker in enumerate(tickers):
        for month_index, month in enumerate(months):
            revenue_rows.append(
                {
                    "Ticker": ticker,
                    "Revenue Month": month,
                    "Monthly Revenue": 10_000_000_000
                    + ticker_index * 1_000_000_000
                    + month_index * (250_000_000 - ticker_index * 20_000_000),
                }
            )
    return {
        "prices": pd.DataFrame(price_rows),
        "classification": classification,
        "flows": pd.DataFrame(flow_rows),
        "revenue": pd.DataFrame(revenue_rows),
    }


def def_build_manifest(run_dir: Path) -> Path:
    manifest_path = run_dir / "MANIFEST.sha256"
    files = [
        path
        for path in run_dir.rglob("*")
        if path.is_file() and path != manifest_path and ".tmp" not in path.name
    ]
    lines = [f"{def_sha256_file(path)}  {path.relative_to(run_dir).as_posix()}" for path in sorted(files)]
    def_atomic_write_text(manifest_path, "\n".join(lines) + "\n")
    return manifest_path


def def_run_pipeline(
    frames: Mapping[str, pd.DataFrame],
    run_dir: Path,
    require_parquet: bool = False,
) -> PipelineResult:
    run_dir.mkdir(parents=True, exist_ok=True)
    output_dir = run_dir / "data"
    error_count = 0
    hydra_count = 0
    unit_pass = 0
    writes: list[WriteResult] = []
    errors: list[str] = []
    try:
        classification = def_build_stock_group_classification(frames["classification"])
        unit_pass += 1
        group_index = def_compute_group_index(frames["prices"], classification)
        unit_pass += 1
        revenue_detail, revenue_group = def_compute_monthly_revenue_analysis(
            frames["revenue"], classification
        )
        unit_pass += 1
        flow_daily, flow_summary = def_compute_flow_simulation(
            frames["flows"], frames["prices"], classification
        )
        unit_pass += 1
        outputs = {
            "VIA_Stock_Group_Classification_v0139A": classification,
            "VIA_Group_Index_v0139A": group_index,
            "VIA_Monthly_Revenue_Detail_v0139A": revenue_detail,
            "VIA_Monthly_Revenue_Group_v0139A": revenue_group,
            "VIA_Flow_Simulation_Daily_v0139A": flow_daily,
            "VIA_Flow_Simulation_Summary_v0139A": flow_summary,
        }
        for stem, frame in outputs.items():
            writes.append(def_write_dual_table(frame, output_dir, stem, require_parquet))
        unit_pass += 6
    except HydraRiskError as error:
        hydra_count += 1
        errors.append(str(error))
        classification = pd.DataFrame()
        group_index = pd.DataFrame()
        revenue_group = pd.DataFrame()
        flow_daily = pd.DataFrame()
        flow_summary = pd.DataFrame()
    except Exception as error:
        error_count += 1
        errors.append(f"{type(error).__name__}: {error}")
        classification = pd.DataFrame()
        group_index = pd.DataFrame()
        revenue_group = pd.DataFrame()
        flow_daily = pd.DataFrame()
        flow_summary = pd.DataFrame()

    parquet_dependency_hold = any(
        result.parquet_status != "PASS" for result in writes
    )
    if error_count != 0 or hydra_count != 0:
        initial_gate = "VIA_ACCELERATED_INTEGRATION_HOLD_FAIL_CLOSED_V0139A"
    elif parquet_dependency_hold:
        initial_gate = "VIA_ACCELERATED_INTEGRATION_READY_WITH_PARQUET_DEPENDENCY_REVIEW_V0139A"
    else:
        initial_gate = "VIA_ACCELERATED_INTEGRATION_PASS_READY_LAUNCHER_ONLY_ACTIVATION_V0139A"
    evidence: dict[str, Any] = {
        "schema": SCHEMA_VERSION,
        "engine_id": ENGINE_ID,
        "version": ENGINE_VERSION,
        "generated_utc": def_utc_now_text(),
        "final_gate": initial_gate,
        "components": list(COMPONENT_IDS),
        "analysis_rounds": 3,
        "repair_rounds": 0,
        "unit_pass": unit_pass,
        "errors": error_count,
        "hydra": hydra_count,
        "network_used": 0,
        "canonical_runtime_executions": 0,
        "base_registry_writes": 0,
        "parquet_dependency_hold": parquet_dependency_hold,
        "writes": [result.__dict__ for result in writes],
        "messages": errors,
    }
    html_path = run_dir / "VIA_Accelerated_Integration_CommandCenter_v0139A.html"
    def_render_vap_html(
        html_path, group_index, flow_daily, flow_summary, revenue_group, evidence
    )
    missing_tokens = def_validate_vap_visual_lock(html_path)
    if missing_tokens:
        error_count += len(missing_tokens)
        evidence["errors"] = error_count
        evidence["messages"].append("Missing Visual Lock: " + ", ".join(missing_tokens))
        evidence["final_gate"] = "VIA_ACCELERATED_INTEGRATION_HOLD_VISUAL_LOCK_V0139A"
    else:
        unit_pass += 1
        evidence["unit_pass"] = unit_pass

    evidence_path = run_dir / "VIA_Accelerated_Integration_Evidence_v0139A.json"
    def_atomic_write_json(evidence_path, evidence)
    manifest_path = def_build_manifest(run_dir)
    return PipelineResult(
        gate=str(evidence["final_gate"]),
        run_dir=str(run_dir),
        html_path=str(html_path),
        evidence_path=str(evidence_path),
        manifest_path=str(manifest_path),
        error_count=error_count,
        hydra_count=hydra_count,
        unit_pass=unit_pass,
        canonical_runtime_executions=0,
        network_used=0,
    )


def def_load_run_frames(arguments: argparse.Namespace) -> dict[str, pd.DataFrame]:
    if arguments.mode == "fixture-uat":
        return def_build_fixture_frames()
    required_paths = {
        "prices": arguments.prices,
        "classification": arguments.classification,
        "flows": arguments.flows,
        "revenue": arguments.revenue,
    }
    missing = [name for name, value in required_paths.items() if not value]
    if missing:
        raise ContractError("Run mode requires paths for: " + ", ".join(missing))
    return {name: def_read_table(Path(value)) for name, value in required_paths.items()}


# =============================================================================
# def 09. CLI
# =============================================================================


def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=ENGINE_ID)
    parser.add_argument("--mode", choices=("fixture-uat", "run"), default="fixture-uat")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--prices")
    parser.add_argument("--classification")
    parser.add_argument("--flows")
    parser.add_argument("--revenue")
    parser.add_argument("--require-parquet", action="store_true")
    return parser


def def_main(argv: Sequence[str] | None = None) -> int:
    parser = def_build_parser()
    arguments = parser.parse_args(argv)
    try:
        frames = def_load_run_frames(arguments)
        result = def_run_pipeline(
            frames,
            Path(arguments.output_dir).resolve(),
            require_parquet=arguments.require_parquet,
        )
    except Exception as error:
        print(f"def Gate : VIA_ACCELERATED_INTEGRATION_HOLD_PRE_FLIGHT_V0139A", file=sys.stderr)
        print(f"def Error: {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    print(f"def Gate                    : {result.gate}")
    print(f"def RunDir                  : {result.run_dir}")
    print(f"def HTML                    : {result.html_path}")
    print(f"def Evidence                : {result.evidence_path}")
    print(f"def Manifest                : {result.manifest_path}")
    print(f"def Errors / Hydra          : {result.error_count} / {result.hydra_count}")
    print(f"def Unit PASS               : {result.unit_pass}")
    print(f"def Canonical Runtime       : {result.canonical_runtime_executions}")
    print(f"def Network Used            : {result.network_used}")
    return 0 if result.error_count == 0 and result.hydra_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(def_main())
