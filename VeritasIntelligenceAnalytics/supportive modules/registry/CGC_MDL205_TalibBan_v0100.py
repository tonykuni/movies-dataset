#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""L50 panoramic check. TA-Lib must not be installed and no live tail may import it.

The scan face is the governed tail set from the console, not every old copy.
A file that only mentions talib is counted and then ignored. QuantGuard remains
the replacement. This door does not uninstall, delete, or import the package.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
IMPORT_TALIB = re.compile(r"(?m)^\s*(?:import\s+talib\b|from\s+talib\s+import\b)")
POLICY = {
    "law": "L50",
    "ban": "TA-Lib",
    "replacement": "VDF_ENG086_QuantGuardOneBridge",
    "ruler": "governed tails and real import statements only",
}


def _tails() -> dict:
    path = HERE / "CGC_MDL149_VeritasCentralGovernanceConsole_v0142.py"
    spec = importlib.util.spec_from_file_location("vcgc_tails_for_talib_ban", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module._tail_files()


def check() -> dict:
    tails = _tails()
    imports = []
    mentions = 0
    for path in tails.values():
        text = path.read_text(encoding="utf-8", errors="replace")
        if IMPORT_TALIB.search(text):
            imports.append(path.name)
        elif "talib" in text.lower():
            mentions += 1
    installed = importlib.util.find_spec("talib") is not None
    missing = []
    if imports:
        missing.append("import")
    if installed:
        missing.append("installed")
    return {
        "via": "vcgc",
        "door": "CGC_MDL205_TalibBan_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "law": POLICY["law"],
        "lamp": "GREEN" if not missing else "RED",
        "tails": len(tails),
        "imports": len(imports),
        "import_files": imports[:12],
        "mentions": mentions,
        "installed": installed,
        "replacement": POLICY["replacement"],
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "pip install TA-Lib",
            "import talib",
            "treat a mention as an import",
            "delete a historical file because it names talib",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the import",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    banned = IMPORT_TALIB.search("import talib\nx = 1\n")
    mention = IMPORT_TALIB.search("note = 'do not import talib'\n")
    card = check()
    ok = bool(banned) and mention is None and card["lock_success"] and card["installed"] is False
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
