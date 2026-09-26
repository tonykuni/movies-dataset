#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Short broker names. A crossed basic row is stored. Financial cells stay empty."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
KEEP = (
    "fileId", "fileName", "reportType", "ticker", "market", "yfinanceTicker", "bloombergTicker",
    "tickerKind", "companyName", "broker", "brokerAbbr", "reportDate", "reportCode", "language",
    "period", "pages", "issuer", "rating", "ratingCat", "validationStatus", "validationRisk", "status",
)


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _code(row: dict) -> str:
    broker = str(row.get("broker") or "")
    ticker = str(row.get("ticker") or "")
    date = str(row.get("reportDate") or "").replace("-", "")
    if broker in {"", "—", "-"} or not re.fullmatch(r"[1-9]\d{3}", ticker) or not re.fullmatch(r"20\d{6}", date):
        return ""
    return f"{broker}-{ticker}-{date}"


def _stamp(basic: dict, found: dict) -> dict:
    report = _load("apply_v0111", HERE / "VRN_ENG110_TabReport_v0111.py")
    out = report._apply(basic, found)
    if found.get("broker"):
        out["broker"] = found["broker"]
        out["brokerAbbr"] = found["broker"]
        out["issuer"] = found["broker"]
    code = found.get("report_code") or _code(out)
    if code:
        out["reportCode"] = code
    if found.get("name"):
        out["companyName"] = found["name"]
    yahoo = str(out.get("yfinanceTicker") or "")
    if code and yahoo not in {"", "—"} and "." in yahoo:
        out["validationStatus"] = "CROSS_CHECKED"
        out["validationRisk"] = "GREEN"
        out["status"] = "ok"
    return out


def _store(root: Path, rows: list) -> int:
    if not rows:
        return 0
    root.mkdir(parents=True, exist_ok=True)
    try:
        import duckdb
    except ImportError:
        (root / "vrn_basic_v0100.jsonl").write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n", encoding="utf-8")
        return len(rows)
    cols = ", ".join(f"{key} VARCHAR" for key in KEEP)
    con = duckdb.connect(str(root / "vrn_basic.duckdb"))
    con.execute(f"CREATE OR REPLACE TABLE basic_info ({cols})")
    marks = ", ".join("?" for _ in KEEP)
    con.executemany(
        f"INSERT INTO basic_info VALUES ({marks})",
        [tuple(str(row.get(key) or "") for key in KEEP) for row in rows],
    )
    con.execute(f"COPY basic_info TO '{(root / 'vrn_basic_v0100.parquet').as_posix()}' (FORMAT PARQUET)")
    con.close()
    return len(rows)


def run(folder: Path, data_root: Path, open_page: bool) -> dict:
    prior = _load("tab_v0103_show", HERE / "VRN_ENG110_TabReport_v0103.py")
    reader = _load("tab_v0107_show", HERE / "VRN_ENG110_TabReport_v0107.py")
    fix = _load("tab_v0108_show", HERE / "VRN_ENG110_TabReport_v0108.py")
    scope = _load("tab_v0110_show", HERE / "VRN_ENG110_TabReport_v0110.py")
    report = _load("tab_v0111_show", HERE / "VRN_ENG110_TabReport_v0111.py")
    ident_mod = _load("stock_ident_v0102", HERE / "VRN_ENG111_StockIdentity_v0102.py")
    cut = _load("cut_show", HERE / "VRN_ENG104_FilenameCut_v0100.py")
    market_mod = _load("tw_market_show", VIA / "functional modules" / "VDF" / "engine" / "VDF_ENG118_TWMarket_v0100.py")
    listing = "LIVE"
    try:
        markets = market_mod.load()
    except Exception as exc:
        markets = {}
        listing = type(exc).__name__
    landed = []
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
        basic = _stamp(basic, found)
        basic["fileId"] = file_id
        basic["fileName"] = path.name
        basic["pages"] = count or basic.get("pages") or ""
        summary = report.field_summary(found) if found.get("report_type") == "STOCK" else ""
        page = {
            "fileId": file_id, "fileName": path.name, "page": "1" if text else "",
            "fixed_page1": found.get("restored") or text, "summary_page1": summary,
        }
        mapped = gate.map_report(basic, page, [])
        if basic.get("validationStatus") == "CROSS_CHECKED":
            landed.append(basic)
        else:
            holds.append({"file": path.name, "ticker": found.get("ticker") or "", "broker": found.get("broker") or ""})
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
    card["door"] = "VRN_ENG110_TabReport_v0113"
    card["scope"] = "stock"
    card["pdf_all"] = len(all_pdf)
    card["skipped_non_stock"] = len(skipped)
    card["later"] = skipped
    card["holds"] = holds[:30]
    card["listing"] = listing
    card["listing_n"] = len(markets)
    card["broker_show"] = "canonical"
    card["basic_written"] = _store(data_root / "basic", landed)
    card["financial"] = "empty until an actual labeled figure is read"
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    prior = _load("tab_v0103_main13", HERE / "VRN_ENG110_TabReport_v0103.py")
    folder = Path(os.environ.get("VIA_VRN_SAMPLES", str(prior.DEFAULT_DIR)))
    data = Path(os.environ["VIA_VRN_DATA"]) if os.environ.get("VIA_VRN_DATA") else HERE / "output_hub" / "vrn"
    card = run(folder, data, True)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card.get("present") else 2


def selftest() -> int:
    ident = _load("ident_self_13", HERE / "VRN_ENG111_StockIdentity_v0102.py").selftest()
    stamped = _stamp(
        {"ticker": "6933", "brokerAbbr": "CTBC", "reportCode": "CTBC-6933-20230925", "reportDate": "2023-09-25", "yfinanceTicker": "6933.TW"},
        {"ticker": "6933", "broker": "中信", "name": "AMAX-KY", "report_date": "", "report_code": "", "yfinance": "6933.TW", "market": "TWSE", "bloomberg": "6933 TT", "rating": ""},
    )
    ok = stamped["reportCode"] == "中信-6933-20230925" and stamped["validationStatus"] == "CROSS_CHECKED"
    print("  [OK]" if ok else "  [FAIL] " + stamped["reportCode"])
    return 0 if ident == 0 and ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
