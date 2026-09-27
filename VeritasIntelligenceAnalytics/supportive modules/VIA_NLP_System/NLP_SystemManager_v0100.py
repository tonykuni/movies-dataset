#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One outside door for the NLP roster. The engines stay inside and are not called."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
ROSTER = VIA / "supportive modules" / "registry" / "VIA_NLP_Roster_v0100.json"
TOKEN = VIA / "supportive modules" / "VIA_TokenSave_v0100.py"


def check() -> dict:
    book = json.loads(ROSTER.read_text(encoding="utf-8")) if ROSTER.is_file() else {"rows": [], "called": True}
    missing = [row["id"] for row in book["rows"] if not (VIA / row["path"]).is_file()]
    return {
        "via": "vcgc",
        "door": "NLP_SystemManager_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "tier": "support",
        "peers": ["accelerator", "network", "nlp"],
        "outside_dock": 1,
        "up": {"to": "token_save", "n": 1, "file": TOKEN.name, "present": TOKEN.is_file()},
        "engines": len(book["rows"]),
        "future_entry": "oneengine_190",
        "called": False,
        "ran_engines": False,
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "let a single NLP engine dock outside",
            "merge accelerator, network, and nlp",
            "call the roster from the report door",
            "delete an older NLP engine",
            "download optional models",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing and book.get("called") is False else "do not unlock; name the drift",
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
    ok = denied and card["outside_dock"] == 1 and card["up"]["n"] == 1 and card["called"] is False and card["ran_engines"] is False and card["engines"] == 13 and card["next"] == "none"
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
