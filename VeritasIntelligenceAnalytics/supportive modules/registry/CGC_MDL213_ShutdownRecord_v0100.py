#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The books stay at the pre-shutdown Git records. This door does not rewrite them."""
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
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
RECORD = HERE / "VIA_ShutdownRecord_v0100.json"
CARD = {
    "baseline": "17f6f974",
    "tails": 497,
    "imports": 0,
    "mentions": 34,
    "lamp": "GREEN",
    "laws": 103,
    "lessons": 362,
    "backfill": "0109",
    "measured_at": "2026-09-27 22:49:21",
    "checks": "12/12",
}


def _blob(commit: str, name: str) -> str:
    rel = f"VeritasIntelligenceAnalytics/supportive modules/registry/{name}"
    try:
        return subprocess.check_output(
            ["git", "rev-parse", f"{commit}:{rel}"], cwd=REPO, text=True, stderr=subprocess.DEVNULL
        ).strip()
    except subprocess.CalledProcessError:
        return ""


def check() -> dict:
    rec = json.loads(RECORD.read_text(encoding="utf-8"))
    pan = rec["panorama"]
    backfill = rec["backfill"]
    drift = []
    if rec.get("baseline") != CARD["baseline"]:
        drift.append("baseline")
    if pan.get("tails") != CARD["tails"] or pan.get("imports") != CARD["imports"] or pan.get("mentions") != CARD["mentions"] or pan.get("lamp") != CARD["lamp"]:
        drift.append("panorama")
    if pan.get("laws") != CARD["laws"] or pan.get("lessons") != CARD["lessons"]:
        drift.append("policy")
    if backfill.get("version") != CARD["backfill"] or backfill.get("measured_at") != CARD["measured_at"] or backfill.get("checks") != CARD["checks"]:
        drift.append("backfill")
    kinds = {}
    for book in rec["books"]:
        kinds[book["kind"]] = kinds.get(book["kind"], 0) + 1
        if _blob("HEAD", book["file"]) != book.get("blob"):
            drift.append(book["file"])
    return {
        "via": "vcgc",
        "door": "CGC_MDL213_ShutdownRecord_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": drift == [],
        "baseline": CARD["baseline"],
        "books": len(rec["books"]),
        "kinds": kinds,
        "lamp": CARD["lamp"],
        "tails": CARD["tails"],
        "imports": CARD["imports"],
        "mentions": CARD["mentions"],
        "backfill": CARD["backfill"],
        "measured_at": CARD["measured_at"],
        "drift": drift[:12],
        "rewritten": False,
        "intake_edited": False,
        "do_not": rec["do_not"],
        "next": "none" if not drift else "do not unlock; name the drift",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card["lock_success"] and card["kinds"].get("ssot", 0) > 0 and card["rewritten"] is False and card["mentions"] == 34
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card.get("drift") or []))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
