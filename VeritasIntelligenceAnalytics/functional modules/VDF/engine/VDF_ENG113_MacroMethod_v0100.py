#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Refresh the Fed-reserve method series into us_macro. Does not edit the intake SSOT."""
from __future__ import annotations
import json, os, sys, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
BOOK = VDF / "VDF_USMacro_Method_v0100.json"
OUT = Path(os.environ["VIA_MACRO_OUT"]) if os.environ.get("VIA_MACRO_OUT") else VDF / "output_hub" / "mega"
DB = OUT / "vdf_global_market.duckdb"
FRED = "https://api.stlouisfed.org/fred/series/observations"
DTS = "https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/dts/operating_cash_balance"

def load() -> dict:
    return json.loads(BOOK.read_text(encoding="utf-8"))

def fred_ids(book: dict) -> list[str]:
    ids = []
    for key, rows in book["units"].items():
        if key.startswith("dts"):
            continue
        ids.extend(rows)
    return ids

def check() -> dict:
    book = load()
    ids = fred_ids(book)
    return {"via": "vcgc", "door": "VDF_ENG113", "fred": len(ids), "rules": len(book["rules"]),
            "table": book["table"], "since": book["since"], "intake_edited": False}

def _fred(key: str, sid: str, start: str) -> list[tuple[str, float]]:
    qs = urllib.parse.urlencode({"series_id": sid, "api_key": key, "file_type": "json",
                                 "observation_start": start, "sort_order": "asc"})
    with urllib.request.urlopen(FRED + "?" + qs, timeout=60) as r:
        obs = json.loads(r.read().decode())["observations"]
    return [(o["date"], float(o["value"])) for o in obs if o["value"] not in ("", ".")]

def _dts(start: str) -> list[tuple[str, float]]:
    qs = urllib.parse.urlencode({
        "filter": f"record_date:gte:{start},account_type:eq:Treasury General Account (TGA) Closing Balance",
        "fields": "record_date,open_today_bal", "page[size]": "10000", "sort": "record_date"})
    with urllib.request.urlopen(DTS + "?" + qs, timeout=60) as r:
        rows = json.loads(r.read().decode())["data"]
    out = []
    for row in rows:
        v = row.get("open_today_bal")
        if v in (None, "", "null"):
            continue
        out.append((row["record_date"], float(v)))
    return out

def refresh() -> dict:
    import duckdb
    book = load()
    key = os.environ.get("FRED_API_KEY", "")
    if not key:
        return {"via": "vcgc", "state": "DENY", "why": "FRED_API_KEY is not set"}
    OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB))
    con.execute("CREATE TABLE IF NOT EXISTS us_macro (date DATE, series VARCHAR, value DOUBLE, fetched_at TIMESTAMP)")
    now = datetime.now()
    wrote = []
    for sid in fred_ids(book):
        rows = _fred(key, sid, book["since"])
        con.execute("DELETE FROM us_macro WHERE series = ? AND date >= ?", [sid, book["since"]])
        con.executemany("INSERT INTO us_macro VALUES (?, ?, ?, ?)", [(d, sid, v, now) for d, v in rows])
        wrote.append({"series": sid, "n": len(rows), "last": rows[-1][0] if rows else None})
    dts = _dts(book["since"])
    con.execute("DELETE FROM us_macro WHERE series = 'DTS_TGA_CLOSE' AND date >= ?", [book["since"]])
    con.executemany("INSERT INTO us_macro VALUES (?, ?, ?, ?)", [(d, "DTS_TGA_CLOSE", v, now) for d, v in dts])
    n = con.execute("SELECT COUNT(*) FROM us_macro").fetchone()[0]
    con.close()
    return {"via": "vcgc", "state": "OK", "db": str(DB), "rows": n, "series": wrote,
            "dts": len(dts), "intake_edited": False, "do_not": book["do_not"], "next": "none"}

def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    if "--refresh" in sys.argv:
        card = refresh()
    else:
        card = check()
        card["next"] = "refresh"
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("state", "OK") != "DENY" else 2

def selftest() -> int:
    card = check()
    book = load()
    ok = card["fred"] == 17 and "RRPONTSYD" in book["units"]["billions_usd"] and "WALCL" in book["units"]["millions_usd"]
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
