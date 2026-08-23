# -*- coding: utf-8 -*-
"""VDF-FLOW-FACTORS flow_factors.py — 因子庫(v0100R)。

從 FIS panel 導出三因子(動能/流量持續/廣度),各附自身 IC 誠實評分;
noise 因子(隨機)必須被剔除 — autotest 以此驗證因子閘不橡皮圖章。
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
import math
import random
from pathlib import Path

from flow_core import _mean, _std
from flow_validate import daily_ic

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
OUTP = ROOT / "data" / "output" / "factors.json"


def _persistence(rows):
    by_t = {}
    for r in rows:
        by_t.setdefault(r["ticker"], []).append(r)
    out = []
    for t, rs in by_t.items():
        rs = sorted(rs, key=lambda r: r["date"])
        for i in range(1, len(rs)):
            same = 1.0 if rs[i]["fis"] * rs[i - 1]["fis"] > 0 else -1.0
            out.append(dict(rs[i], fis=same * abs(rs[i]["fis"])))
    return out


def _breadth(rows):
    by_d = {}
    for r in rows:
        by_d.setdefault(r["date"], []).append(r)
    out = []
    for d, rs in by_d.items():
        b = _mean([1.0 if x["fis"] > 0 else -1.0 for x in rs]) * 100.0
        for x in rs:
            out.append(dict(x, fis=b))
    return out


def build_factors(rows, rets_fwd, min_t=2.0, include_noise_probe=False, seed=11):
    """回 {kept:[{name,ic,t}], rejected:[...]};閘=|t|≥min_t(統計顯著,小樣本隨機不過);
    noise probe 供 selftest/autotest 驗剔除不橡皮圖章。"""
    cands = {"fis_momentum": rows, "flow_persistence": _persistence(rows),
             "flow_breadth": _breadth(rows)}
    if include_noise_probe:
        rng = random.Random(seed)
        cands["noise_probe"] = [dict(r, fis=rng.uniform(-100, 100)) for r in rows]
    kept, rejected = [], []
    for name, rs in cands.items():
        ics = daily_ic(rs, rets_fwd) or [0.0]
        ic = _mean(ics)
        sd = _std(ics)
        t = (ic / (sd / math.sqrt(len(ics)))) if len(ics) > 2 and sd > 1e-12 else 0.0
        rec = {"name": name, "ic": round(ic, 4), "t": round(t, 2)}
        (kept if abs(t) >= min_t else rejected).append(rec)
    result = {"version": "v0100R", "kept": kept, "rejected": rejected}
    OUTP.parent.mkdir(parents=True, exist_ok=True)
    OUTP.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return result
