#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  APM-000: vap_config.py - VeritasAutoPlot System Configuration             ║
║  Module ID: APM-000 | Version: 4.0.0 | Date: 2026-02-15                   ║
║  Description: Global defaults, locked patterns, color palettes,            ║
║               TA-Lib indicator registry, adj close priority logic          ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum
from pathlib import Path


# ═══════════════════════════════════════════════════════════════════════════════
# LOCKED PATTERNS (Inherited from VRN/VIA - DO NOT MODIFY)
# ═══════════════════════════════════════════════════════════════════════════════
TW_TICKER_REGEX    = r"(?!202\d|2030)[1-9]\d{3}"
TW_YFINANCE_REGEX  = r"[1-9]\d{3}\.(TW|TWO)"
TW_BLOOMBERG_REGEX = r"[1-9]\d{3}\s+TT"

# ═══════════════════════════════════════════════════════════════════════════════
# LOCKED COLOR PALETTES
# ═══════════════════════════════════════════════════════════════════════════════
SEABORN_TAB10 = [
    "#4C72B0", "#DD8452", "#55A868", "#C44E52", "#8172B3",
    "#937860", "#DA8BC3", "#8C8C8C", "#CCB974", "#64B5CD",
]

CRISIS_PALETTE = [
    "#7f7f7f", "#777f8c", "#6f7e99", "#677ea5",
    "#5f7db2", "#587cbf", "#507ccc", "#487bd9",
]

UP_COLOR    = "#E15241"
DOWN_COLOR  = "#22AB94"
FOREIGN_BUY  = "#58A6FF"
FOREIGN_SELL = "#DA3633"


# ═══════════════════════════════════════════════════════════════════════════════
# PATHS
# ═══════════════════════════════════════════════════════════════════════════════
class VAPPaths:
    ROOT       = Path(r"C:\VeritasIntelligenceAnalytics\VeritasAutoPlot")
    VDF_ROOT   = Path(r"C:\VeritasIntelligenceAnalytics\VeritasDataForge")
    VRN_ROOT   = Path(r"C:\VeritasIntelligenceAnalytics\VeritasReportNova")
    ENV_BASE   = Path(r"C:\Users\tonyk\envs")
    CORE_ENV   = ENV_BASE / "via_core"
    TEMPLATES  = ROOT / "templates"
    OUTPUT     = ROOT / "output"
    LOGS       = ROOT / "logs"
    FRONTEND   = ROOT / "frontend"


# ═══════════════════════════════════════════════════════════════════════════════
# STANDARD PERIOD SETS
# ═══════════════════════════════════════════════════════════════════════════════
STANDARD_PERIODS = [5, 10, 20, 60, 120, 240]

# Indicator-specific default periods (override STANDARD_PERIODS when specified)
INDICATOR_DEFAULTS = {
    # Overlap Studies
    "SMA":       {"periods": STANDARD_PERIODS},
    "EMA":       {"periods": STANDARD_PERIODS},
    "WMA":       {"periods": STANDARD_PERIODS},
    "DEMA":      {"periods": STANDARD_PERIODS},
    "TEMA":      {"periods": STANDARD_PERIODS},
    "TRIMA":     {"periods": STANDARD_PERIODS},
    "T3":        {"periods": STANDARD_PERIODS, "vfactor": 0.7},
    "KAMA":      {"periods": STANDARD_PERIODS},
    "BBANDS":    {"timeperiod": 20, "nbdevup": 2.0, "nbdevdn": 2.0, "matype": 0},
    "SAR":       {"acceleration": 0.02, "maximum": 0.2},
    "SAREXT":    {"startvalue": 0.02, "offsetonreverse": 0, "accelerationinitlong": 0.02,
                  "accelerationlong": 0.02, "accelerationmaxlong": 0.2,
                  "accelerationinitshort": 0.02, "accelerationshort": 0.02,
                  "accelerationmaxshort": 0.2},
    "MAMA":      {"fastlimit": 0.5, "slowlimit": 0.05},
    "MIDPOINT":  {"periods": STANDARD_PERIODS},
    "MIDPRICE":  {"periods": STANDARD_PERIODS},

    # Momentum Indicators
    "RSI":       {"timeperiod": 14},
    "STOCH":     {"fastk_period": 9, "slowk_period": 3, "slowk_matype": 0,
                  "slowd_period": 3, "slowd_matype": 0},
    "STOCHF":    {"fastk_period": 5, "fastd_period": 3, "fastd_matype": 0},
    "STOCHRSI":  {"timeperiod": 14, "fastk_period": 5, "fastd_period": 3, "fastd_matype": 0},
    "MACD":      {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9},
    "MACDEXT":   {"fastperiod": 12, "slowperiod": 26, "signalperiod": 9,
                  "fastmatype": 0, "slowmatype": 0, "signalmatype": 0},
    "MACDFIX":   {"signalperiod": 9},
    "MOM":       {"periods": STANDARD_PERIODS},
    "ROC":       {"periods": STANDARD_PERIODS},
    "ROCP":      {"periods": STANDARD_PERIODS},
    "ROCR":      {"periods": STANDARD_PERIODS},
    "ROCR100":   {"periods": STANDARD_PERIODS},
    "TRIX":      {"periods": STANDARD_PERIODS},
    "CCI":       {"timeperiod": 14},
    "MFI":       {"timeperiod": 14},
    "WILLR":     {"timeperiod": 14},
    "BOP":       {},
    "AROON":     {"timeperiod": 25},
    "AROONOSC":  {"timeperiod": 25},
    "ADX":       {"timeperiod": 14},
    "ADXR":      {"timeperiod": 14},
    "PLUS_DI":   {"timeperiod": 14},
    "MINUS_DI":  {"timeperiod": 14},
    "PLUS_DM":   {"timeperiod": 14},
    "MINUS_DM":  {"timeperiod": 14},
    "PPO":       {"fastperiod": 12, "slowperiod": 26, "matype": 0},
    "ULTOSC":    {"timeperiod1": 7, "timeperiod2": 14, "timeperiod3": 28},
    "CMO":       {"timeperiod": 14},

    # Volume Indicators
    "OBV":       {},
    "AD":        {},
    "ADOSC":     {"fastperiod": 3, "slowperiod": 10},

    # Volatility
    "ATR":       {"timeperiod": 14},
    "NATR":      {"timeperiod": 14},
    "TRANGE":    {},
    "STDDEV":    {"timeperiod": 20, "nbdev": 1.0},

    # Price Transform
    "AVGPRICE":  {},
    "MEDPRICE":  {},
    "TYPPRICE":  {},
    "WCLPRICE":  {},

    # Cycle Indicators
    "HT_DCPERIOD":  {},
    "HT_DCPHASE":   {},
    "HT_PHASOR":    {},
    "HT_SINE":      {},
    "HT_TRENDMODE": {},

    # Statistic Functions
    "LINEARREG":           {"timeperiod": 14},
    "LINEARREG_ANGLE":     {"timeperiod": 14},
    "LINEARREG_SLOPE":     {"timeperiod": 14},
    "LINEARREG_INTERCEPT": {"timeperiod": 14},
    "CORREL":              {"timeperiod": 30},
    "BETA":                {"timeperiod": 5},
    "VAR":                 {"timeperiod": 20, "nbdev": 1.0},
    "TSF":                 {"timeperiod": 14},

    # Math Transform
    "SIN": {}, "COS": {}, "TAN": {}, "EXP": {}, "LN": {}, "LOG10": {},
    "SQRT": {}, "CEIL": {}, "FLOOR": {}, "ACOS": {}, "ASIN": {}, "ATAN": {},
    "COSH": {}, "SINH": {}, "TANH": {},

    # Math Operators
    "ADD": {}, "SUB": {}, "MULT": {}, "DIV": {},
    "SUM":      {"timeperiod": 30},
    "MAX":      {"timeperiod": 30},
    "MIN":      {"timeperiod": 30},
    "MAXINDEX": {"timeperiod": 30},
    "MININDEX": {"timeperiod": 30},
    "MINMAX":   {"timeperiod": 30},
    "MINMAXINDEX": {"timeperiod": 30},
}


# ═══════════════════════════════════════════════════════════════════════════════
# INDICATOR CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════
class IndicatorCategory(Enum):
    OVERLAP    = "Overlap Studies"
    MOMENTUM   = "Momentum Indicators"
    VOLUME     = "Volume Indicators"
    VOLATILITY = "Volatility"
    PRICE_TRANSFORM = "Price Transform"
    CYCLE      = "Cycle Indicators"
    PATTERN    = "Pattern Recognition"
    STATISTIC  = "Statistic Functions"
    MATH_TRANSFORM = "Math Transform"
    MATH_OPERATORS = "Math Operators"


INDICATOR_CATEGORY_MAP: Dict[str, IndicatorCategory] = {
    # Overlap
    "SMA": IndicatorCategory.OVERLAP, "EMA": IndicatorCategory.OVERLAP,
    "WMA": IndicatorCategory.OVERLAP, "DEMA": IndicatorCategory.OVERLAP,
    "TEMA": IndicatorCategory.OVERLAP, "TRIMA": IndicatorCategory.OVERLAP,
    "T3": IndicatorCategory.OVERLAP, "BBANDS": IndicatorCategory.OVERLAP,
    "SAR": IndicatorCategory.OVERLAP, "SAREXT": IndicatorCategory.OVERLAP,
    "KAMA": IndicatorCategory.OVERLAP, "MAMA": IndicatorCategory.OVERLAP,
    "MIDPOINT": IndicatorCategory.OVERLAP, "MIDPRICE": IndicatorCategory.OVERLAP,
    # Momentum
    "RSI": IndicatorCategory.MOMENTUM, "STOCH": IndicatorCategory.MOMENTUM,
    "STOCHF": IndicatorCategory.MOMENTUM, "STOCHRSI": IndicatorCategory.MOMENTUM,
    "MACD": IndicatorCategory.MOMENTUM, "MACDEXT": IndicatorCategory.MOMENTUM,
    "MACDFIX": IndicatorCategory.MOMENTUM, "MOM": IndicatorCategory.MOMENTUM,
    "ROC": IndicatorCategory.MOMENTUM, "ROCP": IndicatorCategory.MOMENTUM,
    "ROCR": IndicatorCategory.MOMENTUM, "ROCR100": IndicatorCategory.MOMENTUM,
    "TRIX": IndicatorCategory.MOMENTUM, "CCI": IndicatorCategory.MOMENTUM,
    "MFI": IndicatorCategory.MOMENTUM, "WILLR": IndicatorCategory.MOMENTUM,
    "BOP": IndicatorCategory.MOMENTUM, "AROON": IndicatorCategory.MOMENTUM,
    "AROONOSC": IndicatorCategory.MOMENTUM, "ADX": IndicatorCategory.MOMENTUM,
    "ADXR": IndicatorCategory.MOMENTUM, "PLUS_DI": IndicatorCategory.MOMENTUM,
    "MINUS_DI": IndicatorCategory.MOMENTUM, "PLUS_DM": IndicatorCategory.MOMENTUM,
    "MINUS_DM": IndicatorCategory.MOMENTUM, "PPO": IndicatorCategory.MOMENTUM,
    "ULTOSC": IndicatorCategory.MOMENTUM, "CMO": IndicatorCategory.MOMENTUM,
    # Volume
    "OBV": IndicatorCategory.VOLUME, "AD": IndicatorCategory.VOLUME,
    "ADOSC": IndicatorCategory.VOLUME,
    # Volatility
    "ATR": IndicatorCategory.VOLATILITY, "NATR": IndicatorCategory.VOLATILITY,
    "TRANGE": IndicatorCategory.VOLATILITY, "STDDEV": IndicatorCategory.VOLATILITY,
    # Price Transform
    "AVGPRICE": IndicatorCategory.PRICE_TRANSFORM, "MEDPRICE": IndicatorCategory.PRICE_TRANSFORM,
    "TYPPRICE": IndicatorCategory.PRICE_TRANSFORM, "WCLPRICE": IndicatorCategory.PRICE_TRANSFORM,
    # Cycle
    "HT_DCPERIOD": IndicatorCategory.CYCLE, "HT_DCPHASE": IndicatorCategory.CYCLE,
    "HT_PHASOR": IndicatorCategory.CYCLE, "HT_SINE": IndicatorCategory.CYCLE,
    "HT_TRENDMODE": IndicatorCategory.CYCLE,
    # Statistic
    "LINEARREG": IndicatorCategory.STATISTIC, "LINEARREG_ANGLE": IndicatorCategory.STATISTIC,
    "LINEARREG_SLOPE": IndicatorCategory.STATISTIC, "LINEARREG_INTERCEPT": IndicatorCategory.STATISTIC,
    "CORREL": IndicatorCategory.STATISTIC, "BETA": IndicatorCategory.STATISTIC,
    "VAR": IndicatorCategory.STATISTIC, "TSF": IndicatorCategory.STATISTIC,
    # Math Transform
    "SIN": IndicatorCategory.MATH_TRANSFORM, "COS": IndicatorCategory.MATH_TRANSFORM,
    "TAN": IndicatorCategory.MATH_TRANSFORM, "EXP": IndicatorCategory.MATH_TRANSFORM,
    "LN": IndicatorCategory.MATH_TRANSFORM, "LOG10": IndicatorCategory.MATH_TRANSFORM,
    "SQRT": IndicatorCategory.MATH_TRANSFORM, "CEIL": IndicatorCategory.MATH_TRANSFORM,
    "FLOOR": IndicatorCategory.MATH_TRANSFORM, "ACOS": IndicatorCategory.MATH_TRANSFORM,
    "ASIN": IndicatorCategory.MATH_TRANSFORM, "ATAN": IndicatorCategory.MATH_TRANSFORM,
    "COSH": IndicatorCategory.MATH_TRANSFORM, "SINH": IndicatorCategory.MATH_TRANSFORM,
    "TANH": IndicatorCategory.MATH_TRANSFORM,
    # Math Operators
    "ADD": IndicatorCategory.MATH_OPERATORS, "SUB": IndicatorCategory.MATH_OPERATORS,
    "MULT": IndicatorCategory.MATH_OPERATORS, "DIV": IndicatorCategory.MATH_OPERATORS,
    "SUM": IndicatorCategory.MATH_OPERATORS, "MAX": IndicatorCategory.MATH_OPERATORS,
    "MIN": IndicatorCategory.MATH_OPERATORS, "MAXINDEX": IndicatorCategory.MATH_OPERATORS,
    "MININDEX": IndicatorCategory.MATH_OPERATORS, "MINMAX": IndicatorCategory.MATH_OPERATORS,
    "MINMAXINDEX": IndicatorCategory.MATH_OPERATORS,
}

# Complete CDL pattern list (Pattern Recognition)
CDL_PATTERNS = [
    "CDL2CROWS", "CDL3BLACKCROWS", "CDL3INSIDE", "CDL3LINESTRIKE",
    "CDL3OUTSIDE", "CDL3STARSINSOUTH", "CDL3WHITESOLDIERS",
    "CDLABANDONEDBABY", "CDLADVANCEBLOCK", "CDLBELTHOLD",
    "CDLBREAKAWAY", "CDLCLOSINGMARUBOZU", "CDLCONCEALBABYSWALL",
    "CDLCOUNTERATTACK", "CDLDARKCLOUDCOVER", "CDLDOJI",
    "CDLDOJISTAR", "CDLDRAGONFLYDOJI", "CDLENGULFING",
    "CDLEVENINGDOJISTAR", "CDLEVENINGSTAR", "CDLGAPSIDESIDEWHITE",
    "CDLGRAVESTONEDOJI", "CDLHAMMER", "CDLHANGINGMAN",
    "CDLHARAMI", "CDLHARAMICROSS", "CDLHIGHWAVE",
    "CDLHIKKAKE", "CDLHIKKAKEMOD", "CDLHOMINGPIGEON",
    "CDLIDENTICAL3CROWS", "CDLINNECK", "CDLINVERTEDHAMMER",
    "CDLKICKING", "CDLKICKINGBYLENGTH", "CDLLADDERBOTTOM",
    "CDLLONGLEGGEDDOJI", "CDLLONGLINE", "CDLMARUBOZU",
    "CDLMATCHINGLOW", "CDLMATHOLD", "CDLMORNINGDOJISTAR",
    "CDLMORNINGSTAR", "CDLONNECK", "CDLPIERCING",
    "CDLRICKSHAWMAN", "CDLRISEFALL3METHODS", "CDLSEPARATINGLINES",
    "CDLSHOOTINGSTAR", "CDLSHORTLINE", "CDLSPINNINGTOP",
    "CDLSTALLEDPATTERN", "CDLSTICKSANDWICH", "CDLTAKURI",
    "CDLTASUKIGAP", "CDLTHRUSTING", "CDLTRISTAR",
    "CDLUNIQUE3RIVER", "CDLUPSIDEGAP2CROWS", "CDLXSIDEGAP3METHODS",
]
for p in CDL_PATTERNS:
    INDICATOR_CATEGORY_MAP[p] = IndicatorCategory.PATTERN


# ═══════════════════════════════════════════════════════════════════════════════
# INPUT COLUMN REQUIREMENTS PER INDICATOR
# ═══════════════════════════════════════════════════════════════════════════════
# "close" = uses adj_close if available, else close
# Keys: indicator name -> tuple of required OHLCV columns
INDICATOR_INPUTS: Dict[str, Tuple[str, ...]] = {
    # Overlap - most use close (adj_close priority)
    "SMA": ("close",), "EMA": ("close",), "WMA": ("close",), "DEMA": ("close",),
    "TEMA": ("close",), "TRIMA": ("close",), "T3": ("close",), "KAMA": ("close",),
    "BBANDS": ("close",), "MIDPOINT": ("close",),
    "SAR": ("high", "low"), "SAREXT": ("high", "low"),
    "MAMA": ("close",), "MIDPRICE": ("high", "low"),

    # Momentum
    "RSI": ("close",), "MOM": ("close",), "ROC": ("close",),
    "ROCP": ("close",), "ROCR": ("close",), "ROCR100": ("close",),
    "TRIX": ("close",), "CMO": ("close",),
    "STOCH": ("high", "low", "close"),
    "STOCHF": ("high", "low", "close"),
    "STOCHRSI": ("close",),
    "MACD": ("close",), "MACDEXT": ("close",), "MACDFIX": ("close",),
    "CCI": ("high", "low", "close"),
    "MFI": ("high", "low", "close", "volume"),
    "WILLR": ("high", "low", "close"),
    "BOP": ("open", "high", "low", "close"),
    "AROON": ("high", "low"), "AROONOSC": ("high", "low"),
    "ADX": ("high", "low", "close"), "ADXR": ("high", "low", "close"),
    "PLUS_DI": ("high", "low", "close"), "MINUS_DI": ("high", "low", "close"),
    "PLUS_DM": ("high", "low"), "MINUS_DM": ("high", "low"),
    "PPO": ("close",),
    "ULTOSC": ("high", "low", "close"),

    # Volume
    "OBV": ("close", "volume"),
    "AD": ("high", "low", "close", "volume"),
    "ADOSC": ("high", "low", "close", "volume"),

    # Volatility
    "ATR": ("high", "low", "close"), "NATR": ("high", "low", "close"),
    "TRANGE": ("high", "low", "close"),
    "STDDEV": ("close",),

    # Price Transform
    "AVGPRICE": ("open", "high", "low", "close"),
    "MEDPRICE": ("high", "low"),
    "TYPPRICE": ("high", "low", "close"),
    "WCLPRICE": ("high", "low", "close"),

    # Cycle
    "HT_DCPERIOD": ("close",), "HT_DCPHASE": ("close",),
    "HT_PHASOR": ("close",), "HT_SINE": ("close",),
    "HT_TRENDMODE": ("close",),

    # Statistic
    "LINEARREG": ("close",), "LINEARREG_ANGLE": ("close",),
    "LINEARREG_SLOPE": ("close",), "LINEARREG_INTERCEPT": ("close",),
    "CORREL": ("high", "low"),  # two series
    "BETA": ("high", "low"),    # two series
    "VAR": ("close",), "TSF": ("close",),

    # Math Transform - all single series (close)
    **{k: ("close",) for k in ["SIN","COS","TAN","EXP","LN","LOG10","SQRT",
                                 "CEIL","FLOOR","ACOS","ASIN","ATAN","COSH","SINH","TANH"]},
    # Math Operators
    "ADD": ("high", "low"), "SUB": ("high", "low"),
    "MULT": ("high", "low"), "DIV": ("high", "low"),
    "SUM": ("close",), "MAX": ("close",), "MIN": ("close",),
    "MAXINDEX": ("close",), "MININDEX": ("close",),
    "MINMAX": ("close",), "MINMAXINDEX": ("close",),
}

# Pattern Recognition - all use OHLC
for p in CDL_PATTERNS:
    INDICATOR_INPUTS[p] = ("open", "high", "low", "close")


# ═══════════════════════════════════════════════════════════════════════════════
# EXPORT DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class ExportConfig:
    png_width: int = 1920
    png_height: int = 1080
    png_scale: int = 2
    png_dpi: int = 180
    png_format: str = "png"
    png_bg: str = "#FFFFFF"
    html_cdn: bool = True
    html_freeze: bool = True


# ═══════════════════════════════════════════════════════════════════════════════
# CHART DEFAULTS
# ═══════════════════════════════════════════════════════════════════════════════
@dataclass
class ChartDefaults:
    chart_type: str = "candlestick"
    sma_active: List[int] = field(default_factory=lambda: [5, 20, 60])
    ema_active: List[int] = field(default_factory=lambda: [])
    bb_period: int = 20
    bb_std: float = 2.0
    vwap_enabled: bool = False
    volume_enabled: bool = True
    volume_height_pct: float = 0.25
    macd_enabled: bool = True
    macd_height_pct: float = 0.20
    rsi_enabled: bool = True
    rsi_period: int = 14
    rsi_height_pct: float = 0.15
    kd_enabled: bool = False
    kd_height_pct: float = 0.15
    crisis_threshold: float = 0.10
    crisis_enabled: bool = True
    highlow_enabled: bool = True
    line_width: float = 1.5
    font_family: str = "Inter, Noto Sans TC, Arial, sans-serif"
    data_font: str = "JetBrains Mono, Consolas, monospace"


# ═══════════════════════════════════════════════════════════════════════════════
# ADJ CLOSE PRIORITY LOGIC
# ═══════════════════════════════════════════════════════════════════════════════
def get_price_column(df, prefer_adj: bool = True) -> str:
    """
    Adj Close 優先邏輯:
    - 若 DataFrame 中有 adj_close / Adj Close / adjclose 欄位，優先使用
    - 否則 fallback 到 close / Close
    """
    adj_candidates = ["adj_close", "Adj Close", "Adj_Close", "adjclose", "AdjClose", "adjusted_close"]
    close_candidates = ["close", "Close", "CLOSE"]

    if prefer_adj:
        for col in adj_candidates:
            if col in df.columns:
                return col

    for col in close_candidates:
        if col in df.columns:
            return col

    raise KeyError(f"No close/adj_close column found in DataFrame. Columns: {list(df.columns)}")


def resolve_ohlcv_columns(df) -> dict:
    """
    Auto-detect and map OHLCV columns from DataFrame.
    Returns dict with standardized keys: open, high, low, close, volume, adj_close
    Close uses adj_close priority.
    """
    mapping = {}
    col_map = {
        "open":   ["open", "Open", "OPEN", "adj_open", "Adj Open"],
        "high":   ["high", "High", "HIGH", "adj_high", "Adj High"],
        "low":    ["low", "Low", "LOW", "adj_low", "Adj Low"],
        "close":  [],  # handled specially
        "volume": ["volume", "Volume", "VOLUME", "vol", "Vol"],
    }

    # Close: adj_close first
    close_col = get_price_column(df, prefer_adj=True)
    mapping["close"] = close_col

    # Also store raw close if adj exists
    raw_close_candidates = ["close", "Close", "CLOSE"]
    mapping["raw_close"] = None
    for c in raw_close_candidates:
        if c in df.columns:
            mapping["raw_close"] = c
            break

    for key, candidates in col_map.items():
        if key == "close":
            continue
        for c in candidates:
            if c in df.columns:
                mapping[key] = c
                break
        if key not in mapping:
            mapping[key] = None

    return mapping


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL SINGLETON
# ═══════════════════════════════════════════════════════════════════════════════
EXPORT_DEFAULTS = ExportConfig()
CHART_DEFAULTS = ChartDefaults()


if __name__ == "__main__":
    print(f"VeritasAutoPlot Config v4.0")
    print(f"Root: {VAPPaths.ROOT}")
    print(f"Standard Periods: {STANDARD_PERIODS}")
    print(f"Total Indicators: {len(INDICATOR_DEFAULTS)}")
    print(f"CDL Patterns: {len(CDL_PATTERNS)}")
    print(f"Total Category Map: {len(INDICATOR_CATEGORY_MAP)}")
    print(f"Locked Regex: TW_TICKER={TW_TICKER_REGEX}")
