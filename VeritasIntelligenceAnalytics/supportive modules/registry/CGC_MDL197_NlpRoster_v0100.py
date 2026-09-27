#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register the new NLP entry beside the old engines. None of them is called."""
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
BOOK = HERE / "VIA_NLP_Roster_v0100.json"


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    missing = [row["id"] for row in book["rows"] if not (VIA / row["path"]).is_file()]
    entry = next(row for row in book["rows"] if row["role"] == "future_entry")
    return {
        "via": "vcgc",
        "door": "CGC_MDL197_NlpRoster_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [] and book["called"] is False,
        "future_entry": entry["id"],
        "registered": len(book["rows"]),
        "called": False,
        "missing": missing,
        "roles": {row["id"]: row["role"] for row in book["rows"]},
        "wired_to_summary": False,
        "reads_pdf": False,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "delete an older NLP engine",
            "call the roster from the report door",
            "copy fixed_page1 into summary_page1",
            "download optional models",
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
