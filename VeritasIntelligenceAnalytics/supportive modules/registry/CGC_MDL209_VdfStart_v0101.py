#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Start the VDF manager from VCGC. Status only. No fetch.

v0100 pinned VDF_SystemManager_v0107. That body joins a dotted
Register-VIA-Commands chain only inside scrape_gate_split, so read_launch
read the thin tail alone and reported Register via-vdffetch missing.
This door loads the newest VDF_SystemManager, the one that joins the
register chain for read_launch. It still does not fetch and does not
set a consent gate.
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
VDF = VIA / "functional modules" / "VDF"
_VNUM = re.compile(r"_v(\d+)$")


def _vnum(path: Path) -> int:
    match = _VNUM.search(path.stem)
    return int(match.group(1)) if match else -1


def _manager_path() -> Path:
    hits = [p for p in VDF.glob("VDF_SystemManager_v*.py") if _vnum(p) >= 0]
    if not hits:
        raise FileNotFoundError("VDF_SystemManager_v*.py")
    return max(hits, key=_vnum)


def _manager():
    path = _manager_path()
    spec = importlib.util.spec_from_file_location("vdf_start_" + path.stem, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module._VDF_START_PATH = path
    return module


def check() -> dict:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        return {
            "via": "vcgc",
            "door": "CGC_MDL209_VdfStart_v0101",
            "state": "DENY",
            "next": "enter through VCGC",
        }
    module = _manager()
    status = module.collect()
    lamps = status.get("lamps") or {}
    launch = status.get("launch") or {}
    launch_state = launch.get("state") if isinstance(launch, dict) else launch
    missing = list((launch.get("launchers") or {}).get("cmds_missing") or []) if isinstance(launch, dict) else []
    open_rows = [name for name, lamp in lamps.items() if lamp != "GREEN"]
    if launch_state and launch_state != "GREEN":
        open_rows.append("launch")
    return {
        "via": "vcgc",
        "door": "CGC_MDL209_VdfStart_v0101",
        "enter": "vcgc",
        "exit": "vcgc",
        "started": True,
        "lock_success": status.get("rc") == 0 and not open_rows,
        "manager": module._VDF_START_PATH.name,
        "verb": "status",
        "rc": status.get("rc"),
        "lamps": lamps,
        "launch": launch_state,
        "cmds_missing": missing,
        "why": launch.get("why") if isinstance(launch, dict) else None,
        "open": open_rows,
        "fetched": False,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "start VDF without the VCGC mark",
            "fetch from this door",
            "set VIA_NET_CONSENT or VIA_SCRAPE_CONSENT",
            "edit intake macro_ssot",
        ],
        "next": "none" if not open_rows else (launch.get("next") if isinstance(launch, dict) else "started; the open lamps are not locked"),
    }


def main() -> int:
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if card.get("state") == "DENY":
        return 2
    return 0 if card.get("started") else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = check().get("state") == "DENY"
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card.get("started") and card.get("manager") != "VDF_SystemManager_v0107.py" and "via-vdffetch" not in (card.get("cmds_missing") or []) and card.get("launch") != "RED"
    print("  [OK]" if ok else "  [FAIL] " + str(card.get("launch")) + " " + ",".join(card.get("cmds_missing") or []) + " " + str(card.get("manager")))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
