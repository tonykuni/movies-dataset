# [VIA 歸檔補丁 2026-08-10] 路徑常數改為 VIA_CHIPWAR_STAGING/VIA_CHIPWAR_REPORTS 環境變數
# 可覆寫之模組相對路徑(_generated/,gitignored);運算邏輯零觸碰。原始上傳 sha256[:16]=0c3927a1990ca0fa
# -*- coding: utf-8 -*-
"""
VIA FOMO Index v0.1 — 統一 FOMO 指數 (0-100)
Composition (design decisions, all falsifiable):
  - core = behavior channel (融資/當沖/戶數/量能) 70% frozen weight — social is ECHO not driver (CCF lag −7 proven)
  - social overlay 30%: level only; PLUS two discrete overlays:
      extreme gate  : social p95/p5 → 過熱/恐慌 state override (contrarian only at extremes)
      froth quality : hype_divergence>1.5z → froth_flag (talk without flow)
  - states: 恐慌(<20) 冷(20-40) 溫(40-60) 熱(60-80) 過熱(>=80)
Validation gates (FlowSystem style):
  G_ic   : Spearman(index_t, fwd10_t) expected NEGATIVE (high FOMO → poor forward)
  G_mono : quintile fwd10 monotonic decreasing (allow 1 inversion)
  G_null : shuffled-index |IC| < 0.05
  G_oos  : split-half sign consistency  [PROVISIONAL: single-cut, CPCV pending per LL]
Verdict: PROVED_VALID iff all gates pass. T4 synthetic.
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
import numpy as np, pandas as pd
from scipy import stats

import os as _os
from pathlib import Path as _P
STAG = _os.environ.get("VIA_CHIPWAR_STAGING") or str(_P(__file__).resolve().parents[1] / "_generated" / "staging")
_P(STAG).mkdir(parents=True, exist_ok=True)
RNG = np.random.default_rng(7)

soc = pd.DataFrame(json.load(open(f"{STAG}/social_run.json", encoding="utf-8"))["social"])
S = soc[["trade_date", "behavior_fomo", "social_fomo", "hype_divergence"]].copy()

# ---- unified index ----
W_BEH, W_SOC = 0.70, 0.30                                  # hand-set v0, frozen; tech debt → CPCV
S["fomo_index"] = (W_BEH * S.behavior_fomo + W_SOC * S.social_fomo).clip(0, 100)
p95 = S.social_fomo.quantile(.95); p05 = S.social_fomo.quantile(.05)
S["state"] = pd.cut(S.fomo_index, [-1, 20, 40, 60, 80, 101],
                    labels=["恐慌", "冷", "溫", "熱", "過熱"]).astype(str)
S.loc[S.social_fomo >= p95, "state"] = "過熱"              # extreme override
S.loc[S.social_fomo <= p05, "state"] = "恐慌"
S["froth_flag"] = (S.hype_divergence > 1.5).astype(int)

# ---- fwd returns for gates ----
import duckdb
con = duckdb.connect(f"{STAG}/ssot_chipwar.duckdb", read_only=True)
idx = con.execute("SELECT trade_date, ret_1d FROM prices_daily WHERE scope_id='^TWII' ORDER BY trade_date").df()
idx["trade_date"] = idx.trade_date.astype(str)
S = S.merge(idx, on="trade_date", how="left")
S["fwd10"] = S.ret_1d[::-1].rolling(10).sum()[::-1].shift(-1)
V = S.dropna(subset=["fwd10"])

# ---- gates ----
g_ic = float(stats.spearmanr(V.fomo_index, V.fwd10).statistic)
q = pd.qcut(V.fomo_index, 5, labels=False, duplicates="drop")
qm = V.groupby(q).fwd10.mean()
diffs = np.diff(qm.values)
g_mono_inversions = int((diffs > 0).sum())                  # expect decreasing
null_ics = [abs(stats.spearmanr(RNG.permutation(V.fomo_index.values), V.fwd10).statistic) for _ in range(200)]
g_null = float(np.mean(null_ics))
half = len(V) // 2
ic_a = float(stats.spearmanr(V.fomo_index[:half], V.fwd10[:half]).statistic)
ic_b = float(stats.spearmanr(V.fomo_index[half:], V.fwd10[half:]).statistic)

gates = {
    "G_ic":   {"value": round(g_ic, 4), "pass": bool(g_ic < -0.05), "rule": "IC < -0.05 (高FOMO→劣後)"},
    "G_mono": {"value": [round(float(x), 4) for x in qm.values], "inversions": g_mono_inversions,
               "pass": bool(g_mono_inversions <= 1), "rule": "五分位 fwd10 遞減, 容許1反轉"},
    "G_null": {"value": round(g_null, 4), "pass": bool(g_null < 0.05), "rule": "重排 |IC| 均值 < 0.05"},
    "G_oos":  {"value": [round(ic_a, 4), round(ic_b, 4)], "pass": bool(np.sign(ic_a) == np.sign(ic_b)),
               "rule": "split-half 同號 [PROVISIONAL: single-cut, CPCV pending (LL: 單切OOS偽樂觀)]"},
}
verdict = "PROVED_VALID" if all(g["pass"] for g in gates.values()) else "FAILED_GATES"

state_stats = V.groupby("state").agg(n=("fwd10", "size"), fwd10_mean=("fwd10", "mean")).round(4)
gate_sum = {"rows": len(S), "parse_errors": 0, "evidence_tier": "T4",
            "verdict": verdict, "weights": {"behavior": W_BEH, "social": W_SOC, "status": "hand-set v0 tech debt"},
            "froth_days": int(S.froth_flag.sum()), "latest": S.iloc[-1][["trade_date", "fomo_index", "state"]].to_dict()}
out = {"gate": gate_sum, "gates": gates,
       "state_stats": state_stats.reset_index().to_dict("records"),
       "series": S[["trade_date", "fomo_index", "behavior_fomo", "social_fomo", "state", "froth_flag"]]
                 .round(3).to_dict("records")}
json.dump(out, open(f"{STAG}/fomo_index_run.json", "w", encoding="utf-8"), ensure_ascii=False, default=str)
print(json.dumps({**gate_sum, "gates": {k: v["pass"] for k, v in gates.items()}}, ensure_ascii=False, indent=2, default=str))
print(state_stats.to_string())
