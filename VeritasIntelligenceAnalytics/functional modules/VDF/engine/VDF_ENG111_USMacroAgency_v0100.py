#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door for agency sources. Read-only. Does not fetch."""
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

BOOK = Path(__file__).resolve().parents[1] / "VDF_USMacro_Agencies_v0100.json"


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    by = {a["id"]: a for a in book["agencies"]}
    bls = by["BLS"]["rows"]
    agree = [r["bls_id"] for r in bls if str(r["cross"]).startswith("AGREE")]
    irs = by["IRS"]
    tax = [r for r in by["TREASURY"]["rows"] if r.get("endpoint", "").endswith("mts_table_4")]
    return {
        "via": "vcgc",
        "door": "VDF_ENG111",
        "agencies": ["BLS", "TREASURY", "IRS"],
        "bls_cross": agree,
        "cpi_synonym": False,
        "treasury_rows": len(by["TREASURY"]["rows"]),
        "irs": irs["state"],
        "tax_lines": len(tax),
        "do_not": ["call a private IRS feed", "add the FRED deficit to the Treasury deficit", "treat CUSR0000SA0 as a synonym of CPIAUCSL"],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    card = check()
    ok = card["bls_cross"] == ["LNS14000000", "CES0000000001", "CUSR0000SA0"] and card["irs"] == "THROUGH_TREASURY" and card["tax_lines"] == 3 and card["cpi_synonym"] is False
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
