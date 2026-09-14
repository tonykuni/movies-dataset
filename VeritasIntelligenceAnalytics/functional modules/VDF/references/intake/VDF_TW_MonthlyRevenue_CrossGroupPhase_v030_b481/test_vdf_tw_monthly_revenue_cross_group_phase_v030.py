from __future__ import annotations

import hashlib
import importlib.util
import tempfile
import unittest
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ENGINE_PATH = Path(__file__).with_name(
    "vdf_tw_monthly_revenue_cross_group_phase_engine_v030.py"
)
SPEC = importlib.util.spec_from_file_location("vdf_monthly_revenue_v030", ENGINE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Cannot import engine: {ENGINE_PATH}")
ENGINE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ENGINE
SPEC.loader.exec_module(ENGINE)


def def_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class TestVDFMonthlyRevenueCrossGroupPhaseV030(unittest.TestCase):
    def setUp(self) -> None:
        self.monthly, self.company_master, self.group_mapping = (
            ENGINE.def_generate_self_test_data(periods=36)
        )

    def def_config(self, output_dir: Path, **overrides):
        values = dict(
            output_dir=output_dir,
            report_dir=output_dir,
            backup_dir=output_dir / "_backup",
            fetch_latest=False,
            incremental_update=True,
            require_parquet=False,
            require_duckdb=False,
            write_csv=True,
            write_parquet=False,
            write_duckdb=False,
            write_sqlite_fallback=False,
            backup_before_write=True,
            fail_on_duplicate_keys=True,
            fail_on_invalid_period=True,
            fail_on_empty_result=True,
            log_level="ERROR",
            run_id="UNITTEST_FIXED_RUN",
        )
        values.update(overrides)
        return ENGINE.EngineConfig(**values)

    def test_01_roc_and_gregorian_period_parser(self) -> None:
        self.assertEqual(
            ENGINE.def_parse_period_value("11507"),
            pd.Timestamp("2026-07-01"),
        )
        self.assertEqual(
            ENGINE.def_parse_period_value("2026/07"),
            pd.Timestamp("2026-07-01"),
        )
        self.assertTrue(pd.isna(ENGINE.def_parse_period_value("invalid")))

    def test_02_duplicate_is_removed_idempotently(self) -> None:
        normalized = ENGINE.def_normalize_monthly_revenue(
            self.monthly,
            source_priority=20,
        )
        merged_once = ENGINE.def_merge_incremental_monthly_revenue(
            pd.DataFrame(), normalized
        )
        merged_twice = ENGINE.def_merge_incremental_monthly_revenue(
            merged_once, normalized
        )
        self.assertEqual(len(merged_once), 12 * 36)
        self.assertEqual(len(merged_twice), len(merged_once))
        self.assertFalse(
            merged_twice.duplicated(["period", "ticker", "market"]).any()
        )

    def test_03_full_core_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ENGINE.def_run_engine(
                self.def_config(Path(temp_dir)),
                injected_monthly_revenue=self.monthly,
                injected_company_master=self.company_master,
                injected_group_mapping=self.group_mapping,
                write_outputs=False,
            )
        quality = result["quality_report"]
        checks = {row["check_id"]: row for row in quality["checks"]}
        self.assertEqual(checks["Q01_CANONICAL_DUPLICATE_KEY"]["status"], "PASS")
        self.assertEqual(checks["Q06_GROUP_WEIGHT_SUM"]["status"], "PASS")
        self.assertEqual(
            checks["Q07_GROUP_REVENUE_RECONCILIATION"]["status"], "PASS"
        )
        self.assertGreater(
            len(result["tables"]["monthly_revenue_company_group_phase"]), 0
        )
        self.assertGreater(
            len(result["tables"]["monthly_revenue_cross_group"]), 0
        )
        self.assertGreater(
            len(result["tables"]["monthly_revenue_lead_lag_group"]), 0
        )

    def test_04_multi_group_weights_sum_to_one(self) -> None:
        prepared = ENGINE.def_prepare_group_mapping(self.group_mapping)
        weight_sums = prepared.groupby("ticker")["group_weight"].sum()
        self.assertTrue(np.allclose(weight_sums.to_numpy(), 1.0, atol=1e-12))
        self.assertGreater((prepared.groupby("ticker").size() > 1).sum(), 0)

    def test_05_company_by_group_phase_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ENGINE.def_run_engine(
                self.def_config(Path(temp_dir)),
                injected_monthly_revenue=self.monthly,
                injected_company_master=self.company_master,
                injected_group_mapping=self.group_mapping,
                write_outputs=False,
            )
        table = result["tables"]["monthly_revenue_company_group_phase"]
        required = {
            "company_phase",
            "group_phase",
            "group_rotation_state",
            "company_relative_to_group",
            "phase_alignment",
            "company_contribution_to_group",
        }
        self.assertTrue(required.issubset(table.columns))
        self.assertFalse(table.duplicated(["period", "ticker", "group"]).any())

    def test_06_industry_fallback_group_mapping(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = ENGINE.def_run_engine(
                self.def_config(Path(temp_dir)),
                injected_monthly_revenue=self.monthly,
                injected_company_master=self.company_master,
                injected_group_mapping=pd.DataFrame(),
                write_outputs=False,
            )
        mapping = result["group_mapping"]
        self.assertFalse(mapping.empty)
        self.assertTrue(mapping["group_mapping_proxy"].all())
        self.assertTrue(
            np.allclose(
                mapping.groupby("ticker")["group_weight"].sum().to_numpy(),
                1.0,
                atol=1e-12,
            )
        )

    def test_07_invalid_period_fails_closed(self) -> None:
        invalid = self.monthly.copy()
        invalid.loc[0, "資料年月"] = "not-a-period"
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaises(RuntimeError):
                ENGINE.def_run_engine(
                    self.def_config(Path(temp_dir)),
                    injected_monthly_revenue=invalid,
                    injected_company_master=self.company_master,
                    injected_group_mapping=self.group_mapping,
                    write_outputs=False,
                )

    def test_08_output_data_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_dir = Path(temp_dir)
            config_1 = self.def_config(output_dir, run_id="UNITTEST_RUN_1")
            ENGINE.def_run_engine(
                config_1,
                injected_monthly_revenue=self.monthly,
                injected_company_master=self.company_master,
                injected_group_mapping=self.group_mapping,
                write_outputs=True,
            )
            company_path = output_dir / "VDF_TW_MonthlyRevenue_Company.csv"
            group_path = output_dir / "VDF_TW_MonthlyRevenue_Group.csv"
            first_hashes = (def_sha256(company_path), def_sha256(group_path))

            config_2 = self.def_config(output_dir, run_id="UNITTEST_RUN_2")
            ENGINE.def_run_engine(
                config_2,
                injected_monthly_revenue=self.monthly,
                injected_company_master=self.company_master,
                injected_group_mapping=self.group_mapping,
                write_outputs=True,
            )
            second_hashes = (def_sha256(company_path), def_sha256(group_path))
            self.assertEqual(first_hashes, second_hashes)
            backup_files = list((output_dir / "_backup").rglob("*.csv"))
            self.assertGreater(len(backup_files), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
