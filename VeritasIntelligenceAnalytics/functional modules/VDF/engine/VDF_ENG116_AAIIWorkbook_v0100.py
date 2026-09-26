#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Download the AAII survey workbook and load it. An interruption page writes nothing."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime
from io import BytesIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
URL = "https://www.aaii.com/files/surveys/sentiment.xls"
DB = VDF / "output_hub" / "mega" / "aaii_sentiment.duckdb"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"


def allowed() -> bool:
    return os.environ.get("VIA_CENTRAL_ENTRY") == "1" and os.environ.get("VIA_FROM_VCGC") == "YES"


def kind(data: bytes) -> str:
    head = data[:800].lower()
    if b"pardon our interruption" in head or head.lstrip().startswith(b"<"):
        return "block"
    if data[:4] == b"\xd0\xcf\x11\xe0":
        return "xls"
    if data[:2] == b"PK":
        return "xlsx"
    return "unknown"


def fetch() -> tuple[bytes, str]:
    local = os.environ.get("VIA_AAII_XLS", "").strip()
    if local:
        return Path(local).read_bytes(), "file"
    req = urllib.request.Request(URL, headers={"User-Agent": UA, "Accept": "*/*", "Referer": "https://www.aaii.com/sentimentsurvey"})
    with urllib.request.urlopen(req, timeout=40) as response:
        return response.read(), "url"


def rows_from(data: bytes) -> list[dict]:
    import pandas as pd
    frame = pd.read_excel(BytesIO(data), sheet_name=0, header=3)
    frame.columns = [str(c).strip() for c in frame.columns]
    date_col = bull = bear = neut = None
    for col in frame.columns:
        low = col.lower()
        if "date" in low and date_col is None:
            date_col = col
        elif "bullish" in low and bull is None:
            bull = col
        elif "bearish" in low and bear is None:
            bear = col
        elif "neutral" in low and neut is None:
            neut = col
    if not all([date_col, bull, bear, neut]):
        raise ValueError("columns")
    out = []
    for _, row in frame.dropna(subset=[date_col]).iterrows():
        try:
            b, x, n = float(row[bull]), float(row[bear]), float(row[neut])
        except (TypeError, ValueError):
            continue
        if max(b, x, n) <= 1:
            b, x, n = b * 100, x * 100, n * 100
        if not 99 <= b + x + n <= 101:
            continue
        when = row[date_col]
        stamp = when.strftime("%Y-%m-%d") if hasattr(when, "strftime") else str(when)[:10]
        out.append({"date": stamp, "bullish": round(b, 4), "neutral": round(n, 4), "bearish": round(x, 4), "spread": round(b - x, 4)})
    return out


def store(rows: list[dict]) -> int:
    import duckdb
    DB.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now()
    con = duckdb.connect(str(DB))
    con.execute("CREATE TABLE IF NOT EXISTS aaii_sentiment (date DATE, bullish DOUBLE, neutral DOUBLE, bearish DOUBLE, spread DOUBLE, source VARCHAR, fetched_at TIMESTAMP)")
    con.execute("DELETE FROM aaii_sentiment")
    con.executemany(
        "INSERT INTO aaii_sentiment VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(r["date"], r["bullish"], r["neutral"], r["bearish"], r["spread"], "aaii.com/files/surveys/sentiment.xls", now) for r in rows],
    )
    n = con.execute("SELECT COUNT(*) FROM aaii_sentiment").fetchone()[0]
    con.close()
    return int(n)


def run() -> dict:
    card = {
        "via": "vcgc",
        "door": "VDF_ENG116_AAIIWorkbook_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "url": URL,
        "db": str(DB),
        "written": 0,
        "intake_edited": False,
        "do_not": ["write the interruption page into the database", "edit intake macro_ssot"],
    }
    try:
        data, source = fetch()
    except Exception as exc:
        card.update({"state": "FAIL", "why": type(exc).__name__, "next": "none"})
        return card
    got = kind(data)
    card["source"] = source
    card["bytes"] = len(data)
    card["kind"] = got
    if got == "block":
        card.update({"state": "BLOCKED", "why": "official file returned a block page", "next": "save the workbook in a browser, set VIA_AAII_XLS to that file, run this door again"})
        return card
    if got not in ("xls", "xlsx"):
        card.update({"state": "FAIL", "why": "not a workbook", "next": "none"})
        return card
    try:
        rows = rows_from(data)
        card["written"] = store(rows)
        card["last"] = rows[-1] if rows else None
        card["state"] = "LIVE" if rows else "NODATA"
        card["next"] = "none"
    except Exception as exc:
        card.update({"state": "FAIL", "why": type(exc).__name__, "next": "none"})
    return card


def main() -> int:
    if not allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-aaii through Invoke-VIAPython"}, ensure_ascii=False))
        return 2
    card = run()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["state"] in ("LIVE", "BLOCKED") else 2


def selftest() -> int:
    html = Path("/tmp/aaii_sentiment.bin").read_bytes() if Path("/tmp/aaii_sentiment.bin").is_file() else b"<html>Pardon Our Interruption</html>"
    ok = kind(html) == "block" and kind(b"\xd0\xcf\x11\xe0rest") == "xls" and kind(b"<html>bullish") == "block"
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
