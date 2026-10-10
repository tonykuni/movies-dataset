#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read labeled financial lines. An actual covers a forecast. A failed check is discussed, not rewritten."""
# ===== [VIA:ACCEL-BRIDGE:v0100] 加速器橋(2026-10-08 accel sweep 注入;L103 最高政策 PY 導入加速器;缺席不擋,記黃) =====
import sys as _ab_sys
from pathlib import Path as _ab_Path
_ab_p = _ab_Path(__file__).resolve()
while _ab_p.parent != _ab_p:
    if (_ab_p / "supportive modules").is_dir():
        _ab_sys.path.insert(0, str(_ab_p / "supportive modules"))
        break
    _ab_p = _ab_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401
except Exception:  # noqa: BLE001
    _ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

from __future__ import annotations

import re

LABELS = (
    ("revenue", "income", ("營業收入", "銷貨收入", "營收", "net sales", "revenue")),
    ("cogs", "income", ("營業成本", "銷貨成本", "cost of goods")),
    ("gross_profit", "income", ("營業毛利", "毛利", "gross profit")),
    ("gross_margin", "income", ("毛利率", "gross margin")),
    ("operating_income", "income", ("營業利益", "operating income")),
    ("net_income", "income", ("稅後淨利", "本期淨利", "歸母淨利", "net income")),
    ("eps", "income", ("基本每股盈餘", "稀釋每股盈餘", "每股盈餘", "eps")),
)
FORECAST = re.compile(r"預估|預測|forecast|(?<=\d)[FE](?!\d)", re.I)
ACTUAL = re.compile(r"實際|歷史|(?<=\d)A(?!\d)", re.I)
NUMBER = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?")


def _labels() -> list:
    found = []
    for item, statement, names in LABELS:
        for name in names:
            found.append((len(name), name, item, statement))
    return sorted(found, reverse=True)


def _period(line: str, report_year: str) -> tuple[str, str]:
    match = re.search(r"(20\d{2})\s*Q\s*([1-4])", line, re.I)
    if match:
        return f"{match.group(1)}Q{match.group(2)}", ""
    match = re.search(r"(?<!\d)(\d{2})\s*Q\s*([1-4])", line, re.I)
    if match and 20 <= int(match.group(1)) <= 40:
        return f"20{match.group(1)}Q{match.group(2)}", ""
    match = re.search(r"(20\d{2})", line)
    if match:
        return match.group(1), ""
    return report_year, "period_from_report_year" if report_year else ""


def _vintage(line: str, period: str, report_year: str) -> str:
    if FORECAST.search(line):
        return "forecast"
    if ACTUAL.search(line):
        return "actual"
    year = period[:4]
    if report_year and year.isdigit() and year < report_year:
        return "actual"
    return "forecast"


def _unit(line: str, end: int) -> str:
    tail = line[end:end + 6]
    for name in ("億元", "百萬", "億", "%", "元"):
        if name in tail:
            return name
    return "報告原單位"


def _number(line: str, start: int, ticker: str) -> tuple[str, int]:
    match = NUMBER.search(line, start)
    if not match:
        return "", start
    raw = match.group(0).replace(",", "")
    if re.fullmatch(r"20\d{2}", raw) or raw == ticker:
        return _number(line, match.end(), ticker)
    return raw, match.end()


def _hits(text: str, ticker: str, report_year: str) -> list:
    rows = []
    order = _labels()
    for line in (text or "").splitlines():
        folded = line.lower()
        for _length, name, item, statement in order:
            at = folded.find(name.lower())
            if at < 0:
                continue
            value, end = _number(line, at + len(name), ticker)
            if not value:
                continue
            period, note = _period(line, report_year)
            vintage = _vintage(line, period, report_year)
            rows.append({
                "item": item, "statement": statement, "dataName": name, "period": period or "—",
                "value": value, "unit": _unit(line, end), "vintage": vintage, "note": note,
            })
            break
    return rows


def _cover(rows: list) -> tuple[list, list]:
    kept = {}
    discuss = []
    for row in rows:
        key = (row["item"], row["period"])
        prior = kept.get(key)
        if prior and prior["vintage"] == "actual" and row["vintage"] == "forecast":
            prior["defects"].append("forecast_covered:" + row["value"])
            continue
        if prior and prior["vintage"] == "forecast" and row["vintage"] == "actual":
            row["defects"] = ["forecast_covered:" + prior["value"]]
            kept[key] = row
            continue
        row["defects"] = []
        kept[key] = row
    return list(kept.values()), discuss


def _check(rows: list) -> list:
    discuss = []
    by_item = {}
    for row in rows:
        if row["vintage"] != "actual":
            continue
        by_item.setdefault(row["item"], row)
    revenue = by_item.get("revenue")
    cogs = by_item.get("cogs")
    gross = by_item.get("gross_profit")
    if revenue and cogs and gross:
        try:
            gap = abs((float(revenue["value"]) - float(cogs["value"])) - float(gross["value"]))
            if gap > max(abs(float(revenue["value"])) * 0.01, 0.05):
                gross["defects"].append("discuss:add_sub")
                discuss.append({"item": "gross_profit", "check": "add_sub", "detail": "revenue - cogs != gross profit"})
        except ValueError:
            pass
    margin = by_item.get("gross_margin")
    if revenue and gross and margin and margin["unit"] == "%":
        try:
            implied = float(gross["value"]) / float(revenue["value"]) * 100
            if abs(implied - float(margin["value"])) > 1:
                margin["defects"].append("discuss:division")
                discuss.append({"item": "gross_margin", "check": "division", "detail": "gross profit / revenue != labeled margin"})
        except (ValueError, ZeroDivisionError):
            pass
    return discuss


def read(text: str, file_id: str, file_name: str, ticker: str, report_year: str) -> tuple[list, list]:
    rows, _unused = _cover(_hits(text, ticker, report_year))
    discuss = _check(rows)
    out = []
    for row in rows:
        conflict = any(item.startswith("discuss:") for item in row["defects"])
        actual = row["vintage"] == "actual" and not conflict
        out.append({
            "fileId": file_id,
            "fileName": file_name,
            "category": "actual" if row["vintage"] == "actual" else "forecast",
            "statement": row["statement"],
            "item": row["item"],
            "dataName": row["dataName"],
            "period": row["period"],
            "value": row["value"],
            "unit": row["unit"],
            "confidence": "labeled",
            "source": "report_observation",
            "status": "ok" if actual else "discuss" if conflict else "observation",
            "grade": "V" if actual else "F",
            "defects": ",".join(row["defects"]),
        })
    for item in discuss:
        item["file"] = file_name
    return out, discuss


def selftest() -> int:
    text = "\n".join([
        "2024A 營業收入 100",
        "2024A 營業成本 60",
        "2024A 營業毛利 40",
        "2024A 毛利率 40%",
        "2024A 每股盈餘 4.1",
        "2024F 每股盈餘 3.5",
        "2025F 每股盈餘 5.2",
    ])
    rows, discuss = read(text, "f", "a.pdf", "2330", "2025")
    by_key = {(row["item"], row["period"]): row for row in rows}
    bad, bad_discuss = read("2024A 營業收入 100\n2024A 營業成本 60\n2024A 營業毛利 50\n2024A 毛利率 10%", "f", "b.pdf", "2330", "2025")
    ok = by_key[("eps", "2024")]["value"] == "4.1" and "forecast_covered:3.5" in by_key[("eps", "2024")]["defects"]
    ok = ok and by_key[("eps", "2025")]["category"] == "forecast" and discuss == []
    ok = ok and any(item["check"] == "add_sub" for item in bad_discuss) and any(item["check"] == "division" for item in bad_discuss)
    ok = ok and all(row["source"] == "report_observation" for row in bad)
    print("  [OK]" if ok else "  [FAIL] " + str((by_key.get(("eps", "2024")), bad_discuss)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
