#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Green matrix of the synced stock-report rows. Reads the file. Does not call VDF."""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORT = VIA / "VIA_Reports" / "vrn" / "sync" / "SYNC_latest.json"
COLUMNS = (
    ("ticker", "代號"),
    ("name", "簡稱"),
    ("market", "市場"),
    ("broker", "券商"),
    ("report_date", "報告日"),
    ("analyst", "分析師"),
    ("yfinance_ticker", "Yahoo"),
    ("bloomberg_ticker", "Bloomberg"),
    ("rating", "評等"),
    ("target_price_adj", "目標價"),
    ("upside_pct", "上漲%"),
    ("file", "檔名"),
)


def _cell(value) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, float):
        return f"{value:.1f}"
    return str(value)


def _width(rows: list[dict], key: str, title: str) -> int:
    widest = len(title)
    for row in rows:
        widest = max(widest, len(_cell(row.get(key))))
    return min(widest, 28)


def bands(rows: list[dict], console_width: int) -> list[list[tuple[str, str]]]:
    keys = list(COLUMNS[:2])
    key_width = sum(_width(rows, key, title) for key, title in keys) + 4
    out, cur, used = [], list(keys), key_width
    for col in COLUMNS[2:]:
        need = _width(rows, col[0], col[1]) + 3
        if len(cur) > 2 and used + need > console_width:
            out.append(cur)
            cur, used = list(keys), key_width
        cur.append(col)
        used += need
    out.append(cur)
    return out


def render(rows: list[dict], console_width: int | None = None) -> None:
    from rich import box
    from rich.console import Console
    from rich.table import Table
    console = Console(width=console_width, force_terminal=True, color_system="standard")
    width = console_width or console.size.width
    for index, cols in enumerate(bands(rows, width), start=1):
        table = Table(
            title=f"個股基本資料 {index}",
            style="green",
            header_style="bold green",
            box=box.SIMPLE_HEAVY,
            pad_edge=False,
        )
        for _key, title in cols:
            table.add_column(title, overflow="fold", max_width=28, style="green")
        for row in rows:
            table.add_row(*(_cell(row.get(key)) for key, _title in cols))
        console.print(table)


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VRN] 拒絕。只能經 via-vcgc。")
        return 2
    if not REPORT.is_file():
        print("[矩陣] ABSENT 同步結果不在")
        return 2
    rows = json.loads(REPORT.read_text(encoding="utf-8")).get("rows") or []
    render(rows)
    return 0 if rows else 2


def selftest() -> int:
    sample = [
        {"ticker": "2330", "name": "台積電", "market": "TWSE", "broker": "JPM", "report_date": "2025-07-18",
         "analyst": "Gokul Hariharan", "yfinance_ticker": "2330.TW", "bloomberg_ticker": "2330 TT",
         "rating": "BUY", "target_price_adj": 1275.0, "upside_pct": -48.5, "file": "JP-2330 20250718.pdf"},
        {"ticker": "6488", "name": "環球晶", "market": "TPEX", "broker": None, "report_date": None,
         "analyst": None, "yfinance_ticker": "6488.TWO", "bloomberg_ticker": "6488 TT",
         "rating": None, "target_price_adj": None, "upside_pct": None, "file": "6488.pdf"},
    ]
    packed = bands(sample, 80)
    ok = packed[0][0][0] == "ticker" and len(packed) >= 2 and packed[1][0][0] == "ticker"
    print("  [OK]" if ok else f"  [FAIL] {[[c[0] for c in band] for band in packed]}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main())
