#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the VDF copy of the forward-vintage engine. Does not edit intake or the hub."""
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = HERE / "VDF_ENG117_ForwardVintage_v0100.py"


def allowed() -> bool:
    return os.environ.get("VIA_CENTRAL_ENTRY") == "1" and os.environ.get("VIA_FROM_VCGC") == "YES"


def load():
    spec = importlib.util.spec_from_file_location("vdf_eng117_forward_vintage", ENGINE)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def run() -> dict:
    digest = hashlib.sha256(ENGINE.read_bytes()).hexdigest()
    try:
        result = load().run_self_test()
    except Exception as exc:
        return {
            "via": "vcgc",
            "door": "VDF_ENG117_ForwardVintageDoor_v0100",
            "enter": "vcgc",
            "exit": "vcgc",
            "state": "FAIL",
            "why": type(exc).__name__ + ": " + str(exc)[:180],
            "sha256": digest,
            "intake_edited": False,
            "hub_edited": False,
            "next": "none",
        }
    return {
        "via": "vcgc",
        "door": "VDF_ENG117_ForwardVintageDoor_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "central": True,
        "state": result.get("status"),
        "methodology": result.get("methodology_version"),
        "sha256": digest,
        "tests": result.get("tests"),
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "edit the locked engine bytes",
            "edit intake macro_ssot",
            "registry-sync --apply",
            "blend two source vintages into one average",
        ],
        "next": "none" if result.get("status") == "pass" else "do not lock a failed self-test",
    }


def main() -> int:
    if not allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-fwdvintage through Invoke-VIAPython"}, ensure_ascii=False))
        return 2
    card = run()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("state") == "pass" else 2


def selftest() -> int:
    os.environ.pop("VIA_CENTRAL_ENTRY", None)
    denied = not allowed()
    os.environ["VIA_CENTRAL_ENTRY"] = "1"
    os.environ["VIA_FROM_VCGC"] = "YES"
    digest = hashlib.sha256(ENGINE.read_bytes()).hexdigest()
    ok = denied and allowed() and digest.startswith("1df8e2ef5fcf6685")
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
