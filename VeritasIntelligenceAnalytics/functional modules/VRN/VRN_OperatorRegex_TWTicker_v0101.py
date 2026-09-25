#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_OperatorRegex_TWTicker v0101.

v0100 stayed. It only kept 4–5 digits, so 00981A never parsed, and it
printed one yfinance suffix. This version always shows three codes:
the bare exchange code, the TWSE yfinance form (.TW), and the TPEX
yfinance form (.TWO). Bloomberg ({code} TT) stays as an extra, not
instead of one of the three. Market picks which yfinance form is
primary: a typed .TW/.TWO wins; otherwise a 4-digit prefix hint.
ETF letters come from VRN_TWTicker_RIE_v0400.json. An unknown single
letter after 00xxx is still accepted and marked etf_unlisted_suffix.
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
BOOK = HERE / "VRN_TWTicker_RIE_v0400.json"
OTC_PREFIXES = ("3", "4", "5", "6", "8")
TAIL = re.compile(r"(?i)(?P<tail>\.TWO|\.TW|\s*TT)\s*$")
BODY = re.compile(r"(?i)^(?P<code>00\d{2,3}[A-Z]|[1-9]\d{3}|00\d{2,3})$")


def _book() -> dict:
    return json.loads(BOOK.read_text(encoding="utf-8"))


def _types() -> list[tuple[re.Pattern[str], str]]:
    rows = _book()["modules"]["detect_type"]["logic"]
    return [(re.compile(row["pattern"]), row["type"]) for row in rows]


def _factors() -> dict[str, list[str]]:
    rules = _book()["modules"]["factor_engine"]["detect_factor_applicability"]["rules"]
    return {row["type"]: list(row["factors"]) for row in rules}


def _classify(code: str) -> tuple[str, list[str]]:
    for pat, name in _types():
        if pat.fullmatch(code):
            return name, _factors().get(name, [])
    if re.fullmatch(r"00\d{2,3}[A-Z]", code):
        return "etf_unlisted_suffix", []
    return "", []


def _hint(code: str) -> str:
    digits = re.match(r"\d+", code).group(0)
    if len(digits) == 5 or not digits.startswith(OTC_PREFIXES):
        return "TWSE"
    return "TPEX"


def parse_taiwan_ticker(input_ticker, market: str | None = None):
    """Return the three codes for one Taiwan ticker, or is_valid False."""
    clean = str(input_ticker).strip()
    tail_m = TAIL.search(clean)
    tail = tail_m.group("tail").upper().replace(" ", "") if tail_m else ""
    body = clean[: tail_m.start()].strip() if tail_m else clean
    body = re.sub(r"\s+", "", body).upper()
    if not BODY.fullmatch(body):
        return {
            "is_valid": False, "original_input": input_ticker, "core_ticker": None,
            "tw": None, "yf_twse": None, "yf_tpex": None, "bb": None,
            "market_type": None, "yfinance_format": None, "bloomberg_format": None,
            "type": None, "factors": [], "was_corrected": False,
        }
    kind, factors = _classify(body)
    typed = "TPEX" if tail == ".TWO" else ("TWSE" if tail == ".TW" else "")
    asked = str(market or "").upper()
    if asked in {"TWSE", "上市", "TSE"}:
        typed = typed or "TWSE"
    elif asked in {"TPEX", "OTC", "上櫃", "TWO"}:
        typed = typed or "TPEX"
    picked = typed or _hint(body)
    yf_twse = f"{body}.TW"
    yf_tpex = f"{body}.TWO"
    primary = yf_tpex if picked == "TPEX" else yf_twse
    corrected = False
    if tail in {".TW", ".TWO"} and not market:
        corrected = (tail == ".TW" and picked == "TPEX") or (tail == ".TWO" and picked == "TWSE")
    return {
        "is_valid": True,
        "original_input": input_ticker,
        "core_ticker": body,
        "tw": body,
        "yf_twse": yf_twse,
        "yf_tpex": yf_tpex,
        "bb": f"{body} TT",
        "market_type": "上市 (TWSE)" if picked == "TWSE" else "上櫃 (TPEX)",
        "yfinance_format": primary,
        "bloomberg_format": f"{body} TT",
        "type": kind,
        "factors": factors,
        "was_corrected": corrected,
    }


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    a = parse_taiwan_ticker("2330")
    chk("2330 three", a["tw"] == "2330" and a["yf_twse"] == "2330.TW" and a["yf_tpex"] == "2330.TWO" and a["yfinance_format"] == "2330.TW")
    b = parse_taiwan_ticker("5347")
    chk("5347 tpex", b["yfinance_format"] == "5347.TWO" and b["yf_twse"] == "5347.TW")
    c = parse_taiwan_ticker("00981A")
    chk("active etf", c["is_valid"] and c["type"] == "etf_equity_active" and c["tw"] == "00981A" and c["yf_twse"] == "00981A.TW" and c["yf_tpex"] == "00981A.TWO")
    d = parse_taiwan_ticker("00631L.TWO")
    chk("lev typed", d["type"] == "etf_leverage" and d["yfinance_format"] == "00631L.TWO" and d["bb"] == "00631L TT")
    e = parse_taiwan_ticker("0050")
    chk("passive", e["type"] == "etf_equity_passive" and e["yf_twse"] == "0050.TW")
    f = parse_taiwan_ticker("00981Q")
    chk("new suffix", f["is_valid"] and f["type"] == "etf_unlisted_suffix" and f["yf_tpex"] == "00981Q.TWO")
    g = parse_taiwan_ticker("abc")
    chk("reject", not g["is_valid"] and g["yf_twse"] is None)
    h = parse_taiwan_ticker("2330", market="TPEX")
    chk("market arg", h["yfinance_format"] == "2330.TWO" and h["yf_twse"] == "2330.TW")
    bad = [n for n, ok in checks if not ok]
    print(f"[VRN_OperatorRegex_TWTicker v0101] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    import sys
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    sample = sys.argv[1] if len(sys.argv) > 1 else "00981A"
    row = parse_taiwan_ticker(sample, sys.argv[2] if len(sys.argv) > 2 else None)
    if not row["is_valid"]:
        print(f"{sample} 不是台股代號")
        raise SystemExit(1)
    print(f"TW     {row['tw']}")
    print(f"TWSE   {row['yf_twse']}")
    print(f"TPEX   {row['yf_tpex']}")
    print(f"BB     {row['bb']}")
    print(f"primary {row['yfinance_format']} · {row['type']}")
