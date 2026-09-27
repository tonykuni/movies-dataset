#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One outside door for NLP and Layout. The engines stay where they are.

What a later UI should show
    entry     via-vcgc support
    nlp text  SUP_MDL866 v0103 calls SUP_MDL744 v0102
    nlp file  the same orchestrator calls VRN_ENG087 v0101
    nlp kept  ENG066 summary support and ENG078 registration stay
    nlp 1.9.0 registered, not the PDF path, models not downloaded
    layout    body v0104, OCR pointer v0105, v0100 and v0101 stay
    this door names the routes. It does not run a PDF, write a database,
    or delete an older engine.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RULES = VIA / "supportive modules" / "70_VRN_Rules"
VRN = VIA / "functional modules" / "VRN"
NLP = {
    "orchestrator": RULES / "SUP_MDL866_VIAUnifiedNLPOrchestrator_v0103.py",
    "hub": RULES / "SUP_MDL744_NLPApplicationHub_v0102.py",
    "file_bridge": VRN / "VRN_ENG087_NLPTextSummaryBridge_v0101.py",
    "summary_support": VRN / "VRN_ENG066_NLPSupportHub_v0100.py",
    "register": VRN / "VRN_ENG078_NLPOneBridge_v0102.py",
    "oneengine_190": VRN / "references" / "intake" / "VIA_NLP_OneEngine_v1_9_0" / "VIA_NLP_OneEngine_v1_9_0.py",
    "manager": VIA / "supportive modules" / "VIA_NLP_System" / "NLP_SystemManager_v0100.py",
}
LAYOUT = {
    "body": RULES / "SUP_MDL743_GenericLayoutHub_v0104.py",
    "ocr_pointer": RULES / "SUP_MDL743_GenericLayoutHub_v0105.py",
    "mount": RULES / "SUP_MDL743_GenericLayoutHub_v0100.py",
    "bridge": RULES / "SUP_MDL743_GenericLayoutHub_v0101.py",
}


def check() -> dict:
    missing = [name for name, path in {**NLP, **LAYOUT}.items() if not path.is_file()]
    return {
        "via": "vcgc",
        "door": "CGC_MDL216_NlpLayoutDoor_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "outside_dock": 1,
        "faces": ["nlp", "layout"],
        "nlp": {
            "text": NLP["orchestrator"].name,
            "hub": NLP["hub"].name,
            "file": NLP["file_bridge"].name,
            "kept": [NLP["summary_support"].name, NLP["register"].name],
            "oneengine": "1.9.0",
            "oneengine_reads_pdf": False,
            "called": False,
        },
        "layout": {
            "entry": "via-vcgc layout",
            "body": LAYOUT["body"].name,
            "ocr_pointer": LAYOUT["ocr_pointer"].name,
            "kept": [LAYOUT["mount"].name, LAYOUT["bridge"].name],
            "ran": False,
        },
        "missing": missing,
        "ran_engines": False,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "delete an older NLP or Layout engine",
            "use OneEngine 1.9.0 as the PDF path",
            "download a model or a tessdata pack",
            "write the financial database from this door",
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
    return 0 if card["next"] == "none" else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card["outside_dock"] == 1 and card["nlp"]["called"] is False and card["layout"]["ran"] is False and card["next"] == "none"
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
