from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import pandas as pd

from vap_data_adapter import (
    SOURCE_SCHEMA,
    SOURCE_VERSION,
    detect_ohlcv_mapping,
    discover_source,
    normalize_source_spec,
    profile_frame,
    suggest_chart_mapping,
)
from vap_defaults import DEFAULTS_SCHEMA, built_in_defaults, load_defaults


class VAPV22DefaultsAdapterTests(unittest.TestCase):
    def test_v22_defaults_include_candlestick_plotly_and_opacity_controls(self) -> None:
        defaults = load_defaults()
        self.assertEqual(DEFAULTS_SCHEMA, "VIA-VAP-SEABORN-DEFAULTS/2.3")
        self.assertEqual(defaults["schema"], DEFAULTS_SCHEMA)
        self.assertEqual(defaults["version"], "2.3.1")
        self.assertEqual(defaults["project"]["html_renderer"], "plotly")
        self.assertEqual(defaults["project"]["palette"], "deep")
        self.assertEqual(defaults["chart"]["bar_alpha"], 0.75)
        self.assertEqual(defaults["chart"]["area_alpha"], 0.5)
        self.assertEqual(defaults["chart"]["candle_width_ratio"], 0.88)
        self.assertEqual(defaults["chart"]["up_color"], "#D62728")
        self.assertEqual(defaults["chart"]["down_color"], "#2CA02C")
        self.assertEqual(defaults["chart"]["normalized_y"], [])
        preset = defaults["presets"]["candlestick_volume"]
        self.assertEqual(preset["type"], "candlestick")
        self.assertEqual(preset["axis_mode"], "single")
        self.assertEqual(preset["missing"], "ffill")
        self.assertFalse(preset["derive_adjusted_prices"])
        self.assertEqual(defaults["changelog"][0]["version"], "2.3.1")
        self.assertEqual(defaults["changelog"][1]["version"], "2.3.0")
        self.assertEqual(defaults["changelog"][2]["version"], "2.2.0")
        self.assertEqual(built_in_defaults()["presets"]["candlestick_volume"]["volume"], "Volume")

    def test_adjusted_ohlcv_is_preferred_over_raw_prices(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": pd.date_range("2026-01-01", periods=3),
                "Open": [99.0, 100.0, 101.0],
                "High": [102.0, 103.0, 104.0],
                "Low": [98.0, 99.0, 100.0],
                "Close": [101.0, 102.0, 103.0],
                "AdjOpen": [49.5, 50.0, 50.5],
                "Adj High": [51.0, 51.5, 52.0],
                "AdjustedLow": [49.0, 49.5, 50.0],
                "Adj Close": [50.5, 51.0, 51.5],
                "Volume": [1000, 1200, 900],
            }
        )
        profiles = profile_frame(frame)
        mapping = detect_ohlcv_mapping(profiles)
        self.assertEqual(mapping["open"], "AdjOpen")
        self.assertEqual(mapping["high"], "Adj High")
        self.assertEqual(mapping["low"], "AdjustedLow")
        self.assertEqual(mapping["close"], "Adj Close")
        self.assertEqual(mapping["volume"], "Volume")
        self.assertTrue(mapping["adjusted_ohlc"])
        self.assertFalse(mapping["derive_adjusted_prices"])

        suggestion = suggest_chart_mapping(profiles)
        self.assertEqual(suggestion["chart_type"], "candlestick")
        self.assertEqual(suggestion["axis_mode"], "single")
        self.assertEqual(suggestion["preset"], "candlestick_volume")
        self.assertEqual(suggestion["open"], "AdjOpen")
        self.assertEqual(suggestion["close"], "Adj Close")
        self.assertEqual(suggestion["y"], [])
        self.assertEqual(suggestion["secondary_y"], [])
        self.assertEqual(suggestion["price_basis"], "adjusted")
        self.assertFalse(suggestion["derive_adjusted_prices"])

    def test_raw_ohlcv_is_not_mislabeled_as_adjusted_candlestick(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": pd.date_range("2026-01-01", periods=3),
                "Open": [99.0, 100.0, 101.0],
                "High": [102.0, 103.0, 104.0],
                "Low": [98.0, 99.0, 100.0],
                "Close": [101.0, 102.0, 103.0],
                "Volume": [1000, 1200, 900],
            }
        )
        profiles = profile_frame(frame)
        mapping = detect_ohlcv_mapping(profiles)
        self.assertTrue(mapping["complete"])
        self.assertFalse(mapping["adjusted_ohlc"])
        self.assertFalse(mapping["derive_adjusted_prices"])
        suggestion = suggest_chart_mapping(profiles)
        self.assertEqual(suggestion["chart_type"], "line")
        self.assertNotEqual(suggestion["preset"], "candlestick_volume")

    def test_discovery_and_source_spec_emit_v22_schema_and_version(self) -> None:
        spec = normalize_source_spec({"kind": "csv", "path": "market.csv", "schema": "legacy"})
        self.assertEqual(spec["schema"], SOURCE_SCHEMA)
        self.assertEqual(spec["version"], SOURCE_VERSION)
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "market.csv"
            pd.DataFrame(
                {
                    "Date": pd.date_range("2026-01-01", periods=3),
                    "Adj Open": [99.0, 100.0, 101.0],
                    "Adj High": [102.0, 103.0, 104.0],
                    "Adj Low": [98.0, 99.0, 100.0],
                    "Adj Close": [101.0, 102.0, 103.0],
                    "Volume": [1000, 1200, 900],
                }
            ).to_csv(path, index=False)
            manifest = discover_source(path)
        self.assertEqual(manifest["schema"], SOURCE_SCHEMA)
        self.assertEqual(manifest["version"], SOURCE_VERSION)
        self.assertEqual(manifest["source"]["schema"], SOURCE_SCHEMA)
        self.assertEqual(manifest["source"]["version"], SOURCE_VERSION)
        self.assertEqual(manifest["suggestion"]["chart_type"], "candlestick")


if __name__ == "__main__":
    unittest.main()
