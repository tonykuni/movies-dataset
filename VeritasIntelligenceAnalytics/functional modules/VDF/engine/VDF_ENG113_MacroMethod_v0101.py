#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Same Fed-method refresh. The live us_macro table has three columns; add fetched_at, do not rebuild it."""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("method_v0100", HERE / "VDF_ENG113_MacroMethod_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _ensure(con) -> list[str]:
    con.execute("CREATE TABLE IF NOT EXISTS us_macro (date DATE, series VARCHAR, value DOUBLE, fetched_at TIMESTAMP)")
    names = [row[0] for row in con.execute("DESCRIBE us_macro").fetchall()]
    if "fetched_at" not in names:
        con.execute("ALTER TABLE us_macro ADD COLUMN fetched_at TIMESTAMP")
        names.append("fetched_at")
    return names


def _write(con, series: str, rows: list[tuple[str, float]], since: str, now: datetime) -> None:
    con.execute("BEGIN")
    try:
        con.execute("DELETE FROM us_macro WHERE series = ? AND date >= ?", [series, since])
        con.executemany(
            "INSERT INTO us_macro (date, series, value, fetched_at) VALUES (?, ?, ?, ?)",
            [(d, series, v, now) for d, v in rows],
        )
        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise


def refresh() -> dict:
    prior = _prior()
    import duckdb
    book = prior.load()
    key = os.environ.get("FRED_API_KEY", "")
    if not key:
        return {"via": "vcgc", "state": "DENY", "why": "FRED_API_KEY is not set"}
    prior.OUT.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(prior.DB))
    _ensure(con)
    now = datetime.now()
    wrote = []
    for sid in prior.fred_ids(book):
        rows = prior._fred(key, sid, book["since"])
        _write(con, sid, rows, book["since"], now)
        wrote.append({"series": sid, "n": len(rows), "last": rows[-1][0] if rows else None})
    dts = prior._dts(book["since"])
    _write(con, "DTS_TGA_CLOSE", dts, book["since"], now)
    n = con.execute("SELECT COUNT(*) FROM us_macro").fetchone()[0]
    con.close()
    return {
        "via": "vcgc",
        "door": "VDF_ENG113_MacroMethod_v0101",
        "state": "OK",
        "db": str(prior.DB),
        "rows": n,
        "series": wrote,
        "dts": len(dts),
        "columns": ["date", "series", "value", "fetched_at"],
        "intake_edited": False,
        "do_not": book["do_not"],
        "next": "none",
    }


def main() -> int:
    prior = _prior()
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    if "--refresh" in sys.argv:
        card = refresh()
    else:
        card = prior.check()
        card["door"] = "VDF_ENG113_MacroMethod_v0101"
        card["next"] = "refresh"
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("state", "OK") != "DENY" else 2


def selftest() -> int:
    import duckdb
    path = Path("/tmp/us_macro_v0101.duckdb")
    if path.exists():
        path.unlink()
    con = duckdb.connect(str(path))
    con.execute("CREATE TABLE us_macro (date DATE, series VARCHAR, value DOUBLE)")
    con.execute("INSERT INTO us_macro VALUES ('2019-01-01', 'WALCL', 1.0)")
    names = _ensure(con)
    _write(con, "WALCL", [("2020-01-02", 2.0)], "2020-01-01", datetime(2026, 9, 27))
    kept = con.execute("SELECT COUNT(*) FROM us_macro WHERE date < '2020-01-01'").fetchone()[0]
    added = con.execute("SELECT value, fetched_at IS NOT NULL FROM us_macro WHERE series = 'WALCL' AND date >= '2020-01-01'").fetchone()
    con.close()
    path.unlink()
    ok = "fetched_at" in names and kept == 1 and added[0] == 2.0 and added[1] is True
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
