#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door for agency sources. Read-only. Does not fetch."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

BOOK = Path(__file__).resolve().parents[1] / "VDF_USMacro_Agencies_v0100.json"


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    by = {a["id"]: a for a in book["agencies"]}
    bls = by["BLS"]["rows"]
    agree = [r["bls_id"] for r in bls if str(r["cross"]).startswith("AGREE")]
    irs = by["IRS"]
    tax = [r for r in by["TREASURY"]["rows"] if r.get("endpoint", "").endswith("mts_table_4")]
    return {
        "via": "vcgc",
        "door": "VDF_ENG111",
        "agencies": ["BLS", "TREASURY", "IRS"],
        "bls_cross": agree,
        "cpi_synonym": False,
        "treasury_rows": len(by["TREASURY"]["rows"]),
        "irs": irs["state"],
        "tax_lines": len(tax),
        "do_not": ["call a private IRS feed", "add the FRED deficit to the Treasury deficit", "treat CUSR0000SA0 as a synonym of CPIAUCSL"],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    card = check()
    ok = card["bls_cross"] == ["LNS14000000", "CES0000000001", "CUSR0000SA0"] and card["irs"] == "THROUGH_TREASURY" and card["tax_lines"] == 3 and card["cpi_synonym"] is False
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
