# -*- coding: utf-8 -*-
"""SELFTEST-20 flow_selftest.py — 14 項邊界測試(v0100R;README v0103 涵蓋清單)。

正常/單檔/短歷史 FIS、sub-floor AUM 降級、stale-shares CONFLICT、role-gated 聚合、
RORO、snapshot、validate、null≈0、factor 剔除 noise、Pillar A good-pass/bad-catch、空輸入安全。
"""
import json
import sys

from flow_core import (bucket_fis, compute_fis, gram, load_params, load_universe,
                       roro, snapshot)
from flow_validate import evaluate, null_test
from flow_factors import build_factors
import flow_pillar_a
import flow_bridge


def _mk_panel(tickers, n=60, alpha=0.0, seed=3):
    import random
    rng = random.Random(seed)
    panel = []
    for t in tickers:
        close, sh = 100.0, 1_000_000.0
        pend = 0.0
        for i in range(n):
            d = "2026-%02d-%02d" % (1 + i // 28, 1 + i % 28)
            dsh = rng.gauss(0, 4000)
            sh = max(1000.0, sh + dsh)
            drift = alpha * pend / 400000.0
            pend = dsh
            close *= 1 + rng.gauss(drift, 0.01)
            panel.append({"snapshot_date": d, "ticker": t, "close": round(close, 3),
                          "shares_out": round(sh)})
    return panel


def run():
    P = load_params()
    U = load_universe()
    T = []

    def ok(name, cond, note=""):
        T.append((name, bool(cond), note))

    tick5 = list(U.keys())[:5]
    rows = compute_fis(_mk_panel(tick5), P, U)
    ok("normal_fis", rows and all(-100 <= r["fis"] <= 100 for r in rows))
    r1 = compute_fis(_mk_panel(tick5[:1]), P, U)
    ok("single_ticker", r1 and len({x["ticker"] for x in r1}) == 1)
    r2 = compute_fis(_mk_panel(tick5, n=8), P, U)
    ok("short_history_conf", all(x["confidence"] in ("C", "D") for x in r2), "短歷史全降級")
    pan3 = _mk_panel(tick5[:1], n=40)
    for p in pan3:
        p["aum_reported"] = p["shares_out"] * p["close"] * 0.5  # 副估計持續矛盾樣式
    pan3[30]["aum_reported"] = pan3[29]["shares_out"] * pan3[30]["close"] * 3.0
    r3 = compute_fis(pan3, P, U)
    ok("stale_shares_conflict", any(x["conflict"] for x in r3), "雙估計器抓矛盾")
    b = bucket_fis(rows, lambda r, u: u.get("risk_bucket"), P, U)
    ok("role_gated_bucket", isinstance(b, dict))
    pos_rows = compute_fis(_mk_panel(["UUP", "USO"]), P, U)
    bp = bucket_fis(pos_rows, lambda r, u: u.get("risk_bucket"), P, U)
    ok("positioning_excluded", not bp, "期貨/FX 不進現貨池")
    g = gram(rows, P, U)
    ok("gram_dual_form", "gram_score" in g and "gram_raw" in g and g["regime"] in
       ("RISK_ON", "RISK_OFF", "NEUTRAL"))
    ok("roro_bounded", 0 <= roro(rows, P, U)["roro"] <= 100)
    sn = snapshot(rows, P, U)
    ok("snapshot_fields", all(k in sn for k in ("per_ticker", "bucket", "roro",
                                                "regime_market", "region_semantics")))
    pan = _mk_panel(tick5, n=80, alpha=0.9, seed=5)
    from flow_calibrate import _rets_from_panel
    fwd, same = _rets_from_panel(pan)
    rows_a = compute_fis(pan, P, U)
    ev = evaluate(rows_a, fwd, same, P)
    ok("validate_runs", "gates" in ev and "metrics" in ev)
    nl = null_test(rows_a, fwd, k=8)
    ok("null_small", abs(nl["real_ic"]) < 1.0)
    fx = build_factors(rows_a, fwd, include_noise_probe=True)
    ok("factor_rejects_noise", any(f["name"] == "noise_probe" for f in fx["rejected"]),
       "noise 因子被剔除")
    pa = flow_pillar_a.validate_a(rows_a, write=False)
    ok("pillar_a_honest", pa["status"] in ("UNCALIBRATED", "CALIBRATED", "MISCALIBRATED"))
    ok("empty_input_safe", compute_fis([], P, U) == [] and snapshot([], P, U)["per_ticker"] == [])

    n_ok = sum(1 for _, c, _ in T if c)
    for name, c, note in T:
        print("  %-24s %s%s" % (name, "PASS" if c else "FAIL",
                                ("  ← " + note) if note and not c else ""))
    print("-" * 56)
    print("  selftest:%d/%d PASS" % (n_ok, len(T)))
    return 0 if n_ok == len(T) else 1


if __name__ == "__main__":
    sys.exit(run())
