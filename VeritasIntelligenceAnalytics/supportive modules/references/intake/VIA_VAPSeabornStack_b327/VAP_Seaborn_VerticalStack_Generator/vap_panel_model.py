"""Pure panel-model helpers shared by the VAP stack editor and renderers.

The module deliberately contains no Tk, Matplotlib, Plotly, or file-system
code.  It turns a logical chart configuration into render-row metadata,
builds the tree-shaped axis view consumed by the editor, and implements the
drag/drop ordering rule in a way that is straightforward to unit test.

``height_ratio`` remains the persisted, backwards-compatible field name.  In
v2.3 it means a multiple of a 420 px standard panel height and is edited in
quarter-step increments.
"""

from __future__ import annotations

import math
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, TypeVar


STANDARD_PANEL_HEIGHT_PX = 420
MIN_HEIGHT_RATIO = 0.25
MAX_HEIGHT_RATIO = 4.0
HEIGHT_RATIO_STEP = 0.25
CANDLESTICK_PRICE_FRACTION = 0.75
CANDLESTICK_VOLUME_FRACTION = 0.25

_MIN_HEIGHT_DECIMAL = Decimal("0.25")
_MAX_HEIGHT_DECIMAL = Decimal("4.00")
_HEIGHT_STEP_DECIMAL = Decimal("0.25")

T = TypeVar("T")


def _height_decimal(value: Any, field_name: str = "height_ratio") -> Decimal:
    """Coerce a user-entered height value to a finite decimal."""

    if isinstance(value, bool):
        raise ValueError(f"{field_name} 必須是數值，不可為布林值。")
    if value is None or (isinstance(value, str) and not value.strip()):
        raise ValueError(f"{field_name} 不可為空白。")
    try:
        result = Decimal(str(value).strip())
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError(f"{field_name} 必須是數值。") from exc
    if not result.is_finite():
        raise ValueError(f"{field_name} 必須是有限數值。")
    return result


def validate_height_ratio(value: Any) -> float:
    """Validate and return a standard-height multiple without changing it.

    Valid persisted values are 0.25 through 4.0 inclusive and must land on a
    0.25 increment.  Use :func:`normalize_height_ratio` for free-form UI input
    that should be snapped to the nearest supported value first.
    """

    ratio = _height_decimal(value)
    if not _MIN_HEIGHT_DECIMAL <= ratio <= _MAX_HEIGHT_DECIMAL:
        raise ValueError(
            f"height_ratio 必須介於 {MIN_HEIGHT_RATIO:g} 與 {MAX_HEIGHT_RATIO:g}。"
        )
    if (ratio - _MIN_HEIGHT_DECIMAL) % _HEIGHT_STEP_DECIMAL != 0:
        raise ValueError(f"height_ratio 必須以 {HEIGHT_RATIO_STEP:g} 為步進。")
    return float(ratio)


def normalize_height_ratio(
    value: Any,
    *,
    default: Any = 1.0,
    clamp: bool = True,
) -> float:
    """Snap a free-form value to the nearest supported quarter-step.

    ``None`` and blank strings use ``default``.  By default the result is also
    clamped to the supported 0.25–4.0 range, which makes it suitable for a
    spinbox or dropdown.  Set ``clamp=False`` when out-of-range values should
    be reported instead.
    """

    raw_value = default if value is None or (isinstance(value, str) and not value.strip()) else value
    ratio = _height_decimal(raw_value)
    if not clamp and not _MIN_HEIGHT_DECIMAL <= ratio <= _MAX_HEIGHT_DECIMAL:
        raise ValueError(
            f"height_ratio 必須介於 {MIN_HEIGHT_RATIO:g} 與 {MAX_HEIGHT_RATIO:g}。"
        )
    step_count = (ratio / _HEIGHT_STEP_DECIMAL).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    normalized = step_count * _HEIGHT_STEP_DECIMAL
    if clamp:
        normalized = min(_MAX_HEIGHT_DECIMAL, max(_MIN_HEIGHT_DECIMAL, normalized))
    return validate_height_ratio(normalized)


def height_ratio_to_pixels(
    value: Any,
    *,
    standard_height_px: int = STANDARD_PANEL_HEIGHT_PX,
    strict: bool = False,
) -> int:
    """Convert a standard-height multiple to integral pixels.

    The default path normalizes UI-friendly input.  ``strict=True`` rejects a
    value that is not already on an allowed quarter-step.
    """

    if isinstance(standard_height_px, bool) or int(standard_height_px) <= 0:
        raise ValueError("standard_height_px 必須是大於 0 的整數。")
    if isinstance(standard_height_px, float) and not standard_height_px.is_integer():
        raise ValueError("standard_height_px 必須是整數。")
    ratio = validate_height_ratio(value) if strict else normalize_height_ratio(value)
    return int(round(int(standard_height_px) * ratio))


def _chart_id(chart: Mapping[str, Any]) -> str:
    chart_id = chart.get("id")
    if not isinstance(chart_id, str) or not chart_id.strip():
        raise ValueError("每張 logical chart 都必須有非空白字串 id。")
    return chart_id.strip()


def _unique_nonempty(values: Iterable[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value).strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _candlestick_price_series(chart: Mapping[str, Any]) -> list[str]:
    return _unique_nonempty(chart.get(key, "") for key in ("open", "high", "low", "close"))


def expand_chart_render_rows(chart: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Expand one logical chart into one or two physical render rows.

    Ordinary charts produce one row.  A candlestick chart produces a price
    row and a volume row with 75/25 height weights.  Both candlestick rows are
    explicitly single-axis.  Price gaps use forward-fill while the volume row
    is marked as non-fillable and retains missing values.

    The logical ``id`` is preserved on every row.  ``render_id`` is the unique
    physical-row identifier and ``logical_chart_id`` links it back to the
    saved chart configuration.
    """

    if not isinstance(chart, Mapping):
        raise ValueError("chart 必須是 mapping。")
    logical_id = _chart_id(chart)
    logical_height = normalize_height_ratio(chart.get("height_ratio", 1.0))
    source = deepcopy(dict(chart))
    source["id"] = logical_id
    source["height_ratio"] = logical_height
    chart_type = str(source.get("type", "")).strip().lower()

    if chart_type != "candlestick":
        source.update(
            {
                "render_id": logical_id,
                "logical_chart_id": logical_id,
                "logical_height_ratio": logical_height,
                "render_role": "main",
                "render_type": chart_type or "chart",
                "height_fraction": 1.0,
            }
        )
        return [source]

    volume_column = str(source.get("volume", "")).strip()
    if not volume_column:
        raise ValueError("candlestick logical chart 必須設定 volume 欄位。")
    close_column = str(source.get("close", "")).strip()
    price_series = _candlestick_price_series(source)
    if not price_series:
        raise ValueError("candlestick logical chart 必須設定 OHLC 欄位。")

    price_row = deepcopy(source)
    price_row.update(
        {
            "render_id": f"{logical_id}::price",
            "logical_chart_id": logical_id,
            "logical_height_ratio": logical_height,
            "render_role": "price",
            "render_type": "candlestick_price",
            "height_fraction": CANDLESTICK_PRICE_FRACTION,
            "height_ratio": logical_height * CANDLESTICK_PRICE_FRACTION,
            "axis_mode": "single",
            "y": [close_column] if close_column else price_series,
            "secondary_y": [],
            "missing": "ffill",
            "price_missing_policy": "ffill",
            "volume_missing_policy": "none",
        }
    )

    volume_row = deepcopy(source)
    title = str(source.get("title", "")).strip()
    volume_row.update(
        {
            "render_id": f"{logical_id}::volume",
            "logical_chart_id": logical_id,
            "logical_height_ratio": logical_height,
            "render_role": "volume",
            "render_type": "candlestick_volume",
            "height_fraction": CANDLESTICK_VOLUME_FRACTION,
            "height_ratio": logical_height * CANDLESTICK_VOLUME_FRACTION,
            "axis_mode": "single",
            "title": f"{title} · 成交量" if title else "成交量",
            "y": [volume_column],
            "secondary_y": [],
            "unit": str(source.get("secondary_unit", "")).strip() or "Volume",
            "y_format": source.get("secondary_y_format", "magnitude"),
            "axis_zero_policy": source.get("secondary_axis_zero_policy", "include"),
            "missing": "none",
            "price_missing_policy": "ffill",
            "volume_missing_policy": "none",
            "fill_allowed": False,
            "show_legend": False,
            "normalized_y": [],
        }
    )
    return [price_row, volume_row]


def expand_stack_render_rows(charts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Expand a logical chart stack while preserving logical order."""

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for chart in charts:
        logical_id = _chart_id(chart)
        if logical_id in seen_ids:
            raise ValueError(f"logical chart id 重複：{logical_id!r}。")
        seen_ids.add(logical_id)
        rows.extend(expand_chart_render_rows(chart))
    return rows


def axis_tree_view_model(chart: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    """Build a tree-shaped editor model from the current flat chart schema.

    Future nested ``left_axis`` / ``right_axis`` mappings may override the
    corresponding flat fields, so the view model can bridge the v2.2 flat
    schema and a later persisted tree schema without duplicating UI logic.
    Candlestick+volume is represented as two single-axis render rows; its
    legacy right-axis volume mapping therefore does not enable ``right_axis``.
    """

    if not isinstance(chart, Mapping):
        raise ValueError("chart 必須是 mapping。")
    chart_type = str(chart.get("type", "line")).strip().lower() or "line"
    left_override = chart.get("left_axis") if isinstance(chart.get("left_axis"), Mapping) else {}
    right_override = chart.get("right_axis") if isinstance(chart.get("right_axis"), Mapping) else {}

    def left_value(key: str, fallback: Any) -> Any:
        return left_override.get(key, fallback)

    def right_value(key: str, fallback: Any) -> Any:
        return right_override.get(key, fallback)

    if chart_type == "candlestick":
        left_series = _candlestick_price_series(chart)
    else:
        left_series = _unique_nonempty(chart.get("y", []) if not isinstance(chart.get("y"), str) else chart.get("y", "").split(","))
    left_series = _unique_nonempty(left_value("series", left_series))

    raw_secondary = chart.get("secondary_y", [])
    if isinstance(raw_secondary, str):
        raw_secondary = raw_secondary.split(",")
    right_series = _unique_nonempty(right_value("series", raw_secondary))
    axis_mode = str(chart.get("axis_mode", "auto")).strip().lower()
    right_enabled_default = chart_type != "candlestick" and (axis_mode == "dual" or bool(right_series))
    secondary_type = str(right_value("type", chart.get("secondary_type", "line"))).strip().lower() or "line"
    secondary_alpha_default = chart.get("alpha", 0.82)
    if secondary_type == "bar":
        secondary_alpha_default = chart.get("bar_alpha", 0.75)
    elif secondary_type in {"area", "stacked_area", "stacked_area_100"}:
        secondary_alpha_default = chart.get("area_alpha", 0.5)

    general: dict[str, Any] = {
        "label": "一般",
        "id": str(chart.get("id", "")),
        "title": str(chart.get("title", "")),
        "type": chart_type,
        "enabled": bool(chart.get("enabled", True)),
        "height_ratio": normalize_height_ratio(chart.get("height_ratio", 1.0)),
        "standard_height_px": STANDARD_PANEL_HEIGHT_PX,
        "palette": chart.get("palette"),
        "show_legend": bool(chart.get("show_legend", True)),
    }
    if chart_type == "candlestick":
        general.update(
            {
                "render_rows": ["price", "volume"],
                "price_fraction": CANDLESTICK_PRICE_FRACTION,
                "volume_fraction": CANDLESTICK_VOLUME_FRACTION,
                "volume_series": [str(chart.get("volume", "")).strip()],
            }
        )

    left_axis: dict[str, Any] = {
        "label": "左軸",
        "enabled": bool(left_value("enabled", True)),
        "series": left_series,
        "type": str(left_value("type", chart_type)),
        "unit": str(left_value("unit", chart.get("unit", ""))),
        "format": str(left_value("format", chart.get("y_format", "auto"))),
        "tick_count": int(left_value("tick_count", chart.get("tick_count", 5))),
        "line_width": float(left_value("line_width", chart.get("line_width", 1.65))),
        "alpha": float(left_value("alpha", chart.get("alpha", 0.82))),
    }
    right_axis: dict[str, Any] = {
        "label": "右軸",
        "enabled": bool(right_value("enabled", right_enabled_default)),
        "series": right_series if chart_type != "candlestick" else [],
        "type": secondary_type,
        "unit": str(right_value("unit", chart.get("secondary_unit", ""))),
        "format": str(right_value("format", chart.get("secondary_y_format", "auto"))),
        "tick_count": int(right_value("tick_count", chart.get("tick_count", 5))),
        "line_width": float(right_value("line_width", chart.get("secondary_line_width", chart.get("line_width", 1.65)))),
        "alpha": float(right_value("alpha", chart.get("secondary_alpha", secondary_alpha_default))),
    }
    if chart_type == "candlestick":
        right_axis["enabled"] = False
    return {"general": general, "left_axis": left_axis, "right_axis": right_axis}


def axis_tree_rows(chart: Mapping[str, Any]) -> list[dict[str, Any]]:
    """Flatten :func:`axis_tree_view_model` into rows ready for ``Treeview``."""

    tree = axis_tree_view_model(chart)
    rows: list[dict[str, Any]] = []
    for branch_key in ("general", "left_axis", "right_axis"):
        branch = tree[branch_key]
        rows.append(
            {
                "path": branch_key,
                "parent": "",
                "key": branch_key,
                "label": branch["label"],
                "value": "",
            }
        )
        for key, value in branch.items():
            if key == "label":
                continue
            rows.append(
                {
                    "path": f"{branch_key}.{key}",
                    "parent": branch_key,
                    "key": key,
                    "label": key,
                    "value": value,
                }
            )
    return rows


def _item_id(item: Any, id_key: str) -> str:
    if isinstance(item, str):
        value = item
    elif isinstance(item, Mapping):
        value = item.get(id_key)
    else:
        raise ValueError("items 只支援 id 字串或 mapping payload。")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"每個 item 都必須有非空白字串 {id_key!r}。")
    return value.strip()


def reorder_items(
    items: Sequence[T],
    dragged_id: str,
    target_id: str,
    position: str = "before",
    *,
    id_key: str = "id",
) -> list[T]:
    """Return drag/drop order without mutating the sequence or its payloads.

    ``items`` may contain id strings or mapping payloads.  The returned list
    reuses the original payload objects; only their order changes.  ``before``
    and ``after`` are interpreted relative to the target *after* removing the
    dragged item, avoiding the common off-by-one bug when moving downward.
    """

    if position not in {"before", "after"}:
        raise ValueError("position 只支援 'before' 或 'after'。")
    if not isinstance(dragged_id, str) or not dragged_id.strip():
        raise ValueError("dragged_id 必須是非空白字串。")
    if not isinstance(target_id, str) or not target_id.strip():
        raise ValueError("target_id 必須是非空白字串。")
    if not isinstance(id_key, str) or not id_key.strip():
        raise ValueError("id_key 必須是非空白字串。")

    original = list(items)
    ids = [_item_id(item, id_key) for item in original]
    duplicates = sorted({item_id for item_id in ids if ids.count(item_id) > 1})
    if duplicates:
        raise ValueError(f"item id 不可重複：{', '.join(duplicates)}。")

    dragged = dragged_id.strip()
    target = target_id.strip()
    if dragged not in ids:
        raise ValueError(f"找不到 dragged_id：{dragged!r}。")
    if target not in ids:
        raise ValueError(f"找不到 target_id：{target!r}。")
    if dragged == target:
        return original

    dragged_index = ids.index(dragged)
    payload = original.pop(dragged_index)
    remaining_ids = ids.copy()
    remaining_ids.pop(dragged_index)
    target_index = remaining_ids.index(target)
    insert_index = target_index + (1 if position == "after" else 0)
    original.insert(insert_index, payload)
    return original


def reorder_charts_by_drag(
    charts: Sequence[T],
    dragged_id: str,
    target_id: str,
    position: str = "before",
) -> list[T]:
    """Chart-specific alias for :func:`reorder_items`."""

    return reorder_items(charts, dragged_id, target_id, position, id_key="id")


__all__ = [
    "STANDARD_PANEL_HEIGHT_PX",
    "MIN_HEIGHT_RATIO",
    "MAX_HEIGHT_RATIO",
    "HEIGHT_RATIO_STEP",
    "CANDLESTICK_PRICE_FRACTION",
    "CANDLESTICK_VOLUME_FRACTION",
    "validate_height_ratio",
    "normalize_height_ratio",
    "height_ratio_to_pixels",
    "expand_chart_render_rows",
    "expand_stack_render_rows",
    "axis_tree_view_model",
    "axis_tree_rows",
    "reorder_items",
    "reorder_charts_by_drag",
]
