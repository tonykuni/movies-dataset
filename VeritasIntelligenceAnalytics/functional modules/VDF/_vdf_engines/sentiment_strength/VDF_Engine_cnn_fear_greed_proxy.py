# -*- coding: utf-8 -*-
"""
def VDF_Engine_cnn_fear_greed_proxy
CNN Fear & Greed style proxy engine using free market data.
"""

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

import pandas as pd
import numpy as np

from VDF_Engine_sentiment_strength import def_rolling_percentile_score, def_classify_strength


def def_fetch_yfinance_close(symbol: str, period: str = "5y", interval: str = "1d") -> pd.Series:
    import yfinance as yf

    df = yf.download(
        symbol,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
        threads=False,
    )

    if df is None or df.empty:
        raise ValueError(f"yfinance returned empty data: {symbol}")

    if isinstance(df.columns, pd.MultiIndex):
        if ("Close", symbol) in df.columns:
            s = df[("Close", symbol)]
        else:
            close_cols = [c for c in df.columns if str(c[0]).lower() == "close"]
            if not close_cols:
                raise ValueError(f"No close column for {symbol}. columns={df.columns}")
            s = df[close_cols[0]]
    else:
        if "Close" in df.columns:
            s = df["Close"]
        elif "Adj Close" in df.columns:
            s = df["Adj Close"]
        else:
            raise ValueError(f"No Close column for {symbol}. columns={df.columns}")

    s.name = symbol
    s.index = pd.to_datetime(s.index)
    return pd.to_numeric(s, errors="coerce")


def def_fetch_price_matrix(symbols: dict, period: str, interval: str) -> pd.DataFrame:
    series = {}
    errors = {}

    for key, symbol in symbols.items():
        try:
            series[key] = def_fetch_yfinance_close(symbol=symbol, period=period, interval=interval)
        except Exception as exc:
            errors[key] = str(exc)

    if not series:
        raise ValueError(f"All yfinance symbols failed. errors={errors}")

    df = pd.concat(series.values(), axis=1)
    df.columns = list(series.keys())
    df = df.sort_index()
    df.attrs["def_fetch_errors"] = errors
    return df


def def_pct_change(series: pd.Series, periods: int) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").pct_change(periods=periods) * 100.0


def def_build_cnn_fear_greed_proxy(task: dict) -> pd.DataFrame:
    symbols = task.get("symbols") or {
        "SPY": "SPY",
        "QQQ": "QQQ",
        "RSP": "RSP",
        "IWM": "IWM",
        "VIX": "^VIX",
        "IEF": "IEF",
        "TLT": "TLT",
        "HYG": "HYG",
    }

    period = task.get("period", "5y")
    interval = task.get("interval", "1d")
    percentile_window = int(task.get("percentile_window", 252))
    min_periods = int(task.get("min_periods", 60))

    prices = def_fetch_price_matrix(symbols=symbols, period=period, interval=interval)

    required_core = ["SPY", "VIX", "IEF", "HYG"]
    missing_core = [x for x in required_core if x not in prices.columns]
    if missing_core:
        raise ValueError(f"CNN proxy missing required core symbols: {missing_core}")

    out = pd.DataFrame(index=prices.index)

    spy = prices["SPY"]
    vix = prices["VIX"]
    ief = prices["IEF"]
    hyg = prices["HYG"]

    qqq = prices["QQQ"] if "QQQ" in prices.columns else spy
    rsp = prices["RSP"] if "RSP" in prices.columns else prices["IWM"] if "IWM" in prices.columns else spy
    tlt = prices["TLT"] if "TLT" in prices.columns else ief

    out["def_market_momentum_raw"] = (spy / spy.rolling(125, min_periods=80).mean() - 1.0) * 100.0
    out["def_stock_price_strength_raw"] = def_pct_change(qqq, 63) - def_pct_change(spy, 63)
    out["def_stock_price_breadth_proxy_raw"] = def_pct_change(rsp, 63) - def_pct_change(spy, 63)
    out["def_put_call_proxy_raw"] = vix
    out["def_market_volatility_raw"] = vix / vix.rolling(50, min_periods=30).mean()
    out["def_safe_haven_demand_raw"] = def_pct_change(spy, 20) - def_pct_change(ief, 20)
    out["def_junk_bond_demand_raw"] = def_pct_change(hyg, 63) - def_pct_change(ief, 63)

    out["def_market_momentum_score"] = def_rolling_percentile_score(
        out["def_market_momentum_raw"],
        window=percentile_window,
        min_periods=min_periods,
        inverse=False,
    )

    out["def_stock_price_strength_score"] = def_rolling_percentile_score(
        out["def_stock_price_strength_raw"],
        window=percentile_window,
        min_periods=min_periods,
        inverse=False,
    )

    out["def_stock_price_breadth_proxy_score"] = def_rolling_percentile_score(
        out["def_stock_price_breadth_proxy_raw"],
        window=percentile_window,
        min_periods=min_periods,
        inverse=False,
    )

    out["def_put_call_proxy_score"] = def_rolling_percentile_score(
        out["def_put_call_proxy_raw"],
        window=percentile_window,
        min_periods=min_periods,
        inverse=True,
    )

    out["def_market_volatility_score"] = def_rolling_percentile_score(
        out["def_market_volatility_raw"],
        window=percentile_window,
        min_periods=min_periods,
        inverse=True,
    )

    out["def_safe_haven_demand_score"] = def_rolling_percentile_score(
        out["def_safe_haven_demand_raw"],
        window=percentile_window,
        min_periods=min_periods,
        inverse=False,
    )

    out["def_junk_bond_demand_score"] = def_rolling_percentile_score(
        out["def_junk_bond_demand_raw"],
        window=percentile_window,
        min_periods=min_periods,
        inverse=False,
    )

    score_cols = [
        "def_market_momentum_score",
        "def_stock_price_strength_score",
        "def_stock_price_breadth_proxy_score",
        "def_put_call_proxy_score",
        "def_market_volatility_score",
        "def_safe_haven_demand_score",
        "def_junk_bond_demand_score",
    ]

    out["def_cnn_proxy_score"] = out[score_cols].mean(axis=1, skipna=True).clip(0, 100)
    out["def_cnn_proxy_class"] = out["def_cnn_proxy_score"].apply(def_classify_strength)

    out = out.reset_index().rename(columns={"index": "def_date", "Date": "def_date"})
    if "def_date" not in out.columns:
        out = out.rename(columns={out.columns[0]: "def_date"})

    out["def_provider"] = "yfinance_cnn_fear_greed_proxy"
    out["def_indicator_id"] = "CNN_FEAR_GREED_PROXY"
    out["def_indicator_name_zh"] = "CNN Fear & Greed 類代理指標"
    out["def_category_lv1"] = "Sentiment"
    out["def_category_lv2"] = "CNN Fear & Greed Proxy"
    out["def_frequency"] = "D"
    out["def_unit"] = "score_0_100"

    errors = prices.attrs.get("def_fetch_errors", {})
    out["def_fetch_errors"] = str(errors)

    return out
