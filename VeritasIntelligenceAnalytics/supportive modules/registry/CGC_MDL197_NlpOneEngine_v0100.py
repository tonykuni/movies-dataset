#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register NLP OneEngine 1.9.0. It does not read PDFs or fill the report summary."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENGINE = VIA / "functional modules" / "VRN" / "references" / "intake" / "VIA_NLP_OneEngine_v1_9_0" / "VIA_NLP_OneEngine_v1_9_0.py"
SHA = "8a02d0474c3bf472e47133b8ea91ad726b746e540f5f3ae7bc87fa5f19d05eb3"


def check() -> dict:
    drift = []
    if not ENGINE.is_file():
        drift.append("missing")
        digest = ""
    else:
        digest = hashlib.sha256(ENGINE.read_bytes()).hexdigest()
        if digest != SHA:
            drift.append("sha256")
        head = ENGINE.read_text(encoding="utf-8", errors="replace")[:800]
        if 'VERSION = "1.9.0"' not in head:
            drift.append("version")
    return {
        "via": "vcgc",
        "door": "CGC_MDL197_NlpOneEngine_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": drift == [],
        "engine": ENGINE.name,
        "version": "1.9.0",
        "sha256": digest,
        "core": "STDLIB",
        "models_auto_download": False,
        "optional_models": "MISSING",
        "wired_to_summary": False,
        "reads_pdf": False,
        "drift": drift,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "use this engine as OCR for the 10 short pages",
            "copy fixed_page1 into summary_page1",
            "download FunASR, SaT, CKIP, or MacBERT from this door",
            "overwrite a source file",
            "edit intake macro_ssot",
        ],
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
    card = check()
    print("  [OK]" if card["lock_success"] else "  [FAIL] " + ",".join(card["drift"]))
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
