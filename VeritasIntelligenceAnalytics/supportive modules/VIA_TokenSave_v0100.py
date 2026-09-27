#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upper seat. A support tool may dock here once. This seat does not run an engine."""
from __future__ import annotations

import json
import os
import sys

SUPPORTERS = ("accelerator", "network", "nlp")


def check() -> dict:
    return {
        "via": "vcgc",
        "door": "VIA_TokenSave_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "tier": "token_save",
        "from": [{"id": name, "n": 1} for name in SUPPORTERS],
        "ran": False,
        "rule": "call the existing engine and print the card; do not paste its source",
        "do_not": [
            "let one supporter dock here twice",
            "let a single engine dock here",
            "rewrite an engine to save tokens",
        ],
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    print(json.dumps(check(), ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
