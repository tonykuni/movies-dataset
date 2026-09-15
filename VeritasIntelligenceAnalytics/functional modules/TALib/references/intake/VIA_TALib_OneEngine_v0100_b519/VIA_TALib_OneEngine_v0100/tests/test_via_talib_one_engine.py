from __future__ import annotations

import copy
import importlib.util
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("via_talib_one", ROOT / "VIA_TALib_OneEngine.py")
ENGINE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(ENGINE)


def rolling_mean(values: np.ndarray, period: int) -> np.ndarray:
    return pd.Series(values).rolling(period).mean().to_numpy()


class FakeFunction:
    DEFINITIONS = {
        "SMA": ({"price": "close"}, ["real"], {"timeperiod": 30}),
        "RSI": ({"price": "close"}, ["real"], {"timeperiod": 14}),
        "MACD": ({"price": "close"}, ["macd", "macdsignal", "macdhist"], {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9}),
        "BBANDS": ({"price": "close"}, ["upperband", "middleband", "lowerband"], {"timeperiod": 5, "nbdevup": 2.0, "nbdevdn": 2.0, "matype": 0}),
        "OBV": ({"price": "close", "volume": "volume"}, ["real"], {}),
        "BETA": ({"price0": "high", "price1": "low"}, ["real"], {"timeperiod": 5}),
        "CDLDOJI": ({"prices": ["open", "high", "low", "close"]}, ["integer"], {}),
        "MAVP": ({"price": "close", "periods": "periods"}, ["real"], {"minperiod": 2, "maxperiod": 30, "matype": 0}),
    }

    def __init__(self, name: str):
        self.name = name.upper()
        inputs, outputs, parameters = self.DEFINITIONS[self.name]
        self.input_names = inputs
        self.output_names = outputs
        self.parameters = copy.deepcopy(parameters)
        self.info = {"group": FakeTalib.group_for(self.name)}

    def __call__(self, inputs, **parameters):
        close = np.asarray(inputs["close"], dtype=float)
        if self.name == "SMA":
            return rolling_mean(close, int(parameters["timeperiod"]))
        if self.name == "RSI":
            period = int(parameters["timeperiod"])
            delta = pd.Series(close).diff()
            gain = delta.clip(lower=0).rolling(period).mean()
            loss = (-delta.clip(upper=0)).rolling(period).mean()
            rs = gain / loss.replace(0, np.nan)
            return (100 - 100 / (1 + rs)).fillna(100.0).to_numpy()
        if self.name == "MACD":
            fast = pd.Series(close).ewm(span=int(parameters["fastperiod"]), adjust=False).mean()
            slow = pd.Series(close).ewm(span=int(parameters["slowperiod"]), adjust=False).mean()
            dif = fast - slow
            signal = dif.ewm(span=int(parameters["signalperiod"]), adjust=False).mean()
            return dif.to_numpy(), signal.to_numpy(), (dif - signal).to_numpy()
        if self.name == "BBANDS":
            period = int(parameters["timeperiod"])
            middle = pd.Series(close).rolling(period).mean()
            sigma = pd.Series(close).rolling(period).std(ddof=0)
            return (
                (middle + float(parameters["nbdevup"]) * sigma).to_numpy(),
                middle.to_numpy(),
                (middle - float(parameters["nbdevdn"]) * sigma).to_numpy(),
            )
        if self.name == "OBV":
            volume = np.asarray(inputs["volume"], dtype=float)
            direction = np.sign(np.diff(close, prepend=close[0]))
            return np.cumsum(direction * volume)
        if self.name == "BETA":
            left = np.asarray(inputs[self.input_names["price0"]], dtype=float)
            right = np.asarray(inputs[self.input_names["price1"]], dtype=float)
            return pd.Series(left).rolling(int(parameters["timeperiod"])).cov(pd.Series(right)).to_numpy()
        if self.name == "CDLDOJI":
            opening = np.asarray(inputs["open"], dtype=float)
            return np.where(np.abs(close - opening) < 0.01, 100, 0)
        if self.name == "MAVP":
            period = int(np.asarray(inputs["periods"])[-1])
            return rolling_mean(close, period)
        raise AssertionError(self.name)


class FakeAbstract:
    Function = FakeFunction


class FakeTalib:
    __version__ = "test-double"
    __ta_version__ = "test-double"

    @staticmethod
    def group_for(name: str) -> str:
        for group, functions in FakeTalib.get_function_groups().items():
            if name in functions:
                return group
        return "Unknown"

    @staticmethod
    def get_functions():
        return list(FakeFunction.DEFINITIONS)

    @staticmethod
    def get_function_groups():
        return {
            "Overlap Studies": ["SMA", "BBANDS", "MAVP"],
            "Momentum Indicators": ["RSI", "MACD"],
            "Volume Indicators": ["OBV"],
            "Statistic Functions": ["BETA"],
            "Pattern Recognition": ["CDLDOJI"],
        }


def make_frame(rows: int = 320) -> pd.DataFrame:
    index = np.arange(rows, dtype=float)
    raw_close = 100.0 + index * 0.25 + np.sin(index / 8.0)
    raw_open = raw_close - 0.2
    raw_high = raw_close + 0.8
    raw_low = raw_close - 0.9
    factor = np.where(index < rows / 2, 0.5, 1.0)
    volume = 1_000_000.0 + index * 1_000.0
    return pd.DataFrame({
        "交易日期": pd.bdate_range("2025-01-02", periods=rows),
        "證券代號": "2330.TW",
        "開盤價": raw_open,
        "最高價": raw_high,
        "最低價": raw_low,
        "收盤價": raw_close,
        "Adj Close": raw_close * factor,
        "成交股數": volume,
        "成交金額": volume * raw_close,
        "當沖成交股數": volume * 0.25,
        "當沖成交金額": volume * raw_close * 0.25,
    })


class OneEngineTests(unittest.TestCase):
    def setUp(self):
        self.config = copy.deepcopy(ENGINE.DEFAULT_CONFIG)
        self.config["output"]["formats"] = ["csv"]
        self.config["output"]["incremental_merge"] = False

    def test_adjusted_ohlc_and_activity_dual_basis(self):
        normalized, metadata = ENGINE.normalize_market_data(make_frame(), self.config)
        self.assertEqual(metadata["price_policy"], "ADJUSTED_PRICE_ONLY")
        self.assertAlmostEqual(normalized.loc[0, "adj_open"], normalized.loc[0, "open"])
        self.assertAlmostEqual(normalized.loc[0, "adj_open"], make_frame().loc[0, "開盤價"] * 0.5)
        self.assertAlmostEqual(normalized.loc[20, "volume_ex_daytrade"], normalized.loc[20, "volume_raw"] * 0.75)
        self.assertAlmostEqual(normalized.loc[20, "turnover_ex_daytrade"], normalized.loc[20, "turnover_raw"] * 0.75)

    def test_raw_close_never_silently_substitutes_adjusted(self):
        frame = make_frame().drop(columns=["Adj Close"])
        with self.assertRaisesRegex(ValueError, "ADJUSTED_PRICE_ONLY"):
            ENGINE.normalize_market_data(frame, self.config)

    def test_default_and_special_parameter_plans(self):
        catalog = ENGINE.build_function_catalog(FakeTalib, FakeAbstract, self.config)
        by_name = {row["function"]: row for row in catalog}
        self.assertEqual([v["parameters"]["timeperiod"] for v in by_name["SMA"]["resolved_variants"]], [5, 10, 20, 60, 120, 240])
        self.assertEqual([v["parameters"]["timeperiod"] for v in by_name["RSI"]["resolved_variants"]], [14])
        self.assertEqual(len(by_name["MAVP"]["resolved_variants"]), 6)
        self.assertEqual(by_name["MACD"]["resolved_variants"][0]["parameters"], {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9})

    def test_vdf_price_lake_aliases_and_configurable_input_binding(self):
        frame = make_frame(20).rename(columns={"交易日期": "obs_date", "Adj Close": "adj"})
        frame["benchmark_close"] = np.linspace(90.0, 95.0, len(frame))
        normalized, metadata = ENGINE.normalize_market_data(frame, self.config)
        self.assertEqual(metadata["column_resolution"]["date"], "obs_date")
        self.assertEqual(metadata["column_resolution"]["adj_close"], "adj")
        self.assertIn("benchmark_close", normalized.columns)

        config = copy.deepcopy(self.config)
        config["indicators"]["input_overrides"] = {
            "BETA": {"price0": "close", "price1": "benchmark_close"},
        }
        catalog = ENGINE.build_function_catalog(FakeTalib, FakeAbstract, config)
        beta = next(row for row in catalog if row["function"] == "BETA")
        self.assertEqual(beta["input_names"], {"price0": "close", "price1": "benchmark_close"})
        result = ENGINE.run_engine(config, frame=frame, talib_module=FakeTalib, abstract_module=FakeAbstract, write=False)
        self.assertEqual(result["talib"]["function_coverage"], 1.0)

    def test_all_discovered_functions_and_dual_volume_are_computed(self):
        result = ENGINE.run_engine(
            self.config,
            frame=make_frame(),
            talib_module=FakeTalib,
            abstract_module=FakeAbstract,
            write=False,
        )
        self.assertEqual(result["talib"]["function_coverage"], 1.0)
        registry = result["registry_frame"]
        obv = registry.loc[registry["function"] == "OBV"]
        self.assertEqual(set(obv["volume_basis"]), {"raw", "ex_daytrade"})
        self.assertTrue(any("tp240" in feature for feature in registry.loc[registry["function"] == "SMA", "feature"]))

    def test_csv_and_sqlite_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            csv_path = root / "market.csv"
            database_path = root / "market.sqlite"
            make_frame(20).to_csv(csv_path, index=False, encoding="utf-8-sig")
            frame_csv = ENGINE.read_file_source(csv_path, self.config)
            self.assertEqual(len(frame_csv), 20)
            with sqlite3.connect(database_path) as connection:
                make_frame(20).to_sql("tw_prices", connection, index=False)
            config = copy.deepcopy(self.config)
            config["source"].update({"type": "database", "database_type": "sqlite", "database_path": str(database_path), "table": "tw_prices"})
            frame_db = ENGINE.read_database_source(config)
            self.assertEqual(len(frame_db), 20)

    def test_signals_and_vap_catalog(self):
        result = ENGINE.run_engine(
            self.config,
            frame=make_frame(),
            talib_module=FakeTalib,
            abstract_module=FakeAbstract,
            write=False,
        )
        signals = ENGINE.generate_latest_signals(result["feature_frame"], result["registry_frame"], self.config)
        self.assertIn("RSI", set(signals["function"]))
        vap = ENGINE.build_vap_catalog(result["registry_frame"], [], self.config)
        self.assertEqual(vap["schema"], "VIA-VDF-VAP-CONNECTION-MANIFEST/1.0")
        self.assertEqual({item["id"] for item in vap["activity_toggle"]["options"]}, {"raw", "ex_daytrade"})

    def test_external_config_matches_embedded_defaults(self):
        with (ROOT / "VIA_TALib_OneEngine.config.json").open("r", encoding="utf-8") as handle:
            external = json.load(handle)
        self.assertEqual(external, ENGINE.DEFAULT_CONFIG)

    def test_full_csv_output_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            config = copy.deepcopy(self.config)
            config["output"]["directory"] = directory
            manifest = ENGINE.run_engine(
                config,
                frame=make_frame(),
                talib_module=FakeTalib,
                abstract_module=FakeAbstract,
                write=True,
            )
            expected = [
                "VIA_TALib_Features_CSV",
                "VIA_TALib_Feature_Manifest.json",
                "VIA_TALib_Parameter_Catalog.json",
                "VIA_TALib_Feature_Registry.csv",
                "VIA_TALib_Latest_Signals.csv",
                "VIA_TALib_VAP_Catalog.json",
            ]
            for name in expected:
                self.assertTrue((Path(directory) / name).is_file(), name)
            self.assertEqual(manifest["status"], "GREEN")
            self.assertEqual(manifest["talib"]["function_coverage"], 1.0)
            with (Path(directory) / "VIA_TALib_VAP_Catalog.json").open("r", encoding="utf-8") as handle:
                vap = json.load(handle)
            self.assertEqual(vap["price_policy"], "ADJUSTED_PRICE_ONLY")

    def test_sqlite_output_append_deduplicate(self):
        with tempfile.TemporaryDirectory() as directory:
            database_path = Path(directory) / "features.sqlite"
            config = copy.deepcopy(self.config)
            config["output"].update({
                "database_type": "sqlite",
                "database_path": str(database_path),
                "database_table": "talib_features",
                "database_if_exists": "append_deduplicate",
            })
            first = pd.DataFrame({
                "date": pd.to_datetime(["2026-01-02", "2026-01-05"]),
                "ticker": ["2330", "2330"],
                "value": [1.0, 2.0],
            })
            second = pd.DataFrame({
                "date": pd.to_datetime(["2026-01-05", "2026-01-06"]),
                "ticker": ["2330", "2330"],
                "value": [20.0, 3.0],
            })
            ENGINE.write_feature_database(first, config)
            receipt = ENGINE.write_feature_database(second, config)
            with sqlite3.connect(database_path) as connection:
                stored = pd.read_sql_query("SELECT * FROM talib_features ORDER BY date", connection)
            self.assertEqual(receipt["rows"], 3)
            self.assertEqual(len(stored), 3)
            self.assertEqual(float(stored.loc[stored["date"].str.startswith("2026-01-05"), "value"].iloc[0]), 20.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
