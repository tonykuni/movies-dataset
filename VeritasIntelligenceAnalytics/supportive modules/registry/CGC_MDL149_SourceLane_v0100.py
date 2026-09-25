#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read the TWSE / TPEX / yfinance card. No fetch."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENG = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG102_SourceLane_v0100.py"


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    spec = importlib.util.spec_from_file_location("src_lane", ENG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    card = mod.lane()
    body = {
        "via": "vcgc",
        "lane": card,
        "sample": {"2330": mod.yahoo_symbol("2330", "TWSE"), "6488": mod.yahoo_symbol("6488", "TPEX")},
        "do_not": ["fetch", "hand-edit the policy book"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if all(card["files"].values()) else 1


if __name__ == "__main__":
    sys.exit(main())
