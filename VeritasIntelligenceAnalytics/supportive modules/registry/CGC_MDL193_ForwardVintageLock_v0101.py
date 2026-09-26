#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same forward-vintage lock. LF and CRLF of the same text are one hash."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LOCK = HERE / "VIA_ForwardVintageLock_v0101.json"
ENGINE = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG117_ForwardVintage_v0100.py"
PATH = (
    "Invoke-VIA-VCGC-SyncAll.ps1",
    "CGC_MDL193_ForwardVintageLock_v0101.py",
    "VDF_ENG117_ForwardVintage_v0100.py",
    "VIA_ForwardVintageLock_v0101.json",
)


def normalized(data: bytes) -> str:
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def check() -> dict:
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    raw = ENGINE.read_bytes() if ENGINE.is_file() else b""
    live = hashlib.sha256(raw).hexdigest()
    drift = []
    if normalized(raw) != lock["sha256_lf"]:
        drift.append("sha256")
    elif live not in (lock["sha256_lf"], lock["sha256_crlf"]):
        drift.append("newline")
    if lock["selftest"] != "pass":
        drift.append("selftest")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_ForwardVintageLock_v0101",
        "order": ["enter", "lock_success", "lock_record", "lock_path", "exit"],
        "enter": "vcgc",
        "lock_success": drift == [],
        "lock_record": LOCK.name,
        "lock_path": list(PATH),
        "exit": "vcgc",
        "name": "VIA",
        "same": True,
        "sha256": live,
        "newline": "crlf" if b"\r\n" in raw else "lf",
        "methodology": lock["methodology"],
        "parameters": lock["parameters"],
        "drift": drift,
        "hub_edited": False,
        "intake_edited": False,
        "registry_apply": False,
        "do_not": lock["do_not"],
        "next": "none" if not drift else "do not unlock; name the drift",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    raw = ENGINE.read_bytes()
    crlf = raw.replace(b"\n", b"\r\n")
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    ok = check()["lock_success"] and normalized(crlf) == lock["sha256_lf"] and hashlib.sha256(crlf).hexdigest() == lock["sha256_crlf"]
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
