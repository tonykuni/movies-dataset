from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import math
import sys
import unittest
from copy import deepcopy
from datetime import date, timedelta
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENGINE_ROOT = PROJECT_ROOT / "functional modules" / "VDF" / "engine"
SSOT_PATH = PROJECT_ROOT / "config" / "ssot" / "VDF_PricesFactorRegistry.candidate.json"


def def_load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


PRICES = def_load_module("vdf_prices_canonical", ENGINE_ROOT / "VDF_PricesCanonical.py")
FACTORS = def_load_module("vdf_factor_library", ENGINE_ROOT / "VDF_FactorLibrary.py")
REGISTRY = json.loads(SSOT_PATH.read_text(encoding="utf-8"))


def def_source_row(day: str, close: float, volume: float, daytrade: float, value: float, daytrade_value: float):
    return {
        "Ticker": "2330.TW",
        "Date": day,
        "Market": "TWSE",
        "Open": close - 1.0,
        "High": close + 2.0,
        "Low": close - 2.0,
        "Close": close,
        "Adj Close": close * 0.5,
        "Volume": volume,
        "DayTradeVolume": daytrade,
        "Trading_Value": value,
        "DayTrade_Value": daytrade_value,
        "Source_Id": "TWSE",
        "Source_Tier": "T0",
        "As_Of_Date": f"{day}T10:00:00+00:00",
        "Fetch_Time": f"{day}T11:00:00+00:00",
        "Run_Id": "RUN-001",
    }


def def_canonical_rows(count: int, start: date = date(2023, 1, 2)):
    source = []
    for index in range(count):
        current = (start + timedelta(days=index)).isoformat()
        source.append(
            def_source_row(
                current,
                100.0 + index,
                1000.0,
                990.0 - index * 10.0,
                100_000.0,
                99_000.0 - index * 100.0,
            )
        )
    canonical, _ = PRICES.def_canonicalize_prices(source, REGISTRY, run_id="RUN-001")
    return canonical


class PricesCanonicalTests(unittest.TestCase):
    def test_adjusted_ohlc_and_both_ex_daytrade_amounts(self):
        rows, report = PRICES.def_canonicalize_prices(
            [def_source_row("2023-01-03", 100.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)],
            REGISTRY,
            run_id="RUN-001",
        )
        row = rows[0]
        self.assertEqual(row["validation_status"], "READY")
        self.assertAlmostEqual(row["adj_factor"], 0.5)
        self.assertAlmostEqual(row["adj_open"], 49.5)
        self.assertAlmostEqual(row["adj_high"], 51.0)
        self.assertAlmostEqual(row["adj_low"], 49.0)
        self.assertAlmostEqual(row["adj_close"], 50.0)
        self.assertEqual(row["volume_ex_daytrade"], 600.0)
        self.assertEqual(row["trading_value_ex_daytrade"], 1_250_000.0)
        self.assertEqual(report["rows_out"], 1)

    def test_confirmed_no_trade_carries_price_but_never_volume_or_value(self):
        first = def_source_row("2023-01-03", 100.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)
        second = {
            "Ticker": "2330.TW",
            "Date": "2023-01-04",
            "Market": "TWSE",
            "No_Trade_Confirmed": True,
            "Source_Id": "TWSE",
            "Source_Tier": "T0",
        }
        rows, _ = PRICES.def_canonicalize_prices([first, second], REGISTRY, run_id="RUN-001")
        carried = rows[1]
        self.assertEqual(carried["validation_status"], "NO_TRADE_CARRIED_PRICE")
        self.assertEqual(carried["adj_open"], rows[0]["adj_close"])
        self.assertEqual(carried["adj_high"], rows[0]["adj_close"])
        self.assertEqual(carried["adj_low"], rows[0]["adj_close"])
        self.assertEqual(carried["adj_close"], rows[0]["adj_close"])
        self.assertEqual(carried["volume_raw"], 0.0)
        self.assertEqual(carried["volume_ex_daytrade"], 0.0)
        self.assertEqual(carried["trading_value_raw"], 0.0)
        self.assertEqual(carried["trading_value_ex_daytrade"], 0.0)

    def test_unknown_gap_is_blocked_and_does_not_carry_price(self):
        missing = {
            "Ticker": "2330.TW",
            "Date": "2023-01-04",
            "Market": "TWSE",
            "No_Trade_Confirmed": False,
            "Source_Id": "TWSE",
            "Source_Tier": "T0",
        }
        rows, _ = PRICES.def_canonicalize_prices([missing], REGISTRY, run_id="RUN-001")
        self.assertEqual(rows[0]["validation_status"], "CALC_BLOCKED")
        self.assertIsNone(rows[0]["adj_close"])
        self.assertIsNone(rows[0]["volume_ex_daytrade"])

    def test_conflicting_explicit_ex_daytrade_is_blocked(self):
        source = def_source_row("2023-01-03", 100.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)
        source["Ex_DayTrade_Volume"] = 700.0
        rows, report = PRICES.def_canonicalize_prices([source], REGISTRY, run_id="RUN-001")
        self.assertEqual(rows[0]["validation_status"], "PARTIAL_BLOCKED")
        self.assertIsNone(rows[0]["volume_ex_daytrade"])
        warning_text = " ".join(next(iter(report["warnings"].values())))
        self.assertIn("conflicts", warning_text)

    def test_exact_duplicate_dedupes_and_conflicting_duplicate_fails_closed(self):
        first = def_source_row("2023-01-03", 100.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)
        rows, report = PRICES.def_canonicalize_prices([first, deepcopy(first)], REGISTRY, run_id="RUN-001")
        self.assertEqual(len(rows), 1)
        self.assertEqual(report["duplicates_removed"], 1)
        conflict = deepcopy(first)
        conflict["Volume"] = 1100.0
        with self.assertRaisesRegex(RuntimeError, "conflicting duplicate"):
            PRICES.def_canonicalize_prices([first, conflict], REGISTRY, run_id="RUN-001")

    def test_source_evidence_and_aliases_fail_closed(self):
        missing_source = def_source_row("2023-01-03", 100.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)
        del missing_source["Source_Id"]
        with self.assertRaisesRegex(RuntimeError, "source_id evidence is required"):
            PRICES.def_canonicalize_prices([missing_source], REGISTRY, run_id="RUN-001")
        unknown_field = def_source_row("2023-01-03", 100.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)
        unknown_field["Unregistered_Metric"] = 123
        with self.assertRaisesRegex(RuntimeError, "unregistered input fields"):
            PRICES.def_canonicalize_prices([unknown_field], REGISTRY, run_id="RUN-001")

    def test_publication_time_gate_blocks_future_as_of_date(self):
        source = def_source_row("2023-01-03", 100.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)
        source["As_Of_Date"] = "2023-01-03T12:00:00+00:00"
        source["Fetch_Time"] = "2023-01-03T11:00:00+00:00"
        with self.assertRaisesRegex(RuntimeError, "as_of_date must be earlier"):
            PRICES.def_canonicalize_prices([source], REGISTRY, run_id="RUN-001")


class FactorLibraryTests(unittest.TestCase):
    def test_defaults_reconcile_2021_price_history_with_2023_factor_start(self):
        self.assertEqual(REGISTRY["defaults"]["prices_start_date"], "2021-01-01")
        self.assertEqual(REGISTRY["defaults"]["factors_start_date"], "2023-01-02")
        self.assertEqual(REGISTRY["defaults"]["warmup_sessions"], 240)
        self.assertEqual(REGISTRY["defaults"]["horizons"], [5, 10, 20, 60, 120, 240])

    def test_liquidity_factor_uses_ex_daytrade_not_raw_volume(self):
        canonical = def_canonical_rows(3)
        factors, report = FACTORS.def_compute_factor_library(canonical, REGISTRY, horizons=[3])
        target = next(
            row
            for row in factors
            if row["data_date"] == "2023-01-04"
            and row["factor_id"] == "liquidity.volume_ex_daytrade_zscore.3d"
        )
        self.assertAlmostEqual(target["value"], 1.0)
        self.assertEqual(target["input_volume_mode"], "EX_DAYTRADE_ONLY")
        self.assertEqual(report["input_volume_mode"], "EX_DAYTRADE_ONLY")

    def test_factor_output_is_long_versioned_and_has_lineage_hash(self):
        canonical = def_canonical_rows(4)
        factors, _ = FACTORS.def_compute_factor_library(canonical, REGISTRY, horizons=[3])
        passed = next(row for row in factors if row["validation_status"] == "PASS")
        self.assertTrue(passed["factor_id"])
        self.assertEqual(passed["factor_version"], "1.0.0")
        self.assertTrue(passed["formula_id"].startswith("vdf.factor."))
        self.assertEqual(passed["formula_version"], "1.0.0")
        self.assertEqual(len(passed["input_hash"]), 64)
        self.assertTrue(passed["calculation_time"])
        self.assertEqual(passed["input_run_id"], "RUN-001")
        self.assertTrue(passed["run_id"].startswith("VDF-FACTOR-"))

    def test_window_input_hash_covers_upstream_window(self):
        first = def_canonical_rows(4)
        first_factors, _ = FACTORS.def_compute_factor_library(
            first,
            REGISTRY,
            horizons=[3],
            calculation_time="2023-01-10T00:00:00+00:00",
            run_id="FACTOR-RUN-1",
        )
        changed_source = [
            def_source_row(
                (date(2023, 1, 2) + timedelta(days=index)).isoformat(),
                100.0 + index,
                1000.0,
                950.0 - index * 10.0,
                100_000.0,
                99_000.0 - index * 100.0,
            )
            for index in range(4)
        ]
        second, _ = PRICES.def_canonicalize_prices(changed_source, REGISTRY, run_id="RUN-002")
        second_factors, _ = FACTORS.def_compute_factor_library(
            second,
            REGISTRY,
            horizons=[3],
            calculation_time="2023-01-10T00:00:00+00:00",
            run_id="FACTOR-RUN-2",
        )
        factor_id = "liquidity.volume_ex_daytrade_zscore.3d"
        first_hash = next(row["input_hash"] for row in first_factors if row["data_date"] == "2023-01-04" and row["factor_id"] == factor_id)
        second_hash = next(row["input_hash"] for row in second_factors if row["data_date"] == "2023-01-04" and row["factor_id"] == factor_id)
        self.assertNotEqual(first_hash, second_hash)

    def test_appending_future_data_does_not_change_past_factors(self):
        canonical = def_canonical_rows(5)
        baseline, _ = FACTORS.def_compute_factor_library(canonical, REGISTRY, horizons=[3])
        future_source = def_source_row("2023-01-07", 10_000.0, 50_000.0, 1.0, 9_000_000.0, 1.0)
        future, _ = PRICES.def_canonicalize_prices([future_source], REGISTRY, run_id="RUN-001")
        extended, _ = FACTORS.def_compute_factor_library([*canonical, *future], REGISTRY, horizons=[3])
        baseline_map = {
            (row["data_date"], row["factor_id"], row["parameter_set_id"]): row["value"] for row in baseline
        }
        extended_map = {
            (row["data_date"], row["factor_id"], row["parameter_set_id"]): row["value"]
            for row in extended
            if row["data_date"] <= "2023-01-06"
        }
        self.assertEqual(baseline_map, extended_map)

    def test_factor_publication_gate_blocks_future_knowledge(self):
        canonical = def_canonical_rows(3)
        with self.assertRaisesRegex(RuntimeError, "publication-time gate failed"):
            FACTORS.def_compute_factor_library(
                canonical,
                REGISTRY,
                horizons=[3],
                calculation_time="2023-01-01T00:00:00+00:00",
            )

    def test_talib_registry_capability_fails_closed_on_missing_function(self):
        indicator_registry = {
            "schema": "VIA.ParameterIndicatorRegistry",
            "categories": [
                {"indicators": [{"name": "SMA"}, {"name": "RSI"}, {"name": "MFI"}]}
            ],
            "counts": {"indicators": 3},
        }
        blocked = FACTORS.def_talib_capability(indicator_registry, ["SMA", "RSI"])
        self.assertEqual(blocked["status"], "BLOCKED")
        self.assertEqual(blocked["missing"], ["MFI"])
        self.assertEqual(blocked["fallback"], "PROHIBITED")
        passed = FACTORS.def_talib_capability(indicator_registry, ["SMA", "RSI", "MFI"])
        self.assertEqual(passed["status"], "PASS")

    def test_whitespace_normalized_identity_carries_confirmed_no_trade_price(self):
        first = def_source_row("2023-01-03", 100.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)
        first["Ticker"] = "2330.TW "
        first["Market"] = " TWSE "
        second = {
            "Ticker": "2330.TW",
            "Date": "2023-01-04",
            "Market": "TWSE",
            "No_Trade_Confirmed": True,
            "Source_Id": "TWSE",
            "Source_Tier": "T0",
        }
        rows, _ = PRICES.def_canonicalize_prices([first, second], REGISTRY, run_id="RUN-001")
        self.assertEqual(rows[1]["validation_status"], "NO_TRADE_CARRIED_PRICE")
        self.assertEqual(rows[1]["adj_close"], rows[0]["adj_close"])

    def test_factor_input_revalidates_ready_canonical_invariants(self):
        mutations = [
            ("adj_close", -1.0, "adjusted OHLC"),
            ("volume_ex_daytrade", -1.0, "ex-daytrade activity"),
            ("source_hash", "not-a-sha256", "source_hash"),
        ]
        for field, value, message in mutations:
            with self.subTest(field=field):
                canonical = def_canonical_rows(3)
                canonical[0][field] = value
                with self.assertRaisesRegex(RuntimeError, message):
                    FACTORS.def_compute_factor_library(canonical, REGISTRY, horizons=[3])

    def test_partial_factor_input_revalidates_price_and_no_trade_lineage(self):
        missing_ohlc = def_canonical_rows(2)
        missing_ohlc[1]["validation_status"] = "PARTIAL_BLOCKED"
        missing_ohlc[1]["adj_open"] = None
        with self.assertRaisesRegex(RuntimeError, "adjusted OHLC"):
            FACTORS.def_compute_factor_library(missing_ohlc, REGISTRY, horizons=[2])

        fabricated = def_canonical_rows(3)
        partial = fabricated[1]
        carried = fabricated[2]
        for row, status, activity in (
            (partial, "PARTIAL_BLOCKED", None),
            (carried, "NO_TRADE_CARRIED_PRICE", 0.0),
        ):
            row["validation_status"] = status
            row["no_trade_confirmed"] = True
            row["volume_ex_daytrade"] = activity
            row["trading_value_ex_daytrade"] = activity
            for field in ("adj_open", "adj_high", "adj_low", "adj_close"):
                row[field] = 500.0
        with self.assertRaisesRegex(RuntimeError, "previous priced close"):
            FACTORS.def_compute_factor_library(fabricated, REGISTRY, horizons=[2])

    def test_carried_factor_input_tracks_a_partial_priced_observation(self):
        first = def_source_row("2023-01-03", 100.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)
        partial = def_source_row("2023-01-04", 110.0, 1000.0, 400.0, 2_000_000.0, 750_000.0)
        partial["Ex_DayTrade_Volume"] = 700.0
        carried = {
            "Ticker": "2330.TW",
            "Date": "2023-01-05",
            "Market": "TWSE",
            "No_Trade_Confirmed": True,
            "Source_Id": "TWSE",
            "Source_Tier": "T0",
        }
        canonical, _ = PRICES.def_canonicalize_prices(
            [first, partial, carried], REGISTRY, run_id="RUN-001"
        )
        self.assertEqual(
            [row["validation_status"] for row in canonical],
            ["READY", "PARTIAL_BLOCKED", "NO_TRADE_CARRIED_PRICE"],
        )
        self.assertEqual(canonical[2]["adj_close"], canonical[1]["adj_close"])
        factors, _ = FACTORS.def_compute_factor_library(canonical, REGISTRY, horizons=[2])
        carried_return = next(
            row
            for row in factors
            if row["data_date"] == "2023-01-05" and row["factor_id"] == "return.simple.1d"
        )
        self.assertIsNone(carried_return["value"])

    def test_carried_factor_input_must_equal_the_previous_ready_close(self):
        canonical = def_canonical_rows(2)
        previous_close = canonical[0]["adj_close"]
        carried = canonical[1]
        carried["validation_status"] = "NO_TRADE_CARRIED_PRICE"
        carried["no_trade_confirmed"] = True
        carried["volume_ex_daytrade"] = 0.0
        carried["trading_value_ex_daytrade"] = 0.0
        fabricated_close = previous_close * 5.0
        for field in ("adj_open", "adj_high", "adj_low", "adj_close"):
            carried[field] = fabricated_close
        with self.assertRaisesRegex(RuntimeError, "previous priced close"):
            FACTORS.def_compute_factor_library(canonical, REGISTRY, horizons=[2])

    def test_duplicate_factor_horizons_fail_closed(self):
        canonical = def_canonical_rows(3)
        with self.assertRaisesRegex(RuntimeError, "horizons must be unique"):
            FACTORS.def_compute_factor_library(canonical, REGISTRY, horizons=[3, 3])


if __name__ == "__main__":
    unittest.main()
