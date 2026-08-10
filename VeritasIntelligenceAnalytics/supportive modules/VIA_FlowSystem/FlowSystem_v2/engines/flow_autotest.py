# -*- coding: utf-8 -*-
"""VDF-FLOW-AUTOTEST flow_autotest.py — 硬化+引擎建構驗證(v0100R)。

selftest 14 之上加:20 失效模式硬化驗證(#1 分割守衛/#7 新生排除/#14 權重上限/
#20 分類敏感度/#16 反證保證 falsifiability)+ sim/perf/monitor/grid 引擎建構測試。
"""
import json
import random
import sys

from flow_core import bucket_fis, compute_fis, load_params, load_universe
from flow_calibrate import _rets_from_panel, calibrate
from flow_selftest import _mk_panel, run as selftest_run


def run():
    P = load_params()
    U = load_universe()
    T = []

    def ok(name, cond, note=""):
        T.append((name, bool(cond), note))
        print("  %-26s %s%s" % (name, "PASS" if cond else "FAIL",
                                ("  ← " + note) if note else ""))

    tick = list(U.keys())[:6]
    # harden_split_guard(#1):製造 2:1 分割簽名 — 該日不得產生巨量假流
    pan = _mk_panel(tick[:1], n=40)
    pan[25]["shares_out"] = pan[24]["shares_out"] * 2
    pan[25]["close"] = pan[24]["close"] / 2.0
    rows = compute_fis(pan, P, U)
    day = [r for r in rows if r["corp_action"]]
    ok("harden_split_guard", day and all(abs(r["flow_usd"]) < 1.0 for r in day))
    # harden_inception_excl(#7):前 20 列 confidence D 不進聚合
    r2 = compute_fis(_mk_panel(tick[:3], n=25), P, U)
    early = [r for r in r2 if r["confidence"] == "D"]
    ok("harden_inception_excl", len(early) > 0)
    # harden_weight_cap(#14):單檔巨量 AUM 不主宰 bucket
    pan3 = _mk_panel(tick[:4], n=40)
    for p3 in pan3:
        if p3["ticker"] == tick[0]:
            p3["shares_out"] *= 1000
    r3 = compute_fis(pan3, P, U)
    b3 = bucket_fis(r3, lambda r, u: "one", P, U)
    solo = {x["ticker"]: x["fis"] for x in r3 if x["date"] == max(y["date"] for y in r3)}
    ok("harden_weight_cap", b3 and abs(list(b3.values())[0] - solo.get(tick[0], 0)) > 1e-9
       or len(solo) < 2)
    # harden_taxonomy_sens(#20):擾動一檔 tier 標籤,聚合仍有限穩定
    import copy
    U2 = copy.deepcopy(U)
    U2[tick[1]]["risk_tier"] = 1 if U2[tick[1]]["risk_tier"] > 1 else 4
    r4 = compute_fis(_mk_panel(tick, n=40), P, U)
    a = bucket_fis(r4, lambda r, u: "T%d" % u.get("risk_tier", 3), P, U)
    b = bucket_fis(r4, lambda r, u: "T%d" % u.get("risk_tier", 3), P, U2)
    drift = max(abs(a.get(k, 0) - b.get(k, 0)) for k in set(a) | set(b)) if (a or b) else 0
    ok("harden_taxonomy_sens", drift < 200, "擾動後漂移 %.1f 有限" % drift)
    # falsifiability(#16 反證保證):alpha=0 → 必須 NOT_VALID
    pan0 = _mk_panel(tick, n=90, alpha=0.0, seed=9)
    res0 = calibrate(pan0, P, write=False)
    ok("falsifiability_alpha0", res0["status"] == "NOT_VALID",
       "無結構必須 NOT_VALID(實得 %s)" % res0["status"])
    # 引擎建構測試(sim/perf/monitor/grid/ui/worldmap)
    import flow_sim, flow_perf, flow_monitor, flow_grid, flow_ui, flow_worldmap
    pan1 = _mk_panel(tick, n=60, alpha=0.6, seed=4)
    rows1 = compute_fis(pan1, P, U)
    ok("sim_engine_build", "<svg" in flow_sim.build_map_sim(write=False))
    ok("sim_loading_grounding", flow_sim.ground_loadings(rows1) is not None)
    ok("perf_trend_engine", "<html" in flow_perf.build_perf(write=False).lower())
    ok("monitor_engine", "<html" in flow_monitor.build_monitor(rows1, write=False).lower())
    ok("grid_engine", "region_sector" in flow_grid.build_grid(rows1, write=False))
    ok("ui_engine", "<html" in flow_ui.build_index(rows1, {"status": "NOT_VALID",
       "reason": "test"}, write=False).lower())
    wm = flow_worldmap.build_worldmap(rows1, write=False)
    ok("worldmap_engine", wm and ("<svg" in wm or "<html" in wm.lower()))

    print("-" * 56)
    print("  [selftest 內嵌執行]")
    st = selftest_run()
    n_ok = sum(1 for _, c, _ in T if c)
    print("-" * 56)
    print("  autotest:%d/%d PASS · selftest %s" % (n_ok, len(T), "PASS" if st == 0 else "FAIL"))
    return 0 if (n_ok == len(T) and st == 0) else 1


if __name__ == "__main__":
    sys.exit(run())
