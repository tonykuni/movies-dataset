from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

import matplotlib

matplotlib.use("Agg")

import pandas as pd

from vap_atomic_io import (
    atomic_write_text,
    cleanup_stale_temporary_files,
)
from vap_chart_library import (
    default_chart_library,
    load_chart_library,
    upsert_chart,
    validate_chart_library,
    validate_chart_spec as validate_library_chart_spec,
)
from vap_data_adapter import (
    DEFAULT_MAX_ROWS,
    detect_source_kind,
    discover_source,
    list_sqlite_tables,
    read_source_frame,
    sqlite_readonly_uri,
)
from vap_defaults import built_in_defaults, validate_defaults
from vap_seaborn_stack_generator import (
    append_chart_spec,
    default_chart_spec,
    default_project_config,
    read_json,
    safe_relpath,
    validate_config,
    write_json,
)
from vap_seaborn_stack_ui import (
    DEFAULT_LIBRARY_FILENAME,
    chart_form_values_from_spec,
    chart_library_path_for_config,
    chart_spec_from_form_values,
    merge_chart_form_update,
)


PLOTLY_AVAILABLE = importlib.util.find_spec("plotly") is not None


def reusable_line_chart(chart_id: str = "race") -> dict[str, object]:
    chart = default_chart_spec(
        chart_id,
        "line",
        "Adjusted price",
        "Date",
        ["AdjClose"],
    )
    chart.update({"axis_mode": "single", "secondary_y": []})
    return chart


class VAPV231RegressionTests(unittest.TestCase):
    def test_non_finite_visual_numbers_are_rejected_at_all_entry_points(self) -> None:
        chart = reusable_line_chart("finite")
        for field_name in (
            "line_width",
            "secondary_line_width",
            "alpha",
            "bar_alpha",
            "area_alpha",
            "bar_width_ratio",
            "outlier_iqr_multiplier",
        ):
            with self.subTest(entry="config", field=field_name):
                candidate = deepcopy(chart)
                candidate[field_name] = float("nan")
                config = default_project_config()
                config["charts"] = [candidate]
                with self.assertRaises(ValueError):
                    validate_config(config)

        defaults = built_in_defaults()
        defaults["project"]["width_inch"] = float("nan")
        with self.assertRaises(ValueError):
            validate_defaults(defaults)

        values = chart_form_values_from_spec(chart)
        values["line_width"] = "nan"
        with self.assertRaises(ValueError):
            chart_spec_from_form_values(values)

    def test_sqlite_special_character_path_is_read_only_and_query_projection_works(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            database_path = root / "market #? 2026.sqlite"
            with sqlite3.connect(database_path) as connection:
                connection.execute(
                    "CREATE TABLE quotes (Date TEXT, AdjClose REAL, Volume INTEGER, Note TEXT)"
                )
                connection.executemany(
                    "INSERT INTO quotes VALUES (?, ?, ?, ?)",
                    [
                        ("2026-08-31", 100.0, 1_000, "a"),
                        ("2026-09-01", 101.5, 1_200, "b"),
                        ("2026-09-02", 99.5, 900, "c"),
                    ],
                )

            original_bytes = database_path.read_bytes()
            uri = sqlite_readonly_uri(database_path)
            self.assertIn("%23", uri)
            self.assertIn("%3F", uri)
            self.assertTrue(uri.endswith("?mode=ro"))
            self.assertEqual(list_sqlite_tables(database_path), ["quotes"])

            projected = read_source_frame(
                {
                    "kind": "sqlite",
                    "path": str(database_path),
                    "query": "SELECT Date, AdjClose, Volume, Note FROM quotes WHERE AdjClose >= 99",
                },
                columns=["Date", "Volume"],
                limit=2,
            )
            self.assertEqual(list(projected.columns), ["Date", "Volume"])
            self.assertEqual(len(projected), 2)
            self.assertEqual(database_path.read_bytes(), original_bytes)

            missing_path = root / "missing #?.sqlite"
            with self.assertRaises(sqlite3.OperationalError):
                list_sqlite_tables(missing_path)
            self.assertFalse(missing_path.exists(), "read-only discovery must not create a DB")
            self.assertEqual(
                {path.name for path in root.iterdir()},
                {database_path.name},
                "URI punctuation must not create a second, truncated database path",
            )

    def test_semicolon_csv_is_sniffed_and_projected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "semicolon_feed"
            source_path.write_text(
                "Date;AdjClose;Volume\n"
                "2026-08-31;100.25;1000\n"
                "2026-09-01;101.50;1200\n",
                encoding="utf-8",
            )

            self.assertEqual(detect_source_kind(source_path), "csv")
            frame = read_source_frame(
                source_path,
                columns=["Date", "AdjClose"],
                limit=1,
            )
            manifest = discover_source(source_path, sample_rows=2)

        self.assertEqual(list(frame.columns), ["Date", "AdjClose"])
        self.assertEqual(frame.iloc[0]["AdjClose"], 100.25)
        self.assertEqual(manifest["sample_rows"], 2)
        self.assertEqual(
            [column["name"] for column in manifest["columns"]],
            ["Date", "AdjClose", "Volume"],
        )

    def test_sample_rows_and_limit_enforce_integer_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "small.csv"
            pd.DataFrame(
                {
                    "Date": ["2026-08-31", "2026-09-01", "2026-09-02"],
                    "AdjClose": [100.0, 101.0, 102.0],
                }
            ).to_csv(source_path, index=False)

            self.assertEqual(len(read_source_frame(source_path, limit=None)), 3)
            self.assertEqual(len(read_source_frame(source_path, limit=1)), 1)
            self.assertEqual(
                len(read_source_frame(source_path, limit=DEFAULT_MAX_ROWS)),
                3,
            )
            self.assertEqual(discover_source(source_path, sample_rows=1)["sample_rows"], 1)
            self.assertEqual(
                discover_source(source_path, sample_rows=DEFAULT_MAX_ROWS)["sample_rows"],
                3,
            )

            invalid_values = (True, 0, -1, 1.5, DEFAULT_MAX_ROWS + 1)
            for value in invalid_values:
                with self.subTest(api="read_source_frame", value=value):
                    with self.assertRaises(ValueError):
                        read_source_frame(source_path, limit=value)  # type: ignore[arg-type]
                with self.subTest(api="discover_source", value=value):
                    with self.assertRaises(ValueError):
                        discover_source(source_path, sample_rows=value)  # type: ignore[arg-type]

    def test_discovery_manifest_omits_samples_queries_and_secret_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            source_path = Path(temporary_directory) / "manifest.csv"
            pd.DataFrame(
                {
                    "Date": ["2026-09-01", "2026-09-02"],
                    "AdjClose": [100.0, 101.0],
                }
            ).to_csv(source_path, index=False)
            manifest = discover_source(
                {
                    "kind": "csv",
                    "path": str(source_path),
                    "query": "SELECT * FROM source -- SECRET_QUERY_TEXT",
                    "password": "SECRET_DB_PASSWORD",
                    "apiToken": "SECRET_API_TOKEN",
                    "privateKey": "SECRET_PRIVATE_KEY",
                },
                sample_rows=2,
            )

        serialized = json.dumps(manifest, ensure_ascii=False)
        folded = serialized.casefold()
        self.assertNotIn("sample_values", folded)
        self.assertNotIn("secret_query_text", folded)
        self.assertNotIn("secret_db_password", folded)
        self.assertNotIn("secret_api_token", folded)
        self.assertNotIn("secret_private_key", folded)
        self.assertNotIn('"password"', folded)
        self.assertNotIn('"apitoken"', folded)
        self.assertNotIn('"privatekey"', folded)
        self.assertEqual(manifest["source"]["query"], "REDACTED")
        self.assertTrue(manifest["source"]["query_present"])
        self.assertTrue(
            all("sample_values" not in column for column in manifest["columns"])
        )

    def test_parquet_dataset_table_cannot_traverse_outside_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            dataset_root = root / "dataset"
            dataset_root.mkdir()
            outside = root / "outside.parquet"

            for table in ("../outside.parquet", "nested/../../outside.parquet", str(outside)):
                with self.subTest(table=table):
                    with self.assertRaisesRegex(ValueError, "根目錄"):
                        read_source_frame(
                            {
                                "kind": "parquet_dataset",
                                "path": str(dataset_root),
                                "table": table,
                            },
                            limit=1,
                        )

    def test_gallery_rejects_payload_numeric_nesting_and_root_metadata_rows(self) -> None:
        payload_chart = reusable_line_chart("payload")
        payload_chart["payload"] = {"records": [{"Date": "2026-09-02", "AdjClose": 1}]}
        with self.assertRaises(ValueError):
            validate_library_chart_spec(payload_chart)

        numeric_nested_chart = reusable_line_chart("numeric_nested")
        numeric_nested_chart["colors"] = {"AdjClose": [214, 39, 40]}
        with self.assertRaises(ValueError):
            validate_library_chart_spec(numeric_nested_chart)

        library = default_chart_library()
        library["metadata"]["rows"] = [{"Date": "2026-09-02"}]
        with self.assertRaises(ValueError):
            validate_chart_library(library)

    def test_gallery_redacts_camel_case_and_scalar_url_secrets(self) -> None:
        chart = reusable_line_chart("secrets")
        chart["data_source"] = {
            "kind": "sqlalchemy",
            "url": (
                "postgresql://alice:db-password@db.example/vap"
                "?apiToken=query-token&sslmode=require#fragment-token"
            ),
            "apiToken": "body-token",
            "clientSecret": "client-secret",
            "privateKey": "private-key",
        }
        normalized_chart = validate_library_chart_spec(chart)
        source = normalized_chart["data_source"]
        self.assertEqual(source["apiToken"], "REDACTED")
        self.assertEqual(source["clientSecret"], "REDACTED")
        self.assertEqual(source["privateKey"], "REDACTED")
        self.assertNotIn("db-password", source["url"])
        self.assertNotIn("query-token", source["url"])
        self.assertNotIn("fragment-token", source["url"])
        self.assertIn("apiToken=REDACTED", source["url"])
        self.assertIn("sslmode=require", source["url"])

        library = default_chart_library()
        library["metadata"].update(
            {
                "apiToken": "root-token",
                "connectionUrl": (
                    "postgresql://bob:root-password@db.example/vap"
                    "?accessToken=root-query-token"
                ),
            }
        )
        normalized_library = validate_chart_library(library)
        metadata = normalized_library["metadata"]
        self.assertEqual(metadata["apiToken"], "REDACTED")
        self.assertNotIn("root-password", metadata["connectionUrl"])
        self.assertNotIn("root-query-token", metadata["connectionUrl"])
        self.assertIn("accessToken=REDACTED", metadata["connectionUrl"])

    def test_concurrent_config_appends_keep_all_twelve_charts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            config_path = root / "stack.json"
            config = default_project_config("source.csv")
            config["charts"] = []
            write_json(config_path, config)

            def append_one(_index: int) -> str:
                return str(append_chart_spec(config_path, reusable_line_chart())["id"])

            with ThreadPoolExecutor(max_workers=12) as executor:
                returned_ids = list(executor.map(append_one, range(12)))

            saved = read_json(config_path)
            saved_ids = [str(chart["id"]) for chart in saved["charts"]]
            self.assertEqual(len(returned_ids), 12)
            self.assertEqual(len(set(returned_ids)), 12)
            self.assertCountEqual(returned_ids, saved_ids)
            self.assertEqual(len(saved_ids), 12)
            self.assertEqual(list(root.glob(".stack.json.*.tmp")), [])

    def test_concurrent_gallery_appends_keep_all_twelve_items(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            gallery_path = root / "vap_chart_library.json"

            def save_one(_index: int) -> str:
                item = upsert_chart(
                    gallery_path,
                    reusable_line_chart(),
                    name="race",
                    tags=["concurrency"],
                )
                return str(item["id"])

            with ThreadPoolExecutor(max_workers=12) as executor:
                returned_ids = list(executor.map(save_one, range(12)))

            library = load_chart_library(gallery_path, create=False)
            saved_ids = [str(item["id"]) for item in library["items"]]
            self.assertEqual(len(returned_ids), 12)
            self.assertEqual(len(set(returned_ids)), 12)
            self.assertCountEqual(returned_ids, saved_ids)
            self.assertEqual(library["metadata"]["item_count"], 12)
            self.assertEqual(list(root.glob(".vap_chart_library.json.*.tmp")), [])

    def test_safe_relpath_falls_back_to_absolute_path_across_drives(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            target = root / "output" / "report.json"
            start = root / "other-drive"
            with patch(
                "vap_seaborn_stack_generator.os.path.relpath",
                side_effect=ValueError("path is on mount C:, start on mount D:"),
            ):
                result = safe_relpath(target, start)

        self.assertEqual(result, str(target.resolve()))
        self.assertTrue(Path(result).is_absolute())

    def test_ui_single_axis_drops_stale_secondary_series(self) -> None:
        source = reusable_line_chart("single_axis")
        source.update(
            {
                "axis_mode": "dual",
                "secondary_y": ["Volume"],
                "secondary_type": "bar",
                "secondary_unit": "Shares",
            }
        )
        values = chart_form_values_from_spec(source, defaults={})
        values["axis_mode"] = "single"
        rebuilt = chart_spec_from_form_values(values)

        self.assertEqual(rebuilt["axis_mode"], "single")
        self.assertEqual(rebuilt["secondary_y"], [])

    def test_form_update_preserves_hidden_chart_keys(self) -> None:
        existing = reusable_line_chart("hidden")
        existing.update(
            {
                "where": "Ticker = '2330.TW'",
                "data_source": {"kind": "parquet", "path": "StockData.parquet"},
                "left_axis": {"enabled": True, "series": ["AdjClose"]},
                "custom_plugin_option": {"mode": "governed"},
            }
        )
        before = deepcopy(existing)
        form_chart = deepcopy(existing)
        form_chart.update({"title": "Edited title", "y": ["AdjClose", "MA20"]})
        for hidden_key in ("where", "data_source", "left_axis", "custom_plugin_option"):
            form_chart.pop(hidden_key, None)

        merged = merge_chart_form_update(existing, form_chart, replace_hidden=False)

        self.assertEqual(merged["title"], "Edited title")
        self.assertEqual(merged["y"], ["AdjClose", "MA20"])
        self.assertEqual(merged["where"], before["where"])
        self.assertEqual(merged["data_source"], before["data_source"])
        self.assertEqual(merged["left_axis"], before["left_axis"])
        self.assertEqual(
            merged["custom_plugin_option"],
            before["custom_plugin_option"],
        )
        self.assertEqual(existing, before)

    def test_default_gallery_path_is_adjacent_to_active_config(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "portable project" / "stack.json"
            expected = config_path.resolve().parent / DEFAULT_LIBRARY_FILENAME
            self.assertEqual(chart_library_path_for_config(config_path), expected)
            self.assertEqual(expected.name, "vap_chart_library.json")

    @unittest.skipUnless(PLOTLY_AVAILABLE, "Plotly is not installed")
    def test_plotly_single_axis_ignores_stale_secondary_column(self) -> None:
        from vap_plotly_stack_renderer import (
            _add_standard_panel,
            _panel_has_secondary_axis,
            _require_plotly,
        )

        go, _pio, make_subplots = _require_plotly()
        frame = pd.DataFrame(
            {
                "Date": pd.date_range("2026-08-31", periods=3),
                "AdjClose": [100.0, 101.0, 102.0],
            }
        )
        chart = reusable_line_chart("plotly_single")
        chart.update(
            {
                "axis_mode": "single",
                "secondary_y": ["MissingVolume"],
                "secondary_type": "bar",
            }
        )
        figure = make_subplots(
            rows=1,
            cols=1,
            specs=[[{"secondary_y": False}]],
        )

        primary, secondary, normalized, normalized_indices = _add_standard_panel(
            figure,
            go,
            1,
            frame,
            chart,
            frame["Date"],
            {"palette": "deep"},
        )

        self.assertFalse(_panel_has_secondary_axis(chart, frame))
        self.assertEqual([trace.name for trace in figure.data], ["AdjClose"])
        self.assertEqual(len(primary), 3)
        self.assertEqual(secondary, [])
        self.assertEqual(normalized, [])
        self.assertEqual(normalized_indices, [])
        self.assertTrue(all(getattr(trace, "yaxis", "y") in (None, "y") for trace in figure.data))

    def test_atomic_temp_cleanup_removes_stale_and_failed_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            destination = root / "settings.json"
            destination.write_text("original", encoding="utf-8")
            stale = root / ".settings.json.abandoned.tmp"
            recent = root / ".settings.json.active.tmp"
            unrelated = root / ".other.json.abandoned.tmp"
            stale.write_text("stale", encoding="utf-8")
            recent.write_text("recent", encoding="utf-8")
            unrelated.write_text("unrelated", encoding="utf-8")
            old_timestamp = time.time() - 7_200
            os.utime(stale, (old_timestamp, old_timestamp))

            removed = cleanup_stale_temporary_files(
                destination,
                minimum_age_seconds=3_600,
            )
            self.assertEqual(removed, 1)
            self.assertFalse(stale.exists())
            self.assertTrue(recent.exists())
            self.assertTrue(unrelated.exists())

            with patch("vap_atomic_io.os.replace", side_effect=OSError("disk stopped")):
                with self.assertRaisesRegex(OSError, "disk stopped"):
                    atomic_write_text(destination, "replacement")

            self.assertEqual(destination.read_text(encoding="utf-8"), "original")
            self.assertEqual(
                sorted(path.name for path in root.glob(".settings.json.*.tmp")),
                [recent.name],
                "the failed write's unique temporary file must be removed",
            )


if __name__ == "__main__":
    unittest.main()
