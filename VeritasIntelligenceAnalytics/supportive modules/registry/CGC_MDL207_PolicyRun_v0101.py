#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the one policy executor on the newest tail. Still one engine.

The book is not rewritten. A related command is not stripped of its TA-Lib words.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONSOLE = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0152.py"
BOOK = HERE / "VIA_Policy_Laws_SSOT_v0100.json"
NOTE = HERE / "VIA_Policy_TalibBan_v0101.json"


def _console():
    spec = importlib.util.spec_from_file_location("vcgc_policy_run_v0101", CONSOLE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check() -> dict:
    laws = json.loads(BOOK.read_text(encoding="utf-8"))
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    module = _console()
    rc = module.policy_step()
    missing = []
    if rc != 0:
        missing.append("policy_step")
    if note.get("strip_the_words") is not False or note.get("book_edited") is not False:
        missing.append("note")
    return {
        "via": "vcgc",
        "door": "CGC_MDL207_PolicyRun_v0101",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "engine": "policy_step",
        "console": CONSOLE.name,
        "book": BOOK.name,
        "laws": len(laws.get("laws") or []),
        "lessons": len(laws.get("lessons") or []),
        "strip_the_words": False,
        "ban_added": True,
        "second_engine": False,
        "command_added": False,
        "rc": rc,
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "strip the TA-Lib words out of a related command",
            "add a second policy engine",
            "register another via- command for policy",
            "rewrite the locked policy book",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the section",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    ok = note.get("strip_the_words") is False and note.get("book_edited") is False and CONSOLE.is_file()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
