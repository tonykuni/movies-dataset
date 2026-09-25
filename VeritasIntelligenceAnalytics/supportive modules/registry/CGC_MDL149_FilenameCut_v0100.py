#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC door: cut sample filenames, then ask VDF for the exchange short name."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
CUT = VIA / "functional modules" / "VRN" / "VRN_ENG104_FilenameCut_v0100.py"
NAMES = VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG103_ListingName_v0100.py"


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
    cut = _load(CUT, "fncut")
    folder = sample_dir()
    files = []
    codes = []
    if folder.is_dir():
        for item in sorted(folder.iterdir()):
            if not item.is_file():
                continue
            row = cut.read_name(item.name)
            if row["ticker"]:
                codes.append(row["ticker"]["code"])
            files.append(row)
    names = {"state": "SKIP", "names": {}}
    if codes:
        net_path = sorted((VIA / "supportive modules" / "network").glob("via_net_unified_v*.py"))[-1]
        net = _load(net_path, "via_net")
        probe = net.http_json("https://openapi.twse.com.tw/v1/opendata/t187ap03_L")
        if probe.get("state") != "OK":
            names = {"state": probe.get("state") or "FAIL", "note": probe.get("note"), "names": {}}
        else:
            got = _load(NAMES, "names").names_for(net, sorted(set(codes)))
            names = {"state": "OK", "names": got["names"], "missing_n": len(got["missing"])}
    shown = []
    for row in files:
        if not row["ticker"]:
            continue
        code = row["ticker"]["code"]
        hit = (names.get("names") or {}).get(code) or {}
        shown.append({
            "file": row["name"],
            "code": code,
            "broker": (row["broker"] or {}).get("canon"),
            "date": (row["date"] or {}).get("iso"),
            "name": hit.get("name") or None,
            "market": hit.get("market"),
            "symbol": hit.get("symbol"),
        })
    body = {
        "via": "vcgc",
        "folder": str(folder),
        "files": len(files),
        "with_ticker": len(shown),
        "names": names.get("state"),
        "rows": shown[:12],
        "do_not": ["hand-edit the field-rule book"],
        "next": "none",
        "logged_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if files else 2


if __name__ == "__main__":
    sys.exit(main())
