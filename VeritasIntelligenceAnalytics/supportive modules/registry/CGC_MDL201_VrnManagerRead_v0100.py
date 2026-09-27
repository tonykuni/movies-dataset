#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the VRN manager reading. Do not run the body and do not replace v0104 or v0105.

The tail is v0106. It refuses a direct start, then forwards to v0104.
The body still names itself v0104. SyncAll's selftest checks the refusal only.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
VRN = VIA / "functional modules" / "VRN"
TAIL = VRN / "VRN_SystemManager_v0106.py"


def check() -> dict:
    tail = TAIL.read_text(encoding="utf-8") if TAIL.is_file() else ""
    body = (VRN / "VRN_SystemManager_v0104.py").read_text(encoding="utf-8") if (VRN / "VRN_SystemManager_v0104.py").is_file() else ""
    missing = []
    for name in ("VRN_SystemManager_v0104.py", "VRN_SystemManager_v0105.py", "VRN_SystemManager_v0106.py"):
        if not (VRN / name).is_file():
            missing.append(name)
    for needle in ("main only", "deny only", "拒絕。只能經 via-vcgc。"):
        if needle not in tail:
            missing.append(needle)
    if "def read_logic(" not in body or "def collect(" not in body:
        missing.append("body")
    if '"engine"' in body.split("RC_SCOPE = ", 1)[-1].split(")", 1)[0]:
        missing.append("rc_scope")
    return {
        "via": "vcgc",
        "door": "CGC_MDL201_VrnManagerRead_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [],
        "tail": "VRN_SystemManager_v0106.py",
        "body": "VRN_SystemManager_v0104.py",
        "prior_kept": "VRN_SystemManager_v0105.py",
        "gate": "main only",
        "selftest": "deny only",
        "logic": ["book", "guard", "ENG082"],
        "rc_scope": ["policy", "logic", "factor", "param", "handover", "ssot"],
        "not_scored": ["engine", "records"],
        "ran_body": False,
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "rewrite v0104",
            "delete v0105",
            "treat the deny selftest as the twenty-seven checks",
            "run VRN basic or financial from this door",
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
