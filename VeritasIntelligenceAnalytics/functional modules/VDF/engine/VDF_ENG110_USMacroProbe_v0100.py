#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One-point probe of the two-tier US macro list. Does not edit the tree, the lock, or intake."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parents[1]
TREE = VDF / "VDF_USMacro_Tree_v0100.json"
PARAMS = VIA / "supportive modules" / "registry" / "VIA_USMacro_Params_v0100.json"
METHOD = VDF / "VDF_USMacro_Method_v0100.json"
OUT = VDF / "VDF_USMacro_Probe_v0100.json"
FRED = "https://api.stlouisfed.org/fred/series/observations"
DTS = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance"
PARKED_RETRY = ("NAPM", "NMFCI", "NAPMNOI", "USMFGPMI", "AMDMNO", "DISCBORR")


def plan() -> list[dict]:
    tree = json.loads(TREE.read_text(encoding="utf-8"))
    params = json.loads(PARAMS.read_text(encoding="utf-8"))
    method = json.loads(METHOD.read_text(encoding="utf-8"))
    rows = []
    seen = set()

    def add(sid: str, tier: str, family: str, source: str) -> None:
        if not sid or sid in seen:
            return
        seen.add(sid)
        rows.append({"id": sid, "tier": tier, "family": family, "source": source})

    for fam in tree["families"]:
        for row in fam.get("add", []):
            add(row.get("fred_id"), "child", fam["id"], "FRED")
    for key, ids in method["units"].items():
        source = "DTS" if key.startswith("dts") else "FRED"
        tier = "reserve" if source == "FRED" else "treasury"
        for sid in ids:
            add(sid, tier, "fed", source)
    for row in params["parameters"]:
        if row.get("role") == "fed_more":
            add(row["id"], "aside", "fed", "FRED")
    for sid in PARKED_RETRY:
        add(sid, "parked_retry", "fed" if sid == "DISCBORR" else "tree", "FRED")
    return rows


def fred_point(sid: str, key: str) -> dict:
    if not key:
        return {"id": sid, "state": "SKIP", "why": "FRED_API_KEY is not set"}
    qs = urllib.parse.urlencode({
        "series_id": sid, "api_key": key, "file_type": "json",
        "sort_order": "desc", "limit": "1",
    })
    try:
        with urllib.request.urlopen(FRED + "?" + qs, timeout=40) as resp:
            obs = json.loads(resp.read().decode()).get("observations") or []
    except urllib.error.HTTPError as exc:
        state = "PARKED" if exc.code == 400 else "FAIL"
        return {"id": sid, "state": state, "why": f"HTTP {exc.code}"}
    if not obs or obs[0].get("value") in ("", "."):
        return {"id": sid, "state": "NODATA"}
    return {"id": sid, "state": "LIVE", "date": obs[0]["date"], "value": obs[0]["value"]}


def dts_point() -> dict:
    qs = urllib.parse.urlencode({
        "filter": "account_type:eq:Treasury General Account (TGA) Closing Balance",
        "fields": "record_date,open_today_bal",
        "sort": "-record_date",
        "page[size]": "1",
    })
    with urllib.request.urlopen(DTS + "?" + qs, timeout=40) as resp:
        data = json.loads(resp.read().decode())["data"]
    row = data[0]
    return {"id": "DTS_TGA_CLOSE", "state": "LIVE", "date": row["record_date"], "value": row["open_today_bal"], "unit": "millions_usd"}


def run() -> dict:
    key = os.environ.get("FRED_API_KEY", "").strip()
    measured = []
    for row in plan():
        if row["source"] == "DTS":
            got = dts_point()
        else:
            got = fred_point(row["id"], key)
        got["tier"] = row["tier"]
        got["family"] = row["family"]
        measured.append(got)
    counts = {}
    for row in measured:
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    return {
        "via": "vcgc",
        "door": "VDF_ENG110_USMacroProbe_v0100",
        "probed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "series": len(measured),
        "counts": counts,
        "fred_key": bool(key),
        "intake_edited": False,
        "tree_edited": False,
        "lock_edited": False,
        "rows": measured,
        "do_not": [
            "edit intake macro_ssot",
            "mark a series parked because the key is missing",
            "let yfinance own a yield",
            "refresh DISCBORR as a live series",
        ],
        "next": "none" if key else "set FRED_API_KEY and run this door again",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = run()
    OUT.write_text(json.dumps(card, ensure_ascii=False, indent=1), encoding="utf-8")
    show = dict(card)
    show["rows"] = [row for row in card["rows"] if row["state"] != "SKIP"][:8]
    print(json.dumps(show, ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    rows = plan()
    ids = [row["id"] for row in rows]
    missing = fred_point("WALCL", "")
    parked = {"id": "NAPM", "state": "PARKED", "why": "HTTP 400"}
    ok = (
        ids.count("U4RATE") == 1
        and ids.count("WALCL") == 1
        and ids.count("DTS_TGA_CLOSE") == 1
        and ids.count("DISCBORR") == 1
        and missing["state"] == "SKIP"
        and parked["state"] == "PARKED"
        and len(rows) == 19 + 17 + 1 + 13 + 6
    )
    print("  [OK]" if ok else "  [FAIL] " + str(len(rows)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
