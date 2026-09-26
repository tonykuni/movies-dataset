#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Status report from the normalized lock check. Does not change the lock."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORT = VIA / "docs" / "VIA_VCGC_StatusReport.md"
LOCK = HERE / "VIA_StatusLock_v0100.json"


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def update() -> dict:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    card = _load("CGC_MDL193_StatusLock_v0103.py").check()
    text = _load("CGC_MDL194_ReportUpdate_v0100.py").render(card, lock)
    changed = (not REPORT.exists()) or REPORT.read_text(encoding="utf-8") != text
    if changed:
        REPORT.write_text(text, encoding="utf-8")
    return {
        "via": "vcgc", "door": "CGC_MDL194_v0101",
        "state": "GREEN" if not card["drift"] else "RED",
        "changed": changed, "path": "docs/VIA_VCGC_StatusReport.md",
        "drift": card["drift"], "intake_edited": False, "lock_edited": False,
        "next": card["next"],
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = update()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["state"] == "GREEN" else 2


def selftest() -> int:
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = update()
    text = REPORT.read_text(encoding="utf-8")
    ok = card["state"] == "GREEN" and card["drift"] == [] and "usmacro_params: HOLDS" in text and card["lock_edited"] is False
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
