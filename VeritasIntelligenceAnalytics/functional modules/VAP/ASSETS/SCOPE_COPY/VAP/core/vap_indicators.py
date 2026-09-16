#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VAP display adapter backed by VIA QuantGuard.

VAP is a presentation layer. Numerical features are calculated by the central
QuantGuard engine and then joined back to the display dataframe. Unsupported
legacy indicator names fail explicitly instead of silently fabricating values.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, List

import pandas as pd
import polars as pl

HERE = Path(__file__).resolve()
VIA = HERE.parents[5]
QUANTGUARD_ROOT = VIA / "functional modules" / "VDF" / "references" / "intake" / "VIA_QuantGuard_v20260916"
if str(QUANTGUARD_ROOT) not in sys.path:
    sys.path.insert(0, str(QUANTGUARD_ROOT))
import quant_engine as _q  # noqa: E402

try:
    from vap_config import STANDARD_PERIODS, resolve_ohlcv_columns
except Exception:
    STANDARD_PERIODS = [5, 10, 20, 60, 120, 240]

    def resolve_ohlcv_columns(frame: pd.DataFrame) -> dict[str, str | None]:
        names = {str(c).lower(): c for c in frame.columns}
        return {
            "open": names.get("open"), "high": names.get("high"),
            "low": names.get("low"), "close": names.get("adj_close") or names.get("close"),
            "volume": names.get("volume") or names.get("non_day_trade_volume"),
        }


class VAPIndicatorEngine:
    """QuantGuard-backed compatibility facade for VAP charts."""

    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.col_map = resolve_ohlcv_columns(self.df)
        self._features: pd.DataFrame | None = None
        self._windows: tuple[int, ...] = ()
        self._validate_price()

    def _validate_price(self) -> None:
        if not self.col_map.get("close"):
            raise ValueError("QuantGuard requires adj_close or close")

    def _quant_frame(self) -> pl.DataFrame:
        src = self.df.copy()
        date_col = next((c for c in ("date", "Date", "datetime", "Datetime") if c in src.columns), None)
        if date_col is None:
            date_values = pd.to_datetime(src.index)
        else:
            date_values = pd.to_datetime(src[date_col])
        close = self.col_map["close"]
        high = self.col_map.get("high") or close
        low = self.col_map.get("low") or close
        volume = self.col_map.get("volume")
        if volume is None:
            volume_values = 1.0
        else:
            volume_values = src[volume].astype(float)
        frame = pd.DataFrame({
            "date": date_values,
            "ticker": src["ticker"] if "ticker" in src.columns else "VAP",
            "adj_close": src[close].astype(float),
            "high": src[high].astype(float),
            "low": src[low].astype(float),
            "close": src[close].astype(float),
            "non_day_trade_volume": volume_values,
            "volume": volume_values,
        })
        return pl.from_pandas(frame)

    def _build(self, windows: List[int] | None = None) -> pd.DataFrame:
        requested = tuple(sorted(set(int(x) for x in (windows or STANDARD_PERIODS))))
        selected = tuple(sorted(set(requested) | {20, 60}))
        if self._features is None or not set(selected).issubset(self._windows):
            config = _q.EngineConfig(windows=selected)
            _q.validate_governance_frame(self._quant_frame(), require_price=True, require_non_day_trade_volume=True)
            features = _q.build_feature_matrix(
                self._quant_frame(), config=config, include_risk_metrics=False, label_horizons=()
            )
            self._features = features.to_pandas()
            self._windows = selected
        return self._features

    def _join(self, windows: List[int] | None = None) -> pd.DataFrame:
        feat = self._build(windows)
        out = self.df.copy()
        date_col = next((c for c in ("date", "Date", "datetime", "Datetime") if c in out.columns), None)
        left_date = pd.to_datetime(out[date_col] if date_col else out.index).dt.normalize()
        left_ticker = out["ticker"].astype(str) if "ticker" in out.columns else pd.Series("VAP", index=out.index)
        right = feat.copy()
        right["_date_key"] = pd.to_datetime(right["date"]).dt.normalize()
        right["_ticker_key"] = right["ticker"].astype(str)
        out["_date_key"] = left_date.to_numpy()
        out["_ticker_key"] = left_ticker.to_numpy()
        merged = out.merge(
            right.drop(columns=["date", "ticker"], errors="ignore"),
            on=["_date_key", "_ticker_key"], how="left", sort=False, suffixes=("", "_quantguard")
        )
        return merged.drop(columns=["_date_key", "_ticker_key"], errors="ignore")

    def _add_columns(self, mapping: dict[str, str], windows: List[int] | None = None) -> pd.DataFrame:
        merged = self._join(windows)
        for display_name, source_name in mapping.items():
            if source_name not in merged.columns:
                raise NotImplementedError(f"QuantGuard output missing: {source_name}")
            self.df[display_name] = merged[source_name].to_numpy()
        return self.df

    def compute_sma(self, periods: List[int] | None = None) -> pd.DataFrame:
        ps = periods or list(STANDARD_PERIODS)
        return self._add_columns({f"SMA_{p}": f"sma_{p}" for p in ps}, ps)

    def compute_ema(self, periods: List[int] | None = None) -> pd.DataFrame:
        ps = periods or list(STANDARD_PERIODS)
        return self._add_columns({f"EMA_{p}": f"ema_{p}" for p in ps}, ps)

    def compute_rsi(self, timeperiod: int = 14) -> pd.DataFrame:
        return self._add_columns({f"RSI_{timeperiod}": f"rsi_{timeperiod}"}, [20, 60])

    def compute_macd(self, **_: Any) -> pd.DataFrame:
        return self._add_columns({"MACD": "macd_line", "MACD_SIGNAL": "macd_signal", "MACD_HIST": "macd_histogram"}, [20, 60])

    def compute_atr(self, timeperiod: int = 14) -> pd.DataFrame:
        return self._add_columns({f"ATR_{timeperiod}": "atr"}, [20, 60])

    def compute_adx(self, timeperiod: int = 14) -> pd.DataFrame:
        return self._add_columns({f"ADX_{timeperiod}": f"adx_{timeperiod}"}, [20, 60])

    def compute_bbands(self, timeperiod: int = 20, **_: Any) -> pd.DataFrame:
        return self._add_columns({"BB_UPPER": f"bb_upper_{timeperiod}", "BB_MIDDLE": f"sma_{timeperiod}", "BB_LOWER": f"bb_lower_{timeperiod}"}, [timeperiod])

    def compute_obv(self) -> pd.DataFrame:
        return self._add_columns({"OBV": "obv"}, [20, 60])

    def compute_mfi(self, timeperiod: int = 14) -> pd.DataFrame:
        return self._add_columns({f"MFI_{timeperiod}": f"mfi_{timeperiod}"}, [20, 60])

    def compute_by_name(self, indicator_name: str, **kwargs: Any) -> pd.DataFrame:
        name = indicator_name.strip().lower()
        dispatch = {
            "sma": self.compute_sma, "ema": self.compute_ema, "rsi": self.compute_rsi,
            "macd": self.compute_macd, "atr": self.compute_atr, "adx": self.compute_adx,
            "bbands": self.compute_bbands, "obv": self.compute_obv, "mfi": self.compute_mfi,
        }
        if name not in dispatch:
            raise NotImplementedError(f"QuantGuard does not expose VAP indicator: {indicator_name}")
        return dispatch[name](**kwargs)

    def compute_standard_set(self) -> pd.DataFrame:
        self.compute_sma()
        self.compute_ema()
        self.compute_rsi()
        self.compute_macd()
        self.compute_atr()
        self.compute_adx()
        self.compute_bbands()
        self.compute_obv()
        self.compute_mfi()
        return self.df

    def compute_all(self) -> pd.DataFrame:
        return self.compute_standard_set()

    def compute_pattern_summary(self) -> pd.DataFrame:
        self.df["PATTERN_STATUS"] = "NOT_PROVIDED_BY_QUANTGUARD"
        return self.df

    def get_result(self) -> pd.DataFrame:
        return self.df.copy()


__all__ = ["VAPIndicatorEngine"]
