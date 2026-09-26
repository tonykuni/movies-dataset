#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe the AKShare macro candidates. Does not install the package and does not record a miss as a synonym."""
from __future__ import annotations

import ast
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "VDF_ENG090_DataCoverageGate_v0106.py"


def candidates() -> list[tuple]:
    tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "MACRO_CANDIDATES" for t in node.targets):
            return ast.literal_eval(node.value)
    raise RuntimeError("MACRO_CANDIDATES missing")


def probe() -> dict:
    try:
        import akshare as ak
    except ImportError:
        ak = None
    rows = []
    for group, name, fns in candidates():
        for fn in fns:
            row = {"id": fn, "group": group, "name": name}
            if ak is None:
                row.update({"state": "ABSENT", "why": "akshare is not installed"})
            elif not hasattr(ak, fn):
                row.update({"state": "MISSING", "why": "function is not on this akshare"})
            else:
                try:
                    frame = getattr(ak, fn)()
                    n = len(frame) if hasattr(frame, "__len__") else None
                    row.update({"state": "LIVE", "rows": n})
                except Exception as exc:
                    row.update({"state": "FAIL", "why": type(exc).__name__})
            rows.append(row)
    counts = {}
    for row in rows:
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    verified = [row["id"] for row in rows if row["state"] == "LIVE"]
    return {
        "via": "vcgc",
        "door": "VDF_ENG110_AKShareProbe_v0100",
        "probed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": SOURCE.name,
        "groups": len(candidates()),
        "functions": len(rows),
        "installed": ak is not None,
        "counts": counts,
        "verified": verified,
        "rows": rows,
        "intake_edited": False,
        "tree_edited": False,
        "do_not": [
            "pip install akshare from this door",
            "record a function that was not called",
            "let akshare replace FRED",
            "edit intake macro_ssot",
        ],
        "next": "none" if verified else "install akshare yourself, then run this door again",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = probe()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["installed"] else 2


def selftest() -> int:
    rows = candidates()
    us = [fn for group, _, fns in rows if group.startswith("US_") for fn in fns]
    card = probe()
    ok = (
        len(rows) == 16
        and "macro_usa_cpi_monthly" in us
        and len(us) == 8
        and card["verified"] == []
        and card["counts"].get("ABSENT") == card["functions"]
        and card["tree_edited"] is False
    )
    print("  [OK]" if ok else "  [FAIL] " + json.dumps({"groups": len(rows), "us": us, "counts": card["counts"]}, ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
