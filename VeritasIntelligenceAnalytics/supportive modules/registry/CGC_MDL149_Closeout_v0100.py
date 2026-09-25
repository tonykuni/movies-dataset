#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC closeout. Scores the control plane and holds the unrun install plan."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
PASTE = VIA / "VIA_Reports" / "vcgc" / "PASTE_latest.json"
OUT = VIA / "VIA_Reports" / "vcgc" / "CLOSEOUT_latest.json"


def _newest(folder: Path, prefix: str) -> str:
    if not folder.is_dir():
        return ""
    names = sorted(path.name for path in folder.glob(prefix))
    return names[-1] if names else ""


def completeness(root: Path) -> list[dict]:
    rows = [
        ("single_entry", "PRESENT", "via-vcgc"),
        ("policy_gate", "PRESENT", "policy_step"),
        ("token_gate", "PRESENT", "require_token_gate"),
        ("registry_plan", "PRESENT", "registry-sync"),
        ("registry_apply", "WITHHELD", "not run from closeout"),
        ("env_create", "WITHHELD", "stages stay unrun"),
        ("paste", "PRESENT", "CGC_MDL149_PasteBlock_v0101.py"),
        ("vdf_manager", "PRESENT" if _newest(root / "functional modules" / "VDF", "VDF_SystemManager_v*.py") else "GAP", _newest(root / "functional modules" / "VDF", "VDF_SystemManager_v*.py")),
        ("vrn_manager", "PRESENT" if _newest(root / "functional modules" / "VRN", "VRN_SystemManager_v*.py") else "GAP", _newest(root / "functional modules" / "VRN", "VRN_SystemManager_v*.py")),
        ("vap_manager", "PRESENT" if _newest(root / "functional modules" / "VAP", "VAP_SystemManager_v*.py") else "GAP", _newest(root / "functional modules" / "VAP", "VAP_SystemManager_v*.py")),
        ("live_alert", "GAP", "status is pull, not a push"),
        ("auto_heal", "ABSENT_ON_PURPOSE", "LL11"),
    ]
    return [{"fn": fn, "state": state, "note": note} for fn, state, note in rows]


def decide(paste: dict) -> dict:
    tools = paste.get("tools") or {}
    missing = paste.get("missing_env") or []
    reasons = []
    if tools.get("stages_ran") is False:
        reasons.append("six stages were not run")
    if missing:
        reasons.append("missing envs stay missing: " + ", ".join(str(x.get("env")) for x in missing))
    reasons.append("LL11: do not stack installs on a bad base")
    reasons.append("LL54: do not revive TA-Lib")
    return {
        "decision": "HOLD",
        "why": reasons,
        "next": "none",
        "do_not": paste.get("do_not") or ["TOOLS_PLAN_latest.ps1", "registry-sync --apply"],
    }


def closeout(root: Path, paste: dict) -> dict:
    rows = completeness(root)
    decision = decide(paste)
    return {
        "via": "vcgc",
        "decision": decision["decision"],
        "why": decision["why"],
        "do_not": decision["do_not"],
        "next": "none",
        "completeness": rows,
        "gap": [row["fn"] for row in rows if row["state"] == "GAP"],
        "withheld": [row["fn"] for row in rows if row["state"] == "WITHHELD"],
    }


def main() -> int:
    paste = {}
    if PASTE.is_file():
        paste = json.loads(PASTE.read_text(encoding="utf-8"))
    body = closeout(VIA, paste)
    body["logged_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0


def selftest() -> int:
    sample = {
        "tools": {"stages_ran": False},
        "missing_env": [{"env": "via_iso_ml_cuda_H"}],
        "do_not": ["TOOLS_PLAN_latest.ps1"],
    }
    body = closeout(VIA, sample)
    ok = body["decision"] == "HOLD" and body["next"] == "none"
    ok = ok and "vdf_manager" in {row["fn"] for row in body["completeness"] if row["state"] == "PRESENT"}
    ok = ok and "auto_heal" in {row["fn"] for row in body["completeness"] if row["state"] == "ABSENT_ON_PURPOSE"}
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(body, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
