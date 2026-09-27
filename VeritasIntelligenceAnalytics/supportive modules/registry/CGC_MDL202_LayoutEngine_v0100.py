#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register the layout tail. Do not rerun the 45 tests and do not overwrite the inventory.

The measured body is hub v0104: 46 capabilities, 360 statement cells, native
text and FINANCIAL DATA kept. v0105 is only the OCR folder pointer. chi_tra is
not downloaded here. A missing language pack does not fail the text extract.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RULES = VIA / "supportive modules" / "70_VRN_Rules"


def check() -> dict:
    need = {
        "hub_v0104": RULES / "SUP_MDL743_GenericLayoutHub_v0104.py",
        "hub_v0105": RULES / "SUP_MDL743_GenericLayoutHub_v0105.py",
        "hub_v0100": RULES / "SUP_MDL743_GenericLayoutHub_v0100.py",
        "console": HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0148.py",
        "ssot": HERE / "VIA_Layout_Capabilities_SSOT_v0100.json",
    }
    missing = [name for name, path in need.items() if not path.is_file()]
    tail = need["hub_v0105"].read_text(encoding="utf-8") if need["hub_v0105"].is_file() else ""
    if "chi_tra.traineddata" not in tail:
        missing.append("ocr_pointer")
    return {
        "via": "vcgc",
        "door": "CGC_MDL202_LayoutEngine_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": missing == [],
        "entry": "via-vcgc layout",
        "tail": "SUP_MDL743_GenericLayoutHub_v0105.py",
        "body": "SUP_MDL743_GenericLayoutHub_v0104.py",
        "kept": "SUP_MDL743_GenericLayoutHub_v0100.py",
        "measured": {"tests": "45/45", "capabilities": 46, "statement_cells": 360},
        "ocr": "chi_tra only when tessdata_best has chi_tra, chi_sim, and eng",
        "rerun": False,
        "inventory_written": False,
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "overwrite VIA_Component_Inventory_SSOT",
            "download chi_tra from this door",
            "mark native text failed because OCR is unavailable",
            "write the financial database from layout review",
            "delete hub v0100 or v0101",
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
