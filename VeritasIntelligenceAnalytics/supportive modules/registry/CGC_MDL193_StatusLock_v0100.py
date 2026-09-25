#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-check the locked VCGC status. Does not rewrite the lock or the intake SSOT."""
from __future__ import annotations
import importlib.util, json, os, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LOCK = HERE / "VIA_StatusLock_v0100.json"

def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, HERE / name)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

def check() -> dict:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    knowledge = _load("CGC_MDL191_KnowledgeAsset_v0100.py").check()
    params = _load("CGC_MDL192_MacroParamSync_v0100.py").check()
    want = {row["id"]: row for row in lock["locked"]}
    holds = []
    drift = []
    pairs = {
        "knowledge_assets": knowledge["assets"] == want["knowledge_assets"]["assets"] and knowledge["lamps"]["RED"] == 0 and knowledge["cycles"] == [] and knowledge["method_log_linked"],
        "usmacro_params": params["hash_match"] and params["hub"] == want["usmacro_params"]["hub"] and params["parameters"] == want["usmacro_params"]["parameters"] and params["books"] == want["usmacro_params"]["books"],
        "method_selftest": (HERE.parent.parent / "functional modules/VDF/engine/VDF_ENG113_MacroMethod_v0100.py").is_file(),
    }
    for row in lock["locked"]:
        ok = pairs[row["id"]]
        holds.append({"id": row["id"], "holds": ok})
        if not ok:
            drift.append(row["id"])
    return {
        "via": "vcgc", "door": "CGC_MDL193",
        "locked": [h["id"] for h in holds if h["holds"]],
        "drift": drift, "open": lock["open"], "holds": holds,
        "do_not": lock["do_not"], "intake_edited": False,
        "next": "none" if not drift else "do not unlock; name the drift",
    }

def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if not card["drift"] else 2

def selftest() -> int:
    card = check()
    ok = card["drift"] == [] and len(card["locked"]) == 3
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
