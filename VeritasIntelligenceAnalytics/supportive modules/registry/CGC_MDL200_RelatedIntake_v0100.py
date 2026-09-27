#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register related tools that were not already in VCGC.

What this door is
    A catalog, not a runner. SyncAll may read this card. It must not launch
    AzureFlow QA, the report reviewer, or the mother inspector.

What was added
    azureflow_qa       天青智流品保. One copy of plugin 1.1.0, plus the two
                       files that exist only in the earlier zip.
    azureflow_review   天青智流報告覆核. A separate reviewer, not a second plugin.
    mother_inspector   母系統檢視. Read-only, offline. Not a second governor.

What was not copied
    NLP 1.8 / v5 / v7 / v8, the discussion reconstruction JSON, ActiveETF,
    the broker evidence zip, and the selftest fixture named
    VIA_CentralGovernance.py. Those are already owned, or they are not engines.

How a later UI should read this card
    Show imported[].name_zh, role, path, and the one-line writes field.
    Show skipped_duplicate as a second list, so a repeated upload is visible
    and is not imported again.

Rules
    Add only. Do not delete an older module. Do not wire any of these into
    the stock-report door. Do not edit intake macro_ssot.
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
VIA = HERE.parent.parent
BOOK = HERE / "VIA_RelatedIntake_v0100.json"


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    missing = []
    for row in book["imported"]:
        if not (VIA / row["path"]).exists():
            missing.append(row["id"])
    return {
        "via": "vcgc",
        "door": "CGC_MDL200_RelatedIntake_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [] and book["called"] is False and book["wired_to_report"] is False,
        "imported": [row["id"] for row in book["imported"]],
        "imported_n": len(book["imported"]),
        "skipped_duplicate": len(book["skipped_duplicate"]),
        "called": False,
        "wired_to_report": False,
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "launch these tools from SyncAll",
            "copy NLP, ActiveETF, or the broker evidence again",
            "treat the mother inspector as a second governor",
            "call these from the stock report door",
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
    ok = card["lock_success"] and card["imported_n"] == 3 and card["skipped_duplicate"] == 5
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
