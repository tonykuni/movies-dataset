#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Console tail. Steps 1 to 3 finish before the older console prints policy.

v0160 is not rewritten. A red token tool or a missing accelerator or network
bridge does not open the policy book and does not open a subsystem file.
After the older console returns, step 8 compares the SSOT, regex, synonym,
and parameter books and does not rewrite them.
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
PREVIOUS = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0160.py"
DOOR = HERE / "CGC_MDL226_StepMatrix_v0100.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


prev = _load(PREVIOUS, "vcgc_v0160_for_v0161")


def __getattr__(name: str):
    return getattr(prev, name)


def main(argv=None):
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    args = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in args:
        return selftest()
    matrix = _load(DOOR, "steps_for_console")
    card = matrix.front()
    matrix.write_page(card)
    if not card["front_pass"]:
        print(json.dumps(card, ensure_ascii=False, indent=1))
        return 2
    print("[步驟] 1 入口 · 2 省Token GREEN · 3 加速器與網路已接 · 政策與子系統在後")
    rc = prev.main(argv)
    sync = matrix.subsystem_sync()
    if sync.get("missing") or sync.get("drift"):
        print(json.dumps({
            "step": 8,
            "id": "subsystem",
            "lock_success": sync.get("lock_success"),
            "drift": sync.get("drift"),
            "missing": sync.get("missing"),
            "rewritten": False,
        }, ensure_ascii=False, indent=1))
        return 2 if rc == 0 else rc
    print("[子系統] SSOT regex 同義字 參數比對過 · 未改冊 · drift 無")
    return rc


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main(["status"]) == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = _load(DOOR, "steps_self_console").front()
    ok = denied and card["front_pass"] and card["opened_subsystem"] is False and not any(row["may_open_subsystem"] for row in card["rows"] if row["step"] <= 3) and PREVIOUS.is_file()
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
