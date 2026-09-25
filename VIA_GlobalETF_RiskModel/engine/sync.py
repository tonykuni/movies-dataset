# -*- coding: utf-8 -*-
"""
sync.py — M25_SyncMatrix：同步性 / 共振 / 領先滯後 / 離散度
=============================================================================
MODULE M25_SyncMatrix
  [MCFL-M25-C25-F251] compute_sync — ETF×因子滾動相關、lead-lag、回撤同步、
                                     橫斷面離散度、PC1 全球共振占比
"""
from __future__ import annotations

import math

from . import mathkit as mk


def _factor_series(panel, spec):
    kind, fid = spec["kind"], spec["id"]
    if kind == "etf_return":
        return panel.logret(fid)
    if kind == "macro_diff":
        s = panel.macro_series(fid)
        return [b - a for a, b in zip(s, s[1:])]
    if kind == "ratio_return":
        a, b = fid.split("/")
        ratio = panel.ratio_series(a, b)
        clean = [(x if x else None) for x in ratio]
        out = []
        for i in range(1, len(clean)):
            if clean[i] and clean[i - 1]:
                out.append(math.log(clean[i] / clean[i - 1]))
            else:
                out.append(0.0)
        return out
    raise ValueError("未知 factor kind: %s" % kind)


def compute_sync(panel, config, uni_meta):
    """[MCFL-M25-C25-F251]"""
    spec = config["def_sync"]
    meta = {u["ticker"]: u for u in uni_meta}
    factors = {name: _factor_series(panel, fs)
               for name, fs in spec["factor_proxies"].items()}
    factor_names = list(spec["factor_proxies"].keys())

    # ETF × 因子 相關矩陣（各窗）
    matrix = {}
    for win in spec["corr_windows"]:
        rows = {}
        for tkr in spec["matrix_tickers"]:
            r = panel.logret(tkr)
            rows[tkr] = {fn: (None if (c := mk.tail_corr(r, factors[fn], win)) is None
                              else round(c, 3))
                         for fn in factor_names}
        matrix[str(win)] = rows

    # 領先滯後：corr(leader[t-k], follower[t])，取 |corr| 最大的 k
    ll_spec = spec["lead_lag"]
    lead_lag = []
    for leader, follower in ll_spec["pairs"]:
        ls = (factors["rates"] if leader == "DGS10" else panel.logret(leader))
        fs = panel.logret(follower)
        best = None
        curve = {}
        for lag in [0] + list(ll_spec["lags"]):
            c = mk.lead_lag_corr(ls, fs, lag, ll_spec["window"])
            curve[str(lag)] = None if c is None else round(c, 3)
            if c is not None and (best is None or abs(c) > abs(best[1])):
                best = (lag, c)
        lead_lag.append({
            "leader": leader, "follower": follower,
            "best_lag": best[0] if best else None,
            "best_corr": round(best[1], 3) if best else None,
            "curve": curve,
            "reading_zh": ("%s 領先 %s %d 日" % (leader, follower, best[0])
                           if best and best[0] > 0 else "同步"),
        })

    # 回撤同步：輪動宇宙中 60 日回撤 ≥ 5% 的名單
    dd_spec = spec["drawdown_sync"]
    rot_tickers = config["def_rotation"]["tickers"]
    dd_hits = []
    for tkr in rot_tickers:
        dd = mk.drawdown_from_high(panel.prices(tkr), dd_spec["lookback_high"])
        if dd is not None and dd >= dd_spec["trigger_drawdown"]:
            dd_hits.append({"ticker": tkr, "name": meta.get(tkr, {}).get("name", tkr),
                            "drawdown": round(dd, 4)})
    dd_hits.sort(key=lambda r: -r["drawdown"])

    # 橫斷面離散度：輪動宇宙 20 日報酬的樣本標準差
    rets20 = [panel.ret(t, spec["dispersion_window"]) for t in rot_tickers]
    disp = mk.dispersion([r for r in rets20 if r is not None])

    # PC1 全球共振占比
    pc1_rets = [panel.logret(t)[-spec["pc1_window"]:]
                for t in spec["pc1_tickers"] if panel.m.prices.get(t)]
    pc1 = mk.pc1_variance_share(pc1_rets)

    return {
        "mcfl": spec.get("mcfl", ""),
        "factor_names": factor_names,
        "factor_labels": {n: fs.get("name_zh", n)
                          for n, fs in spec["factor_proxies"].items()},
        "matrix": matrix,
        "lead_lag": lead_lag,
        "drawdown_sync": {"trigger": dd_spec["trigger_drawdown"],
                          "count": len(dd_hits), "total": len(rot_tickers),
                          "hits": dd_hits},
        "dispersion_20d": None if disp is None else round(disp, 5),
        "pc1_share": None if pc1 is None else round(pc1, 4),
        "evidence": "Est", "truth_tier": "T3",
    }
