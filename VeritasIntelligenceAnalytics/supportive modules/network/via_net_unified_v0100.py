#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_net_unified_v0100 — VDF 統包網路工具 shim（只增不減）
============================================================
補齊引擎尋找的 supportive modules/network/via_net_unified_v*.py。
本體委派 VIA_NetSupport；提供 VDF 車道慣用 http_json 介面。
紅線：VIA_NET_CONSENT 未開不發包；永不代設同意閘；缺依賴誠實退化。
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

import importlib.util
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUP = HERE.parent
_NS = None
_NS_ERR = ""


def _load_netsupport():
    global _NS, _NS_ERR
    if _NS is not None:
        return _NS
    cand = SUP / "VIA_NetSupport.py"
    if not cand.exists():
        _NS_ERR = "VIA_NetSupport.py missing"
        return None
    try:
        spec = importlib.util.spec_from_file_location("VIA_NetSupport_dyn", cand)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["VIA_NetSupport_dyn"] = mod
        spec.loader.exec_module(mod)
        _NS = mod
        return _NS
    except Exception as exc:
        _NS_ERR = f"{type(exc).__name__}: {str(exc)[:120]}"
        return None


def net_consent() -> bool:
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "net_consent"):
        return bool(ns.net_consent())
    return os.environ.get("VIA_NET_CONSENT", "").upper() in ("YES", "1", "TRUE")


def net_ok() -> bool:
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "net_ok"):
        return bool(ns.net_ok())
    try:
        import requests  # noqa: F401
        return True
    except ImportError:
        return False


def get_session():
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "get_session"):
        return ns.get_session()
    return None


def fetch_json(url: str, **kw):
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "fetch_json"):
        return ns.fetch_json(url, **kw)
    return None


def fetch_text(url: str, **kw):
    ns = _load_netsupport()
    if ns is not None and hasattr(ns, "fetch_text"):
        return ns.fetch_text(url, **kw)
    return None


def http_json(url: str, **kw) -> dict:
    """VDF 車道慣用出口：{state, data, note}。未同意/失敗誠實非 OK。"""
    if not net_consent():
        return {"state": "NO_CONSENT", "data": None, "note": "VIA_NET_CONSENT not YES"}
    data = fetch_json(url, **kw)
    if data is None:
        note = _NS_ERR or "fetch_json returned None"
        return {"state": "FAIL", "data": None, "note": note[:160]}
    return {"state": "OK", "data": data, "note": ""}


def http_text(url: str, **kw) -> dict:
    if not net_consent():
        return {"state": "NO_CONSENT", "data": None, "note": "VIA_NET_CONSENT not YES"}
    text = fetch_text(url, **kw)
    if text is None:
        return {"state": "FAIL", "data": None, "note": _NS_ERR or "fetch_text returned None"}
    return {"state": "OK", "data": text, "note": ""}


def yahoo_quote_summary(*_a, **_k) -> dict:
    return {"state": "SKIP", "data": None, "note": "yahoo_quote_summary not in NetSupport shim (honest)"}


if __name__ == "__main__":
    print(
        f"via_net_unified_v0100 · net_ok={net_ok()} · "
        f"consent={'YES' if net_consent() else 'NO'} · "
        f"support={'OK' if _load_netsupport() else _NS_ERR or 'missing'} · "
        f"accel={'ON' if VIA_ACCEL is not None else 'OFF'}"
    )
