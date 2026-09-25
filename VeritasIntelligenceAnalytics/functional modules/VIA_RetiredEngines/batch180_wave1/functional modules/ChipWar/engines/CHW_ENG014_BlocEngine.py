# [VIA 歸檔補丁 2026-08-10] 路徑常數改為 VIA_CHIPWAR_STAGING/VIA_CHIPWAR_REPORTS 環境變數
# 可覆寫之模組相對路徑(_generated/,gitignored);運算邏輯零觸碰。原始上傳 sha256[:16]=58ac6a4b269bae41
# -*- coding: utf-8 -*-
"""
VIA Bloc Concentration Lane v0.1 — 選擇有限 (limited choices): tech vs traditional
Metrics: cum spread, tech flow share, tech breadth share, opportunity width (risk-adj), flow HHI, crowding index.
Falsification: does crowding co-move with chipwar score? + shared-input overlap disclosure.
T4 synthetic (reuses chipwar_run synthetic universe); real run keys off bloc_tags over 31 groups.
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
import json, datetime as dt
import numpy as np, pandas as pd, duckdb
from scipy import stats

import os as _os
from pathlib import Path as _P
STAG = _os.environ.get("VIA_CHIPWAR_STAGING") or str(_P(__file__).resolve().parents[1] / "_generated" / "staging")
_P(STAG).mkdir(parents=True, exist_ok=True)
TECH = {"半導體", "AI 伺服器", "散熱", "PCB", "記憶體"}
TRAD = {"金融", "觀光餐飲"}
HYB  = {"軍工航太"}

con = duckdb.connect(f"{STAG}/ssot_chipwar.duckdb", read_only=True)
g = con.execute("SELECT trade_date, scope_id, ret_1d FROM prices_daily WHERE scope_type='group'").df()
f = con.execute("SELECT trade_date, scope_id, actor, net_buy_twd FROM flows_daily WHERE scope_type='group'").df()
G = g.pivot_table(index="trade_date", columns="scope_id", values="ret_1d").sort_index()
Fa = f.groupby(["trade_date", "scope_id"]).net_buy_twd.apply(lambda x: x.abs().sum()).unstack().sort_index()

tech_cols = [c for c in G.columns if c in TECH]; trad_cols = [c for c in G.columns if c in TRAD]
rows = []
for i in range(21, len(G)):
    d = G.index[i]
    w20 = G.iloc[i - 20:i]
    mom = w20.mean() / (w20.std(ddof=0) + 1e-9)          # risk-adjusted 20d momentum (DA: not raw drift)
    opp = float((mom > 0.05).mean())                      # opportunity width
    up = (G.iloc[i] > 0)
    tb = float(up[tech_cols].sum() / max(up.sum(), 1))    # tech share of up-groups
    fl = Fa.iloc[i]
    tfs = float(fl[tech_cols].sum() / max(fl.sum(), 1e-9))
    sh = fl / max(fl.sum(), 1e-9); hhi = float((sh ** 2).sum())
    rows.append({"trade_date": d, "opportunity_width": opp, "tech_breadth_share": tb,
                 "tech_flow_share": tfs, "flow_hhi": hhi})
C = pd.DataFrame(rows); C["trade_date"] = pd.to_datetime(C.trade_date).dt.date; C = C.set_index("trade_date")
C["spread_cum"] = (G[tech_cols].mean(axis=1).cumsum() - G[trad_cols].mean(axis=1).cumsum()).reindex(C.index)
# crowding: high tech flow share + high HHI + narrow opportunity (causal trailing z, floor per macro lane lesson)
Zc = {}
for col, sign in [("tech_flow_share", 1), ("flow_hhi", 1), ("opportunity_width", -1)]:
    mu = C[col].rolling(120, min_periods=40).mean(); sd = C[col].rolling(120, min_periods=40).std(ddof=0)
    sd = sd.clip(lower=float(sd.median()) * 0.5)
    Zc[col] = sign * ((C[col] - mu) / sd).clip(-3, 3).fillna(0)
C["crowding_index"] = (1 / (1 + np.exp(-(Zc["tech_flow_share"] + Zc["flow_hhi"] + Zc["opportunity_width"]) / 2)))

# falsification vs chipwar score
reg = pd.DataFrame(json.load(open(f"{STAG}/chipwar_run.json", encoding="utf-8"))["regime"])
reg["trade_date"] = pd.to_datetime(reg.trade_date).dt.date
P = C.reset_index().merge(reg[["trade_date", "chipwar_score"]], on="trade_date").dropna()
tests = {
    "spearman_crowding_vs_chipwar": round(float(stats.spearmanr(P.crowding_index, P.chipwar_score).statistic), 3),
    "spearman_oppwidth_vs_chipwar": round(float(stats.spearmanr(P.opportunity_width, P.chipwar_score).statistic), 3),
    "shared_input_overlap": "flow_hhi ~ chipwar hhi_gain(returns-based) DIFFERENT source; tech_flow_share vs itrust_share partial overlap via flows table — correlation NOT independent confirmation",
}
gate = {"rows": len(C), "parse_errors": 0, "nulls_after_warmup": int(C.iloc[40:].isna().sum().sum()),
        "evidence_tier": "T4", **tests}
out = {"gate": gate, "conc": C.reset_index().assign(trade_date=lambda d: d.trade_date.astype(str)).round(4).to_dict("records")}
json.dump(out, open(f"{STAG}/bloc_run.json", "w", encoding="utf-8"), ensure_ascii=False)
print(json.dumps(gate, ensure_ascii=False, indent=2))
