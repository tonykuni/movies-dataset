#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AAII: spreadsheet first, survey page second. A block page still yields no percentages."""
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
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import importlib.util
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAGE = "https://www.aaii.com/sentimentsurvey"


def _prior():
    spec = importlib.util.spec_from_file_location("sent_v0100", HERE / "VDF_ENG115_SentimentFetch_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def parse_page(text: str):
    if "Pardon Our Interruption" in text or "<html" in text[:200].lower() and "Bullish" not in text:
        return None
    if "Pardon Our Interruption" in text:
        return None

    def grab(label):
        match = re.search(label + r"\s*([\d.]+)\s*%", text, re.I)
        return float(match.group(1)) if match else None

    bull, neutral, bear = grab("Bullish"), grab("Neutral"), grab("Bearish")
    if None in (bull, neutral, bear) or not 99 <= bull + neutral + bear <= 101:
        return None
    dated = re.search(r"Week ending\s+([A-Za-z]+\s+\d{1,2},\s+\d{4})", text)
    return {
        "state": "LIVE",
        "source": "aaii.com/sentimentsurvey",
        "date": dated.group(1) if dated else "",
        "bullish": bull,
        "neutral": neutral,
        "bearish": bear,
        "spread": round(bull - bear, 1),
    }


def aaii(prior) -> dict:
    file_row = prior.aaii()
    if file_row.get("state") != "BLOCKED":
        return file_row
    try:
        status, ctype, raw = prior._get(PAGE, {"User-Agent": prior.UA, "Accept": "text/html", "Referer": "https://www.aaii.com/"})
    except Exception as exc:
        file_row["page"] = type(exc).__name__
        return file_row
    parsed = parse_page(raw.decode("utf-8", "replace"))
    if parsed is None:
        file_row["page"] = "BLOCKED" if b"Pardon Our Interruption" in raw else "unparsed"
        file_row["http"] = status
        return file_row
    parsed["http"] = status
    return parsed


def probe() -> dict:
    prior = _prior()
    card = {
        "via": "vcgc",
        "door": "VDF_ENG115_SentimentFetch_v0101",
        "enter": "vcgc",
        "exit": "vcgc",
        "central": True,
        "cnn": prior.cnn(),
        "aaii": aaii(prior),
        "intake_edited": False,
        "do_not": prior.probe.__doc__ and [] or [
            "fill AAII from the block page",
            "accept three percentages that do not sum to about 100",
            "edit intake macro_ssot",
        ],
    }
    card["do_not"] = [
        "fill AAII from the block page",
        "accept three percentages that do not sum to about 100",
        "edit intake macro_ssot",
    ]
    card["next"] = "none" if card["aaii"].get("state") == "LIVE" else "AAII stays blocked until the survey page is not an interruption page"
    from datetime import datetime
    card["probed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return card


def main() -> int:
    if not _prior().allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-sentiment through Invoke-VIAPython"}, ensure_ascii=False))
        return 2
    print(json.dumps(probe(), ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    good = parse_page("Week ending September 23, 2026\nBullish\n32.7%\nAvg 37.5%\nNeutral\n19.2%\nBearish\n48.1%")
    blocked = parse_page("<html><title>Pardon Our Interruption</title>Bullish 1%")
    bad_sum = parse_page("Bullish 32.7% Neutral 37.5% Bearish 19.2%")
    ok = good and good["bullish"] == 32.7 and good["spread"] == -15.4 and blocked is None and bad_sum is None
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
