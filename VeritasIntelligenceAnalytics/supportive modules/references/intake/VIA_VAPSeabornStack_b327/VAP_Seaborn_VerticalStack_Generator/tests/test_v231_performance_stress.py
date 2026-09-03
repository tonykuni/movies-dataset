from __future__ import annotations

import importlib.util
import tempfile
import time
import unittest
from pathlib import Path

import numpy as np
import pandas as pd

from vap_data_adapter import detect_source_kind, discover_source, read_source_frame
from vap_seaborn_stack_generator import prepare_chart_frame


ROW_COUNT = 50_000
UNIQUE_DATE_COUNT = ROW_COUNT // 2
PARQUET_ENGINE_AVAILABLE = bool(
    importlib.util.find_spec("pyarrow") or importlib.util.find_spec("fastparquet")
)


def _memory_bytes(frame: pd.DataFrame) -> int:
    return int(frame.memory_usage(index=True, deep=True).sum())


def _candlestick_chart(source_path: Path, max_rows: int) -> dict[str, object]:
    return {
        "id": "stress_adjusted_ohlcv",
        "type": "candlestick",
        "title": "50k adjusted OHLCV stress",
        "x": "Date",
        "open": "AdjOpen",
        "high": "AdjHigh",
        "low": "AdjLow",
        "close": "AdjClose",
        "volume": "Volume",
        "y": [],
        "secondary_y": [],
        "normalized_y": [],
        "axis_mode": "single",
        "missing": "ffill",
        "date_column": "Date",
        "invalid_date_policy": "fail",
        "duplicate_date_policy": "last",
        "outlier_policy": "report",
        "quality_mode": "off",
        "max_rows": max_rows,
        "data_source": {"kind": "auto", "path": str(source_path)},
    }


class VAPV231PerformanceStressTests(unittest.TestCase):
    """Bounded UAT for large local sources without creating huge chart files."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._temporary_directory = tempfile.TemporaryDirectory()
        cls.directory = Path(cls._temporary_directory.name)
        cls.csv_path = cls.directory / "market_cp950"
        cls.parquet_path = cls.directory / "market_parquet"

        dates = pd.bdate_range("2020-01-02", periods=UNIQUE_DATE_COUNT).repeat(2)
        row_numbers = np.arange(ROW_COUNT, dtype=np.int64)
        date_numbers = np.repeat(np.arange(UNIQUE_DATE_COUNT, dtype=float), 2)
        close = 100.0 + date_numbers * 0.01
        frame = pd.DataFrame(
            {
                "Row": row_numbers,
                "Date": dates,
                "股票名稱": np.where(row_numbers % 2 == 0, "測試甲", "測試乙"),
                "AdjOpen": close - 0.20,
                "AdjHigh": close + 0.55,
                "AdjLow": close - 0.65,
                "AdjClose": close,
                "Volume": 1_000_000.0 + (row_numbers % 10_000),
            }
        )
        # The last duplicate is retained by duplicate_date_policy=last.  This
        # makes the second trading day prove that price is forward-filled while
        # volume remains missing.
        frame.loc[3, ["AdjOpen", "AdjHigh", "AdjLow", "AdjClose", "Volume"]] = np.nan
        cls.source_frame = frame
        frame.to_csv(
            cls.csv_path,
            index=False,
            encoding="cp950",
            date_format="%Y-%m-%d",
        )
        if PARQUET_ENGINE_AVAILABLE:
            frame.to_parquet(cls.parquet_path, index=False)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._temporary_directory.cleanup()

    def test_extensionless_cp950_csv_discovery_is_sample_bounded(self) -> None:
        started = time.perf_counter()
        manifest = discover_source(self.csv_path, sample_rows=257)
        elapsed = time.perf_counter() - started

        self.assertEqual(detect_source_kind(self.csv_path), "csv")
        self.assertEqual(manifest["kind"], "csv")
        self.assertEqual(manifest["sample_rows"], 257)
        self.assertEqual(manifest["sample_columns"], len(self.source_frame.columns))
        self.assertEqual(manifest["suggestion"]["chart_type"], "candlestick")
        self.assertLess(elapsed, 20.0, msg=f"50k CSV discovery took {elapsed:.2f}s")

    def test_extensionless_cp950_csv_projection_and_limit_are_memory_bounded(self) -> None:
        started = time.perf_counter()
        loaded = read_source_frame(
            self.csv_path,
            columns=["Date", "AdjClose", "Volume"],
            limit=731,
        )
        elapsed = time.perf_counter() - started

        self.assertEqual(list(loaded.columns), ["Date", "AdjClose", "Volume"])
        self.assertEqual(len(loaded), 731)
        self.assertLess(_memory_bytes(loaded), 1_000_000)
        self.assertLess(elapsed, 15.0, msg=f"bounded CSV read took {elapsed:.2f}s")

    @unittest.skipUnless(
        PARQUET_ENGINE_AVAILABLE,
        "pyarrow/fastparquet is not installed in this test runtime",
    )
    def test_extensionless_parquet_discovery_projection_and_limit(self) -> None:
        started = time.perf_counter()
        manifest = discover_source(self.parquet_path, sample_rows=211)
        loaded = read_source_frame(
            self.parquet_path,
            columns=["Date", "AdjClose", "Volume"],
            limit=887,
        )
        elapsed = time.perf_counter() - started

        self.assertEqual(detect_source_kind(self.parquet_path), "parquet")
        self.assertEqual(manifest["kind"], "parquet")
        self.assertEqual(manifest["sample_rows"], 211)
        self.assertEqual(list(loaded.columns), ["Date", "AdjClose", "Volume"])
        self.assertEqual(len(loaded), 887)
        self.assertLess(_memory_bytes(loaded), 1_000_000)
        self.assertLess(elapsed, 20.0, msg=f"bounded Parquet UAT took {elapsed:.2f}s")

    def test_full_50k_prepare_sorts_deduplicates_and_never_fills_volume(self) -> None:
        chart = _candlestick_chart(self.csv_path, ROW_COUNT)
        project = {"date_column": "Date", "max_rows": ROW_COUNT}
        cache: dict[str, pd.DataFrame] = {}

        started = time.perf_counter()
        prepared, quality = prepare_chart_frame(
            chart,
            project,
            self.directory / "stress_config.json",
            cache,
        )
        elapsed = time.perf_counter() - started

        self.assertEqual(len(cache), 1)
        self.assertEqual(len(next(iter(cache.values()))), ROW_COUNT)
        self.assertEqual(len(prepared), UNIQUE_DATE_COUNT)
        self.assertTrue(prepared["Date"].is_monotonic_increasing)
        self.assertFalse(prepared["Date"].duplicated().any())
        for column in ("AdjOpen", "AdjHigh", "AdjLow", "AdjClose"):
            self.assertEqual(float(prepared.loc[1, column]), float(prepared.loc[0, column]))
        self.assertTrue(pd.isna(prepared.loc[1, "Volume"]))
        self.assertEqual(quality["mode"], "off")
        self.assertTrue(
            any(repair["action"] == "drop_rows" for repair in quality["repairs"])
        )
        self.assertLess(_memory_bytes(next(iter(cache.values()))), 15_000_000)
        self.assertLess(elapsed, 25.0, msg=f"50k preparation took {elapsed:.2f}s")

    def test_project_max_rows_caps_work_before_time_series_transforms(self) -> None:
        chart = _candlestick_chart(self.csv_path, 2_000)
        project = {"date_column": "Date", "max_rows": ROW_COUNT}
        cache: dict[str, pd.DataFrame] = {}

        prepared, _quality = prepare_chart_frame(
            chart,
            project,
            self.directory / "stress_config.json",
            cache,
        )

        raw = next(iter(cache.values()))
        self.assertEqual(len(raw), 2_000)
        self.assertEqual(len(prepared), 1_000)

    def test_rows_below_explicit_cap_are_not_silently_sampled(self) -> None:
        chart = {
            "id": "large_line",
            "type": "line",
            "title": "Large line",
            "x": "Row",
            "y": ["AdjClose"],
            "secondary_y": [],
            "normalized_y": [],
            "axis_mode": "single",
            "missing": "none",
            "quality_mode": "off",
            "outlier_policy": "none",
            "max_rows": 4_096,
            "data_source": {"kind": "auto", "path": str(self.csv_path)},
        }
        prepared, _quality = prepare_chart_frame(
            chart,
            {"date_column": "", "max_rows": ROW_COUNT},
            self.directory / "stress_config.json",
            {},
        )

        self.assertEqual(len(prepared), 4_096)
        self.assertEqual(prepared["Row"].tolist(), list(range(4_096)))


if __name__ == "__main__":
    unittest.main()
