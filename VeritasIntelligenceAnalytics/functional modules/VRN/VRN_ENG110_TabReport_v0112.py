#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stock reports. Broker names come from the list. The exchange list sets .TW or .TWO."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _load("tab_v0103_mkt", HERE / "VRN_ENG110_TabReport_v0103.py")
    reader = _load("tab_v0107_mkt", HERE / "VRN_ENG110_TabReport_v0107.py")
    fix = _load("tab_v0108_mkt", HERE / "VRN_ENG110_TabReport_v0108.py")
    scope = _load("tab_v0110_mkt", HERE / "VRN_ENG110_TabReport_v0110.py")
    report = _load("tab_v0111_mkt", HERE / "VRN_ENG110_TabReport_v0111.py")
    ident_mod = _load("stock_ident_v0101", HERE / "VRN_ENG111_StockIdentity_v0101.py")
    cut = _load("cut_mkt", HERE / "VRN_ENG104_FilenameCut_v0100.py")
    market_mod = _load("tw_market", VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG118_TWMarket_v0100.py")
    listing = "LIVE"
    try:
        markets = market_mod.load()
    except Exception as exc:
        markets = {}
        listing = type(exc).__name__
    holds = []

    def one(path, logic, gate, facts_engine):
        text, got, errors = reader.read_page1(path)
        count = fix._pages(path)
        file_id = hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:16]
        found = ident_mod.identify(path.name, text, markets)
        basic = {}
        if logic is not None:
            try:
                basic, _validation = logic.build_basic_info(
                    file_id=file_id, filename=path.name, file_size=path.stat().st_size,
                    first_page_text=text, pages=count or 1,
                )
            except Exception:
                basic = {}
        basic = report._apply(basic, found)
        summary = report.field_summary(found) if found.get("report_type") == "STOCK" else ""
        page = {
            "fileId": file_id, "fileName": path.name, "page": "1" if text else "",
            "fixed_page1": found.get("restored") or text, "summary_page1": summary,
        }
        mapped = gate.map_report(basic, page, [])
        if found.get("report_type") != "STOCK" or not found.get("broker") or not found.get("yfinance"):
            holds.append({
                "file": path.name, "ticker": found.get("ticker") or "", "broker": found.get("broker") or "",
                "market": found.get("market") or "", "yfinance": found.get("yfinance") or "",
            })
        return {
            "file": path.name, "reader": got, "errors": errors, "chars": len(text),
            "basic": basic, "page": page, "facts_ticker": found.get("ticker") or "", "why": mapped["why"],
        }

    all_pdf = sorted(folder.glob("*.pdf")) if folder.is_dir() else []
    skipped = [path.name for path in all_pdf if not scope.is_stock(path.name, cut)]
    original = Path.glob

    def only_stock(self, pattern):
        found = original(self, pattern)
        if self == folder and pattern == "*.pdf":
            return [path for path in found if scope.is_stock(path.name, cut)]
        return found

    Path.glob = only_stock
    try:
        prior._one = one
        card = prior.run(folder, data_root, open_page)
    finally:
        Path.glob = original
    card["door"] = "VRN_ENG110_TabReport_v0112"
    card["scope"] = "stock"
    card["pdf_all"] = len(all_pdf)
    card["skipped_non_stock"] = len(skipped)
    card["later"] = skipped
    card["holds"] = holds[:30]
    card["listing"] = listing
    card["listing_n"] = len(markets)
    card["broker_list"] = "VRN_BROKER_LIST_v02"
    card["financial"] = "empty until an actual labeled figure is read"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _load("tab_v0103_main12", HERE / "VRN_ENG110_TabReport_v0103.py")
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("present") else 2


def selftest() -> int:
    ident = _load("ident_self_12", HERE / "VRN_ENG111_StockIdentity_v0101.py")
    return ident.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
