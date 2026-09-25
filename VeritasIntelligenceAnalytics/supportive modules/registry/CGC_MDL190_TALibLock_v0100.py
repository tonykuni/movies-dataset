#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC entry check. A live file may not import TA-Lib.

Comments and the kill-gate text are not imports. History docs stay.
The door is VIA_FROM_VCGC. This file does not install or delete.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime
from pathlib import Path

VIA = Path(__file__).resolve().parents[2]
SKIP = ("SCOPE_COPY", "Retired", "references/intake", "_inbox", "validation_evidence")
CODE = re.compile(r"""(?m)^\s*(?:import\s+talib\b|from\s+talib\b|talib\s*=\s*_si\(\s*["']talib["']\s*\))""")


def scan(root: Path | None = None) -> dict:
    root = root or VIA
    hits = []
    for path in root.rglob("*.py"):
        rel = str(path.relative_to(root)).replace("\\", "/")
        if any(part in rel for part in SKIP):
            continue
        if path.name.startswith("CGC_MDL187_") or path.name.startswith("CGC_MDL158_"):
            continue
        if path.resolve() == Path(__file__).resolve():
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if CODE.search(text):
            hits.append(rel)
    return {"state": "GREEN" if not hits else "RED", "imports": hits, "n": len(hits)}


def restore_point(scan_result: dict) -> dict:
    lock_path = VIA / "supportive modules" / "registry" / "VIA_ToolVersion_Lock_v0100.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.exists() else {}
    point = {
        "via": "vcgc",
        "kind": "restore_point",
        "policy": "L50",
        "door": "VIA_FROM_VCGC",
        "order": ["policy", "token", "env", "tools", "lock", "talib_scan", "handover"],
        "accelerator": lock.get("accelerator", {}).get("version"),
        "network": lock.get("network", {}).get("version"),
        "talib": scan_result,
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    out = VIA / "VIA_Reports" / "vcgc" / "RESTORE_20260926.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(point, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    point["path"] = str(out)
    return point


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "enter through via-vcgc"}, ensure_ascii=False))
        return 2
    result = scan()
    point = restore_point(result)
    print(json.dumps({"via": "vcgc", "talib": result["state"], "imports": result["n"],
                      "restore": point["path"], "next": "none"}, ensure_ascii=False, indent=1))
    return 0 if result["state"] == "GREEN" else 1


def selftest() -> int:
    bad = "import talib\n"
    quoted = 'if "import talib" in body:\n'
    assign = 'talib = _si("talib")\n'
    ok = CODE.search(bad) and not CODE.search(quoted) and CODE.search(assign)
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    import sys
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
