#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Support tier. Accelerator, network, and NLP sit together. Each supports token-save once."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
SUPPORT = VIA / "supportive modules"
PEERS = (
    ("accelerator", SUPPORT / "VIA_SuperAccel_Module.py"),
    ("network", SUPPORT / "VIA_NetSupport.py"),
    ("nlp", SUPPORT / "VIA_NLP_System" / "NLP_SystemManager_v0100.py"),
)
TOKEN = SUPPORT / "VIA_TokenSave_v0100.py"


def _manager():
    path = SUPPORT / "VIA_NLP_System" / "NLP_SystemManager_v0100.py"
    spec = importlib.util.spec_from_file_location("nlp_manager_tier", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check() -> dict:
    manager = _manager().check()
    peers = [{"id": name, "file": path.name, "present": path.is_file(), "up": TOKEN.name, "n": 1} for name, path in PEERS]
    missing = [row["id"] for row in peers if not row["present"]]
    if not TOKEN.is_file():
        missing.append("token_save")
    ok = missing == [] and manager["outside_dock"] == 1 and manager["up"]["n"] == 1 and manager["called"] is False
    return {
        "via": "vcgc",
        "door": "CGC_MDL199_SupportTier_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": ok,
        "tier": "support",
        "peers": peers,
        "nlp_engines": manager["engines"],
        "nlp_called": False,
        "ran": False,
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "merge accelerator, network, and nlp into one manager",
            "let a single engine dock outside",
            "call NLP from the report door",
            "edit intake macro_ssot",
        ],
        "next": "none" if ok else "do not unlock; name the drift",
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
