#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Cut a report filename at every script change. Rules stay on the hub."""
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


def _hub():
    hits = sorted((VIA / "supportive modules" / "70_VRN_Rules").glob("SUP_MDL749_VRNFieldRuleHub_v*.py"))
    if not hits:
        raise RuntimeError("SUP_MDL749 missing")
    spec = importlib.util.spec_from_file_location("hub749", hits[-1])
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _kind(ch: str) -> str:
    if "\u4e00" <= ch <= "\u9fff":
        return "C"
    if ch.isascii() and ch.isalpha():
        return "E"
    if ch.isdigit():
        return "N"
    return "S"


def _stem(name: str) -> str:
    text = str(name or "").strip()
    for ext in (".pdf", ".docx", ".txt", ".jpg", ".jpeg", ".png"):
        if text.lower().endswith(ext):
            return text[: -len(ext)].strip()
    return text


def cut(name: str) -> list[str]:
    stem = _stem(name)
    parts: list[str] = []
    buf: list[str] = []
    prev = ""
    for ch in stem:
        kind = _kind(ch)
        if kind == "S":
            if buf:
                parts.append("".join(buf))
                buf = []
            prev = ""
            continue
        if prev and kind != prev:
            parts.append("".join(buf))
            buf = []
        buf.append(ch)
        prev = kind
    if buf:
        parts.append("".join(buf))
    return [part.strip() for part in parts if part.strip()]


def read_name(name: str) -> dict:
    hub = _hub()
    rows = []
    for token in cut(name):
        if token.isdigit() and len(token) == 4:
            tick = hub.ticker_platform(token) or {}
            if tick.get("canonical"):
                rows.append({
                    "text": token, "role": "TICKER", "code": tick["canonical"],
                    "ambiguous_year": bool(hub.parse_year_any(token)),
                })
                continue
        if token.isdigit() and len(token) > 4:
            found = hub.parse_date_any(token) or {}
            if found.get("iso"):
                rows.append({"text": token, "role": "DATE", "iso": found["iso"], "gran": found.get("gran")})
                continue
        canon, how = hub.broker_of(token)
        if canon:
            rows.append({"text": token, "role": "BROKER", "canon": canon, "how": how})
            continue
        rows.append({"text": token, "role": "OTHER"})
    ticker = next((row for row in rows if row["role"] == "TICKER"), None)
    date = next((row for row in rows if row["role"] == "DATE"), None)
    broker = next((row for row in rows if row["role"] == "BROKER"), None)
    return {"name": name, "parts": rows, "ticker": ticker, "date": date, "broker": broker}


def selftest() -> int:
    got = read_name("JP-2330 20250718.pdf")
    two = cut("6488.TWO.pdf")
    yuanta = read_name("元大-2330.pdf")
    ok = (
        [row["role"] for row in got["parts"]] == ["BROKER", "TICKER", "DATE"]
        and got["ticker"]["code"] == "2330"
        and got["date"]["iso"] == "2025-07-18"
        and got["broker"]["canon"] == "JPM"
        and two == ["6488", "TWO"]
        and yuanta["broker"]["canon"] == "YUANTA"
    )
    print("  [OK]" if ok else f"  [FAIL] {got} {two} {yuanta}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
