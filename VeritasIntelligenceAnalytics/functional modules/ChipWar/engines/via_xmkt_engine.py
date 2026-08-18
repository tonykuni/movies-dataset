# [VIA 歸檔補丁 2026-08-10] 路徑常數改為 VIA_CHIPWAR_STAGING/VIA_CHIPWAR_REPORTS 環境變數
# 可覆寫之模組相對路徑(_generated/,gitignored);運算邏輯零觸碰。原始上傳 sha256[:16]=1f9b51203d661f48
# -*- coding: utf-8 -*-
"""
VIA Cross-Market FOMO Factor Lab v0.1 — 台灣 FOMO 因子組 → ^TWII + ^GSPC
- factors: fomo_index, behavior_fomo, social_fomo, hype_divergence, boarding_ratio,
           dxy, fed_net_liq, wti, m1b_m2_spread, global_flow   (10 factors)
- targets x horizons: {^TWII, ^GSPC} x {1,5,10,21}d
- SESSION ORDERING (the #1 cross-market leak):
    TWII closes 13:30 TST before US opens → factor(t) legally predicts GSPC fwd starting SAME day t US session;
    TWII fwd must start t+1. Encoded as horizon shift: TWII shift(-1), GSPC shift(0) on fwd windows.
- auto-rolling: 60d rolling Spearman IC per cell; ICIR = mean/std of rolling IC series
- walk-forward optimizer: train 120d → select weights by criteria (max_icir | top_k=3 | equal_w) → eval next 21d OOS
  honesty gap = insample-best IC minus WF OOS IC, reported every run
T4 synthetic: GSPC generated with global factor + small true TW-FOMO extreme spillover, so lab must
  (a) recover the extreme-only spillover, (b) show most raw 'TW leads SPX' IC dies after global-factor control.
"""
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
import json
import numpy as np, pandas as pd, duckdb
from scipy import stats

import os as _os
from pathlib import Path as _P
STAG = _os.environ.get("VIA_CHIPWAR_STAGING") or str(_P(__file__).resolve().parents[1] / "_generated" / "staging")
_P(STAG).mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(514)

# ---- assemble factor panel from prior lanes ----
soc = pd.DataFrame(json.load(open(f"{STAG}/social_run.json", encoding="utf-8"))["social"])
mac = pd.DataFrame(json.load(open(f"{STAG}/macro_run.json", encoding="utf-8"))["macro"])
fom = pd.DataFrame(json.load(open(f"{STAG}/fomo_index_run.json", encoding="utf-8"))["series"])
F = (soc[["trade_date", "behavior_fomo", "social_fomo", "hype_divergence", "boarding_ratio"]]
     .merge(mac[["trade_date", "dxy", "fed_net_liq", "wti", "m1b_m2_spread", "global_flow"]], on="trade_date")
     .merge(fom[["trade_date", "fomo_index"]], on="trade_date"))
FACTORS = ["fomo_index", "behavior_fomo", "social_fomo", "hype_divergence", "boarding_ratio",
           "dxy", "fed_net_liq", "wti", "m1b_m2_spread", "global_flow"]

# ---- targets: TWII from SSOT; GSPC synthetic (global factor + extreme-FOMO spillover truth) ----
con = duckdb.connect(f"{STAG}/ssot_chipwar.duckdb", read_only=True)
tw = con.execute("SELECT trade_date, ret_1d FROM prices_daily WHERE scope_id='^TWII' ORDER BY trade_date").df()
tw["trade_date"] = tw.trade_date.astype(str)
n = len(tw)
glob = RNG.normal(0.0007, 0.009, n)
fi = F.fomo_index.reindex(range(n)).fillna(50).values
extreme_spill = np.where(fi >= np.quantile(fi, 0.93), -0.0022, np.where(fi <= np.quantile(fi, 0.07), 0.0022, 0))
gspc = 0.8 * glob + 0.35 * tw.ret_1d.values + extreme_spill + RNG.normal(0, 0.006, n)   # TW same-day co-move + extreme spill
P = tw.rename(columns={"ret_1d": "twii"}).assign(gspc=gspc).merge(F, on="trade_date", how="inner")

# ---- fwd returns with session ordering ----
HORIZONS = [1, 5, 10, 21]
for h in HORIZONS:
    P[f"twii_f{h}"] = P.twii[::-1].rolling(h).sum()[::-1].shift(-1)      # TW target starts t+1
    P[f"gspc_f{h}"] = P.gspc[::-1].rolling(h).sum()[::-1].shift(0)       # US session same calendar day t = legal
LEAK = {f"twii_f{h}": P.twii[::-1].rolling(h).sum()[::-1].shift(0) for h in HORIZONS}  # leaky TW (t+0) benchmark

# ---- rolling IC grid ----
W = 60
rows = []
for f in FACTORS:
    for tgt in ["twii", "gspc"]:
        for h in HORIZONS:
            y = P[f"{tgt}_f{h}"]
            ics = []
            for e in range(W, len(P) - h):
                ic = stats.spearmanr(P[f].iloc[e - W:e], y.iloc[e - W:e], nan_policy="omit").statistic
                ics.append(ic)
            ics = np.array(ics, float); ics = ics[np.isfinite(ics)]
            icir = float(ics.mean() / (ics.std(ddof=0) + 1e-9))
            rows.append({"factor": f, "target": tgt, "horizon": h,
                         "ic_mean": round(float(ics.mean()), 4), "icir": round(icir, 3), "n_win": len(ics)})
GRID = pd.DataFrame(rows)

# global-factor control: partial IC of each factor on gspc after removing same-day twii co-move
ctrl = []
for f in FACTORS:
    x = P[f].values.astype(float); y = P["gspc_f5"].values; z = P.twii.values
    ok = np.isfinite(x) & np.isfinite(y) & np.isfinite(z)
    xr = x[ok] - np.polyval(np.polyfit(z[ok], x[ok], 1), z[ok])
    yr = y[ok] - np.polyval(np.polyfit(z[ok], y[ok], 1), z[ok])
    ctrl.append({"factor": f, "gspc_f5_raw_ic": round(float(stats.spearmanr(x[ok], y[ok]).statistic), 4),
                 "gspc_f5_partial_ic": round(float(stats.spearmanr(xr, yr).statistic), 4)})
CTRL = pd.DataFrame(ctrl)

# ---- walk-forward optimizer ----
def zsc(v):
    v = pd.Series(v); return ((v - v.mean()) / (v.std(ddof=0) + 1e-9)).values

TRAIN, EVAL = 120, 21
def walkforward(tgt_col, criteria):
    out = []
    X = P[FACTORS].apply(lambda c: (c - c.rolling(120, min_periods=40).mean()) /
                                    c.rolling(120, min_periods=40).std(ddof=0).clip(lower=1e-9))
    y = P[tgt_col]
    for s in range(TRAIN, len(P) - EVAL, EVAL):
        tr = slice(s - TRAIN, s); ev = slice(s, s + EVAL)
        ics = {}
        for f in FACTORS:
            ic = stats.spearmanr(X[f].iloc[tr], y.iloc[tr], nan_policy="omit").statistic
            ics[f] = 0.0 if not np.isfinite(ic) else ic
        if criteria == "equal_w":
            wts = {f: 1 / len(FACTORS) for f in FACTORS}
        elif criteria == "top_k":
            top = sorted(ics, key=lambda k: abs(ics[k]), reverse=True)[:3]
            wts = {f: (np.sign(ics[f]) / 3 if f in top else 0.0) for f in FACTORS}
        else:  # max_icir: IC-weighted
            tot = sum(abs(v) for v in ics.values()) + 1e-9
            wts = {f: ics[f] / tot for f in FACTORS}
        comp_tr = sum(wts[f] * X[f].iloc[tr].fillna(0) for f in FACTORS)
        comp_ev = sum(wts[f] * X[f].iloc[ev].fillna(0) for f in FACTORS)
        ins = stats.spearmanr(comp_tr, y.iloc[tr], nan_policy="omit").statistic
        oos = stats.spearmanr(comp_ev, y.iloc[ev], nan_policy="omit").statistic
        if np.isfinite(oos):
            out.append({"eval_start": P.trade_date.iloc[s], "criteria": criteria,
                        "insample_ic": round(float(ins), 4), "oos_ic": round(float(oos), 4)})
    return pd.DataFrame(out)

WF = pd.concat([walkforward("twii_f5", c) for c in ["max_icir", "top_k", "equal_w"]] +
               [walkforward("gspc_f5", c).assign(criteria=lambda d: d.criteria + "_gspc") for c in ["max_icir"]])
wf_sum = WF.groupby("criteria").agg(n=("oos_ic", "size"), oos_ic_mean=("oos_ic", "mean"),
                                    insample_ic_mean=("insample_ic", "mean")).round(4)
wf_sum["honesty_gap"] = (wf_sum.insample_ic_mean - wf_sum.oos_ic_mean).round(4)

n_tests = len(FACTORS) * 2 * len(HORIZONS)
gate = {"rows_panel": len(P), "parse_errors": 0, "evidence_tier": "T4",
        "n_grid_tests": n_tests, "bonferroni_note": f"{n_tests} cells: demand |ICIR|>0.5 not raw IC",
        "best_cell": GRID.loc[GRID.icir.abs().idxmax()].to_dict(),
        "session_ordering": "twii shift(-1) / gspc shift(0) enforced",
        "extreme_spillover_truth_recovered": bool(
            abs(CTRL.loc[CTRL.factor == "fomo_index", "gspc_f5_partial_ic"].iloc[0]) > 0.04)}
out = {"gate": gate, "grid": GRID.to_dict("records"), "ctrl": CTRL.to_dict("records"),
       "wf": WF.to_dict("records"), "wf_summary": wf_sum.reset_index().to_dict("records")}
json.dump(out, open(f"{STAG}/xmkt_run.json", "w", encoding="utf-8"), ensure_ascii=False)
print(json.dumps(gate, ensure_ascii=False, indent=2, default=str))
print(wf_sum.to_string())
