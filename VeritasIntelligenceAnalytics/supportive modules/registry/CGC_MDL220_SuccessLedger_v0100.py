#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read the success ledger. Older locks stay. Later greens are added beside them.

Nothing in this door rewrites a lock. A held item is not promoted to success.
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
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
NOTE = HERE / "VIA_VCGC_SuccessLedger_v0100.json"
LAWS = HERE / "VIA_Policy_Laws_SSOT_v0100.json"


def check() -> dict:
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    missing = []
    if note.get("book_edited") is not False:
        missing.append("note")
    kept_ids = []
    for row in note["kept"]:
        kept_ids.append(row["id"])
        if not (HERE / row["file"]).is_file():
            missing.append(row["id"])
    status = json.loads((HERE / "VIA_StatusLock_v0100.json").read_text(encoding="utf-8"))
    locked_ids = {row["id"] for row in status.get("locked") or []}
    for name in ("knowledge_assets", "usmacro_params", "method_selftest"):
        if name not in locked_ids:
            missing.append(name)
    still_open = list(status.get("open") or [])
    for row in note["later_green"]:
        if row["id"] not in still_open:
            missing.append("erased_" + row["id"])
    held_ids = {row["id"] for row in note["held"]}
    if kept_ids and held_ids & set(kept_ids):
        missing.append("overlap")
    live = hashlib.sha256(LAWS.read_bytes()).hexdigest()[:16]
    entry = json.loads((HERE / "VIA_EntryLock_v0100.json").read_text(encoding="utf-8"))
    if live != entry.get("policy_sha16"):
        missing.append("policy_sha")
    lexicon = json.loads((HERE / "VIA_VCGC_RegexParamRecord_v0100.json").read_text(encoding="utf-8"))
    if len(lexicon.get("aligned") or []) != 12:
        missing.append("aligned")
    for row in note["added_tail"]:
        if not (VIA / row["tree_tail"]).is_file():
            missing.append("tail")
        if not (VIA / "functional modules" / "VDF" / "engine" / row["cited"]).is_file():
            missing.append("cited")
    return {
        "via": "vcgc",
        "door": "CGC_MDL220_SuccessLedger_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "lock_record": NOTE.name,
        "kept": len(note["kept"]),
        "later_green": [row["id"] for row in note["later_green"]],
        "still_open_in_old_lock": [row["id"] for row in note["later_green"]],
        "held": [row["id"] for row in note["held"]],
        "policy_sha16": live,
        "book_edited": False,
        "intake_edited": False,
        "missing": missing,
        "do_not": [
            "rewrite VIA_StatusLock_v0100.json",
            "delete a held conflict",
            "mark the engine lamp green without a chain report",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the drift",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card["lock_success"] and "vdf_engine" in card["held"] and "vdf_logic" in card["later_green"]
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
