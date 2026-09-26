#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Broker and company names match on a part. The exchange list, not a guess, picks .TW or .TWO."""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _load("ident_v0100", HERE / "VRN_ENG111_StockIdentity_v0100.py")


def broker_rows() -> list:
    hits = sorted((HERE / "registry").glob("VRN_BROKER_LIST_v*.json"))
    if not hits:
        return []
    data = json.loads(hits[-1].read_text(encoding="utf-8"))
    return list(data.get("brokers") or [])


def _abbr(row: dict) -> str:
    aliases = [str(item) for item in row.get("aliases") or []]
    if "MCQN" in aliases:
        return "MCQN"
    if row.get("canonical") == "Daiwa" or "DAIWA" in aliases:
        return "DAIWA"
    english = str(row.get("canonical_en") or row.get("canonical") or "")
    return english.split()[0] if english else ""


def broker_of(text: str, rows: list | None = None) -> str:
    rows = broker_rows() if rows is None else rows
    folded = (text or "").upper()
    best = None
    best_len = 0
    for row in rows:
        for alias in row.get("aliases") or []:
            alias = str(alias).strip()
            if len(alias) < 2:
                continue
            if re.search(r"[\u4e00-\u9fff]", alias):
                hit = alias in (text or "")
            else:
                hit = re.search(rf"(?<![A-Z0-9]){re.escape(alias.upper())}(?![A-Z0-9])", folded) is not None
            if hit and len(alias) > best_len:
                best, best_len = row, len(alias)
    return _abbr(best) if best else ""


def name_part(name: str, text: str) -> bool:
    token = str(name or "").strip()
    if len(token) < 2:
        return False
    if token in (text or ""):
        return True
    return len(token) >= 2 and token[:2] in (text or "")


def identify(filename: str, text: str, markets: dict | None = None) -> dict:
    got = BASE.identify(filename, text)
    head = (got.get("restored") or "").split("評等分級")[0]
    found = broker_of(filename + "\n" + head)
    if found:
        got["broker"] = found
    code = got.get("ticker") or ""
    hit = (markets or {}).get(code) or {}
    if hit.get("market") == "TWSE":
        got["market"] = "TWSE"
        got["yfinance"] = code + ".TW"
    elif hit.get("market") == "TPEX":
        got["market"] = "TPEX"
        got["yfinance"] = code + ".TWO"
    if hit.get("name") and not got.get("name"):
        got["name"] = hit["name"]
    got["name_match"] = name_part(got.get("name") or "", text or "")
    got["forms"] = [code, got.get("yfinance") or "", got.get("bloomberg") or ""] if code else []
    return got


def selftest() -> int:
    page = "泓德能源(6873) 逢低買進 $208 報告日期：2025.08.19 研究員：邱岳霖 收盤價： 169.50 潛在上漲空間22.7%"
    hua = identify("華南投顧-2606-裕民-1141202.pdf", "裕民(2606) 買進 報告日期：2025.12.02")
    daiwa = identify("Daiwa-1319 20260521.pdf", "1319 TT")
    mega = identify("20250819兆豐個股報告-泓德能源(6873).pdf", page, {"6873": {"market": "TWSE", "name": "泓德能源"}})
    ok = hua["broker"] == "HuaNan" and hua["name_match"] is True and daiwa["broker"] == "DAIWA"
    ok = ok and mega["yfinance"] == "6873.TW" and mega["market"] == "TWSE" and mega["rating"] == "逢低買進"
    ok = ok and broker_of("MCQN 麥格理") == "MCQN"
    print("  [OK]" if ok else "  [FAIL] " + str((hua["broker"], daiwa["broker"], mega["yfinance"], mega["rating"])))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
