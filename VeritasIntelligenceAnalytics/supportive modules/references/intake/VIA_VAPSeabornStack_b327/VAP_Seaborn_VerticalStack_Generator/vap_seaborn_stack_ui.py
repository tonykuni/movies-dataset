#!/usr/bin/env python3
"""VAP Seaborn v2.3.1 desktop workbench: design, discover, curate and export."""

from __future__ import annotations

import os
import math
import queue
import subprocess
import sys
import threading
import tkinter as tk
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from typing import Any, Callable

from vap_atomic_io import file_transaction_lock

from vap_data_adapter import (
    detect_source_kind,
    discover_source,
    list_source_tables,
    normalize_source_spec,
    write_discovery_manifest,
)
from vap_defaults import (
    EDITABLE_CHART_KEYS,
    EDITABLE_PROJECT_KEYS,
    apply_preset,
    chart_defaults,
    default_defaults_path,
    load_defaults,
    preset_names,
    project_defaults,
    save_defaults,
)
from vap_seaborn_stack_generator import (
    DEFAULT_TICK_COUNT,
    STACKED_CHART_TYPES,
    SUPPORTED_AXIS_MODES,
    SUPPORTED_CHART_TYPES,
    SUPPORTED_MISSING_POLICIES,
    SUPPORTED_STACK_MODES,
    SUPPORTED_TICK_POLICIES,
    SUPPORTED_Y_FORMATS,
    append_chart_spec,
    chart_from_suggestion,
    default_chart_spec,
    default_project_config,
    move_chart_spec,
    normalize_project_and_charts,
    read_json,
    relative_source_spec,
    remove_chart_spec,
    render_single_chart,
    render_chart_collection,
    render_stack,
    update_chart_spec,
    write_json,
)

try:
    from vap_chart_library import (
        append_library_chart,
        delete_chart as delete_library_chart,
        load_chart_library,
        search_charts as search_library_charts,
        upsert_chart as upsert_library_chart,
    )
except ImportError:  # pragma: no cover - only used while upgrading an older copy.
    append_library_chart = None  # type: ignore[assignment]
    delete_library_chart = None  # type: ignore[assignment]
    load_chart_library = None  # type: ignore[assignment]
    search_library_charts = None  # type: ignore[assignment]
    upsert_library_chart = None  # type: ignore[assignment]

try:
    from vap_panel_model import normalize_height_ratio as model_normalize_height_ratio
    from vap_panel_model import reorder_items as model_reorder_items
except ImportError:  # pragma: no cover - v2.2 compatibility fallback.
    model_normalize_height_ratio = None
    model_reorder_items = None


# =============================================================================
# 0. UI SSOT 參數
# =============================================================================

WINDOW_TITLE = "VAP Seaborn v2.3.1 · Visual Intelligence Workbench"
WINDOW_GEOMETRY = "1520x900"
WINDOW_MIN_WIDTH = 1120
WINDOW_MIN_HEIGHT = 720
UI_FONT = "Microsoft JhengHei UI"
UI_BACKGROUND = "#F3F6F9"
UI_CARD = "#FFFFFF"
UI_TEXT = "#243247"
UI_MUTED = "#68778B"
UI_ACCENT = "#315EFB"
DEFAULT_CONFIG = "examples/demo_stack.json"
DEFAULT_STANDARD_HEIGHT_PX = 420
DEFAULT_LIBRARY_FILENAME = "vap_chart_library.json"
HEIGHT_RATIO_CHOICES = [f"{value / 4:g}" for value in range(1, 17)]
TASK_POLL_INTERVAL_MS = 120
PALETTE_CHOICES = [
    "deep",
    "muted",
    "pastel",
    "bright",
    "dark",
    "colorblind",
    "Set1",
    "Set2",
    "Set3",
    "tab10",
    "tab20",
    "rocket",
    "mako",
    "flare",
    "crest",
    "viridis",
    "coolwarm",
    "Spectral",
    "RdYlGn",
]
SECONDARY_TYPE_CHOICES = ["line", "bar", "area"]
QUALITY_MODE_CHOICES = ["audit", "off"]
INVALID_DATE_POLICY_CHOICES = ["fail", "drop"]
DUPLICATE_DATE_POLICY_CHOICES = ["fail", "last", "first"]
OUTLIER_POLICY_CHOICES = ["report", "none", "clip_iqr"]
DEFAULT_ENUM_CHOICES = {
    "style": ["whitegrid", "white", "ticks", "darkgrid"],
    "context": ["paper", "notebook", "talk", "poster"],
    "palette": PALETTE_CHOICES,
    "layout_profile": ["compact_desktop", "standard", "accessible"],
    "html_renderer": ["plotly", "svg"],
    "axis_mode": sorted(SUPPORTED_AXIS_MODES),
    "tick_policy": sorted(SUPPORTED_TICK_POLICIES),
    "missing": sorted(SUPPORTED_MISSING_POLICIES),
    "y_format": sorted(SUPPORTED_Y_FORMATS),
    "secondary_y_format": sorted(SUPPORTED_Y_FORMATS),
    "stack_mode": sorted(SUPPORTED_STACK_MODES),
    "quality_mode": QUALITY_MODE_CHOICES,
    "invalid_date_policy": INVALID_DATE_POLICY_CHOICES,
    "duplicate_date_policy": DUPLICATE_DATE_POLICY_CHOICES,
    "outlier_policy": OUTLIER_POLICY_CHOICES,
}
SOURCE_FILE_TYPES = [
    ("Data and databases", "*.csv *.tsv *.parquet *.pq *.xlsx *.xls *.json *.jsonl *.sqlite *.sqlite3 *.db *.duckdb *.ddb"),
    ("All files", "*.*"),
]
CANDLESTICK_CHART_TYPE = "candlestick"
CHART_FORM_SCALAR_MAPPING = {
    "chart_id": "id",
    "chart_type": "type",
    "axis_mode": "axis_mode",
    "title": "title",
    "x": "x",
    "secondary_type": "secondary_type",
    "unit": "unit",
    "secondary_unit": "secondary_unit",
    "height_ratio": "height_ratio",
    "missing": "missing",
    "y_format": "y_format",
    "secondary_y_format": "secondary_y_format",
    "palette": "palette",
    "tick_policy": "tick_policy",
    "tick_count": "tick_count",
    "stack_mode": "stack_mode",
    "preset": "preset",
    "quality_mode": "quality_mode",
    "invalid_date_policy": "invalid_date_policy",
    "duplicate_date_policy": "duplicate_date_policy",
    "outlier_policy": "outlier_policy",
    "outlier_iqr_multiplier": "outlier_iqr_multiplier",
    "max_x_ticks": "max_x_ticks",
    "render_max_points": "render_max_points",
    "open": "open",
    "high": "high",
    "low": "low",
    "close": "close",
    "volume": "volume",
    "bar_alpha": "bar_alpha",
    "area_alpha": "area_alpha",
    "bar_width_ratio": "bar_width_ratio",
    "candle_width_ratio": "candle_width_ratio",
    "up_color": "up_color",
    "down_color": "down_color",
    "alpha": "alpha",
    "line_width": "line_width",
    "secondary_alpha": "secondary_alpha",
    "secondary_line_width": "secondary_line_width",
}
CHART_FORM_LIST_MAPPING = {
    "y": "y",
    "secondary_y": "secondary_y",
    "normalized_y": "normalized_y",
}
CHART_FORM_BOOLEAN_MAPPING = {
    "show_legend": "show_legend",
    "zero_line": "show_zero_line",
    "auto_optimize": "auto_optimize",
}
CHART_FORM_FALLBACKS: dict[str, Any] = {
    "chart_id": "new_panel",
    "chart_type": "line",
    "axis_mode": "auto",
    "title": "New Panel",
    "x": "Date",
    "y": [],
    "secondary_y": [],
    "normalized_y": [],
    "secondary_type": "line",
    "unit": "",
    "secondary_unit": "",
    "height_ratio": 1.0,
    "missing": "none",
    "y_format": "auto",
    "secondary_y_format": "auto",
    "palette": "deep",
    "tick_policy": "vap_locked",
    "tick_count": DEFAULT_TICK_COUNT,
    "stack_mode": "absolute",
    "preset": "multi_series",
    "quality_mode": "audit",
    "invalid_date_policy": "fail",
    "duplicate_date_policy": "fail",
    "outlier_policy": "report",
    "outlier_iqr_multiplier": 3.0,
    "max_x_ticks": 10,
    "render_max_points": "",
    "open": "Open",
    "high": "High",
    "low": "Low",
    "close": "Close",
    "volume": "Volume",
    "bar_alpha": 0.75,
    "area_alpha": 0.5,
    "bar_width_ratio": 0.92,
    "candle_width_ratio": 0.88,
    "up_color": "#D62728",
    "down_color": "#2CA02C",
    "alpha": 0.82,
    "line_width": 1.65,
    "secondary_alpha": 0.88,
    "secondary_line_width": 1.35,
    "show_legend": True,
    "zero_line": False,
    "auto_optimize": True,
}
PROJECT_FIELD_LABELS = {
    "title": "系統標題",
    "subtitle": "副標題",
    "source_label": "來源標籤",
    "width_inch": "畫布寬度",
    "panel_height_inch": "每圖高度",
    "dpi": "輸出 DPI",
    "style": "Seaborn Style",
    "context": "Seaborn Context",
    "palette": "全域 Palette",
    "shared_x": "共用 X 軸",
    "output_directory": "輸出目錄",
    "output_name": "輸出檔名",
    "output_formats": "輸出格式",
    "watermark": "浮水印",
    "max_rows": "最大讀取列數",
    "render_max_points": "每圖最大渲染點數",
    "max_x_ticks": "最大 X 刻度數",
    "render_max_points": "單圖渲染點數上限",
    "layout_profile": "版面最佳化設定",
    "html_renderer": "HTML Renderer",
}
CHART_FIELD_LABELS = {
    "axis_mode": "預設軸模式",
    "tick_policy": "刻度策略",
    "tick_count": "刻度數",
    "missing": "空值策略",
    "y_format": "左軸格式",
    "secondary_y_format": "右軸格式",
    "palette": "圖表 Palette",
    "alpha": "透明度",
    "line_width": "線寬",
    "secondary_alpha": "右軸線條透明度",
    "secondary_line_width": "右軸線寬",
    "height_ratio": "相對高度",
    "stack_mode": "堆疊模式",
    "show_legend": "顯示圖例",
    "show_zero_line": "顯示零軸",
    "quality_mode": "資料品質稽核",
    "invalid_date_policy": "無效日期策略",
    "duplicate_date_policy": "重複日期策略",
    "outlier_policy": "極端值策略",
    "outlier_iqr_multiplier": "IQR 倍數",
    "max_x_ticks": "最大 X 刻度數",
    "auto_optimize": "自動最佳化",
    "open": "Open 欄位",
    "high": "High 欄位",
    "low": "Low 欄位",
    "close": "Close 欄位",
    "volume": "Volume 欄位",
    "normalized_y": "Normalized Y",
    "bar_alpha": "Bar Alpha",
    "area_alpha": "Area Alpha",
    "bar_width_ratio": "Bar 寬度比",
    "candle_width_ratio": "Candle 寬度比",
    "up_color": "上漲色（紅）",
    "down_color": "下跌色（綠）",
}


# =============================================================================
# 1. 通用轉換與桌面工具
# =============================================================================


def utc_now_text() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def open_file_with_default_app(path: Path) -> None:
    if sys.platform.startswith("win"):
        os.startfile(path)  # type: ignore[attr-defined]
    elif sys.platform == "darwin":
        subprocess.run(["open", str(path)], check=False)
    else:
        subprocess.run(["xdg-open", str(path)], check=False)


def parse_columns(text: str) -> list[str]:
    normalized = text.replace("，", ",")
    return [part.strip() for part in normalized.split(",") if part.strip()]


def parse_bool(text: str) -> bool:
    return text.strip().lower() in {"1", "true", "yes", "y", "on", "是"}


def display_value(value: Any) -> str:
    if isinstance(value, list):
        return ",".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def standard_height_pixels(height_ratio: Any, standard_height_px: int = DEFAULT_STANDARD_HEIGHT_PX) -> int:
    """Return the visible panel height represented by a standard-height multiple."""
    ratio = float(height_ratio)
    if not math.isfinite(ratio) or ratio <= 0:
        raise ValueError("標準高度倍數必須大於 0。")
    if standard_height_px <= 0:
        raise ValueError("標準高度必須大於 0。")
    return max(1, round(ratio * standard_height_px))


def normalize_ui_height_ratio(value: Any) -> float:
    """Snap free-form input to the supported 0.25× standard-height grid."""
    if model_normalize_height_ratio is not None:
        return float(model_normalize_height_ratio(value, clamp=False))
    ratio = float(value)
    if not 0.25 <= ratio <= 4.0:
        raise ValueError("height_ratio 必須介於 0.25 與 4.0。")
    return round(ratio * 4) / 4


def chart_library_path_for_config(config_path: Path | str) -> Path:
    """Keep a portable VAP chart library beside the active stack configuration."""
    return Path(config_path).expanduser().resolve().parent / DEFAULT_LIBRARY_FILENAME


def axis_tree_rows(values: dict[str, Any]) -> list[dict[str, Any]]:
    """Create a testable left/right-axis tree used by the nested specification UI."""
    chart_type = str(values.get("chart_type") or values.get("type") or "line")
    secondary = parse_columns(display_value(values.get("secondary_y", "")))
    return [
        {
            "id": "general",
            "parent": "",
            "label": "General",
            "summary": f"{chart_type} · {values.get('height_ratio', 1.0)}×{DEFAULT_STANDARD_HEIGHT_PX}px",
        },
        {
            "id": "left_axis",
            "parent": "",
            "label": "左軸",
            "summary": f"{values.get('y_format', 'auto')} · line {values.get('line_width', 1.65)} · α {values.get('alpha', 0.82)}",
        },
        {
            "id": "right_axis",
            "parent": "",
            "label": "右軸",
            "summary": "未啟用" if not secondary else f"{values.get('secondary_type', 'line')} · {', '.join(secondary)}",
        },
        {
            "id": "advanced",
            "parent": "",
            "label": "進階",
            "summary": f"{values.get('missing', 'none')} · {values.get('tick_policy', 'vap_locked')}",
        },
    ]


def duplicate_chart_for_stack(chart: dict[str, Any], existing_ids: list[str] | tuple[str, ...] | set[str]) -> dict[str, Any]:
    """Clone one chart and choose a stable, collision-free ID."""
    duplicate = deepcopy(chart)
    existing = {str(value) for value in existing_ids}
    base = f"{str(chart.get('id') or 'chart')}_copy"
    candidate = base
    suffix = 2
    while candidate in existing:
        candidate = f"{base}_{suffix}"
        suffix += 1
    duplicate["id"] = candidate
    duplicate["title"] = f"{str(chart.get('title') or chart.get('id') or 'Chart')} 副本"
    return duplicate


def reorder_chart_items(
    items: list[dict[str, Any]] | list[str],
    dragged_id: str,
    target_id: str,
    position: str = "before",
) -> list[Any]:
    """Reorder stack items through the v2.3 model, with a strict local fallback."""
    if model_reorder_items is not None:
        return list(model_reorder_items(items, dragged_id, target_id, position=position))
    if position not in {"before", "after"}:
        raise ValueError("position must be 'before' or 'after'")
    identifiers = [str(item.get("id")) if isinstance(item, dict) else str(item) for item in items]
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("duplicate item ids")
    if dragged_id not in identifiers or target_id not in identifiers:
        raise ValueError("unknown dragged or target item")
    result = list(items)
    if dragged_id == target_id:
        return result
    dragged_index = identifiers.index(dragged_id)
    dragged = result.pop(dragged_index)
    remaining_ids = [str(item.get("id")) if isinstance(item, dict) else str(item) for item in result]
    target_index = remaining_ids.index(target_id)
    if position == "after":
        target_index += 1
    result.insert(target_index, dragged)
    return result


def chart_type_choices() -> list[str]:
    """Return the renderer-owned chart type list without duplicating its SSOT."""
    return sorted(str(value) for value in SUPPORTED_CHART_TYPES)


def chart_form_field_mapping() -> dict[str, str]:
    """Expose a stable, testable mapping between form variables and chart JSON."""
    return {
        **CHART_FORM_SCALAR_MAPPING,
        **CHART_FORM_LIST_MAPPING,
        **CHART_FORM_BOOLEAN_MAPPING,
    }


FORM_OWNED_CHART_KEYS = frozenset(chart_form_field_mapping().values()) | {
    "heatmap_index",
    "heatmap_columns",
    "heatmap_value",
    "price_basis",
}


def chart_form_owned_patch(chart: dict[str, Any]) -> dict[str, Any]:
    """Return only fields represented by the editor, preserving opaque config."""

    return {
        key: deepcopy(value)
        for key, value in chart.items()
        if key in FORM_OWNED_CHART_KEYS
    }


def merge_chart_form_update(
    existing: dict[str, Any],
    form_chart: dict[str, Any],
    *,
    replace_hidden: bool = False,
) -> dict[str, Any]:
    """Preserve non-UI fields unless type/preset was deliberately replaced."""

    if replace_hidden:
        return deepcopy(form_chart)
    merged = deepcopy(existing)
    merged.update(chart_form_owned_patch(form_chart))
    return merged


def chart_form_values_from_spec(
    chart: dict[str, Any] | None = None,
    defaults: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a complete form snapshot so sparse chart loads cannot leak stale values."""
    chart_value = dict(chart or {})
    default_value = dict(defaults if defaults is not None else chart_defaults(load_defaults()))
    result: dict[str, Any] = {}
    for variable_name, chart_key in CHART_FORM_SCALAR_MAPPING.items():
        fallback = CHART_FORM_FALLBACKS[variable_name]
        value = chart_value.get(chart_key, default_value.get(chart_key, fallback))
        if value is None:
            value = fallback
        result[variable_name] = display_value(value)
    for variable_name, chart_key in CHART_FORM_LIST_MAPPING.items():
        fallback = CHART_FORM_FALLBACKS[variable_name]
        value = chart_value.get(chart_key, default_value.get(chart_key, fallback))
        result[variable_name] = display_value(value if value is not None else fallback)
    for variable_name, chart_key in CHART_FORM_BOOLEAN_MAPPING.items():
        fallback = bool(CHART_FORM_FALLBACKS[variable_name])
        result[variable_name] = bool(chart_value.get(chart_key, default_value.get(chart_key, fallback)))
    if chart_value.get("type") == CANDLESTICK_CHART_TYPE and "preset" not in chart_value:
        result["preset"] = "candlestick_volume"
    return result


def apply_chart_form_snapshot(state: dict[str, Any], values: dict[str, Any]) -> None:
    """Replace every chart-form field represented by a snapshot."""
    variables = state["variables"]
    for variable_name in chart_form_field_mapping():
        if variable_name in values and variable_name in variables:
            variables[variable_name].set(values[variable_name])


def chart_spec_from_form_values(values: dict[str, Any]) -> dict[str, Any]:
    """Convert a form snapshot to a complete chart spec without requiring a Tk root."""
    chart_type = str(values.get("chart_type", "line")).strip() or "line"
    chart_id = str(values.get("chart_id", "new_panel")).strip() or "new_panel"
    title = str(values.get("title", "")).strip() or chart_id
    x_column = str(values.get("x", "")).strip()
    y_columns = parse_columns(display_value(values.get("y", "")))
    is_candlestick = chart_type == CANDLESTICK_CHART_TYPE
    if chart_type not in {"heatmap", CANDLESTICK_CHART_TYPE} and not y_columns:
        raise ValueError("請至少輸入一個左軸 Y 欄位。")

    ohlcv = {
        key: str(values.get(key, "")).strip()
        for key in ("open", "high", "low", "close", "volume")
    }
    if is_candlestick:
        missing_ohlcv = [key.title() for key, value in ohlcv.items() if not value]
        if missing_ohlcv:
            raise ValueError(f"Candlestick 缺少欄位：{', '.join(missing_ohlcv)}。")
        y_columns = []

    bar_alpha = float(values.get("bar_alpha", 0.75))
    area_alpha = float(values.get("area_alpha", 0.5))
    alpha = float(values.get("alpha", 0.82))
    line_width = float(values.get("line_width", 1.65))
    secondary_alpha = float(values.get("secondary_alpha", 0.88))
    secondary_line_width = float(values.get("secondary_line_width", 1.35))
    height_ratio = normalize_ui_height_ratio(values.get("height_ratio", 1.0))
    bar_width_ratio = float(values.get("bar_width_ratio", 0.92))
    candle_width_ratio = float(values.get("candle_width_ratio", 0.88))
    outlier_iqr_multiplier = float(values.get("outlier_iqr_multiplier", 3.0))
    render_max_points_text = str(values.get("render_max_points", "")).strip()
    render_max_points = int(render_max_points_text) if render_max_points_text else None
    if not math.isfinite(bar_alpha) or not 0 <= bar_alpha <= 1:
        raise ValueError("Bar Alpha 必須介於 0 與 1。")
    if not math.isfinite(area_alpha) or not 0 <= area_alpha <= 1:
        raise ValueError("Area Alpha 必須介於 0 與 1。")
    if not math.isfinite(alpha) or not 0 <= alpha <= 1:
        raise ValueError("線條透明度必須介於 0 與 1。")
    if not math.isfinite(line_width) or line_width <= 0:
        raise ValueError("線寬必須大於 0。")
    if not math.isfinite(secondary_alpha) or not 0 <= secondary_alpha <= 1:
        raise ValueError("右軸線條透明度必須介於 0 與 1。")
    if not math.isfinite(secondary_line_width) or secondary_line_width <= 0:
        raise ValueError("右軸線寬必須大於 0。")
    standard_height_pixels(height_ratio)
    if not math.isfinite(bar_width_ratio) or not 0 < bar_width_ratio < 1:
        raise ValueError("Bar 寬度比必須大於 0 且小於 1，避免長條交疊。")
    if not math.isfinite(candle_width_ratio) or not 0 < candle_width_ratio < 1:
        raise ValueError("Candle 寬度比必須大於 0 且小於 1，避免 K 棒交疊。")
    if not math.isfinite(outlier_iqr_multiplier) or outlier_iqr_multiplier <= 0:
        raise ValueError("IQR 倍數必須是大於 0 的有限數值。")
    if render_max_points is not None and not 2 <= render_max_points <= 500000:
        raise ValueError("單圖渲染點數上限必須介於 2 與 500000，或留空沿用全域值。")

    chart = default_chart_spec(
        chart_id=chart_id,
        chart_type=chart_type,
        title=title,
        x=x_column,
        y=y_columns,
    )
    preset = str(values.get("preset", "")).strip()
    if preset:
        chart = apply_preset(chart, preset)

    axis_mode = str(values.get("axis_mode", "single" if is_candlestick else "auto"))
    supports_secondary = chart_type not in STACKED_CHART_TYPES | {"heatmap", CANDLESTICK_CHART_TYPE}
    secondary_y = parse_columns(display_value(values.get("secondary_y", "")))
    if not supports_secondary or axis_mode == "single":
        secondary_y = []
    chart.update(
        {
            "id": chart_id,
            "type": chart_type,
            "title": title,
            "x": x_column,
            "y": y_columns,
            "secondary_y": [] if is_candlestick else secondary_y,
            "secondary_type": str(values.get("secondary_type", "line")),
            # Preserve legacy candlestick snapshots during a headless
            # round-trip; the live UI locks this variable to ``single`` and
            # both renderers always expand K-line/volume into two single axes.
            "axis_mode": axis_mode,
            "unit": str(values.get("unit", "")).strip(),
            "secondary_unit": (
                str(values.get("secondary_unit", "")).strip()
                or str(chart.get("secondary_unit", "Volume")).strip()
                or "Volume"
            ) if is_candlestick else str(values.get("secondary_unit", "")).strip(),
            "height_ratio": height_ratio,
            "missing": "ffill" if is_candlestick else str(values.get("missing", "none")),
            "y_format": str(values.get("y_format", "auto")),
            "secondary_y_format": str(values.get("secondary_y_format", "auto")),
            "palette": str(values.get("palette", "")).strip() or None,
            "tick_policy": str(values.get("tick_policy", "vap_locked")),
            "tick_count": int(values.get("tick_count", DEFAULT_TICK_COUNT)),
            "stack_mode": str(values.get("stack_mode", "absolute")),
            "show_legend": bool(values.get("show_legend", True)),
            "show_zero_line": bool(values.get("zero_line", False)),
            "quality_mode": str(values.get("quality_mode", "audit")),
            "invalid_date_policy": str(values.get("invalid_date_policy", "fail")),
            "duplicate_date_policy": str(values.get("duplicate_date_policy", "fail")),
            "outlier_policy": str(values.get("outlier_policy", "report")),
            "outlier_iqr_multiplier": outlier_iqr_multiplier,
            "max_x_ticks": int(values.get("max_x_ticks", 10)),
            "render_max_points": render_max_points,
            "auto_optimize": bool(values.get("auto_optimize", True)),
            "normalized_y": parse_columns(display_value(values.get("normalized_y", ""))),
            "bar_alpha": bar_alpha,
            "area_alpha": area_alpha,
            "alpha": alpha,
            "line_width": line_width,
            "secondary_alpha": secondary_alpha,
            "secondary_line_width": secondary_line_width,
            "bar_width_ratio": bar_width_ratio,
            "candle_width_ratio": candle_width_ratio,
            "up_color": str(values.get("up_color", "#D62728")).strip(),
            "down_color": str(values.get("down_color", "#2CA02C")).strip(),
            "price_basis": "adjusted" if is_candlestick else str(chart.get("price_basis", "adjusted")),
            **ohlcv,
        }
    )
    if chart_type == "heatmap":
        if len(y_columns) < 2:
            raise ValueError("熱圖請在左軸 Y 輸入『欄維度,數值欄位』。")
        chart.update(
            {
                "heatmap_index": chart["x"],
                "heatmap_columns": y_columns[0],
                "heatmap_value": y_columns[1],
            }
        )
    return chart


def parse_like(text: Any, reference: Any) -> Any:
    if isinstance(reference, bool):
        return bool(text) if isinstance(text, bool) else parse_bool(str(text))
    normalized_text = str(text)
    if isinstance(reference, int) and not isinstance(reference, bool):
        return int(normalized_text)
    if isinstance(reference, float):
        return float(normalized_text)
    if isinstance(reference, list):
        return parse_columns(normalized_text)
    return normalized_text.strip() or None if reference is None else normalized_text.strip()


def selected_config_path(state: dict[str, Any]) -> Path:
    return Path(state["variables"]["config"].get()).expanduser().resolve()


def clear_source_context(state: dict[str, Any]) -> None:
    """Clear source-derived state before activating another project."""

    variables = state["variables"]
    variables["source_path"].set("")
    variables["source_kind"].set("尚未選擇")
    variables["source_table"].set("")
    variables["suggestion"].set("尚未分析資料來源。")
    state["manifest"] = None
    configure_source_table_choices(state, [])
    tree = state.get("column_tree")
    if tree is not None:
        for item in tree.get_children():
            tree.delete(item)


def activate_config(state: dict[str, Any], config_path: Path | str) -> None:
    """Switch config, gallery, source context and form as one UI transaction."""

    resolved = Path(config_path).expanduser().resolve()
    state["variables"]["config"].set(str(resolved))
    state["variables"]["library_path"].set(str(chart_library_path_for_config(resolved)))
    state["variables"]["library_query"].set("")
    state["variables"]["library_tags"].set("")
    state["last_outputs"] = []
    state["last_report"] = {}
    state.pop("loaded_chart_id", None)
    state.pop("loaded_gallery_item_id", None)
    clear_source_context(state)
    reset_chart_form(state)
    refresh_chart_tree(state)
    refresh_gallery_tree(state)
    load_project_source_to_ui(state)


def selected_tree_item(state: dict[str, Any], quiet: bool = False) -> tuple[str, int] | None:
    tree: ttk.Treeview = state["chart_tree"]
    selection = tree.selection()
    if not selection:
        if not quiet:
            messagebox.showinfo(WINDOW_TITLE, "請先選擇一張圖。")
        return None
    chart_id = str(selection[0])
    values = tree.item(chart_id, "values")
    return chart_id, int(values[0])


def set_status(state: dict[str, Any], text: str) -> None:
    state["variables"]["status"].set(text)


# =============================================================================
# 2. 樣式與小型元件
# =============================================================================


def build_style(root: tk.Tk) -> ttk.Style:
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")
    root.configure(background=UI_BACKGROUND)
    style.configure("TFrame", background=UI_BACKGROUND)
    style.configure("Card.TFrame", background=UI_CARD)
    style.configure("TLabel", background=UI_BACKGROUND, foreground=UI_TEXT, font=(UI_FONT, 9))
    style.configure("Card.TLabel", background=UI_CARD, foreground=UI_TEXT, font=(UI_FONT, 9))
    style.configure("Title.TLabel", background=UI_BACKGROUND, foreground=UI_TEXT, font=(UI_FONT, 16, "bold"))
    style.configure("Subtitle.TLabel", background=UI_BACKGROUND, foreground=UI_MUTED, font=(UI_FONT, 9))
    style.configure("Section.TLabel", background=UI_CARD, foreground=UI_TEXT, font=(UI_FONT, 10, "bold"))
    style.configure("Accent.TButton", foreground="#FFFFFF", background=UI_ACCENT, font=(UI_FONT, 9, "bold"), padding=(12, 7))
    style.map("Accent.TButton", background=[("active", "#2449C9"), ("disabled", "#91A4E8")])
    style.configure("TButton", font=(UI_FONT, 9), padding=(9, 6))
    style.configure("TEntry", font=(UI_FONT, 9), fieldbackground="#FFFFFF")
    style.configure("TCombobox", font=(UI_FONT, 9), fieldbackground="#FFFFFF")
    style.configure("Treeview", font=(UI_FONT, 9), rowheight=26, background="#FFFFFF", fieldbackground="#FFFFFF")
    style.configure("Treeview.Heading", font=(UI_FONT, 9, "bold"))
    style.configure("TNotebook", background=UI_BACKGROUND, borderwidth=0)
    style.configure("TNotebook.Tab", font=(UI_FONT, 9, "bold"), padding=(14, 8))
    return style


def labeled_entry(
    parent: ttk.Frame,
    label: str,
    variable: tk.StringVar,
    row: int,
    column: int,
    columnspan: int = 1,
) -> ttk.Entry:
    ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=column, sticky="w", padx=7, pady=(5, 2))
    entry = ttk.Entry(parent, textvariable=variable)
    entry.grid(row=row + 1, column=column, columnspan=columnspan, sticky="ew", padx=7, pady=(0, 5))
    return entry


def labeled_combo(
    parent: ttk.Frame,
    label: str,
    variable: tk.StringVar,
    values: list[str],
    row: int,
    column: int,
) -> ttk.Combobox:
    ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=column, sticky="w", padx=7, pady=(5, 2))
    combo = ttk.Combobox(parent, textvariable=variable, values=values, state="readonly")
    combo.grid(row=row + 1, column=column, sticky="ew", padx=7, pady=(0, 5))
    return combo


# =============================================================================
# 3. 應用程式主結構
# =============================================================================


def make_variables(root: tk.Tk) -> dict[str, tk.Variable]:
    defaults = load_defaults()
    chart = chart_defaults(defaults)
    form = chart_form_values_from_spec(defaults=chart)
    default_config_path = (Path(__file__).parent / DEFAULT_CONFIG).resolve()
    return {
        "config": tk.StringVar(value=str(default_config_path)),
        "status": tk.StringVar(value="就緒"),
        "preset": tk.StringVar(value=str(form["preset"])),
        "chart_id": tk.StringVar(value=str(form["chart_id"])),
        "chart_type": tk.StringVar(value=str(form["chart_type"])),
        "axis_mode": tk.StringVar(value=str(form["axis_mode"])),
        "title": tk.StringVar(value=str(form["title"])),
        "x": tk.StringVar(value=str(form["x"])),
        "y": tk.StringVar(value=str(form["y"])),
        "secondary_y": tk.StringVar(value=str(form["secondary_y"])),
        "normalized_y": tk.StringVar(value=str(form["normalized_y"])),
        "secondary_type": tk.StringVar(value=str(form["secondary_type"])),
        "unit": tk.StringVar(value=str(form["unit"])),
        "secondary_unit": tk.StringVar(value=str(form["secondary_unit"])),
        "height_ratio": tk.StringVar(value=str(form["height_ratio"])),
        "missing": tk.StringVar(value=str(form["missing"])),
        "y_format": tk.StringVar(value=str(form["y_format"])),
        "secondary_y_format": tk.StringVar(value=str(form["secondary_y_format"])),
        "palette": tk.StringVar(value=str(form["palette"])),
        "tick_policy": tk.StringVar(value=str(form["tick_policy"])),
        "tick_count": tk.StringVar(value=str(form["tick_count"])),
        "stack_mode": tk.StringVar(value=str(form["stack_mode"])),
        "show_legend": tk.BooleanVar(value=bool(form["show_legend"])),
        "zero_line": tk.BooleanVar(value=bool(form["zero_line"])),
        "quality_mode": tk.StringVar(value=str(form["quality_mode"])),
        "invalid_date_policy": tk.StringVar(value=str(form["invalid_date_policy"])),
        "duplicate_date_policy": tk.StringVar(value=str(form["duplicate_date_policy"])),
        "outlier_policy": tk.StringVar(value=str(form["outlier_policy"])),
        "outlier_iqr_multiplier": tk.StringVar(value=str(form["outlier_iqr_multiplier"])),
        "max_x_ticks": tk.StringVar(value=str(form["max_x_ticks"])),
        "render_max_points": tk.StringVar(value=str(form["render_max_points"])),
        "auto_optimize": tk.BooleanVar(value=bool(form["auto_optimize"])),
        "open": tk.StringVar(value=str(form["open"])),
        "high": tk.StringVar(value=str(form["high"])),
        "low": tk.StringVar(value=str(form["low"])),
        "close": tk.StringVar(value=str(form["close"])),
        "volume": tk.StringVar(value=str(form["volume"])),
        "bar_alpha": tk.StringVar(value=str(form["bar_alpha"])),
        "area_alpha": tk.StringVar(value=str(form["area_alpha"])),
        "alpha": tk.StringVar(value=str(form["alpha"])),
        "line_width": tk.StringVar(value=str(form["line_width"])),
        "secondary_alpha": tk.StringVar(value=str(form["secondary_alpha"])),
        "secondary_line_width": tk.StringVar(value=str(form["secondary_line_width"])),
        "bar_width_ratio": tk.StringVar(value=str(form["bar_width_ratio"])),
        "candle_width_ratio": tk.StringVar(value=str(form["candle_width_ratio"])),
        "up_color": tk.StringVar(value=str(form["up_color"])),
        "down_color": tk.StringVar(value=str(form["down_color"])),
        "chart_mode_hint": tk.StringVar(value=""),
        "advanced_visible": tk.BooleanVar(value=False),
        "source_panel_visible": tk.BooleanVar(value=True),
        "spec_panel_visible": tk.BooleanVar(value=True),
        "general_section_visible": tk.BooleanVar(value=True),
        "left_axis_section_visible": tk.BooleanVar(value=True),
        "right_axis_section_visible": tk.BooleanVar(value=True),
        "source_path": tk.StringVar(),
        "source_kind": tk.StringVar(value="尚未選擇"),
        "source_table": tk.StringVar(),
        "sample_rows": tk.StringVar(value="5000"),
        "suggestion": tk.StringVar(value="尚未分析資料來源。"),
        "library_path": tk.StringVar(
            value=str(chart_library_path_for_config(default_config_path))
        ),
        "library_query": tk.StringVar(),
        "library_tags": tk.StringVar(),
    }


def create_application(root: tk.Tk) -> dict[str, Any]:
    build_style(root)
    root.title(WINDOW_TITLE)
    screen_width = max(800, int(root.winfo_screenwidth()))
    screen_height = max(600, int(root.winfo_screenheight()))
    target_width = min(1520, max(980, screen_width - 80))
    target_height = min(900, max(640, screen_height - 80))
    root.geometry(f"{target_width}x{target_height}")
    root.minsize(min(WINDOW_MIN_WIDTH, target_width), min(WINDOW_MIN_HEIGHT, target_height))
    state: dict[str, Any] = {
        "variables": make_variables(root),
        "task_queue": queue.Queue(),
        "busy": False,
        "last_outputs": [],
        "last_report": {},
        "manifest": None,
        "default_variables": {"project": {}, "chart": {}},
        "root": root,
    }

    outer = ttk.Frame(root, padding=16)
    outer.pack(fill="both", expand=True)
    ttk.Label(outer, text="VAP Seaborn v2.3.1 · Visual Intelligence Workbench", style="Title.TLabel").pack(anchor="w")
    ttk.Label(
        outer,
        text="單圖、單軸、雙軸、堆疊、資料庫規格辨識、非破壞品質稽核與可編輯預設值集中在同一介面。",
        style="Subtitle.TLabel",
    ).pack(anchor="w", pady=(2, 10))
    build_config_bar(root, outer, state)

    notebook = ttk.Notebook(outer)
    notebook.pack(fill="both", expand=True, pady=(10, 0))
    design_tab = ttk.Frame(notebook, padding=8)
    data_tab = ttk.Frame(notebook, padding=8)
    defaults_tab = ttk.Frame(notebook, padding=8)
    notebook.add(design_tab, text="圖表設計")
    notebook.add(data_tab, text="資料來源")
    notebook.add(defaults_tab, text="全域預設值")
    state["notebook"] = notebook
    state["data_tab"] = data_tab
    build_design_tab(design_tab, state)
    build_data_tab(root, data_tab, state)
    build_defaults_tab(defaults_tab, state)

    action_bar = ttk.Frame(outer)
    action_bar.pack(fill="x", pady=(10, 0))
    ttk.Label(action_bar, textvariable=state["variables"]["status"], style="Subtitle.TLabel").pack(side="left")
    ttk.Button(action_bar, text="開啟輸出圖", command=lambda: open_last_output(state)).pack(side="right")
    ttk.Button(action_bar, text="開啟稽核報告", command=lambda: open_last_audit(state)).pack(side="right", padx=(0, 8))
    full_button = ttk.Button(action_bar, text="生成完整圖組", style="Accent.TButton", command=lambda: start_render_stack(state))
    full_button.pack(side="right", padx=(0, 8))
    one_button = ttk.Button(action_bar, text="生成選取單圖", command=lambda: start_render_single(state))
    one_button.pack(side="right", padx=(0, 8))
    preview_button = ttk.Button(action_bar, text="預覽目前表單", command=lambda: start_render_form_preview(state))
    preview_button.pack(side="right", padx=(0, 8))
    state["full_render_button"] = full_button
    state["single_render_button"] = one_button
    state["preview_render_button"] = preview_button

    refresh_chart_tree(state)
    refresh_gallery_tree(state)
    load_project_source_to_ui(state)
    poll_task_queue(root, state)
    return state


def build_config_bar(root: tk.Tk, parent: ttk.Frame, state: dict[str, Any]) -> None:
    card = ttk.Frame(parent, style="Card.TFrame", padding=10)
    card.pack(fill="x")
    card.columnconfigure(1, weight=1)
    ttk.Label(card, text="圖組設定檔", style="Card.TLabel").grid(row=0, column=0, padx=(0, 8))
    ttk.Entry(card, textvariable=state["variables"]["config"]).grid(row=0, column=1, sticky="ew")
    ttk.Button(card, text="開啟", command=lambda: select_config(root, state)).grid(row=0, column=2, padx=(8, 0))
    ttk.Button(card, text="新建", command=lambda: create_new_config(root, state)).grid(row=0, column=3, padx=(8, 0))
    ttk.Button(card, text="重新整理", command=lambda: refresh_chart_tree(state)).grid(row=0, column=4, padx=(8, 0))


# =============================================================================
# 4. 圖表設計 Tab
# =============================================================================


def set_collapsible_body(
    body: ttk.Frame,
    button: ttk.Button,
    variable: tk.BooleanVar,
    title: str,
    visible: bool,
    *,
    expand: bool = False,
) -> None:
    variable.set(bool(visible))
    button.configure(text=f"{'\u25be' if visible else '\u25b8'} {title}")
    if visible:
        body.pack(fill="both" if expand else "x", expand=expand)
    else:
        body.pack_forget()


def build_collapsible_body(
    parent: ttk.Frame,
    title: str,
    variable: tk.BooleanVar,
    *,
    expand: bool = False,
    padding: int | tuple[int, ...] = 8,
) -> tuple[ttk.Frame, ttk.Button]:
    shell = ttk.Frame(parent, style="Card.TFrame")
    shell.pack(fill="both" if expand else "x", expand=expand)
    button = ttk.Button(shell, text="", style="TButton")
    button.pack(fill="x")
    body = ttk.Frame(shell, style="Card.TFrame", padding=padding)

    def toggle() -> None:
        set_collapsible_body(body, button, variable, title, not bool(variable.get()), expand=expand)

    button.configure(command=toggle)
    set_collapsible_body(body, button, variable, title, bool(variable.get()), expand=expand)
    return body, button


def build_design_tab(parent: ttk.Frame, state: dict[str, Any]) -> None:
    content = ttk.Panedwindow(parent, orient="horizontal")
    content.pack(fill="both", expand=True)
    source_card = ttk.Frame(content, style="Card.TFrame", padding=8, width=255)
    stack_card = ttk.Frame(content, style="Card.TFrame", padding=8, width=460)
    spec_card = ttk.Frame(content, style="Card.TFrame", padding=8, width=660)
    content.add(source_card, weight=2)
    content.add(stack_card, weight=4)
    content.add(spec_card, weight=6)
    state["design_panes"] = content
    state["source_design_card"] = source_card
    state["spec_design_card"] = spec_card
    build_compact_source_panel(source_card, state)
    build_stack_editor_panel(stack_card, state)
    build_chart_spec_panel(spec_card, state)
    update_axis_controls(state)


def build_compact_source_panel(parent: ttk.Frame, state: dict[str, Any]) -> None:
    variables = state["variables"]
    body, button = build_collapsible_body(
        parent,
        "資料來源",
        variables["source_panel_visible"],
        expand=True,
        padding=6,
    )
    state["source_panel_body"] = body
    state["source_panel_button"] = button
    button.configure(command=lambda: toggle_main_design_pane(state, "source"))
    ttk.Label(body, text="目前來源", style="Card.TLabel").pack(anchor="w")
    ttk.Entry(body, textvariable=variables["source_path"]).pack(fill="x", pady=(3, 7))
    ttk.Label(body, textvariable=variables["source_kind"], style="Subtitle.TLabel").pack(anchor="w", pady=(0, 7))
    source_buttons = ttk.Frame(body, style="Card.TFrame")
    source_buttons.pack(fill="x")
    ttk.Button(source_buttons, text="瀏覽檔案", command=lambda: browse_source(state["root"], state)).pack(side="left", fill="x", expand=True)
    compact_scan = ttk.Button(source_buttons, text="擷取表格", command=lambda: start_source_scan(state))
    compact_scan.pack(side="left", fill="x", expand=True, padx=(5, 0))
    state["compact_scan_button"] = compact_scan
    ttk.Label(body, text="Table / Sheet", style="Card.TLabel").pack(anchor="w", pady=(9, 2))
    table_combo = ttk.Combobox(body, textvariable=variables["source_table"], values=[], state="readonly")
    table_combo.pack(fill="x")
    state.setdefault("source_table_combos", []).append(table_combo)
    compact_analyze = ttk.Button(body, text="分析欄位與自動建議", style="Accent.TButton", command=lambda: start_source_discovery(state))
    compact_analyze.pack(fill="x", pady=(9, 5))
    state["compact_analyze_button"] = compact_analyze
    ttk.Button(body, text="設為目前圖組資料來源", command=lambda: save_manifest_source_to_project(state)).pack(fill="x", pady=(0, 5))
    ttk.Button(body, text="開啟詳細掃描面板", command=lambda: open_data_source_tab(state)).pack(fill="x")
    ttk.Separator(body).pack(fill="x", pady=12)
    ttk.Label(body, text="快速流程", style="Section.TLabel").pack(anchor="w")
    ttk.Label(
        body,
        text="1. 選擇來源\n2. 擷取與分析\n3. 套用建議\n4. 儲存單圖到圖庫",
        style="Card.TLabel",
        foreground=UI_MUTED,
        justify="left",
    ).pack(anchor="w")


def build_stack_editor_panel(parent: ttk.Frame, state: dict[str, Any]) -> None:
    ttk.Label(parent, text="堆疊圖編輯器", style="Section.TLabel").pack(anchor="w")
    ttk.Label(parent, text="按住圖表後上下拖曳可調整順序", style="Subtitle.TLabel").pack(anchor="w", pady=(2, 7))
    tree = ttk.Treeview(parent, columns=("position", "type", "height", "title"), show="headings", selectmode="browse", height=11)
    headings = {"position": "#", "type": "圖型", "height": "高度", "title": "標題"}
    widths = {"position": 34, "type": 95, "height": 64, "title": 230}
    for key, heading in headings.items():
        tree.heading(key, text=heading)
        tree.column(key, width=widths[key], anchor="center" if key != "title" else "w", stretch=key == "title")
    tree.pack(fill="both", expand=True)
    tree.bind("<<TreeviewSelect>>", lambda _event: load_selected_chart_to_form(state))
    tree.bind("<ButtonPress-1>", lambda event: begin_chart_drag(state, event))
    tree.bind("<B1-Motion>", lambda event: preview_chart_drag(state, event))
    tree.bind("<ButtonRelease-1>", lambda event: finish_chart_drag(state, event))
    state["chart_tree"] = tree
    order_bar = ttk.Frame(parent, style="Card.TFrame")
    order_bar.pack(fill="x", pady=(7, 10))
    ttk.Button(order_bar, text="＋", width=3, command=lambda: reset_chart_form(state)).pack(side="left")
    ttk.Button(order_bar, text="複製", command=lambda: duplicate_selected_chart(state)).pack(side="left", padx=(5, 0))
    ttk.Button(order_bar, text="↑", width=3, command=lambda: move_selected_chart(state, -1)).pack(side="left", padx=(5, 0))
    ttk.Button(order_bar, text="↓", width=3, command=lambda: move_selected_chart(state, 1)).pack(side="left", padx=(5, 0))
    ttk.Button(order_bar, text="刪除", command=lambda: remove_selected_chart(state)).pack(side="right")
    build_gallery_panel(parent, state)


def build_gallery_panel(parent: ttk.Frame, state: dict[str, Any]) -> None:
    variables = state["variables"]
    gallery = ttk.Frame(parent, style="Card.TFrame")
    gallery.pack(fill="both", expand=True)
    ttk.Separator(gallery).pack(fill="x", pady=(0, 8))
    ttk.Label(gallery, text="VAP 單圖圖庫", style="Section.TLabel").pack(anchor="w")
    search_bar = ttk.Frame(gallery, style="Card.TFrame")
    search_bar.pack(fill="x", pady=(5, 5))
    query_entry = ttk.Entry(search_bar, textvariable=variables["library_query"])
    query_entry.pack(side="left", fill="x", expand=True)
    query_entry.bind("<Return>", lambda _event: refresh_gallery_tree(state))
    ttk.Button(search_bar, text="搜尋", command=lambda: refresh_gallery_tree(state)).pack(side="left", padx=(5, 0))
    gallery_tree = ttk.Treeview(gallery, columns=("name", "type", "tags"), show="headings", selectmode="browse", height=5)
    for key, heading, width in [("name", "名稱", 185), ("type", "圖型", 82), ("tags", "標籤", 110)]:
        gallery_tree.heading(key, text=heading)
        gallery_tree.column(key, width=width, stretch=key == "name")
    gallery_tree.pack(fill="both", expand=True)
    gallery_tree.bind("<Double-1>", lambda _event: load_selected_gallery_to_form(state))
    state["gallery_tree"] = gallery_tree
    ttk.Label(gallery, text="雙擊圖庫項目可載入右側規格編輯", style="Subtitle.TLabel").pack(anchor="w", pady=(3, 0))
    ttk.Label(gallery, text="標籤（逗號分隔）", style="Card.TLabel").pack(anchor="w", pady=(5, 2))
    ttk.Entry(gallery, textvariable=variables["library_tags"]).pack(fill="x")
    library_bar = ttk.Frame(gallery, style="Card.TFrame")
    library_bar.pack(fill="x", pady=(6, 0))
    ttk.Button(library_bar, text="存入圖庫", command=lambda: save_form_to_gallery(state)).pack(side="left")
    ttk.Button(library_bar, text="加入堆疊", style="Accent.TButton", command=lambda: add_gallery_chart_to_stack(state)).pack(side="left", padx=(5, 0))
    ttk.Button(library_bar, text="覆寫", command=lambda: overwrite_gallery_chart(state)).pack(side="left", padx=(5, 0))
    ttk.Button(library_bar, text="刪除", command=lambda: remove_gallery_chart(state)).pack(side="right")


def build_chart_spec_panel(parent: ttk.Frame, state: dict[str, Any]) -> None:
    variables = state["variables"]
    spec_body, spec_button = build_collapsible_body(
        parent,
        "圖表規格（左軸 / 右軸）",
        variables["spec_panel_visible"],
        expand=True,
        padding=0,
    )
    state["spec_panel_body"] = spec_body
    state["spec_panel_button"] = spec_button
    spec_button.configure(command=lambda: toggle_main_design_pane(state, "spec"))
    canvas = tk.Canvas(spec_body, background=UI_CARD, highlightthickness=0)
    scrollbar = ttk.Scrollbar(spec_body, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    form = ttk.Frame(canvas, style="Card.TFrame", padding=(4, 4, 8, 4))
    window_id = canvas.create_window((0, 0), window=form, anchor="nw")
    form.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
    state["spec_canvas"] = canvas

    general, _general_button = build_collapsible_body(form, "General", variables["general_section_visible"], padding=5)
    for column in range(2):
        general.columnconfigure(column, weight=1)
    preset_combo = labeled_combo(general, "Preset", variables["preset"], preset_names(), 0, 0)
    preset_combo.bind("<<ComboboxSelected>>", lambda _event: apply_selected_preset_to_form(state))
    labeled_entry(general, "圖表 ID", variables["chart_id"], 0, 1)
    labeled_entry(general, "標題", variables["title"], 2, 0, columnspan=2)
    chart_type_combo = labeled_combo(general, "圖型", variables["chart_type"], chart_type_choices(), 4, 0)
    chart_type_combo.bind("<<ComboboxSelected>>", lambda _event: handle_chart_type_change(state))
    labeled_combo(
        general,
        f"標準高度倍數（1.0 = {DEFAULT_STANDARD_HEIGHT_PX}px）",
        variables["height_ratio"],
        HEIGHT_RATIO_CHOICES,
        4,
        1,
    )
    x_combo = labeled_combo(general, "X 欄位", variables["x"], [], 6, 0)
    x_combo.configure(state="normal")
    state["x_column_combo"] = x_combo
    palette_combo = labeled_combo(general, "Seaborn Color Combo", variables["palette"], PALETTE_CHOICES, 6, 1)
    axis_combo = labeled_combo(general, "軸模式", variables["axis_mode"], sorted(SUPPORTED_AXIS_MODES), 8, 0)
    axis_combo.bind("<<ComboboxSelected>>", lambda _event: update_axis_controls(state))
    ttk.Label(general, textvariable=variables["chart_mode_hint"], style="Card.TLabel", foreground=UI_MUTED, wraplength=470).grid(row=10, column=0, columnspan=2, sticky="w", padx=7, pady=(5, 2))

    left_axis, _left_button = build_collapsible_body(form, "├─ 左軸（主軸）", variables["left_axis_section_visible"], padding=5)
    for column in range(2):
        left_axis.columnconfigure(column, weight=1)
    y_entry = labeled_entry(left_axis, "Y 欄位（逗號分隔）", variables["y"], 0, 0, columnspan=2)
    labeled_entry(left_axis, "單位", variables["unit"], 2, 0)
    labeled_combo(left_axis, "數值格式", variables["y_format"], sorted(SUPPORTED_Y_FORMATS), 2, 1)
    labeled_entry(left_axis, "線寬", variables["line_width"], 4, 0)
    labeled_entry(left_axis, "線條透明度", variables["alpha"], 4, 1)
    ttk.Checkbutton(left_axis, text="顯示圖例", variable=variables["show_legend"]).grid(row=6, column=0, sticky="w", padx=7, pady=5)
    ttk.Checkbutton(left_axis, text="顯示零軸", variable=variables["zero_line"]).grid(row=6, column=1, sticky="w", padx=7, pady=5)

    right_axis, _right_button = build_collapsible_body(form, "└─ 右軸（可選）", variables["right_axis_section_visible"], padding=5)
    for column in range(2):
        right_axis.columnconfigure(column, weight=1)
    secondary_y_entry = labeled_entry(right_axis, "Y 欄位（留空即關閉）", variables["secondary_y"], 0, 0, columnspan=2)
    secondary_type_combo = labeled_combo(right_axis, "圖型", variables["secondary_type"], SECONDARY_TYPE_CHOICES, 2, 0)
    secondary_unit_entry = labeled_entry(right_axis, "單位", variables["secondary_unit"], 2, 1)
    secondary_format_combo = labeled_combo(right_axis, "數值格式", variables["secondary_y_format"], sorted(SUPPORTED_Y_FORMATS), 4, 0)
    labeled_entry(right_axis, "長條透明度（default 0.75）", variables["bar_alpha"], 4, 1)
    secondary_line_width_entry = labeled_entry(right_axis, "右軸線寬", variables["secondary_line_width"], 6, 0)
    secondary_alpha_entry = labeled_entry(right_axis, "右軸線條透明度", variables["secondary_alpha"], 6, 1)
    labeled_entry(right_axis, "線下填色透明度（default 0.5）", variables["area_alpha"], 8, 0)

    advanced, advanced_button = build_collapsible_body(form, "進階 / K線與量能", variables["advanced_visible"], padding=5)
    for column in range(2):
        advanced.columnconfigure(column, weight=1)
    labeled_combo(advanced, "空值策略", variables["missing"], sorted(SUPPORTED_MISSING_POLICIES), 0, 0)
    labeled_combo(advanced, "堆疊模式", variables["stack_mode"], sorted(SUPPORTED_STACK_MODES), 0, 1)
    labeled_combo(advanced, "刻度策略", variables["tick_policy"], sorted(SUPPORTED_TICK_POLICIES), 2, 0)
    labeled_entry(advanced, "Y 刻度數", variables["tick_count"], 2, 1)
    labeled_entry(advanced, "最大 X 刻度數", variables["max_x_ticks"], 4, 0)
    labeled_entry(advanced, "IQR 倍數", variables["outlier_iqr_multiplier"], 4, 1)
    labeled_combo(advanced, "品質稽核", variables["quality_mode"], QUALITY_MODE_CHOICES, 6, 0)
    labeled_combo(advanced, "無效日期", variables["invalid_date_policy"], INVALID_DATE_POLICY_CHOICES, 6, 1)
    labeled_combo(advanced, "重複日期", variables["duplicate_date_policy"], DUPLICATE_DATE_POLICY_CHOICES, 8, 0)
    labeled_combo(advanced, "極端值", variables["outlier_policy"], OUTLIER_POLICY_CHOICES, 8, 1)
    labeled_entry(advanced, "Normalized Y（HTML 圖例半隱藏勾選）", variables["normalized_y"], 10, 0, columnspan=2)
    labeled_entry(advanced, "Bar 寬度比", variables["bar_width_ratio"], 12, 0)
    labeled_entry(advanced, "Candle 寬度比", variables["candle_width_ratio"], 12, 1)
    open_entry = labeled_entry(advanced, "Adjusted Open 欄位", variables["open"], 14, 0)
    high_entry = labeled_entry(advanced, "Adjusted High 欄位", variables["high"], 14, 1)
    low_entry = labeled_entry(advanced, "Adjusted Low 欄位", variables["low"], 16, 0)
    close_entry = labeled_entry(advanced, "Adjusted Close 欄位", variables["close"], 16, 1)
    volume_entry = labeled_entry(advanced, "Volume 欄位（不補值）", variables["volume"], 18, 0)
    up_color_entry = labeled_entry(advanced, "上漲色（紅）", variables["up_color"], 18, 1)
    down_color_entry = labeled_entry(advanced, "下跌色（綠）", variables["down_color"], 20, 0)
    ttk.Checkbutton(advanced, text="自動最佳化版面與大資料渲染", variable=variables["auto_optimize"]).grid(row=22, column=0, sticky="w", padx=7, pady=5)
    labeled_entry(advanced, "渲染點數上限（空白沿用全域）", variables["render_max_points"], 22, 1)
    state["advanced_frame"] = advanced
    state["advanced_button"] = advanced_button
    state["secondary_series_widgets"] = [secondary_y_entry, secondary_type_combo]
    state["secondary_axis_format_widgets"] = [
        secondary_unit_entry,
        secondary_format_combo,
        secondary_line_width_entry,
        secondary_alpha_entry,
    ]
    state["general_y_widgets"] = [y_entry]
    state["axis_mode_widget"] = axis_combo
    state["candlestick_widgets"] = [open_entry, high_entry, low_entry, close_entry, volume_entry, up_color_entry, down_color_entry]

    buttons = ttk.Frame(parent, style="Card.TFrame")
    buttons.pack(fill="x", pady=(7, 0))
    ttk.Button(buttons, text="＋ 新增至最下方", style="Accent.TButton", command=lambda: add_chart_from_form(state)).pack(side="left", fill="x", expand=True)
    ttk.Button(buttons, text="覆寫選取圖", command=lambda: update_selected_chart_from_form(state)).pack(side="left", padx=(5, 0))
    ttk.Button(buttons, text="存入圖庫", command=lambda: save_form_to_gallery(state)).pack(side="left", padx=(5, 0))


def toggle_main_design_pane(state: dict[str, Any], pane_name: str) -> None:
    """Collapse a side pane to its header strip while keeping a restore control visible."""
    if pane_name == "source":
        body_key, button_key, variable_key, card_key, title, weight = (
            "source_panel_body",
            "source_panel_button",
            "source_panel_visible",
            "source_design_card",
            "資料來源",
            2,
        )
    elif pane_name == "spec":
        body_key, button_key, variable_key, card_key, title, weight = (
            "spec_panel_body",
            "spec_panel_button",
            "spec_panel_visible",
            "spec_design_card",
            "圖表規格（左軸 / 右軸）",
            6,
        )
    else:
        raise ValueError(f"未知的側邊面板：{pane_name}")
    variable = state["variables"][variable_key]
    visible = not bool(variable.get())
    set_collapsible_body(state[body_key], state[button_key], variable, title, visible, expand=True)
    pane = state["design_panes"]
    card = state[card_key]
    pane.pane(card, weight=weight if visible else 0)
    card.configure(width=(255 if pane_name == "source" else 660) if visible else 118)


def toggle_advanced_panel(state: dict[str, Any]) -> None:
    visible = not bool(state["variables"]["advanced_visible"].get())
    set_collapsible_body(
        state["advanced_frame"],
        state["advanced_button"],
        state["variables"]["advanced_visible"],
        "進階 / K線與量能",
        visible,
    )


def handle_chart_type_change(state: dict[str, Any]) -> None:
    """Switch coherent presets when entering or leaving candlestick mode."""
    variables = state["variables"]
    chart_type = str(variables["chart_type"].get())
    preset = str(variables["preset"].get())
    if chart_type == CANDLESTICK_CHART_TYPE and preset != "candlestick_volume":
        variables["preset"].set("candlestick_volume")
        apply_selected_preset_to_form(state)
        return
    if chart_type != CANDLESTICK_CHART_TYPE and preset == "candlestick_volume":
        variables["preset"].set("multi_series")
        apply_selected_preset_to_form(state)
        return
    update_axis_controls(state)


def update_axis_controls(state: dict[str, Any]) -> None:
    variables = state["variables"]
    chart_type = str(variables["chart_type"].get())
    is_candlestick = chart_type == CANDLESTICK_CHART_TYPE
    if is_candlestick:
        variables["axis_mode"].set("single")
        variables["missing"].set("ffill")
        variables["y"].set("")
        variables["secondary_y"].set("")
        if not str(variables["secondary_unit"].get()).strip():
            variables["secondary_unit"].set("Volume")
        variables["chart_mode_hint"].set(
            "Candlestick 與 Volume 是上下兩個單軸 panel；價格缺值向前取價，Volume 不補值。"
        )
        if "advanced_frame" in state and not bool(variables["advanced_visible"].get()):
            set_collapsible_body(
                state["advanced_frame"],
                state["advanced_button"],
                variables["advanced_visible"],
                "進階 / K線與量能",
                True,
            )
    else:
        variables["chart_mode_hint"].set("一般圖型使用 Y／右軸欄位；Normalized Y 由離線 HTML 圖例半隱藏切換。")
    axis_mode = str(variables["axis_mode"].get())
    supports_secondary = chart_type not in STACKED_CHART_TYPES | {"heatmap", CANDLESTICK_CHART_TYPE}
    widget_state = "normal" if supports_secondary and axis_mode in {"dual", "auto"} else "disabled"
    for widget in state.get("secondary_series_widgets", []):
        if isinstance(widget, ttk.Combobox):
            widget.configure(state="readonly" if widget_state == "normal" else "disabled")
        else:
            widget.configure(state=widget_state)
    format_enabled = is_candlestick or widget_state == "normal"
    for widget in state.get("secondary_axis_format_widgets", []):
        if isinstance(widget, ttk.Combobox):
            widget.configure(state="readonly" if format_enabled else "disabled")
        else:
            widget.configure(state="normal" if format_enabled else "disabled")
    for widget in state.get("general_y_widgets", []):
        widget.configure(state="disabled" if is_candlestick else "normal")
    axis_widget = state.get("axis_mode_widget")
    if axis_widget is not None:
        axis_widget.configure(state="disabled" if is_candlestick else "readonly")
    for widget in state.get("candlestick_widgets", []):
        widget.configure(state="normal" if is_candlestick else "disabled")


def build_chart_from_form(state: dict[str, Any]) -> dict[str, Any]:
    values = {
        variable_name: variable.get()
        for variable_name, variable in state["variables"].items()
        if variable_name in chart_form_field_mapping()
    }
    return chart_spec_from_form_values(values)


def apply_selected_preset_to_form(state: dict[str, Any]) -> None:
    variables = state["variables"]
    base = default_chart_spec("preview", variables["chart_type"].get(), "Preview", variables["x"].get(), parse_columns(variables["y"].get()))
    preset = apply_preset(base, variables["preset"].get())
    snapshot = chart_form_values_from_spec(preset)
    preset_fields = {
        "chart_type",
        "axis_mode",
        "secondary_type",
        "height_ratio",
        "missing",
        "y_format",
        "secondary_y_format",
        "palette",
        "tick_policy",
        "tick_count",
        "stack_mode",
        "quality_mode",
        "invalid_date_policy",
        "duplicate_date_policy",
        "outlier_policy",
        "outlier_iqr_multiplier",
        "max_x_ticks",
        "render_max_points",
        "normalized_y",
        "bar_alpha",
        "area_alpha",
        "alpha",
        "line_width",
        "bar_width_ratio",
        "candle_width_ratio",
        "up_color",
        "down_color",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "show_legend",
        "zero_line",
        "auto_optimize",
    }
    apply_chart_form_snapshot(state, {key: value for key, value in snapshot.items() if key in preset_fields})
    update_axis_controls(state)
    set_status(state, f"已套用 preset：{variables['preset'].get()}。")


def reset_chart_form(state: dict[str, Any]) -> None:
    defaults = chart_defaults(load_defaults())
    apply_chart_form_snapshot(state, chart_form_values_from_spec(defaults=defaults))
    for key in (
        "loaded_chart_id",
        "loaded_gallery_item_id",
        "loaded_form_preset",
        "loaded_form_type",
        "loaded_gallery_chart",
    ):
        state.pop(key, None)
    update_axis_controls(state)


# =============================================================================
# 5. 圖庫、拖曳與堆疊編輯
# =============================================================================


def open_data_source_tab(state: dict[str, Any]) -> None:
    notebook = state.get("notebook")
    data_tab = state.get("data_tab")
    if notebook is not None and data_tab is not None:
        notebook.select(data_tab)


def active_library_path(state: dict[str, Any]) -> Path:
    raw_path = str(state["variables"]["library_path"].get()).strip()
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    path = chart_library_path_for_config(selected_config_path(state))
    state["variables"]["library_path"].set(str(path))
    return path


def require_chart_library() -> None:
    if any(
        function is None
        for function in (
            append_library_chart,
            delete_library_chart,
            load_chart_library,
            search_library_charts,
            upsert_library_chart,
        )
    ):
        raise RuntimeError("此副本尚未包含 v2.3 VAP 圖庫模組。")


def selected_gallery_item_id(state: dict[str, Any], quiet: bool = False) -> str | None:
    tree = state.get("gallery_tree")
    selection = tree.selection() if tree is not None else ()
    if not selection:
        if not quiet:
            messagebox.showinfo(WINDOW_TITLE, "請先在 VAP 圖庫選擇一張圖。")
        return None
    return str(selection[0])


def refresh_gallery_tree(state: dict[str, Any]) -> None:
    tree = state.get("gallery_tree")
    if tree is None:
        return
    for item in tree.get_children():
        tree.delete(item)
    try:
        require_chart_library()
        library_path = active_library_path(state)
        load_chart_library(library_path, create=True)  # type: ignore[misc]
        items = search_library_charts(  # type: ignore[misc]
            library_path,
            query=str(state["variables"]["library_query"].get()).strip(),
        )
    except Exception as exc:
        set_status(state, f"圖庫讀取失敗：{exc}")
        return
    for item in items:
        item_id = str(item.get("id", ""))
        if not item_id:
            continue
        tags = item.get("tags", [])
        tree.insert(
            "",
            "end",
            iid=item_id,
            values=(
                str(item.get("name") or item_id),
                str(item.get("chart_type") or item.get("chart", {}).get("type", "")),
                ", ".join(str(value) for value in tags),
            ),
        )
    set_status(state, f"VAP 圖庫目前顯示 {len(items)} 張圖。")


def save_form_to_gallery(state: dict[str, Any]) -> None:
    try:
        require_chart_library()
        chart = build_chart_from_form(state)
        item = upsert_library_chart(  # type: ignore[misc]
            active_library_path(state),
            chart,
            name=str(chart.get("title") or chart.get("id")),
            tags=parse_columns(str(state["variables"]["library_tags"].get())),
            description=f"VAP 單圖規格；{float(chart.get('height_ratio', 1.0)):g}×{DEFAULT_STANDARD_HEIGHT_PX}px",
        )
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    refresh_gallery_tree(state)
    if state.get("gallery_tree") is not None:
        state["gallery_tree"].selection_set(str(item["id"]))
    set_status(state, f"已將單圖儲存至 VAP 圖庫：{item.get('name', item.get('id'))}。")


def load_selected_gallery_to_form(state: dict[str, Any]) -> None:
    item_id = selected_gallery_item_id(state)
    if item_id is None:
        return
    try:
        require_chart_library()
        library = load_chart_library(active_library_path(state), create=True)  # type: ignore[misc]
        item = next((item for item in library.get("items", []) if str(item.get("id")) == item_id), None)
        if item is None:
            raise ValueError("圖庫中找不到這張圖。")
        chart = dict(item.get("chart", {}))
        if not chart:
            raise ValueError("圖庫項目沒有可編輯圖表規格。")
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    apply_chart_form_snapshot(state, chart_form_values_from_spec(chart))
    state["variables"]["library_tags"].set(",".join(str(value) for value in item.get("tags", [])))
    state["loaded_gallery_item_id"] = item_id
    state["loaded_gallery_chart"] = deepcopy(chart)
    state["loaded_form_preset"] = str(state["variables"]["preset"].get())
    state["loaded_form_type"] = str(state["variables"]["chart_type"].get())
    update_axis_controls(state)
    set_status(state, f"已載入圖庫圖表：{item.get('name', item_id)}。")


def overwrite_gallery_chart(state: dict[str, Any]) -> None:
    item_id = selected_gallery_item_id(state)
    if item_id is None:
        return
    try:
        require_chart_library()
        form_chart = build_chart_from_form(state)
        loaded_chart = state.get("loaded_gallery_chart")
        replace_hidden = (
            item_id != state.get("loaded_gallery_item_id")
            or not isinstance(loaded_chart, dict)
            or str(state["variables"]["preset"].get()) != str(state.get("loaded_form_preset", ""))
            or str(form_chart.get("type", "")) != str(state.get("loaded_form_type", ""))
        )
        chart = merge_chart_form_update(
            loaded_chart if isinstance(loaded_chart, dict) else {},
            form_chart,
            replace_hidden=replace_hidden,
        )
        item = upsert_library_chart(  # type: ignore[misc]
            active_library_path(state),
            chart,
            item_id=item_id,
            name=str(chart.get("title") or chart.get("id")),
            tags=parse_columns(str(state["variables"]["library_tags"].get())),
        )
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    refresh_gallery_tree(state)
    state["gallery_tree"].selection_set(str(item["id"]))
    set_status(state, f"已覆寫圖庫圖表：{item.get('name', item_id)}。")


def add_gallery_chart_to_stack(state: dict[str, Any]) -> None:
    item_id = selected_gallery_item_id(state)
    if item_id is None:
        return
    try:
        require_chart_library()
        chart = append_library_chart(  # type: ignore[misc]
            selected_config_path(state),
            active_library_path(state),
            item_id,
        )
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    refresh_chart_tree(state)
    state["chart_tree"].selection_set(str(chart["id"]))
    set_status(state, f"已從圖庫加入 {chart['id']} 至堆疊最下方。")


def remove_gallery_chart(state: dict[str, Any]) -> None:
    item_id = selected_gallery_item_id(state)
    if item_id is None:
        return
    if not messagebox.askyesno(WINDOW_TITLE, "確定從 VAP 圖庫刪除這張圖？"):
        return
    try:
        require_chart_library()
        deleted = bool(delete_library_chart(active_library_path(state), item_id))  # type: ignore[misc]
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    refresh_gallery_tree(state)
    set_status(state, "已刪除圖庫圖表。" if deleted else "圖庫中找不到該圖表。")


def duplicate_selected_chart(state: dict[str, Any]) -> None:
    selected = selected_tree_item(state)
    if selected is None:
        return
    chart_id, _position = selected
    try:
        config = read_json(selected_config_path(state))
        charts = list(config.get("charts", []))
        source = next(chart for chart in charts if str(chart.get("id")) == chart_id)
        duplicate = duplicate_chart_for_stack(source, [str(chart.get("id")) for chart in charts])
        added = append_chart_spec(selected_config_path(state), duplicate)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    refresh_chart_tree(state)
    state["chart_tree"].selection_set(str(added["id"]))
    set_status(state, f"已複製為 {added['id']}。")


def begin_chart_drag(state: dict[str, Any], event: tk.Event) -> None:
    tree: ttk.Treeview = state["chart_tree"]
    item_id = str(tree.identify_row(event.y) or "")
    state["dragged_chart_id"] = item_id or None
    if item_id:
        tree.selection_set(item_id)


def preview_chart_drag(state: dict[str, Any], event: tk.Event) -> None:
    if not state.get("dragged_chart_id"):
        return
    tree: ttk.Treeview = state["chart_tree"]
    target_id = str(tree.identify_row(event.y) or "")
    if target_id:
        tree.focus(target_id)


def finish_chart_drag(state: dict[str, Any], event: tk.Event) -> None:
    dragged_id = str(state.pop("dragged_chart_id", "") or "")
    tree: ttk.Treeview = state["chart_tree"]
    target_id = str(tree.identify_row(event.y) or "")
    if not dragged_id or not target_id or dragged_id == target_id:
        return
    position = "before"
    bounds = tree.bbox(target_id)
    if bounds and event.y >= bounds[1] + bounds[3] / 2:
        position = "after"
    try:
        config_path = selected_config_path(state)
        with file_transaction_lock(config_path):
            config = read_json(config_path)
            config["charts"] = reorder_chart_items(
                list(config.get("charts", [])),
                dragged_id,
                target_id,
                position,
            )
            write_json(config_path, config)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    refresh_chart_tree(state)
    tree.selection_set(dragged_id)
    set_status(state, f"已拖曳調整 {dragged_id} 的上下順序。")


# =============================================================================
# 6. 圖組 CRUD
# =============================================================================


def config_chart_rows(config_path: Path) -> list[dict[str, Any]]:
    config = read_json(config_path)
    rows = [
        {
            "position": index,
            "id": str(chart.get("id", "")),
            "type": str(chart.get("type", "")),
            "axis": str(chart.get("axis_mode", "auto")),
            "height": f"{float(chart.get('height_ratio', 1.0)):g}×",
            "title": str(chart.get("title", "")),
        }
        for index, chart in enumerate(config.get("charts", []), start=1)
    ]
    identifiers = [row["id"] for row in rows]
    if any(not identifier for identifier in identifiers) or len(set(identifiers)) != len(identifiers):
        raise ValueError("圖組含空白或重複的 chart id；請先修正設定檔。")
    return rows


def refresh_chart_tree(state: dict[str, Any]) -> None:
    tree: ttk.Treeview = state["chart_tree"]
    for item in tree.get_children():
        tree.delete(item)
    config_path = selected_config_path(state)
    if not config_path.exists():
        set_status(state, "設定檔尚不存在；可按『新建』。")
        return
    try:
        rows = config_chart_rows(config_path)
    except Exception as exc:
        set_status(state, f"讀取失敗：{exc}")
        return
    for row in rows:
        tree.insert("", "end", iid=row["id"], values=(row["position"], row["type"], row["height"], row["title"]))
    set_status(state, f"目前共 {len(rows)} 張圖。")


def add_chart_from_form(state: dict[str, Any]) -> None:
    try:
        chart = build_chart_from_form(state)
        added = append_chart_spec(selected_config_path(state), chart)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    refresh_chart_tree(state)
    state["chart_tree"].selection_set(added["id"])
    set_status(state, f"已把 {added['id']} 新增到最下方。")


def update_selected_chart_from_form(state: dict[str, Any]) -> None:
    selected = selected_tree_item(state)
    if selected is None:
        return
    chart_id, _position = selected
    try:
        chart = build_chart_from_form(state)
        replace_hidden = (
            chart_id != state.get("loaded_chart_id")
            or str(state["variables"]["preset"].get()) != str(state.get("loaded_form_preset", ""))
            or str(chart.get("type", "")) != str(state.get("loaded_form_type", ""))
        )
        updates = chart if replace_hidden else chart_form_owned_patch(chart)
        updated = update_chart_spec(selected_config_path(state), chart_id, updates)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    refresh_chart_tree(state)
    state["chart_tree"].selection_set(str(updated["id"]))
    set_status(state, f"已更新 {updated['id']}。")


def load_selected_chart_to_form(state: dict[str, Any]) -> None:
    selected = selected_tree_item(state, quiet=True)
    if selected is None:
        return
    chart_id, _position = selected
    config = read_json(selected_config_path(state))
    chart = next((item for item in config.get("charts", []) if str(item.get("id")) == chart_id), None)
    if chart is None:
        return
    apply_chart_form_snapshot(state, chart_form_values_from_spec(chart))
    state["loaded_chart_id"] = chart_id
    state["loaded_form_preset"] = str(state["variables"]["preset"].get())
    state["loaded_form_type"] = str(state["variables"]["chart_type"].get())
    update_axis_controls(state)


def move_selected_chart(state: dict[str, Any], direction: int) -> None:
    selected = selected_tree_item(state)
    if selected is None:
        return
    chart_id, position = selected
    if move_chart_spec(selected_config_path(state), chart_id, max(1, position + direction)):
        refresh_chart_tree(state)
        state["chart_tree"].selection_set(chart_id)


def remove_selected_chart(state: dict[str, Any]) -> None:
    selected = selected_tree_item(state)
    if selected is None:
        return
    chart_id, _position = selected
    if not messagebox.askyesno(WINDOW_TITLE, f"確定移除圖表 {chart_id}？"):
        return
    remove_chart_spec(selected_config_path(state), chart_id)
    refresh_chart_tree(state)


def select_config(root: tk.Tk, state: dict[str, Any]) -> None:
    if state.get("busy"):
        messagebox.showinfo(WINDOW_TITLE, "任務執行中，完成後再切換圖組設定檔。")
        return
    selected = filedialog.askopenfilename(parent=root, title="選擇圖組設定檔", filetypes=[("JSON", "*.json"), ("All files", "*.*")])
    if selected:
        activate_config(state, selected)


def create_new_config(root: tk.Tk, state: dict[str, Any]) -> None:
    if state.get("busy"):
        messagebox.showinfo(WINDOW_TITLE, "任務執行中，完成後再建立新圖組。")
        return
    config_name = filedialog.asksaveasfilename(parent=root, title="建立圖組設定檔", defaultextension=".json", filetypes=[("JSON", "*.json")])
    if not config_name:
        return
    config_path = Path(config_name).resolve()
    write_json(config_path, default_project_config(""))
    activate_config(state, config_path)
    set_status(state, "已建立空白圖組；請到『資料來源』掃描資料。")


def load_project_source_to_ui(state: dict[str, Any]) -> None:
    config_path = selected_config_path(state)
    if not config_path.exists():
        return
    try:
        config = read_json(config_path)
        project = config.get("project", {})
        raw_source = project.get("data_source") or project.get("data")
        if not raw_source:
            variables = state["variables"]
            variables["source_path"].set("")
            variables["source_kind"].set("尚未選擇")
            variables["source_table"].set("")
            return
        spec = normalize_source_spec(raw_source)
        locator = str(spec.get("url") or spec.get("path") or "")
        if spec.get("kind") != "sqlalchemy" and locator:
            candidate = Path(locator).expanduser()
            if not candidate.is_absolute():
                locator = str((config_path.parent / candidate).resolve())
        variables = state["variables"]
        variables["source_path"].set(locator)
        variables["source_kind"].set(str(spec.get("kind", "unknown")))
        variables["source_table"].set(str(spec.get("table") or spec.get("sheet") or ""))
    except Exception as exc:
        set_status(state, f"資料來源載入失敗：{exc}")


# =============================================================================
# 6. 資料來源 Tab：檔案、Parquet、DuckDB、SQLite、SQLAlchemy
# =============================================================================


def build_data_tab(root: tk.Tk, parent: ttk.Frame, state: dict[str, Any]) -> None:
    source_card = ttk.Frame(parent, style="Card.TFrame", padding=10)
    source_card.pack(fill="x", pady=(0, 8))
    source_card.columnconfigure(1, weight=1)
    variables = state["variables"]
    ttk.Label(source_card, text="資料來源", style="Card.TLabel").grid(row=0, column=0, padx=(0, 8))
    ttk.Entry(source_card, textvariable=variables["source_path"]).grid(row=0, column=1, sticky="ew")
    ttk.Button(source_card, text="選擇檔案", command=lambda: browse_source(root, state)).grid(row=0, column=2, padx=(8, 0))
    ttk.Button(source_card, text="選擇資料夾", command=lambda: browse_source_directory(root, state)).grid(row=0, column=3, padx=(8, 0))
    scan_button = ttk.Button(source_card, text="掃描表格", command=lambda: start_source_scan(state))
    scan_button.grid(row=0, column=4, padx=(8, 0))
    state["scan_button"] = scan_button
    ttk.Label(source_card, text="類型", style="Card.TLabel").grid(row=1, column=0, sticky="w", pady=(8, 0))
    ttk.Label(source_card, textvariable=variables["source_kind"], style="Card.TLabel").grid(row=1, column=1, sticky="w", pady=(8, 0))
    ttk.Label(source_card, text="資料表／Sheet", style="Card.TLabel").grid(row=1, column=2, sticky="e", padx=(0, 8), pady=(8, 0))
    table_combo = ttk.Combobox(source_card, textvariable=variables["source_table"], values=[], state="readonly")
    table_combo.grid(row=1, column=3, columnspan=2, sticky="ew", pady=(8, 0))
    state["source_table_combo"] = table_combo
    state.setdefault("source_table_combos", []).append(table_combo)
    ttk.Label(source_card, text="抽樣列數", style="Card.TLabel").grid(row=2, column=0, sticky="w", pady=(8, 0))
    ttk.Entry(source_card, textvariable=variables["sample_rows"], width=12).grid(row=2, column=1, sticky="w", pady=(8, 0))
    analyze_button = ttk.Button(source_card, text="分析欄位與自動建議", style="Accent.TButton", command=lambda: start_source_discovery(state))
    analyze_button.grid(row=2, column=4, sticky="e", pady=(8, 0))
    state["analyze_button"] = analyze_button

    content = ttk.Panedwindow(parent, orient="horizontal")
    content.pack(fill="both", expand=True)
    column_card = ttk.Frame(content, style="Card.TFrame", padding=10)
    suggestion_card = ttk.Frame(content, style="Card.TFrame", padding=10)
    content.add(column_card, weight=7)
    content.add(suggestion_card, weight=4)
    ttk.Label(column_card, text="欄位規格與資料品質", style="Section.TLabel").pack(anchor="w", pady=(0, 8))
    tree = ttk.Treeview(
        column_card,
        columns=("name", "declared", "dtype", "semantic", "unit", "null", "distinct", "outliers", "range"),
        show="headings",
    )
    headings = {
        "name": "欄位",
        "declared": "來源型別",
        "dtype": "原始型別",
        "semantic": "語意型別",
        "unit": "單位",
        "null": "空值%",
        "distinct": "唯一值",
        "outliers": "極端值",
        "range": "範圍",
    }
    widths = {"name": 130, "declared": 95, "dtype": 85, "semantic": 85, "unit": 55, "null": 60, "distinct": 60, "outliers": 60, "range": 135}
    for key, heading in headings.items():
        tree.heading(key, text=heading)
        tree.column(key, width=widths[key], stretch=key in {"name", "range"})
    tree.pack(fill="both", expand=True)
    state["column_tree"] = tree

    ttk.Label(suggestion_card, text="自動圖表建議", style="Section.TLabel").pack(anchor="w")
    ttk.Label(suggestion_card, textvariable=variables["suggestion"], style="Card.TLabel", wraplength=330, justify="left").pack(anchor="w", pady=(10, 16))
    ttk.Button(suggestion_card, text="套用建議到圖表表單", command=lambda: apply_manifest_suggestion_to_form(state)).pack(fill="x")
    ttk.Button(suggestion_card, text="設為目前圖組資料來源", command=lambda: save_manifest_source_to_project(state)).pack(fill="x", pady=(8, 0))
    ttk.Button(suggestion_card, text="自動建立第一張圖", style="Accent.TButton", command=lambda: auto_add_manifest_chart(state)).pack(fill="x", pady=(8, 0))


def browse_source(root: tk.Tk, state: dict[str, Any]) -> None:
    if state.get("busy"):
        messagebox.showinfo(WINDOW_TITLE, "來源任務執行中，完成後再切換資料來源。")
        return
    selected = filedialog.askopenfilename(parent=root, title="選擇資料來源", filetypes=SOURCE_FILE_TYPES)
    if not selected:
        return
    variables = state["variables"]
    variables["source_path"].set(selected)
    variables["source_kind"].set(detect_source_kind(selected))
    start_source_scan(state)


def browse_source_directory(root: tk.Tk, state: dict[str, Any]) -> None:
    if state.get("busy"):
        messagebox.showinfo(WINDOW_TITLE, "來源任務執行中，完成後再切換資料來源。")
        return
    selected = filedialog.askdirectory(parent=root, title="選擇 Parquet 資料集資料夾")
    if not selected:
        return
    variables = state["variables"]
    variables["source_path"].set(selected)
    variables["source_kind"].set(detect_source_kind(selected))
    start_source_scan(state)


def source_spec_from_ui(state: dict[str, Any], relative_to_config: bool = False) -> dict[str, Any]:
    variables = state["variables"]
    source = variables["source_path"].get().strip()
    if not source:
        raise ValueError("請先選擇資料來源。")
    table = variables["source_table"].get().strip()
    if relative_to_config:
        spec = relative_source_spec(source, selected_config_path(state), table=table)
    else:
        spec = normalize_source_spec(source)
        if spec["kind"] == "excel":
            spec["sheet"] = table
        elif table and spec["kind"] not in {"csv", "tsv", "parquet", "json", "jsonl"}:
            spec["table"] = table
    return spec


def configure_source_table_choices(state: dict[str, Any], tables: list[str]) -> None:
    """Keep the compact left source panel and detailed source tab synchronized."""
    combos = list(state.get("source_table_combos", []))
    if not combos and state.get("source_table_combo") is not None:
        combos = [state["source_table_combo"]]
    for combo in combos:
        combo.configure(values=tables)


def source_task_context(state: dict[str, Any]) -> dict[str, str]:
    variables = state["variables"]
    return {
        "config": str(selected_config_path(state)),
        "source_path": str(variables["source_path"].get()).strip(),
        "source_table": str(variables["source_table"].get()).strip(),
    }


def source_task_context_matches(state: dict[str, Any], context: dict[str, Any]) -> bool:
    return source_task_context(state) == {
        "config": str(context.get("config", "")),
        "source_path": str(context.get("source_path", "")),
        "source_table": str(context.get("source_table", "")),
    }


def scan_source_tables(state: dict[str, Any]) -> None:
    try:
        spec = source_spec_from_ui(state)
        tables = list_source_tables(spec)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    state["variables"]["source_kind"].set(str(spec["kind"]))
    configure_source_table_choices(state, tables)
    if tables:
        state["variables"]["source_table"].set(tables[0])
    set_status(state, f"偵測到 {len(tables)} 個資料表／Sheet。")


def start_source_scan(state: dict[str, Any]) -> None:
    try:
        spec = source_spec_from_ui(state)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    context = source_task_context(state)
    start_async_task(
        state,
        "scan",
        "正在唯讀掃描資料表與 Sheet…",
        lambda: {"spec": spec, "tables": list_source_tables(spec), "_context": context},
    )


def populate_source_scan(state: dict[str, Any], payload: dict[str, Any]) -> None:
    context = payload.get("_context", {})
    if context and not source_task_context_matches(state, context):
        set_status(state, "來源已切換；已丟棄較舊的掃描結果。")
        return
    spec = payload.get("spec", {})
    tables = [str(value) for value in payload.get("tables", [])]
    state["variables"]["source_kind"].set(str(spec.get("kind", "unknown")))
    configure_source_table_choices(state, tables)
    if tables:
        state["variables"]["source_table"].set(tables[0])
    set_status(state, f"偵測到 {len(tables)} 個資料表／Sheet。")


def start_source_discovery(state: dict[str, Any]) -> None:
    try:
        spec = source_spec_from_ui(state)
        sample_rows = int(state["variables"]["sample_rows"].get())
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    context = source_task_context(state)
    start_async_task(
        state,
        "discover",
        "正在抽樣、辨識欄位型別與建立圖表建議…",
        lambda: {
            "manifest": discover_source(spec, sample_rows=sample_rows),
            "_context": context,
        },
    )


def populate_discovery_result(
    state: dict[str, Any],
    manifest: dict[str, Any],
    context: dict[str, Any] | None = None,
) -> None:
    if context and not source_task_context_matches(state, context):
        set_status(state, "來源或圖組已切換；已丟棄較舊的分析結果。")
        return
    state["manifest"] = manifest
    config_path = Path(str(context.get("config"))).resolve() if context and context.get("config") else selected_config_path(state)
    if config_path.exists():
        manifest_path = config_path.with_name(f"{config_path.stem}_source_manifest.json")
        write_discovery_manifest(manifest_path, manifest)
    tree: ttk.Treeview = state["column_tree"]
    for item in tree.get_children():
        tree.delete(item)
    declared_types = {
        str(column.get("name", "")): str(column.get("declared_type", ""))
        for column in manifest.get("declared_schema", {}).get("columns", [])
    }
    for profile in manifest.get("columns", []):
        minimum = profile.get("min")
        maximum = profile.get("max")
        range_text = "" if minimum is None else f"{minimum:g} ~ {maximum:g}"
        tree.insert(
            "",
            "end",
            values=(
                profile.get("name", ""),
                declared_types.get(str(profile.get("name", "")), ""),
                profile.get("dtype", ""),
                profile.get("semantic_type", ""),
                profile.get("unit", ""),
                f"{float(profile.get('null_pct', 0)) * 100:.1f}%",
                profile.get("distinct_count", 0),
                profile.get("outlier_count", 0),
                range_text,
            ),
        )
    column_names = [str(profile.get("name", "")) for profile in manifest.get("columns", [])]
    if "x_column_combo" in state:
        state["x_column_combo"].configure(values=column_names)
    suggestion = manifest.get("suggestion", {})
    roles = manifest.get("roles", {})
    quality = manifest.get("quality", {})
    issue_count = len(quality.get("issues", []))
    state["variables"]["suggestion"].set(
        f"資料粒度：{roles.get('grain', 'row')}\n"
        f"圖型：{suggestion.get('chart_type')}\n"
        f"軸模式：{suggestion.get('axis_mode')}\n"
        f"X：{suggestion.get('x')}\n"
        f"Y：{', '.join(suggestion.get('y', []))}\n"
        f"右軸：{', '.join(suggestion.get('secondary_y', [])) or '無'}\n"
        f"信心：{float(suggestion.get('confidence', 0)):.0%}\n"
        f"品質：{quality.get('status', '未檢查')}（{issue_count} 項提示）\n"
        f"理由：{suggestion.get('reason', '')}"
    )
    set_status(state, f"資料分析完成：{manifest.get('sample_rows', 0)} 列、{manifest.get('sample_columns', 0)} 欄。")


def apply_manifest_suggestion_to_form(state: dict[str, Any]) -> None:
    manifest = state.get("manifest")
    if not manifest:
        messagebox.showinfo(WINDOW_TITLE, "請先分析資料來源。")
        return
    chart = chart_from_suggestion(manifest, chart_id="auto_chart")
    apply_chart_form_snapshot(state, chart_form_values_from_spec(chart))
    update_axis_controls(state)
    set_status(state, "已把自動建議帶入圖表表單，可再修改後新增。")


def save_manifest_source_to_project(state: dict[str, Any]) -> bool:
    config_path = selected_config_path(state)
    if not config_path.exists():
        messagebox.showerror(WINDOW_TITLE, "請先建立圖組設定檔。")
        return False
    try:
        spec = source_spec_from_ui(state, relative_to_config=True)
        with file_transaction_lock(config_path):
            config = read_json(config_path)
            config.setdefault("project", {})["data_source"] = spec
            config["project"]["data"] = str(spec.get("path", ""))
            config["project"]["source"] = Path(state["variables"]["source_path"].get()).name
            manifest = state.get("manifest") or {}
            suggestion = manifest.get("suggestion", {})
            if suggestion.get("x"):
                config["project"]["date_column"] = suggestion["x"]
            write_json(config_path, config)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return False
    set_status(state, "已更新目前圖組的資料來源。")
    return True


def auto_add_manifest_chart(state: dict[str, Any]) -> None:
    if not state.get("manifest"):
        messagebox.showinfo(WINDOW_TITLE, "請先分析資料來源。")
        return
    if not save_manifest_source_to_project(state):
        return
    apply_manifest_suggestion_to_form(state)
    add_chart_from_form(state)


# =============================================================================
# 7. 全域預設值 Tab
# =============================================================================


def add_default_editor(
    parent: ttk.Frame,
    state: dict[str, Any],
    section: str,
    key: str,
    value: Any,
    row: int,
    label: str,
) -> None:
    ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", padx=7, pady=3)
    if isinstance(value, bool):
        variable: tk.Variable = tk.BooleanVar(value=value)
        widget: tk.Widget = ttk.Checkbutton(parent, text="啟用", variable=variable)
    elif key in DEFAULT_ENUM_CHOICES:
        variable = tk.StringVar(value=display_value(value))
        widget = ttk.Combobox(
            parent,
            textvariable=variable,
            values=DEFAULT_ENUM_CHOICES[key],
            state="normal" if key == "palette" else "readonly",
        )
    else:
        variable = tk.StringVar(value=display_value(value))
        widget = ttk.Entry(parent, textvariable=variable)
    state["default_variables"][section][key] = variable
    widget.grid(row=row, column=1, sticky="ew", padx=7, pady=3)


def build_defaults_tab(parent: ttk.Frame, state: dict[str, Any]) -> None:
    defaults = load_defaults()
    canvas = tk.Canvas(parent, background=UI_BACKGROUND, highlightthickness=0)
    scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollbar.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    scroll_body = ttk.Frame(canvas, padding=(0, 0, 8, 0))
    window_id = canvas.create_window((0, 0), window=scroll_body, anchor="nw")
    scroll_body.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window_id, width=event.width))
    state["defaults_canvas"] = canvas

    content = ttk.Panedwindow(scroll_body, orient="horizontal")
    content.pack(fill="both", expand=True)
    project_card = ttk.Frame(content, style="Card.TFrame", padding=10)
    chart_card = ttk.Frame(content, style="Card.TFrame", padding=10)
    content.add(project_card, weight=1)
    content.add(chart_card, weight=1)
    ttk.Label(project_card, text="專案與輸出預設值", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=7)
    ttk.Label(chart_card, text="圖表預設值", style="Section.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=7)
    project_card.columnconfigure(1, weight=1)
    chart_card.columnconfigure(1, weight=1)
    for row, key in enumerate(EDITABLE_PROJECT_KEYS, start=1):
        add_default_editor(project_card, state, "project", key, defaults["project"].get(key), row, PROJECT_FIELD_LABELS.get(key, key))
    for row, key in enumerate(EDITABLE_CHART_KEYS, start=1):
        add_default_editor(chart_card, state, "chart", key, defaults["chart"].get(key), row, CHART_FIELD_LABELS.get(key, key))
    button_row = max(len(EDITABLE_PROJECT_KEYS), len(EDITABLE_CHART_KEYS)) + 2
    buttons = ttk.Frame(scroll_body)
    buttons.pack(fill="x", pady=(10, 0))
    ttk.Button(buttons, text="儲存全域預設值", style="Accent.TButton", command=lambda: save_defaults_from_ui(state)).pack(side="left")
    ttk.Button(buttons, text="套用到目前圖組", command=lambda: apply_defaults_to_current_project(state)).pack(side="left", padx=(8, 0))
    ttk.Button(buttons, text="重新載入", command=lambda: reload_defaults_ui(state)).pack(side="left", padx=(8, 0))


def defaults_from_ui(state: dict[str, Any]) -> dict[str, Any]:
    defaults = load_defaults()
    for section in ["project", "chart"]:
        for key, variable in state["default_variables"][section].items():
            defaults[section][key] = parse_like(variable.get(), defaults[section].get(key))
    defaults["updated_at"] = utc_now_text()
    defaults.setdefault("changelog", []).append(
        {"version": str(defaults.get("version", "2.3.1")), "changes": ["User-edited defaults from VAP desktop UI"], "at": defaults["updated_at"]}
    )
    return defaults


def save_defaults_from_ui(state: dict[str, Any]) -> None:
    try:
        defaults = defaults_from_ui(state)
        save_defaults(default_defaults_path(), defaults)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    set_status(state, "全域預設值已儲存；新圖與新專案會自動套用。")


def apply_defaults_to_current_project(state: dict[str, Any]) -> None:
    config_path = selected_config_path(state)
    if not config_path.exists():
        messagebox.showerror(WINDOW_TITLE, "目前圖組設定檔不存在。")
        return
    apply_to_charts = messagebox.askyesno(
        WINDOW_TITLE,
        "是否同時把圖表預設值套用到目前所有既有圖？\n\n選『否』只更新專案與輸出設定。",
    )
    try:
        defaults = defaults_from_ui(state)
        with file_transaction_lock(config_path):
            config = read_json(config_path)
            current_project = config.setdefault("project", {})
            current_project.update(project_defaults(defaults))
            if apply_to_charts:
                effective_chart_defaults = chart_defaults(defaults)
                candle_preset = defaults.get("presets", {}).get("candlestick_volume", {})
                candle_contract_keys = {
                    "axis_mode",
                    "missing",
                    "height_ratio",
                    "price_height_fraction",
                    "volume_height_fraction",
                    "secondary_y",
                    "secondary_type",
                    "y_format",
                    "secondary_y_format",
                    "bar_alpha",
                    "bar_width_ratio",
                    "candle_width_ratio",
                    "up_color",
                    "down_color",
                    "axis_zero_policy",
                    "secondary_axis_zero_policy",
                    "price_basis",
                    "derive_adjusted_prices",
                }
                for chart in config.get("charts", []):
                    candlestick_mapping = {
                        key: deepcopy(chart.get(key))
                        for key in ("x", "open", "high", "low", "close", "volume")
                    } if str(chart.get("type", "")) == CANDLESTICK_CHART_TYPE else {}
                    for key in EDITABLE_CHART_KEYS:
                        chart[key] = deepcopy(effective_chart_defaults.get(key))
                    if str(chart.get("type", "")) == CANDLESTICK_CHART_TYPE:
                        for key in candle_contract_keys:
                            if key in candle_preset:
                                chart[key] = deepcopy(candle_preset[key])
                        chart["axis_mode"] = "single"
                        chart["secondary_y"] = []
                        chart["missing"] = "ffill"
                        chart.update(candlestick_mapping)
            config.setdefault("metadata", {})["updated_at"] = utc_now_text()
            write_json(config_path, config)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    scope = "專案與所有既有圖" if apply_to_charts else "專案與輸出"
    set_status(state, f"已把預設值套用到目前{scope}。")


def reload_defaults_ui(state: dict[str, Any]) -> None:
    defaults = load_defaults()
    for section in ["project", "chart"]:
        for key, variable in state["default_variables"][section].items():
            value = defaults[section].get(key)
            variable.set(bool(value) if isinstance(variable, tk.BooleanVar) else display_value(value))
    set_status(state, "已重新載入全域預設值。")


# =============================================================================
# 8. 非阻塞任務、渲染與輸出
# =============================================================================


def start_async_task(
    state: dict[str, Any],
    task_name: str,
    status_text: str,
    function: Callable[[], Any],
) -> None:
    if state["busy"]:
        messagebox.showinfo(WINDOW_TITLE, "已有任務執行中，請稍候。")
        return
    state["busy"] = True
    set_status(state, status_text)
    for key in [
        "full_render_button",
        "single_render_button",
        "preview_render_button",
        "analyze_button",
        "scan_button",
        "compact_analyze_button",
        "compact_scan_button",
    ]:
        if key in state:
            state[key].configure(state="disabled")

    def worker() -> None:
        try:
            result = function()
            state["task_queue"].put((task_name, "success", result))
        except Exception as exc:
            state["task_queue"].put((task_name, "error", exc))

    threading.Thread(target=worker, daemon=True).start()


def start_render_stack(state: dict[str, Any]) -> None:
    # Resolve every Tk variable on the UI thread.  Worker threads receive only
    # immutable Python values; Tkinter variables are not thread-safe.
    config_path = selected_config_path(state)
    start_async_task(
        state,
        "render",
        "正在生成完整圖組…",
        lambda: render_stack(config_path),
    )


def start_render_single(state: dict[str, Any]) -> None:
    selected = selected_tree_item(state)
    if selected is None:
        return
    chart_id, _position = selected
    config_path = selected_config_path(state)
    start_async_task(
        state,
        "render",
        f"正在生成單圖 {chart_id}…",
        lambda: render_single_chart(config_path, chart_id),
    )


def render_form_chart_preview(config_path: Path, chart: dict[str, Any]) -> dict[str, Any]:
    """Render an unsaved editor form without inserting it into the stack."""

    config_path = config_path.expanduser().resolve()
    config = read_json(config_path)
    preview_config = deepcopy(config)
    preview_config["charts"] = [deepcopy(chart)]
    project, charts = normalize_project_and_charts(preview_config)
    base_output_name = str(project.get("output_name", "vap_seaborn_chart"))
    project["output_name"] = f"{base_output_name}__preview_{chart['id']}"
    project["shared_x"] = str(chart.get("type", "")) == CANDLESTICK_CHART_TYPE
    return render_chart_collection(
        config_path,
        project,
        charts,
        render_mode="preview",
    )


def start_render_form_preview(state: dict[str, Any]) -> None:
    try:
        config_path = selected_config_path(state)
        if not config_path.exists():
            raise FileNotFoundError("請先建立圖組設定檔並設定資料來源。")
        chart = build_chart_from_form(state)
    except Exception as exc:
        messagebox.showerror(WINDOW_TITLE, str(exc))
        return
    start_async_task(
        state,
        "preview",
        f"正在預覽目前表單 {chart['id']}…",
        lambda: render_form_chart_preview(config_path, chart),
    )


def poll_task_queue(root: tk.Tk, state: dict[str, Any]) -> None:
    try:
        task_name, status, payload = state["task_queue"].get_nowait()
    except queue.Empty:
        root.after(TASK_POLL_INTERVAL_MS, poll_task_queue, root, state)
        return
    try:
        state["busy"] = False
        for key in [
            "full_render_button",
            "single_render_button",
            "preview_render_button",
            "analyze_button",
            "scan_button",
            "compact_analyze_button",
            "compact_scan_button",
        ]:
            if key in state:
                state[key].configure(state="normal")
        if status == "error":
            set_status(state, f"任務失敗：{payload}")
            messagebox.showerror(WINDOW_TITLE, str(payload))
        elif task_name == "scan":
            populate_source_scan(state, payload)
        elif task_name == "discover":
            populate_discovery_result(
                state,
                payload.get("manifest", payload),
                payload.get("_context") if isinstance(payload, dict) else None,
            )
        else:
            state["last_outputs"] = payload.get("outputs", [])
            state["last_report"] = payload
            issue_count = len(payload.get("diagnostics", {}).get("issues", []))
            set_status(state, f"生成完成：{payload.get('chart_count', 0)} 張圖、{len(payload.get('outputs', []))} 種格式、{issue_count} 項品質提示。")
            messagebox.showinfo(WINDOW_TITLE, f"圖表生成完成。\n品質提示：{issue_count} 項")
    except Exception as exc:
        state["busy"] = False
        set_status(state, f"處理任務結果失敗：{exc}")
        messagebox.showerror(WINDOW_TITLE, str(exc))
    finally:
        root.after(TASK_POLL_INTERVAL_MS, poll_task_queue, root, state)


def open_last_output(state: dict[str, Any]) -> None:
    preferred_suffixes = (".html", ".png", ".svg", ".pdf")
    available_outputs = [Path(path) for path in state.get("last_outputs", []) if Path(path).exists()]
    candidates = sorted(
        available_outputs,
        key=lambda path: preferred_suffixes.index(path.suffix.lower()) if path.suffix.lower() in preferred_suffixes else len(preferred_suffixes),
    )
    if not candidates:
        config_path = selected_config_path(state)
        if config_path.exists():
            try:
                config = read_json(config_path)
                project = config.get("project", {})
                raw_directory = Path(str(project.get("output_directory", "output"))).expanduser()
                output_directory = raw_directory if raw_directory.is_absolute() else config_path.parent / raw_directory
                output_name = str(project.get("output_name", "vap_seaborn_chart"))
                configured_formats = [str(value).lower().lstrip(".") for value in project.get("output_formats", [])]
                for suffix in preferred_suffixes:
                    if suffix.lstrip(".") not in configured_formats:
                        continue
                    candidate = (output_directory / f"{output_name}{suffix}").resolve()
                    if candidate.exists():
                        candidates.append(candidate)
                        break
            except Exception as exc:
                messagebox.showerror(WINDOW_TITLE, str(exc))
                return
    if not candidates:
        messagebox.showinfo(WINDOW_TITLE, "尚未找到 HTML／PNG／SVG／PDF 輸出，請先生成圖表。")
        return
    open_file_with_default_app(candidates[0])


def open_last_audit(state: dict[str, Any]) -> None:
    report = state.get("last_report", {})
    audit_path = Path(str(report.get("audit", ""))) if report.get("audit") else None
    if audit_path is None or not audit_path.exists():
        config_path = selected_config_path(state)
        if config_path.exists():
            config = read_json(config_path)
            project = config.get("project", {})
            candidate = (
                config_path.parent
                / str(project.get("output_directory", "output"))
                / f"{project.get('output_name', 'vap_seaborn_chart')}_audit.json"
            ).resolve()
            audit_path = candidate if candidate.exists() else None
    if audit_path is None:
        messagebox.showinfo(WINDOW_TITLE, "尚未找到稽核報告，請先生成圖表。")
        return
    open_file_with_default_app(audit_path)


def main() -> int:
    root = tk.Tk()
    create_application(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
