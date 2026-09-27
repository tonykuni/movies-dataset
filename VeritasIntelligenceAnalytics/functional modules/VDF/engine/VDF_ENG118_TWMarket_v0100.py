#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One TWSE list and one TPEX list. A code that answers decides .TW or .TWO."""
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

import json
import re
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
CACHE = HERE.parent / "output_hub" / "tw_market_v0100.json"
CODE = re.compile(r"^[1-9]\d{3}$")
TWSE = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
TPEX = "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap03_O"


def _get(url: str, timeout: int = 12) -> list:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data if isinstance(data, list) else []


def _keep(rows: list, code_key: str, name_key: str) -> dict:
    found = {}
    for row in rows:
        code = str(row.get(code_key) or "").strip()
        if CODE.fullmatch(code):
            found[code] = str(row.get(name_key) or "").strip()
    return found


def classify(twse: dict, tpex: dict) -> dict:
    out = {}
    for code in set(twse) | set(tpex):
        on_twse, on_tpex = code in twse, code in tpex
        if on_twse and on_tpex:
            market, yahoo = "", ""
        elif on_twse:
            market, yahoo = "TWSE", code + ".TW"
        else:
            market, yahoo = "TPEX", code + ".TWO"
        out[code] = {
            "market": market,
            "yfinance": yahoo,
            "bloomberg": code + " TT",
            "local": code,
            "name": twse.get(code) or tpex.get(code) or "",
            "both": on_twse and on_tpex,
        }
    return out


def load(refresh: bool = False) -> dict:
    if CACHE.is_file() and not refresh:
        return json.loads(CACHE.read_text(encoding="utf-8"))
    table = classify(
        _keep(_get(TWSE), "Code", "Name"),
        _keep(_get(TPEX), "SecuritiesCompanyCode", "CompanyAbbreviation"),
    )
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    CACHE.write_text(json.dumps(table, ensure_ascii=False), encoding="utf-8")
    return table


def selftest() -> int:
    table = classify({"2330": "台積電", "6873": "泓德能源"}, {"6488": "環球晶", "6873": "重複"})
    ok = table["2330"]["yfinance"] == "2330.TW" and table["6488"]["yfinance"] == "6488.TWO"
    ok = ok and table["6873"]["yfinance"] == "" and table["6873"]["both"] is True
    ok = ok and table["2330"]["bloomberg"] == "2330 TT"
    print("  [OK]" if ok else "  [FAIL] " + str(table["6873"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
