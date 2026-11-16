#!/usr/bin/env python3
"""Read VIA-PAR-001 and write the latest watchlist quotes. Does not calculate indicators."""

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFINITION = ROOT / "data" / "via" / "parameter-definition.json"
OUTPUT = ROOT / "data" / "via" / "sync.json"


def main() -> None:
    definition = json.loads(DEFINITION.read_text(encoding="utf-8"))
    rows = []
    note = ""
    try:
        import yfinance as yf
    except ImportError:
        yf = None
        note = "這台沒有 yfinance，只同步名冊，價格留空。"
    for item in definition["watchlist"]:
        price = None
        change = None
        if yf is not None:
            try:
                frame = yf.Ticker(item["symbol"]).history(period="5d", auto_adjust=True)
                if len(frame) >= 1:
                    price = float(frame["Close"].iloc[-1])
                if len(frame) >= 2 and float(frame["Close"].iloc[-2]) != 0:
                    change = price / float(frame["Close"].iloc[-2]) - 1
            except Exception:
                price = None
                change = None
        rows.append(
            {
                "code": item["code"],
                "symbol": item["symbol"],
                "name": item["name"],
                "price": price,
                "changePct": None if change is None else change * 100,
            }
        )
    payload = {
        "parameter": definition["id"],
        "engine": definition["engine"],
        "watchlistEngine": definition["watchlistEngine"],
        "syncedAt": datetime.now(timezone.utc).isoformat(),
        "note": note,
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    filled = sum(1 for row in rows if row["price"] is not None)
    print(f"{definition['id']} {len(rows)} rows, {filled} priced, {OUTPUT}")


if __name__ == "__main__":
    main()
