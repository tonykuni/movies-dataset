#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA and VCGC are one door. Not two systems."""
from __future__ import annotations

import json
import sys

SAME = {"name": "VIA", "door": "VCGC", "via": "vcgc", "same": True}


def card() -> dict:
    return dict(SAME)


def accept(row: dict) -> bool:
    if row.get("via") != "vcgc":
        return False
    name = row.get("name")
    return name in (None, "VIA")


def main() -> int:
    print(json.dumps(card(), ensure_ascii=False))
    return 0


def selftest() -> int:
    fails = []

    def chk(name, ok):
        if not ok:
            fails.append(name)
        print(f"  [{'OK' if ok else 'FAIL'}] {name}")

    got = card()
    chk("VIA is the VCGC door", got["name"] == "VIA" and got["door"] == "VCGC" and got["via"] == "vcgc" and got["same"] is True)
    chk("a vcgc card is accepted", accept({"via": "vcgc"}))
    chk("a card that names VIA is accepted", accept({"via": "vcgc", "name": "VIA"}))
    chk("a second door is refused", accept({"via": "other", "name": "VIA"}) is False)
    print(f"  [計] FAIL {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
