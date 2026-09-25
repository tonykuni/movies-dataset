#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Re-judge stock first pages. Paddle is reported, not called."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _sample() -> Path:
    spec = HERE / "VIA_InputConsole_Spec_v0100.json"
    chosen = ""
    if spec.is_file():
        data = json.loads(spec.read_text(encoding="utf-8"))
        chosen = str(((data.get("user") or {}).get("vrn_dir") or "")).strip()
    return Path(chosen or r"C:\測試樣本報告")


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    lanes = _load(VIA / "functional modules" / "VRN" / "VRN_ENG106_ReadLanes_v0100.py", "lanes106")
    cut = _load(VIA / "functional modules" / "VRN" / "VRN_ENG104_FilenameCut_v0100.py", "cut104")
    texteng = _load(sorted((VIA / "functional modules" / "VRN").glob("VRN_ENG072_FirstPageText_v*.py"))[-1], "text072")
    folder = _sample()
    counts = Counter()
    right = Counter()
    fails = []
    files = 0
    if folder.is_dir():
        for item in sorted(folder.iterdir()):
            if not item.is_file() or item.suffix.lower() != ".pdf":
                continue
            row = cut.read_name(item.name)
            if not row.get("ticker"):
                continue
            files += 1
            try:
                laid = texteng.extract_page1_zones(item) or {}
                plum = texteng.extract_page1_plumber(item) or {}
            except Exception as exc:
                fails.append({"file": item.name, "why": type(exc).__name__})
                continue
            body = lanes.judge(laid.get("body"), plum.get("body"))
            side = lanes.judge(laid.get("right"), plum.get("right"))
            counts[body["state"]] += 1
            right[side["state"]] += 1
    tools = lanes.installed()
    body = {
        "via": "vcgc",
        "stock_pdf": files,
        "body": dict(counts),
        "right": dict(right),
        "tools": tools,
        "paddle_called": False,
        "fails": fails[:8],
        "do_not": ["import paddleocr unless a page is empty on both text engines"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if files else 2


if __name__ == "__main__":
    sys.exit(main())
