#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read the VDF fetch matrix. Does not download and does not edit the hub."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BOOK = Path(__file__).resolve().parent / "VIA_VDF_FetchMatrix_v0100.json"


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    ids = [row["id"] for row in book["classes"]]
    since = {
        row["id"]: row["since"] or book["default_since"]
        for row in book["classes"]
    }
    symbol_since = [row["id"] for row in book["classes"] if row.get("symbol_since")]
    return {
        "via": "vcgc",
        "door": "CGC_MDL195_FetchMatrix_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "default_since": book["default_since"],
        "classes": len(ids),
        "ids": ids,
        "since": since,
        "symbol_since": symbol_since,
        "forms": next(row["forms"] for row in book["classes"] if row["id"] == "VDF-TW-FIN"),
        "tests": [{"id": row["id"], "market": row["market"], "class_id": row["class_id"]} for row in book["tests"]],
        "read": book["store"]["read"],
        "write": book["store"]["write"],
        "knobs": book["knobs"],
        "hub_edited": False,
        "intake_edited": False,
        "fetched": False,
        "do_not": book["do_not"],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    dup = len(card["ids"]) != len(set(card["ids"]))
    return 0 if not dup else 2


def selftest() -> int:
    card = check()
    ok = (
        card["default_since"] == "2023-01-01"
        and card["since"]["VDF-US-MACRO"] == "2020-01-01"
        and card["since"]["VDF-TW-EQ"] == "2023-01-01"
        and card["symbol_since"] == ["VDF-TW-FIN"]
        and card["forms"] == ["quarter", "ytd", "annual"]
        and [row["id"] for row in card["tests"]] == ["2330", "3324", "NVDA"]
        and card["tests"][1]["market"] == "TWSE"
        and card["fetched"] is False
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
