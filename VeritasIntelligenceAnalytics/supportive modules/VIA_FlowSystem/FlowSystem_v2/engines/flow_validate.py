# -*- coding: utf-8 -*-
"""VALIDATE-12 flow_validate.py — IC/decay/quantile/long-short/null + gate 評估(v0100R)。

Gates:G002 null · G003 IC/ICIR/t · G004 quantile 單調 · G008 LS Sharpe(扣成本)
     G009 OOS 確認(calibrate 段執行)· G010 lead_ratio · G011 Newey-West HAC t。
誠實原則:訊號缺結構時必須紅 — 反證保證(synthetic.alpha=0 → NOT_VALID)。
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
import math
import random

from flow_core import _mean, _std


def _rank(xs):
    order = sorted(range(len(xs)), key=lambda i: xs[i])
    rk = [0.0] * len(xs)
    for pos, i in enumerate(order):
        rk[i] = pos
    return rk


def rank_ic(sig, fwd):
    """Spearman-style rank correlation(零依賴)。"""
    pairs = [(s, f) for s, f in zip(sig, fwd)
             if s is not None and f is not None and math.isfinite(s) and math.isfinite(f)]
    if len(pairs) < 3:
        return None
    a = _rank([p[0] for p in pairs])
    b = _rank([p[1] for p in pairs])
    ma, mb = _mean(a), _mean(b)
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    den = math.sqrt(sum((x - ma) ** 2 for x in a) * sum((y - mb) ** 2 for y in b))
    return num / den if den > 1e-12 else 0.0


def _panel_by_date(rows, rets):
    """rows: fis rows;rets: {(date,ticker): fwd_ret(下一日,#9 look-ahead shift 已由呼叫端保證)}"""
    by_d = {}
    for r in rows:
        k = (r["date"], r["ticker"])
        if k in rets:
            by_d.setdefault(r["date"], []).append((r["fis"], rets[k]))
    return by_d


def daily_ic(rows, rets):
    by_d = _panel_by_date(rows, rets)
    ics = []
    for d in sorted(by_d):
        ic = rank_ic([x[0] for x in by_d[d]], [x[1] for x in by_d[d]])
        if ic is not None:
            ics.append(ic)
    return ics


def hac_t(ics, lags=5):
    """#11 Newey-West HAC t 值(自相關校正;誠實降低)。"""
    n = len(ics)
    if n < 8:
        return 0.0
    mu = _mean(ics)
    e = [x - mu for x in ics]
    g0 = sum(x * x for x in e) / n
    s = g0
    for L in range(1, min(lags, n - 1) + 1):
        gl = sum(e[i] * e[i - L] for i in range(L, n)) / n
        s += 2.0 * (1.0 - L / (lags + 1.0)) * gl
    se = math.sqrt(max(s, 1e-12) / n)
    return mu / se if se > 1e-12 else 0.0


def quantile_check(rows, rets, q=5):
    """G004:訊號五分位之前瞻報酬單調性(頂-底同號遞增即過)。"""
    by_d = _panel_by_date(rows, rets)
    tops, bots = [], []
    for d, xs in by_d.items():
        if len(xs) < q:
            continue
        xs = sorted(xs, key=lambda p: p[0])
        k = len(xs) // q
        bots.append(_mean([p[1] for p in xs[:k]]))
        tops.append(_mean([p[1] for p in xs[-k:]]))
    if not tops:
        return False, 0.0
    spread = _mean(tops) - _mean(bots)
    return spread > 0, spread


def long_short(rows, rets, cost_bps=5, q=5):
    """G008:頂減底做多做空日報酬 → 年化 Sharpe(扣成本)。"""
    by_d = _panel_by_date(rows, rets)
    pnl = []
    for d in sorted(by_d):
        xs = sorted(by_d[d], key=lambda p: p[0])
        k = len(xs) // q
        if k < 1:
            continue
        pnl.append(_mean([p[1] for p in xs[-k:]]) - _mean([p[1] for p in xs[:k]])
                   - 2.0 * cost_bps / 10000.0)
    if len(pnl) < 8:
        return 0.0
    sd = _std(pnl)
    return (_mean(pnl) / sd) * math.sqrt(252.0) if sd > 1e-12 else 0.0


def null_test(rows, rets, k=15, seed=7):
    """G002:K 次日期內置換 null — 真 IC 需超越 null 分布(p 值)。"""
    real = _mean(daily_ic(rows, rets) or [0.0])
    rng = random.Random(seed)
    by_d = _panel_by_date(rows, rets)
    beat = 0
    for _ in range(k):
        ics = []
        for d, xs in by_d.items():
            sig = [p[0] for p in xs]
            fwd = [p[1] for p in xs]
            rng.shuffle(sig)
            ic = rank_ic(sig, fwd)
            if ic is not None:
                ics.append(ic)
        if abs(_mean(ics or [0.0])) >= abs(real):
            beat += 1
    return {"real_ic": real, "null_p": beat / float(k)}


def lead_ratio(rows, rets_fwd, rets_same):
    """G010 反身性分解:預測 IC vs 同期 IC — lead = |pred| / (|pred|+|same|)。"""
    icf = _mean(daily_ic(rows, rets_fwd) or [0.0])
    ics = _mean(daily_ic(rows, rets_same) or [0.0])
    den = abs(icf) + abs(ics)
    return abs(icf) / den if den > 1e-12 else 0.0


def evaluate(rows, rets_fwd, rets_same=None, params=None):
    """全 gate 評估 → {gates:{...}, passed, failed:[...], metrics}。"""
    from flow_core import load_params
    p = params or load_params()
    g = p.get("gates", {})
    ics = daily_ic(rows, rets_fwd)
    ic = _mean(ics or [0.0])
    icir = (ic / _std(ics)) if len(ics) > 2 and _std(ics) > 1e-12 else 0.0
    t = (ic / (_std(ics) / math.sqrt(len(ics)))) if len(ics) > 2 and _std(ics) > 1e-12 else 0.0
    thac = hac_t(ics)
    mono, spread = quantile_check(rows, rets_fwd)
    sharpe = long_short(rows, rets_fwd, cost_bps=float(g.get("G008_cost_bps", 5)))
    nul = null_test(rows, rets_fwd, k=int((p.get("calibration", {}) or {}).get("null_permutations", 15)))
    lead = lead_ratio(rows, rets_fwd, rets_same) if rets_same else None
    gates = {
        "G002_null": nul["null_p"] <= float(g.get("G002_null_p", 0.10)),
        "G003_ic": ic >= float(g.get("G003_ic_min", 0.02)),
        "G003_icir": icir >= float(g.get("G003_icir_min", 0.5)),
        "G003_t": t >= float(g.get("G003_t_min", 2.0)),
        "G004_quantile": bool(mono),
        "G008_ls_sharpe": sharpe >= float(g.get("G008_ls_sharpe_min", 0.5)),
        "G011_thac": thac >= float(g.get("G011_thac_min", 2.0)),
    }
    if lead is not None:
        gates["G010_lead"] = lead >= float(g.get("G010_lead_min", 0.5))
    failed = [k for k, v in gates.items() if not v]
    return {"gates": gates, "passed": not failed, "failed": failed,
            "metrics": {"ic": round(ic, 4), "icir": round(icir, 3), "t": round(t, 2),
                        "t_hac": round(thac, 2), "quantile_spread": round(spread, 6),
                        "ls_sharpe": round(sharpe, 2), "null_p": nul["null_p"],
                        "lead_ratio": (round(lead, 3) if lead is not None else None),
                        "n_days": len(ics)}}
