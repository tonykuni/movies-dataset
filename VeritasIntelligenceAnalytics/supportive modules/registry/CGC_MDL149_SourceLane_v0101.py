#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door for the two-name live check. Does not open the gate itself."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
ENG = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG102_SourceLane_v0101.py"


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VDF] 拒絕。只能經 via-vcgc。")
        return 2
    spec = importlib.util.spec_from_file_location("src_live", ENG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    net_path = sorted((VIA / "supportive modules" / "network").glob("via_net_unified_v*.py"))[-1]
    nspec = importlib.util.spec_from_file_location("via_net", net_path)
    net = importlib.util.module_from_spec(nspec)
    nspec.loader.exec_module(net)
    body = {
        "via": "vcgc",
        "live": mod.live(net),
        "do_not": ["full-market backfill", "hand-edit the policy book"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    states = [row.get("state") for row in body["live"]["rows"]]
    return 0 if states == ["OK", "OK"] else 2


if __name__ == "__main__":
    sys.exit(main())
