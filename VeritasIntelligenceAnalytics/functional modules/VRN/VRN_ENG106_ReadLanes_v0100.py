#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Say whether a page was read by one engine, two engines, or still needs Paddle.

Does not import Paddle. A missing library stays ABSENT.
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
import importlib.util
import re
from difflib import SequenceMatcher

SERIES = (
    ("layout", "fitz"),
    ("plumber", "pdfplumber"),
    ("pdfminer", "pdfminer"),
    ("camelot", "camelot"),
    ("tabula", "tabula"),
    ("paddleocr", "paddleocr"),
    ("docling", "docling"),
    ("surya", "surya"),
)
_TOKEN = re.compile(r"[\u4e00-\u9fff]|[A-Za-z0-9]+")


def installed() -> dict:
    return {name: importlib.util.find_spec(mod) is not None for name, mod in SERIES}


def _tokens(text: str) -> list[str]:
    return _TOKEN.findall(text or "")


def judge(left: str, right: str) -> dict:
    a = "".join(str(left or "").split())
    b = "".join(str(right or "").split())
    if not a and not b:
        return {"state": "BOTH_EMPTY", "seq": 1.0, "overlap": 1.0}
    if not a or not b:
        return {"state": "SINGLE", "kept": "plumber" if b else "layout", "seq": 0.0, "overlap": 0.0}
    seq = SequenceMatcher(None, a, b).ratio()
    ta, tb = set(_tokens(a)), set(_tokens(b))
    overlap = len(ta & tb) / len(ta | tb) if ta or tb else 1.0
    if seq >= 0.90:
        state = "AGREE"
    elif overlap >= 0.75 and seq < 0.60:
        state = "ORDER"
    elif seq >= 0.60 or overlap >= 0.60:
        state = "PARTIAL"
    else:
        state = "DIVERGE"
    return {"state": state, "seq": round(seq, 3), "overlap": round(overlap, 3)}


def selftest() -> int:
    same = judge("目標價 1275", "目標價 1275")
    order = judge("目標價 1275 買進", "買進 1275 目標價")
    one = judge("有字", "")
    tools = installed()
    ok = (
        same["state"] == "AGREE"
        and order["state"] == "ORDER"
        and one["state"] == "SINGLE"
        and "paddleocr" in tools
        and isinstance(tools["paddleocr"], bool)
    )
    print("  [OK]" if ok else f"  [FAIL] {same} {order} {one} {tools}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
