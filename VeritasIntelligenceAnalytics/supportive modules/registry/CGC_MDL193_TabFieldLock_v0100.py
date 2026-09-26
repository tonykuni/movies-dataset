#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lock the three VRN tab field lists. Does not read a report."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
BOOK = HERE / "VIA_VRN_TabFields_v0100.json"
LOGIC = VIA / "functional modules" / "VRN" / "references" / "intake" / "VIA_VRNLogic_AllInOne_v0201_b504" / "VIA_VRNLogic_AllInOne_v0201.py"
STORE = VIA / "functional modules" / "VRN" / "VRN_ENG109_TabStore_v0100.py"
HELD = (
    VIA / "supportive modules" / "registry" / "CGC_MDL192_MacroParamSync_v0101.py",
    VIA / "supportive modules" / "registry" / "CGC_MDL191_KnowledgeAsset_v0100.py",
    VIA / "supportive modules" / "registry" / "CGC_MDL193_StatusLock_v0105.py",
    VIA / "supportive modules" / "registry" / "CGC_MDL193_ProbeLock_v0100.py",
    VIA / "supportive modules" / "registry" / "CGC_MDL193_MarketSync_v0101.py",
    VIA / "supportive modules" / "registry" / "CGC_MDL193_ForwardVintageLock_v0101.py",
    VIA / "supportive modules" / "registry" / "CGC_SystemManager_v0100.py",
    VIA / "functional modules" / "VRN" / "VRN_ENG109_TabStore_v0101.py",
)


def _fields(text: str, key: str) -> list[str]:
    body = text.split(f'"{key}": (', 1)[1].split("),", 1)[0]
    return [part.strip().strip('"') for part in body.split(",") if part.strip()]


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    spec = importlib.util.spec_from_file_location("tab_store_fields", STORE)
    store = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(store)
    logic = LOGIC.read_text(encoding="utf-8")
    basic = next(tab["fields"] for tab in book["tabs"] if tab["tab"] == "BASIC INFO")
    page = next(tab for tab in book["tabs"] if tab["tab"] == "PAGE 1")
    financial = next(tab["fields"] for tab in book["tabs"] if tab["tab"] == "FINANCIAL DATA")
    drift = []
    if basic != list(store.BASIC) or basic != _fields(logic, "basic_info"):
        drift.append("basic")
    if financial != list(store.FINANCIAL) or financial != _fields(logic, "financial_data"):
        drift.append("financial")
    if page["fields"] != ["fileId", "fileName", "page", "fixed_page1", "summary_page1"]:
        drift.append("page1")
    if len(page["cells"]) != 2:
        drift.append("cells")
    missing = [path.name for path in HELD if not path.is_file()]
    if missing:
        drift.append("held")
    return {
        "via": "vcgc",
        "door": "CGC_MDL193_TabFieldLock_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": drift == [],
        "basic_fields": len(basic),
        "page1_fields": len(page["fields"]),
        "page1_cells": page["cells"],
        "financial_fields": len(financial),
        "held": book["held"],
        "missing": missing,
        "open": book["open"],
        "github": "pull_only",
        "drift": drift,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": book["do_not"],
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
    ok = card["lock_success"] and card["basic_fields"] == 22 and card["financial_fields"] == 14 and card["page1_fields"] == 5 and card["missing"] == []
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
