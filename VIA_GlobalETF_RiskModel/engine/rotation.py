# -*- coding: utf-8 -*-
"""
rotation.py — M22_Rotation：RRG 象限輪動（RS 水位 × RS 動能）
=============================================================================
MODULE M22_Rotation
  [MCFL-M22-C22-F220] compute_rotation — 每檔區域/風格 ETF 的象限定位與尾跡

軸定義（與 VIA_RotationEngine RRG 同語彙，軸改為價格相對強弱）：
  X = RS 水位 z   robust_z( ln(P/ACWI)[t] , 60 日窗 )
  Y = RS 動能     X(t) − X(t−10)   （ROC，領先性核心）
  加速度         Y(t) − Y(t−5)
象限（順時針 Q3→Q2→Q1→Q4）：
  Q1 領先 LEADING(X+,Y+) Q2 改善 IMPROVING★(X−,Y+)
  Q3 落後 LAGGING(X−,Y−) Q4 轉弱 WEAKENING⚠(X+,Y−)
"""
from __future__ import annotations

import math

from . import mathkit as mk


def _quadrant(rs, vel):
    if rs is None or vel is None:
        return None
    if rs > 0 and vel > 0:
        return "Q1"
    if rs <= 0 and vel > 0:
        return "Q2"
    if rs <= 0 and vel <= 0:
        return "Q3"
    return "Q4"


def compute_rotation(panel, config, uni_meta):
    """[MCFL-M22-C22-F220]"""
    spec = config["def_rotation"]
    bench = spec.get("benchmark", "ACWI")
    rs_win = int(spec.get("rs_window", 60))
    vel_win = int(spec.get("velocity_window", 10))
    acc_lag = int(spec.get("accel_lag", 5))
    quads = spec["quadrants"]
    meta = {u["ticker"]: u for u in uni_meta}

    bench_p = panel.prices(bench)
    rows = []
    for tkr in spec["tickers"]:
        p = panel.prices(tkr)
        n = min(len(p), len(bench_p))
        ratio = []
        for i in range(n):
            a, b = p[i], bench_p[i]
            ratio.append(math.log(a / b) if (a and b and a > 0 and b > 0) else None)

        def rs_z(end):
            if end < rs_win:
                return None
            sample = ratio[end - rs_win:end]
            return mk.robust_z(ratio[end], sample)

        end = n - 1
        x_now = rs_z(end)
        x_lag = rs_z(end - vel_win)
        vel = None if (x_now is None or x_lag is None) else x_now - x_lag
        x_lag2 = rs_z(end - vel_win - acc_lag)
        vel_prev = None if (x_lag is None or x_lag2 is None) else x_lag - x_lag2
        acc = None if (vel is None or vel_prev is None) else vel - vel_prev
        quad = _quadrant(x_now, vel)

        trail = []
        for back in (10, 5, 0):
            e = end - back
            xz = rs_z(e)
            xl = rs_z(e - vel_win)
            v = None if (xz is None or xl is None) else xz - xl
            if xz is not None and v is not None:
                trail.append([round(xz, 3), round(v, 3)])

        m = meta.get(tkr, {})
        rows.append({
            "ticker": tkr, "name": m.get("name", tkr),
            "region": m.get("region", "?"),
            "rs_z": None if x_now is None else round(x_now, 3),
            "velocity": None if vel is None else round(vel, 3),
            "accel": None if acc is None else round(acc, 3),
            "quadrant": quad,
            "quadrant_label": quads.get(quad, {}).get("label_zh") if quad else None,
            "action": quads.get(quad, {}).get("action") if quad else None,
            "trail": trail,
            "evidence": "Est", "truth_tier": "T3",
        })

    rows.sort(key=lambda r: -(r["velocity"] if r["velocity"] is not None else -9e9))
    counts = {}
    for r in rows:
        if r["quadrant"]:
            counts[r["quadrant"]] = counts.get(r["quadrant"], 0) + 1
    return {"rows": rows, "quadrant_counts": counts,
            "axes": {"x": "RS 水位 z（vs %s, %sd）" % (bench, rs_win),
                     "y": "RS 動能（%sd ROC）" % vel_win},
            "mcfl": spec.get("mcfl", "")}
