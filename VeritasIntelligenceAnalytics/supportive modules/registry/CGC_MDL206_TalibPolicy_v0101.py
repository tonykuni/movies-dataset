#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Confirm L50 is wired. LF and CRLF are one book, not two hashes.

The locked policy hash is not changed. L50 is not rewritten. TA-Lib is not
installed from here.
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
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
LAWS = HERE / "VIA_Policy_Laws_SSOT_v0100.json"
LOCK = HERE / "VIA_EntryLock_v0100.json"
NOTE = HERE / "VIA_Policy_TalibBan_v0100.json"
BOOK = HERE / "VIA_Component_Inventory_SSOT_v0100.json"
BRIDGE = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG086_QuantGuardOneBridge_v0101.py"


def _sha16(path: Path) -> str:
    raw = path.read_bytes().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()[:16]


def check() -> dict:
    laws = json.loads(LAWS.read_text(encoding="utf-8"))
    law = next(row for row in laws["laws"] if row.get("id") == "L50")
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    locked = json.loads(LOCK.read_text(encoding="utf-8"))
    live = _sha16(LAWS)
    inventory = json.loads(BOOK.read_text(encoding="utf-8")) if BOOK.is_file() else {}
    code = ""
    for row in inventory.get("records") or []:
        if row.get("key") == "feature|policy/L50" and row.get("state") == "ACTIVE":
            code = row.get("code") or ""
    installed = importlib.util.find_spec("talib") is not None
    missing = []
    if law.get("rank") != 2 or law.get("status") != "ACTIVE":
        missing.append("law")
    if live != locked.get("policy_sha16"):
        missing.append("policy_sha")
    if note.get("check") != "CGC_MDL205_TalibBan_v0100.py" or note.get("book_edited") is not False:
        missing.append("note")
    if not BRIDGE.is_file():
        missing.append("quantguard")
    if not code:
        missing.append("code")
    if installed:
        missing.append("installed")
    return {
        "via": "vcgc",
        "door": "CGC_MDL206_TalibPolicy_v0101",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "law": "L50",
        "rank": law.get("rank"),
        "policy_sha": live == locked.get("policy_sha16"),
        "newline": "lf and crlf are one book",
        "book_edited": False,
        "code": code,
        "replacement": note.get("replacement"),
        "installed": installed,
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "rewrite L50",
            "change the locked policy hash",
            "treat LF and CRLF as two policy books",
            "pip install TA-Lib",
            "import talib",
            "treat a mention as an import",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the drift",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    card = check()
    print("  [OK]" if card["lock_success"] else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
