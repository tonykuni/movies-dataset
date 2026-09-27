#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Name the NLP uses that already sit inside 1.8. Do not call them and do not wire the report."""
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
BOOK = HERE / "VIA_NLP_Uses_v0100.json"
INSIDE = VIA / "functional modules" / "VRN" / "references" / "intake" / "VIA_NLP_Application_System_v1.8.0" / "src" / "via_nlp_engine"


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    missing = [name for name in book["uses"] if not (INSIDE / f"{name}.py").is_file()]
    return {
        "via": "vcgc",
        "door": "CGC_MDL199_NlpUses_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [] and book["called"] is False and book["wired_to_report"] is False,
        "uses": len(book["uses"]),
        "inside_190_only": book["inside_190_only"],
        "kept_out": book["kept_out"],
        "called": False,
        "wired_to_report": False,
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "call these uses from the report door",
            "relabel akshare, autofix, or the layout hub as NLP",
            "treat the absent fusion engine as imported",
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
    print("  [OK]" if card["lock_success"] and card["uses"] == 12 else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if card["lock_success"] and card["uses"] == 12 else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
