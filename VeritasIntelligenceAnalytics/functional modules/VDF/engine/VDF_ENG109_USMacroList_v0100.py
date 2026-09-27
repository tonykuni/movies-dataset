#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door into the US macro lists. Read-only. Does not fetch and does not edit the intake SSOT."""
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

import json
import os
import sys
from pathlib import Path

VDF = Path(__file__).resolve().parents[1]
GAP = VDF / "VDF_USMacro_Gap_v0100.json"
ROSTER = VDF / "VDF_USMacro_Detail_Fetch_Roster_v0100.json"


def inventory() -> dict:
    gap = json.loads(GAP.read_text(encoding="utf-8"))
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    sections = {name: len(items) for name, items in roster["sections"].items()}
    return {
        "via": "vcgc",
        "door": "VDF_ENG109",
        "ssot_rows": gap["ssot_rows"],
        "ssot_unique": gap["ssot_unique_fred"],
        "detail": gap["detail_items"],
        "sections": sections,
        "gap_verified": len(gap["verified"]),
        "no_fred_id": gap["no_fred_id"],
        "anchors": gap["anchors"],
        "engines": {
            "ENG074": "VDF_ENG074_FredMacroSSOT_v0103.py",
            "ENG047": "VDF_ENG047_USMacroDetailFetcher_v0101.py",
        },
        "do_not": ["edit intake macro_ssot", "full backfill", "store FRED_API_KEY"],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "enter through via-vcgc"}, ensure_ascii=False))
        return 2
    print(json.dumps(inventory(), ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    card = inventory()
    ok = card["ssot_rows"] == 190 and card["detail"] == 43 and card["gap_verified"] == 17
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
