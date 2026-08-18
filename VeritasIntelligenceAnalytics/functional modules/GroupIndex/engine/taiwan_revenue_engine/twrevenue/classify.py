"""classify.py -- 產業分類 + 原物料/週期股全市場分流.

核心原則 (Tony 的要求):
    原物料、週期性產業「不看月營收」。
    月營收 = 價格 x 量, 而原物料價格波動遠大於量, 加上庫存循環、
    合約制、批次出貨, 使月營收 YoY/MoM 嚴重失真。

全市場六大週期類 (TWSE + TPEX 全部覆蓋):
    水泥 / 鋼鐵 / 石化 / 化工 / 貨櫃航運 / 散裝航運
    + 其他週期 (橡膠、造紙、玻璃、其他航運等)

歸類方式:
    1. fetcher 解析 MOPS 頁面「產業別」標題 -> 每家公司自動帶 industry,
       全市場零遺漏, 免手工維護名單。
    2. 產業別 -> 週期類 對映 (SECTOR_BY_INDUSTRY)。
    3. 航運業無法從產業別區分貨櫃/散裝/航空 -> 以代號清單細分;
       航空 (客運) 豁免於週期分流 (照 VIA 分類以族群動能對待)。
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

import pandas as pd

# ---- MOPS 產業別 -> 六大週期類 對映 (上市/上櫃產業名一致) ----
SECTOR_BY_INDUSTRY = {
    "水泥工業": "水泥",
    "鋼鐵工業": "鋼鐵",
    "塑膠工業": "石化",
    "油電燃氣業": "石化",     # 台塑化等煉油/油品
    "化學工業": "化工",
    "化學生技醫療": None,     # 上櫃混類, 不自動歸週期 (避免誤殺生技)
    # 其他週期 (不在六大類但仍不宜用月營收)
    "橡膠工業": "其他週期",
    "造紙工業": "其他週期",
    "玻璃陶瓷": "其他週期",
}

# ---- 航運業細分 (產業別只有「航運業」一種, 需以代號分流) ----
CONTAINER_SHIPPING = {"2603", "2609", "2615"}                       # 長榮/陽明/萬海
BULK_SHIPPING = {"2601", "2605", "2606", "2612", "2617",
                 "2637", "2641", "5608"}                             # 益航/新興/裕民/中航/台航/慧洋/正德/四維航
AIRLINES = {"2610", "2618", "2646"}                                  # 華航/長榮航/星宇 -> 豁免週期

# 六大類固定顯示順序
SECTOR_ORDER = ["水泥", "鋼鐵", "石化", "化工",
                "貨櫃航運", "散裝航運", "航運其他", "其他週期"]


def _sector_of(stock_id: str, industry: str) -> str | None:
    """回傳週期類名稱; 非週期回 None."""
    sid = str(stock_id)
    if sid in AIRLINES:
        return None                      # 航空豁免 (照族群動能對待)
    if sid in CONTAINER_SHIPPING:
        return "貨櫃航運"
    if sid in BULK_SHIPPING:
        return "散裝航運"
    ind = str(industry) if pd.notna(industry) else ""
    if ind == "航運業":
        return "航運其他"                # 港埠/物流/貨代等
    return SECTOR_BY_INDUSTRY.get(ind)


def tag_cyclical(df: pd.DataFrame, cyclical_industries: list[str]) -> pd.DataFrame:
    """標記 is_cyclical 與 cyclical_sector (全市場六大類).

    is_cyclical: cyclical_sector 非空即為週期股 (排除於月營收動能排名)。
    cyclical_industries (config) 仍相容: 列於其中且未被對映的產業歸「其他週期」。
    """
    df = df.copy()
    if "industry" not in df.columns:
        df["industry"] = ""
    df["industry"] = df["industry"].fillna("")

    extra = set(cyclical_industries or []) - set(SECTOR_BY_INDUSTRY)
    sectors = []
    for sid, ind in zip(df["stock_id"].astype(str), df["industry"]):
        s = _sector_of(sid, ind)
        if s is None and ind in extra and sid not in AIRLINES:
            s = "其他週期"
        sectors.append(s)
    df["cyclical_sector"] = sectors
    df["is_cyclical"] = df["cyclical_sector"].notna()
    return df


# 給週期股的替代分析提示 (取代月營收)
CYCLICAL_PLAYBOOK = {
    "primary":   "價格 YoY (現貨/期貨/ASP) > 10% => 週期回升",
    "demand":    "庫存 YoY < 0 => 需求回溫",
    "strength":  "產能利用率 > 85% => 景氣強",
    "profit":    "毛利率 YoY > 0 => 獲利週期回升",
    "note":      "月營收僅供參考, 不作為主要買賣判準。",
}
