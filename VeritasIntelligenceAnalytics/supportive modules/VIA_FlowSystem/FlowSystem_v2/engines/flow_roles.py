# -*- coding: utf-8 -*-
"""VDF-FLOW-ROLES flow_roles.py — monitor_role 閘門 + 分類存取(v0100R)。

單一事實源:universe.json 之 monitor_role/risk_tier/asset_class/region;
期貨/FX positioning 不進現貨流量池(GRAM/bucket 聚合皆經此閘)。
"""
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
