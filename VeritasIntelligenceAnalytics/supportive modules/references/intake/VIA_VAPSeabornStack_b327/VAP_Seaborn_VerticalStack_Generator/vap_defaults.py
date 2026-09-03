"""Versioned SSOT defaults and visual presets for VAP Seaborn Generator."""

from __future__ import annotations

import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

from vap_atomic_io import atomic_write_json, file_transaction_lock


# =============================================================================
# 0. SSOT 參數
# =============================================================================

DEFAULTS_SCHEMA = "VIA-VAP-SEABORN-DEFAULTS/2.3"
DEFAULTS_FILENAME = "vap_defaults.json"
DEFAULT_TICK_COUNT = 5
DEFAULT_INTERVAL_COUNT = 4
DEFAULT_OUTPUT_FORMATS = ["png", "pdf", "svg", "html"]
SUPPORTED_LAYOUT_PROFILES = {"compact_desktop", "standard", "accessible"}
SUPPORTED_QUALITY_MODES = {"off", "audit"}
SUPPORTED_INVALID_DATE_POLICIES = {"fail", "drop"}
SUPPORTED_DUPLICATE_DATE_POLICIES = {"last", "first", "fail"}
SUPPORTED_OUTLIER_POLICIES = {"none", "report", "clip_iqr"}
SUPPORTED_OUTPUT_FORMATS = {"png", "pdf", "svg", "html"}
SUPPORTED_HTML_RENDERERS = {"plotly", "svg"}
EDITABLE_PROJECT_KEYS = [
    "title",
    "subtitle",
    "source_label",
    "width_inch",
    "panel_height_inch",
    "standard_panel_height_px",
    "dpi",
    "style",
    "context",
    "palette",
    "shared_x",
    "output_directory",
    "output_name",
    "output_formats",
    "watermark",
    "max_rows",
    "render_max_points",
    "max_x_ticks",
    "layout_profile",
    "html_renderer",
]
EDITABLE_CHART_KEYS = [
    "axis_mode",
    "tick_policy",
    "tick_count",
    "missing",
    "y_format",
    "secondary_y_format",
    "palette",
    "alpha",
    "line_width",
    "secondary_alpha",
    "secondary_line_width",
    "height_ratio",
    "price_height_fraction",
    "volume_height_fraction",
    "stack_mode",
    "show_legend",
    "show_zero_line",
    "quality_mode",
    "invalid_date_policy",
    "duplicate_date_policy",
    "outlier_policy",
    "outlier_iqr_multiplier",
    "max_x_ticks",
    "auto_optimize",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "normalized_y",
    "bar_alpha",
    "area_alpha",
    "bar_width_ratio",
    "candle_width_ratio",
    "up_color",
    "down_color",
]


# =============================================================================
# 1. 內建預設值與 Presets
# =============================================================================


def built_in_defaults() -> dict[str, Any]:
    return {
        "schema": DEFAULTS_SCHEMA,
        "version": "2.3.1",
        "policy": "append-only; changes require version and changelog",
        "project": {
            "title": "Veritas Intelligence Analytics",
            "subtitle": "Seaborn Visual Intelligence Generator",
            "source_label": "資料來源",
            "width_inch": 15.5,
            "panel_height_inch": 2.55,
            "standard_panel_height_px": 420,
            "dpi": 300,
            "style": "whitegrid",
            "context": "notebook",
            "palette": "deep",
            "shared_x": True,
            "figure_face_color": "#F5F7FA",
            "axes_face_color": "#FFFFFF",
            "output_directory": "output",
            "output_name": "vap_seaborn_chart",
            "output_formats": list(DEFAULT_OUTPUT_FORMATS),
            "watermark": "理 · VAP",
            "series_colors": {
                "AdjClose": "#4C78A8",
                "Adj Close": "#4C78A8",
                "MA20": "#F28E2B",
                "Volume": "#76B7B2",
                "Foreign": "#59A14F",
                "Trust": "#F28E2B",
                "Dealer": "#8FA6CF"
            },
            "max_rows": 500000,
            "render_max_points": 5000,
            "sample_rows": 5000,
            "date_column": "Date",
            "max_x_ticks": 10,
            "layout_profile": "compact_desktop",
            "html_renderer": "plotly",
        },
        "chart": {
            "axis_mode": "auto",
            "tick_policy": "vap_locked",
            "tick_count": DEFAULT_TICK_COUNT,
            "missing": "none",
            "y_format": "auto",
            "secondary_y_format": "auto",
            "secondary_type": "line",
            "palette": None,
            "alpha": 0.82,
            "line_width": 1.65,
            "secondary_alpha": 0.88,
            "secondary_line_width": 1.35,
            "height_ratio": 1.0,
            "price_height_fraction": 0.75,
            "volume_height_fraction": 0.25,
            "stack_mode": "absolute",
            "show_legend": True,
            "show_zero_line": False,
            "axis_zero_policy": "auto",
            "bar_gap_ratio": 0.22,
            "show_latest_label": False,
            "show_outliers": False,
            "quality_mode": "audit",
            "invalid_date_policy": "fail",
            "duplicate_date_policy": "fail",
            "outlier_policy": "report",
            "outlier_iqr_multiplier": 3.0,
            "max_x_ticks": 10,
            "auto_optimize": True,
            "open": "Adj Open",
            "high": "Adj High",
            "low": "Adj Low",
            "close": "Adj Close",
            "volume": "Volume",
            "normalized_y": [],
            "bar_alpha": 0.75,
            "area_alpha": 0.5,
            "bar_width_ratio": 0.92,
            "candle_width_ratio": 0.88,
            "up_color": "#D62728",
            "down_color": "#2CA02C",
        },
        "presets": {
            "candlestick_volume": {
                "type": "candlestick",
                "axis_mode": "single",
                "missing": "ffill",
                "open": "Adj Open",
                "high": "Adj High",
                "low": "Adj Low",
                "close": "Adj Close",
                "volume": "Volume",
                "y": [],
                "secondary_y": [],
                "y_format": "number",
                "secondary_y_format": "magnitude",
                "secondary_type": "bar",
                "height_ratio": 1.5,
                "price_height_fraction": 0.75,
                "volume_height_fraction": 0.25,
                "bar_alpha": 0.75,
                "bar_width_ratio": 0.92,
                "candle_width_ratio": 0.88,
                "up_color": "#D62728",
                "down_color": "#2CA02C",
                "axis_zero_policy": "exclude",
                "secondary_axis_zero_policy": "include",
                "price_basis": "adjusted",
                "derive_adjusted_prices": False,
            },
            "price": {
                "type": "line",
                "axis_mode": "single",
                "missing": "ffill",
                "y_format": "number",
                "height_ratio": 1.25,
                "palette": "deep",
                "axis_zero_policy": "exclude",
            },
            "price_volume_dual": {
                "type": "line",
                "axis_mode": "dual",
                "missing": "none",
                "y_format": "number",
                "secondary_y_format": "magnitude",
                "secondary_type": "bar",
                "height_ratio": 1.25,
                "secondary_unit": "Volume",
            },
            "volume": {
                "type": "bar",
                "axis_mode": "single",
                "missing": "none",
                "y_format": "magnitude",
                "height_ratio": 0.75,
                "show_legend": False,
                "axis_zero_policy": "include",
            },
            "signed_flow": {
                "type": "bar",
                "axis_mode": "single",
                "missing": "zero",
                "y_format": "magnitude",
                "height_ratio": 1.0,
                "show_zero_line": True,
                "positive_negative_colors": True,
                "axis_zero_policy": "include",
            },
            "composition": {
                "type": "stacked_area",
                "axis_mode": "single",
                "missing": "zero",
                "y_format": "percent",
                "stack_mode": "percent100",
                "height_ratio": 1.0,
                "palette": "Set2",
                "axis_zero_policy": "include",
            },
            "multi_series": {
                "type": "line",
                "axis_mode": "single",
                "missing": "none",
                "y_format": "auto",
                "height_ratio": 1.0,
                "palette": "deep",
            },
            "heatmap": {
                "type": "heatmap",
                "axis_mode": "single",
                "height_ratio": 1.25,
                "cmap": "RdYlGn",
                "show_legend": False,
            },
        },
        "semantic_aliases": {
            "datetime": ["date", "datetime", "time", "timestamp", "trade_date", "日期", "時間"],
            "price": ["adj close", "adjclose", "close", "open", "high", "low", "price", "nav", "價格", "收盤", "淨值"],
            "volume": ["volume", "turnover_volume", "shares", "成交量", "成交股數"],
            "currency": ["amount", "value", "turnover", "turnover_value", "revenue", "sales", "market_cap", "成交值", "金額", "營收", "市值"],
            "percentage": ["pct", "percent", "ratio", "rate", "yield", "return", "yoy", "mom", "比率", "殖利率", "報酬", "年增", "月增"],
            "flow": ["flow", "net_buy", "foreign", "trust", "dealer", "買賣超", "外資", "投信", "自營商"],
            "identifier": ["ticker", "symbol", "code", "id", "股票代碼", "代碼"],
        },
        "changelog": [
            {
                "version": "2.3.1",
                "changes": [
                    "Added chart-aware bounded rendering for large datasets with an explicit audit trail",
                    "Hardened concurrent config, gallery and output writes with cross-process transactions",
                    "Fixed UI context isolation, unsaved-form preview, right-axis controls and output opening",
                    "Corrected decimal tick labels, single-axis contracts and Windows launcher behavior",
                ],
            },
            {
                "version": "2.3.0",
                "changes": [
                    "Added a local single-chart gallery and drag-reorder stack workflow",
                    "Split candlestick price and volume into 75/25 single-axis rows",
                    "Locked interactive standard panel height to 420 px multiples",
                ],
            },
            {
                "version": "2.2.0",
                "changes": [
                    "Added adjusted-OHLC candlestick and volume defaults with Taiwan red-up/green-down colors",
                    "Added Plotly HTML renderer, normalized-series controls and dedicated bar/area opacity defaults",
                    "Kept Seaborn palettes configurable for stacked and static chart color combinations",
                ],
            },
            {
                "version": "2.1.0",
                "changes": [
                    "Added structured data-quality diagnostics and explicit repair policies",
                    "Added configurable layout optimizer parameters",
                    "Kept financial outliers report-only unless users explicitly enable clipping",
                ],
            },
            {
                "version": "2.0.0",
                "changes": [
                    "Centralized editable project and chart defaults",
                    "Added visual presets and semantic aliases",
                    "Added VAP locked five-tick axis policy",
                ],
            }
        ],
    }


# =============================================================================
# 2. 合併、讀取、驗證與寫回
# =============================================================================


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result


def default_defaults_path(base_directory: Path | None = None) -> Path:
    root = base_directory or Path(__file__).resolve().parent
    return root / DEFAULTS_FILENAME


def load_defaults(path: Path | None = None) -> dict[str, Any]:
    defaults_path = path or default_defaults_path()
    built_in = built_in_defaults()
    if not defaults_path.exists():
        return built_in
    with defaults_path.open("r", encoding="utf-8-sig") as handle:
        loaded = json.load(handle)
    if not isinstance(loaded, dict):
        raise ValueError("VAP defaults 根節點必須是 JSON object。")
    merged = deep_merge(built_in, loaded)
    validate_defaults(merged)
    return merged


def save_defaults(path: Path, defaults: dict[str, Any]) -> None:
    validate_defaults(defaults)
    with file_transaction_lock(path):
        atomic_write_json(path, defaults)


def validate_defaults(defaults: dict[str, Any]) -> None:
    if not str(defaults.get("schema", "")).startswith("VIA-VAP-SEABORN-DEFAULTS/"):
        raise ValueError("VAP defaults schema 無效。")
    project = defaults.get("project")
    chart = defaults.get("chart")
    if not isinstance(project, dict) or not isinstance(chart, dict):
        raise ValueError("VAP defaults 必須包含 project 與 chart。")
    if int(project.get("dpi", 0)) < 72:
        raise ValueError("dpi 不可低於 72。")
    canvas_dimensions = [
        float(project.get("width_inch", 0)),
        float(project.get("panel_height_inch", 0)),
    ]
    if any(not math.isfinite(value) or value <= 0 for value in canvas_dimensions):
        raise ValueError("畫布寬高必須大於 0。")
    if int(project.get("standard_panel_height_px", 0)) < 120:
        raise ValueError("standard_panel_height_px 不可低於 120。")
    max_rows = int(project.get("max_rows", 0))
    render_max_points = int(project.get("render_max_points", 0))
    if not 1 <= max_rows <= 500000:
        raise ValueError("max_rows 必須介於 1 與 500000。")
    if not 2 <= render_max_points <= 500000:
        raise ValueError("render_max_points 必須介於 2 與 500000。")
    if int(chart.get("tick_count", 0)) < 2:
        raise ValueError("tick_count 必須至少為 2。")
    if int(project.get("max_x_ticks", 0)) < 2 or int(chart.get("max_x_ticks", 0)) < 2:
        raise ValueError("max_x_ticks 必須至少為 2。")
    if str(project.get("layout_profile", "")) not in SUPPORTED_LAYOUT_PROFILES:
        raise ValueError("layout_profile 無效。")
    if str(project.get("html_renderer", "")) not in SUPPORTED_HTML_RENDERERS:
        raise ValueError("html_renderer 必須是 plotly 或 svg。")
    if str(chart.get("quality_mode", "")) not in SUPPORTED_QUALITY_MODES:
        raise ValueError("quality_mode 無效。")
    if str(chart.get("invalid_date_policy", "")) not in SUPPORTED_INVALID_DATE_POLICIES:
        raise ValueError("invalid_date_policy 無效。")
    if str(chart.get("duplicate_date_policy", "")) not in SUPPORTED_DUPLICATE_DATE_POLICIES:
        raise ValueError("duplicate_date_policy 無效。")
    if str(chart.get("outlier_policy", "")) not in SUPPORTED_OUTLIER_POLICIES:
        raise ValueError("outlier_policy 無效。")
    outlier_multiplier = float(chart.get("outlier_iqr_multiplier", 0))
    if not math.isfinite(outlier_multiplier) or outlier_multiplier <= 0:
        raise ValueError("outlier_iqr_multiplier 必須大於 0。")
    output_formats = [str(value).lower().lstrip(".") for value in project.get("output_formats", [])]
    if not output_formats or any(value not in SUPPORTED_OUTPUT_FORMATS for value in output_formats):
        raise ValueError("output_formats 必須由 png/pdf/svg/html 組成。")
    for alpha_key in ("alpha", "secondary_alpha", "bar_alpha", "area_alpha"):
        alpha_value = float(chart.get(alpha_key, 0))
        if not math.isfinite(alpha_value) or not 0 <= alpha_value <= 1:
            raise ValueError(f"{alpha_key} 必須介於 0 與 1。")
    bar_width_ratio = float(chart.get("bar_width_ratio", 0))
    if not math.isfinite(bar_width_ratio) or not 0 < bar_width_ratio < 1:
        raise ValueError("bar_width_ratio 必須大於 0 且小於 1。")
    candle_width_ratio = float(chart.get("candle_width_ratio", 0))
    if not math.isfinite(candle_width_ratio) or not 0 < candle_width_ratio < 1:
        raise ValueError("candle_width_ratio 必須大於 0 且小於 1。")
    if not isinstance(chart.get("normalized_y"), list):
        raise ValueError("normalized_y 必須是 array。")
    for field_name in ["open", "high", "low", "close", "volume", "up_color", "down_color"]:
        if not isinstance(chart.get(field_name), str):
            raise ValueError(f"{field_name} 必須是字串。")
    positive_values = [
        float(chart.get("line_width", 0)),
        float(chart.get("secondary_line_width", 0)),
        float(chart.get("height_ratio", 0)),
    ]
    if any(not math.isfinite(value) or value <= 0 for value in positive_values):
        raise ValueError("line_width、secondary_line_width 與 height_ratio 必須大於 0。")
    price_fraction = float(chart.get("price_height_fraction", 0.75))
    volume_fraction = float(chart.get("volume_height_fraction", 0.25))
    if (
        not math.isfinite(price_fraction)
        or not math.isfinite(volume_fraction)
        or price_fraction <= 0
        or volume_fraction <= 0
        or abs(price_fraction + volume_fraction - 1.0) > 1e-9
    ):
        raise ValueError("price_height_fraction + volume_height_fraction 必須等於 1。")
    if not isinstance(defaults.get("presets"), dict):
        raise ValueError("presets 必須是 object。")


def project_defaults(defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    source = defaults or load_defaults()
    return deepcopy(source["project"])


def chart_defaults(defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    source = defaults or load_defaults()
    return deepcopy(source["chart"])


def preset_names(defaults: dict[str, Any] | None = None) -> list[str]:
    source = defaults or load_defaults()
    return sorted(str(name) for name in source.get("presets", {}))


def apply_preset(chart: dict[str, Any], preset_name: str, defaults: dict[str, Any] | None = None) -> dict[str, Any]:
    source = defaults or load_defaults()
    preset = source.get("presets", {}).get(preset_name)
    if not isinstance(preset, dict):
        raise KeyError(f"找不到圖表 preset：{preset_name}")
    result = deep_merge(chart_defaults(source), chart)
    result = deep_merge(result, preset)
    result["preset"] = preset_name
    return result
