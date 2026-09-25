#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The lock above the policy book. VCGC is the only door. A locked item is not reopened."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LOCK = HERE / "VIA_EntryLock_v0100.json"
LAWS = HERE / "VIA_Policy_Laws_SSOT_v0100.json"
OUT = VIA / "VIA_Reports" / "vcgc" / "ENTRY_latest.json"


def allowed() -> bool:
    return os.environ.get("VIA_FROM_VCGC") == "YES"


def matrix() -> dict:
    spec = json.loads(LOCK.read_text(encoding="utf-8"))
    live = hashlib.sha256(LAWS.read_bytes()).hexdigest()[:16] if LAWS.is_file() else ""
    same = live == spec.get("policy_sha16")
    return {
        "via": "vcgc",
        "door": spec["door"],
        "entered": allowed(),
        "policy": {"locked": same, "sha16": live, "expected": spec.get("policy_sha16")},
        "locked": spec["locked"],
        "open": spec["open"],
        "why_not_closed": "VDF logic STALE and VRN logic RED are still open",
        "do_not": ["reopen a locked item", "python a manager without VIA_FROM_VCGC", "TOOLS_PLAN_latest.ps1"],
        "next": "none" if spec["open"] else "vdf-vrn",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def main() -> int:
    if not allowed():
        print("[入口] 拒絕。只能經 via-vcgc。")
        return 2
    body = matrix()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if body["policy"]["locked"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = not allowed()
    os.environ["VIA_FROM_VCGC"] = "YES"
    body = matrix()
    os.environ.pop("VIA_FROM_VCGC", None)
    ok = denied and body["policy"]["locked"] and "vdf_logic" in body["open"] and "token_gate" in body["locked"]
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
