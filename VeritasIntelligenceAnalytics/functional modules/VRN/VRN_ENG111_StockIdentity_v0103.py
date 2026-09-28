#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Display rules. 國票 stays. Daiwa stays Daiwa. JP and JMP both show JPM.

Latin mega of any case shows MEGA. The Chinese name still shows 兆豐.
A rating is the words on the report, not a mapped scale.
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

import re
from pathlib import Path

HERE = Path(__file__).resolve().parent

import importlib.util


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


BASE = _load("ident_v0102_for_v0103", HERE / "VRN_ENG111_StockIdentity_v0102.py")

def _show(row: dict, alias: str) -> str:
    if row.get("canonical") == "JP":
        return "JPM"
    if row.get("canonical") == "Daiwa":
        return "Daiwa"
    if row.get("canonical") == "兆豐" and not re.search(r"[\u4e00-\u9fff]", alias):
        return "MEGA"
    return str(row.get("show") or "")


WRITTEN = ("強力買進", "強力賣出", "逢低買進", "逢高賣出", "區間操作", "增加持股", "未評等", "避免", "買進", "賣出", "中立", "維持", "BUY", "HOLD", "SELL", "NOT RATED", "NOT_RATED", "OW", "UW", "NR")


def broker_of(text: str) -> str:
    folded = BASE.strip_contacts(text).upper()
    best = None
    best_alias = ""
    for row in BASE.BASE.broker_rows():
        for alias in row.get("aliases") or []:
            alias = str(alias).strip()
            if len(alias) < 2:
                continue
            if re.search(r"[\u4e00-\u9fff]", alias):
                hit = alias in BASE.strip_contacts(text)
            else:
                hit = re.search(rf"(?<![A-Z]){re.escape(alias.upper())}(?![A-Z])", folded) is not None
            if hit and len(alias) > len(best_alias):
                best, best_alias = row, alias
    return _show(best, best_alias) if best else ""


def rating_as_written(head: str, ticker: str) -> str:
    pos = (head or "").find(ticker) if ticker else -1
    zone = head[pos:pos + 40] if pos >= 0 else (head or "")[:80]
    zone = zone.split("前次")[0]
    for label in sorted(WRITTEN, key=len, reverse=True):
        if label in zone:
            return label
    return ""


def identify(filename: str, text: str, markets: dict | None = None) -> dict:
    got = BASE.identify(filename, text, markets)
    head = BASE.strip_contacts((got.get("restored") or "").split("評等分級")[0])
    got["broker"] = broker_of(filename) or broker_of(head)
    got["rating"] = rating_as_written(head, str(got.get("ticker") or "")) or got.get("rating") or ""
    return got


def selftest() -> int:
    ok = broker_of("mega") == "MEGA" and broker_of("MEGABANK") == "MEGA" and broker_of("兆豐證券") == "兆豐"
    ok = ok and broker_of("JP") == "JPM" and broker_of("JMP") == "JPM" and broker_of("JPM") == "JPM"
    ok = ok and broker_of("大和證券") == "Daiwa" and broker_of("Daiwa Capital Markets") == "Daiwa"
    ok = ok and broker_of("國票") == "國票" and broker_of("IBF") == "國票" and broker_of("WATERLAND") == "國票"
    written = rating_as_written("2330 避免", "2330")
    ok = ok and written == "避免"
    print("  [OK]" if ok else "  [FAIL] " + str((broker_of("兆豐"), broker_of("JP"), broker_of("國票"), written)))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
