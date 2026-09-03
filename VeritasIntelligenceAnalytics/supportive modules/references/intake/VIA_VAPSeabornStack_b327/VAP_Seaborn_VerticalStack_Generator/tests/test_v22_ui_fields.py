from __future__ import annotations

import unittest

from vap_seaborn_stack_generator import SUPPORTED_CHART_TYPES
from vap_seaborn_stack_ui import (
    PALETTE_CHOICES,
    chart_form_field_mapping,
    chart_form_values_from_spec,
    chart_spec_from_form_values,
    chart_type_choices,
)


class VAPV22UIFieldTests(unittest.TestCase):
    def test_chart_type_choices_follow_generator_ssot(self) -> None:
        self.assertEqual(chart_type_choices(), sorted(SUPPORTED_CHART_TYPES))
        self.assertIn("candlestick", chart_type_choices())

    def test_advanced_chart_fields_have_complete_json_mapping(self) -> None:
        mapping = chart_form_field_mapping()
        expected = {
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
        }
        self.assertTrue(expected.issubset(mapping))
        for key in expected:
            self.assertEqual(mapping[key], key)

    def test_candlestick_form_round_trip_preserves_all_advanced_fields(self) -> None:
        source = {
            "id": "adjusted_price_volume",
            "type": "candlestick",
            "title": "Adjusted OHLCV",
            "x": "Date",
            "y": [],
            "secondary_y": [],
            "axis_mode": "dual",
            "secondary_unit": "Volume",
            "missing": "ffill",
            "open": "Adj Open",
            "high": "Adj High",
            "low": "Adj Low",
            "close": "Adj Close",
            "volume": "Volume",
            "normalized_y": ["Normalized Momentum"],
            "bar_alpha": 0.75,
            "area_alpha": 0.5,
            "bar_width_ratio": 0.92,
            "candle_width_ratio": 0.88,
            "up_color": "#D62728",
            "down_color": "#2CA02C",
        }
        snapshot = chart_form_values_from_spec(source, defaults={})
        rebuilt = chart_spec_from_form_values(snapshot)

        for key in ("open", "high", "low", "close", "volume", "up_color", "down_color"):
            self.assertEqual(rebuilt[key], source[key])
        self.assertEqual(rebuilt["normalized_y"], source["normalized_y"])
        self.assertEqual(rebuilt["y"], [])
        self.assertEqual(rebuilt["secondary_y"], [])
        self.assertEqual(rebuilt["axis_mode"], "dual")
        self.assertEqual(rebuilt["secondary_unit"], "Volume")
        self.assertEqual(rebuilt["missing"], "ffill")
        self.assertEqual(rebuilt["price_basis"], "adjusted")
        self.assertAlmostEqual(rebuilt["bar_alpha"], 0.75)
        self.assertAlmostEqual(rebuilt["area_alpha"], 0.5)
        self.assertAlmostEqual(rebuilt["bar_width_ratio"], 0.92)
        self.assertAlmostEqual(rebuilt["candle_width_ratio"], 0.88)

    def test_sparse_chart_snapshot_resets_hidden_fields_to_defaults(self) -> None:
        defaults = {
            "normalized_y": [],
            "bar_alpha": 0.75,
            "area_alpha": 0.5,
            "bar_width_ratio": 0.92,
            "candle_width_ratio": 0.88,
            "open": "Adj Open",
            "high": "Adj High",
            "low": "Adj Low",
            "close": "Adj Close",
            "volume": "Volume",
            "up_color": "#D62728",
            "down_color": "#2CA02C",
        }
        snapshot = chart_form_values_from_spec(
            {"id": "sparse", "type": "line", "x": "Date", "y": ["Close"]},
            defaults=defaults,
        )
        self.assertEqual(snapshot["normalized_y"], "")
        self.assertEqual(snapshot["open"], "Adj Open")
        self.assertEqual(snapshot["bar_width_ratio"], "0.92")
        self.assertNotIn("stale", snapshot.values())

    def test_palette_combo_covers_seaborn_categorical_and_continuous_sets(self) -> None:
        required = {"deep", "muted", "pastel", "colorblind", "Set2", "tab10", "rocket", "mako"}
        self.assertTrue(required.issubset(PALETTE_CHOICES))

    def test_width_ratios_reject_overlap_values(self) -> None:
        values = chart_form_values_from_spec(
            {
                "id": "bar",
                "type": "bar",
                "x": "Date",
                "y": ["Volume"],
                "bar_width_ratio": 1.0,
            }
        )
        with self.assertRaisesRegex(ValueError, "Bar 寬度比"):
            chart_spec_from_form_values(values)


if __name__ == "__main__":
    unittest.main()
