# -*- coding: utf-8 -*-
"""VDF-FLOW-ROLES flow_roles.py — monitor_role 閘門 + 分類存取(v0100R)。

單一事實源:universe.json 之 monitor_role/risk_tier/asset_class/region;
期貨/FX positioning 不進現貨流量池(GRAM/bucket 聚合皆經此閘)。
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
from flow_core import load_universe


def spot_only(rows, universe=None):
    uni = universe or load_universe()
    return [r for r in rows if uni.get(r["ticker"], {}).get("monitor_role", "spot") == "spot"]


def by_tier(universe=None):
    uni = universe or load_universe()
    out = {}
    for t, u in uni.items():
        out.setdefault("T%d" % u.get("risk_tier", 3), []).append(t)
    return out


def by_region(universe=None):
    uni = universe or load_universe()
    out = {}
    for t, u in uni.items():
        out.setdefault(u.get("region", "US"), []).append(t)
    return out


def by_class(universe=None):
    uni = universe or load_universe()
    out = {}
    for t, u in uni.items():
        out.setdefault(u.get("asset_class", "equity"), []).append(t)
    return out


def fidelity_classes(universe=None):
    """Fidelity 評分卡分群(README v0104 三分頁之三):asset_class×backing。"""
    uni = universe or load_universe()
    out = {}
    for t, u in uni.items():
        key = "%s/%s" % (u.get("asset_class", "?"), u.get("backing", "physical"))
        out.setdefault(key, []).append(u)
    return out
