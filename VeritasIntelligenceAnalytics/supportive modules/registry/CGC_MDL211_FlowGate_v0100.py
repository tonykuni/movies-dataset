#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One gate. Read the policy book, then a ps1 may be written.

The law book is not rewritten. policy_step stays the only executor.
A script that skips this gate is not produced here.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE / "VIA_Policy_Laws_SSOT_v0100.json"
NOTE = HERE / "VIA_Policy_TalibBan_v0101.json"
EXECUTOR = HERE / "CGC_MDL207_PolicyRun_v0101.py"
ORDER = ["enter", "read_policy", "emit_ps", "exit"]
_READ = False

HEADER = """# Generated after the VCGC policy read. Do not skip the mark.
$ErrorActionPreference = "Stop"
if ($env:VIA_FROM_VCGC -ne "YES") {
  Write-Output '{"via":"vcgc","state":"DENY","why":"ps must enter through vcgc"}'
  exit 2
}
"""


def _marked() -> bool:
    return os.environ.get("VIA_FROM_VCGC") == "YES"


def _deny(why: str) -> dict:
    return {
        "via": "vcgc",
        "door": "CGC_MDL211_FlowGate_v0100",
        "state": "DENY",
        "why": why,
        "book_written": False,
        "ps_written": False,
    }


def read_policy() -> dict:
    global _READ
    if not _marked():
        return _deny("enter through VCGC")
    before = BOOK.stat().st_mtime_ns
    laws = json.loads(BOOK.read_text(encoding="utf-8"))
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    row = next(item for item in laws["laws"] if item.get("id") == "L50")
    _READ = True
    return {
        "via": "vcgc",
        "door": "CGC_MDL211_FlowGate_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "verb": "read",
        "order": ORDER,
        "laws": len(laws.get("laws") or []),
        "lessons": len(laws.get("lessons") or []),
        "policy_id": row["id"],
        "rank": row["rank"],
        "status": row["status"],
        "book_edited": note.get("book_edited"),
        "executor": EXECUTOR.name,
        "second_engine": False,
        "book_written": BOOK.stat().st_mtime_ns != before,
        "ps_written": False,
        "intake_edited": False,
        "do_not": [
            "rewrite the locked policy book",
            "add a second policy engine",
            "write a ps1 before read_policy",
            "edit intake macro_ssot",
        ],
        "next": "none",
    }


def update_policy() -> dict:
    """Refresh the read. The locked book stays byte-for-byte."""
    card = read_policy()
    if card.get("state") == "DENY":
        return card
    card["verb"] = "update"
    card["updated"] = False
    card["next"] = "none" if card["book_written"] is False else "stop; the book changed"
    return card


def emit_ps(dest: Path, body: str) -> dict:
    if not _marked():
        return _deny("enter through VCGC")
    if not _READ:
        return _deny("read policy first")
    dest = Path(dest)
    if dest.suffix.lower() != ".ps1":
        return _deny("only a ps1")
    if "references/intake" in dest.as_posix():
        return _deny("intake is closed")
    text = HEADER + body.strip() + "\n"
    if "VIA_FROM_VCGC" not in text:
        return _deny("the mark check is required")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return {
        "via": "vcgc",
        "door": "CGC_MDL211_FlowGate_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "verb": "emit_ps",
        "order": ORDER,
        "ps_written": True,
        "file": dest.name,
        "book_written": False,
        "intake_edited": False,
        "next": "none",
    }


def main() -> int:
    if "update" in sys.argv[1:]:
        card = update_policy()
    elif "ps" in sys.argv[1:]:
        card = read_policy()
        if card.get("state") != "DENY":
            card["verb"] = "ps"
            card["ps_written"] = False
    else:
        card = read_policy()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    if card.get("state") == "DENY":
        return 2
    if card.get("book_written"):
        return 2
    return 0


def selftest() -> int:
    import tempfile
    global _READ
    os.environ.pop("VIA_FROM_VCGC", None)
    _READ = False
    denied = read_policy().get("state") == "DENY"
    os.environ["VIA_FROM_VCGC"] = "YES"
    _READ = False
    early = emit_ps(Path("nope.ps1"), "Write-Output 1")
    before = BOOK.stat().st_mtime_ns
    card = update_policy()
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "Invoke-VIA-VCGC-Sample.ps1"
        written = emit_ps(path, "Write-Output '{\"via\":\"vcgc\"}'")
        text = path.read_text(encoding="utf-8") if path.is_file() else ""
    ok = (
        denied
        and early.get("why") == "read policy first"
        and card["policy_id"] == "L50"
        and card["rank"] == 2
        and card["book_written"] is False
        and card["updated"] is False
        and BOOK.stat().st_mtime_ns == before
        and written["ps_written"] is True
        and "VIA_FROM_VCGC" in text
        and "read policy first" not in text
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
