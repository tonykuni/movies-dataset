#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC manager tail. Entering reads the policy. It does not rewrite the book.

v0102 is not rewritten. ps1 files are only described here; the gate writes them.
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
PRIOR = HERE / "CGC_SystemManager_v0102.py"
GATE = HERE / "CGC_MDL211_FlowGate_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-managers"}, ensure_ascii=False))
        return 2
    gate = _load(GATE, "flow_gate_for_cgc_v0103")
    if "update" in sys.argv[1:]:
        card = gate.update_policy()
    elif "ps" in sys.argv[1:]:
        card = gate.read_policy()
        card["verb"] = "ps"
        card["ps_written"] = False
        card["next"] = "none"
    else:
        card = gate.read_policy()
    card["door"] = "CGC_SystemManager_v0103"
    card["manager"] = Path(__file__).name
    card["prior"] = PRIOR.name
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if card.get("state") == "DENY" or card.get("book_written"):
        return 2
    return 0


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    gate = _load(GATE, "flow_gate_self_cgc_v0103")
    card = gate.read_policy()
    ok = denied and card["policy_id"] == "L50" and card["book_written"] is False and PRIOR.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
