#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC closeout. The console stops here. Open lamps stay open. Nothing is applied."""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
OUT = VIA / "VIA_Reports" / "vcgc" / "CLOSEOUT_latest.json"

DOORS = {
    "policy": "CGC_MDL149_VeritasCentralGovernanceConsole_v0144.py",
    "entry": "CGC_MDL149_EntryLock_v0100.py",
    "matrix": "CGC_MDL149_WorkflowMatrix_v0100.py",
    "dragon": "CGC_MDL149_OneDragon_v0100.py",
    "sync": "CGC_MDL189_GitHubSyncEngine_v0101.py",
    "paste": "CGC_MDL149_PasteBlock_v0101.py",
    "ast": "CGC_MDL158_VIAPanoramaAuditRepair_v0113.py",
}
OPEN = ["vdf_logic", "vdf_bridge", "vdf_handover", "vrn_logic", "vrn_engine", "vrn_handover", "env_rename_5", "numbering_plan", "tools_plan"]
WITHHELD = ["registry-sync --apply", "TOOLS_PLAN_latest.ps1", "page --publish", "eight-hub --execute", "git pull --rebase"]


def score() -> dict:
    doors = {name: "PRESENT" if (HERE / file_name).is_file() else "GAP" for name, file_name in DOORS.items()}
    gaps = [name for name, state in doors.items() if state != "PRESENT"]
    return {
        "via": "vcgc",
        "decision": "CLOSED_HOLD" if not gaps else "GAP",
        "why": "console doors are present; the open lamps are not fixed in this closeout",
        "doors": doors,
        "locked": list(DOORS),
        "open": OPEN,
        "withheld": WITHHELD,
        "applied": False,
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[收尾] 拒絕。只能經 via-vcgc。")
        return 2
    body = score()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if body["decision"] == "CLOSED_HOLD" else 2


def selftest() -> int:
    body = score()
    ok = body["decision"] == "CLOSED_HOLD" and not any(v != "PRESENT" for v in body["doors"].values())
    ok = ok and "registry-sync --apply" in body["withheld"] and body["next"] == "none" and "vdf_bridge" in body["open"]
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(body["doors"]))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
