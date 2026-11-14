#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_OperatorRegex_TWTicker v0101.

v0100 stayed. It only kept 4–5 digits, so 00981A never parsed, and it
printed one yfinance suffix. This version always shows three codes:
the bare exchange code, the TWSE yfinance form (.TW), and the TPEX
yfinance form (.TWO). Bloomberg ({code} TT) stays as an extra.
The primary form is chosen only from a typed suffix or an explicit
market. A leading digit is not a market. 3008 is TWSE even though it
starts with 3.
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0111] 最新有版號的正本加速器(動態取最高 VeritasCeleritas_v####;退回鎖版 v1141)· 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import importlib as _cb_il
import re as _cb_re
import sys as _cb_sys
from pathlib import Path as _cb_Path
_ACCEL, _ACCEL_VER = None, ""
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        _cb_c = sorted(list(_cb_sup.glob("VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")) + list(_cb_sup.glob("*/VeritasCeleritas_v[0-9][0-9][0-9][0-9].py")),
                       key=lambda x: int(_cb_re.search(r"_v(\d{4})", x.name).group(1)))
        for _cb_d in [str(_cb_sup)] + ([str(_cb_c[-1].parent)] if _cb_c else []) + [str(x.parent) for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if _cb_d not in _cb_sys.path:
                _cb_sys.path.insert(0, _cb_d)
        if _cb_c:
            try:
                _ACCEL, _ACCEL_VER = _cb_il.import_module(_cb_c[-1].stem), _cb_c[-1].stem
            except Exception:  # noqa: BLE001
                _ACCEL = None
        break
    _cb_p = _cb_p.parent
if _ACCEL is None:
    try:
        import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  退回鎖版
        _ACCEL_VER = "VeritasCeleritas_v1141"
    except Exception:  # noqa: BLE001
        _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

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


def parse_taiwan_ticker(input_ticker, market: str | None = None):
    """Return the three codes. Primary yfinance is set only by a suffix or market."""
    clean = str(input_ticker).strip()
    tail_m = TAIL.search(clean)
    tail = tail_m.group("tail").upper().replace(" ", "") if tail_m else ""
    body = clean[: tail_m.start()].strip() if tail_m else clean
    body = re.sub(r"\s+", "", body).upper()
    empty = {
        "is_valid": False, "original_input": input_ticker, "core_ticker": None,
        "tw": None, "yf_twse": None, "yf_tpex": None, "bb": None,
        "market_type": None, "yfinance_format": None, "bloomberg_format": None,
        "type": None, "factors": [], "was_corrected": False, "market_source": None,
    }
    if not BODY.fullmatch(body):
        return empty
    kind, factors = _classify(body)
    from_suffix = "TPEX" if tail == ".TWO" else ("TWSE" if tail == ".TW" else "")
    asked = str(market or "").upper()
    from_arg = "TWSE" if asked in {"TWSE", "上市", "TSE"} else (
        "TPEX" if asked in {"TPEX", "OTC", "上櫃", "TWO"} else "")
    corrected = bool(from_arg and from_suffix and from_arg != from_suffix)
    if from_arg:
        picked, source = from_arg, "argument"
    elif from_suffix:
        picked, source = from_suffix, "suffix"
    else:
        picked, source = "", "unknown"
    yf_twse = f"{body}.TW"
    yf_tpex = f"{body}.TWO"
    primary = yf_tpex if picked == "TPEX" else (yf_twse if picked == "TWSE" else None)
    return {
        "is_valid": True,
        "original_input": input_ticker,
        "core_ticker": body,
        "tw": body,
        "yf_twse": yf_twse,
        "yf_tpex": yf_tpex,
        "bb": f"{body} TT",
        "market_type": ("上市 (TWSE)" if picked == "TWSE" else "上櫃 (TPEX)") if picked else None,
        "yfinance_format": primary,
        "bloomberg_format": f"{body} TT",
        "type": kind,
        "factors": factors,
        "was_corrected": corrected,
        "market_source": source,
    }


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    a = parse_taiwan_ticker("2330")
    chk("2330 three", a["tw"] == "2330" and a["yf_twse"] == "2330.TW" and a["yf_tpex"] == "2330.TWO" and a["yfinance_format"] is None)
    b = parse_taiwan_ticker("3008")
    chk("3008 not guessed", b["yfinance_format"] is None and b["yf_twse"] == "3008.TW" and b["yf_tpex"] == "3008.TWO")
    c = parse_taiwan_ticker("3008.TW")
    chk("3008 listed", c["yfinance_format"] == "3008.TW" and c["market_type"] == "上市 (TWSE)" and not c["was_corrected"])
    d = parse_taiwan_ticker("5347.TWO")
    chk("5347 suffix", d["yfinance_format"] == "5347.TWO" and d["market_type"] == "上櫃 (TPEX)")
    e = parse_taiwan_ticker("00981A")
    chk("active etf", e["is_valid"] and e["type"] == "etf_equity_active" and e["yf_twse"] == "00981A.TW" and e["yf_tpex"] == "00981A.TWO")
    f = parse_taiwan_ticker("00631L.TWO")
    chk("lev typed", f["type"] == "etf_leverage" and f["yfinance_format"] == "00631L.TWO" and f["bb"] == "00631L TT")
    g = parse_taiwan_ticker("0050")
    chk("passive", g["type"] == "etf_equity_passive" and g["yf_twse"] == "0050.TW" and g["yfinance_format"] is None)
    h = parse_taiwan_ticker("00981Q")
    chk("new suffix", h["is_valid"] and h["type"] == "etf_unlisted_suffix" and h["yf_tpex"] == "00981Q.TWO")
    i = parse_taiwan_ticker("abc")
    chk("reject", not i["is_valid"] and i["yf_twse"] is None)
    j = parse_taiwan_ticker("3008.TWO", market="TWSE")
    chk("conflict", j["yfinance_format"] == "3008.TW" and j["was_corrected"] and j["yf_tpex"] == "3008.TWO")
    k = parse_taiwan_ticker("2330", market="TPEX")
    chk("market arg", k["yfinance_format"] == "2330.TWO" and k["market_source"] == "argument")
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
