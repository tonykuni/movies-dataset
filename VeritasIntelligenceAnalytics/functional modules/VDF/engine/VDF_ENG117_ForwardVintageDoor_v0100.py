#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the VDF copy of the forward-vintage engine. Does not edit intake or the hub."""
from __future__ import annotations

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
