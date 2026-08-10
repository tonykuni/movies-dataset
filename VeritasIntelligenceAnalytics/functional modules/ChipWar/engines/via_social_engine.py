# [VIA 歸檔補丁 2026-08-10] 路徑常數改為 VIA_CHIPWAR_STAGING/VIA_CHIPWAR_REPORTS 環境變數
# 可覆寫之模組相對路徑(_generated/,gitignored);運算邏輯零觸碰。原始上傳 sha256[:16]=82be50a3ae9a88f1
# -*- coding: utf-8 -*-
"""
VIA Social FOMO Lane v0.1 — 聊天室 FOMO 第二通道
Channels: behavior FOMO (已建: 融資/當沖/戶數) vs social FOMO (聊天室言論).
Core tests:
  1) lead-lag CCF (Spearman): social 領先或落後 behavior/報酬?
  2) extreme contrarian flags: p95 貪婪 / p5 恐慌 之後的 forward return
  3) hype divergence: mention_hhi vs flow_hhi 背離 = 有話題沒資金(純吹)
Lexicon: PTT-native zh-TW slang (jieba custom dict on Tony's machine; here rule-count).
T4 synthetic, embedded truth: social LAGS behavior FOMO by ~7bd, spikes into local tops.
"""
import json, datetime as dt
import numpy as np, pandas as pd
from scipy import stats

def _nan_to_null(o):
    import math
    if isinstance(o,float): return None if (math.isnan(o) or math.isinf(o)) else o
    if isinstance(o,dict): return {k:_nan_to_null(v) for k,v in o.items()}
    if isinstance(o,list): return [_nan_to_null(v) for v in o]
    return o

RNG = np.random.default_rng(20250408)
import os as _os
from pathlib import Path as _P
STAG = _os.environ.get("VIA_CHIPWAR_STAGING") or str(_P(__file__).resolve().parents[1] / "_generated" / "staging")
_P(STAG).mkdir(parents=True, exist_ok=True)
# ---- PTT-native lexicon (ships as JSON for jieba userdict on real crawl) ----
LEXICON = {
    "boarding":     ["上車", "梭哈", "全壓", "all in", "歐印", "無腦多", "衝了", "開槓桿", "融資買", "太神啦", "還在等什麼", "起飛", "噴出", "軋空手"],
    "capitulation": ["畢業", "認賠", "斷頭", "融資追繳", "住套房", "套牢", "崩了", "跳水", "睡公園", "賣在阿呆谷", "多殺多"],
    "leverage":     ["融資", "槓桿", "質押", "當沖", "隔日沖", "無本當沖"],
    "sarcasm_risk": ["反串", "帶風向", "出貨文", "老師", "會員", "群組"],   # posts hitting these are down-weighted
}

days = pd.bdate_range(dt.date(2025, 4, 8), dt.date(2026, 7, 9)).date
n = len(days)
brk = next(i for i, d in enumerate(days) if d >= dt.date(2025, 11, 15))

# ---- synthetic: behavior FOMO from macro lane; social = lagged(7bd) + noise + top-spikes ----
mac = pd.DataFrame(json.load(open(f"{STAG}/macro_run.json", encoding="utf-8"))["macro"])
beh = mac.fomo.values[:n]
lag_true = 7
social_base = np.concatenate([np.full(lag_true, beh[0]), beh[:-lag_true]])
reg = pd.DataFrame(json.load(open(f"{STAG}/chipwar_run.json", encoding="utf-8"))["regime"])
score = np.interp(np.arange(n), np.linspace(0, n - 1, len(reg)), reg.chipwar_score.values)
spikes = np.where(score > np.quantile(score, 0.85), 12, 0)                    # euphoria posts cluster at hot phases
social = np.clip(social_base + spikes + RNG.normal(0, 4, n), 0, 100)

post_vol = np.clip(80 + 2.2 * social + RNG.normal(0, 25, n), 20, None)        # posts/day
boarding = np.clip(0.02 + social / 100 * 0.16 + RNG.normal(0, .012, n), 0, 1)
capitul  = np.clip(0.10 - social / 100 * 0.07 + RNG.normal(0, .010, n), 0, 1)
# mention concentration: talks concentrate on tech late (hype), flows didn't (bloc lane) → embedded divergence
mention_hhi = np.concatenate([np.full(brk, .18), np.linspace(.18, .34, n - brk)]) + RNG.normal(0, .015, n)
bloc = pd.DataFrame(json.load(open(f"{STAG}/bloc_run.json", encoding="utf-8"))["conc"])
flow_hhi = np.interp(np.arange(n), np.linspace(0, n - 1, len(bloc)), bloc.flow_hhi.values)

S = pd.DataFrame({"trade_date": days, "post_volume": post_vol, "boarding_ratio": boarding,
                  "capitulation_ratio": capitul, "mention_hhi": mention_hhi,
                  "social_fomo": social, "behavior_fomo": beh, "flow_hhi_x": flow_hhi})
S["evidence_tier"] = "T4"

# ---- Test 1: lead-lag CCF (Spearman at each shift; + = social LEADS) ----
ccf = []
for k in range(-15, 16):
    a = S.social_fomo.shift(-k) if k > 0 else S.social_fomo.shift(-k)          # shift(-k): k>0 social earlier
    ic = stats.spearmanr(S.social_fomo.shift(k), S.behavior_fomo, nan_policy="omit").statistic
    ccf.append({"lag": k, "spearman": round(float(ic), 3)})
ccf_df = pd.DataFrame(ccf)
best = ccf_df.loc[ccf_df.spearman.abs().idxmax()]

# ---- Test 2: extremes → contrarian forward check (index fwd 10d ret proxy from regime universe) ----
import duckdb
con = duckdb.connect(f"{STAG}/ssot_chipwar.duckdb", read_only=True)
idx = con.execute("SELECT trade_date, ret_1d FROM prices_daily WHERE scope_id='^TWII' ORDER BY trade_date").df()
idx["trade_date"] = pd.to_datetime(idx.trade_date).dt.date
S2 = S.merge(idx, on="trade_date", how="left")
S2["fwd10"] = S2.ret_1d[::-1].rolling(10).sum()[::-1].shift(-1)
p95, p05 = np.nanquantile(S2.social_fomo, .95), np.nanquantile(S2.social_fomo, .05)
S2["extreme_flag"] = np.where(S2.social_fomo >= p95, "p95_greed", np.where(S2.social_fomo <= p05, "p05_fear", None))
ext = {
    "n_greed": int((S2.extreme_flag == "p95_greed").sum()),
    "fwd10_after_greed_mean": round(float(S2.loc[S2.extreme_flag == "p95_greed", "fwd10"].mean()), 4),
    "n_fear": int((S2.extreme_flag == "p05_fear").sum()),
    "fwd10_after_fear_mean": round(float(S2.loc[S2.extreme_flag == "p05_fear", "fwd10"].mean()), 4),
    "fwd10_uncond_mean": round(float(S2.fwd10.mean()), 4),
}

# ---- Test 3: hype divergence — mention_hhi rises while flow_hhi doesn't ----
hz = (S.mention_hhi - S.mention_hhi.rolling(60, min_periods=30).mean()) / S.mention_hhi.rolling(60, min_periods=30).std(ddof=0).clip(lower=1e-6)
fz = (S.flow_hhi_x - S.flow_hhi_x.rolling(60, min_periods=30).mean()) / S.flow_hhi_x.rolling(60, min_periods=30).std(ddof=0).clip(lower=1e-6)
S["hype_divergence"] = (hz - fz).clip(-4, 4)
div_days = int((S.hype_divergence > 1.5).sum())

gate = {"rows": len(S), "parse_errors": 0, "evidence_tier": "T4",
        "embedded_true_lag_bd": lag_true,
        "ccf_best_lag": int(best.lag), "ccf_best_spearman": float(best.spearman),
        "lag_recovered": bool(abs(int(best.lag) - (-lag_true)) <= 2),
        **ext, "hype_divergence_days_gt1p5z": div_days}
out = {"gate": gate, "lexicon": LEXICON, "ccf": ccf,
       "social": S.assign(trade_date=S.trade_date.astype(str)).round(4).to_dict("records")}
json.dump(_nan_to_null(out), open(f"{STAG}/social_run.json", "w", encoding="utf-8"), ensure_ascii=False, allow_nan=False)
print(json.dumps(gate, ensure_ascii=False, indent=2))
