"""synth.py -- 產生合成月營收資料, 供離線測試與 demo.

涵蓋所有動能型態, 並刻意內建三組**已知答案 (ground truth)** 的突破測試案例,
用來驗證真突破偵測器確實能分辨「真創高」與「低基期假象」:

  9001/9002/9003  breakout_real  真突破
      持續加速成長, 當月=歷史新高, TTM 也創高, 基期健康, 兩年 CAGR 強。
      -> 五關全過, 應判 真突破

  9101/9102       lowbase_fake   低基期假突破
      前段平穩 -> 約一年前崩到 45% -> 現在回到原本水準。
      YoY +120% 很漂亮, 但: 沒創高、基期百分位極低、兩年 CAGR ≈ 0。
      -> 應判 假突破·低基期  (這正是要抓的陷阱)

  9201            oneoff_spike   單月暴衝
      基期健康、兩年 CAGR 佳、當月創高, 但近期營收走弱, 單月爆量
      使 TTM 仍低於歷史高點。 -> 應判 單月暴衝·TTM未創高
"""
from __future__ import annotations

import datetime as dt
import os

import numpy as np
import pandas as pd

_CYC_GROUP_IND = {"貨櫃航運": "航運業", "散裝航運": "航運業",
                  "鋼鐵": "鋼鐵工業", "條鋼": "鋼鐵工業"}

# VIA 族群是「題材」, 不是「產業別」— 一個題材可橫跨多個官方產業。
# demo 需給每個族群一個具代表性的官方 MOPS 產業別, 才能真實走過
# 產業階層與國際對照的對映路徑 (真實 fetch 時產業別直接來自 MOPS 頁面)。
_VIA_GROUP_INDUSTRY = {
    "半導體": "半導體業", "AI 伺服器": "電腦及週邊設備業", "金融": "金融保險",
    "被動元件": "電子零組件業", "光學": "光電業", "機器人": "電機機械",
    "散熱": "電子零組件業", "BBU 備援電池": "電子零組件業",
    "CPO 共封裝光學": "光電業", "低軌衛星": "通信網路業", "航空": "航運業",
    "重電": "電機機械", "軍工航太": "其他電子業", "ABF 載板": "電子零組件業",
    "記憶體": "半導體業", "PCB": "電子零組件業", "台積電擴廠": "其他電子業",
    "生技醫療": "生技醫療業", "IC設計": "半導體業", "電源管理": "電子零組件業",
    "ASIC 設計服務": "半導體業", "矽智財 IP": "半導體業",
    "網通設備": "通信網路業", "電動車": "汽車工業", "觀光餐飲": "觀光餐旅",
    "半導體設備": "半導體業", "資安/系統整合": "資訊服務業",
    "CoWoS": "半導體業", "充電樁": "電子零組件業",
    "矽晶圓": "半導體業", "第三代半導體": "半導體業", "晶圓代工": "半導體業",
    "CDMO": "生技醫療業", "離岸風電": "電機機械", "太陽能": "光電業",
    "ADAS車用電子": "汽車工業",
    # 兩階層細分後新增的 L2 子族群
    "AI OEM/ODM": "電腦及週邊設備業", "AI 機殼/機櫃": "電子零組件業",
    "AI 導軌/滑軌": "電子零組件業", "液冷/水冷板": "電子零組件業",
    "封測 OSAT": "半導體業", "測試介面/探針卡": "半導體業",
    "半導體材料/耗材": "半導體業", "半導體通路/代理": "電子通路業",
}

# 刻意混入 TWSE / TPEX / 歷史 的命名變體, 用來驗證 SSOT 正規化確實生效:
#   建材營造業 / 金融保險業 / 貿易百貨業 (TPEX 後綴) · 觀光事業 (歷史更名)
#   文化創意業 / 農業科技業 / 電子商務 (上櫃專有) · 化學生技醫療 (歷史混類)
_MOPS_INDUSTRIES = [
    "半導體業", "電腦及週邊設備業", "光電業", "通信網路業", "電子零組件業",
    "電子通路業", "資訊服務業", "其他電子業", "數位雲端",
    "電機機械", "電器電纜", "汽車工業",
    "食品工業", "紡織纖維", "貿易百貨業", "觀光事業", "居家生活", "運動休閒",
    "建材營造業", "生技醫療業", "金融保險業", "綠能環保",
    "文化創意業", "農業科技業", "電子商務", "化學生技醫療", "綜合", "其他業",
]
_CYC_INDUSTRIES = ["水泥工業", "塑膠工業", "鋼鐵工業", "化學工業",
                   "橡膠工業", "造紙工業", "玻璃陶瓷", "油電燃氣業", "航運業"]

# VIA 之外的全市場週期公司 (模擬 MOPS 產業別覆蓋)
_EXTRA_CYCLICAL = [
    ("1101", "台泥", "水泥工業"), ("1102", "亞泥", "水泥工業"),
    ("1103", "嘉泥", "水泥工業"), ("1104", "環泥", "水泥工業"),
    ("1108", "幸福", "水泥工業"), ("1109", "信大", "水泥工業"),
    ("1110", "東泥", "水泥工業"),
    ("1301", "台塑", "塑膠工業"), ("1303", "南亞", "塑膠工業"),
    ("1304", "台聚", "塑膠工業"), ("1305", "華夏", "塑膠工業"),
    ("1308", "亞聚", "塑膠工業"), ("1309", "台達化", "塑膠工業"),
    ("1310", "台苯", "塑膠工業"), ("1312", "國喬", "塑膠工業"),
    ("1313", "聯成", "塑膠工業"), ("1314", "中石化", "塑膠工業"),
    ("1326", "台化", "塑膠工業"), ("6505", "台塑化", "油電燃氣業"),
    ("1710", "東聯", "化學工業"), ("1717", "長興", "化學工業"),
    ("1718", "中纖", "化學工業"), ("1722", "台肥", "化學工業"),
    ("1723", "中碳", "化學工業"), ("1727", "中華化", "化學工業"),
    ("2010", "春源", "鋼鐵工業"), ("2020", "美亞", "鋼鐵工業"),
    ("2022", "聚亨", "鋼鐵工業"), ("2027", "大成鋼", "鋼鐵工業"),
    ("2031", "新光鋼", "鋼鐵工業"), ("2038", "海光", "鋼鐵工業"),
    ("2601", "益航", "航運業"), ("2607", "榮運", "航運業"),
    ("2608", "嘉里大榮", "航運業"), ("2613", "中櫃", "航運業"),
    ("2636", "台驊投控", "航運業"), ("5609", "中菲行", "航運業"),
    ("2105", "正新", "橡膠工業"), ("2101", "南港", "橡膠工業"),
    ("1907", "永豐餘", "造紙工業"), ("1904", "正隆", "造紙工業"),
    ("1802", "台玻", "玻璃陶瓷"),
]

# ── 已知答案的突破測試案例 (ground truth) ───────────────────────
GT_BREAKOUT = {
    "9001": "breakout_real", "9002": "breakout_real", "9003": "breakout_real",
    "9101": "lowbase_fake", "9102": "lowbase_fake",
    "9201": "oneoff_spike",
}
_GT_META = [
    ("9001", "真突破甲", "半導體業"), ("9002", "真突破乙", "電子零組件業"),
    ("9003", "真突破丙", "電機機械"),
    ("9101", "低基期假象甲", "光電業"), ("9102", "低基期假象乙", "紡織纖維"),
    ("9201", "單月暴衝甲", "其他電子業"),
]
# 讓真突破名單出現熟悉的名字: 指定幾檔 VIA 個股走 breakout_real
_VIA_BREAKOUT = {"3661", "2454", "1519", "3081"}


def _series(kind, rng, n=48):
    """長度 n 的月營收序列 (需 >36+12 才能算 YoY 與 2年CAGR)."""
    base = rng.uniform(3e6, 8e7)
    t = np.arange(n)
    month = (t % 12) + 1
    seas = 1 + 0.18 * np.sin((month - 3) / 12 * 2 * np.pi)

    if kind == "stable":
        s = base * (1 + rng.uniform(0.012, 0.022)) ** t * (0.4 + 0.6 * seas) \
            * rng.normal(1, 0.03, n)
    elif kind == "seasonal":
        s = base * (1 + rng.uniform(0.004, 0.010)) ** t * seas * rng.normal(1, 0.05, n)
    elif kind == "volatile":
        s = base * (1 + rng.uniform(0.0, 0.015)) ** t * (0.5 + 0.5 * seas) \
            * rng.normal(1, 0.22, n)
    elif kind == "declining":
        up = (1 + 0.03) ** np.minimum(t, n - 14)
        down = (1 - 0.02) ** np.maximum(0, t - (n - 14))
        s = base * up * down * (0.5 + 0.5 * seas) * rng.normal(1, 0.04, n)
    elif kind == "cyclical":
        cyc = 1 + 0.5 * np.sin((t + rng.uniform(0, 12)) / 20 * 2 * np.pi)
        s = base * cyc * seas * rng.normal(1, 0.12, n)

    # ── 突破測試案例 (低噪音, 確保判定穩定可重現) ──────────────
    elif kind == "breakout_real":
        # 持續成長 + 近6個月加速 -> 當月與 TTM 皆創高, 基期健康, 2年CAGR 強
        g = (1 + 0.022) ** t
        accel = np.where(t >= n - 6, (1 + 0.05) ** (t - (n - 6)), 1.0)
        s = base * g * accel * (0.85 + 0.15 * seas) * rng.normal(1, 0.015, n)
    elif kind == "lowbase_fake":
        # 平穩 -> 約一年前崩到 45% -> 回復原水準 (YoY 爆高但沒創高)
        s = np.full(n, base, dtype=float)
        s[n - 18:n - 9] = base * 0.45          # 崩盤區間涵蓋去年同月 (index n-13)
        s[n - 9:] = base * np.linspace(0.70, 1.00, 9)
        s = s * rng.normal(1, 0.02, n)
    elif kind == "oneoff_spike":
        # 基期健康 + 兩年前較低 -> 近期走弱 -> 當月單筆暴衝創高但 TTM 未創高
        s = np.full(n, base, dtype=float)
        s[:n - 24] = base * 0.80               # 兩年前較低 -> 2年CAGR 佳
        s[n - 11:n - 1] = base * 0.80          # 近期走弱 (不含去年同月)
        s[n - 1] = base * 2.0                  # 單月暴衝
        s = s * rng.normal(1, 0.015, n)
    else:
        s = base * np.ones(n)
    return np.maximum(s, 1e5)


def _universe_from_groups(cfg: dict):
    from .groups import CYCLICAL_GROUPS
    path = os.path.join(os.path.dirname(__file__), "groups.csv")
    from . import csvio
    g = csvio.read(path, dtype={"stock_id": str}).drop_duplicates("stock_id")
    kinds_by_role = {"L": ["stable", "stable", "seasonal"],
                     "P": ["stable", "seasonal", "volatile"],
                     "G": ["declining", "volatile", "seasonal"]}
    uni = []
    for _, r in g.iterrows():
        sid, name, grp, role = r["stock_id"], r["name"], r["group"], r["role"]
        # 真實 fetch 只涵蓋上市(sii)+上櫃(otc); 興櫃不在 MOPS t21sc03 範圍內。
        # demo 也照此略過, 讓儀表板誠實顯示「無營收資料(未涵蓋)」。
        if str(r.get("market", "")).strip() == "興櫃":
            continue
        if grp in CYCLICAL_GROUPS:
            ind = _CYC_GROUP_IND.get(grp, "鋼鐵工業")
            kind = "cyclical"
        else:
            ind = _VIA_GROUP_INDUSTRY.get(grp, "其他")   # 題材 -> 代表性官方產業別
            opts = kinds_by_role.get(role) or ["stable", "seasonal", "volatile"]
            kind = "breakout_real" if sid in _VIA_BREAKOUT else opts[int(sid) % len(opts)]
        mkt = "otc" if str(r.get("market", "")).strip() == "上櫃" else "sii"
        uni.append((sid, name, ind, kind, mkt))
    have = {u[0] for u in uni}
    for sid, name, ind in _EXTRA_CYCLICAL:
        if sid not in have:
            uni.append((sid, name, ind, "cyclical", "sii"))
    return uni


def _universe_full_market(cfg):
    """台股全部 + 族群全部 + 突破 ground truth, 補到全市場規模."""
    uni = _universe_from_groups(cfg)
    have = {u[0] for u in uni}
    for sid, name, ind in _GT_META:          # 已知答案測試案例
        if sid not in have:
            uni.append((sid, name, ind, GT_BREAKOUT[sid], "sii"))
            have.add(sid)

    target = int((cfg.get("demo") or {}).get("universe_size", 1750))
    kinds = ["stable", "seasonal", "volatile", "declining"]
    idx = 0
    for sid in range(1000, 10000):
        if len(uni) >= target:
            break
        s = str(sid)
        if s in have:
            continue
        if idx % 9 == 0:
            ind, kind = _CYC_INDUSTRIES[(idx // 9) % len(_CYC_INDUSTRIES)], "cyclical"
        elif idx % 53 == 7:                   # 少量低基期假象散佈全市場
            ind, kind = _MOPS_INDUSTRIES[idx % len(_MOPS_INDUSTRIES)], "lowbase_fake"
        elif idx % 71 == 11:                  # 少量真突破散佈全市場
            ind, kind = _MOPS_INDUSTRIES[idx % len(_MOPS_INDUSTRIES)], "breakout_real"
        else:
            ind, kind = _MOPS_INDUSTRIES[idx % len(_MOPS_INDUSTRIES)], kinds[(sid + idx) % 4]
        uni.append((s, f"模擬{s}", ind, kind, "otc" if idx % 3 == 0 else "sii"))
        have.add(s)
        idx += 1
    return uni


def make_synthetic(cfg: dict, ref: dt.date | None = None) -> pd.DataFrame:
    rng = np.random.default_rng(20260725)
    ref = ref or dt.date(2026, 6, 1)
    n = 48
    try:
        universe = _universe_full_market(cfg)
    except Exception:
        universe = _universe_from_groups(cfg)

    end = dt.date(ref.year, ref.month, 1)
    dates, y, m = [], end.year, end.month - 1
    if m == 0:
        y, m = y - 1, 12
    for _ in range(n):
        dates.append(dt.date(y, m, 1))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    dates = list(reversed(dates))

    rows = []
    for sid, name, ind, kind, mkt in universe:
        rev = _series(kind, rng, n)
        for i, d in enumerate(dates):
            r = rev[i]
            prev_m = rev[i - 1] if i >= 1 else np.nan
            prev_y = rev[i - 12] if i >= 12 else np.nan
            mom = (r / prev_m - 1) * 100 if i >= 1 else np.nan
            yoy = (r / prev_y - 1) * 100 if i >= 12 else np.nan
            ytd = [j for j in range(i + 1) if dates[j].year == d.year]
            cum = rev[ytd].sum()
            ly = [j for j in range(n)
                  if dates[j].year == d.year - 1 and dates[j].month <= d.month]
            cum_ly = rev[ly].sum() if ly else np.nan
            cum_yoy = (cum / cum_ly - 1) * 100 if ly else np.nan
            rows.append({
                "stock_id": sid, "name": name, "industry": ind, "market": mkt,
                "year": d.year, "month": d.month, "date": pd.Timestamp(d),
                "revenue": round(r),
                "revenue_prev_month": round(prev_m) if i >= 1 else np.nan,
                "revenue_prev_year": round(prev_y) if i >= 12 else np.nan,
                "mom": round(mom, 2) if i >= 1 else np.nan,
                "yoy": round(yoy, 2) if i >= 12 else np.nan,
                "cum_revenue": round(cum),
                "cum_revenue_prev_year": round(cum_ly) if ly else np.nan,
                "cum_yoy": round(cum_yoy, 2) if ly else np.nan,
            })
    df = pd.DataFrame(rows).sort_values(["stock_id", "date"]).reset_index(drop=True)
    return df
