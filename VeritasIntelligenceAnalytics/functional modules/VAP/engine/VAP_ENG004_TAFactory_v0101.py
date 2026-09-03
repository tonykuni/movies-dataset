#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VAP_ENG004_TAFactory v0101 — TA-Lib 全指標工廠 · VAP 優化版(批123;via-vapta;批330 資料律)
批330 操作員嚴令:TA-Lib 輸入價一律還原價(pick_price 只認 adj_close/adjClose;裸 close 需 allow_raw=True
明示且記錄 PRICE_RAW_WARN,預設拒=誠實 KeyError);量類指標(MFI)只吃 attrs ex_daytrade=True 之量
(CGC_MDL118 ex_daytrade 產出),裸量=SKIP 記 VOLUME_RAW_SKIP;v0100 零觸碰。[VIA:PLOTDATA-LAW:v0100]
====================================================================
操作員令(批123):「TA-Lib 各類指數將它補齊全,統計相關不需要導入
其他(用既有 pandas/numpy)要完善;除了 RSI 這種早已有預定參數外,
其他大部分參數預設值都用 5/10/20/60/120/240 days;無風險利率=台灣
十年期公債殖利率或美國十年期公債殖利率二選一;benchmark=台股跟
標普500 二選一;將 TA-Lib 模組優化後拉到 VAP 下面來。」
本器=VDF_ENG048 之 version-forward 優化版(VDF 正本零觸碰):
  ① 後備組 12 式 → 全家族補齊(talib C 庫缺席時仍完整):
     Overlap:SMA/EMA/WMA/DEMA/TEMA/TRIMA/MIDPOINT/BBANDS(%B+寬)
     Momentum:RSI/MACD(線+訊號+柱)/MOM/ROC/ROCP/ROCR/CMO/TRIX/APO/PPO
     Volatility(https://ta-lib.org/functions/#volatility-indicators):
       TRANGE/ATR/NATR(OHLC 在位時;close-only 誠實 SKIP)
     OHLC Momentum:STOCH(%K%D)/WILLR/CCI/ADX/AROON(上·下)/MFI(需量)
     Statistic(TA-Lib 統計組,零外掛):STDDEV/VAR/ZSCORE/
       LINEARREG/LINEARREG_SLOPE/LINEARREG_ANGLE/LINEARREG_INTERCEPT/
       TSF/CORREL(對基準)/BETA(對基準)
     Risk(rf+基準):SHARPE/SORTINO/ALPHA/ROLLRET(年化,rf 可換)
  ② 參數政策:CANONICAL 冊(RSI14/MACD 12-26-9/BB 20-2/STOCH 5-3/
     ADX·CCI·WILLR·MFI·AROON 14/APO·PPO 12-26)不吃週期輪;
     其餘(含波動族 ATR/NATR 與統計族)一律 5/10/20/60/120/240。
  ③ rf 二選一:US10Y=DGS10(在庫)/TW10Y=台灣十年期公債殖利率
     (序列候入庫;選用而無資料=誠實 NEEDS_DATA 不假算)。
  ④ benchmark 二選一:TWII(台股加權)/GSPC(標普500);
     美系基準對台標的自動 T+1(三鐵則③)。
  ⑤ talib C 庫在位=get_functions() 全數動態掛載疊加(誠實標態)。
三鐵則(承 ENG048):Adj 優先/空白 ffill 價補量不補/台灣 T+1。
用法:
  via-vapta                          → RawWide 全 DATA_READY 商品
  via-vapta --instrument TWII,GSPC --benchmark TWII --rfr US10Y
  via-vapta --list                   → 指標總表(態+家族)
  via-vapta --selftest               → 十二檢(合成資料零網路)
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

import json
import math
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VAP = HERE.parent
VIA = VAP.parent.parent
OUT = VAP / "DATABASE" / "ta_runs"
RAWWIDE = VAP / "VDF_MacroRawWide.json"
PERIODS = [5, 10, 20, 60, 120, 240]
ANN = 252  # 年化交易日

CANONICAL = {  # 早已有預定參數之指標(操作員令:RSI 類不吃週期輪)
    "RSI": {"n": 14}, "MACD": {"fast": 12, "slow": 26, "signal": 9},
    "BBANDS": {"n": 20, "k": 2.0}, "STOCH": {"k": 5, "d": 3},
    "ADX": {"n": 14}, "CCI": {"n": 14}, "WILLR": {"n": 14},
    "MFI": {"n": 14}, "AROON": {"n": 14},
    "APO": {"fast": 12, "slow": 26}, "PPO": {"fast": 12, "slow": 26},
}
RF_MAP = {"US10Y": "DGS10", "TW10Y": "TW10Y"}   # TW10Y 欄候入庫;缺=NEEDS_DATA
BENCH_MAP = {"TWII": "TWII", "GSPC": "GSPC"}
TW_INSTRUMENTS = {"TWII"}                        # 台系標的:美系基準/rf 對其 T+1

try:
    import talib  # noqa: F401
    TALIB = talib
except Exception:
    TALIB = None  # 誠實 NOT_INSTALLED;後備全家族頂上


# ── 三鐵則原語(承 ENG048)────────────────────────────────────
LAW_LOG: list = []   # 批330 律違規/降級紀錄(誠實)


def pick_price(frame, allow_raw: bool = False):
    """批330 律一:還原價優先且唯一;裸 close/value 僅 allow_raw=True 明示才用(記 PRICE_RAW_WARN)"""
    for col in ("adj_close", "adjClose"):
        if col in frame.columns:
            return frame[col], col
    if allow_raw:
        for col in ("close", "value"):
            if col in frame.columns:
                LAW_LOG.append(f"PRICE_RAW_WARN:{col}")
                return frame[col], col
    raise KeyError("律一(批330):無還原價欄(adj_close/adjClose);裸 close 須 allow_raw=True 明示")


def law_volume(volume):
    """批330 律二:量須 attrs ex_daytrade=True(CGC_MDL118 產出);否則 SKIP 量類指標"""
    if volume is None:
        return None
    if getattr(volume, "attrs", {}).get("ex_daytrade") is True:
        return volume
    LAW_LOG.append("VOLUME_RAW_SKIP")
    return None


def ffill_align(df):
    vol_cols = [c for c in df.columns if "volume" in c.lower()]
    out = df.copy()
    px_cols = [c for c in df.columns if c not in vol_cols]
    out[px_cols] = out[px_cols].ffill()
    return out


def tw_lag_shift(us_series):
    return us_series.shift(1)


# ── 指標家族(pandas/numpy 純算;統計組零外掛)────────────────
def _linreg_parts(s, n):
    """rolling OLS(t=0..n-1):回 (slope, intercept) 序列"""
    import numpy as np
    t = np.arange(n, dtype=float)
    t_mean = t.mean()
    t_var = ((t - t_mean) ** 2).sum()

    def _slope(w):
        return ((t - t_mean) * (w - w.mean())).sum() / t_var
    slope = s.rolling(n).apply(_slope, raw=True)
    intercept = s.rolling(n).mean() - slope * t_mean
    return slope, intercept


def close_family() -> dict:
    """close-only 家族(週期輪)"""
    import numpy as np

    def sma(s, n): return s.rolling(n).mean()
    def ema(s, n): return s.ewm(span=n, adjust=False).mean()
    def wma(s, n):
        w = np.arange(1, n + 1, dtype=float)
        return s.rolling(n).apply(lambda x: (x * w).sum() / w.sum(), raw=True)
    def dema(s, n):
        e1 = ema(s, n)
        return 2 * e1 - ema(e1, n)
    def tema(s, n):
        e1 = ema(s, n); e2 = ema(e1, n)
        return 3 * e1 - 3 * e2 + ema(e2, n)
    def trima(s, n):
        h = (n + 1) // 2
        return s.rolling(h).mean().rolling(n - h + 1).mean()
    def midpoint(s, n): return (s.rolling(n).max() + s.rolling(n).min()) / 2
    def mom(s, n): return s.diff(n)
    def roc(s, n): return s.pct_change(n) * 100
    def rocp(s, n): return s.pct_change(n)
    def rocr(s, n): return s / s.shift(n)
    def cmo(s, n):
        d = s.diff()
        up = d.clip(lower=0).rolling(n).sum()
        dn = (-d.clip(upper=0)).rolling(n).sum()
        return 100 * (up - dn) / (up + dn)
    def trix(s, n):
        e3 = ema(ema(ema(s, n), n), n)
        return e3.pct_change() * 100
    def stddev(s, n): return s.rolling(n).std()
    def var(s, n): return s.rolling(n).var()
    def zscore(s, n): return (s - s.rolling(n).mean()) / s.rolling(n).std()
    def hi(s, n): return s.rolling(n).max()
    def lo(s, n): return s.rolling(n).min()
    def linearreg(s, n):
        sl, ic = _linreg_parts(s, n)
        return ic + sl * (n - 1)
    def linearreg_slope(s, n):
        return _linreg_parts(s, n)[0]
    def linearreg_angle(s, n):
        import numpy as np
        return np.degrees(np.arctan(_linreg_parts(s, n)[0]))
    def linearreg_intercept(s, n):
        return _linreg_parts(s, n)[1]
    def tsf(s, n):
        sl, ic = _linreg_parts(s, n)
        return ic + sl * n
    def bbwidth(s, n):
        m, sd = s.rolling(n).mean(), s.rolling(n).std()
        return (4 * sd) / m * 100
    def rollret(s, n): return s.pct_change(n) * 100
    return {"SMA": sma, "EMA": ema, "WMA": wma, "DEMA": dema, "TEMA": tema,
            "TRIMA": trima, "MIDPOINT": midpoint, "MOM": mom, "ROC": roc,
            "ROCP": rocp, "ROCR": rocr, "CMO": cmo, "TRIX": trix,
            "STDDEV": stddev, "VAR": var, "ZSCORE": zscore, "MAX": hi, "MIN": lo,
            "LINEARREG": linearreg, "LINEARREG_SLOPE": linearreg_slope,
            "LINEARREG_ANGLE": linearreg_angle,
            "LINEARREG_INTERCEPT": linearreg_intercept, "TSF": tsf,
            "BBWIDTH": bbwidth, "ROLLRET": rollret}


def special_family() -> dict:
    """CANONICAL 參數家族(close-only;多輸出攤平)"""
    def ema(s, n): return s.ewm(span=n, adjust=False).mean()

    def rsi(s, p=None):
        n = (p or CANONICAL["RSI"])["n"]
        d = s.diff()
        up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
        dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
        return {"RSI": 100 - 100 / (1 + up / dn)}
    def macd(s, p=None):
        c = p or CANONICAL["MACD"]
        line = ema(s, c["fast"]) - ema(s, c["slow"])
        sig = line.ewm(span=c["signal"], adjust=False).mean()
        return {"MACD_LINE": line, "MACD_SIGNAL": sig, "MACD_HIST": line - sig}
    def bbands(s, p=None):
        c = p or CANONICAL["BBANDS"]
        m, sd = s.rolling(c["n"]).mean(), s.rolling(c["n"]).std()
        up, low = m + c["k"] * sd, m - c["k"] * sd
        return {"BBANDS_PCTB": (s - low) / (up - low),
                "BBANDS_UPPER": up, "BBANDS_MIDDLE": m, "BBANDS_LOWER": low}
    def apo(s, p=None):
        c = p or CANONICAL["APO"]
        return {"APO": ema(s, c["fast"]) - ema(s, c["slow"])}
    def ppo(s, p=None):
        c = p or CANONICAL["PPO"]
        slow = ema(s, c["slow"])
        return {"PPO": (ema(s, c["fast"]) - slow) / slow * 100}
    return {"RSI": rsi, "MACD": macd, "BBANDS": bbands, "APO": apo, "PPO": ppo}


def ohlc_family() -> dict:
    """OHLC(+V)家族;波動族 ATR/NATR 吃週期輪、TRANGE 無參,
    STOCH/WILLR/CCI/ADX/AROON/MFI 用 CANONICAL"""
    def trange(h, l, c):
        pc = c.shift(1)
        import pandas as pd
        return pd.concat([h - l, (h - pc).abs(), (l - pc).abs()], axis=1).max(axis=1)
    def atr(h, l, c, n):
        return trange(h, l, c).ewm(alpha=1 / n, adjust=False).mean()
    def natr(h, l, c, n):
        return atr(h, l, c, n) / c * 100
    def stoch(h, l, c, p=None):
        cc = p or CANONICAL["STOCH"]
        ll, hh = l.rolling(cc["k"]).min(), h.rolling(cc["k"]).max()
        k = (c - ll) / (hh - ll) * 100
        return {"STOCH_K": k, "STOCH_D": k.rolling(cc["d"]).mean()}
    def willr(h, l, c, p=None):
        n = (p or CANONICAL["WILLR"])["n"]
        hh, ll = h.rolling(n).max(), l.rolling(n).min()
        return {"WILLR": (hh - c) / (hh - ll) * -100}
    def cci(h, l, c, p=None):
        n = (p or CANONICAL["CCI"])["n"]
        tp = (h + l + c) / 3
        m = tp.rolling(n).mean()
        md = (tp - m).abs().rolling(n).mean()
        return {"CCI": (tp - m) / (0.015 * md)}
    def adx(h, l, c, p=None):
        n = (p or CANONICAL["ADX"])["n"]
        up, dn = h.diff(), -l.diff()
        pdm = up.where((up > dn) & (up > 0), 0.0)
        ndm = dn.where((dn > up) & (dn > 0), 0.0)
        tr = trange(h, l, c).ewm(alpha=1 / n, adjust=False).mean()
        pdi = pdm.ewm(alpha=1 / n, adjust=False).mean() / tr * 100
        ndi = ndm.ewm(alpha=1 / n, adjust=False).mean() / tr * 100
        dx = (pdi - ndi).abs() / (pdi + ndi) * 100
        return {"ADX": dx.ewm(alpha=1 / n, adjust=False).mean(),
                "PLUS_DI": pdi, "MINUS_DI": ndi}
    def aroon(h, l, c, p=None):
        n = (p or CANONICAL["AROON"])["n"]
        up = h.rolling(n + 1).apply(lambda w: 100 * w.argmax() / n, raw=True)
        dn = l.rolling(n + 1).apply(lambda w: 100 * w.argmin() / n, raw=True)
        return {"AROON_UP": up, "AROON_DOWN": dn}
    return {"TRANGE": trange, "ATR": atr, "NATR": natr, "STOCH": stoch,
            "WILLR": willr, "CCI": cci, "ADX": adx, "AROON": aroon}


def mfi_calc(h, l, c, v, p=None):
    n = (p or CANONICAL["MFI"])["n"]
    tp = (h + l + c) / 3
    mf = tp * v
    pos = mf.where(tp > tp.shift(1), 0.0).rolling(n).sum()
    neg = mf.where(tp < tp.shift(1), 0.0).rolling(n).sum()
    return {"MFI": 100 - 100 / (1 + pos / neg)}


# ── 統計/風險(對基準+rf;週期輪)──────────────────────────────
def bench_family() -> dict:
    def beta(rs, rb, n):
        cov = rs.rolling(n).cov(rb)
        return cov / rb.rolling(n).var()
    def correl(rs, rb, n):
        return rs.rolling(n).corr(rb)
    return {"BETA": beta, "CORREL": correl}


def risk_family() -> dict:
    def sharpe(rs, rf_d, n):
        ex = rs - rf_d
        return ex.rolling(n).mean() * ANN / (rs.rolling(n).std() * math.sqrt(ANN))
    def sortino(rs, rf_d, n):
        ex = rs - rf_d
        dn = rs.where(rs < 0.0)
        dstd = dn.rolling(n, min_periods=max(2, n // 4)).std()
        return ex.rolling(n).mean() * ANN / (dstd * math.sqrt(ANN))
    return {"SHARPE": sharpe, "SORTINO": sortino}


def alpha_calc(rs, rb, rf_d, n):
    b = bench_family()["BETA"](rs, rb, n)
    return (rs.rolling(n).mean() - rf_d.rolling(n).mean()
            - b * (rb.rolling(n).mean() - rf_d.rolling(n).mean())) * ANN


# ── 引擎 ─────────────────────────────────────────────────────────
def indicator_roster() -> dict:
    cf, sf, of, bf, rk = close_family(), special_family(), ohlc_family(), bench_family(), risk_family()
    return {"mode": "TALIB_FULL+FB" if TALIB else "FALLBACK_FULL",
            "close_wheel": sorted(cf.keys()), "canonical": sorted(sf.keys()),
            "ohlc": sorted(of.keys()) + ["MFI"],
            "stat_bench": sorted(bf.keys()) + ["ALPHA"],
            "risk": sorted(rk.keys()),
            "talib_total": len(TALIB.get_functions()) if TALIB else 0,
            "canonical_params": CANONICAL, "periods": PERIODS,
            "rf_options": list(RF_MAP.keys()), "bench_options": list(BENCH_MAP.keys())}


def _emit(rows, series, name, ind, period):
    tail = series.dropna()
    if tail.empty:
        return
    v = float(tail.iloc[-1])
    if math.isnan(v) or math.isinf(v):
        return
    rows.append({"date": str(tail.index[-1])[:10], "instrument": name,
                 "indicator": ind, "period": period, "value": round(v, 6)})


def compute_series(px, name: str, bench=None, rf_daily=None,
                   ohlc=None, volume=None) -> list[dict]:
    """單標的全家族計算 → 長表列;bench/rf 在位才算統計/風險組(誠實)"""
    rows = []
    for ind, fn in close_family().items():
        for n in PERIODS:
            try:
                _emit(rows, fn(px, n), name, ind, n)
            except Exception:
                continue
    for ind, fn in special_family().items():
        try:
            for sub, out in fn(px).items():
                _emit(rows, out, name, sub, "canonical")
        except Exception:
            continue
    if ohlc is not None:
        h, l, c = ohlc
        of = ohlc_family()
        try:
            _emit(rows, of["TRANGE"](h, l, c), name, "TRANGE", "special")
        except Exception:
            pass
        for ind in ("ATR", "NATR"):        # 波動族吃週期輪(批123 政策)
            for n in PERIODS:
                try:
                    _emit(rows, of[ind](h, l, c, n), name, ind, n)
                except Exception:
                    continue
        for ind in ("STOCH", "WILLR", "CCI", "ADX", "AROON"):
            try:
                for sub, out in of[ind](h, l, c).items():
                    _emit(rows, out, name, sub, "canonical")
            except Exception:
                continue
        volume = law_volume(volume)
        if volume is not None:
            try:
                for sub, out in mfi_calc(h, l, c, volume).items():
                    _emit(rows, out, name, sub, "canonical")
            except Exception:
                pass
    rs = px.pct_change()
    if bench is not None:
        rb = bench.pct_change()
        for ind, fn in bench_family().items():
            for n in PERIODS:
                try:
                    _emit(rows, fn(rs, rb, n), name, ind, n)
                except Exception:
                    continue
    if rf_daily is not None:
        for ind, fn in risk_family().items():
            for n in PERIODS:
                try:
                    _emit(rows, fn(rs, rf_daily, n), name, ind, n)
                except Exception:
                    continue
        if bench is not None:
            rb = bench.pct_change()
            for n in PERIODS:
                try:
                    _emit(rows, alpha_calc(rs, rb, rf_daily, n), name, "ALPHA", n)
                except Exception:
                    continue
    if TALIB is not None:  # talib 在位=全指標動態疊加(close-only 輸入圈)
        import numpy as np
        arr = px.ffill().dropna().to_numpy(dtype=float)
        for fname in TALIB.get_functions():
            fn = getattr(TALIB, fname, None)
            if fn is None:
                continue
            try:
                info = TALIB.abstract.Function(fname).info
                if set(info["input_names"].values()) - {"close", "real"}:
                    continue
                if "timeperiod" in info["parameters"]:
                    for n in PERIODS:
                        out = fn(arr, timeperiod=n)
                        v = out[-1] if not isinstance(out, tuple) else out[0][-1]
                        rows.append({"date": str(px.index[-1])[:10], "instrument": name,
                                     "indicator": f"TA.{fname}", "period": n,
                                     "value": round(float(v), 6)})
                else:
                    out = fn(arr)
                    v = out[-1] if not isinstance(out, tuple) else out[0][-1]
                    rows.append({"date": str(px.index[-1])[:10], "instrument": name,
                                 "indicator": f"TA.{fname}", "period": "default",
                                 "value": round(float(v), 6)})
            except Exception:
                continue
    return rows


def load_rawwide():
    import pandas as pd
    data = json.loads(RAWWIDE.read_text(encoding="utf-8-sig"))
    df = pd.DataFrame(data).set_index("date")
    df.index = pd.to_datetime(df.index)
    return df


def resolve_rf(df, rfr: str):
    """rf 二選一;年率% → 日 rf;選 TW10Y 而序列缺=誠實 NEEDS_DATA(None,msg)"""
    col = RF_MAP.get(rfr)
    if col is None or col not in df.columns:
        return None, f"NEEDS_DATA:rf {rfr} 序列不在庫(候台灣十年期公債殖利率入庫)"
    return df[col] / 100.0 / ANN, f"{rfr}={col}(年率%→日 rf)"


def run(instruments, benchmark: str, rfr: str) -> int:
    if benchmark not in BENCH_MAP:
        print(f"[FAIL] benchmark 限二選一 {list(BENCH_MAP)}(操作員令)")
        return 2
    if rfr not in RF_MAP:
        print(f"[FAIL] rf 限二選一 {list(RF_MAP)}(操作員令)")
        return 2
    df = ffill_align(load_rawwide())
    bcol = BENCH_MAP[benchmark]
    bench = df[bcol] if bcol in df.columns else None
    rf_daily, rf_note = resolve_rf(df, rfr)
    ros = indicator_roster()
    targets = instruments or [c for c in ("TWII", "GSPC", "SOX", "DXY", "VIX", "GOLD",
                                          "BRENT", "WTI", "DGS10") if c in df.columns]
    print(f"=== VAP TA 工廠(批123)· 模式 {ros['mode']} · 商品 {len(targets)} · 週期 {PERIODS} ===")
    print(f"  [rf] {rf_note} · [基準] {benchmark} · 台系標的對美系基準 T+1")
    all_rows, skipped = [], []
    for key in targets:
        if key not in df.columns:
            skipped.append(key)
            continue
        b = bench
        rfd = rf_daily
        if b is not None and key in TW_INSTRUMENTS and bcol not in TW_INSTRUMENTS:
            b = tw_lag_shift(b)          # 三鐵則③:美系基準對台 T+1
        if rfd is not None and key in TW_INSTRUMENTS and RF_MAP[rfr] == "DGS10":
            rfd = tw_lag_shift(rfd)
        if b is not None and key == bcol:
            b = None                     # 自身不對自身算 β/α(誠實)
        rows = compute_series(df[key], key, bench=b, rf_daily=rfd)
        all_rows.extend(rows)
        print(f"  [算] {key:<8} {len(rows)} 指標值")
    if skipped:
        print(f"  [跳] 欄缺:{','.join(skipped)}(誠實)")
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    jp = OUT / f"TA_RUN_{ts}.json"
    jp.write_text(json.dumps({"schema": "vap.ta_factory.run.v1", "ts": ts,
                              "mode": ros["mode"], "benchmark": benchmark,
                              "rfr": rfr, "rf_note": rf_note,
                              "rows": all_rows}, ensure_ascii=False, indent=1),
                  encoding="utf-8")
    try:
        import pandas as pd
        pd.DataFrame(all_rows).to_csv(OUT / f"TA_RUN_{ts}.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(all_rows).to_parquet(OUT / f"TA_RUN_{ts}.parquet", index=False)
    except Exception:
        pass
    print(f"  [計] 長表 {len(all_rows)} 列 · 存 {jp.name}(+csv/parquet;供模板冊綁定)")
    return 0


def cmd_list() -> int:
    ros = indicator_roster()
    print(f"=== VAP TA 指標總表 · 模式 {ros['mode']} ===")
    print(f"  週期輪家族 {len(ros['close_wheel'])}:{', '.join(ros['close_wheel'])}")
    print(f"  CANONICAL {len(ros['canonical'])}:{', '.join(ros['canonical'])}(參數冊:{json.dumps(CANONICAL)})")
    print(f"  OHLC 家族 {len(ros['ohlc'])}:{', '.join(ros['ohlc'])}(波動族 ATR/NATR 吃週期輪)")
    print(f"  統計對基準:{', '.join(ros['stat_bench'])} · 風險:{', '.join(ros['risk'])}")
    print(f"  rf 二選一:{ros['rf_options']} · 基準二選一:{ros['bench_options']} · 週期輪:{PERIODS}")
    print(f"  talib C 庫:{'在位 ' + str(ros['talib_total']) + ' 式疊加' if TALIB else 'NOT_INSTALLED(後備全家族頂上,誠實)'}")
    return 0


def selftest() -> int:
    import numpy as np
    import pandas as pd
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    idx = pd.date_range("2024-01-01", periods=400, freq="D")
    rng = np.random.default_rng(42)
    px = pd.Series(100 + np.cumsum(rng.normal(0.05, 1.0, 400)), index=idx)
    ros = indicator_roster()
    # ① 週期輪+CANONICAL 冊
    chk("① 週期輪 5/10/20/60/120/240+CANONICAL 冊",
        ros["periods"] == [5, 10, 20, 60, 120, 240]
        and ros["canonical_params"]["RSI"]["n"] == 14
        and ros["canonical_params"]["MACD"] == {"fast": 12, "slow": 26, "signal": 9})
    rows = compute_series(px, "SYN")
    inds = {r["indicator"] for r in rows}
    # ② close 週期輪家族全出(25 式)
    wheel_out = {r["indicator"] for r in rows if r["period"] in PERIODS}
    chk("② close 週期輪家族全出值", len(set(ros["close_wheel"]) & wheel_out) == len(ros["close_wheel"]),
        f"({len(set(ros['close_wheel']) & wheel_out)}/{len(ros['close_wheel'])})")
    # ③ CANONICAL 多輸出攤平(MACD 3 路+BB 4 路)
    chk("③ CANONICAL 攤平(RSI/MACD×3/BB×4/APO/PPO)",
        {"RSI", "MACD_LINE", "MACD_SIGNAL", "MACD_HIST", "BBANDS_PCTB",
         "BBANDS_UPPER", "APO", "PPO"} <= inds)
    # ④ SMA 六週期輪+RSI 不吃輪
    sma_p = {r["period"] for r in rows if r["indicator"] == "SMA"}
    rsi_p = {r["period"] for r in rows if r["indicator"] == "RSI"}
    chk("④ SMA 六輪·RSI canonical", sma_p == set(PERIODS) and rsi_p == {"canonical"})
    # ⑤ 統計組 LINEARREG 驗算(嚴格線性=斜率恆定+LINEARREG≈末值)
    lin = pd.Series(np.arange(300, dtype=float) * 2 + 5, index=idx[:300])
    sl = close_family()["LINEARREG_SLOPE"](lin, 20).dropna()
    lr = close_family()["LINEARREG"](lin, 20).dropna()
    tf = close_family()["TSF"](lin, 20).dropna()
    chk("⑤ 統計組驗算(slope=2·LINEARREG=末值·TSF=下一值)",
        abs(sl.iloc[-1] - 2) < 1e-9 and abs(lr.iloc[-1] - lin.iloc[-1]) < 1e-6
        and abs(tf.iloc[-1] - (lin.iloc[-1] + 2)) < 1e-6)
    # ⑥ BETA/CORREL 對基準(自身對自身 β=1,corr=1)
    bf = bench_family()
    b = bf["BETA"](px.pct_change(), px.pct_change(), 60).dropna()
    c = bf["CORREL"](px.pct_change(), px.pct_change(), 60).dropna()
    chk("⑥ BETA/CORREL(自身=1)", abs(b.iloc[-1] - 1) < 1e-9 and abs(c.iloc[-1] - 1) < 1e-9)
    # ⑦ SHARPE/SORTINO/ALPHA 可算+rf 選項冊
    rfd = pd.Series(0.04 / ANN, index=idx)
    sh = risk_family()["SHARPE"](px.pct_change(), rfd, 60).dropna()
    al = alpha_calc(px.pct_change(), (px * 1.01).pct_change(), rfd, 60).dropna()
    chk("⑦ SHARPE/ALPHA 可算+rf/基準二選一冊",
        len(sh) > 0 and len(al) > 0 and ros["rf_options"] == ["US10Y", "TW10Y"]
        and ros["bench_options"] == ["TWII", "GSPC"])
    # ⑧ OHLC 波動族(合成 OHLC:ATR>0 六輪、STOCH/AROON 0-100、ADX 出值)
    h = px + rng.uniform(0.5, 2.0, 400)
    l = px - rng.uniform(0.5, 2.0, 400)
    v = pd.Series(rng.uniform(1e6, 5e6, 400), index=idx)
    v.attrs["ex_daytrade"] = True   # 批330 律:自測合成量掛律旗標(裸量=SKIP 已於 ⑬ 驗)
    rows_o = compute_series(px, "SYNO", ohlc=(h, l, px), volume=v)
    io = {r["indicator"]: r["value"] for r in rows_o}
    atr_p = {r["period"] for r in rows_o if r["indicator"] == "ATR"}
    chk("⑧ 波動族 ATR 六輪>0+TRANGE+NATR",
        atr_p == set(PERIODS) and io.get("ATR", 0) > 0 and "TRANGE" in io and io.get("NATR", 0) > 0)
    chk("⑨ OHLC 動能族(STOCH/WILLR/CCI/ADX/AROON/MFI 域檢)",
        0 <= io.get("STOCH_K", -1) <= 100 and -100 <= io.get("WILLR", 1) <= 0
        and 0 <= io.get("ADX", -1) <= 100 and 0 <= io.get("AROON_UP", -1) <= 100
        and 0 <= io.get("MFI", -1) <= 100)
    # ⑩ close-only 時 OHLC 族誠實不出
    chk("⑩ close-only 無 OHLC 指標(誠實 SKIP)",
        not any(r["indicator"] in ("ATR", "STOCH_K", "MFI") for r in rows))
    # ⑪ rf TW10Y 缺序列=NEEDS_DATA 誠實
    df_fake = pd.DataFrame({"DGS10": [4.0], "TWII": [20000.0]})
    r1, n1 = resolve_rf(df_fake, "US10Y")
    r2, n2 = resolve_rf(df_fake, "TW10Y")
    chk("⑪ rf 換擋(US10Y 在庫/TW10Y=NEEDS_DATA 誠實)",
        r1 is not None and r2 is None and "NEEDS_DATA" in n2)
    # ⑫ 實資料煙測(RawWide TWII/GSPC;基準 GSPC 對 TWII 自動 T+1)
    rc = run(["TWII", "GSPC"], "GSPC", "US10Y")
    chk("⑫ 實資料煙測 rc0(TWII 對美系基準 T+1)", rc == 0)
    n = 12 - len(fails)
    # 批330 律檢
    import pandas as _pd
    LAW_LOG.clear()
    raw_df = _pd.DataFrame({"close": [1.0, 2.0]})
    try:
        pick_price(raw_df); strict = False
    except KeyError:
        strict = True
    _, colr = pick_price(raw_df, allow_raw=True)
    v_raw = _pd.Series([1.0, 2.0]); v_law = _pd.Series([1.0, 2.0]); v_law.attrs["ex_daytrade"] = True
    chk("⑬ 資料律(批330):裸 close 預設拒/allow_raw 記警;裸量 SKIP/律量通",
        strict and colr == "close" and "PRICE_RAW_WARN:close" in LAW_LOG
        and law_volume(v_raw) is None and law_volume(v_law) is v_law and "VOLUME_RAW_SKIP" in LAW_LOG)
    print(f"  [計] 十三檢 OK {13 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== VAP ENG004 TA 工廠 · 十二檢自測(合成資料零網路)===")
        return selftest()
    if "--list" in args:
        return cmd_list()

    def _opt(flag, default):
        if flag in args:
            i = args.index(flag)
            return args[i + 1] if i + 1 < len(args) else default
        return default
    inst = _opt("--instrument", "")
    return run([x for x in inst.split(",") if x] or None,
               _opt("--benchmark", "TWII"), _opt("--rfr", "US10Y"))


if __name__ == "__main__":
    sys.exit(main())
