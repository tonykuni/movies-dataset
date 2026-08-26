# -*- coding: utf-8 -*-
# ⚠⚠ T4 佔位鏈頭 PLACEHOLDER CHAIN HEAD ⚠⚠
# 真正的 via_chipwar_engine.py 未在 2026-08-10 上傳批次中;本檔由 VIA 歸檔程序依
# CHW_ENG023_TestHarness.py 的 I/O 契約(chipwar_run.json: regime/ic_groups/gate;
# ssot_chipwar.duckdb: prices_daily/flows_daily)重建之 T4 合成宇宙產生器,
# 僅供下游 lane(macro/bloc/social/fomo_index/xmkt)煙測與 harness 驗收。
# 依 SSOT 治理:「T4 synthetic placeholder for pipeline testing - MUST NOT enter
# live decisions」。真鏈頭上傳後,version-forward 取代本檔即可,下游零改動。
"""
VIA ChipWar Chain Head (T4 placeholder) — 合成宇宙 + regime
產出:
  staging/ssot_chipwar.duckdb  — prices_daily(31 族群 + ^TWII) · flows_daily(4 主體×族群)
  staging/chipwar_run.json     — {"regime":[...含 chipwar_score], "ic_groups":[...], "gate":{...}}
嵌入故事(T4 embedded truth):
  phase1(→2025-11-15) 資金盤:廣度寬、流量分散、chipwar_score 低
  phase2(2025-11-15→) 籌碼戰:tech 集中上攻、trad 走平、流量集中投信、score 高
族群清單讀 ssot/SSOT_ChipWar_Schema.json 之 bloc_tags(19 tech + 8 trad + 4 hybrid = 31)。
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
import datetime as dt
import json
import os
from pathlib import Path

import numpy as np
import pandas as pd
import duckdb

STAG = os.environ.get("VIA_CHIPWAR_STAGING") or str(
    Path(__file__).resolve().parents[1] / "_generated" / "staging")
Path(STAG).mkdir(parents=True, exist_ok=True)
SSOT = Path(__file__).resolve().parents[1] / "ssot" / "SSOT_ChipWar_Schema.json"

RNG = np.random.default_rng(20250408)
T0, T1_ = dt.date(2025, 4, 8), dt.date(2026, 7, 9)   # 與 macro/social lane 同窗
BRK = dt.date(2025, 11, 15)

schema = json.loads(SSOT.read_text(encoding="utf-8"))
tags = schema["bloc_tags"]
TECH, TRAD, HYB = tags["tech"], tags["traditional"], tags["hybrid_ai_adjacent"]
GROUPS = TECH + TRAD + HYB
ACTORS = ["foreign", "invest_trust", "dealer", "margin_retail"]

days = pd.bdate_range(T0, T1_).date
n = len(days)
brk = next(i for i, d in enumerate(days) if d >= BRK)
phase2 = np.arange(n) >= brk

# ---- 族群日報酬:市場因子 + 相位相依 bloc 因子 + 個群雜訊 ----
mkt = RNG.normal(0.0004, 0.008, n)
tech_f = RNG.normal(0.0006, 0.010, n) + np.where(phase2, 0.0016, 0.0)
trad_f = RNG.normal(0.0005, 0.007, n) - np.where(phase2, 0.0009, 0.0)
hyb_f = 0.5 * tech_f + 0.3 * trad_f
price_rows, flow_rows = [], []
group_rets = {}
for gname in GROUPS:
    base = tech_f if gname in TECH else (trad_f if gname in TRAD else hyb_f)
    beta = RNG.uniform(0.75, 1.25)
    ret = mkt + beta * base + RNG.normal(0, 0.009, n)
    group_rets[gname] = ret
    close = 100.0 * np.exp(np.cumsum(ret))
    for i, d in enumerate(days):
        price_rows.append((d, "group", gname, float(ret[i]), float(close[i]),
                           float(abs(RNG.normal(2.5e9, 8e8))), "T4"))

# ^TWII = 全群等權(市值加權簡化)
twii = np.mean(np.column_stack(list(group_rets.values())), axis=1) + RNG.normal(0, 0.002, n)
close = 20000.0 * np.exp(np.cumsum(twii))
for i, d in enumerate(days):
    price_rows.append((d, "index", "^TWII", float(twii[i]), float(close[i]),
                       float(abs(RNG.normal(4.0e11, 6e10))), "T4"))

# ---- 法人流量:phase2 集中 tech(投信主導),否則分散 ----
for i, d in enumerate(days):
    hot = phase2[i]
    for gname in GROUPS:
        is_tech = gname in TECH
        for actor in ACTORS:
            scale = 1.0
            if hot and is_tech and actor == "invest_trust":
                scale = 4.0                              # 籌碼戰:投信集中 tech
            elif hot and not is_tech:
                scale = 0.45                             # 非 tech 流量枯竭
            net = RNG.normal(0, 2.2e8) * scale + (6e7 if (hot and is_tech) else 0)
            flow_rows.append((d, "group", gname, actor, float(net), "T4"))

# ---- duckdb 落地(staging 可再生:覆寫)----
db_path = Path(STAG) / "ssot_chipwar.duckdb"
if db_path.exists():
    db_path.unlink()
con = duckdb.connect(str(db_path))
con.execute("""CREATE TABLE prices_daily(
    trade_date DATE, scope_type VARCHAR, scope_id VARCHAR, ret_1d DOUBLE,
    close_adj DOUBLE, volume_twd DOUBLE, evidence_tier VARCHAR)""")
con.execute("""CREATE TABLE flows_daily(
    trade_date DATE, scope_type VARCHAR, scope_id VARCHAR, actor VARCHAR,
    net_buy_twd DOUBLE, evidence_tier VARCHAR)""")
pdf = pd.DataFrame(price_rows, columns=["trade_date", "scope_type", "scope_id",
                                        "ret_1d", "close_adj", "volume_twd", "evidence_tier"])
fdf = pd.DataFrame(flow_rows, columns=["trade_date", "scope_type", "scope_id",
                                       "actor", "net_buy_twd", "evidence_tier"])
con.execute("INSERT INTO prices_daily SELECT * FROM pdf")
con.execute("INSERT INTO flows_daily SELECT * FROM fdf")
con.close()

# ---- regime:chipwar_score = 相位邏輯斯蒂 + 集中度訊號 ----
ramp = 1.0 / (1.0 + np.exp(-(np.arange(n) - brk) / 18.0))
score = np.clip(ramp + RNG.normal(0, 0.04, n), 0.0, 1.0)
up = np.column_stack([group_rets[g] > 0 for g in GROUPS])
breadth = up.mean(axis=1)
regime = []
for i, d in enumerate(days):
    regime.append({
        "trade_date": str(d), "run_id": "t4_placeholder_20260810",
        "breadth_z": round(float((breadth[i] - breadth.mean()) / (breadth.std() + 1e-9)), 4),
        "corr_z": round(float(RNG.normal(0.8 if phase2[i] else -0.3, 0.3)), 4),
        "foreign_share_z": round(float(RNG.normal(-0.5 if phase2[i] else 0.6, 0.3)), 4),
        "itrust_share_z": round(float(RNG.normal(1.1 if phase2[i] else -0.2, 0.3)), 4),
        "hhi_gain_z": round(float(RNG.normal(0.9 if phase2[i] else -0.4, 0.3)), 4),
        "margin_breadth_z": round(float(RNG.normal(0.5 if phase2[i] else 0.0, 0.3)), 4),
        "chipwar_score": round(float(score[i]), 4),
        "dominant_actor": "invest_trust" if phase2[i] else "foreign",
        "evidence_tier": "T4",
    })

# ---- ic_groups:clean/leaky 雙模 + 正交化欄位(供 harness L2 斷言)----
ic_groups = []
for gname in GROUPS:
    for mode in ("clean", "leaky"):
        base_ic = RNG.normal(0.06 if gname in TECH else 0.01, 0.02)
        leak_boost = 0.25 if mode == "leaky" else 0.0    # 洩漏模式虛胖 — 隔離展示用
        ic_groups.append({
            "scope_id": gname, "actor": "invest_trust", "mode": mode,
            "window_days": 60, "fwd_horizon_days": 5,
            "spearman_ic": round(float(base_ic + leak_boost), 4),
            "spearman_ic_orth": round(float(base_ic * 0.6), 4),
            "n_obs": int(n - 60), "evidence_tier": "T4",
        })

gate = {"rows_prices": len(price_rows), "rows_flows": len(flow_rows),
        "n_groups": len(GROUPS), "parse_errors": 0, "evidence_tier": "T4",
        "placeholder_chain_head": True,
        "note": "真 via_chipwar_engine 未上傳;本檔為依 harness 契約重建之 T4 佔位鏈頭"}
out = {"gate": gate, "regime": regime, "ic_groups": ic_groups}
json.dump(out, open(Path(STAG) / "chipwar_run.json", "w", encoding="utf-8"),
          ensure_ascii=False)
print(json.dumps(gate, ensure_ascii=False, indent=2))
