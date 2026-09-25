from __future__ import annotations

import importlib
import importlib.util
import math
import re
import tempfile
import unittest
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.colors import to_rgba

from vap_seaborn_stack_generator import (
    DEFAULT_AREA_ALPHA,
    DEFAULT_BAR_ALPHA,
    DEFAULT_DOWN_COLOR,
    DEFAULT_UP_COLOR,
    apply_missing_policy,
    apply_y_format,
    compute_locked_ticks,
    draw_area_chart,
    draw_bar_chart,
    draw_chart,
    format_panel,
    required_columns_for_chart,
    validate_chart_spec,
)


def financial_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.to_datetime(["2026-01-02", "2026-01-05", "2026-01-06"]),
            "AdjOpen": [100.0, 104.0, 101.0],
            "AdjHigh": [106.0, 105.0, 108.0],
            "AdjLow": [99.0, 100.0, 100.0],
            "AdjClose": [105.0, 101.0, 107.0],
            "Volume": [1_000_000.0, 1_400_000.0, 900_000.0],
            "Normalized": [-0.5, 0.0, 0.75],
        }
    )


def candlestick_chart() -> dict[str, object]:
    return {
        "id": "adjusted_ohlcv",
        "type": "candlestick",
        "title": "Adjusted OHLC + Volume",
        "x": "Date",
        "open": "AdjOpen",
        "high": "AdjHigh",
        "low": "AdjLow",
        "close": "AdjClose",
        "volume": "Volume",
        "y": [],
        "secondary_y": [],
        "normalized_y": [],
        "axis_mode": "dual",
        "missing": "ffill",
        "tick_policy": "vap_locked",
        "tick_count": 6,
        "max_x_ticks": 8,
        "height_ratio": 1.5,
        "bar_alpha": DEFAULT_BAR_ALPHA,
        "area_alpha": DEFAULT_AREA_ALPHA,
        "candle_width_ratio": 0.88,
        "up_color": DEFAULT_UP_COLOR,
        "down_color": DEFAULT_DOWN_COLOR,
        "unit": "Price",
        "secondary_unit": "Volume",
        "y_format": "number",
        "secondary_y_format": "magnitude",
        "show_legend": True,
    }


def assert_rgba_close(test: unittest.TestCase, actual: object, expected: object) -> None:
    test.assertTrue(np.allclose(to_rgba(actual)[:3], to_rgba(expected)[:3], atol=1e-7))


class VAPV22FinancialFeatureTests(unittest.TestCase):
    def tearDown(self) -> None:
        plt.close("all")

    def test_candlestick_requires_and_reports_all_adjusted_ohlcv_columns(self) -> None:
        chart = candlestick_chart()
        validate_chart_spec(chart, 1)
        self.assertEqual(
            required_columns_for_chart(chart),
            ["Date", "AdjOpen", "AdjHigh", "AdjLow", "AdjClose", "Volume"],
        )

        for mapping in ("x", "open", "high", "low", "close", "volume"):
            incomplete = dict(chart)
            incomplete[mapping] = ""
            with self.subTest(mapping=mapping):
                with self.assertRaisesRegex(ValueError, re.escape(mapping)):
                    validate_chart_spec(incomplete, 1)

    def test_forward_fill_repairs_prices_but_never_volume(self) -> None:
        frame = financial_frame()
        frame.loc[1, ["AdjOpen", "AdjHigh", "AdjLow", "AdjClose", "Volume"]] = np.nan
        repaired = apply_missing_policy(
            frame,
            ["AdjOpen", "AdjHigh", "AdjLow", "AdjClose", "Volume"],
            "ffill",
        )

        for column in ("AdjOpen", "AdjHigh", "AdjLow", "AdjClose"):
            self.assertEqual(float(repaired.loc[1, column]), float(frame.loc[0, column]))
        self.assertTrue(pd.isna(repaired.loc[1, "Volume"]))
        self.assertEqual(float(repaired.loc[2, "Volume"]), 900_000.0)
        for policy in ("interpolate", "zero"):
            with self.subTest(policy=policy):
                protected = apply_missing_policy(
                    frame,
                    ["AdjOpen", "AdjHigh", "AdjLow", "AdjClose", "Volume"],
                    policy,
                )
                self.assertTrue(pd.isna(protected.loc[1, "Volume"]))

    def test_default_bar_and_area_opacity_are_applied_to_artists(self) -> None:
        frame = financial_frame()
        project = {"palette": "deep"}

        bar_figure, bar_axis = plt.subplots()
        draw_bar_chart(
            bar_axis,
            frame,
            {"x": "Date", "y": ["Volume"]},
            [(0.2, 0.4, 0.6)],
        )
        self.assertTrue(bar_axis.patches)
        self.assertTrue(
            all(math.isclose(float(patch.get_alpha()), DEFAULT_BAR_ALPHA) for patch in bar_axis.patches)
        )

        area_figure, area_axis = plt.subplots()
        draw_area_chart(
            area_axis,
            frame,
            {"x": "Date", "y": ["AdjClose"]},
            [(0.2, 0.4, 0.6)],
        )
        filled_collections = [
            collection
            for collection in area_axis.collections
            if collection.get_alpha() is not None
        ]
        self.assertTrue(filled_collections)
        self.assertTrue(
            all(
                math.isclose(float(collection.get_alpha()), DEFAULT_AREA_ALPHA)
                for collection in filled_collections
            )
        )
        plt.close(bar_figure)
        plt.close(area_figure)

    def test_datetime_bars_use_most_of_the_available_slot_without_overlap(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": pd.to_datetime(["2026-01-02", "2026-01-03", "2026-01-05"]),
                "Value": [1.0, 2.0, 3.0],
            }
        )
        figure, axis = plt.subplots()
        draw_bar_chart(axis, frame, {"x": "Date", "y": ["Value"]}, ["#336699"])
        patches = sorted(axis.patches, key=lambda patch: patch.get_x())
        self.assertEqual(len(patches), 3)

        widths = [float(patch.get_width()) for patch in patches]
        self.assertTrue(all(0.85 <= width < 1.0 for width in widths))
        for left, right in zip(patches, patches[1:]):
            left_edge = float(left.get_x() + left.get_width())
            right_edge = float(right.get_x())
            self.assertLessEqual(left_edge, right_edge + 1e-10)
        plt.close(figure)

    def test_locked_axes_have_equal_tick_counts_nice_steps_and_trailing_zero_labels(self) -> None:
        primary_ticks = compute_locked_ticks(101.1, 110.7, tick_count=6, include_zero=False)
        secondary_ticks = compute_locked_ticks(0.0, 9.8, tick_count=6, include_zero=True)
        self.assertEqual(len(primary_ticks), 6)
        self.assertEqual(len(secondary_ticks), 6)

        for ticks in (primary_ticks, secondary_ticks):
            step = float(ticks[1] - ticks[0])
            exponent = math.floor(math.log10(abs(step)))
            mantissa = step / (10.0**exponent)
            self.assertTrue(
                any(math.isclose(mantissa, allowed, rel_tol=1e-9) for allowed in (1.25, 2.0, 2.5, 5.0, 10.0)),
                msg=f"unexpected VAP interval {step}",
            )
            self.assertLessEqual(float(ticks[0]), 0.0 if ticks is secondary_ticks else 101.1)
            self.assertGreaterEqual(float(ticks[-1]), 9.8 if ticks is secondary_ticks else 110.7)

        figure, axis = plt.subplots()
        axis.set_yticks([0.0, 1.25, 2.5])
        apply_y_format(axis, "number")
        figure.canvas.draw()
        self.assertEqual([label.get_text() for label in axis.get_yticklabels()], ["0.00", "1.25", "2.50"])
        plt.close(figure)

    def test_format_panel_locks_left_and_right_axes_to_the_same_interval_count(self) -> None:
        frame = financial_frame()
        figure, axis = plt.subplots()
        axis.plot(frame["Date"], frame["AdjClose"])
        secondary_axis = axis.twinx()
        secondary_axis.bar(frame["Date"], frame["Volume"])
        chart = {
            "id": "dual",
            "type": "line",
            "title": "Dual",
            "tick_policy": "vap_locked",
            "tick_count": 6,
            "axis_zero_policy": "exclude",
            "secondary_axis_zero_policy": "include",
            "y_format": "number",
            "secondary_y_format": "number",
            "unit": "Price",
            "secondary_unit": "Volume",
            "show_legend": False,
            "show_zero_line": False,
            "auto_optimize": False,
        }
        format_panel(axis, secondary_axis, chart, {}, is_last=True, x_is_date=True)
        self.assertEqual(len(axis.get_yticks()), 6)
        self.assertEqual(len(secondary_axis.get_yticks()), 6)
        plt.close(figure)

    def test_normalized_series_is_available_but_not_drawn_on_static_primary_axis(self) -> None:
        frame = financial_frame()
        chart = {
            "id": "price",
            "type": "line",
            "title": "Price",
            "x": "Date",
            "y": ["AdjClose"],
            "secondary_y": [],
            "normalized_y": ["Normalized"],
            "axis_mode": "single",
            "palette": "deep",
        }
        self.assertIn("Normalized", required_columns_for_chart(chart))
        figure, axis = plt.subplots()
        secondary_axis = draw_chart(axis, frame, chart, {"palette": "deep"})
        self.assertIsNone(secondary_axis)
        labels = [line.get_label() for line in axis.lines]
        self.assertIn("AdjClose", labels)
        self.assertNotIn("Normalized", labels)
        plt.close(figure)

    def test_candlestick_and_volume_share_taiwan_red_up_green_down_colors(self) -> None:
        frame = financial_frame()
        chart = candlestick_chart()
        figure, axis = plt.subplots()
        secondary_axis = draw_chart(axis, frame, chart, {"palette": "deep"})
        self.assertIsNotNone(secondary_axis)
        assert secondary_axis is not None

        candle_bodies = axis.patches
        volume_bars = secondary_axis.patches
        self.assertEqual(len(candle_bodies), len(frame))
        self.assertEqual(len(volume_bars), len(frame))
        expected = [DEFAULT_UP_COLOR, DEFAULT_DOWN_COLOR, DEFAULT_UP_COLOR]
        for body, volume, color in zip(candle_bodies, volume_bars, expected):
            assert_rgba_close(self, body.get_facecolor(), color)
            assert_rgba_close(self, volume.get_facecolor(), color)
            self.assertTrue(math.isclose(float(volume.get_alpha()), DEFAULT_BAR_ALPHA))
        plt.close(figure)

    def test_plotly_html_is_self_contained_stacked_and_exposes_normalized_checkbox(self) -> None:
        if importlib.util.find_spec("vap_plotly_stack_renderer") is None:
            self.skipTest("vap_plotly_stack_renderer 尚未安裝")
        try:
            renderer = importlib.import_module("vap_plotly_stack_renderer")
        except ModuleNotFoundError as exc:
            if exc.name and exc.name.startswith("plotly"):
                self.skipTest("Plotly dependency 尚未安裝")
            raise

        frame = financial_frame()
        panels = [
            {"chart": candlestick_chart(), "frame": frame},
            {
                "chart": {
                    "id": "price_line",
                    "type": "line",
                    "title": "Price with optional normalized data",
                    "x": "Date",
                    "y": ["AdjClose"],
                    "secondary_y": [],
                    "normalized_y": ["Normalized"],
                    "axis_mode": "single",
                    "height_ratio": 1.0,
                    "palette": "deep",
                },
                "frame": frame,
            },
        ]
        project = {
            "title": "VAP Plotly Stack",
            "palette": "deep",
            "paper_face_color": "#FFFFFF",
            "axes_face_color": "#FFFFFF",
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            output_path = Path(temporary_directory) / "financial_stack.html"
            result = renderer.write_plotly_stack_html(output_path, project, panels)
            self.assertEqual(Path(result), output_path)
            html = output_path.read_text(encoding="utf-8")

        lowered = html.lower()
        self.assertGreater(len(html), 1_000_000, "HTML 應內嵌 Plotly.js，而不是依賴 CDN")
        self.assertNotRegex(lowered, r'<script[^>]+src=["\']https?://')
        self.assertIn("plotly", lowered)
        self.assertRegex(lowered, r'type\s*=\s*["\']checkbox["\']')
        self.assertIn("normalized", lowered)
        self.assertIn("candlestick", lowered)
        self.assertIn("price with optional normalized data", lowered)
        self.assertRegex(lowered, r'"xaxis2"|"xaxis3"')
        self.assertIn(DEFAULT_UP_COLOR.lower(), lowered)
        self.assertIn(DEFAULT_DOWN_COLOR.lower(), lowered)
        self.assertIn(f'"opacity":{DEFAULT_BAR_ALPHA}', lowered.replace(" ", ""))


if __name__ == "__main__":
    unittest.main()
