#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VeritaQuantGuard(VQG)v0108 — v0107 薄尾(v0107 一字不改 · SHA-256 釘在 PRIOR_SHA256)。

操作員 2026-11-09:「VQG VAP VCGC 一併順勢完成 · VQG 可能有增加指標 · 量化分析內容以增加」。
規格 /quant-roll(VIA_AgentOS_SuperPrompt v2.0 §B):動態 rolling CRITERIA · 台債 10y 為 rf · 乾淨資金流動比排除當沖與 2330 非當沖扭曲 · 禁硬編碼靜態值。

本版加的(公式引擎仍是 v0104 · 三解 · 驗證 · 曆 · 批次 · export-vap 全照 v0107;新指標「換裝在位」掛進 v0104 的 CORE,不改 v0104 / v0105 / v0107 任何一字):
  ① 五個新指標(每個三解 · 單窗在 SPECIAL · --windows 可覆蓋):
     obv(20)                 VQG.IND.OBV              量能方向:S1 n 日 OBV 增量(股) · S2 增量 / n 日總量(−1..1) · S3 用乾淨量(扣當沖;沒當沖欄 = null)
     atr(14)                 VQG.IND.ATR              真實波幅:S1 Wilder 平滑 · S2 簡單均 · S3 ATR / 收盤(fraction);要 high / low 欄,沒有 = null
     clean_flow_ratio(20)    VQG.IND.CLEAN_FLOW_RATIO 乾淨資金流動比:近 n 日乾淨量均 / 前 n 日(S1 量 · S2 乾淨成交值 · S3 中位數);當沖欄缺 = null(不猜)
     rolling_sharpe(60)      VQG.IND.ROLLING_SHARPE   風險調整報酬(不年化):S1 (均報酬 − rf 日化) / 標準差(rf 欄 rf_annual 缺 = null · 不硬編碼 rf)· S2 均 / 標準差 · S3 Sortino
     rel_strength(60)        VQG.IND.REL_STRENGTH     相對強弱:S1 n 日超額報酬(票 − 基準)· S2 (1+r)/(1+r_b)−1 · S3 票 − 2330 因子序列(factor_adj_close;缺 = null)
     缺的輸入一律 null + 原因(WARMUP_MISSING_OR_DEGENERATE),不補、不假設。rf 日化用序列自己近一年的交易日數(資料推),不寫死 252。
  ② export-vap 預設指標 sma rsi macd → + volatility drawdown obv atr clean_flow_ratio rolling_sharpe rel_strength(window_plan 25 組 · 75 列 ≤ v0104 上限 100)。
  ③ 量化分析(有加工 · 給其他應用 · 不登 VAP 來源):export-vap 跑完後讀輸出夾 indicators/<票> + series/<票>,每張票出
     analysis/<票>.json 與 vqg_quant_analysis.parquet / .csv / .json:趨勢(價 vs SMA 20/60/120)· 動能(RSI 14 + 自身歷史百分位 · MACD 柱符號與連續日數)·
     波動(VOL 20 百分位 · 五分位)· 回撤(DD 60)· 真實波幅 %(ATR S3 百分位)· 量能方向(OBV S2)· 乾淨資金流動比 · 風險調整報酬 · 相對強弱 · 缺什麼輸入。
     門檻全部來自序列自己的歷史分布(百分位 / 五分位),只有定義性常數(RSI 50 · 柱 0 · 價 vs 均)。
     寫完重生 SHA256SUMS.txt(含新檔)· export_receipt.json 與 VQG_ExportVAP_latest.json 加 analysis 節。VAP config / 連線證據一字不動(VAP 契約不變)。
  邊界:同 v0107(只讀 VDF 庫 · 零網路 · 不 import VAP · 不寫 VDF 的夾 · 前版被改過 → rc 2)。
自測:python VQG_AllInOne_v0108.py selftest(本版 12 項 + v0107 自測全部 · 零網路 · 只在 tempfile 寫)。
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import math
import os
import sys
import tempfile
import types
from datetime import date, datetime, timedelta
from pathlib import Path

VERSION_TAIL = "v0108"
HERE = Path(__file__).resolve().parent
PRIOR_NAME = "VQG_AllInOne_v0107.py"
PRIOR_SHA256 = "7e278523b28fdf47927ac0ccb79607a750a1e07f403e061701f8f46865a30c46"   # v0107 入倉版(2026-11-06 · PR #600)
PRIOR_PATH = HERE / PRIOR_NAME
if not PRIOR_PATH.is_file():
    raise SystemExit("[RED] 前版 %s 不在 %s(v0108 是 v0107 的薄尾 · 兩支要放同一夾)" % (PRIOR_NAME, HERE))
PRIOR_SHA_OK = hashlib.sha256(PRIOR_PATH.read_bytes().replace(b"\r\n", b"\n")).hexdigest() == PRIOR_SHA256
_spec = importlib.util.spec_from_file_location("vqg_v0107_for_v0108", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
for _n, _v in vars(PRIOR).items():
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = _v
V5 = PRIOR.PRIOR                      # v0105(曆 / 批次 / run_local)
V4 = V5.PRIOR                         # v0104(公式引擎:CORE · make_rows · calculate)
pl = PRIOR.pl
ENGINE_VERSION = PRIOR.ENGINE_VERSION
_EXPORT_VAP_0107 = PRIOR.export_vap                                        # 原版 export-vap(main 換裝時仍指得到原件,不遞迴)


def __getattr__(name: str):
    """公開名稱轉接:本檔沒定義的一律交前版鏈(v0107 → v0105 → v0104)。"""
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)

# ── ① 新指標(公式照 v0104 的寫法:(frame, n) → 三解;helper 全用 v0104 的)──────────────
_price, _finite, _series, _divide, _rolling, _last, _seeded_ema, net_series = (V4._price, V4._finite, V4._series, V4._divide, V4._rolling, V4._last, V4._seeded_ema, V4.net_series)


def _col(frame, name):
    return _finite(frame[name].cast(pl.Float64, strict=False)) if name in frame.columns else _series([None] * frame.height)


def _sign(s):
    return s.sign().cast(pl.Float64)


def obv(frame, n):
    p = _price(frame["adj_close"])
    vol = _col(frame, "volume")
    sign = _sign(p - p.shift(1))
    flow = sign * vol
    s1 = _last(_rolling(flow, n, "sum"))
    s2 = _last(_divide(_rolling(flow, n, "sum"), _rolling(vol, n, "sum")))
    clean = net_series(frame, "volume")
    s3 = _last(_divide(_rolling(sign * clean, n, "sum"), _rolling(clean, n, "sum")))
    return s1, s2, s3


def atr(frame, n):
    if not {"high", "low"}.issubset(frame.columns):
        return None, None, None
    h, lo, c = _col(frame, "high"), _col(frame, "low"), _price(frame["adj_close"])
    pc = c.shift(1)
    tr = pl.DataFrame({"a": h - lo, "b": (h - pc).abs(), "c": (lo - pc).abs()}).max_horizontal()
    tr = _finite(tr)
    s1 = _last(_seeded_ema(tr, n, 1 / n))
    s2 = _last(_rolling(tr, n, "mean"))
    s3 = _last(_divide(_rolling(tr, n, "mean"), c))
    return s1, s2, s3


def clean_flow_ratio(frame, n):
    clean = net_series(frame, "volume")
    cur = _rolling(clean, n, "mean")
    s1 = _last(_divide(cur, cur.shift(n)))
    clean_t = net_series(frame, "turnover")
    cur_t = _rolling(clean_t, n, "mean")
    s2 = _last(_divide(cur_t, cur_t.shift(n)))
    med = _rolling(clean, n, "median")
    s3 = _last(_divide(med, med.shift(n)))
    return s1, s2, s3


def _periods_per_year(frame) -> int | None:
    """rf 日化用的「一年幾個交易日」:從序列自己近 365 天的交易日數推(資料驅動 · 不寫死 252)。"""
    try:
        dates = [d for d in frame["date"].to_list() if d is not None]
    except Exception:
        return None
    if len(dates) < 2:
        return None
    last = dates[-1]
    n = sum(1 for d in dates if (last - d).days < 365)
    span = (last - dates[0]).days
    return n if span >= 300 else None


def rolling_sharpe(frame, n):
    p = _price(frame["adj_close"])
    r = _divide(p, p.shift(1)) - 1
    mean, sd = _rolling(r, n, "mean"), _rolling(r, n, "std")
    s1 = None
    if "rf_annual" in frame.columns:
        ppy = _periods_per_year(frame)
        rf = _col(frame, "rf_annual")
        if ppy:
            rf_d = (rf + 1.0) ** (1.0 / ppy) - 1.0
            s1 = _last(_divide(mean - _rolling(rf_d, n, "mean"), sd))
    s2 = _last(_divide(mean, sd))
    down = r.clip(upper_bound=0)
    dd = _rolling(down * down, n, "mean").sqrt()
    s3 = _last(_divide(mean, dd))
    return s1, s2, s3


def rel_strength(frame, n):
    if not {"benchmark_adj_close", "benchmark_market"}.issubset(frame.columns):
        return None, None, None
    if frame["benchmark_market"].n_unique() != 1 or frame["benchmark_market"][0] != frame["market"][0]:
        return None, None, None
    p, b = _price(frame["adj_close"]), _price(frame["benchmark_adj_close"])
    rp, rb = _divide(p, p.shift(n)) - 1, _divide(b, b.shift(n)) - 1
    s1 = _last(rp - rb)
    s2 = _last(_divide(rp + 1.0, rb + 1.0) - 1.0)
    s3 = None
    if "factor_adj_close" in frame.columns:
        f = _price(frame["factor_adj_close"])
        s3 = _last(rp - (_divide(f, f.shift(n)) - 1))
    return s1, s2, s3


NEW_CORE = {
    "obv": {"stable_id": "VQG.IND.OBV", "formula": "OBV_n = sum_{t-n+1..t} sign(p_t - p_{t-1}) * v_t ; S2 = OBV_n / sum v ; S3 用乾淨量(扣當沖)",
            "solutions": [{"id": "S1", "name": "obv_delta_shares", "method": "n 日 OBV 增量(股數);缺價 / 缺量那天不計"},
                          {"id": "S2", "name": "obv_normalized", "method": "增量除以 n 日總量 → −1..1;總量 0 = null"},
                          {"id": "S3", "name": "obv_clean_volume", "method": "同 S2 但用 net_series 乾淨量(volume − daytrade_volume);沒當沖欄 = null"}], "window": 20},
    "atr": {"stable_id": "VQG.IND.ATR", "formula": "TR = max(h−l, |h−c_{t-1}|, |l−c_{t-1}|) ; ATR_n = Wilder(TR, n)",
            "solutions": [{"id": "S1", "name": "wilder", "method": "alpha=1/n 的 Wilder 平滑 · 前 n 根 SMA 種子"},
                          {"id": "S2", "name": "simple_mean", "method": "TR 的 n 日簡單均;未滿 n = null"},
                          {"id": "S3", "name": "atr_pct_of_close", "method": "S2 / 收盤(fraction);要 high / low 欄"}], "window": 14},
    "clean_flow_ratio": {"stable_id": "VQG.IND.CLEAN_FLOW_RATIO", "formula": "CFR_n = mean(clean_v_{t-n+1..t}) / mean(clean_v_{t-2n+1..t-n}) ; clean_v = v − daytrade_v",
                         "solutions": [{"id": "S1", "name": "clean_volume_ratio", "method": "乾淨量 n 日均 / 前 n 日均;當沖欄缺 = null(不猜)"},
                                       {"id": "S2", "name": "clean_turnover_ratio", "method": "同 S1 用乾淨成交值(turnover − daytrade_turnover)"},
                                       {"id": "S3", "name": "clean_volume_median_ratio", "method": "n 日中位數 / 前 n 日中位數(抗極端值)"}], "window": 20},
    "rolling_sharpe": {"stable_id": "VQG.IND.ROLLING_SHARPE", "formula": "SR_n = (mean(r) − rf_d) / std(r) ; rf_d = (1+rf_annual)^(1/ppy) − 1 ; ppy 由序列近 365 天交易日數推",
                       "solutions": [{"id": "S1", "name": "excess_over_rf", "method": "rf 來自 rf_annual 欄(台債 10y);欄缺或歷史不足一年 = null,不硬編碼 rf"},
                                     {"id": "S2", "name": "raw_mean_over_std", "method": "mean / std(樣本);不年化"},
                                     {"id": "S3", "name": "sortino_raw", "method": "mean / sqrt(mean(min(r,0)^2));下檔為 0 = null"}], "window": 60},
    "rel_strength": {"stable_id": "VQG.IND.REL_STRENGTH", "formula": "RS_n = (p_t/p_{t-n} − 1) − (b_t/b_{t-n} − 1)",
                     "solutions": [{"id": "S1", "name": "excess_return_vs_benchmark", "method": "票 n 日報酬 − 基準 n 日報酬;要 benchmark_adj_close + 同市場"},
                                   {"id": "S2", "name": "ratio_vs_benchmark", "method": "(1+r)/(1+r_b) − 1"},
                                   {"id": "S3", "name": "excess_vs_factor_2330", "method": "票 n 日報酬 − 因子序列(factor_adj_close · 2330)n 日報酬;缺 = null"}], "window": 60},
}
NEW_SPECIAL = {"obv": 20, "atr": 14, "clean_flow_ratio": 20, "rolling_sharpe": 60, "rel_strength": 60}
NEW_EXTRA = {"obv": 1, "atr": 1, "clean_flow_ratio": None, "rolling_sharpe": None, "rel_strength": None}
NEW_OPTIONAL = {"obv": ["volume", "daytrade_volume", "clean_volume"], "atr": ["high", "low"],
                "clean_flow_ratio": ["volume", "daytrade_volume", "clean_volume", "turnover", "daytrade_turnover", "clean_turnover"],
                "rolling_sharpe": ["rf_annual"], "rel_strength": ["benchmark_adj_close", "benchmark_market", "factor_adj_close"]}
NEW_UNITS = {"obv": ("volume", "dimensionless", "dimensionless"), "atr": ("price", "price", "fraction"), "clean_flow_ratio": ("dimensionless",) * 3,
             "rolling_sharpe": ("dimensionless",) * 3, "rel_strength": ("fraction",) * 3}
NEW_ALIASES = {"high": ("high", "high_price", "最高價"), "low": ("low", "low_price", "最低價"),
               "rf_annual": ("rf_annual", "risk_free_annual", "tw10y_yield", "台債10年殖利率", "無風險利率"),
               "factor_adj_close": ("factor_adj_close", "factor_2330_adj_close")}
NEW_METRICS = tuple(NEW_CORE)
DEFAULT_METRICS_0108 = ["sma", "rsi", "macd", "volatility", "drawdown", "obv", "atr", "clean_flow_ratio", "rolling_sharpe", "rel_strength"]
_DEFAULT_METRICS_0107 = list(PRIOR.DEFAULT_METRICS)
_UNITS_0104 = V4.units


def _units_0108(metric, i):
    if metric in NEW_UNITS:
        return NEW_UNITS[metric][i]
    return _UNITS_0104(metric, i)


def install() -> dict:
    """換裝在位:新指標掛進 v0104 的 CORE / SPECIAL / EXTRA / OPTIONAL / NONCOMPARABLE / units;v0107 預設指標換成本版。冪等。"""
    for m, spec in NEW_CORE.items():
        V4.CORE[m] = spec
        V4.SPECIAL[m] = NEW_SPECIAL[m]
        V4.EXTRA[m] = NEW_EXTRA[m]
        V4.OPTIONAL[m] = NEW_OPTIONAL[m]
        V4.NONCOMPARABLE.add(m)
        setattr(V4, m, globals()[m])
    for k, aliases in NEW_ALIASES.items():
        V4.COLUMN_ALIASES.setdefault(k, aliases)                            # 欄名對照:high / low / rf_annual / factor_adj_close 才讀得進來(v0105 load_series 只載認得的欄)
    V4.units = _units_0108
    PRIOR.DEFAULT_METRICS = list(DEFAULT_METRICS_0108)
    return {"metrics": list(NEW_METRICS), "default_metrics": list(DEFAULT_METRICS_0108), "aliases": list(NEW_ALIASES)}


install()


# ── ③ 量化分析(讀輸出夾 · 門檻來自序列自己的分布)────────────────────────────────────────
def _pct_rank(values: list, x) -> float | None:
    hist = [v for v in values if v is not None and math.isfinite(v)]
    if x is None or not hist:
        return None
    return sum(1 for v in hist if v <= x) / len(hist)


def _quintile(rank) -> int | None:
    return None if rank is None else min(5, max(1, math.ceil(rank * 5)))


def _last_valid(frame, col):
    if col not in frame.columns:
        return None
    vals = [v for v in frame[col].to_list() if v is not None and math.isfinite(v)]
    return vals[-1] if vals else None


def _streak(frame, col) -> int | None:
    """柱狀圖最後同號連續幾個觀測日(定義性:符號比 0)。"""
    if col not in frame.columns:
        return None
    vals = [v for v in frame[col].to_list() if v is not None and math.isfinite(v)]
    if not vals:
        return None
    sign = 1 if vals[-1] > 0 else (-1 if vals[-1] < 0 else 0)
    k = 0
    for v in reversed(vals):
        s = 1 if v > 0 else (-1 if v < 0 else 0)
        if s != sign:
            break
        k += 1
    return k * (sign if sign else 1)


def analyze_ticker(ticker: str, wide, series) -> dict:
    """一張票的量化分析(只用 indicators/<票> 的歷史分布 + series/<票> 的收盤)。"""
    W = wide
    cols = set(W.columns)
    obs = [d for d in W["observation_date"].to_list() if d is not None]
    last_obs = obs[-1] if obs else None
    price = None
    if series is not None and last_obs is not None and "adj_close" in series.columns:
        hit = series.filter(pl.col("date") == last_obs)
        if hit.height:
            v = hit["adj_close"][0]
            price = float(v) if v is not None else None
    missing = []
    out = {"ticker": ticker, "observation_date": str(last_obs) if last_obs else None, "points": W.height, "adj_close": price, "engine": "VQG " + VERSION_TAIL, "formula_engine": ENGINE_VERSION}
    # 趨勢:價 vs SMA 20 / 60 / 120(定義性比較 · 不設百分比門檻)
    above, used = 0, 0
    for w in (20, 60, 120):
        c = "SMA_%d_S1" % w
        s = _last_valid(W, c)
        out["sma_%d" % w] = s
        if s is not None and price is not None:
            used += 1
            above += int(price > s)
            out["price_vs_sma_%d" % w] = "ABOVE" if price > s else "BELOW"
    out["trend_regime"] = ("INSUFFICIENT" if used == 0 else "ALL_ABOVE" if above == used else "ALL_BELOW" if above == 0 else "MIXED")
    out["trend_used_windows"] = used
    # 動能:RSI 14 + 自身歷史百分位;MACD 柱符號與連續日數
    rsi = _last_valid(W, "RSI_14_S1")
    out["rsi_14"] = rsi
    out["rsi_14_pct_rank"] = _pct_rank(W["RSI_14_S1"].to_list(), rsi) if "RSI_14_S1" in cols else None
    out["rsi_side"] = None if rsi is None else ("ABOVE_50" if rsi > 50 else "BELOW_50" if rsi < 50 else "AT_50")
    hist_col = "MACD_26_S1_histogram"
    out["macd_hist"] = _last_valid(W, hist_col)
    out["macd_hist_streak"] = _streak(W, hist_col)
    # 波動 · 回撤 · 真實波幅
    vol = _last_valid(W, "VOLATILITY_20_S1")
    out["volatility_20"] = vol
    out["volatility_20_pct_rank"] = _pct_rank(W["VOLATILITY_20_S1"].to_list(), vol) if "VOLATILITY_20_S1" in cols else None
    out["volatility_quintile"] = _quintile(out["volatility_20_pct_rank"])
    out["drawdown_60"] = _last_valid(W, "DRAWDOWN_60_S1")
    atrp = _last_valid(W, "ATR_14_S3")
    out["atr_pct_14"] = atrp
    out["atr_pct_14_pct_rank"] = _pct_rank(W["ATR_14_S3"].to_list(), atrp) if "ATR_14_S3" in cols else None
    # 量能 · 資金流 · 風險調整 · 相對強弱
    out["obv_20_normalized"] = _last_valid(W, "OBV_20_S2")
    out["obv_direction"] = None if out["obv_20_normalized"] is None else ("INFLOW" if out["obv_20_normalized"] > 0 else "OUTFLOW" if out["obv_20_normalized"] < 0 else "FLAT")
    out["clean_flow_ratio_20"] = _last_valid(W, "CLEAN_FLOW_RATIO_20_S1")
    if out["clean_flow_ratio_20"] is None:
        missing.append("DAYTRADE_SERIES_MISSING(clean_flow_ratio 要 daytrade_volume / clean_volume 欄 · VDF 線出)")
    out["sharpe_60_excess_rf"] = _last_valid(W, "ROLLING_SHARPE_60_S1")
    out["sharpe_60_raw"] = _last_valid(W, "ROLLING_SHARPE_60_S2")
    out["sortino_60_raw"] = _last_valid(W, "ROLLING_SHARPE_60_S3")
    if out["sharpe_60_excess_rf"] is None:
        missing.append("RF_SERIES_MISSING(rolling_sharpe S1 要 rf_annual 欄 = 台債 10y · VDF 線出;S2 / S3 不需要)")
    out["rel_strength_60"] = _last_valid(W, "REL_STRENGTH_60_S1")
    out["rel_strength_60_vs_factor_2330"] = _last_valid(W, "REL_STRENGTH_60_S3")
    if out["rel_strength_60"] is None:
        missing.append("BENCHMARK_SERIES_MISSING(rel_strength 要 benchmark_adj_close + benchmark_market 欄;S3 另要 factor_adj_close = 2330)")
    core = [out["trend_regime"] != "INSUFFICIENT", rsi is not None, out["macd_hist"] is not None, vol is not None, out["drawdown_60"] is not None, atrp is not None, out["obv_20_normalized"] is not None]
    out["core_fields_present"] = sum(core)
    out["lamp"] = "RED" if W.height == 0 else ("GREEN" if all(core) and not missing else "YELLOW")
    out["missing_inputs"] = missing
    out["rules"] = ("趨勢 = 價 vs SMA(定義性);動能 / 波動 / 真實波幅的「高低」= 該票自己歷史的百分位與五分位(資料驅動 · 無靜態門檻);"
                    "RSI 50 · MACD 柱 0 為定義性常數;缺輸入照實列 missing_inputs,不補不猜")
    return out


ANALYSIS_SCHEMA = {"ticker": pl.String, "observation_date": pl.String, "points": pl.Int64, "adj_close": pl.Float64, "engine": pl.String, "formula_engine": pl.String,
                   "sma_20": pl.Float64, "sma_60": pl.Float64, "sma_120": pl.Float64, "price_vs_sma_20": pl.String, "price_vs_sma_60": pl.String, "price_vs_sma_120": pl.String,
                   "trend_regime": pl.String, "trend_used_windows": pl.Int64, "rsi_14": pl.Float64, "rsi_14_pct_rank": pl.Float64, "rsi_side": pl.String,
                   "macd_hist": pl.Float64, "macd_hist_streak": pl.Int64, "volatility_20": pl.Float64, "volatility_20_pct_rank": pl.Float64, "volatility_quintile": pl.Int64,
                   "drawdown_60": pl.Float64, "atr_pct_14": pl.Float64, "atr_pct_14_pct_rank": pl.Float64, "obv_20_normalized": pl.Float64, "obv_direction": pl.String,
                   "clean_flow_ratio_20": pl.Float64, "sharpe_60_excess_rf": pl.Float64, "sharpe_60_raw": pl.Float64, "sortino_60_raw": pl.Float64,
                   "rel_strength_60": pl.Float64, "rel_strength_60_vs_factor_2330": pl.Float64, "core_fields_present": pl.Int64, "lamp": pl.String, "missing_inputs": pl.String, "rules": pl.String}


def quant_analysis(export_dir: Path) -> dict:
    """export-vap 輸出夾 → analysis/<票>.json + vqg_quant_analysis.parquet / .csv / .json;回摘要。只讀 indicators/ 與 series/。"""
    export_dir = Path(export_dir)
    ind_dir, ser_dir = export_dir / "indicators", export_dir / "series"
    rows, per = [], {}
    for p in sorted(ind_dir.glob("*.parquet")) if ind_dir.is_dir() else []:
        tk = p.stem
        W = pl.read_parquet(p)
        S = pl.read_parquet(ser_dir / p.name) if (ser_dir / p.name).is_file() else None
        a = analyze_ticker(tk, W, S)
        per[tk] = a
        rows.append({k: (json.dumps(v, ensure_ascii=False) if isinstance(v, list) else v) for k, v in a.items()})
    (export_dir / "analysis").mkdir(exist_ok=True)
    for tk, a in per.items():
        (export_dir / "analysis" / (tk + ".json")).write_text(json.dumps(a, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    frame = pl.DataFrame([{k: r.get(k) for k in ANALYSIS_SCHEMA} for r in rows], schema=ANALYSIS_SCHEMA) if rows else pl.DataFrame(schema=ANALYSIS_SCHEMA)
    frame.write_parquet(export_dir / "vqg_quant_analysis.parquet", compression="zstd")
    frame.write_csv(export_dir / "vqg_quant_analysis.csv", include_bom=True)
    (export_dir / "vqg_quant_analysis.json").write_text(json.dumps({"schema": "VIA-VQG-QUANT-ANALYSIS/1.0", "engine": "VQG " + VERSION_TAIL, "formula_engine": ENGINE_VERSION,
                                                                     "at": datetime.now().isoformat(timespec="seconds"), "tickers": rows}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    lamps = [a["lamp"] for a in per.values()]
    summary = {"schema": "VIA-VQG-QUANT-ANALYSIS/1.0", "tickers": len(per), "green": lamps.count("GREEN"), "yellow": lamps.count("YELLOW"), "red": lamps.count("RED"),
               "lamp": "RED" if not per else ("GREEN" if all(l == "GREEN" for l in lamps) else "YELLOW"),
               "missing_inputs": sorted({m.split("(")[0] for a in per.values() for m in a["missing_inputs"]}),
               "files": ["analysis/<票>.json", "vqg_quant_analysis.parquet", "vqg_quant_analysis.csv", "vqg_quant_analysis.json"], "vap_source": False,
               "meaning": "量化分析給其他應用(快照 · 無時間軸)· 不登 VAP 來源;YELLOW = 有輸入缺(當沖 / rf / 基準欄由 VDF 線出)"}
    return summary


def _resign(export_dir: Path) -> int:
    """重生 SHA256SUMS.txt(同 v0107 公式:全檔 · 含子夾 · 不含自己)。"""
    sums = "\n".join("%s  %s" % (PRIOR._sha256_file(p), str(p.relative_to(export_dir)).replace("\\", "/")) for p in sorted(export_dir.rglob("*")) if p.is_file() and p.name != "SHA256SUMS.txt") + "\n"
    (export_dir / "SHA256SUMS.txt").write_text(sums, encoding="utf-8")
    return sums.count("\n")


def export_vap_0108(args) -> int:
    """v0107 export_vap 原樣跑完 → 量化分析 → 收據補 analysis 節 → 重生 SHA256SUMS。"""
    rc = _EXPORT_VAP_0107(args)
    if rc != 0:
        return rc
    via = PRIOR.via_root(getattr(args, "via_root", None))
    out_root = Path(getattr(args, "out_dir", None) or ((via / "VIA_Reports" / "vqg" / "vap_export") if via else Path.cwd() / "VIA_Reports" / "vqg" / "vap_export"))
    receipt_dir = Path(getattr(args, "receipt_dir", None) or ((via / "VIA_Reports" / "vqg") if via else Path.cwd() / "VIA_Reports" / "vqg"))
    try:
        latest = json.loads((out_root / "latest.json").read_text(encoding="utf-8"))
        final = Path(latest["export_dir"])
    except (OSError, ValueError, KeyError) as error:
        print("[RED] VQG %s 量化分析 · 找不到剛匯出的夾(%s)" % (VERSION_TAIL, error), flush=True)
        return 2
    try:
        summary = quant_analysis(final)
        n_sums = _resign(final)
        rp = final / "export_receipt.json"
        rec = json.loads(rp.read_text(encoding="utf-8"))
        rec["analysis"] = summary
        rec["engine"] = "VeritaQuantGuard " + VERSION_TAIL
        rec["steps"].append({"step": "⑧ 量化分析(v0108)", "lamp": summary["lamp"], "detail": "票 %d · 綠 %d 黃 %d 紅 %d · 缺輸入 %s · SHA256SUMS 重生 %d 檔" % (
            summary["tickers"], summary["green"], summary["yellow"], summary["red"], ",".join(summary["missing_inputs"]) or "無", n_sums)})
        rp.write_text(json.dumps(rec, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        _resign(final)                                                   # 收據改了 → 再簽一次(SHA256SUMS 永遠最後寫)
        lp = receipt_dir / "VQG_ExportVAP_latest.json"
        if lp.is_file():
            lr = json.loads(lp.read_text(encoding="utf-8"))
            lr["analysis"] = summary
            lr["engine"] = "VeritaQuantGuard " + VERSION_TAIL
            lp.write_text(json.dumps(lr, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        print("[%s] VQG %s 量化分析 · 票 %d · 綠 %d 黃 %d 紅 %d · 缺輸入 %s → %s" % (summary["lamp"], VERSION_TAIL, summary["tickers"], summary["green"], summary["yellow"], summary["red"],
                                                                        ",".join(summary["missing_inputs"]) or "無", final / "vqg_quant_analysis.parquet"), flush=True)
    except (OSError, ValueError) as error:
        print("[RED] VQG %s 量化分析中斷 · %s: %s" % (VERSION_TAIL, type(error).__name__, str(error)[:200]), flush=True)
        return 2
    return rc


# ── 自測 ────────────────────────────────────────────────────────────────────────
def _frame(n=130, start=date(2026, 1, 5), base=100.0, bench=None, daytrade=False, high_low=True, rf=None):
    rows = []
    d, p = start, base
    k = 0
    while len(rows) < n:
        if d.weekday() < 5:
            p = p * (1.0 + (0.004 if k % 3 else -0.002))
            r = {"ticker": "T", "date": d, "session_index": k + 1, "market": "TW", "adj_close": p, "available_on": d, "volume": 1000.0 + 10 * k}
            if high_low:
                r["high"], r["low"] = p * 1.02, p * 0.98
            if daytrade:
                r["daytrade_volume"] = r["volume"] * 0.5
            if bench is not None:
                r["benchmark_adj_close"], r["benchmark_market"] = bench * (1.0 + 0.001 * k), "TW"
                r["factor_adj_close"] = bench * (1.0 + 0.002 * k)
            if rf is not None:
                r["rf_annual"] = rf
            rows.append(r)
            k += 1
        d += timedelta(days=1)
    return pl.DataFrame(rows)


def selftest() -> int:
    ok = 0
    total = 0

    def chk(label, cond):
        nonlocal ok, total
        total += 1
        ok += bool(cond)
        print("  [%s] %s" % ("PASS" if cond else "FAIL", label), flush=True)

    print("[VQG %s selftest]" % VERSION_TAIL, flush=True)
    chk("① 前版 v0107 SHA-256 釘住 · 公式引擎仍 v0104", PRIOR_SHA_OK and ENGINE_VERSION == "v0104")
    chk("② 換裝在位:五個新指標在 v0104 CORE / SPECIAL / EXTRA / OPTIONAL / NONCOMPARABLE · units 接上 · 預設指標 10 個",
        all(m in V4.CORE and m in V4.SPECIAL and m in V4.EXTRA and m in V4.OPTIONAL and m in V4.NONCOMPARABLE and getattr(V4, m) is globals()[m] for m in NEW_METRICS)
        and V4.units("atr", 2) == "fraction" and V4.units("sma", 0) == "price" and PRIOR.DEFAULT_METRICS == DEFAULT_METRICS_0108
        and all(k in V4.COLUMN_ALIASES for k in NEW_ALIASES))
    plan = V4.window_plan(DEFAULT_METRICS_0108, {})
    chk("③ window_plan 預設 10 指標 = 25 組(75 列 ≤ 100)· 新指標單窗", len(plan) == 25 and all((m, NEW_SPECIAL[m]) in plan for m in NEW_METRICS))
    F = _frame(daytrade=True, bench=50.0, rf=0.02)
    a1, a2, a3 = atr(F, 14)
    chk("④ atr:三解皆數 · S3 = S2 / 收盤 · 高低差固定 4% 時 S2 ≈ 0.04 × 價", all(x is not None for x in (a1, a2, a3)) and abs(a3 - a2 / F["adj_close"][-1]) < 1e-9 and abs(a2 / F["adj_close"][-1] - 0.04) < 0.003)
    o1, o2, o3 = obv(F, 20)
    chk("⑤ obv:S1 = 20 日 sign×量總和 · S2 在 −1..1 · S3(乾淨量 = 一半)方向同 S2", o1 is not None and -1 <= o2 <= 1 and o3 is not None and (o2 > 0) == (o3 > 0))
    c1, c2, c3 = clean_flow_ratio(F, 20)
    chk("⑥ clean_flow_ratio:量線性遞增 → S1 > 1 · S2 null(無 turnover 欄)· S3 > 1", c1 is not None and c1 > 1 and c2 is None and c3 is not None and c3 > 1)
    FL = _frame(n=300, daytrade=True, bench=50.0, rf=0.02)                 # 近一年交易日數要推得出來:歷史跨度 ≥ 300 天
    s1, s2, s3 = rolling_sharpe(FL, 60)
    s1_norf = rolling_sharpe(FL.drop("rf_annual"), 60)[0]
    chk("⑦ rolling_sharpe:有 rf 欄且歷史 ≥ 300 天 → S1 數(≤ S2)· S2 = mean/std · S3 Sortino 數;沒 rf 欄 → S1 null · 歷史不足一年 → S1 null(不硬編碼 rf / 252)",
        s1 is not None and s2 is not None and s1 <= s2 and s3 is not None and s1_norf is None and rolling_sharpe(F, 60)[0] is None and rolling_sharpe(F, 60)[1] is not None)
    r1, r2, r3 = rel_strength(F, 60)
    r_none = rel_strength(F.drop(["benchmark_adj_close", "benchmark_market", "factor_adj_close"]), 60)
    chk("⑧ rel_strength:有基準 → 三解皆數;沒基準 → 三 null;atr 沒 high/low → 三 null", all(x is not None for x in (r1, r2, r3)) and r_none == (None, None, None) and atr(F.drop(["high", "low"]), 14) == (None, None, None))
    chk("⑨ 缺當沖欄:obv S3 / clean_flow_ratio S1 null · S2(obv) 仍數", obv(F.drop("daytrade_volume"), 20)[2] is None and clean_flow_ratio(F.drop("daytrade_volume"), 20)[0] is None and obv(F.drop("daytrade_volume"), 20)[1] is not None)
    env_root = os.environ.pop("VQG_VDF_ROOT", None)
    try:
        with tempfile.TemporaryDirectory() as td:
            t = Path(td)
            vdf = t / "vdf_database"
            (vdf / "output_hub").mkdir(parents=True)
            d0 = date(2026, 1, 5)
            V5._vdf_like(vdf / "output_hub" / "tw_daily_prices_20261101_120000.parquet", V5._bars("2330.TW", d0, 130) + V5._bars("2317.TW", d0, 130, base=80))
            as_of = d0 + timedelta(days=170)
            out = t / "out"
            ns = types.SimpleNamespace(via_root=None, root=str(vdf), out_dir=str(out), receipt_dir=str(t / "rcpt"), ticker=[], max_tickers=50, metrics=None, windows=None,
                                       as_of=as_of, series_rows=0, indicator_points=40, calendar="auto", snapshots="latest", market=None, vap_port=8765)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(io.StringIO()):
                rc = export_vap_0108(ns)
            ed = Path(json.loads((out / "latest.json").read_text(encoding="utf-8"))["export_dir"]) if (out / "latest.json").is_file() else None
            W = pl.read_parquet(ed / "indicators" / "2330_TW.parquet") if ed else pl.DataFrame()
            chk("⑩ export-vap(預設 10 指標 · 夾具 2 票)rc 0 · 一票一表含 OBV_20_S1 · ATR_14_S3 · CLEAN_FLOW_RATIO_20_S1 · ROLLING_SHARPE_60_S2 · SMA_120_S1 欄",
                rc == 0 and ed is not None and {"OBV_20_S1", "ATR_14_S3", "CLEAN_FLOW_RATIO_20_S1", "ROLLING_SHARPE_60_S2", "SMA_120_S1", "DRAWDOWN_60_S1"} <= set(W.columns))
            rec = json.loads((ed / "export_receipt.json").read_text(encoding="utf-8")) if ed else {}
            an = rec.get("analysis") or {}
            sums_ok = ed is not None and all(PRIOR._sha256_file(ed / ln.split("  ", 1)[1]) == ln.split("  ", 1)[0] for ln in (ed / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines() if ln.strip())
            qa = pl.read_parquet(ed / "vqg_quant_analysis.parquet") if ed and (ed / "vqg_quant_analysis.parquet").is_file() else pl.DataFrame()
            chk("⑪ 量化分析:analysis/<票>.json ×2 · vqg_quant_analysis parquet/csv/json · 收據 analysis 節 · 燈 YELLOW(夾具無當沖 / rf / 基準欄 → missing_inputs 三項)· SHA256SUMS 全對(含新檔)",
                ed is not None and (ed / "analysis" / "2330_TW.json").is_file() and (ed / "analysis" / "2317_TW.json").is_file() and qa.height == 2 and an.get("tickers") == 2
                and an.get("lamp") == "YELLOW" and set(an.get("missing_inputs") or []) == {"DAYTRADE_SERIES_MISSING", "RF_SERIES_MISSING", "BENCHMARK_SERIES_MISSING"} and sums_ok)
            row = {r["ticker"]: r for r in qa.to_dicts()}.get("2330_TW", {})
            cfg = json.loads((ed / PRIOR.VAP_CONFIG_NAME).read_text(encoding="utf-8")) if ed else {}
            srcs = json.dumps(cfg, ensure_ascii=False)
            chk("⑫ 2330 分析列:趨勢 regime 非 INSUFFICIENT · RSI 百分位 0..1 · 波動五分位 1..5 · OBV 方向 · ATR% 數;VAP config / 連線證據一字不動(分析不登 VAP 來源)",
                row.get("trend_regime") in ("ALL_ABOVE", "ALL_BELOW", "MIXED") and row.get("rsi_14_pct_rank") is not None and 0 <= row["rsi_14_pct_rank"] <= 1
                and row.get("volatility_quintile") in (1, 2, 3, 4, 5) and row.get("obv_direction") in ("INFLOW", "OUTFLOW", "FLAT") and row.get("atr_pct_14") is not None
                and "quant_analysis" not in srcs and "VQG-INDICATOR-2330_TW" in srcs)
    finally:
        if env_root is not None:
            os.environ["VQG_VDF_ROOT"] = env_root
    print("  == v0108 %d/%d" % (ok, total), flush=True)
    # 前版自測:預設指標暫時還原成 v0107 的,跑完再換回
    PRIOR.DEFAULT_METRICS = list(_DEFAULT_METRICS_0107)
    try:
        prior_rc = PRIOR.selftest()
    finally:
        PRIOR.DEFAULT_METRICS = list(DEFAULT_METRICS_0108)
    good = ok == total and prior_rc == 0
    print("[%s] VQG %s selftest · 本版 %d/%d · 前版鏈 v0107 %s" % ("PASS" if good else "FAIL", VERSION_TAIL, ok, total, "PASS" if prior_rc == 0 else "FAIL"), flush=True)
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = next((a for a in argv if not a.startswith("-")), "scan")
    if cmd in ("selftest", "test") or "--selftest" in argv:
        try:
            return selftest()
        except Exception as error:  # noqa: BLE001
            print("[FAIL] VQG %s selftest 中斷 · %s: %s" % (VERSION_TAIL, type(error).__name__, str(error)[:200]), flush=True)
            return 1
    if cmd == "export-vap":
        _orig = PRIOR.export_vap
        PRIOR.export_vap = export_vap_0108                               # v0107 main 解析指令列後呼叫 export_vap → 走本版(先原樣匯出再量化分析)
        try:
            return PRIOR.main(argv)
        finally:
            PRIOR.export_vap = _orig
    if "--help" in argv or "-h" in argv:
        rc = PRIOR.main(argv)
        print("v0108:export-vap 預設指標 %s · 新指標 %s · 量化分析 analysis/<票>.json + vqg_quant_analysis.*" % (" ".join(DEFAULT_METRICS_0108), " ".join(NEW_METRICS)), flush=True)
        return rc
    return PRIOR.main(argv)


if __name__ == "__main__":
    sys.exit(main())
