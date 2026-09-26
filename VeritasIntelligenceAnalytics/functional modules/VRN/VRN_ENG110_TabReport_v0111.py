#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stock reports use the filename code when the first page repeats it. Years and legends do not."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def field_summary(ident: dict) -> str:
    rows = (
        ("報告日", "report_date"), ("券商", "broker"), ("分析師", "analyst"),
        ("代號", "ticker"), ("Yahoo", "yfinance"), ("Bloomberg", "bloomberg"),
        ("名稱", "name"), ("英文名", "english_name"), ("評等", "rating"),
        ("目標價", "target"), ("收盤價", "close"), ("上漲空間", "upside"),
    )
    parts = [label + " " + str(ident.get(key)) for label, key in rows if ident.get(key)]
    if not parts:
        return ""
    summary = "。".join(parts) + "。此列是欄位摘要，不是第 1 頁原文。"
    page = " ".join(str(ident.get("restored") or "").split())
    right = " ".join(summary.split())
    if page.startswith(right) or right.startswith(page):
        return ""
    return summary


def _apply(basic: dict, ident: dict) -> dict:
    if not ident.get("ticker"):
        return basic
    out = dict(basic)
    out["reportType"] = "STOCK"
    out["ticker"] = ident["ticker"]
    out["companyName"] = ident["name"] or out.get("companyName") or "—"
    if ident["broker"]:
        out["broker"] = ident["broker"]
        out["brokerAbbr"] = ident["broker"]
        out["issuer"] = ident["broker"]
    if ident["report_date"]:
        out["reportDate"] = ident["report_date"]
        out["period"] = ident["report_date"][:4]
    if ident["rating"]:
        out["rating"] = ident["rating"]
        out["ratingCat"] = ident["rating"]
    if ident["bloomberg"]:
        out["bloombergTicker"] = ident["bloomberg"]
    if ident["yfinance"]:
        out["yfinanceTicker"] = ident["yfinance"]
        out["market"] = ident["market"] or out.get("market") or "—"
    elif str(out.get("yfinanceTicker") or "").split(".")[0] != ident["ticker"]:
        out["yfinanceTicker"] = "—"
        out["market"] = "UNKNOWN"
    out["validationStatus"] = "REVIEW_REQUIRED"
    out["validationRisk"] = "YELLOW"
    out["status"] = "warn"
    return out


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _load("tab_v0103_ident", HERE / "VRN_ENG110_TabReport_v0103.py")
    reader = _load("tab_v0107_ident", HERE / "VRN_ENG110_TabReport_v0107.py")
    fix = _load("tab_v0108_ident", HERE / "VRN_ENG110_TabReport_v0108.py")
    scope = _load("tab_v0110_ident", HERE / "VRN_ENG110_TabReport_v0110.py")
    ident_mod = _load("stock_ident", HERE / "VRN_ENG111_StockIdentity_v0100.py")
    cut = _load("cut_ident", HERE / "VRN_ENG104_FilenameCut_v0100.py")
    holds = []

    def one(path, logic, gate, facts_engine):
        text, got, errors = reader.read_page1(path)
        count = fix._pages(path)
        file_id = hashlib.sha256(path.name.encode("utf-8")).hexdigest()[:16]
        found = ident_mod.identify(path.name, text)
        basic = {}
        if logic is not None:
            try:
                basic, _validation = logic.build_basic_info(
                    file_id=file_id, filename=path.name, file_size=path.stat().st_size,
                    first_page_text=text, pages=count or 1,
                )
            except Exception:
                basic = {}
        basic = _apply(basic, found)
        summary = field_summary(found) if found.get("report_type") == "STOCK" else ""
        page = {
            "fileId": file_id, "fileName": path.name, "page": "1" if text else "",
            "fixed_page1": found["restored"] or text, "summary_page1": summary,
        }
        mapped = gate.map_report(basic, page, [])
        if found.get("report_type") != "STOCK" or errors:
            holds.append({"file": path.name, "ticker": found.get("ticker") or "", "codes": found.get("codes") or [], "errors": errors[:2]})
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
    card["door"] = "VRN_ENG110_TabReport_v0111"
    card["scope"] = "stock"
    card["pdf_all"] = len(all_pdf)
    card["skipped_non_stock"] = len(skipped)
    card["later"] = skipped
    card["holds"] = holds
    card["identity"] = "filename code must repeat on page 1"
    card["english_name"] = "not fetched"
    card["factset_median"] = "not fetched"
    card["financial"] = "empty until an actual labeled figure is read"
    card["web_lookup"] = False
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _load("tab_v0103_main11", HERE / "VRN_ENG110_TabReport_v0103.py")
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("present") else 2


def selftest() -> int:
    ident = _load("stock_ident_test", HERE / "VRN_ENG111_StockIdentity_v0100.py")
    if ident.selftest() != 0:
        return 1
    filename = "20250819兆豐個股報告-泓德能源(6873).pdf"
    page = "泓德能源(6873) 逢低買進 $208 報告日期：2025.08.19 融資餘額 3005 評等分級：賣出"
    found = ident.identify(filename, page)
    summary = field_summary(found)
    basic = _apply({"ticker": "3005", "yfinanceTicker": "3005.TW", "validationStatus": "PHASE2_OK"}, found)
    ok = "6873" in summary and "3005" not in summary and "SELL" not in summary and basic["ticker"] == "6873"
    ok = ok and basic["rating"] == "逢低買進" and basic["validationStatus"] == "REVIEW_REQUIRED"
    print("  [OK]" if ok else "  [FAIL] " + summary + " " + str(basic.get("ticker")))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
