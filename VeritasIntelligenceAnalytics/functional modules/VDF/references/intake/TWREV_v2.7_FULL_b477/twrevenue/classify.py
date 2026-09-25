"""classify.py -- 產業分類 + 原物料/週期股全市場分流.

核心原則: 原物料、週期性產業「不看月營收」。
    月營收 = 價格 x 量, 而原物料價格波動遠大於量, 加上庫存循環、
    合約制、批次出貨, 使月營收 YoY/MoM 嚴重失真。

全市場六大週期類 (TWSE + TPEX 全覆蓋):
    水泥 / 鋼鐵 / 石化 / 化工 / 貨櫃航運 / 散裝航運
    + 航運其他、其他週期 (橡膠、造紙、玻璃)

歸類方式:
    1. fetcher 解析 MOPS「產業別」標題 -> 每家公司自動帶 industry, 全市場零遺漏。
    2. 產業別 -> 週期類 對映 (SECTOR_BY_INDUSTRY)。
    3. 航運業無法由產業別區分貨櫃/散裝/航空 -> 以代號清單細分;
       航空 (客運) 豁免於週期分流。
"""
from __future__ import annotations

import pandas as pd

SECTOR_BY_INDUSTRY = {
    "水泥工業": "水泥",
    "鋼鐵工業": "鋼鐵",
    "塑膠工業": "石化",
    "油電燃氣業": "石化",
    "化學工業": "化工",
    "化學生技醫療": None,     # 上櫃混類, 不自動歸週期 (避免誤殺生技)
    "橡膠工業": "其他週期",
    "造紙工業": "其他週期",
    "玻璃陶瓷": "其他週期",
}

CONTAINER_SHIPPING = {"2603", "2609", "2615"}                  # 長榮/陽明/萬海
BULK_SHIPPING = {"2601", "2605", "2606", "2612", "2617",
                 "2637", "2641", "5608"}
AIRLINES = {"2610", "2618", "2646"}                            # 航空 -> 豁免

SECTOR_ORDER = ["水泥", "鋼鐵", "石化", "化工",
                "貨櫃航運", "散裝航運", "航運其他", "其他週期"]


def _sector_of(stock_id: str, industry) -> str | None:
    """industry 先經 SSOT 正規化, 故 TWSE/TPEX 命名差異 (觀光事業/觀光餐旅、
    建材營造/建材營造業…) 不會造成歸類分裂。"""
    from .taxonomy import normalize
    sid = str(stock_id)
    if sid in AIRLINES:
        return None
    if sid in CONTAINER_SHIPPING:
        return "貨櫃航運"
    if sid in BULK_SHIPPING:
        return "散裝航運"
    ind = normalize(industry) or (str(industry) if pd.notna(industry) else "")
    if ind == "航運業":
        return "航運其他"
    return SECTOR_BY_INDUSTRY.get(ind)


def tag_cyclical(df: pd.DataFrame, cyclical_industries: list[str]) -> pd.DataFrame:
    """標記 is_cyclical / cyclical_sector, 並補上產業階層 (L1/L2/L3)."""
    from .taxonomy import attach, normalize
    df = df.copy()
    if "industry" not in df.columns:
        df["industry"] = ""
    df["industry"] = df["industry"].fillna("")
    df = attach(df, "industry")          # industry_canon / sector_l1 / sector_l2

    extra = {normalize(x) or x for x in (cyclical_industries or [])} - set(SECTOR_BY_INDUSTRY)
    sectors = []
    for sid, ind in zip(df["stock_id"].astype(str), df["industry"]):
        s = _sector_of(sid, ind)
        if s is None and (normalize(ind) or ind) in extra and sid not in AIRLINES:
            s = "其他週期"
        sectors.append(s)
    df["cyclical_sector"] = sectors
    df["is_cyclical"] = df["cyclical_sector"].notna()

    from .intl import attach as intl_attach      # GICS / yfinance / ICB 對照
    df = intl_attach(df)
    return df


CYCLICAL_PLAYBOOK = {
    "primary":  "價格 YoY (現貨/期貨/ASP) > 10% => 週期回升",
    "demand":   "庫存 YoY < 0 => 需求回溫",
    "strength": "產能利用率 > 85% => 景氣強",
    "profit":   "毛利率 YoY > 0 => 獲利週期回升",
}
