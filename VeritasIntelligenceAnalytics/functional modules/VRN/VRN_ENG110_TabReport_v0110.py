#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stock reports only. Morning notes, industry notes, and forums wait."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def is_stock(name: str, cut) -> bool:
    named = cut.read_name(name)
    tickers = [row for row in named.get("parts") or [] if row.get("role") == "TICKER"]
    return bool(tickers) and not all(row.get("ambiguous_year") for row in tickers)


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    wire = _load("tab_report_v0109_stock", HERE / "VRN_ENG110_TabReport_v0109.py")
    cut = _load("filename_cut_stock", HERE / "VRN_ENG104_FilenameCut_v0100.py")
    all_pdf = sorted(folder.glob("*.pdf")) if folder.is_dir() else []
    skipped = [path.name for path in all_pdf if not is_stock(path.name, cut)]
    original = Path.glob

    def only_stock(self, pattern):
        found = original(self, pattern)
        if self == folder and pattern == "*.pdf":
            return [path for path in found if is_stock(path.name, cut)]
        return found

    Path.glob = only_stock
    try:
        card = wire.run(folder, data_root, open_page)
    finally:
        Path.glob = original
    card["door"] = "VRN_ENG110_TabReport_v0110"
    card["scope"] = "stock"
    card["pdf_all"] = len(all_pdf)
    card["skipped_non_stock"] = len(skipped)
    card["later"] = skipped
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _load("tab_report_v0103_stock", HERE / "VRN_ENG110_TabReport_v0103.py")
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("present") else 2


def selftest() -> int:
    cut = _load("filename_cut_self", HERE / "VRN_ENG104_FilenameCut_v0100.py")
    ok = is_stock("華南投顧-2606-裕民-1141202.pdf", cut) and is_stock("JP-2330 20250718.pdf", cut)
    ok = ok and not is_stock("今日台股盤勢重點-CTBC260915.pdf", cut)
    ok = ok and not is_stock("20260916兆豐台灣產業專題-AI末日論？假的.pdf", cut)
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
