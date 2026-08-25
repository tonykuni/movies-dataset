#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GRP_ENG041_RotationMethodLab v0101 — 輪動方法論實測室(批155;via-methodlab)
====================================================================
方法論冊=docs/VIA_RotationMethodology_v*(glob 尾版);實測全節產數值
報告(全數值非分數;零固定參數=滾動分位制;多窗並列)。
  S1 主動 ETF↔投信買賣超結構確認(持股 Δ×trust_net;資料階梯誠實)
  S2 金流佔比指標(市場成交值−台積電−當沖為分母)+動態規模三分位
  S3 族群性證據:逆勢集體事件 vs 偽群 null+殘差相關抬升+領先性(核心複用)
  S4 TA 組合定義回測:超漲/超跌/背離(滾動分位帶)+大盤例外旗標
  S5 穩健性:震盪日含/排+walk-forward 對半
  S6 全球風險程度動態分級+資金傾斜可比性
v0101(批155)新增:
  S7 外資×新台幣×美元三角:亞幣籃共同因子(9 對等權)分解 TWD=
     美元共同面×β+TWD 特異面;特異升值日 vs 美元驅動日之外資
     買賣金額(股數×收盤 PROXY)條件均值+相關+前後 ±3 日領先落後
  S8 資金流四線分解:外資/投信(含主動 ETF ⊂,見 S1)/自營/融資槓桿
     (Δ融資餘額張×1000×價)逐日金額化+互相關+對大盤次日回測;
     內資全貌=PENDING 誠實(可觀察面=三法人+主動 ETF+資券)
評估窗=2026-01-02→庫內最新;產出 output_hub/methodlab_runs/(gitignored)
用法:via-methodlab run | --status | --selftest
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

import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
GRP = HERE.parent
VIA = GRP.parent.parent
MEGA = VIA / "functional modules" / "VDF" / "output_hub" / "mega"
DB_TW = MEGA / "vdf_tw_market.duckdb"
DB_GL = MEGA / "vdf_global_market.duckdb"
DB_ETF = (VIA / "functional modules" / "VDF" / "output_hub" / "active_tw_etf"
          / "active_tw_etf_holdings" / "ActiveTWETF.duckdb")
OUT_ROOT = GRP / "output_hub" / "methodlab_runs"
EVAL_START = "2026-01-02"
RNG_SEED = 20260825  # 偽群抽樣再現性(抽樣種子非市場門檻;紅線不涉)
N_NULL = 1000
WINDOWS = (20, 60, 120)  # 多窗並列(不擇一=非固定參數)


def _pkg_membership() -> Path | None:
    hits = sorted(GRP.glob("VIA_TW_Grouping_LatestCommand_v*"))
    if not hits:
        return None
    m = sorted(hits[-1].glob("VIA_ThreeList_CanonicalMembershipInput_v*.csv"))
    return m[-1] if m else None


def load_prices() -> pd.DataFrame:
    """價量面(名冊宇宙):adj_close/volume+成交值(真值層優先,缺=PROXY 標記)"""
    import csv
    import duckdb
    memb = _pkg_membership()
    rows = list(csv.DictReader(open(memb, encoding="utf-8-sig")))
    yf2code = {r["YFTicker"]: r["Ticker"] for r in rows if r.get("YFTicker")}
    con = duckdb.connect(str(DB_TW), read_only=True)
    ph = ",".join("?" * len(yf2code))
    px = con.execute(
        f"SELECT p.date, p.ticker, p.adj_close, p.close, p.volume, t.trade_value "
        f"FROM tw_daily_prices p LEFT JOIN tw_trading_daily t "
        f"ON t.date=p.date AND p.ticker = t.code || "
        f"(CASE WHEN t.market='TWSE' THEN '.TW' ELSE '.TWO' END) "
        f"WHERE p.ticker IN ({ph}) AND p.adj_close IS NOT NULL "
        f"ORDER BY p.ticker, p.date", list(yf2code)).df()
    con.close()
    px["code"] = px["ticker"].map(lambda t: yf2code.get(t, t.split(".")[0]))
    px["group"] = px["code"].map({r["Ticker"]: r["Group"] for r in rows})
    px["val_source"] = np.where(px["trade_value"].notna(), "TRUE_VALUE", "PROXY")
    px["val"] = px["trade_value"].fillna(px["close"] * px["volume"])
    return px


def load_market() -> pd.DataFrame:
    import duckdb
    con = duckdb.connect(str(DB_GL), read_only=True)
    m = con.execute("SELECT date, adj_close FROM global_daily WHERE ticker='^TWII' "
                    "AND adj_close IS NOT NULL ORDER BY date").df()
    con.close()
    m["mkt_ret"] = m["adj_close"].pct_change()
    return m.rename(columns={"adj_close": "twii"})


# ---------------------------------------------------------------- S1
def s1_structure() -> dict:
    import duckdb
    out = {"section": "S1 主動 ETF↔投信買賣超結構確認"}
    if not DB_ETF.exists():
        out["state"] = "PENDING(持股庫缺)"
        return out
    con = duckdb.connect(str(DB_ETF), read_only=True)
    h = con.execute("SELECT portfolio_date, etf_ticker, holding_ticker, shares "
                    "FROM holdings_daily").df()
    con.close()
    dates = sorted(h["portfolio_date"].unique())
    out["snapshot_dates"] = [str(d) for d in dates]
    # 跨日 Δ=兩日皆在冊之 ETF(首快照無前值=誠實不視為買進)
    if len(dates) < 2:
        out["state"] = "PENDING(單快照;每日累積中)"
        return out
    a, b = dates[-2], dates[-1]
    ea = set(h.loc[h["portfolio_date"].eq(a), "etf_ticker"])
    eb = set(h.loc[h["portfolio_date"].eq(b), "etf_ticker"])
    both = sorted(ea & eb)
    out["etf_with_both_snapshots"] = len(both)
    if not both:
        out["state"] = "PENDING(無 ETF 具連續兩快照;累積中)"
        return out
    hh = h.loc[h["etf_ticker"].isin(both)]
    piv = hh.pivot_table(index=["etf_ticker", "holding_ticker"],
                         columns="portfolio_date", values="shares", aggfunc="last")
    delta = (piv[b].fillna(0) - piv[a].fillna(0)).groupby("holding_ticker").sum()
    delta = delta[delta.ne(0)]
    import duckdb as dk
    con = dk.connect(str(DB_TW), read_only=True)
    tn = con.execute("SELECT code, SUM(trust_net) v FROM tw_chip_inst "
                     "WHERE date=? GROUP BY code", [str(b)]).df().set_index("code")["v"]
    con.close()
    j = pd.DataFrame({"etf_delta": delta}).join(tn.rename("trust_net"), how="inner").dropna()
    out["joined_stocks"] = int(len(j))
    if len(j):
        same_sign = (np.sign(j["etf_delta"]) == np.sign(j["trust_net"]))
        contained = (j["etf_delta"].abs() <= j["trust_net"].abs()) & same_sign
        out["sign_agreement_rate"] = round(float(same_sign.mean()), 4)
        out["magnitude_containment_rate"] = round(float(contained.mean()), 4)
        out["cross_section_corr"] = round(float(j["etf_delta"].corr(j["trust_net"])), 4)
        out["state"] = "INITIAL_EVIDENCE(單 Δ 日;N 隨日累積)"
    else:
        out["state"] = "PENDING(join 空)"
    return out


# ---------------------------------------------------------------- S2
def s2_flow_share(px: pd.DataFrame) -> dict:
    out = {"section": "S2 金流佔比指標+動態規模分級",
           "formula": "share=(val_i−dt_i)/(Σval−val_2330−DT_mkt)",
           "data_ladder": {}}
    src = px.groupby("val_source")["date"].count().to_dict()
    out["data_ladder"]["val"] = {k: int(v) for k, v in src.items()}
    out["data_ladder"]["dt_i"] = "PENDING(TWSE 逐股當沖 WAF)=0 代入標記"
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    try:
        dtm = con.execute("SELECT date, SUM(dt_buy_value+dt_sell_value)/2 v "
                          "FROM tw_daytrade_market GROUP BY date").df().set_index("date")["v"]
    except Exception:
        dtm = pd.Series(dtype=float)
    con.close()
    out["data_ladder"]["DT_mkt"] = f"{len(dtm)} 日可得(缺日=0 標記)"
    d = px[["date", "code", "val"]].copy()
    tot = d.groupby("date")["val"].sum().rename("tot")
    tsmc = d.loc[d["code"].eq("2330")].set_index("date")["val"].rename("tsmc")
    d = d.join(tot, on="date").join(tsmc, on="date")
    d["dtm"] = d["date"].map(dtm).fillna(0.0)
    d["share"] = d["val"] / (d["tot"] - d["tsmc"].fillna(0) - d["dtm"])
    # 60d 滾動中位 share → 逐日橫斷面動態三分位
    d = d.sort_values(["code", "date"])
    d["share_roll"] = d.groupby("code")["share"].transform(
        lambda s: s.rolling(60, min_periods=20).median())
    def _tier(g):
        q1, q2 = g["share_roll"].quantile([1 / 3, 2 / 3])
        return pd.Series(np.where(g["code"].eq("2330"), "LARGE",
                         np.where(g["share_roll"] >= q2, "LARGE",
                         np.where(g["share_roll"] >= q1, "MID", "SMALL"))), index=g.index)
    d["tier"] = d.groupby("date", group_keys=False).apply(_tier)
    last = d.loc[d["date"].ge(EVAL_START)].copy()
    # 有效性數值:延續率/單調性
    lp = last.pivot_table(index="date", columns="code", values="tier", aggfunc="last")
    stab = float((lp == lp.shift()).mean().mean())
    vol_rank = last.groupby("code")["val"].median().rank()
    tier_ord = last.groupby("code")["tier"].agg(
        lambda s: {"SMALL": 0, "MID": 1, "LARGE": 2}[s.mode().iat[0]])
    mono = float(vol_rank.corr(tier_ord, method="spearman"))
    out["eval_window"] = {"start": EVAL_START,
                         "days": int(last["date"].nunique()),
                         "stocks": int(last["code"].nunique())}
    out["classification_persistence_rate"] = round(stab, 4)
    out["monotonic_spearman_vs_value_rank"] = round(mono, 4)
    out["tier_counts_latest"] = last.loc[last["date"].eq(last["date"].max()),
                                         "tier"].value_counts().to_dict()
    out["tsmc_rule"] = "2330 逕判 LARGE 且自分母剔除"
    return out


# ---------------------------------------------------------------- S3
def s3_group_evidence(px: pd.DataFrame, mkt: pd.DataFrame) -> dict:
    out = {"section": "S3 族群性證據(逆勢集體事件+殘差相關抬升 vs 偽群 null)"}
    rng = np.random.default_rng(RNG_SEED)
    ret = px.pivot_table(index="date", columns="code", values="adj_close",
                         aggfunc="last").pct_change()
    ret = ret.loc[ret.index >= EVAL_START]
    m = mkt.set_index("date")["mkt_ret"].reindex(ret.index)
    groups = px.dropna(subset=["group"]).groupby("group")["code"].agg(
        lambda s: sorted(set(s)))
    down = m < 0
    # 市場殘差(全窗迴歸=評估窗內;逐股 beta)
    resid = pd.DataFrame(index=ret.index, columns=ret.columns, dtype=float)
    mv = m.fillna(0).to_numpy()
    denom = float(np.dot(mv, mv)) or 1.0
    for c in ret.columns:
        y = ret[c].fillna(0).to_numpy()
        beta = float(np.dot(mv, y)) / denom
        resid[c] = ret[c] - beta * m
    universe = [c for c in ret.columns if ret[c].notna().sum() > 60]
    rows = []
    for gname, members in groups.items():
        mem = [c for c in members if c in universe]
        if len(mem) < 3:
            continue
        gret = ret[mem].mean(axis=1)
        counter = int(((down) & (gret > 0)).sum())
        all_up = int((down & (ret[mem] > 0).all(axis=1) & ret[mem].notna().all(axis=1)).sum())
        med_corr = float(np.nanmedian(resid[mem].corr().values[
            np.triu_indices(len(mem), 1)]))
        null_counter, null_corr = [], []
        for _ in range(N_NULL):
            pseudo = rng.choice(universe, size=len(mem), replace=False)
            pret = ret[list(pseudo)].mean(axis=1)
            null_counter.append(int((down & (pret > 0)).sum()))
            if _ < 200:  # 相關 null 取 200 樣(計算量控制,樣本數冊上明示)
                null_corr.append(float(np.nanmedian(
                    resid[list(pseudo)].corr().values[np.triu_indices(len(mem), 1)])))
        nc = np.array(null_counter)
        p_counter = float((nc >= counter).mean())
        corr_lift = med_corr - float(np.mean(null_corr))
        p_corr = float((np.array(null_corr) >= med_corr).mean())
        rows.append({"group": gname, "members": len(mem),
                     "counter_days": counter, "all_up_days": all_up,
                     "null_mean_counter": round(float(nc.mean()), 2),
                     "p_counter": round(p_counter, 4),
                     "resid_median_corr": round(med_corr, 4),
                     "corr_lift_vs_null": round(corr_lift, 4),
                     "p_corr": round(p_corr, 4)})
    df = pd.DataFrame(rows).sort_values("p_corr")
    out["market_down_days_in_eval"] = int(down.sum())
    out["groups_tested"] = len(df)
    out["significant_corr_p_lt_05"] = int((df["p_corr"] < 0.05).sum())
    out["significant_counter_p_lt_05"] = int((df["p_counter"] < 0.05).sum())
    out["null_samples"] = {"counter": N_NULL, "corr": 200}
    out["per_group"] = df.to_dict("records")
    # 領先性=核心複用(最新 TW 實跑 role_snapshots)
    runs = sorted((GRP / "output_hub" / "rotation_runs").glob("ROTATION_TW_*"))
    if runs:
        rs = runs[-1] / "csv" / "role_snapshots.csv"
        if rs.exists():
            r = pd.read_csv(rs)
            lead = r.loc[r.get("PermutationPValue", pd.Series(dtype=float)) < 0.05]
            out["leadlag_from_core"] = {
                "run": runs[-1].name, "role_snapshots": int(len(r)),
                "sig_lead_members_p_lt_05": int(len(lead))}
    return out


# ---------------------------------------------------------------- S4/S5
def s4_ta_backtest(px: pd.DataFrame, mkt: pd.DataFrame) -> dict:
    out = {"section": "S4 TA 組合定義回測(+S5 穩健性)", "windows": {}}
    ret = px.pivot_table(index="date", columns="code", values="adj_close",
                         aggfunc="last").pct_change()
    m = mkt.set_index("date")["mkt_ret"].reindex(ret.index).fillna(0)
    shock = m.abs() > m.abs().rolling(252, min_periods=60).quantile(0.95)
    mv = m.to_numpy()
    denom = float(np.dot(mv, mv)) or 1.0
    resid = {}
    for c in ret.columns:
        y = ret[c].fillna(0).to_numpy()
        resid[c] = ret[c] - (float(np.dot(mv, y)) / denom) * m
    resid = pd.DataFrame(resid)
    px_close = px.pivot_table(index="date", columns="code", values="adj_close",
                              aggfunc="last")
    fwd5 = px_close.shift(-5) / px_close - 1
    for W in (20, 60):
        cum = resid.rolling(W).sum()
        hi = cum.rolling(252, min_periods=120).quantile(0.95)
        lo = cum.rolling(252, min_periods=120).quantile(0.05)
        over = cum > hi     # 超漲(滾動 q95)
        under = cum < lo    # 超跌(滾動 q05)
        mom = ret.rolling(W).sum()
        hi60 = px_close.rolling(60).max()
        div_bear = px_close.ge(hi60) & (mom < mom.rolling(60).median())
        # 大盤例外旗標:^TWII 同態
        mcum = m.rolling(W).sum()
        m_over = mcum > mcum.rolling(252, min_periods=120).quantile(0.95)
        m_under = mcum < mcum.rolling(252, min_periods=120).quantile(0.05)
        def _vals(frame, signal):
            """訊號選值展平+去 NaN(修正①:stack 留 NaN 使勝率假值)"""
            return frame.where(signal).stack().dropna()

        res = {}
        for name, sig, mflag in (("超漲", over, m_over), ("超跌", under, m_under),
                                 ("背離空", div_bear, None)):
            sig = (sig.loc[sig.index >= EVAL_START]).fillna(False)
            f = fwd5.loc[sig.index]
            sv = _vals(f, sig)
            base = f.stack().dropna()
            stats = {"N": int(sig.sum().sum()),
                     "fwd5_mean": round(float(sv.mean()), 5) if len(sv) else None,
                     "fwd5_hit_rate": round(float((sv > 0).mean()), 4) if len(sv) else None,
                     "baseline_fwd5_mean": round(float(base.mean()), 5),
                     "baseline_hit_rate": round(float((base > 0).mean()), 4)}
            if mflag is not None:
                mf = mflag.reindex(sig.index).fillna(False)
                own = sig.mul(~mf, axis=0)  # 修正②:列軸廣播(大盤同態日剔除=個股特異態)
                stats["market_driven_days_flagged"] = int(sig.sum().sum() - own.sum().sum())
                so = _vals(f, own)
                stats["stock_specific_N"] = int(own.sum().sum())
                stats["stock_specific_fwd5_mean"] = round(float(so.mean()), 5) if len(so) else None
                stats["stock_specific_hit_rate"] = round(float((so > 0).mean()), 4) if len(so) else None
            # S5 震盪日排除重算
            calm = sig.mul(~shock.reindex(sig.index).fillna(False), axis=0)
            sc = _vals(f, calm)
            stats["ex_shock_N"] = int(calm.sum().sum())
            stats["ex_shock_fwd5_mean"] = round(float(sc.mean()), 5) if len(sc) else None
            # walk-forward 對半
            half = sorted(sig.index)[len(sig.index) // 2]
            for tag, mask_ in (("wf1", sig.index < half), ("wf2", sig.index >= half)):
                sw = _vals(f.loc[mask_], sig.loc[mask_])
                stats[f"{tag}_fwd5_mean"] = round(float(sw.mean()), 5) if len(sw) else None
            res[name] = stats
        out["windows"][f"W{W}"] = res
    out["shock_days_in_eval"] = int(shock.loc[shock.index >= EVAL_START].sum())
    return out


# ---------------------------------------------------------------- S6
def s6_global_risk() -> dict:
    import duckdb
    out = {"section": "S6 全球風險程度動態分級+資金傾斜可比性"}
    memb = sorted(GRP.glob("global/VIA_GlobalFlowRotation_Membership_v*.csv"))
    if not memb:
        out["state"] = "PENDING(全球冊缺)"
        return out
    import csv
    rows = list(csv.DictReader(open(memb[-1], encoding="utf-8-sig")))
    tickers = sorted({r["YFTicker"] for r in rows})
    grp = {r["YFTicker"]: r["Group"] for r in rows}
    con = duckdb.connect(str(DB_GL), read_only=True)
    ph = ",".join("?" * len(tickers))
    d = con.execute(f"SELECT date, ticker, adj_close, volume FROM global_daily "
                    f"WHERE ticker IN ({ph}) AND adj_close IS NOT NULL", tickers).df()
    con.close()
    p = d.pivot_table(index="date", columns="ticker", values="adj_close", aggfunc="last")
    r = p.pct_change()
    vol = r.rolling(60, min_periods=30).std() * np.sqrt(252)
    dd = p / p.cummax() - 1
    last = vol.index.max()
    # 各標的取最後有效值(修正:共同末日因美亞時區日差使美系標的 NaN)
    v_last, dd_last = vol.ffill().iloc[-1], dd.ffill().iloc[-1]
    q1, q2 = v_last.quantile([1 / 3, 2 / 3])
    tier = pd.Series(np.where(v_last >= q2, "HIGH", np.where(v_last >= q1, "MID", "LOW")),
                     index=v_last.index)
    val = (d.pivot_table(index="date", columns="ticker", values="adj_close", aggfunc="last")
           * d.pivot_table(index="date", columns="ticker", values="volume", aggfunc="last"))
    share = val.div(val.sum(axis=1), axis=0)
    tilt = (share.rolling(20, min_periods=10).mean().rank(axis=1)
            - share.rolling(120, min_periods=60).mean().rank(axis=1)).ffill()
    out["as_of"] = str(last)
    t_last = tilt.iloc[-1] if len(tilt) else pd.Series(dtype=float)
    out["risk_tiers"] = [{"ticker": t, "group": grp.get(t), "vol60_ann": round(float(v_last[t]), 4),
                          "drawdown": (round(float(dd_last[t]), 4)
                                       if pd.notna(dd_last.get(t)) else None),
                          "tier": tier[t],
                          "flow_tilt_rank20_120": (round(float(t_last[t]), 1)
                                                   if pd.notna(t_last.get(t)) else None)}
                         for t in sorted(tickers, key=lambda x: -v_last.get(x, 0))
                         if pd.notna(v_last.get(t))]
    out["note"] = "val=TURNOVER_PROXY(close×volume);傾斜=20d vs 120d 佔比排名差(動態零門檻)"
    return out


# ---------------------------------------------------------------- S7
USD_BASKET = ("JPY=X", "KRW=X", "SGD=X", "CNY=X", "THB=X",
              "MYR=X", "IDR=X", "INR=X", "PHP=X")


def _fx_frame() -> pd.DataFrame:
    import duckdb
    con = duckdb.connect(str(DB_GL), read_only=True)
    ph = ",".join("?" * (len(USD_BASKET) + 1))
    d = con.execute(f"SELECT date, ticker, adj_close FROM global_daily "
                    f"WHERE ticker IN ({ph}) AND adj_close IS NOT NULL",
                    ["TWD=X", *USD_BASKET]).df()
    con.close()
    p = d.pivot_table(index="date", columns="ticker", values="adj_close", aggfunc="last")
    return np.log(p).diff()


def _foreign_amount() -> pd.Series:
    """外資買賣超金額化(股數×收盤=PROXY 明示;單位:億元)"""
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    d = con.execute("""
        SELECT c.date, SUM(c.foreign_net * p.close) / 1e8 amt
        FROM tw_chip_inst c
        JOIN tw_daily_prices p
          ON p.date = c.date
         AND p.ticker = c.code || (CASE WHEN c.market='TWSE' THEN '.TW' ELSE '.TWO' END)
        WHERE c.foreign_net IS NOT NULL
        GROUP BY c.date ORDER BY c.date""").df()
    con.close()
    return d.set_index("date")["amt"]


def s7_fx_triangle() -> dict:
    out = {"section": "S7 外資×新台幣×美元三角分解",
           "amount_unit": "億元(股數×收盤 PROXY 明示)",
           "usd_common": f"亞幣籃 {len(USD_BASKET)} 對等權 Δlog 均值"}
    fx = _fx_frame()
    fx = fx.loc[fx.index >= EVAL_START]
    twd = fx["TWD=X"].dropna()
    usd = fx[list(USD_BASKET)].mean(axis=1).reindex(twd.index)
    beta = float(np.dot(usd.fillna(0), twd.fillna(0))
                 / (np.dot(usd.fillna(0), usd.fillna(0)) or 1.0))
    spec = twd - beta * usd
    amt = _foreign_amount().reindex(twd.index)
    out["days"] = int(len(twd))
    out["beta_twd_on_usd_common"] = round(beta, 4)
    out["corr"] = {
        "twd_ret_vs_foreign_amt": round(float(twd.corr(amt)), 4),
        "twd_specific_vs_foreign_amt": round(float(spec.corr(amt)), 4),
        "usd_common_vs_foreign_amt": round(float(usd.corr(amt)), 4)}
    # 條件均值:TWD=X 下跌=台幣升值。特異升值日=spec<滾動 q10;
    # 美元驅動升值日=twd<滾動 q10 但 spec 非低分位(=升值主因在美元面)
    q10s = spec.rolling(120, min_periods=40).quantile(0.10)
    q10t = twd.rolling(120, min_periods=40).quantile(0.10)
    d_spec = spec < q10s
    d_usd = (twd < q10t) & (~d_spec)
    out["conditional_foreign_amt_mean"] = {
        "twd_specific_appreciation_days": {"N": int(d_spec.sum()),
                                           "mean_amt": round(float(amt[d_spec].mean()), 1)},
        "usd_driven_appreciation_days": {"N": int(d_usd.sum()),
                                         "mean_amt": round(float(amt[d_usd].mean()), 1)},
        "all_days_mean_amt": round(float(amt.mean()), 1)}
    out["leadlag_corr_spec_vs_amt"] = {
        f"lag{k:+d}": round(float(spec.corr(amt.shift(-k))), 4) for k in range(-3, 4)}
    out["reading_rule"] = ("TWD 升值(=TWD=X 跌)之外資買超解讀,須先剔除美元共同面;"
                           "特異升值日條件均值>美元驅動日=真資金流入訊號成立")
    return out


# ---------------------------------------------------------------- S8
def s8_flow_decomp(mkt: pd.DataFrame) -> dict:
    out = {"section": "S8 資金流四線分解(外資/投信/自營/融資槓桿)",
           "amount_unit": "億元(股數/張×價 PROXY 明示)",
           "coverage_note": ("可觀察面=三法人+主動 ETF(⊂投信,S1)+資券;"
                             "內資現貨全貌=PENDING(候集保/期權籌碼源)")}
    import duckdb
    con = duckdb.connect(str(DB_TW), read_only=True)
    inst = con.execute("""
        SELECT c.date,
               SUM(c.foreign_net * p.close)/1e8 foreign_amt,
               SUM(c.trust_net   * p.close)/1e8 trust_amt,
               SUM(c.dealer_net  * p.close)/1e8 dealer_amt
        FROM tw_chip_inst c
        JOIN tw_daily_prices p ON p.date=c.date
         AND p.ticker = c.code || (CASE WHEN c.market='TWSE' THEN '.TW' ELSE '.TWO' END)
        GROUP BY c.date ORDER BY c.date""").df().set_index("date")
    marg = con.execute("""
        SELECT m.date, SUM((m.margin_bal - m.margin_bal_prev) * 1000 * p.close)/1e8 margin_amt,
               SUM((m.short_bal - m.short_bal_prev) * 1000 * p.close)/1e8 short_amt
        FROM tw_chip_margin m
        JOIN tw_daily_prices p ON p.date=m.date
         AND p.ticker = m.code || (CASE WHEN m.market='TWSE' THEN '.TW' ELSE '.TWO' END)
        WHERE m.margin_bal IS NOT NULL AND m.margin_bal_prev IS NOT NULL
        GROUP BY m.date ORDER BY m.date""").df().set_index("date")
    con.close()
    f = inst.join(marg, how="inner")
    f = f.loc[f.index >= EVAL_START]
    m = mkt.set_index("date")["mkt_ret"].reindex(f.index)
    nxt = m.shift(-1)
    out["days"] = int(len(f))
    out["daily_mean_amt"] = {c: round(float(f[c].mean()), 1) for c in f.columns}
    out["cross_corr"] = {f"{a}×{b}": round(float(f[a].corr(f[b])), 4)
                         for i, a in enumerate(f.columns) for b in f.columns[i + 1:]}
    out["vs_market"] = {}
    for c in f.columns:
        hi = f[c] > f[c].rolling(120, min_periods=40).quantile(0.8)
        out["vs_market"][c] = {
            "corr_same_day_mkt": round(float(f[c].corr(m)), 4),
            "corr_next_day_mkt": round(float(f[c].corr(nxt)), 4),
            "top_quantile_days_next_ret": (round(float(nxt[hi].mean()), 5)
                                           if hi.sum() else None),
            "top_quantile_N": int(hi.sum()),
            "base_next_ret": round(float(nxt.mean()), 5)}
    return out


# ---------------------------------------------------------------- run
def run() -> int:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = OUT_ROOT / f"METHODLAB_{ts}"
    out_dir.mkdir(parents=True, exist_ok=True)
    print("[載入] 價量+市場面…", flush=True)
    px = load_prices()
    mkt = load_market()
    report = {"methodology": sorted(p.name for p in
                                    GRP.glob("docs/VIA_RotationMethodology_v*.md"))[-1],
              "eval_start": EVAL_START, "generated": ts,
              "red_lines": "零固定參數(滾動分位)·全數值非分數·多窗並列·誠實資料階梯"}
    for name, fn in (("S1", s1_structure), ("S2", lambda: s2_flow_share(px)),
                     ("S3", lambda: s3_group_evidence(px, mkt)),
                     ("S4S5", lambda: s4_ta_backtest(px, mkt)),
                     ("S6", s6_global_risk), ("S7", s7_fx_triangle),
                     ("S8", lambda: s8_flow_decomp(mkt))):
        print(f"[{name}] …", flush=True)
        try:
            report[name] = fn()
        except Exception as e:
            report[name] = {"state": f"FAIL({type(e).__name__}: {str(e)[:100]})"}
    (out_dir / "methodlab_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    for k in ("S1", "S2", "S3", "S4S5", "S6", "S7", "S8"):
        sec = report[k]
        head = {kk: vv for kk, vv in sec.items()
                if not isinstance(vv, (list, dict)) or kk == "windows"}
        print(f"  [{k}] {json.dumps(head, ensure_ascii=False, default=str)[:400]}")
    print(f"[OK] 報告 → {out_dir / 'methodlab_report.json'}")
    return 0


def status() -> int:
    runs = sorted(OUT_ROOT.glob("METHODLAB_*")) if OUT_ROOT.exists() else []
    print(f"實測 {len(runs)} 次{' · 最新 ' + runs[-1].name if runs else ''}")
    return 0


def selftest() -> int:
    fails = []

    def chk(name, cond, note=""):
        print(f"  [{'OK' if cond else 'FAIL'}] {name} {note}")
        if not cond:
            fails.append(name)

    meth = sorted(GRP.glob("docs/VIA_RotationMethodology_v*.md"))
    chk("① 方法論冊在位(glob 尾版)", bool(meth),
        f"({meth[-1].name if meth else '缺'})")
    src_m = meth[-1].read_text(encoding="utf-8") if meth else ""
    chk("② 冊載紅線(零固定參數/全數值/誠實階梯/walk-forward)",
        all(k in src_m for k in ("零固定參數", "全數值", "資料階梯", "walk-forward")))
    chk("③ 三庫在位(tw/global/ETF 持股)",
        DB_TW.exists() and DB_GL.exists() and DB_ETF.exists())
    r = s1_structure()
    chk("④ S1 結構確認可跑(誠實階梯態)",
        "state" in r and ("EVIDENCE" in r["state"] or "PENDING" in r["state"]),
        f"({r.get('state', '')[:40]})")
    # 合成微型宇宙:S3 核心數學(偽群 null 分離度)
    rng = np.random.default_rng(7)
    n = 120
    mret = rng.normal(0, 0.01, n)
    common = rng.normal(0, 0.012, n)
    data = {}
    for i in range(6):
        data[f"G{i}"] = 0.9 * mret + common + rng.normal(0, 0.006, n)  # 真族群
    for i in range(24):
        data[f"N{i}"] = 0.9 * mret + rng.normal(0, 0.013, n)           # 散兵
    dates = pd.date_range("2026-01-02", periods=n, freq="B").strftime("%Y-%m-%d")
    ret = pd.DataFrame(data, index=dates)
    px = ret.add(1).cumprod().mul(100)
    long = px.reset_index().melt(id_vars="index", var_name="code",
                                 value_name="adj_close").rename(columns={"index": "date"})
    long["group"] = np.where(long["code"].str.startswith("G"), "真群", None)
    long["volume"] = 1e6
    long["close"] = long["adj_close"]
    long["val"] = long["close"] * long["volume"]
    long["val_source"] = "PROXY"
    mkt = pd.DataFrame({"date": dates, "twii": 100 * np.cumprod(1 + mret)})
    mkt["mkt_ret"] = pd.Series(mret, index=mkt.index)
    r3 = s3_group_evidence(long, mkt)
    g = next((x for x in r3["per_group"] if x["group"] == "真群"), None)
    chk("⑤ S3 合成真群偵測(殘差相關抬升 p<0.05)",
        g is not None and g["p_corr"] < 0.05 and g["corr_lift_vs_null"] > 0,
        f"(lift={g['corr_lift_vs_null'] if g else '?'} p={g['p_corr'] if g else '?'})")
    chk("⑥ S3 null 為數值報告(非分數)",
        g is not None and "null_mean_counter" in g and "p_counter" in g)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 滾動分位紀律(rolling quantile;禁固定門檻)",
        src.count("rolling") >= 10 and "quantile(0.95)" in src)
    chk("⑧ 誠實階梯宣告(PROXY/PENDING/TRUE_VALUE 三層)",
        all(k in src for k in ("TRUE_VALUE", "PROXY", "PENDING")))

    # ⑨ S7 合成分解:TWD=β×美元共同+特異;β 回收+條件均值方向正確
    rng2 = np.random.default_rng(11)
    n2 = 300
    usd = rng2.normal(0, 0.004, n2)
    spec_true = rng2.normal(0, 0.003, n2)
    twd = 0.8 * usd + spec_true
    beta_hat = float(np.dot(usd, twd) / np.dot(usd, usd))
    spec_hat = twd - beta_hat * usd
    chk("⑨ S7 分解數學(β 回收±0.1 內+特異面與真值相關>0.95)",
        abs(beta_hat - 0.8) < 0.1
        and float(np.corrcoef(spec_hat, spec_true)[0, 1]) > 0.95,
        f"(β̂={beta_hat:.3f})")
    chk("⑩ S7/S8 誠實宣告(金額 PROXY 明示+內資全貌 PENDING+美元剔除規則)",
        all(k in src for k in ("股數×收盤 PROXY", "內資現貨全貌", "剔除美元共同面")))
    print(f"  [計] 十檢 OK {10 - len(fails)} · FAIL {len(fails)}")
    return 1 if fails else 0


def main() -> int:
    args = sys.argv[1:]
    if "--selftest" in args:
        print("=== 輪動方法論實測室(GRP_ENG041 v0101)· 十檢自測 ===")
        return selftest()
    if "--status" in args:
        return status()
    if "run" in args:
        return run()
    print(__doc__.split("用法:")[1])
    return 0


if __name__ == "__main__":
    sys.exit(main())
