"""taxonomy.py -- 台灣產業分類階層 SSOT (TWSE / TPEX 整合治理).

三層階層:
    L1 大類   電子 / 非電子 / 金融          (台股慣用的三分法)
    L2 中類   電子八大次產業、原物料、民生消費、機電工業 …
    L3 小類   TWSE / TPEX 官方產業別 (正規化後的標準名)

── 為什麼需要正規化 (SSOT 同義字治理) ──────────────────────
TWSE 與 TPEX 的產業別名稱並不一致, 不處理會讓同一種產業在兩個市場被切成兩群:

  1. 後綴差異   建材營造 / 建材營造業 · 金融保險 / 金融保險業 ·
                貿易百貨 / 貿易百貨業 · 其他 / 其他業
  2. 歷史更名   觀光事業 -> 觀光餐旅
  3. 上櫃專有   文化創意業 · 農業科技業 · 電子商務 (TWSE 官方 33 類不含這三類)
  4. 歷史混類   化學生技醫療 (舊代碼 07, 後拆為 化學工業 + 生技醫療業)
                電子工業     (舊代碼 13, 後拆為 半導體業…其他電子業 八類)

混類 (4) 一律標記 ambiguous=True 且**不強制拆解** — 硬歸到化學工業會把生技股
誤判成原物料週期股 (實際踩過的坑)。

資料來源: 臺灣證券交易所「上市公司產業類別劃分暨調整要點」(33 類)
         + 證券編碼分類查詢 (上市/上櫃/公開發行通用代碼 01-38)
"""
from __future__ import annotations

import re

import numpy as np
import pandas as pd

L1_ELEC, L1_NONELEC, L1_FIN = "電子", "非電子", "金融"

# ── L3 正式產業別 -> (L1 大類, L2 中類) ─────────────────────
# 電子八大次產業 = TWSE 電子類指數成分 (代碼 24-31), 台股慣用定義。
HIERARCHY: dict[str, tuple[str, str]] = {
    # ── 電子 ──────────────────────────────────────────────
    "半導體業":          (L1_ELEC, "半導體"),
    "電腦及週邊設備業":  (L1_ELEC, "電腦及週邊"),
    "光電業":            (L1_ELEC, "光電"),
    "通信網路業":        (L1_ELEC, "通信網路"),
    "電子零組件業":      (L1_ELEC, "電子零組件"),
    "電子通路業":        (L1_ELEC, "電子通路"),
    "資訊服務業":        (L1_ELEC, "資訊服務"),
    "其他電子業":        (L1_ELEC, "其他電子"),
    # 數位雲端 (2023 新增) 非電子類指數八大成分, 但性質屬科技基礎建設 -> 歸電子。
    "數位雲端":          (L1_ELEC, "數位雲端"),

    # ── 金融 ──────────────────────────────────────────────
    "金融保險":          (L1_FIN, "金融保險"),

    # ── 非電子 · 原物料 (與週期六大類高度重疊) ───────────────
    "水泥工業":          (L1_NONELEC, "原物料"),
    "塑膠工業":          (L1_NONELEC, "原物料"),
    "化學工業":          (L1_NONELEC, "原物料"),
    "鋼鐵工業":          (L1_NONELEC, "原物料"),
    "橡膠工業":          (L1_NONELEC, "原物料"),
    "造紙工業":          (L1_NONELEC, "原物料"),
    "玻璃陶瓷":          (L1_NONELEC, "原物料"),
    "油電燃氣業":        (L1_NONELEC, "原物料"),
    # ── 非電子 · 機電工業 ─────────────────────────────────
    "電機機械":          (L1_NONELEC, "機電工業"),
    "電器電纜":          (L1_NONELEC, "機電工業"),
    "汽車工業":          (L1_NONELEC, "機電工業"),
    # ── 非電子 · 民生消費 ─────────────────────────────────
    "食品工業":          (L1_NONELEC, "民生消費"),
    "紡織纖維":          (L1_NONELEC, "民生消費"),
    "貿易百貨":          (L1_NONELEC, "民生消費"),
    "觀光餐旅":          (L1_NONELEC, "民生消費"),
    "居家生活":          (L1_NONELEC, "民生消費"),
    "運動休閒":          (L1_NONELEC, "民生消費"),
    "電子商務":          (L1_NONELEC, "民生消費"),   # 名為電子, 實為零售通路
    # ── 非電子 · 其他中類 ─────────────────────────────────
    "航運業":            (L1_NONELEC, "運輸"),
    "建材營造":          (L1_NONELEC, "建材營造"),
    "生技醫療業":        (L1_NONELEC, "生技醫療"),
    "綠能環保":          (L1_NONELEC, "綠能環保"),
    "農業科技業":        (L1_NONELEC, "農業科技"),
    "文化創意業":        (L1_NONELEC, "文化創意"),
    "綜合":              (L1_NONELEC, "其他"),
    "其他":              (L1_NONELEC, "其他"),
    # ── 歷史混類 (不強制拆解, 標記 ambiguous) ───────────────
    "化學生技醫療":      (L1_NONELEC, "混類(化學/生技)"),
    "電子工業":          (L1_ELEC, "混類(電子未細分)"),
}

# 歷史混類: 無法安全歸入單一中類, 不得自動當原物料週期處理
AMBIGUOUS = {"化學生技醫療", "電子工業"}

# 上櫃專有類別 (TWSE 官方 33 類不含)
TPEX_ONLY = {"文化創意業", "農業科技業", "電子商務"}

# ── 同義字 / 別名 -> 正式名 (SSOT 正規化) ────────────────────
ALIASES: dict[str, str] = {
    # 後綴差異 (TWSE vs TPEX vs 證券編碼)
    "建材營造業": "建材營造", "金融保險業": "金融保險",
    "貿易百貨業": "貿易百貨", "其他業": "其他",
    "綜合企業": "綜合", "農業科技": "農業科技業",
    "文化創意": "文化創意業", "生技醫療": "生技醫療業",
    # 歷史更名
    "觀光事業": "觀光餐旅", "觀光": "觀光餐旅", "觀光餐飲": "觀光餐旅",
    # 電子次產業簡稱 (含 VIA 族群命名)
    "半導體": "半導體業", "電腦及週邊": "電腦及週邊設備業",
    "電腦週邊": "電腦及週邊設備業", "電腦及周邊設備業": "電腦及週邊設備業",
    "光電": "光電業", "通信網路": "通信網路業", "電信": "通信網路業",
    "電子零組件": "電子零組件業", "電子通路": "電子通路業",
    "資訊服務": "資訊服務業", "其他電子": "其他電子業",
    # 其他常見簡稱
    "鋼鐵": "鋼鐵工業", "水泥": "水泥工業", "塑膠": "塑膠工業",
    "化學": "化學工業", "橡膠": "橡膠工業", "造紙": "造紙工業",
    "食品": "食品工業", "紡織": "紡織纖維", "汽車": "汽車工業",
    "航運": "航運業", "金融": "金融保險", "油電燃氣": "油電燃氣業",
    "玻璃": "玻璃陶瓷",
}

_STRIP = re.compile(r"[\s　()（）]+")


def normalize(name) -> str | None:
    """產業別 -> 正式名. 未知回 None.

    比對順序: 精確 -> 別名 -> 去空白/括號後精確 -> 去空白後別名 -> 補「業」字。
    """
    if name is None or (isinstance(name, float) and pd.isna(name)):
        return None
    s = str(name).strip()
    if not s:
        return None
    if s in HIERARCHY:
        return s
    if s in ALIASES:
        return ALIASES[s]
    t = _STRIP.sub("", s)
    if t in HIERARCHY:
        return t
    if t in ALIASES:
        return ALIASES[t]
    if t + "業" in HIERARCHY:          # 「半導體」-> 「半導體業」
        return t + "業"
    if t.endswith("業") and t[:-1] in HIERARCHY:
        return t[:-1]
    return None


def levels(name) -> tuple[str | None, str | None, str | None]:
    """回傳 (L3 正式名, L1 大類, L2 中類); 未知回 (None, None, None)."""
    canon = normalize(name)
    if canon is None:
        return None, None, None
    l1, l2 = HIERARCHY[canon]
    return canon, l1, l2


def attach(df: pd.DataFrame, col: str = "industry") -> pd.DataFrame:
    """為資料表補上 industry_canon / sector_l1 / sector_l2 / industry_ambiguous."""
    df = df.copy()
    if col not in df.columns:
        df[col] = np.nan
    uniq = {v: levels(v) for v in pd.unique(df[col].astype(object))}
    df["industry_canon"] = df[col].map(lambda v: uniq.get(v, (None, None, None))[0])
    df["sector_l1"] = df[col].map(lambda v: uniq.get(v, (None, None, None))[1])
    df["sector_l2"] = df[col].map(lambda v: uniq.get(v, (None, None, None))[2])
    df["industry_ambiguous"] = df["industry_canon"].isin(AMBIGUOUS)
    # 未知產業歸入「其他」, 但保留 unknown 旗標供治理檢視
    df["industry_unknown"] = df["industry_canon"].isna() & df[col].notna()
    df.loc[df["industry_canon"].isna(), ["industry_canon", "sector_l1", "sector_l2"]] = \
        ["其他", L1_NONELEC, "其他"]
    return df


# ── 階層彙總 (營收加權) ────────────────────────────────────
def rollup(analysis: pd.DataFrame, level: str, cfg: dict,
           parent: str | None = None) -> pd.DataFrame:
    """依 L1 / L2 / L3 彙總營收動能 (加總 = 營收加權, 與族群層一致).

    level:  'sector_l1' | 'sector_l2' | 'industry_canon'
    parent: 限定上層 (例: level='sector_l2', parent='電子')
    """
    df = analysis
    if parent is not None:
        up = {"sector_l2": "sector_l1", "industry_canon": "sector_l2"}[level]
        df = df[df[up] == parent]
    if df.empty:
        return pd.DataFrame()

    ac = cfg["analyze"]
    rows = []
    for key, g in df.groupby(level, sort=False):
        cov = g.dropna(subset=["cum_yoy"])
        n_cov = len(cov)

        def _sum(c):
            return cov[c].dropna().sum() if c in cov else np.nan

        rev, rev_ly = _sum("revenue"), _sum("revenue_prev_year")
        cum, cum_ly = _sum("cum_revenue"), _sum("cum_revenue_prev_year")
        agg_yoy = ((rev / rev_ly - 1) * 100) if rev_ly and rev_ly > 0 else np.nan
        agg_cum = ((cum / cum_ly - 1) * 100) if cum_ly and cum_ly > 0 else np.nan
        noncyc = cov[~cov["is_cyclical"]] if "is_cyclical" in cov else cov
        med_score = float(noncyc["score"].dropna().median()) \
            if len(noncyc) and noncyc["score"].notna().any() else np.nan
        breadth = float((cov["yoy"] > 0).mean()) * 100 if n_cov else np.nan
        n_cyc = int(cov["is_cyclical"].sum()) if "is_cyclical" in cov else 0

        if n_cov and n_cyc == n_cov:
            verdict = "週期(改看價格/庫存)"
        elif pd.isna(agg_cum):
            verdict = "資料不足"
        elif agg_cum >= ac["cum_yoy_strong"] and (breadth or 0) >= 60:
            verdict = "族群加速"
        elif agg_cum < 0 or (breadth or 0) < 40:
            verdict = "族群轉弱"
        else:
            verdict = "分歧/中性"

        rows.append({
            "key": key, "level": level,
            "members": len(g), "covered": n_cov,
            "n_cyclical": n_cyc,
            "revenue": rev,
            "agg_cum_yoy": round(agg_cum, 1) if pd.notna(agg_cum) else np.nan,
            "agg_yoy": round(agg_yoy, 1) if pd.notna(agg_yoy) else np.nan,
            "score": round(med_score, 1) if pd.notna(med_score) else np.nan,
            "breadth_pos": round(breadth, 0) if pd.notna(breadth) else np.nan,
            "n_pref": int((cov["tier"] == "優選").sum()) if n_cov else 0,
            "n_warn": int((cov["tier"] == "警戒").sum()) if n_cov else 0,
            "verdict": verdict,
        })

    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # 依營收體量排序 (大類看體量比看分數有意義)
    return out.sort_values("revenue", ascending=False).reset_index(drop=True)


L1_ORDER = [L1_ELEC, L1_NONELEC, L1_FIN]


def audit() -> dict:
    """SSOT 自我稽核: 別名是否都指向合法正式名、階層是否完整."""
    bad_alias = {k: v for k, v in ALIASES.items() if v not in HIERARCHY}
    bad_l1 = {k: v[0] for k, v in HIERARCHY.items() if v[0] not in L1_ORDER}
    # 別名不可與正式名衝突 (同一字串既是正式名又被當別名指向別處)
    conflict = {k for k in ALIASES if k in HIERARCHY}
    return {"n_canon": len(HIERARCHY), "n_alias": len(ALIASES),
            "bad_alias": bad_alias, "bad_l1": bad_l1, "conflict": conflict,
            "ambiguous": sorted(AMBIGUOUS), "tpex_only": sorted(TPEX_ONLY)}
