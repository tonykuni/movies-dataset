#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL149 UnitScale v0100. From VCGC. No fetch. No policy-book write.

Compare in integers. Display is rounded after that, half away from zero.
Amount: NTD integer, show million with 1 decimal.
Per share: cents, show NTD with 2 decimals. Never fold into millions.
Ratio: 0.01 percentage point, show percent with 2 decimals.
Times: 0.01x, show times with 2 decimals.
Shares: one share, show thousands as an integer. Capital stock stays an amount.
"""
from __future__ import annotations

import json
import re
from io import StringIO

ACCOUNTS = {
    "revenue": ("營業收入", "amount", "百萬元"),
    "cogs": ("營業成本", "amount", "百萬元"),
    "gross_profit": ("毛利", "amount", "百萬元"),
    "operating_income": ("營業利益", "amount", "百萬元"),
    "net_income": ("本期淨利", "amount", "百萬元"),
    "total_assets": ("資產總額", "amount", "百萬元"),
    "total_equity": ("權益總額", "amount", "百萬元"),
    "parent_equity": ("母公司業主權益", "amount", "百萬元"),
    "common_stock": ("股本", "amount", "百萬元"),
    "basic_eps": ("基本每股盈餘", "per_share", "元"),
    "diluted_eps": ("稀釋每股盈餘", "per_share", "元"),
    "eps": ("EPS（未拆）", "per_share", "元"),
    "bvps": ("每股淨值", "per_share", "元"),
    "dps": ("每股股利", "per_share", "元"),
    "target_price": ("目標價", "per_share", "元"),
    "close": ("收盤", "per_share", "元"),
    "gross_margin": ("毛利率", "ratio", "%"),
    "operating_margin": ("營益率", "ratio", "%"),
    "roe": ("ROE", "ratio", "%"),
    "roa": ("ROA", "ratio", "%"),
    "current_ratio": ("流動比率", "ratio", "%"),
    "debt_ratio": ("負債比率", "ratio", "%"),
    "upside": ("上漲空間", "ratio", "%"),
    "pe": ("本益比", "times", "x"),
    "inventory_turnover": ("存貨週轉率", "times", "x"),
    "shares": ("股數", "shares", "股"),
}

UNIT_KIND = {
    "元": "ntd", "ntd": "ntd", "twd": "ntd", "新台幣": "ntd",
    "千元": "thousand", "thousand": "thousand", "k": "thousand",
    "百萬": "million", "百萬元": "million", "million": "million", "mn": "million",
    "億": "yi", "億元": "yi", "hundred_million": "yi",
    "billion": "billion", "b": "billion",
    "分": "cent", "cent": "cent",
    "%": "pct", "percent": "pct", "pct": "pct", "百分點": "pct",
    "小數": "decimal", "ratio": "decimal", "decimal": "decimal",
    "x": "times", "倍": "times", "times": "times",
    "股": "share", "share": "share", "shares": "share",
    "千股": "kshare", "thousand_share": "kshare",
    "百萬股": "mshare",
}
FAMILY_UNITS = {
    "amount": {"ntd", "thousand", "million", "yi", "billion"},
    "per_share": {"ntd", "cent"},
    "ratio": {"pct", "decimal"},
    "times": {"times"},
    "shares": {"share", "kshare", "mshare"},
}
MULT = {
    "ntd": 1, "thousand": 1_000, "million": 1_000_000, "yi": 100_000_000, "billion": 1_000_000_000,
    "cent": 1, "pct": 100, "decimal": 10_000, "times": 100,
    "share": 1, "kshare": 1_000, "mshare": 1_000_000,
}


def _norm_unit(unit: str) -> str:
    return re.sub(r"\s+", "", str(unit or "").strip().lower())


def _parse(raw: str):
    text = str(raw or "").strip().replace(",", "").replace("，", "").replace(" ", "")
    if text in {"", "--", "—", "–", "N/A", "n/a"}:
        return None
    neg = False
    if text.startswith("(") and text.endswith(")"):
        neg = True
        text = text[1:-1]
    if text.startswith("+"):
        text = text[1:]
    if text.startswith("-") or text.startswith("−"):
        neg = not neg
        text = text[1:]
    marker = ""
    if text.endswith("%"):
        marker, text = "%", text[:-1]
    elif text.endswith(("x", "X")):
        marker, text = "x", text[:-1]
    elif text.endswith("倍"):
        marker, text = "x", text[:-1]
    if not re.fullmatch(r"\d+(\.\d+)?", text):
        return None
    whole, _, frac = text.partition(".")
    digits = (whole + frac).lstrip("0") or "0"
    return neg, int(digits), 10 ** len(frac), marker


def _round_half_away(num: int, den: int, neg: bool) -> int:
    whole, rem = divmod(num, den)
    mag = whole + 1 if rem * 2 >= den else whole
    if mag == 0:
        return 0
    return -mag if neg else mag


def _quantum(family: str, kind: str) -> int:
    if family == "per_share" and kind == "ntd":
        return 100
    return MULT[kind]


def _grouped(value: int, decimals: int) -> str:
    neg = value < 0
    mag = -value if neg else value
    scale = 10 ** decimals
    whole, frac = divmod(mag, scale)
    body = f"{whole:,}" if decimals == 0 else f"{whole:,}.{frac:0{decimals}d}"
    return f"-{body}" if neg else body


def convert_unit(value: str, account_id: str, unit: str = "") -> dict:
    account = ACCOUNTS.get(account_id)
    if not account:
        return {"ok": False, "error": "科目不在刻度冊。"}
    parsed = _parse(value)
    if not parsed:
        return {"ok": False, "error": "數字認不出。空值、N/A、破折號不換。"}
    neg, num, den, marker = parsed
    zh, family, default_unit = account
    unit_text = str(unit or "").strip()
    if not unit_text and marker == "%":
        unit_text = "%"
    if not unit_text and marker == "x":
        unit_text = "x"
    if not unit_text:
        unit_text = default_unit
    kind = UNIT_KIND.get(_norm_unit(unit_text))
    if not kind:
        return {"ok": False, "error": f"單位「{unit_text}」不認識。不默認當成百萬元。"}
    if kind not in FAMILY_UNITS[family]:
        if family == "per_share":
            return {"ok": False, "error": "每股不收成百萬元，也不換成比率。"}
        if family == "shares":
            return {"ok": False, "error": "股數不是金額。股本金額用「股本」。"}
        return {"ok": False, "error": f"{zh} 不接受單位「{unit_text}」。"}
    compare = _round_half_away(num * _quantum(family, kind), den, neg)
    if family == "amount":
        display = _grouped(_round_half_away(abs(compare), 100_000, compare < 0), 1)
        compare_unit, display_unit = "元", "百萬元"
    elif family == "shares":
        display = _grouped(_round_half_away(abs(compare), 1_000, compare < 0), 0)
        compare_unit, display_unit = "股", "千股"
    elif family == "per_share":
        display = _grouped(compare, 2)
        compare_unit, display_unit = "分", "元"
    elif family == "ratio":
        display = _grouped(compare, 2)
        compare_unit, display_unit = "0.01 個百分點", "%"
    else:
        display = _grouped(compare, 2)
        compare_unit, display_unit = "0.01 倍", "x"
    warn = ""
    if account_id == "eps":
        warn = "只寫 EPS。基本與稀釋要各算各的，這格不代填兩欄。"
    return {
        "ok": True,
        "account": account_id,
        "zh": zh,
        "family": family,
        "compare": str(compare),
        "compare_unit": compare_unit,
        "display": display,
        "display_unit": display_unit,
        "warn": warn,
    }


def _show(account_id: str, value: str, unit: str = "") -> str:
    row = convert_unit(value, account_id, unit)
    if not row["ok"]:
        return ""
    return row["display"]


def measured_matrix() -> dict:
    """Last measured stock-report row. Not a new parse. Sample folder is not here."""
    target = _show("target_price", "1275")
    close = _show("close", "2475")
    upside = _show("upside", "-48.484848484848484")
    basic = [
        {
            "file": "JP-2330 20250718.pdf",
            "code": "2330",
            "name": "台積電",
            "mkt": "TWSE",
            "broker": "JPM",
            "date": "2025-07-18",
            "analyst": "Gokul Hariharan",
            "yf": "2330.TW",
            "bb": "2330 TT",
            "rating": "BUY",
            "target": target,
            "close": close,
            "up": upside,
            "lamp": "RED",
        }
    ]
    errors = [
        {"lamp": "GREEN", "check": "three", "detail": "2330 · 2330.TW · 2330 TT"},
        {"lamp": "GREEN", "check": "name", "detail": "台積電"},
        {"lamp": "GREEN", "check": "close", "detail": f"locked {close} overlap"},
        {"lamp": "GREEN", "check": "rating", "detail": "BUY"},
        {"lamp": "RED", "check": "upside", "detail": f"target {target} vs close {close} = {upside}%"},
        {"lamp": "YELLOW", "check": "eps", "detail": "page did not split basic / diluted"},
        {"lamp": "YELLOW", "check": "annual", "detail": "NODATA"},
        {"lamp": "GREEN", "check": "body", "detail": "AGREE seq 0.947"},
        {"lamp": "YELLOW", "check": "right", "detail": "DIVERGE seq 0.475"},
        {"lamp": "YELLOW", "check": "paddle", "detail": "ABSENT not called"},
    ]
    return {
        "source": "last measured paste 2026-09-26 04:18:27",
        "refetched": False,
        "basic": basic,
        "errors": errors,
    }


def _fit(rows: list[dict], columns: list[str]) -> str:
    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(pad_edge=False, padding=(0, 1), show_lines=False, expand=False)
        for name in columns:
            table.add_column(name, no_wrap=True, overflow="ignore")
        for row in rows:
            table.add_row(*[str(row.get(name, "")) for name in columns])
        buf = StringIO()
        Console(file=buf, width=240, force_terminal=False, color_system=None).print(table)
        return buf.getvalue().rstrip()
    except Exception:
        widths = {name: len(name) for name in columns}
        for row in rows:
            for name in columns:
                widths[name] = max(widths[name], len(str(row.get(name, ""))))
        head = " ".join(name.ljust(widths[name]) for name in columns)
        lines = [head]
        for row in rows:
            lines.append(" ".join(str(row.get(name, "")).ljust(widths[name]) for name in columns))
        return "\n".join(lines)


def selftest() -> list[str]:
    fails = []

    def chk(name: str, ok: bool) -> None:
        if not ok:
            fails.append(name)

    revenue = convert_unit("1234.55", "revenue", "百萬元")
    chk("revenue", revenue.get("compare") == "1234550000" and revenue.get("display") == "1,234.6")
    loss = convert_unit("-1.25", "gross_profit", "百萬元")
    chk("neg", loss.get("compare") == "-1250000" and loss.get("display") == "-1.3")
    paren = convert_unit("(1,000)", "net_income", "千元")
    chk("paren", paren.get("compare") == "-1000000" and paren.get("display") == "-1.0")
    half = convert_unit("50000", "revenue", "元")
    chk("half", half.get("compare") == "50000" and half.get("display") == "0.1")
    eps = convert_unit("32.486", "basic_eps", "元")
    chk("eps", eps.get("compare") == "3249" and eps.get("display") == "32.49")
    chk("eps_refuse", not convert_unit("32.48", "diluted_eps", "百萬元")["ok"])
    bare = convert_unit("8.7", "eps")
    chk("bare", bare.get("compare") == "870" and "不代填" in bare.get("warn", ""))
    margin = convert_unit("53.216%", "gross_margin")
    chk("margin", margin.get("compare") == "5322" and margin.get("display") == "53.22")
    frac = convert_unit("0.5321", "operating_margin", "小數")
    chk("frac", frac.get("compare") == "5321" and frac.get("display") == "53.21")
    pe = convert_unit("18.255", "pe", "x")
    chk("pe", pe.get("compare") == "1826" and pe.get("display") == "18.26")
    shares = convert_unit("259320450", "shares", "股")
    chk("shares", shares.get("compare") == "259320450" and shares.get("display") == "259,320")
    chk("share_half", convert_unit("1500", "shares", "股").get("display") == "2")
    chk("capital", convert_unit("259321", "common_stock", "百萬元").get("display_unit") == "百萬元")
    chk("mix", not convert_unit("259320", "shares", "百萬元")["ok"])
    chk("unknown", not convert_unit("10", "revenue", "箱")["ok"])
    book = measured_matrix()
    chk("matrix", book["basic"][0]["lamp"] == "RED" and book["basic"][0]["target"] == "1,275.00")
    return fails


def main() -> int:
    fails = selftest()
    book = measured_matrix()
    basic_cols = ["lamp", "file", "code", "name", "mkt", "broker", "date", "analyst", "yf", "bb", "rating", "target", "close", "up"]
    error_cols = ["lamp", "check", "detail"]
    print("BASIC")
    print(_fit(book["basic"], basic_cols))
    print("ERROR")
    print(_fit(book["errors"], error_cols))
    payload = {
        "via": "vcgc",
        "door": "CGC_MDL149_UnitScale_v0100",
        "selftest": "FAIL" if fails else "OK",
        "fails": fails,
        "matrix": book,
        "do_not": ["refetch the locked close", "fill basic and diluted with the same EPS", "parse non-stock reports"],
        "next": "none",
    }
    print("BEGIN_PASTE")
    print(json.dumps(payload, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
