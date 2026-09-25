from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
import warnings
from copy import deepcopy
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pandas as pd

from vap_chart_library import (
    append_library_chart,
    get_chart_item,
    load_chart_library,
    search_charts,
    upsert_chart,
)
from vap_data_adapter import detect_source_kind, discover_source, read_source_frame
from vap_seaborn_stack_generator import (
    append_chart_spec,
    auto_configure_source,
    move_chart_spec,
    read_json,
    remove_chart_spec,
    render_single_chart,
    render_stack,
    write_json,
)


def adjusted_ohlcv_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Date": pd.bdate_range("2026-08-17", periods=7),
            "AdjOpen": [100.0, 101.0, 102.0, 104.0, 103.0, 105.0, 106.0],
            "AdjHigh": [102.0, 103.0, 104.0, 105.0, 106.0, 108.0, 109.0],
            "AdjLow": [99.0, 100.0, 101.0, 102.0, 102.0, 104.0, 105.0],
            "AdjClose": [101.0, 102.0, 103.0, 102.5, 105.0, 107.0, 108.0],
            "Volume": [1_000, 1_100, 900, 1_300, 1_200, 1_400, 1_250],
        }
    )


def configure_fast_uat_outputs(config_path: Path) -> dict[str, object]:
    config = read_json(config_path)
    config["project"].update(
        {
            "output_formats": ["html", "png"],
            "output_directory": "output",
            "output_name": "vap_v231_uat",
            "dpi": 72,
            "width_inch": 5.5,
            "panel_height_inch": 0.8,
            "source": "",
            "watermark": "",
        }
    )
    write_json(config_path, config)
    return config


def render_without_missing_glyph_noise(renderer, *args):
    # Linux CI may not have a CJK font even though Windows end users do.  This
    # warning does not affect the generated artifact, so keep UAT output clear.
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", message=r"Glyph .* missing from font")
        return renderer(*args)


class VAPV231UserAcceptanceTests(unittest.TestCase):
    def test_extensionless_cp950_csv_is_discovered_and_read_without_user_hints(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "台股日資料"
            expected = pd.DataFrame(
                {
                    "日期": ["2026-08-17", "2026-08-18", "2026-08-19"],
                    "收盤價": [101.5, 102.0, 103.25],
                    "成交量": [1_000, 1_200, 980],
                }
            )
            expected.to_csv(source_path, index=False, encoding="cp950")

            self.assertEqual(detect_source_kind(source_path), "csv")
            manifest = discover_source(source_path)
            loaded = read_source_frame(source_path)

        self.assertEqual(manifest["status"], "OK")
        self.assertEqual(manifest["kind"], "csv")
        self.assertEqual(manifest["sample_rows"], 3)
        self.assertEqual([column["name"] for column in manifest["columns"]], list(expected.columns))
        self.assertEqual(loaded["日期"].tolist(), expected["日期"].tolist())
        self.assertEqual(loaded["成交量"].tolist(), expected["成交量"].tolist())
        self.assertEqual(manifest["suggestion"]["axis_mode"], "dual")

    @unittest.skipUnless(
        importlib.util.find_spec("pyarrow") is not None
        or importlib.util.find_spec("fastparquet") is not None,
        "Parquet UAT requires the pyarrow/fastparquet dependency from requirements.txt",
    )
    def test_extensionless_parquet_is_discovered_with_adjusted_ohlcv_schema(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "adjusted_prices"
            expected = adjusted_ohlcv_frame()
            expected.to_parquet(source_path, index=False)

            self.assertEqual(detect_source_kind(source_path), "parquet")
            manifest = discover_source(source_path)
            loaded = read_source_frame(source_path)

        self.assertEqual(manifest["kind"], "parquet")
        self.assertEqual(manifest["suggestion"]["chart_type"], "candlestick")
        self.assertEqual(manifest["suggestion"]["price_basis"], "adjusted")
        self.assertEqual(manifest["suggestion"]["open"], "AdjOpen")
        self.assertEqual(manifest["suggestion"]["volume"], "Volume")
        pd.testing.assert_frame_equal(loaded, expected)

    def test_full_no_display_user_workflow_from_auto_config_to_gallery_and_stack(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_path = root / "utf8_market_data"
            config_path = root / "vap_stack.json"
            library_path = root / "vap_chart_library.json"
            adjusted_ohlcv_frame().to_csv(
                source_path,
                index=False,
                encoding="utf-8-sig",
                date_format="%Y-%m-%d",
            )

            config, manifest, manifest_path = auto_configure_source(
                config_path,
                str(source_path),
            )
            self.assertTrue(config_path.is_file())
            self.assertTrue(manifest_path.is_file())
            self.assertEqual(manifest["kind"], "csv")
            self.assertEqual(manifest["suggestion"]["chart_type"], "candlestick")
            self.assertEqual(config["charts"][0]["axis_mode"], "single")
            self.assertEqual(config["charts"][0]["price_basis"], "adjusted")
            self.assertEqual(config["charts"][0]["secondary_y"], [])
            with self.assertRaises(FileExistsError):
                auto_configure_source(config_path, str(source_path))

            config = configure_fast_uat_outputs(config_path)
            with self.assertRaises(KeyError):
                render_without_missing_glyph_noise(
                    render_single_chart,
                    config_path,
                    "does_not_exist",
                )
            single_report = render_without_missing_glyph_noise(
                render_single_chart,
                config_path,
                "auto_chart",
            )
            self.assertEqual(single_report["status"], "OK")
            self.assertEqual(single_report["render_mode"], "single")
            self.assertEqual(single_report["chart_count"], 1)
            self.assertEqual(single_report["render_panel_count"], 2)
            self.assertEqual(
                {Path(output).suffix for output in single_report["outputs"]},
                {".html", ".png"},
            )
            for raw_output in single_report["outputs"]:
                output_path = Path(raw_output)
                self.assertTrue(output_path.is_file())
                self.assertGreater(output_path.stat().st_size, 500)

            original_chart = deepcopy(config["charts"][0])
            library_item = upsert_chart(
                library_path,
                original_chart,
                name="Adjusted OHLCV Template",
                tags=["UAT", "stock", "uat"],
                description="Reusable chart design without embedded rows",
            )
            library = load_chart_library(library_path, create=False)
            self.assertEqual(library["metadata"]["item_count"], 1)
            self.assertEqual(library_item["tags"], ["UAT", "stock"])
            self.assertEqual(
                get_chart_item(library_path, library_item["id"])["chart"],
                original_chart,
            )
            matches = search_charts(
                library_path,
                query="AdjClose",
                tags=["stock"],
                chart_type="candlestick",
            )
            self.assertEqual([item["id"] for item in matches], [library_item["id"]])

            gallery_chart = append_library_chart(
                config_path,
                library_path,
                library_item["id"],
            )
            self.assertEqual(gallery_chart["id"], "auto_chart_2")
            self.assertEqual(gallery_chart["gallery_item_id"], library_item["id"])

            duplicate = deepcopy(read_json(config_path)["charts"][0])
            duplicate["id"] = "auto_chart"
            duplicated_chart = append_chart_spec(config_path, duplicate)
            self.assertEqual(duplicated_chart["id"], "auto_chart_3")
            self.assertTrue(move_chart_spec(config_path, "auto_chart_3", 1))
            self.assertTrue(remove_chart_spec(config_path, "auto_chart_2"))
            self.assertFalse(remove_chart_spec(config_path, "missing_chart"))
            final_config = read_json(config_path)
            self.assertEqual(
                [chart["id"] for chart in final_config["charts"]],
                ["auto_chart_3", "auto_chart"],
            )

            stack_report = render_without_missing_glyph_noise(render_stack, config_path)
            self.assertEqual(stack_report["status"], "OK")
            self.assertEqual(stack_report["render_mode"], "stack")
            self.assertEqual(stack_report["chart_count"], 2)
            self.assertEqual(stack_report["render_panel_count"], 4)
            self.assertEqual(
                {Path(output).suffix for output in stack_report["outputs"]},
                {".html", ".png"},
            )
            self.assertTrue(all(Path(output).is_file() for output in stack_report["outputs"]))
            self.assertTrue(Path(stack_report["audit"]).is_file())
            self.assertTrue(Path(stack_report["report"]).is_file())

            saved_report = json.loads(Path(stack_report["report"]).read_text(encoding="utf-8"))
            saved_audit = json.loads(Path(stack_report["audit"]).read_text(encoding="utf-8"))
            self.assertEqual(saved_report["render_mode"], "stack")
            self.assertFalse(Path(saved_report["config"]).is_absolute())
            self.assertTrue(all(not Path(path).is_absolute() for path in saved_report["outputs"]))
            self.assertEqual(saved_audit["schema"], "VIA-VAP-DIAGNOSTICS/2.3")
            self.assertEqual([chart["chart_id"] for chart in saved_audit["charts"]], ["auto_chart_3", "auto_chart"])
            self.assertEqual(list(root.rglob("*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
