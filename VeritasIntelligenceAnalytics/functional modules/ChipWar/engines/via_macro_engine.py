# [VIA 歸檔補丁 2026-08-10] 路徑常數改為 VIA_CHIPWAR_STAGING/VIA_CHIPWAR_REPORTS 環境變數
# 可覆寫之模組相對路徑(_generated/,gitignored);運算邏輯零觸碰。原始上傳 sha256[:16]=febba0a413a5b1e8
# -*- coding: utf-8 -*-
"""
VIA Macro Liquidity Lane v0.1 — 資金盤根因層
Series: TW M1B/M2 YoY cross, FED_NET_LIQ (WALCL-TGA-RRP), DXY, WTI, FOMO composite, global flow proxy.
Question answered: does macro liquidity LEAD the chipwar regime? (lagged Spearman, clean ASOF)
SANDBOX HONESTY: synthetic T4; real fetch = endpoint_registry on Tony's machine.
"""
import json, datetime as dt
import numpy as np, pandas as pd
from scipy import stats

RNG = np.random.default_rng(20250408)
T0, T1_ = dt.date(2025, 4, 8), dt.date(2026, 7, 9)
BRK = dt.date(2025, 11, 15)
import os as _os
from pathlib import Path as _P
STAG = _os.environ.get("VIA_CHIPWAR_STAGING") or str(_P(__file__).resolve().parents[1] / "_generated" / "staging")
_P(STAG).mkdir(parents=True, exist_ok=True)
days = pd.bdate_range(T0, T1_).date
n = len(days); brk = next(i for i, d in enumerate(days) if d >= BRK)

# ---- synthetic macro (T4), embedded story: phase1 liquidity expansion; phase2 plateau/drain while FOMO climbs ----
t = np.arange(n)
fed_liq = np.concatenate([np.linspace(0, 1.0, brk), 1.0 - np.linspace(0, 0.35, n - brk)]) + RNG.normal(0, .03, n)
dxy     = np.concatenate([np.linspace(0, -1.0, brk), -1.0 + np.linspace(0, 0.45, n - brk)]) + RNG.normal(0, .05, n)
wti     = np.cumsum(RNG.normal(0, .04, n)) + np.where(t > brk, 0.3, 0)          # geopolitical drift late
# monthly M1B/M2 YoY: golden cross mid phase1, spread narrows in phase2
mdates = pd.date_range(T0, T1_, freq="ME").date
m1b = np.concatenate([np.linspace(2.5, 8.5, len(mdates)//2), np.linspace(8.5, 5.5, len(mdates)-len(mdates)//2)]) + RNG.normal(0,.3,len(mdates))
m2  = np.linspace(5.5, 6.0, len(mdates)) + RNG.normal(0,.15,len(mdates))
# FOMO components (daily): climb hard in phase2
fomo_raw = np.concatenate([np.linspace(.2,.45,brk), np.linspace(.45,.85,n-brk)]) + RNG.normal(0,.05,n)
glob_flow = 0.7*fed_liq - 0.4*dxy + RNG.normal(0,.15,n)                          # global flow proxy (ICI/FIS analog)

# ---- ASOF discipline: M1B/M2 usable only 25 days after month end ----
m_rel = [pd.Timestamp(d) + pd.Timedelta(days=25) for d in mdates]
m_df = pd.DataFrame({"obs": mdates, "rel": m_rel, "m1b": m1b, "m2": m2})

def _nan_to_null(o):
    """完整性誠實: NaN/inf → None(JSON null); 缺值記錄為null不內插"""
    import math
    if isinstance(o, float):
        return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o, dict):  return {k: _nan_to_null(v) for k, v in o.items()}
    if isinstance(o, list):  return [_nan_to_null(v) for v in o]
    return o

def asof_monthly(day):
    ok = m_df[m_df.rel <= pd.Timestamp(day)]
    return (ok.iloc[-1].m1b, ok.iloc[-1].m2) if len(ok) else (np.nan, np.nan)
m1b_d, m2_d = zip(*[asof_monthly(d) for d in days])
m1b_d, m2_d = np.array(m1b_d), np.array(m2_d)
golden = (m1b_d > m2_d).astype(float)

# fed liq weekly release lag 2bd
def lag_weekly(x, lag=7):
    s = pd.Series(x, index=pd.DatetimeIndex(days))
    return s.shift(freq=f"{lag}D").reindex(pd.DatetimeIndex(days), method="ffill").values
fed_asof = pd.Series(fed_liq, index=pd.DatetimeIndex(days)).rolling(5).mean().shift(2).values

M = pd.DataFrame({"trade_date": days, "fed_net_liq": fed_asof, "dxy": dxy, "wti": wti,
                  "m1b_yoy": m1b_d, "m2_yoy": m2_d, "golden_cross": golden,
                  "fomo": np.clip(fomo_raw,0,1)*100, "global_flow": glob_flow})
M["m1b_m2_spread"] = M.m1b_yoy - M.m2_yoy
M["evidence_tier"] = "T4"

# ---- lead-lag: does each macro series LEAD chipwar score? ----
run = json.load(open(f"{STAG}/chipwar_run.json", encoding="utf-8"))
reg = pd.DataFrame(run["regime"])
reg["trade_date"] = pd.to_datetime(reg.trade_date).dt.date
P = M.merge(reg[["trade_date", "chipwar_score"]], on="trade_date", how="inner").dropna()
series = ["fed_net_liq", "dxy", "wti", "m1b_m2_spread", "fomo", "global_flow"]
LL = []
for s in series:
    for lag in [0, 5, 10, 21, 42, 63]:
        x = P[s].shift(lag).iloc[lag:]; y = P.chipwar_score.iloc[lag:]
        ic = stats.spearmanr(x, y).statistic
        LL.append({"series": s, "lag_days": lag, "spearman": round(float(ic), 3)})
LLd = pd.DataFrame(LL)
best = LLd.loc[LLd.groupby("series").spearman.apply(lambda g: g.abs().idxmax())]

out = {
    "gate": {"rows_macro": len(M), "null_after_warmup": int(M.iloc[40:].drop(columns='trade_date').isna().sum().sum()),
             "parse_errors": 0, "evidence_tier": "T4",
             "m1b_asof_lag_days": 25, "fed_asof_lag_bd": 2},
    "macro": M.assign(trade_date=M.trade_date.astype(str)).round(3).to_dict("records"),
    "leadlag": LL, "leadlag_best": best.to_dict("records"),
}
json.dump(_nan_to_null(out), open(f"{STAG}/macro_run.json", "w", encoding="utf-8"), ensure_ascii=False, allow_nan=False)
print(json.dumps(out["gate"], ensure_ascii=False))
print(best.to_string(index=False))
