# -*- coding: utf-8 -*-
"""
VIA_TALibEngine.py v0100 — TA-Lib 技術指標引擎(原生 numpy 實作 + talib 在位直用)
=================================================================================
操作員令(2026-08-11):new engine · 有 adj close / close 將所有價格轉換為 adj,
若無才使用一般價格。

治理:
  ①Adj 鐵律讀 VAP SSOT(vap_spec.json price 節):useAdjClose/adjustAllPrices/
    splitAdjustVolume/fallbackWhenNoAdj/labelSuffix — 引擎不寫死規則;
    VAP SSOT 缺席時用同義預設並誠實註記 provenance.spec_source="builtin_default"。
    有 adj_close → 全部 OHLC × (adj/close),volume ÷ factor(split 慣例);
    無 adj → 一般價 + price_basis="raw" 誠實標示。
  ②指標分類 SSOT = ssot/talib_indicators_classification.md(12 類 + 轉折點基準);
    引擎 REGISTRY 逐項對照該表,threshold 訊號依表列基準。
  ③後端誠實:talib(C 庫)在位 → --backend talib 直用;缺席 → 原生 numpy 實作
    (Hilbert HT_* 家族原生不實作 = 誠實 talib_only,selftest 記 SKIP)。
  ④產物可再生:輸出落 --out 指定處;不觸碰輸入正本。

動詞:
  probe    後端/SSOT/VAP price 規則在位探測
  list     指標清單(分類/範圍/轉折點基準;--category 過濾)
  sample   產生示範 OHLCV CSV(含 adj_close 欄,嵌入 1:2 分割事件供 adj 驗證)
  compute  --file 資料檔 → 指標值(--indicators a,b|all;--out csv/--json)
  signals  依 SSOT 轉折點基準出旗標表(超買/超賣/交叉/型態)
  chart    指標 × VAP 圖庫(K線+RSI+MACD 三面板;需 VAP 引擎與繪圖庫)
  selftest 全功能自我驗證(數學正確性 + adj 鐵律 + 型態 + talib 交叉核對)

USAGE:
  python VIA_TALibEngine.py sample -o ohlcv.csv
  python VIA_TALibEngine.py compute --file ohlcv.csv --indicators rsi,macd,bbands --out ind.csv
  python VIA_TALibEngine.py signals --file ohlcv.csv
  python VIA_TALibEngine.py chart --file ohlcv.csv --out talib_charts
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

__version__ = "0100"

import argparse
import csv as _csv
import importlib.util
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

HERE = Path(__file__).resolve()
SSOT_MD = HERE.parent / "ssot" / "talib_indicators_classification.md"


class TAError(RuntimeError):
    """誠實 FAIL。"""


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False

# ============================================================================
# §1 VAP price SSOT — Adj 鐵律的唯一規則來源(缺席誠實用同義預設)
# ============================================================================

_PRICE_DEFAULT = {
    "useAdjClose": True, "adjustAllPrices": True, "splitAdjustVolume": True,
    "sourcePriority": ["adjClose", "close"], "fallbackWhenNoAdj": "close",
    "labelSuffix": {"adj": " (adj)", "raw": ""},
}


def load_price_rules() -> Tuple[Dict[str, Any], str]:
    for base in [HERE.parent, *HERE.parents]:
        cand = base / "VAP" / "spec" / "ssot" / "vap_spec.json"
        if cand.exists():
            spec = json.loads(cand.read_text(encoding="utf-8"))
            if "price" in spec:
                return dict(spec["price"]), str(cand)
    return dict(_PRICE_DEFAULT), "builtin_default"

# ============================================================================
# §2 資料層 — OHLCV 載入(csv/tsv/json/sqlite/duckdb)+ 欄名別名 + Adj 鐵律
# ============================================================================

_ALIASES = {
    "date": ["date", "trade_date", "time", "datetime", "day", "日期"],
    "open": ["open", "o", "開盤", "開盤價"],
    "high": ["high", "h", "最高", "最高價"],
    "low": ["low", "l", "最低", "最低價"],
    "close": ["close", "c", "收盤", "收盤價", "price"],
    "adj_close": ["adj_close", "adjclose", "adj close", "adjusted_close", "close_adj",
                  "adjusted close", "還原收盤"],
    "volume": ["volume", "vol", "v", "成交量", "turnover_shares"],
}


def load_table(path: Path, table: Optional[str] = None) -> Dict[str, List[Any]]:
    suffix = path.suffix.lower()
    if not path.exists():
        raise TAError("資料檔不存在:%s" % path)
    if suffix in (".csv", ".tsv"):
        with open(path, encoding="utf-8-sig", newline="") as f:
            rows = list(_csv.DictReader(f, delimiter="\t" if suffix == ".tsv" else ","))
    elif suffix == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            n = max((len(v) for v in data.values() if isinstance(v, list)), default=0)
            return {k: list(v)[:n] for k, v in data.items() if isinstance(v, list)}
        rows = list(data)
    elif suffix in (".sqlite", ".sqlite3", ".db", ".duckdb"):
        if suffix == ".duckdb":
            if not _module_available("duckdb"):
                raise TAError("讀 .duckdb 需要 duckdb — pip install duckdb")
            import duckdb as _dd
            con = _dd.connect(str(path), read_only=True)
            tables = [r[0] for r in con.execute("SHOW TABLES").fetchall()]
        else:
            import sqlite3
            con = sqlite3.connect(str(path))
            tables = [r[0] for r in con.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")]
        try:
            if not tables:
                raise TAError("資料庫無資料表:%s" % path)
            if table is None:
                if len(tables) > 1:
                    raise TAError("多表 %s — 請用 --table 指定" % tables)
                table = tables[0]
            if table not in tables:
                raise TAError("--table %r 不存在(可用:%s)" % (table, tables))
            cur = con.execute('SELECT * FROM "%s"' % table.replace('"', '""'))
            names = [d[0] for d in cur.description]
            rows = [dict(zip(names, r)) for r in cur.fetchall()]
        finally:
            con.close()
    else:
        raise TAError("不支援格式 %r(.csv/.tsv/.json/.sqlite/.duckdb)" % suffix)
    if not rows:
        raise TAError("資料檔無資料列:%s" % path)
    cols: Dict[str, List[Any]] = {k: [] for k in rows[0]}
    for r in rows:
        for k in cols:
            cols[k].append(r.get(k))
    return cols


def _find_col(cols: Dict[str, List[Any]], want: str) -> Optional[str]:
    lower = {k.lower().strip(): k for k in cols}
    for alias in _ALIASES[want]:
        if alias in lower:
            return lower[alias]
    return None


def _numf(vals: Sequence[Any]) -> np.ndarray:
    out = np.full(len(vals), np.nan)
    for i, v in enumerate(vals):
        if v is None:
            continue
        s = str(v).replace(",", "").strip()
        if not s:
            continue
        try:
            out[i] = float(s)
        except ValueError:
            raise TAError("欄位含非數值:%r" % v)
    return out


def load_ohlcv(path: Path, table: Optional[str] = None,
               price_rules: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """載入 + Adj 鐵律:回傳 dates/open/high/low/close/volume + provenance。"""
    rules, spec_src = (price_rules, "caller") if price_rules else load_price_rules()
    cols = load_table(path, table)
    name = {k: _find_col(cols, k) for k in _ALIASES}
    if name["close"] is None:
        raise TAError("找不到 close 欄(別名:%s;在檔欄位:%s)"
                      % (_ALIASES["close"], sorted(cols)))
    dates = [str(v) for v in cols[name["date"]]] if name["date"] else \
        [str(i) for i in range(len(cols[name["close"]]))]
    close_raw = _numf(cols[name["close"]])
    o = _numf(cols[name["open"]]) if name["open"] else close_raw.copy()
    h = _numf(cols[name["high"]]) if name["high"] else np.maximum(o, close_raw)
    l = _numf(cols[name["low"]]) if name["low"] else np.minimum(o, close_raw)
    vol = _numf(cols[name["volume"]]) if name["volume"] else None

    prov: Dict[str, Any] = {"spec_source": spec_src, "columns": {k: v for k, v in name.items() if v},
                            "rows": len(close_raw)}
    use_adj = bool(rules.get("useAdjClose", True)) and name["adj_close"] is not None
    if use_adj:
        adj = _numf(cols[name["adj_close"]])
        with np.errstate(divide="ignore", invalid="ignore"):
            factor = np.where(close_raw != 0, adj / close_raw, 1.0)
        factor = np.where(np.isfinite(factor), factor, 1.0)
        if bool(rules.get("adjustAllPrices", True)):
            o, h, l = o * factor, h * factor, l * factor
        c = adj
        if vol is not None and bool(rules.get("splitAdjustVolume", True)):
            with np.errstate(divide="ignore", invalid="ignore"):
                vol = np.where(factor != 0, vol / factor, vol)
        prov.update(price_basis="adj",
                    label_suffix=rules.get("labelSuffix", {}).get("adj", " (adj)"),
                    adj_factor_min=round(float(np.nanmin(factor)), 6),
                    adj_factor_max=round(float(np.nanmax(factor)), 6),
                    volume_split_adjusted=bool(vol is not None and
                                               rules.get("splitAdjustVolume", True)))
    else:
        c = close_raw
        prov.update(price_basis="raw",
                    label_suffix=rules.get("labelSuffix", {}).get("raw", ""),
                    note="adj_close 缺席 → 依 SSOT fallbackWhenNoAdj 用一般價"
                    if name["adj_close"] is None else "useAdjClose=False")
    if np.isnan(c).all():
        raise TAError("close 序列全空")
    return {"dates": dates, "open": o, "high": h, "low": l, "close": c,
            "volume": vol, "provenance": prov}

# ============================================================================
# §3 原生指標庫(numpy;NaN 暖機;Wilder 平滑照原典)
# ============================================================================

def _roll(fn: Callable[[np.ndarray], float], x: np.ndarray, n: int) -> np.ndarray:
    out = np.full(len(x), np.nan)
    for i in range(n - 1, len(x)):
        w = x[i - n + 1:i + 1]
        out[i] = fn(w)
    return out


def sma(x: np.ndarray, n: int = 30) -> np.ndarray:
    return _roll(np.mean, x, n)


def ema(x: np.ndarray, n: int = 30) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    k = 2.0 / (n + 1)
    out[n - 1] = np.mean(x[:n])          # talib 慣例:以 SMA 起種
    for i in range(n, len(x)):
        out[i] = x[i] * k + out[i - 1] * (1 - k)
    return out


def dema(x: np.ndarray, n: int = 30) -> np.ndarray:
    e1 = ema(x, n)
    e2 = ema(np.where(np.isnan(e1), x, e1), n)
    return 2 * e1 - e2


def tema(x: np.ndarray, n: int = 30) -> np.ndarray:
    e1 = ema(x, n)
    e2 = ema(np.where(np.isnan(e1), x, e1), n)
    e3 = ema(np.where(np.isnan(e2), x, e2), n)
    return 3 * e1 - 3 * e2 + e3


def kama(x: np.ndarray, n: int = 30) -> np.ndarray:
    out = np.full(len(x), np.nan)
    if len(x) <= n:
        return out
    fast, slow = 2.0 / 3.0, 2.0 / 31.0
    out[n] = x[n]
    for i in range(n + 1, len(x)):
        change = abs(x[i] - x[i - n])
        vola = np.sum(np.abs(np.diff(x[i - n:i + 1])))
        er = change / vola if vola > 0 else 0.0
        sc = (er * (fast - slow) + slow) ** 2
        out[i] = out[i - 1] + sc * (x[i] - out[i - 1])
    return out


def _wilder(x: np.ndarray, n: int) -> np.ndarray:
    """Wilder 平滑(RSI/ATR/ADX 原典)。"""
    out = np.full(len(x), np.nan)
    if len(x) < n:
        return out
    out[n - 1] = np.nanmean(x[:n])
    for i in range(n, len(x)):
        out[i] = (out[i - 1] * (n - 1) + x[i]) / n
    return out


def rsi(c: np.ndarray, n: int = 14) -> np.ndarray:
    d = np.diff(c, prepend=c[0])
    gain = np.where(d > 0, d, 0.0)
    loss = np.where(d < 0, -d, 0.0)
    ag, al = _wilder(gain[1:], n), _wilder(loss[1:], n)
    out = np.full(len(c), np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        rs = ag / al
        val = np.where(al == 0, 100.0, 100.0 - 100.0 / (1.0 + rs))
    out[1:] = val
    out[:n] = np.nan
    return out


def stoch(h, l, c, k_n: int = 9, d_n: int = 3):
    hh = _roll(np.max, h, k_n)
    ll = _roll(np.min, l, k_n)
    with np.errstate(divide="ignore", invalid="ignore"):
        raw_k = np.where(hh - ll != 0, (c - ll) / (hh - ll) * 100.0, 50.0)
    slow_k = sma(raw_k, d_n)
    slow_d = sma(slow_k, d_n)
    return slow_k, slow_d


def stochf(h, l, c, k_n: int = 9, d_n: int = 3):
    hh = _roll(np.max, h, k_n)
    ll = _roll(np.min, l, k_n)
    with np.errstate(divide="ignore", invalid="ignore"):
        fast_k = np.where(hh - ll != 0, (c - ll) / (hh - ll) * 100.0, 50.0)
    return fast_k, sma(fast_k, d_n)


def stochrsi(c, n: int = 14):
    r = rsi(c, n)
    safe_max = lambda w: np.nan if np.isnan(w).all() else np.nanmax(w)
    safe_min = lambda w: np.nan if np.isnan(w).all() else np.nanmin(w)
    hh = _roll(safe_max, r, n)
    ll = _roll(safe_min, r, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(hh - ll != 0, (r - ll) / (hh - ll) * 100.0, 50.0)


def willr(h, l, c, n: int = 14) -> np.ndarray:
    hh = _roll(np.max, h, n)
    ll = _roll(np.min, l, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(hh - ll != 0, (hh - c) / (hh - ll) * -100.0, -50.0)


def cci(h, l, c, n: int = 14) -> np.ndarray:
    tp = (h + l + c) / 3.0
    m = sma(tp, n)
    md = _roll(lambda w: np.mean(np.abs(w - np.mean(w))), tp, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(md != 0, (tp - m) / (0.015 * md), 0.0)


def cmo(c, n: int = 14) -> np.ndarray:
    d = np.diff(c, prepend=c[0])
    up = _roll(np.sum, np.where(d > 0, d, 0.0), n)
    dn = _roll(np.sum, np.where(d < 0, -d, 0.0), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(up + dn != 0, (up - dn) / (up + dn) * 100.0, 0.0)


def mom(c, n: int = 10) -> np.ndarray:
    out = np.full(len(c), np.nan)
    out[n:] = c[n:] - c[:-n]
    return out


def roc(c, n: int = 10) -> np.ndarray:
    out = np.full(len(c), np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        out[n:] = (c[n:] / c[:-n] - 1.0) * 100.0
    return out


def rocp(c, n: int = 10) -> np.ndarray:
    return roc(c, n) / 100.0


def rocr(c, n: int = 10) -> np.ndarray:
    out = np.full(len(c), np.nan)
    with np.errstate(divide="ignore", invalid="ignore"):
        out[n:] = c[n:] / c[:-n]
    return out


def obv(c, v) -> np.ndarray:
    sign = np.sign(np.diff(c, prepend=c[0]))
    sign[0] = 0
    return np.cumsum(sign * v)


def ad_line(h, l, c, v) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        mfm = np.where(h - l != 0, ((c - l) - (h - c)) / (h - l), 0.0)
    return np.cumsum(mfm * v)


def adosc(h, l, c, v, fast: int = 3, slow: int = 10) -> np.ndarray:
    a = ad_line(h, l, c, v)
    return ema(a, fast) - ema(a, slow)


def mfi(h, l, c, v, n: int = 14) -> np.ndarray:
    tp = (h + l + c) / 3.0
    mf = tp * v
    d = np.diff(tp, prepend=tp[0])
    pos = _roll(np.sum, np.where(d > 0, mf, 0.0), n)
    neg = _roll(np.sum, np.where(d < 0, mf, 0.0), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(pos + neg != 0, pos / (pos + neg) * 100.0, 50.0)


def trange(h, l, c) -> np.ndarray:
    pc = np.roll(c, 1)
    pc[0] = c[0]
    return np.maximum(h - l, np.maximum(np.abs(h - pc), np.abs(l - pc)))


def atr(h, l, c, n: int = 14) -> np.ndarray:
    return _wilder(trange(h, l, c), n)


def natr(h, l, c, n: int = 14) -> np.ndarray:
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(c != 0, atr(h, l, c, n) / c * 100.0, np.nan)


def bbands(c, n: int = 20, k: float = 2.0):
    mid = sma(c, n)
    sd = _roll(lambda w: np.std(w), c, n)
    return mid + k * sd, mid, mid - k * sd


def stddev(c, n: int = 20) -> np.ndarray:
    return _roll(lambda w: np.std(w), c, n)


def var(c, n: int = 20) -> np.ndarray:
    return _roll(lambda w: np.var(w), c, n)


def avgprice(o, h, l, c):
    return (o + h + l + c) / 4.0


def medprice(h, l):
    return (h + l) / 2.0


def typprice(h, l, c):
    return (h + l + c) / 3.0


def wclprice(h, l, c):
    return (h + l + 2 * c) / 4.0


def macd(c, fast: int = 12, slow: int = 26, sig: int = 9):
    dif = ema(c, fast) - ema(c, slow)
    ok = ~np.isnan(dif)
    dea = np.full(len(c), np.nan)
    if ok.any():
        dea_part = ema(dif[ok], sig)
        dea[np.where(ok)[0]] = dea_part
    return dif, dea, dif - dea


def macdfix(c, sig: int = 9):
    return macd(c, 12, 26, sig)


def macdext(c, fast: int = 12, slow: int = 26, sig: int = 9, ma_type: str = "sma"):
    f = sma if ma_type == "sma" else ema
    dif = f(c, fast) - f(c, slow)
    ok = ~np.isnan(dif)
    dea = np.full(len(c), np.nan)
    if ok.any():
        dea[np.where(ok)[0]] = f(dif[ok], sig)
    return dif, dea, dif - dea


def _dm(h, l):
    up = np.diff(h, prepend=h[0])
    dn = -np.diff(l, prepend=l[0])
    plus = np.where((up > dn) & (up > 0), up, 0.0)
    minus = np.where((dn > up) & (dn > 0), dn, 0.0)
    plus[0] = minus[0] = 0.0
    return plus, minus


def plus_dm(h, l, n: int = 14):
    return _wilder(_dm(h, l)[0], n) * n


def minus_dm(h, l, n: int = 14):
    return _wilder(_dm(h, l)[1], n) * n


def _di(h, l, c, n: int = 14):
    p, m = _dm(h, l)
    tr_s = _wilder(trange(h, l, c), n)
    with np.errstate(divide="ignore", invalid="ignore"):
        pdi = np.where(tr_s != 0, _wilder(p, n) / tr_s * 100.0, 0.0)
        mdi = np.where(tr_s != 0, _wilder(m, n) / tr_s * 100.0, 0.0)
    return pdi, mdi


def plus_di(h, l, c, n: int = 14):
    return _di(h, l, c, n)[0]


def minus_di(h, l, c, n: int = 14):
    return _di(h, l, c, n)[1]


def dx(h, l, c, n: int = 14):
    p, m = _di(h, l, c, n)
    with np.errstate(divide="ignore", invalid="ignore"):
        return np.where(p + m != 0, np.abs(p - m) / (p + m) * 100.0, 0.0)


def adx(h, l, c, n: int = 14):
    return _wilder(dx(h, l, c, n), n)


def adxr(h, l, c, n: int = 14):
    a = adx(h, l, c, n)
    out = np.full(len(c), np.nan)
    out[n:] = (a[n:] + a[:-n]) / 2.0
    return out


def ta_max(x, n: int = 30):
    return _roll(np.max, x, n)


def ta_min(x, n: int = 30):
    return _roll(np.min, x, n)


def maxindex(x, n: int = 30):
    return _roll(lambda w: float(n - 1 - int(np.argmax(w))), x, n)  # 0=最新棒創高


def minindex(x, n: int = 30):
    return _roll(lambda w: float(n - 1 - int(np.argmin(w))), x, n)


def sar(h, l, accel: float = 0.02, maximum: float = 0.2) -> np.ndarray:
    out = np.full(len(h), np.nan)
    if len(h) < 2:
        return out
    long = h[1] >= h[0]
    ep = h[0] if long else l[0]
    s = l[0] if long else h[0]
    af = accel
    for i in range(1, len(h)):
        s = s + af * (ep - s)
        if long:
            s = min(s, l[i - 1], l[i - 2] if i >= 2 else l[i - 1])
            if l[i] < s:
                long, s, ep, af = False, ep, l[i], accel
            elif h[i] > ep:
                ep, af = h[i], min(af + accel, maximum)
        else:
            s = max(s, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if h[i] > s:
                long, s, ep, af = True, ep, h[i], accel
            elif l[i] < ep:
                ep, af = l[i], min(af + accel, maximum)
        out[i] = s
    return out


def correl(a, b, n: int = 30) -> np.ndarray:
    out = np.full(len(a), np.nan)
    for i in range(n - 1, len(a)):
        wa, wb = a[i - n + 1:i + 1], b[i - n + 1:i + 1]
        sa, sb = np.std(wa), np.std(wb)
        out[i] = float(np.corrcoef(wa, wb)[0, 1]) if sa > 0 and sb > 0 else 0.0
    return out


def beta(a, b, n: int = 30) -> np.ndarray:
    ra = np.diff(a) / a[:-1]
    rb = np.diff(b) / b[:-1]
    out = np.full(len(a), np.nan)
    for i in range(n, len(a)):
        wa, wb = ra[i - n:i], rb[i - n:i]
        vb = np.var(wb)
        out[i] = float(np.cov(wa, wb)[0, 1] / vb) if vb > 0 else np.nan
    return out


def ta_sum(x, n: int = 30):
    return _roll(np.sum, x, n)

# ============================================================================
# §4 K線型態(SSOT §12 十型;規則依表列確認條件,回傳 ±100/0 talib 慣例)
# ============================================================================

def _candle_parts(o, h, l, c):
    body = np.abs(c - o)
    upper = h - np.maximum(o, c)
    lower = np.minimum(o, c) - l
    rng = np.where(h - l > 0, h - l, 1e-12)
    return body, upper, lower, rng


def _trend(c, i, n: int = 3) -> int:
    """前 n 棒方向:+1 升 −1 跌 0 平(型態的高位/低位語境)。"""
    if i < n:
        return 0
    seg = c[i - n:i]
    if seg[-1] > seg[0]:
        return 1
    if seg[-1] < seg[0]:
        return -1
    return 0


def _pattern(o, h, l, c, kind: str) -> np.ndarray:
    body, upper, lower, rng = _candle_parts(o, h, l, c)
    n = len(c)
    out = np.zeros(n)
    for i in range(n):
        b, up, lo, r = body[i], upper[i], lower[i], rng[i]
        t = _trend(c, i)
        small = b <= r * 0.1
        if kind == "cdldoji" and small:
            out[i] = 100
        elif kind == "cdlspinningtop" and (r * 0.1 < b <= r * 0.35) and up > b and lo > b:
            out[i] = 100
        elif kind == "cdlhammer" and t < 0 and lo >= 2 * b and up <= b * 0.5 and b > 0:
            out[i] = 100
        elif kind == "cdlinvertedhammer" and t < 0 and up >= 2 * b and lo <= b * 0.5 and b > 0:
            out[i] = 100
        elif kind == "cdlhangingman" and t > 0 and lo >= 2 * b and up <= b * 0.5 and b > 0:
            out[i] = -100
        elif kind == "cdlshootingstar" and t > 0 and up >= 2 * b and lo <= b * 0.5 and b > 0:
            out[i] = -100
        elif kind == "cdlpiercing" and i >= 1:
            prev_bear = c[i - 1] < o[i - 1]
            if prev_bear and c[i] > o[i] and o[i] < l[i - 1] and \
                    c[i] > (o[i - 1] + c[i - 1]) / 2 and c[i] < o[i - 1]:
                out[i] = 100
        elif kind == "cdldarkcloudcover" and i >= 1:
            prev_bull = c[i - 1] > o[i - 1]
            if prev_bull and c[i] < o[i] and o[i] > h[i - 1] and \
                    c[i] < (o[i - 1] + c[i - 1]) / 2 and c[i] > o[i - 1]:
                out[i] = -100
        elif kind == "cdlmorningstar" and i >= 2:
            b0 = c[i - 2] < o[i - 2] and body[i - 2] > rng[i - 2] * 0.5
            star = body[i - 1] <= rng[i - 1] * 0.3
            b2 = c[i] > o[i] and c[i] > (o[i - 2] + c[i - 2]) / 2
            if b0 and star and b2:
                out[i] = 100
        elif kind == "cdleveningstar" and i >= 2:
            b0 = c[i - 2] > o[i - 2] and body[i - 2] > rng[i - 2] * 0.5
            star = body[i - 1] <= rng[i - 1] * 0.3
            b2 = c[i] < o[i] and c[i] < (o[i - 2] + c[i - 2]) / 2
            if b0 and star and b2:
                out[i] = -100
    return out

# ============================================================================
# §5 指標登記簿 — 逐項對照 ssot/talib_indicators_classification.md
#    inputs: c/o/h/l/v/b(第二序列)  outputs: 欄名list  th: 轉折點基準(訊號用)
# ============================================================================

def _reg(cat, zh, inputs, fn, outs, rng="", th=None, period=None, talib_only=False):
    return {"category": cat, "zh": zh, "inputs": inputs, "fn": fn, "outputs": outs,
            "range": rng, "threshold": th or {}, "period": period,
            "talib_only": talib_only}


REGISTRY: Dict[str, Dict[str, Any]] = {
    # 1 趨勢
    "sma": _reg("趨勢", "簡單移動平均", "c", lambda d, n=20: sma(d["close"], n), ["sma"], period=20),
    "ema": _reg("趨勢", "指數移動平均", "c", lambda d, n=20: ema(d["close"], n), ["ema"], period=20),
    "dema": _reg("趨勢", "雙指數移動平均", "c", lambda d, n=20: dema(d["close"], n), ["dema"], period=20),
    "tema": _reg("趨勢", "三重指數移動平均", "c", lambda d, n=20: tema(d["close"], n), ["tema"], period=20),
    "kama": _reg("趨勢", "自適應移動平均", "c", lambda d, n=20: kama(d["close"], n), ["kama"], period=20),
    # 2 動量
    "rsi": _reg("動量", "相對強弱指標", "c", lambda d, n=14: rsi(d["close"], n), ["rsi"],
                "0-100", {"overbought": 70, "oversold": 30}, 14),
    "stoch": _reg("動量", "隨機指標KD", "hlc", lambda d, n=9: stoch(d["high"], d["low"], d["close"], n),
                  ["stoch_k", "stoch_d"], "0-100", {"overbought": 80, "oversold": 20}, 9),
    "stochf": _reg("動量", "快速隨機", "hlc", lambda d, n=9: stochf(d["high"], d["low"], d["close"], n),
                   ["stochf_k", "stochf_d"], "0-100", {"overbought": 85, "oversold": 15}, 9),
    "stochrsi": _reg("動量", "隨機RSI", "c", lambda d, n=14: stochrsi(d["close"], n), ["stochrsi"],
                     "0-100", {"overbought": 80, "oversold": 20}, 14),
    "willr": _reg("動量", "威廉指標", "hlc", lambda d, n=14: willr(d["high"], d["low"], d["close"], n),
                  ["willr"], "-100-0", {"overbought": -20, "oversold": -80}, 14),
    "cci": _reg("動量", "商品通道", "hlc", lambda d, n=14: cci(d["high"], d["low"], d["close"], n),
                ["cci"], "", {"overbought": 100, "oversold": -100}, 14),
    "cmo": _reg("動量", "錢德動量", "c", lambda d, n=14: cmo(d["close"], n), ["cmo"],
                "-100-100", {"strong": 50, "weak": -50}, 14),
    "mom": _reg("動量", "動量", "c", lambda d, n=10: mom(d["close"], n), ["mom"], "", {"zero": 0}, 10),
    "roc": _reg("動量", "變化率%", "c", lambda d, n=10: roc(d["close"], n), ["roc"], "%",
                {"strong": 10, "weak": -10}, 10),
    "rocp": _reg("動量", "變化率比例", "c", lambda d, n=10: rocp(d["close"], n), ["rocp"], "", None, 10),
    "rocr": _reg("動量", "變化率比值", "c", lambda d, n=10: rocr(d["close"], n), ["rocr"], "", None, 10),
    # 3 量能
    "obv": _reg("量能", "能量潮", "cv", lambda d, n=0: obv(d["close"], d["volume"]), ["obv"]),
    "ad": _reg("量能", "累積派發線", "hlcv",
               lambda d, n=0: ad_line(d["high"], d["low"], d["close"], d["volume"]), ["ad"]),
    "adosc": _reg("量能", "累積派發振盪", "hlcv",
                  lambda d, n=0: adosc(d["high"], d["low"], d["close"], d["volume"]),
                  ["adosc"], "", {"zero": 0}),
    "mfi": _reg("量能", "資金流量", "hlcv",
                lambda d, n=14: mfi(d["high"], d["low"], d["close"], d["volume"], n), ["mfi"],
                "0-100", {"overbought": 80, "oversold": 20}, 14),
    # 4 波動
    "trange": _reg("波動", "真實區間", "hlc", lambda d, n=0: trange(d["high"], d["low"], d["close"]), ["trange"]),
    "atr": _reg("波動", "平均真實區間", "hlc", lambda d, n=14: atr(d["high"], d["low"], d["close"], n),
                ["atr"], ">0", None, 14),
    "natr": _reg("波動", "標準化ATR", "hlc", lambda d, n=14: natr(d["high"], d["low"], d["close"], n),
                 ["natr"], "0-100", {"high_vol": 2.0, "low_vol": 0.5}, 14),
    "bbands": _reg("波動", "布林通道", "c", lambda d, n=20: bbands(d["close"], n),
                   ["bb_upper", "bb_mid", "bb_lower"], "", None, 20),
    "stddev": _reg("波動", "標準差", "c", lambda d, n=20: stddev(d["close"], n), ["stddev"], ">0", None, 20),
    "var": _reg("波動", "方差", "c", lambda d, n=20: var(d["close"], n), ["var"], ">0", None, 20),
    # 5 價格
    "avgprice": _reg("價格", "四價平均", "ohlc",
                     lambda d, n=0: avgprice(d["open"], d["high"], d["low"], d["close"]), ["avgprice"]),
    "medprice": _reg("價格", "中位價", "hl", lambda d, n=0: medprice(d["high"], d["low"]), ["medprice"]),
    "typprice": _reg("價格", "典型價", "hlc",
                     lambda d, n=0: typprice(d["high"], d["low"], d["close"]), ["typprice"]),
    "wclprice": _reg("價格", "加權收盤價", "hlc",
                     lambda d, n=0: wclprice(d["high"], d["low"], d["close"]), ["wclprice"]),
    # 6 MACD
    "macd": _reg("MACD", "移動平均聚散", "c", lambda d, n=0: macd(d["close"]),
                 ["macd_dif", "macd_dea", "macd_hist"], "", {"zero": 0}),
    "macdfix": _reg("MACD", "固定參數MACD", "c", lambda d, n=0: macdfix(d["close"]),
                    ["macdfix_dif", "macdfix_dea", "macdfix_hist"]),
    "macdext": _reg("MACD", "可控MA型MACD", "c", lambda d, n=0: macdext(d["close"]),
                    ["macdext_dif", "macdext_dea", "macdext_hist"]),
    # 7 方向
    "adx": _reg("方向", "趨勢強度", "hlc", lambda d, n=14: adx(d["high"], d["low"], d["close"], n),
                ["adx"], "0-100", {"trend": 25, "strong": 40}, 14),
    "adxr": _reg("方向", "ADX評級", "hlc", lambda d, n=14: adxr(d["high"], d["low"], d["close"], n),
                 ["adxr"], "0-100", None, 14),
    "dx": _reg("方向", "方向指數", "hlc", lambda d, n=14: dx(d["high"], d["low"], d["close"], n),
               ["dx"], "0-100", None, 14),
    "plus_di": _reg("方向", "正方向指標", "hlc",
                    lambda d, n=14: plus_di(d["high"], d["low"], d["close"], n), ["plus_di"],
                    "0-100", None, 14),
    "minus_di": _reg("方向", "負方向指標", "hlc",
                     lambda d, n=14: minus_di(d["high"], d["low"], d["close"], n), ["minus_di"],
                     "0-100", None, 14),
    "plus_dm": _reg("方向", "正方向運動", "hl", lambda d, n=14: plus_dm(d["high"], d["low"], n),
                    ["plus_dm"], ">0", None, 14),
    "minus_dm": _reg("方向", "負方向運動", "hl", lambda d, n=14: minus_dm(d["high"], d["low"], n),
                     ["minus_dm"], ">0", None, 14),
    # 8 極值
    "max": _reg("極值", "期間最高", "c", lambda d, n=30: ta_max(d["close"], n), ["max"], "", None, 30),
    "min": _reg("極值", "期間最低", "c", lambda d, n=30: ta_min(d["close"], n), ["min"], "", None, 30),
    "maxindex": _reg("極值", "最高位置", "c", lambda d, n=30: maxindex(d["close"], n),
                     ["maxindex"], "0..n-1", None, 30),
    "minindex": _reg("極值", "最低位置", "c", lambda d, n=30: minindex(d["close"], n),
                     ["minindex"], "0..n-1", None, 30),
    "minmax": _reg("極值", "低高雙值", "c",
                   lambda d, n=30: (ta_min(d["close"], n), ta_max(d["close"], n)),
                   ["minmax_min", "minmax_max"], "", None, 30),
    # 9 拋物線
    "sar": _reg("拋物線", "停損轉向點", "hl", lambda d, n=0: sar(d["high"], d["low"]), ["sar"]),
    "sarext": _reg("拋物線", "擴展SAR", "hl", lambda d, n=0: sar(d["high"], d["low"], 0.02, 0.2),
                   ["sarext"]),
    # 10 Hilbert(誠實 talib_only)
    "ht_dcperiod": _reg("Hilbert", "主導週期", "c", None, ["ht_dcperiod"], "10-50", None,
                        talib_only=True),
    "ht_dcphase": _reg("Hilbert", "主導週期相位", "c", None, ["ht_dcphase"], "0-360",
                       None, talib_only=True),
    "ht_sine": _reg("Hilbert", "正弦波", "c", None, ["ht_sine", "ht_leadsine"], "-1-1",
                    None, talib_only=True),
    "ht_trendmode": _reg("Hilbert", "趨勢模式", "c", None, ["ht_trendmode"], "0/1",
                         None, talib_only=True),
    # 11 統計(correl/beta 需 --map b=<欄> 第二序列)
    "correl": _reg("統計", "皮爾森相關", "cb", lambda d, n=30: correl(d["close"], d["b"], n),
                   ["correl"], "-1-1", {"strong": 0.7}, 30),
    "beta": _reg("統計", "貝塔係數", "cb", lambda d, n=30: beta(d["close"], d["b"], n),
                 ["beta"], "", {"high_risk": 1.0}, 30),
    "sum": _reg("統計", "加總", "c", lambda d, n=30: ta_sum(d["close"], n), ["sum"], "", None, 30),
}
for _pat, _zh, _bias in [("cdlhammer", "錘子線", "看漲"), ("cdlinvertedhammer", "倒錘子", "看漲"),
                         ("cdlpiercing", "刺透", "看漲"), ("cdlmorningstar", "早晨之星", "看漲"),
                         ("cdlhangingman", "上吊線", "看跌"), ("cdlshootingstar", "流星線", "看跌"),
                         ("cdldarkcloudcover", "烏雲蓋頂", "看跌"), ("cdleveningstar", "黃昏之星", "看跌"),
                         ("cdldoji", "十字星", "中性"), ("cdlspinningtop", "陀螺線", "中性")]:
    REGISTRY[_pat] = _reg("K線型態", "%s(%s)" % (_zh, _bias), "ohlc",
                          (lambda kind: lambda d, n=0: _pattern(
                              d["open"], d["high"], d["low"], d["close"], kind))(_pat),
                          [_pat], "±100/0")

NATIVE_IDS = [k for k, m in REGISTRY.items() if not m["talib_only"]]

# ============================================================================
# §6 計算層(native / talib 雙後端)+ 訊號層(SSOT 轉折點基準)
# ============================================================================

def compute_indicators(data: Dict[str, Any], ids: Sequence[str],
                       backend: str = "auto", period: Optional[int] = None
                       ) -> Tuple[Dict[str, np.ndarray], Dict[str, str]]:
    use_talib = backend == "talib" or (backend == "auto" and _module_available("talib"))
    if backend == "talib" and not _module_available("talib"):
        raise TAError("--backend talib 但 talib 未安裝(pip install TA-Lib 需 C 庫)")
    tl = __import__("talib") if use_talib else None
    out: Dict[str, np.ndarray] = {}
    used: Dict[str, str] = {}
    for iid in ids:
        meta = REGISTRY.get(iid)
        if meta is None:
            raise TAError("未知指標 %r(list 動詞看全表)" % iid)
        if "v" in meta["inputs"] and data.get("volume") is None:
            raise TAError("指標 %r 需要 volume 欄,資料檔缺" % iid)
        if "b" in meta["inputs"] and data.get("b") is None:
            raise TAError("指標 %r 需要第二序列 — 用 --map b=<欄名>" % iid)
        n = period or meta["period"] or 0
        got = None
        if tl is not None:
            fn = getattr(tl, iid.upper(), None)
            if fn is not None:
                try:
                    args = {"c": (data["close"],), "hl": (data["high"], data["low"]),
                            "hlc": (data["high"], data["low"], data["close"]),
                            "ohlc": (data["open"], data["high"], data["low"], data["close"]),
                            "hlcv": (data["high"], data["low"], data["close"], data["volume"]),
                            "cv": (data["close"], data["volume"]),
                            "cb": (data["close"], data["b"])}[meta["inputs"]]
                    got = fn(*[np.asarray(a, float) for a in args],
                             **({"timeperiod": n} if n else {}))
                    used[iid] = "talib"
                except Exception:
                    got = None  # talib 簽名不合 → 回退原生
        if got is None:
            if meta["talib_only"]:
                used[iid] = "SKIP(talib_only,原生不實作)"
                continue
            got = meta["fn"](data, n) if n else meta["fn"](data)
            used[iid] = "native"
        vals = got if isinstance(got, tuple) else (got,)
        for name, v in zip(meta["outputs"], vals):
            out[name] = np.asarray(v, float)
    return out, used


def latest_signals(data: Dict[str, Any], ind: Dict[str, np.ndarray]) -> List[Dict[str, str]]:
    """末棒訊號旗標(依 SSOT 轉折點基準;誠實:訊號≠建議)。"""
    sig: List[Dict[str, str]] = []

    def last(name):
        v = ind.get(name)
        if v is None or np.isnan(v[-1]):
            return None
        return float(v[-1])

    def add(ind_id, state, value, basis):
        sig.append({"indicator": ind_id, "state": state,
                    "value": "%.4g" % value, "basis": basis})

    checks = [("rsi", "rsi", 70, 30, "70以上超買,30以下超賣"),
              ("stoch", "stoch_k", 80, 20, "K>80超買;K<20超賣"),
              ("stochrsi", "stochrsi", 80, 20, ">80下彎賣出;<20上彎買入"),
              ("mfi", "mfi", 80, 20, "80以上超買,20以下超賣"),
              ("cci", "cci", 100, -100, "±100為超買超賣警戒線")]
    for iid, colname, hi, lo, basis in checks:
        v = last(colname)
        if v is None:
            continue
        state = "超買" if v >= hi else ("超賣" if v <= lo else "中性")
        add(iid, state, v, basis)
    v = last("willr")
    if v is not None:
        add("willr", "超買" if v >= -20 else ("超賣" if v <= -80 else "中性"),
            v, "-20以上超買,-80以下超賣")
    v = last("adx")
    if v is not None:
        p, m = last("plus_di"), last("minus_di")
        direction = ""
        if p is not None and m is not None:
            direction = "·+DI>-DI 偏多" if p > m else "·-DI>+DI 偏空"
        add("adx", ("強趨勢" if v >= 40 else "趨勢明確" if v >= 25 else "無趨勢") + direction,
            v, ">25趨勢明確,>40強趨勢")
    dif, dea = last("macd_dif"), last("macd_dea")
    if dif is not None and dea is not None:
        state = "多頭(DIF>DEA%s)" % (",0軸上" if dif > 0 else ",0軸下") if dif > dea \
            else "空頭(DIF<DEA)"
        add("macd", state, dif - dea, "DIF上穿0軸且柱狀體轉正")
    up, lo_b, c_last = last("bb_upper"), last("bb_lower"), float(data["close"][-1])
    if up is not None and lo_b is not None:
        state = "觸上軌" if c_last >= up else ("觸下軌" if c_last <= lo_b else "通道內")
        add("bbands", state, c_last, "價格觸及上下軌為極端值")
    for pat in [k for k in REGISTRY if k.startswith("cdl")]:
        v = last(pat)
        if v:
            add(pat, "%s(%+d)" % (REGISTRY[pat]["zh"], int(v)), v, "SSOT §12 確認條件")
    return sig

# ============================================================================
# §7 sample / 輸出 / chart / selftest / CLI
# ============================================================================

def make_sample(n: int = 260, seed: int = 20260811) -> List[Dict[str, Any]]:
    """合成 OHLCV+adj_close:第 180 棒嵌入 1:2 分割(close 減半,adj 連續)供鐵律驗證。"""
    rng = np.random.default_rng(seed)
    rows = []
    adj = 50.0
    split_at = 180
    for i in range(n):
        ret = rng.normal(0.0006, 0.015)
        adj *= (1 + ret)
        # 1:2 分割正典:分割「前」raw=2×adj(factor=adj/close=0.5);分割後 raw=adj(factor=1)
        factor = 0.5 if i < split_at else 1.0
        close = adj / factor
        o = close * (1 + rng.normal(0, 0.004))
        hi = max(o, close) * (1 + abs(rng.normal(0, 0.005)))
        lo = min(o, close) * (1 - abs(rng.normal(0, 0.005)))
        # 分割後每股數量倍增 → raw 量 ×2;vol/factor 還原後前後同級距(連續)
        vol = abs(rng.normal(1.5e6, 4e5)) * (2.0 if i >= split_at else 1.0)
        rows.append({"date": "D%03d" % (i + 1), "open": round(o, 3), "high": round(hi, 3),
                     "low": round(lo, 3), "close": round(close, 3),
                     "adj_close": round(adj, 3), "volume": round(vol, 0)})
    return rows


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = _csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def indicators_to_rows(data: Dict[str, Any], ind: Dict[str, np.ndarray]) -> List[Dict[str, Any]]:
    rows = []
    for i, d in enumerate(data["dates"]):
        row: Dict[str, Any] = {"date": d, "close": round(float(data["close"][i]), 6)}
        for name, v in ind.items():
            row[name] = "" if np.isnan(v[i]) else round(float(v[i]), 6)
        rows.append(row)
    return rows


def run_chart(data: Dict[str, Any], ind: Dict[str, np.ndarray], out_dir: Path) -> List[str]:
    """三面板 × VAP 圖庫:K線 / RSI / MACD(title 誠實帶 price_basis 後綴)。"""
    vap_path = None
    for base in [HERE.parent, *HERE.parents]:
        cand = base / "VAP" / "engine" / "VAP_ENG003_AutoplotSeabornPlotly_v0100.py"
        if cand.exists():
            vap_path = cand
            break
    if vap_path is None:
        raise TAError("找不到 VAP 引擎(chart 動詞需要它);compute/signals 不受影響")
    spec_mod = importlib.util.spec_from_file_location("vap_engine", str(vap_path))
    vap = importlib.util.module_from_spec(spec_mod)
    spec_mod.loader.exec_module(vap)
    spec = vap.Spec(vap.find_ssot_dir(None))
    if not vap.SeabornBackend.available():
        raise TAError("chart 需 seaborn/matplotlib(pip install seaborn)")
    backend = vap.SeabornBackend(spec)
    suf = data["provenance"]["label_suffix"]
    dates = data["dates"]
    outs = []

    def clean_xy(y):
        keep = [i for i in range(len(dates)) if not np.isnan(y[i])]
        return [dates[i] for i in keep], [float(y[i]) for i in keep]

    candle = {"date": dates, "open": list(map(float, data["open"])),
              "high": list(map(float, data["high"])), "low": list(map(float, data["low"])),
              "close": list(map(float, data["close"])),
              "volume": list(map(float, data["volume"] if data["volume"] is not None
                                 else np.zeros(len(dates))))}
    backend.render("candle", candle, out_dir / "ta_candle.png", scale=1,
                   title="K線 × SMA/EMA/BB × Volume%s" % suf)
    outs.append("ta_candle.png")
    if "rsi" in ind:
        x, y = clean_xy(ind["rsi"])
        backend.render("rollsharpe", {"date": x, "sharpe": y}, out_dir / "ta_rsi.png",
                       scale=1, title="RSI(14)%s · 70/30 超買超賣" % suf)
        outs.append("ta_rsi.png")
    if "macd_dif" in ind and "macd_hist" in ind:
        keep = [i for i in range(len(dates)) if not np.isnan(ind["macd_hist"][i])]
        backend.render("dbarline", {"date": [dates[i] for i in keep],
                                    "bar": [float(ind["macd_hist"][i]) for i in keep],
                                    "line": [float(ind["macd_dif"][i]) for i in keep]},
                       out_dir / "ta_macd.png", scale=1,
                       title="MACD 柱狀體(左)× DIF(右)%s" % suf)
        outs.append("ta_macd.png")
    return outs


def selftest() -> int:
    results: List[Tuple[str, str, str]] = []

    def check(name, fn):
        try:
            fn()
            results.append((name, "PASS", ""))
        except TAError as e:
            results.append((name, "SKIP", str(e)[:70]))
        except Exception as e:
            results.append((name, "FAIL", "%s: %s" % (type(e).__name__, str(e)[:90])))

    def t_sma_ema():
        x = np.array([1., 2., 3., 4., 5., 6.])
        assert np.allclose(sma(x, 3)[2:], [2, 3, 4, 5])
        e = ema(x, 3)
        assert abs(e[2] - 2.0) < 1e-9 and abs(e[3] - 3.0) < 1e-9  # 種子SMA後遞推
    check("sma_ema_精確值", t_sma_ema)

    def t_rsi():
        up = np.linspace(1, 60, 60)
        assert rsi(up, 14)[-1] > 99.0            # 全漲 → RSI→100
        dn = np.linspace(60, 1, 60)
        assert rsi(dn, 14)[-1] < 1.0
    check("rsi_極端方向", t_rsi)

    def t_macd_identity():
        rng = np.random.default_rng(7)
        c = 100 + np.cumsum(rng.normal(0, 1, 200))
        dif, _, _ = macd(c)
        ref = ema(c, 12) - ema(c, 26)
        ok = ~np.isnan(dif) & ~np.isnan(ref)
        assert np.allclose(dif[ok], ref[ok])
    check("macd_恆等式", t_macd_identity)

    def t_bbands():
        rng = np.random.default_rng(9)
        c = 50 + np.cumsum(rng.normal(0, 1, 100))
        u, m, l = bbands(c, 20)
        i = 60
        assert abs(m[i] - np.mean(c[i - 19:i + 1])) < 1e-9
        assert abs((u[i] - m[i]) - 2 * np.std(c[i - 19:i + 1])) < 1e-9
    check("bbands_恆等式", t_bbands)

    def t_atr():
        h = np.array([10., 11, 12, 13])
        l = np.array([9., 10, 11, 12])
        c = np.array([9.5, 10.5, 11.5, 12.5])
        tr = trange(h, l, c)
        assert np.allclose(tr, [1, 1.5, 1.5, 1.5])
    check("trange_手算", t_atr)

    def t_adj_discipline():
        import tempfile
        rows = make_sample()
        d = Path(tempfile.mkdtemp(prefix="ta_"))
        p = d / "s.csv"
        write_csv(p, rows)
        data = load_ohlcv(p)
        pr = data["provenance"]
        assert pr["price_basis"] == "adj" and pr["label_suffix"].strip() == "(adj)"
        assert abs(pr["adj_factor_min"] - 0.5) < 1e-3 and abs(pr["adj_factor_max"] - 1.0) < 1e-3
        # 分割日 adj 連續:跨第 180 棒不得出現 ±50% 跳空
        rets = np.diff(data["close"]) / data["close"][:-1]
        assert np.max(np.abs(rets)) < 0.2, "adj 序列在分割日應連續"
        # volume 還原連續:raw 量分割後 ×2,pre 段 ÷factor(0.5) 亦 ×2 → 前後同級距
        pre = float(np.mean(data["volume"][150:179]))
        post = float(np.mean(data["volume"][181:210]))
        assert 0.6 < post / pre < 1.6, "還原量能應跨分割連續(pre=%.0f post=%.0f)" % (pre, post)
        # raw 後備:去掉 adj 欄
        rows2 = [{k: v for k, v in r.items() if k != "adj_close"} for r in rows]
        p2 = d / "s2.csv"
        write_csv(p2, rows2)
        pr2 = load_ohlcv(p2)["provenance"]
        assert pr2["price_basis"] == "raw"
    check("adj_鐵律_含分割與後備", t_adj_discipline)

    def t_patterns():
        # 構造:下跌三棒後錘子線(下影≥2×實體,上影≤0.5×實體)
        o = np.array([10., 9.5, 9.0, 8.62])
        c = np.array([9.5, 9.0, 8.5, 8.60])
        h = np.array([10.1, 9.6, 9.1, 8.625])
        l = np.array([9.4, 8.9, 8.4, 8.0])
        assert _pattern(o, h, l, c, "cdlhammer")[-1] == 100
        # 十字星
        o2 = np.array([10., 10.0])
        c2 = np.array([10., 10.005])
        h2 = np.array([10.2, 10.3])
        l2 = np.array([9.8, 9.7])
        assert _pattern(o2, h2, l2, c2, "cdldoji")[-1] == 100
    check("candle_型態構造樣本", t_patterns)

    def t_compute_signals():
        import tempfile
        d = Path(tempfile.mkdtemp(prefix="ta2_"))
        p = d / "s.csv"
        write_csv(p, make_sample())
        data = load_ohlcv(p)
        ind, used = compute_indicators(data, NATIVE_IDS_NO_B)
        assert all(b in ("native", "talib") for b in used.values())
        sig = latest_signals(data, ind)
        assert any(s["indicator"] == "rsi" for s in sig)
        rows = indicators_to_rows(data, ind)
        assert len(rows) == data["provenance"]["rows"]
    check("compute_signals_全譜", t_compute_signals)

    def t_ht_honest():
        data_stub = {"close": np.linspace(1, 10, 50), "open": None, "high": None,
                     "low": None, "volume": None}
        _, used = compute_indicators(
            {**data_stub}, ["ht_dcperiod"],
            backend="native" if not _module_available("talib") else "auto")
        assert "SKIP" in used.get("ht_dcperiod", "") or used.get("ht_dcperiod") == "talib"
    check("hilbert_誠實talib_only", t_ht_honest)

    def t_talib_crosscheck():
        if not _module_available("talib"):
            raise TAError("talib 未安裝 — 交叉核對誠實 SKIP")
        import talib as tl
        rng = np.random.default_rng(3)
        c = 100 + np.cumsum(rng.normal(0, 1, 300))
        ours, ref = rsi(c, 14), tl.RSI(c, timeperiod=14)
        ok = ~np.isnan(ours) & ~np.isnan(ref)
        assert np.nanmax(np.abs(ours[ok] - ref[ok])) < 1e-6
    check("talib_交叉核對", t_talib_crosscheck)

    def t_registry_ssot():
        assert SSOT_MD.exists(), "指標分類 SSOT 缺席"
        assert len(REGISTRY) >= 55
        cats = {m["category"] for m in REGISTRY.values()}
        assert {"趨勢", "動量", "量能", "波動", "價格", "MACD", "方向",
                "極值", "拋物線", "Hilbert", "統計", "K線型態"} <= cats
    check("registry_對照SSOT", t_registry_ssot)

    width = max(len(n) for n, _, _ in results)
    print("=" * 66)
    print("VIA_TALibEngine v%s selftest(%d 項)" % (__version__, len(results)))
    print("=" * 66)
    fails = 0
    for name, st, note in results:
        if st == "FAIL":
            fails += 1
        print("  %-*s  %s%s" % (width, name, st, ("  ← " + note) if note else ""))
    print("-" * 66)
    print("  合計:%d PASS / %d SKIP / %d FAIL"
          % (sum(1 for _, s, _ in results if s == "PASS"),
             sum(1 for _, s, _ in results if s == "SKIP"), fails))
    return 1 if fails else 0


NATIVE_IDS_NO_B = [k for k in NATIVE_IDS if "b" not in REGISTRY[k]["inputs"]]


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="VIA_TALibEngine",
                                 description="VIA TA-Lib 指標引擎 v%s(adj 鐵律 · 原生+talib 雙後端)" % __version__)
    sub = ap.add_subparsers(dest="verb")
    sub.add_parser("probe", help="後端/SSOT 探測")
    li = sub.add_parser("list", help="指標清單")
    li.add_argument("--category", help="分類過濾(趨勢/動量/量能/波動/價格/MACD/方向/極值/拋物線/Hilbert/統計/K線型態)")
    sp = sub.add_parser("sample", help="產生示範 OHLCV(含 adj_close 與 1:2 分割)")
    sp.add_argument("-o", "--out", default="ohlcv_sample.csv")
    for name in ("compute", "signals", "chart"):
        pp = sub.add_parser(name)
        pp.add_argument("--file", required=True, help="OHLCV 資料檔(.csv/.tsv/.json/.sqlite/.duckdb)")
        pp.add_argument("--table", help="資料庫表名")
        pp.add_argument("--indicators", nargs="+", default=["all"],
                        help="指標 id(逗號/空格皆可;all=全部原生)")
        pp.add_argument("--backend", default="auto", choices=["auto", "native", "talib"])
        pp.add_argument("--period", type=int, help="覆寫預設週期")
        pp.add_argument("--map", dest="map_pairs", action="append", default=[],
                        help="b=<欄名>(correl/beta 第二序列)")
        pp.add_argument("--out", help="輸出(csv 檔或 chart 目錄)")
        pp.add_argument("--json", action="store_true", help="JSON 輸出(stdout)")
    sub.add_parser("selftest")
    args = ap.parse_args(argv)
    if not args.verb:
        ap.print_help()
        return 0

    if args.verb == "probe":
        rules, src = load_price_rules()
        print("VIA_TALibEngine v%s" % __version__)
        print("  [%s] talib C 後端 %s" % (("在位" if _module_available("talib") else "缺席"),
                                          "" if _module_available("talib") else "→ 原生 numpy 全譜(Hilbert 例外誠實 SKIP)"))
        print("  [在位] 指標分類 SSOT %s" % SSOT_MD if SSOT_MD.exists()
              else "  [缺席] 指標分類 SSOT")
        print("  price 規則來源:%s" % src)
        print("  useAdjClose=%s adjustAllPrices=%s splitAdjustVolume=%s fallback=%s"
              % (rules.get("useAdjClose"), rules.get("adjustAllPrices"),
                 rules.get("splitAdjustVolume"), rules.get("fallbackWhenNoAdj")))
        print("  指標 %d 型(原生 %d · talib_only %d)"
              % (len(REGISTRY), len(NATIVE_IDS), len(REGISTRY) - len(NATIVE_IDS)))
        return 0

    if args.verb == "list":
        for iid, m in REGISTRY.items():
            if args.category and m["category"] != args.category:
                continue
            th = " · 基準:%s" % m["threshold"] if m["threshold"] else ""
            extra = " [talib_only]" if m["talib_only"] else ""
            print("%-18s %-6s %s(%s)%s%s" % (iid, m["category"], m["zh"],
                                             m["range"] or "無限制", th, extra))
        return 0

    if args.verb == "sample":
        p = Path(args.out)
        write_csv(p, make_sample())
        print("已產生 %s(260 棒,含 adj_close;第 180 棒嵌 1:2 分割)" % p)
        print("  compute:python VIA_TALibEngine.py compute --file %s --out ind.csv" % p)
        return 0

    if args.verb == "selftest":
        return selftest()

    # compute / signals / chart 共用載入
    try:
        data = load_ohlcv(Path(args.file), args.table)
        for pair in args.map_pairs:
            k, _, v = pair.partition("=")
            if k.strip() == "b":
                cols = load_table(Path(args.file), args.table)
                if v.strip() not in cols:
                    raise TAError("--map b=%r 欄不存在" % v)
                data["b"] = _numf(cols[v.strip()])
        ids_raw = [t for tok in args.indicators for t in str(tok).split(",") if t.strip()]
        ids = NATIVE_IDS_NO_B if ids_raw == ["all"] else ids_raw
        ind, used = compute_indicators(data, ids, backend=args.backend, period=args.period)
    except TAError as e:
        print("誠實 FAIL:%s" % e, file=sys.stderr)
        return 1
    prov = data["provenance"]
    print("price_basis=%s%s · rows=%d · 後端:%s"
          % (prov["price_basis"], prov["label_suffix"], prov["rows"],
             json.dumps(used, ensure_ascii=False)[:160]))

    if args.verb == "compute":
        rows = indicators_to_rows(data, ind)
        if args.json:
            print(json.dumps({"provenance": prov, "rows": rows[-5:]}, ensure_ascii=False, indent=2))
        if args.out:
            write_csv(Path(args.out), rows)
            print("已寫出 %s(%d 列 × %d 欄)" % (args.out, len(rows), len(rows[0])))
        elif not args.json:
            for r in rows[-3:]:
                print(json.dumps(r, ensure_ascii=False))
        return 0

    if args.verb == "signals":
        sig = latest_signals(data, ind)
        print("末棒(%s)訊號 — 依 SSOT 轉折點基準;訊號≠建議:" % data["dates"][-1])
        for s in sig:
            print("  %-12s %-24s 值=%-10s 基準:%s" % (s["indicator"], s["state"],
                                                     s["value"], s["basis"]))
        if args.out:
            write_csv(Path(args.out), sig)
            print("已寫出 %s" % args.out)
        return 0

    if args.verb == "chart":
        try:
            outs = run_chart(data, ind, Path(args.out or "talib_charts"))
        except TAError as e:
            print("誠實 FAIL:%s" % e, file=sys.stderr)
            return 1
        for f in outs:
            print("[OK] %s/%s" % (args.out or "talib_charts", f))
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
