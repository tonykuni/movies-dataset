"""Deterministic, chart-aware row reduction for large VAP renders.

The optimizer is intentionally independent from the renderers.  It never
mutates the caller's frame and always returns an explicit report so lossy
sampling cannot happen silently.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from numbers import Integral
from typing import Any

import numpy as np
import pandas as pd


ENVELOPE_CHART_TYPES = frozenset({"line", "area", "step"})
CANDLESTICK_CHART_TYPE = "candlestick"


def _validate_inputs(
    frame: pd.DataFrame,
    chart: Mapping[str, Any],
    max_points: int,
) -> int:
    if not isinstance(frame, pd.DataFrame):
        raise TypeError("frame 必須是 pandas.DataFrame。")
    if not isinstance(chart, Mapping):
        raise TypeError("chart 必須是 mapping。")
    if isinstance(max_points, bool) or not isinstance(max_points, Integral):
        raise TypeError("max_points 必須是整數。")
    normalized_limit = int(max_points)
    if normalized_limit < 2:
        raise ValueError("max_points 必須至少為 2，才能保留首尾資料點。")
    return normalized_limit


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, Sequence):
        raise TypeError("圖表 series 欄位必須是字串或字串序列。")
    result: list[str] = []
    for item in value:
        text = str(item).strip()
        if text and text not in result:
            result.append(text)
    return result


def _resolve_column(frame: pd.DataFrame, requested: Any, role: str) -> str:
    name = str(requested or "").strip()
    if not name:
        raise ValueError(f"chart 缺少 {role} 欄位 mapping。")
    if name in frame.columns:
        return name

    token = name.casefold()
    matches = [
        str(column)
        for column in frame.columns
        if str(column).strip().casefold() == token
    ]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise ValueError(f"{role} 欄位 {name!r} 有多個不分大小寫的相符欄位。")
    raise ValueError(f"找不到 {role} 欄位：{name}")


def _base_report(
    frame: pd.DataFrame,
    chart_type: str,
    max_points: int,
) -> dict[str, Any]:
    return {
        "optimized": False,
        "lossy": False,
        "method": "none",
        "chart_type": chart_type,
        "input_points": int(len(frame)),
        "output_points": int(len(frame)),
        "max_points": int(max_points),
        "preserved_endpoints": bool(len(frame)),
        "warnings": [],
    }


def _continuous_bucket_bounds(length: int, bucket_count: int) -> list[tuple[int, int]]:
    """Return non-empty half-open, position-based contiguous buckets."""

    boundaries = np.linspace(0, length, num=bucket_count + 1, dtype=np.int64)
    return [
        (int(boundaries[position]), int(boundaries[position + 1]))
        for position in range(bucket_count)
        if boundaries[position] < boundaries[position + 1]
    ]


def _numeric_extreme_position(values: np.ndarray, mode: str) -> int | None:
    finite_positions = np.flatnonzero(~pd.isna(values))
    if not len(finite_positions):
        return None
    finite_values = values[finite_positions]
    relative = int(np.argmin(finite_values) if mode == "min" else np.argmax(finite_values))
    return int(finite_positions[relative])


def _envelope_series(frame: pd.DataFrame, chart: Mapping[str, Any]) -> list[str]:
    requested = [
        *_string_list(chart.get("y")),
        *_string_list(chart.get("secondary_y")),
        *_string_list(chart.get("normalized_y")),
    ]
    result: list[str] = []
    for position, name in enumerate(dict.fromkeys(requested), start=1):
        resolved = _resolve_column(frame, name, f"series {position}")
        if resolved not in result:
            result.append(resolved)
    return result


def _optimize_envelope(
    frame: pd.DataFrame,
    chart: Mapping[str, Any],
    chart_type: str,
    max_points: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    series_names = _envelope_series(frame, chart)
    if not series_names:
        return _optimize_equidistant(frame, chart_type, max_points)

    numeric_values = {
        name: pd.to_numeric(frame[name], errors="coerce").to_numpy(dtype=float)
        for name in series_names
    }
    # A bucket contributes at most first + last + min/max for every series.
    worst_case_points = 2 + (2 * len(series_names))
    bucket_count = max(1, min(len(frame), max_points // worst_case_points))

    while bucket_count >= 1:
        selected: set[int] = set()
        for start, stop in _continuous_bucket_bounds(len(frame), bucket_count):
            selected.add(start)
            selected.add(stop - 1)
            for values in numeric_values.values():
                bucket_values = values[start:stop]
                minimum = _numeric_extreme_position(bucket_values, "min")
                maximum = _numeric_extreme_position(bucket_values, "max")
                if minimum is not None:
                    selected.add(start + minimum)
                if maximum is not None:
                    selected.add(start + maximum)
        selected.add(0)
        selected.add(len(frame) - 1)
        ordered_positions = sorted(selected)
        if len(ordered_positions) <= max_points:
            result = frame.iloc[ordered_positions].copy(deep=True)
            report = _base_report(frame, chart_type, max_points)
            report.update(
                {
                    "optimized": True,
                    "lossy": True,
                    "method": "multi_series_first_min_max_last_envelope",
                    "output_points": int(len(result)),
                    "bucket_count": int(bucket_count),
                    "series": series_names,
                    "preserved_endpoints": True,
                    "warnings": [
                        "已依連續資料桶保留首筆、各 series 極小/極大與末筆；其餘點未送入 renderer。"
                    ],
                }
            )
            return result, report
        bucket_count -= 1

    raise ValueError(
        "max_points 太小，無法同時保留首尾及所有 series 的極值；"
        "請提高 max_points。"
    )


def _candlestick_columns(
    frame: pd.DataFrame,
    chart: Mapping[str, Any],
) -> dict[str, str]:
    columns = {
        role: _resolve_column(frame, chart.get(role), role)
        for role in ("x", "open", "high", "low", "close", "volume")
    }
    if len(set(columns.values())) != len(columns):
        raise ValueError("candlestick 的 x/OHLC/Volume mapping 必須對應不同欄位。")
    return columns


def _numeric_min(series: pd.Series) -> float:
    return pd.to_numeric(series, errors="coerce").min(skipna=True)


def _numeric_max(series: pd.Series) -> float:
    return pd.to_numeric(series, errors="coerce").max(skipna=True)


def _numeric_sum_preserve_missing(series: pd.Series) -> float:
    return pd.to_numeric(series, errors="coerce").sum(min_count=1)


def _optimize_candlestick(
    frame: pd.DataFrame,
    chart: Mapping[str, Any],
    max_points: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    columns = _candlestick_columns(frame, chart)
    bucket_count = min(len(frame), max_points)
    bounds = _continuous_bucket_bounds(len(frame), bucket_count)
    records: list[dict[Any, Any]] = []
    output_indexes: list[Any] = []

    for bucket_position, (start, stop) in enumerate(bounds):
        bucket = frame.iloc[start:stop]
        # Start from each column's last value.  This is deliberate for metadata
        # and normalized overlays; OHLCV roles are replaced below.
        record = bucket.iloc[-1].to_dict()
        x_position = 0 if bucket_position == 0 else -1
        record[columns["x"]] = bucket[columns["x"]].iloc[x_position]
        record[columns["open"]] = bucket[columns["open"]].iloc[0]
        record[columns["high"]] = _numeric_max(bucket[columns["high"]])
        record[columns["low"]] = _numeric_min(bucket[columns["low"]])
        record[columns["close"]] = bucket[columns["close"]].iloc[-1]
        record[columns["volume"]] = _numeric_sum_preserve_missing(
            bucket[columns["volume"]]
        )
        records.append(record)
        output_indexes.append(bucket.index[x_position])

    result = pd.DataFrame(
        records,
        columns=frame.columns,
        index=pd.Index(output_indexes, name=frame.index.name),
    )
    report = _base_report(frame, CANDLESTICK_CHART_TYPE, max_points)
    report.update(
        {
            "optimized": True,
            "lossy": True,
            "method": "ohlcv_contiguous_bucket_aggregation",
            "output_points": int(len(result)),
            "bucket_count": int(len(bounds)),
            "series": list(columns.values()),
            "preserved_endpoints": True,
            "x_label_policy": "first_bucket_start_then_bucket_end",
            "warnings": [
                "K 線已依連續資料桶聚合；Volume 使用 sum(min_count=1)，不以前值或 0 補量。"
            ],
        }
    )
    return result, report


def _equidistant_positions(length: int, max_points: int) -> list[int]:
    positions = np.linspace(0, length - 1, num=max_points, dtype=np.int64)
    positions[0] = 0
    positions[-1] = length - 1
    return np.unique(positions).astype(int).tolist()


def _optimize_equidistant(
    frame: pd.DataFrame,
    chart_type: str,
    max_points: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    positions = _equidistant_positions(len(frame), max_points)
    result = frame.iloc[positions].copy(deep=True)
    report = _base_report(frame, chart_type, max_points)
    report.update(
        {
            "optimized": True,
            "lossy": True,
            "method": "equidistant_sampling",
            "output_points": int(len(result)),
            "preserved_endpoints": True,
            "warnings": [
                f"{chart_type or 'unknown'} 使用等距抽樣；此方法不聚合數值，可能略過局部尖峰。"
            ],
        }
    )
    return result, report


def optimize_frame_for_chart(
    frame: pd.DataFrame,
    chart: Mapping[str, Any],
    max_points: int,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    """Reduce a render frame without mutating it and return an audit report.

    Frames already within ``max_points`` are returned as deep, value-identical
    copies.  Candlesticks use OHLCV aggregation; line/area/step charts use a
    multi-series min/max envelope; all other chart types use explicit lossy
    equidistant sampling.
    """

    normalized_limit = _validate_inputs(frame, chart, max_points)
    chart_type = str(chart.get("type", "")).strip().lower()
    if len(frame) <= normalized_limit:
        return frame.copy(deep=True), _base_report(
            frame,
            chart_type,
            normalized_limit,
        )
    if chart_type == CANDLESTICK_CHART_TYPE:
        return _optimize_candlestick(frame, chart, normalized_limit)
    if chart_type in ENVELOPE_CHART_TYPES:
        return _optimize_envelope(frame, chart, chart_type, normalized_limit)
    return _optimize_equidistant(frame, chart_type, normalized_limit)


__all__ = ["optimize_frame_for_chart"]
