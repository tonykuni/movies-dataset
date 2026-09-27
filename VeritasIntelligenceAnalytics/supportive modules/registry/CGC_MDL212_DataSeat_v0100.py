#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One computer, one database root. GitHub is not that root.

This door does not open a database and does not write the policy book.
If the root is not on this machine, the status is OFF_PC.
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
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = HERE / "VIA_Policy_DataSeat_v0100.json"
BOOK = HERE / "VIA_Policy_Laws_SSOT_v0100.json"


def _root(note: dict) -> str:
    picked = os.environ.get(note["env"], "").strip()
    return picked or note["root"]


def _here(root: str) -> bool:
    try:
        return Path(root).is_dir()
    except OSError:
        return False


def check() -> dict:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        return {
            "via": "vcgc",
            "door": "CGC_MDL212_DataSeat_v0100",
            "state": "DENY",
            "why": "enter through VCGC",
            "opened": False,
            "book_written": False,
        }
    before = BOOK.stat().st_mtime_ns
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    picked = os.environ.get(note["env"], "").strip()
    root = picked or note["root"]
    present = _here(root)
    return {
        "via": "vcgc",
        "door": "CGC_MDL212_DataSeat_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "github": note["github"],
        "pair": note["pair"],
        "computer_role": note["computer_role"],
        "root": root,
        "cloud": note["cloud"] if not picked else "env",
        "on_this_machine": present,
        "status": "HERE" if present else "OFF_PC",
        "off_pc_means": note["off_pc_means"],
        "opened": False,
        "book_edited": note["book_edited"],
        "book_written": BOOK.stat().st_mtime_ns != before,
        "intake_edited": False,
        "do_not": note["do_not"],
        "next": "none" if note["book_edited"] is False else "stop; the book changed",
    }


def main() -> int:
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if card.get("state") == "DENY" or card.get("book_written"):
        return 2
    return 0


def selftest() -> int:
    import tempfile
    os.environ.pop("VIA_FROM_VCGC", None)
    os.environ.pop("VIA_VRN_DATA", None)
    denied = check().get("state") == "DENY"
    os.environ["VIA_FROM_VCGC"] = "YES"
    away = check()
    with tempfile.TemporaryDirectory() as folder:
        os.environ["VIA_VRN_DATA"] = folder
        here = check()
    os.environ.pop("VIA_VRN_DATA", None)
    ok = (
        denied
        and away["github"] == "code_and_policy_only"
        and away["computer_role"] == "database_storage_only"
        and away["status"] == "OFF_PC"
        and away["on_this_machine"] is False
        and away["opened"] is False
        and away["book_written"] is False
        and here["status"] == "HERE"
        and here["opened"] is False
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
