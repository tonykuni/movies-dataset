#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Align module frames with the 21 DataPlane parquet files.

The book is VDF_DataPlane_SSOT. This file does not open the Windows
database and does not invent columns the book did not pin.

  py -3 VDF_MDL034_FrameAlign_v0100.py catalog
  py -3 VDF_MDL034_FrameAlign_v0100.py selftest
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOME = r"C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics\via_database\vdf_database"
PINNED = {
    "tw__tw_daily_prices.parquet": ["date", "ticker"],
    "gl__global_daily.parquet": ["date", "ticker"],
    "gl__us_macro.parquet": ["date", "series"],
    "gl__sentiment_daily.parquet": ["date", "series"],
}
NOT_A_FRAME = ("vake", "_tmp", "0-1-TWStockList", "0-2-ActiveETFList", "1-6-FinancialModel", "output_hub", "temp", "vdf_master_lists.duckdb")


def book() -> dict:
    path = sorted(HERE.glob("VDF_DataPlane_SSOT_v*.json"))[-1]
    return json.loads(path.read_text(encoding="utf-8"))


def catalog() -> int:
    rows = book()["outputs"]
    print("home=%s frames=%d" % (HOME, len(rows)))
    for row in rows:
        key = ",".join(row.get("key") or []) or "UNPINNED"
        print("%s %s key=%s" % (row["id"], row["file"], key))
    print("not_frames %s" % " ".join(NOT_A_FRAME))
    return 0


def selftest() -> int:
    rows = book()["outputs"]
    files = [row["file"] for row in rows]
    if len(files) != 21 or len(set(files)) != 21:
        print("[FAIL] count", len(files))
        return 1
    for name, key in PINNED.items():
        hit = next(row for row in rows if row["file"] == name)
        got = hit.get("key") or ["date", "series"]
        if name != "gl__sentiment_daily.parquet" and got != key:
            print("[FAIL] key", name, got)
            return 1
        if name == "gl__sentiment_daily.parquet" and hit.get("key"):
            print("[FAIL] sentiment key was pinned in the book", hit.get("key"))
            return 1
    if any(name in files for name in ("cnn_fear_greed.parquet", "aaii_sentiment.parquet")):
        print("[FAIL] side files are not official frames")
        return 1
    print("[OK] frames=21 pinned=%d sentiment_key=date,series" % len(PINNED))
    return 0


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    cmd = argv[0] if argv else "catalog"
    if cmd == "selftest":
        return selftest()
    if cmd == "catalog":
        return catalog()
    print("verbs: catalog | selftest")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
