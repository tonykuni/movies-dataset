"""synth.py -- 產生合成月營收資料, 供離線測試與 demo.

會涵蓋所有動能型態 (穩定成長 / 季節性 / 高波動 / 見頂衰退 / 週期股),
並依真實 MOPS 欄位定義計算 yoy / mom / 累計營收 / 累計YoY,
用來驗證分析引擎的公式與儀表板版面 (免連網)。
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

import datetime as dt
import os

import numpy as np
import pandas as pd

# 週期族群 -> 對應到 config.cyclical_industries 內的產業, 使公司層與族群層一致
_CYC_GROUP_IND = {
    "貨櫃航運": "航運業", "散裝航運": "航運業",
    "鋼鐵": "鋼鐵工業", "條鋼": "鋼鐵工業",
}

# 模擬全市場週期覆蓋: VIA 族群之外的週期公司 (代號, 名稱, MOPS 產業別)
_EXTRA_CYCLICAL = [
    # 水泥 (全上市)
    ("1101", "台泥", "水泥工業"), ("1102", "亞泥", "水泥工業"),
    ("1103", "嘉泥", "水泥工業"), ("1104", "環泥", "水泥工業"),
    ("1108", "幸福", "水泥工業"), ("1109", "信大", "水泥工業"),
    ("1110", "東泥", "水泥工業"),
    # 石化 (塑膠工業 + 油電燃氣)
    ("1301", "台塑", "塑膠工業"), ("1303", "南亞", "塑膠工業"),
    ("1304", "台聚", "塑膠工業"), ("1305", "華夏", "塑膠工業"),
    ("1308", "亞聚", "塑膠工業"), ("1309", "台達化", "塑膠工業"),
    ("1310", "台苯", "塑膠工業"), ("1312", "國喬", "塑膠工業"),
    ("1313", "聯成", "塑膠工業"), ("1314", "中石化", "塑膠工業"),
    ("1326", "台化", "塑膠工業"), ("6505", "台塑化", "油電燃氣業"),
    # 化工
    ("1710", "東聯", "化學工業"), ("1717", "長興", "化學工業"),
    ("1718", "中纖", "化學工業"), ("1722", "台肥", "化學工業"),
    ("1723", "中碳", "化學工業"), ("1727", "中華化", "化學工業"),
    # 鋼鐵 (VIA 之外)
    ("2010", "春源", "鋼鐵工業"), ("2020", "美亞", "鋼鐵工業"),
    ("2022", "聚亨", "鋼鐵工業"), ("2027", "大成鋼", "鋼鐵工業"),
    ("2031", "新光鋼", "鋼鐵工業"), ("2038", "海光", "鋼鐵工業"),
    # 散裝 (VIA 之外) + 航運其他 (港埠/物流/貨代)
    ("2601", "益航", "航運業"),
    ("2607", "榮運", "航運業"), ("2608", "嘉里大榮", "航運業"),
    ("2613", "中櫃", "航運業"), ("2636", "台驊投控", "航運業"),
    ("5609", "中菲行", "航運業"),
    # 其他週期 (橡膠/造紙/玻璃)
    ("2105", "正新", "橡膠工業"), ("2101", "南港", "橡膠工業"),
    ("1907", "永豐餘", "造紙工業"), ("1904", "正隆", "造紙工業"),
    ("1802", "台玻", "玻璃陶瓷"),
]


def _universe_from_groups(cfg: dict):
    """從 groups.csv 建立 demo 宇宙, 涵蓋所有族群成員以填滿族群動能矩陣."""
    from .groups import CYCLICAL_GROUPS
    path = os.path.join(os.path.dirname(__file__), "groups.csv")
    g = pd.read_csv(path, dtype={"stock_id": str}).drop_duplicates("stock_id")
    kinds_by_role = {
        "L": ["stable", "stable", "seasonal"],
        "P": ["stable", "seasonal", "volatile"],
        "G": ["declining", "volatile", "seasonal"],
    }
    uni = []
    for _, r in g.iterrows():
        sid, name, grp, role = r["stock_id"], r["name"], r["group"], r["role"]
        if grp in CYCLICAL_GROUPS:
            kind = "cyclical"
            ind = _CYC_GROUP_IND.get(grp, "鋼鐵工業")
        else:
            opts = kinds_by_role.get(role, ["stable"])
            kind = opts[int(sid) % len(opts)]        # 依代號決定 (可重現)
            ind = grp                                 # 非週期: 產業=族群名
        uni.append((sid, name, ind, kind))
    # 補上 VIA 之外的全市場週期公司 (模擬 MOPS 產業別覆蓋)
    have = {u[0] for u in uni}
    for sid, name, ind in _EXTRA_CYCLICAL:
        if sid not in have:
            uni.append((sid, name, ind, "cyclical"))
    return uni


# 模擬全市場: MOPS 非週期產業別 (真實 fetch 時由 MOPS 頁面自動取得)
_MOPS_INDUSTRIES = [
    "半導體業", "電腦及週邊設備業", "光電業", "通信網路業", "電子零組件業",
    "電子通路業", "資訊服務業", "其他電子業", "電機機械", "電器電纜",
    "食品工業", "紡織纖維", "建材營造", "汽車工業", "生技醫療業",
    "觀光事業", "金融保險", "貿易百貨", "文化創意業", "其他",
]
_CYC_INDUSTRIES = ["水泥工業", "塑膠工業", "鋼鐵工業", "化學工業",
                   "橡膠工業", "造紙工業", "玻璃陶瓷", "油電燃氣業", "航運業"]


def _universe_full_market(cfg):
    """台股全部 + 族群全部: VIA 149 檔 + 週期補充 + 模擬公司補到全市場規模.

    真實 fetch 時全市場自動來自 MOPS; 此函式讓 demo 也具備同等規模,
    以驗證引擎在 ~1,750 檔下的效能與版面。
    """
    uni = _universe_from_groups(cfg)          # VIA 149 檔 + 週期補充
    have = {u[0] for u in uni}
    target = int((cfg.get("demo") or {}).get("universe_size", 1750))
    kinds = ["stable", "seasonal", "volatile", "declining"]
    idx = 0
    for sid in range(1000, 10000):
        if len(uni) >= target:
            break
        s = str(sid)
        if s in have:
            continue
        if idx % 9 == 0:                       # 約 1/9 為週期產業 (貼近實況)
            ind = _CYC_INDUSTRIES[(idx // 9) % len(_CYC_INDUSTRIES)]
            kind = "cyclical"
        else:
            ind = _MOPS_INDUSTRIES[idx % len(_MOPS_INDUSTRIES)]
            kind = kinds[(sid + idx) % 4]
        uni.append((s, f"模擬{s}", ind, kind))
        have.add(s)
        idx += 1
    return uni


# (代號, 名稱, 產業, 型態)  型態: stable/seasonal/volatile/declining/cyclical
# 註: 此為後備清單; make_synthetic 會優先用 groups.csv 建立完整族群宇宙。
_UNIVERSE = [
    ("2330", "台積電",   "半導體業",   "stable"),
    ("2454", "聯發科",   "半導體業",   "stable"),
    ("3034", "聯詠",     "半導體業",   "seasonal"),
    ("2379", "瑞昱",     "半導體業",   "stable"),
    ("3008", "大立光",   "光電業",     "seasonal"),
    ("2308", "台達電",   "電子零組件", "stable"),
    ("2317", "鴻海",     "其他電子業", "seasonal"),
    ("2382", "廣達",     "電腦週邊",   "stable"),
    ("2357", "華碩",     "電腦週邊",   "volatile"),
    ("2412", "中華電",   "通信網路業", "stable"),
    ("3661", "世芯-KY",  "半導體業",   "stable"),
    ("6415", "矽力-KY",  "半導體業",   "declining"),
    ("3231", "緯創",     "電腦週邊",   "stable"),
    ("2376", "技嘉",     "電腦週邊",   "volatile"),
    ("4966", "譜瑞-KY",  "半導體業",   "declining"),
    ("2345", "智邦",     "通信網路業", "stable"),
    ("6669", "緯穎",     "電腦週邊",   "stable"),
    ("3017", "奇鋐",     "電子零組件", "stable"),
    ("2383", "台光電",   "電子零組件", "stable"),
    ("1519", "華城",     "電機機械",   "stable"),
    ("1513", "中興電",   "電機機械",   "seasonal"),
    ("2027", "大成鋼",   "鋼鐵工業",   "cyclical"),
    ("2002", "中鋼",     "鋼鐵工業",   "cyclical"),
    ("1301", "台塑",     "塑膠工業",   "cyclical"),
    ("1303", "南亞",     "塑膠工業",   "cyclical"),
    ("1326", "台化",     "化學工業",   "cyclical"),
    ("2603", "長榮",     "航運業",     "cyclical"),
    ("2609", "陽明",     "航運業",     "cyclical"),
    ("1101", "台泥",     "水泥工業",   "cyclical"),
    ("1102", "亞泥",     "水泥工業",   "cyclical"),
    ("9945", "潤泰新",   "建材營造",   "volatile"),
    ("2915", "潤泰全",   "貿易百貨",   "seasonal"),
    ("1216", "統一",     "食品工業",   "stable"),
    ("2912", "統一超",   "貿易百貨",   "seasonal"),
    ("2207", "和泰車",   "汽車工業",   "declining"),
    ("9910", "豐泰",     "紡織纖維",   "declining"),
    ("2884", "玉山金",   "金融保險",   "stable"),
    ("2603B","範例衰退", "其他業",     "declining"),
    ("8069", "元太",     "光電業",     "volatile"),
    ("3037", "欣興",     "電子零組件", "declining"),
]


def _series(kind, rng, n=48):
    """回傳長度 n 的月營收序列 (需 >36+12 才能算 YoY 與 2年CAGR)."""
    base = rng.uniform(3e6, 8e7)  # 千元
    t = np.arange(n)
    month = (t % 12) + 1
    # 季節性: 電子業旺季在 Q3/Q4
    seas = 1 + 0.18 * np.sin((month - 3) / 12 * 2 * np.pi)

    if kind == "stable":
        trend = (1 + rng.uniform(0.012, 0.022)) ** t     # 穩定月增
        noise = rng.normal(1, 0.03, n)
        s = base * trend * (0.4 + 0.6 * seas) * noise
    elif kind == "seasonal":
        trend = (1 + rng.uniform(0.004, 0.010)) ** t
        noise = rng.normal(1, 0.05, n)
        s = base * trend * seas * noise
    elif kind == "volatile":
        trend = (1 + rng.uniform(0.000, 0.015)) ** t
        noise = rng.normal(1, 0.22, n)                   # 高波動
        s = base * trend * (0.5 + 0.5 * seas) * noise
    elif kind == "declining":
        # 前段成長, 後段動能衰退 (見頂)
        up = (1 + 0.03) ** np.minimum(t, n - 14)
        down = (1 - 0.02) ** np.maximum(0, t - (n - 14))
        noise = rng.normal(1, 0.04, n)
        s = base * up * down * (0.5 + 0.5 * seas) * noise
    elif kind == "cyclical":
        # 價格驅動的長週期 + 大幅波動 (模擬原物料)
        cyc = 1 + 0.5 * np.sin((t + rng.uniform(0, 12)) / 20 * 2 * np.pi)
        noise = rng.normal(1, 0.12, n)
        s = base * cyc * seas * noise
    else:
        s = base * np.ones(n)
    return np.maximum(s, 1e5)


def make_synthetic(cfg: dict, ref: dt.date | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(20260725)
    ref = ref or dt.date(2026, 6, 1)  # 最新資料月份 = 2026-05
    n = 48
    try:
        universe = _universe_full_market(cfg)   # 台股全部 (~1750 檔) 含族群全部
    except Exception:
        universe = _UNIVERSE                     # 後備
    # 建立日期軸 (由舊到新, 最後一個 = 上個月)
    end = dt.date(ref.year, ref.month, 1)
    dates = []
    y, m = end.year, end.month
    m -= 1
    if m == 0:
        y, m = y - 1, 12
    for _ in range(n):
        dates.append(dt.date(y, m, 1))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    dates = list(reversed(dates))

    rows = []
    for sid, name, ind, kind in universe:
        rev = _series(kind, rng, n)
        rev_s = pd.Series(rev)
        for i, d in enumerate(dates):
            r = rev[i]
            prev_m = rev[i - 1] if i >= 1 else np.nan
            prev_y = rev[i - 12] if i >= 12 else np.nan
            mom = (r / prev_m - 1) * 100 if i >= 1 else np.nan
            yoy = (r / prev_y - 1) * 100 if i >= 12 else np.nan
            # 累計營收: 當年 1 月到當月
            ytd_idx = [j for j in range(i + 1) if dates[j].year == d.year]
            cum = rev[ytd_idx].sum()
            # 去年同期累計
            ly_idx = [j for j in range(n)
                      if dates[j].year == d.year - 1 and dates[j].month <= d.month]
            cum_ly = rev[ly_idx].sum() if ly_idx else np.nan
            cum_yoy = (cum / cum_ly - 1) * 100 if ly_idx else np.nan
            rows.append({
                "stock_id": sid, "name": name, "industry": ind,
                "market": "sii", "year": d.year, "month": d.month,
                "date": pd.Timestamp(d),
                "revenue": round(r), "revenue_prev_month": round(prev_m) if i >= 1 else np.nan,
                "revenue_prev_year": round(prev_y) if i >= 12 else np.nan,
                "mom": round(mom, 2) if i >= 1 else np.nan,
                "yoy": round(yoy, 2) if i >= 12 else np.nan,
                "cum_revenue": round(cum),
                "cum_revenue_prev_year": round(cum_ly) if ly_idx else np.nan,
                "cum_yoy": round(cum_yoy, 2) if ly_idx else np.nan,
            })
    df = pd.DataFrame(rows).sort_values(["stock_id", "date"]).reset_index(drop=True)
    # 只保留最近 months_back 個月 (符合 config)
    keep_dates = sorted(df["date"].unique())[-cfg["fetch"]["months_back"]:]
    df = df[df["date"].isin(keep_dates)].reset_index(drop=True)
    return df
