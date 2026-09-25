#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG101 — who is allowed into the next live test.

Taiwan monthly revenue uses the exchange master list already read by
ENG063. This file does not replace that list and it does not fetch.
International probe names start at NVDA and can be added or removed.
"""
from __future__ import annotations

DEFAULT_INTL = ("NVDA",)


def intl_universe(current: list[str] | None = None, add: list[str] | None = None, remove: list[str] | None = None) -> list[str]:
    chosen = []
    seed = list(DEFAULT_INTL if current is None else current)
    for item in seed + list(add or []):
        code = str(item or "").strip().upper()
        if code and code not in chosen and code not in {str(x).strip().upper() for x in (remove or [])}:
            chosen.append(code)
    return chosen


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    chk("default nvda", intl_universe() == ["NVDA"])
    chk("add", intl_universe(add=["aapl", "NVDA"]) == ["NVDA", "AAPL"])
    chk("remove", intl_universe(add=["AAPL"], remove=["nvda"]) == ["AAPL"])
    chk("taiwan not here", "2330" not in intl_universe())
    bad = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG101 v0100] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
