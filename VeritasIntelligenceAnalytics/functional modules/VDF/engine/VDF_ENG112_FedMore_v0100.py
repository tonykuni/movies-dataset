#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door for the extra Fed series. Read-only."""
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
import json, os, sys
from pathlib import Path
BOOK = Path(__file__).resolve().parents[1] / "VDF_USMacro_FedMore_v0100.json"

def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ids = [r["fred_id"] for r in book["add"]]
    return {
        "via": "vcgc", "door": "VDF_ENG112",
        "added": len(ids), "ids": ids,
        "already": len(book["already_in_parent"]),
        "stale": [r["fred_id"] for r in book["stale"]],
        "intake_edited": False,
        "do_not": ["fetch DISCBORR", "edit intake macro_ssot", "full backfill"],
        "next": "none",
    }

def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False)); return 2
    print(json.dumps(check(), ensure_ascii=False, indent=1)); return 0

def selftest() -> int:
    card = check()
    ok = card["added"] == 15 and card["stale"] == ["DISCBORR"] and len(set(card["ids"])) == 15
    print("  [OK]" if ok else "  [FAIL]"); return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
