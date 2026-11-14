#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN tail. The reader stays v0104. This file only records that contract.

What a later UI should show
    tail     VRN_SystemManager_v0106.py
    body     VRN_SystemManager_v0104.py
    prior    VRN_SystemManager_v0105.py is still on disk
    gate     main() only. Importing read_logic() does not pass this refusal.
    selftest the refusal only. The twenty-seven checks in v0104 are not run here.
    logic    index book, guard, and ENG082. A missing book or a red guard fails the domain.
    rc       policy, logic, factor, param, handover, ssot. Engine and records are shown, not scored.
    version  the body still reports v0104, because it reads its own file name.

Rules
    Do not rewrite v0104. Do not delete v0105. Do not treat this selftest as a full manager pass.
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
BODY = HERE / "VRN_SystemManager_v0104.py"
PRIOR = HERE / "VRN_SystemManager_v0105.py"
_body = None


def _load():
    global _body
    if _body is None:
        spec = importlib.util.spec_from_file_location(BODY.stem, BODY)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _body = mod
    return _body


def __getattr__(name: str):
    return getattr(_load(), name)


def card() -> dict:
    body = BODY.read_text(encoding="utf-8") if BODY.is_file() else ""
    prior = PRIOR.read_text(encoding="utf-8") if PRIOR.is_file() else ""
    return {
        "via": "vcgc",
        "door": "VRN_SystemManager_v0106",
        "tail": "VRN_SystemManager_v0106.py",
        "body": "VRN_SystemManager_v0104.py",
        "prior": "VRN_SystemManager_v0105.py",
        "prior_kept": "拒絕。只能經 via-vcgc。" in prior and "VRN_SystemManager_v0104.py" in prior,
        "body_has_logic": "def read_logic(" in body and "def collect(" in body,
        "rc_scope": ["policy", "logic", "factor", "param", "handover", "ssot"],
        "not_scored": ["engine", "records"],
        "gate": "main only",
        "selftest": "deny only",
        "version_reported_by_body": "v0104",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    if "--card" in sys.argv:
        print(json.dumps(card(), ensure_ascii=False, indent=1))
        return 0
    return _load().main()


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    looked = card()
    ok = denied and looked["prior_kept"] and looked["body_has_logic"] and "engine" not in looked["rc_scope"]
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
