#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console tail. Policy and the subsystem managers finish before the verb runs.

v0158 is not rewritten. A red gate does not start the verb.
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
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0158.py"
DOOR = HERE / "CGC_MDL223_FlowConsistency_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0158_for_v0159")


def __getattr__(name: str):
    return getattr(prev, name)


def main(argv=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    flow = _load(DOOR, "flow_for_console")
    card = flow.gate()
    flow.write_page(card)
    if not card["lock_success"]:
        print(json.dumps(card, ensure_ascii=False, indent=1))
        return 2
    print("[流程] 政策過 · 子系統已對齊 · 才執行")
    rc = prev.main(argv)
    if os.environ.get("VIA_VCGC_PUSH") != "NO":
        sent = flow.publish()
        print("[github] " + sent.get("why", ""))
    return rc


def selftest() -> int:
    os.environ["VIA_VCGC_PUSH"] = "NO"
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["status"]) == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = _load(DOOR, "flow_self_console").gate()
    ok = denied and card["lock_success"] and PREVIOUS.is_file()
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
