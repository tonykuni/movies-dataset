#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read one statement table and check it. Basic EPS and diluted EPS stay apart.

An unlabeled EPS is not assigned to either. No outside history, no invented base.
"""
from __future__ import annotations

import re

_KEYS = (
    ("diluted_eps", ("稀釋每股盈餘", "稀釋eps", "diluted eps", "diluted earnings per share")),
    ("basic_eps", ("基本每股盈餘", "基本eps", "basic eps", "basic earnings per share")),
    ("gross", ("營業毛利", "毛利", "gross profit")),
    ("cost", ("營業成本", "cost of revenue", "cost of sales")),
    ("revenue", ("營業收入", "收益合計", "net revenue", "total revenue", "revenue")),
    ("net", ("本期淨利", "稅後淨利", "net income", "net profit")),
    ("margin", ("毛利率", "gross margin")),
    ("eps", ("每股盈餘", "eps")),
)
_PAGE = ("基本每股盈餘", "稀釋每股盈餘", "合併綜合損益", "basic eps", "diluted eps", "gross profit", "income statement")
_NUM = re.compile(r"\(?-?\d[\d,]*(?:\.\d+)?\)?%?")


def _kind(label: str) -> str | None:
    low = label.lower().replace(" ", "")
    raw = label.lower()
    for kind, names in _KEYS:
        for name in names:
            if name.replace(" ", "") in low or name in raw:
                if kind == "eps" and ("basic" in raw or "diluted" in raw or "基本" in label or "稀釋" in label):
                    continue
                if kind == "revenue" and "cost" in raw:
                    continue
                return kind
    return None


def _num(cell: str) -> float | None:
    text = str(cell or "").strip().replace(",", "").replace("，", "")
    if not text or text in {"-", "—", "–", "n.a.", "na"}:
        return None
    match = _NUM.search(text)
    if match is None:
        return None
    token = match.group(0).replace("%", "")
    negative = token.startswith("(") and token.endswith(")")
    token = token.strip("()")
    try:
        value = float(token)
    except ValueError:
        return None
    return -value if negative else value


def _last_number(line: str) -> float | None:
    found = [_num(token) for token in _NUM.findall(line)]
    found = [item for item in found if item is not None]
    return found[-1] if found else None


def from_text(text: str) -> dict:
    got: dict[str, float] = {}
    for line in (text or "").splitlines():
        kind = _kind(line)
        if kind is None or kind in got:
            continue
        value = _last_number(line)
        if value is not None:
            got[kind] = value
    revenue, cost, gross = got.get("revenue"), got.get("cost"), got.get("gross")
    if None not in (revenue, cost, gross):
        add = "OK" if abs((revenue - cost) - gross) <= 0.02 * max(abs(revenue), 1.0) else "FAIL"
    else:
        add = "SKIP"
    margin = got.get("margin")
    if None not in (revenue, gross) and revenue and margin is not None:
        ratio = gross / revenue
        reported = margin / 100.0 if abs(margin) > 1.5 else margin
        div = "OK" if abs(ratio - reported) <= 0.02 else "FAIL"
    else:
        div = "SKIP"
    unlabeled = got.get("eps")
    return {
        "basic_eps": got.get("basic_eps"),
        "diluted_eps": got.get("diluted_eps"),
        "unlabeled_eps": unlabeled if "basic_eps" not in got and "diluted_eps" not in got else None,
        "add": add,
        "div": div,
        "hist": "NO_BASE",
    }


def inspect(path) -> dict:
    try:
        import fitz
    except Exception:
        return {"state": "ABSENT", "hist": "NO_BASE"}
    try:
        with fitz.open(str(path)) as doc:
            for index, page in enumerate(doc):
                if index == 0 or index > 12:
                    continue
                text = page.get_text("text") or ""
                low = text.lower()
                if not any(key in low or key in text for key in _PAGE):
                    continue
                card = from_text(text)
                card.update({"state": "SEEN", "page": index + 1})
                return card
    except Exception as exc:
        return {"state": f"FAIL {type(exc).__name__}", "hist": "NO_BASE"}
    return {"state": "NODATA", "add": "SKIP", "div": "SKIP", "hist": "NO_BASE",
            "basic_eps": None, "diluted_eps": None, "unlabeled_eps": None}


def selftest() -> int:
    good = from_text("\n".join([
        "Revenue 80 100",
        "Cost of revenue 30 40",
        "Gross profit 50 60",
        "Gross margin 62.5% 60%",
        "Basic EPS 8 10",
        "Diluted EPS 7 9",
    ]))
    bare = from_text("EPS 5.2")
    bad = from_text("Revenue 100\nCost of sales 40\nGross profit 50")
    ok = (
        good["add"] == "OK" and good["div"] == "OK"
        and good["basic_eps"] == 10 and good["diluted_eps"] == 9
        and good["unlabeled_eps"] is None
        and bare["unlabeled_eps"] == 5.2 and bare["basic_eps"] is None
        and bad["add"] == "FAIL"
    )
    print("  [OK]" if ok else f"  [FAIL] {good} {bare} {bad}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
