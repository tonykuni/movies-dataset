#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Register the VCGC and VDF tails that just passed. This door does not fetch.

WATERLAND is not a live broker name. 兆豐 shows MEGA. The chain file is not invented.
"""
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
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
NOTE = HERE / "VIA_VCGC_SystemBackup_v0100.json"


def check() -> dict:
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    missing = []
    vcgc = HERE / note["vcgc"]
    vdf = VIA / "functional modules" / "VDF" / note["vdf"]
    chain = HERE / note["chain"]
    show = VIA / "functional modules" / "VRN" / note["show"]
    for path, name in ((vcgc, "vcgc"), (vdf, "vdf"), (chain, "chain"), (show, "show"), (NOTE, "note")):
        if not path.is_file():
            missing.append(name)
    text = show.read_text(encoding="utf-8") if show.is_file() else ""
    if '"兆豐": "MEGA"' not in text or "WATERLAND" not in text:
        missing.append("display")
    if (VIA / "VIA_Reports" / "vdf_chain" / "VDFCHAIN_latest.json").is_file():
        missing.append("chain_file")
    if note["lamps"].get("engine") != "NODATA":
        missing.append("engine")
    green = [name for name, lamp in note["lamps"].items() if lamp == "GREEN"]
    return {
        "via": "vcgc",
        "door": "CGC_MDL221_SystemBackup_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "lock_record": NOTE.name,
        "lock_path": [NOTE.name, note["vcgc"], note["vdf"], note["chain"], note["show"]],
        "green": len(green),
        "held": "engine",
        "mega": "MEGA",
        "dropped": note["dropped"],
        "kept_show": note["kept_show"],
        "chain_checks": note["chain_checks"],
        "chain_written": False,
        "book_edited": False,
        "intake_edited": False,
        "missing": missing,
        "do_not": [
            "write VDFCHAIN_latest.json from a plan",
            "map WATERLAND back onto 國票",
            "show 兆豐 as Chinese",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "do not unlock; name the drift",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card["lock_success"] and card["green"] == 8 and card["kept_show"] == "IBF"
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
