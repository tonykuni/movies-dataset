#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_NetSupport — 網路支援模組(輔助性工具;graceful 全退化)
============================================================
操作員令(2026-08-12):功能工具統一導入「網路支援模組」。本模組為
輕量網路輔助層,紅線內建:
  ① 不爬站 — 僅供引擎對「已授權 API/自家端點」呼叫之統一出口
  ② 零 CDN — 不下載第三方資產;快取只落本機
  ③ 憑證/金鑰只走環境變數 — 本模組永不落鍵
  ④ graceful — requests 缺席/離線時全退化 None,引擎行為零改變
  ⑤ 代理感知 — 尊重 HTTPS_PROXY/REQUESTS_CA_BUNDLE 環境,不停用驗證
  ⑥ 同意閘(2026-08-12 規定)— 網路工具開啟使用前須經操作員同意:
     環境變數 VIA_NET_CONSENT=YES 才發包;未同意一律 None+誠實告示
介面:
  net_ok()                     → bool 網路棧可用性(不發包,只驗依賴)
  get_session()                → requests.Session|None(重試+退避內建)
  fetch_json(url, **kw)        → dict|None(誠實 None,不假資料)
  fetch_text(url, **kw)        → str|None
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
import os
import time

_UA = "VIA-NetSupport/0100 (internal-engine)"


def net_consent() -> bool:
    """操作員同意閘:VIA_NET_CONSENT=YES/1/TRUE 才視為已同意(紅線)。"""
    return os.environ.get("VIA_NET_CONSENT", "").upper() in ("YES", "1", "TRUE")


def net_ok() -> bool:
    try:
        import requests  # noqa: F401
        return True
    except ImportError:
        return False


def get_session():
    """代理感知 Session;未經同意/requests 缺席回 None(graceful)。"""
    if not net_consent():
        print("  [同意閘] 網路工具未經操作員同意——setx VIA_NET_CONSENT YES 後新視窗生效(紅線)")
        return None
    try:
        import requests
    except ImportError:
        return None
    s = requests.Session()
    s.headers.update({"User-Agent": _UA})
    ca = os.environ.get("REQUESTS_CA_BUNDLE")
    if ca and os.path.exists(ca):
        s.verify = ca
    return s


def _fetch(url: str, retries: int = 3, timeout: int = 30, backoff: float = 2.0):
    s = get_session()
    if s is None:
        return None
    last = None
    for i in range(retries):
        try:
            r = s.get(url, timeout=timeout)
            if r.status_code == 200:
                return r
            last = f"HTTP {r.status_code}"
        except Exception as exc:
            last = f"{type(exc).__name__}"
        time.sleep(backoff ** i)
    # 誠實退化:不假資料;呼叫端自決 fallback
    _ = last
    return None


def fetch_json(url: str, **kw):
    r = _fetch(url, **kw)
    if r is None:
        return None
    try:
        return r.json()
    except (ValueError, json.JSONDecodeError):
        return None


def fetch_text(url: str, **kw):
    r = _fetch(url, **kw)
    return r.text if r is not None else None


if __name__ == "__main__":
    print(f"VIA_NetSupport · net_ok={net_ok()} · 同意閘={'已同意' if net_consent() else '未同意(預設關)'} · proxy={'在' if os.environ.get('HTTPS_PROXY') else '無'}")
