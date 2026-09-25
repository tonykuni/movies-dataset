"""breakout.py -- 真突破偵測 (Genuine Breakout Detection).

目標: 抓出「表現特別優異、創歷史新高、年增率強」的公司,
      並嚴格排除「YoY 高只是因為去年基期低」的假突破。

── 為什麼單看 YoY 會被騙 ────────────────────────────────────
    YoY = 本月營收 / 去年同月營收 − 1
    分母(去年同月)若異常低迷, YoY 會被灌得很漂亮, 但公司實際營收可能
    只是「回到原本的水準」, 根本沒有創新高。這是月營收分析最大的陷阱:
    一家去年崩掉一半的公司, 今年只要回到原點, YoY 就是 +100%。

── 五道關卡 (全過才算真突破) ────────────────────────────────
  關卡 1  ATH        當月營收 = 歷史最高
                     -> 等級面證明: 客觀上比過去任何一個月都大,
                        基期低不低都不影響「現在是史上最強」這個事實。
  關卡 2  TTM ATH    近 12 個月滾動營收也創歷史新高
                     -> 排除單月一次性訂單/出貨集中造成的假高點。
  關卡 3  YoY 強     年增率 >= 門檻 (預設 30%)
  關卡 4  基期不低   (a) 去年同月營收在歷史分布的百分位 >= 門檻
                     (b) 去年同月 / 其前 12 個月中位數 >= 門檻
                     -> 直接檢查分母健康度: 去年那個月是不是塌陷的?
  關卡 5  兩年 CAGR  完全跳過去年基期, 直接和兩年前比, 年化成長 >= 門檻
                     -> 若成長只是從谷底反彈, 兩年 CAGR 會很難看。

任一關卡未過者不會被丟掉, 而是歸入「假突破」清單並標明**是哪一關擋下的**,
讓篩選過程可稽核 — 這份反面清單本身就是濾網有效的證明。

週期股 (原物料) 一律排除: 其營收由價格驅動, ATH 常是價格高點而非需求強度。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# 判定結果 (verdict) 常數
V_REAL = "真突破"
V_LOWBASE = "假突破·低基期"
V_NO_ATH = "高YoY·未創新高"
V_NO_CAGR = "假突破·兩年無成長"
V_ONEOFF = "單月暴衝·TTM未創高"
V_ATH_WEAK_YOY = "創高·YoY未達門檻"
V_CYCLICAL = "排除·週期股"

REJECT_ORDER = [V_LOWBASE, V_NO_CAGR, V_NO_ATH, V_ONEOFF, V_ATH_WEAK_YOY]


def _pct_rank(series: pd.Series, value: float) -> float:
    """value 在 series 中的百分位 (0-100)."""
    s = series.dropna()
    if len(s) == 0 or pd.isna(value):
        return np.nan
    return float((s <= value).sum()) / len(s) * 100.0


def compute_breakout_metrics(g: pd.DataFrame, cfg: dict) -> dict | None:
    """單一公司的突破指標. 歷史不足回 None."""
    bc = cfg["breakout"]
    g = g.sort_values("date").reset_index(drop=True)
    rev = pd.to_numeric(g["revenue"], errors="coerce")
    n = len(g)
    if n < bc["min_history_months"] or rev.notna().sum() < bc["min_history_months"]:
        return None

    latest = g.iloc[-1]
    cur = rev.iloc[-1]
    if pd.isna(cur) or cur <= 0:
        return None

    # ── 關卡 1: 單月創歷史新高 ────────────────────────────────
    prev = rev.iloc[:-1].dropna()
    prev_max = float(prev.max()) if len(prev) else np.nan
    is_ath = bool(pd.notna(prev_max) and cur > prev_max)
    ath_margin = ((cur / prev_max - 1) * 100) if (pd.notna(prev_max) and prev_max > 0) else np.nan
    # 距離前次高點幾個月 (越久代表這次突破越有意義)
    months_since_ath = np.nan
    if len(prev) and pd.notna(prev_max):
        idx = prev[prev == prev_max].index
        if len(idx):
            months_since_ath = int(n - 1 - idx[-1])

    # 連續創高月數: 由最新往回, 連續幾個月都是「當時的歷史新高」
    # -> 持續性指標。一次性暴衝 streak=1; 真正強勢公司會連月刷新紀錄。
    prior_max = rev.shift(1).expanding().max()
    new_high = (rev > prior_max).fillna(False)
    ath_streak = 0
    for v in reversed(new_high.tolist()):
        if v:
            ath_streak += 1
        else:
            break

    # ── 關卡 2: TTM (近12月滾動營收) 創歷史新高 ────────────────
    ttm = rev.rolling(12).sum()
    ttm_cur = ttm.iloc[-1]
    ttm_prev = ttm.iloc[:-1].dropna()
    ttm_prev_max = float(ttm_prev.max()) if len(ttm_prev) else np.nan
    is_ttm_ath = bool(pd.notna(ttm_cur) and pd.notna(ttm_prev_max) and ttm_cur > ttm_prev_max)
    ttm_margin = ((ttm_cur / ttm_prev_max - 1) * 100) \
        if (pd.notna(ttm_cur) and pd.notna(ttm_prev_max) and ttm_prev_max > 0) else np.nan
    # TTM 年增率: 近12月營收 vs 前一個12月 -> 免疫於單月噪音的成長率
    ttm_yoy = np.nan
    if n >= 25 and pd.notna(ttm_cur):
        ttm_ly = ttm.iloc[-13]
        if pd.notna(ttm_ly) and ttm_ly > 0:
            ttm_yoy = (ttm_cur / ttm_ly - 1) * 100

    # ── 關卡 3: 年增率 ───────────────────────────────────────
    yoy = latest.get("yoy", np.nan)
    base = rev.iloc[-13] if n >= 13 else np.nan          # 去年同月營收
    if pd.isna(yoy) and pd.notna(base) and base > 0:
        yoy = (cur / base - 1) * 100

    # ── 關卡 4: 基期品質 (拆穿低基期的核心) ───────────────────
    # (a) 去年同月在「當時為止的歷史」中的百分位
    base_pct = _pct_rank(rev.iloc[:n - 12], base) if n >= 13 else np.nan
    # (b) 去年同月 / 其前 12 個月中位數 -> 那個月是否相對自身水準塌陷
    base_ratio = np.nan
    if n >= 25:
        window = rev.iloc[n - 25:n - 13].dropna()        # 基期月之前的 12 個月
        med = float(window.median()) if len(window) else np.nan
        if pd.notna(med) and med > 0 and pd.notna(base):
            base_ratio = float(base / med)

    # ── 關卡 5: 兩年 CAGR (完全跳過去年基期) ──────────────────
    cagr_2y = np.nan
    if n >= 25:
        base2 = rev.iloc[-25]
        if pd.notna(base2) and base2 > 0:
            cagr_2y = ((cur / base2) ** 0.5 - 1) * 100

    return {
        "stock_id": latest["stock_id"],
        "name": latest.get("name", ""),
        "industry": latest.get("industry", ""),
        "is_cyclical": bool(latest.get("is_cyclical", False)),
        "date": latest["date"],
        "revenue": cur,
        "prev_max_revenue": prev_max,
        "is_ath": is_ath,
        "ath_margin": ath_margin,
        "ath_streak": ath_streak,
        "months_since_prev_ath": months_since_ath,
        "ttm_revenue": ttm_cur,
        "is_ttm_ath": is_ttm_ath,
        "ttm_margin": ttm_margin,
        "ttm_yoy": ttm_yoy,
        "yoy": yoy,
        "base_revenue": base,
        "base_pct": base_pct,
        "base_ratio": base_ratio,
        "cagr_2y": cagr_2y,
        "n_months": n,
    }


def _gates(m: dict, cfg: dict) -> dict:
    """回傳五道關卡的通過與否.

    關卡 2 (持續性) 同時檢查兩件事:
      (a) TTM 創歷史新高  -> 排除單月一次性訂單灌爆
      (b) TTM 年增率達標  -> 排除「單月很強但整年其實是平的」
          (只看 (a) 會讓 TTM 只是微幅刷新的公司矇混過關)
    """
    bc = cfg["breakout"]
    ttm_ok = bool(m["is_ttm_ath"]) if bc["require_ttm_ath"] else True
    min_ttm_yoy = bc.get("min_ttm_yoy")
    if min_ttm_yoy is not None:
        ttm_ok = ttm_ok and bool(pd.notna(m["ttm_yoy"]) and m["ttm_yoy"] >= min_ttm_yoy)
    return {
        "g1_ath": bool(m["is_ath"]),
        "g2_ttm_ath": ttm_ok,
        "g3_yoy": bool(pd.notna(m["yoy"]) and m["yoy"] >= bc["min_yoy"]),
        "g4_base": bool(
            pd.notna(m["base_pct"]) and m["base_pct"] >= bc["min_base_pct"]
            and pd.notna(m["base_ratio"]) and m["base_ratio"] >= bc["min_base_ratio"]),
        "g5_cagr": bool(pd.notna(m["cagr_2y"]) and m["cagr_2y"] >= bc["min_cagr_2y"]),
    }


def _verdict(m: dict, gates: dict) -> str:
    """判定 + 指出是哪一關擋下的 (優先報告最具診斷價值的原因)."""
    if m["is_cyclical"]:
        return V_CYCLICAL
    if all(gates.values()):
        return V_REAL
    # 低基期是最重要的診斷: 高 YoY 但基期塌陷
    if gates["g3_yoy"] and not gates["g4_base"]:
        return V_LOWBASE
    if gates["g3_yoy"] and not gates["g5_cagr"]:
        return V_NO_CAGR
    if gates["g3_yoy"] and not gates["g1_ath"]:
        return V_NO_ATH
    if gates["g3_yoy"] and not gates["g2_ttm_ath"]:
        return V_ONEOFF
    return ""      # 非候選 (YoY 未達門檻)


def breakout_score(m: dict, cfg: dict) -> float:
    """真突破強度 0-100. 透明加權, 便於稽核.

    創高幅度 15 + TTM 創高幅度 15 + 連續創高 10
    + 單月YoY 15 + TTM YoY 15          (成長力道: 單月與平滑各半)
    + 基期品質 20                       (分母健康度 — 反低基期的核心)
    + 兩年CAGR 10                       (跳過基期的長期驗證)
    """
    bc = cfg["breakout"]
    s = 0.0
    # 滿分門檻依實測分布校準 (ath_margin 中位 ~7%, ttm_margin 中位 ~4%),
    # 否則分數會全擠在中段、拉不開強弱。
    s += 15 * _c(m["ath_margin"] / 10.0)              # 超越前高 10% = 滿分
    s += 15 * _c(m["ttm_margin"] / 5.0)               # TTM 超越 5% = 滿分
    s += 10 * _c(m["ath_streak"] / 6.0)               # 連6個月刷新紀錄 = 滿分
    s += 15 * _c(m["yoy"] / (bc["min_yoy"] * 2))
    s += 15 * _c(m["ttm_yoy"] / bc["min_yoy"])        # TTM YoY 達門檻 = 滿分
    if pd.notna(m["base_ratio"]):
        s += 10 * _c(m["base_pct"] / 100.0)
        s += 10 * _c((m["base_ratio"] - bc["min_base_ratio"]) / 0.30)
    s += 10 * _c(m["cagr_2y"] / (bc["min_cagr_2y"] * 2))
    return round(min(100.0, s), 1)


def _c(x) -> float:
    if x is None or pd.isna(x):
        return 0.0
    return float(max(0.0, min(1.0, x)))


def detect(data: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """全市場真突破偵測.

    回傳候選池 (YoY 達門檻 或 已創新高 的公司), 含 verdict 與各關卡欄位。
    verdict == '真突破' 者依 breakout_score 排序。
    """
    bc = cfg["breakout"]
    rows = []
    for _sid, g in data.groupby("stock_id", sort=False):
        m = compute_breakout_metrics(g, cfg)
        if m is None:
            continue
        gates = _gates(m, cfg)
        v = _verdict(m, gates)
        # 候選池: YoY 達門檻, 或雖未達但已創歷史新高 (仍值得看)
        if not v and not m["is_ath"]:
            continue
        if not v:
            v = V_ATH_WEAK_YOY      # 創高但 YoY 未達門檻
        m.update(gates)
        m["verdict"] = v
        m["score"] = breakout_score(m, cfg) if v == V_REAL else np.nan
        m["gates_passed"] = int(sum(gates.values()))
        rows.append(m)

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out["_k"] = out["score"].fillna(-1)
    out = out.sort_values(["_k", "yoy"], ascending=[False, False]).drop(columns="_k")
    out = out.reset_index(drop=True)
    out.insert(0, "rank", range(1, len(out) + 1))
    return out


def summary(bo: pd.DataFrame) -> dict:
    """給儀表板用的統計."""
    if bo is None or bo.empty:
        return {"real": 0, "lowbase": 0, "candidates": 0, "no_cagr": 0,
                "no_ath": 0, "oneoff": 0}
    return {
        "candidates": len(bo),
        "real": int((bo["verdict"] == V_REAL).sum()),
        "lowbase": int((bo["verdict"] == V_LOWBASE).sum()),
        "no_cagr": int((bo["verdict"] == V_NO_CAGR).sum()),
        "no_ath": int((bo["verdict"] == V_NO_ATH).sum()),
        "oneoff": int((bo["verdict"] == V_ONEOFF).sum()),
    }
