#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door for the two-name live check. Does not open the gate itself."""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
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
