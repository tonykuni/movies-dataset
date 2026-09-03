from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pandas as pd

from vap_plotly_stack_renderer import write_plotly_stack_html
from vap_seaborn_stack_generator import (
    default_chart_spec,
    default_project_config,
    expand_render_row_specs,
    render_single_chart,
    render_stack,
    write_json,
)


def financial_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.bdate_range("2026-08-24", periods=5),
            "AdjOpen": [100.0, None, 102.0, 104.0, 103.0],
            "AdjHigh": [102.0, None, 104.0, 105.0, 106.0],
            "AdjLow": [99.0, None, 101.0, 102.0, 102.0],
            "AdjClose": [101.0, None, 103.0, 102.5, 105.0],
            "Volume": [1_000.0, None, 1_250.0, 980.0, 1_400.0],
            "Price": [50.0, 51.0, 50.5, 52.0, 53.0],
            "Turnover": [100_000.0, 110_000.0, 90_000.0, 130_000.0, 125_000.0],
            "Normalized": [-0.5, -0.1, 0.25, 0.7, 0.4],
        }
    )


def candlestick_chart(height_ratio: float = 2.0) -> dict[str, object]:
    chart = default_chart_spec(
        "adjusted_ohlcv",
        "candlestick",
        "Adjusted OHLCV",
        "Date",
        [],
    )
    chart.update(
        {
            "open": "AdjOpen",
            "high": "AdjHigh",
            "low": "AdjLow",
            "close": "AdjClose",
            "volume": "Volume",
            "axis_mode": "single",
            "secondary_y": [],
            "unit": "Adjusted Price",
            "secondary_unit": "Volume",
            "missing": "ffill",
            "height_ratio": height_ratio,
            "price_height_fraction": 0.75,
            "volume_height_fraction": 0.25,
            "tick_policy": "vap_locked",
            "tick_count": 5,
        }
    )
    return chart


def line_chart() -> dict[str, object]:
    chart = default_chart_spec("price_line", "line", "Price", "Date", ["Price"])
    chart.update({"unit": "Price", "height_ratio": 1.0})
    return chart


def plotly_payload(html: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    plot_call = html.rindex("Plotly.newPlot(")
    trace_start = html.index("[", plot_call)
    traces, trace_length = json.JSONDecoder().raw_decode(html[trace_start:])
    layout_start = html.index("{", trace_start + trace_length)
    layout, _layout_length = json.JSONDecoder().raw_decode(html[layout_start:])
    return traces, layout


def layout_axis_key(trace_axis: str) -> str:
    suffix = trace_axis.removeprefix("y")
    return f"yaxis{suffix}"


class VAPV23RenderIntegrationTests(unittest.TestCase):
    def test_candlestick_expands_to_75_25_single_axis_rows_without_height_drift(self) -> None:
        chart = candlestick_chart(height_ratio=2.0)
        rows = expand_render_row_specs([line_chart(), chart])

        self.assertEqual(len(rows), 3)
        price_row, volume_row = rows[1:]
        self.assertEqual(price_row["_render_role"], "candlestick_price")
        self.assertEqual(volume_row["_render_role"], "candlestick_volume")
        self.assertEqual(price_row["_logical_chart_id"], chart["id"])
        self.assertEqual(volume_row["_logical_chart_id"], chart["id"])
        self.assertEqual(price_row["axis_mode"], "single")
        self.assertEqual(volume_row["axis_mode"], "single")
        self.assertEqual(price_row["secondary_y"], [])
        self.assertEqual(volume_row["secondary_y"], [])
        self.assertTrue(math.isclose(float(price_row["height_ratio"]), 1.5))
        self.assertTrue(math.isclose(float(volume_row["height_ratio"]), 0.5))
        self.assertTrue(
            math.isclose(
                float(price_row["height_ratio"]) + float(volume_row["height_ratio"]),
                float(chart["height_ratio"]),
            )
        )

    def test_single_and_stack_reports_count_physical_rows_and_no_candle_right_axis(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "financial.csv"
            financial_frame().to_csv(data_path, index=False, date_format="%Y-%m-%d")
            config_path = root / "stack.json"
            config = default_project_config(data_path.name)
            config["project"].update(
                {
                    "output_formats": ["png"],
                    "output_directory": "output",
                    "output_name": "v23_render_qa",
                    "dpi": 72,
                    "width_inch": 6.0,
                    "panel_height_inch": 1.0,
                    "source": "",
                    "watermark": "",
                }
            )
            config["charts"] = [candlestick_chart(), line_chart()]
            write_json(config_path, config)

            single_report = render_single_chart(config_path, "adjusted_ohlcv")
            stack_report = render_stack(config_path)

        self.assertEqual(single_report["render_mode"], "single")
        self.assertEqual(single_report["chart_count"], 1)
        self.assertEqual(single_report["render_panel_count"], 2)
        self.assertEqual(stack_report["chart_count"], 2)
        self.assertEqual(stack_report["render_panel_count"], 3)
        for report in (single_report, stack_report):
            candle_panel = next(
                panel for panel in report["panels"] if panel["id"] == "adjusted_ohlcv"
            )
            self.assertEqual(candle_panel["axis_mode"], "split_single")
            self.assertIsNone(candle_panel["axis_ticks"]["right"])
            self.assertEqual(
                [subpanel["role"] for subpanel in candle_panel["render_panels"]],
                ["price", "volume"],
            )
            self.assertTrue(
                all(
                    subpanel["axis_mode"] == "single"
                    and subpanel["axis_ticks"]["right"] is None
                    for subpanel in candle_panel["render_panels"]
                )
            )

    def test_plotly_candle_and_raw_volume_use_separate_primary_subplot_domains(self) -> None:
        chart = candlestick_chart(height_ratio=2.0)
        project = {
            "title": "Split OHLCV",
            "shared_x": True,
            "standard_panel_height_px": 420,
            "palette": "deep",
        }
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = write_plotly_stack_html(
                Path(temporary_directory) / "split.html",
                project,
                [{"chart": chart, "frame": financial_frame()}],
            )
            traces, layout = plotly_payload(output.read_text(encoding="utf-8"))

        candle_trace = next(trace for trace in traces if trace["type"] == "candlestick")
        volume_trace = next(
            trace
            for trace in traces
            if trace.get("meta", {}).get("vap_candle_volume") is True
        )
        self.assertNotEqual(candle_trace["yaxis"], volume_trace["yaxis"])

        price_axis = layout[layout_axis_key(str(candle_trace["yaxis"]))]
        volume_axis = layout[layout_axis_key(str(volume_trace["yaxis"]))]
        self.assertNotIn("overlaying", price_axis)
        self.assertNotIn("overlaying", volume_axis)
        self.assertGreater(float(price_axis["domain"][0]), float(volume_axis["domain"][1]))
        price_span = float(price_axis["domain"][1]) - float(price_axis["domain"][0])
        volume_span = float(volume_axis["domain"][1]) - float(volume_axis["domain"][0])
        self.assertTrue(math.isclose(price_span / volume_span, 3.0, rel_tol=0.03))

        # 155 px is the fixed document chrome; the physical rows retain the
        # logical chart's 2x standard height: 155 + 420 * (1.5 + 0.5).
        self.assertEqual(layout["height"], 995)
        self.assertIsInstance(
            volume_trace["y"],
            list,
            "Volume must be emitted as inspectable JSON values so a missing trade stays null.",
        )
        self.assertIsNone(volume_trace["y"][1])
        self.assertEqual(volume_trace["y"][2], 1_250.0)

    def test_plotly_dual_axis_and_normalized_overlay_survive_split_candle_rows(self) -> None:
        dual = default_chart_spec("dual", "line", "Dual", "Date", ["Price"])
        dual.update(
            {
                "secondary_y": ["Turnover"],
                "normalized_y": ["Normalized"],
                "secondary_type": "bar",
                "axis_mode": "dual",
                "unit": "Price",
                "secondary_unit": "Turnover",
                "tick_policy": "vap_locked",
                "tick_count": 5,
            }
        )
        panels = [
            {"chart": candlestick_chart(height_ratio=1.0), "frame": financial_frame()},
            {"chart": dual, "frame": financial_frame()},
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = write_plotly_stack_html(
                Path(temporary_directory) / "dual.html",
                {"title": "Dual QA", "shared_x": True, "standard_panel_height_px": 420},
                panels,
            )
            html = output.read_text(encoding="utf-8")
            traces, layout = plotly_payload(html)

        by_name = {str(trace.get("name")): trace for trace in traces}
        primary = by_name["Price"]
        secondary = by_name["Turnover"]
        normalized = by_name["Normalized"]
        self.assertNotEqual(primary["yaxis"], secondary["yaxis"])
        self.assertNotIn(normalized["yaxis"], {primary["yaxis"], secondary["yaxis"]})
        self.assertEqual(normalized["visible"], "legendonly")
        secondary_axis = layout[layout_axis_key(str(secondary["yaxis"]))]
        normalized_axis = layout[layout_axis_key(str(normalized["yaxis"]))]
        self.assertEqual(secondary_axis["overlaying"], primary["yaxis"])
        self.assertEqual(normalized_axis["overlaying"], primary["yaxis"])
        self.assertFalse(normalized_axis["showticklabels"])
        self.assertIn('id="vap-normalized-toggle"', html)


if __name__ == "__main__":
    unittest.main()
