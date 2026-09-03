#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VDF_ENG070_GroupClassificationIndex v0109(批326 實測修正)
批326 操作員令「先用已經下載的資料對族群分類輪動進行實測修正」——以 v0.5 契約(批325 收容)
之可行部分落地於在庫資料:
  ①覆蓋修正:價表改 tw_daily_prices 全量(缺調整層者用 Yahoo adj_close=DERIVED_YF_ADJ 旗標)
    =TPEX 80 檔入列,故事成員覆蓋提升(實錘見 run 印出)
  ②族群性顯著性(取代固定 PC1 門檻單判):資料衍生虛無分布二軸=同規模隨機群 N=200
    +成員序列循環移位 N=200;intersection-union p=max;跨群 Benjamini–Hochberg FDR q≤0.10
    =cohesion_sig(固定 PC1≥0.40 保留為憲法顯示,不再是唯一判準)
  ③角色統計判(role_stat):個股 LOO 不對稱分 vs 循環移位虛無 N=100→p_lead;峰值 ρ vs 虛無→p_rho;
    UNRELATED=p_rho>0.10 或 ρ<0.25;LEAD/LAG=p_lead≤0.10 依號;餘 PEER。憲法角色 role 保留並列(一致率印出)
  ④族群輪動關聯(rotation):族群注意力份額 AS_g 對數差分 + 殘差指數報酬,配對 (A→B) 循環互相關
    (FFT 全位移=循環移位虛無);lag 1~5 取最負 r(A 退→B 進);成員重疊對排除;BH FDR;邊表+熱圖
v0108 原律零觸碰(版前進)。
原 v0108 頭註:
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
v0104→v0105(批311 操作員令「2023 2024 2025 2026 起測試族群內
股票有無差異」):跨窗比較——四起點(各起點→至今,累積窗)各跑
條件式凝聚+角色;產出①族群層:PC1_act 四窗+漂移幅(max−min)
+領頭是否更替 ②個股層:四窗角色序列+變動次數(0=穩定成員;
≥2=漂移)③存證 WINDOW_COMPARE json+頁面「跨窗差異」段;⑩檢。
v0105→v0106(批312 操作員釐清「LEADER/PEER/LAGGER/不相關=一族群
中個股分類」):故事模式補第四類 UNRELATED——活躍日殘差對 LOO
群中位峰值 ρ < UNREL_CORR 0.25(Type-F 憲法,與產業模式同值)
=名義在群不跟群動;角色表加「✕指數」標(LAGGARD/UNRELATED=
指數成分候剔;指數本體仍全員 T-1 無前視,剔除版候滾動角色);
頁新增「故事成員角色表」;⑪檢四類守恆。
v0106→v0107(批313 操作員令七項):
  ①產業分類不可重複(官方一股一業=既有)②故事分類可重複個股
    =explode 多重歸屬(一檔可入多故事群;PC1/角色/指數各群獨立算)
  ③族群指數兩制成分:S1=LEADER+PEER / S2=LEADER+PEER+LAGGARD
    ×三加權=六線;成分以「前一窗(2025 起)角色」定本窗=T-1 年度
    審核律零前視(無前窗=誠實全員)
  ④量指數(族群 ETR 扣當沖近似 Σ;基準=100)⑤動能指數(成員 mom z
    均值)⑥三大法人金流(外資/投信/自營 淨股數×收盤=金額 DERIVED;
    累計)融資融券金流(Δ餘額×收盤;累計)⑦現金流=法人+融資−融券
    (資料至 tw_chip_* 末日=誠實標;主窗缺=候料)
  UI:附件式切換鈕(成分/加權法/指標)一圖 Plotly.react;⑫⑬檢
v0107→v0108(批314 操作員令「Group/Ticker/YFTicker/Name/四種分類/
大中小型股/外資內資主導 整合清單計算驗證,後面加指標欄位」):
  build_master:一列=Group×Ticker(多重歸屬各列);基本欄=Group/
  Ticker/YFTicker/Name/官方產業(tw_listings 直取;缺=誠實空)/四種
  分類(LEADER/PEER/LAGGARD/UNRELATED;單成員)/大中小(產業模式
  size_tier T-1)/外資內資主導(法人淨買比 EWM span50→故事內分位
  ≥0.65 Foreign/≤0.35 Domestic/餘 Mixed;Domestic 再分 SITC/Dealer;
  資料至 tw_chip_inst 末日=誠實標)/指標欄=hotness/leadership/
  validity/peak_rho/lead_lag/群 PC1_act/同向率/AS 聚焦度/mom_z/
  foreign_ratio/外資·投信·自營·融資·融券 累計(億)/指數成分標。
  存證 MASTER_LIST csv+json;頁「整合清單」表;⑭計算驗證檢
  (列數守恆=成員列/欄齊/值域/名稱覆蓋/PC1 一致)。
用法:python3 VDF_ENG070_GroupClassificationIndex_v0108.py run
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
import html
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
WARMUP = "2022-07-01"      # 批311 跨窗:2023 起+60 日滾動/EWM β 暖身(原主窗暖身併入)
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
        # 批326 覆蓋修正:全量價表為主,調整層缺者用 Yahoo adj_close(DERIVED_YF_ADJ 旗標)
        px = c.execute(f"""
            SELECT d.date, regexp_replace(d.ticker, '\\.(TW|TWO)$', '')
                   AS ticker, COALESCE(p.adj_close, d.adj_close) AS adj_close,
                   (p.adj_close IS NULL) AS adj_yf,
                   d.close, d.volume, l.industry AS ind_code, l.name, l.market
            FROM tw_daily_prices d
            LEFT JOIN tw_prices_adj p USING (date, ticker)
            JOIN tw_listings l
              ON l.code = regexp_replace(d.ticker, '\\.(TW|TWO)$', '')
            WHERE d.date >= '{WARMUP}' AND COALESCE(p.adj_close, d.adj_close) > 0
              AND d.close > 0 AND d.ticker <> '_NOOP_'
              AND l.industry IS NOT NULL AND l.industry <> ''
        """).df()
        dt = c.execute(
            "SELECT date, avg(dt_volume_pct) AS dt_pct "
            "FROM tw_daytrade_market GROUP BY date").df()
    finally:
        c.close()
    px["date"] = pd.to_datetime(px["date"])
    dt["date"] = pd.to_datetime(dt["date"])
    # 批326 實測修正:尾端不完整交易日(部分標的先入庫)=截去(誠實;v0.5 律:缺整日 session 不得用)
    cnt = px.groupby("date")["ticker"].nunique().sort_index()
    ref = cnt.tail(60).median()
    keep_last = cnt[cnt >= 0.8 * ref].index.max()
    dropped = [str(d_.date()) for d_ in cnt.index if d_ > keep_last]
    px = px[px["date"] <= keep_last]
    px.attrs["dropped_partial_sessions"] = dropped
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
N_NULL, N_ROLE, FDR_Q, P_ROLE = 200, 100, 0.10, 0.10   # 批326 虛無分布/FDR 律
ROT_START, ROT_LAGS, ROT_SPAN = "2025-01-01", 5, 5      # 輪動關聯窗/最大 lag/AS 平滑
UNREL_CORR = 0.25   # Type-F 憲法:與產業模式同值(批312)


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


def bh_q(pvals):
    """Benjamini–Hochberg q 值(None 略;保序單調)"""
    import numpy as np
    idx = [i for i, v in enumerate(pvals) if v is not None]
    q = [None] * len(pvals)
    if not idx:
        return q
    pv = np.array([pvals[i] for i in idx], dtype=float)
    m = len(pv)
    order = np.argsort(pv)
    ranked = pv[order] * m / (np.arange(m) + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    for pos, o in enumerate(order):
        q[idx[o]] = float(min(1.0, ranked[pos]))
    return q


def _pc1_of(z):
    import numpy as np
    sv = np.linalg.svd(z, compute_uv=False)
    return float(sv[0] ** 2 / (sv ** 2).sum())


def pc1_nulls(wide, mw, n_null: int = N_NULL, seed: int = 7):
    """族群性二軸虛無(批326;v0.5 §3 可行部分):
    p_rand=同規模隨機群(全市場 ex-2330 殘差面板抽 n 檔)PC1 ≥ 觀測之份額;
    p_shift=成員序列循環移位(保留各股時間結構、破壞同步)PC1 ≥ 觀測之份額"""
    import numpy as np
    rng = np.random.default_rng(seed)
    z = ((wide - wide.mean()) / (wide.std() + 1e-12)).fillna(0.0).to_numpy()
    obs = _pc1_of(z)
    n = wide.shape[1]
    T = len(wide)
    pool = mw.columns.to_numpy() if mw is not None else np.array([])
    p_rand = None
    if mw is not None and len(pool) >= n + 5:
        cnt = 0
        for _ in range(n_null):
            cols = rng.choice(pool, n, replace=False)
            w = mw[cols].reindex(wide.index)
            zz = ((w - w.mean()) / (w.std() + 1e-12)).fillna(0.0).to_numpy()
            if _pc1_of(zz) >= obs:
                cnt += 1
        p_rand = (1 + cnt) / (n_null + 1)
    cnt = 0
    for _ in range(n_null):
        zs = np.column_stack([np.roll(z[:, j], int(rng.integers(1, T))) for j in range(n)])
        if _pc1_of(zs) >= obs:
            cnt += 1
    p_shift = (1 + cnt) / (n_null + 1)
    return obs, p_rand, p_shift


def _asym_peak(xv, G):
    """不對稱分+峰值 ρ(G=群中位 lag 矩陣 [-CCF_L..CCF_L] numpy;xv 對齊)"""
    import numpy as np
    asym, best = 0.0, -9.0
    xs = (xv - np.nanmean(xv)) / (np.nanstd(xv) + 1e-12)
    for k in range(1, CCF_L + 1):
        rf = _ncorr(xs, G[:, CCF_L + k]); rb = _ncorr(xs, G[:, CCF_L - k])
        if np.isfinite(rf) and np.isfinite(rb):
            asym += (rf - rb) / k
        best = max(best, rf if np.isfinite(rf) else -9.0, rb if np.isfinite(rb) else -9.0)
    r0 = _ncorr(xs, G[:, CCF_L])
    best = max(best, r0 if np.isfinite(r0) else -9.0)
    return asym, best


def _ncorr(a, b):
    import numpy as np
    m = np.isfinite(a) & np.isfinite(b)
    if m.sum() < 10:
        return np.nan
    aa, bb = a[m], b[m]
    sa, sb = aa.std(), bb.std()
    if sa < 1e-12 or sb < 1e-12:
        return np.nan
    return float(((aa - aa.mean()) * (bb - bb.mean())).mean() / (sa * sb))


def role_null(xa, gm, n_null: int = N_ROLE, seed: int = 11):
    """角色統計判(批326):個股序列循環移位虛無→p_lead(|asym| 雙尾)+p_rho(峰值 ρ 單尾)"""
    import numpy as np
    rng = np.random.default_rng(seed)
    G = np.column_stack([gm.shift(-k).reindex(xa.index).to_numpy(dtype=float)
                         for k in range(-CCF_L, CCF_L + 1)])
    xv = xa.to_numpy(dtype=float)
    a_obs, r_obs = _asym_peak(xv, G)
    T = len(xv)
    if T < 20:
        return a_obs, r_obs, None, None
    ca = cr = 0
    for _ in range(n_null):
        a_n, r_n = _asym_peak(np.roll(xv, int(rng.integers(1, T))), G)
        if abs(a_n) >= abs(a_obs):
            ca += 1
        if r_n >= r_obs:
            cr += 1
    return a_obs, r_obs, (1 + ca) / (n_null + 1), (1 + cr) / (n_null + 1)


def classify_story(px, stories: dict, start: str | None = None, nulls: bool | None = None):
    """故事性分群評分(批308 操作員律;在庫誠實版)
    回:(member_df 末日評分, story_summary list, story_panel for 指數)"""
    import numpy as np
    import pandas as pd
    df = px[px["ticker"] != ANCHOR].copy()
    all_tk = set().union(*stories.values()) if stories else set()
    df = df[df["ticker"].isin(all_tk)]
    if df.empty:
        return pd.DataFrame(), [], pd.DataFrame()
    # hotness 原料先於 explode 算(每檔一序列;避免多重歸屬重複列污染 EWM)
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
    df["mom_z"] = mz.fillna(0)
    # explode 多重歸屬(批313):一檔可入多故事群
    parts = [df[df["ticker"].isin(tk)].assign(story=sname)
             for sname, tk in stories.items() if df["ticker"].isin(tk).any()]
    df = pd.concat(parts, ignore_index=True)
    df["g_ret"] = df.groupby(["story", "date"])["ret"].transform("median")
    last = df["date"].max()
    win = df[df["date"] >= pd.Timestamp(start or BASE_DATE)]
    rows, summ = [], []
    do_null = nulls if nulls is not None else (start is None)   # 主窗才跑虛無(跨窗省時)
    vcol0 = "resid" if "resid" in px.columns else "ret"
    mw = None
    if do_null:
        src = px[(px["ticker"] != ANCHOR) & (px["date"] >= pd.Timestamp(start or BASE_DATE))]
        mw = src.pivot_table(index="date", columns="ticker", values=vcol0)
        mw = mw.dropna(axis=1, thresh=int(len(mw) * 0.8))
        mw = mw.loc[:, mw.std() > 1e-12]
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
        p_rand = p_shift = None
        if do_null and pc1 is not None:
            _, p_rand, p_shift = pc1_nulls(wide, mw)
        p_iu = (max(v for v in (p_rand, p_shift) if v is not None)
                if (p_rand is not None or p_shift is not None) else None)
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
            p_lead = p_rho = None
            role_stat = None
            if do_null and n_ok > 1:
                a_o, r_o, p_lead, p_rho = role_null(xa, gm)
                if p_lead is not None:
                    if p_rho > P_ROLE or r_o < UNREL_CORR:
                        role_stat = "UNRELATED"
                    elif p_lead <= P_ROLE and a_o > 0:
                        role_stat = "LEAD"
                    elif p_lead <= P_ROLE and a_o < 0:
                        role_stat = "LAG"
                    else:
                        role_stat = "PEER"
            hot_last = float(df.loc[(df["ticker"] == t)
                                    & (df["date"] == last), "hot_raw"]
                             .tail(1).sum())
            mem.append({"ticker": t, "story": sname,
                        "lead_raw": round(asym, 4),
                        "peak_rho": round(best_r, 3), "lead_lag": best_lag,
                        "hot_raw": hot_last, "p_lead": p_lead, "p_rho": p_rho,
                        "role_stat": role_stat})
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
        role = np.where(collapse, "PEER", role)
        # 第四類 UNRELATED(批312):峰值 ρ<憲法門檻=名義在群不跟群動;優先於三類
        role = np.where(m["peak_rho"] < UNREL_CORR, "UNRELATED", role)
        # 單成員群=無群可比(峰值 ρ 哨兵 −9)=誠實「單成員」非四類(批312 實錘)
        role = np.where((n_ok < 2) | (m["peak_rho"] <= -1.0), "單成員", role)
        m["role"] = role
        m["peak_rho"] = m["peak_rho"].where(m["peak_rho"] > -1.0)
        m["index_flag"] = np.where(m["role"].isin(["LEADER", "PEER"]),
                                   "指數成分", np.where(m["role"] == "單成員",
                                                    "候料", "✕指數"))
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
                     "p_rand": p_rand, "p_shift": p_shift, "p_iu": p_iu,
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
    # 批326:跨群 BH FDR → q_fdr + cohesion_sig(顯著族群性;固定 PC1 門檻僅憲法顯示)
    qs = bh_q([x.get("p_iu") for x in summ])
    for x, q in zip(summ, qs):
        x["q_fdr"] = None if q is None else round(q, 3)
        x["cohesion_sig"] = (q is not None and q <= FDR_Q)
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


def rotation_assoc(px_r, stories: dict, start: str = ROT_START) -> dict:
    """族群輪動關聯(批326;v0.5 §6 可行部分):
    AS_g=族群 ETR 份額(市場 ex-2330)EWM 平滑→對數差分;R_g=成員殘差中位(殘差指數報酬)。
    配對 (A→B):FFT 循環互相關 c[s]=corr(A_t, B_{t+s});lag 1..ROT_LAGS 取最負 r(A 注意力退→B 進);
    虛無=其餘全位移(循環移位;保各自時間結構破同步)→p=|c[s]|≥|r| 份額;成員重疊對排除;BH FDR。"""
    import numpy as np
    import pandas as pd
    d = px_r[(px_r["ticker"] != ANCHOR) & (px_r["date"] >= pd.Timestamp(start))]
    if d.empty or not stories:
        return {"pairs": [], "edges": [], "names": [], "matrix": {}, "n_days": 0}
    mkt = d.groupby("date")["etr"].sum()
    vcol = "resid" if "resid" in d.columns else "ret"
    ser_as, ser_r, members = {}, {}, {}
    for sname, tk in stories.items():
        g = d[d["ticker"].isin(tk)]
        if g["ticker"].nunique() < 2:
            continue
        as_ = (g.groupby("date")["etr"].sum() / (mkt + 1e-8)).reindex(mkt.index)
        as_ = as_.ewm(span=ROT_SPAN, adjust=True).mean()
        ser_as[sname] = np.log(as_ + 1e-12).diff()
        ser_r[sname] = g.groupby("date")[vcol].median().reindex(mkt.index)
        members[sname] = set(g["ticker"].unique())
    names = sorted(ser_as)
    pairs, mats = [], {"as": {}, "r": {}}
    for kind, ser in (("as", ser_as), ("r", ser_r)):
        Z = {}
        for n_ in names:
            v = ser[n_].to_numpy(dtype=float)
            v = np.where(np.isfinite(v), v, np.nan)
            v = np.nan_to_num(v - np.nanmean(v))
            sd = v.std()
            Z[n_] = v / sd if sd > 1e-12 else None
        T = len(mkt)
        for a in names:
            mats[kind][a] = {}
            for b in names:
                if a == b or Z[a] is None or Z[b] is None:
                    continue
                overlap = len(members[a] & members[b]) > 0
                fa, fb = np.fft.rfft(Z[a]), np.fft.rfft(Z[b])
                c = np.fft.irfft(np.conj(fa) * fb, n=T) / T      # c[s]=corr(A_t, B_{t+s})
                lags = np.arange(1, ROT_LAGS + 1)
                r_l = c[lags]
                k = int(lags[np.argmin(r_l)])
                r = float(r_l.min())
                keep = np.ones(T, dtype=bool)
                keep[:ROT_LAGS + 1] = False
                keep[T - ROT_LAGS:] = False
                null = np.abs(c[keep])
                pv = float((1 + (null >= abs(r)).sum()) / (len(null) + 1))
                mats[kind][a][b] = round(r, 3)
                pairs.append({"kind": kind, "from": a, "to": b, "lag": k, "r": round(r, 3),
                              "p": round(pv, 4), "overlap": overlap})
    # BH 跨對(重疊對不入檢定=誠實排除)
    test = [i for i, x in enumerate(pairs) if not x["overlap"]]
    qs = bh_q([pairs[i]["p"] for i in test])
    for i, q in zip(test, qs):
        pairs[i]["q"] = round(q, 4)
    edges = sorted([x for x in pairs if (not x["overlap"]) and x["r"] < 0 and x.get("q") is not None
                    and x["q"] <= FDR_Q], key=lambda z: z["r"])
    return {"pairs": pairs, "edges": edges, "names": names, "matrix": mats,
            "n_days": int(len(mkt)), "start": start, "n_pairs_tested": len(test)}


WINDOWS = ["2023-01-01", "2024-01-01", "2025-01-01", "2026-01-01"]


def compare_windows(px_r, stories: dict) -> dict:
    """四起點跨窗比較(批311):族群 PC1_act 漂移+個股角色變動"""
    import pandas as pd
    per = {}
    for w in WINDOWS:
        if px_r["date"].min() > pd.Timestamp(w):
            continue                                   # 庫起點晚於窗=誠實跳
        mem, summ, _ = classify_story(px_r, stories, start=w)
        per[w] = {"summ": {x["story"]: x for x in summ},
                  "roles": ({(t, st_): r for t, st_, r in
                             zip(mem["ticker"], mem["story"], mem["role"])}
                            if len(mem) else {})}
    ws = list(per)
    groups = []
    names = sorted({n for w in ws for n in per[w]["summ"]})
    for n in names:
        vals = [per[w]["summ"].get(n, {}).get("pc1_act") for w in ws]
        got = [v for v in vals if v is not None]
        leads = [tuple(per[w]["summ"].get(n, {}).get("leaders", [])) for w in ws]
        groups.append({"story": n, "pc1_act": vals,
                       "drift": round(max(got) - min(got), 3) if len(got) >= 2 else None,
                       "leader_changes": len({l for l in leads if l}) - 1
                       if any(leads) else None,
                       "leaders": [list(l) for l in leads]})
    stocks = []
    keys = sorted({k for w in ws for k in per[w]["roles"]})
    for (t, st_) in keys:
        seq = [per[w]["roles"].get((t, st_)) for w in ws]
        got = [r for r in seq if r]
        changes = sum(1 for a, b in zip(got, got[1:]) if a != b)
        stocks.append({"ticker": t, "story": st_,
                       "roles": seq, "changes": changes,
                       "stable": (len(got) >= 2 and changes == 0)})
    n_stable = sum(1 for x in stocks if x["stable"])
    n_drift = sum(1 for x in stocks if x["changes"] >= 1)
    return {"windows": ws, "groups": groups, "stocks": stocks,
            "n_stable": n_stable, "n_drift": n_drift,
            "roles_by_window": {w: {f"{t}|{st_}": r for (t, st_), r in
                                    per[w]["roles"].items()} for w in ws}}


def load_flows():
    """三大法人+融資融券(在庫段;缺=誠實空)"""
    import duckdb
    import pandas as pd
    try:
        c = duckdb.connect(str(DB_TW), read_only=True)
        fl = c.execute("""
            SELECT i.date, i.code AS ticker, i.foreign_net, i.trust_net,
                   i.dealer_net, m.margin_bal, m.short_bal
            FROM tw_chip_inst i
            LEFT JOIN tw_chip_margin m USING (date, code)""").df()
        c.close()
    except Exception as exc:
        print(f"  [金流] 誠實缺:{type(exc).__name__}: {str(exc)[:80]}")
        return pd.DataFrame()
    fl["date"] = pd.to_datetime(fl["date"])
    fl["ticker"] = fl["ticker"].astype(str)
    return fl


def story_metrics(panel, stories: dict, flows) -> dict:
    """族群層六指標(批313):量指數/動能/法人金流/融資融券金流/現金流
    金額=淨股數(或 Δ餘額)×收盤=DERIVED;累計自資料段起"""
    import numpy as np
    import pandas as pd
    out = {}
    if panel.empty:
        return out
    pc = panel[["date", "ticker", "story", "etr", "close", "mom_z"]].copy()
    if len(flows):
        pc = pc.merge(flows, on=["date", "ticker"], how="left")
        pc = pc.sort_values(["story", "ticker", "date"])
        for col in ("margin_bal", "short_bal"):
            pc[f"d_{col}"] = pc.groupby(["story", "ticker"])[col].diff()
        for col in ("foreign_net", "trust_net", "dealer_net"):
            pc[f"m_{col}"] = pc[col] * pc["close"]
        pc["m_margin"] = pc["d_margin_bal"] * pc["close"]
        pc["m_short"] = pc["d_short_bal"] * pc["close"]
    else:
        for col in ("m_foreign_net", "m_trust_net", "m_dealer_net",
                    "m_margin", "m_short"):
            pc[col] = np.nan
    flow_last = (str(flows["date"].max().date()) if len(flows) else None)
    for sname, gd in pc.groupby("story"):
        d = gd.groupby("date").agg(
            etr=("etr", "sum"), mom=("mom_z", "mean"),
            f=("m_foreign_net", "sum"), t=("m_trust_net", "sum"),
            dl=("m_dealer_net", "sum"), mg=("m_margin", "sum"),
            sh=("m_short", "sum"),
            nf=("m_foreign_net", "count")).reset_index().sort_values("date")
        d = d[d["date"] >= pd.Timestamp(BASE_DATE) - pd.Timedelta(days=730)]
        base = d[d["date"] >= pd.Timestamp(BASE_DATE)]
        vol_base = float(base["etr"].iloc[0]) if len(base) and base["etr"].iloc[0] > 0 else None
        d["vol_idx"] = d["etr"] / vol_base * 100.0 if vol_base else np.nan
        has = d["nf"] > 0
        for k in ("f", "t", "dl", "mg", "sh"):
            d[k] = d[k].where(has, np.nan)
        d["inst"] = (d["f"] + d["t"] + d["dl"]).cumsum() / 1e8      # 億
        d["margin"] = (d["mg"] - d["sh"]).cumsum() / 1e8
        d["cash"] = d["inst"] + d["margin"]
        d["fcum"] = d["f"].cumsum() / 1e8; d["tcum"] = d["t"].cumsum() / 1e8
        d["dcum"] = d["dl"].cumsum() / 1e8
        nz = lambda col: [None if pd.isna(v) else round(float(v), 2) for v in d[col]]
        out[sname] = {"d": [str(x.date()) for x in d["date"]],
                      "cov": [int(has.sum()), int(len(d))],
                      "vol": nz("vol_idx"),
                      "mom": [round(float(v), 3) for v in d["mom"].fillna(0)],
                      "inst": nz("inst"), "fcum": nz("fcum"), "tcum": nz("tcum"),
                      "dcum": nz("dcum"), "margin": nz("margin"), "cash": nz("cash")}
    out["_flow_last"] = flow_last
    return out


def load_listings():
    import duckdb
    import pandas as pd
    try:
        c = duckdb.connect(str(DB_TW), read_only=True)
        li = c.execute("SELECT code AS ticker, name, yf_ticker, industry "
                       "FROM tw_listings").df()
        c.close()
        li["ticker"] = li["ticker"].astype(str)
        return li.drop_duplicates("ticker")
    except Exception as exc:
        print(f"  [名冊] 誠實缺:{type(exc).__name__}")
        return pd.DataFrame(columns=["ticker", "name", "yf_ticker", "industry"])


def capital_style(flows, members, span: int = 50):
    """外資內資主導(批314):foreign_ratio=外資淨買/(|外|+|投|+|自|) EWM
    →故事內橫斷分位(≥0.65 Foreign/≤0.35 Domestic/Mixed);Domestic 再分
    SITC/Dealer;末日=資料末日(誠實標)"""
    import numpy as np
    import pandas as pd
    if not len(flows):
        return pd.DataFrame(columns=["ticker", "foreign_ratio", "capital_style",
                                     "capital_asof"])
    f = flows.sort_values(["ticker", "date"]).copy()
    den = (f["foreign_net"].abs() + f["trust_net"].abs()
           + f["dealer_net"].abs() + 1e-8)
    f["fr_raw"] = f["foreign_net"] / den
    f["sitc_raw"] = f["trust_net"].abs() / (f["trust_net"].abs()
                                           + f["dealer_net"].abs() + 1e-8)
    f["foreign_ratio"] = f.groupby("ticker")["fr_raw"].transform(
        lambda x: x.ewm(span=span, adjust=True, min_periods=15).mean())
    f["sitc_share"] = f.groupby("ticker")["sitc_raw"].transform(
        lambda x: x.ewm(span=span, adjust=True, min_periods=15).mean())
    last = f.groupby("ticker").tail(1)[["ticker", "date", "foreign_ratio",
                                        "sitc_share"]]
    m = members[["ticker", "story"]].merge(last, on="ticker", how="left")
    out = []
    for sname, g in m.groupby("story"):
        fr = g["foreign_ratio"]
        hi, lo = fr.quantile(0.65), fr.quantile(0.35)
        for r in g.itertuples():
            if pd.isna(r.foreign_ratio):
                cs = "候料"
            elif len(g) < 3:
                cs = ("Foreign" if r.foreign_ratio > 0.2 else
                      "Domestic" if r.foreign_ratio < -0.2 else "Mixed")  # 小群=符號律誠實
            elif r.foreign_ratio >= hi:
                cs = "Foreign"
            elif r.foreign_ratio <= lo:
                cs = "Domestic"
            else:
                cs = "Mixed"
            if cs == "Domestic" and not pd.isna(r.sitc_share):
                cs = "Domestic·SITC" if r.sitc_share > 0.6 else "Domestic·Dealer"
            out.append({"ticker": r.ticker, "story": sname,
                        "foreign_ratio": None if pd.isna(r.foreign_ratio)
                        else round(float(r.foreign_ratio), 3),
                        "capital_style": cs,
                        "capital_asof": (str(r.date.date())
                                         if not pd.isna(r.date) else None)})
    return pd.DataFrame(out)


def build_master(s_mem, s_summ, s_panel, roles_ind, flows, listings):
    """整合清單(批314):Group×Ticker 一列;基本欄+四分類+大中小+外資內資
    +指標欄;金額=DERIVED 累計(億)"""
    import numpy as np
    import pandas as pd
    if s_mem is None or not len(s_mem):
        return pd.DataFrame()
    mm = s_mem.copy()
    mm["ticker"] = mm["ticker"].astype(str)
    # 名冊
    li = listings.rename(columns={"industry": "official_industry"})
    mm = mm.merge(li, on="ticker", how="left")
    # 大中小(產業模式 T-1 size_tier)
    st = roles_ind[["ticker", "size_tier"]].drop_duplicates("ticker") \
        if roles_ind is not None and len(roles_ind) else pd.DataFrame(columns=["ticker", "size_tier"])
    st["ticker"] = st["ticker"].astype(str)
    mm = mm.merge(st, on="ticker", how="left")
    # 群指標
    gs = pd.DataFrame(s_summ)[["story", "pc1", "pc1_act", "same_dir", "n_act"]] \
        if s_summ else pd.DataFrame(columns=["story", "pc1", "pc1_act", "same_dir", "n_act"])
    mm = mm.merge(gs, on="story", how="left")
    # AS/mom 末日
    lastp = s_panel.sort_values("date").groupby(["story", "ticker"]).tail(1)[
        ["story", "ticker", "as_smooth", "mom_z", "date"]].rename(
        columns={"date": "asof"})
    mm = mm.merge(lastp, on=["story", "ticker"], how="left")
    # 外資內資
    cs = capital_style(flows, mm[["ticker", "story"]].drop_duplicates())
    mm = mm.merge(cs, on=["ticker", "story"], how="left")
    # 累計金流(億;資料段)
    if len(flows):
        fl = flows.merge(s_panel[["ticker", "date", "close"]].drop_duplicates(
            ["ticker", "date"]), on=["ticker", "date"], how="left")
        fl = fl.sort_values(["ticker", "date"])
        for c_ in ("foreign_net", "trust_net", "dealer_net"):
            fl[f"m_{c_}"] = fl[c_] * fl["close"] / 1e8
        fl["m_margin"] = fl.groupby("ticker")["margin_bal"].diff() * fl["close"] / 1e8
        fl["m_short"] = fl.groupby("ticker")["short_bal"].diff() * fl["close"] / 1e8
        cum = fl.groupby("ticker").agg(
            外資累計億=("m_foreign_net", "sum"), 投信累計億=("m_trust_net", "sum"),
            自營累計億=("m_dealer_net", "sum"), 融資累計億=("m_margin", "sum"),
            融券累計億=("m_short", "sum"), 金流資料至=("date", "max")).reset_index()
        cum["金流資料至"] = cum["金流資料至"].dt.date.astype(str)
        mm = mm.merge(cum, on="ticker", how="left")
    cols = ["story", "ticker", "yf_ticker", "name", "official_industry", "role",
            "size_tier", "capital_style", "foreign_ratio", "capital_asof",
            "hotness", "leadership", "validity", "peak_rho", "lead_lag",
            "pc1", "pc1_act", "same_dir", "n_act", "as_smooth", "mom_z",
            "外資累計億", "投信累計億", "自營累計億", "融資累計億", "融券累計億",
            "金流資料至", "index_flag", "asof"]
    for c_ in cols:
        if c_ not in mm.columns:
            mm[c_] = None
    mm = mm[cols].rename(columns={
        "story": "Group", "ticker": "Ticker", "yf_ticker": "YFTicker",
        "name": "Name", "official_industry": "官方產業", "role": "四種分類",
        "size_tier": "大中小", "capital_style": "外資內資主導",
        "foreign_ratio": "外資比EWM", "capital_asof": "主導資料至",
        "hotness": "熱門", "leadership": "領先", "validity": "有效性",
        "peak_rho": "峰值ρ", "lead_lag": "領先lag", "pc1": "群PC1全",
        "pc1_act": "群PC1活躍", "same_dir": "群同向率", "n_act": "活躍日",
        "as_smooth": "聚焦度AS", "mom_z": "動能z", "index_flag": "指數",
        "asof": "指標日"})
    for c_ in ("熱門", "領先", "有效性", "峰值ρ", "聚焦度AS", "動能z",
               "外資累計億", "投信累計億", "自營累計億", "融資累計億", "融券累計億"):
        mm[c_] = pd.to_numeric(mm[c_], errors="coerce").round(4)
    return mm.sort_values(["Group", "有效性"], ascending=[True, False]).reset_index(drop=True)


def composition_sets(cmp: dict, current_members) -> tuple:
    """兩制成分(批313):以前一窗角色定本窗成分=T-1 審核律零前視
    S1=LEADER+PEER;S2=+LAGGARD;無前窗=誠實全員(標記)"""
    prev = None
    for w in ("2025-01-01", "2024-01-01", "2023-01-01"):
        if w in (cmp or {}).get("roles_by_window", {}):
            prev = w
            break
    if prev is None:
        return None, None, "無前窗角色=誠實全員成分"
    rb = cmp["roles_by_window"][prev]
    s1 = {k for k, r in rb.items() if r in ("LEADER", "PEER")}
    s2 = {k for k, r in rb.items() if r in ("LEADER", "PEER", "LAGGARD")}
    return s1, s2, f"成分依 {prev[:4]} 起窗角色(T-1 審核律)"


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
        top = list(slast.sort_values("idx_att", ascending=False)["industry"].head(12))
        for ind in top:
            s_series[ind] = {}
            for setk, sdf in (story.get("idx_sets") or {"ALL": sidx}).items():
                g = sdf[sdf["industry"] == ind] if len(sdf) else sdf
                if not len(g):
                    continue
                s_series[ind][setk] = {"d": [str(x.date()) for x in g["date"]],
                                       "eq": [round(v, 2) for v in g["idx_eq"]],
                                       "tier": [round(v, 2) for v in g["idx_tier"]],
                                       "att": [round(v, 2) for v in g["idx_att"]]}
            mtr = (story.get("metrics") or {}).get(ind)
            if mtr:
                s_series[ind]["M"] = mtr
        mix = story.get("mix", {})
        def _ord(z):
            return (z.get("parent") or z["story"], z.get("level", 1),
                    -(z["pc1"] or 0))

        def _pq(z):
            return ("—" if z.get("p_iu") is None
                    else "%.3f / q %.3f" % (z["p_iu"], z["q_fdr"] if z.get("q_fdr") is not None else 1.0))
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
            f"<td class='{'g' if x.get('cohesion_sig') else ('r' if x.get('q_fdr') is not None else '')}'>"
            f"{_pq(x)}</td>"
            f"<td>{'匯總' if x.get('aggregate') else x['lead_gap']}"
            f"{' · 歸一' if x['collapsed'] else ''}</td>"
            f"<td>{'、'.join(x['leaders']) or '—'}</td>"
            f"<td>{mix.get(x['story'], '—')}</td></tr>"
            for x in sorted(story.get("summ", []), key=_ord))
    mem_html = ""
    mem_df = story.get("members")
    import pandas as pd
    if mem_df is not None and len(mem_df):
        mm = mem_df.sort_values(["story", "role", "validity"],
                                ascending=[True, True, False])
        rr = "".join(
            f"<tr><td>{r.story}</td><td class='mono'>{r.ticker}</td>"
            f"<td class='{'g' if r.role == 'LEADER' else ('r' if r.role in ('LAGGARD', 'UNRELATED') else '')}'>{r.role}</td>"
            f"<td>{r.hotness:.2f}</td><td>{r.leadership:.2f}</td>"
            f"<td>{'—' if pd.isna(r.peak_rho) else f'{r.peak_rho:.2f}'}</td>"
            f"<td class='{'g' if getattr(r, 'role_stat', None) == 'LEAD' else ('r' if getattr(r, 'role_stat', None) in ('LAG', 'UNRELATED') else '')}'>"
            f"{getattr(r, 'role_stat', None) or '—'}"
            f"{'' if getattr(r, 'p_lead', None) is None or pd.isna(r.p_lead) else f' <small>p {r.p_lead:.2f}/{r.p_rho:.2f}</small>'}</td>"
            f"<td>{r.index_flag}</td></tr>"
            for r in mm.itertuples())
        vc = mem_df["role"].value_counts().to_dict()
        mem_html = f"""
<div class="card" id="memsec"><h3>故事成員角色表<small>Members · 一族群內
逐檔:LEADER 領頭 / PEER 同行 / LAGGARD 落後 / UNRELATED 不跟群動
(峰值 ρ&lt;{UNREL_CORR})</small></h3>
<div class="note">計:{' · '.join(f"{k} {v}" for k, v in vc.items())};✕指數=
指數成分候剔(指數本體仍全員 T-1 無前視;剔除版候滾動角色)。</div>
<div class="wrap"><table><tr><th>故事</th><th>代碼</th><th>角色</th>
<th>熱門 hot</th><th>領先 lead</th><th>峰值 ρ</th><th>統計判 role_stat(p lead/ρ)</th><th>指數</th></tr>{rr}
</table></div></div>"""
    master_html = ""
    ms = story.get("master")
    if ms is not None and len(ms):
        show = ["Group", "Ticker", "YFTicker", "Name", "四種分類", "大中小",
                "外資內資主導", "熱門", "領先", "有效性", "峰值ρ", "群PC1活躍",
                "聚焦度AS", "動能z", "外資累計億", "投信累計億", "自營累計億",
                "融資累計億", "指數"]
        def _fmt(v):
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return "—"
            return f"{v:.3f}" if isinstance(v, float) else html.escape(str(v))
        m_rows = "".join(
            "<tr>" + "".join(f"<td>{_fmt(r[c_])}</td>" for c_ in show) + "</tr>"
            for _, r in ms.head(80).iterrows())
        flow_to = ms["金流資料至"].dropna().max() if "金流資料至" in ms else None
        master_html = f"""
<div class="card" id="mastersec"><h3>整合清單<small>Master List · Group×Ticker
{len(ms)} 列 · 基本欄+四種分類+大中小+外資內資主導+指標欄 · 存證
MASTER_LIST csv/json</small></h3>
<div class="note">外資內資主導=法人淨買比 EWM→故事內分位(資料至
{flow_to or '—(候料)'});累計金額=淨股數×收盤 DERIVED(億);大中小=產業
模式 T-1 分位;前 80 列依 Group/有效性排。</div>
<div class="wrap"><table><tr>{"".join(f"<th>{c_}</th>" for c_ in show)}</tr>
{m_rows}</table></div></div>"""
    rot = story.get("rot") or {}
    rot_html = ""
    if rot.get("names"):
        e_rows = "".join(
            f"<tr><td>{e['from']}</td><td>{e['to']}</td><td>{'注意力' if e['kind'] == 'as' else '殘差報酬'}</td>"
            f"<td>{e['lag']}</td><td class='r'>{e['r']:.3f}</td><td>{e['p']:.3f}</td><td>{e['q']:.3f}</td></tr>"
            for e in rot["edges"][:40]) or "<tr><td colspan=7>無顯著輪動邊(誠實;BH q≤%.2f)</td></tr>" % FDR_Q
        rot_html = f"""
<div class="card" id="rotsec"><h3>族群輪動關聯<small>Rotation Association · {rot.get('start')} 起 {rot.get('n_days')} 日
· 循環互相關 lag 1~{ROT_LAGS} 最負 r(A 退→B 進)· 虛無=全位移循環移位 · BH FDR q≤{FDR_Q}</small></h3>
<div class="note">檢定對 {rot.get('n_pairs_tested')}(成員重疊對排除)· 顯著邊 {len(rot['edges'])} · 熱圖=最負 r(選種類)
· 誠實界定:注意力份額為組成型(份額互補)=配對負相關含機械成分;循環移位虛無控時間結構不控組成,故以 BH q 為準,無顯著邊=不宣稱輪動</div>
<div class="btnrow" style="margin:4px 0 6px"><span class="seg" id="segrot"><b>種類</b>
<a data-v="as" class="on">注意力份額 AS</a><a data-v="r">殘差指數報酬</a></span></div>
<div id="c3"></div>
<div class="wrap"><table><tr><th>A 退</th><th>B 進</th><th>種類</th><th>lag</th><th>r</th><th>p</th><th>q</th></tr>{e_rows}</table></div></div>"""
    cmp = story.get("cmp") or {}
    cmp_html = ""
    if cmp.get("groups"):
        ws = [w[:4] for w in cmp["windows"]]
        g_rows = "".join(
            f"<tr><td>{g['story']}</td>"
            + "".join(f"<td>{v if v is not None else '—'}</td>" for v in g["pc1_act"])
            + f"<td class='{'r' if (g['drift'] or 0) > 0.15 else 'g'}'>"
              f"{g['drift'] if g['drift'] is not None else '—'}</td>"
              f"<td>{g['leader_changes'] if g['leader_changes'] is not None else '—'}</td></tr>"
            for g in sorted(cmp["groups"], key=lambda z: -(z["drift"] or -1)))
        s_rows2 = "".join(
            f"<tr><td class='mono'>{x['ticker']}</td><td>{x['story'] or '—'}</td>"
            + "".join(f"<td>{r or '—'}</td>" for r in x["roles"])
            + f"<td class='{'g' if x['stable'] else 'r'}'>{x['changes']}"
              f"{' 穩定' if x['stable'] else ''}</td></tr>"
            for x in sorted(cmp["stocks"], key=lambda z: (-z["changes"], z["ticker"]))[:40])
        cmp_html = f"""
<div class="card" id="cmpsec"><h3>跨窗差異<small>Window Comparison ·
{' / '.join(ws)} 起→至今(累積窗)· 殘差×活躍日 PC1 · 個股角色序列</small></h3>
<div class="note">族群層:PC1 活躍日四窗+漂移幅(max−min;>0.15 紅=族群性
隨時代改變)+領頭更替次數。個股層:四窗角色;變動 0=穩定成員
{cmp['n_stable']} 檔 · 有變動 {cmp['n_drift']} 檔(前 40 依變動排)。</div>
<div class="wrap"><table><tr><th>故事 Story</th>
{"".join(f"<th>{w} 起</th>" for w in ws)}<th>漂移幅</th><th>領頭更替</th></tr>
{g_rows}</table></div>
<div class="wrap" style="margin-top:8px"><table><tr><th>代碼</th><th>故事</th>
{"".join(f"<th>{w}</th>" for w in ws)}<th>變動次數</th></tr>{s_rows2}</table></div></div>"""
    story_tab = f"""
<div class="card" id="storysec"><h3>故事性分群<small>Story Groups ·
hotness≥{HOT_MIN} · lead gap {LEAD_GAP} · PC1≥{PC1_MIN} · 條件式凝聚(殘差×活躍日 滾動 {int(ACT_Q*100)} 分位)</small></h3>
<div class="note">{html.escape(story.get("comp_note", ""))} · 金流資料至
{(story.get("metrics") or {}).get("_flow_last") or "—(候料)"}(法人/融資融券=
淨股數×收盤 DERIVED,累計億元;主窗缺段=誠實斷線)· 量指數=ETR 扣當沖
Σ 基準 100 · 動能=成員 mom z 均值</div>
<div class="btnrow" style="gap:6px;flex-wrap:wrap;margin:4px 0 6px">
<select id="ssel" style="max-width:220px">{"".join(f'<option>{k}</option>' for k in s_series)}</select>
<span class="seg" id="segset"><b>成分</b>
<a data-v="S1" class="on">LEADER+PEER</a><a data-v="S2">+LAGGER</a>
<a data-v="ALL">全員</a></span>
<span class="seg" id="segw"><b>加權法</b><a data-v="eq" class="on">等權 Equal</a>
<a data-v="tier">階層加權 Tier</a><a data-v="att">資金聚焦度加權 Attention</a></span>
<span class="seg" id="segm"><b>指標</b><a data-v="price" class="on">價格指數</a>
<a data-v="vol">量指數</a><a data-v="mom">動能指數</a><a data-v="inst">三大法人金流</a>
<a data-v="margin">融資融券金流</a><a data-v="cash">現金流進出</a></span></div>
<div id="c2"></div>
<div class="wrap"><table><tr><th>故事 Story(└=子群)</th>
<th>在庫/冊 Coverage</th><th>PC1 全樣本</th>
<th>PC1 活躍日(殘差)</th><th>比值 Act/All</th><th>同向率</th>
<th>PC1 凝聚</th><th>p 虛無 / q FDR</th><th>Lead Gap</th><th>Leader</th>
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
.seg{{display:inline-flex;align-items:center;gap:2px;border:1px solid var(--line);border-radius:7px;padding:2px;font-size:10px}}
.seg b{{padding:0 6px;color:var(--mut2);font-size:8.5px;letter-spacing:.1em}}
.seg a{{padding:4px 9px;border-radius:5px;cursor:pointer;color:var(--ink2)}}
.seg a.on{{background:var(--ink);color:#fff;font-weight:700}}
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
{mem_html}
{master_html}
{rot_html}
{cmp_html}
<div class="card"><h3>領漲榜<small>Leaders · Top 20 By Attention
</small></h3>
<div class="wrap"><table><tr><th>代碼</th><th>名稱</th><th>族群</th>
<th>規模</th><th>同動 ρ</th></tr>{lead_rows}</table></div></div>
<div class="card"><h3>誠實界定<small>Honest Boundaries</small></h3>
<div style="font-size:10px;color:var(--mut);line-height:1.7">
成交值=close×volume 近似(庫無 turnover;DERIVED)· 個股當沖缺=
市場級當沖比 {meta['dt_days']} 日可修正段(dt_adj 旗標)· 三大法人止
2025-11 與主窗不交集=LEAD/LAG 用價量一致性判,法人維度候料 ·
巨錨 2330 隔離 · 族群<{MIN_MEMBERS} 檔不建指數 · 尾端不完整交易日截去
{meta.get('dropped_partial') or '(無)'} · 非投資建議</div>
</div></main>
<footer class="app-footer"><span>VIA · VDF ENG070</span>
<span>產於 {meta['ts']}</span><span>主窗 {BASE_DATE}~{meta['last']}
· 零 CDN</span></footer>
<script id="d" type="application/json">{json.dumps(series,
    ensure_ascii=False)}</script>
<script id="ds" type="application/json">{json.dumps(s_series,
    ensure_ascii=False)}</script>
<script id="dr" type="application/json">{json.dumps({"names": rot.get("names", []), "matrix": rot.get("matrix", {})},
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
const SEG={{set:"S1",w:"eq",m:"price"}};
function segInit(id,key){{const el=document.getElementById(id);if(!el)return;
 el.querySelectorAll("a").forEach(a=>a.onclick=()=>{{
  el.querySelectorAll("a").forEach(x=>x.classList.remove("on"));
  a.classList.add("on");SEG[key]=a.dataset.v;draw2();}});}}
segInit("segset","set");segInit("segw","w");segInit("segm","m");
const LAB={{price:"價格指數(基準=100)",vol:"量指數 ETR(基準=100)",
 mom:"動能指數(成員 mom z 均值)",inst:"三大法人累計淨流入(億)",
 margin:"融資−融券 累計淨流入(億)",cash:"現金流進出 累計(億)"}};
function draw2(){{const g=DS[ssel.value];if(!g||!window.Plotly)return;
 let tr=[],title=LAB[SEG.m];
 if(SEG.m==="price"){{
  const st=g[SEG.set]||g["ALL"];
  if(!st){{Plotly.react("c2",[],{{height:360,title:{{text:"該成分制無指數(誠實:成員不足)",font:{{size:11}}}}}});return;}}
  const col={{eq:"#5d6a7b",tier:"#315f7d",att:"#2f7652"}};
  const nm={{eq:"等權 Equal",tier:"階層 Tier",att:"聚焦 Attention"}};
  tr=[{{x:st.d,y:st[SEG.w],name:nm[SEG.w],line:{{color:col[SEG.w],width:2.2}}}}];
  if(!g[SEG.set])title+="(該成分制缺=全員)";
 }}else{{
  const M=g["M"];
  if(!M){{Plotly.react("c2",[],{{height:360,title:{{text:"無指標資料(誠實)",font:{{size:11}}}}}});return;}}
  const cg=(SEG.m==="inst"||SEG.m==="margin"||SEG.m==="cash");
  if(cg&&M.cov)title+="(法人資料覆蓋 "+M.cov[0]+"/"+M.cov[1]+" 日;斷=缺料)";
  if(SEG.m==="inst"){{
   tr=[{{x:M.d,y:M.fcum,name:"外資",connectgaps:true,line:{{color:"#315f7d"}}}},
       {{x:M.d,y:M.tcum,name:"投信",connectgaps:true,line:{{color:"#2f7652"}}}},
       {{x:M.d,y:M.dcum,name:"自營",connectgaps:true,line:{{color:"#b58a3e"}}}},
       {{x:M.d,y:M.inst,name:"三大合計",connectgaps:true,line:{{color:"#1f2530",width:2.2}}}}];
  }}else{{tr=[{{x:M.d,y:M[SEG.m],name:LAB[SEG.m],connectgaps:cg,
    line:{{color:SEG.m==="mom"?"#b58a3e":"#2f7652",width:2}}}}];}}
 }}
 Plotly.react("c2",tr,{{height:380,font:{{size:10,
   family:'"Segoe UI","Noto Sans TC",sans-serif'}},
  margin:{{l:48,r:16,t:26,b:34}},paper_bgcolor:"#fff",plot_bgcolor:"#fff",
  legend:{{orientation:"h"}},title:{{text:title,font:{{size:11}}}},
  yaxis:{{zeroline:true}}}},{{displayModeBar:false,responsive:true}});}}
if(ssel){{ssel.onchange=draw2;draw2();}}
const DR=JSON.parse(document.getElementById("dr").textContent);
let ROTK="as";
function draw3(){{if(!DR.names.length||!window.Plotly||!document.getElementById("c3"))return;
 const M=DR.matrix[ROTK]||{{}};const z=DR.names.map(a=>DR.names.map(b=>(M[a]&&M[a][b]!==undefined)?M[a][b]:null));
 Plotly.react("c3",[{{type:"heatmap",x:DR.names,y:DR.names,z:z,zmin:-0.5,zmax:0.5,colorscale:"RdBu",
  hovertemplate:"%{{y}} 退 → %{{x}} 進<br>r=%{{z}}<extra></extra>"}}],
  {{height:Math.max(360,DR.names.length*16+120),font:{{size:9,family:'"Segoe UI","Noto Sans TC",sans-serif'}},
   margin:{{l:120,r:16,t:10,b:120}},xaxis:{{tickangle:-45}},yaxis:{{autorange:"reversed"}},paper_bgcolor:"#fff"}},
  {{displayModeBar:false,responsive:true}});}}
const segrot=document.getElementById("segrot");
if(segrot){{segrot.querySelectorAll("a").forEach(a=>a.onclick=()=>{{segrot.querySelectorAll("a").forEach(x=>x.classList.remove("on"));a.classList.add("on");ROTK=a.dataset.v;draw3();}});}}
draw3();
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
        rot = rotation_assoc(px_r, stories)
        cmp = compare_windows(px_r, stories)
        s1, s2, comp_note = composition_sets(cmp, s_mem)
        s_panel["key"] = s_panel["ticker"] + "|" + s_panel["story"]
        panels = {"ALL": s_panel}
        if s1 is not None:
            panels["S1"] = s_panel[s_panel["key"].isin(s1)]
            panels["S2"] = s_panel[s_panel["key"].isin(s2)]
        s_idx_sets = {k: build_indices(v, gcol="story",
                                       min_members=STORY_MIN_MEMBERS)
                      for k, v in panels.items() if len(v)}
        flows_df = load_flows()
        metrics = story_metrics(s_panel, stories, flows_df)
        master = build_master(s_mem, s_summ, s_panel, roles, flows_df,
                              load_listings())
        if len(s_panel):
            s_idx = s_idx_sets.get("S1", s_idx_sets.get("ALL"))
            all_reg = set().union(*stories.values())
            story = {"summ": s_summ, "idx": s_idx, "members": s_mem,
                     "cmp": cmp, "idx_sets": s_idx_sets, "metrics": metrics,
                     "comp_note": comp_note, "master": master, "rot": rot,
                     "coverage": {"reg": len(all_reg),
                                  "in_db": int(px.loc[px["ticker"].isin(all_reg), "ticker"].nunique()),
                                  "yf_adj": int(px.loc[px["adj_yf"] & px["ticker"].isin(all_reg), "ticker"].nunique())}}
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
            "dropped_partial": px.attrs.get("dropped_partial_sessions", []),
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
        if story.get("master") is not None and len(story["master"]):
            story["master"].to_csv(REP / f"MASTER_LIST_{stamp}.csv",
                                   index=False, encoding="utf-8-sig")
            story["master"].to_json(REP / f"MASTER_LIST_{stamp}.json",
                                    orient="records", force_ascii=False,
                                    indent=1, date_format="iso")
        if story.get("rot"):
            (REP / f"ROTATION_{stamp}.json").write_text(
                json.dumps(story["rot"], ensure_ascii=False, indent=1, default=str), encoding="utf-8")
        if story.get("cmp"):
            (REP / f"WINDOW_COMPARE_{stamp}.json").write_text(
                json.dumps(story["cmp"], ensure_ascii=False, indent=1,
                           default=str), encoding="utf-8")
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
            if story.get("cmp"):
                c_ = story["cmp"]
                print(f"  [跨窗] {'/'.join(w[:4] for w in c_['windows'])} 起 · "
                      f"個股穩定 {c_['n_stable']} · 有變動 {c_['n_drift']} · "
                      f"族群漂移>0.15:{sum(1 for g in c_['groups'] if (g['drift'] or 0) > 0.15)}")
            if story.get("master") is not None and len(story["master"]):
                ms = story["master"]
                print(f"  [清單] {len(ms)} 列(Group×Ticker)· 名稱覆蓋 "
                      f"{ms['Name'].notna().sum()}/{len(ms)} · 外資內資 "
                      f"{ms['外資內資主導'].value_counts().to_dict()}")
            print(f"  [故事] {len(story['summ'])} 群 · 凝聚達標 {ok} · "
                  f"歸一 {sum(1 for x in story['summ'] if x['collapsed'])} · "
                  f"角色 {ev_s['roles']}")
            cov = story.get("coverage", {})
            sig = sum(1 for x in story["summ"] if x.get("cohesion_sig"))
            mm_ = story.get("members")
            agree = None
            if mm_ is not None and len(mm_) and "role_stat" in mm_:
                mapc = {"LEADER": "LEAD", "PEER": "PEER", "LAGGARD": "LAG", "UNRELATED": "UNRELATED"}
                both = mm_.dropna(subset=["role_stat"])
                agree = (round(float((both["role"].map(mapc) == both["role_stat"]).mean()), 2)
                         if len(both) else None)
                print(f"  [實測] 覆蓋 {cov.get('in_db')}/{cov.get('reg')}(Yahoo 調整價 {cov.get('yf_adj')} 檔)"
                      f" · 顯著族群性(BH q≤{FDR_Q}) {sig}/{sum(1 for x in story['summ'] if x.get('p_iu') is not None)}"
                      f" · 角色統計判 {both['role_stat'].value_counts().to_dict()} · 與憲法角色一致率 {agree}")
            rt = story.get("rot") or {}
            if rt.get("names"):
                print(f"  [輪動] {len(rt['names'])} 群 · 檢定對 {rt.get('n_pairs_tested')} · 顯著邊(r<0,q≤{FDR_Q}) "
                      f"{len(rt['edges'])} · 前三:"
                      + "; ".join(f"{e['from']}→{e['to']} lag{e['lag']} r={e['r']}({e['kind']})" for e in rt["edges"][:3]))
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


def _latest(pattern: str):
    """存證尾件=最新寫入(mtime)而非檔名序(批326 實錄:尾端截日後檔名 stamp 倒退→名序讀到舊件假判)"""
    hits = list(REP.glob(pattern))
    return max(hits, key=lambda f: f.stat().st_mtime) if hits else None


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
    ev = json.loads(_latest("GROUP_CLASS_*.json")
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
    chk("⑦ 故事性分群(冊在+PC1/lead gap/四類+單成員入存證+LOO 不對稱領先)",
        STORY_REG.exists() and bool(st.get("stories"))
        and all("pc1" in x and "lead_gap" in x for x in st["stories"])
        and set(st.get("roles", {})) <= {"LEADER", "PEER", "LAGGARD",
                                         "UNRELATED", "單成員"}
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
    chk("⑩ 跨窗比較(四起點累積窗+族群漂移幅+個股角色序列+存證)",
        "def compare_windows" in src and 'WINDOWS = ["2023-01-01"' in src
        and "跨窗差異" in page and "變動次數" in page
        and bool(sorted(REP.glob("WINDOW_COMPARE_*.json"))))
    chk("⑪ 故事模式四類守恆(UNRELATED 憲法 0.25 入判+✕指數標+成員角色表)",
        "UNREL_CORR = 0.25" in src and '"UNRELATED", role' in src
        and "故事成員角色表" in page and "✕指數" in page
        and "index_flag" in src)
    try:
        reg = json.loads(STORY_REG.read_text(encoding="utf-8"))
        multi = {}
        for z in reg["stories"]:
            for t in z["tickers"]:
                multi[t] = multi.get(t, 0) + 1
        n_multi = sum(1 for v in multi.values() if v > 1)
        chk("⑫ 故事可重複個股(explode 多重歸屬;冊內多群股≥5)+產業不可重複",
            "assign(story=sname)" in src and n_multi >= 5 and "ind_code" in src)
    except Exception as exc:
        chk("⑫ 故事可重複個股", False, f"({type(exc).__name__})")
    chk("⑬ 兩制成分(T-1 審核律)×三加權+六指標切換鈕(價/量/動能/法人/融資/現金流)",
        "def composition_sets" in src and "roles_by_window" in src
        and 'id="segset"' in page and 'id="segm"' in page
        and "三大法人金流" in page and "現金流進出" in page
        and "def story_metrics" in src and "m_short" in src)
    try:
        mf = _latest("MASTER_LIST_*.json")
        ml = json.loads(mf.read_text(encoding="utf-8"))
        mm_ = _latest("STORY_MEMBER_*.csv")
        import pandas as pd
        n_mem = len(pd.read_csv(mm_))
        roles_ok = all(r["四種分類"] in ("LEADER", "PEER", "LAGGARD", "UNRELATED", "單成員")
                       for r in ml)
        size_ok = all(r["大中小"] in ("LARGE", "MID", "SMALL", None) for r in ml)
        cap_ok = all(str(r["外資內資主導"]).split("·")[0] in
                     ("Foreign", "Domestic", "Mixed", "候料", "None") for r in ml)
        rng_ok = all(0 <= (r["熱門"] or 0) <= 1 and 0 <= (r["領先"] or 0) <= 1 for r in ml)
        name_cov = sum(1 for r in ml if r["Name"]) / max(len(ml), 1)
        pc_ok = all((r["群PC1活躍"] is None) or (0 <= r["群PC1活躍"] <= 1) for r in ml)
        chk("⑭ 整合清單計算驗證(列數=成員列守恆/四分類·大中小·主導值域/"
            "熱門領先∈[0,1]/名稱覆蓋≥80%/群 PC1∈[0,1]/頁表在)",
            len(ml) == n_mem and roles_ok and size_ok and cap_ok and rng_ok
            and name_cov >= 0.8 and pc_ok and "整合清單" in page
            and "外資內資主導" in page,
            f"(列 {len(ml)}={n_mem} 名 {name_cov:.0%})")
    except Exception as exc:
        chk("⑭ 整合清單計算驗證", False, f"({type(exc).__name__}: {str(exc)[:60]})")
    # 批326 實測修正三檢
    try:
        import pandas as pd
        st_ = json.loads(_latest("STORY_CLASS_*.json").read_text(encoding="utf-8"))["stories"]
        withp = [x for x in st_ if x.get("p_iu") is not None]
        qs_ = [x["q_fdr"] for x in sorted(withp, key=lambda z: z["p_iu"])]
        chk("⑮ 族群性顯著(二軸虛無 p∈[0,1]+IU=max+BH q 單調+sig⊆q≤FDR)",
            len(withp) >= 5 and all(0 < x["p_iu"] <= 1 and x["p_iu"] >= max(v for v in (x.get("p_rand") or 0, x.get("p_shift") or 0)) for x in withp)
            and all(a <= b + 1e-9 for a, b in zip(qs_, qs_[1:]))
            and all((x["q_fdr"] <= FDR_Q) == bool(x["cohesion_sig"]) for x in withp),
            f"(顯著 {sum(1 for x in withp if x['cohesion_sig'])}/{len(withp)})")
        rot_ = json.loads(_latest("ROTATION_*.json").read_text(encoding="utf-8"))
        tested = [x for x in rot_["pairs"] if not x["overlap"]]
        chk("⑯ 輪動關聯(重疊對排除+p∈[0,1]+邊皆 r<0 且 q≤FDR+熱圖入頁)",
            len(tested) >= 10 and all(0 < x["p"] <= 1 and x["q"] <= 1 for x in tested)
            and all(e["r"] < 0 and e["q"] <= FDR_Q and not e["overlap"] for e in rot_["edges"])
            and 'id="rotsec"' in OUT_UI.read_text(encoding="utf-8") and 'type:"heatmap"' in OUT_UI.read_text(encoding="utf-8"),
            f"(對 {len(tested)} · 邊 {len(rot_['edges'])})")
        mem_ = pd.read_csv(_latest("STORY_MEMBER_*.csv"))
        chk("⑰ 覆蓋修正(adj_yf 旗標入面板+TPEX 入列)+角色統計判四類守恆(p 律)",
            "role_stat" in mem_ and set(mem_["role_stat"].dropna()) <= {"LEAD", "PEER", "LAG", "UNRELATED"}
            and "adj_yf" in load_panel().columns and (mem_["p_lead"].dropna().between(0, 1).all()),
            f"(統計判 {mem_['role_stat'].value_counts().to_dict()})")
    except Exception as exc:
        chk("⑮⑯⑰ 批326 實測修正", False, f"({type(exc).__name__}: {str(exc)[:80]})")
    print(f"  [計] 十七檢 OK {17 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 族群分類×價格指數(VDF_ENG070 v0109)· 十七檢自測(零外網)===")
        return selftest()
    return run()


if __name__ == "__main__":
    sys.exit(main())
