#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Three ticker forms must share one core. Zones must agree before a field is kept.

Does not open a PDF and does not call Paddle. Those engines are named here
so the order stays in one place.
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
import importlib.util
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
FIELDS = (
    "report_date", "filename", "broker", "analyst", "ticker",
    "yfinance_ticker", "bloomberg_ticker", "rating", "target_price_adj",
    "upside_pct", "yfinance_target_median", "factset_target_median",
)
ORDER = ("layout", "restore", "plumber", "paddle")


def _hub():
    hits = sorted((VIA / "supportive modules" / "70_VRN_Rules").glob("SUP_MDL749_VRNFieldRuleHub_v*.py"))
    spec = importlib.util.spec_from_file_location("hub749b", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _core(token: str, hub) -> str:
    found = hub.ticker_platform(token) or {}
    code = str(found.get("canonical") or "")
    return code[:4] if len(code) >= 4 else ""


def confirm_codes(code: str, market: str | None) -> dict:
    hub = _hub()
    local = _core(code, hub)
    if not local:
        return {"ok": False, "why": "not a listed form"}
    yahoo = {"TWSE": local + ".TW", "TPEX": local + ".TWO"}.get(str(market or "").upper())
    bloomberg = f"{local} TT"
    cores = {"local": local, "bloomberg": _core(bloomberg, hub)}
    if yahoo:
        cores["yfinance"] = _core(yahoo, hub)
    ok = bool(yahoo) and len(set(cores.values())) == 1 and "" not in cores.values()
    return {
        "ok": ok,
        "why": "" if ok else ("market unknown" if not yahoo else "core mismatch"),
        "core": local,
        "yfinance_ticker": yahoo,
        "bloomberg_ticker": bloomberg if cores.get("bloomberg") == local else None,
    }


def upside(target_adj, price) -> float | None:
    try:
        target = float(target_adj)
        last = float(price)
    except (TypeError, ValueError):
        return None
    if last == 0:
        return None
    return (target / last - 1.0) * 100.0


def cross(info: dict, body: dict, annual: dict) -> dict:
    """info = left/right page zones, body = center, annual = statement page."""
    out = {}
    for field in FIELDS:
        seen = {}
        for zone, src in (("info", info), ("body", body), ("annual", annual)):
            value = src.get(field)
            if value not in (None, ""):
                seen[zone] = value
        vals = list(seen.values())
        if not vals:
            state = "NODATA"
        elif all(item == vals[0] for item in vals):
            state = "AGREE"
        else:
            state = "CONFLICT"
        out[field] = {"state": state, "seen": seen}
    return out


def engine_order() -> list[dict]:
    vrn = HERE
    layout = next(vrn.glob("20260804/VRN_MDL002_LayoutExtractor.py"), None)
    restore = sorted(vrn.glob("VRN_ENG085_MarkdownRestore_v*.py"))
    plumber = sorted(vrn.glob("VRN_ENG072_FirstPageText_v*.py"))
    return [
        {"id": "layout", "state": "PRESENT" if layout else "ABSENT", "file": layout.name if layout else None},
        {"id": "restore", "state": "PRESENT" if restore else "ABSENT", "file": restore[-1].name if restore else None},
        {"id": "plumber", "state": "PRESENT" if plumber else "ABSENT", "file": plumber[-1].name if plumber else None},
        {"id": "paddle", "state": "ABSENT", "file": None, "why": "no Paddle engine in this tree"},
    ]


def selftest() -> int:
    tw = confirm_codes("2330", "TWSE")
    two = confirm_codes("6488", "TPEX")
    bad = confirm_codes("2330", None)
    up = upside(100, 80)
    zones = cross(
        {"ticker": "2330", "target_price_adj": 100},
        {"ticker": "2330", "target_price_adj": 100},
        {"ticker": "2330"},
    )
    clash = cross({"rating": "Buy"}, {"rating": "Hold"}, {})
    ok = (
        tw["ok"] and tw["yfinance_ticker"] == "2330.TW" and tw["bloomberg_ticker"] == "2330 TT"
        and two["ok"] and two["yfinance_ticker"] == "6488.TWO"
        and bad["ok"] is False
        and abs(up - 25) < 1e-9
        and zones["ticker"]["state"] == "AGREE"
        and clash["rating"]["state"] == "CONFLICT"
        and [row["id"] for row in engine_order()] == list(ORDER)
    )
    print("  [OK]" if ok else f"  [FAIL] {tw} {two} {up} {zones['ticker']} {clash['rating']}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
