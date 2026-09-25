#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC to VRN: sealed quotes, then filename survey of the sample folder."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
JOIN = VIA / "functional modules" / "VRN" / "VRN_ENG103_SourceLaneJoin_v0100.py"


def sample_dir() -> Path:
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
    spec = importlib.util.spec_from_file_location("vrn_join", JOIN)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    body = {
        "via": "vcgc",
        "locked_quotes": [mod.quote_for("2330"), mod.quote_for("6488")],
        "non_stock": "not_run",
        "survey": mod.survey(sample_dir()),
        "do_not": ["refetch the locked quotes", "parse non-stock reports"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    quotes_ok = all(row["state"] == "OK" for row in body["locked_quotes"])
    return 0 if quotes_ok and body["survey"]["state"] in {"OK", "ABSENT"} else 1


if __name__ == "__main__":
    sys.exit(main())
