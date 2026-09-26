#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Load the AAII workbook. Dates must be YYYY-MM-DD and numbers must be plain Python floats."""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from datetime import datetime
from io import BytesIO
from pathlib import Path

HERE = Path(__file__).resolve().parent
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _prior():
    spec = importlib.util.spec_from_file_location("aaii_v0100", HERE / "VDF_ENG116_AAIIWorkbook_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _iso(when) -> str:
    import pandas as pd
    if hasattr(when, "strftime"):
        text = when.strftime("%Y-%m-%d")
    else:
        parsed = pd.to_datetime(when, errors="coerce")
        text = "" if pd.isna(parsed) else parsed.strftime("%Y-%m-%d")
    return text if ISO.match(text or "") else ""


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
        raise ValueError("columns " + ",".join(frame.columns[:8]))
    out = []
    for _, row in frame.dropna(subset=[date_col]).iterrows():
        stamp = _iso(row[date_col])
        if not stamp:
            continue
        try:
            b, x, n = float(row[bull]), float(row[bear]), float(row[neut])
        except (TypeError, ValueError):
            continue
        if max(b, x, n) <= 1:
            b, x, n = b * 100, x * 100, n * 100
        if not 99 <= b + x + n <= 101:
            continue
        out.append({
            "date": stamp,
            "bullish": float(round(b, 4)),
            "neutral": float(round(n, 4)),
            "bearish": float(round(x, 4)),
            "spread": float(round(b - x, 4)),
        })
    return out


def store(rows: list[dict], db: Path) -> int:
    import duckdb
    db.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE IF NOT EXISTS aaii_sentiment (date DATE, bullish DOUBLE, neutral DOUBLE, bearish DOUBLE, spread DOUBLE, source VARCHAR, fetched_at TIMESTAMP)")
    con.execute("DELETE FROM aaii_sentiment")
    con.executemany(
        "INSERT INTO aaii_sentiment VALUES (CAST(? AS DATE), CAST(? AS DOUBLE), CAST(? AS DOUBLE), CAST(? AS DOUBLE), CAST(? AS DOUBLE), ?, CAST(? AS TIMESTAMP))",
        [(r["date"], r["bullish"], r["neutral"], r["bearish"], r["spread"], "aaii.com/files/surveys/sentiment.xls", now) for r in rows],
    )
    n = con.execute("SELECT COUNT(*) FROM aaii_sentiment").fetchone()[0]
    con.close()
    return int(n)


def run() -> dict:
    prior = _prior()
    card = {
        "via": "vcgc",
        "door": "VDF_ENG116_AAIIWorkbook_v0101",
        "enter": "vcgc",
        "exit": "vcgc",
        "url": prior.URL,
        "db": str(prior.DB),
        "written": 0,
        "intake_edited": False,
        "do_not": ["write the interruption page into the database", "edit intake macro_ssot"],
    }
    try:
        data, source = prior.fetch()
    except Exception as exc:
        card.update({"state": "FAIL", "why": type(exc).__name__ + ": " + str(exc)[:180], "next": "none"})
        return card
    got = prior.kind(data)
    card.update({"source": source, "bytes": len(data), "kind": got})
    if got == "block":
        card.update({"state": "BLOCKED", "why": "official file returned a block page", "next": "save the workbook in a browser, set VIA_AAII_XLS to that file, run this door again"})
        return card
    if got not in ("xls", "xlsx"):
        card.update({"state": "FAIL", "why": "not a workbook", "next": "none"})
        return card
    try:
        rows = rows_from(data)
        card["written"] = store(rows, prior.DB)
        card["first"] = rows[0]["date"] if rows else None
        card["last"] = rows[-1] if rows else None
        card["state"] = "LIVE" if rows else "NODATA"
        card["next"] = "none"
    except Exception as exc:
        card.update({"state": "FAIL", "why": type(exc).__name__ + ": " + str(exc)[:180], "next": "none"})
    return card


def main() -> int:
    if not _prior().allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-aaii through Invoke-VIAPython"}, ensure_ascii=False))
        return 2
    card = run()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["state"] in ("LIVE", "BLOCKED") else 2


def selftest() -> int:
    import duckdb
    from openpyxl import Workbook
    book = Workbook()
    sheet = book.active
    for _ in range(3):
        sheet.append(["title"])
    sheet.append(["Date", "Bullish", "Neutral", "Bearish"])
    sheet.append([datetime(1987, 7, 24), 0.36, 0.32, 0.32])
    sheet.append(["not a date", 0.1, 0.2, 0.7])
    sheet.append([datetime(2026, 9, 23), 32.7, 19.2, 48.1])
    raw = BytesIO()
    book.save(raw)
    rows = rows_from(raw.getvalue())
    path = Path("/tmp/aaii_selftest.duckdb")
    if path.exists():
        path.unlink()
    n = store(rows, path)
    last = duckdb.connect(str(path)).execute("SELECT bullish, bearish FROM aaii_sentiment ORDER BY date DESC LIMIT 1").fetchone()
    path.unlink()
    ok = n == 2 and rows[0]["date"] == "1987-07-24" and last[0] == 32.7 and abs(last[1] - 48.1) < 0.01
    print("  [OK]" if ok else "  [FAIL] " + json.dumps({"n": n, "rows": rows, "last": last}, default=str))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
