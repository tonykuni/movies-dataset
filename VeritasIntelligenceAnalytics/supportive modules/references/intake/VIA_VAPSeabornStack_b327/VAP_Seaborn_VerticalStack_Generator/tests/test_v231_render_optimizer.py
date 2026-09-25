from __future__ import annotations

import json
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from vap_render_optimizer import optimize_frame_for_chart
from vap_seaborn_stack_generator import (
    default_chart_spec,
    default_project_config,
    render_chart_collection,
)


class RenderOptimizerContractTests(unittest.TestCase):
    def test_frame_within_limit_is_value_identical_copy(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=3),
                "Price": [10.0, np.nan, 12.0],
            },
            index=pd.Index([10, 20, 30], name="row_id"),
        )

        result, report = optimize_frame_for_chart(
            frame,
            {"type": "line", "x": "Date", "y": ["Price"]},
            3,
        )

        pd.testing.assert_frame_equal(result, frame)
        self.assertIsNot(result, frame)
        self.assertFalse(report["optimized"])
        self.assertFalse(report["lossy"])
        self.assertEqual(report["method"], "none")
        result.loc[10, "Price"] = -1.0
        self.assertEqual(frame.loc[10, "Price"], 10.0)

    def test_invalid_max_points_is_rejected(self) -> None:
        frame = pd.DataFrame({"x": [1, 2], "y": [3, 4]})
        chart = {"type": "line", "x": "x", "y": ["y"]}
        for value in (0, 1, -1):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    optimize_frame_for_chart(frame, chart, value)
        for value in (True, 2.5, "10"):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    optimize_frame_for_chart(frame, chart, value)  # type: ignore[arg-type]

    def test_non_dataframe_and_non_mapping_are_rejected(self) -> None:
        with self.assertRaises(TypeError):
            optimize_frame_for_chart([], {"type": "line"}, 10)  # type: ignore[arg-type]
        with self.assertRaises(TypeError):
            optimize_frame_for_chart(pd.DataFrame(), [], 10)  # type: ignore[arg-type]


class CandlestickOptimizationTests(unittest.TestCase):
    def setUp(self) -> None:
        dates = pd.date_range("2024-01-02", periods=12, freq="B")
        opens = np.arange(100.0, 112.0)
        self.frame = pd.DataFrame(
            {
                "Date": dates,
                "Adj Open": opens,
                "Adj High": opens + np.array([1, 4, 2, 3] * 3),
                "Adj Low": opens - np.array([1, 3, 2, 4] * 3),
                "Adj Close": opens + np.array([0.5, -0.5] * 6),
                "Volume": [1.0, 2.0, np.nan, 4.0, *([np.nan] * 4), 8.0, 9.0, 10.0, 11.0],
                "NormalizedMomentum": np.arange(12.0) / 10.0,
                "Ticker": ["2330"] * 12,
            },
            index=pd.Index(np.arange(100, 112), name="source_row"),
        )
        self.chart = {
            "type": "candlestick",
            "x": "Date",
            "open": "Adj Open",
            "high": "Adj High",
            "low": "Adj Low",
            "close": "Adj Close",
            "volume": "Volume",
            "normalized_y": ["NormalizedMomentum"],
        }

    def test_ohlcv_uses_contiguous_buckets_without_filling_volume(self) -> None:
        untouched = self.frame.copy(deep=True)

        result, report = optimize_frame_for_chart(self.frame, self.chart, 3)

        self.assertEqual(len(result), 3)
        self.assertEqual(result["Date"].tolist(), [
            self.frame["Date"].iloc[0],
            self.frame["Date"].iloc[7],
            self.frame["Date"].iloc[11],
        ])
        self.assertEqual(result["Adj Open"].tolist(), [100.0, 104.0, 108.0])
        self.assertEqual(result["Adj Close"].tolist(), [102.5, 106.5, 110.5])
        self.assertEqual(result["Adj High"].tolist(), [106.0, 110.0, 114.0])
        self.assertEqual(result["Adj Low"].tolist(), [98.0, 102.0, 106.0])
        self.assertEqual(result["Volume"].iloc[0], 7.0)
        self.assertTrue(pd.isna(result["Volume"].iloc[1]))
        self.assertEqual(result["Volume"].iloc[2], 38.0)
        self.assertEqual(result["NormalizedMomentum"].tolist(), [0.3, 0.7, 1.1])
        self.assertEqual(result.index[[0, -1]].tolist(), [100, 111])
        self.assertEqual(report["method"], "ohlcv_contiguous_bucket_aggregation")
        self.assertTrue(report["lossy"])
        self.assertIn("min_count=1", report["warnings"][0])
        pd.testing.assert_frame_equal(self.frame, untouched)

    def test_case_insensitive_mapping_is_deterministic(self) -> None:
        lower_mapping = dict(self.chart)
        lower_mapping.update(
            {
                "x": "date",
                "open": "adj open",
                "high": "adj high",
                "low": "adj low",
                "close": "adj close",
                "volume": "volume",
            }
        )
        first, first_report = optimize_frame_for_chart(self.frame, lower_mapping, 4)
        second, second_report = optimize_frame_for_chart(self.frame, lower_mapping, 4)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(first_report, second_report)

    def test_missing_or_duplicate_ohlcv_mapping_is_rejected(self) -> None:
        missing = dict(self.chart, volume="NotThere")
        with self.assertRaisesRegex(ValueError, "volume"):
            optimize_frame_for_chart(self.frame, missing, 4)
        duplicate = dict(self.chart, close="Adj Open")
        with self.assertRaisesRegex(ValueError, "不同欄位"):
            optimize_frame_for_chart(self.frame, duplicate, 4)


class EnvelopeAndSamplingTests(unittest.TestCase):
    def test_line_envelope_merges_all_series_extrema_and_preserves_endpoints(self) -> None:
        size = 120
        frame = pd.DataFrame(
            {
                "Date": pd.date_range("2024-01-01", periods=size),
                "Left": np.sin(np.arange(size) / 3.0),
                "Right": np.cos(np.arange(size) / 5.0) * 10.0,
                "Normalized": ((np.arange(size) * 17) % 31).astype(float),
                "Label": [f"r{position}" for position in range(size)],
            },
            index=pd.Index(np.arange(1000, 1000 + size), name="source_row"),
        )
        frame.loc[17, "Left"] = -99.0
        frame.loc[42, "Right"] = 199.0
        frame.loc[83, "Normalized"] = -299.0
        chart = {
            "type": "line",
            "x": "Date",
            "y": ["Left"],
            "secondary_y": ["Right"],
            "normalized_y": ["Normalized"],
        }

        result, report = optimize_frame_for_chart(frame, chart, 20)

        self.assertLessEqual(len(result), 20)
        self.assertEqual(result.index[0], frame.index[0])
        self.assertEqual(result.index[-1], frame.index[-1])
        self.assertEqual(
            report["method"],
            "multi_series_first_min_max_last_envelope",
        )
        self.assertEqual(report["series"], ["Left", "Right", "Normalized"])

        bucket_count = report["bucket_count"]
        boundaries = np.linspace(0, len(frame), num=bucket_count + 1, dtype=np.int64)
        expected_positions: set[int] = {0, len(frame) - 1}
        for bucket_number in range(bucket_count):
            start = int(boundaries[bucket_number])
            stop = int(boundaries[bucket_number + 1])
            expected_positions.update({start, stop - 1})
            for name in report["series"]:
                values = frame[name].iloc[start:stop].to_numpy(dtype=float)
                expected_positions.add(start + int(np.nanargmin(values)))
                expected_positions.add(start + int(np.nanargmax(values)))
        selected_positions = {frame.index.get_loc(index) for index in result.index}
        self.assertEqual(selected_positions, expected_positions)

    def test_bar_stack_and_scatter_use_explicit_equidistant_sampling(self) -> None:
        frame = pd.DataFrame({"x": np.arange(101), "y": np.arange(101) ** 2})
        for chart_type in ("bar", "stacked_bar", "stacked_area_100", "scatter"):
            with self.subTest(chart_type=chart_type):
                result, report = optimize_frame_for_chart(
                    frame,
                    {"type": chart_type, "x": "x", "y": ["y"]},
                    12,
                )
                self.assertLessEqual(len(result), 12)
                self.assertEqual(result.index[[0, -1]].tolist(), [0, 100])
                self.assertEqual(report["method"], "equidistant_sampling")
                self.assertIn("局部尖峰", report["warnings"][0])

    def test_fifty_thousand_row_envelope_is_fast_and_keeps_spikes(self) -> None:
        size = 50_000
        values = np.sin(np.arange(size, dtype=float) / 40.0)
        values[12_345] = 10_000.0
        values[43_210] = -9_000.0
        frame = pd.DataFrame({"x": np.arange(size), "value": values})
        chart = {"type": "line", "x": "x", "y": ["value"]}

        started = time.perf_counter()
        result, report = optimize_frame_for_chart(frame, chart, 1_000)
        elapsed = time.perf_counter() - started

        self.assertLessEqual(len(result), 1_000)
        self.assertIn(12_345, result.index)
        self.assertIn(43_210, result.index)
        self.assertEqual(result.index[[0, -1]].tolist(), [0, size - 1])
        self.assertLess(elapsed, 5.0)
        self.assertEqual(report["input_points"], size)


class RenderCollectionOptimizationIntegrationTests(unittest.TestCase):
    def test_static_and_html_render_share_audited_optimized_frame(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "prices.csv"
            frame = pd.DataFrame(
                {
                    "Date": pd.date_range("2026-01-01", periods=120),
                    "Price": np.sin(np.arange(120) / 4.0),
                }
            )
            frame.loc[57, "Price"] = 999.0
            frame.to_csv(data_path, index=False)

            config_path = root / "stack.json"
            project = default_project_config(str(data_path))["project"]
            project.update(
                {
                    "output_directory": str(root / "output"),
                    "output_name": "optimized",
                    "output_formats": ["html"],
                    "render_max_points": 20,
                }
            )
            chart = default_chart_spec("price", "line", "Price", "Date", ["Price"])
            chart["render_max_points"] = None

            report = render_chart_collection(config_path, project, [chart])

            panel = report["panels"][0]
            optimization = panel["render_optimization"]
            self.assertEqual(panel["rows"], 120)
            self.assertLessEqual(panel["rendered_rows"], 20)
            self.assertTrue(optimization["optimized"])
            self.assertEqual(optimization["input_points"], 120)
            self.assertEqual(optimization["output_points"], panel["rendered_rows"])
            self.assertTrue(Path(report["outputs"][0]).exists())

            audit = json.loads(Path(report["audit"]).read_text(encoding="utf-8"))
            render_steps = [
                item
                for item in audit["transformations"]
                if item.get("action") == "render_optimize"
            ]
            self.assertEqual(len(render_steps), 1)
            self.assertEqual(render_steps[0]["chart_id"], "price")


if __name__ == "__main__":
    unittest.main()
