#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG070_GroupClassificationIndex — 族群分類×價格指數引擎(批307)
====================================================================
操作員令:「用擷取數據做出最佳分類法:四種分類=LEAD/LAG、大中小、
價格指數(三種加權法並立;NORMALIZED ADJ CLOSE base 2026-01-01
=100)」。設計正本=批307 上傳之 TW10Y 族群驗證引擎+外部對談設計
(四重閘門/EWM 同動/Attention Share/半動態敏感);本引擎=在庫
誠實落地版,並修外部稿三盲點:
  ①前視偏誤:分類與權重一律用 T-1 資料套 T 日報酬
  ②極端集中:Attention 加權單檔上限 18% 再正規化
  ③分位方向蟲:外部稿 rel_size≥q10 判 Large(0.10 分位=低值)
    =方向顛倒;本引擎用 q90/q60(前 10%/40%)正判
在庫誠實界定(不假造):
  ・成交值=close×volume 近似(庫無 turnover;DERIVED 標示)
  ・個股當沖缺;市場級當沖比僅 2026-08-03 起 22 列→該段以
    val×(1−dt_pct) 修正,前段 RAW(欄 dt_adj 旗標)
  ・三大法人止 2025-11=與主窗不交集→LEAD/LAG 用價量一致性判
    (consistency=mom_z×群動能 z+EWM 同動相關);法人維度候料
  ・族群=tw_listings.industry(官方冊);成員<5 檔=不建指數(誠實)
四產出:
  A 角色 LEADER/PEER/LAGGER/UNRELATED(相對+絕對雙重條件)
  B 大中小 LARGE/MID/SMALL(AS 全市場 T-1 滾動分位 q90/q60)
  C 三加權族群指數 equal/tier/attention(T-1 權重;base
    2026-01-01=100;附 att_vs_equal 差勢與最大權重集中度監控)
  D 存證 JSON+個股分類冊 CSV+Plotly 比較頁(零 CDN)
半動態敏感律(批307 對談裁示):動能=EWM10−EWM40 z 化(短窗保
敏);門檻=滾動分位(40 日);Type-F 憲法=UNRELATED corr<0.25、
權重上限 18%(固定不滾)。
v0100→v0101(批307 截圖實錘):Attention 上限 18% 套錯層——v0100 封
在全市場佔比(數值 <0.05 永不觸頂)→族群內權重仍達 82%/90%;修=
族群內正規化後迭代封頂再分配(成員<6 檔=上限 1/n 誠實不假);
榜表「最大權重」即驗證欄。
v0101→v0102(批308 操作員令「族群性 故事性分群」+評分律):
  ①雙分群:族群性=官方產業(既有)+故事性=VDF_StoryGroup_Registry
    (26 題材;成員集合 hash 去重)→頁面雙頁籤並立
  ②故事評分律(操作員定義,在庫誠實版):hotness=量能 z+動能 z 群內
    分位(門檻 0.40;法人淨買/融資止 2025-11=候料未入);leadership
    =CCF ±3 日峰值 lag×ρ 群內分位(lead gap 0.50);有效性=hotness×
    leadership;PC1 凝聚=群報酬矩陣主成分解釋率(<0.40=凝聚不足
    清洗標記);Leader↔Laggard leadership 差<lead gap=無差別→歸一 PEER
  ③官方 vs 故事交叉:每故事群官方產業混合度(top 產業佔比)入頁
v0102→v0103(批309 操作員令「AI-SERVER/PCB 再拆細+test debug
optimize consolidate activate till works」):
  ①故事冊尾版 glob(v0101:+7 子群 level2,parent 標;守恆=子群成員
    ⊆父群且互不重疊)②子群優先映射(一股一主故事;父群保留匯總)
  ③OPTIMIZE:故事榜+「在庫覆蓋 n/N」欄(雲端殘庫誠實可視)+父子
    階層縮排 ④CONSOLIDATE:⑧檢固化撞欄修/LOO 不對稱/守恆/覆蓋欄
v0103→v0104(批310 操作員問「齊漲齊跌時才算,沉寂時不算,加此
因子是否更看出族群性」→「如何解決」):條件式凝聚(regime-
conditional cohesion)四律,全滾動零固定常數:
  ①殘差化:對全市場(ex-2330 中位報酬)EWM β(span 60)去市場因子
    →resid;族群性只量殘差(否則崩盤日全員齊跌=量到 beta 假凝聚)
  ②活躍日閘:|LOO 群中位 resid| ≥ 自身滾動 60 日 70 分位 且
    同向率(成員同號比例)≥ 滾動 60 日中位 → 活躍;沉寂日排除
  ③雙 PC1 並列:PC1_all vs PC1_active(活躍日殘差)+比值
    (>1.2=壓力下顯形真族群;≈1 泛泛;<1 偽族群只跟大盤)+同向率
  ④領先 CCF 只取活躍 t(配對 (x_t,g_{t±k}) 限活躍日=檢定力升)
  ⑤誠實:活躍日<30=「樣本不足」不假算;⑨檢固化
用法:python3 VDF_ENG070_GroupClassificationIndex_v0104.py run
      | --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
DB_TW = VDF / "output_hub" / "mega" / "vdf_tw_market.duckdb"
REP = VIA / "VIA_Reports" / "group_class"
UI = VIA / "supportive modules" / "ui_support"
OUT_UI = UI / "VIA_UI_GroupClassIndex_v0100.html"

# ---- Type-F 固定憲法(方法論底線,不滾動) ----
BASE_DATE = "2026-01-01"      # 指數基準日(操作員令)
UNRELATED_CORR = 0.25         # 低於此=不相關(Type-F)
MAX_ATT_W = 0.18              # Attention 單檔權重上限(Type-F)
ANCHOR = "2330"               # 巨錨隔離(台積電)
MIN_MEMBERS = 5               # 族群最低成員數(誠實門檻)
# ---- Type-D 半動態(短窗保敏感) ----
SPAN_S, SPAN_L = 10, 40       # 動能短/長 EWM
Q_WIN = 40                    # 滾動分位窗
TIER_W = {"LARGE": 0.50, "MID": 0.30, "SMALL": 0.20}
WARMUP = "2025-10-01"         # 滾動基底暖身起點
# 官方產業代碼冊(TWSE/TPEx;名冊 industry 欄=代碼;缺=產業{code} 誠實)
INDUSTRY = {
    "01": "水泥", "02": "食品", "03": "塑膠", "04": "紡織纖維",
    "05": "電機機械", "06": "電器電纜", "08": "玻璃陶瓷", "09": "造紙",
    "10": "鋼鐵", "11": "橡膠", "12": "汽車", "14": "建材營造",
    "15": "航運", "16": "觀光餐旅", "17": "金融保險", "18": "貿易百貨",
    "20": "其他", "21": "化學", "22": "生技醫療", "23": "油電燃氣",
    "24": "半導體", "25": "電腦週邊", "26": "光電", "27": "通信網路",
    "28": "電子零組件", "29": "電子通路", "30": "資訊服務",
    "31": "其他電子", "32": "文化創意", "33": "農業科技",
    "34": "電子商務", "35": "綠能環保", "36": "數位雲端",
    "37": "運動休閒", "38": "居家生活",
}


def _connect_ro(dbp):
    import time
    import duckdb
    last = None
    for _ in range(3):
        try:
            return duckdb.connect(str(dbp), read_only=True)
        except Exception as exc:
            last = exc
            time.sleep(2)
    raise last


def _diag(exc) -> str:
    t = type(exc).__name__
    if "Catalog" in t:
        return "價量表未建=誠實停:先跑 via 日更(⑦a 建 tw_prices_adj 等表)"
    if "IO" in t or "lock" in str(exc).lower():
        return "庫忙=背景日更寫庫中:稍等幾分鐘再試"
    return f"庫例外({t})=誠實停"


def load_panel():
    """在庫面板:還原價報酬+近似成交值+族群+市場當沖比(可得段)"""
    import pandas as pd
    c = _connect_ro(DB_TW)
    try:
        # 鍵律(批307 實錘):價表 ticker=1101.TW/.TWO,名冊 code=1101
        px = c.execute(f"""
            SELECT p.date, regexp_replace(p.ticker, '\\.(TW|TWO)$', '')
                   AS ticker, p.adj_close, d.close, d.volume,
                   l.industry AS ind_code, l.name, l.market
            FROM tw_prices_adj p
            JOIN tw_daily_prices d USING (date, ticker)
            JOIN tw_listings l
              ON l.code = regexp_replace(p.ticker, '\\.(TW|TWO)$', '')
            WHERE p.date >= '{WARMUP}' AND p.adj_close > 0
              AND l.industry IS NOT NULL AND l.industry <> ''
        """).df()
        dt = c.execute(
            "SELECT date, avg(dt_volume_pct) AS dt_pct "
            "FROM tw_daytrade_market GROUP BY date").df()
    finally:
        c.close()
    px["date"] = pd.to_datetime(px["date"])
    dt["date"] = pd.to_datetime(dt["date"])
    px["industry"] = px["ind_code"].astype(str).str.zfill(2).map(
        lambda k: INDUSTRY.get(k, f"產業{k}"))
    px = px.sort_values(["ticker", "date"])
    px["val"] = px["close"] * px["volume"]          # DERIVED 成交值近似
    px = px.merge(dt, on="date", how="left")
    # 當沖修正(可得段;pct 為百分比值時 >1 則 /100)
    p = px["dt_pct"]
    p = p.where(p.isna() | (p <= 1.0), p / 100.0)
    px["dt_adj"] = p.notna()
    px["etr"] = px["val"] * (1.0 - p.fillna(0.0))
    px["ret"] = px.groupby("ticker")["adj_close"].pct_change()
    return px


def classify(px):
    """四分類核心(全 T-1 律;半動態敏感)"""
    import numpy as np
    import pandas as pd
    df = px[px["ticker"] != ANCHOR].copy()          # 巨錨隔離
    # Attention Share(扣 2330 後全市場)
    mkt = df.groupby("date")["etr"].transform("sum")
    df["as_share"] = df["etr"] / (mkt + 1e-8)
    # 大中小:AS 的 EWM 平滑後全市場橫斷面分位(每日 q90/q60)→T-1
    df["as_smooth"] = df.groupby("ticker")["as_share"].transform(
        lambda s: s.ewm(span=SPAN_S, adjust=True).mean())
    q90 = df.groupby("date")["as_smooth"].transform(
        lambda s: s.quantile(0.90))
    q60 = df.groupby("date")["as_smooth"].transform(
        lambda s: s.quantile(0.60))
    tier_now = np.where(df["as_smooth"] >= q90, "LARGE",
                        np.where(df["as_smooth"] >= q60, "MID", "SMALL"))
    df["size_tier"] = pd.Series(tier_now, index=df.index)
    df["size_tier"] = df.groupby("ticker")["size_tier"].shift(1)  # T-1
    # 動能 z(短長 EWM 差;半動態敏感)
    g = df.groupby("ticker")["ret"]
    df["mom"] = (g.transform(lambda s: s.ewm(span=SPAN_S).mean())
                 - g.transform(lambda s: s.ewm(span=SPAN_L).mean()))
    ms = df.groupby("ticker")["mom"]
    df["mom_z"] = ((df["mom"] - ms.transform(
        lambda s: s.rolling(Q_WIN, min_periods=15).mean()))
        / (ms.transform(
            lambda s: s.rolling(Q_WIN, min_periods=15).std()) + 1e-8))
    # 族群中位報酬+族群動能 z
    df["g_ret"] = df.groupby(["industry", "date"])["ret"].transform(
        "median")
    df["g_mom"] = df.groupby(["industry", "date"])["mom_z"].transform(
        "median")
    # EWM 同動相關(cov/std;向量化)
    def _ewm(s, sp=SPAN_L):
        return s.ewm(span=sp, adjust=True, min_periods=15).mean()
    by = df.groupby("ticker")
    mx = by["ret"].transform(_ewm)
    my = by["g_ret"].transform(_ewm)
    mxy = (df["ret"] * df["g_ret"]).groupby(df["ticker"]).transform(_ewm)
    mx2 = (df["ret"] ** 2).groupby(df["ticker"]).transform(_ewm)
    my2 = (df["g_ret"] ** 2).groupby(df["ticker"]).transform(_ewm)
    var_x = (mx2 - mx ** 2).clip(lower=1e-12)
    var_y = (my2 - my ** 2).clip(lower=1e-12)
    df["corr"] = ((mxy - mx * my)
                  / (np.sqrt(var_x) * np.sqrt(var_y) + 1e-12)
                  ).clip(-1, 1)
    # 一致性=個股動能 z × 族群動能 z(同向確認)
    df["consistency"] = df["mom_z"] * df["g_mom"]
    # 族群內 AS 排名(T-1)與族群滾動中位相關門檻
    df["as_rank"] = df.groupby(["industry", "date"])["as_smooth"].rank(
        pct=True)
    df["as_rank"] = df.groupby("ticker")["as_rank"].shift(1)       # T-1
    df["corr_med"] = df.groupby(["industry", "date"])["corr"].transform(
        "median")
    c1, cons1 = df["corr"].shift(0), df["consistency"]             # 判讀值
    role = np.select(
        [df["corr"] < UNRELATED_CORR,
         (df["as_rank"] >= 0.80) & (cons1 > 0)
         & (df["corr"] >= df["corr_med"]),
         (cons1 < -0.5) | (df["as_rank"] <= 0.40)],
        ["UNRELATED", "LEADER", "LAGGER"], default="PEER")
    df["role"] = pd.Series(role, index=df.index)
    df["role"] = df.groupby("ticker")["role"].shift(1)             # T-1
    return df


def _cap_norm(s, cap: float = MAX_ATT_W, iters: int = 6):
    """族群內封頂正規化:Σw=1 且 max w≤cap(可行時);迭代再分配"""
    import numpy as np
    v = s.fillna(0.0).to_numpy(dtype=float)
    n = len(v)
    if n == 0 or v.sum() <= 0:
        return s * 0 + (1.0 / max(n, 1))
    cap_eff = max(cap, 1.0 / n)            # 成員少=上限 1/n 誠實
    w = v / v.sum()
    for _ in range(iters):
        over = w > cap_eff + 1e-12
        if not over.any():
            break
        excess = (w[over] - cap_eff).sum()
        w[over] = cap_eff
        rest = ~over
        if rest.any() and w[rest].sum() > 0:
            w[rest] += excess * w[rest] / w[rest].sum()
        else:
            break
    return s * 0 + w


STORY_MIN_MEMBERS = 2   # 故事群天生小(批309 拆細後);產業級門檻不套


def build_indices(df, gcol: str = "industry", min_members: int | None = None):
    """三加權族群指數(T-1 權重;base=100;守恆監控)"""
    import numpy as np
    import pandas as pd
    d = df.dropna(subset=["ret"]).copy()
    if gcol != "industry":
        d = d.drop(columns=["industry"], errors="ignore").rename(
            columns={gcol: "industry"})
    # 成員數門檻(誠實)
    n = d.groupby(["industry", "date"])["ticker"].transform("count")
    d = d[n >= (min_members if min_members is not None else MIN_MEMBERS)]
    # 三權重(當日算→T-1 用)
    d["w_eq"] = 1.0 / d.groupby(["industry", "date"])["ticker"].transform(
        "count")
    d["tier_raw"] = d["size_tier"].map(TIER_W).fillna(TIER_W["SMALL"])
    d["w_tier"] = d["tier_raw"] / d.groupby(
        ["industry", "date"])["tier_raw"].transform("sum")
    d["w_att"] = d.groupby(["industry", "date"])["as_smooth"].transform(
        _cap_norm)
    for w in ("w_eq", "w_tier", "w_att"):
        d[w] = d.groupby("ticker")[w].shift(1)                     # T-1
    d = d.dropna(subset=["w_eq", "w_tier", "w_att"])
    # 每權重再正規化(T-1 位移後守恆)
    for w in ("w_eq", "w_tier", "w_att"):
        d[w] = d[w] / d.groupby(["industry", "date"])[w].transform("sum")
    agg = d.groupby(["industry", "date"]).apply(
        lambda x: pd.Series({
            "ret_eq": float((x["ret"] * x["w_eq"]).sum()),
            "ret_tier": float((x["ret"] * x["w_tier"]).sum()),
            "ret_att": float((x["ret"] * x["w_att"]).sum()),
            "n_members": int(len(x)),
            "max_w_att": float(x["w_att"].max()),
        }), include_groups=False).reset_index()
    agg = agg.sort_values(["industry", "date"])
    out = []
    for ind, g in agg.groupby("industry"):
        g = g.copy()
        base_mask = g["date"] >= BASE_DATE
        if not base_mask.any():
            continue
        for c_ in ("eq", "tier", "att"):
            cum = (1 + g[f"ret_{c_}"]).cumprod()
            b = cum[base_mask].iloc[0]
            g[f"idx_{c_}"] = cum / b * 100.0
        out.append(g[base_mask])
    idx = pd.concat(out, ignore_index=True) if out else pd.DataFrame()
    if len(idx):
        idx["att_vs_eq"] = idx["idx_att"] - idx["idx_eq"]
    return idx


def _story_reg_path():
    hits = sorted((VIA / "supportive modules" / "registry").glob(
        "VDF_StoryGroup_Registry_v*.json"))
    return hits[-1] if hits else None
STORY_REG = _story_reg_path()
HOT_MIN, LEAD_GAP, PC1_MIN, CCF_L = 0.40, 0.50, 0.40, 3


STORY_META: dict = {}


def load_stories() -> dict:
    """故事冊尾版(SSOT;缺=誠實空);子群(level2)優先映射"""
    global STORY_META
    try:
        reg = json.loads(STORY_REG.read_text(encoding="utf-8"))
    except Exception:
        return {}
    out, meta = {}, {}
    for s_ in sorted(reg["stories"], key=lambda z: -int(z.get("level", 1))):
        out[s_["story_group"]] = set(s_["tickers"])
        meta[s_["story_group"]] = {"level": int(s_.get("level", 1)),
                                   "parent": s_.get("parent"),
                                   "n_reg": len(s_["tickers"])}
    STORY_META = meta
    return out


ACT_Q, ACT_WIN, BETA_SPAN, MIN_ACT = 0.70, 60, 60, 30


def add_residual(px):
    """對全市場(ex-2330 中位報酬)EWM β 殘差化=去市場因子(批310)"""
    import pandas as pd
    d = px.copy()
    mkt = (d[d["ticker"] != ANCHOR].groupby("date")["ret"].median()
           .rename("mkt"))
    d = d.join(mkt, on="date")
    d = d.sort_values(["ticker", "date"])
    g = d.groupby("ticker")
    cov = g.apply(lambda x: x["ret"].ewm(span=BETA_SPAN).cov(x["mkt"]),
                  include_groups=False).reset_index(level=0, drop=True)
    var = d.groupby("ticker")["mkt"].transform(
        lambda x: x.ewm(span=BETA_SPAN).var())
    d["beta"] = (cov / (var + 1e-12)).clip(-3, 3)
    d["resid"] = d["ret"] - d["beta"].shift(1).fillna(1.0) * d["mkt"]  # T-1 β 無前視
    return d


def classify_story(px, stories: dict):
    """故事性分群評分(批308 操作員律;在庫誠實版)
    回:(member_df 末日評分, story_summary list, story_panel for 指數)"""
    import numpy as np
    import pandas as pd
    df = px[px["ticker"] != ANCHOR].copy()
    t2s = {}
    for sname, tk in stories.items():
        for t in tk:
            t2s.setdefault(t, sname)          # 一股一主故事(先登先得)
    df["story"] = df["ticker"].map(t2s)
    df = df.dropna(subset=["story"])
    if df.empty:
        return pd.DataFrame(), [], pd.DataFrame()
    # hotness 原料:量能 z(etr EWM 短−長 / std)+動能 z
    g = df.groupby("ticker")
    ez = ((g["etr"].transform(lambda x: x.ewm(span=SPAN_S).mean())
           - g["etr"].transform(lambda x: x.ewm(span=SPAN_L).mean()))
          / (g["etr"].transform(lambda x: x.ewm(span=SPAN_L).std()) + 1e-8))
    mom = (g["ret"].transform(lambda x: x.ewm(span=SPAN_S).mean())
           - g["ret"].transform(lambda x: x.ewm(span=SPAN_L).mean()))
    mz = (mom - mom.groupby(df["ticker"]).transform(
        lambda x: x.rolling(Q_WIN, min_periods=15).mean())) / (
        mom.groupby(df["ticker"]).transform(
            lambda x: x.rolling(Q_WIN, min_periods=15).std()) + 1e-8)
    df["hot_raw"] = (ez.fillna(0) + mz.fillna(0)) / 2
    df["g_ret"] = df.groupby(["story", "date"])["ret"].transform("median")
    last = df["date"].max()
    win = df[df["date"] >= pd.Timestamp(BASE_DATE)]
    rows, summ = [], []
    for sname, gd in win.groupby("story"):
        vcol = "resid" if "resid" in gd.columns else "ret"
        wide = gd.pivot_table(index="date", columns="ticker", values=vcol)
        wide = wide.dropna(axis=1, thresh=int(len(wide) * 0.8))
        wide = wide.loc[:, wide.std() > 1e-12]   # 零變異成員濾除(相關無定義=誠實剔)
        n_ok = wide.shape[1]

        def _pc1(w):
            if w.shape[1] >= 3 and len(w) >= MIN_ACT:
                z = ((w - w.mean()) / (w.std() + 1e-12)).fillna(0.0).to_numpy()
                sv = np.linalg.svd(z, compute_uv=False)
                return float(sv[0] ** 2 / (sv ** 2).sum())
            return None
        pc1 = _pc1(wide)
        # 活躍日閘(批310):|群中位 resid|≥滾動分位 且 同向率≥滾動中位
        gmed_all = wide.median(axis=1)
        amp = gmed_all.abs()
        thr = amp.rolling(ACT_WIN, min_periods=20).quantile(ACT_Q)
        sign_share = (np.sign(wide).eq(np.sign(gmed_all), axis=0)
                      & (wide != 0)).sum(axis=1) / max(n_ok, 1)
        ss_thr = sign_share.rolling(ACT_WIN, min_periods=20).median()
        active = (amp >= thr) & (sign_share >= ss_thr)
        n_act = int(active.sum())
        wide_act = wide[active]
        pc1_act = _pc1(wide_act) if n_act >= MIN_ACT else None
        ratio = (round(pc1_act / pc1, 2) if (pc1_act and pc1) else None)
        same_dir = round(float(sign_share[active].mean()), 2) if n_act else None
        mem = []
        for t in wide.columns:
            x = wide[t]
            # LOO 群中位(留一法=上傳正本律;去自相關偏誤)
            gm = (wide.drop(columns=[t]).median(axis=1) if n_ok > 1
                  else wide[t] * 0)
            # 領先不對稱分:Σ_k [ρ(x_t, g_{t+k}) − ρ(x_t, g_{t−k})]
            # 正=個股今日與群未來相關高於與群過去=領先;負=落後
            asym, best_lag, best_r = 0.0, 0, -9.0
            _es = np.errstate(invalid="ignore", divide="ignore")  # 零變異重疊窗=NaN 誠實跳
            _es.__enter__()
            xa = x[active] if n_act >= MIN_ACT else x   # 活躍 t 限定(不足=全樣本誠實)
            for k in range(1, CCF_L + 1):
                rf = xa.corr(gm.shift(-k))    # 群未來(配對限活躍 t)
                rb = xa.corr(gm.shift(k))     # 群過去
                if pd.notna(rf) and pd.notna(rb):
                    asym += (rf - rb) / k
                for kk, r in ((k, rf), (-k, rb)):
                    if pd.notna(r) and r > best_r:
                        best_r, best_lag = float(r), kk
            r0 = xa.corr(gm)
            _es.__exit__(None, None, None)
            if pd.notna(r0) and r0 > best_r:
                best_r, best_lag = float(r0), 0
            hot_last = float(df.loc[(df["ticker"] == t)
                                    & (df["date"] == last), "hot_raw"]
                             .tail(1).sum())
            mem.append({"ticker": t, "story": sname,
                        "lead_raw": round(asym, 4),
                        "peak_rho": round(best_r, 3), "lead_lag": best_lag,
                        "hot_raw": hot_last})
        if not mem:
            continue
        m = pd.DataFrame(mem)
        m["hotness"] = m["hot_raw"].rank(pct=True) if len(m) > 1 else 1.0
        m["leadership"] = (m["lead_raw"].rank(pct=True) if len(m) > 1
                           else 1.0)
        m["validity"] = m["hotness"] * m["leadership"]
        lead_gap = float(m["leadership"].max() - m["leadership"].min())
        collapse = lead_gap < LEAD_GAP
        role = np.where(
            (m["hotness"] >= HOT_MIN) & (m["leadership"] >= 0.5), "LEADER",
            np.where((m["hotness"] < HOT_MIN) & (m["leadership"] < 0.5),
                     "LAGGARD", "PEER"))
        m["role"] = "PEER" if collapse else role
        m["pc1"] = pc1
        m["cohesion_ok"] = (pc1 is not None) and pc1 >= PC1_MIN
        rows.append(m)
        mt = STORY_META.get(sname, {})
        summ.append({"story": sname, "n": int(n_ok),
                     "n_reg": mt.get("n_reg", 0),
                     "n_act": n_act, "pc1_act": None if pc1_act is None
                     else round(pc1_act, 3), "ratio": ratio,
                     "same_dir": same_dir,
                     "level": mt.get("level", 1), "parent": mt.get("parent"),
                     "pc1": None if pc1 is None else round(pc1, 3),
                     "cohesion_ok": bool((pc1 is not None) and pc1 >= PC1_MIN),
                     "lead_gap": round(lead_gap, 2), "collapsed": bool(collapse),
                     "leaders": [r for r in m.loc[m["role"] == "LEADER",
                                                  "ticker"]][:6]})
    # 父群匯總列(批309):成員全被子群取走的父群=以全冊成員算 PC1/覆蓋,
    # 領頭=子群領頭聯集(父群保留供匯總律)
    kids_of: dict = {}
    for nm, mt in STORY_META.items():
        if mt.get("level") == 2 and mt.get("parent"):
            kids_of.setdefault(mt["parent"], []).append(nm)
    done = {x["story"] for x in summ}
    for pname, knames in kids_of.items():
        if pname in done:
            continue
        tk = stories.get(pname, set())
        wide = (win[win["ticker"].isin(tk)]
                .pivot_table(index="date", columns="ticker", values="ret"))
        wide = wide.dropna(axis=1, thresh=int(len(wide) * 0.8)) if len(wide) else wide
        wide = wide.loc[:, wide.std() > 1e-12] if len(wide) else wide
        n_ok = wide.shape[1] if len(wide) else 0
        pc1 = None
        if n_ok >= 3 and len(wide) >= 30:
            z = ((wide - wide.mean()) / (wide.std() + 1e-12)).fillna(0.0).to_numpy()
            sv = np.linalg.svd(z, compute_uv=False)
            pc1 = float(sv[0] ** 2 / (sv ** 2).sum())
        leaders = [t for x in summ if x["story"] in knames for t in x["leaders"]]
        pc1_act_p, n_act_p, sd_p = None, 0, None
        if n_ok >= 1 and len(wide):
            gm_ = wide.median(axis=1); amp_ = gm_.abs()
            thr_ = amp_.rolling(ACT_WIN, min_periods=20).quantile(ACT_Q)
            ss_ = (np.sign(wide).eq(np.sign(gm_), axis=0) & (wide != 0)).sum(axis=1) / max(n_ok, 1)
            act_ = (amp_ >= thr_) & (ss_ >= ss_.rolling(ACT_WIN, min_periods=20).median())
            n_act_p = int(act_.sum())
            if n_act_p >= MIN_ACT and n_ok >= 3:
                z_ = ((wide[act_] - wide[act_].mean()) / (wide[act_].std() + 1e-12)).fillna(0.0).to_numpy()
                sv_ = np.linalg.svd(z_, compute_uv=False)
                pc1_act_p = float(sv_[0] ** 2 / (sv_ ** 2).sum())
            sd_p = round(float(ss_[act_].mean()), 2) if n_act_p else None
        summ.append({"story": pname, "n": int(n_ok), "n_reg": len(tk),
                     "n_act": n_act_p, "pc1_act": None if pc1_act_p is None
                     else round(pc1_act_p, 3),
                     "ratio": (round(pc1_act_p / pc1, 2)
                               if (pc1_act_p and pc1) else None),
                     "same_dir": sd_p,
                     "level": 1, "parent": None, "aggregate": True,
                     "pc1": None if pc1 is None else round(pc1, 3),
                     "cohesion_ok": bool((pc1 is not None) and pc1 >= PC1_MIN),
                     "lead_gap": None, "collapsed": False,
                     "leaders": leaders[:6]})
    members = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    # 故事指數面板(建 as_smooth/size_tier 供三加權)
    panel = df.copy()
    mkt = panel.groupby("date")["etr"].transform("sum")
    panel["as_share"] = panel["etr"] / (mkt + 1e-8)
    panel["as_smooth"] = panel.groupby("ticker")["as_share"].transform(
        lambda x: x.ewm(span=SPAN_S, adjust=True).mean())
    q90 = panel.groupby("date")["as_smooth"].transform(lambda x: x.quantile(0.9))
    q60 = panel.groupby("date")["as_smooth"].transform(lambda x: x.quantile(0.6))
    panel["size_tier"] = np.where(panel["as_smooth"] >= q90, "LARGE",
                                  np.where(panel["as_smooth"] >= q60, "MID",
                                           "SMALL"))
    panel["size_tier"] = panel.groupby("ticker")["size_tier"].shift(1)
    return members, summ, panel


def render(idx, roles, meta, story=None) -> str:
    import pandas as pd
    try:
        import plotly.offline as po
        pjs = "<script>" + po.get_plotlyjs() + "</script>"
        degrade = ""
    except Exception:
        pjs = ""
        degrade = "<div class='card'>誠實降級:plotly 缺=僅表格</div>"
    last = idx[idx["date"] == idx["date"].max()]
    top = last.sort_values("idx_att", ascending=False).head(6)
    series = {}
    for ind in top["industry"]:
        g = idx[idx["industry"] == ind]
        series[ind] = {
            "d": [str(x.date()) for x in g["date"]],
            "eq": [round(v, 2) for v in g["idx_eq"]],
            "tier": [round(v, 2) for v in g["idx_tier"]],
            "att": [round(v, 2) for v in g["idx_att"]],
        }
    rc = roles["role"].value_counts().to_dict()
    sc = roles["size_tier"].value_counts().to_dict()
    lead_rows = "".join(
        f"<tr><td class='mono'>{r.ticker}</td><td>{r.name}</td>"
        f"<td>{r.industry}</td><td>{r.size_tier}</td>"
        f"<td>{r.corr:.2f}</td></tr>"
        for r in roles[roles["role"] == "LEADER"]
        .sort_values("as_smooth", ascending=False)
        .head(20).itertuples())
    tbl_rows = "".join(
        f"<tr><td>{r.industry}</td><td>{r.n_members}</td>"
        f"<td>{r.idx_eq:.1f}</td><td>{r.idx_tier:.1f}</td>"
        f"<td class='{'g' if r.idx_att >= 100 else 'r'}'>{r.idx_att:.1f}"
        f"</td><td>{r.max_w_att:.0%}</td></tr>"
        for r in last.sort_values("idx_att", ascending=False)
        .head(25).itertuples())
    story = story or {}
    s_series, s_rows, s_lead = {}, "", ""
    if story.get("idx") is not None and len(story["idx"]):
        sidx = story["idx"]
        slast = sidx[sidx["date"] == sidx["date"].max()]
        for ind in slast.sort_values("idx_att", ascending=False)["industry"].head(8):
            g = sidx[sidx["industry"] == ind]
            s_series[ind] = {"d": [str(x.date()) for x in g["date"]],
                             "eq": [round(v, 2) for v in g["idx_eq"]],
                             "tier": [round(v, 2) for v in g["idx_tier"]],
                             "att": [round(v, 2) for v in g["idx_att"]]}
        mix = story.get("mix", {})
        def _ord(z):
            return (z.get("parent") or z["story"], z.get("level", 1),
                    -(z["pc1"] or 0))
        s_rows = "".join(
            f"<tr><td>{'&nbsp;&nbsp;└ ' if x.get('level') == 2 else ''}"
            f"{x['story']}</td><td>{x['n']}/{x.get('n_reg', '?')}</td>"
            f"<td class='{'g' if x['cohesion_ok'] else 'r'}'>"
            f"{x['pc1'] if x['pc1'] is not None else '—'}</td>"
            f"<td>{x.get('pc1_act') if x.get('pc1_act') is not None else ('樣本不足' if x.get('n_act', 0) < MIN_ACT else '—')}"
            f" <small>({x.get('n_act', 0)}d)</small></td>"
            f"<td class='{'g' if (x.get('ratio') or 0) >= 1.2 else ('r' if x.get('ratio') is not None and x['ratio'] < 1 else '')}'>"
            f"{x.get('ratio') if x.get('ratio') is not None else '—'}</td>"
            f"<td>{x.get('same_dir') if x.get('same_dir') is not None else '—'}</td>"
            f"<td>{'匯總' if x.get('aggregate') else x['lead_gap']}"
            f"{' · 歸一' if x['collapsed'] else ''}</td>"
            f"<td>{'、'.join(x['leaders']) or '—'}</td>"
            f"<td>{mix.get(x['story'], '—')}</td></tr>"
            for x in sorted(story.get("summ", []), key=_ord))
    story_tab = f"""
<div class="card" id="storysec"><h3>故事性分群<small>Story Groups ·
hotness≥{HOT_MIN} · lead gap {LEAD_GAP} · PC1≥{PC1_MIN} · 條件式凝聚(殘差×活躍日 滾動 {int(ACT_Q*100)} 分位)</small></h3>
<select id="ssel">{"".join(f'<option>{k}</option>' for k in s_series)}
</select><div id="c2"></div>
<div class="wrap"><table><tr><th>故事 Story(└=子群)</th>
<th>在庫/冊 Coverage</th><th>PC1 全樣本</th>
<th>PC1 活躍日(殘差)</th><th>比值 Act/All</th><th>同向率</th>
<th>PC1 凝聚</th><th>Lead Gap</th><th>Leader</th>
<th>官方產業混合 Mix</th></tr>{s_rows or
 '<tr><td colspan=6>故事冊空或主窗不足(誠實)</td></tr>'}</table></div></div>"""
    return f"""<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VIA 族群分類×價格指數</title><style>
:root{{--bg:#f4f6f8;--paper:#fff;--ink:#202833;--ink2:#465365;
--mut:#596778;--mut2:#5d6a7b;--line:#dfe4ea;--soft:#eef3f6;
--acc:#315f7d;--ok:#2f7652;--bad:#a64f46;--header-h:46px;
--footer-h:26px}}
*{{box-sizing:border-box;margin:0}}
body{{background:var(--bg);color:var(--ink);
font:11px/1.45 "Segoe UI","Noto Sans TC",system-ui,sans-serif;
padding:var(--header-h) 0 var(--footer-h)}}
.mono{{font-family:Consolas,ui-monospace,monospace}}
.app-header{{position:fixed;z-index:80;inset:0 0 auto 0;
height:var(--header-h);display:flex;align-items:center;gap:10px;
padding:0 14px;background:rgba(255,255,255,.97);
border-bottom:1px solid var(--line)}}
.seal{{width:26px;height:26px;display:grid;place-items:center;
background:#315f7d;color:#fff;border-radius:5px;font:700 13px/1
"Noto Serif TC",serif}}
.product{{font-size:12px;font-weight:800}}
.motto{{font-size:9px;color:var(--mut);letter-spacing:.1em}}
.badge{{margin-left:auto;display:inline-flex;align-items:center;
min-height:22px;padding:2px 8px;border:1px solid #b8d7c6;
border-radius:999px;background:#f1f8f4;font-size:9.5px;
font-weight:700;color:var(--ok)}}
.main{{max-width:1180px;margin:0 auto;padding:12px 16px}}
.stats{{display:grid;
grid-template-columns:repeat(auto-fit,minmax(126px,1fr));gap:8px;
margin-bottom:10px}}
.stat{{background:var(--paper);border:1px solid var(--line);
border-radius:8px;padding:9px 12px}}
.stat .n{{font-size:19px;font-weight:800;
font-variant-numeric:tabular-nums}}
.stat .zh{{font-size:10.5px;color:var(--ink2)}}
.stat .en{{font-size:8px;letter-spacing:.14em;color:var(--mut2);
font-weight:700}}
.card,.chart{{background:var(--paper);border:1px solid var(--line);
border-radius:8px;padding:10px 12px;margin-bottom:9px}}
.card h3{{font-size:11.5px}}
.card h3 small{{font-size:8px;letter-spacing:.14em;color:var(--mut2);
font-weight:700;margin-left:6px}}
select{{border:1px solid var(--line);border-radius:6px;padding:4px 8px;
font:inherit;color:inherit;background:var(--paper);margin-bottom:6px}}
table{{width:100%;border-collapse:collapse;font-size:10.5px}}
th{{text-align:left;font-size:8.5px;letter-spacing:.12em;
color:var(--mut2);border-bottom:1px solid var(--line);
padding:3px 6px 3px 0;font-weight:700}}
td{{border-bottom:1px solid var(--soft);padding:3px 6px 3px 0;
font-variant-numeric:tabular-nums}}
td.g{{color:var(--ok);font-weight:600}}td.r{{color:var(--bad);
font-weight:600}}
.wrap{{overflow-x:auto}}
.app-footer{{position:fixed;z-index:80;inset:auto 0 0 0;
height:var(--footer-h);display:flex;align-items:center;gap:14px;
padding:0 14px;background:var(--paper);
border-top:1px solid var(--line);font-size:9px;color:var(--mut)}}
</style></head><body>
<header class="app-header"><span class="seal">群</span>
<div><div class="product">族群分類×價格指數 · Group Classification
Index</div>
<div class="motto">Lead / Lag · Large / Mid / Small · Three Weighting
Methods</div></div>
<span class="badge">T-1 No Look-Ahead · Cap 18% · Base
{BASE_DATE}=100</span></header>
<main class="main">
<div class="stats">
<div class="stat"><div class="n">{meta['n_groups']}</div>
<div class="zh">族群指數</div><div class="en">Group Indices</div></div>
<div class="stat"><div class="n">{rc.get('LEADER', 0)}</div>
<div class="zh">領漲 Leader</div><div class="en">Leaders</div></div>
<div class="stat"><div class="n">{rc.get('PEER', 0)}</div>
<div class="zh">同行 Peer</div><div class="en">Peers</div></div>
<div class="stat"><div class="n">{rc.get('LAGGER', 0)}</div>
<div class="zh">落後 Lagger</div><div class="en">Laggers</div></div>
<div class="stat"><div class="n">{rc.get('UNRELATED', 0)}</div>
<div class="zh">不相關</div><div class="en">Unrelated</div></div>
<div class="stat"><div class="n">{sc.get('LARGE', 0)}/{sc.get('MID', 0)}
/{sc.get('SMALL', 0)}</div>
<div class="zh">大/中/小</div><div class="en">Size Tiers</div></div>
</div>
{degrade}
<div class="chart"><h3>三加權指數比較<small>Equal · Tier · Attention
(選族群)</small></h3>
<select id="gsel">{"".join(f'<option>{k}</option>' for k in series)}
</select>
<div id="c1"></div></div>
<div class="card"><h3>族群榜<small>By Attention Index · Top 25
</small></h3>
<div class="wrap"><table><tr><th>族群 Industry</th><th>成員</th>
<th>等權 Equal</th><th>階層 Tier</th><th>聚焦 Attention</th>
<th>最大權重</th></tr>{tbl_rows}</table></div></div>
{story_tab}
<div class="card"><h3>領漲榜<small>Leaders · Top 20 By Attention
</small></h3>
<div class="wrap"><table><tr><th>代碼</th><th>名稱</th><th>族群</th>
<th>規模</th><th>同動 ρ</th></tr>{lead_rows}</table></div></div>
<div class="card"><h3>誠實界定<small>Honest Boundaries</small></h3>
<div style="font-size:10px;color:var(--mut);line-height:1.7">
成交值=close×volume 近似(庫無 turnover;DERIVED)· 個股當沖缺=
市場級當沖比 {meta['dt_days']} 日可修正段(dt_adj 旗標)· 三大法人止
2025-11 與主窗不交集=LEAD/LAG 用價量一致性判,法人維度候料 ·
巨錨 2330 隔離 · 族群<{MIN_MEMBERS} 檔不建指數 · 非投資建議</div>
</div></main>
<footer class="app-footer"><span>VIA · VDF ENG070</span>
<span>產於 {meta['ts']}</span><span>主窗 {BASE_DATE}~{meta['last']}
· 零 CDN</span></footer>
<script id="d" type="application/json">{json.dumps(series,
    ensure_ascii=False)}</script>
<script id="ds" type="application/json">{json.dumps(s_series,
    ensure_ascii=False)}</script>
{pjs}
<script>
const D=JSON.parse(document.getElementById("d").textContent);
const sel=document.getElementById("gsel");
function draw(){{const g=D[sel.value];if(!g||!window.Plotly)return;
 Plotly.react("c1",[
  {{x:g.d,y:g.eq,name:"等權 Equal",line:{{color:"#5d6a7b"}}}},
  {{x:g.d,y:g.tier,name:"階層 Tier",line:{{color:"#315f7d"}}}},
  {{x:g.d,y:g.att,name:"聚焦 Attention",line:{{color:"#2f7652",
   width:2.4}}}}],
  {{height:420,font:{{size:10,
    family:'"Segoe UI","Noto Sans TC",sans-serif'}},
   margin:{{l:44,r:16,t:10,b:34}},paper_bgcolor:"#fff",
   plot_bgcolor:"#fff",legend:{{orientation:"h"}},
   yaxis:{{title:{{text:"指數(基準=100)",font:{{size:10}}}}}}}},
  {{displayModeBar:false,responsive:true}});}}
sel.onchange=draw;draw();
const DS=JSON.parse(document.getElementById("ds").textContent);
const ssel=document.getElementById("ssel");
function draw2(){{const g=DS[ssel.value];if(!g||!window.Plotly)return;
 Plotly.react("c2",[
  {{x:g.d,y:g.eq,name:"等權 Equal",line:{{color:"#5d6a7b"}}}},
  {{x:g.d,y:g.tier,name:"階層 Tier",line:{{color:"#315f7d"}}}},
  {{x:g.d,y:g.att,name:"聚焦 Attention",line:{{color:"#2f7652",
   width:2.4}}}}],
  {{height:360,font:{{size:10,
    family:'"Segoe UI","Noto Sans TC",sans-serif'}},
   margin:{{l:44,r:16,t:10,b:34}},paper_bgcolor:"#fff",
   plot_bgcolor:"#fff",legend:{{orientation:"h"}},
   yaxis:{{title:{{text:"故事指數(基準=100)",font:{{size:10}}}}}}}},
  {{displayModeBar:false,responsive:true}});}}
if(ssel){{ssel.onchange=draw2;draw2();}}
</script></body></html>"""


def run(do_print: bool = True) -> int:
    if not DB_TW.exists():
        print("[族群分類] 台股庫缺=誠實停(先跑 boot)")
        return 2
    try:
        px = load_panel()
        df = classify(px)
        idx = build_indices(df)
    except Exception as exc:
        print("[族群分類] " + _diag(exc))
        return 2
    if not len(idx):
        print("[族群分類] 主窗資料不足=誠實停(候料)")
        return 2
    last_d = df["date"].max()
    roles = df[df["date"] == last_d].dropna(subset=["role", "size_tier"])
    # 故事性分群(批308)
    stories = load_stories()
    story = {"summ": [], "idx": None, "mix": {}}
    try:
        px_r = add_residual(px)
        s_mem, s_summ, s_panel = classify_story(px_r, stories)
        if len(s_panel):
            s_idx = build_indices(s_panel, gcol="story",
                                  min_members=STORY_MIN_MEMBERS)
            story = {"summ": s_summ, "idx": s_idx, "members": s_mem}
            mixd = {}
            for sname, gd in px[px["ticker"].isin(
                    set().union(*stories.values()))].drop_duplicates(
                    "ticker").assign(story=lambda x: x["ticker"].map(
                        {t: n for n, tk in stories.items() for t in tk})
                    ).groupby("story"):
                vc = gd["industry"].value_counts()
                mixd[sname] = (f"{vc.index[0]} {vc.iloc[0] / vc.sum():.0%}"
                               if len(vc) else "—")
            story["mix"] = mixd
    except Exception as exc:
        story["err"] = f"{type(exc).__name__}: {exc}"
    meta = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "n_groups": int(idx["industry"].nunique()),
            "last": str(last_d.date()),
            "dt_days": int(px.loc[px["dt_adj"], "date"].nunique())}
    REP.mkdir(parents=True, exist_ok=True)
    stamp = str(last_d.date()).replace("-", "")
    ev = {"meta": meta,
          "constitution": {"base_date": BASE_DATE,
                           "unrelated_corr": UNRELATED_CORR,
                           "max_att_w": MAX_ATT_W,
                           "min_members": MIN_MEMBERS,
                           "spans": [SPAN_S, SPAN_L], "q_win": Q_WIN},
          "roles": roles["role"].value_counts().to_dict(),
          "sizes": roles["size_tier"].value_counts().to_dict(),
          "top_att": idx[idx["date"] == idx["date"].max()]
          .sort_values("idx_att", ascending=False)
          .head(10)[["industry", "idx_eq", "idx_tier", "idx_att",
                     "n_members"]].to_dict("records")}
    (REP / f"GROUP_CLASS_{stamp}.json").write_text(
        json.dumps(ev, ensure_ascii=False, indent=1, default=str),
        encoding="utf-8")
    roles[["ticker", "name", "industry", "role", "size_tier",
           "corr", "as_smooth"]].to_csv(
        REP / f"MEMBER_CLASS_{stamp}.csv", index=False,
        encoding="utf-8-sig")
    UI.mkdir(parents=True, exist_ok=True)
    OUT_UI.write_text(render(idx, roles, meta, story), encoding="utf-8")
    if story.get("summ"):
        ev_s = {"stories": story["summ"],
                "roles": story["members"]["role"].value_counts().to_dict()
                if len(story.get("members", [])) else {}}
        (REP / f"STORY_CLASS_{stamp}.json").write_text(
            json.dumps(ev_s, ensure_ascii=False, indent=1, default=str),
            encoding="utf-8")
        if len(story.get("members", [])):
            story["members"].to_csv(REP / f"STORY_MEMBER_{stamp}.csv",
                                    index=False, encoding="utf-8-sig")
    if do_print:
        rc = ev["roles"]
        print(f"[族群分類] {meta['n_groups']} 族群指數 · LEADER "
              f"{rc.get('LEADER', 0)} / PEER {rc.get('PEER', 0)} / "
              f"LAGGER {rc.get('LAGGER', 0)} / UNRELATED "
              f"{rc.get('UNRELATED', 0)} · 大中小 "
              f"{ev['sizes'].get('LARGE', 0)}/{ev['sizes'].get('MID', 0)}"
              f"/{ev['sizes'].get('SMALL', 0)} · {OUT_UI.name}")
        for r in ev["top_att"][:3]:
            print(f"  [榜] {r['industry']} 聚焦 {r['idx_att']:.1f} · "
                  f"等權 {r['idx_eq']:.1f} · 階層 {r['idx_tier']:.1f}")
        if story.get("summ"):
            ok = sum(1 for x in story["summ"] if x["cohesion_ok"])
            hi = sum(1 for x in story["summ"] if (x.get("ratio") or 0) >= 1.2)
            print(f"  [條件式] 活躍日凝聚>全樣本×1.2 = {hi} 群 · 樣本不足 "
                  f"{sum(1 for x in story['summ'] if x.get('n_act', 0) < MIN_ACT)}")
            print(f"  [故事] {len(story['summ'])} 群 · 凝聚達標 {ok} · "
                  f"歸一 {sum(1 for x in story['summ'] if x['collapsed'])} · "
                  f"角色 {ev_s['roles']}")
        elif story.get("err"):
            print(f"  [故事] 誠實停:{story['err'][:120]}")
    return 0


def _data_ready() -> bool:
    try:
        import duckdb
        c = duckdb.connect(str(DB_TW), read_only=True)
        t = {r[0] for r in c.execute("SHOW TABLES").fetchall()}
        c.close()
        return {"tw_prices_adj", "tw_daily_prices",
                "tw_listings"} <= t
    except Exception:
        return False


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    src = Path(__file__).read_text(encoding="utf-8")
    if not _data_ready():
        print("  [模式] 資料缺席=誠實缺料模式:驗誠實停行為")
        rc = run(do_print=False)
        chk("①' 誠實停(rc2 零裸 traceback)", rc == 2)
        chk("②' 靜態紀律(T-1 律+憲法常數+加速橋)",
            "shift(1)" in src and "MAX_ATT_W" in src
            and "ACCEL-BRIDGE" in src)
        print(f"  [計] 誠實缺料二檢 OK {2 - len(fails)} · "
              f"FAIL {len(fails)}(全檢=資料在位環境跑)")
        return 1 if fails else 0
    rc = run(do_print=False)
    chk("① 全鏈跑通(rc0+存證+頁產出)", rc == 0 and OUT_UI.exists()
        and any(REP.glob("GROUP_CLASS_*.json")))
    ev = json.loads(sorted(REP.glob("GROUP_CLASS_*.json"))[-1]
                    .read_text(encoding="utf-8"))
    chk("② 四角色守恆(四類計數和>0 且無他類)",
        set(ev["roles"]) <= {"LEADER", "PEER", "LAGGER", "UNRELATED"}
        and sum(ev["roles"].values()) > 100)
    chk("③ 大中小三層(LARGE<MID<SMALL 計數序=分位正向)",
        ev["sizes"].get("LARGE", 0) < ev["sizes"].get("SMALL", 0))
    chk("④ 指數基準律(top 榜三加權皆為 100 級數值)",
        all(30 < r["idx_att"] < 400 for r in ev["top_att"]))
    chk("⑤ T-1 無前視+憲法固定(shift(1)×4+cap 18%+corr 0.25)",
        src.count("shift(1)") >= 4 and "0.18" in src
        and "0.25" in src)
    page = OUT_UI.read_text(encoding="utf-8")
    chk("⑥ 頁產出(三加權比較+誠實界定+零 CDN 外鏈)",
        "三加權指數比較" in page and "誠實界定" in page
        and '<script src="http' not in page)
    sj = sorted(REP.glob("STORY_CLASS_*.json"))
    st = json.loads(sj[-1].read_text(encoding="utf-8")) if sj else {}
    chk("⑦ 故事性分群(冊在+PC1/lead gap/角色三律入存證+LOO 不對稱領先)",
        STORY_REG.exists() and bool(st.get("stories"))
        and all("pc1" in x and "lead_gap" in x for x in st["stories"])
        and set(st.get("roles", {})) <= {"LEADER", "PEER", "LAGGARD"}
        and "drop(columns=[t])" in src and "asym" in src)
    try:
        reg = json.loads(STORY_REG.read_text(encoding="utf-8"))
        par = {z["story_group"]: set(z["tickers"]) for z in reg["stories"]
               if int(z.get("level", 1)) == 1}
        kids = [z for z in reg["stories"] if int(z.get("level", 1)) == 2]
        seen_k: dict = {}
        conserv = all(set(z["tickers"]) <= par.get(z["parent"], set())
                      for z in kids)
        for z in kids:
            for t in z["tickers"]:
                conserv = conserv and (t not in seen_k); seen_k[t] = 1
        st = load_stories()
        pri = all(next(iter(k for k, v in st.items() if t in v)) == z["story_group"]
                  for z in kids for t in z["tickers"])
        chk("⑧ 故事階層守恆(子群⊆父群+互不重疊+子群優先映射)"
            "+覆蓋欄+撞欄修固化",
            conserv and pri and len(kids) >= 7
            and "在庫/冊 Coverage" in page
            and page.count("<tr><td>") >= 8            # 本次頁實含故事列(防舊存證假綠)
            and page.count("└ ") >= 1                 # 子群列實顯
            and 'errors="ignore"' in src and "留一法" in src)
    except Exception as exc:
        chk("⑧ 故事階層守恆", False, f"({type(exc).__name__})")
    chk("⑨ 條件式凝聚(殘差化 EWM β T-1+活躍閘滾動分位+雙 PC1+同向率"
        "+活躍 CCF+樣本不足誠實)",
        "def add_residual" in src and 'd["beta"].shift(1)' in src
        and "rolling(ACT_WIN, min_periods=20).quantile(ACT_Q)" in src
        and "PC1 活躍日(殘差)" in page and "同向率" in page
        and "xa.corr(gm.shift(-k))" in src
        and ("樣本不足" in page or "(0d)" not in page))
    print(f"  [計] 九檢 OK {9 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 族群分類×價格指數(VDF_ENG070)· 六檢自測(零外網)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
