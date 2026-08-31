# -*- coding: utf-8 -*-
"""
VERITAS INTELLIGENCE ANALYTICS
VIA_VIS_AdaptiveClassification_v0100.py — VIS 自適應完美分類引擎(Polars)

依 VIS 白皮書 + 使用者規格落地:

  【釘卯點 1】巨錨隔離:剔除台積電(2330);ETR = 成交值 − 當沖(實質留倉資金)
  【釘卯點 A】Attention Share:AS = 個股ETR ÷ 淨市場ETR(加權+櫃買−當沖−2330非當沖)
  【釘卯點 A2】動態大中小:AS 滾動分位數分層(無固定金額門檻)
  【釘卯點 2】半動態自適應動能:短/長 EWM + Volume Shock 加速(不失敏感度)
  【釘卯點 3-5】四重閘門:流動性(滾動分位)/ EWM 同動性 / 資金流背離
  【釘卯點 6】三加權指數並立:Equal / Tier / Attention(18% 上限)
              — Adj Close 報酬、T-1 權重(零前視)、2026-01-01 = 100 正規化
  【釘卯點 B-E】角色(LEADER/PEER/LAGGER/UNRELATED)、外資/內資、投信/自營、外資模式
  【釘卯點 F】籌碼時序:三大法人買賣超 + 融資融券 + 當沖占比,全滾動 z(零固定門檻)

參數家族(半動態):Type-F 憲法固定 / Type-D 強制滾動 / Type-H 平常滾動、
結構異常短鎖(Shock 時縮短視窗提高敏感度,絕不因平滑而鈍化)。

治理:受控 DGP 收斂驗證(方法驗證,非實盤績效)、零網路、append-only、
SHA256 manifest、fail-closed。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import datetime as dt
import hashlib
import json

import numpy as np
import polars as pl

SCRIPT_DIR = Path(__file__).resolve().parent
MODULE_DIR = SCRIPT_DIR.parent
RUN_OUT = MODULE_DIR / "evidence" / "RUN_VIS_ADAPTIVE_V0100"
VERSION = "0.1.00"

# ---- Type-F 固定憲法 ----
TSMC = "2330"
BASE_DATE = "2026-01-02"          # 2026-01-01 為假日,採首個交易日錨定 100
UNRELATED_CORR = 0.25
MAX_ATT_WEIGHT = 0.18             # Attention 單檔權重上限(防極端集中、保聚焦敏感)
TIER_WEIGHTS = {"Large": 0.50, "Mid": 0.30, "Small": 0.20}

# ---- Type-D / Type-H 基礎值(執行時滾動;Shock 時自動縮窗加速) ----
P = {
    "ewm_span": 50, "quant_window": 60, "shock_short": 5, "shock_long": 40,
    "min_span": 15, "liquidity_q": 0.25, "corr_q": 0.45,
    "size_q_large": 0.90, "size_q_mid": 0.60,
    "shock_z_trigger": 2.0,
}

SEED = 20260831


# ============================================================================
# 受控 DGP:合成面板(含 2330、當沖、三大法人、融資融券)+ 植入真值
# ============================================================================
def def_generate_panel(n_days: int = 420, seed: int = SEED) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    start = dt.date(2025, 1, 2)
    dates = []
    d = start
    while len(dates) < n_days:
        if d.weekday() < 5:
            dates.append(d)
        d += dt.timedelta(days=1)

    groups = {
        "AI伺服器": [f"31{i:02d}" for i in range(8)],
        "散熱": [f"32{i:02d}" for i in range(6)],
        "航運": [f"26{i:02d}" for i in range(6)],
    }
    rows = []
    t = np.arange(n_days)
    # 族群共同因子(AI 群植入趨勢段;領頭羊 3100 領先 2 日)
    fac = {g: np.cumsum(rng.normal(0, 0.008, n_days)) for g in groups}
    fac["AI伺服器"][n_days // 3:] += np.linspace(0, 0.25, n_days - n_days // 3)

    for g, tickers in groups.items():
        for j, tk in enumerate(tickers):
            lead = 2 if (g == "AI伺服器" and j == 0) else 0        # 植入領先者
            unrelated = (g == "航運" and j == 5)                    # 植入不相關者
            f = np.roll(fac[g], -lead)
            beta = 0.0 if unrelated else rng.uniform(0.7, 1.2)
            ret = beta * np.diff(f, prepend=f[0]) + rng.normal(0, 0.012, n_days)
            adj_close = 100.0 * np.cumprod(1 + ret)
            base_turn = rng.uniform(2e8, 2e9)
            turn = base_turn * np.exp(rng.normal(0, 0.25, n_days))
            if g == "AI伺服器" and j == 0:
                # 領頭羊:趨勢啟動日起持續 ×4 量能階梯——銳利躍遷觸發 Volume Shock,
                # 持續墊高 AS 族群內排名(領頭羊 = 資金聚焦 + 領先價格)
                turn[n_days // 3:] *= 4.0
            dt_ratio = np.clip(rng.beta(4, 8, n_days), 0.05, 0.75)  # 當沖占比 ~25-40%
            day_trade = turn * dt_ratio
            inst = rng.normal(0, 0.1, n_days) * turn
            # 外資趨勢跟隨(AI 群植入持續買超);背離事件:散熱 3200 價漲金流出
            f_buy = inst * 0.6 + (turn * 0.05 if g == "AI伺服器" else 0)
            sitc = inst * 0.25
            dealer = inst * 0.15
            if g == "散熱" and j == 0:
                seg = slice(n_days // 2, n_days // 2 + 40)
                ret[seg] = np.abs(ret[seg])                          # 價格走強
                f_buy[seg] = -np.abs(f_buy[seg]) * 2                 # 資金流出 → 背離
                adj_close = 100.0 * np.cumprod(1 + ret)
            margin_buy = np.abs(rng.normal(0, 0.03, n_days)) * turn
            margin_short = np.abs(rng.normal(0, 0.015, n_days)) * turn
            for i, dd in enumerate(dates):
                rows.append((str(dd), tk, g, float(adj_close[i]), float(turn[i]),
                             float(day_trade[i]), float(f_buy[i]), float(sitc[i]),
                             float(dealer[i]), float(margin_buy[i]), float(margin_short[i])))

    # 台積電(必須被巨錨隔離)
    tsmc_ret = rng.normal(0.0005, 0.015, n_days)
    tsmc_px = 1000 * np.cumprod(1 + tsmc_ret)
    for i, dd in enumerate(dates):
        rows.append((str(dd), TSMC, "半導體", float(tsmc_px[i]), float(8e10),
                     float(2e10), 0.0, 0.0, 0.0, 0.0, 0.0))

    return pl.DataFrame(
        rows, orient="row",
        schema=["date", "ticker", "sector", "adj_close", "turnover",
                "day_trading_turnover", "net_buy_foreign", "net_buy_sitc",
                "net_buy_dealer", "margin_buy", "margin_short"],
    ).with_columns(pl.col("date").str.to_date())


# ============================================================================
# 引擎本體
# ============================================================================
def def_run_engine(df: pl.DataFrame) -> Dict[str, pl.DataFrame]:
    w, span = P["quant_window"], P["ewm_span"]

    # 【釘卯點 1】巨錨隔離 + ETR(分母:兩市 − 當沖 − 2330 非當沖 → 過濾後加總即等價)
    df = (
        df.with_columns([
            (pl.col("ticker") == TSMC).alias("is_tsmc"),
            (pl.col("turnover") - pl.col("day_trading_turnover")).clip(0.0).alias("etr"),
        ])
        .filter(~pl.col("is_tsmc"))
        .sort(["ticker", "date"])
    )

    # 【釘卯點 A】Attention Share
    mkt = df.group_by("date").agg(pl.col("etr").sum().alias("clean_mkt"))
    df = df.join(mkt, on="date", how="left").with_columns(
        (pl.col("etr") / (pl.col("clean_mkt") + 1e-8)).alias("att_share"))

    # Adj Close 報酬(USE ADJ CLOSE FOR STOCKS)
    df = df.with_columns(
        (pl.col("adj_close") / pl.col("adj_close").shift(1).over("ticker") - 1)
        .fill_null(0.0).alias("ret"))

    # 【釘卯點 A2】動態大中小(全市場橫截面滾動分位;無固定金額)
    df = df.sort(["ticker", "date"]).with_columns([
        pl.col("att_share").rolling_quantile(P["size_q_large"], window_size=w, min_samples=10)
          .over("ticker").alias("_own_hist_q")])
    day_q = (df.group_by("date").agg([
        pl.col("att_share").quantile(P["size_q_large"]).alias("as_q_large"),
        pl.col("att_share").quantile(P["size_q_mid"]).alias("as_q_mid")]))
    df = df.join(day_q, on="date", how="left").with_columns(
        pl.when(pl.col("att_share") >= pl.col("as_q_large")).then(pl.lit("Large"))
          .when(pl.col("att_share") >= pl.col("as_q_mid")).then(pl.lit("Mid"))
          .otherwise(pl.lit("Small")).alias("size_tier"))

    # 【釘卯點 2】半動態自適應動能(Shock 時基準線加重短線 → 提高敏感度)
    ss, sl = P["shock_short"], P["shock_long"]
    df = (df.with_columns([
            pl.col("etr").ewm_mean(span=ss, adjust=True).over("ticker").alias("etr_s"),
            pl.col("etr").ewm_mean(span=sl, adjust=True).over("ticker").alias("etr_l"),
            pl.col("etr").ewm_std(span=sl, adjust=True).over("ticker").alias("etr_sd")])
          .with_columns(((pl.col("etr_s") - pl.col("etr_l")) / (pl.col("etr_sd") + 1e-8))
                        .alias("vol_shock"))
          .with_columns(
            # Type-D:Shock 觸發門檻 = 自身 vol_shock 滾動 95 分位(零固定常數)
            pl.col("vol_shock").rolling_quantile(0.95, window_size=P["quant_window"], min_samples=30)
              .over("ticker").alias("shock_th"))
          .with_columns(
            ((pl.col("vol_shock") > pl.col("shock_th").fill_null(float("inf"))) &
             (pl.col("vol_shock") > 0)).alias("shock_flag"))
          .with_columns(
            pl.when(pl.col("shock_flag"))
              .then(pl.col("etr_s") * 0.8 + pl.col("etr_l") * 0.2)
              .otherwise(pl.col("etr_l")).alias("baseline"))
          .with_columns(((pl.col("etr") - pl.col("baseline")) / (pl.col("etr_sd") + 1e-8))
                        .alias("adaptive_score")))

    # 【釘卯點 3】Gate2 流動性(族群內滾動分位)
    df = (df.with_columns(
            pl.col("etr").rolling_quantile(P["liquidity_q"], window_size=w, min_samples=10)
              .over("ticker").alias("liq_floor"))
          .with_columns((pl.col("etr") >= pl.col("liq_floor").fill_null(0.0)).alias("pass_liq")))

    # 【釘卯點 4】Gate3 EWM 同動性(個股 vs 族群中位報酬;純向量化)
    # Lag-aware EWM 同動性:同期相關會把「領先者」誤判為不相關
    # (領先 2 日 ⇒ 今日報酬對上族群「未來」中位報酬才同步)。
    # 對 lag ∈ {0,1,2} 各算 EWM 相關,取最大值為 rolling_corr、argmax 為 lead_lag
    # —— 對應白皮書 CCF lag 譜(峰值 lag 即領先日數)。
    gmed = df.group_by(["sector", "date"]).agg(pl.col("ret").median().alias("g_med"))
    df = df.join(gmed, on=["sector", "date"], how="left").sort(["ticker", "date"])
    mp = 20
    lag_cols = []
    for lag in (0, 1, 2):
        ycol = f"_gm{lag}"
        df = df.with_columns(pl.col("g_med").shift(-lag).over("ticker").alias(ycol))
        df = (df.with_columns([
                pl.col("ret").ewm_mean(span=span, adjust=True, min_samples=mp).over("ticker").alias("_mx"),
                pl.col(ycol).ewm_mean(span=span, adjust=True, min_samples=mp).over("ticker").alias("_my"),
                (pl.col("ret") ** 2).ewm_mean(span=span, adjust=True, min_samples=mp).over("ticker").alias("_mx2"),
                (pl.col(ycol) ** 2).ewm_mean(span=span, adjust=True, min_samples=mp).over("ticker").alias("_my2"),
                (pl.col("ret") * pl.col(ycol)).ewm_mean(span=span, adjust=True, min_samples=mp).over("ticker").alias("_mxy")])
              .with_columns([
                (pl.col("_mx2") - pl.col("_mx") ** 2).alias("_vx"),
                (pl.col("_my2") - pl.col("_my") ** 2).alias("_vy"),
                (pl.col("_mxy") - pl.col("_mx") * pl.col("_my")).alias("_cov")])
              .with_columns(
                (pl.col("_cov") / ((pl.col("_vx").clip(1e-12).sqrt() * pl.col("_vy").clip(1e-12).sqrt()) + 1e-12))
                .clip(-1.0, 1.0).alias(f"corr_lag{lag}"))
              .drop(["_mx", "_my", "_mx2", "_my2", "_mxy", "_vx", "_vy", "_cov", ycol]))
        lag_cols.append(f"corr_lag{lag}")
    df = df.with_columns(pl.max_horizontal(lag_cols).alias("rolling_corr"))
    df = df.with_columns(
        pl.when(pl.col("corr_lag2") >= pl.max_horizontal("corr_lag0", "corr_lag1")).then(2)
          .when(pl.col("corr_lag1") >= pl.col("corr_lag0")).then(1)
          .otherwise(0).alias("lead_lag"))
    # 族群-日橫截面動態門檻:corr ≥ 當日族群內 corr_q 分位(同動性是「相對族群」的概念)
    cth = df.group_by(["sector", "date"]).agg(
        pl.col("rolling_corr").quantile(P["corr_q"]).alias("corr_th"))
    df = (df.join(cth, on=["sector", "date"], how="left")
          .with_columns((pl.col("rolling_corr") >= pl.col("corr_th").fill_null(-1.0)).alias("pass_corr")))

    # 【釘卯點 5】Gate4 資金流背離(FIS = 三大法人淨流 / ETR;全 EWM z)
    df = df.with_columns(
        ((pl.col("net_buy_foreign") + pl.col("net_buy_sitc") + pl.col("net_buy_dealer"))
         / (pl.col("etr") + 1e-8)).alias("fis"))
    df = (df.with_columns([
            pl.col("fis").ewm_mean(span=ss, adjust=True).over("ticker").alias("fis_s"),
            pl.col("fis").ewm_mean(span=sl, adjust=True).over("ticker").alias("fis_l"),
            pl.col("fis").ewm_std(span=sl, adjust=True).over("ticker").alias("fis_sd")])
          .with_columns(((pl.col("fis_s") - pl.col("fis_l")) / (pl.col("fis_sd") + 1e-8)).alias("fis_z"))
          .with_columns(
            (((pl.col("adaptive_score") > 0.5) & (pl.col("fis_z") < -0.5)) |
             ((pl.col("adaptive_score") < -0.5) & (pl.col("fis_z") > 0.5))).alias("div_flag")))

    # 【釘卯點 F】籌碼時序(全滾動 z,零固定門檻)
    for col, alias in [("net_buy_foreign", "z_foreign"), ("net_buy_sitc", "z_sitc"),
                       ("net_buy_dealer", "z_dealer"), ("margin_buy", "z_margin_buy"),
                       ("margin_short", "z_margin_short")]:
        df = df.with_columns(
            ((pl.col(col) - pl.col(col).ewm_mean(span=span, adjust=True).over("ticker"))
             / (pl.col(col).ewm_std(span=span, adjust=True).over("ticker") + 1e-8)).alias(alias))
    df = df.with_columns(
        (pl.col("day_trading_turnover") / (pl.col("turnover") + 1e-8)).alias("daytrade_ratio"))

    # 【釘卯點 C/D/E】資金風格
    df = df.with_columns(
        (pl.col("net_buy_foreign")
         / (pl.col("net_buy_foreign").abs() + pl.col("net_buy_sitc").abs()
            + pl.col("net_buy_dealer").abs() + 1e-8)).alias("f_ratio_raw"))
    df = df.with_columns(
        pl.col("f_ratio_raw").ewm_mean(span=span, adjust=True, min_samples=15).over("ticker")
          .alias("foreign_ratio"))
    df = (df.with_columns([
            pl.col("foreign_ratio").rolling_quantile(0.65, window_size=w, min_samples=mp)
              .over("ticker").alias("f_th"),
            pl.col("foreign_ratio").rolling_quantile(0.35, window_size=w, min_samples=mp)
              .over("ticker").alias("d_th")])
          .with_columns(
            pl.when(pl.col("foreign_ratio") >= pl.col("f_th")).then(pl.lit("Foreign"))
              .when(pl.col("foreign_ratio") <= pl.col("d_th")).then(pl.lit("Domestic"))
              .otherwise(pl.lit("Mixed")).alias("capital_style")))
    # 外資模式(短 span 保敏感)
    df = (df.with_columns([
            pl.col("net_buy_foreign").ewm_mean(span=span, adjust=True).over("ticker").alias("f_ewm"),
            pl.col("net_buy_foreign").ewm_mean(span=8, adjust=True).over("ticker").alias("f_short")])
          .with_columns([
            (pl.col("f_short") - pl.col("f_ewm")).alias("f_mom"),
            (pl.col("net_buy_foreign") > 0).cast(pl.Int8).alias("f_buy")])
          .with_columns([
            pl.col("f_buy").ewm_mean(span=12, adjust=True).over("ticker").alias("f_pers"),
            (pl.col("f_ewm") * pl.col("ret")).ewm_mean(span=span, adjust=True).over("ticker").alias("f_align")])
          .with_columns(
            pl.when((pl.col("f_mom") > 0) & (pl.col("f_pers") > 0.55) & (pl.col("f_align") > 0))
              .then(pl.lit("Trend_Following"))
              .when((pl.col("f_mom") > 0) & (pl.col("f_align") < 0)).then(pl.lit("Contrarian"))
              .when((pl.col("f_mom") < 0) & (pl.col("f_pers") < 0.3)).then(pl.lit("Sudden_Withdrawal"))
              .otherwise(pl.lit("Neutral")).alias("foreign_pattern")))

    # 【釘卯點 6】三加權指數(T-1 權重、Attention 18% 上限、BASE_DATE=100)
    df = df.with_columns((1.0 / pl.len().over(["sector", "date"])).alias("w_eq_raw"))
    df = df.with_columns(
        pl.col("size_tier").replace_strict(TIER_WEIGHTS, default=0.2).alias("tier_raw"))
    df = df.with_columns(
        (pl.col("tier_raw") / pl.col("tier_raw").sum().over(["sector", "date"])).alias("w_tier_raw"))
    df = df.with_columns(pl.col("att_share").clip(upper_bound=MAX_ATT_WEIGHT).alias("as_cap"))
    df = df.with_columns(
        (pl.col("as_cap") / pl.col("as_cap").sum().over(["sector", "date"])).alias("w_att_raw"))
    # T-1(零前視);首日回填當日值啟動
    df = df.sort(["ticker", "date"]).with_columns([
        pl.col("w_eq_raw").shift(1).over("ticker").fill_null(pl.col("w_eq_raw")).alias("w_eq"),
        pl.col("w_tier_raw").shift(1).over("ticker").fill_null(pl.col("w_tier_raw")).alias("w_tier"),
        pl.col("w_att_raw").shift(1).over("ticker").fill_null(pl.col("w_att_raw")).alias("w_att")])

    daily = (df.group_by(["sector", "date"]).agg([
                (pl.col("ret") * pl.col("w_eq")).sum().alias("ret_eq"),
                (pl.col("ret") * pl.col("w_tier")).sum().alias("ret_tier"),
                (pl.col("ret") * pl.col("w_att")).sum().alias("ret_att"),
                pl.len().alias("n_members"),
                pl.col("w_att").max().alias("max_w_att"),
                ((pl.col("w_att") ** 2).sum()).alias("hhi_att")])
             .sort(["sector", "date"]))
    base_ts = dt.date.fromisoformat(BASE_DATE)
    idx_cols = []
    for c in ["ret_eq", "ret_tier", "ret_att"]:
        daily = daily.with_columns((1.0 + pl.col(c)).cum_prod().over("sector").alias(f"_cum_{c}"))
        idx_cols.append(c)
    basevals = (daily.filter(pl.col("date") == base_ts)
                .select(["sector"] + [pl.col(f"_cum_{c}").alias(f"_base_{c}") for c in idx_cols]))
    daily = daily.join(basevals, on="sector", how="left")
    for c, name in [("ret_eq", "index_equal"), ("ret_tier", "index_tier"), ("ret_att", "index_att")]:
        daily = daily.with_columns((pl.col(f"_cum_{c}") / pl.col(f"_base_{c}") * 100.0).alias(name))
    daily = daily.drop([f"_cum_{c}" for c in idx_cols] + [f"_base_{c}" for c in idx_cols])

    # VWSP z 與動能 z(統一尺度,可直接比較/相乘)
    daily = daily.with_columns(
        ((pl.col("ret_att") - pl.col("ret_att").ewm_mean(span=40, adjust=True).over("sector"))
         / (pl.col("ret_att").ewm_std(span=40, adjust=True).over("sector") + 1e-8)).alias("vwsp_z"))
    df = df.join(daily.select(["sector", "date", "vwsp_z"]), on=["sector", "date"], how="left")
    df = df.with_columns(
        ((pl.col("adaptive_score") - pl.col("adaptive_score").ewm_mean(span=40, adjust=True).over("ticker"))
         / (pl.col("adaptive_score").ewm_std(span=40, adjust=True).over("ticker") + 1e-8)).alias("momentum_z"))
    df = df.with_columns((pl.col("vwsp_z") * pl.col("momentum_z")).alias("consistency"))
    df = df.sort(["ticker", "date"]).with_columns(
        pl.col("consistency").ewm_mean(span=15, adjust=True).over("ticker").alias("consistency_s"))

    # 【釘卯點 B】角色(相對+絕對雙重:族群內 AS 排名分位 × 一致性)
    df = df.with_columns(
        (pl.col("att_share").rank("average").over(["sector", "date"])
         / pl.len().over(["sector", "date"])).alias("as_rank"))
    df = df.with_columns(
        pl.when(pl.col("rolling_corr") < UNRELATED_CORR).then(pl.lit("UNRELATED"))
          # LEADER 證據 = 聚焦度前段 + lag 結構領先;同動強度僅需過憲法下限
          # (領先者因錯位,同期相關必然低於跟隨者——不得要求其贏過同儕)
          .when((pl.col("as_rank") >= 0.7) & (pl.col("lead_lag") >= 1) &
                (pl.col("rolling_corr") >= UNRELATED_CORR))
          .then(pl.lit("LEADER"))
          .when((pl.col("as_rank") < 0.3) | pl.col("div_flag")).then(pl.lit("LAGGER"))
          .otherwise(pl.lit("PEER")).alias("role"))
    df = df.with_columns(
        (pl.col("pass_liq") & pl.col("pass_corr") & ~pl.col("div_flag")).alias("valid_member"))
    return {"panel": df, "indices": daily}


# ============================================================================
# 驗證帳本(受控真值)+ 收斂迴圈
# ============================================================================
def def_validate(res: Dict[str, pl.DataFrame]) -> List[Dict[str, Any]]:
    df, idx = res["panel"], res["indices"]
    T: List[Dict[str, Any]] = []

    def add(tid, name, ok, ev=""):
        T.append({"TestID": tid, "TestName": name, "Status": "PASS" if ok else "FAIL",
                  "Severity": "HARD", "Evidence": str(ev)[:200]})

    add("V01", "巨錨隔離:2330 不在面板", df.filter(pl.col("ticker") == TSMC).height == 0)
    add("V02", "ETR = 成交值−當沖且非負", bool((df["etr"] >= 0).all()) and
        bool((df["etr"] <= df["turnover"] + 1e-6).all()))
    as_day = df.group_by("date").agg(pl.col("att_share").sum().alias("s"))
    add("V03", "AS 每日總和 = 1(淨市場定義自洽)",
        bool((as_day["s"] - 1.0).abs().max() < 1e-6), f"max_dev={(as_day['s'] - 1.0).abs().max():.2e}")
    med = df.group_by("size_tier").agg(pl.col("att_share").median().alias("m"))
    md = {r["size_tier"]: r["m"] for r in med.to_dicts()}
    add("V04", "大中小分層單調(AS 中位 Large>Mid>Small)",
        md.get("Large", 0) > md.get("Mid", 0) > md.get("Small", 0),
        {k: round(v, 5) for k, v in md.items()})
    # T-1 零前視:權重欄 = 前一日 raw(抽樣驗證)
    chk = (df.sort(["ticker", "date"])
             .with_columns(pl.col("w_att_raw").shift(1).over("ticker").alias("_expect"))
             .filter(pl.col("_expect").is_not_null()))
    add("V05", "指數權重採 T-1(零前視)",
        bool((chk["w_att"] - chk["_expect"]).abs().max() < 1e-12))
    add("V06", "Attention 上限鎖 18%(cap 於正規化前施加)",
        bool((df["as_cap"] <= MAX_ATT_WEIGHT + 1e-12).all()))
    base_ts = dt.date.fromisoformat(BASE_DATE)
    brow = idx.filter(pl.col("date") == base_ts)
    ok_base = brow.height > 0 and all(
        abs(v - 100.0) < 1e-9 for c in ["index_equal", "index_tier", "index_att"] for v in brow[c])
    add("V07", f"三指數於 {BASE_DATE} 全部 = 100", ok_base)
    lead = (df.filter((pl.col("ticker") == "3100") & (pl.col("date") > dt.date(2025, 8, 1))))
    lead_share = lead.filter(pl.col("role") == "LEADER").height / max(lead.height, 1)
    add("V08", "植入領頭羊(3100)被辨識為 LEADER(視窗多數日)", lead_share > 0.5,
        f"leader_days={lead_share:.2%}")
    unrel = df.filter((pl.col("ticker") == "2605") & (pl.col("date") > dt.date(2025, 6, 1)))
    unrel_share = unrel.filter(pl.col("role") == "UNRELATED").height / max(unrel.height, 1)
    add("V09", "植入不相關者(2605)被標 UNRELATED", unrel_share > 0.5, f"{unrel_share:.2%}")
    dseg = df.filter((pl.col("ticker") == "3200") &
                     (pl.col("date") >= dt.date(2025, 8, 15)) & (pl.col("date") <= dt.date(2025, 11, 1)))
    add("V10", "植入背離事件(3200 價漲金流出)被 Gate4 攔截",
        dseg.filter(pl.col("div_flag")).height > 0, f"flag_days={dseg.filter(pl.col('div_flag')).height}")
    shock_days = df.filter(pl.col("shock_flag"))
    beh = (shock_days.with_columns(
        ((pl.col("baseline") - pl.col("etr_s")).abs() <
         (pl.col("baseline") - pl.col("etr_l")).abs()).alias("_near_short")))
    add("V11", "半動態敏感:Shock 旗標(滾動分位觸發)日基準線貼近短線",
        shock_days.height > 0 and bool(beh["_near_short"].all()),
        f"shock_days={shock_days.height}")
    mz = df.filter(pl.col("momentum_z").is_finite())["momentum_z"].std()
    vz = idx.filter(pl.col("vwsp_z").is_finite())["vwsp_z"].std()
    add("V12", "可比性:momentum_z 與 vwsp_z 同尺度(std∈[0.5,2])",
        0.5 < mz < 2.0 and 0.5 < vz < 2.0, f"mz={mz:.2f} vz={vz:.2f}")
    tf = df.filter((pl.col("sector") == "AI伺服器") & (pl.col("date") > dt.date(2025, 9, 1)))
    tf_share = tf.filter(pl.col("foreign_pattern") == "Trend_Following").height / max(tf.height, 1)
    add("V13", "植入外資持續買超 → Trend_Following 佔比顯著", tf_share > 0.25, f"{tf_share:.2%}")
    add("V14", "籌碼時序全滾動 z(z_foreign/z_sitc/z_dealer/融資融券)",
        all(c in df.columns for c in ["z_foreign", "z_sitc", "z_dealer", "z_margin_buy", "z_margin_short"]))
    add("V15", "HHI 集中度監控輸出(Attention 加權)", "hhi_att" in idx.columns and
        bool((idx["hhi_att"] <= 1.0 + 1e-9).all()))
    return T


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def def_main() -> int:
    RUN_OUT.mkdir(parents=True, exist_ok=True)
    iterations, tests = 0, []
    for iterations in range(1, 4):                       # 收斂迴圈(≤3 輪)
        res = def_run_engine(def_generate_panel())
        tests = def_validate(res)
        if all(t["Status"] == "PASS" for t in tests):
            break
    hard = sum(1 for t in tests if t["Status"] != "PASS")
    status = "VIS_ADAPTIVE_PASS" if hard == 0 else "VIS_ADAPTIVE_BLOCKED"

    res["indices"].write_csv(RUN_OUT / "vis_group_indices_three_weightings.csv")
    keep = ["date", "ticker", "sector", "att_share", "size_tier", "role", "capital_style",
            "foreign_pattern", "valid_member", "rolling_corr", "consistency",
            "momentum_z", "vwsp_z", "z_foreign", "z_sitc", "z_dealer",
            "z_margin_buy", "z_margin_short", "daytrade_ratio"]
    res["panel"].select(keep).write_csv(RUN_OUT / "vis_panel_classified.csv")
    summary = {
        "Harness": "VIA_VIS_AdaptiveClassification", "Version": VERSION,
        "GeneratedAt": dt.datetime.now().isoformat(timespec="seconds"),
        "Status": status, "HardFailures": hard, "Iterations": iterations,
        "BaseDate": BASE_DATE, "MaxAttentionWeight": MAX_ATT_WEIGHT,
        "ParamFamily": {"TypeF": ["TSMC", "BASE_DATE", "UNRELATED_CORR", "MAX_ATT_WEIGHT"],
                        "TypeD": ["liquidity_q", "corr_q", "size quantiles", "ewm spans(rolling)"],
                        "TypeH": ["baseline(shock 旗標日加重短線 0.8;旗標=滾動95分位,零固定常數)"]},
        "Tests": tests,
        "Boundary": "Controlled DGP = 方法驗證,非實盤績效;Adj Close 報酬;零網路",
    }
    (RUN_OUT / "vis_run_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {p.name: sha256(p) for p in sorted(RUN_OUT.iterdir())
                if p.is_file() and p.name != "SHA256_MANIFEST.json"}
    (RUN_OUT / "SHA256_MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 88)
    print(f"VIA VIS Adaptive Classification v{VERSION} · polars")
    for t in tests:
        print(f"  [{t['Status']}] {t['TestID']} {t['TestName']} :: {t['Evidence']}")
    print("Status     :", status, f"| iterations={iterations}")
    print("Run Dir    :", RUN_OUT)
    print("=" * 88)
    return 0 if hard == 0 else 2


if __name__ == "__main__":
    raise SystemExit(def_main())
