#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG099 — TAIEX and TPEx index rows follow the stock day.

Trading and chip fields use the same names as a stock. The only allowed
sources are TWSE for 加權 and TPEX for 櫃買. yfinance is rejected.
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent.parent
POLICY = VIA / "supportive modules" / "registry" / "VIA_TW_IndexSameDay_Policy_v0100.json"

FIELDS = (
    "open", "high", "low", "close", "volume", "value",
    "foreign_net", "trust_net", "dealer_net", "total_net",
    "foreign_holding_pct", "trust_holding_pct", "dealer_holding_pct",
    "margin_bal", "short_bal", "short_margin_ratio",
    "margin_maint_pct", "margin_usage_pct", "short_usage_pct",
    "daytrade_volume", "daytrade_value",
)


def _num(value):
    if value is None or value == "":
        return None
    return float(value)


def accept(row: dict, book: dict | None = None) -> dict:
    book = book or json.loads(POLICY.read_text(encoding="utf-8"))
    code = str(row.get("code") or "").upper()
    spec = (book.get("indexes") or {}).get(code)
    source = str(row.get("source") or "")
    provider = str(row.get("provider") or "")
    if provider.lower() == "yfinance" or code in set(book.get("excluded") or []):
        return {"ok": False, "why": "yfinance excluded"}
    if spec is None:
        return {"ok": False, "why": "not an index"}
    if source != spec["source"]:
        return {"ok": False, "why": f"{code} requires {spec['source']}"}
    out = {"ok": True, "date": row.get("date"), "code": code, "source": source, "name": spec["name"]}
    for key in FIELDS:
        out[key] = _num(row.get(key))
    return out


def selftest() -> int:
    checks = []

    def chk(name, ok):
        checks.append((name, bool(ok)))

    book = json.loads(POLICY.read_text(encoding="utf-8"))
    taiex = accept({"date": "2026-09-25", "code": "TAIEX", "source": "TWSE",
                    "close": 22000, "volume": 100, "value": 200, "total_net": 5})
    otc = accept({"date": "2026-09-25", "code": "TPEX", "source": "TPEX", "close": 250})
    chk("policy", book["indexes"]["TAIEX"]["source"] == "TWSE" and book["indexes"]["TPEX"]["name"] == "櫃買指數")
    chk("taiex", taiex["ok"] and taiex["close"] == 22000 and taiex["total_net"] == 5 and taiex["margin_bal"] is None)
    chk("tpex", otc["ok"] and otc["source"] == "TPEX")
    chk("reject yahoo index", accept({"code": "^TWII", "source": "TWSE", "provider": "yfinance"})["ok"] is False)
    chk("reject crossed source", accept({"code": "TAIEX", "source": "TPEX", "close": 1})["ok"] is False)
    bad = [name for name, ok in checks if not ok]
    print(f"[VDF_ENG099 v0100] {len(checks) - len(bad)}/{len(checks)}" + (f" FAIL {bad}" if bad else " OK"))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(selftest())
