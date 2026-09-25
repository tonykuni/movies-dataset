# -*- coding: utf-8 -*-
"""
factors.py — M15_FactorPanel：衍生因子面板與指標解析器
=============================================================================
MODULE M15_FactorPanel
  [MCFL-M15-C15-F150] FactorPanel        — 報酬/差分/比值/回撤 快取面板
  [MCFL-M15-C15-F151] resolve_indicator  — 規則指標 id 解析（SSOT 驅動）

指標 id 文法（config def_regimes / def_scores 共用）：
  ret_<k>_<TICKER>      k 日對數報酬                    ret_20_USO
  neg_ret_<k>_<TICKER>  k 日對數報酬取負（弱勢=正值）    neg_ret_20_TLT
  rs_<k>_<TICKER>       相對基準（ACWI）k 日超額報酬     rs_20_QQQ
  rel_<k>_<A>_<B>       A 減 B 的 k 日報酬差            rel_20_HYG_IEF
  chg_<k>_<SERIES>      宏觀水位序列 k 日差分（pp）      chg_20_DGS10
  dd_<k>_<TICKER>       k 窗回撤（正值）                dd_60_EMB
  dd_<k>_<A>_<B>        A/B 比值序列的 k 窗回撤          dd_60_HYG_IEF
  curvechg_<k>          (DGS10-DGS2) 的 k 日差分
  score_<name>          已算出的風險分數（0..100），由呼叫端注入
治理：解析失敗擲 ValueError（SSOT 打錯要炸，不能靜默略過）。
"""
from __future__ import annotations

from . import mathkit as mk


class FactorPanel:
    """[MCFL-M15-C15-F150] 一次建構、全模組共用的衍生因子快取。"""

    def __init__(self, market, benchmark="ACWI"):
        self.m = market
        self.benchmark = benchmark
        self._logret = {}
        self._ratio = {}

    # -- 基礎序列 ----------------------------------------------------------- #
    def prices(self, ticker):
        s = self.m.prices.get(ticker)
        if not s:
            raise ValueError("universe 缺少 ticker: %s" % ticker)
        return s

    def macro_series(self, name):
        s = self.m.macro.get(name)
        if not s:
            raise ValueError("macro 缺少序列: %s" % name)
        return s

    def logret(self, ticker):
        if ticker not in self._logret:
            self._logret[ticker] = mk.log_returns(self.prices(ticker))
        return self._logret[ticker]

    def ratio_series(self, a, b):
        key = (a, b)
        if key not in self._ratio:
            pa, pb = self.prices(a), self.prices(b)
            n = min(len(pa), len(pb))
            self._ratio[key] = [
                (pa[i] / pb[i]) if (pa[i] and pb[i] and pb[i] > 0) else None
                for i in range(n)]
        return self._ratio[key]

    # -- 點值因子（end 可回溯，供 z 歷史 / sparkline 用）--------------------- #
    def ret(self, ticker, k, end=None):
        return mk.window_return(self.prices(ticker), k, end)

    def rs(self, ticker, k, end=None):
        a = self.ret(ticker, k, end)
        b = self.ret(self.benchmark, k, end)
        if a is None or b is None:
            return None
        return a - b

    def rel(self, a, b, k, end=None):
        ra, rb = self.ret(a, k, end), self.ret(b, k, end)
        if ra is None or rb is None:
            return None
        return ra - rb

    def chg(self, series, k, end=None):
        return mk.series_change(self.macro_series(series), k, end)

    def curve_chg(self, k, end=None):
        y10, y2 = self.macro_series("DGS10"), self.macro_series("DGS2")
        n = min(len(y10), len(y2))
        curve = [y10[i] - y2[i] for i in range(n)]
        return mk.series_change(curve, k, end)

    def dd(self, ticker, k, end=None):
        return mk.drawdown_from_high(self.prices(ticker), k, end)

    def dd_ratio(self, a, b, k, end=None):
        return mk.drawdown_from_high(self.ratio_series(a, b), k, end)

    def n_obs(self):
        return len(self.m.dates)


def resolve_indicator(panel, ind_id, end=None, scores=None):
    """[MCFL-M15-C15-F151] 依 SSOT 指標 id 求值；未知文法直接 ValueError。"""
    parts = ind_id.split("_")
    try:
        if parts[0] == "score":
            name = "_".join(parts[1:])
            if scores is None or name not in scores:
                return None
            return scores[name]
        if parts[0] == "neg" and parts[1] == "ret":
            v = panel.ret(parts[3], int(parts[2]), end)
            return None if v is None else -v
        if parts[0] == "ret":
            return panel.ret(parts[2], int(parts[1]), end)
        if parts[0] == "rs":
            return panel.rs(parts[2], int(parts[1]), end)
        if parts[0] == "rel":
            return panel.rel(parts[2], parts[3], int(parts[1]), end)
        if parts[0] == "chg":
            return panel.chg(parts[2], int(parts[1]), end)
        if parts[0] == "dd":
            if len(parts) == 3:
                return panel.dd(parts[2], int(parts[1]), end)
            if len(parts) == 4:
                return panel.dd_ratio(parts[2], parts[3], int(parts[1]), end)
        if parts[0] == "curvechg":
            return panel.curve_chg(int(parts[1]), end)
    except (IndexError, ValueError) as exc:
        raise ValueError("指標 id 無法解析: %s (%s)" % (ind_id, exc)) from exc
    raise ValueError("未知指標文法: %s" % ind_id)
