from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import tempfile
import unittest
from pathlib import Path
from urllib.parse import parse_qsl, urlsplit

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")

from vap_data_adapter import (
    detect_source_kind,
    discover_source,
    ensure_read_only_query,
    infer_semantic_type,
    numeric_profile,
    read_source_frame,
    sanitize_connection_url,
)
from vap_defaults import built_in_defaults, load_defaults
from vap_quality_engine import apply_outlier_policy, audit_frame
from vap_seaborn_stack_generator import (
    append_chart_spec,
    apply_missing_policy,
    build_parser,
    command_add,
    default_chart_spec,
    default_project_config,
    parse_date_column,
    read_json,
    render_stack,
    update_chart_spec,
    write_json,
)


class VAPV21FeatureTests(unittest.TestCase):
    def test_column_profile_uses_same_three_iqr_default_as_quality_audit(self) -> None:
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 9.0])
        self.assertEqual(numeric_profile(series)["outlier_count"], 0)

    def test_invalid_or_missing_dates_require_explicit_drop(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": ["2026-01-02", "2026-01-02", None, "bad-date"],
                "Close": [3.0, 4.0, 1.0, 2.0],
            }
        )
        with self.assertRaisesRegex(ValueError, "無效、缺失"):
            parse_date_column(
                frame,
                "Date",
                invalid_policy="fail",
                duplicate_policy="last",
            )

        dropped = parse_date_column(
            frame,
            "Date",
            invalid_policy="drop",
            duplicate_policy="last",
        )
        self.assertEqual(len(dropped), 1)
        self.assertEqual(float(dropped.loc[0, "Close"]), 4.0)
        self.assertFalse(dropped["Date"].isna().any())

    def test_cli_add_preset_is_overridden_only_by_explicit_arguments(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "stack.json"
            write_json(config_path, default_project_config("data.csv"))
            parser = build_parser()

            preset_args = parser.parse_args(
                [
                    "add",
                    "--config",
                    str(config_path),
                    "--id",
                    "preset_price",
                    "--type",
                    "line",
                    "--x",
                    "Date",
                    "--y",
                    "Close",
                    "--preset",
                    "price",
                ]
            )
            with redirect_stdout(StringIO()):
                command_add(preset_args)
            preset_chart = read_json(config_path)["charts"][0]
            self.assertEqual(preset_chart["missing"], "ffill")
            self.assertEqual(preset_chart["axis_mode"], "single")
            self.assertEqual(float(preset_chart["height_ratio"]), 1.25)

            override_args = parser.parse_args(
                [
                    "add",
                    "--config",
                    str(config_path),
                    "--id",
                    "explicit_price",
                    "--type",
                    "bar",
                    "--x",
                    "Date",
                    "--y",
                    "Close",
                    "--preset",
                    "price",
                    "--missing",
                    "zero",
                    "--axis-mode",
                    "auto",
                    "--height-ratio",
                    "2.0",
                ]
            )
            with redirect_stdout(StringIO()):
                command_add(override_args)
            override_chart = read_json(config_path)["charts"][1]
            self.assertEqual(override_chart["type"], "bar")
            self.assertEqual(override_chart["missing"], "zero")
            self.assertEqual(override_chart["axis_mode"], "auto")
            self.assertEqual(float(override_chart["height_ratio"]), 2.0)

    def test_chart_id_and_output_name_cannot_escape_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            config_path = root / "stack.json"
            config = default_project_config("data.csv")
            write_json(config_path, config)
            unsafe_chart = default_chart_spec("../escape", "line", "Unsafe", "Date", ["Close"])
            with self.assertRaisesRegex(ValueError, "安全"):
                append_chart_spec(config_path, unsafe_chart)

            pd.DataFrame({"Date": ["2026-01-01"], "Close": [100.0]}).to_csv(
                root / "data.csv",
                index=False,
            )
            config["project"].update(
                {
                    "output_directory": "output",
                    "output_name": "../escape",
                    "output_formats": ["png"],
                }
            )
            config["charts"] = [default_chart_spec("price", "line", "Price", "Date", ["Close"])]
            write_json(config_path, config)
            with self.assertRaisesRegex(ValueError, "安全"):
                render_stack(config_path)
            self.assertFalse((root / "escape.png").exists())

    def test_semantic_alias_matching_uses_tokens_not_substrings(self) -> None:
        values = pd.Series([1.25, -2.5, 3.75])
        self.assertEqual(infer_semantic_type("Flow", values), "flow")
        self.assertEqual(infer_semantic_type("AdjClose", values), "price")
        self.assertEqual(infer_semantic_type("TurnoverValue", values), "currency")

    def test_connection_url_masks_sensitive_query_values(self) -> None:
        safe = sanitize_connection_url(
            "postgresql://analyst:db-password@db.example.com/market"
            "?sslmode=require&password=query-password&passwd=query-passwd"
            "&pwd=query-pwd&token=query-token&secret=query-secret"
            "&clientSecret=query-client-secret&api_key=query-api-key&apiKey=query-camel-api-key"
        )
        self.assertNotIn("db-password", safe)
        query = dict(parse_qsl(urlsplit(safe).query, keep_blank_values=True))
        self.assertEqual(query["sslmode"], "require")
        for key in ("password", "passwd", "pwd", "token", "secret", "clientSecret", "api_key", "apiKey"):
            self.assertEqual(query[key], "REDACTED")

    def test_extensionless_csv_is_sniffed_and_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "market_csv_no_suffix"
            pd.DataFrame({"Date": ["2026-01-01"], "Close": [100.0]}).to_csv(path, index=False)
            self.assertEqual(detect_source_kind(path), "csv")
            frame = read_source_frame(path)
            self.assertEqual(list(frame.columns), ["Date", "Close"])
            self.assertEqual(float(frame.loc[0, "Close"]), 100.0)

    def test_extensionless_cp950_csv_falls_back_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "台股成交值"
            pd.DataFrame({"日期": ["2026-01-01"], "成交值": [123456]}).to_csv(path, index=False, encoding="cp950")
            self.assertEqual(detect_source_kind(path), "csv")
            frame = read_source_frame(path)
            self.assertEqual(list(frame.columns), ["日期", "成交值"])
            self.assertEqual(int(frame.loc[0, "成交值"]), 123456)

    def test_extensionless_parquet_is_sniffed_and_read(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "market_parquet_no_suffix"
            try:
                pd.DataFrame({"Date": ["2026-01-01"], "Close": [100.0]}).to_parquet(path, index=False)
            except (ImportError, ModuleNotFoundError):
                path.write_bytes(b"PAR1" + bytes(32))
                self.assertEqual(detect_source_kind(path), "parquet")
                return
            self.assertEqual(detect_source_kind(path), "parquet")
            frame = read_source_frame(path, columns=["Close"])
            self.assertEqual(list(frame.columns), ["Close"])

    def test_quality_audit_flags_without_mutating_source(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": ["2026-01-02", "2026-01-02", "bad-date", "2026-01-08"],
                "Close": [1.0, None, 3.0, 1000.0],
            }
        )
        original = frame.copy(deep=True)
        report = audit_frame(frame, date_column="Date", columns=["Date", "Close"])
        codes = {issue["code"] for issue in report["issues"]}
        self.assertIn("missing_values", codes)
        self.assertIn("invalid_dates", codes)
        self.assertIn("duplicate_grain", codes)
        pd.testing.assert_frame_equal(frame, original)

    def test_outliers_are_report_only_until_clipping_is_explicit(self) -> None:
        frame = pd.DataFrame({"Value": [1.0, 2, 3, 4, 5, 6, 7, 8, 9, 10, 1000]})
        report_only, repairs = apply_outlier_policy(frame, ["Value"], policy="report")
        self.assertEqual(float(report_only.iloc[-1, 0]), 1000.0)
        self.assertEqual(repairs, [])
        clipped, repairs = apply_outlier_policy(frame, ["Value"], policy="clip_iqr")
        self.assertLess(float(clipped.iloc[-1, 0]), 1000.0)
        self.assertEqual(repairs[0]["action"], "clip_iqr")

    def test_duplicate_dates_fail_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "multi_entity.csv"
            pd.DataFrame(
                {
                    "Date": ["2026-01-02", "2026-01-02"],
                    "Ticker": ["2330.TW", "2317.TW"],
                    "Close": [1000.0, 200.0],
                }
            ).to_csv(data_path, index=False)
            config_path = root / "stack.json"
            config = default_project_config(data_path.name)
            config["project"].update({"output_formats": ["png"], "watermark": "", "source": ""})
            config["charts"] = [default_chart_spec("price", "line", "Price", "Date", ["Close"])]
            write_json(config_path, config)
            with self.assertRaisesRegex(ValueError, "重複日期"):
                render_stack(config_path)

    def test_interpolation_never_fills_volume(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": ["2026-01-01", "2026-01-02", "2026-01-03"],
                "AdjClose": [100.0, None, 103.0],
                "Volume": [1000.0, None, 1300.0],
            }
        )
        result = apply_missing_policy(frame, ["Date", "AdjClose", "Volume"], "interpolate")
        self.assertEqual(float(result.loc[1, "AdjClose"]), 101.5)
        self.assertTrue(pd.isna(result.loc[1, "Volume"]))

    def test_html_export_is_offline_and_responsive(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            data_path = root / "data.csv"
            pd.DataFrame(
                {"Date": pd.date_range("2026-01-01", periods=8), "Close": np.arange(8) + 100}
            ).to_csv(data_path, index=False)
            config_path = root / "stack.json"
            config = default_project_config(data_path.name)
            config["project"].update(
                {"output_formats": ["html"], "output_directory": "output", "watermark": "", "source": ""}
            )
            config["charts"] = [default_chart_spec("price", "line", "Price", "Date", ["Close"])]
            write_json(config_path, config)
            report = render_stack(config_path)
            html_path = Path(report["outputs"][0])
            content = html_path.read_text(encoding="utf-8")
            self.assertIn("<svg", content)
            self.assertIn("@media", content)
            self.assertNotIn("cdn.plot.ly", content)
            self.assertTrue(Path(report["audit"]).exists())

    def test_chart_can_be_renamed_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            config_path = Path(temporary_directory) / "stack.json"
            write_json(config_path, default_project_config("data.csv"))
            append_chart_spec(config_path, default_chart_spec("one", "line", "One", "Date", ["A"]))
            append_chart_spec(config_path, default_chart_spec("two", "line", "Two", "Date", ["B"]))
            updated = update_chart_spec(config_path, "one", {"id": "renamed"})
            self.assertEqual(updated["id"], "renamed")
            with self.assertRaisesRegex(ValueError, "已存在"):
                update_chart_spec(config_path, "renamed", {"id": "two"})

    def test_discovery_includes_quality_and_turnover_value_is_currency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "turnover.csv"
            pd.DataFrame(
                {
                    "Date": ["2026-01-01", "2026-01-02", "2026-01-03"],
                    "TurnoverValue": [100000, 120000, 90000],
                }
            ).to_csv(path, index=False)
            manifest = discover_source(path)
            profile = next(item for item in manifest["columns"] if item["name"] == "TurnoverValue")
            self.assertEqual(profile["semantic_type"], "currency")
            self.assertIn("quality", manifest)
            self.assertEqual(manifest["quality"]["schema"], "VIA-VAP-DATA-QUALITY/2.2")

    def test_defaults_are_v22_and_complete(self) -> None:
        defaults = load_defaults()
        self.assertEqual(defaults["version"], "2.3.1")
        self.assertEqual(defaults["chart"]["duplicate_date_policy"], "fail")
        self.assertIn("html", defaults["project"]["output_formats"])
        self.assertEqual(built_in_defaults()["schema"], "VIA-VAP-SEABORN-DEFAULTS/2.3")

    def test_writable_cte_is_rejected(self) -> None:
        self.assertEqual(ensure_read_only_query("SELECT * FROM prices"), "SELECT * FROM prices")
        with self.assertRaisesRegex(ValueError, "非唯讀"):
            ensure_read_only_query("WITH changed AS (DELETE FROM prices RETURNING *) SELECT * FROM changed")


if __name__ == "__main__":
    unittest.main()
