#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG100 v0101 — bare EPS, actuals, and display dates.

A broker sentence that only says EPS is not classified by itself.
The annual statement page is read first. If that page splits basic and
diluted, the split stands. If the page also says only EPS, history may
name it. A later actual replaces the forecast for that period.
Display dates are YYYY, YYYY-MM, YYYY-MM-DD, or 2Q26 with nothing around them.
"""
from __future__ import annotations

import importlib.util
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
BOOK = VIA / "supportive modules" / "registry" / "VIA_FinStatement_Query_v0101.json"
_DISPLAY = re.compile(r"^(\d{4}|\d{4}-\d{2}|\d{4}-\d{2}-\d{2}|[1-4]Q\d{2})$")


def _prior():
    path = HERE / "VDF_ENG100_FinStatementQuery_v0100.py"
    spec = importlib.util.spec_from_file_location("eng100_v0100", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def resolve_body_eps(page_labels, series=None, known=None) -> dict:
    prior = _prior()
    found = {prior.eps_kind(label) for label in page_labels or []}
    found.discard(None)
    if {"basic", "diluted"} <= found:
        return {"status": "PAGE_SPLIT", "kind": None}
    hit = prior.match_history(series, known) if series is not None and known else None
    if hit in {"basic", "diluted"}:
        return {"status": "HISTORY", "kind": hit}
    return {"status": "UNRESOLVED", "kind": None}


def replace_with_actual(estimate: dict, actual: dict | None) -> dict:
    out = dict(estimate)
    if not actual or actual.get("value") is None:
        return out
    out["forecast"] = estimate.get("value")
    out["value"] = actual["value"]
    out["value_kind"] = "ACTUAL"
    return out


def display_time(grain: str, year: int, month: int | None = None, day: int | None = None, quarter: int | None = None) -> str:
    year = int(year)
    if grain == "year":
        text = f"{year:04d}"
    elif grain == "month":
        text = f"{year:04d}-{int(month):02d}"
    elif grain == "day":
        text = f"{year:04d}-{int(month):02d}-{int(day):02d}"
    elif grain == "quarter":
        quarter = int(quarter)
        if quarter not in (1, 2, 3, 4):
            raise ValueError("quarter")
        text = f"{quarter}Q{year % 100:02d}"
    else:
        raise ValueError("grain")
    if not _DISPLAY.fullmatch(text):
        raise ValueError(text)
    return text


def accept_display(text: str) -> bool:
    return bool(_DISPLAY.fullmatch(str(text or "").strip()))


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    book = json.loads(BOOK.read_text(encoding="utf-8"))
    split = resolve_body_eps(["Basic EPS", "Diluted EPS"], [1, 2], {"basic": [1, 2]})
    bare_page = resolve_body_eps(["EPS"], [2.85, 5.10], {"basic": [2.85, 5.10], "diluted": [2.80, 5.00]})
    no_hit = resolve_body_eps(["EPS"], [1, 2], {"basic": [9, 9], "diluted": [8, 8]})
    chk("policy", "2Q26" in book["display_time"] and book["display_rule"].startswith("只允許"))
    chk("page split", split["status"] == "PAGE_SPLIT" and split["kind"] is None)
    chk("page bare uses history", bare_page == {"status": "HISTORY", "kind": "basic"})
    chk("no equal series", no_hit["status"] == "UNRESOLVED")
    replaced = replace_with_actual({"value": 6.0, "value_kind": "FORECAST"}, {"value": 5.53})
    chk("actual replaces", replaced["value"] == 5.53 and replaced["forecast"] == 6.0 and replaced["value_kind"] == "ACTUAL")
    chk("display", display_time("year", 2026) == "2026"
        and display_time("month", 2026, 9) == "2026-09"
        and display_time("day", 2026, 9, 25) == "2026-09-25"
        and display_time("quarter", 2026, quarter=2) == "2Q26")
    chk("reject decoration", not any(accept_display(x) for x in ("2026Q2", "FY2026", "2Q26E", "Q2 2026", "2026/09/25")))
    bad = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG100 v0101] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
