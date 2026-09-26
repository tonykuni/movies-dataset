#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Stock identity. A year is not a ticker, and a legend is not the rating."""
from __future__ import annotations

import re

BROKERS = {
    "MEGA": ("兆豐", "兆豐證券", "兆豐投顧", "兆豐國際", "MEGA"),
    "DAIWA": ("DAIWA", "Daiwa", "Daiwa Securities", "大和", "大和證券"),
    "CLSA": ("CLSA", "CLST", "中信里昂"),
    "MCQN": ("MCQN", "MACQUARIE", "Macquarie", "麥格理"),
    "JPM": ("JPM", "JP", "J.P. Morgan", "摩根大通"),
    "CITI": ("CITI", "Citi", "花旗"),
    "KGI": ("KGI", "凱基", "凱基投顧"),
    "CTBC": ("CTBC", "中信", "中國信託"),
    "MS": ("MS", "Morgan Stanley", "大摩", "摩根士丹利"),
}
RATINGS = ("逢低買進", "逢高賣出", "區間操作", "強力買進", "買進", "中立", "賣出", "BUY", "HOLD", "SELL")
LEGEND = "評等分級"


def restore(text: str) -> str:
    raw = str(text or "").replace("\r", "\n")
    raw = re.sub(r"[ \t]{2,}", "\n", raw)
    lines = [re.sub(r"\s+", " ", line).strip() for line in raw.splitlines()]
    lines = [line for line in lines if line]
    out = []
    index = 0
    while index < len(lines):
        step = 1
        pair = _pair(lines[index])
        if pair is None and index + 1 < len(lines) and re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?%?", lines[index + 1]):
            if not re.fullmatch(r"(?:19|20)\d{2}", lines[index]):
                pair = (lines[index], lines[index + 1])
                step = 2
        if pair is None:
            out.append(lines[index])
            index += 1
            continue
        block = []
        while index < len(lines):
            pair = _pair(lines[index])
            step = 1
            if pair is None and index + 1 < len(lines) and re.fullmatch(r"-?\d[\d,]*(?:\.\d+)?%?", lines[index + 1]):
                if not re.fullmatch(r"(?:19|20)\d{2}", lines[index]):
                    pair = (lines[index], lines[index + 1])
                    step = 2
            if pair is None:
                break
            block.append(pair)
            index += step
        if len(block) >= 2:
            caption = _near(lines, index - len(block), r"表\s*\d|基本資料|結論|Table")
            source = _near_after(lines, index, r"資料來源|來源[:：]|Source")
            if caption:
                out.append(caption)
            out.append("| 項目 | 值 |")
            out.append("| --- | --- |")
            out.extend(f"| {left} | {right} |" for left, right in block)
            if source:
                out.append(source)
        else:
            left, right = block[0]
            out.append(f"{left} {right}")
    return "\n".join(out)


def _pair(line: str):
    match = re.fullmatch(r"(.+?)\s+(-?\d[\d,]*(?:\.\d+)?%?)", line.strip())
    if not match:
        return None
    left, right = match.group(1).strip(), match.group(2).strip()
    if re.fullmatch(r"(?:19|20)\d{2}", left):
        return None
    return left, right


def _near(lines, start, pattern):
    for index in range(start - 1, max(-1, start - 4), -1):
        if 0 <= index < len(lines) and re.search(pattern, lines[index], re.I):
            return lines[index]
    return ""


def _near_after(lines, start, pattern):
    for index in range(start, min(len(lines), start + 3)):
        if re.search(pattern, lines[index], re.I):
            return lines[index]
    return ""


def _ticker(name: str) -> str:
    for token in re.findall(r"(?<!\d)([1-9]\d{3})(?!\d)", name or ""):
        if not _year(token):
            return token
    return ""


def _year(token: str) -> bool:
    return bool(re.fullmatch(r"(?:19|20)\d{2}", token or ""))


def _codes(text: str, ticker: str) -> list:
    found = []
    if re.search(rf"(?<!\d){ticker}(?!\d)", text):
        found.append("local")
    if re.search(rf"(?<!\d){ticker}\.(?:TW|TWO)\b", text, re.I):
        found.append("yahoo")
    if re.search(rf"(?<!\d){ticker}\s*TT\b", text, re.I):
        found.append("bloomberg")
    return found


def _broker(text: str) -> str:
    folded = text.upper()
    best = ""
    best_len = 0
    for key, names in BROKERS.items():
        for name in names:
            if re.search(r"[\u4e00-\u9fff]", name):
                hit = name in text
            else:
                hit = re.search(rf"(?<![A-Z0-9]){re.escape(name.upper())}(?![A-Z0-9])", folded) is not None
            if hit and len(name) > best_len:
                best, best_len = key, len(name)
    return best


def _date(head: str, filename: str) -> str:
    match = re.search(r"報告日期[:：\s]*((?:19|20)\d{2})[./-](\d{1,2})[./-](\d{1,2})", head)
    if match:
        year, month, day = match.groups()
        return f"{year}-{int(month):02d}-{int(day):02d}"
    match = re.search(r"(?<!\d)((?:19|20)\d{2})(\d{2})(\d{2})(?!\d)", filename or "")
    if match and 1 <= int(match.group(2)) <= 12 and 1 <= int(match.group(3)) <= 31:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return ""


def _rating(head: str, ticker: str) -> str:
    pos = head.find(ticker)
    zone = head[pos:pos + 40] if pos >= 0 else head[:80]
    zone = zone.split("前次")[0]
    for label in sorted(RATINGS, key=len, reverse=True):
        if label in zone:
            return label
    return ""


def _header_target(head: str, ticker: str) -> str:
    pos = head.find(f"({ticker})") if ticker else -1
    zone = head[pos:pos + 80] if pos >= 0 else head[:80]
    zone = zone.split("前次")[0]
    match = re.search(r"\$\s*([0-9][0-9,]*(?:\.[0-9]+)?)", zone)
    if match:
        return match.group(1).replace(",", "")
    match = re.search(r"目標價[^0-9$]{0,8}([0-9][0-9,]*(?:\.[0-9]+)?)", zone)
    return match.group(1).replace(",", "") if match else ""


def _number(pattern: str, text: str) -> str:
    match = re.search(pattern, text, re.I)
    return match.group(1).replace(",", "") if match else ""


def english_from_info(info: dict) -> str:
    def latin(value: str) -> bool:
        return bool(value) and not re.search(r"[\u4e00-\u9fff]", value)

    short = str((info or {}).get("shortName") or "").strip()
    long = str((info or {}).get("longName") or "").strip()
    if latin(short) and (not latin(long) or len(short) <= len(long)):
        return short
    return long if latin(long) else ""


def identify(filename: str, text: str) -> dict:
    restored = restore(text)
    ticker = _ticker(filename)
    codes = _codes(restored, ticker) if ticker else []
    head = restored.split(LEGEND)[0]
    name = ""
    if ticker:
        match = re.search(rf"([\u4e00-\u9fffA-Za-z][\u4e00-\u9fffA-Za-z0-9\-]{{1,20}})\({ticker}\)", head)
        name = match.group(1) if match else ""
    analyst = ""
    match = re.search(r"研究員[:：\s]*([\u4e00-\u9fff]{2,4})", head)
    if match:
        analyst = match.group(1)
    mail = re.search(r"([A-Za-z][A-Za-z.\-]*)@([A-Za-z0-9.\-]+)", restored)
    close = _number(r"收盤價[:：\s]*([0-9][0-9,]*(?:\.[0-9]+)?)", head)
    upside = _number(r"上漲空間\s*([0-9]+(?:\.[0-9]+)?)\s*%", head)
    market = ""
    yahoo = ""
    if "yahoo" in codes:
        market = "TWO" if re.search(rf"{ticker}\.TWO\b", restored, re.I) else "TWSE"
        yahoo = f"{ticker}.TWO" if market == "TWO" else f"{ticker}.TW"
    return {
        "report_type": "STOCK" if codes else "",
        "ticker": ticker if codes else "",
        "name": name,
        "english_name": "",
        "broker": _broker(filename + "\n" + head),
        "analyst": analyst,
        "analyst_email": mail.group(0) if mail else "",
        "report_date": _date(head, filename),
        "rating": _rating(head, ticker) if codes else "",
        "target": _header_target(head, ticker) if codes else "",
        "close": close,
        "upside": upside,
        "market": market,
        "yfinance": yahoo,
        "bloomberg": f"{ticker} TT" if codes else "",
        "codes": codes,
        "restored": restored,
    }


def selftest() -> int:
    filename = "20250819兆豐個股報告-泓德能源(6873).pdf"
    page = (
        "個股報告 投資評等 目標價 泓德能源(6873) 逢低買進 $208 "
        "前次投資建議：2024.12.09 「買進」,目標價:$345 "
        "報告日期：2025.08.19 研究員：邱岳霖 "
        "2025/8/18 收盤價： 169.50 "
        "普通股股本(百萬股)  123  市值(NT$ 百萬)  20766  "
        "融資餘額 3005 融券餘額 57 "
        "潛在上漲空間22.7%，投資評等調降至「逢低買進」。 "
        "評等分級：買進；賣出。"
    )
    got = identify(filename, page)
    name = english_from_info({"shortName": "台積電", "longName": "Taiwan Semiconductor Manufacturing"})
    short = english_from_info({"shortName": "TSMC", "longName": "Taiwan Semiconductor Manufacturing"})
    ok = (
        got["report_type"] == "STOCK"
        and got["ticker"] == "6873"
        and got["name"] == "泓德能源"
        and got["broker"] == "MEGA"
        and got["report_date"] == "2025-08-19"
        and got["rating"] == "逢低買進"
        and got["analyst"] == "邱岳霖"
        and got["target"] == "208"
        and got["close"] == "169.50"
        and got["upside"] == "22.7"
        and "| 項目 | 值 |" in got["restored"]
        and name == "Taiwan Semiconductor Manufacturing"
        and short == "TSMC"
        and _broker("CLST-6669.pdf") == "CLSA"
        and _broker("MCQN note") == "MCQN"
        and _broker("Daiwa-1319.pdf") == "DAIWA"
    )
    print("  [OK]" if ok else "  [FAIL] " + str({k: got[k] for k in got if k != "restored"}))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
