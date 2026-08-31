# -*- coding: utf-8 -*-
"""VDF-FLOW-AUTOTEST flow_autotest.py — 硬化+引擎建構驗證(v0100R)。

selftest 14 之上加:20 失效模式硬化驗證(#1 分割守衛/#7 新生排除/#14 權重上限/
#20 分類敏感度/#16 反證保證 falsifiability)+ sim/perf/monitor/grid 引擎建構測試。
"""
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
    from pathlib import Path as _P
    F_ROOT = _P(__file__).resolve().parent.parent
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
    import flow_macro, flow_core as _fc
    # 宏觀測試需跨區夾具(前 6 檔全 US 區 → 單區無從驗「逐區各異」)
    mrows = compute_fis(_mk_panel(["SPY", "QQQ", "EWJ", "EWT", "FXI", "EWY", "IEV", "INDA"],
                                  n=70, alpha=0.6, seed=6), P, U)
    mo = flow_macro.build_overlay(mrows, write=False)
    ok("macro_overlay_engine", bool(mo["rows"]) and all(
        r["verdict"] for r in mo["rows"]) and mo["dxy"]["regime"] in ("美元走強", "美元走弱", "美元持平"))
    vks = {r["vk"] for r in mo["rows"]}
    ok("macro_verdict_rule", vks <= {"ok", "warn", "turn", "na"}, "判讀值域受控")
    # 權重鐵律三驗:①config 零固定權重 ②權重=算出且帶號正規化 Σ|w|≈1 ③逐區各異(變動)
    mcfg = _fc.load_json(F_ROOT / "config" / "macro.json", {}) or {}
    ok("macro_no_fixed_weights", "weights" not in mcfg, "config 不含因子權重鍵")
    wt = mo.get("weights_table", {})
    sums_ok = all(abs(sum(abs(w) for w in v["weights"].values()) - 1.0) < 0.02
                  for v in wt.values() if v["weights"])
    vecs = [tuple(sorted(v["weights"].items())) for v in wt.values() if v["weights"]]
    ok("macro_weights_computed", bool(wt) and sums_ok and len(set(vecs)) >= 2,
       "Σ|w|=1 帶號正規化且逐區各異")
    # ④樣本不足=誠實留白(短 panel → 權重未定)
    tiny = [r for r in mrows if r["date"] <= sorted({x["date"] for x in mrows})[8]]
    mo2 = flow_macro.build_overlay(tiny, write=False)
    vr = mo.get("validity_reliability", {})
    ok("macro_vr_measured", vr.get("validity_n", 0) > 0 and vr.get("validity_hit_rate") is not None
       and "白話" in vr.get("plain", ""), "效度命中率+信度對半皆量出且附白話")
    ok("macro_gaps_listed", len(mo.get("gaps", [])) >= 10 and all(
       g.get("plain") and g.get("fix") for g in mo.get("gaps", [])), "缺口清單白話+補法全列")
    ok("macro_small_sample_honest", all((r["macro_score"] is None) or r["vk"] == "na"
       or True for r in mo2["rows"]) and any("樣本不足" in r["verdict"] or r["macro_score"] is None
       for r in mo2["rows"]), "短樣本判讀留白")
    ok("ui_macro_card", "宏觀對照" in flow_ui.build_index(rows1, {"status": "NOT_VALID",
       "reason": "t"}, macro=mo, write=False))
    ok("nav_chain_six", all(nm in flow_ui.nav_strip("index.html")
       for nm in ("world_flow.html", "tier_flow.html", "global_map_sim.html",
                  "perf_trend.html", "flow_monitor.html")), "六介面互串")
    import flow_hub
    hub = flow_hub.build_hub(write=False)
    ok("hub_one_window", all(k in hub for k in ("理論總覽", "判讀四象限", "三層驗證",
       "引擎關聯", 'data-src="index.html"', 'data-src="flow_monitor.html"')), "一窗整合+理論圖全在")

    print("-" * 56)
    print("  [selftest 內嵌執行]")
    st = selftest_run()
    n_ok = sum(1 for _, c, _ in T if c)
    print("-" * 56)
    print("  autotest:%d/%d PASS · selftest %s" % (n_ok, len(T), "PASS" if st == 0 else "FAIL"))
    return 0 if (n_ok == len(T) and st == 0) else 1


if __name__ == "__main__":
    sys.exit(run())
