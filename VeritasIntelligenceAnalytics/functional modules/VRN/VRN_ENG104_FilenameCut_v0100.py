#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cut a report filename at every script change. Rules stay on the hub."""
from __future__ import annotations

import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent


def _hub():
    hits = sorted((VIA / "supportive modules" / "70_VRN_Rules").glob("SUP_MDL749_VRNFieldRuleHub_v*.py"))
    if not hits:
        raise RuntimeError("SUP_MDL749 missing")
    spec = importlib.util.spec_from_file_location("hub749", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _kind(ch: str) -> str:
    if "\u4e00" <= ch <= "\u9fff":
        return "C"
    if ch.isascii() and ch.isalpha():
        return "E"
    if ch.isdigit():
        return "N"
    return "S"


def _stem(name: str) -> str:
    text = str(name or "").strip()
    for ext in (".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png"):
        if text.lower().endswith(ext):
            return text[: -len(ext)].strip()
    return text


def cut(name: str) -> list[str]:
    stem = _stem(name)
    parts: list[str] = []
    buf: list[str] = []
    prev = ""
    for ch in stem:
        kind = _kind(ch)
        if kind == "S":
            if buf:
                parts.append("".join(buf))
                buf = []
            prev = ""
            continue
        if prev and kind != prev:
            parts.append("".join(buf))
            buf = []
        buf.append(ch)
        prev = kind
    if buf:
        parts.append("".join(buf))
    return [part.strip() for part in parts if part.strip()]


def read_name(name: str) -> dict:
    hub = _hub()
    rows = []
    for token in cut(name):
        if token.isdigit() and len(token) == 4:
            tick = hub.ticker_platform(token) or {}
            if tick.get("canonical"):
                rows.append({
                    "text": token, "role": "TICKER", "code": tick["canonical"],
                    "ambiguous_year": bool(hub.parse_year_any(token)),
                })
                continue
        if token.isdigit() and len(token) > 4:
            found = hub.parse_date_any(token) or {}
            if found.get("iso"):
                rows.append({"text": token, "role": "DATE", "iso": found["iso"], "gran": found.get("gran")})
                continue
        canon, how = hub.broker_of(token)
        if canon:
            rows.append({"text": token, "role": "BROKER", "canon": canon, "how": how})
            continue
        rows.append({"text": token, "role": "OTHER"})
    ticker = next((row for row in rows if row["role"] == "TICKER"), None)
    date = next((row for row in rows if row["role"] == "DATE"), None)
    broker = next((row for row in rows if row["role"] == "BROKER"), None)
    return {"name": name, "parts": rows, "ticker": ticker, "date": date, "broker": broker}


def selftest() -> int:
    got = read_name("JP-2330 20250718.pdf")
    two = cut("6488.TWO.pdf")
    yuanta = read_name("元大-2330.pdf")
    ok = (
        [row["role"] for row in got["parts"]] == ["BROKER", "TICKER", "DATE"]
        and got["ticker"]["code"] == "2330"
        and got["date"]["iso"] == "2025-07-18"
        and got["broker"]["canon"] == "JPM"
        and two == ["6488", "TWO"]
        and yuanta["broker"]["canon"] == "YUANTA"
    )
    print("  [OK]" if ok else f"  [FAIL] {got} {two} {yuanta}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
