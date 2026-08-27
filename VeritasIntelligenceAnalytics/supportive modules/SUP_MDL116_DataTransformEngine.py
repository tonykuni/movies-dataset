# -*- coding: utf-8 -*-
"""
VIA_DataTransformEngine.py
=====================================================================
VIA 數據轉換引擎 (Data Transformation / Indicator Engine)

LOCKED RULES ENCODED
  [ADJ]  yfinance 有 Adj Close -> adj_factor = adj_close/close ;
         adj_open/high/low = raw * factor ; 技術分析一律用 ADJ 價。
         無 Adj Close -> 用原始 OHLC。
  [TALIB] 除「形態學(CDL)」與「統計」外，指標一律走 TA-Lib（主用），
         TA-Lib 不在 -> pandas fallback（本檔自帶核心 fallback）。
  [STAT] BETA / Sharpe / 相關係數 / 標準差 用公式計算；基準可選
         TWII / ^GSPC / NVDA；無風險利率可選 TW10Y / US10Y。
  [TZ]   新聞/事件時間對齊台北時間；影響美股的事件 N 日 -> 台股 N+1 日。
  [DAYS] 視窗統一 5/10/20/60/120/240/YTD/特殊；RSI 類保留原生週期，
         BETA/相關/特殊區間之週期可調。
  [EVT]  自動偵測大波段 + EventMatrix（最高/最低/MaxDD%/峰->谷天數/
         谷->回前高 日期與天數）；內建 1929 以來股災事件矩陣。
  [IO]   來源多型（parquet/duckdb/sqlite/csv/json/gsheet/VDF）含 fallback；
         原始資料 -> DB；衍生資料 -> 暫存 + 升圖（避免數據爆量）。
  [BRIDGE] 七模組支援橋（silent graceful fallback）。
=====================================================================
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

import os
import sys
import json
import sqlite3
import argparse
import datetime as _dt
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# ---- optional seven-module bridge (never hard-fail) -----------------
try:
    import importlib.util  # explicit (silent-crash LL)
    from via_support_bridge import BRIDGE  # type: ignore
    _BRIDGE_OK = True
except Exception:
    BRIDGE = None
    _BRIDGE_OK = False

# ---- TA-Lib primary, pandas fallback --------------------------------
try:
    import talib as _talib  # type: ignore
    _TALIB_OK = True
except Exception:
    _talib = None
    _TALIB_OK = False


# =====================================================================
# CONFIG
# =====================================================================
DEFAULT_DICT = r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics\dict"
STD_WINDOWS = [5, 10, 20, 60, 120, 240]  # + YTD + special

# term parameter sets (from TA-Lib classification doc; adjustable)
TERMS: Dict[str, Dict[str, Any]] = {
    "short": {"rsi": 9,  "macd": (5, 10, 5),  "stoch": (9, 3, 3),
              "sma": [5, 10, 20], "ema": [12, 26], "adx": 14, "atr": 14,
              "bbands": (20, 2.0), "cci": 14, "willr": 14, "mom": 10, "roc": 10},
    "mid":   {"rsi": 14, "macd": (12, 26, 9), "stoch": (14, 3, 3),
              "sma": [20, 60], "ema": [12, 26], "adx": 14, "atr": 14,
              "bbands": (20, 2.0), "cci": 20, "willr": 14, "mom": 12, "roc": 12},
    "long":  {"rsi": 21, "macd": (12, 26, 9), "stoch": (21, 5, 5),
              "sma": [60, 120, 240], "ema": [26, 52], "adx": 14, "atr": 20,
              "bbands": (20, 2.0), "cci": 20, "willr": 28, "mom": 20, "roc": 20},
}
TERMS["special"] = dict(TERMS["mid"])  # special overrides via params/CLI


def load_config(params_file: Optional[str]) -> Dict[str, Any]:
    """Pull engine knobs from params.json if present (panel-controlled)."""
    cfg = {
        "dict_root": DEFAULT_DICT,
        "source_order": ["parquet", "duckdb", "sqlite", "csv", "json", "gsheet", "vdf"],
        "benchmark": "^GSPC",         # TWII / ^GSPC / NVDA
        "risk_free": "US10Y",         # TW10Y / US10Y
        "rf_annual": 0.045,           # fallback constant if no series
        "windows": STD_WINDOWS,
        "ytd_start": f"{_dt.date.today().year}-01-01",
        "term": "mid",
    }
    if params_file and os.path.exists(params_file):
        try:
            with open(params_file, "r", encoding="utf-8-sig") as f:
                p = json.load(f)
            cfg["dict_root"] = p.get("paths", {}).get("dict_root", cfg["dict_root"])
            eng = p.get("engine", {})
            for k in ("source_order", "benchmark", "risk_free", "rf_annual", "windows", "ytd_start", "term"):
                if k in eng:
                    cfg[k] = eng[k]
        except Exception:
            pass
    return cfg


# =====================================================================
# DATA SOURCE  (multi-type, fallback chain)
# =====================================================================
class DataSource:
    """Load OHLCV by trying configured sources in order; each guarded."""

    def __init__(self, cfg: Dict[str, Any], base_dir: Optional[str] = None):
        self.cfg = cfg
        self.base = base_dir or cfg["dict_root"]

    def _f(self, ticker: str, ext: str) -> str:
        return os.path.join(self.base, f"{ticker}.{ext}")

    def _parquet(self, t): return pd.read_parquet(self._f(t, "parquet"))
    def _csv(self, t):     return pd.read_csv(self._f(t, "csv"))
    def _json(self, t):    return pd.read_json(self._f(t, "json"))

    def _duckdb(self, t):
        import duckdb  # local import; optional
        con = duckdb.connect(os.path.join(self.base, "via.duckdb"), read_only=True)
        try:
            return con.execute(f'SELECT * FROM "{t}"').df()
        finally:
            con.close()

    def _sqlite(self, t):
        con = sqlite3.connect(os.path.join(self.base, "via.sqlite"))
        try:
            return pd.read_sql_query(f'SELECT * FROM "{t}"', con)
        finally:
            con.close()

    def _gsheet(self, t):
        raise NotImplementedError("gsheet connector hook — wire gspread here")

    def _vdf(self, t):
        raise NotImplementedError("VDF direct-fetch hook — call VDF fetcher here")

    def load(self, ticker: str) -> Tuple[Optional[pd.DataFrame], str]:
        chain = {
            "parquet": self._parquet, "duckdb": self._duckdb, "sqlite": self._sqlite,
            "csv": self._csv, "json": self._json, "gsheet": self._gsheet, "vdf": self._vdf,
        }
        errs = []
        for name in self.cfg["source_order"]:
            fn = chain.get(name)
            if fn is None:
                continue
            try:
                df = fn(ticker)
                if df is not None and len(df):
                    return _canon_columns(df), name
            except Exception as e:
                errs.append(f"{name}:{type(e).__name__}")
        return None, "FAILED(" + ",".join(errs) + ")"


def _canon_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise column names to date/open/high/low/close/volume/adj_close."""
    df = df.copy()
    df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]
    ren = {"adjclose": "adj_close", "adj_close.": "adj_close", "vol": "volume",
           "datetime": "date", "timestamp": "date", "index": "date"}
    df = df.rename(columns=ren)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
    return df


# =====================================================================
# ADJ RULE
# =====================================================================
def apply_adjust(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """If adj_close present & valid -> derive adj OHLC; else use raw. [ADJ]"""
    d = df.copy()
    has_adj = "adj_close" in d.columns and d["adj_close"].notna().any()
    if has_adj:
        factor = (d["adj_close"] / d["close"]).replace([np.inf, -np.inf], np.nan).fillna(1.0)
        d["o"] = d["open"] * factor
        d["h"] = d["high"] * factor
        d["l"] = d["low"] * factor
        d["c"] = d["adj_close"]
    else:
        d["o"], d["h"], d["l"], d["c"] = d["open"], d["high"], d["low"], d["close"]
    d["v"] = d.get("volume", pd.Series(np.nan, index=d.index))
    return d, bool(has_adj)


# =====================================================================
# INDICATOR BACKEND  (TA-Lib primary -> pandas fallback)
# =====================================================================
def _ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def _rsi_fb(c: pd.Series, n: int) -> pd.Series:
    d = c.diff()
    up = d.clip(lower=0).ewm(alpha=1/n, adjust=False).mean()
    dn = (-d.clip(upper=0)).ewm(alpha=1/n, adjust=False).mean()
    rs = up / dn.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def _atr_fb(h, l, c, n: int) -> pd.Series:
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1/n, adjust=False).mean()


def _adx_fb(h, l, c, n: int) -> Tuple[pd.Series, pd.Series, pd.Series]:
    up = h.diff()
    dn = -l.diff()
    plus_dm = ((up > dn) & (up > 0)) * up
    minus_dm = ((dn > up) & (dn > 0)) * dn
    pc = c.shift(1)
    tr = pd.concat([(h - l), (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    atr = tr.ewm(alpha=1/n, adjust=False).mean().replace(0, np.nan)
    plus_di = 100 * plus_dm.ewm(alpha=1/n, adjust=False).mean() / atr
    minus_di = 100 * minus_dm.ewm(alpha=1/n, adjust=False).mean() / atr
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
    adx = dx.ewm(alpha=1/n, adjust=False).mean()
    return adx, plus_di, minus_di


def compute_indicators(d: pd.DataFrame, term: Dict[str, Any]) -> pd.DataFrame:
    """Return derived indicator frame on ADJ prices. TA-Lib if available."""
    o, h, l, c, v = d["o"], d["h"], d["l"], d["c"], d["v"]
    out = pd.DataFrame(index=d.index)
    if "date" in d.columns:
        out["date"] = d["date"]

    if _TALIB_OK:
        ta = _talib
        for n in term["sma"]:
            out[f"sma_{n}"] = ta.SMA(c, n)
        for n in term["ema"]:
            out[f"ema_{n}"] = ta.EMA(c, n)
        out["rsi"] = ta.RSI(c, term["rsi"])
        f, s, sig = term["macd"]
        out["macd"], out["macd_sig"], out["macd_hist"] = ta.MACD(c, f, s, sig)
        kp, kd, dd = term["stoch"]
        out["stoch_k"], out["stoch_d"] = ta.STOCH(h, l, c, kp, kd, 0, dd, 0)
        out["willr"] = ta.WILLR(h, l, c, term["willr"])
        out["cci"] = ta.CCI(h, l, c, term["cci"])
        out["mom"] = ta.MOM(c, term["mom"])
        out["roc"] = ta.ROC(c, term["roc"])
        out["atr"] = ta.ATR(h, l, c, term["atr"])
        out["natr"] = ta.NATR(h, l, c, term["atr"])
        bb_n, bb_k = term["bbands"]
        out["bb_up"], out["bb_mid"], out["bb_low"] = ta.BBANDS(c, bb_n, bb_k, bb_k)
        out["adx"] = ta.ADX(h, l, c, term["adx"])
        out["plus_di"] = ta.PLUS_DI(h, l, c, term["adx"])
        out["minus_di"] = ta.MINUS_DI(h, l, c, term["adx"])
        out["obv"] = ta.OBV(c, v.fillna(0))
        engine = "talib"
    else:
        for n in term["sma"]:
            out[f"sma_{n}"] = c.rolling(n).mean()
        for n in term["ema"]:
            out[f"ema_{n}"] = _ema(c, n)
        out["rsi"] = _rsi_fb(c, term["rsi"])
        f, s, sig = term["macd"]
        macd = _ema(c, f) - _ema(c, s)
        out["macd"] = macd
        out["macd_sig"] = _ema(macd, sig)
        out["macd_hist"] = macd - out["macd_sig"]
        kp, kd, dd = term["stoch"]
        ll = l.rolling(kp).min(); hh = h.rolling(kp).max()
        k = 100 * (c - ll) / (hh - ll).replace(0, np.nan)
        out["stoch_k"] = k.rolling(kd).mean()
        out["stoch_d"] = out["stoch_k"].rolling(dd).mean()
        hh_w = h.rolling(term["willr"]).max(); ll_w = l.rolling(term["willr"]).min()
        out["willr"] = -100 * (hh_w - c) / (hh_w - ll_w).replace(0, np.nan)
        tp = (h + l + c) / 3
        out["cci"] = (tp - tp.rolling(term["cci"]).mean()) / \
                     (0.015 * tp.rolling(term["cci"]).apply(lambda x: np.abs(x - x.mean()).mean(), raw=True))
        out["mom"] = c.diff(term["mom"])
        out["roc"] = c.pct_change(term["roc"]) * 100
        out["atr"] = _atr_fb(h, l, c, term["atr"])
        out["natr"] = 100 * out["atr"] / c
        bb_n, bb_k = term["bbands"]
        mid = c.rolling(bb_n).mean(); sd = c.rolling(bb_n).std(ddof=0)
        out["bb_mid"], out["bb_up"], out["bb_low"] = mid, mid + bb_k * sd, mid - bb_k * sd
        adx, pdi, mdi = _adx_fb(h, l, c, term["adx"])
        out["adx"], out["plus_di"], out["minus_di"] = adx, pdi, mdi
        out["obv"] = (np.sign(c.diff()).fillna(0) * v.fillna(0)).cumsum()
        engine = "pandas_fallback"

    # price indicators (always formula)
    out["avgprice"] = (o + h + l + c) / 4
    out["medprice"] = (h + l) / 2
    out["typprice"] = (h + l + c) / 3
    out["wclprice"] = (h + l + 2 * c) / 4
    out.attrs["engine"] = engine
    return out


def compute_patterns(d: pd.DataFrame) -> pd.DataFrame:
    """Candlestick patterns — TA-Lib CDL only (形態學另路). Skipped if absent."""
    out = pd.DataFrame(index=d.index)
    if "date" in d.columns:
        out["date"] = d["date"]
    if not _TALIB_OK:
        out.attrs["engine"] = "skipped(no talib)"
        return out
    o, h, l, c = d["o"], d["h"], d["l"], d["c"]
    for name in ["CDLHAMMER", "CDLINVERTEDHAMMER", "CDLPIERCING", "CDLMORNINGSTAR",
                 "CDLHANGINGMAN", "CDLSHOOTINGSTAR", "CDLDARKCLOUDCOVER",
                 "CDLEVENINGSTAR", "CDLDOJI", "CDLSPINNINGTOP"]:
        try:
            out[name.lower()] = getattr(_talib, name)(o, h, l, c)
        except Exception:
            pass
    out.attrs["engine"] = "talib"
    return out


# =====================================================================
# STATISTICS  (formula; benchmark + risk-free selectable) [STAT]
# =====================================================================
def _to_ret(c: pd.Series) -> pd.Series:
    return c.pct_change()


def stats_block(c_asset: pd.Series, c_bench: Optional[pd.Series],
                windows: List[int], ytd_start: Optional[str],
                rf_annual: float) -> pd.DataFrame:
    """rolling stddev / beta / sharpe / correl over standard windows + YTD."""
    ra = _to_ret(c_asset)
    rb = _to_ret(c_bench) if c_bench is not None else None
    rf_daily = (1 + rf_annual) ** (1/252) - 1
    rows = []
    wins = [(str(w), w) for w in windows]
    if ytd_start:
        wins.append(("YTD", None))
    for label, w in wins:
        if w is None:  # YTD slice by date index
            mask = ra.index >= pd.to_datetime(ytd_start) if isinstance(ra.index, pd.DatetimeIndex) else None
            ra_w = ra[mask] if mask is not None else ra.tail(120)
            rb_w = rb[mask] if (rb is not None and mask is not None) else (rb.tail(120) if rb is not None else None)
        else:
            ra_w = ra.tail(w)
            rb_w = rb.tail(w) if rb is not None else None
        ra_w = ra_w.dropna()
        if len(ra_w) < 3:
            continue
        std = ra_w.std(ddof=1)
        ann = np.sqrt(252)
        sharpe = ((ra_w.mean() - rf_daily) / std * ann) if std else np.nan
        beta = corr = np.nan
        if rb_w is not None:
            j = pd.concat([ra_w, rb_w], axis=1, join="inner").dropna()
            if len(j) >= 3 and j.iloc[:, 1].var(ddof=1):
                cov = np.cov(j.iloc[:, 0], j.iloc[:, 1], ddof=1)[0, 1]
                beta = cov / j.iloc[:, 1].var(ddof=1)
                corr = j.iloc[:, 0].corr(j.iloc[:, 1])
        rows.append({"window": label, "n": len(ra_w),
                     "stddev_d": round(float(std), 6),
                     "vol_ann": round(float(std * ann), 6),
                     "sharpe_ann": round(float(sharpe), 4),
                     "beta": (round(float(beta), 4) if pd.notna(beta) else None),
                     "correl": (round(float(corr), 4) if pd.notna(corr) else None)})
    return pd.DataFrame(rows)


# =====================================================================
# NEWS-TIME ALIGNMENT  [TZ]  US event day N -> TW day N+1
# =====================================================================
def align_event_to_tw(event_utc: _dt.datetime, source_market: str = "US") -> _dt.date:
    """Convert event to Taipei date; US-impacting -> next TW trading day (N+1)."""
    tpe = event_utc + _dt.timedelta(hours=8)  # UTC+8, no DST in Taipei
    d = tpe.date()
    if source_market.upper() == "US":
        d = d + _dt.timedelta(days=1)  # N+1 to TW
    while d.weekday() >= 5:             # skip weekend (holidays handled upstream)
        d = d + _dt.timedelta(days=1)
    return d


# =====================================================================
# EVENT MATRIX  [EVT]  swing detection + crash registry
# =====================================================================
# 1929 以來 S&P500/道瓊重大股災（近似值，供結構比較；對話可查）
CRASH_EVENTS: List[Dict[str, Any]] = [
    {"event": "1929 大蕭條", "peak": "1929-09", "trough": "1932-07", "dd_pct": -86, "recover_yrs": 25, "index": "DJIA"},
    {"event": "1937 衰退",   "peak": "1937-03", "trough": "1938-03", "dd_pct": -49, "recover_yrs": 9,  "index": "DJIA"},
    {"event": "1973-74 滯脹","peak": "1973-01", "trough": "1974-10", "dd_pct": -48, "recover_yrs": 7,  "index": "SP500"},
    {"event": "1987 黑色星期一","peak": "1987-08","trough": "1987-12","dd_pct": -34, "recover_yrs": 2,  "index": "SP500"},
    {"event": "2000 網路泡沫","peak": "2000-03", "trough": "2002-10", "dd_pct": -49, "recover_yrs": 7,  "index": "SP500"},
    {"event": "2008 金融海嘯","peak": "2007-10", "trough": "2009-03", "dd_pct": -57, "recover_yrs": 5,  "index": "SP500"},
    {"event": "2011 歐債/降評","peak": "2011-04","trough": "2011-10","dd_pct": -19, "recover_yrs": 1,  "index": "SP500"},
    {"event": "2018 Q4",     "peak": "2018-09", "trough": "2018-12", "dd_pct": -20, "recover_yrs": 1,  "index": "SP500"},
    {"event": "2020 疫情",   "peak": "2020-02", "trough": "2020-03", "dd_pct": -34, "recover_mo": 5,   "index": "SP500"},
    {"event": "2022 升息",   "peak": "2022-01", "trough": "2022-10", "dd_pct": -25, "recover_yrs": 2,  "index": "SP500"},
]


def detect_swings(c: pd.Series, dates: pd.Series, pct: float = 0.12) -> Dict[str, Any]:
    """Zigzag pivots by reversal threshold; report biggest peak->trough swing,
       MaxDD%, days to trough, recovery date & days. [EVT]"""
    vals = c.values.astype(float)
    n = len(vals)
    pivots = [0]
    direction = 0
    last_ext = vals[0]
    for i in range(1, n):
        chg = (vals[i] - last_ext) / last_ext
        if direction >= 0 and chg <= -pct:
            pivots.append(i); direction = -1; last_ext = vals[i]
        elif direction <= 0 and chg >= pct:
            pivots.append(i); direction = 1; last_ext = vals[i]
        else:
            if (direction >= 0 and vals[i] > last_ext) or (direction <= 0 and vals[i] < last_ext):
                last_ext = vals[i]; pivots[-1] = i
    if pivots[-1] != n - 1:
        pivots.append(n - 1)

    # largest drawdown episode via running-max (classic MaxDD) — captures the
    # real crash even when later recovery exceeds the prior peak. [EVT]
    run_max = np.maximum.accumulate(vals)
    dd = vals / run_max - 1.0
    trough_i = int(np.argmin(dd))                 # point of deepest drawdown
    peak_i = int(np.argmax(vals[:trough_i + 1]))  # the prior high it fell from
    peak_v, trough_v = float(vals[peak_i]), float(vals[trough_i])
    maxdd = (trough_v - peak_v) / peak_v * 100.0 if peak_v else 0.0

    # recovery: first index after trough that reaches/exceeds the prior peak
    rec_i = None
    for j in range(trough_i + 1, n):
        if vals[j] >= peak_v:
            rec_i = j; break

    def _d(i): return pd.to_datetime(dates.iloc[i]).date().isoformat() if i is not None else None
    days = lambda a, b: (pd.to_datetime(dates.iloc[b]) - pd.to_datetime(dates.iloc[a])).days if b is not None else None

    return {
        "n_pivots": len(pivots),
        "peak_date": _d(peak_i), "peak": round(peak_v, 4),
        "trough_date": _d(trough_i), "trough": round(trough_v, 4),
        "maxdd_pct": round(maxdd, 2),
        "peak_to_trough_days": days(peak_i, trough_i),
        "recover_date": _d(rec_i),
        "trough_to_recover_days": days(trough_i, rec_i),
        "recovered": rec_i is not None,
        "_pivots": pivots, "_peak_i": peak_i, "_trough_i": trough_i, "_rec_i": rec_i,
    }


def render_event_png(d: pd.DataFrame, swing: Dict[str, Any], title: str, out_png: str) -> str:
    """Derived -> image (avoid data bloat). TW colours: 跌=綠 漲=紅。"""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    dates = pd.to_datetime(d["date"]) if "date" in d.columns else pd.RangeIndex(len(d))
    c = d["c"].values
    pk, tr, rc = swing["_peak_i"], swing["_trough_i"], swing.get("_rec_i")
    fig, ax = plt.subplots(figsize=(11, 4.6), dpi=120)
    ax.plot(dates, c, color="#3a3a34", lw=1.1)
    # drawdown segment green (down), recovery segment red (up) — TW inversion
    ax.plot(dates[pk:tr+1], c[pk:tr+1], color="#2e7d52", lw=1.8, label="drawdown")
    if rc is not None:
        ax.plot(dates[tr:rc+1], c[tr:rc+1], color="#c0392b", lw=1.8, label="recovery")
    ax.scatter([dates[pk]], [c[pk]], color="#c0392b", zorder=5, s=36)
    ax.scatter([dates[tr]], [c[tr]], color="#2e7d52", zorder=5, s=36)
    ax.annotate(f"PEAK\n{swing['peak_date']}", (dates[pk], c[pk]),
                textcoords="offset points", xytext=(0, 10), ha="center", fontsize=8, color="#c0392b")
    ax.annotate(f"TROUGH  MaxDD {swing['maxdd_pct']}%\n{swing['trough_date']}", (dates[tr], c[tr]),
                textcoords="offset points", xytext=(0, -24), ha="center", fontsize=8, color="#2e7d52")
    if rc is not None:
        ax.scatter([dates[rc]], [c[rc]], color="#c9a227", zorder=5, s=36)
        ax.annotate(f"RECOVER\n{swing['recover_date']}", (dates[rc], c[rc]),
                    textcoords="offset points", xytext=(0, 10), ha="center", fontsize=8, color="#b7791f")
    ax.set_title(title, fontsize=11)
    ax.grid(alpha=0.18); ax.legend(fontsize=8, loc="upper left")
    fig.tight_layout()
    os.makedirs(os.path.dirname(out_png), exist_ok=True)
    fig.savefig(out_png); plt.close(fig)
    return out_png


# =====================================================================
# SINK  [IO]  raw -> DB ; derived -> temp + image
# =====================================================================
class Sink:
    def __init__(self, dict_root: str, temp_root: Optional[str] = None):
        self.dict_root = dict_root
        self.temp_root = temp_root or os.path.join(dict_root, "_temp")
        os.makedirs(self.dict_root, exist_ok=True)
        os.makedirs(self.temp_root, exist_ok=True)

    def save_raw(self, ticker: str, d: pd.DataFrame) -> str:
        """Full original (+adj) -> parquet in dict (the complete raw DB)."""
        p = os.path.join(self.dict_root, f"{ticker}__raw.parquet")
        d.to_parquet(p, index=False)
        return p

    def save_derived_snapshot(self, ticker: str, term: str,
                              ind: pd.DataFrame, stats: pd.DataFrame) -> str:
        """Derived = TEMP. Persist only the latest snapshot + stats (small),
           NOT the full indicator history (avoid data explosion)."""
        snap = {
            "ticker": ticker, "term": term, "utc": _utc(),
            "engine": ind.attrs.get("engine"),
            "last": _last_row_json(ind),
            "stats": stats.to_dict(orient="records"),
        }
        p = os.path.join(self.temp_root, f"{ticker}__{term}__derived.json")
        with open(p, "w", encoding="utf-8") as f:
            json.dump(snap, f, ensure_ascii=False, indent=2)
        return p


def _last_row_json(df: pd.DataFrame) -> Dict[str, Any]:
    if not len(df):
        return {}
    row = df.iloc[-1].to_dict()
    return {k: (None if (isinstance(v, float) and np.isnan(v))
                else (v.isoformat() if hasattr(v, "isoformat") else
                      (float(v) if isinstance(v, (np.floating,)) else
                       (int(v) if isinstance(v, (np.integer,)) else v))))
            for k, v in row.items()}


def _utc() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# =====================================================================
# PIPELINE
# =====================================================================
def transform(ticker: str, term: str, cfg: Dict[str, Any],
              df: Optional[pd.DataFrame] = None,
              source_dir: Optional[str] = None,
              bench_df: Optional[pd.DataFrame] = None,
              out_dir: Optional[str] = None) -> Dict[str, Any]:
    dict_root = out_dir or cfg["dict_root"]
    # 1) load
    src_name = "in-memory"
    if df is None:
        ds = DataSource(cfg, base_dir=source_dir)
        df, src_name = ds.load(ticker)
        if df is None:
            return {"ok": False, "error": f"load failed: {src_name}"}
    df = _canon_columns(df)
    # 2) ADJ
    d, adjusted = apply_adjust(df)
    # 3) indicators (ADJ) + patterns
    tparams = TERMS.get(term, TERMS["mid"])
    ind = compute_indicators(d, tparams)
    pat = compute_patterns(d)
    # 4) statistics (benchmark + rf)
    cb = None
    if bench_df is not None:
        bdf, _ = apply_adjust(_canon_columns(bench_df))
        cb = bdf["c"].reset_index(drop=True)
    sc = d["c"].copy()
    if "date" in d.columns:
        sc.index = pd.to_datetime(d["date"])
        if cb is not None and "date" in bench_df.columns:
            cb.index = pd.to_datetime(_canon_columns(bench_df)["date"])
    stats = stats_block(sc, cb, cfg["windows"], cfg.get("ytd_start"), cfg.get("rf_annual", 0.045))
    # 5) event matrix
    swing = detect_swings(d["c"], d["date"]) if "date" in d.columns else None
    # 6) sink: raw->DB, derived->temp, image
    sink = Sink(dict_root)
    raw_p = sink.save_raw(ticker, d)
    snap_p = sink.save_derived_snapshot(ticker, term, ind, stats)
    png_p = None
    if swing is not None:
        png_p = render_event_png(d, swing,
                                 f"{ticker}  ·  {term}  ·  EventMatrix (MaxDD {swing['maxdd_pct']}%)",
                                 os.path.join(sink.temp_root, f"{ticker}__{term}__event.png"))
    return {
        "ok": True, "ticker": ticker, "term": term, "source": src_name,
        "adjusted": adjusted, "rows": int(len(d)),
        "indicator_engine": ind.attrs.get("engine"),
        "pattern_engine": pat.attrs.get("engine"),
        "talib": _TALIB_OK, "bridge": _BRIDGE_OK,
        "swing": {k: v for k, v in (swing or {}).items() if not k.startswith("_")},
        "stats": stats.to_dict(orient="records"),
        "out_raw": raw_p, "out_derived": snap_p, "out_png": png_p,
    }


def main(argv: List[str]) -> int:
    p = argparse.ArgumentParser(prog="VIA_DataTransformEngine")
    p.add_argument("ticker")
    p.add_argument("--term", default="mid", choices=list(TERMS.keys()))
    p.add_argument("--params", default=None, help="params.json (panel-controlled config)")
    p.add_argument("--source-dir", default=None)
    p.add_argument("--out-dir", default=None)
    p.add_argument("--json", dest="as_json", action="store_true")
    a = p.parse_args(argv)
    cfg = load_config(a.params)
    res = transform(a.ticker, a.term, cfg, source_dir=a.source_dir, out_dir=a.out_dir)
    if a.as_json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        for k, v in res.items():
            if k == "stats":
                print("stats:")
                for r in v:
                    print("  ", r)
            else:
                print(f"{k}: {v}")
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
