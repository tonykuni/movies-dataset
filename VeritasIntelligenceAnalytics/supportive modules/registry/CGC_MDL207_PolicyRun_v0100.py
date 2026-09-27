#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the one policy executor. Do not add a second policy engine.

The book decides. policy_step on the newest console executes. This door only
calls that function. It does not score laws again and it does not register a
new command.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONSOLE = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0151.py"
BOOK = HERE / "VIA_Policy_Laws_SSOT_v0100.json"


def _console():
    spec = importlib.util.spec_from_file_location("vcgc_policy_run", CONSOLE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def check() -> dict:
    laws = json.loads(BOOK.read_text(encoding="utf-8"))
    module = _console()
    rc = module.policy_step()
    return {
        "via": "vcgc",
        "door": "CGC_MDL207_PolicyRun_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": rc == 0,
        "engine": "policy_step",
        "console": CONSOLE.name,
        "book": BOOK.name,
        "laws": len(laws.get("laws") or []),
        "lessons": len(laws.get("lessons") or []),
        "second_engine": False,
        "command_added": False,
        "rc": rc,
        "missing": [] if rc == 0 else ["policy_step"],
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "add a second policy engine",
            "register another via- command for policy",
            "rewrite the locked policy book",
            "stop the command chain to build a new manager",
            "edit intake macro_ssot",
        ],
        "next": "none" if rc == 0 else "do not unlock; name the section",
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
    print("  [OK]" if card["lock_success"] else "  [FAIL]")
    return 0 if card["lock_success"] else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
