#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Map a logic result onto the store gate. The original row is not rewritten."""
from __future__ import annotations

import importlib.util
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
DASH = "—"


def _store():
    spec = importlib.util.spec_from_file_location("tab_store_gate", HERE / "VRN_ENG109_TabStore_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _filled(value) -> bool:
    text = _text(value)
    return bool(text) and text not in {DASH, "None"}


def _basic_ready(basic: dict, fields: tuple[str, ...]) -> str:
    if basic.get("validationStatus") != "PHASE2_OK":
        return "basic_status"
    if basic.get("validationRisk") != "GREEN":
        return "basic_risk"
    if basic.get("status") != "ok":
        return "basic_state"
    for field in fields:
        if not _filled(basic.get(field)):
            return "basic_blank:" + field
    return ""


def _copy_text(fixed: str, summary: str) -> bool:
    left = " ".join(fixed.split())
    right = " ".join(summary.split())
    return (not left) or (not right) or left.startswith(right) or right.startswith(left)


def _page_ready(page: dict) -> str:
    if str(page.get("page", "")).strip() != "1":
        return "page_not_1"
    fixed = _text(page.get("fixed_page1"))
    summary = _text(page.get("summary_page1"))
    if not fixed or not summary:
        return "page_empty"
    if _copy_text(fixed, summary):
        return "summary_is_copy"
    return ""


def _defects_empty(value) -> bool:
    if value in (None, "", [], ()):
        return True
    return _text(value) in {"[]", ""}


def _row_ready(row: dict, fields: tuple[str, ...]) -> str:
    if row.get("grade") != "V" or row.get("status") != "ok" or not _defects_empty(row.get("defects")):
        return "row_grade"
    value = row.get("value")
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        return "row_value"
    for field in fields:
        if field in {"value", "defects", "status", "grade"}:
            continue
        if not _filled(row.get(field)):
            return "row_blank:" + field
    return ""


def map_report(basic: dict, page: dict, financial: list[dict]) -> dict:
    store = _store()
    why = []
    basic_why = _basic_ready(basic, store.BASIC)
    page_why = _page_ready(page)
    if basic_why:
        why.append(basic_why)
    if page_why:
        why.append(page_why)
    if not financial:
        why.append("financial_empty")
    else:
        for index, row in enumerate(financial):
            row_why = _row_ready(row, store.FINANCIAL)
            if row_why:
                why.append(f"{index}:{row_why}")
    if why:
        return {"ready": False, "why": why, "report": None}
    basic_copy = dict(basic)
    basic_copy["validationStatus"] = "VERIFIED"
    rows = []
    for row in financial:
        copied = dict(row)
        copied["status"] = "VERIFIED"
        copied["defects"] = [] if _defects_empty(row.get("defects")) else row.get("defects")
        rows.append(copied)
    report = {"basic": basic_copy, "page1": dict(page), "financial": rows}
    if not store.accept(report):
        return {"ready": False, "why": ["accept"], "report": None}
    return {"ready": True, "why": [], "report": report}


def _sample() -> tuple[dict, dict, dict]:
    store = _store()
    basic = {field: "x" for field in store.BASIC}
    basic.update({"validationStatus": "PHASE2_OK", "validationRisk": "GREEN", "status": "ok", "fileId": "f1"})
    page = {"fileId": "f1", "fileName": "a.pdf", "page": 1, "fixed_page1": "The company raised its target.", "summary_page1": "Target raised after the visit."}
    row = {field: "x" for field in store.FINANCIAL}
    row.update({"fileId": "f1", "grade": "V", "status": "ok", "defects": [], "value": 12.5})
    return basic, page, row


def selftest() -> int:
    basic, page, row = _sample()
    good = map_report(basic, page, [row])
    dashed = dict(basic)
    dashed["companyName"] = DASH
    bad_name = map_report(dashed, page, [row])
    later = dict(page)
    later["page"] = 2
    bad_page = map_report(basic, later, [row])
    copied = dict(page)
    copied["summary_page1"] = page["fixed_page1"][:40]
    bad_summary = map_report(basic, copied, [row])
    weak = dict(row)
    weak["grade"] = "M"
    weak["status"] = "warn"
    bad_row = map_report(basic, page, [row, weak])
    ok = (
        good["ready"] is True
        and good["report"]["basic"]["validationStatus"] == "VERIFIED"
        and basic["validationStatus"] == "PHASE2_OK"
        and row["status"] == "ok"
        and bad_name["ready"] is False
        and bad_page["why"] == ["page_not_1"]
        and bad_summary["why"] == ["summary_is_copy"]
        and bad_row["ready"] is False
        and map_report(basic, page, [])["why"] == ["financial_empty"]
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
