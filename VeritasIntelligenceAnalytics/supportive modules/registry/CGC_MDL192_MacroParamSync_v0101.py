#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same parameter check. Line endings are not a drift."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PARAMS = HERE / "VIA_USMacro_Params_v0100.json"
INDEX = HERE / "VIA_Central_Params_SSOT_v0100.json"


def _prior():
    spec = importlib.util.spec_from_file_location("param_v0100", HERE / "CGC_MDL192_MacroParamSync_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canon(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def check() -> dict:
    card = _prior().check()
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    hit = [row for row in index["books"] if row["id"] == "USMACRO_PARAMS"]
    sha = hashlib.sha256(canon(PARAMS.read_bytes())).hexdigest()
    card["hash_match"] = bool(hit) and hit[0].get("sha256") == sha
    card["door"] = "CGC_MDL192_v0101"
    card["next"] = "none" if card["hash_match"] and card["hub"] == "v0110" else "register"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["hash_match"] else 2


def selftest() -> int:
    stored = json.loads(INDEX.read_text(encoding="utf-8"))
    want = next(row["sha256"] for row in stored["books"] if row["id"] == "USMACRO_PARAMS")
    raw = PARAMS.read_bytes()
    crlf = hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest()
    card = check()
    ok = (
        hashlib.sha256(canon(raw.replace(b"\n", b"\r\n"))).hexdigest() == want
        and crlf != want
        and card["hash_match"]
        and card["parameters"] == 33
        and card["hub"] == "v0110"
        and card["books"] == 67
    )
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(card, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
