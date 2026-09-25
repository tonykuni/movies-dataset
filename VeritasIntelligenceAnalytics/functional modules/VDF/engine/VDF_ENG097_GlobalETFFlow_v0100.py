#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG097 — classify global ETFs and compute net cash flow.

Does not fetch. AUM and NAV must already be in etf_stats_daily.
Flow = today's AUM - yesterday's AUM * (today NAV / yesterday NAV).
Positive is inflow, negative is outflow. One net number, not two official prints.
"""
from __future__ import annotations

import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parent.parent
BOOK = VIA / "supportive modules" / "registry" / "VIA_GlobalETF_Class_v0100.json"
DB_GL = VDF / "output_hub" / "mega" / "vdf_global_market.duckdb"
TABLE = "etf_flow_daily"

# Every symbol L5 already requests: ENG055 ETF_REGION plus the universe etf list.
FETCHED = {
    "SPY", "DIA", "QQQ", "IWM", "ONEQ", "EWJ", "EWY", "EWT", "FXI", "MCHI",
    "EWH", "EWS", "EWM", "EIDO", "THD", "INDA", "EPI", "EWU", "EWG", "EWQ",
    "FEZ", "EZU", "EWL", "EWI", "EWP", "VGK", "TLT", "VT", "EFA", "EEM",
    "IEF", "SOXX",
}


def load_book(path: Path = BOOK) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def classify(symbol: str, book: dict | None = None) -> dict:
    book = book or load_book()
    row = (book.get("symbols") or {}).get(str(symbol or "").upper())
    if not row:
        return {"symbol": str(symbol or "").upper(), "region": None, "risk": None,
                "listing_ccy": None, "underlying_ccy": None}
    return {"symbol": str(symbol or "").upper(), **row}


def cash_flow(rows: list[dict]) -> list[dict]:
    """rows need symbol, date, aum, nav. First date of each symbol has no flow."""
    ordered = sorted(rows, key=lambda r: (str(r.get("symbol") or ""), str(r.get("date") or "")))
    prev: dict[str, tuple[float, float]] = {}
    out = []
    for row in ordered:
        symbol = str(row.get("symbol") or "").upper()
        aum, nav = row.get("aum"), row.get("nav")
        flow = None
        if symbol in prev and aum is not None and nav is not None and prev[symbol][1]:
            flow = float(aum) - float(prev[symbol][0]) * (float(nav) / float(prev[symbol][1]))
        if aum is not None and nav is not None:
            prev[symbol] = (float(aum), float(nav))
        item = dict(row)
        item["symbol"] = symbol
        item["flow"] = flow
        item["inflow"] = flow if flow is not None and flow > 0 else (0.0 if flow is not None else None)
        item["outflow"] = -flow if flow is not None and flow < 0 else (0.0 if flow is not None else None)
        item["kind"] = "ESTIMATE" if flow is not None else None
        out.append(item)
    return out


def attach(rows: list[dict], book: dict | None = None) -> list[dict]:
    book = book or load_book()
    tagged = []
    for row in cash_flow(rows):
        meta = classify(row["symbol"], book)
        tagged.append({**row, **{k: v for k, v in meta.items() if k != "symbol"}})
    return tagged


def write_flows(rows: list[dict], db: Path = DB_GL) -> int:
    if not rows or not db.exists():
        return 0
    import duckdb
    con = duckdb.connect(str(db))
    try:
        con.execute(f"""
            CREATE TABLE IF NOT EXISTS {TABLE} (
                date VARCHAR, symbol VARCHAR, aum DOUBLE, nav DOUBLE,
                flow DOUBLE, inflow DOUBLE, outflow DOUBLE, kind VARCHAR,
                region VARCHAR, risk VARCHAR, listing_ccy VARCHAR, underlying_ccy VARCHAR
            )
        """)
        n = 0
        for row in rows:
            if row.get("flow") is None:
                continue
            con.execute(f"DELETE FROM {TABLE} WHERE date = ? AND symbol = ?", [row.get("date"), row["symbol"]])
            con.execute(
                f"INSERT INTO {TABLE} VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                [row.get("date"), row["symbol"], row.get("aum"), row.get("nav"),
                 row.get("flow"), row.get("inflow"), row.get("outflow"), row.get("kind"),
                 row.get("region"), row.get("risk"), row.get("listing_ccy"), row.get("underlying_ccy")],
            )
            n += 1
        return n
    finally:
        con.close()


def from_stats(db: Path = DB_GL) -> dict:
    if not db.exists():
        return {"state": "ABSENT", "rows": 0}
    import duckdb
    con = duckdb.connect(str(db), read_only=True)
    try:
        tables = {r[0] for r in con.execute("SHOW TABLES").fetchall()}
        if "etf_stats_daily" not in tables:
            return {"state": "NODATA", "rows": 0}
        cols = {r[0] for r in con.execute("DESCRIBE etf_stats_daily").fetchall()}
        if not {"date", "symbol", "aum", "nav"} <= cols:
            return {"state": "SCHEMA_MISSING", "rows": 0}
        raw = con.execute(
            "SELECT date, symbol, aum, nav FROM etf_stats_daily WHERE aum IS NOT NULL AND nav IS NOT NULL"
        ).fetchall()
    finally:
        con.close()
    rows = attach([{"date": a, "symbol": b, "aum": c, "nav": d} for a, b, c, d in raw])
    n = write_flows(rows, db)
    return {"state": "OK", "rows": n, "classified": len(rows)}


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    book = load_book()
    have = set(book["symbols"])
    chk("covers fetched", FETCHED <= have)
    ewt = classify("EWT", book)
    chk("taiwan", ewt["region"] == "TAIWAN" and ewt["underlying_ccy"] == "TWD" and ewt["listing_ccy"] == "USD")
    chk("rates", classify("TLT", book)["risk"] == "rates")
    chk("spy", classify("SPY", book)["region"] == "US" and classify("SPY", book)["risk"] == "liquid")
    flows = attach([
        {"date": "2026-09-24", "symbol": "SPY", "aum": 100.0, "nav": 10.0},
        {"date": "2026-09-25", "symbol": "SPY", "aum": 110.0, "nav": 10.0},
        {"date": "2026-09-24", "symbol": "EWT", "aum": 100.0, "nav": 10.0},
        {"date": "2026-09-25", "symbol": "EWT", "aum": 101.0, "nav": 10.1},
    ], book)
    by = {(r["symbol"], r["date"]): r for r in flows}
    chk("inflow", by[("SPY", "2026-09-25")]["inflow"] == 10.0 and by[("SPY", "2026-09-25")]["region"] == "US")
    chk("flat", abs(by[("EWT", "2026-09-25")]["flow"]) < 1e-9 and by[("EWT", "2026-09-25")]["underlying_ccy"] == "TWD")
    chk("first day empty", by[("SPY", "2026-09-24")]["flow"] is None)
    chk("unknown kept", classify("ZZZ", book)["region"] is None)
    bad = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG097 v0100] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    import sys
    raise SystemExit(selftest())
