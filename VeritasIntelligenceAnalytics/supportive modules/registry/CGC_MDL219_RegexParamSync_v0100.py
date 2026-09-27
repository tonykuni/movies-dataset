#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Record that the regex book, the synonym book, and the parameter book agree.

The three books are not rewritten. A locked pattern that differs is named, not changed.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = HERE / "VIA_VCGC_RegexParamRecord_v0100.json"


def check() -> dict:
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    regex = json.loads((HERE / note["regex_book"]).read_text(encoding="utf-8"))
    params = json.loads((HERE / note["param_book"]).read_text(encoding="utf-8"))
    union = json.loads((HERE / note["synonym_book"]).read_text(encoding="utf-8"))
    align = {row["name"]: row["pattern"] for row in params.get("locked_alignment") or []}
    patterns = regex.get("regex") or {}
    drift = []
    for name in note["aligned"]:
        left = align.get(name)
        raw = patterns.get(name)
        right = raw.get("pattern") if isinstance(raw, dict) else raw
        if left != right or left is None:
            drift.append(name)
    missing = []
    if note.get("book_edited") is not False:
        missing.append("note")
    if params.get("books_total") != note.get("param_books"):
        missing.append("param_books")
    if not any(row.get("id") == note["param_id"] for row in params.get("books") or []):
        missing.append("param_id")
    if union.get("version") != note.get("synonym_version"):
        missing.append("synonym_version")
    if (union.get("tally") or {}).get("CONFLICT") != note.get("synonym_conflicts_stay"):
        missing.append("conflicts")
    if not (HERE / note["regex_dict"]).is_file():
        missing.append("regex_dict")
    if drift:
        missing.append("pattern")
    return {
        "via": "vcgc",
        "door": "CGC_MDL219_RegexParamSync_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "lock_record": NOTE.name,
        "lock_path": [NOTE.name, "CGC_MDL219_RegexParamSync_v0100.py", note["regex_book"], note["synonym_book"], note["param_book"]],
        "regex_book": note["regex_book"],
        "synonym_book": note["synonym_book"],
        "synonym_version": union.get("version"),
        "param_books": params.get("books_total"),
        "aligned": len(note["aligned"]),
        "drift": drift,
        "conflicts_stay": (union.get("tally") or {}).get("CONFLICT"),
        "book_edited": False,
        "intake_edited": False,
        "missing": missing,
        "do_not": [
            "rewrite a locked pattern",
            "delete a recorded synonym conflict",
            "add a 68th parameter book",
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
    ok = denied and card["lock_success"] and card["aligned"] == 12 and card["param_books"] == 67
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"] + card["drift"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
