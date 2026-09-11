"""analyze.py -- 三層動能分析引擎.

Layer 1 (主判準)   累計 YoY (cum_yoy)       -- 年度大局錨點, 最不易被騙
Layer 2 (第二判準) 多月 YoY 趨勢            -- 成長品質 (連續正月數/均值/波動)
Layer 3 (第三判準) MoM vs 季節性            -- 動能拐點 (淡季不淡/旺季不旺)
輔助                2 年 CAGR                -- 修正基期扭曲

每家公司會被:
  1. 計算上述指標 (以「最新月份」為基準, 並回看歷史);
  2. 給一個綜合動能分數 (0-100, 僅非週期股);
  3. 分到一個「動能型態」: 穩定成長 / 季節性 / 高波動 / 見頂衰退;
  4. 若為原物料/週期股 -> 不排名, 標記提示改看價格/庫存/毛利率。

所有公式對應 MOPS 官方欄位, 不自行重算 (直接採官方 YoY/MoM/累計YoY),
另外用歷史序列自行計算「趨勢、波動、季節性、CAGR」等衍生指標。
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# ----------------------------------------------------------------------------
#  衍生指標計算 (逐公司)
# ----------------------------------------------------------------------------
def _linear_slope(y: np.ndarray) -> float:
    """回傳序列的線性斜率 (最小平方). 用來判斷累計YoY是加速還是減速."""
    n = len(y)
    if n < 2:
        return 0.0
    x = np.arange(n)
    xm, ym = x.mean(), y.mean()
    denom = ((x - xm) ** 2).sum()
    if denom == 0:
        return 0.0
    return float(((x - xm) * (y - ym)).sum() / denom)


def _consecutive_positive(series: pd.Series) -> int:
    """由最新月份往回, 連續 > 0 的月數."""
    count = 0
    for v in reversed(series.tolist()):
        if pd.notna(v) and v > 0:
            count += 1
        else:
            break
    return count


def _seasonal_flag(g: pd.DataFrame, min_years: int) -> str:
    """MoM vs 季節性: 判斷 淡季不淡 / 旺季不旺 / 正常.

    作法: 對每個「月份(1-12)」算歷史平均 MoM 當季節性基準, 再看最新月的
    實際 MoM 相對其季節性基準的偏離。
    """
    if g["mom"].notna().sum() < min_years * 6:
        return "資料不足"
    latest = g.iloc[-1]
    mth = int(latest["month"])
    hist = g[(g["month"] == mth) & (g.index != g.index[-1])]["mom"].dropna()
    if len(hist) < min_years:
        return "資料不足"
    baseline = hist.mean()          # 該月的季節性常態 MoM
    actual = latest["mom"]
    if pd.isna(actual):
        return "資料不足"
    # 這個月歷史上偏強還是偏弱 (相對全年)?
    all_mom_mean = g["mom"].dropna().mean()
    is_peak_season = baseline > all_mom_mean       # 旺季月
    diff = actual - baseline
    if is_peak_season:
        # 旺季: 實際遠低於季節常態 => 旺季不旺 (警訊)
        return "旺季不旺(警訊)" if diff < -5 else "旺季正常"
    else:
        # 淡季: 實際明顯高於季節常態 => 淡季不淡 (強訊)
        return "淡季不淡(強訊)" if diff > 5 else "淡季正常"


def compute_company_metrics(g: pd.DataFrame, cfg: dict) -> dict:
    """對單一公司的歷史序列, 計算最新一期的動能指標."""
    ac = cfg["analyze"]
    g = g.sort_values("date").reset_index(drop=True)
    latest = g.iloc[-1]

    yoy = g["yoy"]
    cum = g["cum_yoy"]
    win = ac["trend_window"]

    # ---- Layer 1: 累計 YoY ----
    cum_yoy_now = latest.get("cum_yoy", np.nan)
    cum_recent = cum.dropna().tail(ac["cum_yoy_decline_months"] + 1)
    cum_declining = (
        len(cum_recent) >= 2 and all(np.diff(cum_recent.values) < 0)
    )
    cum_slope = _linear_slope(cum.dropna().tail(win).values)

    # ---- Layer 2: 多月 YoY 趨勢 ----
    yoy_recent = yoy.dropna().tail(win)
    consec_pos = _consecutive_positive(yoy)
    mean_yoy = float(yoy_recent.mean()) if len(yoy_recent) else np.nan
    std_yoy = float(yoy_recent.std(ddof=0)) if len(yoy_recent) > 1 else np.nan
    # YoY 加速 = 近3月均值 > 前3月均值
    last3 = yoy.dropna().tail(3).mean()
    prev3 = yoy.dropna().tail(6).head(3).mean()
    yoy_accel = bool(pd.notna(last3) and pd.notna(prev3) and last3 > prev3)

    # ---- Layer 3: MoM vs 季節性 ----
    season = _seasonal_flag(g, ac["seasonality_min_years"])

    # ---- 2 年 CAGR (基期修正) ----
    cagr = np.nan
    ny = ac["cagr_years"]
    if len(g) > 12 * ny:
        rev_now = latest.get("revenue", np.nan)
        rev_base = g.iloc[-1 - 12 * ny].get("revenue", np.nan)
        if pd.notna(rev_now) and pd.notna(rev_base) and rev_base > 0:
            cagr = (rev_now / rev_base) ** (1 / ny) - 1
            cagr *= 100

    return {
        "stock_id": latest["stock_id"],
        "name": latest.get("name", ""),
        "industry": latest.get("industry", ""),
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


# ----------------------------------------------------------------------------
#  型態分群 + 綜合分數
# ----------------------------------------------------------------------------
def classify_pattern(m: dict, cfg: dict) -> str:
    ac = cfg["analyze"]
    cum = m["cum_yoy"]
    mean_yoy = m["mean_yoy_6m"]
    std_yoy = m["std_yoy_6m"]

    if m["is_cyclical"]:
        return "原物料/週期(不看月營收)"

    # 見頂/衰退型: 累計YoY下滑且已低於門檻, 或 旺季不旺且YoY轉弱
    weak_now = pd.isna(cum) or cum < ac["cum_yoy_strong"]
    peak_signal = "旺季不旺" in str(m["seasonality"])
    if (m["cum_yoy_declining"] and weak_now) or (peak_signal and (pd.isna(m["yoy"]) or m["yoy"] < 0)):
        return "見頂/動能衰退型"

    # 高波動訂單型
    if pd.notna(std_yoy) and std_yoy >= ac["yoy_std_high"]:
        return "高波動訂單型"

    # 穩定成長型 (若動能減速但仍強 -> 成長趨緩型)
    if (pd.notna(cum) and cum >= ac["cum_yoy_strong"]
            and m["consec_pos_yoy"] >= ac["min_positive_months"]
            and pd.notna(mean_yoy) and mean_yoy >= ac["mean_yoy_strong"]):
        if m["cum_yoy_declining"] or not m["yoy_accelerating"]:
            return "成長趨緩型" if m["cum_yoy_declining"] else "穩定成長型"
        return "穩定成長型"

    # 季節性明顯型: 累計YoY向上但單月YoY擺動
    if pd.notna(cum) and cum > 0 and m["cum_yoy_slope"] >= 0:
        return "季節性/緩成長型"

    return "中性/觀察型"


def momentum_score(m: dict, cfg: dict) -> float:
    """綜合動能分數 0-100 (僅非週期股). 透明加權, 便於稽核.

    權重: Layer1 累計YoY 45 / Layer2 多月趨勢 35 / Layer3 季節+加速 20。
    """
    if m["is_cyclical"]:
        return np.nan
    ac = cfg["analyze"]
    score = 0.0

    # Layer 1 (45): 累計YoY 水準 (35) + 未下滑/斜率 (10)
    cum = m["cum_yoy"]
    if pd.notna(cum):
        score += 35 * _clip01(cum / (ac["cum_yoy_strong"] * 3))  # 30% 封頂
    if not m["cum_yoy_declining"]:
        score += 5
    if m["cum_yoy_slope"] > 0:
        score += 5

    # Layer 2 (35): 連續正月數 (12) + 平均YoY (13) + 低波動 (10)
    score += 12 * _clip01(m["consec_pos_yoy"] / ac["trend_window"])
    if pd.notna(m["mean_yoy_6m"]):
        score += 13 * _clip01(m["mean_yoy_6m"] / (ac["mean_yoy_strong"] * 2))
    if pd.notna(m["std_yoy_6m"]):
        # 波動越低分越高
        score += 10 * _clip01(1 - m["std_yoy_6m"] / ac["yoy_std_high"])

    # Layer 3 (20): YoY 加速 (10) + 季節訊號 (10)
    if m["yoy_accelerating"]:
        score += 10
    s = str(m["seasonality"])
    if "淡季不淡" in s:
        score += 10
    elif "旺季不旺" in s:
        score += 0
    elif "正常" in s:
        score += 5

    return round(min(100.0, score), 1)


def _clip01(x: float) -> float:
    if pd.isna(x):
        return 0.0
    return float(max(0.0, min(1.0, x)))


def tier(m: dict, cfg: dict) -> str:
    """決策分級: 優選 / 觀察 / 警戒 / 排除(週期)."""
    if m["is_cyclical"]:
        return "排除(週期股改看價格/庫存/毛利)"
    ac = cfg["analyze"]
    cum = m["cum_yoy"]
    strong = ac["cum_yoy_strong"]
    peak_weak = "旺季不旺" in str(m["seasonality"])

    # 優選: 累計YoY強、未連續下滑、連續正YoY
    if (pd.notna(cum) and cum >= strong
            and not m["cum_yoy_declining"]
            and m["consec_pos_yoy"] >= ac["min_positive_months"]):
        return "優選"
    # 警戒: 真正的弱 — 累計YoY轉負、或由高轉低已跌破門檻、或旺季不旺且YoY為負
    if pd.notna(cum) and cum < 0:
        return "警戒"
    if m["cum_yoy_declining"] and (pd.isna(cum) or cum < strong):
        return "警戒"
    if peak_weak and (pd.isna(m["yoy"]) or m["yoy"] < 0):
        return "警戒"
    return "觀察"


# ----------------------------------------------------------------------------
#  主入口
# ----------------------------------------------------------------------------
def analyze(data: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """對整份長格式資料跑三層引擎, 回傳「最新月份」每家公司的動能總表."""
    rows = []
    for _sid, g in data.groupby("stock_id", sort=False):
        if g["revenue"].notna().sum() < 3:
            continue  # 歷史太短, 跳過
        m = compute_company_metrics(g, cfg)
        m["pattern"] = classify_pattern(m, cfg)
        m["score"] = momentum_score(m, cfg)
        m["tier"] = tier(m, cfg)
        rows.append(m)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # 排名: 非週期股依分數; 週期股放最後
    out["_rankkey"] = out["score"].fillna(-1)
    out = out.sort_values("_rankkey", ascending=False).drop(columns="_rankkey")
    out = out.reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out
