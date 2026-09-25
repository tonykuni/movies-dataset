#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Short names for tickers already cut from a filename. Uses ENG054's listing read."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _listings():
    spec = importlib.util.spec_from_file_location("eng054", HERE / "VDF_ENG054_TWDailyBackfill_v0108.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def names_for(net, codes: list[str]) -> dict:
    wanted = {str(code).strip() for code in codes if str(code).strip()}
    rows, per = _listings().fetch_listings(net)
    found = {}
    for row in rows:
        if row.get("code") in wanted and row["code"] not in found:
            found[row["code"]] = {
                "name": row.get("name") or "",
                "market": row.get("market"),
                "symbol": row.get("yf_ticker"),
            }
    missing = sorted(wanted - set(found))
    return {"per": per, "names": found, "missing": missing}


def selftest() -> int:
    class Net:
        def http_json(self, url):
            if "twse" in url:
                return {"state": "OK", "data": [{"公司代號": "2330", "公司簡稱": "台積電"}]}
            return {"state": "OK", "data": [{"公司代號": "6488", "公司簡稱": "環球晶"}]}
    got = names_for(Net(), ["2330", "6488", "9999"])
    ok = got["names"]["2330"]["name"] == "台積電" and got["names"]["6488"]["symbol"].endswith(".TWO") and got["missing"] == ["9999"]
    print("  [OK]" if ok else f"  [FAIL] {got}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
