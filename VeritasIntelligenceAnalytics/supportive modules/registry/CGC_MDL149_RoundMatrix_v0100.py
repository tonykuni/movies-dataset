#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One round. Classify first. This round writes nothing in the open subsystems."""
from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LAWS = HERE / "VIA_Policy_Laws_SSOT_v0100.json"
LOCK = HERE / "VIA_EntryLock_v0100.json"
OUT = VIA / "VIA_Reports" / "vcgc" / "ROUND_latest.json"


def locate(source: str, name: str) -> dict:
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return {"name": name, "line": 0, "why": f"SyntaxError {exc.lineno}"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.name == name:
            return {"name": name, "line": node.lineno, "end": node.end_lineno, "precise": True}
    return {"name": name, "line": 0, "precise": False}


def _sha(path: Path) -> dict:
    raw = path.read_bytes() if path.is_file() else b""
    norm = raw.replace(b"\r\n", b"\n")
    return {"raw16": hashlib.sha256(raw).hexdigest()[:16], "norm16": hashlib.sha256(norm).hexdigest()[:16], "cr": raw.count(b"\r")}


def _diff() -> str:
    try:
        out = subprocess.run(
            ["git", "diff", "--numstat", "--", "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Policy_Laws_SSOT_v0100.json"],
            cwd=VIA.parent, capture_output=True, text=True, timeout=20,
        )
        return (out.stdout or out.stderr or "").strip()[:200]
    except Exception as exc:
        return type(exc).__name__


def classify(expected: str, live: dict) -> dict:
    same = live["norm16"] == expected or live["raw16"] == expected
    serial = [
        {"id": "policy_bytes", "order": 1, "write": False, "why": "bytes differ from the lock; do not rewrite the book" if not same else "hash matches; leave it locked"},
        {"id": "vdf_logic", "order": 2, "write": False, "why": "card book is drifted; report only, never hand-edit"},
        {"id": "handover", "order": 3, "write": False, "why": "one publish feeds both VDF and VRN; not in a logic round"},
        {"id": "vrn_logic", "order": 4, "write": False, "why": "two stale tails, one FAIL, six behind; name them before any edit"},
        {"id": "vrn_engine", "order": 5, "write": False, "why": "NODATA is missing input, not a broken engine"},
    ]
    return {
        "via": "vcgc",
        "round": 1,
        "policy_hash_same": same,
        "policy_sha": live,
        "diff": _diff() if not same else "",
        "parallel_write": [],
        "serial": serial,
        "fixed_this_round": ["classifier added", "newline no longer looks like a changed book"],
        "ast": {"used": False, "why": "no production function was edited"},
        "do_not": ["rewrite VIA_Policy_Laws_SSOT", "hand-edit the card book", "page --publish", "edit VRN logic in this round"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[輪次] 拒絕。只能經 via-vcgc。")
        return 2
    expected = json.loads(LOCK.read_text(encoding="utf-8")).get("policy_sha16", "")
    body = classify(expected, _sha(LAWS))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0


def selftest() -> int:
    found = locate("def alpha():\n    return 1\n", "alpha")
    body = classify("aaaaaaaaaaaaaaaa", {"raw16": "bbbbbbbbbbbbbbbb", "norm16": "bbbbbbbbbbbbbbbb", "cr": 0})
    same = classify("aaaaaaaaaaaaaaaa", {"raw16": "aaaaaaaaaaaaaaaa", "norm16": "aaaaaaaaaaaaaaaa", "cr": 0})
    ok = found["line"] == 1 and found["precise"] is True
    ok = ok and body["parallel_write"] == [] and [x["order"] for x in body["serial"]] == [1, 2, 3, 4, 5]
    ok = ok and same["policy_hash_same"] is True and body["policy_hash_same"] is False
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
