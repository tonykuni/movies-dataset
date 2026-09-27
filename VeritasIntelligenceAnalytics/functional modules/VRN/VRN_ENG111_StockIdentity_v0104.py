#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Every broker shows its English short name. 兆豐 is MEGA. WATERLAND is not a name.

國票 stays and shows IBF. Older lists are not rewritten.
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
import importlib.util

HERE = Path(__file__).resolve().parent
SHOW = {
    "中信": "CTBC",
    "元大": "Yuanta",
    "兆豐": "MEGA",
    "凱基": "KGI",
    "台新": "Taishin",
    "國泰": "Cathay",
    "富邦": "Fubon",
    "永豐": "SinoPac",
    "統一": "President",
    "華南": "HuaNan",
    "MQ": "MQ",
    "CLSA": "CLSA",
    "Daiwa": "Daiwa",
    "UBS": "UBS",
    "Citi": "Citi",
    "GS": "GS",
    "JP": "JPM",
    "MS": "MS",
    "國票": "IBF",
}
DROPPED = {"WATERLAND"}


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PRIOR = _load("ident_v0103_for_v0104", HERE / "VRN_ENG111_StockIdentity_v0103.py")


def broker_of(text: str) -> str:
    folded = PRIOR.BASE.strip_contacts(text).upper()
    best = None
    best_alias = ""
    for row in PRIOR.BASE.BASE.broker_rows():
        for alias in row.get("aliases") or []:
            alias = str(alias).strip()
            if len(alias) < 2 or alias.upper() in DROPPED:
                continue
            if re.search(r"[\u4e00-\u9fff]", alias):
                hit = alias in PRIOR.BASE.strip_contacts(text)
            else:
                hit = re.search(rf"(?<![A-Z]){re.escape(alias.upper())}(?![A-Z])", folded) is not None
            if hit and len(alias) > len(best_alias):
                best, best_alias = row, alias
    if not best:
        return ""
    return SHOW.get(str(best.get("canonical") or ""), str(best.get("show") or ""))


def identify(filename: str, text: str, markets: dict | None = None) -> dict:
    got = PRIOR.identify(filename, text, markets)
    head = PRIOR.BASE.strip_contacts((got.get("restored") or "").split("評等分級")[0])
    got["broker"] = broker_of(filename) or broker_of(head)
    got["rating"] = PRIOR.rating_as_written(head, str(got.get("ticker") or "")) or got.get("rating") or ""
    return got


def selftest() -> int:
    ok = broker_of("兆豐證券") == "MEGA" and broker_of("mega") == "MEGA" and broker_of("MEGABANK") == "MEGA"
    ok = ok and broker_of("中信") == "CTBC" and broker_of("華南投顧") == "HuaNan" and broker_of("國票") == "IBF"
    ok = ok and broker_of("IBF") == "IBF" and broker_of("WATERLAND") == ""
    ok = ok and broker_of("JP") == "JPM" and broker_of("大和") == "Daiwa"
    ok = ok and PRIOR.rating_as_written("2330 避免", "2330") == "避免"
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
