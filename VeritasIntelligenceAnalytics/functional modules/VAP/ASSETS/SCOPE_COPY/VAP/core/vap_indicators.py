#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-002: vap_indicators.py - TA-Lib Indicator Engine                      ║
║  Module ID: APM-002 | Version: 4.0.0                                       ║
║  Complete TA-Lib wrapper: 9 categories, 80+ indicators, CDL patterns       ║
║  Adj Close Priority: uses adj_close when available                         ║
║  Standard Periods: 5, 10, 20, 60, 120, 240 (unless indicator-specific)    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import logging
from typing import Dict, List, Optional, Any, Union

import numpy as np
import pandas as pd
import talib

from vap_config import (
    STANDARD_PERIODS, INDICATOR_DEFAULTS, INDICATOR_INPUTS,
    INDICATOR_CATEGORY_MAP, CDL_PATTERNS, IndicatorCategory,
    resolve_ohlcv_columns, get_price_column,
)

logger = logging.getLogger(__name__)


class VAPIndicatorEngine:
    """
    Complete TA-Lib indicator computation engine.
    - Auto-resolves adj_close vs close
    - Supports multi-period computation for period-based indicators
    - Returns results as new DataFrame columns with standardized naming
    """

    def __init__(self, df: pd.DataFrame):
        """
        Initialize with a normalized OHLCV DataFrame.
        Automatically resolves adj_close priority.
        """
        self.df = df.copy()
        self.col_map = resolve_ohlcv_columns(self.df)
        self._prepare_arrays()

    def _prepare_arrays(self):
        """Pre-extract numpy arrays for TA-Lib (requires float64)."""
        def _col(key: str) -> np.ndarray:
            col_name = self.col_map.get(key)
            if col_name and col_name in self.df.columns:
                return self.df[col_name].values.astype(np.float64)
            return None

        self._open   = _col("open")
        self._high   = _col("high")
        self._low    = _col("low")
        self._close  = _col("close")    # adj_close prioritized
        self._volume = _col("volume")

    def _get_input(self, col_key: str) -> np.ndarray:
        """Get input array by standardized key."""
        arr_map = {
            "open": self._open, "high": self._high,
            "low": self._low, "close": self._close,
            "volume": self._volume,
        }
        arr = arr_map.get(col_key)
        if arr is None:
            raise ValueError(f"Required column '{col_key}' not available in DataFrame")
        return arr

    # ═══════════════════════════════════════════════════════════════════
    # OVERLAP STUDIES
    # ═══════════════════════════════════════════════════════════════════
    def compute_sma(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        close = self._close
        for p in periods:
            self.df[f"SMA_{p}"] = talib.SMA(close, timeperiod=p)
        return self.df

    def compute_ema(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        close = self._close
        for p in periods:
            self.df[f"EMA_{p}"] = talib.EMA(close, timeperiod=p)
        return self.df

    def compute_wma(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"WMA_{p}"] = talib.WMA(self._close, timeperiod=p)
        return self.df

    def compute_dema(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"DEMA_{p}"] = talib.DEMA(self._close, timeperiod=p)
        return self.df

    def compute_tema(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"TEMA_{p}"] = talib.TEMA(self._close, timeperiod=p)
        return self.df

    def compute_trima(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"TRIMA_{p}"] = talib.TRIMA(self._close, timeperiod=p)
        return self.df

    def compute_t3(self, periods: List[int] = None, vfactor: float = 0.7) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"T3_{p}"] = talib.T3(self._close, timeperiod=p, vfactor=vfactor)
        return self.df

    def compute_kama(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"KAMA_{p}"] = talib.KAMA(self._close, timeperiod=p)
        return self.df

    def compute_bbands(self, timeperiod: int = 20, nbdevup: float = 2.0,
                       nbdevdn: float = 2.0, matype: int = 0) -> pd.DataFrame:
        upper, middle, lower = talib.BBANDS(
            self._close, timeperiod=timeperiod, nbdevup=nbdevup,
            nbdevdn=nbdevdn, matype=matype
        )
        self.df["BB_UPPER"] = upper
        self.df["BB_MIDDLE"] = middle
        self.df["BB_LOWER"] = lower
        return self.df

    def compute_sar(self, acceleration: float = 0.02, maximum: float = 0.2) -> pd.DataFrame:
        self.df["SAR"] = talib.SAR(self._high, self._low,
                                    acceleration=acceleration, maximum=maximum)
        return self.df

    def compute_sarext(self, **kwargs) -> pd.DataFrame:
        defaults = INDICATOR_DEFAULTS["SAREXT"]
        params = {**defaults, **kwargs}
        self.df["SAREXT"] = talib.SAREXT(self._high, self._low, **params)
        return self.df

    def compute_mama(self, fastlimit: float = 0.5, slowlimit: float = 0.05) -> pd.DataFrame:
        mama, fama = talib.MAMA(self._close, fastlimit=fastlimit, slowlimit=slowlimit)
        self.df["MAMA"] = mama
        self.df["FAMA"] = fama
        return self.df

    def compute_midpoint(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"MIDPOINT_{p}"] = talib.MIDPOINT(self._close, timeperiod=p)
        return self.df

    def compute_midprice(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"MIDPRICE_{p}"] = talib.MIDPRICE(self._high, self._low, timeperiod=p)
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # MOMENTUM INDICATORS
    # ═══════════════════════════════════════════════════════════════════
    def compute_rsi(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"RSI_{timeperiod}"] = talib.RSI(self._close, timeperiod=timeperiod)
        return self.df

    def compute_stoch(self, fastk_period: int = 9, slowk_period: int = 3,
                      slowk_matype: int = 0, slowd_period: int = 3,
                      slowd_matype: int = 0) -> pd.DataFrame:
        slowk, slowd = talib.STOCH(
            self._high, self._low, self._close,
            fastk_period=fastk_period, slowk_period=slowk_period,
            slowk_matype=slowk_matype, slowd_period=slowd_period,
            slowd_matype=slowd_matype
        )
        self.df["STOCH_K"] = slowk
        self.df["STOCH_D"] = slowd
        return self.df

    def compute_stochf(self, fastk_period: int = 5, fastd_period: int = 3,
                       fastd_matype: int = 0) -> pd.DataFrame:
        fastk, fastd = talib.STOCHF(
            self._high, self._low, self._close,
            fastk_period=fastk_period, fastd_period=fastd_period,
            fastd_matype=fastd_matype
        )
        self.df["STOCHF_K"] = fastk
        self.df["STOCHF_D"] = fastd
        return self.df

    def compute_stochrsi(self, timeperiod: int = 14, fastk_period: int = 5,
                         fastd_period: int = 3, fastd_matype: int = 0) -> pd.DataFrame:
        fastk, fastd = talib.STOCHRSI(
            self._close, timeperiod=timeperiod, fastk_period=fastk_period,
            fastd_period=fastd_period, fastd_matype=fastd_matype
        )
        self.df["STOCHRSI_K"] = fastk
        self.df["STOCHRSI_D"] = fastd
        return self.df

    def compute_macd(self, fastperiod: int = 12, slowperiod: int = 26,
                     signalperiod: int = 9) -> pd.DataFrame:
        macd, signal, hist = talib.MACD(
            self._close, fastperiod=fastperiod,
            slowperiod=slowperiod, signalperiod=signalperiod
        )
        self.df["MACD"] = macd
        self.df["MACD_SIGNAL"] = signal
        self.df["MACD_HIST"] = hist
        return self.df

    def compute_macdext(self, **kwargs) -> pd.DataFrame:
        defaults = INDICATOR_DEFAULTS["MACDEXT"]
        params = {**defaults, **kwargs}
        macd, signal, hist = talib.MACDEXT(self._close, **params)
        self.df["MACDEXT"] = macd
        self.df["MACDEXT_SIGNAL"] = signal
        self.df["MACDEXT_HIST"] = hist
        return self.df

    def compute_macdfix(self, signalperiod: int = 9) -> pd.DataFrame:
        macd, signal, hist = talib.MACDFIX(self._close, signalperiod=signalperiod)
        self.df["MACDFIX"] = macd
        self.df["MACDFIX_SIGNAL"] = signal
        self.df["MACDFIX_HIST"] = hist
        return self.df

    def compute_mom(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"MOM_{p}"] = talib.MOM(self._close, timeperiod=p)
        return self.df

    def compute_roc(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"ROC_{p}"] = talib.ROC(self._close, timeperiod=p)
        return self.df

    def compute_rocp(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"ROCP_{p}"] = talib.ROCP(self._close, timeperiod=p)
        return self.df

    def compute_rocr(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"ROCR_{p}"] = talib.ROCR(self._close, timeperiod=p)
        return self.df

    def compute_rocr100(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"ROCR100_{p}"] = talib.ROCR100(self._close, timeperiod=p)
        return self.df

    def compute_trix(self, periods: List[int] = None) -> pd.DataFrame:
        periods = periods or STANDARD_PERIODS
        for p in periods:
            self.df[f"TRIX_{p}"] = talib.TRIX(self._close, timeperiod=p)
        return self.df

    def compute_cci(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"CCI_{timeperiod}"] = talib.CCI(self._high, self._low, self._close,
                                                   timeperiod=timeperiod)
        return self.df

    def compute_mfi(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"MFI_{timeperiod}"] = talib.MFI(self._high, self._low, self._close,
                                                   self._volume, timeperiod=timeperiod)
        return self.df

    def compute_willr(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"WILLR_{timeperiod}"] = talib.WILLR(self._high, self._low, self._close,
                                                      timeperiod=timeperiod)
        return self.df

    def compute_bop(self) -> pd.DataFrame:
        self.df["BOP"] = talib.BOP(self._open, self._high, self._low, self._close)
        return self.df

    def compute_aroon(self, timeperiod: int = 25) -> pd.DataFrame:
        down, up = talib.AROON(self._high, self._low, timeperiod=timeperiod)
        self.df["AROON_DOWN"] = down
        self.df["AROON_UP"] = up
        return self.df

    def compute_aroonosc(self, timeperiod: int = 25) -> pd.DataFrame:
        self.df[f"AROONOSC_{timeperiod}"] = talib.AROONOSC(self._high, self._low,
                                                             timeperiod=timeperiod)
        return self.df

    def compute_adx(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"ADX_{timeperiod}"] = talib.ADX(self._high, self._low, self._close,
                                                   timeperiod=timeperiod)
        return self.df

    def compute_adxr(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"ADXR_{timeperiod}"] = talib.ADXR(self._high, self._low, self._close,
                                                     timeperiod=timeperiod)
        return self.df

    def compute_plus_di(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"PLUS_DI_{timeperiod}"] = talib.PLUS_DI(self._high, self._low, self._close,
                                                           timeperiod=timeperiod)
        return self.df

    def compute_minus_di(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"MINUS_DI_{timeperiod}"] = talib.MINUS_DI(self._high, self._low, self._close,
                                                             timeperiod=timeperiod)
        return self.df

    def compute_plus_dm(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"PLUS_DM_{timeperiod}"] = talib.PLUS_DM(self._high, self._low,
                                                           timeperiod=timeperiod)
        return self.df

    def compute_minus_dm(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"MINUS_DM_{timeperiod}"] = talib.MINUS_DM(self._high, self._low,
                                                             timeperiod=timeperiod)
        return self.df

    def compute_ppo(self, fastperiod: int = 12, slowperiod: int = 26,
                    matype: int = 0) -> pd.DataFrame:
        self.df["PPO"] = talib.PPO(self._close, fastperiod=fastperiod,
                                    slowperiod=slowperiod, matype=matype)
        return self.df

    def compute_ultosc(self, timeperiod1: int = 7, timeperiod2: int = 14,
                       timeperiod3: int = 28) -> pd.DataFrame:
        self.df["ULTOSC"] = talib.ULTOSC(self._high, self._low, self._close,
                                          timeperiod1=timeperiod1, timeperiod2=timeperiod2,
                                          timeperiod3=timeperiod3)
        return self.df

    def compute_cmo(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"CMO_{timeperiod}"] = talib.CMO(self._close, timeperiod=timeperiod)
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # VOLUME INDICATORS
    # ═══════════════════════════════════════════════════════════════════
    def compute_obv(self) -> pd.DataFrame:
        self.df["OBV"] = talib.OBV(self._close, self._volume)
        return self.df

    def compute_ad(self) -> pd.DataFrame:
        self.df["AD"] = talib.AD(self._high, self._low, self._close, self._volume)
        return self.df

    def compute_adosc(self, fastperiod: int = 3, slowperiod: int = 10) -> pd.DataFrame:
        self.df["ADOSC"] = talib.ADOSC(self._high, self._low, self._close, self._volume,
                                        fastperiod=fastperiod, slowperiod=slowperiod)
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # VOLATILITY
    # ═══════════════════════════════════════════════════════════════════
    def compute_atr(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"ATR_{timeperiod}"] = talib.ATR(self._high, self._low, self._close,
                                                   timeperiod=timeperiod)
        return self.df

    def compute_natr(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"NATR_{timeperiod}"] = talib.NATR(self._high, self._low, self._close,
                                                     timeperiod=timeperiod)
        return self.df

    def compute_trange(self) -> pd.DataFrame:
        self.df["TRANGE"] = talib.TRANGE(self._high, self._low, self._close)
        return self.df

    def compute_stddev(self, timeperiod: int = 20, nbdev: float = 1.0) -> pd.DataFrame:
        self.df[f"STDDEV_{timeperiod}"] = talib.STDDEV(self._close, timeperiod=timeperiod,
                                                         nbdev=nbdev)
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # PRICE TRANSFORM
    # ═══════════════════════════════════════════════════════════════════
    def compute_avgprice(self) -> pd.DataFrame:
        self.df["AVGPRICE"] = talib.AVGPRICE(self._open, self._high, self._low, self._close)
        return self.df

    def compute_medprice(self) -> pd.DataFrame:
        self.df["MEDPRICE"] = talib.MEDPRICE(self._high, self._low)
        return self.df

    def compute_typprice(self) -> pd.DataFrame:
        self.df["TYPPRICE"] = talib.TYPPRICE(self._high, self._low, self._close)
        return self.df

    def compute_wclprice(self) -> pd.DataFrame:
        self.df["WCLPRICE"] = talib.WCLPRICE(self._high, self._low, self._close)
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # CYCLE INDICATORS
    # ═══════════════════════════════════════════════════════════════════
    def compute_ht_dcperiod(self) -> pd.DataFrame:
        self.df["HT_DCPERIOD"] = talib.HT_DCPERIOD(self._close)
        return self.df

    def compute_ht_dcphase(self) -> pd.DataFrame:
        self.df["HT_DCPHASE"] = talib.HT_DCPHASE(self._close)
        return self.df

    def compute_ht_phasor(self) -> pd.DataFrame:
        inphase, quadrature = talib.HT_PHASOR(self._close)
        self.df["HT_PHASOR_INPHASE"] = inphase
        self.df["HT_PHASOR_QUAD"] = quadrature
        return self.df

    def compute_ht_sine(self) -> pd.DataFrame:
        sine, leadsine = talib.HT_SINE(self._close)
        self.df["HT_SINE"] = sine
        self.df["HT_LEADSINE"] = leadsine
        return self.df

    def compute_ht_trendmode(self) -> pd.DataFrame:
        self.df["HT_TRENDMODE"] = talib.HT_TRENDMODE(self._close)
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # PATTERN RECOGNITION (All CDL patterns)
    # ═══════════════════════════════════════════════════════════════════
    def compute_patterns(self, patterns: List[str] = None) -> pd.DataFrame:
        """Compute all or selected candlestick patterns."""
        patterns = patterns or CDL_PATTERNS
        for pat in patterns:
            func = getattr(talib, pat, None)
            if func:
                try:
                    self.df[pat] = func(self._open, self._high, self._low, self._close)
                except Exception as e:
                    logger.warning(f"Pattern {pat} failed: {e}")
        return self.df

    def compute_pattern_summary(self) -> pd.DataFrame:
        """Compute all patterns and add summary column counting active signals."""
        self.compute_patterns()
        pattern_cols = [c for c in self.df.columns if c.startswith("CDL")]
        if pattern_cols:
            self.df["CDL_BULLISH_COUNT"] = (self.df[pattern_cols] > 0).sum(axis=1)
            self.df["CDL_BEARISH_COUNT"] = (self.df[pattern_cols] < 0).sum(axis=1)
            self.df["CDL_NET_SIGNAL"] = self.df["CDL_BULLISH_COUNT"] - self.df["CDL_BEARISH_COUNT"]
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # STATISTIC FUNCTIONS
    # ═══════════════════════════════════════════════════════════════════
    def compute_linearreg(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"LINEARREG_{timeperiod}"] = talib.LINEARREG(self._close, timeperiod=timeperiod)
        return self.df

    def compute_linearreg_angle(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"LINEARREG_ANGLE_{timeperiod}"] = talib.LINEARREG_ANGLE(self._close, timeperiod=timeperiod)
        return self.df

    def compute_linearreg_slope(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"LINEARREG_SLOPE_{timeperiod}"] = talib.LINEARREG_SLOPE(self._close, timeperiod=timeperiod)
        return self.df

    def compute_linearreg_intercept(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"LINEARREG_INTERCEPT_{timeperiod}"] = talib.LINEARREG_INTERCEPT(self._close, timeperiod=timeperiod)
        return self.df

    def compute_correl(self, timeperiod: int = 30) -> pd.DataFrame:
        self.df[f"CORREL_{timeperiod}"] = talib.CORREL(self._high, self._low, timeperiod=timeperiod)
        return self.df

    def compute_beta(self, timeperiod: int = 5) -> pd.DataFrame:
        self.df[f"BETA_{timeperiod}"] = talib.BETA(self._high, self._low, timeperiod=timeperiod)
        return self.df

    def compute_var(self, timeperiod: int = 20, nbdev: float = 1.0) -> pd.DataFrame:
        self.df[f"VAR_{timeperiod}"] = talib.VAR(self._close, timeperiod=timeperiod, nbdev=nbdev)
        return self.df

    def compute_tsf(self, timeperiod: int = 14) -> pd.DataFrame:
        self.df[f"TSF_{timeperiod}"] = talib.TSF(self._close, timeperiod=timeperiod)
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # MATH TRANSFORM
    # ═══════════════════════════════════════════════════════════════════
    def compute_math_transform(self, functions: List[str] = None) -> pd.DataFrame:
        all_funcs = ["SIN","COS","TAN","EXP","LN","LOG10","SQRT",
                     "CEIL","FLOOR","ACOS","ASIN","ATAN","COSH","SINH","TANH"]
        functions = functions or all_funcs
        for fn in functions:
            func = getattr(talib, fn, None)
            if func:
                try:
                    self.df[f"MATH_{fn}"] = func(self._close)
                except Exception as e:
                    logger.warning(f"Math {fn} failed: {e}")
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # MATH OPERATORS
    # ═══════════════════════════════════════════════════════════════════
    def compute_math_operators(self) -> pd.DataFrame:
        self.df["MATH_ADD"] = talib.ADD(self._high, self._low)
        self.df["MATH_SUB"] = talib.SUB(self._high, self._low)
        self.df["MATH_MULT"] = talib.MULT(self._high, self._low)
        self.df["MATH_DIV"] = talib.DIV(self._high, self._low)
        for p in [30]:
            self.df[f"MATH_SUM_{p}"] = talib.SUM(self._close, timeperiod=p)
            self.df[f"MATH_MAX_{p}"] = talib.MAX(self._close, timeperiod=p)
            self.df[f"MATH_MIN_{p}"] = talib.MIN(self._close, timeperiod=p)
            self.df[f"MATH_MAXINDEX_{p}"] = talib.MAXINDEX(self._close, timeperiod=p)
            self.df[f"MATH_MININDEX_{p}"] = talib.MININDEX(self._close, timeperiod=p)
            mn, mx = talib.MINMAX(self._close, timeperiod=p)
            self.df[f"MATH_MINMAX_MIN_{p}"] = mn
            self.df[f"MATH_MINMAX_MAX_{p}"] = mx
            mni, mxi = talib.MINMAXINDEX(self._close, timeperiod=p)
            self.df[f"MATH_MINMAXIDX_MIN_{p}"] = mni
            self.df[f"MATH_MINMAXIDX_MAX_{p}"] = mxi
        return self.df

    # ═══════════════════════════════════════════════════════════════════
    # BATCH / ALL-IN-ONE
    # ═══════════════════════════════════════════════════════════════════
    def compute_by_name(self, indicator_name: str, **kwargs) -> pd.DataFrame:
        """Compute a single indicator by name with optional parameter overrides."""
        method_name = f"compute_{indicator_name.lower()}"
        method = getattr(self, method_name, None)
        if method:
            return method(**kwargs)
        # Try pattern
        if indicator_name.startswith("CDL"):
            return self.compute_patterns([indicator_name])
        raise ValueError(f"Unknown indicator: {indicator_name}")

    def compute_category(self, category: IndicatorCategory) -> pd.DataFrame:
        """Compute all indicators in a category with defaults."""
        cat_map = {
            IndicatorCategory.OVERLAP: [
                "sma", "ema", "wma", "dema", "tema", "trima", "t3", "kama",
                "bbands", "sar", "mama", "midpoint", "midprice"
            ],
            IndicatorCategory.MOMENTUM: [
                "rsi", "stoch", "stochf", "stochrsi", "macd", "macdext", "macdfix",
                "mom", "roc", "rocp", "rocr", "rocr100", "trix",
                "cci", "mfi", "willr", "bop", "aroon", "aroonosc",
                "adx", "adxr", "plus_di", "minus_di", "plus_dm", "minus_dm",
                "ppo", "ultosc", "cmo"
            ],
            IndicatorCategory.VOLUME: ["obv", "ad", "adosc"],
            IndicatorCategory.VOLATILITY: ["atr", "natr", "trange", "stddev"],
            IndicatorCategory.PRICE_TRANSFORM: ["avgprice", "medprice", "typprice", "wclprice"],
            IndicatorCategory.CYCLE: ["ht_dcperiod", "ht_dcphase", "ht_phasor", "ht_sine", "ht_trendmode"],
            IndicatorCategory.PATTERN: ["pattern_summary"],
            IndicatorCategory.STATISTIC: [
                "linearreg", "linearreg_angle", "linearreg_slope", "linearreg_intercept",
                "correl", "beta", "var", "tsf"
            ],
            IndicatorCategory.MATH_TRANSFORM: ["math_transform"],
            IndicatorCategory.MATH_OPERATORS: ["math_operators"],
        }
        for method_name in cat_map.get(category, []):
            method = getattr(self, f"compute_{method_name}", None)
            if method:
                try:
                    method()
                except Exception as e:
                    logger.warning(f"compute_{method_name} failed: {e}")
        return self.df

    def compute_all(self) -> pd.DataFrame:
        """Compute ALL indicators across ALL categories."""
        for cat in IndicatorCategory:
            logger.info(f"Computing category: {cat.value}")
            self.compute_category(cat)
        return self.df

    def compute_standard_set(self) -> pd.DataFrame:
        """Compute a standard analysis set (most commonly used indicators)."""
        self.compute_sma([5, 10, 20, 60, 120, 240])
        self.compute_ema([12, 26])
        self.compute_bbands()
        self.compute_rsi()
        self.compute_macd()
        self.compute_stoch()
        self.compute_obv()
        self.compute_atr()
        self.compute_adx()
        self.compute_cci()
        self.compute_mfi()
        self.compute_willr()
        self.compute_trange()
        self.compute_avgprice()
        self.compute_typprice()
        return self.df

    def get_result(self) -> pd.DataFrame:
        """Return the enriched DataFrame."""
        return self.df


if __name__ == "__main__":
    from vap_data_adapter import VAPDataAdapter
    adapter = VAPDataAdapter()
    demo = adapter.generate_demo_data()
    engine = VAPIndicatorEngine(demo)
    engine.compute_standard_set()
    result = engine.get_result()
    print(f"Result shape: {result.shape}")
    print(f"Columns: {sorted(result.columns.tolist())}")
    print(f"Adj close used: {engine.col_map['close']}")
