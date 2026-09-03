from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from vap_seaborn_stack_ui import (
    DEFAULT_STANDARD_HEIGHT_PX,
    axis_tree_rows,
    chart_form_field_mapping,
    chart_form_values_from_spec,
    chart_library_path_for_config,
    chart_spec_from_form_values,
    config_chart_rows,
    duplicate_chart_for_stack,
    reorder_chart_items,
    standard_height_pixels,
)


class VAPV23UIWorkflowTests(unittest.TestCase):
    def test_standard_height_is_a_visible_420px_multiple(self) -> None:
        self.assertEqual(DEFAULT_STANDARD_HEIGHT_PX, 420)
        self.assertEqual(standard_height_pixels(1), 420)
        self.assertEqual(standard_height_pixels("1.5"), 630)
        with self.assertRaisesRegex(ValueError, "高度倍數"):
            standard_height_pixels(0)

    def test_form_snaps_height_to_quarter_step(self) -> None:
        values = chart_form_values_from_spec(
            {"id": "height", "type": "line", "x": "Date", "y": ["A"], "height_ratio": 1.13},
            defaults={},
        )
        self.assertEqual(chart_spec_from_form_values(values)["height_ratio"], 1.25)

    def test_left_axis_style_fields_round_trip_through_form(self) -> None:
        mapping = chart_form_field_mapping()
        self.assertEqual(mapping["line_width"], "line_width")
        self.assertEqual(mapping["alpha"], "alpha")
        source = {
            "id": "price",
            "type": "line",
            "title": "Price",
            "x": "Date",
            "y": ["Adj Close"],
            "line_width": 2.25,
            "alpha": 0.68,
            "height_ratio": 1.5,
        }
        rebuilt = chart_spec_from_form_values(chart_form_values_from_spec(source, defaults={}))
        self.assertAlmostEqual(rebuilt["line_width"], 2.25)
        self.assertAlmostEqual(rebuilt["alpha"], 0.68)
        self.assertAlmostEqual(rebuilt["height_ratio"], 1.5)

    def test_axis_tree_has_clear_left_and_optional_right_branches(self) -> None:
        rows = axis_tree_rows(
            {
                "chart_type": "line",
                "height_ratio": 1.5,
                "y_format": "decimal",
                "line_width": 2.0,
                "alpha": 0.75,
                "secondary_y": "Volume",
                "secondary_type": "bar",
            }
        )
        by_id = {row["id"]: row for row in rows}
        self.assertEqual({"general", "left_axis", "right_axis", "advanced"}, set(by_id))
        self.assertIn("2.0", by_id["left_axis"]["summary"])
        self.assertIn("bar", by_id["right_axis"]["summary"])
        self.assertIn("1.5×420px", by_id["general"]["summary"])

    def test_duplicate_chart_uses_collision_free_id_and_deep_copy(self) -> None:
        source = {"id": "panel", "title": "Panel", "type": "line", "y": ["A"]}
        duplicate = duplicate_chart_for_stack(source, {"panel", "panel_copy", "panel_copy_2"})
        self.assertEqual(duplicate["id"], "panel_copy_3")
        self.assertEqual(duplicate["title"], "Panel 副本")
        duplicate["y"].append("B")
        self.assertEqual(source["y"], ["A"])

    def test_drag_reorder_supports_before_and_after(self) -> None:
        charts = [{"id": "a"}, {"id": "b"}, {"id": "c"}]
        before = reorder_chart_items(charts, "c", "a", "before")
        after = reorder_chart_items(charts, "a", "b", "after")
        self.assertEqual([item["id"] for item in before], ["c", "a", "b"])
        self.assertEqual([item["id"] for item in after], ["b", "a", "c"])
        self.assertEqual([item["id"] for item in charts], ["a", "b", "c"])

    def test_library_path_is_portable_beside_stack_config(self) -> None:
        path = chart_library_path_for_config("examples/demo_stack.json")
        self.assertEqual(path.name, "vap_chart_library.json")
        self.assertEqual(path.parent.name, "examples")

    def test_stack_rows_show_standard_height_multiple(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "stack.json"
            config_path.write_text(
                json.dumps(
                    {
                        "charts": [
                            {
                                "id": "price",
                                "type": "line",
                                "axis_mode": "single",
                                "height_ratio": 1.5,
                                "title": "Price",
                            }
                        ]
                    }
                ),
                encoding="utf-8",
            )
            rows = config_chart_rows(config_path)
        self.assertEqual(rows[0]["height"], "1.5×")


if __name__ == "__main__":
    unittest.main()
