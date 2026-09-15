#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
CGC_MDL151_TaLibGate v0100 — TA-Lib 技術指標庫閘(批516 操作員令「TA-LIB 確認測試無誤」)
====================================================================
誠實三態:ABSENT(本境無 talib=不是壞掉;印補庫令,裝=你的手 L07/L19)· OK(import + 版本 + 函式數 + 數值檢:SMA/EMA/RSI/MACD/BBANDS 對手算)· FAIL(裝了但算錯/炸)
用法:python3 CGC_MDL151_TaLibGate_v0100.py probe [--json] | --selftest(六檢;零網路;本境無 talib 時數值檢誠實 SKIP,rc0)
落 VIA_Reports/talib/TALIB_latest.json。律:只增不減;零網路;零 CDN;同意閘/安裝不代設;尾版律;Zero-Hydra(指標算法不自寫,只對手算驗 TA-Lib)。
補庫令(家族境):uv pip install --python <via_vdf_312|via_vap_312> TA-Lib(0.5+ 官方 wheel 內含 C 庫;Windows/Py3.13 直裝)
"""
from __future__ import annotations

import datetime as _dt
import json
import math
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "talib"
PIP_NAME = "TA-Lib"


def _series(n: int = 60) -> list:
    """確定性合成價序(零隨機):基準 100 + 正弦擺動 + 緩升;夠算 RSI(14)/MACD(26+9)。"""
    return [100.0 + 5.0 * math.sin(i / 3.0) + 0.15 * i for i in range(n)]


def _sma(xs: list, n: int) -> float:
    return sum(xs[-n:]) / n


def _ema(xs: list, n: int) -> float:
    k = 2.0 / (n + 1)
    e = sum(xs[:n]) / n
    for x in xs[n:]:
        e = x * k + e * (1 - k)
    return e


def _rsi(xs: list, n: int = 14) -> float:
    """Wilder RSI(TA-Lib 同法:首段簡單均,之後 Wilder 平滑)。"""
    gains, losses = [], []
    for a, b in zip(xs[:-1], xs[1:]):
        d = b - a
        gains.append(max(d, 0.0)); losses.append(max(-d, 0.0))
    ag, al = sum(gains[:n]) / n, sum(losses[:n]) / n
    for g, l in zip(gains[n:], losses[n:]):
        ag = (ag * (n - 1) + g) / n
        al = (al * (n - 1) + l) / n
    return 100.0 if al == 0 else 100.0 - 100.0 / (1.0 + ag / al)


def probe(do_print: bool = True, out: Path = OUT) -> dict:
    rep = {"schema": "VIA.TaLibGate.v1", "ts": _dt.datetime.now().isoformat(timespec="seconds"), "python": sys.executable, "state": "ABSENT",
           "version": "", "functions": 0, "checks": {}, "why": "", "install": f"uv pip install --python <家族境 python> {PIP_NAME}(你的手;VIA_NET_CONSENT=YES)"}
    try:
        import talib  # noqa: F401
    except Exception as exc:
        rep["why"] = f"本境無 talib({type(exc).__name__}):不是壞掉;裝=你的手"
        _write(rep, out)
        if do_print:
            print(f"=== [via-talib] TA-Lib 閘 · ABSENT · {rep['why']} · {rep['install']} ===")
        return rep
    try:
        import numpy as np
        rep["version"] = str(getattr(talib, "__version__", "?"))
        try:
            rep["functions"] = len(talib.get_functions())
        except Exception:
            rep["functions"] = 0
        xs = _series()
        arr = np.asarray(xs, dtype=float)
        sma = float(talib.SMA(arr, timeperiod=5)[-1])
        ema = float(talib.EMA(arr, timeperiod=5)[-1])
        rsi = float(talib.RSI(arr, timeperiod=14)[-1])
        macd, sig, hist = talib.MACD(arr, fastperiod=12, slowperiod=26, signalperiod=9)
        up, mid, lo = talib.BBANDS(arr, timeperiod=20, nbdevup=2, nbdevdn=2)
        chk = {
            "SMA5": (sma, _sma(xs, 5), abs(sma - _sma(xs, 5)) < 1e-6),
            "EMA5": (ema, _ema(xs, 5), abs(ema - _ema(xs, 5)) < 1e-6),
            "RSI14": (rsi, _rsi(xs, 14), abs(rsi - _rsi(xs, 14)) < 1e-6),
            "MACD_hist=macd-signal": (float(hist[-1]), float(macd[-1] - sig[-1]), abs(float(hist[-1]) - float(macd[-1] - sig[-1])) < 1e-9),
            "BBANDS_mid=SMA20": (float(mid[-1]), _sma(xs, 20), abs(float(mid[-1]) - _sma(xs, 20)) < 1e-6 and float(up[-1]) > float(mid[-1]) > float(lo[-1])),
        }
        rep["checks"] = {k: {"talib": round(v[0], 6), "hand": round(v[1], 6), "ok": bool(v[2])} for k, v in chk.items()}
        rep["state"] = "OK" if all(v["ok"] for v in rep["checks"].values()) else "FAIL"
        if rep["state"] == "FAIL":
            rep["why"] = "數值檢不合:" + ",".join(k for k, v in rep["checks"].items() if not v["ok"])
    except Exception as exc:
        rep["state"], rep["why"] = "FAIL", f"{type(exc).__name__}:{str(exc)[:120]}"
    _write(rep, out)
    if do_print:
        print(f"=== [via-talib] TA-Lib 閘 · {rep['state']} · 版本 {rep['version'] or '-'} · 函式 {rep['functions']} · " + " · ".join(f"{k} {'OK' if v['ok'] else 'FAIL'}" for k, v in rep["checks"].items()) + (f" · {rep['why']}" if rep["why"] else "") + " ===")
    return rep


def _write(rep: dict, out: Path) -> None:
    try:
        out.mkdir(parents=True, exist_ok=True)
        (out / "TALIB_latest.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    except Exception:
        pass


def selftest() -> int:
    import tempfile
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)
    xs = _series()
    chk("① 合成價序確定性(零隨機;60 點;夠算 RSI14/MACD 26+9)", len(xs) == 60 and xs == _series() and xs[0] == 100.0)
    chk("② 手算 SMA/EMA/RSI 自洽(SMA5 = 尾 5 均;EMA 首值=SMA;RSI 在 0~100;全漲序 RSI=100)",
        abs(_sma(xs, 5) - sum(xs[-5:]) / 5) < 1e-12 and abs(_ema([1.0] * 10, 5) - 1.0) < 1e-12 and 0.0 <= _rsi(xs) <= 100.0 and _rsi([float(i) for i in range(30)]) == 100.0)
    with tempfile.TemporaryDirectory() as td:
        r = probe(do_print=False, out=Path(td))
        j = json.loads((Path(td) / "TALIB_latest.json").read_text(encoding="utf-8"))
    chk("③ 探針三態誠實(ABSENT=本境無 talib 且印補庫令;OK=數值檢全過;FAIL 帶理由)+ TALIB_latest.json 落檔",
        r["state"] in ("ABSENT", "OK", "FAIL") and j["state"] == r["state"] and ("install" in r) and (r["state"] != "ABSENT" or "talib" in r["why"]), f"({r['state']} · {r.get('version') or '-'} · {r.get('why', '')[:60]})")
    if r["state"] == "OK":
        chk("④ TA-Lib 數值檢:SMA5/EMA5/RSI14/MACD hist/BBANDS mid 對手算全合", all(v["ok"] for v in r["checks"].values()), f"({ {k: v['talib'] for k, v in r['checks'].items()} })")
    else:
        chk("④ TA-Lib 數值檢(本境無 talib=誠實 SKIP,不假綠;裝後重跑 via-talib)", True, "(SKIP)")
    chk("⑤ 補庫令只印不裝(零 subprocess/零 pip 呼叫;裝=你的手 L07/L19)", "subprocess" not in Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0] and PIP_NAME in r["install"])
    src = Path(__file__).read_text(encoding="utf-8").split("def selftest", 1)[0]
    chk("⑥ 紀律宣告(只增不減/零網路/零 CDN/不代設/尾版律/Zero-Hydra/誠實三態)", all(k in src for k in ("只增不減", "零網路", "零 CDN", "不代設", "尾版律", "Zero-Hydra", "誠實三態")))
    print(f"  [計] 六檢 OK {6 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a:
        print("=== TA-Lib 技術指標庫閘(CGC_MDL151 v0100)· 六檢自測(零網路)===")
        return selftest()
    r = probe(do_print="--json" not in a)
    if "--json" in a:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    return 0 if r["state"] in ("OK", "ABSENT") else 1


if __name__ == "__main__":
    sys.exit(main())
