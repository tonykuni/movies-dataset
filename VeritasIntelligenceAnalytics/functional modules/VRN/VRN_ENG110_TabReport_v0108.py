#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit fixes that stay on the gate: a year is not a ticker, and pages is the real count.

The summary stays empty. Financial rows stay empty. Company names are not invented.
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
HOLDS: list[dict] = []


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _year(token: str) -> bool:
    return bool(re.fullmatch(r"(?:19|20)\d{2}", token or ""))


def correct_year(basic: dict, facts: dict) -> tuple[dict, str]:
    ticker = str((basic or {}).get("ticker") or "")
    found = str((facts or {}).get("ticker") or "")
    if not (_year(ticker) and re.fullmatch(r"[1-9]\d{3}", found) and not _year(found) and found != ticker):
        return basic, ""
    out = dict(basic)
    out["ticker"] = found
    for key in ("yfinanceTicker", "bloombergTicker", "reportCode"):
        out[key] = str(out.get(key) or "").replace(ticker, found, 1)
    return out, "year_not_ticker"


def _pages(path: Path) -> int:
    try:
        import fitz
        with fitz.open(str(path)) as doc:
            return int(doc.page_count)
    except Exception:
        pass
    try:
        from pypdf import PdfReader
        return len(PdfReader(str(path)).pages)
    except Exception:
        return 0


def _one(path, logic, gate, facts_engine, read_page1):
    text, reader, errors = read_page1(path)
    count = _pages(path)
    file_id = __import__("hashlib").sha256(path.name.encode("utf-8")).hexdigest()[:16]
    basic = {}
    if logic is not None:
        try:
            basic, _validation = logic.build_basic_info(
                file_id=file_id, filename=path.name, file_size=path.stat().st_size,
                first_page_text=text, pages=count or 1,
            )
        except Exception:
            basic = {}
    facts = {}
    if facts_engine is not None:
        try:
            facts = facts_engine.filename_facts(path.name)
        except Exception:
            facts = {}
    basic, note = correct_year(basic, facts)
    page = {"fileId": file_id, "fileName": path.name, "page": "1" if text else "", "fixed_page1": text, "summary_page1": ""}
    mapped = gate.map_report(basic, page, [])
    if note or not reader or errors:
        HOLDS.append({
            "file": path.name, "reader": reader or "none", "errors": errors[:3],
            "pages": count, "ticker": basic.get("ticker", ""), "facts_ticker": str(facts.get("ticker") or ""),
            "note": note,
        })
    return {
        "file": path.name, "reader": reader, "errors": errors, "chars": len(text),
        "basic": basic, "page": page, "facts_ticker": str(facts.get("ticker") or ""), "why": mapped["why"],
    }


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _load("tab_report_v0103_audit", HERE / "VRN_ENG110_TabReport_v0103.py")
    reader = _load("tab_report_v0107_audit", HERE / "VRN_ENG110_TabReport_v0107.py")
    HOLDS.clear()
    prior._one = lambda path, logic, gate, facts: _one(path, logic, gate, facts, reader.read_page1)
    prior.read_page1 = reader.read_page1
    card = prior.run(folder, data_root, open_page)
    card["door"] = "VRN_ENG110_TabReport_v0108"
    card["holds"] = list(HOLDS)
    card["html_written"] = True
    card["db_written"] = 0
    card["summary"] = "empty"
    card["financial"] = "empty"
    card["company_name"] = "official roster not passed"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _load("tab_report_v0103_main", HERE / "VRN_ENG110_TabReport_v0103.py")
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("present") else 2


def selftest() -> int:
    fixed, note = correct_year(
        {"ticker": "2025", "yfinanceTicker": "2025.TW", "bloombergTicker": "2025 TT", "validationStatus": "FAIL_CLOSED"},
        {"ticker": "2606"},
    )
    kept, none = correct_year({"ticker": "3231", "validationStatus": "PHASE2_OK"}, {"ticker": "3231"})
    ok = note == "year_not_ticker" and fixed["ticker"] == "2606" and fixed["validationStatus"] == "FAIL_CLOSED" and none == "" and kept["ticker"] == "3231"
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
