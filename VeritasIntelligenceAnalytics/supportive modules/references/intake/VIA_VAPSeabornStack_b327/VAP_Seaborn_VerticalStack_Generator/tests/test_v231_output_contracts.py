from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path
from xml.etree import ElementTree

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image

from vap_plotly_stack_renderer import _fixed_ticks, write_plotly_stack_html
from vap_seaborn_stack_generator import (
    default_chart_spec,
    default_project_config,
    draw_chart,
    render_single_chart,
    render_stack,
    write_json,
)


NICE_MANTISSAS = (1.25, 2.0, 2.5, 5.0, 10.0)
ONE_DAY_MS = 24 * 60 * 60 * 1000


def financial_frame() -> pd.DataFrame:
    """Small frame that exposes fill, decimal-tick and up/down-color edges."""

    return pd.DataFrame(
        {
            "Date": pd.bdate_range("2026-08-24", periods=5),
            "AdjOpen": [100.0, 101.0, None, 103.0, 104.0],
            "AdjHigh": [102.0, 103.0, None, 105.0, 106.0],
            "AdjLow": [99.0, 100.0, None, 102.0, 103.0],
            "AdjClose": [101.0, 100.0, None, 104.0, 103.0],
            "Volume": [1_000.0, 1_200.0, None, 800.0, 1_500.0],
            "Price": [0.0, 1.25, 2.50, 3.75, 5.00],
            "Turnover": [100.0, 200.0, 300.0, 400.0, 500.0],
            "Normalized": [0.00, 0.20, 0.35, 0.70, 1.00],
        }
    )


def candlestick_chart(height_ratio: float = 1.0) -> dict[str, object]:
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
            "unit": "Adjusted Price",
            "secondary_unit": "Volume",
            "axis_mode": "single",
            "secondary_y": [],
            "missing": "ffill",
            "height_ratio": height_ratio,
            "price_height_fraction": 0.75,
            "volume_height_fraction": 0.25,
            "up_color": "#D62728",
            "down_color": "#2CA02C",
            "bar_alpha": 0.75,
            "bar_width_ratio": 0.92,
            "tick_policy": "vap_locked",
            "tick_count": 5,
            "y_format": "auto",
        }
    )
    return chart


def dual_area_bar_chart() -> dict[str, object]:
    chart = default_chart_spec(
        "price_volume_normalized",
        "area",
        "Price, turnover and normalized series",
        "Date",
        ["Price"],
    )
    chart.update(
        {
            "secondary_y": ["Turnover"],
            "normalized_y": ["Normalized"],
            "secondary_type": "bar",
            "axis_mode": "dual",
            "unit": "Adjusted Price",
            "secondary_unit": "Turnover",
            "tick_policy": "vap_locked",
            "tick_count": 5,
            "y_format": "number",
            "secondary_y_format": "number",
            "line_width": 1.65,
            "alpha": 0.82,
            "bar_alpha": 0.75,
            "area_alpha": 0.50,
            "bar_width_ratio": 0.92,
            "height_ratio": 1.0,
        }
    )
    return chart


def plotly_payload(html: str) -> tuple[list[dict[str, object]], dict[str, object]]:
    plot_call = html.rindex("Plotly.newPlot(")
    trace_start = html.index("[", plot_call)
    traces, trace_length = json.JSONDecoder().raw_decode(html[trace_start:])
    layout_start = html.index("{", trace_start + trace_length)
    layout, _layout_length = json.JSONDecoder().raw_decode(html[layout_start:])
    return traces, layout


def y_layout_key(trace_axis: str) -> str:
    suffix = trace_axis.removeprefix("y")
    return f"yaxis{suffix}"


def x_layout_key(trace_axis: str) -> str:
    suffix = trace_axis.removeprefix("x")
    return f"xaxis{suffix}"


def label_number(text: str) -> float:
    return float(text.replace(",", "").removesuffix("%"))


def decimal_places(text: str) -> int:
    normalized = text.replace(",", "").removesuffix("%")
    return len(normalized.rsplit(".", 1)[1]) if "." in normalized else 0


def is_vap_nice_step(step: float) -> bool:
    return any(
        math.isclose(step, mantissa * (10.0**exponent), rel_tol=1e-9, abs_tol=1e-12)
        for exponent in range(-12, 13)
        for mantissa in NICE_MANTISSAS
    )


class VAPV231OutputContractTests(unittest.TestCase):
    def assert_locked_axis(
        self,
        axis: dict[str, object],
        minimum: float,
        maximum: float,
    ) -> None:
        tick_values = [float(value) for value in axis["tickvals"]]
        tick_text = [str(value) for value in axis["ticktext"]]
        self.assertEqual(len(tick_values), 5)
        self.assertEqual(len(tick_text), 5)
        differences = np.diff(tick_values)
        self.assertEqual(len(differences), 4)
        self.assertTrue(np.allclose(differences, differences[0]))
        self.assertTrue(is_vap_nice_step(float(differences[0])))
        self.assertLessEqual(float(axis["range"][0]), minimum)
        self.assertGreaterEqual(float(axis["range"][1]), maximum)

        # Tick labels are data, not decoration: an offset such as 98.5 must
        # never be silently rounded to 98 merely because the step is 2.
        for value, text in zip(tick_values, tick_text):
            self.assertTrue(
                math.isclose(label_number(text), value, rel_tol=1e-9, abs_tol=1e-9),
                f"tick label {text!r} does not represent tick value {value!r}",
            )
        if any(not math.isclose(value, round(value), abs_tol=1e-9) for value in tick_values):
            places = [decimal_places(text) for text in tick_text]
            self.assertGreater(min(places), 0)
            self.assertEqual(len(set(places)), 1)

    def test_plotly_offline_stack_enforces_financial_visual_contract(self) -> None:
        project = {
            "title": "VAP output contract",
            "subtitle": "Offline QA",
            "source": "Generated fixture",
            "shared_x": True,
            "standard_panel_height_px": 420,
            "palette": "deep",
            "bar_gap_ratio": 0.03,
        }
        panels = [
            {"chart": candlestick_chart(), "frame": financial_frame()},
            {"chart": dual_area_bar_chart(), "frame": financial_frame()},
        ]
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = write_plotly_stack_html(
                Path(temporary_directory) / "financial_contract.html",
                project,
                panels,
            )
            html = output.read_text(encoding="utf-8")
            traces, layout = plotly_payload(html)

        lowered = html.lower()
        self.assertGreater(len(html), 1_000_000)
        self.assertIn("plotly.js v", lowered)
        self.assertIn("plotly.newplot", lowered)
        self.assertNotIn("<script src=", lowered)
        self.assertNotIn("cdn.plot.ly", lowered)
        self.assertNotIn("unpkg.com", lowered)
        self.assertIn("connect-src 'none'", lowered)
        self.assertEqual(layout["hovermode"], "x unified")
        self.assertEqual(layout["height"], 995)
        self.assertLessEqual(float(layout["bargap"]), 0.03)
        self.assertEqual(float(layout["bargroupgap"]), 0.0)

        by_name = {str(trace.get("name")): trace for trace in traces}
        candle = by_name["Adjusted OHLCV"]
        volume = by_name["Volume"]
        price = by_name["Price"]
        turnover = by_name["Turnover"]
        normalized = by_name["Normalized"]

        self.assertEqual(candle["type"], "candlestick")
        self.assertEqual(candle["increasing"]["line"]["color"], "#D62728")
        self.assertEqual(candle["increasing"]["fillcolor"], "#D62728")
        self.assertEqual(candle["decreasing"]["line"]["color"], "#2CA02C")
        self.assertEqual(candle["decreasing"]["fillcolor"], "#2CA02C")
        self.assertEqual(
            volume["marker"]["color"],
            ["#D62728", "#2CA02C", "#2CA02C", "#D62728", "#2CA02C"],
        )
        self.assertEqual(volume["opacity"], 0.75)
        self.assertEqual(volume["y"], [1_000.0, 1_200.0, None, 800.0, 1_500.0])
        self.assertLess(float(volume["width"]), ONE_DAY_MS)
        self.assertGreater(float(volume["width"]), 0.0)
        self.assertTrue(volume["meta"]["vap_candle_volume"])

        self.assertEqual(price["fill"], "tozeroy")
        self.assertEqual(price["opacity"], 0.50)
        self.assertEqual(price["line"]["width"], 1.65)
        self.assertEqual(turnover["type"], "bar")
        self.assertEqual(turnover["opacity"], 0.75)
        self.assertEqual(normalized["visible"], "legendonly")
        self.assertTrue(normalized["meta"]["vap_normalized_y"])
        self.assertNotIn(normalized["yaxis"], {price["yaxis"], turnover["yaxis"]})
        normalized_axis = layout[y_layout_key(str(normalized["yaxis"]))]
        self.assertEqual(normalized_axis["overlaying"], price["yaxis"])
        self.assertFalse(normalized_axis["showticklabels"])
        self.assertIn('id="vap-normalized-toggle"', html)
        self.assertIn('type="checkbox"', html)
        self.assertNotIn('type="checkbox" checked', html)
        self.assertIn('checkbox.checked ? true : "legendonly"', html)

        candle_axis = layout[y_layout_key(str(candle["yaxis"]))]
        volume_axis = layout[y_layout_key(str(volume["yaxis"]))]
        price_axis = layout[y_layout_key(str(price["yaxis"]))]
        turnover_axis = layout[y_layout_key(str(turnover["yaxis"]))]
        self.assertNotEqual(candle["yaxis"], volume["yaxis"])
        self.assertNotIn("overlaying", candle_axis)
        self.assertNotIn("overlaying", volume_axis)
        self.assertGreater(float(candle_axis["domain"][0]), float(volume_axis["domain"][1]))
        price_span = float(candle_axis["domain"][1]) - float(candle_axis["domain"][0])
        volume_span = float(volume_axis["domain"][1]) - float(volume_axis["domain"][0])
        self.assertTrue(math.isclose(price_span / volume_span, 3.0, rel_tol=0.03))

        # Three physical rows (price, volume, dual chart) share one time axis.
        bottom_x_reference = str(price["xaxis"])
        self.assertEqual(
            layout[x_layout_key(str(candle["xaxis"]))].get("matches"),
            bottom_x_reference,
        )
        self.assertEqual(
            layout[x_layout_key(str(volume["xaxis"]))].get("matches"),
            bottom_x_reference,
        )

        self.assert_locked_axis(candle_axis, 99.0, 106.0)
        self.assert_locked_axis(volume_axis, 0.0, 1_500.0)
        self.assert_locked_axis(price_axis, 0.0, 5.0)
        self.assert_locked_axis(turnover_axis, 0.0, 500.0)
        self.assertEqual(price_axis["ticktext"], ["0.00", "1.25", "2.50", "3.75", "5.00"])
        self.assertEqual(len(price_axis["tickvals"]), len(turnover_axis["tickvals"]))

    def test_fractional_tick_precision_has_no_binary_float_noise(self) -> None:
        result = _fixed_ticks([0.1, 0.3, 0.5, 0.7, 0.9], 5, False, "auto")
        self.assertIsNotNone(result)
        assert result is not None
        tick_values, tick_text, axis_range = result
        self.assertTrue(np.allclose(tick_values, [0.1, 0.3, 0.5, 0.7, 0.9]))
        self.assertEqual(tick_text, ["0.1", "0.3", "0.5", "0.7", "0.9"])
        self.assertTrue(np.allclose(axis_range, [0.1, 0.9]))

    def test_static_area_and_bar_use_default_stroke_alpha_and_nonoverlap_width(self) -> None:
        figure, axis = plt.subplots()
        try:
            secondary = draw_chart(
                axis,
                financial_frame(),
                dual_area_bar_chart(),
                {"palette": "deep"},
            )
            self.assertIsNotNone(secondary)
            assert secondary is not None
            self.assertEqual(len(axis.lines), 1)
            self.assertTrue(math.isclose(float(axis.lines[0].get_linewidth()), 1.65))
            self.assertTrue(math.isclose(float(axis.lines[0].get_alpha()), 0.82))
            fills = [item for item in axis.collections if item.get_alpha() is not None]
            self.assertTrue(fills)
            self.assertTrue(all(math.isclose(float(item.get_alpha()), 0.50) for item in fills))
            self.assertEqual(len(secondary.patches), len(financial_frame()))
            self.assertTrue(
                all(math.isclose(float(patch.get_alpha()), 0.75) for patch in secondary.patches)
            )
            widths = [float(patch.get_width()) for patch in secondary.patches]
            self.assertTrue(all(0.0 < width < 1.0 for width in widths))
        finally:
            plt.close(figure)

    def test_public_render_one_keeps_candle_and_volume_time_axis_shared_and_consistent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "financial.csv"
            financial_frame().to_csv(data_path, index=False, date_format="%Y-%m-%d")
            config_path = root / "stack.json"
            config = default_project_config(data_path.name)
            config["project"].update(
                {
                    "title": "Render-one QA",
                    "subtitle": "",
                    "source": "",
                    "watermark": "",
                    "output_directory": "output",
                    "output_name": "render_one_contract",
                    "output_formats": ["html"],
                    "shared_x": True,
                    "standard_panel_height_px": 420,
                }
            )
            config["charts"] = [candlestick_chart(), dual_area_bar_chart()]
            write_json(config_path, config)

            stack_report = render_stack(config_path)
            single_report = render_single_chart(config_path, "adjusted_ohlcv")
            stack_html = Path(stack_report["outputs"][0]).read_text(encoding="utf-8")
            single_html = Path(single_report["outputs"][0]).read_text(encoding="utf-8")
            stack_traces, stack_layout = plotly_payload(stack_html)
            single_traces, single_layout = plotly_payload(single_html)

            self.assertTrue(Path(stack_report["outputs"][0]).exists())
            self.assertTrue(Path(single_report["outputs"][0]).exists())
            self.assertNotEqual(stack_report["outputs"][0], single_report["outputs"][0])

        self.assertEqual(single_report["render_mode"], "single")
        self.assertEqual(single_report["chart_count"], 1)
        self.assertEqual(single_report["render_panel_count"], 2)
        self.assertEqual(single_report["panels"][0]["axis_mode"], "split_single")
        self.assertEqual(
            [panel["role"] for panel in single_report["panels"][0]["render_panels"]],
            ["price", "volume"],
        )

        stack_by_name = {str(trace.get("name")): trace for trace in stack_traces}
        single_by_name = {str(trace.get("name")): trace for trace in single_traces}
        single_candle = single_by_name["Adjusted OHLCV"]
        single_volume = single_by_name["Volume"]
        candle_x_axis = single_layout[x_layout_key(str(single_candle["xaxis"]))]
        volume_x_axis = single_layout[x_layout_key(str(single_volume["xaxis"]))]
        self.assertTrue(
            candle_x_axis.get("matches") == single_volume["xaxis"]
            or volume_x_axis.get("matches") == single_candle["xaxis"],
            "render-one must still share the OHLC and volume X axis",
        )

        for name in ("Adjusted OHLCV", "Volume"):
            stack_trace = stack_by_name[name]
            single_trace = single_by_name[name]
            self.assertEqual(stack_trace["type"], single_trace["type"])
            stack_axis = stack_layout[y_layout_key(str(stack_trace["yaxis"]))]
            single_axis = single_layout[y_layout_key(str(single_trace["yaxis"]))]
            self.assertEqual(stack_axis["tickvals"], single_axis["tickvals"])
            self.assertEqual(stack_axis["ticktext"], single_axis["ticktext"])

    def test_300dpi_png_pdf_svg_and_offline_html_are_valid_high_quality_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "financial.csv"
            financial_frame().to_csv(data_path, index=False, date_format="%Y-%m-%d")
            config_path = root / "exports.json"
            config = default_project_config(data_path.name)
            config["project"].update(
                {
                    "title": "Export contract",
                    "subtitle": "",
                    "source": "",
                    "watermark": "",
                    "output_directory": "output",
                    "output_name": "export_contract",
                    "output_formats": ["png", "pdf", "svg", "html"],
                    "dpi": 300,
                    "width_inch": 15.5,
                    "panel_height_inch": 2.55,
                    "standard_panel_height_px": 420,
                }
            )
            config["charts"] = [dual_area_bar_chart()]
            write_json(config_path, config)
            report = render_stack(config_path)
            outputs = {Path(path).suffix: Path(path) for path in report["outputs"]}

            self.assertEqual(set(outputs), {".png", ".pdf", ".svg", ".html"})
            self.assertTrue(all(path.exists() and path.stat().st_size > 100 for path in outputs.values()))

            with Image.open(outputs[".png"]) as image:
                self.assertGreaterEqual(image.width, 4_000)
                self.assertGreaterEqual(image.height, 1_000)
                dpi = image.info.get("dpi")
                self.assertIsNotNone(dpi)
                assert dpi is not None
                self.assertTrue(all(295.0 <= float(value) <= 305.0 for value in dpi))

            pdf_bytes = outputs[".pdf"].read_bytes()
            self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
            self.assertIn(b"%%EOF", pdf_bytes[-1024:])
            self.assertNotIn(b"Plotly.newPlot", pdf_bytes)

            svg_root = ElementTree.parse(outputs[".svg"]).getroot()
            self.assertTrue(svg_root.tag.endswith("svg"))
            self.assertTrue(svg_root.attrib.get("width"))
            self.assertTrue(svg_root.attrib.get("height"))

            html = outputs[".html"].read_text(encoding="utf-8")
            self.assertIn("Plotly.newPlot", html)
            self.assertNotIn("<script src=", html.lower())
            self.assertNotIn("cdn.plot.ly", html.lower())

            panel = report["panels"][0]
            self.assertEqual(panel["axis_ticks"]["left"]["count"], 5)
            self.assertEqual(panel["axis_ticks"]["right"]["count"], 5)
            self.assertTrue(Path(report["report"]).exists())
            self.assertTrue(Path(report["audit"]).exists())


if __name__ == "__main__":
    unittest.main()
