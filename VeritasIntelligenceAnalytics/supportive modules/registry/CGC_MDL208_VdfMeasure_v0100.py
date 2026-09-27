#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Measure VDF through its own gate. No second manager and no fetch.

The tail refuses a direct start. This door sets the VCGC mark, then calls
that tail with --selftest. The thirty-one checks stay in VDF_SystemManager_v0104.
"""
from __future__ import annotations

import importlib.util
import io
import json
import os
import sys
from contextlib import redirect_stdout
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
VDF = VIA / "functional modules" / "VDF" / "VDF_SystemManager_v0107.py"


def _load():
    spec = importlib.util.spec_from_file_location("vdf_manager_v0105_measure", VDF)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check() -> dict:
    module = _load()
    os.environ.pop("VIA_FROM_VCGC", None)
    denied_buf = io.StringIO()
    with redirect_stdout(denied_buf):
        denied = module.main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    held = sys.argv
    out = io.StringIO()
    sys.argv = [str(VDF), "--selftest"]
    try:
        with redirect_stdout(out):
            rc = module.main()
    finally:
        sys.argv = held
    text = out.getvalue()
    fails = [line.split("]", 1)[1].strip() for line in text.splitlines() if line.startswith("  [FAIL]")]
    count = next((line.strip() for line in text.splitlines() if line.startswith("  [計]")), "")
    missing = []
    if not denied:
        missing.append("gate")
    if rc != 0:
        missing.append("selftest")
    return {
        "via": "vcgc",
        "door": "CGC_MDL208_VdfMeasure_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "tail": VDF.name,
        "body": "VDF_SystemManager_v0104.py",
        "tools": "versioned tails replace unversioned canon",
        "denied_direct": denied,
        "checks": count,
        "fails": fails[:12],
        "fetched": False,
        "intake_edited": False,
        "hub_edited": False,
        "missing": missing,
        "do_not": [
            "start VDF without the VCGC mark",
            "merge the managers",
            "fetch from this measure",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the failed check",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    os.environ.pop("VIA_FROM_VCGC", None)
    print("  [OK]" if card["lock_success"] else "  [FAIL] " + " | ".join(card["fails"][:4]))
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
