#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Start the VDF manager from VCGC. Status only. No fetch.

Direct start of the manager stays refused. This door sets nothing by itself.
The launcher must already carry the VCGC mark.
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
VIA = HERE.parents[1]
MANAGER = VIA / "functional modules" / "VDF" / "VDF_SystemManager_v0107.py"


def _manager():
    spec = importlib.util.spec_from_file_location("vdf_start_v0107", MANAGER)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check() -> dict:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        return {
            "via": "vcgc",
            "door": "CGC_MDL209_VdfStart_v0100",
            "state": "DENY",
            "next": "enter through Invoke-VIA-VCGC-Vdf.ps1",
        }
    module = _manager()
    body = module._load()
    status = body.collect()
    body._print_status(status)
    lamps = status.get("lamps") or {}
    launch = (status.get("launch") or {}).get("state")
    open_rows = [name for name, lamp in lamps.items() if lamp != "GREEN"]
    if launch and launch != "GREEN":
        open_rows.append("launch")
    rc = status.get("rc")
    return {
        "via": "vcgc",
        "door": "CGC_MDL209_VdfStart_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "started": True,
        "lock_success": rc == 0 and not open_rows,
        "manager": MANAGER.name,
        "verb": "status",
        "rc": rc,
        "lamps": lamps,
        "launch": launch,
        "open": open_rows,
        "fetched": False,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "start VDF without the VCGC mark",
            "fetch from this door",
            "edit intake macro_ssot",
        ],
        "next": "none" if not open_rows else "started; the open lamps are not locked",
    }


def main() -> int:
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if card.get("state") == "DENY":
        return 2
    return 0 if card.get("started") else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    card = check()
    ok = card.get("state") == "DENY"
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
