# -*- coding: utf-8 -*-
"""
mathkit.py — 純標準庫統計核心（與 MDL008 FIS 同式的 robust-z / tanh 合成）
=============================================================================
MODULE M00_MathKit
  [MCFL-M00-C01-F001] median / mad / robust_z     — (x-median)/(1.4826*MAD)
  [MCFL-M00-C01-F002] fis_scale                   — 100*tanh(z/2) → ±100
  [MCFL-M00-C01-F003] returns / drawdown / corr   — 對數報酬、回撤、Pearson
  [MCFL-M00-C01-F004] pc1_variance_share          — 冪迭代求相關矩陣第一主成分
治理：無外部依賴；所有函式對短樣本 fail-soft 回傳 None，不擲例外污染管線。
"""
from __future__ import annotations

import math

Z_CLIP = 3.0


# --------------------------------------------------------------------------- #
# 基本統計
# --------------------------------------------------------------------------- #

def mean(xs):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    return sum(xs) / len(xs) if xs else None


def stdev(xs):
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    n = len(xs)
    if n < 2:
        return None
    mu = sum(xs) / n
    var = sum((x - mu) ** 2 for x in xs) / (n - 1)
    return math.sqrt(var)


def median(xs):
    xs = sorted(x for x in xs if x is not None and math.isfinite(x))
    n = len(xs)
    if n == 0:
        return None
    mid = n // 2
    return xs[mid] if n % 2 else (xs[mid - 1] + xs[mid]) / 2.0


def mad(xs, med=None):
    """Median absolute deviation. [MCFL-M00-C01-F001]"""
    xs = [x for x in xs if x is not None and math.isfinite(x)]
    if not xs:
        return None
    if med is None:
        med = median(xs)
    return median([abs(x - med) for x in xs])


def robust_z(x, sample, clip=Z_CLIP):
    """MAD 穩健 z（MDL008 FIS 同式）：(x-median)/(1.4826*MAD)。
    MAD=0 時退回 std z；樣本不足回 None。 [MCFL-M00-C01-F001]"""
    if x is None or not math.isfinite(x):
        return None
    sample = [v for v in sample if v is not None and math.isfinite(v)]
    if len(sample) < 20:
        return None
    med = median(sample)
    m = mad(sample, med)
    if m is not None and m > 1e-12:
        z = (x - med) / (1.4826 * m)
    else:
        sd = stdev(sample)
        if sd is None or sd <= 1e-12:
            return None
        z = (x - med) / sd
    return clamp(z, -clip, clip)


def fis_scale(z_mean):
    """FIS 合成尺度：100*tanh(z/2) → ±100。 [MCFL-M00-C01-F002]"""
    if z_mean is None:
        return None
    return 100.0 * math.tanh(z_mean / 2.0)


def clamp(x, lo, hi):
    return max(lo, min(hi, x))


def percentile_rank(x, xs):
    """x 在母體 xs 的百分位（0..100）。"""
    xs = sorted(v for v in xs if v is not None and math.isfinite(v))
    if x is None or not xs:
        return None
    below = sum(1 for v in xs if v <= x)
    return 100.0 * below / len(xs)


# --------------------------------------------------------------------------- #
# 報酬 / 回撤 / 序列工具
# --------------------------------------------------------------------------- #

def log_returns(prices):
    """對數日報酬序列（長度 n-1）。 [MCFL-M00-C01-F003]"""
    out = []
    for a, b in zip(prices, prices[1:]):
        if a and b and a > 0 and b > 0:
            out.append(math.log(b / a))
        else:
            out.append(0.0)
    return out


def window_return(prices, k, end=None):
    """截至 end（預設最後一筆）的 k 日對數報酬。"""
    if end is None:
        end = len(prices) - 1
    start = end - k
    if start < 0 or end >= len(prices):
        return None
    a, b = prices[start], prices[end]
    if not a or not b or a <= 0 or b <= 0:
        return None
    return math.log(b / a)


def series_change(values, k, end=None):
    """水位序列（如殖利率）k 日差分。"""
    if end is None:
        end = len(values) - 1
    start = end - k
    if start < 0 or end >= len(values):
        return None
    a, b = values[start], values[end]
    if a is None or b is None:
        return None
    return b - a


def drawdown_from_high(values, lookback, end=None):
    """相對 lookback 窗內高點的回撤幅度（正數=回撤）。 [MCFL-M00-C01-F003]"""
    if end is None:
        end = len(values) - 1
    start = max(0, end - lookback + 1)
    window = [v for v in values[start:end + 1] if v is not None and v > 0]
    if len(window) < 2:
        return None
    peak = max(window)
    last = values[end]
    if last is None or last <= 0 or peak <= 0:
        return None
    return max(0.0, 1.0 - last / peak)


def rolling_metric_series(n_obs, fn, tail):
    """對最後 tail 個觀測點逐日評估 fn(end_index)，供 z 歷史與 sparkline 用。"""
    out = []
    for end in range(max(0, n_obs - tail), n_obs):
        out.append(fn(end))
    return out


# --------------------------------------------------------------------------- #
# 相關 / 領先滯後 / PCA
# --------------------------------------------------------------------------- #

def pearson(a, b):
    pairs = [(x, y) for x, y in zip(a, b)
             if x is not None and y is not None
             and math.isfinite(x) and math.isfinite(y)]
    n = len(pairs)
    if n < 8:
        return None
    ax = [p[0] for p in pairs]
    by = [p[1] for p in pairs]
    ma, mb = sum(ax) / n, sum(by) / n
    cov = sum((x - ma) * (y - mb) for x, y in pairs)
    va = sum((x - ma) ** 2 for x in ax)
    vb = sum((y - mb) ** 2 for y in by)
    if va <= 0 or vb <= 0:
        return None
    return cov / math.sqrt(va * vb)


def tail_corr(a, b, window):
    """兩序列尾端 window 筆的 Pearson 相關。"""
    if len(a) < window or len(b) < window:
        return None
    return pearson(a[-window:], b[-window:])


def lead_lag_corr(leader, follower, lag, window):
    """corr(leader[t-lag], follower[t])：正值代表 leader 領先 follower lag 日。"""
    if lag <= 0:
        return tail_corr(leader, follower, window)
    if len(leader) < window + lag or len(follower) < window:
        return None
    a = leader[-(window + lag):-lag]
    b = follower[-window:]
    return pearson(a, b)


def pc1_variance_share(return_lists):
    """相關矩陣冪迭代 → PC1 解釋變異占比（全球共振度）。 [MCFL-M00-C01-F004]
    return_lists: 已對齊等長的報酬序列 list[list[float]]。"""
    m = len(return_lists)
    if m < 3:
        return None
    n = min(len(r) for r in return_lists)
    if n < 20:
        return None
    data = [r[-n:] for r in return_lists]
    # 標準化
    zs = []
    for r in data:
        mu = sum(r) / n
        sd = math.sqrt(sum((x - mu) ** 2 for x in r) / (n - 1)) or 1e-12
        zs.append([(x - mu) / sd for x in r])
    # 相關矩陣
    corr = [[0.0] * m for _ in range(m)]
    for i in range(m):
        corr[i][i] = 1.0
        for j in range(i + 1, m):
            c = sum(zs[i][k] * zs[j][k] for k in range(n)) / (n - 1)
            corr[i][j] = corr[j][i] = c
    # 冪迭代
    v = [1.0] * m
    lam = 0.0
    for _ in range(200):
        w = [sum(corr[i][j] * v[j] for j in range(m)) for i in range(m)]
        norm = math.sqrt(sum(x * x for x in w)) or 1e-12
        v_new = [x / norm for x in w]
        lam = norm
        if sum(abs(a - b) for a, b in zip(v, v_new)) < 1e-10:
            v = v_new
            break
        v = v_new
    return clamp(lam / m, 0.0, 1.0)


def dispersion(values):
    """橫斷面離散度（樣本標準差）。"""
    return stdev(values)
