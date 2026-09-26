#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Wire the official local name and a field summary. Do not invent financials or copy the page."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def official_of(engine, facts: dict) -> tuple[dict | None, str]:
    ticker = str((facts or {}).get("ticker") or "")
    if engine is None or not ticker or not hasattr(engine, "reconcile"):
        return None, "no_official"
    try:
        found = engine.reconcile(ticker, facts.get("name_hint"), allow_web=False)
    except TypeError:
        found = engine.reconcile(ticker, facts.get("name_hint"))
    verdict = str((found or {}).get("verdict") or "")
    name = str((found or {}).get("official") or "")
    if verdict in {"MATCH", "NO_HINT"} and name:
        return {"companyName": name, "ticker": ticker, "source": "official"}, verdict
    return None, verdict or "no_official"


def field_summary(page_text: str, basic: dict) -> str:
    left = " ".join((page_text or "").split())
    if not left:
        return ""
    parts = []
    for label, key in (("代號", "ticker"), ("公司", "companyName"), ("評等", "rating"), ("報告日", "reportDate")):
        value = str((basic or {}).get(key) or "")
        if value and value != "—":
            parts.append(label + " " + value)
    if not parts:
        return ""
    summary = "。".join(parts) + "。此列是欄位摘要，不是第 1 頁原文。"
    right = " ".join(summary.split())
    if left.startswith(right) or right.startswith(left):
        return ""
    return summary


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _load("tab_report_v0103_wire", HERE / "VRN_ENG110_TabReport_v0103.py")
    reader = _load("tab_report_v0107_wire", HERE / "VRN_ENG110_TabReport_v0107.py")
    fix = _load("tab_report_v0108_wire", HERE / "VRN_ENG110_TabReport_v0108.py")
    holds: list[dict] = []
    names: Counter = Counter()

    def one(path, logic, gate, facts_engine):
        text, got, errors = reader.read_page1(path)
        count = fix._pages(path)
        file_id = hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:16]
        facts = {}
        if facts_engine is not None:
            try:
                facts = facts_engine.filename_facts(path.name)
            except Exception:
                facts = {}
        official, name_state = official_of(facts_engine, facts)
        basic = {}
        if logic is not None:
            try:
                basic, _validation = logic.build_basic_info(
                    file_id=file_id, filename=path.name, file_size=path.stat().st_size,
                    first_page_text=text, pages=count or 1, official=official,
                )
            except Exception:
                basic = {}
        basic, note = fix.correct_year(basic, facts)
        summary = field_summary(text, basic)
        page = {"fileId": file_id, "fileName": path.name, "page": "1" if text else "", "fixed_page1": text, "summary_page1": summary}
        mapped = gate.map_report(basic, page, [])
        names[name_state] += 1
        if note or not got or errors or (text and not summary):
            holds.append({
                "file": path.name, "reader": got or "none", "errors": errors[:3], "pages": count,
                "ticker": basic.get("ticker", ""), "facts_ticker": str(facts.get("ticker") or ""),
                "name": name_state, "summary": "yes" if summary else "empty", "note": note,
            })
        return {
            "file": path.name, "reader": got, "errors": errors, "chars": len(text),
            "basic": basic, "page": page, "facts_ticker": str(facts.get("ticker") or ""), "why": mapped["why"],
        }

    prior._one = one
    prior.read_page1 = reader.read_page1
    card = prior.run(folder, data_root, open_page)
    card["door"] = "VRN_ENG110_TabReport_v0109"
    card["holds"] = holds
    card["names"] = dict(names)
    card["html_written"] = True
    card["db_written"] = card.get("written", 0)
    card["financial"] = "empty until an actual labeled figure is read"
    card["web_lookup"] = False
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _load("tab_report_v0103_main9", HERE / "VRN_ENG110_TabReport_v0103.py")
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("present") else 2


def selftest() -> int:
    page = "裕民(2606) 2025 年稅後 EPS 4.19"
    basic = {"ticker": "2606", "companyName": "裕民", "rating": "—", "reportDate": "2025-12-02"}
    summary = field_summary(page, basic)
    blocked = official_of(None, {"ticker": "2606"})
    ok = summary and "第 1 頁原文" in summary and not page.startswith(summary) and blocked == (None, "no_official")
    print("  [OK]" if ok else "  [FAIL] " + summary)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
