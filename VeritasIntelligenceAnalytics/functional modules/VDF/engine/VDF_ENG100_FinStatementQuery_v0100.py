#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG100 — financial query contract for VRN.

Taiwan statements stay on TWSE/TPEX. International statements stay on
yfinance. 2330 and 3324 may be typed as the bare code, the Yahoo suffix,
or the Bloomberg form. A bare code is not guessed onto .TW.
Basic EPS and diluted EPS never share a label.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
BOOK = VIA / "supportive modules" / "registry" / "VIA_FinStatement_Query_v0100.json"
BROKERS = VIA / "functional modules" / "VRN" / "knowledge" / "VRN_Broker_Dict_v0100.json"

_YF = re.compile(r"^(\d{4})\.(TW|TWO)$", re.I)
_BB = re.compile(r"^(\d{4})\s+TT$", re.I)
_BARE = re.compile(r"^(\d{4})$")


def parse_ticker(text: str, market: str | None = None) -> dict:
    raw = str(text or "").strip().upper()
    market = {"TWSE": "TWSE", "TPEX": "TPEX", "TW": "TWSE", "TWO": "TPEX"}.get(str(market or "").upper())
    code = suffix = None
    matched_yf = _YF.match(raw)
    matched_bb = _BB.match(raw)
    if matched_yf:
        code = matched_yf.group(1)
        market = "TWSE" if matched_yf.group(2) == "TW" else "TPEX"
    elif matched_bb:
        code = matched_bb.group(1)
    elif _BARE.match(raw):
        code = raw
    else:
        return {"ok": False, "why": "unparsed", "raw": raw}
    if market not in {"TWSE", "TPEX"}:
        return {"ok": False, "why": "needs_market", "code": code, "raw": raw}
    yf = code + (".TW" if market == "TWSE" else ".TWO")
    return {"ok": True, "code": code, "market": market, "native": code, "yfinance": yf, "bloomberg": code + " TT"}


def select_tickers(current: list[str], add: list[str] | None = None, remove: list[str] | None = None) -> list[str]:
    chosen = []
    for item in list(current) + list(add or []):
        if item not in chosen and item not in set(remove or []):
            chosen.append(item)
    return chosen


def eps_kind(label: str, book: dict | None = None) -> str | None:
    book = book or json.loads(BOOK.read_text(encoding="utf-8"))
    text = str(label or "").strip()
    folded = text.casefold().replace(" ", "")
    basic = any(text == item or folded == item.casefold().replace(" ", "") for item in book["eps"]["basic"])
    diluted = any(text == item or folded == item.casefold().replace(" ", "") for item in book["eps"]["diluted"])
    if "基本" in text and "稀釋" in text:
        return None
    if basic and diluted:
        return None
    if basic or "基本每股盈餘" in text:
        return "basic"
    if diluted or "稀釋每股盈餘" in text:
        return "diluted"
    return None


def single_quarter(ytd: dict) -> dict:
    """Income statements from MOPS are year-to-date. Q1 stands alone."""
    out = {}
    previous = 0.0
    for quarter in (1, 2, 3, 4):
        value = ytd.get(quarter)
        if value is None or previous is None:
            out[quarter] = None
            previous = None if value is None else value
            continue
        out[quarter] = float(value) - float(previous)
        previous = float(value)
    return out


def period_span(start: str, latest: str) -> list[str]:
    def parse(token: str) -> tuple[int, int]:
        year, quarter = token.upper().split("Q")
        return int(year), int(quarter)
    sy, sq = parse(start)
    ey, eq = parse(latest)
    out = []
    year, quarter = sy, sq
    while (year, quarter) <= (ey, eq):
        out.append(f"{year}Q{quarter}")
        quarter += 1
        if quarter == 5:
            year, quarter = year + 1, 1
    return out


def match_history(candidate: list, known: dict) -> str | None:
    """Same length and same numbers, or no match. Close values do not count."""
    hits = [name for name, series in known.items() if list(series) == list(candidate)]
    return hits[0] if len(hits) == 1 else None


def check_forecast(op: str, parts: list[float], result: float, tol: float = 1e-6) -> bool:
    if op == "add":
        return abs(sum(parts) - result) <= tol
    if op == "div":
        if len(parts) != 2 or parts[1] == 0:
            return False
        return abs(parts[0] / parts[1] - result) <= tol
    raise ValueError("op must be add or div")


def broker_alias_collisions(brokers: dict) -> list[str]:
    seen = {}
    hits = []
    for name, row in brokers.items():
        aliases = [name] + list((row or {}).get("aliases") or [])
        for alias in aliases:
            key = str(alias).casefold()
            if key in seen and seen[key] != name:
                hits.append(key)
            seen[key] = name
    return hits


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    book = json.loads(BOOK.read_text(encoding="utf-8"))
    tsm = parse_ticker("2330.TW")
    bare = parse_ticker("3324")
    bloomberg = parse_ticker("2330 TT", market="TWSE")
    otc = parse_ticker("3324.two")
    listed = parse_ticker("3324", market="TPEX")
    chk("2330 forms", tsm["ok"] and tsm["yfinance"] == "2330.TW" and tsm["bloomberg"] == "2330 TT"
        and bloomberg["native"] == "2330" and bloomberg["yfinance"] == "2330.TW")
    chk("bare needs market", bare["ok"] is False and bare["why"] == "needs_market")
    chk("3324 suffix", otc["market"] == "TPEX" and listed["yfinance"] == "3324.TWO")
    chk("add remove", select_tickers(["2330"], add=["3324", "2330"], remove=["3324"]) == ["2330"])
    chk("eps split", eps_kind("基本每股盈餘（元）", book) == "basic" and eps_kind("Diluted EPS", book) == "diluted")
    chk("eps ambiguous", eps_kind("EPS", book) is None and eps_kind("Basic EPS / Diluted EPS", book) is None)
    chk("single quarter", single_quarter({1: 10, 2: 25, 3: None, 4: 40}) == {1: 10, 2: 15, 3: None, 4: None})
    chk("span", period_span("2025Q4", "2026Q2") == ["2025Q4", "2026Q1", "2026Q2"])
    chk("history", match_history([2.85, 5.10], {"basic": [2.85, 5.10], "diluted": [2.80, 5.00]}) == "basic")
    chk("forecast", check_forecast("add", [1, 2, 3, 4], 10) and check_forecast("div", [30, 100], 0.3)
        and not check_forecast("add", [1, 2], 10))
    chk("brokers", broker_alias_collisions({"A": {"aliases": ["甲"]}, "B": {"aliases": ["乙"]}}) == []
        and broker_alias_collisions({"A": {"aliases": ["甲"]}, "B": {"aliases": ["甲"]}}) == ["甲"])
    bad = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG100 v0100] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
