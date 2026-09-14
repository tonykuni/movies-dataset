"""analyze.py -- 三層動能分析引擎.

Layer 1 (主判準)   累計 YoY        -- 年度大局錨點, 最不易被騙
Layer 2 (第二判準) 多月 YoY 趨勢   -- 成長品質 (連續正月數/均值/波動)
Layer 3 (第三判準) MoM vs 季節性   -- 動能拐點 (淡季不淡/旺季不旺)
輔助                2 年 CAGR       -- 修正基期扭曲

每家公司會被: 計算指標 -> 給綜合動能分數 (0-100, 僅非週期股)
-> 分到動能型態 -> 給決策分級 (優選/觀察/警戒/排除)。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _linear_slope(y: np.ndarray) -> float:
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n)
    xm, ym = x.mean(), y.mean()
    denom = ((x - xm) ** 2).sum()
    return 0.0 if denom == 0 else float(((x - xm) * (y - ym)).sum() / denom)


def _consecutive_positive(series: pd.Series) -> int:
    count = 0
    for v in reversed(series.tolist()):
        if pd.notna(v) and v > 0:
            count += 1
        else:
            break
    return count


def _seasonal_flag(g: pd.DataFrame, min_years: int) -> str:
    """MoM vs 季節性: 淡季不淡 / 旺季不旺 / 正常.

    對每個月份(1-12)算歷史平均 MoM 當季節性基準, 再看最新月實際 MoM
    相對其季節性基準的偏離。
    """
    if g["mom"].notna().sum() < min_years * 6:
        return "資料不足"
    latest = g.iloc[-1]
    mth = int(latest["month"])
    hist = g[(g["month"] == mth) & (g.index != g.index[-1])]["mom"].dropna()
    if len(hist) < min_years:
        return "資料不足"
    baseline = hist.mean()
    actual = latest["mom"]
    if pd.isna(actual):
        return "資料不足"
    is_peak = baseline > g["mom"].dropna().mean()
    diff = actual - baseline
    if is_peak:
        return "旺季不旺(警訊)" if diff < -5 else "旺季正常"
    return "淡季不淡(強訊)" if diff > 5 else "淡季正常"


def compute_company_metrics(g: pd.DataFrame, cfg: dict) -> dict:
    ac = cfg["analyze"]
    g = g.sort_values("date").reset_index(drop=True)
    latest = g.iloc[-1]
    yoy, cum = g["yoy"], g["cum_yoy"]
    win = ac["trend_window"]

    # Layer 1
    cum_yoy_now = latest.get("cum_yoy", np.nan)
    cum_recent = cum.dropna().tail(ac["cum_yoy_decline_months"] + 1)
    cum_declining = len(cum_recent) >= 2 and all(np.diff(cum_recent.values) < 0)
    cum_slope = _linear_slope(cum.dropna().tail(win).values)

    # Layer 2
    yoy_recent = yoy.dropna().tail(win)
    consec_pos = _consecutive_positive(yoy)
    mean_yoy = float(yoy_recent.mean()) if len(yoy_recent) else np.nan
    std_yoy = float(yoy_recent.std(ddof=0)) if len(yoy_recent) > 1 else np.nan
    last3 = yoy.dropna().tail(3).mean()
    prev3 = yoy.dropna().tail(6).head(3).mean()
    yoy_accel = bool(pd.notna(last3) and pd.notna(prev3) and last3 > prev3)

    # Layer 3
    season = _seasonal_flag(g, ac["seasonality_min_years"])

    # 2 年 CAGR (基期修正)
    cagr, ny = np.nan, ac["cagr_years"]
    if len(g) > 12 * ny:
        rev_now = latest.get("revenue", np.nan)
        rev_base = g.iloc[-1 - 12 * ny].get("revenue", np.nan)
        if pd.notna(rev_now) and pd.notna(rev_base) and rev_base > 0:
            cagr = ((rev_now / rev_base) ** (1 / ny) - 1) * 100

    return {
        "stock_id": latest["stock_id"],
        "name": latest.get("name", ""),
        "industry": latest.get("industry", ""),
        "industry_canon": latest.get("industry_canon", None),
        "sector_l1": latest.get("sector_l1", None),
        "sector_l2": latest.get("sector_l2", None),
        "industry_ambiguous": bool(latest.get("industry_ambiguous", False)),
        "gics_sector": latest.get("gics_sector", ""),
        "gics_zh": latest.get("gics_zh", ""),
        "gics_mixed": bool(latest.get("gics_mixed", False)),
        "yf_sector": latest.get("yf_sector", ""),
        "yf_super": latest.get("yf_super", ""),
        "icb_industry": latest.get("icb_industry", ""),
        "yf_ticker": latest.get("yf_ticker", ""),
        "is_cyclical": bool(latest.get("is_cyclical", False)),
        "cyclical_sector": latest.get("cyclical_sector", None),
        "date": latest["date"],
        "revenue": latest.get("revenue", np.nan),
        "revenue_prev_year": latest.get("revenue_prev_year", np.nan),
        "cum_revenue": latest.get("cum_revenue", np.nan),
        "cum_revenue_prev_year": latest.get("cum_revenue_prev_year", np.nan),
        "yoy": latest.get("yoy", np.nan),
        "mom": latest.get("mom", np.nan),
        "cum_yoy": cum_yoy_now,
        "cum_yoy_slope": cum_slope,
        "cum_yoy_declining": cum_declining,
        "consec_pos_yoy": consec_pos,
        "mean_yoy_6m": mean_yoy,
        "std_yoy_6m": std_yoy,
        "yoy_accelerating": yoy_accel,
        "seasonality": season,
        "cagr_2y": cagr,
        "n_months": len(g),
    }


def classify_pattern(m: dict, cfg: dict) -> str:
    ac = cfg["analyze"]
    cum, mean_yoy, std_yoy = m["cum_yoy"], m["mean_yoy_6m"], m["std_yoy_6m"]
    if m["is_cyclical"]:
        return "原物料/週期(不看月營收)"

    weak_now = pd.isna(cum) or cum < ac["cum_yoy_strong"]
    peak_signal = "旺季不旺" in str(m["seasonality"])
    if (m["cum_yoy_declining"] and weak_now) or \
       (peak_signal and (pd.isna(m["yoy"]) or m["yoy"] < 0)):
        return "見頂/動能衰退型"
    if pd.notna(std_yoy) and std_yoy >= ac["yoy_std_high"]:
        return "高波動訂單型"
    if (pd.notna(cum) and cum >= ac["cum_yoy_strong"]
            and m["consec_pos_yoy"] >= ac["min_positive_months"]
            and pd.notna(mean_yoy) and mean_yoy >= ac["mean_yoy_strong"]):
        return "成長趨緩型" if m["cum_yoy_declining"] else "穩定成長型"
    if pd.notna(cum) and cum > 0 and m["cum_yoy_slope"] >= 0:
        return "季節性/緩成長型"
    return "中性/觀察型"


def _clip01(x) -> float:
    return 0.0 if pd.isna(x) else float(max(0.0, min(1.0, x)))


def momentum_score(m: dict, cfg: dict) -> float:
    """綜合動能分數 0-100 (僅非週期股). 透明加權, 便於稽核.

    Layer1 累計YoY 45 / Layer2 多月趨勢 35 / Layer3 季節+加速 20。
    """
    if m["is_cyclical"]:
        return np.nan
    ac = cfg["analyze"]
    score = 0.0
    cum = m["cum_yoy"]
    if pd.notna(cum):
        score += 35 * _clip01(cum / (ac["cum_yoy_strong"] * 3))
    if not m["cum_yoy_declining"]:
        score += 5
    if m["cum_yoy_slope"] > 0:
        score += 5
    score += 12 * _clip01(m["consec_pos_yoy"] / ac["trend_window"])
    if pd.notna(m["mean_yoy_6m"]):
        score += 13 * _clip01(m["mean_yoy_6m"] / (ac["mean_yoy_strong"] * 2))
    if pd.notna(m["std_yoy_6m"]):
        score += 10 * _clip01(1 - m["std_yoy_6m"] / ac["yoy_std_high"])
    if m["yoy_accelerating"]:
        score += 10
    s = str(m["seasonality"])
    if "淡季不淡" in s:
        score += 10
    elif "正常" in s:
        score += 5
    return round(min(100.0, score), 1)


def tier(m: dict, cfg: dict) -> str:
    if m["is_cyclical"]:
        return "排除(週期股改看價格/庫存/毛利)"
    ac = cfg["analyze"]
    cum, strong = m["cum_yoy"], ac["cum_yoy_strong"]
    peak_weak = "旺季不旺" in str(m["seasonality"])
    if (pd.notna(cum) and cum >= strong and not m["cum_yoy_declining"]
            and m["consec_pos_yoy"] >= ac["min_positive_months"]):
        return "優選"
    if pd.notna(cum) and cum < 0:
        return "警戒"
    if m["cum_yoy_declining"] and (pd.isna(cum) or cum < strong):
        return "警戒"
    if peak_weak and (pd.isna(m["yoy"]) or m["yoy"] < 0):
        return "警戒"
    return "觀察"


def analyze(data: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """對整份長格式資料跑三層引擎, 回傳最新月份每家公司的動能總表."""
    rows = []
    for _sid, g in data.groupby("stock_id", sort=False):
        if g["revenue"].notna().sum() < 3:
            continue
        m = compute_company_metrics(g, cfg)
        m["pattern"] = classify_pattern(m, cfg)
        m["score"] = momentum_score(m, cfg)
        m["tier"] = tier(m, cfg)
        rows.append(m)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["_k"] = out["score"].fillna(-1)
    out = out.sort_values("_k", ascending=False).drop(columns="_k")
    out = out.reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out
