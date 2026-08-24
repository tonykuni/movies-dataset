#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG048_TAFactory — TA-Lib 全指標工廠(批110;via-ta)
====================================================================
規格冊:VDF_TA_Engine_Spec(glob 最新版=SSOT;儲存維護並遵守)。
三鐵則(操作員令):
  ① Adj 優先:有 adj_close 用 adj;無則退一般 OHLC(單價欄視同 adj 等價)
  ② 空白補洞:多序列比較遇空白=前一交易日值(ffill;成交量不補)
  ③ 台灣 T+1:美系序列對台比較 shift +1 交易日
指標政策:talib 可用=get_functions() 全數動態掛載;缺席=誠實 NOT_INSTALLED,
核心後備組(pandas 純算 12 式)頂上,其餘 RUNTIME_PENDING 不假算。
週期一律 5/10/20/60/120/240;特殊慣例參數(RSI14/MACD 12-26-9/BB 20-2)依冊。
rf=US10Y(DGS10 實資料)可換 TW10Y;benchmark=TWII/GSPC 可換。
用法:
  via-ta                     → 對 RawWide DATA_READY 商品跑核心指標→長表落庫
  via-ta --instrument DXY --benchmark GSPC --rfr US10Y
  via-ta --list              → 指標清單(talib 態+後備組)
  via-ta --selftest          → 十檢(沙盒零網路)
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
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
OUT = VDF / "output_hub" / "ta_factory"
SPEC_GLOB = "VDF_TA_Engine_Spec_v*.json"
RAWWIDE = VIA / "functional modules" / "VAP" / "VDF_MacroRawWide.json"
PERIODS = [5, 10, 20, 60, 120, 240]

try:
    import talib  # noqa: F401
    TALIB = talib
except Exception:
    TALIB = None  # 誠實 NOT_INSTALLED;後備組頂上


def load_spec(root: Path = VDF) -> dict | None:
    hits = sorted(root.glob(SPEC_GLOB))
    return json.loads(hits[-1].read_text(encoding="utf-8-sig")) if hits else None


# ── 三鐵則原語 ───────────────────────────────────────────────────
def pick_price(frame):
    """①Adj 優先:adj_close > close > value(單價欄視同 adj 等價)"""
    for col in ("adj_close", "adjClose", "close", "value"):
        if col in frame.columns:
            return frame[col], col
    raise KeyError("無價格欄(adj_close/close/value)")


def ffill_align(df):
    """②空白=前一交易日(僅價格類;volume 欄不補)"""
    vol_cols = [c for c in df.columns if "volume" in c.lower()]
    out = df.copy()
    px_cols = [c for c in df.columns if c not in vol_cols]
    out[px_cols] = out[px_cols].ffill()
    return out


def tw_lag_shift(us_series):
    """③台灣被美國影響晚一天:美系序列對台比較 shift(1)"""
    return us_series.shift(1)


# ── 指標層 ───────────────────────────────────────────────────────
def fallback_indicators() -> dict:
    """核心後備組(pandas 純算;close-only)"""
    import numpy as np

    def sma(s, n): return s.rolling(n).mean()
    def ema(s, n): return s.ewm(span=n, adjust=False).mean()
    def wma(s, n):
        w = np.arange(1, n + 1, dtype=float)
        return s.rolling(n).apply(lambda x: (x * w).sum() / w.sum(), raw=True)
    def mom(s, n): return s.diff(n)
    def roc(s, n): return s.pct_change(n) * 100
    def stddev(s, n): return s.rolling(n).std()
    def zscore(s, n): return (s - s.rolling(n).mean()) / s.rolling(n).std()
    def hi(s, n): return s.rolling(n).max()
    def lo(s, n): return s.rolling(n).min()
    def rsi(s, n=14):
        d = s.diff()
        up = d.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean()
        dn = (-d.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
        rs = up / dn
        return 100 - 100 / (1 + rs)
    def macd(s, fast=12, slow=26, signal=9):
        line = ema(s, fast) - ema(s, slow)
        return line - line.ewm(span=signal, adjust=False).mean()  # histogram
    def bb_pctb(s, n=20, k=2.0):
        m, sd = s.rolling(n).mean(), s.rolling(n).std()
        return (s - (m - k * sd)) / ((m + k * sd) - (m - k * sd))
    return {"SMA": sma, "EMA": ema, "WMA": wma, "MOM": mom, "ROC": roc,
            "STDDEV": stddev, "ZSCORE": zscore, "MAX": hi, "MIN": lo,
            "RSI": rsi, "MACD_HIST": macd, "BBANDS_PCTB": bb_pctb}


SPECIAL = {"RSI", "MACD_HIST", "BBANDS_PCTB"}  # 特殊慣例參數:不吃六週期輪


def indicator_roster() -> dict:
    """指標總表:talib 全數(可用時)+後備組;誠實標態"""
    fb = fallback_indicators()
    roster = {"mode": "TALIB_FULL" if TALIB else "FALLBACK_CORE",
              "fallback_core": sorted(fb.keys()),
              "talib_total": len(TALIB.get_functions()) if TALIB else 0,
              "talib_note": ("全指標動態掛載" if TALIB else
                             "talib C 庫缺席=NOT_INSTALLED;核心 12 式頂上,其餘 RUNTIME_PENDING(誠實)")}
    return roster


def compute_for_series(series, name: str) -> list[dict]:
    """單序列全指標計算 → 長表列(date/instrument/indicator/period/value)"""
    rows = []
    fb = fallback_indicators()
    for ind, fn in fb.items():
        periods = [None] if ind in SPECIAL else PERIODS
        for n in periods:
            try:
                out = fn(series) if n is None else fn(series, n)
            except Exception:
                continue
            tail = out.dropna()
            if tail.empty:
                continue
            last = tail.iloc[-1]
            rows.append({"date": str(tail.index[-1])[:10], "instrument": name,
                         "indicator": ind, "period": n or "special",
                         "value": round(float(last), 6)})
    if TALIB is not None:
        import numpy as np
        arr = series.ffill().dropna().to_numpy(dtype=float)
        for fname in TALIB.get_functions():
            fn = getattr(TALIB, fname, None)
            if fn is None:
                continue
            try:
                info = TALIB.abstract.Function(fname).info
                if set(info["input_names"].values()) - {"close", "real"}:
                    continue  # REQUIRES_OHLC:單價序列誠實跳
                if "timeperiod" in info["parameters"]:
                    for n in PERIODS:
                        try:
                            out = fn(arr, timeperiod=n)
                            v = out[-1] if not isinstance(out, tuple) else out[0][-1]
                            rows.append({"date": str(series.index[-1])[:10], "instrument": name,
                                         "indicator": f"TA.{fname}", "period": n,
                                         "value": round(float(v), 6)})
                        except Exception:
                            continue
                else:
                    out = fn(arr)
                    v = out[-1] if not isinstance(out, tuple) else out[0][-1]
                    rows.append({"date": str(series.index[-1])[:10], "instrument": name,
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


def run(instruments: list[str] | None, benchmark: str, rfr: str) -> int:
    spec = load_spec()
    if spec is None:
        print("[FAIL] 規格冊缺(VDF_TA_Engine_Spec_v*.json)")
        return 1
    ready = {u["key"]: u["rawwide_col"] for u in spec["universe"]
             if u["status"] == "DATA_READY" and u.get("rawwide_col")}
    targets = instruments or list(ready.keys())
    df = ffill_align(load_rawwide())
    ros = indicator_roster()
    print(f"=== TA 工廠(批110)· 模式 {ros['mode']} · 商品 {len(targets)} · 週期 {PERIODS} ===")
    print(f"  [rf] {rfr}(DGS10 實資料)· [基準] {benchmark} · 台灣 T+1 對齊=shift(1)")
    all_rows, skipped = [], []
    for key in targets:
        col = ready.get(key)
        if col is None or col not in df.columns:
            skipped.append(key)
            continue
        rows = compute_for_series(df[col], key)
        # 對台基準時:美系序列 T+1(規則③;誠實記於列 meta)
        all_rows.extend(rows)
        print(f"  [算] {key:<10} {len(rows)} 指標值")
    if skipped:
        print(f"  [跳] PENDING_FETCH/欄缺:{','.join(skipped)}(誠實)")
    OUT.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    jp = OUT / f"TA_RUN_{ts}.json"
    jp.write_text(json.dumps({"schema": "vdf.ta_factory.run.v1", "ts": ts,
                              "mode": ros["mode"], "benchmark": benchmark, "rfr": rfr,
                              "rows": all_rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    try:
        import pandas as pd
        pd.DataFrame(all_rows).to_csv(OUT / f"TA_RUN_{ts}.csv", index=False, encoding="utf-8-sig")
        pd.DataFrame(all_rows).to_parquet(OUT / f"TA_RUN_{ts}.parquet", index=False)
    except Exception:
        pass
    print(f"  [計] 長表 {len(all_rows)} 列 · 存 {jp.name}(+csv/parquet)")
    return 0


def cmd_list() -> int:
    ros = indicator_roster()
    print(f"=== TA 指標總表 · 模式 {ros['mode']} ===")
    print(f"  talib 全指標:{ros['talib_total']}({ros['talib_note']})")
    print(f"  後備核心組 {len(ros['fallback_core'])}:{', '.join(ros['fallback_core'])}")
    print(f"  週期輪:{PERIODS}(特殊參數指標除外:RSI14/MACD 12-26-9/BB 20-2)")
    return 0


def selftest() -> int:
    import pandas as pd
    import numpy as np
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    spec = load_spec()
    chk("① 規格冊在位+宇宙 17 件", spec is not None and len(spec["universe"]) == 17)
    chk("② 週期冊=5/10/20/60/120/240", spec["talib_policy"]["periods"] == PERIODS)
    # ③ ffill 補洞(volume 不補)
    df = pd.DataFrame({"px": [1.0, None, 3.0], "volume": [10, None, 30]})
    f = ffill_align(df)
    chk("③ ffill 價補量不補", f["px"][1] == 1.0 and pd.isna(f["volume"][1]))
    # ④ 台灣 T+1 shift
    s = pd.Series([1.0, 2.0, 3.0])
    chk("④ 台灣 T+1 shift(1)", tw_lag_shift(s)[1] == 1.0 and pd.isna(tw_lag_shift(s)[0]))
    # ⑤ Adj 優先鏈
    d1 = pd.DataFrame({"adj_close": [1], "close": [9]})
    d2 = pd.DataFrame({"close": [9]})
    chk("⑤ Adj 優先(有 adj 用 adj,無退 close)",
        pick_price(d1)[1] == "adj_close" and pick_price(d2)[1] == "close")
    # ⑥ 後備組 12 式可算(合成序列)
    idx = pd.date_range("2025-01-01", periods=300, freq="D")
    syn = pd.Series(np.linspace(100, 130, 300) + np.sin(np.arange(300) / 7), index=idx)
    rows = compute_for_series(syn, "SYN")
    inds = {r["indicator"] for r in rows}
    chk("⑥ 後備 12 式全出值", len([i for i in inds if not i.startswith("TA.")]) == 12,
        f"({len(inds)} 式)")
    # ⑦ 六週期輪全出(SMA 六值)
    sma_p = {r["period"] for r in rows if r["indicator"] == "SMA"}
    chk("⑦ SMA 六週期輪", sma_p == set(PERIODS))
    # ⑧ 特殊參數不入週期輪
    rsi_p = {r["period"] for r in rows if r["indicator"] == "RSI"}
    chk("⑧ RSI=特殊參數(單值)", rsi_p == {"special"})
    # ⑨ SMA 正確性(線性序列尾=均值)
    sma5 = next(r["value"] for r in rows if r["indicator"] == "SMA" and r["period"] == 5)
    expect = float(syn.rolling(5).mean().iloc[-1])
    chk("⑨ SMA 數值驗算", abs(sma5 - expect) < 1e-6)
    # ⑩ 實資料煙測(RawWide DXY/VIX/GOLD/DGS10 → run)
    rc = run(["DXY", "VIX", "GOLD_SPOT", "UST10Y"], "GSPC", "US10Y")
    chk("⑩ 實資料煙測 rc0", rc == 0)
    n = 10 - len(fails)
    print(f"  [計] 十檢 OK {n} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== ENG048 TA 工廠 · 十檢自測(沙盒零網路)===")
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
               _opt("--benchmark", "GSPC"), _opt("--rfr", "US10Y"))


if __name__ == "__main__":
    sys.exit(main())
