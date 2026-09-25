from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from vap_seaborn_stack_generator import (
    append_chart_spec,
    default_chart_spec,
    default_project_config,
    make_demo_config,
    move_chart_spec,
    read_json,
    remove_chart_spec,
    render_stack,
    write_json,
)


class VAPSeabornStackTests(unittest.TestCase):
    def test_demo_renders_all_formats_and_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            config_path = root / "examples" / "demo_stack.json"
            make_demo_config(config_path)
            report = render_stack(config_path)
            self.assertEqual(report["status"], "OK")
            self.assertEqual(report["chart_count"], 5)
            self.assertEqual(len(report["panels"]), 5)
            for output in report["outputs"]:
                output_path = Path(output)
                self.assertTrue(output_path.exists())
                self.assertGreater(output_path.stat().st_size, 1_000)
            self.assertTrue(Path(report["report"]).exists())
            saved_report = json.loads(Path(report["report"]).read_text(encoding="utf-8"))
            self.assertFalse(Path(saved_report["config"]).is_absolute())
            self.assertTrue(all(not Path(path).is_absolute() for path in saved_report["outputs"]))
            self.assertFalse(Path(saved_report["audit"]).is_absolute())
            self.assertFalse(Path(saved_report["report"]).is_absolute())
            audit = json.loads(Path(report["audit"]).read_text(encoding="utf-8"))
            self.assertEqual(audit["schema"], "VIA-VAP-DIAGNOSTICS/2.3")
            self.assertEqual(len(audit["charts"]), 5)
            self.assertIn("before", audit["charts"][0])
            self.assertIn("after", audit["charts"][0])
            self.assertIn("data_changed", audit)

    def test_append_move_and_remove(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "stack.json"
            config = default_project_config("data.csv")
            write_json(config_path, config)
            first = default_chart_spec("price", "line", "Price", "Date", ["Close"])
            second = default_chart_spec("volume", "bar", "Volume", "Date", ["Volume"])
            append_chart_spec(config_path, first)
            append_chart_spec(config_path, second)
            self.assertTrue(move_chart_spec(config_path, "volume", 1))
            loaded = read_json(config_path)
            self.assertEqual([chart["id"] for chart in loaded["charts"]], ["volume", "price"])
            self.assertTrue(remove_chart_spec(config_path, "price"))
            self.assertFalse(remove_chart_spec(config_path, "missing"))
            loaded = read_json(config_path)
            self.assertEqual([chart["id"] for chart in loaded["charts"]], ["volume"])

    def test_duplicate_id_is_renamed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "stack.json"
            write_json(config_path, default_project_config("data.csv"))
            chart = default_chart_spec("price", "line", "Price", "Date", ["Close"])
            first = append_chart_spec(config_path, chart.copy())
            second = append_chart_spec(config_path, chart.copy())
            self.assertEqual(first["id"], "price")
            self.assertEqual(second["id"], "price_2")

    def test_invalid_data_column_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "data.csv"
            data_path.write_text("Date,Close\n2026-01-01,100\n", encoding="utf-8")
            config_path = root / "stack.json"
            config = default_project_config(data_path.name)
            config["project"]["output_formats"] = ["png"]
            config["charts"] = [default_chart_spec("bad", "line", "Bad", "Date", ["Missing"])]
            write_json(config_path, config)
            with self.assertRaisesRegex(ValueError, "找不到欄位"):
                render_stack(config_path)

    def test_all_chart_types_render(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "all_types.csv"
            rows = ["Date,A,B,C,Group,Month,Return"]
            for index in range(1, 25):
                month = f"M{((index - 1) % 6) + 1}"
                group = f"G{((index - 1) % 4) + 1}"
                rows.append(f"2026-01-{index:02d},{100 + index},{index * 2},{index - 12},{group},{month},{(index - 12) / 100}")
            data_path.write_text("\n".join(rows) + "\n", encoding="utf-8")
            config_path = root / "all_types.json"
            config = default_project_config(data_path.name)
            config["project"].update(
                {
                    "output_formats": ["png"],
                    "output_name": "all_types",
                    "output_directory": "output",
                    "source": "",
                    "watermark": "",
                    "panel_height_inch": 1.2,
                }
            )
            config["charts"] = [
                default_chart_spec("line", "line", "Line", "Date", ["A", "B"]),
                default_chart_spec("bar", "bar", "Bar", "Date", ["B"]),
                default_chart_spec("area", "area", "Area", "Date", ["C"]),
                default_chart_spec("scatter", "scatter", "Scatter", "Date", ["A"]),
                default_chart_spec("step", "step", "Step", "Date", ["B"]),
                default_chart_spec("stacked_bar", "stacked_bar", "Stacked Bar", "Date", ["B", "C"]),
                default_chart_spec("stacked_area", "stacked_area", "Stacked Area", "Date", ["A", "B"]),
                {
                    "id": "heatmap",
                    "type": "heatmap",
                    "title": "Heatmap",
                    "heatmap_index": "Group",
                    "heatmap_columns": "Month",
                    "heatmap_value": "Return",
                    "height_ratio": 1.2,
                    "missing": "none",
                    "unit": "%",
                    "show_legend": False,
                },
            ]
            write_json(config_path, config)
            report = render_stack(config_path)
            self.assertEqual(report["chart_count"], 8)
            self.assertTrue(Path(report["outputs"][0]).exists())


if __name__ == "__main__":
    unittest.main()
