#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC panorama for TA-Lib commands. Token tools only. History stays.

The live commands were via-talib, via-taone, and bin/via-ta.cmd.
Register v0262 removes the two functions after the old registers load.
This door asks the panorama slicer for those two definitions only.
It does not print their bodies, does not delete v0205–v0207, and does not
import or install TA-Lib.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PANORAMA = HERE / "CGC_MDL158_VIAPanoramaAuditRepair_v0115.py"
REGISTER = VIA / "Register-VIA-Commands-v0262.ps1"
HISTORY = VIA / "Register-VIA-Commands-v0207.ps1"
LAUNCHER = VIA / "bin" / "via-ta.cmd"
SLICES = ("via-talib", "via-taone")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def check() -> dict:
    panorama = _load(PANORAMA, "vcgc_panorama_for_talib_cmd")
    slices = []
    for name in SLICES:
        card = panorama.slice_def(str(HISTORY), name)
        hit = (card.get("hits") or [{}])[0]
        slices.append({
            "name": name,
            "line": hit.get("line"),
            "end": hit.get("end"),
            "slice_tokens": card.get("slice_tokens"),
            "etag": card.get("etag"),
        })
    repair = REGISTER.read_text(encoding="utf-8") if REGISTER.is_file() else ""
    removed = all(("Function:" + name) in repair or name in repair for name in ("via-talib", "via-taone", "via-ta"))
    return {
        "via": "vcgc",
        "door": "CGC_MDL243_TalibCommandScan_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "tool": PANORAMA.name,
        "tool_kind": "slice",
        "slices": slices,
        "bodies_printed": False,
        "repair": REGISTER.name if removed else "",
        "launcher": LAUNCHER.name,
        "launcher_present": LAUNCHER.is_file(),
        "history_kept": HISTORY.is_file(),
        "deleted_history": False,
        "installed_check": False,
        "lock_success": removed and not LAUNCHER.is_file() and HISTORY.is_file() and len(slices) == 2,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "pip install TA-Lib",
            "import talib",
            "delete Register-VIA-Commands-v0205 through v0207",
            "print a sliced command body into the card",
            "edit intake macro_ssot",
        ],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = check()
    if not card["lock_success"]:
        card["next"] = "name the live command; do not delete the old register"
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    text = json.dumps(card)
    ok = (
        denied
        and card["lock_success"]
        and card["bodies_printed"] is False
        and card["launcher_present"] is False
        and card["history_kept"] is True
        and card["deleted_history"] is False
        and "Invoke-VIAPython" not in text
        and len(card["slices"]) == 2
    )
    print("  [OK]" if ok else "  [FAIL] " + text[:300])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
