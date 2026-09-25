from __future__ import annotations

import unittest
from unittest.mock import patch

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

from vap_seaborn_stack_generator import (
    draw_stacked_area_chart,
    format_panel,
    prepare_stack_values,
)


class RecordingAxes:
    def __init__(self) -> None:
        self.stackplot_calls: list[tuple[tuple, dict]] = []

    def stackplot(self, *args, **kwargs) -> None:
        self.stackplot_calls.append((args, kwargs))

    def set_ylim(self, *_args) -> None:
        return None


class VAPV21StackSafetyTests(unittest.TestCase):
    def test_missing_stack_values_are_not_silently_zero_filled(self) -> None:
        frame = pd.DataFrame({"A": [1.0, np.nan], "B": [2.0, 3.0]})
        with self.assertRaisesRegex(ValueError, "空值或非有限值"):
            prepare_stack_values(frame, ["A", "B"], "absolute")

    def test_percent_stack_rejects_zero_total_rows(self) -> None:
        frame = pd.DataFrame({"A": [0.0, 1.0], "B": [0.0, 2.0]})
        with self.assertRaisesRegex(ValueError, "合計必須大於 0"):
            prepare_stack_values(frame, ["A", "B"], "percent100")

    def test_signed_area_uses_separate_positive_and_negative_stacks(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": pd.date_range("2026-01-01", periods=2),
                "A": [2.0, -3.0],
                "B": [-1.0, 4.0],
            }
        )
        axes = RecordingAxes()
        chart = {"x": "Date", "y": ["A", "B"], "type": "stacked_area", "stack_mode": "absolute"}
        draw_stacked_area_chart(axes, frame, chart, ["#111111", "#222222"])
        self.assertEqual(len(axes.stackplot_calls), 2)
        positive_args = axes.stackplot_calls[0][0][1:]
        negative_args = axes.stackplot_calls[1][0][1:]
        self.assertTrue(all(np.all(values >= 0) for values in positive_args))
        self.assertTrue(all(np.all(values <= 0) for values in negative_args))

    def test_auto_optimize_switch_can_defer_date_tick_optimization(self) -> None:
        figure, axes = plt.subplots()
        axes.plot(pd.date_range("2026-01-01", periods=2), [1.0, 2.0])
        chart = {
            "id": "manual_layout",
            "type": "line",
            "unit": "",
            "x_label": "",
            "show_zero_line": False,
            "show_legend": False,
            "y_format": "auto",
            "tick_policy": "auto",
            "tick_count": 5,
            "stack_mode": "absolute",
            "auto_optimize": False,
        }
        try:
            with patch("vap_seaborn_stack_generator.format_date_axis") as optimizer:
                format_panel(axes, None, chart, {}, is_last=True, x_is_date=True)
                optimizer.assert_not_called()
        finally:
            plt.close(figure)


if __name__ == "__main__":
    unittest.main()
