#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register US macro parameters into the VCGC index. Does not move source books."""
from __future__ import annotations
import hashlib, importlib.util, json, os, sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
PARAMS = HERE / "VIA_USMacro_Params_v0100.json"
INDEX = HERE / "VIA_Central_Params_SSOT_v0100.json"
HUB = HERE / "via_params_central_v0109.py"

def check() -> dict:
    book = json.loads(PARAMS.read_text(encoding="utf-8"))
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    hit = [b for b in index["books"] if b["id"] == "USMACRO_PARAMS"]
    raw = PARAMS.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    linked = bool(hit) and hit[0].get("sha256") == sha
    live = [r for r in book["parameters"] if r["state"] == "LIVE" and r["role"] == "method_series"]
    return {
        "via": "vcgc", "door": "CGC_MDL192",
        "parameters": len(book["parameters"]), "method_series": len(live),
        "indexed": bool(hit), "hash_match": linked, "books": index["books_total"],
        "intake_edited": False,
        "do_not": ["edit intake macro_ssot", "treat RRP billions as millions"],
        "next": "none" if linked else "register",
    }

def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    print(json.dumps(check(), ensure_ascii=False, indent=1))
    return 0 if check()["hash_match"] else 2

def selftest() -> int:
    card = check()
    book = json.loads(PARAMS.read_text(encoding="utf-8"))
    rrp = next(r for r in book["parameters"] if r["id"] == "RRPONTSYD")
    ok = card["hash_match"] and card["method_series"] == 18 and rrp["scale_to_millions"] == 1000
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
