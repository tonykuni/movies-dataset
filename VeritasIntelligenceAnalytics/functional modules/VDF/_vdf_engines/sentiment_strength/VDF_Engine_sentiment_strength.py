# -*- coding: utf-8 -*-
"""
def VDF_Engine_sentiment_strength
Common sentiment scoring utilities.
"""

from __future__ import annotations

import math
from typing import Optional

import numpy as np
import pandas as pd


def def_clip_score(value: float, low: float = 0.0, high: float = 100.0) -> float:
    if value is None:
        return np.nan
    try:
        if math.isnan(float(value)):
            return np.nan
    except Exception:
        return np.nan
    return float(max(low, min(high, float(value))))


def def_classify_strength(score: float) -> str:
    if pd.isna(score):
        return "UNKNOWN"
    score = float(score)
    if score <= 20:
        return "EXTREME_FEAR"
    if score <= 40:
        return "FEAR"
    if score < 60:
        return "NEUTRAL"
    if score < 80:
        return "GREED"
    return "EXTREME_GREED"


def def_calc_zscore(series: pd.Series, window: int = 156, min_periods: int = 52) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    mean = s.rolling(window=window, min_periods=min_periods).mean()
    std = s.rolling(window=window, min_periods=min_periods).std()
    z = (s - mean) / std.replace(0, np.nan)
    return z


def def_zscore_to_strength(zscore: pd.Series, center: float = 50.0, scale: float = 15.0) -> pd.Series:
    z = pd.to_numeric(zscore, errors="coerce")
    score = center + z * scale
    return score.clip(0, 100)


def def_rolling_percentile_score(
    series: pd.Series,
    window: int = 252,
    min_periods: int = 60,
    inverse: bool = False
) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")

    def _rank_last(x: pd.Series) -> float:
        x = pd.Series(x).dropna()
        if len(x) == 0:
            return np.nan
        return float(x.rank(pct=True).iloc[-1] * 100.0)

    score = s.rolling(window=window, min_periods=min_periods).apply(_rank_last, raw=False)

    if inverse:
        score = 100.0 - score

    return score.clip(0, 100)


def def_normalize_percent_column(series: pd.Series) -> pd.Series:
    s = (
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    out = pd.to_numeric(s, errors="coerce")

    if out.dropna().empty:
        return out

    max_value = out.dropna().abs().max()
    if max_value <= 1.5:
        out = out * 100.0

    return out


def def_calc_aaii_strength(df: pd.DataFrame, z_window: int = 156, min_periods: int = 52) -> pd.DataFrame:
    work = df.copy()

    required = ["def_bullish", "def_neutral", "def_bearish"]
    for col in required:
        if col not in work.columns:
            raise ValueError(f"AAII dataframe missing column: {col}")

    work["def_bull_bear_spread"] = work["def_bullish"] - work["def_bearish"]

    denom = work["def_bullish"] + work["def_bearish"]
    work["def_bull_ratio"] = work["def_bullish"] / denom.replace(0, np.nan)

    work["def_aaii_spread_zscore"] = def_calc_zscore(
        work["def_bull_bear_spread"],
        window=z_window,
        min_periods=min_periods,
    )

    work["def_aaii_sentiment_strength"] = def_zscore_to_strength(
        work["def_aaii_spread_zscore"],
        center=50.0,
        scale=15.0,
    )

    work["def_aaii_sentiment_class"] = work["def_aaii_sentiment_strength"].apply(def_classify_strength)
    return work


def def_blend_scores(score_items: list[dict]) -> dict:
    valid = []
    for item in score_items:
        score = item.get("score")
        weight = float(item.get("weight", 0.0))
        name = item.get("name", "UNKNOWN")

        if score is None or pd.isna(score) or weight <= 0:
            continue

        valid.append({"name": name, "score": float(score), "weight": weight})

    if not valid:
        return {
            "def_final_sentiment_strength": np.nan,
            "def_final_sentiment_class": "UNKNOWN",
            "def_components_used": [],
        }

    total_weight = sum(x["weight"] for x in valid)
    blended = sum(x["score"] * x["weight"] for x in valid) / total_weight

    return {
        "def_final_sentiment_strength": def_clip_score(blended),
        "def_final_sentiment_class": def_classify_strength(blended),
        "def_components_used": valid,
    }
