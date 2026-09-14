"""intl.py -- 國際產業分類對照 (GICS / yfinance / ICB).

── 三套標準的真實關係 (常被混淆, 先講清楚) ──────────────────
  GICS  Global Industry Classification Standard
        S&P Dow Jones Indices + MSCI 共同維護, 最近改版 2023-03。
        11 sectors / 25 industry groups / 74 industries / 163 sub-industries
        -> **S&P 500 與道瓊工業指數用的就是這一套**。
        所以「S&P 500 的分類」和「Dow Jones 的分類」其實是同一套 = GICS。

  ICB   Industry Classification Benchmark
        11 industries / 20 supersectors / 45 sectors / 173 subsectors
        曾是 Dow Jones + FTSE 各半合資, 但 **Dow Jones 於 2011 年賣掉持股**,
        現由 FTSE Russell 維護 (FTSE、STOXX 指數採用)。
        -> 今天的 Dow Jones 已經不用 ICB 了。

  yfinance
        回傳的 sector/industry 來自 Yahoo Finance, 而 Yahoo 採用的是
        **Morningstar Global Equity Classification**, 不是 GICS。
        3 super sectors / 11 sectors / 55 industry groups / 145 industries
        11 個 sector 與 GICS 可一對一對應, 但**名稱不同**
        (GICS: Information Technology -> Yahoo: Technology 等)。
        直接拿 yfinance 的 sector 字串去比對 GICS 會全部對不上。

Morningstar 的 3 個 super sector (Cyclical / Defensive / Sensitive) 在概念上
與台股慣用的三分法 (電子 / 非電子 / 金融) 是同一層級的粗分, 故本模組同時輸出,
方便做「台股電子權重 vs S&P 500 Information Technology 權重」這類跨市場比較。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# ── GICS 11 sectors (S&P 500 / Dow Jones) ───────────────────
GICS_SECTORS = {
    "10": "Energy", "15": "Materials", "20": "Industrials",
    "25": "Consumer Discretionary", "30": "Consumer Staples",
    "35": "Health Care", "40": "Financials",
    "45": "Information Technology", "50": "Communication Services",
    "55": "Utilities", "60": "Real Estate",
}
GICS_CODE = {v: k for k, v in GICS_SECTORS.items()}
GICS_ZH = {
    "Energy": "能源", "Materials": "原物料", "Industrials": "工業",
    "Consumer Discretionary": "非必需消費", "Consumer Staples": "必需消費",
    "Health Care": "醫療保健", "Financials": "金融",
    "Information Technology": "資訊科技", "Communication Services": "通訊服務",
    "Utilities": "公用事業", "Real Estate": "不動產",
}

# ── GICS -> yfinance (Morningstar) sector, 一對一但名稱不同 ──
GICS_TO_YF = {
    "Information Technology": "Technology",
    "Financials": "Financial Services",
    "Health Care": "Healthcare",
    "Consumer Discretionary": "Consumer Cyclical",
    "Consumer Staples": "Consumer Defensive",
    "Industrials": "Industrials",
    "Energy": "Energy",
    "Materials": "Basic Materials",
    "Real Estate": "Real Estate",
    "Utilities": "Utilities",
    "Communication Services": "Communication Services",
}
YF_TO_GICS = {v: k for k, v in GICS_TO_YF.items()}

# ── Morningstar 3 super sectors (yfinance 的最上層) ──────────
YF_SUPER = {
    "Basic Materials": "Cyclical", "Consumer Cyclical": "Cyclical",
    "Financial Services": "Cyclical", "Real Estate": "Cyclical",
    "Consumer Defensive": "Defensive", "Healthcare": "Defensive",
    "Utilities": "Defensive",
    "Communication Services": "Sensitive", "Energy": "Sensitive",
    "Industrials": "Sensitive", "Technology": "Sensitive",
}
YF_SUPER_ZH = {"Cyclical": "景氣循環", "Defensive": "防禦", "Sensitive": "景氣敏感"}

# ── GICS -> ICB industry (FTSE Russell) ─────────────────────
# 除 Communication Services 外皆可一對一; ICB 把電信與媒體拆在不同 industry。
GICS_TO_ICB = {
    "Information Technology": "Technology",
    "Communication Services": "Telecommunications",   # 媒體部分實屬 ICB Consumer Discretionary
    "Health Care": "Health Care",
    "Financials": "Financials",
    "Real Estate": "Real Estate",
    "Consumer Discretionary": "Consumer Discretionary",
    "Consumer Staples": "Consumer Staples",
    "Industrials": "Industrials",
    "Materials": "Basic Materials",
    "Energy": "Energy",
    "Utilities": "Utilities",
}
ICB_SPLIT_NOTE = {"Communication Services":
                  "ICB 將電信業者歸 Telecommunications、媒體娛樂歸 Consumer Discretionary, 非一對一"}

# ── TWSE/TPEX 正式產業別 -> GICS sector ──────────────────────
# (gics_sector, mixed, note)  mixed=True 表示該產業內部跨多個 GICS sector,
# 預設取佔比最大者, 個別公司以 GICS_OVERRIDE_BY_TICKER 修正。
_M = True
GICS_BY_INDUSTRY: dict[str, tuple[str, bool, str]] = {
    # 電子 -> Information Technology
    "半導體業":         ("Information Technology", False, ""),
    "電腦及週邊設備業": ("Information Technology", False, ""),
    "光電業":           ("Information Technology", False, ""),
    "電子零組件業":     ("Information Technology", False, ""),
    "電子通路業":       ("Information Technology", False, "GICS: Technology Distributors"),
    "資訊服務業":       ("Information Technology", False, ""),
    "其他電子業":       ("Information Technology", False, ""),
    "數位雲端":         ("Information Technology", False, ""),
    "通信網路業":       ("Information Technology", _M,
                        "設備商屬 IT、電信業者屬 Communication Services (見 ticker 覆寫)"),
    "電子工業":         ("Information Technology", _M, "歷史混類, 未細分"),
    # 金融
    "金融保險":         ("Financials", False, ""),
    # 原物料 -> Materials
    "水泥工業":         ("Materials", False, ""),
    "塑膠工業":         ("Materials", False, ""),
    "化學工業":         ("Materials", False, ""),
    "鋼鐵工業":         ("Materials", False, ""),
    "造紙工業":         ("Materials", False, ""),
    "玻璃陶瓷":         ("Materials", False, ""),
    # 工業
    "電機機械":         ("Industrials", False, ""),
    "電器電纜":         ("Industrials", False, ""),
    "航運業":           ("Industrials", False, "GICS: Marine / Passenger Airlines 皆屬 Industrials"),
    "綜合":             ("Industrials", False, "GICS: Industrial Conglomerates"),
    "綠能環保":         ("Industrials", _M,
                        "環保服務屬 Industrials、太陽能電池屬 IT、再生電力屬 Utilities"),
    # 非必需消費
    "汽車工業":         ("Consumer Discretionary", False, ""),
    "橡膠工業":         ("Consumer Discretionary", False, "GICS: 輪胎屬 Automobile Components"),
    "觀光餐旅":         ("Consumer Discretionary", False, ""),
    "運動休閒":         ("Consumer Discretionary", False, ""),
    "居家生活":         ("Consumer Discretionary", False, ""),
    "電子商務":         ("Consumer Discretionary", False, "GICS: Broadline Retail"),
    "紡織纖維":         ("Consumer Discretionary", _M,
                        "成衣紡織屬 Consumer Discretionary、上游化纖屬 Materials"),
    "貿易百貨":         ("Consumer Discretionary", _M,
                        "百貨零售屬 Consumer Discretionary、超商食品通路屬 Consumer Staples"),
    # 必需消費
    "食品工業":         ("Consumer Staples", False, ""),
    "農業科技業":       ("Consumer Staples", False, ""),
    # 醫療
    "生技醫療業":       ("Health Care", False, ""),
    # 通訊服務
    "文化創意業":       ("Communication Services", False, "GICS: Media & Entertainment"),
    # 公用事業 / 能源
    "油電燃氣業":       ("Utilities", _M, "燃氣電力屬 Utilities、煉油屬 Energy (見 ticker 覆寫)"),
    # 不動產
    "建材營造":         ("Real Estate", _M,
                        "開發商屬 Real Estate、營造工程屬 Industrials"),
    # 無法對應
    "其他":             ("", _M, "未分類"),
    "化學生技醫療":     ("", _M, "歷史混類: 化學屬 Materials、生技屬 Health Care, 不強制歸類"),
}

# 個別公司覆寫 (產業別內跨 GICS sector 的已知案例)
#   ticker -> (GICS sector, 允許套用的產業別集合, 公司名)
# **以產業別設防**: 只有當該檔的正式產業別確實落在預期集合時才覆寫。
# 避免代號被重新配發、或資料異常時, 覆寫套到不相干的公司身上。
GICS_OVERRIDE_BY_TICKER: dict[str, tuple[str, frozenset, str]] = {
    # 電信業者 (產業別為通信網路業, 但 GICS 屬 Communication Services)
    "2412": ("Communication Services", frozenset({"通信網路業"}), "中華電"),
    "3045": ("Communication Services", frozenset({"通信網路業"}), "台灣大"),
    "4904": ("Communication Services", frozenset({"通信網路業"}), "遠傳"),
    # 煉油 (產業別為油電燃氣業, 但 GICS 屬 Energy)
    "6505": ("Energy", frozenset({"油電燃氣業"}), "台塑化"),
    # 食品通路 (產業別為貿易百貨, 但 GICS 屬 Consumer Staples)
    "2912": ("Consumer Staples", frozenset({"貿易百貨"}), "統一超"),
    "5903": ("Consumer Staples", frozenset({"貿易百貨"}), "全家"),
}


def gics_of(industry_canon, stock_id=None) -> tuple[str, bool, str]:
    """正式產業別 (+可選代號) -> (GICS sector, mixed, note)."""
    canon = None
    if industry_canon is not None and not (
            isinstance(industry_canon, float) and pd.isna(industry_canon)):
        canon = str(industry_canon)

    sid = str(stock_id) if stock_id is not None else None
    if sid and sid in GICS_OVERRIDE_BY_TICKER:
        sector, expect, who = GICS_OVERRIDE_BY_TICKER[sid]
        if canon in expect:
            return sector, False, f"ticker 覆寫 ({who})"
        # 產業別與預期不符 -> 不套用覆寫, 退回依產業別對映
    if canon is None:
        return "", True, "未知產業"
    return GICS_BY_INDUSTRY.get(canon, ("", True, "未對應"))


def yf_ticker(stock_id, market=None, industry=None) -> str:
    """台股代號 -> yfinance ticker (.TW 上市 / .TWO 上櫃).

    market 可為 '上市'/'上櫃'/'sii'/'otc'; 未給時預設 .TW。
    """
    sid = str(stock_id).strip()
    m = str(market or "").strip()
    otc = m in ("上櫃", "otc", "OTC", "TWO", ".TWO")
    return f"{sid}.TWO" if otc else f"{sid}.TW"


def attach(df: pd.DataFrame) -> pd.DataFrame:
    """補上 gics_sector / gics_code / gics_zh / yf_sector / yf_super / icb_industry
    / gics_mixed / gics_note。需先經 taxonomy.attach (要有 industry_canon)。"""
    df = df.copy()
    canon = df.get("industry_canon", pd.Series([None] * len(df), index=df.index))
    sids = df.get("stock_id", pd.Series([None] * len(df), index=df.index)).astype(str)

    trip = [gics_of(c, s) for c, s in zip(canon, sids)]
    df["gics_sector"] = [t[0] for t in trip]
    df["gics_mixed"] = [t[1] for t in trip]
    df["gics_note"] = [t[2] for t in trip]
    df["gics_code"] = df["gics_sector"].map(GICS_CODE).fillna("")
    df["gics_zh"] = df["gics_sector"].map(GICS_ZH).fillna("")
    df["yf_sector"] = df["gics_sector"].map(GICS_TO_YF).fillna("")
    df["yf_super"] = df["yf_sector"].map(YF_SUPER).fillna("")
    df["yf_super_zh"] = df["yf_super"].map(YF_SUPER_ZH).fillna("")
    df["icb_industry"] = df["gics_sector"].map(GICS_TO_ICB).fillna("")
    if "market" in df.columns:
        df["yf_ticker"] = [yf_ticker(s, m) for s, m in zip(sids, df["market"])]
    else:
        df["yf_ticker"] = [yf_ticker(s) for s in sids]
    return df


def crosswalk() -> pd.DataFrame:
    """完整對照表: TWSE/TPEX 產業別 -> GICS -> yfinance -> ICB."""
    rows = []
    for canon, (g, mixed, note) in GICS_BY_INDUSTRY.items():
        rows.append({
            "twse_tpex": canon,
            "gics_code": GICS_CODE.get(g, ""),
            "gics_sector": g,
            "gics_zh": GICS_ZH.get(g, ""),
            "yf_sector": GICS_TO_YF.get(g, ""),
            "yf_super": YF_SUPER.get(GICS_TO_YF.get(g, ""), ""),
            "icb_industry": GICS_TO_ICB.get(g, ""),
            "mixed": mixed, "note": note,
        })
    return pd.DataFrame(rows)


def rollup(analysis: pd.DataFrame, level: str, cfg: dict) -> pd.DataFrame:
    """依國際分類彙總營收動能 (營收加權), 與台灣階層同一套算法.

    level: 'gics_sector' | 'yf_sector' | 'yf_super' | 'icb_industry'
    """
    from .taxonomy import rollup as _tw_rollup
    if level not in analysis:
        return pd.DataFrame()
    s = analysis[level].astype("string")
    df = analysis[s.notna() & (s.str.strip() != "")]
    if df.empty:
        return pd.DataFrame()
    return _tw_rollup(df, level, cfg)


def unmapped(analysis: pd.DataFrame) -> pd.DataFrame:
    """未對映到 GICS 的公司 (產業別為「其他」或未知). 供治理檢視, 不靜默丟棄."""
    if "gics_sector" not in analysis:
        return pd.DataFrame()
    s = analysis["gics_sector"].astype("string")
    return analysis[s.isna() | (s.str.strip() == "")]


def audit() -> dict:
    """對照表自我稽核."""
    from .taxonomy import HIERARCHY
    missing = [c for c in HIERARCHY if c not in GICS_BY_INDUSTRY]
    bad_gics = {c: g for c, (g, _m, _n) in GICS_BY_INDUSTRY.items()
                if g and g not in GICS_CODE}
    yf_missing = [g for g in GICS_CODE if g not in GICS_TO_YF]
    icb_missing = [g for g in GICS_CODE if g not in GICS_TO_ICB]
    super_missing = [y for y in GICS_TO_YF.values() if y not in YF_SUPER]
    bad_override = {k: v[0] for k, v in GICS_OVERRIDE_BY_TICKER.items()
                    if v[0] not in GICS_CODE}
    # 覆寫的預期產業別必須是合法正式名
    from .taxonomy import HIERARCHY as _H
    bad_expect = {k: sorted(set(v[1]) - set(_H)) for k, v in GICS_OVERRIDE_BY_TICKER.items()
                  if set(v[1]) - set(_H)}
    if bad_expect:
        bad_override.update(bad_expect)
    return {"n_industry": len(GICS_BY_INDUSTRY), "n_gics": len(GICS_CODE),
            "n_override": len(GICS_OVERRIDE_BY_TICKER),
            "missing_industry": missing, "bad_gics": bad_gics,
            "yf_missing": yf_missing, "icb_missing": icb_missing,
            "super_missing": super_missing, "bad_override": bad_override,
            "mixed": sorted(c for c, (_g, m, _n) in GICS_BY_INDUSTRY.items() if m)}
