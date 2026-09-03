from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from vap_data_adapter import discover_source, read_source_frame, sanitize_connection_url
from vap_defaults import built_in_defaults, load_defaults, save_defaults
from vap_seaborn_stack_generator import (
    apply_missing_policy,
    auto_configure_source,
    compute_locked_ticks,
    default_chart_spec,
    default_project_config,
    prepare_stack_values,
    render_stack,
    render_single_chart,
    write_json,
)


class VAPV2FeatureTests(unittest.TestCase):
    def test_connection_url_manifest_removes_password(self) -> None:
        safe = sanitize_connection_url("postgresql+psycopg://user:secret@db.example.com:5432/market")
        self.assertNotIn("secret", safe)
        self.assertIn("user@db.example.com", safe)

    def test_locked_ticks_are_five_equal_intervals_and_cover_data(self) -> None:
        ticks = compute_locked_ticks(-3.2, 8.7, tick_count=5, include_zero=True)
        self.assertEqual(len(ticks), 5)
        self.assertTrue(np.allclose(np.diff(ticks), np.diff(ticks)[0]))
        self.assertLessEqual(ticks[0], -3.2)
        self.assertGreaterEqual(ticks[-1], 8.7)
        self.assertTrue(ticks[0] <= 0 <= ticks[-1])

    def test_percent_stack_normalizes_rows(self) -> None:
        frame = pd.DataFrame({"A": [1.0, 2.0], "B": [3.0, 2.0], "C": [0.0, 4.0]})
        values = prepare_stack_values(frame, ["A", "B", "C"], "percent100")
        matrix = np.column_stack(values)
        self.assertTrue(np.allclose(matrix.sum(axis=1), 1.0))
        with self.assertRaisesRegex(ValueError, "非負"):
            prepare_stack_values(pd.DataFrame({"A": [1], "B": [-1]}), ["A", "B"], "percent100")

    def test_forward_fill_does_not_fill_volume_or_date(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": ["2026-01-01", None, "2026-01-03"],
                "AdjClose": [100.0, None, 102.0],
                "Volume": [1000.0, None, 1200.0],
            }
        )
        result = apply_missing_policy(frame, ["Date", "AdjClose", "Volume"], "ffill")
        self.assertEqual(result.loc[1, "AdjClose"], 100.0)
        self.assertTrue(pd.isna(result.loc[1, "Volume"]))
        self.assertTrue(pd.isna(result.loc[1, "Date"]))

    def test_sqlite_discovery_profiles_schema_and_suggests_dual_axis(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database_path = Path(temporary_directory) / "market.sqlite"
            with sqlite3.connect(database_path) as connection:
                connection.execute(
                    "CREATE TABLE prices (Date TEXT, Ticker TEXT, AdjClose REAL, Volume INTEGER, ForeignFlow REAL)"
                )
                connection.executemany(
                    "INSERT INTO prices VALUES (?, ?, ?, ?, ?)",
                    [
                        ("2026-01-01", "2330.TW", 1000.0, 120000, 1.2e8),
                        ("2026-01-01", "2317.TW", 200.0, 90000, 0.2e8),
                        ("2026-01-02", "2330.TW", 1015.0, 150000, -0.8e8),
                        ("2026-01-03", "2330.TW", 1020.0, 130000, 0.4e8),
                    ],
                )
            manifest = discover_source(
                {"kind": "sqlite", "path": str(database_path), "table": "prices"},
                sample_rows=100,
            )
            profiles = {column["name"]: column for column in manifest["columns"]}
            self.assertEqual(manifest["kind"], "sqlite")
            self.assertEqual(profiles["Date"]["semantic_type"], "datetime")
            self.assertEqual(profiles["Date"]["frequency"], "daily")
            self.assertEqual(profiles["AdjClose"]["semantic_type"], "price")
            self.assertEqual(profiles["Volume"]["semantic_type"], "volume")
            self.assertEqual(manifest["suggestion"]["axis_mode"], "dual")
            self.assertEqual(manifest["roles"]["grain"], "Ticker + Date")
            self.assertEqual(manifest["quality"]["date"]["duplicate_count"], 0)
            self.assertEqual(manifest["quality"]["date"]["duplicate_basis"], ["Ticker", "Date"])
            declared_names = [column["name"] for column in manifest["declared_schema"]["columns"]]
            self.assertEqual(declared_names, ["Date", "Ticker", "AdjClose", "Volume", "ForeignFlow"])
            frame = read_source_frame(
                {"kind": "sqlite", "path": str(database_path), "table": "prices"},
                columns=["Date", "AdjClose"],
                limit=2,
            )
            self.assertEqual(list(frame.columns), ["Date", "AdjClose"])
            self.assertEqual(len(frame), 2)

    def test_auto_config_and_single_chart_render(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "market.csv"
            pd.DataFrame(
                {
                    "Date": pd.date_range("2026-01-01", periods=20),
                    "AdjClose": np.linspace(100, 120, 20),
                    "Volume": np.arange(20) * 1000 + 10000,
                }
            ).to_csv(data_path, index=False)
            config_path = root / "auto.json"
            config, manifest, manifest_path = auto_configure_source(config_path, str(data_path), chart_id="auto_price")
            config["project"]["output_formats"] = ["png"]
            config["project"]["watermark"] = ""
            config["project"]["source"] = ""
            write_json(config_path, config)
            report = render_single_chart(config_path, "auto_price")
            self.assertEqual(manifest["suggestion"]["axis_mode"], "dual")
            self.assertTrue(manifest_path.exists())
            self.assertEqual(report["render_mode"], "single")
            self.assertEqual(report["chart_count"], 1)
            tick_report = report["panels"][0]["axis_ticks"]
            self.assertEqual(tick_report["left"]["count"], tick_report["right"]["count"])
            self.assertNotEqual(tick_report["left"]["step"], tick_report["right"]["step"])
            self.assertTrue(Path(report["outputs"][0]).exists())

    def test_single_axis_does_not_require_unused_secondary_column(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "single.csv"
            pd.DataFrame({"Date": ["2026-01-01", "2026-01-02"], "Close": [10, 11]}).to_csv(data_path, index=False)
            config_path = root / "single.json"
            config = default_project_config(data_path.name)
            config["project"].update({"output_formats": ["png"], "watermark": "", "source": ""})
            chart = default_chart_spec("single", "line", "Single", "Date", ["Close"])
            chart.update({"axis_mode": "single", "secondary_y": ["MissingRightAxis"]})
            config["charts"] = [chart]
            write_json(config_path, config)
            report = render_stack(config_path)
            self.assertEqual(report["status"], "OK")
            self.assertTrue(any("secondary_y" in warning for warning in report["warnings"]))

    def test_partial_defaults_file_merges_with_built_in_ssot(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "vap_defaults.json"
            defaults = built_in_defaults()
            defaults["project"]["dpi"] = 222
            save_defaults(path, defaults)
            loaded = load_defaults(path)
            self.assertEqual(loaded["project"]["dpi"], 222)
            self.assertIn("price_volume_dual", loaded["presets"])


if __name__ == "__main__":
    unittest.main()
