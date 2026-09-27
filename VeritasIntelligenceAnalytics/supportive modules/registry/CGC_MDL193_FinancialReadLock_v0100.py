#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Financial rows are labeled observations. Actual covers forecast. Disagreements are not rewritten."""
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
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
READ = VIA / "functional modules" / "VRN" / "VRN_ENG112_FinancialRead_v0100.py"


def check() -> dict:
    text = READ.read_text(encoding="utf-8") if READ.is_file() else ""
    missing = [name for name in ("forecast_covered", "discuss:add_sub", "discuss:division", "report_observation") if name not in text]
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_FinancialReadLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [],
        "policy": "actual covers forecast",
        "vdf": "support only; a conflict is discussed",
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "treat a broker figure as historical truth",
            "rewrite a figure that failed add_sub or division",
            "invent a financial value",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the drift",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    card = check()
    print("  [OK]" if card["lock_success"] else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
