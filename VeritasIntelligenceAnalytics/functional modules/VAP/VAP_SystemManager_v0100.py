#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VAP downward mouth. VCGC is the only caller. This file does not install or launch engines."""
from __future__ import annotations

import os
import sys


def enter() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VAP] 拒絕。只能經 via-vcgc。")
        return 2
    print("[VAP] 對接口在。不安裝,不啟動引擎。")
    return 0


def selftest() -> int:
    old = os.environ.pop("VIA_FROM_VCGC", None)
    denied = enter()
    os.environ["VIA_FROM_VCGC"] = "YES"
    allowed = enter()
    if old is None:
        os.environ.pop("VIA_FROM_VCGC", None)
    else:
        os.environ["VIA_FROM_VCGC"] = old
    ok = denied == 2 and allowed == 0
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else enter())
