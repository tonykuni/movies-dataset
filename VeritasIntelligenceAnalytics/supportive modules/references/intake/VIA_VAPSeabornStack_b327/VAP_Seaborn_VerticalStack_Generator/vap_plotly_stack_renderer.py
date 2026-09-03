#!/usr/bin/env python3
"""Offline Plotly renderer for VAP vertical chart stacks.

This module is intentionally independent from the Seaborn renderer.  Plotly is
loaded only when :func:`write_plotly_stack_html` is called, so static output
continues to work when the optional interactive dependency is unavailable.
"""

from __future__ import annotations

import json
import math
from decimal import Decimal
from html import escape
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd

from vap_atomic_io import atomic_write_text, file_transaction_lock


# =============================================================================
# 0. Renderer parameters
# =============================================================================

PLOTLY_DEPENDENCY_HINT = "pip install \"plotly>=5,<7\""
DEFAULT_PALETTE = "deep"
DEFAULT_UP_COLOR = "#D62728"
DEFAULT_DOWN_COLOR = "#2CA02C"
DEFAULT_ZERO_COLOR = "#98A2B3"
DEFAULT_BAR_ALPHA = 0.75
DEFAULT_AREA_ALPHA = 0.50
DEFAULT_LINE_WIDTH = 1.65
DEFAULT_CANDLE_WIDTH_RATIO = 0.90
DEFAULT_BAR_WIDTH_RATIO = 0.92
DEFAULT_BAR_GAP_RATIO = 0.03
DEFAULT_TICK_COUNT = 5
DEFAULT_PANEL_HEIGHT_PX = 420
DEFAULT_PRICE_HEIGHT_FRACTION = 0.75
DEFAULT_VOLUME_HEIGHT_FRACTION = 0.25
DEFAULT_MIN_HEIGHT_PX = 480
DEFAULT_BACKGROUND_COLOR = "#F5F7FA"
DEFAULT_PLOT_COLOR = "#FFFFFF"
DEFAULT_GRID_COLOR = "#DCE3EA"
DEFAULT_TEXT_COLOR = "#243247"
DEFAULT_MUTED_COLOR = "#68778B"
NICE_STEP_MANTISSAS = (1.25, 2.0, 2.5, 5.0, 10.0)
SUPPORTED_CHART_TYPES = {
    "line",
    "bar",
    "area",
    "scatter",
    "step",
    "stacked_bar",
    "stacked_area",
    "stacked_bar_100",
    "stacked_area_100",
    "heatmap",
    "candlestick",
}
VAP_PLOT_DIV_ID = "vap-plotly-stack"
VAP_NORMALIZED_CHECKBOX_ID = "vap-normalized-toggle"


# =============================================================================
# 1. Dependency and value helpers
# =============================================================================


def _require_plotly() -> tuple[Any, Any, Any]:
    """Return Plotly modules or raise one actionable optional-dependency error."""

    try:
        import plotly.graph_objects as go
        import plotly.io as pio
        from plotly.subplots import make_subplots
    except ImportError as exc:
        raise RuntimeError(
            "互動式 HTML 需要選用套件 Plotly；請先執行："
            f"{PLOTLY_DEPENDENCY_HINT}"
        ) from exc
    return go, pio, make_subplots


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if isinstance(value, Iterable) and not isinstance(value, (bytes, dict)):
        return [str(item).strip() for item in value if str(item).strip()]
    return [str(value).strip()] if str(value).strip() else []


def _clamp_float(value: Any, default: float, minimum: float, maximum: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    if not math.isfinite(result):
        return default
    return min(maximum, max(minimum, result))


def _numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        raise ValueError(f"圖表欄位不存在：{column}")
    return pd.to_numeric(frame[column], errors="coerce")


def _column_token(value: Any) -> str:
    return "".join(character for character in str(value).casefold() if character.isalnum())


def _resolve_column(
    frame: pd.DataFrame,
    explicit: Any,
    candidates: Iterable[str],
    field_name: str,
    required: bool = True,
) -> str | None:
    column_names = [str(column) for column in frame.columns]
    exact = {name: name for name in column_names}
    normalized = {_column_token(name): name for name in column_names}
    requested = str(explicit).strip() if explicit is not None else ""
    if requested:
        if requested in exact:
            return requested
        match = normalized.get(_column_token(requested))
        if match:
            return match
        if required:
            raise ValueError(f"{field_name} 指定的欄位不存在：{requested}")
        return None
    for candidate in candidates:
        match = normalized.get(_column_token(candidate))
        if match:
            return match
    if required:
        raise ValueError(
            f"無法辨識 {field_name} 欄位；請在 chart 設定明確指定 {field_name}。"
        )
    return None


def _frame_x_values(frame: pd.DataFrame, chart: dict[str, Any]) -> pd.Series:
    x_column = str(chart.get("x", "")).strip()
    if not x_column:
        raise ValueError("每張圖都必須指定 chart.x。")
    if x_column not in frame.columns:
        raise ValueError(f"X 軸欄位不存在：{x_column}")
    values = frame[x_column]
    if pd.api.types.is_datetime64_any_dtype(values):
        return values
    if pd.api.types.is_numeric_dtype(values):
        return values
    converted = pd.to_datetime(values, errors="coerce")
    if bool(converted.notna().all()) and not values.empty:
        return converted
    return values


def _ensure_panel(panel: dict[str, Any], index: int) -> tuple[dict[str, Any], pd.DataFrame]:
    if not isinstance(panel, dict):
        raise TypeError(f"panels[{index}] 必須是 dict。")
    chart = panel.get("chart")
    frame = panel.get("frame")
    if not isinstance(chart, dict):
        raise TypeError(f"panels[{index}].chart 必須是 dict。")
    if not isinstance(frame, pd.DataFrame):
        raise TypeError(f"panels[{index}].frame 必須是 pandas DataFrame。")
    chart_type = str(chart.get("type", "line")).strip().lower()
    if chart_type not in SUPPORTED_CHART_TYPES:
        raise ValueError(
            f"不支援的 Plotly 圖型：{chart_type}；可用類型："
            f"{', '.join(sorted(SUPPORTED_CHART_TYPES))}"
        )
    if frame.empty:
        raise ValueError(f"panels[{index}].frame 沒有可繪製資料。")
    result = dict(chart)
    result["type"] = chart_type
    return result, frame.copy()


# =============================================================================
# 2. Seaborn-compatible color handling
# =============================================================================


def seaborn_palette_to_hex(palette: Any, color_count: int) -> list[str]:
    """Convert a Seaborn palette name/list into Plotly-ready hex colors."""

    if color_count <= 0:
        return []
    try:
        import seaborn as sns
        from matplotlib.colors import to_hex
    except ImportError as exc:
        raise RuntimeError(
            "Seaborn 配色轉換需要 seaborn 與 matplotlib；請先安裝專案 requirements.txt。"
        ) from exc

    selected = palette if palette not in (None, "") else DEFAULT_PALETTE
    try:
        colors = sns.color_palette(selected, n_colors=color_count)
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"無法解析 Seaborn palette：{selected!r}") from exc
    return [to_hex(color, keep_alpha=False).upper() for color in colors]


def _series_color_map(
    project: dict[str, Any],
    chart: dict[str, Any],
    names: list[str],
) -> dict[str, str]:
    palette = chart.get("palette") or project.get("palette") or DEFAULT_PALETTE
    palette_colors = seaborn_palette_to_hex(palette, max(1, len(names)))
    configured: dict[str, Any] = {}
    if isinstance(project.get("series_colors"), dict):
        configured.update(project["series_colors"])
    if isinstance(chart.get("series_colors"), dict):
        configured.update(chart["series_colors"])
    result: dict[str, str] = {}
    for position, name in enumerate(names):
        result[name] = str(configured.get(name) or palette_colors[position % len(palette_colors)])
    return result


def _normalized_name_list(chart: dict[str, Any], available: list[str]) -> list[str]:
    value = chart.get("normalized_y", [])
    if value is True:
        return list(dict.fromkeys(available))
    if value in (False, None, ""):
        return []
    if isinstance(value, dict):
        return [str(name) for name, enabled in value.items() if bool(enabled)]
    return list(dict.fromkeys(_as_string_list(value)))


def _normalized_names(chart: dict[str, Any], available: list[str]) -> set[str]:
    return set(_normalized_name_list(chart, available))


def _trace_visibility(name: str, normalized_names: set[str]) -> tuple[Any, dict[str, Any]]:
    if name in normalized_names:
        return "legendonly", {"vap_normalized_y": True, "vap_series": name}
    return True, {"vap_normalized_y": False, "vap_series": name}


# =============================================================================
# 3. Axis range and formatting
# =============================================================================


def _next_nice_step(raw_step: float) -> float:
    if not math.isfinite(raw_step) or raw_step <= 0:
        return 1.0
    exponent = math.floor(math.log10(raw_step))
    scale = 10.0**exponent
    mantissa = raw_step / scale
    for candidate in NICE_STEP_MANTISSAS:
        if candidate + 1e-12 >= mantissa:
            return candidate * scale
    return 10.0 * scale


def _tick_decimals(step: float) -> int:
    if not math.isfinite(step) or step <= 0:
        return 0
    # Round away IEEE-754 noise before asking Decimal for display precision.
    # Without this, 0.1 + 0.2 can become 0.30000000000000004 and force eight
    # meaningless decimal places across the whole axis.
    rounded = round(abs(float(step)), 12)
    decimal_step = Decimal(f"{rounded:.12f}").normalize()
    return min(8, max(0, -decimal_step.as_tuple().exponent))


def _tick_label(
    value: float,
    step: float,
    y_format: str,
    decimals: int | None = None,
) -> str:
    if y_format == "magnitude":
        absolute_step = abs(step)
        for scale, suffix in (
            (1_000_000_000.0, "B"),
            (1_000_000.0, "M"),
            (1_000.0, "K"),
        ):
            if absolute_step >= scale or abs(value) >= scale:
                scaled_step = step / scale
                decimals = max(1, _tick_decimals(scaled_step))
                scaled_value = 0.0 if abs(value) < max(step, 1.0) * 1e-12 else value / scale
                return f"{scaled_value:,.{decimals}f}{suffix}"
        return f"{value:.1f}"
    decimals = _tick_decimals(step) if decimals is None else max(0, int(decimals))
    if y_format == "number":
        decimals = max(2, decimals)
    if abs(value) < max(step, 1.0) * 1e-12:
        value = 0.0
    label = f"{value:,.{decimals}f}"
    return f"{label}%" if y_format == "percent" else label


def _fixed_ticks(
    values: Iterable[Any],
    tick_count: int,
    include_zero: bool,
    y_format: str,
) -> tuple[list[float], list[str], list[float]] | None:
    numeric = pd.to_numeric(pd.Series(list(values), dtype="object"), errors="coerce")
    finite = numeric[np.isfinite(numeric.to_numpy(dtype=float, na_value=np.nan))]
    if finite.empty:
        return None
    minimum = float(finite.min())
    maximum = float(finite.max())
    if include_zero:
        minimum = min(0.0, minimum)
        maximum = max(0.0, maximum)
    intervals = max(1, int(tick_count) - 1)
    span = maximum - minimum
    if span <= 0:
        reference = max(abs(maximum), 1.0)
        minimum -= reference * 0.02
        maximum += reference * 0.02
        span = maximum - minimum
    step = _next_nice_step(span / intervals)
    total = step * intervals
    padding = max(0.0, total - span)
    if include_zero and minimum >= 0:
        lower = 0.0
    elif include_zero and maximum <= 0:
        lower = -total
    else:
        lower = minimum - padding / 2.0
    upper = lower + total
    if upper < maximum:
        upper = maximum
        lower = upper - total
    if lower > minimum:
        lower = minimum
        upper = lower + total
    tick_values = [lower + step * index for index in range(intervals + 1)]
    tick_values = [0.0 if abs(value) < step * 1e-12 else float(value) for value in tick_values]
    # A valid nice step can be integral while the tight range begins at a
    # fractional quantum (for example 98.50 + n * 2).  Formatting only from
    # the step would silently relabel 98.50 as 98.  Use one precision for the
    # whole axis so every fractional tick and its trailing zero remain visible.
    tick_decimals = max(
        [_tick_decimals(step), *(_tick_decimals(abs(value)) for value in tick_values)]
    )
    tick_text = [
        _tick_label(value, step, y_format, decimals=tick_decimals)
        for value in tick_values
    ]
    return tick_values, tick_text, [float(lower), float(upper)]


def _apply_axis_ticks(
    figure: Any,
    row: int,
    values: list[Any],
    chart: dict[str, Any],
    secondary: bool,
    force_include_zero: bool,
) -> None:
    if not values or str(chart.get("tick_policy", "vap_locked")) != "vap_locked":
        return
    tick_count = max(2, int(chart.get("tick_count", DEFAULT_TICK_COUNT)))
    axis_policy = str(chart.get("axis_zero_policy", "auto"))
    include_zero = force_include_zero or axis_policy == "include"
    y_format_key = "secondary_y_format" if secondary else "y_format"
    result = _fixed_ticks(values, tick_count, include_zero, str(chart.get(y_format_key, "auto")))
    if result is None:
        return
    tick_values, tick_text, axis_range = result
    figure.update_yaxes(
        tickmode="array",
        tickvals=tick_values,
        ticktext=tick_text,
        range=axis_range,
        row=row,
        col=1,
        secondary_y=secondary,
    )


def _axis_reference(layout_name: str) -> str:
    return "y" if layout_name == "yaxis" else f"y{layout_name.removeprefix('yaxis')}"


def _attach_normalized_overlay_axis(
    figure: Any,
    row: int,
    trace_indices: list[int],
    values: list[Any],
    chart: dict[str, Any],
) -> None:
    """Give normalized traces an independent hidden-scale overlay axis.

    This prevents a 0–1 or z-score series from disappearing when the existing
    right axis contains million-unit volume, while hover still exposes the
    original normalized values.
    """

    if not trace_indices or not values:
        return
    existing_numbers = [
        1 if str(name) == "yaxis" else int(str(name).removeprefix("yaxis"))
        for name in figure.layout
        if str(name).startswith("yaxis")
    ]
    axis_number = max(existing_numbers, default=0) + 1
    layout_name = f"yaxis{axis_number}"
    trace_reference = f"y{axis_number}"
    subplot = figure.get_subplot(row, 1)
    primary_layout_name = str(subplot.yaxis._plotly_name)
    primary_reference = _axis_reference(primary_layout_name)
    x_domain = list(subplot.xaxis.domain or [0.0, 1.0])
    tick_count = max(2, int(chart.get("tick_count", DEFAULT_TICK_COUNT)))
    tick_result = _fixed_ticks(values, tick_count, True, "number")
    axis_config: dict[str, Any] = {
        "overlaying": primary_reference,
        "anchor": "free",
        "position": float(x_domain[-1]),
        "side": "right",
        "showgrid": False,
        "showticklabels": False,
        "zeroline": True,
        "zerolinecolor": DEFAULT_ZERO_COLOR,
        "fixedrange": False,
    }
    if tick_result is not None:
        tick_values, tick_text, axis_range = tick_result
        axis_config.update(
            {
                "tickmode": "array",
                "tickvals": tick_values,
                "ticktext": tick_text,
                "range": axis_range,
            }
        )
    figure.update_layout({layout_name: axis_config})
    for trace_index in trace_indices:
        figure.data[trace_index].update(yaxis=trace_reference)


# =============================================================================
# 4. Trace builders
# =============================================================================


def _bar_width(x_values: pd.Series, width_ratio: float) -> float | None:
    if len(x_values) < 2:
        return None
    if pd.api.types.is_datetime64_any_dtype(x_values):
        numeric = pd.Series(pd.to_datetime(x_values, errors="coerce").astype("int64") / 1_000_000.0)
    else:
        numeric = pd.to_numeric(x_values, errors="coerce")
    differences = numeric.sort_values().diff().dropna()
    differences = differences[differences > 0]
    if differences.empty:
        return None
    return float(differences.min()) * width_ratio


def _bar_width_ratio(chart: dict[str, Any]) -> float:
    configured = chart.get("bar_width_ratio")
    if configured is None:
        configured = chart.get("candle_width_ratio")
    return _clamp_float(configured, DEFAULT_BAR_WIDTH_RATIO, 0.10, 0.98)


def _percent100_values(frame: pd.DataFrame, columns: list[str]) -> dict[str, pd.Series]:
    numeric = pd.DataFrame({name: _numeric_series(frame, name) for name in columns})
    denominator = numeric.abs().sum(axis=1).replace(0.0, np.nan)
    return {name: numeric[name].divide(denominator).multiply(100.0) for name in columns}


def _stack_axis_values(frame: pd.DataFrame, columns: list[str], percent100: bool) -> list[Any]:
    if percent100:
        return [0.0, 100.0]
    numeric = pd.DataFrame({name: _numeric_series(frame, name) for name in columns})
    positive = numeric.clip(lower=0.0).sum(axis=1)
    negative = numeric.clip(upper=0.0).sum(axis=1)
    return [*positive.tolist(), *negative.tolist()]


def _add_xy_trace(
    figure: Any,
    go: Any,
    row: int,
    x_values: pd.Series,
    y_values: pd.Series,
    name: str,
    color: str,
    trace_type: str,
    chart: dict[str, Any],
    normalized_names: set[str],
    secondary_y: bool,
    offset_group: str,
    stack_group: str | None = None,
    group_norm: str | None = None,
) -> None:
    visible, meta = _trace_visibility(name, normalized_names)
    line_width_key = "secondary_line_width" if secondary_y else "line_width"
    alpha_key = "secondary_alpha" if secondary_y else "alpha"
    line_width = _clamp_float(
        chart.get(line_width_key),
        1.35 if secondary_y else DEFAULT_LINE_WIDTH,
        0.25,
        8.0,
    )
    line_alpha = _clamp_float(chart.get(alpha_key), 0.88 if secondary_y else 1.0, 0.0, 1.0)
    bar_alpha = _clamp_float(chart.get("bar_alpha"), DEFAULT_BAR_ALPHA, 0.05, 1.0)
    area_alpha = _clamp_float(chart.get("area_alpha"), DEFAULT_AREA_ALPHA, 0.05, 1.0)
    width_ratio = _bar_width_ratio(chart)
    if trace_type in {"bar", "stacked_bar", "stacked_bar_100"}:
        trace = go.Bar(
            x=x_values,
            y=y_values,
            name=name,
            marker={"color": color, "line": {"width": 0}},
            opacity=bar_alpha,
            width=_bar_width(x_values, width_ratio),
            offsetgroup=offset_group,
            visible=visible,
            meta=meta,
            hovertemplate=f"%{{x}}<br>{escape(name)}: %{{y:,.4g}}<extra></extra>",
        )
    elif trace_type == "scatter":
        trace = go.Scatter(
            x=x_values,
            y=y_values,
            name=name,
            mode="markers",
            marker={"color": color, "size": 5.5, "opacity": 0.88},
            visible=visible,
            meta=meta,
            hovertemplate=f"%{{x}}<br>{escape(name)}: %{{y:,.4g}}<extra></extra>",
        )
    else:
        line_shape = "hv" if trace_type == "step" else "linear"
        fill_value = "tozeroy" if trace_type == "area" else None
        trace = go.Scatter(
            x=x_values,
            y=y_values,
            name=name,
            mode="lines",
            line={"color": color, "width": line_width, "shape": line_shape},
            fill=fill_value,
            fillcolor=color,
            opacity=area_alpha if trace_type in {"area", "stacked_area", "stacked_area_100"} else line_alpha,
            stackgroup=stack_group,
            groupnorm=group_norm,
            visible=visible,
            meta=meta,
            hovertemplate=f"%{{x}}<br>{escape(name)}: %{{y:,.4g}}<extra></extra>",
        )
    figure.add_trace(trace, row=row, col=1, secondary_y=secondary_y)


def _candlestick_columns(frame: pd.DataFrame, chart: dict[str, Any]) -> dict[str, str | None]:
    return {
        "open": _resolve_column(
            frame,
            chart.get("open"),
            ("AdjOpen", "Adj Open", "Adjusted Open", "Open"),
            "open",
        ),
        "high": _resolve_column(
            frame,
            chart.get("high"),
            ("AdjHigh", "Adj High", "Adjusted High", "High"),
            "high",
        ),
        "low": _resolve_column(
            frame,
            chart.get("low"),
            ("AdjLow", "Adj Low", "Adjusted Low", "Low"),
            "low",
        ),
        "close": _resolve_column(
            frame,
            chart.get("close"),
            ("AdjClose", "Adj Close", "Adjusted Close", "Close"),
            "close",
        ),
        "volume": _resolve_column(
            frame,
            chart.get("volume"),
            ("Volume", "TurnoverVolume", "Turnover Volume", "成交量"),
            "volume",
            required=False,
        ),
    }


def _add_candlestick_panel(
    figure: Any,
    go: Any,
    row: int,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    x_values: pd.Series,
    normalized_names: set[str],
    volume_row: int | None = None,
) -> tuple[list[Any], list[Any]]:
    columns = _candlestick_columns(frame, chart)
    open_values = _numeric_series(frame, str(columns["open"])).ffill()
    high_values = _numeric_series(frame, str(columns["high"])).ffill()
    low_values = _numeric_series(frame, str(columns["low"])).ffill()
    close_values = _numeric_series(frame, str(columns["close"])).ffill()
    up_color = str(chart.get("up_color") or DEFAULT_UP_COLOR)
    down_color = str(chart.get("down_color") or DEFAULT_DOWN_COLOR)
    candle_width_ratio = _clamp_float(
        chart.get("candle_width_ratio"), DEFAULT_CANDLE_WIDTH_RATIO, 0.10, 0.98
    )
    volume_width_ratio = _bar_width_ratio(chart)
    candle_name = str(chart.get("name") or chart.get("title") or "OHLC")
    candle_visible, candle_meta = _trace_visibility(candle_name, normalized_names)
    figure.add_trace(
        go.Candlestick(
            x=x_values,
            open=open_values,
            high=high_values,
            low=low_values,
            close=close_values,
            name=candle_name,
            increasing={"line": {"color": up_color}, "fillcolor": up_color},
            decreasing={"line": {"color": down_color}, "fillcolor": down_color},
            whiskerwidth=candle_width_ratio,
            visible=candle_visible,
            meta={**candle_meta, "vap_candle_width_ratio": candle_width_ratio},
        ),
        row=row,
        col=1,
        secondary_y=False,
    )
    primary_values: list[Any] = [*open_values, *high_values, *low_values, *close_values]
    secondary_values: list[Any] = []

    volume_column = columns["volume"]
    if volume_column:
        volume_values = _numeric_series(frame, volume_column)
        volume_plot_values = [
            None if pd.isna(value) else float(value) for value in volume_values
        ]
        bar_alpha = _clamp_float(chart.get("bar_alpha"), DEFAULT_BAR_ALPHA, 0.05, 1.0)
        colors = np.where(close_values >= open_values, up_color, down_color).tolist()
        volume_visible, volume_meta = _trace_visibility(volume_column, normalized_names)
        figure.add_trace(
            go.Bar(
                x=x_values,
                y=volume_plot_values,
                name=volume_column,
                marker={"color": colors, "line": {"width": 0}},
                opacity=bar_alpha,
                width=_bar_width(x_values, volume_width_ratio),
                offsetgroup=f"vap-volume-{row}",
                visible=volume_visible,
                meta={**volume_meta, "vap_candle_volume": True},
                hovertemplate=f"%{{x}}<br>{escape(volume_column)}: %{{y:,.4g}}<extra></extra>",
            ),
            row=volume_row or row,
            col=1,
            secondary_y=volume_row is None,
        )
        secondary_values.extend(volume_values.tolist())
    return primary_values, secondary_values


def _add_heatmap_panel(
    figure: Any,
    go: Any,
    row: int,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    x_values: pd.Series,
) -> None:
    y_columns = _as_string_list(chart.get("y"))
    if not y_columns:
        raise ValueError("heatmap 至少需要一個 chart.y 欄位。")
    z_values = np.vstack([_numeric_series(frame, name).to_numpy() for name in y_columns])
    figure.add_trace(
        go.Heatmap(
            x=x_values,
            y=y_columns,
            z=z_values,
            colorscale=str(chart.get("colorscale") or chart.get("cmap") or "RdYlGn"),
            colorbar={"thickness": 10, "len": 0.75},
            name=str(chart.get("title") or "Heatmap"),
            hovertemplate="%{x}<br>%{y}: %{z:,.4g}<extra></extra>",
        ),
        row=row,
        col=1,
    )


def _add_standard_panel(
    figure: Any,
    go: Any,
    row: int,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    x_values: pd.Series,
    project: dict[str, Any],
) -> tuple[list[Any], list[Any], list[Any], list[int]]:
    chart_type = str(chart["type"])
    primary_names = _as_string_list(chart.get("y"))
    secondary_names = _as_string_list(chart.get("secondary_y"))
    if (
        str(chart.get("axis_mode", "auto")) == "single"
        or chart_type in {"heatmap", "stacked_bar", "stacked_area", "stacked_bar_100", "stacked_area_100"}
    ):
        secondary_names = []
    if not primary_names and not secondary_names:
        raise ValueError(f"{chart_type} 至少需要一個 y 或 secondary_y 欄位。")
    requested_normalized = _normalized_name_list(chart, [*primary_names, *secondary_names])
    extra_normalized_names = [
        name
        for name in requested_normalized
        if name not in primary_names and name not in secondary_names
    ]
    all_names = [*primary_names, *secondary_names, *extra_normalized_names]
    colors = _series_color_map(project, chart, all_names)
    normalized_names = _normalized_names(chart, all_names)
    primary_values: list[Any] = []
    secondary_values: list[Any] = []
    normalized_values: list[Any] = []
    normalized_trace_indices: list[int] = []
    percent_values = (
        _percent100_values(frame, primary_names)
        if chart_type in {"stacked_bar_100", "stacked_area_100"}
        else {}
    )

    for position, name in enumerate(primary_names):
        y_values = percent_values.get(name, _numeric_series(frame, name))
        if name in normalized_names:
            normalized_values.extend(y_values.tolist())
            normalized_trace_indices.append(len(figure.data))
        else:
            primary_values.extend(y_values.tolist())
        stack_group = f"vap-stack-{row}" if chart_type in {"stacked_area", "stacked_area_100"} else None
        group_norm = "percent" if chart_type == "stacked_area_100" else None
        offset_group = f"vap-stack-{row}" if chart_type in {"stacked_bar", "stacked_bar_100"} else f"vap-bar-{row}-{position}"
        _add_xy_trace(
            figure,
            go,
            row,
            x_values,
            y_values,
            name,
            colors[name],
            chart_type,
            chart,
            normalized_names,
            False,
            offset_group,
            stack_group,
            group_norm,
        )

    if chart_type in {"stacked_bar", "stacked_area", "stacked_bar_100", "stacked_area_100"}:
        primary_values = _stack_axis_values(
            frame,
            primary_names,
            chart_type in {"stacked_bar_100", "stacked_area_100"},
        )

    secondary_type = str(chart.get("secondary_type", "line")).strip().lower()
    if secondary_type not in {"line", "bar", "area", "scatter", "step"}:
        secondary_type = "line"
    for position, name in enumerate(secondary_names):
        y_values = _numeric_series(frame, name)
        if name in normalized_names:
            normalized_values.extend(y_values.tolist())
            normalized_trace_indices.append(len(figure.data))
        else:
            secondary_values.extend(y_values.tolist())
        _add_xy_trace(
            figure,
            go,
            row,
            x_values,
            y_values,
            name,
            colors[name],
            secondary_type,
            chart,
            normalized_names,
            True,
            f"vap-secondary-{row}-{position}",
        )
    for position, name in enumerate(extra_normalized_names):
        y_values = _numeric_series(frame, name)
        normalized_values.extend(y_values.tolist())
        normalized_trace_indices.append(len(figure.data))
        _add_xy_trace(
            figure,
            go,
            row,
            x_values,
            y_values,
            name,
            colors[name],
            "line",
            chart,
            normalized_names,
            False,
            f"vap-normalized-{row}-{position}",
        )
    return primary_values, secondary_values, normalized_values, normalized_trace_indices


# =============================================================================
# 5. Figure and HTML assembly
# =============================================================================


def _panel_has_secondary_axis(chart: dict[str, Any], frame: pd.DataFrame) -> bool:
    chart_type = str(chart["type"])
    if chart_type in {"heatmap", "stacked_bar", "stacked_area", "stacked_bar_100", "stacked_area_100"}:
        return False
    if chart_type == "candlestick":
        return False
    if str(chart.get("axis_mode", "auto")) == "single":
        return False
    primary_names = _as_string_list(chart.get("y"))
    secondary_names = _as_string_list(chart.get("secondary_y"))
    return (
        bool(secondary_names)
        or str(chart.get("axis_mode")) == "dual"
    )


def _candlestick_height_fractions(chart: dict[str, Any]) -> tuple[float, float]:
    price_fraction = _clamp_float(
        chart.get("price_height_fraction"),
        DEFAULT_PRICE_HEIGHT_FRACTION,
        0.05,
        0.95,
    )
    volume_fraction = _clamp_float(
        chart.get("volume_height_fraction"),
        DEFAULT_VOLUME_HEIGHT_FRACTION,
        0.05,
        0.95,
    )
    total = price_fraction + volume_fraction
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError(
            "price_height_fraction + volume_height_fraction 必須等於 1。"
        )
    return price_fraction, volume_fraction


def _expand_render_rows(
    prepared: list[tuple[dict[str, Any], pd.DataFrame]],
) -> list[dict[str, Any]]:
    """Expand OHLCV into price/volume rows while preserving logical order."""

    rows: list[dict[str, Any]] = []
    for logical_index, (chart, frame) in enumerate(prepared):
        if chart["type"] != "candlestick":
            rows.append(
                {
                    "chart": chart,
                    "frame": frame,
                    "logical_chart": chart,
                    "logical_index": logical_index,
                    "role": "chart",
                }
            )
            continue
        columns = _candlestick_columns(frame, chart)
        total_height = _clamp_float(chart.get("height_ratio"), 1.0, 0.25, 4.0)
        price_fraction, volume_fraction = _candlestick_height_fractions(chart)
        price_chart = dict(chart)
        price_chart.update(
            {
                "axis_mode": "single",
                "secondary_y": [],
                "height_ratio": total_height * price_fraction,
            }
        )
        rows.append(
            {
                "chart": price_chart,
                "frame": frame,
                "logical_chart": chart,
                "logical_index": logical_index,
                "role": "candlestick_price",
            }
        )
        if columns["volume"] is None:
            price_chart["height_ratio"] = total_height
            continue
        volume_chart = dict(chart)
        volume_chart.update(
            {
                "type": "bar",
                "title": str(
                    chart.get("volume_title")
                    or chart.get("volume_label")
                    or columns["volume"]
                    or "Volume"
                ),
                "axis_mode": "single",
                "y": [str(columns["volume"])],
                "secondary_y": [],
                "unit": str(chart.get("secondary_unit") or columns["volume"] or "Volume"),
                "y_format": str(chart.get("secondary_y_format", "magnitude")),
                "axis_zero_policy": "include",
                "height_ratio": total_height * volume_fraction,
            }
        )
        rows.append(
            {
                "chart": volume_chart,
                "frame": frame,
                "logical_chart": chart,
                "logical_index": logical_index,
                "role": "candlestick_volume",
            }
        )
    return rows


def _figure_height(project: dict[str, Any], charts: list[dict[str, Any]]) -> int:
    base_panel_height = int(
        project.get(
            "standard_panel_height_px",
            project.get("panel_height_px", DEFAULT_PANEL_HEIGHT_PX),
        )
    )
    weighted_height = sum(
        # ``charts`` are physical render rows.  A standard-height candle uses
        # 0.75 + 0.25 rows; clamping the volume row to 0.35 changes the logical
        # chart height.  The public logical editor already validates 0.25–4x.
        base_panel_height * _clamp_float(chart.get("height_ratio"), 1.0, 0.05, 4.0)
        for chart in charts
    )
    return max(DEFAULT_MIN_HEIGHT_PX, int(155 + weighted_height))


def _normalized_checkbox_markup(has_normalized: bool) -> str:
    if not has_normalized:
        return ""
    return (
        f'<label class="vap-normalized-control" for="{VAP_NORMALIZED_CHECKBOX_ID}">'
        f'<input id="{VAP_NORMALIZED_CHECKBOX_ID}" type="checkbox">'
        "顯示標準化資料（Normalized）</label>"
    )


def _normalized_checkbox_script(has_normalized: bool) -> str:
    if not has_normalized:
        return ""
    return f"""
<script>
(function () {{
  const checkbox = document.getElementById({json.dumps(VAP_NORMALIZED_CHECKBOX_ID)});
  const graph = document.getElementById({json.dumps(VAP_PLOT_DIV_ID)});
  if (!checkbox || !graph || typeof Plotly === "undefined") return;
  const normalizedIndices = [];
  (graph.data || []).forEach(function (trace, index) {{
    if (trace.meta && trace.meta.vap_normalized_y === true) normalizedIndices.push(index);
  }});
  checkbox.addEventListener("change", function () {{
    Plotly.restyle(
      graph,
      {{visible: checkbox.checked ? true : "legendonly"}},
      normalizedIndices
    );
  }});
}})();
</script>
"""


def _html_document(
    project: dict[str, Any],
    plot_fragment: str,
    has_normalized: bool,
) -> str:
    title = escape(str(project.get("title") or "VAP Plotly Chart Stack"))
    subtitle = escape(str(project.get("subtitle") or ""))
    source = escape(str(project.get("source") or project.get("source_label") or ""))
    checkbox = _normalized_checkbox_markup(has_normalized)
    checkbox_script = _normalized_checkbox_script(has_normalized)
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline' 'unsafe-eval'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; connect-src 'none'; worker-src blob:">
  <title>{title}</title>
  <style>
    :root {{ color-scheme: light; font-family: Inter, "Noto Sans TC", "Microsoft JhengHei", sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: {DEFAULT_BACKGROUND_COLOR}; color: {DEFAULT_TEXT_COLOR}; }}
    .vap-shell {{ width: min(100%, 1920px); margin: 0 auto; padding: 12px 14px 16px; }}
    .vap-toolbar {{ display: flex; align-items: center; flex-wrap: wrap; gap: 8px 18px; padding: 8px 10px; background: #fff; border: 1px solid #E2E8F0; border-radius: 8px; }}
    .vap-heading {{ min-width: 240px; flex: 1 1 auto; }}
    .vap-heading h1 {{ margin: 0; font-size: 17px; font-weight: 700; }}
    .vap-heading p {{ margin: 3px 0 0; color: {DEFAULT_MUTED_COLOR}; font-size: 11px; }}
    .vap-normalized-control {{ display: inline-flex; align-items: center; gap: 7px; color: {DEFAULT_MUTED_COLOR}; font-size: 12px; cursor: pointer; user-select: none; }}
    .vap-normalized-control input {{ accent-color: #4C78A8; }}
    .vap-chart {{ min-width: 0; margin-top: 8px; overflow: hidden; background: #fff; border: 1px solid #E2E8F0; border-radius: 8px; }}
    .vap-source {{ margin: 5px 4px 0; color: {DEFAULT_MUTED_COLOR}; font-size: 10px; text-align: right; }}
    @media (max-width: 720px) {{ .vap-shell {{ padding: 6px; }} .vap-toolbar {{ border-radius: 5px; }} .vap-chart {{ border-radius: 5px; }} }}
  </style>
</head>
<body>
  <main class="vap-shell">
    <header class="vap-toolbar">
      <div class="vap-heading"><h1>{title}</h1><p>{subtitle}</p></div>
      {checkbox}
    </header>
    <section class="vap-chart">{plot_fragment}</section>
    <p class="vap-source">{source}</p>
  </main>
  {checkbox_script}
</body>
</html>
"""


def write_plotly_stack_html(
    output_path: Path,
    project: dict[str, Any],
    panels: list[dict[str, Any]],
) -> Path:
    """Write one responsive, self-contained Plotly vertical stack HTML file.

    ``panels`` must contain ``{"chart": chart_spec, "frame": DataFrame}``
    records.  Price gaps inside candlesticks are forward-filled, while volume
    is deliberately left missing.  The function never downloads JavaScript or
    writes any PDF output.
    """

    go, pio, make_subplots = _require_plotly()
    if not isinstance(project, dict):
        raise TypeError("project 必須是 dict。")
    if not panels:
        raise ValueError("panels 至少需要一張圖。")

    prepared = [_ensure_panel(panel, index) for index, panel in enumerate(panels)]
    render_rows = _expand_render_rows(prepared)
    charts = [dict(row["chart"]) for row in render_rows]
    row_specs = [
        [{"secondary_y": _panel_has_secondary_axis(row["chart"], row["frame"])}]
        for row in render_rows
    ]
    row_heights = [
        _clamp_float(chart.get("height_ratio"), 1.0, 0.05, 4.0)
        for chart in charts
    ]
    spacing = min(0.055, max(0.012, 0.12 / len(render_rows)))
    figure = make_subplots(
        rows=len(render_rows),
        cols=1,
        shared_xaxes=bool(project.get("shared_x", True)),
        vertical_spacing=spacing,
        row_heights=row_heights,
        specs=row_specs,
        subplot_titles=[str(chart.get("title") or chart.get("id") or "") for chart in charts],
    )

    has_normalized = False
    has_stacked_bar = False
    for row, render_row in enumerate(render_rows, start=1):
        chart = render_row["chart"]
        frame = render_row["frame"]
        logical_chart = render_row["logical_chart"]
        role = str(render_row["role"])
        if role == "candlestick_volume":
            continue
        x_values = _frame_x_values(frame, chart)
        panel_has_secondary = _panel_has_secondary_axis(chart, frame)
        y_names = [*_as_string_list(chart.get("y")), *_as_string_list(chart.get("secondary_y"))]
        has_normalized = has_normalized or bool(_normalized_names(chart, y_names))
        chart_type = str(chart["type"])
        if chart_type == "heatmap":
            _add_heatmap_panel(figure, go, row, frame, chart, x_values)
            figure.update_yaxes(
                title_text=str(chart.get("unit", "")),
                row=row,
                col=1,
                secondary_y=False,
            )
            continue
        if role == "candlestick_price":
            candle_columns = _candlestick_columns(frame, logical_chart)
            candle_names = [str(value) for value in candle_columns.values() if value]
            requested_normalized = _normalized_name_list(logical_chart, candle_names)
            has_normalized = has_normalized or bool(requested_normalized)
            volume_row = None
            volume_chart: dict[str, Any] | None = None
            if (
                row < len(render_rows)
                and render_rows[row]["role"] == "candlestick_volume"
                and render_rows[row]["logical_index"] == render_row["logical_index"]
            ):
                volume_row = row + 1
                volume_chart = render_rows[row]["chart"]
            primary_values, secondary_values = _add_candlestick_panel(
                figure,
                go,
                row,
                frame,
                logical_chart,
                x_values,
                set(),
                volume_row=volume_row,
            )
            extra_normalized = [
                name for name in requested_normalized if name not in candle_names
            ]
            normalized_values: list[Any] = []
            normalized_trace_indices: list[int] = []
            normalized_colors = _series_color_map(project, logical_chart, extra_normalized)
            for position, name in enumerate(extra_normalized):
                y_values = _numeric_series(frame, name)
                normalized_values.extend(y_values.tolist())
                normalized_trace_indices.append(len(figure.data))
                _add_xy_trace(
                    figure,
                    go,
                    row,
                    x_values,
                    y_values,
                    name,
                    normalized_colors[name],
                    "line",
                    logical_chart,
                    set(extra_normalized),
                    False,
                    f"vap-candle-normalized-{row}-{position}",
                )
            _apply_axis_ticks(figure, row, primary_values, logical_chart, False, False)
            if volume_row is not None and volume_chart is not None:
                _apply_axis_ticks(
                    figure,
                    volume_row,
                    secondary_values,
                    volume_chart,
                    False,
                    True,
                )
            _attach_normalized_overlay_axis(
                figure,
                row,
                normalized_trace_indices,
                normalized_values,
                logical_chart,
            )
            figure.update_yaxes(
                title_text=str(logical_chart.get("unit", "")),
                row=row,
                col=1,
                secondary_y=False,
            )
            if volume_row is not None and volume_chart is not None:
                figure.update_yaxes(
                    title_text=str(
                        logical_chart.get("secondary_unit")
                        or candle_columns.get("volume")
                        or "Volume"
                    ),
                    row=volume_row,
                    col=1,
                    secondary_y=False,
                )
            figure.update_xaxes(rangeslider_visible=False, row=row, col=1)
            if volume_row is not None:
                figure.update_xaxes(
                    rangeslider_visible=False,
                    row=volume_row,
                    col=1,
                )
            continue

        primary_values, secondary_values, normalized_values, normalized_trace_indices = _add_standard_panel(
            figure, go, row, frame, chart, x_values, project
        )
        is_bar = chart_type in {"bar", "stacked_bar", "stacked_bar_100"}
        is_percent = chart_type in {"stacked_bar_100", "stacked_area_100"}
        _apply_axis_ticks(figure, row, primary_values, chart, False, is_bar or is_percent)
        secondary_type = str(chart.get("secondary_type", "line")).lower()
        _apply_axis_ticks(figure, row, secondary_values, chart, True, secondary_type == "bar")
        _attach_normalized_overlay_axis(
            figure,
            row,
            normalized_trace_indices,
            normalized_values,
            chart,
        )
        figure.update_yaxes(
            title_text=str(chart.get("unit", "")),
            row=row,
            col=1,
            secondary_y=False,
        )
        if panel_has_secondary:
            figure.update_yaxes(
                title_text=str(chart.get("secondary_unit", "")),
                row=row,
                col=1,
                secondary_y=True,
            )
        has_stacked_bar = has_stacked_bar or chart_type in {"stacked_bar", "stacked_bar_100"}

    title_text = str(project.get("title") or "VAP Plotly Chart Stack")
    figure.update_layout(
        template="plotly_white",
        height=_figure_height(project, charts),
        autosize=True,
        margin={"l": 58, "r": 58, "t": 54, "b": 42},
        paper_bgcolor=str(project.get("figure_face_color") or DEFAULT_BACKGROUND_COLOR),
        plot_bgcolor=str(project.get("axes_face_color") or DEFAULT_PLOT_COLOR),
        font={"family": 'Inter, "Noto Sans TC", "Microsoft JhengHei", sans-serif', "size": 11, "color": DEFAULT_TEXT_COLOR},
        hovermode="x unified",
        dragmode="pan",
        barmode="relative" if has_stacked_bar else "group",
        bargap=_clamp_float(project.get("bar_gap_ratio"), DEFAULT_BAR_GAP_RATIO, 0.0, 0.18),
        bargroupgap=0.0,
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.015, "xanchor": "right", "x": 1.0},
        title={"text": title_text, "x": 0.01, "xanchor": "left", "font": {"size": 15}},
        uirevision="vap-plotly-stack",
    )
    figure.update_xaxes(
        showgrid=False,
        showspikes=True,
        spikemode="across",
        spikesnap="cursor",
        rangeslider_visible=False,
    )
    figure.update_yaxes(
        showgrid=True,
        gridcolor=DEFAULT_GRID_COLOR,
        zerolinecolor=DEFAULT_ZERO_COLOR,
        fixedrange=False,
    )

    config = {
        "responsive": True,
        "displaylogo": False,
        "displayModeBar": False,
        "scrollZoom": True,
        "modeBarButtonsToRemove": [
            "zoom2d",
            "zoomIn2d",
            "zoomOut2d",
            "autoScale2d",
            "resetScale2d",
            "lasso2d",
            "select2d",
        ],
    }
    plot_fragment = pio.to_html(
        figure,
        full_html=False,
        include_plotlyjs=True,
        config=config,
        div_id=VAP_PLOT_DIV_ID,
    )
    # Plotly's full offline bundle contains dormant map/geo CDN defaults.  The
    # VAP renderer does not expose those trace types; neutralizing both known
    # CDN roots plus the CSP above guarantees that this document performs no
    # external request while retaining candlestick and heatmap support.
    plot_fragment = plot_fragment.replace(
        "https://cdn.plot.ly/un/", "data:application/json,%7B%7D"
    ).replace(
        "https://unpkg.com/maki@2.1.0/icons/", "data:image/svg+xml,"
    )
    document = _html_document(project, plot_fragment, has_normalized)
    destination = Path(output_path).expanduser()
    if destination.suffix.lower() not in {".html", ".htm"}:
        destination = destination.with_suffix(".html")
    with file_transaction_lock(destination):
        atomic_write_text(destination, document)
    return destination.resolve()


__all__ = ["seaborn_palette_to_hex", "write_plotly_stack_html"]
