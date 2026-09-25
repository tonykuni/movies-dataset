#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0144. The new file keeps the old console's functions, and one door prints the yellow paste."""
from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
_PREV = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0143.py"
_spec = importlib.util.spec_from_file_location("vcgc_v0143", _PREV)
prev = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = prev
_spec.loader.exec_module(prev)


def __getattr__(name: str):
    return getattr(prev.body, name)


def _load(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def systems() -> int:
    via = HERE.parent.parent
    vdf = _load(via / "functional modules" / "VDF" / "VDF_SystemManager_v0104.py")
    vrn = _load(via / "functional modules" / "VRN" / "VRN_SystemManager_v0104.py")
    a, b = vdf.collect(), vrn.collect()
    body = {
        "via": "vcgc",
        "vdf": {"rc": a.get("rc"), "rc_name": a.get("rc_name"), "lamps": a.get("lamps")},
        "vrn": {"rc": b.get("rc"), "rc_name": b.get("rc_name"), "lamps": b.get("lamps")},
        "do_not": ["page --publish", "hand-edit the card book", "TOOLS_PLAN_latest.ps1"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    out = via / "VIA_Reports" / "vcgc" / "SYSTEMS_latest.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if a.get("rc") == 0 and b.get("rc") == 0 else (1 if b.get("rc") == 1 else 2)


def selftest() -> int:
    ok = callable(__getattr__("handover_src")) and callable(__getattr__("spec_items"))
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


def main() -> int:
    args = sys.argv[1:]
    if args[:1] == ["systems"]:
        if "--selftest" in args:
            return selftest()
        return systems()
    if args[:1] == ["--selftest"]:
        return selftest()
    return prev.main()


if __name__ == "__main__":
    sys.exit(main())
