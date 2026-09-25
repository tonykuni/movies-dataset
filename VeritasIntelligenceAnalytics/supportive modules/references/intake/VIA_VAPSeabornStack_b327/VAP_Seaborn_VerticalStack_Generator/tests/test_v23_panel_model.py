from __future__ import annotations

import unittest

from vap_panel_model import (
    CANDLESTICK_PRICE_FRACTION,
    CANDLESTICK_VOLUME_FRACTION,
    HEIGHT_RATIO_STEP,
    MAX_HEIGHT_RATIO,
    MIN_HEIGHT_RATIO,
    STANDARD_PANEL_HEIGHT_PX,
    axis_tree_rows,
    axis_tree_view_model,
    expand_chart_render_rows,
    expand_stack_render_rows,
    height_ratio_to_pixels,
    normalize_height_ratio,
    reorder_charts_by_drag,
    reorder_items,
    validate_height_ratio,
)


def line_chart(chart_id: str = "price") -> dict[str, object]:
    return {
        "id": chart_id,
        "type": "line",
        "title": "價格",
        "x": "Date",
        "y": ["Adj Close"],
        "secondary_y": [],
        "axis_mode": "single",
        "unit": "TWD",
        "y_format": "number",
        "tick_count": 5,
        "line_width": 1.75,
        "alpha": 0.8,
        "height_ratio": 1.0,
        "show_legend": True,
    }


def candlestick_chart() -> dict[str, object]:
    return {
        "id": "adjusted_ohlcv",
        "type": "candlestick",
        "title": "還原權息價量",
        "x": "Date",
        "open": "Adj Open",
        "high": "Adj High",
        "low": "Adj Low",
        "close": "Adj Close",
        "volume": "Volume",
        "y": ["Adj Close"],
        # Legacy v2.2 data may still describe volume as the right axis.
        "secondary_y": ["Volume"],
        "axis_mode": "dual",
        "unit": "TWD",
        "secondary_unit": "shares",
        "y_format": "number",
        "secondary_y_format": "magnitude",
        "secondary_axis_zero_policy": "include",
        "tick_count": 6,
        "line_width": 1.65,
        "alpha": 0.82,
        "bar_alpha": 0.75,
        "area_alpha": 0.5,
        "height_ratio": 2.0,
        "missing": "interpolate",
        "normalized_y": ["Adj Close"],
    }


class HeightModelTests(unittest.TestCase):
    def test_standard_height_constants_are_quarter_step_based(self) -> None:
        self.assertEqual(STANDARD_PANEL_HEIGHT_PX, 420)
        self.assertEqual(MIN_HEIGHT_RATIO, 0.25)
        self.assertEqual(MAX_HEIGHT_RATIO, 4.0)
        self.assertEqual(HEIGHT_RATIO_STEP, 0.25)

    def test_validate_accepts_supported_boundaries_and_steps(self) -> None:
        self.assertEqual(validate_height_ratio("0.25"), 0.25)
        self.assertEqual(validate_height_ratio(1.5), 1.5)
        self.assertEqual(validate_height_ratio(4), 4.0)

    def test_validate_rejects_bad_range_step_and_nonfinite_values(self) -> None:
        for value in (0, 0.1, 4.25, 1.1, True, "", float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    validate_height_ratio(value)

    def test_normalize_uses_half_up_quarter_steps_and_clamps(self) -> None:
        self.assertEqual(normalize_height_ratio(1.12), 1.0)
        self.assertEqual(normalize_height_ratio(1.125), 1.25)
        self.assertEqual(normalize_height_ratio(1.38), 1.5)
        self.assertEqual(normalize_height_ratio(-99), 0.25)
        self.assertEqual(normalize_height_ratio(99), 4.0)
        self.assertEqual(normalize_height_ratio("", default=1.75), 1.75)
        with self.assertRaises(ValueError):
            normalize_height_ratio(4.1, clamp=False)

    def test_height_ratio_converts_against_420px_standard(self) -> None:
        self.assertEqual(height_ratio_to_pixels(1), 420)
        self.assertEqual(height_ratio_to_pixels(1.5), 630)
        self.assertEqual(height_ratio_to_pixels(0.25), 105)
        # Non-strict rendering path snaps values received from an older config.
        self.assertEqual(height_ratio_to_pixels(1.1), 420)
        with self.assertRaises(ValueError):
            height_ratio_to_pixels(1.1, strict=True)
        with self.assertRaises(ValueError):
            height_ratio_to_pixels(1, standard_height_px=0)


class RenderRowExpansionTests(unittest.TestCase):
    def test_ordinary_chart_expands_to_one_row_and_does_not_mutate_input(self) -> None:
        chart = line_chart()
        original = dict(chart)
        rows = expand_chart_render_rows(chart)
        self.assertEqual(chart, original)
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row["id"], "price")
        self.assertEqual(row["render_id"], "price")
        self.assertEqual(row["logical_chart_id"], "price")
        self.assertEqual(row["render_role"], "main")
        self.assertEqual(row["height_fraction"], 1.0)
        self.assertEqual(row["height_ratio"], 1.0)

    def test_candlestick_expands_to_price_and_volume_single_axis_rows(self) -> None:
        chart = candlestick_chart()
        original = dict(chart)
        rows = expand_chart_render_rows(chart)
        self.assertEqual(chart, original)
        self.assertEqual(len(rows), 2)
        price, volume = rows

        self.assertEqual(price["id"], chart["id"])
        self.assertEqual(volume["id"], chart["id"])
        self.assertEqual(price["logical_chart_id"], chart["id"])
        self.assertEqual(volume["logical_chart_id"], chart["id"])
        self.assertNotEqual(price["render_id"], volume["render_id"])
        self.assertEqual(price["render_role"], "price")
        self.assertEqual(volume["render_role"], "volume")
        self.assertEqual(price["axis_mode"], "single")
        self.assertEqual(volume["axis_mode"], "single")
        self.assertEqual(price["secondary_y"], [])
        self.assertEqual(volume["secondary_y"], [])

        self.assertEqual(price["height_fraction"], CANDLESTICK_PRICE_FRACTION)
        self.assertEqual(volume["height_fraction"], CANDLESTICK_VOLUME_FRACTION)
        self.assertEqual(price["height_ratio"], 1.5)
        self.assertEqual(volume["height_ratio"], 0.5)
        self.assertAlmostEqual(price["height_ratio"] + volume["height_ratio"], 2.0)

        self.assertEqual(price["missing"], "ffill")
        self.assertEqual(price["price_missing_policy"], "ffill")
        self.assertEqual(volume["missing"], "none")
        self.assertEqual(volume["volume_missing_policy"], "none")
        self.assertFalse(volume["fill_allowed"])
        self.assertEqual(volume["y"], ["Volume"])
        self.assertEqual(volume["unit"], "shares")
        self.assertEqual(volume["y_format"], "magnitude")
        self.assertEqual(volume["normalized_y"], [])

    def test_render_rows_are_deep_copies(self) -> None:
        chart = line_chart()
        rows = expand_chart_render_rows(chart)
        rows[0]["y"].append("MA20")
        self.assertEqual(chart["y"], ["Adj Close"])

    def test_candlestick_requires_volume_and_ohlc_mapping(self) -> None:
        chart = candlestick_chart()
        chart["volume"] = ""
        with self.assertRaisesRegex(ValueError, "volume"):
            expand_chart_render_rows(chart)
        chart = candlestick_chart()
        for key in ("open", "high", "low", "close"):
            chart[key] = ""
        with self.assertRaisesRegex(ValueError, "OHLC"):
            expand_chart_render_rows(chart)

    def test_stack_expansion_preserves_logical_order(self) -> None:
        rows = expand_stack_render_rows(
            [line_chart("before"), candlestick_chart(), line_chart("after")]
        )
        self.assertEqual(
            [row["render_id"] for row in rows],
            ["before", "adjusted_ohlcv::price", "adjusted_ohlcv::volume", "after"],
        )
        with self.assertRaisesRegex(ValueError, "重複"):
            expand_stack_render_rows([line_chart("same"), line_chart("same")])


class AxisTreeTests(unittest.TestCase):
    def test_flat_single_axis_schema_becomes_three_branches(self) -> None:
        tree = axis_tree_view_model(line_chart())
        self.assertEqual(list(tree), ["general", "left_axis", "right_axis"])
        self.assertEqual(tree["general"]["height_ratio"], 1.0)
        self.assertEqual(tree["general"]["standard_height_px"], 420)
        self.assertTrue(tree["left_axis"]["enabled"])
        self.assertEqual(tree["left_axis"]["series"], ["Adj Close"])
        self.assertEqual(tree["left_axis"]["type"], "line")
        self.assertEqual(tree["left_axis"]["unit"], "TWD")
        self.assertEqual(tree["left_axis"]["format"], "number")
        self.assertEqual(tree["left_axis"]["tick_count"], 5)
        self.assertEqual(tree["left_axis"]["line_width"], 1.75)
        self.assertEqual(tree["left_axis"]["alpha"], 0.8)
        self.assertFalse(tree["right_axis"]["enabled"])

    def test_flat_dual_axis_uses_secondary_type_unit_format_and_opacity(self) -> None:
        chart = line_chart()
        chart.update(
            {
                "axis_mode": "dual",
                "secondary_y": ["Volume"],
                "secondary_type": "bar",
                "secondary_unit": "shares",
                "secondary_y_format": "magnitude",
                "bar_alpha": 0.75,
            }
        )
        tree = axis_tree_view_model(chart)
        self.assertTrue(tree["right_axis"]["enabled"])
        self.assertEqual(tree["right_axis"]["series"], ["Volume"])
        self.assertEqual(tree["right_axis"]["type"], "bar")
        self.assertEqual(tree["right_axis"]["unit"], "shares")
        self.assertEqual(tree["right_axis"]["format"], "magnitude")
        self.assertEqual(tree["right_axis"]["alpha"], 0.75)

    def test_candlestick_legacy_dual_mapping_is_shown_as_two_single_axis_rows(self) -> None:
        tree = axis_tree_view_model(candlestick_chart())
        self.assertEqual(tree["general"]["render_rows"], ["price", "volume"])
        self.assertEqual(tree["general"]["price_fraction"], 0.75)
        self.assertEqual(tree["general"]["volume_fraction"], 0.25)
        self.assertEqual(tree["general"]["volume_series"], ["Volume"])
        self.assertEqual(
            tree["left_axis"]["series"],
            ["Adj Open", "Adj High", "Adj Low", "Adj Close"],
        )
        self.assertFalse(tree["right_axis"]["enabled"])
        self.assertEqual(tree["right_axis"]["series"], [])

    def test_nested_axis_overrides_flat_schema_when_present(self) -> None:
        chart = line_chart()
        chart["left_axis"] = {
            "series": ["MA20"],
            "type": "step",
            "unit": "points",
            "format": "comma",
            "tick_count": 7,
            "line_width": 2.5,
            "alpha": 0.6,
        }
        chart["right_axis"] = {
            "enabled": True,
            "series": ["Turnover"],
            "type": "area",
            "unit": "TWD",
            "format": "magnitude",
            "tick_count": 7,
            "line_width": 1.25,
            "alpha": 0.5,
        }
        tree = axis_tree_view_model(chart)
        self.assertEqual(tree["left_axis"]["series"], ["MA20"])
        self.assertEqual(tree["left_axis"]["type"], "step")
        self.assertEqual(tree["left_axis"]["tick_count"], 7)
        self.assertEqual(tree["left_axis"]["line_width"], 2.5)
        self.assertTrue(tree["right_axis"]["enabled"])
        self.assertEqual(tree["right_axis"]["series"], ["Turnover"])
        self.assertEqual(tree["right_axis"]["alpha"], 0.5)

    def test_tree_rows_have_explicit_parent_paths(self) -> None:
        rows = axis_tree_rows(line_chart())
        roots = [row for row in rows if row["parent"] == ""]
        self.assertEqual([row["path"] for row in roots], ["general", "left_axis", "right_axis"])
        left_series = next(row for row in rows if row["path"] == "left_axis.series")
        self.assertEqual(left_series["parent"], "left_axis")
        self.assertEqual(left_series["value"], ["Adj Close"])


class DragReorderTests(unittest.TestCase):
    def test_dict_payload_moves_before_without_mutation_or_reconstruction(self) -> None:
        first = {"id": "a", "payload": {"value": 1}}
        second = {"id": "b", "payload": {"value": 2}}
        third = {"id": "c", "payload": {"value": 3}}
        original = [first, second, third]
        result = reorder_items(original, "c", "a")
        self.assertEqual([item["id"] for item in result], ["c", "a", "b"])
        self.assertEqual([item["id"] for item in original], ["a", "b", "c"])
        self.assertIs(result[0], third)
        self.assertIs(result[1], first)

    def test_move_after_handles_downward_target_without_off_by_one(self) -> None:
        items = [{"id": value} for value in "abcd"]
        result = reorder_charts_by_drag(items, "a", "c", "after")
        self.assertEqual([item["id"] for item in result], ["b", "c", "a", "d"])
        result = reorder_charts_by_drag(items, "d", "b", "after")
        self.assertEqual([item["id"] for item in result], ["a", "b", "d", "c"])

    def test_string_ids_and_custom_mapping_key_are_supported(self) -> None:
        self.assertEqual(reorder_items(["a", "b", "c"], "a", "c", "after"), ["b", "c", "a"])
        payloads = [{"key": "x"}, {"key": "y"}]
        self.assertEqual(
            [item["key"] for item in reorder_items(payloads, "y", "x", id_key="key")],
            ["y", "x"],
        )

    def test_dropping_on_self_is_a_noop_copy(self) -> None:
        items = ["a", "b"]
        result = reorder_items(items, "a", "a")
        self.assertEqual(result, items)
        self.assertIsNot(result, items)

    def test_invalid_drag_inputs_fail_loudly(self) -> None:
        cases = [
            (["a", "a"], "a", "a", "before"),
            (["a", "b"], "missing", "a", "before"),
            (["a", "b"], "a", "missing", "before"),
            (["a", "b"], "a", "b", "middle"),
            ([{"name": "a"}], "a", "a", "before"),
            ([1, 2], "1", "2", "before"),
        ]
        for items, dragged, target, position in cases:
            with self.subTest(items=items, dragged=dragged, target=target, position=position):
                with self.assertRaises(ValueError):
                    reorder_items(items, dragged, target, position)


if __name__ == "__main__":
    unittest.main()
