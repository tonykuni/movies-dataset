#!/usr/bin/env python3
"""VAP-style Seaborn vertical chart stack generator.

The engine keeps chart specifications in JSON.  Adding a chart appends it to
the bottom of the stack; rendering rebuilds a single aligned figure.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from copy import deepcopy
from datetime import datetime, timezone
from html import escape
from io import StringIO
from pathlib import Path
from typing import Any, Iterable

import matplotlib

# UI rendering runs in a worker thread and only writes files.  Force the
# non-interactive backend before importing pyplot to avoid Windows Tk/Tcl
# cross-thread errors.
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator, FuncFormatter, MaxNLocator, PercentFormatter

from vap_data_adapter import (
    DEFAULT_MAX_ROWS,
    discover_source,
    normalize_source_spec,
    read_source_frame,
    write_discovery_manifest,
)
from vap_atomic_io import atomic_write_json, cleanup_stale_temporary_files, file_transaction_lock
from vap_defaults import (
    apply_preset,
    chart_defaults,
    deep_merge,
    load_defaults,
    preset_names,
    project_defaults,
)
from vap_quality_engine import (
    SUPPORTED_DUPLICATE_POLICIES,
    SUPPORTED_INVALID_DATE_POLICIES,
    SUPPORTED_OUTLIER_POLICIES,
    apply_outlier_policy,
    audit_frame,
    is_volume_column,
    summarize_repairs,
)
from vap_render_optimizer import optimize_frame_for_chart


# =============================================================================
# 0. 全域參數：常用設定集中於此，便於替換
# =============================================================================

APP_NAME = "VAP Seaborn Vertical Stack Generator"
APP_VERSION = "2.3.1"
DEFAULT_STYLE = "whitegrid"
DEFAULT_CONTEXT = "notebook"
DEFAULT_PALETTE = "deep"
DEFAULT_WIDTH_INCH = 15.5
DEFAULT_PANEL_HEIGHT_INCH = 2.45
DEFAULT_STANDARD_PANEL_HEIGHT_PX = 420
DEFAULT_DPI = 300
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_OUTPUT_FORMATS = ["png", "pdf", "svg", "html"]
DEFAULT_FONT_CANDIDATES = [
    "Noto Sans CJK TC",
    "Noto Sans TC",
    "Microsoft JhengHei",
    "PingFang TC",
    "Arial Unicode MS",
    "DejaVu Sans",
]
DEFAULT_FIGURE_FACE_COLOR = "#F5F7FA"
DEFAULT_AXES_FACE_COLOR = "#FFFFFF"
DEFAULT_GRID_COLOR = "#DCE3EA"
DEFAULT_TEXT_COLOR = "#243247"
DEFAULT_MUTED_COLOR = "#68778B"
DEFAULT_UP_COLOR = "#D62728"
DEFAULT_DOWN_COLOR = "#2CA02C"
DEFAULT_ZERO_COLOR = "#98A2B3"
DEFAULT_LINE_WIDTH = 1.65
DEFAULT_ALPHA = 0.82
DEFAULT_BAR_ALPHA = 0.75
DEFAULT_AREA_ALPHA = 0.50
DEFAULT_BAR_WIDTH_RATIO = 0.92
DEFAULT_CANDLE_WIDTH_RATIO = 0.88
DEFAULT_LEGEND_COLUMNS = 4
DEFAULT_MAX_X_TICKS = 10
DEFAULT_RENDER_MAX_POINTS = 5000
DEFAULT_MIN_FIGURE_HEIGHT = 4.8
DEFAULT_TICK_COUNT = 5
DEFAULT_PRICE_HEIGHT_FRACTION = 0.75
DEFAULT_VOLUME_HEIGHT_FRACTION = 0.25
NICE_STEP_MANTISSAS = [1.25, 2.0, 2.5, 5.0, 10.0]
SUPPORTED_CHART_TYPES = {
    "candlestick",
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
}
SUPPORTED_MISSING_POLICIES = {"none", "ffill", "interpolate", "zero", "drop"}
SUPPORTED_Y_FORMATS = {"auto", "number", "comma", "percent", "magnitude"}
SUPPORTED_AXIS_MODES = {"auto", "single", "dual"}
SUPPORTED_TICK_POLICIES = {"auto", "vap_locked"}
SUPPORTED_STACK_MODES = {"absolute", "percent100"}
STACKED_CHART_TYPES = {"stacked_bar", "stacked_area", "stacked_bar_100", "stacked_area_100"}
WINDOWS_RESERVED_BASENAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{number}" for number in range(1, 10)),
    *(f"LPT{number}" for number in range(1, 10)),
}


# =============================================================================
# 1. 基本工具與設定檔
# =============================================================================


def utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_project_config(data_path: str = "examples/demo_market_data.csv") -> dict[str, Any]:
    defaults = load_defaults()
    project = project_defaults(defaults)
    project.update(
        {
            "name": "vap_seaborn_stack",
            "data": data_path,
            "data_source": normalize_source_spec(data_path) if data_path else {},
            "source": "",
            "output_name": "vap_seaborn_vertical_stack",
        }
    )
    return {
        "schema_version": "2.3",
        "defaults_schema": str(defaults.get("schema", "")),
        "project": project,
        "charts": [],
        "metadata": {
            "created_at": utc_now_text(),
            "updated_at": utc_now_text(),
            "generator": APP_NAME,
            "generator_version": APP_VERSION,
        },
    }


def default_chart_spec(
    chart_id: str,
    chart_type: str,
    title: str,
    x: str,
    y: Iterable[str],
) -> dict[str, Any]:
    result = chart_defaults(load_defaults())
    result.update({
        "id": chart_id,
        "type": chart_type,
        "title": title,
        "x": x,
        "y": list(y),
        "secondary_y": [],
        "unit": "",
        "secondary_unit": "",
        "positive_negative_colors": False,
        "notes": "",
    })
    return result


def normalize_project_and_charts(config: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    defaults = load_defaults()
    project = deep_merge(project_defaults(defaults), config.get("project", {}))
    charts = [deep_merge(chart_defaults(defaults), chart) for chart in config.get("charts", [])]
    return project, charts


def candlestick_height_fractions(chart: dict[str, Any]) -> tuple[float, float]:
    """Return validated price/volume fractions for a logical OHLCV chart."""

    price_fraction = float(
        chart.get("price_height_fraction", DEFAULT_PRICE_HEIGHT_FRACTION)
    )
    volume_fraction = float(
        chart.get("volume_height_fraction", DEFAULT_VOLUME_HEIGHT_FRACTION)
    )
    if (
        not math.isfinite(price_fraction)
        or not math.isfinite(volume_fraction)
        or price_fraction <= 0
        or volume_fraction <= 0
        or not math.isclose(price_fraction + volume_fraction, 1.0, abs_tol=1e-9)
    ):
        raise ValueError(
            "K 線 price_height_fraction 與 volume_height_fraction 必須大於 0 且合計為 1。"
        )
    return price_fraction, volume_fraction


def expand_render_row_specs(charts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Expand logical charts into physical single-axis rows.

    A candlestick chart is intentionally represented by two rows: adjusted
    price above and raw volume below.  Its logical height remains one standard
    height multiple and is divided using the VAP 75/25 visual lock.
    """

    rows: list[dict[str, Any]] = []
    for chart in charts:
        if str(chart.get("type", "")).lower() != "candlestick":
            row = deepcopy(chart)
            row["_render_role"] = "chart"
            row["_logical_chart_id"] = str(chart.get("id", ""))
            rows.append(row)
            continue
        price_fraction, volume_fraction = candlestick_height_fractions(chart)
        total_height = float(chart.get("height_ratio", 1.0))
        price_row = deepcopy(chart)
        price_row.update(
            {
                "_render_role": "candlestick_price",
                "_logical_chart_id": str(chart.get("id", "")),
                "axis_mode": "single",
                "secondary_y": [],
                "height_ratio": total_height * price_fraction,
            }
        )
        volume_row = deepcopy(chart)
        volume_row.update(
            {
                "_render_role": "candlestick_volume",
                "_logical_chart_id": str(chart.get("id", "")),
                "type": "bar",
                "title": str(chart.get("volume_title") or f"{chart.get('title') or chart.get('id')} · Volume"),
                "axis_mode": "single",
                "y": [str(chart.get("volume", "Volume"))],
                "secondary_y": [],
                "unit": str(chart.get("secondary_unit") or chart.get("volume") or "Volume"),
                "y_format": str(chart.get("secondary_y_format", "magnitude")),
                "axis_zero_policy": "include",
                "show_zero_line": False,
                "show_legend": False,
                "height_ratio": total_height * volume_fraction,
            }
        )
        rows.extend([price_row, volume_row])
    return rows


def read_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            value = json.load(handle)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"找不到設定檔：{path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON 格式錯誤：{path}；{exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("設定檔根節點必須是 JSON object。")
    return value


def write_json(path: Path, value: dict[str, Any]) -> None:
    with file_transaction_lock(path):
        atomic_write_json(path, value)


def resolve_from_config(config_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path).expanduser()
    if candidate.is_absolute():
        return candidate
    return (config_path.parent / candidate).resolve()


def safe_relpath(path: str | Path, start: str | Path) -> str:
    """Return a portable relative path, falling back across Windows drives."""

    try:
        return os.path.relpath(Path(path), Path(start))
    except ValueError:
        return str(Path(path).expanduser().resolve())


def ensure_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        result = [part.strip() for part in value.split(",") if part.strip()]
    elif isinstance(value, list):
        result = [str(part).strip() for part in value if str(part).strip()]
    else:
        raise ValueError(f"{field_name} 必須是字串或字串陣列。")
    return result


def validate_safe_basename(value: Any, field_name: str) -> str:
    """Return a cross-platform-safe single path component or reject it.

    Chart ids become part of single-chart filenames, so they deliberately use
    the same rules as ``project.output_name``.
    """

    name = str(value).strip()
    invalid_characters = '<>:"/\\|?*'
    if not name:
        raise ValueError(f"{field_name} 不可為空白。")
    if name in {".", ".."} or name.endswith((".", " ")):
        raise ValueError(f"{field_name} 必須是安全的單一檔名，不可使用路徑或保留名稱：{name!r}")
    if any(character in invalid_characters or ord(character) < 32 for character in name):
        raise ValueError(f"{field_name} 必須是安全的單一檔名，不可含路徑或非法字元：{name!r}")
    windows_stem = name.split(".", 1)[0].upper()
    if windows_stem in WINDOWS_RESERVED_BASENAMES:
        raise ValueError(f"{field_name} 不可使用 Windows 保留名稱：{name!r}")
    return name


def unique_chart_id(existing_ids: set[str], preferred: str) -> str:
    base = validate_safe_basename(preferred.strip() or "chart", "chart id")
    candidate = base
    counter = 2
    while candidate in existing_ids:
        candidate = f"{base}_{counter}"
        counter += 1
    return candidate


def append_chart_spec(config_path: Path, chart: dict[str, Any]) -> dict[str, Any]:
    with file_transaction_lock(config_path):
        config = read_json(config_path)
        charts = config.setdefault("charts", [])
        chart = deep_merge(chart_defaults(load_defaults()), chart)
        existing_ids = {str(item.get("id", "")) for item in charts}
        chart["id"] = unique_chart_id(existing_ids, str(chart.get("id", "chart")))
        validate_chart_spec(chart, len(charts) + 1)
        charts.append(chart)
        config.setdefault("metadata", {})["updated_at"] = utc_now_text()
        write_json(config_path, config)
        return chart


def remove_chart_spec(config_path: Path, chart_id: str) -> bool:
    with file_transaction_lock(config_path):
        config = read_json(config_path)
        charts = config.get("charts", [])
        remaining = [chart for chart in charts if str(chart.get("id")) != chart_id]
        if len(remaining) == len(charts):
            return False
        config["charts"] = remaining
        config.setdefault("metadata", {})["updated_at"] = utc_now_text()
        write_json(config_path, config)
        return True


def update_chart_spec(
    config_path: Path,
    chart_id: str,
    updates: dict[str, Any],
) -> dict[str, Any]:
    with file_transaction_lock(config_path):
        config = read_json(config_path)
        charts = config.get("charts", [])
        index = next(
            (position for position, chart in enumerate(charts) if str(chart.get("id")) == chart_id),
            None,
        )
        if index is None:
            raise KeyError(f"找不到圖表 id：{chart_id}")
        requested_id = str(updates.get("id", chart_id)).strip() or chart_id
        conflicting_ids = {
            str(chart.get("id", ""))
            for position, chart in enumerate(charts)
            if position != index
        }
        if requested_id in conflicting_ids:
            raise ValueError(f"圖表 id 已存在：{requested_id}")
        updated = deep_merge(chart_defaults(load_defaults()), charts[index])
        updated = deep_merge(updated, updates)
        updated["id"] = requested_id
        validate_chart_spec(updated, index + 1)
        charts[index] = updated
        config.setdefault("metadata", {})["updated_at"] = utc_now_text()
        write_json(config_path, config)
        return updated


def move_chart_spec(config_path: Path, chart_id: str, new_position: int) -> bool:
    with file_transaction_lock(config_path):
        config = read_json(config_path)
        charts = config.get("charts", [])
        old_index = next(
            (index for index, chart in enumerate(charts) if str(chart.get("id")) == chart_id),
            None,
        )
        if old_index is None:
            return False
        chart = charts.pop(old_index)
        bounded_index = max(0, min(new_position - 1, len(charts)))
        charts.insert(bounded_index, chart)
        config.setdefault("metadata", {})["updated_at"] = utc_now_text()
        write_json(config_path, config)
        return True


# =============================================================================
# 2. 資料讀取、清理與驗證
# =============================================================================


def load_table(path: Path) -> pd.DataFrame:
    return read_source_frame(path)


def parse_date_column(
    frame: pd.DataFrame,
    date_column: str,
    invalid_policy: str = "fail",
    duplicate_policy: str = "fail",
) -> pd.DataFrame:
    if date_column not in frame.columns:
        return frame
    if invalid_policy not in SUPPORTED_INVALID_DATE_POLICIES:
        raise ValueError(f"invalid_date_policy={invalid_policy!r} 不支援。")
    if duplicate_policy not in SUPPORTED_DUPLICATE_POLICIES:
        raise ValueError(f"duplicate_date_policy={duplicate_policy!r} 不支援。")
    result = frame.copy()
    parsed = pd.to_datetime(result[date_column], errors="coerce", format="mixed")
    invalid_or_missing_count = int(parsed.isna().sum())
    if invalid_or_missing_count > 0:
        if invalid_policy == "fail":
            raise ValueError(
                f"欄位 {date_column} 有 {invalid_or_missing_count} 筆無效、缺失或無法解析的日期。"
            )
        # Only the explicit ``drop`` policy may remove NaT rows.  Never let
        # drop_duplicates silently coalesce multiple invalid/missing dates.
        result = result.loc[parsed.notna()].copy()
        parsed = parsed.loc[parsed.notna()]
    result[date_column] = parsed
    result = result.sort_values(date_column, kind="stable")
    duplicate_mask = result[date_column].notna() & result[date_column].duplicated(keep=False)
    if bool(duplicate_mask.any()) and duplicate_policy == "fail":
        raise ValueError(f"欄位 {date_column} 有 {int(duplicate_mask.sum())} 筆重複日期。")
    keep_value = duplicate_policy if duplicate_policy in {"first", "last"} else "last"
    result = result.drop_duplicates(subset=[date_column], keep=keep_value)
    return result.reset_index(drop=True)


def apply_missing_policy(
    frame: pd.DataFrame,
    columns: list[str],
    policy: str,
    never_fill_columns: Iterable[str] | None = None,
) -> pd.DataFrame:
    result = frame.copy()
    protected_columns = {str(column) for column in (never_fill_columns or [])}
    numeric_columns = [
        column
        for column in columns
        if column in result.columns and pd.api.types.is_numeric_dtype(result[column])
    ]
    if policy == "ffill":
        forward_fill_columns = [
            column
            for column in numeric_columns
            if column not in protected_columns and not is_volume_column(column)
        ]
        if forward_fill_columns:
            result[forward_fill_columns] = result[forward_fill_columns].ffill()
    elif policy == "interpolate":
        interpolate_columns = [
            column
            for column in numeric_columns
            if column not in protected_columns and not is_volume_column(column)
        ]
        if interpolate_columns:
            result[interpolate_columns] = result[interpolate_columns].interpolate(
                method="linear",
                limit_area="inside",
            )
    elif policy == "zero":
        zero_fill_columns = [
            column
            for column in numeric_columns
            if column not in protected_columns and not is_volume_column(column)
        ]
        if zero_fill_columns:
            result[zero_fill_columns] = result[zero_fill_columns].fillna(0)
    elif policy == "drop":
        result = result.dropna(subset=columns)
    return result


def validate_chart_spec(chart: dict[str, Any], position: int) -> None:
    chart_type = str(chart.get("type", "")).lower()
    if chart_type not in SUPPORTED_CHART_TYPES:
        raise ValueError(
            f"第 {position} 張圖 type={chart_type!r} 不支援；"
            f"可用：{', '.join(sorted(SUPPORTED_CHART_TYPES))}。"
        )
    validate_safe_basename(chart.get("id", ""), f"第 {position} 張圖 id")
    if chart_type == "candlestick":
        required = ["x", "open", "high", "low", "close", "volume"]
        missing = [name for name in required if not str(chart.get(name, "")).strip()]
        if missing:
            raise ValueError(f"K 線圖缺少欄位 mapping：{', '.join(missing)}。")
        candlestick_height_fractions(chart)
    elif chart_type == "heatmap":
        required = ["heatmap_index", "heatmap_columns", "heatmap_value"]
        missing = [name for name in required if not chart.get(name)]
        if missing:
            raise ValueError(f"熱圖缺少欄位：{', '.join(missing)}。")
    else:
        if not str(chart.get("x", "")).strip():
            raise ValueError(f"第 {position} 張圖缺少 x。")
        if not ensure_string_list(chart.get("y"), "y"):
            raise ValueError(f"第 {position} 張圖至少需要一個 y 欄位。")
    missing_policy = str(chart.get("missing", "none"))
    if missing_policy not in SUPPORTED_MISSING_POLICIES:
        raise ValueError(f"missing={missing_policy!r} 不支援。")
    height_ratio = float(chart.get("height_ratio", 1.0))
    if not math.isfinite(height_ratio) or height_ratio <= 0:
        raise ValueError("height_ratio 必須大於 0。")
    axis_mode = str(chart.get("axis_mode", "auto"))
    if axis_mode not in SUPPORTED_AXIS_MODES:
        raise ValueError(f"axis_mode={axis_mode!r} 不支援。")
    has_secondary = bool(ensure_string_list(chart.get("secondary_y"), "secondary_y"))
    if chart_type == "candlestick" and str(chart.get("volume", "")).strip():
        has_secondary = True
    if axis_mode == "dual" and not has_secondary:
        raise ValueError("axis_mode=dual 時必須設定 secondary_y。")
    tick_policy = str(chart.get("tick_policy", "vap_locked"))
    if tick_policy not in SUPPORTED_TICK_POLICIES:
        raise ValueError(f"tick_policy={tick_policy!r} 不支援。")
    if int(chart.get("tick_count", DEFAULT_TICK_COUNT)) < 2:
        raise ValueError("tick_count 必須至少為 2。")
    if int(chart.get("max_x_ticks", DEFAULT_MAX_X_TICKS)) < 2:
        raise ValueError("max_x_ticks 必須至少為 2。")
    if str(chart.get("quality_mode", "audit")) not in {"off", "audit"}:
        raise ValueError("quality_mode 只支援 off 或 audit。")
    if str(chart.get("invalid_date_policy", "fail")) not in SUPPORTED_INVALID_DATE_POLICIES:
        raise ValueError("invalid_date_policy 無效。")
    if str(chart.get("duplicate_date_policy", "fail")) not in SUPPORTED_DUPLICATE_POLICIES:
        raise ValueError("duplicate_date_policy 無效。")
    if str(chart.get("outlier_policy", "report")) not in SUPPORTED_OUTLIER_POLICIES:
        raise ValueError("outlier_policy 無效。")
    outlier_multiplier = float(chart.get("outlier_iqr_multiplier", 3.0))
    if not math.isfinite(outlier_multiplier) or outlier_multiplier <= 0:
        raise ValueError("outlier_iqr_multiplier 必須大於 0。")
    for alpha_key, alpha_default in [
        ("alpha", DEFAULT_ALPHA),
        ("secondary_alpha", 0.88),
        ("bar_alpha", DEFAULT_BAR_ALPHA),
        ("area_alpha", DEFAULT_AREA_ALPHA),
    ]:
        alpha_value = float(chart.get(alpha_key, alpha_default))
        if not math.isfinite(alpha_value) or not 0 <= alpha_value <= 1:
            raise ValueError(f"{alpha_key} 必須介於 0 與 1。")
    line_width = float(chart.get("line_width", DEFAULT_LINE_WIDTH))
    if not math.isfinite(line_width) or line_width <= 0:
        raise ValueError("line_width 必須大於 0。")
    secondary_line_width = float(chart.get("secondary_line_width", 1.35))
    if not math.isfinite(secondary_line_width) or secondary_line_width <= 0:
        raise ValueError("secondary_line_width 必須大於 0。")
    bar_width_ratio = float(chart.get("bar_width_ratio", DEFAULT_BAR_WIDTH_RATIO))
    if not math.isfinite(bar_width_ratio) or not 0 < bar_width_ratio < 1:
        raise ValueError("bar_width_ratio 必須大於 0 且小於 1，避免長條交疊。")
    candle_width_ratio = float(chart.get("candle_width_ratio", DEFAULT_CANDLE_WIDTH_RATIO))
    if not math.isfinite(candle_width_ratio) or not 0 < candle_width_ratio < 1:
        raise ValueError("candle_width_ratio 必須大於 0 且小於 1，避免 K 棒交疊。")
    chart_render_max_points = chart.get("render_max_points")
    if chart_render_max_points not in (None, ""):
        render_max_points = int(chart_render_max_points)
        if not 2 <= render_max_points <= DEFAULT_MAX_ROWS:
            raise ValueError(
                f"render_max_points 必須介於 2 與 {DEFAULT_MAX_ROWS}。"
            )
    stack_mode = "percent100" if chart_type.endswith("_100") else str(chart.get("stack_mode", "absolute"))
    if stack_mode not in SUPPORTED_STACK_MODES:
        raise ValueError(f"stack_mode={stack_mode!r} 不支援。")


def validate_config(config: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if not isinstance(config.get("project"), dict):
        raise ValueError("設定檔缺少 project object。")
    project = config["project"]
    width_inch = float(project.get("width_inch", DEFAULT_WIDTH_INCH))
    panel_height_inch = float(
        project.get("panel_height_inch", DEFAULT_PANEL_HEIGHT_INCH)
    )
    if any(
        not math.isfinite(value) or value <= 0
        for value in (width_inch, panel_height_inch)
    ):
        raise ValueError("project.width_inch 與 panel_height_inch 必須是正有限數值。")
    if int(project.get("dpi", DEFAULT_DPI)) < 72:
        raise ValueError("project.dpi 不可低於 72。")
    if int(
        project.get("standard_panel_height_px", DEFAULT_STANDARD_PANEL_HEIGHT_PX)
    ) < 120:
        raise ValueError("project.standard_panel_height_px 不可低於 120。")
    max_rows = int(project.get("max_rows", DEFAULT_MAX_ROWS))
    if not 1 <= max_rows <= DEFAULT_MAX_ROWS:
        raise ValueError(f"project.max_rows 必須介於 1 與 {DEFAULT_MAX_ROWS}。")
    sample_rows = int(project.get("sample_rows", min(5000, max_rows)))
    if not 1 <= sample_rows <= DEFAULT_MAX_ROWS:
        raise ValueError(f"project.sample_rows 必須介於 1 與 {DEFAULT_MAX_ROWS}。")
    render_max_points = int(project.get("render_max_points", DEFAULT_RENDER_MAX_POINTS))
    if not 2 <= render_max_points <= DEFAULT_MAX_ROWS:
        raise ValueError(
            f"project.render_max_points 必須介於 2 與 {DEFAULT_MAX_ROWS}。"
        )
    charts = config.get("charts")
    if not isinstance(charts, list) or not charts:
        raise ValueError("設定檔尚未加入任何圖表。")
    seen_ids: set[str] = set()
    for position, chart in enumerate(charts, start=1):
        validate_chart_spec(chart, position)
        chart_id = str(chart["id"])
        if chart_id in seen_ids:
            raise ValueError(f"圖表 id 重複：{chart_id}")
        seen_ids.add(chart_id)
        if chart.get("secondary_y") and chart["type"] in STACKED_CHART_TYPES | {"heatmap"}:
            warnings.append(f"{chart_id} 的 secondary_y 在 {chart['type']} 中不會使用。")
        if chart.get("axis_mode") == "single" and chart.get("secondary_y"):
            warnings.append(f"{chart_id} 設為 single，secondary_y 將不會繪製。")
    return warnings


def required_columns_for_chart(chart: dict[str, Any]) -> list[str]:
    chart_type = str(chart["type"])
    if chart_type == "heatmap":
        columns = [chart["heatmap_index"], chart["heatmap_columns"], chart["heatmap_value"]]
    elif chart_type == "candlestick":
        columns = [
            str(chart["x"]),
            str(chart["open"]),
            str(chart["high"]),
            str(chart["low"]),
            str(chart["close"]),
            str(chart["volume"]),
        ]
    else:
        columns = [str(chart["x"])]
        columns.extend(ensure_string_list(chart.get("y"), "y"))
        if chart_type not in STACKED_CHART_TYPES and str(chart.get("axis_mode", "auto")) != "single":
            columns.extend(ensure_string_list(chart.get("secondary_y"), "secondary_y"))
    columns.extend(ensure_string_list(chart.get("normalized_y"), "normalized_y"))
    return list(dict.fromkeys(columns))


def validate_data_columns(frame: pd.DataFrame, chart: dict[str, Any]) -> None:
    required = required_columns_for_chart(chart)
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise ValueError(f"圖表 {chart['id']} 找不到欄位：{', '.join(missing)}")


def prepare_chart_frame(
    chart: dict[str, Any],
    project: dict[str, Any],
    config_path: Path,
    cache: dict[str, pd.DataFrame],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    source_setting = chart.get("data_source") or project.get("data_source") or chart.get("data") or project.get("data")
    if not source_setting:
        raise ValueError(f"圖表 {chart['id']} 未設定資料來源。")
    columns = required_columns_for_chart(chart)
    source_spec = normalize_source_spec(source_setting)
    max_rows = int(chart.get("max_rows") or project.get("max_rows") or 0) or None
    cache_key = json.dumps(
        {"source": source_spec, "columns": columns, "limit": max_rows},
        ensure_ascii=False,
        sort_keys=True,
        default=str,
    )
    if cache_key not in cache:
        cache[cache_key] = read_source_frame(
            source_spec,
            columns=columns,
            limit=max_rows,
            config_directory=config_path.parent,
        )
    raw_frame = cache[cache_key].copy()
    date_column = str(chart.get("date_column") or project.get("date_column") or "").strip()
    if date_column not in raw_frame.columns and str(chart.get("x", "")) in raw_frame.columns:
        x_name = str(chart.get("x", ""))
        if any(token in x_name.lower() for token in ["date", "time", "日期", "時間"]):
            date_column = x_name
    quality_mode = str(chart.get("quality_mode", "audit"))
    outlier_multiplier = float(chart.get("outlier_iqr_multiplier", 3.0))
    before_audit = (
        audit_frame(raw_frame, date_column, columns, outlier_multiplier)
        if quality_mode == "audit"
        else {"status": "OFF", "issues": [], "rows": int(len(raw_frame)), "null_cells": 0}
    )
    frame = raw_frame.copy()
    if date_column:
        frame = parse_date_column(
            frame,
            date_column,
            invalid_policy=str(chart.get("invalid_date_policy", "fail")),
            duplicate_policy=str(chart.get("duplicate_date_policy", "fail")),
        )
    validate_data_columns(frame, chart)
    missing_policy = str(chart.get("missing", "none"))
    never_fill_columns = (
        [str(chart.get("volume", ""))]
        if str(chart.get("type", "")) == "candlestick"
        else []
    )
    treated_frame = apply_missing_policy(
        frame,
        columns,
        missing_policy,
        never_fill_columns=never_fill_columns,
    )
    treated_frame, outlier_repairs = apply_outlier_policy(
        treated_frame,
        columns,
        policy=str(chart.get("outlier_policy", "report")),
        multiplier=outlier_multiplier,
    )
    repairs = summarize_repairs(raw_frame, treated_frame, columns, missing_policy, outlier_repairs)
    after_audit = (
        audit_frame(treated_frame, date_column, columns, outlier_multiplier)
        if quality_mode == "audit"
        else {"status": "OFF", "issues": [], "rows": int(len(treated_frame)), "null_cells": 0}
    )
    quality_report = {
        "mode": quality_mode,
        "date_column": date_column,
        "policies": {
            "missing": missing_policy,
            "invalid_date": str(chart.get("invalid_date_policy", "fail")),
            "duplicate_date": str(chart.get("duplicate_date_policy", "fail")),
            "outlier": str(chart.get("outlier_policy", "report")),
            "outlier_iqr_multiplier": outlier_multiplier,
        },
        "before": before_audit,
        "after": after_audit,
        "repairs": repairs,
        "data_changed": bool(repairs),
    }
    return treated_frame, quality_report


def load_chart_frame(
    chart: dict[str, Any],
    project: dict[str, Any],
    config_path: Path,
    cache: dict[str, pd.DataFrame],
) -> pd.DataFrame:
    frame, _quality_report = prepare_chart_frame(chart, project, config_path, cache)
    return frame


# =============================================================================
# 3. Seaborn／Matplotlib 圖型繪製
# =============================================================================


def configure_theme(project: dict[str, Any]) -> None:
    sns.set_theme(
        style=str(project.get("style", DEFAULT_STYLE)),
        context=str(project.get("context", DEFAULT_CONTEXT)),
        palette=str(project.get("palette", DEFAULT_PALETTE)),
        rc={
            "font.sans-serif": DEFAULT_FONT_CANDIDATES,
            "axes.unicode_minus": False,
            "axes.edgecolor": "#B8C2CC",
            "axes.labelcolor": DEFAULT_TEXT_COLOR,
            "text.color": DEFAULT_TEXT_COLOR,
            "xtick.color": DEFAULT_MUTED_COLOR,
            "ytick.color": DEFAULT_MUTED_COLOR,
            "grid.color": DEFAULT_GRID_COLOR,
            "grid.linewidth": 0.65,
        },
    )


def get_palette(
    chart: dict[str, Any],
    project: dict[str, Any],
    count: int,
    series_names: list[str] | None = None,
) -> list[Any]:
    palette_name = chart.get("palette") or project.get("palette") or DEFAULT_PALETTE
    fallback = list(sns.color_palette(palette_name, n_colors=max(count, 1)))
    chart_map = chart.get("colors") if isinstance(chart.get("colors"), dict) else {}
    project_map = project.get("series_colors") if isinstance(project.get("series_colors"), dict) else {}
    if not series_names:
        return fallback
    return [chart_map.get(name) or project_map.get(name) or fallback[index % len(fallback)] for index, name in enumerate(series_names)]


def to_numeric_series(frame: pd.DataFrame, column: str) -> pd.Series:
    values = pd.to_numeric(frame[column], errors="coerce")
    if values.notna().sum() == 0:
        raise ValueError(f"欄位 {column} 沒有可繪製的數值。")
    return values


def compact_bar_geometry(
    x_values: pd.Series,
    width_ratio: float = DEFAULT_BAR_WIDTH_RATIO,
) -> tuple[np.ndarray, float, bool]:
    """Return non-overlapping numeric x positions and a compact bar width.

    Datetime bars use the smallest observed positive spacing, so an irregular
    trading calendar cannot make Friday's bar overlap Monday's.  Other x types
    are treated as ordered categories with one unit between adjacent rows.
    """

    ratio = float(width_ratio)
    if not 0 < ratio < 1:
        raise ValueError("bar/candle width ratio 必須大於 0 且小於 1。")
    is_date = pd.api.types.is_datetime64_any_dtype(x_values)
    if is_date:
        positions = np.asarray(mdates.date2num(x_values), dtype=float)
    else:
        positions = np.arange(len(x_values), dtype=float)
    finite_unique = np.unique(positions[np.isfinite(positions)])
    positive_differences = np.diff(finite_unique)
    positive_differences = positive_differences[positive_differences > 0]
    minimum_spacing = float(np.min(positive_differences)) if len(positive_differences) else 1.0
    return positions, minimum_spacing * ratio, is_date


def candlestick_plot_values(
    frame: pd.DataFrame,
    chart: dict[str, Any],
    width_ratio: float | None = None,
) -> dict[str, Any]:
    """Prepare aligned OHLCV geometry without filling volume gaps."""

    x_values = frame[str(chart["x"])]
    plot_x, width, x_is_date = compact_bar_geometry(
        x_values,
        float(
            chart.get("candle_width_ratio", DEFAULT_CANDLE_WIDTH_RATIO)
            if width_ratio is None
            else width_ratio
        ),
    )
    open_values = to_numeric_series(frame, str(chart["open"])).to_numpy(dtype=float)
    high_values = to_numeric_series(frame, str(chart["high"])).to_numpy(dtype=float)
    low_values = to_numeric_series(frame, str(chart["low"])).to_numpy(dtype=float)
    close_values = to_numeric_series(frame, str(chart["close"])).to_numpy(dtype=float)
    volume_values = pd.to_numeric(
        frame[str(chart["volume"])], errors="coerce"
    ).to_numpy(dtype=float)
    valid_price = (
        np.isfinite(plot_x)
        & np.isfinite(open_values)
        & np.isfinite(high_values)
        & np.isfinite(low_values)
        & np.isfinite(close_values)
    )
    if not bool(np.any(valid_price)):
        raise ValueError(f"K 線圖 {chart['id']} 沒有完整可繪製的 OHLC 價格。")
    up_color = str(chart.get("up_color", DEFAULT_UP_COLOR))
    down_color = str(chart.get("down_color", DEFAULT_DOWN_COLOR))
    up_mask = valid_price & (close_values >= open_values)
    colors = np.where(up_mask, up_color, down_color)
    return {
        "x_values": x_values,
        "plot_x": plot_x,
        "width": width,
        "x_is_date": x_is_date,
        "open": open_values,
        "high": high_values,
        "low": low_values,
        "close": close_values,
        "volume": volume_values,
        "valid_price": valid_price,
        "colors": colors,
    }


def configure_candlestick_x_axis(ax: Axes, values: dict[str, Any]) -> None:
    if bool(values["x_is_date"]):
        ax.xaxis_date()
    else:
        ax.set_xticks(values["plot_x"])
        ax.set_xticklabels(values["x_values"].astype(str))


def draw_candlestick_price_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
) -> None:
    """Draw only adjusted OHLC candles on one left axis."""

    values = candlestick_plot_values(frame, chart)
    valid_price = values["valid_price"]
    plot_x = values["plot_x"]
    colors = values["colors"]
    ax.vlines(
        plot_x[valid_price],
        values["low"][valid_price],
        values["high"][valid_price],
        colors=colors[valid_price],
        linewidth=1.0,
        zorder=4,
    )
    body_bottom = np.minimum(values["open"], values["close"])
    body_height = np.abs(values["close"] - values["open"])
    ax.bar(
        plot_x[valid_price],
        body_height[valid_price],
        bottom=body_bottom[valid_price],
        width=values["width"],
        color=colors[valid_price],
        edgecolor=colors[valid_price],
        linewidth=0.7,
        alpha=0.96,
        label=str(chart.get("price_label", "K 線（紅漲／綠跌）")),
        zorder=5,
    )
    doji_mask = valid_price & np.isclose(
        values["open"], values["close"], rtol=1e-10, atol=1e-12
    )
    if bool(np.any(doji_mask)):
        ax.hlines(
            values["open"][doji_mask],
            plot_x[doji_mask] - values["width"] / 2,
            plot_x[doji_mask] + values["width"] / 2,
            colors=colors[doji_mask],
            linewidth=1.2,
            zorder=6,
        )
    configure_candlestick_x_axis(ax, values)


def draw_candlestick_volume_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
) -> None:
    """Draw raw volume on a separate single left axis using candle colors."""

    values = candlestick_plot_values(
        frame,
        chart,
        float(chart.get("bar_width_ratio", DEFAULT_BAR_WIDTH_RATIO)),
    )
    volume_mask = values["valid_price"] & np.isfinite(values["volume"])
    if bool(np.any(volume_mask)):
        ax.bar(
            values["plot_x"][volume_mask],
            values["volume"][volume_mask],
            width=values["width"],
            color=values["colors"][volume_mask],
            edgecolor="none",
            alpha=float(chart.get("bar_alpha", DEFAULT_BAR_ALPHA)),
            label=str(chart.get("volume_label") or chart.get("volume", "Volume")),
            zorder=2,
        )
    configure_candlestick_x_axis(ax, values)


def draw_candlestick_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
) -> Axes:
    """Legacy twin-axis helper; stack rendering uses two single-axis rows."""

    draw_candlestick_price_chart(ax, frame, chart)
    secondary_ax = ax.twinx()
    draw_candlestick_volume_chart(secondary_ax, frame, chart)
    secondary_ax.set_ylabel(str(chart.get("secondary_unit", "Volume")), color=DEFAULT_MUTED_COLOR)
    secondary_ax.grid(False)
    ax.set_zorder(secondary_ax.get_zorder() + 1)
    ax.patch.set_visible(False)
    return secondary_ax


def draw_line_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    colors: list[Any],
) -> None:
    x = chart["x"]
    line_width = float(chart.get("line_width", DEFAULT_LINE_WIDTH))
    alpha = float(chart.get("alpha", DEFAULT_ALPHA))
    for index, column in enumerate(ensure_string_list(chart["y"], "y")):
        sns.lineplot(
            data=frame,
            x=x,
            y=column,
            ax=ax,
            label=column,
            color=colors[index],
            linewidth=line_width,
            alpha=alpha,
            errorbar=None,
        )


def draw_bar_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    colors: list[Any],
) -> None:
    x_values = frame[chart["x"]]
    y_columns = ensure_string_list(chart["y"], "y")
    alpha = float(chart.get("bar_alpha", DEFAULT_BAR_ALPHA))
    group_count = len(y_columns)
    numeric_x, base_width, x_is_date = compact_bar_geometry(
        x_values,
        float(chart.get("bar_width_ratio", DEFAULT_BAR_WIDTH_RATIO)),
    )
    width = base_width / max(group_count, 1)
    for index, column in enumerate(y_columns):
        values = to_numeric_series(frame, column)
        offset = (index - (group_count - 1) / 2) * width
        if bool(chart.get("positive_negative_colors")) and group_count == 1:
            bar_colors = np.where(values >= 0, DEFAULT_UP_COLOR, DEFAULT_DOWN_COLOR)
        else:
            bar_colors = colors[index]
        ax.bar(numeric_x + offset, values, width=width, label=column, color=bar_colors, alpha=alpha)
    if x_is_date:
        ax.xaxis_date()
    else:
        ax.set_xticks(numeric_x)
        ax.set_xticklabels(x_values.astype(str))


def draw_area_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    colors: list[Any],
) -> None:
    x_values = frame[chart["x"]]
    line_alpha = float(chart.get("alpha", DEFAULT_ALPHA))
    fill_alpha = float(chart.get("area_alpha", DEFAULT_AREA_ALPHA))
    for index, column in enumerate(ensure_string_list(chart["y"], "y")):
        values = to_numeric_series(frame, column)
        ax.plot(
            x_values,
            values,
            color=colors[index],
            linewidth=float(chart.get("line_width", DEFAULT_LINE_WIDTH)),
            alpha=line_alpha,
            label=column,
        )
        ax.fill_between(x_values, values, 0, color=colors[index], alpha=fill_alpha)


def draw_scatter_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    colors: list[Any],
) -> None:
    x = chart["x"]
    alpha = float(chart.get("alpha", DEFAULT_ALPHA))
    for index, column in enumerate(ensure_string_list(chart["y"], "y")):
        sns.scatterplot(
            data=frame,
            x=x,
            y=column,
            ax=ax,
            label=column,
            color=colors[index],
            alpha=alpha,
            s=float(chart.get("marker_size", 22)),
            edgecolor="none",
        )


def draw_step_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    colors: list[Any],
) -> None:
    x_values = frame[chart["x"]]
    for index, column in enumerate(ensure_string_list(chart["y"], "y")):
        ax.step(
            x_values,
            to_numeric_series(frame, column),
            where=str(chart.get("where", "post")),
            label=column,
            color=colors[index],
            linewidth=float(chart.get("line_width", DEFAULT_LINE_WIDTH)),
        )


def prepare_stack_values(
    frame: pd.DataFrame,
    columns: list[str],
    stack_mode: str,
) -> list[np.ndarray]:
    matrix = np.column_stack(
        [to_numeric_series(frame, column).to_numpy(dtype=float) for column in columns]
    )
    if not np.isfinite(matrix).all():
        raise ValueError(
            "堆疊圖仍含空值或非有限值；請明確選擇 zero、drop、ffill 或 interpolate 策略後再生成。"
        )
    if stack_mode == "percent100":
        if np.any(matrix < 0):
            raise ValueError("100% 堆疊只接受非負且可加總的數值。")
        totals = matrix.sum(axis=1)
        if np.any(totals <= 0):
            raise ValueError("100% 堆疊每一列的合計必須大於 0。")
        matrix = np.divide(
            matrix,
            totals[:, None],
            out=np.zeros_like(matrix, dtype=float),
            where=totals[:, None] != 0,
        )
    return [matrix[:, index] for index in range(matrix.shape[1])]


def resolved_stack_mode(chart: dict[str, Any]) -> str:
    if str(chart.get("type", "")).endswith("_100"):
        return "percent100"
    return str(chart.get("stack_mode", "absolute"))


def draw_stacked_bar_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    colors: list[Any],
) -> None:
    x_values = frame[chart["x"]]
    plot_x, width, x_is_date = compact_bar_geometry(
        x_values,
        float(chart.get("bar_width_ratio", DEFAULT_BAR_WIDTH_RATIO)),
    )
    columns = ensure_string_list(chart["y"], "y")
    stack_mode = resolved_stack_mode(chart)
    prepared_values = prepare_stack_values(frame, columns, stack_mode)
    positive_bottom = np.zeros(len(frame), dtype=float)
    negative_bottom = np.zeros(len(frame), dtype=float)
    for index, (column, values) in enumerate(zip(columns, prepared_values)):
        bottoms = np.where(values >= 0, positive_bottom, negative_bottom)
        ax.bar(
            plot_x,
            values,
            bottom=bottoms,
            width=width,
            label=column,
            color=colors[index],
            alpha=float(chart.get("bar_alpha", DEFAULT_BAR_ALPHA)),
        )
        positive_bottom += np.where(values >= 0, values, 0)
        negative_bottom += np.where(values < 0, values, 0)
    if stack_mode == "percent100":
        ax.set_ylim(0, 1)
    if x_is_date:
        ax.xaxis_date()
    else:
        ax.set_xticks(plot_x)
        ax.set_xticklabels(x_values.astype(str))


def draw_stacked_area_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    colors: list[Any],
) -> None:
    columns = ensure_string_list(chart["y"], "y")
    stack_mode = resolved_stack_mode(chart)
    values = prepare_stack_values(frame, columns, stack_mode)
    alpha = float(chart.get("area_alpha", DEFAULT_AREA_ALPHA))
    if stack_mode == "absolute" and any(np.any(values_item < 0) for values_item in values):
        positive_values = [np.clip(values_item, 0, None) for values_item in values]
        negative_values = [np.clip(values_item, None, 0) for values_item in values]
        ax.stackplot(
            frame[chart["x"]],
            *positive_values,
            labels=columns,
            colors=colors,
            alpha=alpha,
        )
        ax.stackplot(
            frame[chart["x"]],
            *negative_values,
            labels=["_nolegend_" for _column in columns],
            colors=colors,
            alpha=alpha,
        )
        return
    ax.stackplot(
        frame[chart["x"]],
        *values,
        labels=columns,
        colors=colors,
        alpha=alpha,
    )
    if stack_mode == "percent100":
        ax.set_ylim(0, 1)


def draw_heatmap_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
) -> None:
    pivot = frame.pivot_table(
        index=chart["heatmap_index"],
        columns=chart["heatmap_columns"],
        values=chart["heatmap_value"],
        aggfunc=str(chart.get("heatmap_aggfunc", "mean")),
    )
    sns.heatmap(
        pivot,
        ax=ax,
        cmap=str(chart.get("cmap", "RdYlGn")),
        center=chart.get("center", 0),
        annot=bool(chart.get("annot", False)),
        fmt=str(chart.get("annot_format", ".1f")),
        linewidths=0.35,
        linecolor=DEFAULT_GRID_COLOR,
        cbar_kws={"label": str(chart.get("unit", "")), "shrink": 0.72},
    )


def draw_secondary_axis(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    colors: list[Any],
) -> Axes | None:
    secondary_columns = ensure_string_list(chart.get("secondary_y"), "secondary_y")
    axis_mode = str(chart.get("axis_mode", "auto"))
    if not secondary_columns or axis_mode == "single":
        return None
    secondary_ax = ax.twinx()
    x = chart["x"]
    secondary_type = str(chart.get("secondary_type", "line"))
    for index, column in enumerate(secondary_columns):
        color = colors[index % len(colors)]
        if secondary_type == "bar":
            x_values = frame[x]
            plot_x, width, x_is_date = compact_bar_geometry(
                x_values,
                float(chart.get("bar_width_ratio", DEFAULT_BAR_WIDTH_RATIO)),
            )
            secondary_ax.bar(
                plot_x,
                to_numeric_series(frame, column),
                width=width,
                label=column,
                color=color,
                alpha=float(chart.get("bar_alpha", DEFAULT_BAR_ALPHA)),
                zorder=0,
            )
            if x_is_date:
                secondary_ax.xaxis_date()
        elif secondary_type == "area":
            values = to_numeric_series(frame, column)
            secondary_ax.plot(frame[x], values, label=column, color=color, linewidth=1.1)
            secondary_ax.fill_between(
                frame[x],
                values,
                0,
                color=color,
                alpha=float(chart.get("area_alpha", DEFAULT_AREA_ALPHA)),
            )
        else:
            sns.lineplot(
                data=frame,
                x=x,
                y=column,
                ax=secondary_ax,
                label=column,
                color=color,
                linewidth=float(chart.get("secondary_line_width", 1.35)),
                linestyle=str(chart.get("secondary_line_style", "--")),
                alpha=float(chart.get("secondary_alpha", 0.88)),
                errorbar=None,
            )
    secondary_ax.set_ylabel(str(chart.get("secondary_unit", "")), color=DEFAULT_MUTED_COLOR)
    secondary_ax.grid(False)
    return secondary_ax


def draw_chart(
    ax: Axes,
    frame: pd.DataFrame,
    chart: dict[str, Any],
    project: dict[str, Any],
) -> Axes | None:
    chart_type = chart["type"]
    if chart_type == "candlestick":
        return draw_candlestick_chart(ax, frame, chart)
    y_columns = ensure_string_list(chart.get("y"), "y")
    y_count = len(y_columns)
    colors = get_palette(chart, project, max(y_count, 1), y_columns)
    if chart_type == "line":
        draw_line_chart(ax, frame, chart, colors)
    elif chart_type == "bar":
        draw_bar_chart(ax, frame, chart, colors)
    elif chart_type == "area":
        draw_area_chart(ax, frame, chart, colors)
    elif chart_type == "scatter":
        draw_scatter_chart(ax, frame, chart, colors)
    elif chart_type == "step":
        draw_step_chart(ax, frame, chart, colors)
    elif chart_type in {"stacked_bar", "stacked_bar_100"}:
        draw_stacked_bar_chart(ax, frame, chart, colors)
    elif chart_type in {"stacked_area", "stacked_area_100"}:
        draw_stacked_area_chart(ax, frame, chart, colors)
    elif chart_type == "heatmap":
        draw_heatmap_chart(ax, frame, chart)
    if chart_type in STACKED_CHART_TYPES | {"heatmap"}:
        return None
    secondary_columns = ensure_string_list(chart.get("secondary_y"), "secondary_y")
    secondary_colors = get_palette({"palette": "Set2"}, project, max(len(secondary_columns), 1), secondary_columns)
    return draw_secondary_axis(ax, frame, chart, secondary_colors)


# =============================================================================
# 4. 格式、共用時間軸、圖例與整體版面
# =============================================================================


def magnitude_formatter(value: float, _position: int) -> str:
    absolute = abs(value)
    if absolute >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    if absolute >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if absolute >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:.1f}"


def nice_step_candidates(rough_step: float) -> list[float]:
    safe_rough = max(abs(float(rough_step)), np.finfo(float).eps)
    exponent = int(math.floor(math.log10(safe_rough)))
    candidates = {
        mantissa * (10.0**power)
        for power in range(exponent - 2, exponent + 4)
        for mantissa in NICE_STEP_MANTISSAS
    }
    return sorted(step for step in candidates if step > 0)


def compute_locked_ticks(
    minimum: float,
    maximum: float,
    tick_count: int = DEFAULT_TICK_COUNT,
    include_zero: bool = False,
) -> np.ndarray:
    if tick_count < 2:
        raise ValueError("tick_count 必須至少為 2。")
    if not math.isfinite(minimum) or not math.isfinite(maximum):
        return np.linspace(0, 1, tick_count)
    if minimum > maximum:
        minimum, maximum = maximum, minimum
    data_is_nonnegative = minimum >= 0
    data_is_nonpositive = maximum <= 0
    if minimum == maximum:
        padding = abs(minimum) * 0.1 or 1.0
        minimum -= padding
        maximum += padding
    if include_zero:
        minimum = min(minimum, 0.0)
        maximum = max(maximum, 0.0)
    interval_count = tick_count - 1
    rough_step = (maximum - minimum) / interval_count
    best: tuple[float, float, float] | None = None
    for step in nice_step_candidates(rough_step):
        total_span = interval_count * step
        start_quantum = step / 4.0
        start_min = int(math.ceil((maximum - total_span) / start_quantum - 1e-12))
        start_max = int(math.floor(minimum / start_quantum + 1e-12))
        for start_index in range(start_min, start_max + 1):
            lower = start_index * start_quantum
            upper = lower + total_span
            if lower > minimum + 1e-10 or upper < maximum - 1e-10:
                continue
            if include_zero and not (lower <= 0 <= upper):
                continue
            if include_zero and data_is_nonnegative and not math.isclose(lower, 0.0, abs_tol=step * 1e-10):
                continue
            if include_zero and data_is_nonpositive and not math.isclose(upper, 0.0, abs_tol=step * 1e-10):
                continue
            slack = (minimum - lower) + (upper - maximum)
            center_distance = abs(((lower + upper) / 2) - ((minimum + maximum) / 2))
            score = slack + center_distance * 0.01
            if best is None or score < best[0] - 1e-12 or (abs(score - best[0]) <= 1e-12 and step < best[1]):
                best = (score, step, lower)
        if best is not None and step > rough_step * 10:
            break
    if best is None:
        step = nice_step_candidates(rough_step)[0]
        lower = math.floor(minimum / step) * step
    else:
        _score, step, lower = best
    ticks = lower + np.arange(tick_count, dtype=float) * step
    ticks[np.isclose(ticks, 0, atol=step * 1e-10)] = 0.0
    return ticks


def chart_requires_zero(chart: dict[str, Any]) -> bool:
    zero_policy = str(chart.get("axis_zero_policy", "auto"))
    if zero_policy == "include":
        return True
    if zero_policy == "exclude":
        return False
    return str(chart.get("type", "")) in {"bar", "stacked_bar", "stacked_bar_100"}


def axis_data_limits(ax: Axes) -> tuple[float, float]:
    """Use artist data limits instead of Matplotlib's padded view limits."""

    data_minimum, data_maximum = [float(value) for value in ax.dataLim.intervaly]
    if math.isfinite(data_minimum) and math.isfinite(data_maximum):
        return data_minimum, data_maximum
    view_minimum, view_maximum = ax.get_ylim()
    return float(view_minimum), float(view_maximum)


def apply_axis_policy(ax: Axes, chart: dict[str, Any], secondary: bool = False) -> None:
    tick_count = int(chart.get("tick_count", DEFAULT_TICK_COUNT))
    tick_policy = str(chart.get("tick_policy", "vap_locked"))
    if resolved_stack_mode(chart) == "percent100" and not secondary:
        ticks = np.linspace(0, 1, tick_count)
        ax.set_ylim(0, 1)
        ax.set_yticks(ticks)
        return
    if tick_policy == "vap_locked":
        minimum, maximum = axis_data_limits(ax)
        include_zero = chart_requires_zero(chart)
        if secondary:
            secondary_zero_policy = str(chart.get("secondary_axis_zero_policy", "auto"))
            include_zero = secondary_zero_policy == "include" or (
                secondary_zero_policy == "auto"
                and (
                    str(chart.get("type", "")) == "candlestick"
                    or str(chart.get("secondary_type", "line")) == "bar"
                )
            )
        ticks = compute_locked_ticks(float(minimum), float(maximum), tick_count, include_zero)
        ax.set_ylim(float(ticks[0]), float(ticks[-1]))
        ax.set_yticks(ticks)
    else:
        ax.yaxis.set_major_locator(MaxNLocator(nbins=tick_count - 1, prune=None))


def decimal_places_for_step(step: float | None, minimum: int = 0) -> int:
    if step is None or not math.isfinite(step) or step == 0:
        return minimum
    rounded = round(abs(float(step)), 12)
    text = f"{rounded:.12f}".rstrip("0").rstrip(".")
    decimals = len(text.split(".", 1)[1]) if "." in text else 0
    return max(minimum, min(decimals, 8))


def axis_uniform_step(ax: Axes) -> float | None:
    ticks = np.asarray(ax.get_yticks(), dtype=float)
    finite_ticks = ticks[np.isfinite(ticks)]
    differences = np.diff(finite_ticks)
    if not len(differences) or not np.allclose(differences, differences[0]):
        return None
    return float(differences[0])


def axis_required_decimals(ax: Axes, minimum: int = 0) -> int:
    step = axis_uniform_step(ax)
    values = [step, *np.asarray(ax.get_yticks(), dtype=float).tolist()]
    decimals = [decimal_places_for_step(value) for value in values if value is not None]
    return max([minimum, *decimals])


def apply_y_format(ax: Axes, y_format: str) -> None:
    if y_format not in SUPPORTED_Y_FORMATS:
        raise ValueError(f"不支援 y_format={y_format!r}")
    step = axis_uniform_step(ax)
    if y_format == "percent":
        percent_decimals = decimal_places_for_step(None if step is None else step * 100, 1)
        ax.yaxis.set_major_formatter(PercentFormatter(xmax=1.0, decimals=percent_decimals))
    elif y_format == "comma":
        decimals = axis_required_decimals(ax)
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda value, _position: f"{value:,.{decimals}f}")
        )
    elif y_format == "magnitude":
        ax.yaxis.set_major_formatter(FuncFormatter(magnitude_formatter))
    elif y_format == "number":
        decimals = axis_required_decimals(ax, minimum=2)
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda value, _position: f"{value:.{decimals}f}")
        )
    elif y_format == "auto":
        decimals = axis_required_decimals(ax)
        if decimals:
            ax.yaxis.set_major_formatter(
                FuncFormatter(lambda value, _position: f"{value:.{decimals}f}")
            )


def format_date_axis(ax: Axes, max_ticks: int = DEFAULT_MAX_X_TICKS) -> None:
    locator = mdates.AutoDateLocator(minticks=4, maxticks=max_ticks)
    data_min, data_max = [float(value) for value in ax.dataLim.intervalx]
    if math.isfinite(data_min) and math.isfinite(data_max) and data_min < data_max:
        automatic = locator.tick_values(mdates.num2date(data_min), mdates.num2date(data_max))
        span_days = data_max - data_min
        edge_clearance = max(1.0, span_days / max(max_ticks * 2, 1))
        interior = automatic[
            (automatic > data_min + edge_clearance)
            & (automatic < data_max - edge_clearance)
        ]
        ticks = np.unique(np.concatenate(([data_min], interior, [data_max])))
        effective_locator = FixedLocator(ticks)
        def date_tick_formatter(value: float, _position: int) -> str:
            date_value = mdates.num2date(value)
            if math.isclose(value, data_min, abs_tol=0.5) or math.isclose(value, data_max, abs_tol=0.5):
                return date_value.strftime("%Y-%m-%d")
            if span_days <= 100:
                return date_value.strftime("%m-%d")
            if span_days <= 730:
                return date_value.strftime("%b")
            return date_value.strftime("%Y-%m")
        formatter = FuncFormatter(date_tick_formatter)
    else:
        effective_locator = locator
        formatter = mdates.ConciseDateFormatter(effective_locator)
    ax.xaxis.set_major_locator(effective_locator)
    ax.xaxis.set_major_formatter(formatter)


def combine_legends(ax: Axes, secondary_ax: Axes | None) -> None:
    handles, labels = ax.get_legend_handles_labels()
    if secondary_ax is not None:
        secondary_handles, secondary_labels = secondary_ax.get_legend_handles_labels()
        handles.extend(secondary_handles)
        labels.extend(secondary_labels)
        old_legend = secondary_ax.get_legend()
        if old_legend is not None:
            old_legend.remove()
    old_primary = ax.get_legend()
    if old_primary is not None:
        old_primary.remove()
    if not handles:
        return
    unique: dict[str, Any] = {}
    for handle, label in zip(handles, labels):
        unique.setdefault(label, handle)
    ax.legend(
        unique.values(),
        unique.keys(),
        loc="upper left",
        bbox_to_anchor=(0, 1.01),
        frameon=False,
        ncol=min(DEFAULT_LEGEND_COLUMNS, max(len(unique), 1)),
        fontsize=8.3,
        handlelength=1.8,
        columnspacing=1.15,
    )


def axis_tick_report(ax: Axes | None) -> dict[str, Any] | None:
    if ax is None:
        return None
    ticks = np.asarray(ax.get_yticks(), dtype=float)
    finite_ticks = ticks[np.isfinite(ticks)]
    differences = np.diff(finite_ticks)
    step = float(differences[0]) if len(differences) and np.allclose(differences, differences[0]) else None
    formatter = ax.yaxis.get_major_formatter()
    return {
        "count": int(len(finite_ticks)),
        "minimum": float(finite_ticks[0]) if len(finite_ticks) else None,
        "maximum": float(finite_ticks[-1]) if len(finite_ticks) else None,
        "step": step,
        "decimals": axis_required_decimals(ax),
        "values": [float(value) for value in finite_ticks.tolist()],
        "labels": [str(formatter(value, index)) for index, value in enumerate(finite_ticks)],
    }


def format_panel(
    ax: Axes,
    secondary_ax: Axes | None,
    chart: dict[str, Any],
    project: dict[str, Any],
    is_last: bool,
    x_is_date: bool,
) -> None:
    ax.set_facecolor(str(project.get("axes_face_color", DEFAULT_AXES_FACE_COLOR)))
    ax.set_title(str(chart.get("title") or chart["id"]), loc="left", fontsize=10.8, fontweight="semibold", pad=10)
    ax.set_ylabel(str(chart.get("unit", "")), fontsize=8.7, color=DEFAULT_MUTED_COLOR)
    ax.set_xlabel(str(chart.get("x_label", "")) if is_last else "", fontsize=8.7)
    ax.tick_params(axis="both", labelsize=8.2)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", visible=True, alpha=0.78)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    if bool(chart.get("show_zero_line")):
        ax.axhline(0, color=DEFAULT_ZERO_COLOR, linewidth=0.8, zorder=0)
    if chart["type"] != "heatmap":
        apply_axis_policy(ax, chart, secondary=False)
        apply_y_format(ax, str(chart.get("y_format", "auto")))
        if secondary_ax is not None:
            apply_axis_policy(secondary_ax, chart, secondary=True)
            apply_y_format(secondary_ax, str(chart.get("secondary_y_format", "auto")))
    if not bool(chart.get("show_legend", True)):
        for target in [ax, secondary_ax]:
            if target is not None and target.get_legend() is not None:
                target.get_legend().remove()
    else:
        combine_legends(ax, secondary_ax)
    notes = str(chart.get("notes", "")).strip()
    if notes:
        ax.text(1.0, 1.015, notes, transform=ax.transAxes, ha="right", va="bottom", fontsize=7.6, color=DEFAULT_MUTED_COLOR)
    if x_is_date and is_last and bool(chart.get("auto_optimize", True)):
        format_date_axis(ax, max_ticks=int(chart.get("max_x_ticks") or project.get("max_x_ticks") or DEFAULT_MAX_X_TICKS))
    if not is_last:
        ax.tick_params(axis="x", which="both", labelbottom=False)


def figure_dimensions(project: dict[str, Any], charts: list[dict[str, Any]]) -> tuple[float, float]:
    width = float(project.get("width_inch", DEFAULT_WIDTH_INCH))
    base_height = float(project.get("panel_height_inch", DEFAULT_PANEL_HEIGHT_INCH))
    profile = str(project.get("layout_profile", "compact_desktop"))
    profile_scale = {"compact_desktop": 1.0, "standard": 1.15, "accessible": 1.35}.get(profile, 1.0)
    total_ratio = sum(float(chart.get("height_ratio", 1.0)) for chart in charts)
    height = max(DEFAULT_MIN_FIGURE_HEIGHT, (base_height * total_ratio + 1.35) * profile_scale)
    return width * (1.08 if profile == "accessible" else 1.0), height


def create_axes(
    project: dict[str, Any],
    charts: list[dict[str, Any]],
) -> tuple[Figure, list[Axes]]:
    width, height = figure_dimensions(project, charts)
    ratios = [float(chart.get("height_ratio", 1.0)) for chart in charts]
    has_heatmap = any(chart["type"] == "heatmap" for chart in charts)
    share_x = bool(project.get("shared_x", True)) and not has_heatmap
    figure, axes_value = plt.subplots(
        nrows=len(charts),
        ncols=1,
        figsize=(width, height),
        sharex=share_x,
        gridspec_kw={"height_ratios": ratios, "hspace": 0.28 if share_x else 0.34},
        facecolor=str(project.get("figure_face_color", DEFAULT_FIGURE_FACE_COLOR)),
        squeeze=False,
    )
    axes = [axes_value[index, 0] for index in range(len(charts))]
    return figure, axes


def add_figure_header(figure: Figure, project: dict[str, Any], single_panel: bool = False) -> None:
    title = str(project.get("title", APP_NAME))
    subtitle = str(project.get("subtitle", ""))
    source = str(project.get("source", "")).strip()
    source_label = str(project.get("source_label", "資料來源")).strip()
    watermark = str(project.get("watermark", "")).strip()
    title_y = 0.965 if single_panel else 0.982
    subtitle_y = 0.885 if single_panel else 0.952
    figure.suptitle(title, x=0.055, y=title_y, ha="left", va="top", fontsize=17, fontweight="bold", color=DEFAULT_TEXT_COLOR)
    if subtitle:
        figure.text(0.055, subtitle_y, subtitle, ha="left", va="top", fontsize=9.6, color=DEFAULT_MUTED_COLOR)
    if source:
        figure.text(0.055, 0.012, f"{source_label}: {source}", ha="left", va="bottom", fontsize=7.8, color=DEFAULT_MUTED_COLOR)
    if watermark:
        figure.text(0.955, 0.012, watermark, ha="right", va="bottom", fontsize=8.2, color=DEFAULT_MUTED_COLOR)


def verify_output_artifact(path: Path, output_format: str) -> None:
    """Reject incomplete output before it replaces the last valid artifact."""

    if not path.exists() or path.stat().st_size < 100:
        raise OSError(f"輸出檔不存在或不完整：{path}")
    normalized = output_format.lower().lstrip(".")
    if normalized == "png":
        from PIL import Image

        with Image.open(path) as image:
            image.verify()
    elif normalized == "pdf":
        with path.open("rb") as handle:
            header = handle.read(5)
            handle.seek(max(0, path.stat().st_size - 1024))
            trailer = handle.read()
        if header != b"%PDF-" or b"%%EOF" not in trailer:
            raise OSError(f"PDF header/trailer 不完整：{path}")
    elif normalized == "svg":
        from xml.etree import ElementTree

        ElementTree.parse(path)
    elif normalized == "html":
        with path.open("r", encoding="utf-8") as handle:
            prefix = handle.read(4096).lower()
        if "<!doctype html" not in prefix or "<html" not in prefix:
            raise OSError(f"HTML 文件結構不完整：{path}")


def save_figure(
    figure: Figure,
    config_path: Path,
    project: dict[str, Any],
    html_panels: list[dict[str, Any]] | None = None,
) -> list[Path]:
    output_directory = resolve_from_config(config_path, str(project.get("output_directory", "output")))
    output_directory.mkdir(parents=True, exist_ok=True)
    output_name = validate_safe_basename(
        project.get("output_name", "vap_seaborn_vertical_stack"),
        "project.output_name",
    )
    formats = ensure_string_list(project.get("output_formats", DEFAULT_OUTPUT_FORMATS), "output_formats")
    saved_paths: list[Path] = []
    for output_format in formats:
        normalized = output_format.lower().lstrip(".")
        if normalized not in {"png", "pdf", "svg", "html"}:
            raise ValueError(f"不支援的輸出格式：{normalized}")
        output_path = output_directory / f"{output_name}.{normalized}"
        cleanup_stale_temporary_files(output_path)
        if normalized == "html":
            html_renderer = str(project.get("html_renderer", "plotly")).strip().lower()
            if html_renderer == "plotly":
                if not html_panels:
                    raise ValueError("Plotly HTML 輸出缺少已準備的 panel 資料。")
                try:
                    from vap_plotly_stack_renderer import write_plotly_stack_html
                except ImportError as exc:
                    raise RuntimeError(
                        "Plotly HTML renderer 無法載入；請確認 vap_plotly_stack_renderer.py "
                        "與 requirements.txt 已完整安裝。"
                    ) from exc
                write_plotly_stack_html(output_path, project, html_panels)
                verify_output_artifact(output_path, normalized)
                saved_paths.append(output_path)
                continue
            if html_renderer != "svg":
                raise ValueError("html_renderer 只支援 plotly 或 svg。")
            svg_buffer = StringIO()
            figure.savefig(
                svg_buffer,
                format="svg",
                bbox_inches="tight",
                facecolor=figure.get_facecolor(),
                metadata={"Creator": f"{APP_NAME} {APP_VERSION}"},
            )
            svg_text = svg_buffer.getvalue()
            svg_start = svg_text.find("<svg")
            if svg_start >= 0:
                svg_text = svg_text[svg_start:]
            title = escape(str(project.get("title", APP_NAME)))
            html_text = f"""<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{ color-scheme: light; font-family: Arial, 'Microsoft JhengHei', sans-serif; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #f3f6f9; color: #243247; }}
    main {{ width: min(100%, 1680px); margin: 0 auto; padding: 10px; }}
    .chart-card {{ width: 100%; overflow-x: auto; background: #fff; border: 1px solid #dce3ea; border-radius: 4px; padding: 6px; }}
    .chart-card svg {{ display: block; width: 100%; height: auto; min-width: 760px; }}
    .note {{ margin: 7px 2px 0; color: #68778b; font-size: 11px; }}
    @media (max-width: 768px) {{ main {{ padding: 4px; }} .chart-card svg {{ min-width: 620px; }} }}
    @media print {{ body, main {{ background: #fff; padding: 0; }} .chart-card {{ border: 0; }} .note {{ display: none; }} }}
  </style>
</head>
<body>
  <main>
    <section class="chart-card" aria-label="{title}">{svg_text}</section>
    <p class="note">離線響應式 Seaborn 向量輸出；互動 hover／縮放需使用獨立 Plotly renderer。</p>
  </main>
</body>
</html>
"""
            temporary_output = output_path.with_name(
                f".{output_path.name}.{os.getpid()}.tmp"
            )
            try:
                temporary_output.write_text(html_text, encoding="utf-8", newline="\n")
                verify_output_artifact(temporary_output, normalized)
                temporary_output.replace(output_path)
            finally:
                temporary_output.unlink(missing_ok=True)
        else:
            temporary_output = output_path.with_name(
                f".{output_path.name}.{os.getpid()}.tmp"
            )
            try:
                figure.savefig(
                    temporary_output,
                    format=normalized,
                    dpi=int(project.get("dpi", DEFAULT_DPI)),
                    bbox_inches="tight",
                    facecolor=figure.get_facecolor(),
                    metadata={"Creator": f"{APP_NAME} {APP_VERSION}"},
                )
                verify_output_artifact(temporary_output, normalized)
                temporary_output.replace(output_path)
            finally:
                temporary_output.unlink(missing_ok=True)
        saved_paths.append(output_path)
    return saved_paths


# =============================================================================
# 5. 單圖／圖組渲染主流程
# =============================================================================


def render_chart_collection(
    config_path: Path,
    project: dict[str, Any],
    charts: list[dict[str, Any]],
    show: bool = False,
    render_mode: str = "stack",
) -> dict[str, Any]:
    effective_config = {"project": project, "charts": charts}
    warnings = validate_config(effective_config)
    output_name = validate_safe_basename(
        project.get("output_name", "vap_seaborn_vertical_stack"),
        "project.output_name",
    )
    configure_theme(project)
    render_rows = expand_render_row_specs(charts)
    figure, axes = create_axes(project, render_rows)
    frame_cache: dict[str, pd.DataFrame] = {}
    panel_report: list[dict[str, Any]] = []
    html_panels: list[dict[str, Any]] = []
    diagnostics: list[dict[str, Any]] = []
    try:
        axis_cursor = 0
        for chart in charts:
            full_frame, quality_report = prepare_chart_frame(
                chart,
                project,
                config_path,
                frame_cache,
            )
            render_max_points = int(
                chart.get("render_max_points")
                or project.get("render_max_points", DEFAULT_RENDER_MAX_POINTS)
            )
            if bool(chart.get("auto_optimize", True)):
                frame, render_optimization = optimize_frame_for_chart(
                    full_frame,
                    chart,
                    render_max_points,
                )
            else:
                frame = full_frame.copy(deep=True)
                render_optimization = {
                    "optimized": False,
                    "lossy": False,
                    "method": "disabled",
                    "chart_type": str(chart.get("type", "")).lower(),
                    "input_points": int(len(full_frame)),
                    "output_points": int(len(full_frame)),
                    "max_points": render_max_points,
                    "preserved_endpoints": bool(len(full_frame)),
                    "warnings": ["auto_optimize 已關閉；renderer 使用完整資料。"],
                }
            html_panels.append({"chart": deepcopy(chart), "frame": frame.copy()})
            x_column = str(chart.get("x", ""))
            x_is_date = bool(x_column and pd.api.types.is_datetime64_any_dtype(frame[x_column]))
            rendered_subpanels: list[dict[str, Any]] = []
            secondary_ax: Axes | None = None
            if str(chart.get("type", "")).lower() == "candlestick":
                price_ax = axes[axis_cursor]
                volume_ax = axes[axis_cursor + 1]
                price_row = render_rows[axis_cursor]
                volume_row = render_rows[axis_cursor + 1]
                draw_candlestick_price_chart(price_ax, frame, chart)
                draw_candlestick_volume_chart(volume_ax, frame, chart)
                format_panel(
                    price_ax,
                    None,
                    price_row,
                    project,
                    False,
                    x_is_date,
                )
                format_panel(
                    volume_ax,
                    None,
                    volume_row,
                    project,
                    axis_cursor + 1 == len(axes) - 1,
                    x_is_date,
                )
                ax = price_ax
                rendered_subpanels = [
                    {
                        "role": "price",
                        "axis_mode": "single",
                        "height_ratio": float(price_row["height_ratio"]),
                        "axis_ticks": {"left": axis_tick_report(price_ax), "right": None},
                    },
                    {
                        "role": "volume",
                        "axis_mode": "single",
                        "height_ratio": float(volume_row["height_ratio"]),
                        "axis_ticks": {"left": axis_tick_report(volume_ax), "right": None},
                    },
                ]
                axis_cursor += 2
            else:
                ax = axes[axis_cursor]
                secondary_ax = draw_chart(ax, frame, chart, project)
                format_panel(
                    ax,
                    secondary_ax,
                    chart,
                    project,
                    axis_cursor == len(axes) - 1,
                    x_is_date,
                )
                rendered_subpanels = [
                    {
                        "role": "chart",
                        "axis_mode": str(chart.get("axis_mode", "auto")),
                        "height_ratio": float(chart.get("height_ratio", 1.0)),
                        "axis_ticks": {
                            "left": axis_tick_report(ax),
                            "right": axis_tick_report(secondary_ax),
                        },
                    }
                ]
                axis_cursor += 1
            panel_report.append(
                {
                    "id": chart["id"],
                    "type": chart["type"],
                    "axis_mode": (
                        "split_single"
                        if str(chart.get("type", "")).lower() == "candlestick"
                        else chart.get("axis_mode", "auto")
                    ),
                    "tick_policy": chart.get("tick_policy", "vap_locked"),
                    "stack_mode": resolved_stack_mode(chart),
                    "html_renderer": str(project.get("html_renderer", "plotly")),
                    "price_basis": str(chart.get("price_basis", "")),
                    "normalized_y": ensure_string_list(chart.get("normalized_y"), "normalized_y"),
                    "rows": int(len(full_frame)),
                    "rendered_rows": int(len(frame)),
                    "columns": required_columns_for_chart(chart),
                    "axis_ticks": {
                        "left": axis_tick_report(ax),
                        "right": axis_tick_report(secondary_ax),
                    },
                    "render_panels": rendered_subpanels,
                    "render_optimization": render_optimization,
                    "quality": quality_report,
                }
            )
            repair_actions = {str(repair.get("action", "")) for repair in quality_report.get("repairs", [])}
            for issue in quality_report.get("before", {}).get("issues", []):
                issue_code = str(issue.get("code", ""))
                repaired = (
                    (issue_code == "missing_values" and any(action.startswith("missing_") or action == "drop_rows" for action in repair_actions))
                    or (issue_code in {"invalid_dates", "duplicate_grain"} and "drop_rows" in repair_actions)
                    or (issue_code == "outliers" and "clip_iqr" in repair_actions)
                )
                diagnostics.append(
                    {
                        **issue,
                        "scope": "chart",
                        "chart_id": str(chart["id"]),
                        "stage": "data_quality",
                        "action_status": "applied" if repaired else "not_applied",
                        "data_changed": repaired,
                    }
                )
        single_panel = len(render_rows) == 1
        add_figure_header(figure, project, single_panel=single_panel)
        figure.subplots_adjust(
            left=0.055,
            right=0.955,
            top=0.76 if single_panel else 0.895,
            bottom=0.14 if single_panel else 0.055,
        )
        saved_paths = save_figure(
            figure,
            config_path,
            project,
            html_panels=html_panels,
        )
        if show:
            plt.show()
    finally:
        plt.close(figure)
    diagnostic_status = "ERROR" if any(item.get("severity") == "error" for item in diagnostics) else (
        "WARN" if any(item.get("severity") == "warning" for item in diagnostics) else "OK"
    )
    diagnostic_payload = {
        "schema": "VIA-VAP-DIAGNOSTICS/2.3",
        "status": diagnostic_status,
        "issues": diagnostics,
        "transformations": [
            {"chart_id": panel["id"], **repair}
            for panel in panel_report
            for repair in panel.get("quality", {}).get("repairs", [])
        ]
        + [
            {
                "chart_id": panel["id"],
                "action": "render_optimize",
                **panel["render_optimization"],
            }
            for panel in panel_report
            if bool(panel.get("render_optimization", {}).get("optimized"))
        ],
    }
    report = {
        "status": "OK",
        "generator": APP_NAME,
        "version": APP_VERSION,
        "config": str(config_path),
        "render_mode": render_mode,
        "chart_count": len(charts),
        "render_panel_count": len(render_rows),
        "outputs": [str(path) for path in saved_paths],
        "panels": panel_report,
        "warnings": warnings,
        "diagnostics": diagnostic_payload,
        "rendered_at": utc_now_text(),
    }
    output_directory = resolve_from_config(config_path, str(project.get("output_directory", "output")))
    audit_path = output_directory / f"{output_name}_audit.json"
    audit_payload = {
        **diagnostic_payload,
        "data_changed": any(
            bool(panel.get("quality", {}).get("data_changed"))
            for panel in panel_report
        ),
        "charts": [
            {
                "chart_id": panel["id"],
                "before": panel.get("quality", {}).get("before", {}),
                "after": panel.get("quality", {}).get("after", {}),
                "repairs": panel.get("quality", {}).get("repairs", []),
                "render_optimization": panel.get("render_optimization", {}),
                "data_changed": bool(panel.get("quality", {}).get("data_changed")),
            }
            for panel in panel_report
        ],
    }
    write_json(audit_path, audit_payload)
    report["audit"] = str(audit_path)
    report_path = output_directory / f"{output_name}_report.json"
    report["report"] = str(report_path)
    portable_report = deepcopy(report)
    portable_report["config"] = safe_relpath(config_path, output_directory)
    portable_report["outputs"] = [
        safe_relpath(path, output_directory)
        for path in saved_paths
    ]
    portable_report["audit"] = safe_relpath(audit_path, output_directory)
    portable_report["report"] = safe_relpath(report_path, output_directory)
    write_json(report_path, portable_report)
    return report


def render_stack(config_path: Path, show: bool = False) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = read_json(config_path)
    project, charts = normalize_project_and_charts(config)
    return render_chart_collection(config_path, project, charts, show=show, render_mode="stack")


def render_single_chart(config_path: Path, chart_id: str, show: bool = False) -> dict[str, Any]:
    config_path = config_path.resolve()
    config = read_json(config_path)
    project, charts = normalize_project_and_charts(config)
    selected = next((chart for chart in charts if str(chart.get("id")) == chart_id), None)
    if selected is None:
        raise KeyError(f"找不到圖表 id：{chart_id}")
    single_project = deepcopy(project)
    base_output_name = str(project.get("output_name", "vap_seaborn_chart"))
    single_project["output_name"] = f"{base_output_name}__{chart_id}"
    # A logical candlestick still expands into two physical panels (price and
    # volume).  Keep those panels on one matched time axis in render-one mode;
    # only a truly single-row chart can safely disable shared-X matching.
    single_project["shared_x"] = str(selected.get("type", "")) == "candlestick"
    return render_chart_collection(
        config_path,
        single_project,
        [selected],
        show=show,
        render_mode="single",
    )


# =============================================================================
# 6. 範例資料、範例圖組與 CLI
# =============================================================================


def make_demo_data(path: Path, row_count: int = 180, seed: int = 42) -> pd.DataFrame:
    random = np.random.default_rng(seed)
    dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=row_count)
    returns = random.normal(0.0007, 0.013, row_count)
    close = 100 * np.exp(np.cumsum(returns))
    previous_close = np.concatenate(([close[0]], close[:-1]))
    adjusted_open = previous_close * np.exp(random.normal(0.0, 0.0045, row_count))
    intraday_range = np.abs(random.normal(0.009, 0.004, row_count))
    adjusted_high = np.maximum(adjusted_open, close) * (1.0 + intraday_range)
    adjusted_low = np.minimum(adjusted_open, close) * np.maximum(0.01, 1.0 - intraday_range)
    volume = random.lognormal(mean=16.1, sigma=0.35, size=row_count)
    foreign = random.normal(0, 1.8e8, row_count)
    trust = random.normal(0, 8.5e7, row_count)
    dealer = random.normal(0, 5.5e7, row_count)
    composition = random.dirichlet([4.0, 3.0, 2.0], row_count)
    frame = pd.DataFrame(
        {
            "Date": dates,
            "AdjOpen": adjusted_open,
            "AdjHigh": adjusted_high,
            "AdjLow": adjusted_low,
            "AdjClose": close,
            "MA20": pd.Series(close).rolling(20, min_periods=1).mean(),
            "Volume": volume,
            "Foreign": foreign,
            "Trust": trust,
            "Dealer": dealer,
            "Momentum": pd.Series(close).pct_change(20),
            "NormalizedMomentum": (returns - float(np.mean(returns))) / float(np.std(returns)),
            "SectorA": composition[:, 0],
            "SectorB": composition[:, 1],
            "SectorC": composition[:, 2],
        }
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False, encoding="utf-8-sig", date_format=DEFAULT_DATE_FORMAT)
    return frame


def make_demo_config(config_path: Path) -> dict[str, Any]:
    data_path = config_path.parent / "demo_market_data.csv"
    make_demo_data(data_path)
    config = default_project_config(data_path.name)
    config["project"].update(
        {
            "title": "VAP · Plotly Stack × Seaborn Color Combo",
            "subtitle": "Adjusted OHLCV, single/dual axes and stacked panels appended downward",
            "source": "Synthetic demonstration data",
            "source_label": "Source",
            "output_directory": "../output",
            "output_name": "vap_seaborn_stack_demo",
            "watermark": "VAP",
        }
    )
    candlestick = default_chart_spec(
        "adjusted_candlestick_volume",
        "candlestick",
        "Adjusted Candlestick + Volume · Red Up / Green Down",
        "Date",
        [],
    )
    candlestick = apply_preset(candlestick, "candlestick_volume")
    candlestick.update(
        {
            "open": "AdjOpen",
            "high": "AdjHigh",
            "low": "AdjLow",
            "close": "AdjClose",
            "volume": "Volume",
            "y": [],
            "secondary_y": [],
            "unit": "Adjusted Price",
            "secondary_unit": "Volume",
            "price_label": "Candlestick (red up / green down)",
        }
    )
    price = default_chart_spec("single_axis_price", "line", "Single Axis · Adjusted Close and MA20", "Date", ["AdjClose", "MA20"])
    price = apply_preset(price, "price")
    price.update(
        {
            "unit": "Price",
            "tick_policy": "vap_locked",
            "normalized_y": ["NormalizedMomentum"],
        }
    )
    dual = default_chart_spec("dual_axis_price_volume", "line", "Dual Axis · Price and Volume", "Date", ["AdjClose"])
    dual = apply_preset(dual, "price_volume_dual")
    dual.update({"secondary_y": ["Volume"], "unit": "Price", "secondary_unit": "Volume"})
    flow = default_chart_spec("institutional_flow", "stacked_bar", "Institutional Net Flow", "Date", ["Foreign", "Trust", "Dealer"])
    flow.update({"unit": "TWD", "height_ratio": 1.0, "y_format": "magnitude", "show_zero_line": True, "palette": "Set2", "axis_mode": "single"})
    composition_chart = default_chart_spec("composition_100", "stacked_area_100", "100% Stacked Composition", "Date", ["SectorA", "SectorB", "SectorC"])
    composition_chart = apply_preset(composition_chart, "composition")
    composition_chart.update({"type": "stacked_area_100", "unit": "%"})
    config["charts"] = [candlestick, price, dual, flow, composition_chart]
    write_json(config_path, config)
    return config


def chart_from_suggestion(manifest: dict[str, Any], chart_id: str = "auto_chart") -> dict[str, Any]:
    suggestion = manifest.get("suggestion", {})
    x_column = str(suggestion.get("x", ""))
    y_columns = ensure_string_list(suggestion.get("y"), "y")
    secondary_columns = ensure_string_list(suggestion.get("secondary_y"), "secondary_y")
    chart_type = str(suggestion.get("chart_type", "line"))
    if chart_type == "candlestick":
        y_columns = []
        secondary_columns = []
    title_metric = ", ".join(y_columns[:3]) or "Auto Chart"
    if chart_type == "candlestick":
        title = "Adjusted Candlestick + Volume"
    else:
        title = f"{title_metric} by {x_column}" if x_column else title_metric
    chart = default_chart_spec(chart_id, chart_type, title, x_column, y_columns)
    preset = str(suggestion.get("preset", "")).strip()
    if preset:
        chart = apply_preset(chart, preset)
    chart.update(
        {
            "id": chart_id,
            "type": chart_type,
            "title": title,
            "x": x_column,
            "y": y_columns,
            "secondary_y": secondary_columns,
            "axis_mode": (
                "single"
                if chart_type == "candlestick"
                else str(suggestion.get("axis_mode", "auto"))
            ),
            "auto_reason": str(suggestion.get("reason", "")),
            "auto_confidence": float(suggestion.get("confidence", 0.0)),
        }
    )
    for mapping_key in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "normalized_y",
        "price_basis",
        "derive_adjusted_prices",
    ]:
        if mapping_key in suggestion:
            chart[mapping_key] = deepcopy(suggestion[mapping_key])
    profiles = {str(profile["name"]): profile for profile in manifest.get("columns", [])}
    if y_columns and y_columns[0] in profiles:
        chart["unit"] = str(profiles[y_columns[0]].get("unit", ""))
        if profiles[y_columns[0]].get("semantic_type") == "percentage":
            chart["y_format"] = "percent"
    if secondary_columns and secondary_columns[0] in profiles:
        chart["secondary_unit"] = str(profiles[secondary_columns[0]].get("unit", ""))
    return chart


def relative_source_spec(
    source: str,
    config_path: Path,
    table: str = "",
    sheet: str = "",
) -> dict[str, Any]:
    spec = normalize_source_spec(source)
    if spec.get("kind") != "sqlalchemy" and spec.get("path"):
        absolute_path = Path(str(spec["path"])).expanduser().resolve()
        spec["path"] = safe_relpath(absolute_path, config_path.parent)
    if table:
        spec["table"] = table
    if sheet:
        spec["sheet"] = sheet
    return spec


def auto_configure_source(
    config_path: Path,
    source: str,
    table: str = "",
    sheet: str = "",
    chart_id: str = "auto_chart",
    overwrite: bool = False,
) -> tuple[dict[str, Any], dict[str, Any], Path]:
    config_path = config_path.resolve()
    if config_path.exists() and not overwrite:
        raise FileExistsError(f"設定檔已存在：{config_path}；如需覆寫請加 --force。")
    source_spec = relative_source_spec(source, config_path, table=table, sheet=sheet)
    manifest = discover_source(source_spec, config_directory=config_path.parent)
    chart = chart_from_suggestion(manifest, chart_id=chart_id)
    config = default_project_config("")
    config["project"]["data_source"] = source_spec
    config["project"]["data"] = str(source_spec.get("path", ""))
    config["project"]["date_column"] = str(chart.get("x", "Date"))
    config["project"]["source"] = Path(source).name if "://" not in source else str(manifest.get("kind", "database"))
    config["charts"] = [chart]
    write_json(config_path, config)
    manifest_path = config_path.with_name(f"{config_path.stem}_source_manifest.json")
    write_discovery_manifest(manifest_path, manifest)
    return config, manifest, manifest_path


def print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def command_init(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    if config_path.exists() and not args.force:
        raise FileExistsError(f"設定檔已存在：{config_path}；如需覆寫請加 --force。")
    config = default_project_config(args.data)
    if args.table or args.sheet:
        config["project"]["data_source"] = relative_source_spec(
            args.data,
            config_path,
            table=args.table,
            sheet=args.sheet,
        )
    write_json(config_path, config)
    print_json({"status": "OK", "action": "init", "config": str(config_path)})
    return 0


def command_add(args: argparse.Namespace) -> int:
    provided = vars(args)
    y_columns = ensure_string_list(provided.get("y", []), "y")
    chart = default_chart_spec(
        args.id,
        args.type,
        str(provided.get("title") or args.id),
        str(provided.get("x", "")),
        y_columns,
    )
    if provided.get("preset"):
        chart = apply_preset(chart, str(provided["preset"]))

    # Required arguments are necessarily explicit.  Optional arguments are
    # present only when the user typed them because the add parser uses
    # argparse.SUPPRESS.  This prevents parser defaults from undoing a preset.
    explicit_updates: dict[str, Any] = {"id": args.id, "type": args.type}
    direct_fields = {
        "x": "x",
        "unit": "unit",
        "secondary_unit": "secondary_unit",
        "height_ratio": "height_ratio",
        "missing": "missing",
        "y_format": "y_format",
        "secondary_y_format": "secondary_y_format",
        "axis_mode": "axis_mode",
        "tick_policy": "tick_policy",
        "tick_count": "tick_count",
        "stack_mode": "stack_mode",
        "secondary_type": "secondary_type",
        "alpha": "alpha",
        "line_width": "line_width",
        "secondary_alpha": "secondary_alpha",
        "secondary_line_width": "secondary_line_width",
        "bar_alpha": "bar_alpha",
        "area_alpha": "area_alpha",
        "palette": "palette",
        "data": "data",
        "zero_line": "show_zero_line",
        "positive_negative_colors": "positive_negative_colors",
        "notes": "notes",
    }
    for argument_name, chart_field in direct_fields.items():
        if argument_name in provided:
            explicit_updates[chart_field] = provided[argument_name]
    if "title" in provided:
        explicit_updates["title"] = str(provided["title"] or args.id)
    if "y" in provided:
        explicit_updates["y"] = ensure_string_list(provided["y"], "y")
    if "secondary_y" in provided:
        explicit_updates["secondary_y"] = ensure_string_list(
            provided["secondary_y"],
            "secondary_y",
        )
    chart.update(explicit_updates)
    if args.type == "heatmap":
        for argument_name in ["heatmap_index", "heatmap_columns", "heatmap_value", "cmap"]:
            if argument_name in provided:
                chart[argument_name] = provided[argument_name]
    added = append_chart_spec(Path(args.config).resolve(), chart)
    print_json({"status": "OK", "action": "append_to_bottom", "chart": added})
    return 0


def command_remove(args: argparse.Namespace) -> int:
    removed = remove_chart_spec(Path(args.config).resolve(), args.id)
    if not removed:
        raise KeyError(f"找不到圖表 id：{args.id}")
    print_json({"status": "OK", "action": "remove", "chart_id": args.id})
    return 0


def command_move(args: argparse.Namespace) -> int:
    moved = move_chart_spec(Path(args.config).resolve(), args.id, args.position)
    if not moved:
        raise KeyError(f"找不到圖表 id：{args.id}")
    print_json({"status": "OK", "action": "move", "chart_id": args.id, "position": args.position})
    return 0


def command_list(args: argparse.Namespace) -> int:
    config = read_json(Path(args.config).resolve())
    charts = [
        {"position": index, "id": chart.get("id"), "type": chart.get("type"), "title": chart.get("title")}
        for index, chart in enumerate(config.get("charts", []), start=1)
    ]
    print_json({"status": "OK", "chart_count": len(charts), "charts": charts})
    return 0


def command_render(args: argparse.Namespace) -> int:
    print_json(render_stack(Path(args.config), show=args.show))
    return 0


def command_render_one(args: argparse.Namespace) -> int:
    print_json(render_single_chart(Path(args.config), args.id, show=args.show))
    return 0


def command_discover(args: argparse.Namespace) -> int:
    source_spec = normalize_source_spec(args.source)
    if args.table:
        source_spec["table"] = args.table
    if args.sheet:
        source_spec["sheet"] = args.sheet
    manifest = discover_source(source_spec, sample_rows=args.sample_rows)
    if args.output:
        write_discovery_manifest(Path(args.output).resolve(), manifest)
    print_json(manifest)
    return 0


def command_auto_config(args: argparse.Namespace) -> int:
    config, manifest, manifest_path = auto_configure_source(
        Path(args.config),
        args.source,
        table=args.table,
        sheet=args.sheet,
        chart_id=args.id,
        overwrite=args.force,
    )
    print_json(
        {
            "status": "OK",
            "action": "auto_config",
            "config": str(Path(args.config).resolve()),
            "manifest": str(manifest_path),
            "suggestion": manifest.get("suggestion", {}),
            "chart": config["charts"][0],
        }
    )
    return 0


def command_demo(args: argparse.Namespace) -> int:
    config_path = Path(args.config).resolve()
    make_demo_config(config_path)
    report = render_stack(config_path, show=args.show)
    report["demo_config"] = str(config_path)
    print_json(report)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"{APP_NAME} {APP_VERSION}")
    parser.add_argument("--version", action="version", version=f"%(prog)s {APP_VERSION}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", help="建立空白圖組設定檔")
    init_parser.add_argument("--config", default="vap_stack.json")
    init_parser.add_argument("--data", required=True, help="CSV／Parquet／Excel／JSON／SQLite／DuckDB 資料來源")
    init_parser.add_argument("--table", default="", help="資料庫 table")
    init_parser.add_argument("--sheet", default="", help="Excel sheet")
    init_parser.add_argument("--force", action="store_true")
    init_parser.set_defaults(handler=command_init)

    add_parser = subparsers.add_parser(
        "add",
        help="把新圖追加到圖組最下方",
        argument_default=argparse.SUPPRESS,
    )
    add_parser.add_argument("--config", default="vap_stack.json")
    add_parser.add_argument("--id", required=True)
    add_parser.add_argument("--type", required=True, choices=sorted(SUPPORTED_CHART_TYPES))
    add_parser.add_argument("--title")
    add_parser.add_argument("--x")
    add_parser.add_argument("--y", nargs="*")
    add_parser.add_argument("--secondary-y", nargs="*")
    add_parser.add_argument("--preset", choices=preset_names())
    add_parser.add_argument("--unit")
    add_parser.add_argument("--secondary-unit")
    add_parser.add_argument("--height-ratio", type=float)
    add_parser.add_argument("--missing", choices=sorted(SUPPORTED_MISSING_POLICIES))
    add_parser.add_argument("--y-format", choices=sorted(SUPPORTED_Y_FORMATS))
    add_parser.add_argument("--secondary-y-format", choices=sorted(SUPPORTED_Y_FORMATS))
    add_parser.add_argument("--axis-mode", choices=sorted(SUPPORTED_AXIS_MODES))
    add_parser.add_argument("--tick-policy", choices=sorted(SUPPORTED_TICK_POLICIES))
    add_parser.add_argument("--tick-count", type=int)
    add_parser.add_argument("--stack-mode", choices=sorted(SUPPORTED_STACK_MODES))
    add_parser.add_argument("--secondary-type", choices=["line", "bar", "area"])
    add_parser.add_argument("--alpha", type=float)
    add_parser.add_argument("--line-width", type=float)
    add_parser.add_argument("--secondary-alpha", type=float)
    add_parser.add_argument("--secondary-line-width", type=float)
    add_parser.add_argument("--bar-alpha", type=float)
    add_parser.add_argument("--area-alpha", type=float)
    add_parser.add_argument("--palette")
    add_parser.add_argument("--data", help="本圖專用資料來源；留空則沿用 project.data")
    add_parser.add_argument("--zero-line", action="store_true")
    add_parser.add_argument("--positive-negative-colors", action="store_true")
    add_parser.add_argument("--notes")
    add_parser.add_argument("--heatmap-index", help="熱圖列欄位")
    add_parser.add_argument("--heatmap-columns", help="熱圖欄欄位")
    add_parser.add_argument("--heatmap-value", help="熱圖數值欄位")
    add_parser.add_argument("--cmap", help="熱圖 colormap")
    add_parser.set_defaults(handler=command_add)

    remove_parser = subparsers.add_parser("remove", help="移除指定圖")
    remove_parser.add_argument("--config", default="vap_stack.json")
    remove_parser.add_argument("--id", required=True)
    remove_parser.set_defaults(handler=command_remove)

    move_parser = subparsers.add_parser("move", help="調整圖表上下順序")
    move_parser.add_argument("--config", default="vap_stack.json")
    move_parser.add_argument("--id", required=True)
    move_parser.add_argument("--position", type=int, required=True, help="新位置，從 1 開始")
    move_parser.set_defaults(handler=command_move)

    list_parser = subparsers.add_parser("list", help="列出圖組順序")
    list_parser.add_argument("--config", default="vap_stack.json")
    list_parser.set_defaults(handler=command_list)

    render_parser = subparsers.add_parser("render", help="渲染整個垂直圖組")
    render_parser.add_argument("--config", default="vap_stack.json")
    render_parser.add_argument("--show", action="store_true")
    render_parser.set_defaults(handler=command_render)

    render_one_parser = subparsers.add_parser("render-one", help="只渲染指定單圖")
    render_one_parser.add_argument("--config", default="vap_stack.json")
    render_one_parser.add_argument("--id", required=True)
    render_one_parser.add_argument("--show", action="store_true")
    render_one_parser.set_defaults(handler=command_render_one)

    discover_parser = subparsers.add_parser("discover", help="掃描資料來源、表格、欄位型別與建議")
    discover_parser.add_argument("--source", required=True)
    discover_parser.add_argument("--table", default="")
    discover_parser.add_argument("--sheet", default="")
    discover_parser.add_argument("--sample-rows", type=int, default=5000)
    discover_parser.add_argument("--output", default="")
    discover_parser.set_defaults(handler=command_discover)

    auto_config_parser = subparsers.add_parser("auto-config", help="掃描來源並自動建立第一張圖")
    auto_config_parser.add_argument("--source", required=True)
    auto_config_parser.add_argument("--config", default="vap_auto_stack.json")
    auto_config_parser.add_argument("--table", default="")
    auto_config_parser.add_argument("--sheet", default="")
    auto_config_parser.add_argument("--id", default="auto_chart")
    auto_config_parser.add_argument("--force", action="store_true")
    auto_config_parser.set_defaults(handler=command_auto_config)

    demo_parser = subparsers.add_parser("demo", help="建立並渲染完整示範")
    demo_parser.add_argument("--config", default="examples/demo_stack.json")
    demo_parser.add_argument("--show", action="store_true")
    demo_parser.set_defaults(handler=command_demo)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except Exception as exc:
        print_json(
            {
                "status": "FAIL",
                "error_type": type(exc).__name__,
                "message": str(exc),
            }
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
