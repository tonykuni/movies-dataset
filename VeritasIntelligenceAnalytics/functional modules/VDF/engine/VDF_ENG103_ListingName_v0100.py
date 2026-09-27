#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Short names for tickers already cut from a filename. Uses ENG054's listing read."""
from __future__ import annotations
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _listings():
    spec = importlib.util.spec_from_file_location("eng054", HERE / "VDF_ENG054_TWDailyBackfill_v0108.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def names_for(net, codes: list[str]) -> dict:
    wanted = {str(code).strip() for code in codes if str(code).strip()}
    rows, per = _listings().fetch_listings(net)
    found = {}
    for row in rows:
        if row.get("code") in wanted and row["code"] not in found:
            found[row["code"]] = {
                "name": row.get("name") or "",
                "market": row.get("market"),
                "symbol": row.get("yf_ticker"),
            }
    missing = sorted(wanted - set(found))
    return {"per": per, "names": found, "missing": missing}


def selftest() -> int:
    class Net:
        def http_json(self, url):
            if "twse" in url:
                return {"state": "OK", "data": [{"公司代號": "2330", "公司簡稱": "台積電"}]}
            return {"state": "OK", "data": [{"公司代號": "6488", "公司簡稱": "環球晶"}]}
    got = names_for(Net(), ["2330", "6488", "9999"])
    ok = got["names"]["2330"]["name"] == "台積電" and got["names"]["6488"]["symbol"].endswith(".TWO") and got["missing"] == ["9999"]
    print("  [OK]" if ok else f"  [FAIL] {got}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
