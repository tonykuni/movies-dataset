#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door. Filename to three codes. PDF engines are listed, not run."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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
    cut = _load(VIA / "functional modules" / "VRN" / "VRN_ENG104_FilenameCut_v0100.py", "cut104")
    page = _load(VIA / "functional modules" / "VRN" / "VRN_ENG105_PageCrosscheck_v0100.py", "page105")
    folder = sample_dir()
    rows = []
    if folder.is_dir():
        for item in sorted(folder.iterdir()):
            if item.is_file():
                rows.append(cut.read_name(item.name))
    codes = sorted({row["ticker"]["code"] for row in rows if row.get("ticker")})
    markets = {}
    name_state = "SKIP"
    if codes:
        net = _load(sorted((VIA / "supportive modules" / "network").glob("via_net_unified_v*.py"))[-1], "net")
        probe = net.http_json("https://openapi.twse.com.tw/v1/opendata/t187ap03_L")
        if probe.get("state") != "OK":
            name_state = probe.get("state") or "FAIL"
        else:
            got = _load(VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG103_ListingName_v0100.py", "names").names_for(net, codes)
            name_state = "OK"
            markets = {code: item.get("market") for code, item in got["names"].items()}
    agree = missing = 0
    example = None
    for row in rows:
        tick = row.get("ticker") or {}
        code = tick.get("code")
        if not code:
            continue
        checked = page.confirm_codes(code, markets.get(code))
        if checked["ok"]:
            agree += 1
            if example is None:
                example = {
                    "file": row["name"],
                    "broker": (row.get("broker") or {}).get("canon"),
                    "report_date": (row.get("date") or {}).get("iso"),
                    **checked,
                    "analyst": None,
                    "rating": None,
                    "target_price_adj": None,
                    "upside_pct": None,
                    "yfinance_target_median": None,
                    "factset_target_median": None,
                }
        else:
            missing += 1
    body = {
        "via": "vcgc",
        "folder": str(folder),
        "files": len(rows),
        "codes": len(codes),
        "names": name_state,
        "three_code_agree": agree,
        "not_confirmed": missing,
        "example": example,
        "engines": page.engine_order(),
        "pdf_opened": False,
        "do_not": ["run paddle while it is ABSENT", "guess a market"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if agree else 2


if __name__ == "__main__":
    sys.exit(main())
