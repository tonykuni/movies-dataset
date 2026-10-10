#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Store verified VRN tabs only. Unverified rows are not written."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASIC = (
    "fileId", "fileName", "reportType", "ticker", "market",
    "yfinanceTicker", "bloombergTicker", "tickerKind", "companyName",
    "broker", "brokerAbbr", "reportDate", "reportCode", "language",
    "period", "pages", "issuer", "rating", "ratingCat",
    "validationStatus", "validationRisk", "status",
)
FINANCIAL = (
    "fileId", "fileName", "category", "statement", "item", "dataName",
    "period", "value", "unit", "confidence", "source", "status",
    "grade", "defects",
)
CLOUDS = ("onedrive", "dropbox", "google drive", "googledrive", "box", "icloud", "mega", "pcloud")


def cloud_of(path: Path) -> str:
    text = str(path).lower()
    for name in CLOUDS:
        if name in text:
            return "googledrive" if name.startswith("google") else name
    return "local"


def choose_root() -> Path:
    picked = os.environ.get("VIA_VRN_DATA", "").strip()
    if picked:
        return Path(picked)
    return HERE / "output_hub" / "vrn"


def _full(row: dict, fields: tuple[str, ...]) -> bool:
    return all(str(row.get(field, "")).strip() for field in fields)


def accept(report: dict) -> bool:
    basic = report.get("basic") or {}
    page = report.get("page1") or {}
    financial = report.get("financial") or []
    if basic.get("validationStatus") != "VERIFIED" or not _full(basic, BASIC):
        return False
    if not str(page.get("fixed_page1", "")).strip() or not str(page.get("summary_page1", "")).strip():
        return False
    if not financial:
        return False
    return all(row.get("status") == "VERIFIED" and _full(row, FINANCIAL) for row in financial)


def probe(root: Path) -> dict:
    root.mkdir(parents=True, exist_ok=True)
    mark = root / ".via_link"
    mark.write_text("ok", encoding="utf-8")
    linked = mark.read_text(encoding="utf-8") == "ok"
    mark.unlink()
    return {"root": str(root), "cloud": cloud_of(root), "linked": linked}


def store(report: dict, root: Path) -> dict:
    if not accept(report):
        return {"written": 0, "why": "UNVERIFIED"}
    import duckdb
    import pandas as pd
    root.mkdir(parents=True, exist_ok=True)
    basic = dict(report["basic"])
    page = {
        "fileId": basic["fileId"],
        "fixed_page1": report["page1"]["fixed_page1"],
        "summary_page1": report["page1"]["summary_page1"],
    }
    frames = {
        "basic": pd.DataFrame([basic]),
        "page1": pd.DataFrame([page]),
        "financial": pd.DataFrame(report["financial"]),
    }
    digest = hashlib.sha256(json.dumps(report, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:20]
    for name, frame in frames.items():
        folder = root / name
        folder.mkdir(parents=True, exist_ok=True)
        target = folder / f"part-{digest}.parquet"
        if not target.exists():
            frame.to_parquet(target, index=False)
    database = root / "vrn_tabs.duckdb"
    con = duckdb.connect(str(database))
    for name in frames:
        glob = str(root / name / "part-*.parquet").replace("'", "''")
        con.execute(f"CREATE OR REPLACE VIEW vrn_{name} AS SELECT * FROM read_parquet('{glob}', union_by_name=true)")
    counts = {name: con.execute(f"SELECT COUNT(*) FROM vrn_{name}").fetchone()[0] for name in frames}
    con.close()
    return {"written": 1, "why": "VERIFIED", "counts": counts, "part": digest}


def run() -> dict:
    root = choose_root()
    link = probe(root)
    return {
        "via": "vcgc",
        "door": "VRN_ENG109_TabStore_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "tabs": ["BASIC INFO", "FIXED FETCH CONTENTS ON PAGE 1 / SUMMARY OF PAGE 1", "FINANCIAL DATA"],
        "basic_fields": len(BASIC),
        "financial_fields": len(FINANCIAL),
        "root": link["root"],
        "cloud": link["cloud"],
        "linked": link["linked"],
        "written": 0,
        "hub_edited": False,
        "intake_edited": False,
        "do_not": ["write an unverified tab", "edit intake macro_ssot", "scan every cloud account"],
        "next": "none",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    print(json.dumps(run(), ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    bad = store({"basic": {"validationStatus": "FAIL"}, "page1": {}, "financial": []}, Path("/tmp/vrn_tab_bad"))
    good_basic = {field: "x" for field in BASIC}
    good_basic["validationStatus"] = "VERIFIED"
    good_basic["fileId"] = "t1"
    good_fin = {field: "x" for field in FINANCIAL}
    good_fin["status"] = "VERIFIED"
    good_fin["fileId"] = "t1"
    root = Path("/tmp/vrn_tab_good")
    if root.exists():
        for path in sorted(root.rglob("*"), reverse=True):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                path.rmdir()
    good = store({
        "basic": good_basic,
        "page1": {"fixed_page1": "FIXED", "summary_page1": "SUMMARY"},
        "financial": [good_fin],
    }, root)
    link = probe(Path("/tmp/OneDrive/vrn"))
    ok = bad["written"] == 0 and bad["why"] == "UNVERIFIED" and good["written"] == 1 and good["counts"]["basic"] == 1 and link["cloud"] == "onedrive" and link["linked"] is True and len(BASIC) == 22 and len(FINANCIAL) == 14
    print("  [OK]" if ok else "  [FAIL] " + json.dumps({"bad": bad, "good": good, "link": link}, default=str))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
