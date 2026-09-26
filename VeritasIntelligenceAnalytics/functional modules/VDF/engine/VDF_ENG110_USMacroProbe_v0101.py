#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same one-point probe. The key comes from the environment or the local key file, never from git."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
KEY_FILE = VDF / "output_hub" / "mega" / ".fred_api_key"
OUT = VDF / "VDF_USMacro_Probe_v0100.json"


def _prior():
    spec = importlib.util.spec_from_file_location("probe_v0100", HERE / "VDF_ENG110_USMacroProbe_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def key_from() -> tuple[str, str]:
    env = os.environ.get("FRED_API_KEY", "").strip()
    if env:
        return env, "env"
    if KEY_FILE.is_file():
        text = KEY_FILE.read_text(encoding="utf-8").strip()
        if text:
            return text, "keyfile"
    return "", "missing"


def run() -> dict:
    prior = _prior()
    key, source = key_from()
    os.environ["FRED_API_KEY"] = key
    card = prior.run()
    card["door"] = "VDF_ENG110_USMacroProbe_v0101"
    card["fred_key"] = source
    if source == "missing":
        card["next"] = "put the key in output_hub/mega/.fred_api_key or FRED_API_KEY, then run this door again"
    else:
        card["next"] = "none"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = run()
    OUT.write_text(json.dumps(card, ensure_ascii=False, indent=1), encoding="utf-8")
    show = dict(card)
    show["rows"] = [row for row in card["rows"] if row.get("state") != "SKIP"]
    print(json.dumps(show, ensure_ascii=False, indent=1))
    return 0 if card["fred_key"] != "missing" else 2


def selftest() -> int:
    os.environ.pop("FRED_API_KEY", None)
    missing, source = key_from()
    os.environ["FRED_API_KEY"] = "probe-selftest"
    found, found_source = key_from()
    os.environ.pop("FRED_API_KEY", None)
    ok = missing == "" and source == "missing" and found == "probe-selftest" and found_source == "env" and not KEY_FILE.exists()
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
