#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC manager tail. The same three VDF verbs, still one engine.

v0100 keeps the old dock and is not rewritten. This tail calls that check,
then reads the start/test/register cross-check. It does not run VDF or VRN work
unless the verb is start, test, or register.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
PRIOR = HERE / "CGC_SystemManager_v0100.py"
ENGINE = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG119_StartTestRegister_v0100.py"
VDF = VIA / "functional modules" / "VDF" / "VDF_SystemManager_v0108.py"
VERBS = {"start", "test", "register"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-managers"}, ensure_ascii=False))
        return 2
    if VERBS.intersection(sys.argv[1:]):
        return _load(ENGINE, "eng119_for_cgc_v0101").main(sys.argv)
    prior = _load(PRIOR, "cgc_manager_v0100_for_v0101")
    card = prior.check()
    looked = _load(ENGINE, "eng119_align_for_cgc_v0101").align()
    card["door"] = "CGC_SystemManager_v0101"
    card["vdf_manager"] = VDF.name
    card["verbs"] = looked["verbs"]
    card["conflicts"] = looked["conflicts"]
    card["policy_missing"] = looked["policy_missing"]
    card["crosscheck"] = looked["lock_success"]
    card["ran_vdf"] = False
    card["fetched"] = False
    card["intake_edited"] = False
    card["do_not"] = list(card.get("do_not") or []) + [
        "copy the three verbs into this manager",
        "write the synonym union",
        "registry-sync --apply",
    ]
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["review"]["basic_ok"] and card["review"]["financial_ok"] and looked["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    engine = _load(ENGINE, "eng119_self_for_cgc_v0101")
    looked = engine.align()
    ok = denied and looked["lock_success"] and VDF.is_file() and PRIOR.is_file() and ENGINE.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
