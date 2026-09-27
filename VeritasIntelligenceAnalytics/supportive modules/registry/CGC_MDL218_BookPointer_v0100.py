#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Point the new VCGC routes at the locked policy, logic, and parameter books.

The three books are not rewritten. support and matrix add no law and no parameter.
Logic stays on the VRN reader. This file only records that.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = HERE / "VIA_VCGC_BookPointer_v0100.json"
LAWS = HERE / "VIA_Policy_Laws_SSOT_v0100.json"
LOCK = HERE / "VIA_EntryLock_v0100.json"
PARAMS = HERE / "VIA_Central_Params_SSOT_v0100.json"


def check() -> dict:
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    locked = json.loads(LOCK.read_text(encoding="utf-8"))
    params = json.loads(PARAMS.read_text(encoding="utf-8"))
    live = hashlib.sha256(LAWS.read_bytes()).hexdigest()[:16]
    missing = []
    if note.get("book_edited") is not False:
        missing.append("note")
    if live != locked.get("policy_sha16") or live != note.get("policy_sha16"):
        missing.append("policy_sha")
    if params.get("books_total") != note.get("param_books"):
        missing.append("param_books")
    for route in note.get("routes") or []:
        if not (HERE / route["door"]).is_file():
            missing.append(route["verb"])
        if route.get("policy") != "no new law" or route.get("params") != "none":
            missing.append(route["verb"] + "_claim")
    return {
        "via": "vcgc",
        "door": "CGC_MDL218_BookPointer_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "policy_book": note["policy_book"],
        "policy_sha16": live,
        "policy_edited": False,
        "logic_reader": note["logic_reader"],
        "logic_edited": False,
        "param_book": note["param_book"],
        "param_books": params.get("books_total"),
        "param_edited": False,
        "routes": [row["verb"] for row in note["routes"]],
        "missing": missing,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "rewrite the locked policy book",
            "add a 68th parameter book",
            "write the logic book from this door",
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
    ok = denied and card["policy_edited"] is False and card["param_books"] == 67 and card["next"] == "none"
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
