#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AKShare probe. Refuses a raw python call. The central launcher must enter first."""
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
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("ak_v0101", HERE / "VDF_ENG110_AKShareProbe_v0101.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def allowed() -> bool:
    return os.environ.get("VIA_CENTRAL_ENTRY") == "1" and os.environ.get("VIA_FROM_VCGC") == "YES"


def main() -> int:
    if not allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-akshare through Invoke-VIAPython"}, ensure_ascii=False))
        return 2
    card = _prior().probe()
    card["door"] = "VDF_ENG110_AKShareProbe_v0102"
    card["enter"] = "vcgc"
    card["exit"] = "vcgc"
    card["central"] = True
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["installed"] else 2


def selftest() -> int:
    os.environ.pop("VIA_CENTRAL_ENTRY", None)
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = not allowed()
    os.environ["VIA_CENTRAL_ENTRY"] = "1"
    still = not allowed()
    os.environ["VIA_FROM_VCGC"] = "YES"
    opened = allowed()
    ok = denied and still and opened
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
