#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA and VCGC are one door. Not two systems."""
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
import sys

SAME = {"name": "VIA", "door": "VCGC", "via": "vcgc", "same": True}


def card() -> dict:
    return dict(SAME)


def accept(row: dict) -> bool:
    if row.get("via") != "vcgc":
        return False
    name = row.get("name")
    return name in (None, "VIA")


def main() -> int:
    print(json.dumps(card(), ensure_ascii=False))
    return 0


def selftest() -> int:
    fails = []

    def chk(name, ok):
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    got = card()
    chk("VIA is the VCGC door", got["name"] == "VIA" and got["door"] == "VCGC" and got["via"] == "vcgc" and got["same"] is True)
    chk("a vcgc card is accepted", accept({"via": "vcgc"}))
    chk("a card that names VIA is accepted", accept({"via": "vcgc", "name": "VIA"}))
    chk("a second door is refused", accept({"via": "other", "name": "VIA"}) is False)
    print(f"  [計] FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
