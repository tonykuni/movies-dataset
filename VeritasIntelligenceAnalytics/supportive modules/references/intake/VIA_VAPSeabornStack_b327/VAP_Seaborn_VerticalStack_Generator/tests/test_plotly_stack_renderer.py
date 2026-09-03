from __future__ import annotations

import builtins
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd

from vap_plotly_stack_renderer import (
    _bar_width,
    _require_plotly,
    seaborn_palette_to_hex,
    write_plotly_stack_html,
)


class PlotlyStackRendererTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = pd.DataFrame(
            {
                "Date": pd.date_range("2026-01-02", periods=6, freq="B"),
                "AdjOpen": [100.0, 101.0, None, 103.0, 102.0, 104.0],
                "AdjHigh": [101.25, 102.5, None, 104.0, 103.75, 105.0],
                "AdjLow": [98.75, 100.0, None, 101.25, 100.0, 102.5],
                "AdjClose": [101.0, 100.5, None, 103.75, 102.5, 104.5],
                "Volume": [1000.0, 1200.0, None, 900.0, 1500.0, 1300.0],
                "A": [1.0, 2.0, 3.0, 4.0, 3.0, 5.0],
                "B": [5.0, 4.0, 3.0, 2.0, 3.0, 1.0],
                "Signed": [-2.0, 1.0, 3.0, -1.0, 2.0, 4.0],
                "Normalized": [0.10, 0.20, 0.35, 0.30, 0.45, 0.40],
            }
        )
        self.project = {
            "title": "VAP Plotly Test",
            "subtitle": "Offline vertical stack",
            "source": "Unit test",
            "shared_x": True,
            "palette": "deep",
            "bar_gap_ratio": 0.03,
        }

    def test_seaborn_palette_is_converted_to_uppercase_hex(self) -> None:
        colors = seaborn_palette_to_hex("deep", 3)
        self.assertEqual(3, len(colors))
        self.assertTrue(all(color.startswith("#") and len(color) == 7 for color in colors))
        self.assertTrue(all(color == color.upper() for color in colors))

    def test_optional_plotly_dependency_has_actionable_error(self) -> None:
        original_import = builtins.__import__

        def blocked_import(name: str, *args: object, **kwargs: object) -> object:
            if name.startswith("plotly"):
                raise ImportError("blocked for test")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=blocked_import):
            with self.assertRaisesRegex(RuntimeError, "pip install.*plotly"):
                _require_plotly()

    def test_datetime_bar_width_uses_smallest_spacing_without_overlap(self) -> None:
        dates = pd.Series(pd.to_datetime(["2026-01-01", "2026-01-02", "2026-01-09"]))
        one_day_ms = 24 * 60 * 60 * 1000
        self.assertEqual(one_day_ms * 0.92, _bar_width(dates, 0.92))

    def test_offline_html_supports_all_requested_plot_types(self) -> None:
        chart_types = [
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
        ]
        panels: list[dict[str, object]] = []
        for chart_type in chart_types:
            chart: dict[str, object] = {
                "id": chart_type,
                "type": chart_type,
                "title": chart_type,
                "x": "Date",
                "y": ["A", "B"],
                "tick_policy": "vap_locked",
                "tick_count": 5,
                "bar_alpha": 0.75,
                "area_alpha": 0.50,
            }
            if chart_type == "line":
                chart.update(
                    {
                        "y": ["A", "Normalized"],
                        "normalized_y": ["Normalized"],
                        "secondary_y": ["Volume"],
                        "secondary_type": "bar",
                        "axis_mode": "dual",
                    }
                )
            panels.append({"chart": chart, "frame": self.frame})
        panels.append(
            {
                "chart": {
                    "id": "candlestick",
                    "type": "candlestick",
                    "title": "Adjusted OHLC and Volume",
                    "x": "Date",
                    "open": "AdjOpen",
                    "high": "AdjHigh",
                    "low": "AdjLow",
                    "close": "AdjClose",
                    "volume": "Volume",
                    "up_color": "#C7353A",
                    "down_color": "#17835D",
                    "bar_alpha": 0.75,
                    "candle_width_ratio": 0.90,
                    "tick_policy": "vap_locked",
                    "tick_count": 5,
                },
                "frame": self.frame,
            }
        )

        with tempfile.TemporaryDirectory() as temporary_directory:
            destination = Path(temporary_directory) / "stack.html"
            result = write_plotly_stack_html(destination, self.project, panels)
            html = result.read_text(encoding="utf-8")

        self.assertEqual(destination.name, result.name)
        self.assertGreater(len(html), 1_000_000)
        self.assertIn("plotly.js v", html.lower())
        self.assertIn("Plotly.newPlot", html)
        self.assertNotIn("<script src=", html.lower())
        self.assertNotIn("cdn.plot.ly", html.lower())
        self.assertNotIn("unpkg.com", html.lower())
        self.assertIn("connect-src 'none'", html)
        self.assertIn('id="vap-normalized-toggle"', html)
        self.assertIn('"visible":"legendonly"', html)
        self.assertIn('"vap_normalized_y":true', html)
        normalized_position = html.index('"name":"Normalized"')
        self.assertIn('"yaxis":"y2"', html[normalized_position : normalized_position + 1200])
        self.assertIn('"type":"candlestick"', html)
        self.assertIn('"color":"#C7353A"', html)
        self.assertIn('"color":"#17835D"', html)
        self.assertIn('"vap_candle_volume":true', html)
        self.assertIn('"opacity":0.75', html)
        self.assertIn('"opacity":0.5', html)
        self.assertIn('"shape":"hv"', html)
        self.assertIn('"stackgroup":"vap-stack-', html)
        self.assertIn('"groupnorm":"percent"', html)
        self.assertIn('"barmode":"relative"', html)
        self.assertIn('"bargap":0.03', html)
        self.assertIn('"ticktext":["0.00","1.25","2.50","3.75","5.00"]', html)

    def test_non_html_suffix_is_safely_replaced_and_no_pdf_is_written(self) -> None:
        panel = {
            "chart": {"type": "line", "title": "Line", "x": "Date", "y": ["A"]},
            "frame": self.frame,
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            requested = Path(temporary_directory) / "interactive.pdf"
            result = write_plotly_stack_html(requested, self.project, [panel])
            self.assertEqual(".html", result.suffix)
            self.assertTrue(result.exists())
            self.assertFalse(requested.exists())

    def test_dual_axis_normalized_trace_has_independent_scale_and_axis_titles(self) -> None:
        panel = {
            "chart": {
                "id": "dual_normalized",
                "type": "line",
                "title": "Dual normalized",
                "x": "Date",
                "y": ["A"],
                "secondary_y": ["Volume"],
                "normalized_y": ["Normalized"],
                "secondary_type": "bar",
                "axis_mode": "dual",
                "unit": "Price",
                "secondary_unit": "Volume",
                "tick_policy": "vap_locked",
                "tick_count": 5,
            },
            "frame": self.frame,
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            result = write_plotly_stack_html(
                Path(temporary_directory) / "dual_normalized.html",
                self.project,
                [panel],
            )
            html = result.read_text(encoding="utf-8")

        plot_call = html.rindex("Plotly.newPlot(")
        trace_start = html.index("[", plot_call)
        traces, trace_length = json.JSONDecoder().raw_decode(html[trace_start:])
        layout_start = html.index("{", trace_start + trace_length)
        layout, _layout_length = json.JSONDecoder().raw_decode(html[layout_start:])
        by_name = {trace["name"]: trace for trace in traces}
        self.assertEqual(by_name["A"]["yaxis"], "y")
        self.assertEqual(by_name["Volume"]["yaxis"], "y2")
        self.assertNotIn(by_name["Normalized"]["yaxis"], {"y", "y2"})
        self.assertEqual(by_name["Normalized"]["visible"], "legendonly")
        normalized_axis = "yaxis" + by_name["Normalized"]["yaxis"].removeprefix("y")
        self.assertEqual(layout[normalized_axis]["overlaying"], "y")
        self.assertFalse(layout[normalized_axis]["showticklabels"])
        self.assertEqual(layout["yaxis"]["title"]["text"], "Price")
        self.assertEqual(layout["yaxis2"]["title"]["text"], "Volume")


if __name__ == "__main__":
    unittest.main()
