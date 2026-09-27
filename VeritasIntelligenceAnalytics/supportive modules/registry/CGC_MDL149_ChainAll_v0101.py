#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One VCGC pass. A missing param_ids no longer drops the other steps.

Read-only. Numbering stays a plan. The VDF matrix is measured, not fetched.
"""
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
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ORDER = ["policy", "params", "vdf"]


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def run() -> dict:
    os.environ["VIA_FROM_VCGC"] = "YES"
    lock = _load(HERE / "CGC_MDL149_EntryLock_v0100.py", "entry_for_chain_v0101").matrix()
    params = _load(HERE / "CGC_MDL192_MacroParamSync_v0101.py", "params_for_chain_v0101").check()
    vdf = _load(VIA / "functional modules" / "VDF" / "VDF_SystemManager_v0114.py", "vdf_for_chain_v0101").measure()
    steps = [
        {"n": 1, "id": "policy", "locked": lock["policy"]["locked"], "sha16": lock["policy"]["sha16"], "write": False},
        {"n": 2, "id": "params", "books": params.get("books") or params.get("param_books"), "next": params.get("next"), "write": False},
        {"n": 3, "id": "vdf", "rc_name": vdf.get("rc_name"), "open": vdf.get("open"), "page": vdf.get("page"), "write": False},
    ]
    open_rows = list(vdf.get("open") or [])
    return {
        "via": "vcgc",
        "door": "CGC_MDL149_ChainAll_v0101",
        "order": steps,
        "missing": [name for name in ORDER if name not in {step["id"] for step in steps}],
        "open": open_rows,
        "applied": False,
        "fetched": False,
        "do_not": ["registry-sync --apply", "invent a chain result", "edit intake macro_ssot"],
        "next": "none" if lock["policy"]["locked"] and params.get("next") == "none" and not open_rows else "open lamps remain",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = run()
    print("BEGIN_PASTE")
    print(json.dumps(card, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if card["next"] == "none" else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    print("  [OK]" if denied else "  [FAIL]")
    return 0 if denied else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
