#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One check for the VRN logic book. The rules stay in their own files.

The architecture book is an index. Copying a rule into this file would open a
second head, and the copy would go stale first. This door reads that index,
finds the newest tail of each family, and names three states:

- current: the book already points at the newest file
- updated: a newer tail is on disk and the book has not moved
- missing: the book names a file that is not on disk

It does not rewrite the book, does not read a PDF, and does not write a tab.
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
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
BOOK = VIA / "supportive modules" / "registry" / "VIA_VRN_LogicArchitecture_SSOT_v0100.json"
VERSION = re.compile(r"_v(\d+)")
TALIB = re.compile(r"(?m)^[ \t]*(?:import[ \t]+talib\b|from[ \t]+talib[ \t]+import\b)")


def _version(name: str) -> int:
    found = VERSION.search(name)
    return int(found.group(1)) if found else -1


def _newest(folder: Path, family: str) -> Path | None:
    if not folder.is_dir():
        return None
    hits = list(folder.glob(family + "_v*.py"))
    plain = folder / (family + ".py")
    if plain.is_file():
        hits.append(plain)
    if not hits:
        return None
    return max(hits, key=lambda path: (_version(path.name), path.name))


def _talib(path: Path) -> bool:
    if not path.is_file():
        return False
    seen = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            seen += len(line)
            if TALIB.search(line):
                return True
            if seen > 2_000_000:
                return False
    return False


def _rows(book: dict) -> list[dict]:
    rows = []
    for layer, body in (book.get("layers") or {}).items():
        for node in body.get("nodes") or []:
            rows.append({"kind": "layer", "where": layer, **node})
    for name, node in (book.get("rule_canons") or {}).items():
        if isinstance(node, dict) and node.get("tail"):
            rows.append({"kind": "canon", "where": name, **node})
    return rows


def check() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    current = []
    updated = []
    missing = []
    talib = []
    for row in _rows(book):
        tail = str(row.get("tail") or "")
        family = str(row.get("family") or "")
        recorded = VIA / tail
        item = {
            "where": row.get("where"),
            "family": family,
            "role": row.get("role") or "",
            "book": Path(tail).name,
        }
        if not tail or not recorded.is_file():
            item["why"] = "book tail absent"
            missing.append(item)
            continue
        if recorded.suffix != ".py":
            item["disk"] = recorded.name
            current.append(item)
            continue
        newest = _newest(recorded.parent, family) or recorded
        item["disk"] = newest.name
        if _talib(newest):
            talib.append(item["disk"])
        if newest.name == recorded.name:
            current.append(item)
        elif _version(newest.name) > _version(recorded.name):
            updated.append(item)
        else:
            item["why"] = "book is ahead of the sorted tail"
            missing.append(item)
    return {
        "via": "vcgc",
        "door": "VRN_ENG113_LogicRollup_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "book": BOOK.name,
        "book_version": book.get("version"),
        "layers": len(book.get("layers") or {}),
        "nodes": len(_rows(book)),
        "current": len(current),
        "updated_n": len(updated),
        "missing_n": len(missing),
        "updated": updated,
        "missing": missing,
        "talib_imports": talib,
        "rules_copied": False,
        "book_edited": False,
        "intake_edited": False,
        "lock_success": not missing and not talib,
        "do_not": [
            "copy a logic rule into this file",
            "rewrite VIA_VRN_LogicArchitecture_SSOT",
            "treat an updated tail as permission to delete the older one",
            "import talib",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing and not updated and not talib else "name the drift; do not copy the rule",
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
    text = Path(__file__).read_text(encoding="utf-8")
    needles = ("repair_text", "fix_contents")
    ok = (
        denied
        and card["layers"] == 6
        and card["nodes"] >= 47
        and card["rules_copied"] is False
        and all(("def " + needle + "(") not in text for needle in needles)
        and card["book_edited"] is False
        and not card["talib_imports"]
    )
    print("  [OK]" if ok else "  [FAIL] " + str(card["missing_n"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
