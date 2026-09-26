#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show the short broker name. A filename hit beats the email domain."""
from __future__ import annotations

import importlib.util
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONTACT = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+|(?:https?://|www\.)\S+", re.I)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _load("ident_v0101", HERE / "VRN_ENG111_StockIdentity_v0101.py")


def strip_contacts(text: str) -> str:
    return CONTACT.sub(" ", text or "")


def _show(row: dict) -> str:
    return str(row.get("show") or row.get("canonical") or "")


def broker_of(text: str) -> str:
    folded = strip_contacts(text).upper()
    best = None
    best_len = 0
    for row in BASE.broker_rows():
        for alias in row.get("aliases") or []:
            alias = str(alias).strip()
            if len(alias) < 2:
                continue
            if re.search(r"[\u4e00-\u9fff]", alias):
                hit = alias in strip_contacts(text)
            else:
                hit = re.search(rf"(?<![A-Z]){re.escape(alias.upper())}(?![A-Z])", folded) is not None
            if hit and len(alias) > best_len:
                best, best_len = row, len(alias)
    return _show(best) if best else ""


def _roc(filename: str) -> str:
    match = re.search(r"(?<!\d)(1\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)", filename or "")
    if not match:
        return ""
    year, month, day = match.groups()
    return f"{1911 + int(year)}-{month}-{day}"


def _short_year(filename: str) -> str:
    match = re.search(r"(?<=[A-Za-z])(\d{2})(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])(?!\d)", filename or "")
    if not match:
        return ""
    year, month, day = match.groups()
    if not 20 <= int(year) <= 40:
        return ""
    return f"20{year}-{month}-{day}"


def identify(filename: str, text: str, markets: dict | None = None) -> dict:
    got = BASE.identify(filename, text, markets)
    head = strip_contacts((got.get("restored") or "").split("評等分級")[0])
    got["broker"] = broker_of(filename) or broker_of(head)
    name = str(got.get("name") or "").replace("*", "")
    if not name and got.get("ticker"):
        hit = re.search(r"([\u4e00-\u9fffA-Za-z0-9\-\.]{2,12})\*+\s*[（(]\s*" + re.escape(got["ticker"]), text or "")
        name = hit.group(1) if hit else ""
    got["name"] = name
    if not got.get("report_date"):
        got["report_date"] = _roc(filename) or _short_year(filename)
    date = str(got.get("report_date") or "").replace("-", "")
    ticker = str(got.get("ticker") or "")
    if got["broker"] and re.fullmatch(r"[1-9]\d{3}", ticker) and re.fullmatch(r"20\d{6}", date):
        got["report_code"] = f"{got['broker']}-{ticker}-{date}"
    else:
        got["report_code"] = ""
    got["cross"] = bool(got["report_code"] and got.get("yfinance"))
    return got


def selftest() -> int:
    daiwa = identify(
        "Daiwa-1319 20231011.pdf",
        "東陽(1319) HOLD Target price 80 報告日期：2023.10.11 helen.chien@daiwacm-cathay.com.tw Source: Daiwa",
    )
    mega = identify("20250819兆豐個股報告-泓德能源(6873).pdf", "泓德能源(6873) 逢低買進 $208 報告日期：2025.08.19", {"6873": {"market": "TWSE", "name": "泓德能源"}})
    ctbc = identify("南亞(1303,B_買進)-CTBC260918.pdf", "南亞(1303) 買進", {"1303": {"market": "TWSE"}})
    hua = identify("華南投顧-2606-裕民-1141202.pdf", "裕民(2606) 買進", {"2606": {"market": "TWSE"}})
    odd = identify("華南投顧-3017-奇鋐-1141202.pdf", "奇鋐(3017)", {"3017": {"market": "TWSE"}})
    mq = identify("MQ-1560 20260520.pdf", "中砂(1560) BUY 報告日期：2026.05.20")
    star = identify("Citi-5904 20260916.pdf", "寶雅*(5904) BUY 報告日期：2026.09.16", {"5904": {"market": "TPEX"}})
    ok = daiwa["broker"] == "Daiwa" and daiwa["report_code"] == "Daiwa-1319-20231011"
    ok = ok and mega["broker"] == "兆豐" and mega["report_code"] == "兆豐-6873-20250819" and mega["yfinance"] == "6873.TW"
    ok = ok and ctbc["broker"] == "中信" and ctbc["report_code"] == "中信-1303-20260918" and ctbc["cross"] is True
    ok = ok and hua["report_code"] == "華南-2606-20251202" and odd["report_code"] == "華南-3017-20251202"
    ok = ok and mq["broker"] == "MQ" and star["name"] == "寶雅" and star["broker"] == "Citi"
    print("  [OK]" if ok else "  [FAIL] " + str((ctbc["report_code"], hua["report_code"], odd["report_code"], daiwa["broker"])))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
